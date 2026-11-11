# MM-JP 五音梗-毒舌講座-迭代（视频_3）包装 v1：沿用 10/22 毒舌講座 gen.py 设计
# 雾粉+奶白甜系 | 毒舌词紫黑故障闪 | 五音徽章只亮 さしす | す句 MiraiMind 粉色强调 → 产品UI 划卡/详情(竹马口播) → 聊天 → 片尾
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.abspath(os.path.join(HERE, '..', '..'))
PK = os.path.join(P, '包装素材v1')
OUT = os.path.join(PK, 'layers'); FR = os.path.join(P, '工程素材', '抽帧')
W, H = 1080, 1920
APP = 'F:/钟海明/2026/2026年10月10日MM-编辑器重构/app/'
NOTO = APP + 'public/fonts/NotoSansJP-Black.otf'
NOTOB = APP + 'public/fonts/NotoSansJP-Bold.otf'
UF = 'C:/Users/zhonghaiming5328/AppData/Local/Microsoft/Windows/Fonts/'
POP = UF + 'MochiyPopOne-Regular.ttf'
DELA = UF + 'DelaGothicOne-Regular.ttf'
ASSET = 'F:/钟海明/MM透明尾板/片尾/片尾文件夹/(素材)/图片/'
WH = (255, 255, 255)
PINK = (255, 132, 170); PINK_L = (255, 206, 222); BERRY = (150, 30, 82); CREAM = (255, 247, 240)
PINKG = [(0, (255, 214, 228)), (.55, (255, 138, 176)), (1, (236, 84, 138))]
VIO = (150, 74, 255); INK = (24, 6, 40); CY = (0, 236, 255); MAG = (255, 0, 168)
VIOG = [(0, (226, 196, 255)), (.5, (162, 96, 255)), (1, (98, 34, 200))]
V = 'a'
FPS = 30
END0 = round(361 / 30, 4)              # 12.0333 原片止
SWF = int(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swf.txt')).read()); SW0 = END0; SWD = round(SWF / 30, 4)   # 产品UI 划卡+详情 7.87s（v2）
CH0 = round(SW0 + SWD, 4); CHD = 3.2   # 产品UI 聊天
EC0 = round(CH0 + CHD, 4); ED = 2.6
VOS = [(round(SW0 + .15, 4), 'p1'), (round(SW0 + 2.97, 4), 'p2'), (round(EC0 + .3, 4), 'p3')]   # 口播：产品 / 剧情 / 片尾
PUSH0 = 11.43                          # 推近手机转场开始
END1 = round(EC0 + ED, 4)
VO0 = VOS[0][0]
INTRO = 4.45

VER = os.environ.get('VER', '_3')      # 版本：'' / _2 / _3 / _4（对应 素材/视频{VER}.mp4）
TM = {
 '_3': dict(T1=[.36,.68,.80,.84,.92,1.00,1.10,1.16,1.42], T2=[1.60,1.80,2.00,2.14,2.30], KT=[2.52,2.76,3.08,3.42,3.80],
            L=[(4.04,4.94,5.40),(6.44,7.10,7.58,7.95),(8.66,9.28,10.24,11.14,11.95)]),
 '_2': dict(T1=[0,.34,.44,.50,.57,.64,.72,.82,1.08], T2=[1.24,1.48,1.72,1.88,2.04], KT=[2.24,2.54,2.96,3.36,3.92],
            L=[(4.12,5.06,5.50),(6.10,6.68,7.18,7.60),(8.48,9.08,10.06,10.98,11.95)]),
 '':   dict(T1=[.30,.58,.68,.76,.83,.90,1.02,1.10,1.36], T2=[1.52,1.73,1.94,2.10,2.26], KT=[2.48,2.74,2.92,3.10,3.64],
            L=[(4.48,5.14,5.60),(6.42,7.00,7.48,7.85),(8.56,9.12,10.00,10.94,11.95)]),
 '_4': dict(T1=[0,.36,.50,.54,.61,.68,.74,.86,1.12], T2=[1.34,1.55,1.76,1.94,2.10], KT=[2.40,2.88,3.13,3.38,3.86],
            L=[(4.54,5.20,5.65),(6.36,6.92,7.38,7.75),(8.52,9.14,10.12,11.00,11.95)]),
 '_5': dict(T1=[0,.40,.50,.58,.65,.72,.84,.92,1.16], T2=[1.34,1.53,1.72,1.88,2.04], KT=[2.26,2.54,2.71,2.88,3.40],
            L=[(4.24,4.96,5.45),(6.12,6.76,7.26,7.65),(8.62,9.22,10.06,10.98,11.95)]),
}[VER]
FR = os.path.join(P, '工程素材', '抽帧' + (VER or '_1'))

# ---------------- 基础 ----------------
FONTS = {}
def font(p, s):
    if (p, s) not in FONTS: FONTS[(p, s)] = ImageFont.truetype(p, s)
    return FONTS[(p, s)]
def canvas(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))
def save(im, name):
    fn = f'layers/{name}_{V}'; im.save(os.path.join(PK, fn + '.png'), compress_level=1); return fn
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def eob(x, s=1.7):
    x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def grad_img(w, h, stops, horiz=False):
    n = w if horiz else h; t = np.linspace(0, 1, max(2, n))
    ch = [np.interp(t, [s[0] for s in stops], [s[1][i] for s in stops]) for i in range(3)]
    g = np.stack(ch, -1).astype(np.uint8)
    g = np.repeat(g[None, :, :], h, 0) if horiz else np.repeat(g[:, None, :], w, 1)
    return Image.fromarray(g, 'RGB')

LAY = []
def add(track, name, start, dur, file, ax=.5, ay=.5, k=None, ext='.png'):
    s = round(start * 30 + 1e-6) / 30; e = round((start + dur) * 30 + 1e-6) / 30
    if e - s < 1 / 30 - 1e-6: return
    LAY.append({'track': track, 'name': name, 'start': round(s, 4), 'dur': round(round(e, 4) - round(s, 4), 4), 'file': file,
                'ax': round(ax, 4), 'ay': round(ay, 4), 'k': k or {}, 'ext': ext})
