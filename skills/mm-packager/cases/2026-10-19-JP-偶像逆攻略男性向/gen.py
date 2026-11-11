import os, json, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance, ImageChops

W, H = 1080, 1920
OUT = 'F:/钟海明/2026/2026年10月19日MM-JP-偶像妄想迭代/包装素材v2'
os.makedirs(OUT, exist_ok=True)
T = 'F:/钟海明/2026/2026年10月19日MM-JP-偶像妄想迭代/包装素材v2/脚本'
POP = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Fonts\MochiyPopOne-Regular.ttf')
KLEE = 'C:/Windows/Fonts/03_手写私信心声_加粗_KleeOne-SemiBold.ttf'
ASSET = 'F:/钟海明/MM透明尾板/片尾/片尾文件夹/(素材)/图片/'
APPA = 'F:/钟海明/2026/2026年10月10日MM-编辑器重构/app/public/assets/'
PINK = (255, 79, 154); DEEP = (120, 20, 80)

def canvas(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))
def font(p, s): return ImageFont.truetype(p, s)
def save(im, name): im.save(f'{OUT}/{name}.png'); print('saved', name)

def tsize(txt, f):
    b = f.getbbox(txt); return b[2] - b[0], b
def glow(layer, r, color, strength=1.0):
    a = layer.split()[3].filter(ImageFilter.GaussianBlur(r))
    if strength != 1: a = a.point(lambda v: min(255, int(v * strength)))
    g = Image.new('RGBA', layer.size, color + (0,)); g.putalpha(a); return g

def text_layer(txt, f, cx, y, fill=(255, 255, 255), stroke=0, stroke_fill=None, gradient=None, anchor='mt'):
    """draw centered text; gradient=(top,bottom) colors replaces fill"""
    L = canvas(); d = ImageDraw.Draw(L)
    if stroke: d.text((cx, y), txt, font=f, fill=stroke_fill + (255,), anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill + (255,))
    M = canvas(); dm = ImageDraw.Draw(M); dm.text((cx, y), txt, font=f, fill=(255, 255, 255, 255), anchor=anchor)
    if gradient:
        bb = M.getbbox(); g = Image.new('RGBA', (W, H)); gd = ImageDraw.Draw(g)
        for yy in range(bb[1], bb[3] + 1):
            k = (yy - bb[1]) / max(1, bb[3] - bb[1]); c = tuple(int(gradient[0][i] * (1 - k) + gradient[1][i] * k) for i in range(3))
            gd.line([(0, yy), (W, yy)], fill=c + (255,))
        g.putalpha(M.split()[3]); L.alpha_composite(g)
    else:
        f2 = Image.new('RGBA', (W, H), fill + (0,)); f2.putalpha(M.split()[3]); L.alpha_composite(f2)
    return L

def stack(*layers):
    c = canvas()
    for l in layers: c.alpha_composite(l)
    return c

