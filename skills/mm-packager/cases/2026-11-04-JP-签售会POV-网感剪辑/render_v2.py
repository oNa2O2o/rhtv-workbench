# -*- coding: utf-8 -*-
"""v2 正片渲染（POV 剪辑 → 定格缩进手机 → 划卡/聊天 UI），口播驱动排期。输出无声 mp4。
用法: python -I render_v2.py spec.json out.mp4 [--stills t1,t2]
"""
import sys, os, json, math, glob, subprocess
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_pov import sticker, emoji_img, place, pop, drop_shadow, src_frame

P = "F:/钟海明/2026/2026年11月4日MM-JP-女性向-签售会POV"
W, H, FPS = 1080, 1920, 30
F_CAP = f"{P}/工作/fonts/MPLUSRounded1c-Black.ttf"
LOGO = [(64, 240, 224), (112, 144, 240), (224, 160, 240)]      # 青 → 蓝紫 → 粉紫
INK = (40, 30, 110)
PH = dict(x=108, y=340, w=864, h=1536, r=60)                   # 手机屏位置（0.8 倍）


def lerp(a, b, p): return a + (b - a) * p
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eo(x): return 1 - (1 - clamp(x)) ** 3


def hgrad(w, h):
    g = Image.new("RGB", (w, 1)); px = g.load()
    for x in range(w):
        u = x / max(1, w - 1) * (len(LOGO) - 1); i = min(int(u), len(LOGO) - 2); f = u - i
        px[x, 0] = tuple(int(lerp(LOGO[i][k], LOGO[i + 1][k], f)) for k in range(3))
    return g.resize((w, h))


@lru_cache(None)
def cap_img(lines_json, size, maxw=1000):
    """lines: [[[text, 'w'|'g'], ...], ...]  白字/渐变字 + 深紫粗描边，无底框"""
    lines = json.loads(lines_json)
    while True:
        f = ImageFont.truetype(F_CAP, size); sw = max(6, int(size * .13))
        widths = [sum(f.getlength(t) for t, _ in ln) for ln in lines]
        if max(widths) + sw * 2 <= maxw or size < 60: break
        size -= 4
    lh = int(size * 1.22); Wd = int(max(widths)) + sw * 2 + 20; Hd = lh * len(lines) + sw * 2 + 20
    out = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    for li, ln in enumerate(lines):
        x = (Wd - widths[li]) / 2; y = 10 + sw + li * lh
        for t, kind in ln:
            d = ImageDraw.Draw(out)
            d.text((x, y), t, font=f, fill=INK + (255,), stroke_width=sw, stroke_fill=INK + (255,))
            m = Image.new("L", (Wd, Hd), 0); ImageDraw.Draw(m).text((x, y), t, font=f, fill=255)
            fill = hgrad(Wd, Hd).convert("RGBA") if kind == "g" else Image.new("RGBA", (Wd, Hd), (255, 255, 255, 255))
            out.paste(fill, (0, 0), m)
            x += f.getlength(t)
    return drop_shadow(out, (0, 10), 12, 120)


class Clip:
    """按顺序读取 mp4 帧（30fps）"""
    def __init__(self, path):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.i = -1; self.last = None
    def get(self, idx):
        while self.i < idx:
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            self.last = Image.frombytes("RGB", (W, H), b); self.i += 1
        return self.last


def clip_still(path, t):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return Image.frombytes("RGB", (W, H), b[:W * H * 3])


def pov_frame(sh, lt):
    u = lt / sh["dur"]
    st = sh["t0"] if sh.get("freeze") else sh["t0"] + (sh["t1"] - sh["t0"]) * u
    fr = src_frame(sh["src"], int(round(st * 24)) + 1)
    z0, z1 = sh.get("z", [1.0, 1.04]); z = lerp(z0, z1, eo(u) if not sh.get("freeze") else 1)
    cx, cy = sh.get("c", [.5, .42]); cw, ch = W / z, H / z
    x0 = clamp(cx * W - cw / 2, 0, W - cw); y0 = clamp(cy * H - ch / 2, 0, H - ch)
    im = fr.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    if sh.get("freeze"):
        im = Image.blend(im, im.convert("L").convert("RGB"), .35)
    return im


@lru_cache(None)
def phone_mask(w, h, r):
    m = Image.new("L", (w * 2, h * 2), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), r * 2, fill=255)
    return m.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def stage_bg(path):
    im = Image.open(path).convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(40))
    g = hgrad(W, H).rotate(0)
    im = Image.blend(im, g, .55)
    return im.convert("RGBA")