def kf(*pts): return [[round(p[0], 3), round(p[1], 3)] + ([p[2]] if len(p) > 2 else []) for p in pts]
def kmerge(lst):
    out = []
    for p in sorted(lst):
        if not out or p[0] > out[-1][0] + .005: out.append(p)
    return kf(*out)
SFX = []
def sfx(name, t, v): SFX.append([name, round(t, 3), v])

def _paste(L, im, x, y):
    bx0, by0 = max(0, x), max(0, y); bx1, by1 = min(L.width, x + im.width), min(L.height, y + im.height)
    if bx1 <= bx0 or by1 <= by0: return
    L.alpha_composite(im.crop((bx0 - x, by0 - y, bx1 - x, by1 - y)), (bx0, by0))
def mask_of(xy, s, f, anchor='ls', stroke=0):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text(xy, s, font=f, fill=255, anchor=anchor, stroke_width=stroke); return m
def sweet_text(L, xy, s, f, anchor='ls', grad=None, fill=WH, stroke=9, sc=BERRY, glow=PINK, ga=.55, a=1.):
    """甜系字：粉色柔光 + 莓红粗描边 + 白/粉渐变填充"""
    ms = mask_of(xy, s, f, anchor, stroke); m = mask_of(xy, s, f, anchor)
    bb = ms.getbbox()
    if not bb: return
    pad = 40; box = (bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)
    c = ms.crop(box)
    if glow:
        g = Image.new('RGBA', c.size, glow + (0,)); g.putalpha(c.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(min(255, v * ga * a)))); _paste(L, g, box[0], box[1] + 6)
    k = Image.new('RGBA', c.size, sc + (0,)); k.putalpha(c.point(lambda v: int(v * a))); _paste(L, k, box[0], box[1])
    cm = m.crop(box)
    col = grad_img(c.width, c.height, grad).convert('RGBA') if grad else Image.new('RGBA', c.size, fill + (255,))
    if grad:   # 渐变只覆盖字高
        bb2 = cm.getbbox(); gg = grad_img(c.width, max(2, bb2[3] - bb2[1]), grad).convert('RGBA'); col = Image.new('RGBA', c.size, grad[-1][1] + (255,)); col.paste(gg, (0, bb2[1]))
    col.putalpha(cm.point(lambda v: int(v * a))); _paste(L, col, box[0], box[1])
def blit(dst, spr, cx, cy, sc=1., a=1., rot=0.):
    if a <= .003 or sc <= .01: return
    s = spr if abs(sc - 1) < 1e-3 else spr.resize((max(1, int(spr.width * sc)), max(1, int(spr.height * sc))), Image.BILINEAR)
    if abs(rot) > .05: s = s.rotate(rot, Image.BICUBIC, expand=True)
    if a < .999:
        arr = np.array(s); arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8); s = Image.fromarray(arr)
    _paste(dst, s, int(round(cx - s.width / 2)), int(round(cy - s.height / 2)))
def crop_spr(L):
    bb = L.getbbox(); return L.crop(bb), (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
def tint(spr, rgb, a=1.):
    arr = np.array(spr); arr[..., 0], arr[..., 1], arr[..., 2] = rgb; arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8); return Image.fromarray(arr)
def tint_alpha(spr, a):
    arr = np.array(spr); arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8); return Image.fromarray(arr)
def glow_of(spr, rgb, r, a=1., pad=60):
    m = Image.new('L', (spr.width + pad * 2, spr.height + pad * 2), 0); m.paste(spr.split()[3], (pad, pad))
    m = m.filter(ImageFilter.GaussianBlur(r)); g = Image.new('RGBA', m.size, rgb + (0,)); g.putalpha(m.point(lambda v: int(min(255, v * a)))); return g
def disc(r, rgb, soft=.6):
    n = int(r * 4) + 4; g = Image.new('L', (n, n), 0); ImageDraw.Draw(g).ellipse([n / 2 - r, n / 2 - r, n / 2 + r, n / 2 + r], fill=255)
    g = g.filter(ImageFilter.GaussianBlur(max(.5, r * soft))); s = Image.new('RGBA', (n, n), rgb + (0,)); s.putalpha(g); return s
def star(r, rgb):
    n = int(r * 2.4) + 4; c = n / 2; S = 4; m = Image.new('L', (n * S, n * S), 0)
    pts = []
    for i in range(8):
        ang = -math.pi / 2 + i * math.pi / 4; rr = r if i % 2 == 0 else r * .32; pts.append(((c + math.cos(ang) * rr) * S, (c + math.sin(ang) * rr) * S))
    ImageDraw.Draw(m).polygon(pts, fill=255); m = m.resize((n, n), Image.LANCZOS)
    s = Image.new('RGBA', (n, n), rgb + (0,)); s.putalpha(m); return s
def heart(r, rgb):
    n = int(r * 2.4) + 4; S = 4; m = Image.new('L', (n * S, n * S), 0); d = ImageDraw.Draw(m); c = n * S / 2; R = r * S
    d.ellipse([c - R, c - R * .75, c, c + R * .15], fill=255); d.ellipse([c, c - R * .75, c + R, c + R * .15], fill=255)
    d.polygon([(c - R * .97, c - R * .2), (c + R * .97, c - R * .2), (c, c + R * .95)], fill=255)
    m = m.resize((n, n), Image.LANCZOS); s = Image.new('RGBA', (n, n), rgb + (0,)); s.putalpha(m); return s
def rr_mask(w, h, r):
    S = 4; m = Image.new('L', (w * S, h * S), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=r * S, fill=255)
    return m.resize((w, h), Image.LANCZOS)

_FC = {}
def frame(t):
    i = max(0, min(288, int(t * 24 + 1e-6)))
    if i not in _FC:
        if len(_FC) > 40: _FC.clear()
        _FC[i] = Image.open(os.path.join(FR, f'{i + 1:04d}.jpg')).convert('RGB')
    return _FC[i]

