# -*- coding: utf-8 -*-
"""尾板 v2：Logo 开场即出（顶部）→ 角色卡扇形占中上 → 文案 → 按钮 → 商店标。
卡片带「💬 チャット数 ○○万」滚动计数 + 飘心动画，表现热度。
用法: python -I render_end_v2.py HERO out.mp4 [--stills t1,t2]
口播 t7 在尾板内 0.10s 开始：0–1.2「次はあなたの番！」1.9–2.75「MiraiMindで」3.05–5.2「あなただけの推し活を体験しよう！」
"""
import sys, os, json, math, random, subprocess
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_pov import place, pop, drop_shadow, emoji_img
from render_v2 import cap_img, hgrad, lerp, clamp, eo, F_CAP
from render_end import background, logo, button, badges, touch, CH, P

W, H, FPS, DUR = 1080, 1920, 30, 6.8
random.seed(20261104)
COUNT = {k: random.uniform(93, 118) for k in "ABCDE"}       # 万


@lru_cache(None)
def card_base(key, w, h, r=36):
    c = CH[key]; im = Image.open(f"{P}/工作/up/{c['frame']}.jpg").convert("RGB")
    s = max(w / im.width, h / im.height); im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    y0 = int(clamp(im.height * c["focusY"] - h * .35, 0, im.height - h)); x0 = (im.width - w) // 2
    im = im.crop((x0, y0, x0 + w, y0 + h)).convert("RGBA")
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for k in range(h // 3):
        gd.line((0, h - k, w, h - k), fill=(15, 10, 35, int(210 * (1 - k / (h / 3)))))
    im.alpha_composite(g)
    d = ImageDraw.Draw(im)
    d.text((w / 2, h - w * .25), c["name"], font=ImageFont.truetype(F_CAP, int(w * .19)), fill="white", anchor="ms")
    m = Image.new("L", (w * 2, h * 2), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), r * 2, fill=255)
    im.putalpha(m.resize((w, h), Image.LANCZOS))
    out = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    bm = Image.new("L", ((w + 16) * 2, (h + 16) * 2), 0); ImageDraw.Draw(bm).rounded_rectangle((0, 0, (w + 16) * 2 - 1, (h + 16) * 2 - 1), (r + 8) * 2, fill=255)
    border = hgrad(w + 16, h + 16).convert("RGBA"); border.putalpha(bm.resize((w + 16, h + 16), Image.LANCZOS))
    out.alpha_composite(border); out.alpha_composite(im, (8, 8))
    return out


@lru_cache(None)
def bubble_icon(sz): return emoji_img("💬", sz)


