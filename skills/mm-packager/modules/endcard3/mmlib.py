"""本片图层绘制工具：1080×1920 透明整画布 PNG，元素画在最终位置（规则见 mm-packager rules/工程交付.md「图层」）。"""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1920
RES = os.environ.get("MM_RES", "Z:/创新事业部/AIGC项目视频组/mm-packager资源")
FONT_DIR = RES + "/fonts"
FONTS = {
    "mincho": FONT_DIR + "/01_诱惑台词主力_特粗标题_ShipporiMinchoB1-ExtraBold.ttf",
    "noto_black": FONT_DIR + "/NotoSansJP-Black.otf",
    "noto_bold": FONT_DIR + "/NotoSansJP-Bold.otf",
    "maru": FONT_DIR + "/ZenMaruGothic-Black.ttf",
    "mochiy": FONT_DIR + "/MochiyPopOne-Regular.ttf",
    "klee": FONT_DIR + "/03_手写私信心声_加粗_KleeOne-SemiBold.ttf",
    "oldmincho_black": FONT_DIR + "/ZenOldMincho-Black.ttf",
    "oldmincho_bold": FONT_DIR + "/ZenOldMincho-Bold.ttf",
}
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace("\\", "/")
OFFICIAL = SKILL_DIR + "/assets/官方素材"   # 官方 Logo、商店标原图 skill 内置，不去 Z: 找（用户：「官方图片这种通用素材给我内置到放到skill里」）
LOGO_ICON = OFFICIAL + "/logo_icon.png"
LOGO_WORD = OFFICIAL + "/logo_word.png"
BADGES = OFFICIAL + "/badges.png"          # 两个官方标同尺寸的合图（由 store_badges() 生成）

_fc = {}


def font(name, size):
    k = (name, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONTS.get(name, name), size)
    return _fc[k]


def check_glyphs(name, text):
    """fontTools 检查字体覆盖全部用字（规则：缺字会显示成方块）。返回缺的字。"""
    from fontTools.ttLib import TTFont
    cmap = TTFont(FONTS.get(name, name), fontNumber=0).getBestCmap()
    return sorted({ch for ch in text if not ch.isspace() and ord(ch) not in cmap})


def canvas():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def text_size(txt, f, spacing=0):
    b = f.getbbox(txt)
    return b[2] - b[0] + spacing * max(0, len(txt) - 1), b[3] - b[1]


def draw_text(img, xy, txt, f, fill, stroke=0, stroke_fill=None, anchor="mm", shadow=None, glow=None, spacing=0):
    """在 img 上画文字。shadow=(dx,dy,blur,color)；glow=(radius,color)。"""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if spacing:
        # 逐字排（字距）：先算总宽
        tw = sum(f.getlength(c) for c in txt) + spacing * (len(txt) - 1)
        x, y = xy
        if anchor[0] == "m": x -= tw / 2
        elif anchor[0] == "r": x -= tw
        for c in txt:
            d.text((x, y), c, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill, anchor="l" + anchor[1])
            x += f.getlength(c) + spacing
    else:
        d.text(xy, txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill, anchor=anchor)
    if glow:
        r, col = glow
        a = lay.getchannel("A").filter(ImageFilter.GaussianBlur(r))
        g = Image.new("RGBA", img.size, col[:3] + (0,)); g.putalpha(a.point(lambda v: min(255, int(v * (col[3] / 255) * 1.6))))
        img.alpha_composite(g)
    if shadow:
        dx, dy, blur, col = shadow
        a = lay.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
        s = Image.new("RGBA", img.size, col[:3] + (0,)); s.putalpha(a.point(lambda v: int(v * col[3] / 255)))
        img.alpha_composite(s, (dx, dy))
    img.alpha_composite(lay)
    return img


def rrect(img, box, r, fill=None, outline=None, width=0, ss=3):
    """抗锯齿圆角矩形（超采样后缩小，避免锯齿）。"""
    x0, y0, x1, y1 = box
    w, h = int(x1 - x0), int(y1 - y0)
    pad = width + 2
    big = Image.new("RGBA", ((w + 2 * pad) * ss, (h + 2 * pad) * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.rounded_rectangle((pad * ss, pad * ss, (pad + w) * ss - 1, (pad + h) * ss - 1), r * ss, fill=fill, outline=outline, width=width * ss)
    sm = big.resize((w + 2 * pad, h + 2 * pad), Image.LANCZOS)
    img.alpha_composite(sm, (int(x0) - pad, int(y0) - pad))
    return img


def soft_shadow(img, box, r, blur=24, color=(0, 0, 0, 120), dy=10):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((box[0], box[1] + dy, box[2], box[3] + dy), r, fill=color)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)))
    return img