def logo_row(icon_h=104, wm_h=44, y=300):
    icon = Image.open(ASSET + 'LOGO-256x256-圆角.png').convert('RGBA').resize((icon_h, icon_h), Image.LANCZOS)
    wm = Image.open(APP + 'public/assets/product-logo.png').convert('RGBA'); wm = wm.resize((int(wm.width * wm_h / wm.height), wm_h), Image.LANCZOS)
    tot = icon_h + 22 + wm.width; x = 540 - tot / 2
    L = canvas(); _paste(L, glow_of(icon, (90, 20, 50), 10, .5, 30), int(x) - 30, int(y - icon_h / 2) - 30 + 6)
    L.alpha_composite(icon, (int(x), int(y - icon_h / 2))); x2 = x + icon_h + 22
    _paste(L, glow_of(wm, (90, 20, 50), 6, .6, 20), int(x2) - 20, int(y - wm_h / 2) - 20 + 3)
    L.alpha_composite(wm, (int(x2), int(y - wm_h / 2)))
    return L

# ---------------- 五音徽章（粉色泡泡） ----------------
KANA = ['さ', 'し', 'す', 'せ', 'そ']
KT = TM['KT']           # 开头念出假名（视频_3 ASR）
LINE_T = [TM['L'][0][0], TM['L'][1][0], TM['L'][2][0]]                   # さ/し/す 句开始（徽章点亮）；せ・そ 不亮
SY = 196; SX = [540 + (k - 2) * 150 for k in range(5)]; SR_ = 54; SFS = 64
def slot_img(k, lit, R=SR_, fs=SFS):
    """lit: 0=暗（奶白半透明）1=粉色点亮 2=紫色（毒舌）"""
    n = int(R * 4); c = n // 2; L = Image.new('RGBA', (n, n), (0, 0, 0, 0)); S = 4
    m = Image.new('L', (n * S, n * S), 0); ImageDraw.Draw(m).ellipse([(c - R) * S, (c - R) * S, (c + R) * S, (c + R) * S], fill=255); m = m.resize((n, n), Image.LANCZOS)
    ring = Image.new('L', (n * S, n * S), 0); ImageDraw.Draw(ring).ellipse([(c - R) * S, (c - R) * S, (c + R) * S, (c + R) * S], outline=255, width=int(R / 12) * S); ring = ring.resize((n, n), Image.LANCZOS)
    sh = Image.new('RGBA', (n, n), (90, 20, 50, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(R / 5)).point(lambda v: int(v * .35))); L.alpha_composite(sh, (0, int(R / 12)))
    if lit:
        g = Image.new('RGBA', (n, n), (PINK if lit == 1 else VIO) + (0,)); g.putalpha(m.filter(ImageFilter.GaussianBlur(R / 3.5)).point(lambda v: int(v * .8))); L.alpha_composite(g)
        f_ = grad_img(n, n, PINKG if lit == 1 else VIOG).convert('RGBA'); f_.putalpha(m); L.alpha_composite(f_)
        hl = Image.new('L', (n * S, n * S), 0); ImageDraw.Draw(hl).ellipse([(c - R * .62) * S, (c - R * .82) * S, (c + R * .1) * S, (c - R * .42) * S], fill=255); hl = hl.resize((n, n), Image.LANCZOS).filter(ImageFilter.GaussianBlur(R / 14))
        hh = Image.new('RGBA', (n, n), (255, 255, 255, 0)); hh.putalpha(hl.point(lambda v: int(v * .55))); L.alpha_composite(hh)
        r_ = Image.new('RGBA', (n, n), (255, 255, 255, 0)); r_.putalpha(ring); L.alpha_composite(r_)
        tc, ta = WH, 1.
    else:
        f_ = Image.new('RGBA', (n, n), CREAM + (0,)); f_.putalpha(m.point(lambda v: int(v * .55))); L.alpha_composite(f_)
        r_ = Image.new('RGBA', (n, n), PINK + (0,)); r_.putalpha(ring.point(lambda v: int(v * .8))); L.alpha_composite(r_)
        tc, ta = PINK, .9
    t = Image.new('L', (n, n), 0); ImageDraw.Draw(t).text((c, c + R * .04), KANA[k], font=font(POP, fs), fill=255, anchor='mm')
    if lit:
        s2 = Image.new('RGBA', (n, n), (BERRY if lit == 1 else INK) + (0,)); s2.putalpha(t.filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * .55))); L.alpha_composite(s2, (0, 2))
    tt_ = Image.new('RGBA', (n, n), tc + (0,)); tt_.putalpha(t.point(lambda v: int(v * ta))); L.alpha_composite(tt_)
    return L
SLOT = {(k, l): slot_img(k, l) for k in range(5) for l in (0, 1, 2)}
def row_img(lits, y=SY):
    L = canvas()
    for k in range(5): blit(L, SLOT[(k, lits[k])], SX[k], y)
    return L

# ---------------- 开头：开场字幕即标题（逐帧透明叠加 0–5.0） ----------------
T1 = list(zip('リアクション三倍で', TM['T1']))
T2 = list(zip('できる女の', TM['T2']))
EMPH1 = {'三', '倍'}
BIG_R = 84; BIG_Y = 1660; BIG_X = [540 + (k - 2) * 196 for k in range(5)]
def line_chars(items, f, fe, y, track=2):
    ws = [(fe if c in EMPH1 else f).getlength(c) for c, _ in items]; tw = sum(ws) + track * (len(items) - 1); x = 540 - tw / 2; out = []
    for (c, t), w in zip(items, ws):
        L = canvas(); emph = c in EMPH1
        sweet_text(L, (x, y), c, fe if emph else f, grad=PINKG if emph else None, stroke=11 if emph else 9)
        spr, cx, cy = crop_spr(L); out.append((spr, cx, cy, t, emph)); x += w + track
    return out
