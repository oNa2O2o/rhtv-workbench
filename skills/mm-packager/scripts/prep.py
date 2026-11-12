#!/usr/bin/env python
"""拆片准备（一个版本一条命令）：
  python prep.py --p <05_包装目录> --ver N --src <母版.mp4> [--copy <全量文案.md>] [--lang ja] [--around 12.3,27.9]
                 [--force video|frames|energy|asr]
依次做（输出已存在就跳过，可重复跑）：
  1 video   复制 <src> → $P/素材/视频_N.mp4；高度不足 1920 才放大 → 素材/视频_N_1080.mp4（lanczos + unsharp，crf 14，排 heavy_lock("upscale")）
  2 frames  24 fps 抽帧 → 工程素材/抽帧_版本N/0001.jpg…（第 n 张 = (n−1)/24 s）+ 联系表.jpg（每 0.5 s 一格，格上标秒数和帧号）
  3 energy  audio16k.pcm（16k 单声道 s16le）→ energy.json（−35 dB 能量段）
  4 asr     调 scripts/asr.py 出 words.json；prompt = 全量文案里的台词（表演指示之后、选项之前的行，不写死），whisper 备选时按 energy.json 切句
--force 重做指定步骤（逗号分隔可多个；video 连带重做后面全部）。
--around 12.3,27.9：每个切点前后 ±0.3 s 的整帧拼成 候选_<秒>.jpg，挑定格帧（定格帧 = 切点那一帧，红框标出：floor(秒×24)+1）。
临时文件放 抽帧_版本N/_tmp/，写完再改名到位（多版本并行互不覆盖；中途断了不会被当成已完成）。
"""
import argparse, json, os, re, shutil, subprocess, sys

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SK, "scripts"))
RES = os.environ.get("MM_RES") or "Z:/创新事业部/AIGC项目视频组/mm-packager资源"
STEPS = ("video", "frames", "energy", "asr")
FPS = 24
LANG_COL = {"ja": ("日语", "日本語", "日文", "JP"), "ko": ("韩语", "한국어", "韩文", "KR"),
            "en": ("英语", "English", "英文", "EN"), "zh": ("中文",)}


def ff(*a):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *a], check=True)


def probe_wh(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
                       capture_output=True, text=True, check=True)
    w, h = r.stdout.strip().split(",")[:2]
    return int(w), int(h)


# ---------------------------------------------------------------- 全量文案 → 台词
def dialogue_lines(md_path, lang="ja"):
    """读全量文案里对照表的台词：每张表按表头挑本语言那一列，取「表演指示」行之后、选项（①）或下一个加粗标题之前的行，按 <br> 分句，
    去掉括号里的舞台说明。认不出返回 []。"""
    try: text = open(md_path, encoding="utf-8").read()
    except OSError: return []
    keys = LANG_COL.get(lang, ())
    lines, col, header, on = [], None, True, False
    for raw in text.splitlines():
        s = raw.strip()
        if not s.startswith("|"):
            header, col, on = True, None, False
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c): continue
        if header:
            col = next((i for i, c in enumerate(cells) if any(k in c for k in keys)), len(cells) - 1)
            header = False
            continue
        if any("表演指示" in c for c in cells):
            on = True
            continue
        if not on or col >= len(cells): continue
        cell = cells[col]
        if not cell: continue
        if cell.startswith(("①", "**")):
            on = False
            continue
        for x in re.split(r"<br\s*/?>", cell):
            x = re.sub(r"（[^）]*）|\([^)]*\)", "", x).strip()
            if x: lines.append(x)
    return lines


