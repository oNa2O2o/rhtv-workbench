#!/usr/bin/env python
"""逐词 ASR：视频/音频 → words.json（每个词的起止时间），用来对齐字幕和音效。屏幕文字一律用全量文案，ASR 只用来取时间。

用法：
  python asr.py <视频或音频> [--lang ja] [--out words.json] [--engine scribe|whisper] [--model medium]
                [--prompt "台词"] [--segments 0-4.5,4.5-12] [--energy energy.json] [--threads 2]
- 默认 ElevenLabs scribe_v2（逐字，质量最好）。scribe 失败（CLI 没装、没登录、报错、没出词）自动转 whisper，并打印原因。
- whisper 是离线备选：faster-whisper medium（--model 或环境变量 ASR_MODEL 可改），CPU int8、--threads 线程、beam 1、
  不接上文；ffmpeg 先解成 16k 单声道数组再交给 transcribe。不降级到 small（small 会幻听）；large-v3 在本机加载就 OOM，不作默认。
- whisper 切段：--segments 手给；或 --energy 读 energy.json（−35 dB 能量段）按句切，每句前后各留 0.25 s；都不给就整段。
- --prompt 自动去掉「……」「——」（带省略号的 prompt 会让 whisper 只吐省略号）。scribe 不用 prompt，也不切段。
- ElevenLabs CLI 调用经 heavy_lock("elevenlabs") 串行（并发会把 CLI 的 OAuth 登录清掉，之后 TTS/SFX 全停）；
  whisper 经 heavy_lock("asr") 排队，可用内存不够先等。
输出：{"words":[{"w":"さ","s":2.52,"e":2.70}], "text": "...", "engine": "scribe|whisper", "model": "..."}，同时打印「起点+词」一行。
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mmkit.heavy import heavy_lock

SR = 16000
PAD = 0.25                      # 能量段前后各留的秒数
LANG3 = {"ja": "jpn", "ko": "kor", "en": "eng", "zh": "zho"}


def build_parser():
    ap = argparse.ArgumentParser(description="逐词 ASR → words.json")
    ap.add_argument("src")
    ap.add_argument("--lang", default="ja")
    ap.add_argument("--out")
    ap.add_argument("--engine", default="scribe", choices=["scribe", "whisper"])
    ap.add_argument("--model", default=os.environ.get("ASR_MODEL", "medium"))
    ap.add_argument("--prompt")
    ap.add_argument("--segments", help="手给切段：0-4.5,4.5-12（秒）")
    ap.add_argument("--energy", help="energy.json：按能量段切句（whisper 用）")
    ap.add_argument("--threads", type=int, default=2)
    return ap


def clean_prompt(s):
    """去掉省略号和破折号（……、…、‥、——、―、─、...），保留长音「ー」。"""
    if not s: return None
    s = re.sub(r"[…‥]+|[—―─]+|\.{3,}|・{3,}", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def parse_segments(s):
    """'0-4.5,4.5-12' → [(0.0, 4.5), (4.5, 12.0)]。"""
    out = []
    for x in (s or "").split(","):
        x = x.strip()
        if not x: continue
        a, b = x.split("-", 1)
        a, b = float(a), float(b)
        if b <= a: raise ValueError(f"切段 {x} 终点不大于起点")
        out.append((a, b))
    return out


def energy_segments(segs, dur=None, pad=PAD):
    """能量段 → 每句前后各留 pad 秒；相邻两句留白重叠时在两句原始间隙中点分开。"""
    out = []
    for a, b in segs:
        lo, hi = max(0.0, a - pad), b + pad
        if dur: hi = min(dur, hi)
        if out and lo < out[-1][1]:
            mid = (out[-1][2] + a) / 2
            out[-1][1] = mid; lo = mid
        out.append([lo, hi, b])
    return [(round(lo, 3), round(hi, 3)) for lo, hi, _ in out if hi > lo]


def decode16k(path):
    """ffmpeg 解成 16k 单声道 float32 数组（不把文件路径交给 transcribe，新版 PyAV 会报 metadata_errors）。"""
    import numpy as np
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).copy()


def whisper(path, lang, prompt, segs, model, threads):
    from faster_whisper import WhisperModel
    a = decode16k(path)
    dur = len(a) / SR
    segs = segs or [(0.0, dur)]
    words, text = [], []
    with heavy_lock("asr"):
        m = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=threads)
        for t0, t1 in segs:
            seg = a[int(t0 * SR):int(min(t1, dur) * SR)]
            if len(seg) < SR * 0.1: continue
            ss, _ = m.transcribe(seg, language=lang, word_timestamps=True, initial_prompt=prompt, beam_size=1,
                                 condition_on_previous_text=False)
            for sg in ss:
                text.append(sg.text.strip())
                for w in sg.words or []:
                    words.append({"w": w.word.strip(), "s": round(w.start + t0, 3), "e": round(w.end + t0, 3)})
    return words, "".join(text)


def el_exe():
    exe = shutil.which("elevenlabs")
    if not exe: raise RuntimeError("找不到 elevenlabs CLI（npm i -g @elevenlabs/cli 后 elevenlabs auth login）")
    return exe


def scribe(path, lang):
    exe = el_exe()
    fd, wav = tempfile.mkstemp(suffix=".wav"); os.close(fd)
    try:
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), wav], check=True)
        with heavy_lock("elevenlabs", min_free_gb=0):
            r = subprocess.run([exe, "speech-to-text", "convert", "--model-id", "scribe_v2", "--file", wav,
                                "--language-code", LANG3.get(lang, lang), "--format", "json"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
    finally:
        os.remove(wav)
    if r.returncode != 0:
        raise RuntimeError(f"elevenlabs 退出码 {r.returncode}：{(r.stderr or r.stdout).strip()[-300:]}")
    try: d = json.loads(r.stdout)
    except ValueError: raise RuntimeError(f"elevenlabs 输出不是 JSON：{r.stdout.strip()[:200]}")
    words = [{"w": w["text"], "s": w["start"], "e": w["end"]} for w in d.get("words", []) if w.get("type", "word") == "word"]
    if not words: raise RuntimeError("scribe 没出词")
    return words, d.get("text") or "".join(w["w"] for w in words)


def main(argv=None):
    a = build_parser().parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    prompt = clean_prompt(a.prompt)
    segs = parse_segments(a.segments) if a.segments else None
    if segs is None and a.energy:
        segs = energy_segments(json.load(open(a.energy, encoding="utf-8"))["segments"])
    engine, model = a.engine, a.model
    if engine == "scribe":
        try:
            words, text = scribe(a.src, a.lang); model = "scribe_v2"
        except Exception as e:
            print(f"scribe 失败：{e}\n→ 改用离线备选 whisper {model}（CPU int8，按{'能量段切句' if a.energy and not a.segments else '给定切段' if segs else '整段'}）",
                  file=sys.stderr, flush=True)
            engine = "whisper"
    if engine == "whisper":
        words, text = whisper(a.src, a.lang, prompt, segs, model, a.threads)
    out = a.out or os.path.splitext(a.src)[0] + "_words.json"
    json.dump({"words": words, "text": text, "engine": engine, "model": model}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[{engine} {model}]", " ".join(f"{w['s']:.2f}{w['w']}" for w in words)); print(out)


if __name__ == "__main__":
    main()
