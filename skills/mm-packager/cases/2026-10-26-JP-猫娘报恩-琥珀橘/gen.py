# MM-JP 猫娘报恩 · 图层生成（琥珀橘，无框跟脸字幕 / 选项犹豫 / 选项段弹幕 / Logo 开头 / 片尾）
import os, sys, json, math, subprocess, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
sys.path.insert(0, os.path.dirname(__file__))
from mmstyle import ZM, MOCHIY, APP, dm_sprite
ROOT = 'F:/钟海明/2026/2026年10月26日MM-JP-猫娘报恩/'
OUT = ROOT + '包装素材v1/layers/'; SRC = ROOT + '猫娘报恩.mp4'
ASSET = 'F:/钟海明/MM透明尾板/片尾/片尾文件夹/(素材)/图片/'
W, H = 1080, 1920; V = 'g'
WH = (255, 255, 255); DARK = (52, 26, 8)
EMPH = [(0, (255, 238, 196)), (.55, (255, 192, 108)), (1, (242, 142, 62))]
AMB = [(0, (255, 226, 160)), (.5, (255, 182, 92)), (1, (236, 128, 48))]
SEG = [(0.0, 8.70, 0.0), (8.70, 15.9667, 2.5), (15.9667, 27.0333, 5.0)]
CH = [(8.70, 2.5, 8.66), (18.4667, 2.5, 15.92), (32.0333, 3.2, 26.95)]   # 成片起点, 时长, 定格源帧
END0, ED = 35.2333, 5.0; END1 = END0 + ED
OUTF = .35; CLICK = 3.6
def o(src):
    for a, b, off in SEG:
        if a - 1e-6 <= src < b + 1e-6: return src + off
    raise ValueError(src)

FONTS = {}
def font(p, s):
    if (p, s) not in FONTS: FONTS[(p, s)] = ImageFont.truetype(p, s)
    return FONTS[(p, s)]
def canvas(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))
def save(im, name):
    fn = f'{name}_{V}'; im.save(OUT + fn + '.png', compress_level=1); return fn
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def grad_img(w, h, stops, horiz=False):
    n = w if horiz else h; t = np.linspace(0, 1, max(2, n))
    ch = [np.interp(t, [s[0] for s in stops], [s[1][i] for s in stops]) for i in range(3)]
    g = np.stack(ch, -1).astype(np.uint8)
    g = np.repeat(g[None, :, :], h, 0) if horiz else np.repeat(g[:, None, :], w, 1)
    return Image.fromarray(g, 'RGB')
LAY = []
def add(track, name, start, dur, file, ax=.5, ay=.5, k=None):
    s = round(start * 30 + 1e-6) / 30; e = round((start + dur) * 30 + 1e-6) / 30
    if e - s < 1 / 30 - 1e-6: return
    LAY.append({'track': track, 'name': name, 'start': round(s, 4), 'dur': round(round(e, 4) - round(s, 4), 4), 'file': file,
                'ax': round(ax, 4), 'ay': round(ay, 4), 'k': k or {}, 'ext': '.png'})
def kf(*pts): return [[round(p[0], 3), round(p[1], 3)] + ([p[2]] if len(p) > 2 else []) for p in pts]
SFX = []
def sfx(name, t, v): SFX.append([name, round(t, 3), v])
def _paste(L, im, x, y):
    bx0, by0 = max(0, x), max(0, y); bx1, by1 = min(W, x + im.width), min(H, y + im.height)
    if bx1 <= bx0 or by1 <= by0: return
    L.alpha_composite(im.crop((bx0 - x, by0 - y, bx1 - x, by1 - y)), (bx0, by0))
def text(L, xy, s, f, fill=WH, a=1.0, anchor='ls', shadow=.55, grad=None):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text(xy, s, font=f, fill=255, anchor=anchor)
    bb = m.getbbox()
    if not bb: return
    if shadow:
        pad = 24; c = m.crop((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)).filter(ImageFilter.GaussianBlur(7))
        sh = Image.new('RGBA', c.size, (0, 0, 0, 0)); sh.putalpha(c.point(lambda v: int(v * shadow * a)))
        _paste(L, sh, bb[0] - pad, bb[1] - pad + 4)
    c = m.crop(bb)
    col = grad_img(c.width, c.height, grad).convert('RGBA') if grad else Image.new('RGBA', c.size, fill + (255,))
    col.putalpha(c.point(lambda v: int(v * a))); _paste(L, col, bb[0], bb[1])
def hair(L, x0, x1, y, a=.8, w=2, fade=True, stops=None):
    n = int(x1 - x0); g = grad_img(n, w, stops or EMPH, horiz=True).convert('RGBA')
    al = (np.clip(1 - np.abs(np.linspace(-1, 1, n)), 0, 1) ** .5 if fade else np.ones(n)) * 255 * a
    g.putalpha(Image.fromarray(np.repeat(al.astype(np.uint8)[None], w, 0))); _paste(L, g, int(x0), int(y))