# ---------------------------------------------------------------- 各步
def font(size):
    from PIL import ImageFont
    cands = []
    fd = os.path.join(RES, "fonts")
    if os.path.isdir(fd):
        names = sorted(os.listdir(fd))
        cands += [os.path.join(fd, n) for n in names if "NotoSansJP-Bold" in n] + [os.path.join(fd, n) for n in names if n.lower().endswith((".ttf", ".otf"))]
    cands += ["C:/Windows/Fonts/arial.ttf", "/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for c in cands:
        try: return ImageFont.truetype(c, size)
        except Exception: pass
    return ImageFont.load_default()


def frame_list(fr):
    return sorted(f for f in os.listdir(fr) if re.fullmatch(r"\d{4}\.jpg", f))


def contact_sheet(fr, tmp):
    from PIL import Image, ImageDraw
    frames = frame_list(fr)
    tw, th, cols, lab = 180, 320, 10, 26
    picks = list(range(1, len(frames) + 1, FPS // 2))
    rows = (len(picks) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + lab)), (20, 20, 20))
    d, f = ImageDraw.Draw(sheet), font(20)
    for i, n in enumerate(picks):
        with Image.open(f"{fr}/{n:04d}.jpg") as im:
            th_img = im.convert("RGB").resize((tw, th))
        x, y = (i % cols) * tw, (i // cols) * (th + lab)
        sheet.paste(th_img, (x, y + lab)); d.text((x + 4, y + 2), f"{(n - 1) / FPS:.1f}s #{n}", fill=(255, 220, 120), font=f)
    out = f"{tmp}/联系表.jpg"; sheet.save(out, quality=88)
    os.replace(out, f"{fr}/联系表.jpg")


def cut_frame(t):
    """切点那一帧：t 秒时画面上的那张（第 n 张 = (n−1)/24 s）。"""
    return int(t * FPS + 1e-6) + 1


def around_sheet(fr, tmp, t, span=0.3):
    from PIL import Image, ImageDraw
    nmax = len(frame_list(fr))
    c = cut_frame(t); k = int(round(span * FPS))
    ns = [n for n in range(c - k, c + k + 1) if 1 <= n <= nmax]
    if not ns: return None
    tw, th, cols, lab = 270, 480, 5, 30
    rows = (len(ns) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + lab)), (20, 20, 20))
    d, f = ImageDraw.Draw(sheet), font(22)
    for i, n in enumerate(ns):
        with Image.open(f"{fr}/{n:04d}.jpg") as im:
            th_img = im.convert("RGB").resize((tw, th))
        x, y = (i % cols) * tw, (i // cols) * (th + lab)
        sheet.paste(th_img, (x, y + lab))
        d.text((x + 4, y + 3), f"#{n}  {(n - 1) / FPS:.3f}s" + ("  切点" if n == c else ""), fill=(255, 90, 90) if n == c else (255, 220, 120), font=f)
        if n == c: d.rectangle((x + 1, y + lab, x + tw - 2, y + lab + th - 2), outline=(255, 40, 40), width=5)
    out = f"{tmp}/候选.jpg"; sheet.save(out, quality=90)
    dst = f"{fr}/候选_{t:.2f}.jpg"; os.replace(out, dst)
    return dst, c


def energy(pcm, thr=-35):
    import numpy as np
    a = np.fromfile(pcm, np.int16).astype(np.float32) / 32768
    hop = 160
    rms = np.sqrt(np.convolve(a ** 2, np.ones(400) / 400, "same")[::hop] + 1e-12)
    on = 20 * np.log10(rms + 1e-9) > thr
    segs, s = [], None
    for i, v in enumerate(on):
        t = i * hop / 16000
        if v and s is None: s = t
        if not v and s is not None:
            if t - s > 0.08: segs.append([round(s, 2), round(t, 2)])
            s = None
    if s is not None and len(on) * hop / 16000 - s > 0.08: segs.append([round(s, 2), round(len(on) * hop / 16000, 2)])
    merged = []
    for g in segs:
        if merged and g[0] - merged[-1][1] < 0.25: merged[-1][1] = g[1]
        else: merged.append(g)
    return {"threshold_db": thr, "segments": merged}


def parse_force(s):
    out = set()
    for x in (s or "").split(","):
        x = x.strip()
        if not x: continue
        if x not in STEPS: raise SystemExit(f"--force 只认 {'/'.join(STEPS)}，收到 {x}")
        out.add(x)
    if "video" in out: out.update(STEPS)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="拆片准备：复制/放大/抽帧/联系表/能量/ASR")
    ap.add_argument("--p", required=True, help="05_包装目录")
    ap.add_argument("--ver", required=True, help="版本号 N")
    ap.add_argument("--src", required=True, help="母版视频")
    ap.add_argument("--copy", help="全量文案.md（缺省 $P/全量文案.md）")
    ap.add_argument("--lang", default="ja")
    ap.add_argument("--around", help="切点秒数，逗号分隔：出前后 ±0.3 s 候选帧拼图")
    ap.add_argument("--force", default="", help="重做：video,frames,energy,asr")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    P, N = a.p.replace("\\", "/").rstrip("/"), str(a.ver)
    force = parse_force(a.force)
    FR = f"{P}/工程素材/抽帧_版本{N}"; TMP = f"{FR}/_tmp"
    os.makedirs(f"{P}/素材", exist_ok=True); os.makedirs(TMP, exist_ok=True)
    SRC, UP = f"{P}/素材/视频_{N}.mp4", f"{P}/素材/视频_{N}_1080.mp4"
    done = []

    # 1 复制 + 放大
    if "video" in force:
        for p in (SRC, UP):
            if os.path.exists(p): os.remove(p)
    if os.path.exists(SRC):
        if os.path.abspath(a.src) != os.path.abspath(SRC) and os.path.exists(a.src) and os.path.getsize(a.src) != os.path.getsize(SRC):
            print(f"注意：{SRC} 和 --src 大小不同，没覆盖；要换母版加 --force video", flush=True)
        done.append("复制（已有，跳过）")
    else:
        shutil.copy2(a.src, f"{TMP}/视频.mp4"); os.replace(f"{TMP}/视频.mp4", SRC); done.append("复制")
    w, h = probe_wh(SRC)
    if h < 1920:
        if os.path.exists(UP): done.append("放大（已有，跳过）")
        else:
            from mmkit.heavy import heavy_lock
            with heavy_lock("upscale"):
                ff("-i", SRC, "-vf", "scale=1080:1920:flags=lanczos,unsharp=5:5:0.6", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                   "-pix_fmt", "yuv420p", "-c:a", "copy", f"{TMP}/放大.mp4")
            os.replace(f"{TMP}/放大.mp4", UP); done.append(f"放大 {w}×{h} → 1080×1920")
        WORK = UP
    else:
        WORK = SRC; done.append(f"不放大（{w}×{h}）")
    print("视频：", WORK, flush=True)

    # 2 抽帧 + 联系表
    if frame_list(FR) and "frames" not in force:
        done.append("抽帧（已有，跳过）")
        if not os.path.exists(f"{FR}/联系表.jpg"): contact_sheet(FR, TMP); done.append("联系表")
    else:
        tdir = f"{TMP}/frames"; shutil.rmtree(tdir, ignore_errors=True); os.makedirs(tdir)
        ff("-i", WORK, "-vf", f"fps={FPS}", "-q:v", "2", f"{tdir}/%04d.jpg")
        for f in frame_list(FR): os.remove(f"{FR}/{f}")          # 新帧抽好了才删旧帧
        for f in frame_list(tdir): os.replace(f"{tdir}/{f}", f"{FR}/{f}")
        shutil.rmtree(tdir, ignore_errors=True)
        contact_sheet(FR, TMP); done.append(f"抽帧 {len(frame_list(FR))} 张 + 联系表")

    # 3 16k pcm + 能量
    PCM, EN = f"{FR}/audio16k.pcm", f"{FR}/energy.json"
    if not os.path.exists(PCM) or "energy" in force:
        ff("-i", SRC, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", f"{TMP}/audio16k.pcm"); os.replace(f"{TMP}/audio16k.pcm", PCM)
    if os.path.exists(EN) and "energy" not in force: done.append("能量（已有，跳过）")
    else:
        json.dump(energy(PCM), open(f"{TMP}/energy.json", "w", encoding="utf-8"), ensure_ascii=False); os.replace(f"{TMP}/energy.json", EN)
        done.append("能量")
    print("能量段：", json.load(open(EN, encoding="utf-8"))["segments"], flush=True)

    # 4 ASR
    WJ = f"{FR}/words.json"
    if os.path.exists(WJ) and "asr" not in force: done.append("ASR（已有，跳过）")
    else:
        copy = a.copy or f"{P}/全量文案.md"
        lines = dialogue_lines(copy, a.lang)
        if not lines: print(f"注意：{copy} 里没认出台词行（表演指示之后、选项之前），ASR 不带 prompt", flush=True)
        cmd = [sys.executable, os.path.join(SK, "scripts", "asr.py"), SRC, "--lang", a.lang, "--out", f"{TMP}/words.json", "--energy", EN]
        if lines: cmd += ["--prompt", " ".join(lines)]
        r = subprocess.run(cmd)
        if r.returncode or not os.path.exists(f"{TMP}/words.json"):
            raise SystemExit(f"ASR 失败（asr.py 退出码 {r.returncode}），{WJ} 没动；看上面 asr.py 的报错")
        os.replace(f"{TMP}/words.json", WJ); done.append("ASR")

    # 候选帧
    for t in [float(x) for x in (a.around or "").split(",") if x.strip()]:
        r = around_sheet(FR, TMP, t)
        if r: print(f"候选帧：{r[0]}（切点帧 #{r[1]}）", flush=True)
    try: os.rmdir(TMP)
    except OSError: pass
    print("完成：" + "；".join(done), flush=True)


if __name__ == "__main__":
    main()
