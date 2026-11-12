"""多版本拆片准备：python prep_version.py N
04_母版/vN_母版.mp4 → 素材/视频_N.mp4 → 放大 视频_N_1080.mp4（lanczos + unsharp，同版本1）
→ 工程素材/抽帧_版本N/0001.jpg…（24 fps，1080×1920）+ 联系表.jpg（每 0.5 s 一格，带时间）
→ audio16k.pcm + words.json（faster-whisper medium CPU，两幕分段 + 全量文案 prompt；屏幕文字照全量文案，ASR 只取时间）
→ energy.json（−35 dB 能量段，用来核对台词起止）。"""
import json, os, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

N = sys.argv[1]
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
ROOT = os.path.dirname(P)
FR = f"{P}/工程素材/抽帧_版本{N}"
os.makedirs(FR, exist_ok=True)
SRC0, SRC, SRC1080 = f"{ROOT}/04_母版/v{N}_母版.mp4", f"{P}/素材/视频_{N}.mp4", f"{P}/素材/视频_{N}_1080.mp4"


def ff(*a):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *a], check=True)


if not os.path.exists(SRC): shutil.copy2(SRC0, SRC)
if not os.path.exists(SRC1080):
    ff("-i", SRC, "-vf", "scale=1080:1920:flags=lanczos,unsharp=5:5:0.6", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
       "-pix_fmt", "yuv420p", "-c:a", "copy", SRC1080)
print("video ok", flush=True)

if not os.path.exists(f"{FR}/0001.jpg"):
    ff("-i", SRC1080, "-vf", "fps=24", "-q:v", "2", f"{FR}/%04d.jpg")
frames = sorted(f for f in os.listdir(FR) if f[:4].isdigit() and f.endswith(".jpg"))
print("frames", len(frames), flush=True)

# 联系表：每 0.5 s 一格（第 n 张 ≈ (n−1)/24 s）
tw, th, cols = 180, 320, 10
picks = list(range(1, len(frames) + 1, 12))
rows = (len(picks) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * (th + 26)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
try: font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
except Exception: font = ImageFont.load_default()
for i, n in enumerate(picks):
    im = Image.open(f"{FR}/{n:04d}.jpg").resize((tw, th))
    x, y = (i % cols) * tw, (i // cols) * (th + 26)
    sheet.paste(im, (x, y + 26)); d.text((x + 4, y + 2), f"{(n - 1) / 24:.1f}s #{n}", fill=(255, 220, 120), font=font)
sheet.save(f"{FR}/联系表.jpg", quality=88)

# 音频 + 能量
pcm = f"{FR}/audio16k.pcm"
if not os.path.exists(pcm): ff("-i", SRC, "-ac", "1", "-ar", "16000", "-f", "s16le", pcm)
a = np.fromfile(pcm, np.int16).astype(np.float32) / 32768
hop = 160
rms = np.sqrt(np.convolve(a ** 2, np.ones(400) / 400, "same")[::hop] + 1e-12)
db = 20 * np.log10(rms + 1e-9)
on = db > -35
segs, s = [], None
for i, v in enumerate(on):
    t = i * hop / 16000
    if v and s is None: s = t
    if not v and s is not None:
        if t - s > 0.08: segs.append([round(s, 2), round(t, 2)])
        s = None
merged = []
for g in segs:
    if merged and g[0] - merged[-1][1] < 0.25: merged[-1][1] = g[1]
    else: merged.append(g)
json.dump({"threshold_db": -35, "segments": merged}, open(f"{FR}/energy.json", "w"), ensure_ascii=False)
print("energy", merged, flush=True)

# 逐词 ASR（medium；large-v3 在这台机器上 OOM）
from faster_whisper import WhisperModel
MODEL = os.environ.get("ASR_MODEL", "medium")
try: m = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=4)
except RuntimeError: MODEL = "small"; m = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=4)
ACTS = [(0.0, 13.0, "ねぇ、最後の検診がまだでしょ？実習終了はダメよ。……何震えてるの、先生が食べちゃうわけないじゃない？"),
        (13.0, len(a) / 16000, "冗談よ、閉じ込めようなんて思ってないわ。ただ健康なままだと……すぐ先生から逃げちゃうから——")]
words, text = [], []
for t0, t1, prompt in ACTS:
    seg = a[int(t0 * 16000):int(t1 * 16000)]
    try: ss = list(m.transcribe(seg, language="ja", word_timestamps=True, initial_prompt=prompt, beam_size=1)[0])
    except RuntimeError:                       # 内存不够 → 换 small 重来
        MODEL = "small"; m = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=4)
        ss = list(m.transcribe(seg, language="ja", word_timestamps=True, initial_prompt=prompt, beam_size=1)[0])
    for sg in ss:
        text.append(sg.text)
        for w in sg.words:
            words.append({"w": w.word.strip(), "s": round(w.start + t0, 3), "e": round(w.end + t0, 3)})
json.dump({"words": words, "text": "".join(text)}, open(f"{FR}/words.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("ASR", MODEL, "".join(text), flush=True)
for w in words: print(f"{w['s']:6.2f}-{w['e']:5.2f} {w['w']}")
