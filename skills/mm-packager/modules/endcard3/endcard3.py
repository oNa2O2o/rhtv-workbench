"""三卡片尾板（用户指定的默认样式，参考 mm-packager/reference/投放参考/三卡片尾板_参考.webp）：
深藏青背景 + 光斑 → 顶部 Logo（第一帧就在）→ 三张角色卡扇形（中间本片角色金边高亮 + 名字 + チャット数胶囊，两侧往期卡蓝边）
→ 卡底聊天数持续往上跳 → 结尾卡文案（末行金色大字，跟口播逐词出现兼作字幕）→ 金橙渐变下载按钮 → 手指连点 4 下。
plan(E0, vo_t, vo_d) 按片尾口播长度算首次点击和片尾时长；build(ctx) 往 timeline 里加图层和音效，返回实际片尾时长。"""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import mmlib as m

_SCRIPTS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))   # $SK/scripts（mmkit）
if os.path.isdir(_SCRIPTS) and _SCRIPTS not in sys.path: sys.path.insert(0, _SCRIPTS)
try:
    from mmkit import layers as mk
except ImportError:                     # 复制到工程里单独用时没有 mmkit：ctx 里传 add_img/kf/snap/us/pointer_path（旧用法）
    mk = None

W, H = 1080, 1920
NAVY0, NAVY1 = (10, 14, 35), (22, 30, 66)
GOLD_L, GOLD_R = (253, 224, 165), (255, 169, 68)
PILL_GOLD = (249, 188, 113)
CARD_BLUE = (110, 150, 255)
WHITE = (255, 255, 255, 255)
NAVY_TXT = (24, 26, 52, 255)
DUR = 4.9                               # 片尾最短时长（下限，旧用法 END = E0 + DUR 仍可用）；实际时长用 plan() 算


def vgrad(size, stops):
    """竖直多段渐变，stops=[(pos, (r,g,b,a)), ...]"""
    w, h = size
    arr = np.zeros((h, w, 4), np.float32)
    ys = np.linspace(0, 1, h)
    for c in range(4):
        arr[:, :, c] = np.interp(ys, [p for p, _ in stops], [col[c] for _, col in stops])[:, None]
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def hgrad(size, c0, c1):
    w, h = size
    arr = np.zeros((h, w, 4), np.float32)
    xs = np.linspace(0, 1, w)
    for c in range(4):
        arr[:, :, c] = (c0[c] + (c1[c] - c0[c]) * xs)[None, :]
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def rounded_mask(size, r, ss=3):
    w, h = size
    mk = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(mk).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    return mk.resize((w, h), Image.LANCZOS)


def cover(img, w, h, focus_y=0.3):
    s = max(w / img.width, h / img.height)
    im = img.resize((int(img.width * s + 0.5), int(img.height * s + 0.5)), Image.LANCZOS)
    x0 = (im.width - w) // 2
    y0 = int(max(0, min(im.height - h, im.height * focus_y - h * 0.35)))
    return im.crop((x0, y0, x0 + w, y0 + h))


def background():
    bg = vgrad((W, H), [(0, (10, 14, 35, 255)), (0.45, (20, 30, 70, 255)), (0.72, (40, 24, 40, 255)), (1, (70, 34, 22, 255))])
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((-200, 1350, 1280, 2250), fill=(255, 150, 60, 120))
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
    return bg


def bokeh_layer(seed, n, rmin, rmax, alpha):
    rnd = random.Random(seed)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(rmin, rmax)
        col = rnd.choice([(170, 200, 255), (255, 210, 150), (255, 255, 255)])
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (int(alpha * rnd.uniform(0.4, 1)),))
    return lay.filter(ImageFilter.GaussianBlur(rmin * 0.6))


def chat_icon(size, fg, bg=None):
    ss = 3
    im = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size * ss
    if bg: d.ellipse((0, 0, s - 1, s - 1), fill=bg)
    d.rounded_rectangle((s * 0.2, s * 0.24, s * 0.8, s * 0.68), s * 0.14, fill=fg)
    d.polygon([(s * 0.32, s * 0.64), (s * 0.28, s * 0.82), (s * 0.48, s * 0.66)], fill=fg)
    return im.resize((size, size), Image.LANCZOS)