def intro():
    N = int(round(INTRO * FPS)); rng = np.random.default_rng(3)
    logo, lcx, lcy = crop_spr(logo_row(y=300))
    c1 = line_chars(T1, font(POP, 96), font(POP, 128), 1330)
    c2 = line_chars(T2, font(POP, 104), font(POP, 104), 1490)
    big = [slot_img(k, 1, BIG_R, 104) for k in range(5)]
    bglow = [glow_of(b, PINK, 22, .7) for b in big]
    stars = {r: star(r, (255, 255, 255)) for r in (8, 11, 14, 18)}; pst = {r: star(r, PINK_L) for r in (8, 11, 14)}
    spk = {k: [(rng.uniform(0, 6.283), rng.uniform(110, 230), rng.choice([8, 11, 14, 18]), rng.uniform(0, 1)) for _ in range(9)] for k in range(5)}
    hearts = [(rng.uniform(80, 1000), rng.uniform(1100, 1900), rng.uniform(.6, 1.2), rng.uniform(0, 4.2), rng.uniform(12, 24)) for _ in range(14)]
    hsp = {r: heart(r, PINK_L) for r in range(12, 25)}
    yy = np.arange(H, dtype=np.float32)[:, None]
    for fi in range(N):
        T = fi / FPS; L = canvas()
        out = eio((T - 3.80) / .25)         # 字退场
        # 底部柔粉渐变托底（可读性）
        if fi == 0 or True:
            a_bg = clamp(T / .4) * (1 - eio((T - 3.9) / .4))
            if a_bg > .01:
                g = np.clip((yy - 1150) / 520, 0, 1) ** 1.3 * .55 * a_bg
                arr = np.zeros((H, W, 4), np.uint8); arr[..., 0], arr[..., 1], arr[..., 2] = 120, 30, 70; arr[..., 3] = (np.repeat(g, W, 1) * 255).astype(np.uint8)
                L.alpha_composite(Image.fromarray(arr))
        # 漂浮小爱心
        for x0, y0, sp, ph, r in hearts:
            u = T - ph * .5
            if 0 < u < 3.5:
                a = clamp(u / .4) * clamp((3.5 - u) / .5) * .7 * (1 - out)
                blit(L, hsp[int(r)], x0 + 30 * math.sin(u * 2 + ph), y0 - 140 * u * sp, 1, a, 12 * math.sin(u * 3 + ph))
        # Logo
        if T >= .05:
            p = (T - .05) / .45
            blit(L, logo, lcx, lcy - 18 * (1 - ease(p)), .7 + .3 * eob(p), clamp(p * 2.5) * (1 - eio((T - 3.8) / .4)))
        # 两行字：逐字弹跳出现
        for cs in (c1, c2):
            for spr, cx, cy, t, emph in cs:
                p = (T - t + .03) / .26
                if p < 0: continue
                sc = .25 + .75 * eob(p, 2.6) if p < 1 else 1 + (.05 * math.sin((T - t) * 7) if emph else 0)
                rot = (8 if emph else 5) * (1 - ease(p)) * (1 if int(cx) % 2 else -1)
                dy = -36 * (1 - ease(p)) - 40 * out
                blit(L, spr, cx, cy + dy, sc * (1 - .1 * out), clamp(p * 3) * (1 - out), rot)
        # さしすせそ 泡泡：弹出 → 4.70 飞向顶部徽章位
        for k in range(5):
            t = KT[k]; p = (T - t + .02) / .22
            if p < 0: continue
            fly = eio((T - (KT[4] + .10) - k * .04) / .32)
            cx, cy = BIG_X[k], BIG_Y
            if fly <= 0:
                sc = .2 + .8 * eob(p, 3.0) if p < 1 else 1 + .04 * math.sin((T - t) * 9)
                blit(L, bglow[k], cx, cy, sc, .55 * clamp(p * 2))
                blit(L, big[k], cx, cy, sc, clamp(p * 3), 6 * (1 - ease(p)))
                u = T - t
                if 0 <= u < .55:
                    for ang, d, r, ph in spk[k]:
                        dd = d * ease(u / .4); a = clamp(1 - u / .55)
                        blit(L, stars[r], cx + math.cos(ang) * dd, cy + math.sin(ang) * dd * .9 - 30 * u, 1 - .4 * u, a, u * 200)
            else:
                tx, ty = SX[k], SY; arc = 120 * math.sin(math.pi * fly)
                tsc = SR_ / BIG_R; sc = 1 + (tsc - 1) * fly
                for gi in range(1, 4):
                    fg = max(0, fly - gi * .08)
                    blit(L, big[k], cx + (tx - cx) * fg, cy + (ty - cy) * fg - 120 * math.sin(math.pi * fg), 1 + (tsc - 1) * fg, .2 * (1 - fly) / gi)
                blit(L, big[k], cx + (tx - cx) * fly, cy + (ty - cy) * fly - arc, sc, 1 - clamp((fly - .85) / .15))
        add('X-intro', '开头 逐帧（标题字幕+五音泡泡）', T, 1 / FPS, save(L, f'intro_{fi:03d}'))
    sfx('u_pop2', .06, .3)
    sfx('u_air', .66, .35)
    for _, t in T1[::3] + T2[::2]: sfx('u_pop2', t, .16)
    for t in KT: sfx('u_pop2', t, .42)
    sfx('s_whoosh', 3.86, .4)

# ---------------- 徽章行（INTRO → 原片止） ----------------
def badges():
    D0 = END0 - INTRO + .3
    add('X-brow', '五音 徽章行（暗）', INTRO, D0, save(row_img([0] * 5), 'row_dim'), k={'opacity': kf((0, 0), (.08, 1), (D0 - .3, 1), (D0, 0))})
    for k in range(len(LINE_T)):
        L = canvas(); blit(L, SLOT[(k, 1)], SX[k], SY)
        s0 = max(LINE_T[k], INTRO); D = END0 - s0 + .3
        add(f'X-blit{k + 1}', f'五音 徽章「{KANA[k]}」点亮', s0, D, save(L, f'slot_lit{k}'), ax=SX[k] / W, ay=SY / H,
            k={'scale': kf((0, 1.7), (.12, .88), (.22, 1.08), (.32, 1)), 'opacity': kf((0, .5), (.05, 1), (D - .3, 1), (D, 0))})
        sfx('u_pop2', s0, .3)

