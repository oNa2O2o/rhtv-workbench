#!/usr/bin/env python
"""逐词 ASR：视频/音频 → words.json（每个词的起止时间），用来对齐字幕和音效。屏幕文字一律用全量文案，ASR 只用来取时间。

用法：
  python asr.py <视频或音频> [--lang ja] [--out words.json] [--prompt "该段文案"] [--segments 0-4.5,4.5-12]
- 默认 faster-whisper large-v3：先试 CUDA float16，失败转 CPU int8（CPU 跑 12 s 视频约 1 分钟）。
- 长视频一次识别会把前面糊成一个词 → 用 --segments 按幕切开，并用 --prompt 传该幕文案。
- faster-whisper 段错误（segfault）时加 --engine scribe，改用 ElevenLabs scribe_v2（需 elevenlabs CLI 已登录）。
输出：{"words":[{"w":"さ","s":2.52,"e":2.70}], "text": "..."}，同时打印「起点+词」一行一段。
"""
import argparse, json, os, subprocess, sys, tempfile


def whisper(path, lang, prompt, segs):
    from faster_whisper import WhisperModel
    try: m = WhisperModel("large-v3", device="cuda", compute_type="float16")
    except Exception: m = WhisperModel("large-v3", device="cpu", compute_type="int8")
    out = []
    for a, b in segs or [(None, None)]:
        src = path
        if a is not None:
            src = tempfile.mktemp(suffix=".wav")
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(a), "-to", str(b), "-i", path, "-ac", "1", "-ar", "16000", src], check=True)
        try:
            ss, _ = m.transcribe(src, language=lang, word_timestamps=True, initial_prompt=prompt)
            for s in ss:
                for w in s.words: out.append({"w": w.word.strip(), "s": round(w.start + (a or 0), 3), "e": round(w.end + (a or 0), 3)})
        except RuntimeError:
            m = WhisperModel("large-v3", device="cpu", compute_type="int8")
            ss, _ = m.transcribe(src, language=lang, word_timestamps=True, initial_prompt=prompt)
            for s in ss:
                for w in s.words: out.append({"w": w.word.strip(), "s": round(w.start + (a or 0), 3), "e": round(w.end + (a or 0), 3)})
        if src != path: os.remove(src)
    return out


def scribe(path, lang):
    wav = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", "16000", wav], check=True)
    code = {"ja": "jpn", "ko": "kor", "en": "eng", "zh": "zho"}.get(lang, lang)
    r = subprocess.run(["elevenlabs", "speech-to-text", "convert", "--model-id", "scribe_v2", "--file", wav, "--language-code", code, "--format", "json"],
                       capture_output=True, text=True, encoding="utf-8")
    os.remove(wav)
    d = json.loads(r.stdout)
    return [{"w": w["text"], "s": w["start"], "e": w["end"]} for w in d.get("words", []) if w.get("type", "word") == "word"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("--lang", default="ja"); ap.add_argument("--out")
    ap.add_argument("--prompt"); ap.add_argument("--segments"); ap.add_argument("--engine", default="whisper", choices=["whisper", "scribe"])
    a = ap.parse_args()
    segs = [tuple(map(float, x.split("-"))) for x in a.segments.split(",")] if a.segments else None
    words = scribe(a.src, a.lang) if a.engine == "scribe" else whisper(a.src, a.lang, a.prompt, segs)
    out = a.out or os.path.splitext(a.src)[0] + "_words.json"
    json.dump({"words": words, "text": "".join(w["w"] for w in words)}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.stdout.reconfigure(encoding="utf-8")
    print(" ".join(f"{w['s']:.2f}{w['w']}" for w in words)); print(out)


if __name__ == "__main__":
    main()