def chat_pill(count, gold, scale=1.0):
    w, h = int(450 * scale), int(106 * scale)
    pill = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    box = (10, 10, 10 + w, 10 + h)
    if gold:
        g = hgrad((w, h), (255, 214, 150, 255), PILL_GOLD + (255,))
        g.putalpha(rounded_mask((w, h), h // 2)); pill.alpha_composite(g, (10, 10))
        m.rrect(pill, box, h // 2, outline=(255, 240, 210, 255), width=3)
        txt, sub, icon = NAVY_TXT, (60, 50, 60, 255), chat_icon(int(64 * scale), (255, 255, 255, 255), (35, 40, 80, 255))
    else:
        m.rrect(pill, box, h // 2, fill=(18, 26, 60, 255), outline=CARD_BLUE + (255,), width=3)
        txt, sub, icon = WHITE, (200, 210, 240, 255), chat_icon(int(64 * scale), (255, 255, 255, 255))
    pill.alpha_composite(icon, (10 + int(24 * scale), 10 + (h - icon.height) // 2))
    fx = 10 + int(104 * scale)
    m.draw_text(pill, (fx, 10 + h * 0.32), "チャット数", m.font("noto_black", int(28 * scale)), sub, anchor="lm")
    m.draw_text(pill, (fx, 10 + h * 0.68), f"{count:,}", m.font("noto_black", int(44 * scale)), txt, anchor="lm")
    return pill


def card_img(photo, w, h, border, name=None, focus_y=0.3, glow=None):
    pad = 60
    card = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if glow:
        g = Image.new("RGBA", card.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).rounded_rectangle((pad - 10, pad - 10, pad + w + 10, pad + h + 10), 44, fill=glow)
        card.alpha_composite(g.filter(ImageFilter.GaussianBlur(26)))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 16, pad + w, pad + h + 16), 36, fill=(0, 0, 0, 150))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    ph = cover(photo, w, h, focus_y)
    shade = vgrad((w, h), [(0, (0, 0, 0, 0)), (0.6, (0, 0, 0, 0)), (1, (8, 10, 30, 210))])
    ph.alpha_composite(shade)
    ph.putalpha(rounded_mask((w, h), 34))
    card.alpha_composite(ph, (pad, pad))
    m.rrect(card, (pad, pad, pad + w, pad + h), 34, outline=border, width=7)
    if name:
        m.draw_text(card, (pad + w / 2, pad + h - 195), name, m.font("noto_black", 60), WHITE, stroke=6, stroke_fill=(10, 12, 30, 255), anchor="mm",
                    shadow=(0, 4, 14, (0, 0, 0, 180)))
    return card, pad


def place_rot(img, cx, cy, angle):
    """把小图旋转后居中贴到整画布 (cx, cy)。"""
    r = img.rotate(angle, resample=Image.BICUBIC, expand=True)
    can = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    can.alpha_composite(r, (int(cx - r.width / 2), int(cy - r.height / 2)))
    return can


def gold_text(text, font, center, stroke=7):
    """金色渐变大字 + 深色描边 + 暖光。"""
    lay = m.canvas()
    m.draw_text(lay, center, text, font, (255, 255, 255, 255), stroke=0, anchor="mm")
    a = lay.getchannel("A")
    bb = a.getbbox()
    g = vgrad((W, H), [(0, (255, 244, 200, 255)), (bb[1] / H, (255, 236, 170, 255)), (bb[3] / H, (243, 150, 52, 255)), (1, (243, 150, 52, 255))])
    out = m.canvas()
    m.draw_text(out, center, text, font, (0, 0, 0, 0), stroke=stroke, stroke_fill=(40, 20, 12, 255), anchor="mm",
                glow=(20, (255, 160, 60, 200)))
    g.putalpha(a); out.alpha_composite(g)
    return out


def plan(E0, vo_t=None, vo_d=None):
    """按片尾口播算点击和时长（成片绝对秒）：首次点击 = max(E0+3.7, 口播结束+0.15)，连点 4 下间隔 0.3 s；
    片尾时长 = max(DUR, 末次点击+0.4−E0, 口播结束+1.0−E0)，向上吸附到 1/30。没给口播就按 E0+3.7 起点。返回 {"dur", "taps"}。"""
    snap = lambda t: round(t * 30) / 30
    vo_end = vo_t + vo_d if vo_t is not None and vo_d is not None else None
    first = E0 + 3.7 if vo_end is None else max(E0 + 3.7, vo_end + 0.15)
    taps = [snap(first + 0.3 * k) for k in range(4)]
    d = max(DUR, taps[-1] + 0.4 - E0, (vo_end + 1.0 - E0) if vo_end is not None else 0)
    return {"dur": math.ceil(d * 30 - 1e-6) / 30, "taps": taps}


def build(ctx):
    """ctx 键：
    E0（片尾起点，成片秒）、VO4_T（片尾口播开始）、VO4_D（片尾口播时长；不给就取 VO4_W 末词结束）、VO4_W（片尾口播逐词时间，可选）、
    button_text、copy、cards（见 README）；
    图层函数二选一：layers = mmkit.layers.Layers 实例（新用法），或 add_img、kf、snap、us、pointer_path（旧用法，工程 gen.py 里的同名函数）。
    返回实际片尾时长（≥ DUR，按片尾口播长度加长），成片总长 = E0 + 返回值。"""
    L = ctx.get("layers")
    if L is None and not all(k in ctx for k in ("add_img", "us", "pointer_path")):
        raise ValueError("endcard3.build：ctx 要给 layers（mmkit.layers.Layers），或给 add_img/kf/snap/us/pointer_path")
    if mk is None and not all(k in ctx for k in ("kf", "snap")):
        raise ImportError("endcard3.build：导入不了 mmkit（$SK/scripts），ctx 里要给 kf、snap")
    add_img = ctx.get("add_img") or L.add_img
    kf = ctx.get("kf") or mk.kf
    snap = ctx.get("snap") or mk.snap
    us = ctx.get("us") or L.us
    pointer_path = ctx.get("pointer_path") or L.pointer_path
    E0 = ctx["E0"]
    # 官方商店标先读，找不到直接报错（不跳过）
    try:
        bdg, _ = m.store_badges(height=86, gap=40)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"endcard3：找不到官方商店标 {e.filename}；设环境变量 MM_BADGE_DIR 指向商店图标目录（现在是 {m.BADGE_DIR}），商店标不能省") from e
    vo_d = ctx.get("VO4_D")
    if vo_d is None and ctx.get("VO4_W"): vo_d = max(w["e"] for w in ctx["VO4_W"])
    p = plan(E0, ctx.get("VO4_T"), vo_d)
    dur, taps = p["dur"], p["taps"]
    END = E0 + dur
    # 背景 + 光斑（两层慢漂，一层闪烁）
    add_img(background(), "ec_bg", E0, END)
    b1 = bokeh_layer(11, 26, 10, 34, 70)
    add_img(b1, "ec_bokeh1", E0, END, kf(y=[(0, 0), (dur, -40, "linear")]))
    b2 = bokeh_layer(23, 40, 3, 8, 160)
    add_img(b2, "ec_bokeh2", E0, END, kf(opacity=[(i * 0.6, 0.45 if i % 2 else 1.0) for i in range(int(dur / 0.6) + 2)], y=[(0, 0), (dur, -20, "linear")]))
    # Logo（第一帧就在）
    lg = m.canvas(); m.paste_logo(lg, 540, 70, height=176, gap=30)
    add_img(lg, "ec_logo", E0, END)
    # 三张卡：两侧往期卡（蓝边、旋转），中间本片角色（金边高亮）
    cards = ctx["cards"]                       # [(photo_path, focusY, name, count, kind)] 左、右、中
    cw, ch = 560, 830
    sw, sh = int(cw * 0.78), int(ch * 0.78)
    pos = {"left": (150, 760, 9), "right": (930, 760, -9), "center": (540, 730, 0)}
    rnd_steps = [2, 1, 3, 2, 1, 2, 3, 1, 2]
    for slot, (ph, fy, name, count, _) in zip(("left", "right", "center"), cards):
        photo = Image.open(ph).convert("RGBA")
        cx, cy, ang = pos[slot]
        center = slot == "center"
        w_, h_ = (cw, ch) if center else (sw, sh)
        card, pad = card_img(photo, w_, h_, (255, 196, 110, 255) if center else CARD_BLUE + (255,), name if center else None, fy,
                             glow=(255, 170, 70, 170) if center else (90, 130, 255, 90))
        base = place_rot(card, cx, cy, ang)
        t_in = 0.0 if not center else 0.15
        dx = (540 - cx) * 0.55
        add_img(base, f"ec_card_{slot}", E0 + t_in, END,
                kf(opacity=[(0, 0), (0.18, 1)], scale=[(0, 0.6), (0.32, 1.06 if center else 1.03), (0.48, 1.0)], x=[(0, dx), (0.32, 0)],
                   rotation=[(0, -ang * 0.8), (0.32, 0)]),
                {"anchorX": cx / W, "anchorY": cy / H})
        # 聊天数胶囊：卡底居中，持续往上跳（中间 0.1 s 一跳，两侧 0.2 s）
        step = 0.1 if center else 0.2
        t, k, c = E0 + t_in + 0.2, 0, count
        sc = 1.0 if center else 0.78
        py = cy + h_ / 2 - 70 * sc               # 胶囊在卡片底部里面（照参考图）
        first = True
        while t < END - 1e-3:
            pill = chat_pill(c, center, sc)
            lay = place_rot(pill, cx + (0 if center else (h_ / 2 - 20) * math.sin(math.radians(-ang)) * 0), py, ang)
            if not center:   # 旋转后胶囊跟着卡底走
                rx, ry = 0, h_ / 2 - 70 * sc
                a = math.radians(-ang)
                lay = place_rot(pill, cx + rx * math.cos(a) - ry * math.sin(a), cy + rx * math.sin(a) + ry * math.cos(a), ang)
            add_img(lay, f"ec_pill_{slot}", t, min(END, t + step), kf(opacity=[(0, 0), (0.15, 1)], scale=[(0, 0.7), (0.15, 1.0)]) if first else None,
                    {"anchorX": cx / W, "anchorY": py / H} if first else None)
            c += rnd_steps[k % len(rnd_steps)] * (37 if center else 13); k += 1; t += step; first = False
    # 中间卡金边呼吸高亮
    hl = m.canvas()
    ImageDraw.Draw(hl).rounded_rectangle((540 - cw / 2 - 6, 730 - ch / 2 - 6, 540 + cw / 2 + 6, 730 + ch / 2 + 6), 40, outline=(255, 214, 140, 255), width=8)
    hl = hl.filter(ImageFilter.GaussianBlur(6))
    add_img(hl, "ec_highlight", E0 + 0.6, END, kf(opacity=[(i * 0.5, 0.25 if i % 2 else 0.9) for i in range(int(dur / 0.5) + 1)]))
    # 片尾文案 = 片尾口播（兼作字幕），逐词出现；金色行用渐变大字弹入
    t4 = ctx["VO4_T"]
    for ln in ctx["copy"]:                      # {"y", "size", "gold", "tokens": [(text, t_rel)]}
        f = m.font("noto_black", ln["size"])
        toks = ln["tokens"]
        tw = sum(f.getlength(t) for t, _ in toks)
        assert 540 - tw / 2 >= 60, "片尾文案出界"
        if ln["gold"]:                          # 金色行按 半宽 + 描边 7 + 光晕 20、再乘弹入最大缩放 1.1 算出界
            assert 540 - (tw / 2 + 7 + 20) * 1.1 >= 0, "片尾金色文案出界（按描边、光晕和弹入 1.1 倍算）"
            txt = "".join(t for t, _ in toks)
            big = gold_text(txt, f, (540, ln["y"]))
            add_img(big, "ec_copy_gold", t4 + toks[0][1], END, kf(scale=[(0, 0.6), (0.12, 1.1), (0.24, 1.0)], opacity=[(0, 0), (0.06, 1)]),
                    {"anchorX": 0.5, "anchorY": ln["y"] / H})
            continue
        times = [tt for _, tt in toks]
        for i, tr in enumerate(times):
            img = m.canvas(); x = 540 - tw / 2
            for t, tt in toks:
                if tt <= tr + 1e-6:
                    m.draw_text(img, (x, ln["y"]), t, f, WHITE, stroke=7, stroke_fill=(12, 14, 34, 255), anchor="lm", shadow=(0, 4, 16, (0, 0, 0, 170)))
                x += f.getlength(t)
            end_ = t4 + times[i + 1] if i + 1 < len(times) else END
            add_img(img, "ec_copy", t4 + tr, end_)
    # 下载按钮（金橙渐变胶囊，深色字），文字照全量文案
    bw_, bh_ = 880, 160
    btn = m.canvas()
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    BX, BY = 100, 1500
    ImageDraw.Draw(gl).rounded_rectangle((BX, BY, BX + bw_, BY + bh_), bh_ // 2, fill=(255, 150, 50, 150))
    btn.alpha_composite(gl.filter(ImageFilter.GaussianBlur(28)))
    g = hgrad((bw_, bh_), GOLD_L + (255,), GOLD_R + (255,)); g.putalpha(rounded_mask((bw_, bh_), bh_ // 2))
    btn.alpha_composite(g, (BX, BY))
    BCY = BY + bh_ / 2
    m.draw_text(btn, (540, BCY), ctx["button_text"], m.font("noto_black", 66), NAVY_TXT, anchor="mm")
    bsc = [(0, 0.6), (0.12, 1.08), (0.22, 1.0)]
    t_btn = E0 + 0.5                            # 卡片 0 → 按钮 0.5 → 文案和口播 1.0 → 商店标 1.5（约每 0.5 s 一个）
    for tp in taps:
        r0 = tp - t_btn; bsc += [(r0 - 0.03, 1.0), (r0 + 0.05, 0.93), (r0 + 0.16, 1.0)]
    for k in range(3):
        a0 = 1.0 + 0.6 * k; bsc += [(a0, 1.0), (a0 + 0.3, 1.035), (a0 + 0.6, 1.0)]
    bsc = sorted({round(t, 3): v for t, v in bsc if t <= END - t_btn}.items())
    add_img(btn, "ec_button", t_btn, END, kf(scale=bsc, opacity=[(0, 0), (0.08, 1)]), {"anchorX": 0.5, "anchorY": BCY / H})
    # 两个一样大的商店下载标（rules/通用.md：按钮下方；图在开头已读好）
    bimg = m.canvas(); bimg.alpha_composite(bdg, (int(540 - bdg.width / 2), BY + bh_ + 40))
    t_bdg = E0 + 1.5
    add_img(bimg, "ec_badges", t_bdg, END, kf(scale=[(0, 0.7), (0.12, 1.06), (0.22, 1.0)], opacity=[(0, 0), (0.08, 1)]),
            {"anchorX": 0.5, "anchorY": (BY + bh_ + 83) / H})
    # 按钮扫光
    bm = Image.new("L", (W, H), 0); bm.paste(rounded_mask((bw_, bh_), bh_ // 2), (BX, BY))
    for k in range(3):
        t0 = E0 + 0.9 + 1.2 * k
        for i in range(10):
            band = Image.new("L", (W, H), 0); xx0 = 60 + i * 100
            ImageDraw.Draw(band).polygon([(xx0, BY), (xx0 + 80, BY), (xx0 + 20, BY + bh_), (xx0 - 60, BY + bh_)], fill=170)
            from PIL import ImageChops
            band = ImageChops.multiply(band.filter(ImageFilter.GaussianBlur(10)), bm)
            s = Image.new("RGBA", (W, H), (255, 255, 255, 0)); s.putalpha(band)
            if t0 + (i + 1) / 30 < END: add_img(s, "ec_shine", t0 + i / 30, t0 + (i + 1) / 30)
    # 手指连点 4 下（口播说完后，时间见 plan()）
    t_p = taps[0] - 0.25
    pointer_path([(t_p, 820, 1760), (taps[0] - 0.05, 600, BCY + 8)] + [(tp, 600, BCY + 8) for tp in taps] + [(END, 600, BCY + 8)], t_p, END, clicks=taps)
    # 声音
    us("进选项、闪白、照相音效.MP3", E0, 0.45)
    us("回声弹出音效.MP3", E0 + 0.05, 0.35)
    us("气泡提示音.MP3", t_btn, 0.3)
    us("气泡提示音.MP3", t_bdg, 0.2)
    for tp in taps: us("咔嗒清脆点击.MP3", tp, 0.6)
    return dur