def disc(r, rgb, soft=.6):
    n = int(r * 4) + 4; g = Image.new('L', (n, n), 0); ImageDraw.Draw(g).ellipse([n / 2 - r, n / 2 - r, n / 2 + r, n / 2 + r], fill=255)
    g = g.filter(ImageFilter.GaussianBlur(max(.5, r * soft))); s = Image.new('RGBA', (n, n), rgb + (0,)); s.putalpha(g); return s

_FR = {}
def frame(src):
    if src not in _FR:
        b = subprocess.run(['ffmpeg', '-v', 'quiet', '-ss', f'{src:.3f}', '-i', SRC, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
        _FR[src] = Image.open(io.BytesIO(b)).convert('RGB').resize((W, H), Image.LANCZOS)
    return _FR[src]
def soft_bg(im, blur=20, br=.62, sat=1.15):
    b = im.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur / 4)).resize((W, H), Image.BILINEAR)
    b = ImageEnhance.Color(b).enhance(sat); b = ImageEnhance.Brightness(b).enhance(br)
    y, x = np.mgrid[0:H, 0:W]; r = np.sqrt(((x - W / 2) / (W * .7)) ** 2 + ((y - H / 2) / (H * .62)) ** 2)
    v = np.clip(1 - .45 * np.clip(r - .45, 0, 1), 0, 1)[..., None]
    return Image.fromarray((np.asarray(b).astype(np.float32) * v).astype(np.uint8))

# ---------------- Logo ----------------
def logo_row(icon_h=104, wm_h=44):
    icon = Image.open(ASSET + 'LOGO-256x256-圆角.png').convert('RGBA').resize((icon_h, icon_h), Image.LANCZOS)
    wm = Image.open(APP + 'public/assets/product-logo.png').convert('RGBA'); wm = wm.resize((int(wm.width * wm_h / wm.height), wm_h), Image.LANCZOS)
    tot = icon_h + 22 + wm.width; x = int(540 - tot / 2)
    return icon, wm, x