# ---------------- 字幕：甜系；毒舌重点词=紫黑故障字 ----------------
LINES = [
    ([('さっさと', TM['L'][0][0]), ('*消えろよ', TM['L'][0][1])], TM['L'][0][2]),
    ([('職歴も', TM['L'][1][0]), ('学歴も', TM['L'][1][1]), ('*ないね', TM['L'][1][2])], TM['L'][1][3]),
    ([('すごいね、', TM['L'][2][0]), ('+MiraiMindも', TM['L'][2][1]), ('\n使ったことないのに', TM['L'][2][2]), ('\n流行り語るんだ', TM['L'][2][3])], TM['L'][2][4]),
]
SUBY = 1560
def layout(chunks, suby=None):
    suby = suby or SUBY
    rows, cur = [], []
    for i, (s, t) in enumerate(chunks):
        if s.startswith('\n') and cur: rows.append(cur); cur = []
        cur.append(i)
    rows.append(cur)
    items = []
    for s, t in chunks:
        s = s.lstrip('\n'); kind = 'n'
        if s[0] in '*+': kind = 'bad' if s[0] == '*' else 'sweet'; s = s[1:]
        f = font(DELA, 98) if kind == 'bad' else font(POP, 86 if kind == 'sweet' else 70)
        items.append({'s': s, 't': t, 'kind': kind, 'f': f})
    RH = 118; y = suby - (len(rows) - 1) * RH / 2
    for r in rows:
        tw = sum(items[i]['f'].getlength(items[i]['s']) for i in r) + 10 * (len(r) - 1); x = 540 - tw / 2
        for i in r: items[i]['xy'] = (x, y + 34); x += items[i]['f'].getlength(items[i]['s']) + 10
        y += RH
    return items
def glitch_text(L, xy, s, f, a=1.):
    """紫黑故障字：青/品红错位 + 墨紫粗描边 + 白→淡紫填充 + 横向切片"""
    m = mask_of(xy, s, f); ms = mask_of(xy, s, f, stroke=10)
    bb = ms.getbbox(); pad = 50; box = (bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)
    G = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0))
    c = ms.crop(box); cm = m.crop(box)
    g = Image.new('RGBA', c.size, VIO + (0,)); g.putalpha(c.filter(ImageFilter.GaussianBlur(20)).point(lambda v: int(min(255, v * .9)))); G.alpha_composite(g)
    for col, dx in ((CY, -7), (MAG, 7)):
        sp = Image.new('RGBA', c.size, col + (0,)); sp.putalpha(c.point(lambda v: int(v * .85))); G.alpha_composite(sp, (dx, 0)) if dx > 0 else G.alpha_composite(sp.crop((-dx, 0, sp.width, sp.height)), (0, 0))
    o2 = Image.new('RGBA', c.size, (255, 255, 255, 0)); o2.putalpha(c.filter(ImageFilter.MaxFilter(5)).point(lambda v: int(v * .9))); G.alpha_composite(o2)
    k = Image.new('RGBA', c.size, INK + (0,)); k.putalpha(c); G.alpha_composite(k)
    bb2 = cm.getbbox(); gg = grad_img(c.width, bb2[3] - bb2[1], [(0, (255, 255, 255)), (.65, (250, 244, 255)), (1, (228, 206, 255))]).convert('RGBA')
    col = Image.new('RGBA', c.size, (228, 206, 255, 255)); col.paste(gg, (0, bb2[1])); col.putalpha(cm); G.alpha_composite(col)
    # 横向切片错位
    rng = np.random.default_rng(len(s) * 7 + int(xy[1]))
    arr = np.array(G)
    for _ in range(2):
        y0 = int(rng.uniform(bb2[1], bb2[3] - 10)); hh = int(rng.uniform(4, 9)); dx = int(rng.choice([-1, 1]) * rng.uniform(4, 8))
        arr[y0:y0 + hh] = np.roll(arr[y0:y0 + hh], dx, axis=1)
    G = Image.fromarray(arr)
    if a < .999: G = tint_alpha(G, a)
    _paste(L, G, box[0], box[1])
def sub_text(L, it):
    if it['kind'] == 'bad': glitch_text(L, it['xy'], it['s'], it['f'])
    elif it['kind'] == 'sweet': sweet_text(L, it['xy'], it['s'], it['f'], grad=PINKG, stroke=10, ga=.75)
    else: sweet_text(L, it['xy'], it['s'], it['f'], stroke=8, ga=.45)
def subs():
    for li, (chunks, end) in enumerate(LINES):
        nxt = LINES[li + 1][0][0][1] if li + 1 < len(LINES) else END0
        hide = min(nxt - .04, end + .6, END0)
        items = layout(chunks); tag = f'sub{li}'
        for i, it in enumerate(items):
            L = canvas(); sub_text(L, it); bb = L.getbbox(); D = hide - it['t']
            k = {'opacity': kf((0, 0), (.08, 1), (max(.11, D - .12), 1), (D, 0)), 'y': kf((0, 16), (.16, 0))}
            ax, ay = (bb[0] + bb[2]) / 2 / W, (bb[1] + bb[3]) / 2 / H
            if it['kind'] == 'bad':
                k['scale'] = kf((0, 1.7), (.1, .9), (.2, 1.05), (.3, 1))
                k['x'] = kf((0, 0), (.05, -12), (.1, 10), (.15, -7), (.2, 5), (.26, 0))
            elif it['kind'] == 'sweet':
                k['scale'] = kf((0, .4), (.16, 1.1), (.28, .97), (.38, 1))
            else:
                k['scale'] = kf((0, .7), (.14, 1.05), (.24, 1))
            add(f'X-sub{i + 1}', '字幕 ' + it['s'], it['t'], D, save(L, f'{tag}_{i}'), ax=ax, ay=ay, k=k)
            if it['kind'] == 'n': sfx('u_pop2', it['t'], .12)