def gradient_rect(size, c0, c1, horizontal=True):
    w, h = size
    g = Image.new("RGBA", (w, h))
    px = g.load()
    for i in range(w if horizontal else h):
        u = i / max(1, (w if horizontal else h) - 1)
        c = tuple(int(c0[k] + (c1[k] - c0[k]) * u) for k in range(4))
        if horizontal:
            for j in range(h): px[i, j] = c
        else:
            for j in range(w): px[j, i] = c
    return g


def paste_logo(img, cx, y, height=86, word=True, gap=18):
    """开头/片尾 Logo：图标 + 字标图（规则：品牌名一律用 Logo 字标图）。返回占用的 bbox。"""
    icon = Image.open(LOGO_ICON).convert("RGBA")
    icon = icon.resize((int(icon.width * height / icon.height), height), Image.LANCZOS)
    parts = [icon]
    if word:
        wd = Image.open(LOGO_WORD).convert("RGBA")
        wh = int(height * 0.62)
        wd = wd.resize((int(wd.width * wh / wd.height), wh), Image.LANCZOS)
        parts.append(wd)
    tw = sum(p.width for p in parts) + gap * (len(parts) - 1)
    x = int(cx - tw / 2)
    for p in parts:
        img.alpha_composite(p, (x, int(y + (height - p.height) / 2)))
        x += p.width + gap
    return (int(cx - tw / 2), y, int(cx + tw / 2), y + height)


def ring(img, cx, cy, r, width, color, ss=3):
    big = Image.new("RGBA", (int(2 * r + 2 * width + 4) * ss,) * 2, (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    o = (width + 2) * ss
    d.ellipse((o, o, o + 2 * r * ss, o + 2 * r * ss), outline=color, width=width * ss)
    sm = big.resize((big.width // ss, big.height // ss), Image.LANCZOS)
    img.alpha_composite(sm, (int(cx - r - width - 2), int(cy - r - width - 2)))
    return img


def disc(img, cx, cy, r, color, ss=3):
    big = Image.new("RGBA", (int(2 * r + 4) * ss,) * 2, (0, 0, 0, 0))
    ImageDraw.Draw(big).ellipse((2 * ss, 2 * ss, (2 + 2 * r) * ss, (2 + 2 * r) * ss), fill=color)
    sm = big.resize((big.width // ss, big.height // ss), Image.LANCZOS)
    img.alpha_composite(sm, (int(cx - r - 2), int(cy - r - 2)))
    return img


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path): os.remove(path)       # 规则：重出图层先清旧图
    img.save(path)
    return path


BADGE_DIR = os.environ.get("MM_BADGE_DIR", OFFICIAL)   # 官方原版商店标（用户指定）；环境变量 MM_BADGE_DIR 可覆盖，见 reference/环境.md


def store_badges(height=86, gap=40):
    """官方原版日文商店标：Google Play「で手に入れよう」+ App Store「からダウンロード」，两个外框完全一样大。
    两个都按同一高度等比缩放、内容不改；App Store 原版比 Google Play 窄，它的黑底圆角外框按 Google Play 宽度补齐
    （边框颜色、粗细比例、圆角照它自己的原版取样），原版内容居中放进去。返回 (图, 各自 bbox)。"""
    gp = Image.open(BADGE_DIR + "/Google_Play_Badge_JA.svg.png").convert("RGBA"); gp = gp.crop(gp.getchannel("A").getbbox())
    ios = Image.open(BADGE_DIR + "/ios_badge.png").convert("RGBA"); ios = ios.crop(ios.getchannel("A").getbbox())
    gw = round(gp.width * height / gp.height)
    gp_s = gp.resize((gw, height), Image.LANCZOS)
    k = height / ios.height
    inset, inset_x = 5, 30                                       # 上下裁掉原版 3 px 灰边；左右避开原版圆角
    inner = ios.crop((inset_x, inset, ios.width - inset_x, ios.height - inset))
    inner = inner.resize((round(inner.width * k), round(inner.height * k)), Image.LANCZOS)
    ss = 4
    fr = Image.new("RGBA", (gw * ss, height * ss), (0, 0, 0, 0))
    bwid = max(1, round(3 * k * ss))
    ImageDraw.Draw(fr).rounded_rectangle((0, 0, gw * ss - 1, height * ss - 1), round(27 / 167 * height * ss), fill=(4, 4, 3, 255),
                                         outline=(178, 177, 177, 255), width=bwid)
    fr = fr.resize((gw, height), Image.LANCZOS)
    fr.alpha_composite(inner, ((gw - inner.width) // 2, (height - inner.height) // 2))
    out = Image.new("RGBA", (gw * 2 + gap, height), (0, 0, 0, 0))
    out.alpha_composite(gp_s, (0, 0)); out.alpha_composite(fr, (gw + gap, 0))
    boxes = [(0, 0, gw, height), (gw + gap, 0, gw * 2 + gap, height)]
    return out, boxes