@lru_cache(64)
def card(key, w, h, val, hot):
    """val = 聊天数（整数）"""
    out = card_base(key, w, h).copy(); d = ImageDraw.Draw(out)
    fs = int(w * .105); f = ImageFont.truetype(F_CAP, fs); fl = ImageFont.truetype(F_CAP, int(fs * .62))
    num = f"{val:,}"
    ic = bubble_icon(int(fs * 1.05))
    lab = "チャット数"
    tw = ic.width + 8 + max(f.getlength(num), fl.getlength(lab)); pw, ph = int(tw + fs * .9), int(fs * 1.95)
    px, py = (out.width - pw) // 2, int(out.height - 8 - w * .25 + fs * .3)
    pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle((0, 0, pw - 1, ph - 1), ph // 2, fill=(255, 62, 142, 235) if hot else (255, 255, 255, 60),
                                           outline=(255, 255, 255, 200), width=2)
    out.alpha_composite(pill, (px, py))
    x = px + int(fs * .45); out.alpha_composite(ic, (x, py + (ph - ic.height) // 2)); x += ic.width + 8
    d.text((x, py + ph * .30), lab, font=fl, fill=(255, 255, 255, 230), anchor="lm")
    d.text((x, py + ph * .70), num, font=f, fill="white", anchor="lm")
    return drop_shadow(out, (0, 16), 20, 150)


def count_at(key, t, t_in):
    v = COUNT[key] * 10000; u = eo((t - t_in) / 1.1)
    if t <= t_in + 1.1: return int(v * u)
    steps = int((t - t_in - 1.1) / .28)               # 到位后持续往上跳，表现实时热度
    rnd = random.Random(ord(key))
    return int(v) + sum(rnd.randint(40, 380) for _ in range(steps))


def main():
    hero, out = sys.argv[1], sys.argv[2]
    stills = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")] if "--stills" in sys.argv else None
    order = [k for k in "ABCDE" if k != hero]; order.insert(2, hero)
    COUNT[hero] = max(COUNT.values()) + 12.3                          # 主角最热
    BG = background(); LG = logo(); BT = button(); BD = badges()
    HEART = [emoji_img(e, 64) for e in ("💗", "💕", "💖")]
    fan = [(-2, -13), (-1, -6.5), (0, 0), (1, 6.5), (2, 13)]
    size = {True: (480, 720), False: (340, 510)}
    disc = Image.new("RGBA", (1000, 40), (0, 0, 0, 0))
    ImageDraw.Draw(disc).text((500, 20), "※本動画はイメージです。アプリ内キャラクターとは異なる場合があります。", font=ImageFont.truetype(F_CAP, 24), fill=(255, 255, 255, 150), anchor="mm")
    cap1 = cap_img(json.dumps([[["次は", "w"], ["あなた", "g"], ["の番！", "w"]]], ensure_ascii=False), 116)
    cap2 = cap_img(json.dumps([[["あなただけの", "w"], ["推し活", "g"], ["を", "w"]], [["体験しよう！", "w"]]], ensure_ascii=False), 104)
    hr = random.Random(7); hearts = [(hr.uniform(.2, 5.6), hr.uniform(120, 960), hr.choice(range(3)), hr.uniform(.8, 1.3)) for _ in range(16)]
    N = int(round(DUR * FPS)); frames = [int(round(x * FPS)) for x in stills] if stills else range(N)
    proc = None if stills else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                                 "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    TAP, CY = 5.5, 830
    for fi in frames:
        t = fi / FPS; cv = BG.copy()
        # Logo：一开场就在顶部
        place(cv, LG, W / 2, 235 + 4 * math.sin(t * 2.4), pop(t - .02, .35))
        # 飘心（卡片后方）
        for (t0, x, k, sp) in hearts:
            u = (t - t0) / 1.6
            if 0 <= u < 1: place(cv, HEART[k], x + 30 * math.sin(u * 6 + x), 1150 - 650 * u * sp, .7 + .5 * u, 12 * math.sin(u * 5), alpha=1 - u)
        # 角色卡：外→内依次飞入，主角最后落位；之后浮动，主角呼吸
        for i in [0, 4, 1, 3, 2]:
            key = order[i]; off, rot = fan[i]; isH = i == 2
            t_in = .15 + .09 * (2 - abs(off)) + (.12 if isH else 0)
            p = pop(t - t_in, .45)
            if p <= 0: continue
            x = W / 2 + off * 232 + (1 - clamp(p)) * off * 140
            y = CY + abs(off) * 45 + 7 * math.sin(t * 2.6 + i) + (1 - clamp(p)) * 620
            sc = p * ((1 + .025 * math.sin((t - 1) * 4.2)) if isH and t > 1 else 1)
            w, h = size[isH]
            place(cv, card(key, w, h, count_at(key, t, t_in), isH), x, y, sc, -rot - (1 - clamp(p)) * off * 6)
        # 文案
        if t < 2.95: place(cv, cap1, W / 2, 1400, pop(t - .1, .25) * (1 if t < 2.85 else max(0, (2.95 - t) / .1)))
        else: place(cv, cap2, W / 2, 1380, pop(t - 2.95, .25))
        # 按钮 + 商店标
        if t >= 3.5:
            press = max(0, 1 - abs(t - TAP) / .1)
            breathe = 1 + .03 * math.sin((t - 3.5) * 6) * (t > TAP + .35)
            place(cv, BT, W / 2, 1625, pop(t - 3.5, .3) * (1 - .05 * press) * breathe)
            if t >= TAP:
                pr = (t - TAP) / .5
                if pr < 1:
                    o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rr = 60 + 200 * eo(pr)
                    ImageDraw.Draw(o).ellipse((780 - rr, 1625 - rr, 780 + rr, 1625 + rr), outline=(255, 255, 255, int(220 * (1 - pr))), width=int(10 * (1 - pr)) + 1)
                    cv.alpha_composite(o)
            a = clamp((t - (TAP - .4)) / .15) * (1 - clamp((t - (TAP + .3)) / .2)); mv = eo((t - (TAP - .4)) / .3)
            touch(cv, 780 + 80 * (1 - mv), 1625 + 160 * (1 - mv), a, press)
        if t >= 3.8: place(cv, BD, W / 2, 1790, pop(t - 3.8, .3))
        cv.alpha_composite(disc, ((W - 1000) // 2, 1870))
        img = cv.convert("RGB")
        if stills: os.makedirs(out, exist_ok=True); img.save(f"{out}/e{t:04.2f}.jpg", quality=88)
        else: proc.stdin.write(img.tobytes())
    if proc: proc.stdin.close(); proc.wait()
    print("done", DUR, "tap", TAP, {k: round(v, 1) for k, v in COUNT.items()})


if __name__ == "__main__":
    main()