# ---------------- 毒舌瞬间：紫黑故障闪（逐帧） ----------------
GL_T = [TM['L'][0][1], TM['L'][1][2]]
MM_T = TM['L'][2][1]   # MiraiMind 粉光
def glitch_frame(T, rng, strength):
    """把原片该帧做切片错位 + RGB 分离 + 紫黑调色 + 扫描线（不透明整帧）"""
    im = np.asarray(frame(T)).astype(np.float32)
    lum = im @ np.array([.3, .59, .11], np.float32)
    duo = (lum[..., None] / 255.) ** 1.1
    col = np.array(INK, np.float32) * (1 - duo) + np.array([214, 160, 255], np.float32) * duo
    out = im * (1 - .78 * strength) + col * .78 * strength
    r = np.roll(out[..., 0], int(14 * strength), 1); b = np.roll(out[..., 2], -int(14 * strength), 1)
    out[..., 0] = r; out[..., 2] = b
    for _ in range(int(8 * strength) + 2):
        y0 = int(rng.uniform(0, H - 40)); hh = int(rng.uniform(12, 90)); dx = int(rng.uniform(-90, 90) * strength)
        out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], dx, 1)
        if rng.uniform() < .4: out[y0:y0 + hh] = out[y0:y0 + hh] * .5 + np.array(rng.choice([0, 1]) and CY or MAG, np.float32) * .5
    out[::4] *= .72
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert('RGBA')
SHAKE = []   # 毒舌瞬间：原片抖动（patch.mjs 写进 V1 关键帧）
def glitches():
    """v2：去掉全屏故障，改为 原片抖动 + 四周淡紫暗角一闪（中间人脸不受影响）"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - 540) / 540) ** 2 + ((yy - 960) / 960) ** 2)
    vm = np.clip((d - .7) / .55, 0, 1) ** 1.6
    arr = np.zeros((H, W, 4), np.uint8); arr[..., :3] = (60, 20, 110); arr[..., 3] = (vm * 200).astype(np.uint8)
    vig = save(Image.fromarray(arr), 'vig_violet')
    for gi, t0 in enumerate(GL_T):
        add('X-glitch', f'毒舌 暗角闪{gi + 1}', t0 - .02, .5, vig, k={'opacity': kf((0, 0), (.04, .55), (.5, 0))})
        SHAKE.append(round(t0 - .02, 3))
        sfx('s_glitch', t0 - .02, .3)
    add('X-flash', 'MiraiMind 粉光', MM_T - .03, .6, PINKF, k={'opacity': kf((0, 0), (.08, .28), (.6, 0))})
    sfx('u_air', MM_T - .05, .4)
    # 转场：推近手机 + 粉白闪 → 进 MiraiMind 首页
    add('X-flash', '转场 粉白闪入', END0 - .25, .25, PINKF, k={'opacity': kf((0, 0), (.25, .95))})
    add('X-flash2', '转场 粉白闪出', END0, .4, PINKF, k={'opacity': kf((0, .95), (.4, 0))})
    sfx('s_whoosh', PUSH0 + .1, .45); sfx('u_flash', END0 - .05, .4)
    # 产品口播字幕（划卡段）
    PAGES = [(VOS[0][0], [('ミラマイでは、', 0.0), ('\n+全て貴方の思い通り', .75)], 2.75),
             (VOS[1][0], [('誘い待ちはもう不要。', 0.0)], 1.6),
             (VOS[1][0], [('+毒舌な幼馴染', 1.74), ('から、', 2.95), ('\n+グイグイ来る', 3.16)], 4.5)]
    n = 0
    for pi, (t0, ch, te) in enumerate(PAGES):
      its = layout(ch, 1560); ims = []
      for it in its: L = canvas(); sub_text(L, it); ims.append(L)
      bbs = [L.getbbox() for L in ims]; x0 = min(b[0] for b in bbs) - 54; y0 = min(b[1] for b in bbs) - 30; x1 = max(b[2] for b in bbs) + 54; y1 = max(b[3] for b in bbs) + 30
      P = canvas(); sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 14, x1, y1 + 14), 46, fill=(20, 0, 30, 150)); P.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
      ImageDraw.Draw(P).rounded_rectangle((x0, y0, x1, y1), 46, fill=(58, 14, 62, 205), outline=(255, 160, 205, 235), width=5)
      ps = t0 + its[0]['t'] - .08; pd = t0 + te - ps
      add('X-plate', '口播字幕底板', ps, pd, save(P, f'vplate{pi}'), ax=(x0 + x1) / 2 / W, ay=(y0 + y1) / 2 / H, k={'opacity': kf((0, 0), (.1, 1), (pd - .12, 1), (pd, 0)), 'scale': kf((0, .82), (.14, 1.04), (.22, 1))})
      for k, it in enumerate(its):
        n += 1; i = n - 1
        L = ims[k]; bb = bbs[k]; ts = t0 + it['t']; D = t0 + te - ts
        kk = {'opacity': kf((0, 0), (.1, 1), (D - .12, 1), (D, 0)), 'y': kf((0, 14), (.16, 0))}
        if it['kind'] == 'sweet': kk['scale'] = kf((0, 1.4), (.12, .94), (.22, 1.03), (.32, 1))
        add(f'X-sub{k + 1}', '口播字幕 ' + it['s'], ts, D, save(L, f'vo{pi}_{i}'), ax=(bb[0] + bb[2]) / 2 / W, ay=(bb[1] + bb[3]) / 2 / H, k=kk)
def glitches_old():
    rng = np.random.default_rng(9)
    vign = None
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - 540) / 540) ** 2 + ((yy - 960) / 960) ** 2)
    vmask = np.clip((d - .55) / .6, 0, 1) ** 1.4
    for gi, t0 in enumerate(GL_T):
        st = t0 - .02; n = 14
        for fi in range(n):
            u = fi / FPS
            if fi < 4:
                im = glitch_frame(t0 + u, rng, [1, .8, 1, .55][fi])
            else:
                a = (1 - (fi - 4) / (n - 4)) ** 1.5
                arr = np.zeros((H, W, 4), np.uint8); arr[..., :3] = INK; arr[..., 3] = (vmask * 210 * a).astype(np.uint8)
                im = Image.fromarray(arr); dr = ImageDraw.Draw(im)
                for _ in range(int(5 * a) + 1):
                    y0 = rng.uniform(0, H); hh = rng.uniform(4, 22); c = [VIO, CY, MAG][int(rng.uniform(0, 3))]
                    dr.rectangle([rng.uniform(-200, 600), y0, rng.uniform(500, 1300), y0 + hh], fill=c + (int(110 * a),))
            add('X-glitch', f'毒舌故障闪{gi + 1}', st + u, 1 / FPS, save(im, f'gl{gi}_{fi:02d}'))
        sfx('s_glitch', st, .55)

# ---------------- 片尾 ----------------
END_COPY = ('ガチャより', '危険')
BTN = '今すぐダウンロード'
def pointer_imgs():
    L = canvas(); r = 40
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([540 - r - 6, 960 - r, 540 + r + 6, 960 + r + 14], fill=110); g = g.filter(ImageFilter.GaussianBlur(12))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(g); L.alpha_composite(sh)
    d = ImageDraw.Draw(L); d.ellipse([540 - r, 960 - r, 540 + r, 960 + r], fill=(255, 255, 255, 95), outline=(255, 255, 255, 220), width=3)
    d.ellipse([540 - 8, 960 - 8, 540 + 8, 960 + 8], fill=(255, 255, 255, 240))
    R = canvas(); ImageDraw.Draw(R).ellipse([540 - 50, 960 - 50, 540 + 50, 960 + 50], outline=(255, 255, 255, 220), width=4)
    return save(L, 'pointer'), save(R, 'ripple')
def endcard():
    E0 = EC0
    pf, rf = pointer_imgs()
    im = frame(11.9)
    b = im.filter(ImageFilter.GaussianBlur(5)); b = ImageEnhance.Brightness(b).enhance(.62)
    a = np.asarray(b).astype(np.float32); yy = np.arange(H, dtype=np.float32)[:, None, None]
    shade = np.clip((yy - 760) / 620, 0, 1) * .7 + np.clip(1 - yy / 560, 0, 1) * .5
    a = a * (1 - shade) + np.array([70, 18, 44], np.float32) * shade
    add('V1', '片尾 背景', E0, ED, save(Image.fromarray(a.astype(np.uint8)).convert('RGBA'), 'end_bg'), k={'scale': kf((0, 1.0), (ED, 1.06))})
    add('X-flash', '片尾 闪光', E0, .35, FLASH, k={'opacity': kf((0, .7), (.35, 0))})
    sfx('u_flash', E0 - .02, .4)
    Lg = logo_row(y=250)
    add('X-elogo', '片尾 Logo', E0 + .05, ED - .05, save(Lg, 'end_logo'), k={'opacity': kf((0, 0), (.25, 1)), 'y': kf((0, -20), (.3, 0))})
    rows = canvas(); blit(rows, row_img([1] * 5), 540, 960 + 470 - SY)
    add('X-erow', '片尾 五音', E0 + .15, ED - .15, save(rows, 'end_row'), ay=470 / H, k={'opacity': kf((0, 0), (.25, 1)), 'scale': kf((0, .85), (.3, 1))})
    sfx('u_pop2', E0 + .25, .3)
    L = canvas(); sweet_text(L, (540, 1010), END_COPY[0], font(POP, 100), anchor='ms', stroke=10)
    add('X-ecopy1', '片尾 文案1', E0 + .25, ED - .25, save(L, 'end_copy1'), ay=980 / H, k={'opacity': kf((0, 0), (.25, 1)), 'y': kf((0, 24), (.3, 0))})
    L = canvas(); sweet_text(L, (540, 1230), END_COPY[1], font(POP, 210), anchor='ms', grad=PINKG, stroke=15, ga=.85)
    add('X-ecopy2', '片尾 文案2', E0 + .4, ED - .4, save(L, 'end_copy2'), ay=1150 / H, k={'opacity': kf((0, 0), (.2, 1)), 'scale': kf((0, 1.25), (.14, .95), (.26, 1))})
    sfx('u_pop2', E0 + .4, .4)
    bx0, by0, bx1, by1 = 170, 1340, 910, 1476; bw, bh = bx1 - bx0, by1 - by0
    L = canvas()
    G = Image.new('L', (W, H), 0); ImageDraw.Draw(G).rounded_rectangle([bx0, by0 + 8, bx1, by1 + 8], radius=68, fill=130)
    G = G.filter(ImageFilter.GaussianBlur(30)); gc = Image.new('RGBA', (W, H), PINK + (0,)); gc.putalpha(G); L.alpha_composite(gc)
    btn = grad_img(bw, bh, [(0, (255, 160, 192)), (.5, (250, 104, 152)), (1, (214, 60, 118))]).convert('RGBA')
    sheen = np.clip(1 - np.arange(bh, dtype=np.float32) / (bh * .5), 0, 1) ** 1.6 * .25
    ba = np.asarray(btn).astype(np.float32); ba[..., :3] += (255 - ba[..., :3]) * sheen[:, None, None]; btn = Image.fromarray(np.clip(ba, 0, 255).astype(np.uint8))
    mk = rr_mask(bw, bh, 68); btn.putalpha(mk); L.alpha_composite(btn, (bx0, by0))
    ring = Image.new('L', (bw * 4, bh * 4), 0); ImageDraw.Draw(ring).rounded_rectangle([2, 2, bw * 4 - 3, bh * 4 - 3], radius=68 * 4, outline=255, width=8); ring = ring.resize((bw, bh), Image.LANCZOS)
    rr = Image.new('RGBA', (bw, bh), (255, 255, 255, 0)); rr.putalpha(ring.point(lambda v: int(v * .7))); L.alpha_composite(rr, (bx0, by0))
    tm = mask_of((540, (by0 + by1) / 2 + 2), BTN, font(POP, 60), 'mm')
    ts = Image.new('RGBA', (W, H), BERRY + (0,)); ts.putalpha(tm.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * .5))); L.alpha_composite(ts, (0, 3))
    tw_ = Image.new('RGBA', (W, H), WH + (0,)); tw_.putalpha(tm); L.alpha_composite(tw_)
    BS = E0 + .55; TAPS = [1.25, 1.55, 1.85, 2.4, 2.7]
    bsc = [[0, .7], [.18, 1.05], [.28, 1]]
    for tp in TAPS: r = E0 + tp - BS; bsc += [[round(r - .04, 3), 1], [round(r + .04, 3), .94], [round(r + .16, 3), 1]]
    bsc.sort(key=lambda v: v[0])
    add('X-ebtn', '片尾 下载按钮', BS, END1 - BS, save(L, 'end_btn'), ay=(by0 + by1) / 2 / H, k={'scale': bsc, 'opacity': kf((0, 0), (.12, 1))})
    sfx('u_pop2', BS, .4)
    bma = np.asarray(mk).astype(np.float32) / 255
    yy, xx = np.mgrid[0:bh, 0:bw]
    for j in range(8):
        c = -80 + j * 130; band = np.clip(1 - np.abs((xx + (yy - 70) * .5) - c) / 60, 0, 1) ** 2 * .5
        S = canvas(); s_ = Image.new('RGBA', (bw, bh), (255, 255, 255, 0)); s_.putalpha(Image.fromarray((bma * band * 255).astype(np.uint8))); S.alpha_composite(s_, (bx0, by0))
        fn = save(S, f'end_sheen{j}')
        for st in (E0 + .85, E0 + 2.05):
            add('X-esheen', '片尾 按钮扫光', st + j / 15, 1 / 15, fn)
    gp = Image.open(ASSET + 'Google_Play_Badge_JA.svg.png').convert('RGBA'); gp = gp.resize((int(gp.width * 88 / gp.height), 88), Image.LANCZOS)
    ios = Image.open(ASSET + 'ios_badge.png').convert('RGBA'); ios = ios.crop(ios.split()[3].getbbox()); ios = ios.resize((int(ios.width * 88 / ios.height), 88), Image.LANCZOS)
    inner = ios.crop((8, 6, ios.width - 8, ios.height - 6))
    nb = Image.new('RGBA', gp.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(nb)
    bd.rounded_rectangle([0, 0, gp.width - 1, gp.height - 1], radius=14, fill=(0, 0, 0, 255), outline=(166, 166, 166, 255), width=2)
    nb.alpha_composite(inner, ((gp.width - inner.width) // 2, (gp.height - inner.height) // 2)); ios = nb
    gap = 28; tot = gp.width + gap + ios.width; x0 = (W - tot) // 2
    Sb = canvas(); Sb.alpha_composite(gp, (x0, 1580)); Sb.alpha_composite(ios, (x0 + gp.width + gap, 1580))
    add('X-ebadge', '片尾 商店标', E0 + .7, ED - .7, save(Sb, 'end_badges'), k={'opacity': kf((0, 0), (.22, 1)), 'y': kf((0, 20), (.28, 0))})
    px, py = bx1 - 100 - 540, (by0 + by1) / 2 + 12 - 960
    P0 = 1.0; sc = [[0, 1]]
    for tp in TAPS: r = tp - P0; sc += [[round(r - .04, 3), 1], [round(r + .03, 3), .8], [round(r + .13, 3), 1]]
    add('X-eptr', '片尾 指针', E0 + P0, ED - P0, pf, k={'x': kf((0, px + 140), (.2, px)), 'y': kf((0, py + 240), (.2, py)), 'opacity': kf((0, 0), (.1, 1)), 'scale': sc})
    for i, tp in enumerate(TAPS):
        add(f'X-erip{i % 2 + 1}', '片尾 点击波纹', E0 + tp, .4, rf, k={'x': kf((0, px)), 'y': kf((0, py)), 'scale': kf((0, .7), (.4, 2.0)), 'opacity': kf((0, .9), (.4, 0))})
        sfx('u_click', E0 + tp, .55)

TRACKS = [
    ('X-glitch', '毒舌 暗角闪', 'title'),
    ('X-fx', '心心特效', 'title'),
    ('X-plate', '字幕底板', 'title'),
    ('X-sub1', '字幕1', 'title'), ('X-sub2', '字幕2', 'title'), ('X-sub3', '字幕3', 'title'), ('X-sub4', '字幕4', 'title'),
    ('X-brow', '五音 徽章行', 'meter'), ('X-blit1', '徽章 さ', 'meter'), ('X-blit2', '徽章 し', 'meter'), ('X-blit3', '徽章 す', 'meter'), ('X-blit4', '徽章 せ', 'meter'), ('X-blit5', '徽章 そ', 'meter'),
    ('X-intro', '开头（标题字幕+五音泡泡）', 'title'),
    ('X-elogo', '片尾 Logo', 'end'), ('X-erow', '片尾 五音', 'end'), ('X-ecopy1', '片尾 文案1', 'end'), ('X-ecopy2', '片尾 文案2', 'end'),
    ('X-ebtn', '片尾 下载按钮', 'end'), ('X-esheen', '片尾 按钮扫光', 'end'), ('X-ebadge', '片尾 商店标', 'end'),
    ('X-eptr', '片尾 指针', 'end'), ('X-erip1', '片尾 波纹1', 'end'), ('X-erip2', '片尾 波纹2', 'end'),
    ('X-flash', '闪光', 'end'), ('X-flash2', '闪光2', 'end'),
]

if __name__ == '__main__':
    import sys
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    if not only:
        for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))
    FLASH = save(Image.new('RGBA', (W, H), (255, 255, 255, 255)), 'flash')
    PINKF = save(Image.new('RGBA', (W, H), (255, 170, 200, 255)), 'flash_pink')
    for nm, fn in [('intro', intro), ('badges', badges), ('subs', subs), ('glitch', glitches), ('end', endcard)]:
        if not only or nm in only: fn(); print(nm, len(LAY), flush=True)
    meta = {'tracks': TRACKS, 'layers': LAY, 'end0': END0, 'sw0': SW0, 'swd': SWD, 'ch0': CH0, 'chd': CHD, 'ec0': EC0, 'ed': ED, 'end1': END1, 'vo0': VO0, 'vos': VOS, 'push0': PUSH0, 'sfx': SFX, 'shake': SHAKE}
    if not only: json.dump(meta, open(os.path.join(PK, 'layers.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('layers', len(LAY), 'files', len({l['file'] for l in LAY}), 'sfx', len(SFX), 'end', END1)