def logo_layer(y):
    icon, wm, x = logo_row(); L = canvas()
    for im, px, py in [(icon, x, y - icon.height // 2), (wm, x + icon.width + 22, y - wm.height // 2)]:
        m = Image.new('L', (W, H), 0); m.paste(im.split()[3], (px, py)); m = m.filter(ImageFilter.GaussianBlur(9))
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(m.point(lambda v: int(v * .55))); L.alpha_composite(sh, (0, 5))
        L.alpha_composite(im, (px, py))
    return L

def intro():
    LY = 250
    Lg = logo_layer(LY); fn = save(Lg, 'intro_logo')
    add('X-ilogo', '开头 Logo', .08, 2.4, fn, ay=LY / H,
        k={'scale': kf((0, .4), (.24, 1.12), (.38, .95), (.5, 1.02), (.6, 1)), 'opacity': kf((0, 0), (.12, 1), (2.05, 1), (2.32, 0)), 'y': kf((2.0, 0), (2.32, -24))})
    G = canvas(); h = disc(170, (255, 196, 120), .55); _paste(G, h, 540 - h.width // 2, LY - h.height // 2)
    add('X-ihalo', '开头 光晕', .08, 1.6, save(G, 'intro_halo'), ay=LY / H, k={'scale': kf((0, .5), (.5, 1.15), (1.6, 1.3)), 'opacity': kf((0, 0), (.15, .75), (1.6, 0))})
    R = canvas(); ImageDraw.Draw(R).ellipse([540 - 120, LY - 120, 540 + 120, LY + 120], outline=(255, 226, 180, 230), width=5)
    add('X-iring', '开头 冲击环', .2, .6, save(R, 'intro_ring'), ay=LY / H, k={'scale': kf((0, .5), (.6, 3.2)), 'opacity': kf((0, .95), (.6, 0))})
    # 星星爆发（15fps 逐帧）
    rng = np.random.default_rng(3); stars = [(rng.uniform(0, 6.283), rng.uniform(260, 620), rng.uniform(5, 11)) for _ in range(26)]
    for j in range(12):
        t = j / 15; L = canvas(); d = ImageDraw.Draw(L)
        for a, v, r in stars:
            q = t / .8; dist = v * ease(q); px, py = 540 + math.cos(a) * dist * 1.1, LY + math.sin(a) * dist * .7
            al = int(255 * (1 - q) ** 1.3); rr = r * (1 - .5 * q)
            d.polygon([(px, py - rr * 2), (px + rr * .5, py - rr * .5), (px + rr * 2, py), (px + rr * .5, py + rr * .5), (px, py + rr * 2), (px - rr * .5, py + rr * .5), (px - rr * 2, py), (px - rr * .5, py - rr * .5)], fill=(255, 230, 180, al))
        add('X-ispark', '开头 星星', .22 + t, 1 / 15, save(L, f'intro_spark{j}'))
    # 扫光
    icon, wm, x = logo_row(); tm = Image.new('L', (W, H), 0)
    tm.paste(icon.split()[3], (x, LY - icon.height // 2)); tm.paste(wm.split()[3], (x + icon.width + 22, LY - wm.height // 2))
    tma = np.asarray(tm).astype(np.float32) / 255; yy, xx = np.mgrid[0:H, 0:W]
    for j in range(8):
        c = 180 + j * 100; band = np.clip(1 - np.abs((xx + (yy - LY) * .5) - c) / 70, 0, 1) ** 2
        S = Image.new('RGBA', (W, H), (255, 250, 236, 0)); S.putalpha(Image.fromarray((tma * band * 210).astype(np.uint8)))
        add('X-isheen', '开头 Logo扫光', .75 + j / 15, 1 / 15, save(S, f'intro_sheen{j}'))
    sfx('u_end', .05, .45); sfx('u_pop', .2, .4)

def flash_file(): return save(Image.new('RGBA', (W, H), (255, 255, 255, 255)), 'flash')
def transforms():
    ff = flash_file()
    # 变身：烟雾出现处闪白
    add('X-flash', '变身 闪白', 2.78, .55, ff, k={'opacity': kf((0, 0), (.05, .85), (.55, 0))})
    sfx('u_flash', 2.76, .6)
    # 变回猫：ポンッ！
    T = o(25.13); L = canvas()
    f = font(MOCHIY, 150); cx, cy = 690, 560
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text((cx, cy), 'ポンッ！', font=f, fill=255, anchor='mm', stroke_width=14, stroke_fill=255)
    sh = Image.new('RGBA', (W, H), (60, 24, 4, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * .6))); L.alpha_composite(sh, (0, 8))
    wb = Image.new('RGBA', (W, H), (255, 255, 255, 0)); wb.putalpha(m); L.alpha_composite(wb)
    text(L, (cx, cy), 'ポンッ！', f, anchor='mm', shadow=0, grad=AMB)
    add('X-pon', 'ポンッ！', T, 1.0, save(L, 'pon'), ax=cx / W, ay=cy / H,
        k={'scale': kf((0, .3), (.14, 1.18), (.26, .96), (.36, 1)), 'rotation': kf((0, -14), (.2, -6)), 'opacity': kf((0, 0), (.06, 1), (.75, 1), (1.0, 0))})
    add('X-flash', '变回猫 闪白', T, .35, ff, k={'opacity': kf((0, .5), (.35, 0))})
    sfx('u_pop', T, .7); sfx('u_coin', o(16.5), .45)

# ---------------- 字幕（无框跟脸） ----------------
ANCH = [(0, .46, .43, .30), (3.5, .47, .38, .40), (4, .48, .35, .46), (6.5, .48, .37, .42), (7, .49, .30, .38), (9, .5, .29, .4), (10, .49, .37, .45),
        (12.5, .54, .38, .42), (13.3, .55, .32, .45), (13.6, .40, .14, .25), (16.3, .45, .12, .22), (17.5, .48, .46, .25), (19.5, .43, .37, .35),
        (20, .41, .36, .38), (21.5, .35, .35, .38), (23, .30, .38, .35), (24.5, .32, .35, .3), (25, .28, .37, .25), (26, .46, .45, .3), (27.1, .46, .45, .3)]
_A = np.array(ANCH)
def face(t): return [float(np.interp(t, _A[:, 0], _A[:, i])) for i in (1, 2, 3)]
LINES = [
    ([('にゃむ…', 2.25), ('にゃ…', 2.83), ('*うぇっ！', 3.15)], 3.48),
    ([('何食べさせたにゃ', 4.03), ('\n*貧乏ご主人！', 4.98)], 5.83),
    ([('……え', 6.54), (' 手？', 6.95), ('\nなんで', 7.64), ('*人間に！？', 7.94)], 8.55),
    ([('*……フシャーッ！', 9.59)], 10.33),
    ([('人間になったなら', 11.25), ('\nもう', 12.22), ('*出てくにゃ', 12.66)], 13.3),
    ([('お金持ちの家へ', 14.42), ('*行くにゃ', 15.4)], 15.84),
    ([('にゃにゃにゃっ！？', 16.84), ('\n*これは違うにゃ！', 17.84)], 19.06),
    ([('金持ちのお金で', 19.6), ('ご主人を', 20.64), ('\n助けようなんて', 21.18), ('\n*考えてないにゃ！', 21.92)], 22.95),
    ([('にゃーはただ……', 24.05)], 25.08),
    ([('*にゃっ！', 25.46)], 26.16),
]
MARK_H = 16; RH = 90
def layout(chunks):
    rows, cur = [], []
    for i, (s, t) in enumerate(chunks):
        if s.startswith('\n') and cur: rows.append(cur); cur = []
        cur.append(i)
    rows.append(cur); items = []
    for s, t in chunks:
        s = s.lstrip('\n'); emph = s.startswith('*'); s = s.lstrip('*')
        items.append({'s': s, 't': t, 'emph': emph, 'f': font(ZM, 76 if emph else 58)})
    y = 960 + MARK_H + 18; maxw = 0
    for r in rows:
        tw = sum(items[i]['f'].getlength(items[i]['s']) for i in r); x = 540 - tw / 2
        for i in r: items[i]['xy'] = (x, y + 66); x += items[i]['f'].getlength(items[i]['s'])
        y += RH; maxw = max(maxw, tw)
    return items, maxw, y - 960
def sub_text(L, it):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text(it['xy'], it['s'], font=it['f'], fill=255, anchor='ls')
    bb = m.getbbox(); pad = 40; c = m.crop((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad))
    for r, a in [(18, .62), (5, .9)]:
        h_ = c.filter(ImageFilter.GaussianBlur(r)); sh = Image.new('RGBA', c.size, (20, 10, 4, 0)); sh.putalpha(h_.point(lambda v: int(min(255, v * a * 1.6))))
        _paste(L, sh, bb[0] - pad, bb[1] - pad + 3)
    if it['emph']:
        g_ = c.filter(ImageFilter.GaussianBlur(14)); gc = Image.new('RGBA', c.size, (246, 150, 60, 0)); gc.putalpha(g_.point(lambda v: int(min(255, v * .4))))
        _paste(L, gc, bb[0] - pad, bb[1] - pad)
    text(L, it['xy'], it['s'], it['f'], WH, anchor='ls', shadow=0, grad=EMPH if it['emph'] else None)
def marker():
    L = canvas(); tri = [(540, 960), (540 - 13, 960 + MARK_H), (540 + 13, 960 + MARK_H)]
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).polygon([(x, y + 3) for x, y in tri], fill=150); g = g.filter(ImageFilter.GaussianBlur(5))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(g); L.alpha_composite(sh)
    ImageDraw.Draw(L).polygon(tri, fill=(255, 226, 170, 245)); return save(L, 'sub_marker')
def path_k(t0, dur, bw, bh):
    xs, ys = [], []; n = max(1, int(math.ceil(dur / .2)))
    for j in range(n + 1):
        tt = min(dur, j * .2); cx, cy, fw = face(t0 + tt)
        x = min(max(cx * W, 50 + bw / 2), 1030 - bw / 2) - 540
        top = (cy + .30 * fw) * H + 30
        top = min(max(top, 420), 1480 - bh)
        xs.append([round(tt, 3), round(x, 1)]); ys.append([round(tt, 3), round(top - 960, 1)])
    return xs, ys
def subs():
    mk = marker()
    for li, (chunks, end) in enumerate(LINES):
        t0 = chunks[0][1]; seg = next(sg for sg in SEG if sg[0] <= t0 < sg[1]); a, b, off = seg
        nxt = LINES[li + 1][0][0][1] if li + 1 < len(LINES) else 99
        hide = min(nxt - .1, end + .9, b - .05)
        if li == 8: hide = 25.1
        items, bw, bh = layout(chunks); tag = f'sub_{int(t0 * 100):04d}'
        def lay(track, name, s0, fn, pivot=None):
            D = hide - s0; xs, ys = path_k(s0, D, bw, bh)
            k = {'x': xs, 'y': ys, 'opacity': kf((0, 0), (.15, 1), (max(.16, D - .15), 1), (D, 0))}; ax = ay = .5
            if pivot:
                ax, ay = pivot[0] / W, pivot[1] / H; k['scale'] = kf((0, 1.45), (.12, .94), (.22, 1.03), (.32, 1))
            add(track, name, s0 + off, D, fn, ax=ax, ay=ay, k=k)
        lay('X-sub0', '字幕 箭头', t0, mk)
        for i, it in enumerate(items):
            L = canvas(); sub_text(L, it); bb = L.getbbox()
            lay(f'X-sub{i + 1}', '字幕 ' + it['s'].strip(), it['t'], save(L, f'{tag}_{i}'), ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2) if it['emph'] else None)
            if it['emph']: sfx('u_pop', it['t'] + off, .1)

# ---------------- 选项 v2：中下方小胶囊 + 倒计时条，无全屏模糊，点击后快速过渡 ----------------
QS = None
OPTS = [['①おやつだよ', '②貧乏ご主人って何？', '③人間でも可愛いね'], ['①行かないで', '②ポケットの中 何？', '③好きにすれば'], ['①もう一本おやつをあげる', '②抱っこして帰る']]
PICK = [0, 1, None]
CLICK = 2.0
HOVER = [[(.55, 2), (1.0, 1), (1.45, 0)], [(.55, 0), (1.0, 2), (1.45, 1)], [(.55, 0), (1.1, 1), (1.7, 0), (2.3, 1), (2.8, 0)]]
OYS = [1215, 1310, 1405]; BAR_Y = 1138; BAR_W = 420; PH = 76
DMQ = [['おやつ一択', '選択肢ひどくて草', 'ご主人の財布事情…', 'wwwww'],
       ['ポケット膨らんでない？', '引き止めろ！', '好きにすればは鬼', 'www'],
       ['変身おやつ一択', 'もっと食べさせろw', 'また人間になるの！？', 'おやつで釣るなw', '無限ループ確定']]
DM_LANES = [170, 1640, 265, 1735, 360]
TICKS = []   # BGM 同步点：(kind, t)
def pointer_imgs():
    L = canvas(); r = 30
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([540 - r - 5, 960 - r, 540 + r + 5, 960 + r + 12], fill=110); g = g.filter(ImageFilter.GaussianBlur(10))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(g); L.alpha_composite(sh)
    d = ImageDraw.Draw(L); d.ellipse([540 - r, 960 - r, 540 + r, 960 + r], fill=(255, 255, 255, 95), outline=(255, 255, 255, 230), width=3)
    d.ellipse([540 - 7, 960 - 7, 540 + 7, 960 + 7], fill=(255, 255, 255, 245))
    R = canvas(); ImageDraw.Draw(R).ellipse([540 - 40, 960 - 40, 540 + 40, 960 + 40], outline=(255, 255, 255, 230), width=4)
    return save(L, 'pointer'), save(R, 'ripple')
def pill_w(txt): return max(380, int(font(ZM, 38).getlength(txt[1:]) + 150))
def pill(txt, y, sel):
    L = canvas(); w = pill_w(txt); x0, x1, y0, y1 = 540 - w // 2, 540 + w // 2, y - PH // 2, y + PH // 2
    S = Image.new('L', (W, H), 0); ImageDraw.Draw(S).rounded_rectangle([x0, y0 + 8, x1, y1 + 8], radius=PH // 2, fill=150 if sel else 120)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(S.filter(ImageFilter.GaussianBlur(14))); L.alpha_composite(sh)
    if sel:
        G = Image.new('L', (W, H), 0); ImageDraw.Draw(G).rounded_rectangle([x0 - 6, y0 - 6, x1 + 6, y1 + 6], radius=PH // 2 + 6, fill=150)
        gc = Image.new('RGBA', (W, H), (255, 170, 80, 0)); gc.putalpha(G.filter(ImageFilter.GaussianBlur(16))); L.alpha_composite(gc)
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([x0, y0, x1, y1], radius=PH // 2, fill=255)
    if sel:
        body = Image.new('RGBA', (W, H), (0, 0, 0, 0)); body.paste(grad_img(w, PH, AMB, horiz=True).convert('RGBA'), (x0, y0)); body.putalpha(m)
    else:
        body = Image.new('RGBA', (W, H), (24, 14, 8, 0)); body.putalpha(m.point(lambda v: int(v * .72)))
    L.alpha_composite(body)
    ImageDraw.Draw(L).rounded_rectangle([x0, y0, x1, y1], radius=PH // 2, outline=(255, 236, 200, 255) if sel else (255, 210, 150, 150), width=2)
    cx, cy = x0 + 44, y
    ImageDraw.Draw(L).ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(255, 250, 240, 255) if sel else (255, 190, 100, 255))
    text(L, (cx, cy + 1), str('①②③'.index(txt[0]) + 1), font(MOCHIY, 28), DARK, anchor='mm', shadow=0)
    text(L, (x0 + 82, cy + 2), txt[1:], font(ZM, 38), DARK if sel else WH, anchor='lm', shadow=0 if sel else .5)
    return L
def bar_img(p):
    """p=剩余比例"""
    L = canvas(); x0 = 540 - BAR_W // 2; d = ImageDraw.Draw(L)
    d.rounded_rectangle([x0, BAR_Y - 5, x0 + BAR_W, BAR_Y + 5], radius=5, fill=(255, 255, 255, 70))
    fw = int(BAR_W * p)
    if fw > 6:
        col = AMB if p > .35 else [(0, (255, 170, 120)), (1, (240, 70, 60))]
        g = grad_img(fw, 10, col, horiz=True).convert('RGBA'); mk = Image.new('L', (fw, 10), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, fw - 1, 9], radius=5, fill=255)
        G = Image.new('L', (W, H), 0); ImageDraw.Draw(G).rounded_rectangle([x0, BAR_Y - 5, x0 + fw, BAR_Y + 5], radius=5, fill=200)
        gc = Image.new('RGBA', (W, H), (255, 160, 70, 0)); gc.putalpha(G.filter(ImageFilter.GaussianBlur(8))); L.alpha_composite(gc)
        g.putalpha(mk); L.alpha_composite(g, (x0, BAR_Y - 5))
        d.ellipse([x0 + fw - 8, BAR_Y - 8, x0 + fw + 8, BAR_Y + 8], fill=(255, 248, 230, 255))
    return L
def shade_img():
    a = np.clip((np.arange(H) - 900) / 500, 0, 1) ** 1.3 * 150
    L = Image.new('RGBA', (W, H), (16, 8, 2, 0)); L.putalpha(Image.fromarray(np.repeat(a.astype(np.uint8)[:, None], W, 1))); return L
def ptr_pos(opts, idx): return pill_w(opts[idx]) // 2 - 16, OYS[idx] + 18 - 960
def choices(pf, rf):
    ff = flash_file(); shf = save(shade_img(), 'ch_shade')
    for ci, (s0, D, fr) in enumerate(CH):
        last = PICK[ci] is None; pick = PICK[ci]; opts = OPTS[ci]
        TICKS.append(('start', s0))
        add('X-flash', f'选项{ci + 1} 定格闪', s0, .22, ff, k={'opacity': kf((0, .35), (.22, 0))}); sfx('u_flash', s0, .35)
        add('X-cshade', f'选项{ci + 1} 底部压暗', s0, D, shf, k={'opacity': kf((0, 0), (.2, 1), *([(D - .15, 1), (D, 0)] if not last else []))})
        # 倒计时条（15fps 逐帧）
        T0, TOT = .3, (2.7 if not last else D - .3 - .05)
        stop = CLICK if not last else D
        n = int(round((stop - T0) * 15))
        add('X-cbar', f'选项{ci + 1} 倒计时', s0 + .15, T0 - .15, save(bar_img(1), f'ch{ci + 1}_bar_full'), k={'opacity': kf((0, 0), (.12, 1)), 'scale': kf((0, .6), (.15, 1))})
        for j in range(n + 1):
            t = T0 + j / 15; p = clamp(1 - (t - T0) / TOT)
            dur = 1 / 15 if j < n else (D - .15 - t if not last else D - t)
            k = {'opacity': kf((dur - .12, 1), (dur, 0))} if (j == n and not last) else None
            add('X-cbar', f'选项{ci + 1} 倒计时', s0 + t, dur, save(bar_img(p), f'ch{ci + 1}_bar{j:02d}'), k=k)
            if j % 4 == 0 and t < stop - .05: TICKS.append(('tick', s0 + t))
        # 胶囊选项
        for oi, txt in enumerate(opts):
            t0 = s0 + .08 + oi * .07; y = OYS[oi]; fn = save(pill(txt, y, False), f'ch{ci + 1}_o{oi + 1}')
            k = {'scale': kf((0, .8), (.16, 1.04), (.26, 1)), 'opacity': kf((0, 0), (.12, 1))}; dur = s0 + D - t0
            if not last:
                r0 = s0 + CLICK + .03 - t0
                if oi != pick: k['opacity'] = kf((0, 0), (.12, 1), (r0, 1), (r0 + .15, 0)); dur = r0 + .15
                else: k['opacity'] = kf((0, 0), (.12, 1), (r0, 1), (r0 + .01, 0)); dur = r0 + .01
            add(f'X-co{oi + 1}', f'选项{ci + 1} {txt}', t0, dur, fn, ay=y / H, k=k)
        sfx('u_bubble', s0 + .1, .3)
        # 指针
        hv = HOVER[ci]; P0 = .35; px0, py0 = ptr_pos(opts, hv[0][1])
        xs, ys_ = [(0, px0 + 120), (hv[0][0] - P0, px0)], [(0, py0 + 260), (hv[0][0] - P0, py0)]
        for (t, idx), (_, pidx) in zip(hv[1:], hv[:-1]):
            a, b = ptr_pos(opts, pidx), ptr_pos(opts, idx)
            xs += [(t - .22 - P0, a[0]), (t - P0, b[0])]; ys_ += [(t - .22 - P0, a[1]), (t - P0, b[1])]
        if not last:
            end = D - .1 - P0
            add('X-ptr', f'选项{ci + 1} 指针', s0 + P0, end, pf, k={'x': kf(*xs), 'y': kf(*ys_), 'opacity': kf((0, 0), (.1, 1), (end - .12, 1), (end, 0)),
                'scale': kf((CLICK - .08 - P0, 1), (CLICK - P0, .78), (CLICK + .1 - P0, 1))})
            px, py = ptr_pos(opts, pick)
            add('X-prip', f'选项{ci + 1} 点击波纹', s0 + CLICK, .35, rf, k={'x': kf((0, px)), 'y': kf((0, py)), 'scale': kf((0, .7), (.35, 2.0)), 'opacity': kf((0, .9), (.35, 0))})
            y = OYS[pick]; r = D - CLICK - .03
            add('X-cs', f'选项{ci + 1} 选中', s0 + CLICK + .03, r, save(pill(opts[pick], y, True), f'ch{ci + 1}_sel'), ay=y / H,
                k={'scale': kf((0, 1), (.1, 1.1), (.22, 1.02)), 'opacity': kf((0, 1), (r - .13, 1), (r, 0))})
            sfx('u_click', s0 + CLICK - .02, .8); sfx('u_ok', s0 + CLICK + .03, .55)
            TICKS.append(('click', s0 + CLICK))
            add('X-flash', f'选项{ci + 1} 过渡闪', s0 + D - .12, .3, ff, k={'opacity': kf((0, 0), (.1, .45), (.3, 0))})
        else:
            add('X-ptr', f'选项{ci + 1} 指针犹豫', s0 + P0, D - P0, pf, k={'x': kf(*xs, (D - P0, xs[-1][1])), 'y': kf(*ys_, (D - P0, ys_[-1][1])), 'opacity': kf((0, 0), (.1, 1))})
            add('X-flash', '选项3→片尾 闪光', s0 + D - .22, .6, ff, k={'opacity': kf((0, 0), (.2, 1), (.6, 0))}); sfx('u_flash', s0 + D - .2, .7)
            TICKS.append(('end', s0 + D))
        # 选项段弹幕（上方/最下车道，不压选项）
        for j, s in enumerate(DMQ[ci]):
            st = s0 + .05 + j * .38; dur = s0 + D - st
            if dur < .5: continue
            sp = dm_sprite(s, amber=(j % 3 == 1)); L = canvas(); lane = DM_LANES[j % len(DM_LANES)]
            L.alpha_composite(sp, (540 - sp.width // 2, lane - sp.height // 2)); span = 540 + sp.width / 2 + 24
            add(f'X-dm{j + 1}', f'弹幕 {s}', st, dur, save(L, f'ch{ci + 1}_dm{j}'), k={'x': kf((0, span), (3.2, -span)), 'opacity': kf((0, .95))})

# ---------------- 片尾 ----------------
def endcard(pf, rf):
    im = frame(20.0)
    b = ImageEnhance.Brightness(im.filter(ImageFilter.GaussianBlur(3))).enhance(.62)
    a = np.asarray(b).astype(np.float32); yy = np.arange(H, dtype=np.float32)[:, None, None]
    shade = np.clip((yy - 700) / 700, 0, 1) * .78 + np.clip(1 - yy / 420, 0, 1) * .5
    a = a * (1 - shade) + np.array([14, 9, 5], np.float32) * shade
    bgi = Image.fromarray(a.astype(np.uint8))
    add('V1', '片尾 背景', END0, ED, save(bgi.convert('RGBA'), 'end_bg'), k={'scale': kf((0, 1.0), (ED, 1.05))})
    sfx('u_end', END0, .5)
    add('X-elogo', '片尾 Logo', END0 + .1, ED - .1, save(logo_layer(200), 'end_logo'), ay=200 / H,
        k={'opacity': kf((0, 0), (.2, 1)), 'scale': kf((0, .6), (.22, 1.08), (.34, 1))})
    L = canvas(); text(L, (540, 1050), '恩返しする猫', font(MOCHIY, 128), anchor='ms', grad=AMB, shadow=.8)
    add('X-ecard', '片尾 卡片标题', END0 + .5, ED - .5, save(L, 'end_title'), ay=1000 / H,
        k={'opacity': kf((0, 0), (.15, 1)), 'scale': kf((0, 1.4), (.18, .95), (.3, 1))})
    sfx('u_pop', END0 + .5, .55)
    L = canvas(); hair(L, 420, 660, 1120, .9, stops=AMB)
    text(L, (540, 1190), 'ツンデレ猫が こっそり小銭を拾って', font(ZM, 50), WH, anchor='mm', shadow=.75)
    text(L, (540, 1260), '恩返ししようとしてた', font(ZM, 50), WH, anchor='mm', shadow=.75)
    add('X-ehead', '片尾 文案', END0 + 1.0, ED - 1.0, save(L, 'end_copy'), ay=1220 / H, k={'y': kf((0, 30), (.3, 0)), 'opacity': kf((0, 0), (.22, 1))})
    sfx('u_bubble', END0 + 1.0, .4)
    bx0, by0, bx1, by1 = 150, 1380, 930, 1516; L = canvas()
    G = Image.new('L', (W, H), 0); ImageDraw.Draw(G).rounded_rectangle([bx0, by0 + 6, bx1, by1 + 6], radius=70, fill=110)
    G = G.filter(ImageFilter.GaussianBlur(30)); gc = Image.new('RGBA', (W, H), (246, 160, 70, 0)); gc.putalpha(G); L.alpha_composite(gc)
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([bx0, by0, bx1, by1], radius=68, fill=255)
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); g.paste(grad_img(bx1 - bx0, by1 - by0, AMB, horiz=True).convert('RGBA'), (bx0, by0)); g.putalpha(m); L.alpha_composite(g)
    hl = Image.new('L', (W, H), 0); ImageDraw.Draw(hl).rounded_rectangle([bx0 + 6, by0 + 4, bx1 - 6, by0 + 60], radius=60, fill=70)
    hw = Image.new('RGBA', (W, H), (255, 255, 255, 0)); hw.putalpha(hl.filter(ImageFilter.GaussianBlur(6))); L.alpha_composite(hw)
    text(L, (540, (by0 + by1) / 2 + 2), 'ダウンロードして続きを見よう', font(ZM, 50), DARK, anchor='mm', shadow=0)
    BS = END0 + 1.5; TAPS = [2.6, 2.9, 3.2, 3.5]
    bsc = [[0, .7], [.18, 1.05], [.28, 1]]
    for tp in TAPS: r = END0 + tp - BS; bsc += [[round(r - .04, 3), 1], [round(r + .04, 3), .95], [round(r + .16, 3), 1]]
    add('X-ebtn', '片尾 下载按钮', BS, END1 - BS, save(L, 'end_btn'), ay=(by0 + by1) / 2 / H, k={'scale': bsc, 'opacity': kf((0, 0), (.12, 1))})
    sfx('u_bubble', BS, .45)
    bma = np.asarray(m.crop((bx0, by0, bx1, by1))).astype(np.float32) / 255; yy, xx = np.mgrid[0:by1 - by0, 0:bx1 - bx0]
    for j in range(8):
        c = -80 + j * 130; band = np.clip(1 - np.abs((xx + (yy - 70) * .5) - c) / 60, 0, 1) ** 2 * .6
        S = canvas(); s_ = Image.new('RGBA', (bx1 - bx0, by1 - by0), (255, 255, 255, 0)); s_.putalpha(Image.fromarray((bma * band * 255).astype(np.uint8))); S.alpha_composite(s_, (bx0, by0))
        fn = save(S, f'end_sheen{j}')
        for st in (END0 + 1.9, END0 + 3.9): add('X-esheen', '片尾 按钮扫光', st + j / 15, 1 / 15, fn)
    gp = Image.open(ASSET + 'Google_Play_Badge_JA.svg.png').convert('RGBA'); gp = gp.resize((int(gp.width * 88 / gp.height), 88), Image.LANCZOS)
    ios = Image.open(ASSET + 'ios_badge.png').convert('RGBA'); ios = ios.crop(ios.split()[3].getbbox()); ios = ios.resize((int(ios.width * 88 / ios.height), 88), Image.LANCZOS)
    inner = ios.crop((8, 6, ios.width - 8, ios.height - 6))
    nb = Image.new('RGBA', gp.size, (0, 0, 0, 0)); ImageDraw.Draw(nb).rounded_rectangle([0, 0, gp.width - 1, gp.height - 1], radius=14, fill=(0, 0, 0, 255), outline=(166, 166, 166, 255), width=2)
    nb.alpha_composite(inner, ((gp.width - inner.width) // 2, (gp.height - inner.height) // 2)); ios = nb
    gap = 28; tot = gp.width + gap + ios.width; x0 = (W - tot) // 2
    Sb = canvas(); Sb.alpha_composite(gp, (x0, 1600)); Sb.alpha_composite(ios, (x0 + gp.width + gap, 1600))
    add('X-ebadge', '片尾 商店标', END0 + 2.0, ED - 2.0, save(Sb, 'end_badges'), k={'opacity': kf((0, 0), (.22, 1)), 'y': kf((0, 20), (.28, 0))})
    sfx('u_bubble', END0 + 2.0, .3)
    px, py = bx1 - 90 - 540, (by0 + by1) / 2 + 10 - 960; P0 = 2.3; sc = [[0, 1]]
    for tp in TAPS: r = tp - P0; sc += [[round(r - .04, 3), 1], [round(r + .03, 3), .8], [round(r + .13, 3), 1]]
    add('X-eptr', '片尾 指针', END0 + P0, ED - P0, pf, k={'x': kf((0, px + 140), (.2, px)), 'y': kf((0, py + 240), (.2, py)), 'opacity': kf((0, 0), (.1, 1)), 'scale': sc})
    for i, tp in enumerate(TAPS):
        add(f'X-erip{i % 2 + 1}', '片尾 点击波纹', END0 + tp, min(.4, ED - tp), rf, k={'x': kf((0, px)), 'y': kf((0, py)), 'scale': kf((0, .7), (.4, 2.0)), 'opacity': kf((0, .9), (.4, 0))})
        sfx('u_click', END0 + tp, .55)

TRACKS = [(f'X-sub{i}', f'字幕{i}（跟脸）', 'title') for i in range(5)] + [('X-pon', 'ポンッ', 'title'),
    ('X-cshade', '选项 底部压暗', 'choice'), ('X-cbar', '选项 倒计时', 'choice'), ('X-co1', '选项 ①', 'choice'), ('X-co2', '选项 ②', 'choice'), ('X-co3', '选项 ③', 'choice'), ('X-cs', '选项 选中', 'choice')] + \
    [(f'X-dm{i}', f'选项弹幕{i}', 'choice') for i in range(1, 8)] + [('X-ptr', '选项 指针', 'choice'), ('X-prip', '选项 点击波纹', 'choice'),
    ('X-elogo', '片尾 Logo', 'end'), ('X-ecard', '片尾 标题', 'end'), ('X-ehead', '片尾 文案', 'end'), ('X-ebtn', '片尾 下载按钮', 'end'), ('X-esheen', '片尾 按钮扫光', 'end'),
    ('X-ebadge', '片尾 商店标', 'end'), ('X-eptr', '片尾 指针', 'end'), ('X-erip1', '片尾 波纹1', 'end'), ('X-erip2', '片尾 波纹2', 'end'),
    ('X-ihalo', '开头 光晕', 'title'), ('X-iring', '开头 冲击环', 'title'), ('X-ispark', '开头 星星', 'title'), ('X-ilogo', '开头 Logo', 'title'), ('X-isheen', '开头 Logo扫光', 'title'),
    ('X-flash', '闪光', 'end')]

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith('.png'): os.remove(OUT + f)
    pf, rf = pointer_imgs()
    intro(); transforms(); subs(); choices(pf, rf); endcard(pf, rf)
    used = {t for t, _, _ in TRACKS} | {'V1'}
    assert all(l['track'] in used for l in LAY), {l['track'] for l in LAY} - used
    VB = '包装素材v1/猫娘报恩_弹幕.mp4'
    meta = {'tracks': TRACKS, 'layers': LAY, 'seg': [[a, b, off] for a, b, off in SEG], 'frz': [[s, d, fr] for s, d, fr in CH],
            'end0': END0, 'ed': ED, 'sfx': SFX, 'ticks': TICKS}
    json.dump(meta, open(OUT + 'layers.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('layers', len(LAY), 'sfx', len(SFX), 'end', END1)