# ---------------- TITLE ----------------
def title():
    icon = Image.open(ASSET + 'LOGO-256x256-圆角.png').convert('RGBA').resize((64, 64), Image.LANCZOS)
    f_tag = font(POP, 38); tw, _ = tsize('MiraiMindで', f_tag)
    cw = 64 + 16 + tw + 56; ch = 84; x0 = (W - cw) // 2; y0 = 1150
    cap = canvas(); d = ImageDraw.Draw(cap)
    d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], radius=42, fill=(255, 255, 255, 240))
    cap.alpha_composite(icon, (x0 + 18, y0 + 10))
    d.text((x0 + 18 + 64 + 14, y0 + ch // 2), 'MiraiMindで', font=f_tag, fill=PINK + (255,), anchor='lm')
    sh = glow(cap, 14, (60, 0, 40), 0.6)
    l1 = text_layer('アンチのフリがバレた！', font(POP, 78), W // 2, 1280, stroke=12, stroke_fill=DEEP)
    l2 = text_layer('推しアイドルに', font(POP, 70), W // 2, 1390, stroke=12, stroke_fill=DEEP)
    l3 = text_layer('逆攻略される！？', font(POP, 124), W // 2, 1490, stroke=16, stroke_fill=(255, 255, 255), gradient=((255, 120, 190), (230, 40, 120)))
    l3o = text_layer('逆攻略される！？', font(POP, 124), W // 2, 1490, stroke=26, stroke_fill=DEEP)
    body = stack(l1, l2, l3o, l3)
    save(stack(glow(body, 22, (255, 60, 150), 0.9), glow(body, 6, (40, 0, 30), 1.2), sh, cap, body), 'title_b')

# ---------------- METER ----------------
NODES = [180, 420, 660, 900]; NY = 196; R = 60
FACES = [('fr_11.0.png', 245, 235, 250), ('fr_20.4.png', 240, 250, 230), ('fr_43.0.png', 240, 360, 400)]
LABELS = ['1日目', '2日目', '3日目', '制限モード']
def face(i, gray=False):
    f, cx, cy, s = FACES[i]
    im = Image.open(f'{T}/{f}').convert('RGB').crop((cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2)).resize((R * 2, R * 2), Image.LANCZOS)
    if gray: im = ImageEnhance.Brightness(ImageOps.grayscale(im).convert('RGB')).enhance(0.7)
    m = Image.new('L', (R * 2, R * 2), 0); ImageDraw.Draw(m).ellipse([0, 0, R * 2 - 1, R * 2 - 1], fill=255)
    o = im.convert('RGBA'); o.putalpha(m); return o
def lock_icon(cx, cy, s, L):
    d = ImageDraw.Draw(L)
    d.arc([cx - s * .42, cy - s * 1.0, cx + s * .42, cy - s * .05], 180, 360, fill=(255, 255, 255, 255), width=int(s * .16))
    d.line([(cx - s * .42 + s * .08, cy - s * .52), (cx - s * .42 + s * .08, cy - s * .1)], fill=(255, 255, 255, 255), width=int(s * .16))
    d.line([(cx + s * .42 - s * .08, cy - s * .52), (cx + s * .42 - s * .08, cy - s * .1)], fill=(255, 255, 255, 255), width=int(s * .16))
    d.rounded_rectangle([cx - s * .62, cy - s * .2, cx + s * .62, cy + s * .72], radius=int(s * .16), fill=(255, 255, 255, 255))
    d.ellipse([cx - s * .12, cy + s * .1, cx + s * .12, cy + s * .34], fill=(120, 40, 140, 255))
    d.rectangle([cx - s * .05, cy + s * .25, cx + s * .05, cy + s * .5], fill=(120, 40, 140, 255))
def meter():
    base = canvas(); d = ImageDraw.Draw(base)
    d.line([(NODES[0], NY), (NODES[2], NY)], fill=(255, 255, 255, 150), width=6)
    x = NODES[2] + R
    while x < NODES[3] - R:
        d.line([(x, NY), (min(x + 14, NODES[3] - R), NY)], fill=(200, 160, 255, 170), width=6); x += 26
    for i, x in enumerate(NODES[:3]):
        d.ellipse([x - R - 5, NY - R - 5, x + R + 5, NY + R + 5], fill=(255, 255, 255, 140))
        base.alpha_composite(face(i, True), (x - R, NY - R))
    labs = canvas()
    for i, x in enumerate(NODES[:3]):
        labs.alpha_composite(text_layer(LABELS[i], font(POP, 34), x, NY + R + 18, fill=(235, 235, 235), stroke=6, stroke_fill=(40, 30, 40)))
    full = stack(base, labs)
    save(stack(glow(full, 10, (0, 0, 0), 0.7), full), 'mt2_base')
    fill = canvas(); fd = ImageDraw.Draw(fill)
    fd.line([(NODES[0], NY), (NODES[2], NY)], fill=(255, 90, 165, 255), width=10)
    save(stack(glow(fill, 10, (255, 60, 150), 1.4), fill), 'mt2_fill')
    for i, x in enumerate(NODES[:3]):
        on = canvas()
        ring = canvas(); rd = ImageDraw.Draw(ring)
        rd.ellipse([x - R - 9, NY - R - 9, x + R + 9, NY + R + 9], fill=(255, 255, 255, 255))
        rd.ellipse([x - R - 5, NY - R - 5, x + R + 5, NY + R + 5], fill=(255, 80, 160, 255))
        on.alpha_composite(glow(ring, 18, (255, 60, 150), 1.6)); on.alpha_composite(ring)
        on.alpha_composite(face(i), (x - R, NY - R))
        hb = heart(42, (255, 70, 150)); on.alpha_composite(hb, (x + R - 32, NY + R - 44))
        lab = text_layer(LABELS[i], font(POP, 38), x, NY + R + 16, fill=(255, 255, 255), stroke=7, stroke_fill=(230, 40, 120))
        on.alpha_composite(glow(lab, 10, (255, 60, 150), 1.0)); on.alpha_composite(lab)
        save(on, f'mt2_on{i + 1}')
    # locked 4th node
    x = NODES[3]; Lk = canvas()
    src = Image.open(f'{T}/fr_end.png').convert('RGB'); sw = 300
    im = src.crop((240 - sw // 2, 330 - sw // 2, 240 + sw // 2, 330 + sw // 2)).resize((R * 2, R * 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(7))
    im = ImageEnhance.Brightness(im).enhance(0.45)
    tint = Image.new('RGB', im.size, (90, 30, 140)); im = Image.blend(im, tint, 0.45)
    m = Image.new('L', (R * 2, R * 2), 0); ImageDraw.Draw(m).ellipse([0, 0, R * 2 - 1, R * 2 - 1], fill=255)
    ring = canvas(); rd = ImageDraw.Draw(ring)
    rd.ellipse([x - R - 8, NY - R - 8, x + R + 8, NY + R + 8], fill=(190, 140, 255, 255))
    Lk.alpha_composite(glow(ring, 16, (150, 70, 255), 1.4)); Lk.alpha_composite(ring)
    o = im.convert('RGBA'); o.putalpha(m); Lk.alpha_composite(o, (x - R, NY - R))
    ic = canvas(); lock_icon(x, NY - 4, 58, ic)
    Lk.alpha_composite(glow(ic, 8, (60, 0, 90), 1.6)); Lk.alpha_composite(ic)
    # chains crossing
    ch = canvas(); cd = ImageDraw.Draw(ch)
    for k in range(-4, 5):
        for sgn in (1, -1):
            cx = x + k * 26; cy = NY + sgn * k * 26 * 0.55
            cd.ellipse([cx - 13, cy - 8, cx + 13, cy + 8], outline=(225, 215, 240, 235), width=5)
    mm = Image.new('L', (W, H), 0); ImageDraw.Draw(mm).ellipse([x - R - 14, NY - R - 14, x + R + 14, NY + R + 14], fill=255)
    ch.putalpha(ImageChops.multiply(ch.split()[3], mm))
    Lk.alpha_composite(glow(ic, 8, (60, 0, 90), 1.6)); Lk.alpha_composite(ic)
    lab = text_layer(LABELS[3], font(POP, 32), x, NY + R + 20, fill=(235, 220, 255), stroke=6, stroke_fill=(70, 20, 110))
    Lk.alpha_composite(glow(lab, 10, (150, 70, 255), 1.0)); Lk.alpha_composite(lab)
    save(Lk, 'mt2_lock')

def unlock():
    x = NODES[3]; U = canvas()
    src = Image.open(f'{T}/fr_end.png').convert('RGB'); sw = 300
    im = src.crop((240 - sw // 2, 330 - sw // 2, 240 + sw // 2, 330 + sw // 2)).resize((R * 2, R * 2), Image.LANCZOS)
    m = Image.new('L', (R * 2, R * 2), 0); ImageDraw.Draw(m).ellipse([0, 0, R * 2 - 1, R * 2 - 1], fill=255)
    ring = canvas(); rd = ImageDraw.Draw(ring)
    rd.ellipse([x - R - 9, NY - R - 9, x + R + 9, NY + R + 9], fill=(255, 255, 255, 255))
    rd.ellipse([x - R - 5, NY - R - 5, x + R + 5, NY + R + 5], fill=(255, 80, 160, 255))
    U.alpha_composite(glow(ring, 20, (255, 60, 150), 1.8)); U.alpha_composite(ring)
    o = im.convert('RGBA'); o.putalpha(m); U.alpha_composite(o, (x - R, NY - R))
    U.alpha_composite(heart(42, (255, 70, 150)), (x + R - 32, NY + R - 44))
    lab = text_layer('制限解除', font(POP, 34), x, NY + R + 18, fill=(255, 255, 255), stroke=7, stroke_fill=(230, 40, 120))
    U.alpha_composite(glow(lab, 10, (255, 60, 150), 1.0)); U.alpha_composite(lab)
    save(U, 'mt2_unlock')
    f2 = canvas(); fd = ImageDraw.Draw(f2)
    fd.line([(NODES[2] + R, NY), (NODES[3] - R, NY)], fill=(255, 90, 165, 255), width=10)
    save(stack(glow(f2, 10, (255, 60, 150), 1.4), f2), 'mt2_fill2')

def lock_icon_open(cx, cy, s, L):
    d = ImageDraw.Draw(L); w = int(s * .16); up = s * .34
    d.arc([cx - s * .42, cy - s * 1.0 - up, cx + s * .42, cy - s * .05 - up], 180, 360, fill=(255, 255, 255, 255), width=w)
    d.line([(cx - s * .34, cy - s * .52 - up), (cx - s * .34, cy - s * .1)], fill=(255, 255, 255, 255), width=w)
    d.line([(cx + s * .34, cy - s * .52 - up), (cx + s * .34, cy - s * .3 - up)], fill=(255, 255, 255, 255), width=w)
    d.rounded_rectangle([cx - s * .62, cy - s * .2, cx + s * .62, cy + s * .72], radius=int(s * .16), fill=(255, 255, 255, 255))
    d.ellipse([cx - s * .12, cy + s * .1, cx + s * .12, cy + s * .34], fill=(120, 40, 140, 255))
    d.rectangle([cx - s * .05, cy + s * .25, cx + s * .05, cy + s * .5], fill=(120, 40, 140, 255))

def unlockfx():
    # open-lock version of node 4 (same geometry as mt2_lock)
    x = NODES[3]; Lk = canvas()
    src = Image.open(f'{T}/fr_end.png').convert('RGB'); sw = 300
    im = src.crop((240 - sw // 2, 330 - sw // 2, 240 + sw // 2, 330 + sw // 2)).resize((R * 2, R * 2), Image.LANCZOS).filter(ImageFilter.GaussianBlur(5))
    im = ImageEnhance.Brightness(im).enhance(0.6); im = Image.blend(im, Image.new('RGB', im.size, (120, 40, 160)), 0.35)
    m = Image.new('L', (R * 2, R * 2), 0); ImageDraw.Draw(m).ellipse([0, 0, R * 2 - 1, R * 2 - 1], fill=255)
    ring = canvas(); rd = ImageDraw.Draw(ring)
    rd.ellipse([x - R - 8, NY - R - 8, x + R + 8, NY + R + 8], fill=(255, 200, 250, 255))
    Lk.alpha_composite(glow(ring, 22, (255, 120, 230), 2.0)); Lk.alpha_composite(ring)
    o = im.convert('RGBA'); o.putalpha(m); Lk.alpha_composite(o, (x - R, NY - R))
    ic = canvas(); lock_icon_open(x, NY - 4, 58, ic)
    Lk.alpha_composite(glow(ic, 10, (255, 120, 230), 1.8)); Lk.alpha_composite(ic)
    lab = text_layer(LABELS[3], font(POP, 32), x, NY + R + 20, fill=(235, 220, 255), stroke=6, stroke_fill=(70, 20, 110))
    Lk.alpha_composite(glow(lab, 10, (150, 70, 255), 1.0)); Lk.alpha_composite(lab)
    save(Lk, 'mt2_lock_open')
    # burst flash at node centre (scaled with node later): rays + radial glow
    import numpy as np
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); dx = xx - W / 2; dy = yy - H / 2
    r = np.sqrt(dx * dx + dy * dy) + 1e-3; ang = np.arctan2(dy, dx)
    core = np.exp(-(r / 70) ** 2) * 255
    halo = np.exp(-(r / 220) ** 1.4) * 200 * np.clip(1 - r / 530, 0, 1)
    rays = (np.cos(ang * 12) ** 24) * np.exp(-r / 300) * 230 * np.clip(1 - r / 520, 0, 1)
    a = np.clip(np.maximum.reduce([core, halo, rays]), 0, 255).astype(np.uint8)
    F_ = Image.new('RGBA', (W, H), (255, 225, 245, 0)); F_.putalpha(Image.fromarray(a)); save(F_, 'ul_burst2')
    dim = Image.new('RGBA', (W, H), (16, 4, 24, 170)); save(dim, 'ul_dim')
    wf = Image.new('RGBA', (W, H), (255, 240, 250, 255)); save(wf, 'ul_white')

def heart(s, color, outline=True):
    im = Image.new('RGBA', (s * 4, s * 4), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = []
    for k in range(200):
        t = k / 200 * 2 * math.pi
        x = 16 * math.sin(t) ** 3; y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((s * 2 + x * s / 9, s * 2 + y * s / 9 - s * 0.1))
    if outline: d.polygon(pts, fill=(255, 255, 255, 255)); pts2 = [(s * 2 + (px - s * 2) * 0.78, s * 2 + (py - s * 2) * 0.78) for px, py in pts]; d.polygon(pts2, fill=color + (255,))
    else: d.polygon(pts, fill=color + (255,))
    return im.resize((s, s), Image.LANCZOS)

# ---------------- MONOLOGUE ----------------
MONO = [
    [['これって……', '現実か？'], ['それとも、', 'ただの妄想……？']],
    [['でも……', 'もし本当に'], ['付き合えたりしたら、', 'なんてな…']],
    [['大嫌いなはずなのに', '……']],
    [['なんで近づかれるだけで、'], ['こんなに息が'], ['苦しくなるんだよ…']],
    [['やばい……'], ['心臓がバクバクして'], ['止まらねぇ…']],
    [['ちょ、', 'ちょっと待て……'], ['さすがに反則だろ！']],
]
def mono():
    f = font(KLEE, 64); LH = 104; CY = 1360
    meta = []
    for li, lines in enumerate(MONO):
        n = len(lines); top = CY - (n * LH) // 2
        chunks = []; widths = []
        for row, parts in enumerate(lines):
            full = ''.join(parts); tw, _ = tsize(full, f); widths.append(tw)
            x = (W - tw) // 2; y = top + row * LH
            for p in parts:
                L = canvas(); d = ImageDraw.Draw(L)
                d.text((x, y), p, font=f, fill=(255, 255, 255, 255), anchor='lt')
                shadow = glow(L, 12, (40, 10, 50), 1.6); shine = glow(L, 4, (255, 170, 215), 1.2)
                chunks.append(stack(shadow, shine, L))
                x += f.getlength(p)
        # brackets
        bw = max(widths); bf = font(KLEE, 150)
        B = canvas(); bd = ImageDraw.Draw(B)
        bh = n * LH; ymid = top + bh // 2 - 6
        bd.text(((W - bw) // 2 - 30, ymid), '（', font=bf, fill=(255, 150, 200, 200), anchor='rm')
        bd.text(((W + bw) // 2 + 30, ymid), '）', font=bf, fill=(255, 150, 200, 200), anchor='lm')
        save(stack(glow(B, 14, (255, 60, 150), 1.0), B), f'mv2_{li + 1}_br')
        for ci, c in enumerate(chunks): save(c, f'mv2_{li + 1}_{ci + 1}')
        meta.append(len(chunks))
    # vignette
    V = Image.new('L', (W, H), 0); vd = ImageDraw.Draw(V)
    v = Image.new('L', (W // 4, H // 4), 0)
    for yy in range(H // 4):
        for xx in range(W // 4):
            dx = (xx - W / 8) / (W / 8); dy = (yy - H / 8) / (H / 8)
            r = math.sqrt(dx * dx * 1.0 + dy * dy * 0.8)
            v.putpixel((xx, yy), int(max(0, min(1, (r - 0.55) / 0.6)) ** 1.6 * 200))
    v = v.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(20))
    vg = Image.new('RGBA', (W, H), (30, 6, 34, 0)); vg.putalpha(v)
    # bottom haze for text legibility
    hz = Image.new('L', (W, H), 0); hd = ImageDraw.Draw(hz)
    for yy in range(1100, 1700):
        k = 1 - abs(yy - 1370) / 300; hd.line([(0, yy), (W, yy)], fill=int(max(0, k) ** 1.5 * 120))
    hzl = Image.new('RGBA', (W, H), (20, 4, 26, 0)); hzl.putalpha(hz.filter(ImageFilter.GaussianBlur(30)))
    save(stack(vg), 'mono_vignette'); save(hzl, 'mono_haze')
    json.dump(meta, open(f'{OUT}/mono_meta.json', 'w'))

# ---------------- END CARD ----------------
def endcard():
    src = Image.open(f'{T}/fr_end.png').convert('RGB')
    s = max(W / src.width, H / src.height)
    bg = src.resize((math.ceil(src.width * s), math.ceil(src.height * s)), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(1.2))
    bg = ImageEnhance.Color(bg).enhance(1.1).convert('RGBA')
    grad = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(grad)
    for yy in range(H):
        a = 0
        if yy < 380: a = (1 - yy / 380) ** 1.3 * 175
        if yy > 980: a = max(a, min(1, (yy - 980) / 520) ** 1.2 * 245)
        gd.line([(0, yy), (W, yy)], fill=int(a))
    g = Image.new('RGBA', (W, H), (26, 6, 32, 0)); g.putalpha(grad)
    bg.alpha_composite(g)
    # pink haze band
    pk = Image.new('L', (W, H), 0); pd = ImageDraw.Draw(pk)
    for yy in range(1050, 1450):
        k = 1 - abs(yy - 1250) / 200; pd.line([(0, yy), (W, yy)], fill=int(max(0, k) * 70))
    pkl = Image.new('RGBA', (W, H), (255, 60, 150, 0)); pkl.putalpha(pk.filter(ImageFilter.GaussianBlur(40)))
    bg.alpha_composite(pkl)
    bg.convert('RGB').save(f'{OUT}/end_bg_b.png'); print('saved end_bg_b')
    # headline
    h1 = text_layer('アンチのはずが、', font(POP, 66), W // 2, 1250, stroke=10, stroke_fill=DEEP)
    h2o = text_layer('気づけば沼の底', font(POP, 116), W // 2, 1340, stroke=24, stroke_fill=DEEP)
    h2 = text_layer('気づけば沼の底', font(POP, 116), W // 2, 1340, stroke=12, stroke_fill=(255, 255, 255), gradient=((255, 140, 200), (225, 35, 115)))
    hb = stack(h1, h2o, h2)
    save(stack(glow(hb, 26, (255, 50, 140), 1.0), hb), 'end_headline_b')
    # logo row
    icon = Image.open(ASSET + 'LOGO-256x256-圆角.png').convert('RGBA').resize((124, 124), Image.LANCZOS)
    wm = Image.open(APPA + 'product-logo.png').convert('RGBA'); wm = wm.resize((int(wm.width * 58 / wm.height), 58), Image.LANCZOS)
    rw = 124 + 26 + wm.width; x0 = (W - rw) // 2; y0 = 130
    L = canvas(); L.alpha_composite(icon, (x0, y0)); L.alpha_composite(wm, (x0 + 150, y0 + 33))
    save(stack(glow(L, 16, (255, 80, 170), 0.9), L), 'end_logo_b')
    # button
    bx0, by0, bx1, by1 = 170, 1530, 910, 1672
    B = canvas(); bm = Image.new('L', (W, H), 0); ImageDraw.Draw(bm).rounded_rectangle([bx0, by0, bx1, by1], radius=71, fill=255)
    gr = Image.new('RGBA', (W, H)); grd = ImageDraw.Draw(gr)
    for xx in range(bx0, bx1 + 1):
        k = (xx - bx0) / (bx1 - bx0); c = (int(255 * (1 - k) + 168 * k), int(92 * (1 - k) + 70 * k), int(170 * (1 - k) + 255 * k))
        grd.line([(xx, by0), (xx, by1)], fill=c + (255,))
    gr.putalpha(bm); B.alpha_composite(glow(gr, 26, (255, 70, 170), 1.2)); B.alpha_composite(gr)
    hl = Image.new('L', (W, H), 0); ImageDraw.Draw(hl).rounded_rectangle([bx0 + 14, by0 + 8, bx1 - 14, by0 + 62], radius=30, fill=70)
    hlay = Image.new('RGBA', (W, H), (255, 255, 255, 0)); hlay.putalpha(ImageChops.multiply(hl, bm)); B.alpha_composite(hlay)
    ImageDraw.Draw(B).rounded_rectangle([bx0, by0, bx1, by1], radius=71, outline=(255, 255, 255, 230), width=4)
    bt = text_layer('今すぐダウンロード', font(POP, 58), W // 2 - 20, (by0 + by1) // 2, anchor='mm', stroke=4, stroke_fill=(170, 30, 110))
    B.alpha_composite(bt)
    # arrow circle
    ac = canvas(); ad = ImageDraw.Draw(ac); cx = bx1 - 70; cy = (by0 + by1) // 2
    ad.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=(255, 255, 255, 255))
    ad.line([(cx - 14, cy), (cx + 14, cy)], fill=(230, 50, 140, 255), width=8); ad.line([(cx + 2, cy - 14), (cx + 16, cy), (cx + 2, cy + 14)], fill=(230, 50, 140, 255), width=8, joint='curve')
    B.alpha_composite(ac)
    save(B, 'end_button')
    # badges
    gp = Image.open(ASSET + 'Google_Play_Badge_JA.svg.png').convert('RGBA'); gp = gp.resize((int(gp.width * 92 / gp.height), 92), Image.LANCZOS)
    ios = Image.open(ASSET + 'ios_badge.png').convert('RGBA'); ios = ios.crop(ios.split()[3].getbbox()); ios = ios.resize((int(ios.width * 92 / ios.height), 92), Image.LANCZOS)
    inner = ios.crop((8, 6, ios.width - 8, ios.height - 6))
    nb = Image.new('RGBA', gp.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(nb)
    bd.rounded_rectangle([0, 0, gp.width - 1, gp.height - 1], radius=14, fill=(0, 0, 0, 255), outline=(166, 166, 166, 255), width=2)
    nb.alpha_composite(inner, ((gp.width - inner.width) // 2, (gp.height - inner.height) // 2)); ios = nb
    gap = 28; tot = gp.width + gap + ios.width; x0 = (W - tot) // 2; y0 = 1730
    S = canvas(); S.alpha_composite(gp, (x0, y0)); S.alpha_composite(ios, (x0 + gp.width + gap, y0))
    save(S, 'end_badges_c')
    # hand pointer
    hp = Image.open(APPA + 'user-pointer.png').convert('RGBA'); hp = hp.resize((190, int(190 * hp.height / hp.width)), Image.LANCZOS)
    P = canvas(); P.alpha_composite(glow(hp, 8, (0, 0, 0), 0.6), (cx - 50, cy - 10)); P.alpha_composite(hp, (cx - 50, cy - 10))
    save(P, 'end_hand'); json.dump({'tapX': cx, 'tapY': cy}, open(f'{OUT}/end_meta.json', 'w'))
    # sparkles
    import random; random.seed(7)
    for k in range(2):
        SP = canvas()
        for j in range(9):
            x = random.randint(80, 1000); y = random.choice([random.randint(1060, 1130), random.randint(1330, 1380), random.randint(150, 900)])
            sz = random.randint(26, 54)
            if j % 3 == 0: SP.alpha_composite(heart(sz, (255, 110, 180), outline=False), (x, y))
            else:
                st = canvas(); sd = ImageDraw.Draw(st); r = sz // 2
                sd.polygon([(x, y - r), (x + r * 0.22, y - r * 0.22), (x + r, y), (x + r * 0.22, y + r * 0.22), (x, y + r), (x - r * 0.22, y + r * 0.22), (x - r, y), (x - r * 0.22, y - r * 0.22)], fill=(255, 245, 250, 255))
                SP.alpha_composite(glow(st, 8, (255, 120, 200), 1.4)); SP.alpha_composite(st)
        save(SP, f'end_spark{k + 1}')

if __name__ == '__main__':
    import sys
    for name in (sys.argv[1:] or ['title', 'meter', 'mono', 'endcard']): globals()[name]()