def put_phone(cv, scr, p):
    """p=0 全屏, p=1 手机位置"""
    x = lerp(0, PH["x"], p); y = lerp(0, PH["y"], p); w = int(lerp(W, PH["w"], p)); h = int(lerp(H, PH["h"], p)); r = int(lerp(0, PH["r"], p))
    s = scr.resize((w, h), Image.BILINEAR).convert("RGBA")
    if r > 0:
        bz = int(10 * p)
        sh = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((40, 50, 40 + w, 50 + h), r, fill=(30, 20, 70, 120))
        cv.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (int(x) - 40, int(y) - 40))
        ImageDraw.Draw(cv).rounded_rectangle((int(x) - bz, int(y) - bz, int(x) + w + bz, int(y) + h + bz), r + bz, fill=(255, 255, 255, 255))
        s.putalpha(phone_mask(w, h, r))
    cv.alpha_composite(s, (int(x), int(y)))


def main():
    S = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
    stills = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")] if "--stills" in sys.argv else None
    shots = S["shots"]; t = 0
    for s in shots: s["start"] = t; t += s["dur"]
    END = S["end"]; N = int(round(END * FPS))
    FZ, SHR, APP, CHAT = S["freezeAt"], S["shrinkAt"], S["appAt"], S["chatAt"]
    bg = stage_bg(f"{P}/工作/up/{S['bgFrame']}.jpg")
    sw = Clip(S["swipe"]) if not stills else None; ct = Clip(S["chat"]) if not stills else None
    flashes = [s["start"] for s in shots[1:] if s.get("flash")]
    frames = [int(round(x * FPS)) for x in stills] if stills else range(N)
    proc = None if stills else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                                 "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    from render_end import logo as _logo
    LOGO = _logo()
    freeze_img = None
    for fi in frames:
        gt = fi / FPS
        # ---- 屏幕内容 ----
        if gt < FZ:
            sh = next((s for s in shots if s["start"] <= gt < s["start"] + s["dur"]), shots[-1])
            scr = pov_frame(sh, gt - sh["start"])
        else:
            if freeze_img is None:
                sh = shots[-1]; freeze_img = pov_frame({**sh, "freeze": True, "t0": sh["t1"]}, 0)
            scr = freeze_img
            if gt >= APP - .25:
                if gt < CHAT:
                    li = int(round((gt - APP) * FPS))
                    ui = (sw.get(max(0, li)) if sw else clip_still(S["swipe"], max(0, gt - APP)))
                else:
                    ui = ct.get(int(round((gt - CHAT) * FPS))) if ct else clip_still(S["chat"], gt - CHAT)
                a = clamp((gt - (APP - .25)) / .25)
                scr = Image.blend(scr, ui, a) if a < 1 else ui
        p = eio((gt - SHR) / .6) if gt >= SHR else 0
        if p > 0:
            cv = bg.copy(); put_phone(cv, scr, p)
        else:
            cv = scr.convert("RGBA")
        # ---- 贴纸 / emoji ----
        for o in S.get("stickers", []):
            ot = gt - o["t"]
            if ot < 0 or ot > o["d"]: continue
            sc = pop(ot) * min(1, (o["d"] - ot) / .12)
            im = sticker(o["n"], o.get("w", 300)) if "n" in o else emoji_img(o["e"], o.get("size", 120))
            place(cv, im, o["x"], o["y"] + 8 * math.sin(gt * 5 + o["x"]), sc, o.get("rot", 0) + 5 * math.sin(gt * 6 + o["y"]))
        # ---- 大字幕 ----
        for c in S["caps"]:
            ot = gt - c["t"]
            if ot < 0 or ot > c["d"]: continue
            im = cap_img(json.dumps(c["lines"], ensure_ascii=False), c.get("size", 130))
            sc = pop(ot, .22) * (min(1, (c["d"] - ot) / .08) if c.get("out", True) else 1)
            sk = c.get("shake", 0) * max(0, 1 - ot / .6)
            dx = sk * math.sin(ot * 75); dy = sk * .6 * math.cos(ot * 61)
            place(cv, im, W / 2 + dx, c["y"] + dy, sc, c.get("rot", 0) + sk * .08 * math.sin(ot * 50))
        # ---- 顶部 Logo（剪辑段常驻，缩进手机时淡出）----
        if gt < SHR:
            la = 1 - clamp((gt - (SHR - .25)) / .25)
            place(cv, LOGO, W / 2, 150 + 3 * math.sin(gt * 2.4), .62 * pop(gt - .05, .35), 0, alpha=la)
        # ---- 闪白 ----
        for f0 in flashes:
            dt = gt - f0
            if 0 <= dt < .15:
                cv = Image.blend(cv, Image.new("RGBA", (W, H), (255, 255, 255, 255)), .7 * (1 - dt / .15))
        img = cv.convert("RGB")
        if stills:
            os.makedirs(out, exist_ok=True); img.save(f"{out}/v{gt:05.2f}.jpg", quality=88)
        else:
            proc.stdin.write(img.tobytes())
            if fi % 60 == 0: print("frame", fi, "/", N, flush=True)
    if proc: proc.stdin.close(); proc.wait()
    print("done", END)


if __name__ == "__main__":
    main()
