# MM-JP floze迭代2「1年ぶりの彼を部屋に入れた結果…」包装 v1（琥珀·深夜，UI克制）
# 开场分屏 2.5s | 正片 + ドキドキ 心动值 | 选项1 定格(弹幕) | 选项2 定格(心跳+弹幕, 不点) | AI聊天手机+口播 | 片尾卡
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.abspath(os.path.join(HERE, '..', '..'))
PK = os.path.join(P, '包装素材v1'); OUT = os.path.join(PK, 'layers'); FR = os.path.join(P, '工程素材', '抽帧')
W, H = 1080, 1920
APP = 'F:/钟海明/2026/2026年10月10日MM-编辑器重构/app/'
NOTO = APP + 'public/fonts/NotoSansJP-Black.otf'
NOTOB = APP + 'public/fonts/NotoSansJP-Bold.otf'
ASSET = 'F:/钟海明/MM透明尾板/片尾/片尾文件夹/(素材)/图片/'
WH = (255, 255, 255)
AMB = (255, 178, 84); AMB_D = (120, 60, 14)
AMBG = [(0, (255, 222, 160)), (.55, (255, 180, 88)), (1, (232, 130, 50))]
COOL = (206, 226, 255)
V = 'a'; FPS = 30

# ---------------- 时间线 ----------------
OFF = 2.5                       # 开场分屏
CUT = 7.958                     # 原片硬切（选项1）
FZ1 = 3.0                       # 选项1 定格
VSTOP = 20.9                    # 选项2 定格帧（之后手挡镜头）
AEND = 22.0                     # 原声放到
F1 = math.floor((OFF + CUT) * 30) / 30   # 10.4333 定格1 起（向下吸附，避免露出第二幕首帧）
SH2 = F1 + FZ1 - CUT            # 第二段原片的工程偏移
def pt(v): return v + (SH2 if v >= CUT - 1e-6 else OFF)    # 原片时间 → 工程时间
F2 = round(pt(VSTOP) * 30) / 30  # 定格2 起
O2 = round((pt(21.95) + .05) * 30) / 30  # 选项2 出现（台词说完）
PH0 = round((O2 + 3.0) * 30) / 30; PHD = 9.4           # 聊天手机 + 口播
EC0 = round((PH0 + PHD) * 30) / 30; ED = 3.0; END1 = EC0 + ED

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
def kf(*pts): return [[round(p[0], 3), round(p[1], 4)] + ([p[2]] if len(p) > 2 else []) for p in pts]
def kmerge(lst):
    out = []
    for p in sorted(lst, key=lambda q: q[0]):
        if not out or p[0] > out[-1][0] + .005: out.append(p)
    return kf(*out)
SFX = []
def sfx(name, t, v): SFX.append([name, round(t, 3), v])

def _paste(L, im, x, y):
    bx0, by0 = max(0, x), max(0, y); bx1, by1 = min(L.width, x + im.width), min(L.height, y + im.height)
    if bx1 <= bx0 or by1 <= by0: return
    L.alpha_composite(im.crop((bx0 - x, by0 - y, bx1 - x, by1 - y)), (bx0, by0))
def text(L, xy, s, f, fill=WH, a=1.0, anchor='ls', shadow=.55, grad=None, stroke=0, scol=(0, 0, 0)):
    if a <= 0.003: return
    m = Image.new('L', L.size, 0); ImageDraw.Draw(m).text(xy, s, font=f, fill=255, anchor=anchor)
    bb = m.getbbox()
    if not bb: return
    if shadow:
        pad = 30; c = m.crop((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)).filter(ImageFilter.GaussianBlur(9))
        sh = Image.new('RGBA', c.size, (0, 0, 0, 0)); sh.putalpha(c.point(lambda v: int(min(255, v * shadow * a * 1.3))))
        _paste(L, sh, bb[0] - pad, bb[1] - pad + 4)
    if stroke:
        sm = Image.new('L', L.size, 0); ImageDraw.Draw(sm).text(xy, s, font=f, fill=255, anchor=anchor, stroke_width=stroke)
        sk = Image.new('RGBA', L.size, scol + (0,)); sk.putalpha(sm.point(lambda v: int(v * a * .9))); L.alpha_composite(sk)
    c = m.crop(bb)
    col = grad_img(c.width, c.height, grad).convert('RGBA') if grad else Image.new('RGBA', c.size, fill + (255,))
    col.putalpha(c.point(lambda v: int(v * a))); _paste(L, col, bb[0], bb[1])
def blit(dst, spr, cx, cy, sc=1., a=1.):
    if a <= .003 or sc <= .01: return
    s = spr if abs(sc - 1) < 1e-3 else spr.resize((max(1, int(spr.width * sc)), max(1, int(spr.height * sc))), Image.BILINEAR)
    if a < .999: s = tint_alpha(s, a)
    _paste(dst, s, int(round(cx - s.width / 2)), int(round(cy - s.height / 2)))
def tint_alpha(spr, a):
    arr = np.array(spr); arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8); return Image.fromarray(arr)
def glow_of(spr, rgb, r, a=1., pad=60):
    m = Image.new('L', (spr.width + pad * 2, spr.height + pad * 2), 0); m.paste(spr.split()[3], (pad, pad))
    m = m.filter(ImageFilter.GaussianBlur(r)); g = Image.new('RGBA', m.size, rgb + (0,)); g.putalpha(m.point(lambda v: int(min(255, v * a)))); return g
def rr_mask(w, h, r):
    S = 4; m = Image.new('L', (w * S, h * S), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=r * S, fill=255)
    return m.resize((w, h), Image.LANCZOS)

_FC = {}
def frame(v):
    i = max(0, min(528, int(v * 24 + 1e-6)))
    if i not in _FC:
        if len(_FC) > 40: _FC.clear()
        _FC[i] = Image.open(os.path.join(FR, f'{i + 1:04d}.jpg')).convert('RGB')
    return _FC[i]

def logo_row(icon_h=104, wm_h=44, y=300):
    icon = Image.open(ASSET + 'LOGO-256x256-圆角.png').convert('RGBA').resize((icon_h, icon_h), Image.LANCZOS)
    wm = Image.open(APP + 'public/assets/product-logo.png').convert('RGBA'); wm = wm.resize((int(wm.width * wm_h / wm.height), wm_h), Image.LANCZOS)
    tot = icon_h + 20 + wm.width; x = 540 - tot / 2
    L = canvas(); _paste(L, glow_of(icon, (0, 0, 0), 10, .6, 30), int(x) - 30, int(y - icon_h / 2) - 30 + 6)
    L.alpha_composite(icon, (int(x), int(y - icon_h / 2))); x2 = x + icon_h + 20
    _paste(L, glow_of(wm, (0, 0, 0), 6, .6, 20), int(x2) - 20, int(y - wm_h / 2) - 20 + 3)
    L.alpha_composite(wm, (int(x2), int(y - wm_h / 2)))
    return L
def pill(L, box, r, fill, outline=None, ow=2):
    x0, y0, x1, y1 = [int(v) for v in box]; w, h = x1 - x0, y1 - y0
    m = rr_mask(w, h, r)
    f = Image.new('RGBA', (w, h), fill[:3] + (0,)); f.putalpha(m.point(lambda v: int(v * fill[3] / 255))); L.alpha_composite(f, (x0, y0))
    if outline:
        S = 4; ring = Image.new('L', (w * S, h * S), 0); ImageDraw.Draw(ring).rounded_rectangle([1, 1, w * S - 2, h * S - 2], radius=r * S, outline=255, width=ow * S)
        ring = ring.resize((w, h), Image.LANCZOS); o = Image.new('RGBA', (w, h), outline[:3] + (0,)); o.putalpha(ring.point(lambda v: int(v * outline[3] / 255))); L.alpha_composite(o, (x0, y0))
def heart_spr(s, rgb):
    S = 4; n = s * S; m = Image.new('L', (n, n), 0); d = ImageDraw.Draw(m)
    r = n * .27; d.ellipse([n * .5 - 2 * r, n * .12, n * .5, n * .12 + 2 * r], fill=255); d.ellipse([n * .5, n * .12, n * .5 + 2 * r, n * .12 + 2 * r], fill=255)
    d.polygon([(n * .5 - 2 * r + n * .012, n * .12 + r * 1.25), (n * .5 + 2 * r - n * .012, n * .12 + r * 1.25), (n * .5, n * .93)], fill=255)
    m = m.resize((s, s), Image.LANCZOS); im = Image.new('RGBA', (s, s), rgb + (0,)); im.putalpha(m); return im

# ---------------- 开场分屏（0–2.5） ----------------
TITLE = ('1年ぶりの彼を', '部屋に入れた結果…')
def intro():
    bg = Image.new('RGBA', (W, H), (10, 7, 6, 255))
    add('V1', '开场 底', 0, OFF, save(bg, 'intro_bg'))
    def half(v, cy, crop_y):
        im = frame(v).resize((W, H)).crop((0, crop_y, W, crop_y + 940)); L = canvas(); L.paste(im, (0, cy - 470)); return L
    top = half(3.2, 480, 300); bot = half(19.6, 1440, 360)
    # 下半屏压一点琥珀
    add('X-intro1', '开场 上屏「入れる前」', 0, OFF, save(top, 'intro_top'), k={'x': kf((0, -1080), (.32, 0, 'ease')), 'scale': kf((0, 1.0), (OFF, 1.05))}, ay=.25)
    add('X-intro2', '开场 下屏「入れた後」', .12, OFF - .12, save(bot, 'intro_bot'), k={'x': kf((0, 1080), (.32, 0, 'ease')), 'scale': kf((0, 1.05), (OFF, 1.0))}, ay=.75)
    sfx('s_whoosh', 0, .45); sfx('s_whoosh', .12, .35)
    # 标签（小）
    for lab, y, nm, t0 in (('入れる前', 880, 'tag_before', .35), ('入れた後', 1010, 'tag_after', .5)):
        L = canvas(); f = font(NOTOB, 34); tw = f.getlength(lab); x0 = 540 - tw / 2 - 26
        pill(L, (x0, y - 30, x0 + tw + 52, y + 30), 30, (12, 8, 6, 170), (255, 190, 110, 200) if 'after' in nm else (255, 255, 255, 150))
        text(L, (540, y + 1), lab, f, AMB if 'after' in nm else WH, anchor='mm', shadow=0)
        add('X-intro3' if 'before' in nm else 'X-intro4', '开场 标签 ' + lab, t0, OFF - t0, save(L, nm), k={'opacity': kf((0, 0), (.2, 1))})
    # 分隔线
    L = canvas(); d = ImageDraw.Draw(L); d.rectangle([0, 949, W, 951], fill=(255, 200, 130, 220))
    add('X-intro5', '开场 分隔线', .3, OFF - .3, save(L, 'intro_line'), ax=.5, k={'scaleX': kf((0, 0), (.3, 1, 'ease'))})
    # 标题：压在分屏中缝
    L = canvas(); band = Image.new('L', (W, H), 0); ImageDraw.Draw(band).rectangle([0, 780, W, 1120], fill=200); band = band.filter(ImageFilter.GaussianBlur(50))
    sh = Image.new('RGBA', (W, H), (8, 5, 4, 0)); sh.putalpha(band); L.alpha_composite(sh)
    text(L, (540, 925), TITLE[0], font(NOTO, 70), WH, anchor='ms', shadow=.9)
    text(L, (540, 1040), TITLE[1], font(NOTO, 86), anchor='ms', shadow=.9, grad=AMBG, stroke=4, scol=AMB_D)
    add('X-intro6', '开场 标题', .55, OFF - .55, save(L, 'intro_title'), ay=980 / H, k={'opacity': kf((0, 0), (.12, 1)), 'scale': kf((0, 1.25), (.14, .96), (.26, 1))})
    sfx('u_pop2', .55, .5)
    Lg = logo_row(icon_h=72, wm_h=30, y=150)
    add('X-intro7', '开场 Logo', .2, OFF - .2, save(Lg, 'intro_logo'), k={'opacity': kf((0, 0), (.25, 1))})
    add('X-flash', '开场→正片 闪', OFF - .02, .25, FLASH, k={'opacity': kf((0, .55), (.25, 0))})

# ---------------- 字幕 ----------------
# (说话人, [(文字, 原片时间)], 结束)    '\n' 换行  '*' 重点
LINES = [
    ('F', [('入って', .80)], 1.12),
    ('M', [('うわ、', 1.54), ('なっつ', 1.88)], 2.30),
    ('M', [('*一年ぶり', 2.86), ('だよね', 3.28)], 3.66),
    ('M', [('全然', 4.16), ('変わってない', 4.46), ('じゃん…', 4.96)], 5.20),
    ('F', [('そりゃそうでしょ', 5.62), ('\nすぐ変わるわけないじゃん', 6.60)], 7.70),
    ('M', [('てか、', 8.30), ('その*部屋着', 8.84), ('\nまだ着ててくれたんだ', 9.76)], 10.90),
    ('M', [('やっぱ', 11.50), ('*可愛いね', 11.78)], 12.25),
    ('F', [('これ飲んだら', 13.42), ('\nもう帰ってよね', 13.98)], 14.70),
    ('M', [('*帰るわけ', 15.50), ('ないじゃん', 15.90)], 16.40),
    ('M', [('部屋に入れたってことは、', 17.04), ('\nそういうことでしょ？', 18.72)], 19.50),
    ('M', [('…もう、', 20.48), ('*我慢できないよ', 21.18)], 21.95),
]
MSUBY, FSUBY = 1330, 1720
def layout(chunks, who):
    rows, cur = [], []
    for i, (s, t) in enumerate(chunks):
        if s.startswith('\n') and cur: rows.append(cur); cur = []
        cur.append(i)
    rows.append(cur)
    items = []
    for s, t in chunks:
        s = s.lstrip('\n')
        parts = []   # 片段内 '*' 之后为重点
        if '*' in s: a, b = s.split('*', 1); parts = [(a, False), (b, True)]
        else: parts = [(s, False)]
        for j, (ps, em) in enumerate(parts):
            if not ps: continue
            items.append({'s': ps, 't': t, 'emph': em, 'who': who, 'row': None,
                          'f': font(NOTO, (78 if em else 62)) if who == 'M' else font(NOTOB, 50)})
    # 重新按行
    rowmap = []; ci = 0; k = 0
    for s, t in chunks:
        if s.startswith('\n') and k: ci += 1
        n = len([p for p in (s.lstrip('\n').split('*', 1) if '*' in s else [s.lstrip('\n')]) if p]); rowmap += [ci] * n; k += 1
    nrow = ci + 1; RH = 92 if who == 'M' else 72; base = MSUBY if who == 'M' else FSUBY
    y = base - (nrow - 1) * RH
    for r in range(nrow):
        idx = [i for i in range(len(items)) if rowmap[i] == r]
        tw = sum(items[i]['f'].getlength(items[i]['s']) for i in idx) + 4 * (len(idx) - 1); x = 540 - tw / 2
        for i in idx: items[i]['xy'] = (x, y); x += items[i]['f'].getlength(items[i]['s']) + 4
        y += RH
    return items
def sub_text(L, it):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text(it['xy'], it['s'], font=it['f'], fill=255, anchor='ls')
    bb = m.getbbox(); pad = 40; c = m.crop((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad))
    for r, a in [(16, .5), (4, .75)]:
        h_ = c.filter(ImageFilter.GaussianBlur(r)); sh = Image.new('RGBA', c.size, (4, 3, 2, 0)); sh.putalpha(h_.point(lambda v: int(min(255, v * a * 1.6))))
        _paste(L, sh, bb[0] - pad, bb[1] - pad + 3)
    if it['emph']:
        g_ = c.filter(ImageFilter.GaussianBlur(14)); gc = Image.new('RGBA', c.size, AMB + (0,)); gc.putalpha(g_.point(lambda v: int(min(255, v * .55))))
        _paste(L, gc, bb[0] - pad, bb[1] - pad)
        text(L, it['xy'], it['s'], it['f'], anchor='ls', shadow=0, grad=AMBG, stroke=4, scol=AMB_D)
    else:
        text(L, it['xy'], it['s'], it['f'], COOL if it['who'] == 'F' else WH, anchor='ls', shadow=0)
def put_subs(lines, tmap, tagp, limit=None, track=False):
    for li, (who, chunks, end) in enumerate(lines):
        nxt = tmap(lines[li + 1][1][0][1]) if li + 1 < len(lines) else 1e9
        hide = min(nxt - .04, tmap(end) + .55)
        if limit: hide = min(hide, limit(chunks[0][1]))
        items = layout(chunks, who); tag = f'{tagp}{li:02d}'
        # 男主台词跟踪面部：整句一起平移到下巴下方
        blk = None
        if track and who == 'M':
            ys = [it['xy'][1] for it in items]; y0 = min(ys); y1 = max(ys)
            bw = max(sum(items[i]['f'].getlength(items[i]['s']) for i in range(len(items)) if items[i]['xy'][1] == yy) for yy in set(ys))
            blk = (y0, y1, bw)
        for i, it in enumerate(items):
            L = canvas(); sub_text(L, it); bb = L.getbbox(); ts = tmap(it['t']); D = hide - ts
            k = {'opacity': kf((0, 0), (.1, 1), (max(.11, D - .12), 1), (D, 0)), 'y': kf((0, 12), (.16, 0))}
            if blk:
                xs, yv = [], []
                n = max(2, int(D / .1) + 1)
                for j in range(n):
                    t = min(D, j * .1); fx, fy = sub_target(ts + t, blk)
                    xs.append((t, fx)); yv.append((t, fy + (12 * (1 - t / .16) if t < .16 else 0)))
                k['x'] = kmerge(xs); k['y'] = kmerge(yv)
            ax = ay = .5
            if it['emph']:
                ax, ay = (bb[0] + bb[2]) / 2 / W, (bb[1] + bb[3]) / 2 / H
                k['scale'] = kf((0, 1.4), (.12, .94), (.22, 1.03), (.32, 1))
            add(f'X-sub{i + 1}', ('女 ' if who == 'F' else '男 ') + it['s'], ts, D, save(L, f'{tag}_{i}'), ax=ax, ay=ay, k=k)
def subs():
    put_subs(LINES, pt, 'sub', limit=lambda v: F1 if v < CUT else 1e9, track=True)

# ---------------- 人物蒙版 / 面部跟踪 ----------------
MK = os.path.join(P, '工程素材', '人物蒙版')
def kval(lst, t):
    if t <= lst[0][0]: return lst[0][1]
    for a, b in zip(lst, lst[1:]):
        if a[0] <= t <= b[0]: return a[1] + (b[1] - a[1]) * (t - a[0]) / max(1e-6, b[0] - a[0])
    return lst[-1][1]
HB = []   # 定格2 心跳缩放关键帧（freeze2 里填）
def src_at(T):
    """工程时间 → (原片时间, 画面缩放, 锚点y)；非正片段返回 None"""
    if OFF <= T < F1: return T - OFF, 1.0, .5
    if F1 <= T < F1 + FZ1: return CUT - .05, 1 + .035 * (T - F1) / FZ1, .3
    if F1 + FZ1 <= T < F2: return T - SH2, 1.0, .5
    if F2 <= T < PH0: return VSTOP, (kval(HB, T - F2) if HB else 1.0), .42
    return None
_MC = {}
def mask_raw(v):
    i = max(0, min(528, int(v * 24 + 1e-6)))
    if i not in _MC:
        if len(_MC) > 60: _MC.clear()
        m = Image.open(os.path.join(MK, f'{i + 1:04d}.png')).convert('L')
        _MC[i] = m
    return _MC[i]
def mask_at(T):
    s = src_at(T)
    if not s: return None
    v, sc, ay = s
    m = mask_raw(v).resize((W, H), Image.BILINEAR)
    if abs(sc - 1) > 1e-3:
        big = m.resize((int(W * sc), int(H * sc)), Image.BILINEAR); ox, oy = int(540 - 540 * sc), int(ay * H - ay * H * sc)
        m = Image.new('L', (W, H), 0); m.paste(big, (ox, oy))
    return m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2.5))
_HEAD = {}
def head_raw(i):
    """原片帧 i 的男主头部 (cx, chin_y)（1080×1920），由人物蒙版顶部估算"""
    if i in _HEAD: return _HEAD[i]
    a = np.asarray(Image.open(os.path.join(MK, f'{i + 1:04d}.png')).convert('L')) > 128
    a[:, :20] = False; a[:, -20:] = False
    import scipy.ndimage as nd
    lab, n = nd.label(a)
    if n > 1:   # 只留面积最大的人（男主），排除女主手臂/门边
        sz = nd.sum(a, lab, range(1, n + 1)); a = lab == (int(np.argmax(sz)) + 1)
    rows = np.where(a.sum(1) > 12)[0]
    if len(rows) == 0: _HEAD[i] = None; return None
    top = rows[0]
    seg = a[top + 15: top + 70]
    wid = np.median([r.sum() for r in seg if r.sum() > 0]) if seg.any() else 120
    hh = float(np.clip(wid * 1.35, 120, 640))
    reg = a[top: int(top + hh)]; ys, xs = np.nonzero(reg)
    cx = xs.mean() if len(xs) else 270
    _HEAD[i] = (cx * 2, (top + hh) * 2); return _HEAD[i]
def head_smooth(v):
    """时间平滑（±0.25s，不跨硬切）"""
    i0 = int(v * 24 + 1e-6); pts = []
    for d in range(-6, 7):
        j = i0 + d
        if j < 0 or j > 528: continue
        if (j < 191) != (i0 < 191): continue      # 7.958s 硬切 = 第191帧
        h = head_raw(j)
        if h: pts.append(h)
    if not pts: return (540, 1100)
    return (float(np.median([p[0] for p in pts])), float(np.median([p[1] for p in pts])))
def sub_target(T, blk):
    """字幕块 (首行基线 y0, 末行 y1, 宽) → 相对基准的 (dx, dy)"""
    s = src_at(T)
    if not s: return 0, 0
    v, sc, ay = s; cx, chin = head_smooth(v)
    cx = 540 + (cx - 540) * sc; chin = ay * H + (chin - ay * H) * sc
    y0, y1, bw = blk
    ty = float(np.clip(chin + 130, 890, 1560 - (y1 - y0)))
    half = bw / 2 + 50; tx = float(np.clip(cx, half, W - half))
    return round(tx - 540, 1), round(ty - y0, 1)

# ---------------- 全程弹幕（从人物身后穿过，逐帧烘焙） ----------------
DAN0 = [  # (工程时间, 文字)
    (3.0, '夜中に来るのずるい'), (3.9, 'え、イケメンすぎん？'), (4.9, '1年ぶりの破壊力'), (5.9, '入れちゃダメ！'),
    (7.0, 'この声好き'), (8.1, 'もう入れてるやん'), (9.2, '変わってないのはそっち'),
    (13.8, '部屋着覚えてるの反則'), (14.9, 'まだ着てるの健気すぎ'), (16.0, '可愛いって言われたい'), (17.1, '顔近い近い'),
    (18.2, '水じゃ帰らないって'), (19.3, '帰る気ゼロで草'), (20.4, '絶対帰らないやつ'),
    (21.6, 'そういうことです'), (22.7, '目線がやばい'), (23.8, '理性もたない'), (24.9, '心臓もたない'), (25.9, 'ここで止めないで'),
]
LANES = [300, 410, 520, 630, 740]
DANS = []
def dan_sched():
    f = font(NOTOB, 40); free = {y: -9 for y in LANES}; li = 0
    ev = [(t, s, 300) for t, s in DAN0]
    ev += [(F1 + .1 + j * 2.4 / len(DAN1), s, 470) for j, s in enumerate(DAN1)]
    ev += [(O2 + .05 + j * 2.4 / len(DAN2), s, 470) for j, s in enumerate(DAN2)]
    for t, s, spd in sorted(ev):
        tw = f.getlength(s) + 40
        for k in range(len(LANES)):
            y = LANES[(li + k) % len(LANES)]
            if free[y] <= t: break
        else: y = LANES[li % len(LANES)]
        li = (LANES.index(y) + 2) % len(LANES)
        free[y] = t + (tw + 90) / spd
        L = Image.new('RGBA', (int(tw) + 20, 72), (0, 0, 0, 0))
        hot = len(DANS) % 3 == 1
        pill(L, (0, 4, tw, 66), 31, (10, 7, 5, 80))
        tL = Image.new('RGBA', (W, H), (0, 0, 0, 0)); text(tL, (20, 37), s, f, (255, 214, 160) if hot else WH, a=.95, anchor='lm', shadow=.5)
        L.alpha_composite(tL.crop((0, 0, L.width, L.height)))
        DANS.append({'t': t, 's': s, 'spd': spd, 'y': y, 'img': L, 'end': t + (1090 + tw) / spd})
def danmaku_all():
    dan_sched()
    t0 = min(d['t'] for d in DANS); t1 = min(PH0, max(d['end'] for d in DANS))
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS)); cnt = 0
    for fi in range(n0, n1):
        T = fi / FPS; act = [d for d in DANS if d['t'] <= T < d['end']]
        if not act: continue
        L = canvas()
        for d in act: _paste(L, d['img'], int(1090 - (T - d['t']) * d['spd']), d['y'] - 36)
        m = mask_at(T)
        if m is not None: L.putalpha(ImageChops.multiply(L.split()[3], ImageChops.invert(m)))
        add('X-dan', '弹幕（逐帧，人物遮挡）', T, 1 / FPS, save(L, f'dan{fi:04d}')); cnt += 1
    print('danmaku frames', cnt, 'items', len(DANS))

# ---------------- ドキドキ 心动值（右上，小） ----------------
STEPS = [(1.54, 12), (2.86, 24), (4.16, 33), (8.30, 47), (11.50, 61), (15.50, 74), (17.04, 87), (20.48, 99)]
MX0, MY0, MX1, MY1 = 742, 132, 1044, 196
def meter_img(v):
    L = canvas(); pill(L, (MX0, MY0, MX1, MY1), 32, (14, 9, 6, 150), (255, 200, 140, 90), 2)
    hs = heart_spr(34, AMB if v else (180, 160, 150)); L.alpha_composite(hs, (MX0 + 16, (MY0 + MY1) // 2 - 16))
    text(L, (MX0 + 60, (MY0 + MY1) // 2 - 6), 'ドキドキ', font(NOTOB, 22), (255, 236, 214), anchor='lm', shadow=0)
    bx0, bx1, by = MX0 + 62, MX1 - 78, (MY0 + MY1) // 2 + 14
    d = ImageDraw.Draw(L); d.rounded_rectangle([bx0, by - 3, bx1, by + 3], 3, fill=(255, 255, 255, 60))
    if v:
        gw = int((bx1 - bx0) * v / 100); g = grad_img(max(2, gw), 6, [(0, (255, 214, 150)), (1, (255, 150, 60))], horiz=True).convert('RGBA')
        g.putalpha(rr_mask(max(2, gw), 6, 3)); L.alpha_composite(g, (bx0, by - 3))
    text(L, (MX1 - 18, (MY0 + MY1) // 2 + 2), str(v), font(NOTO, 34), AMB if v else WH, anchor='rm', shadow=0)
    return L
def meter():
    t0 = OFF; prev = 0; seq = [(OFF - OFF, 0)] + [(v, n) for v, n in STEPS]
    for j, (v, n) in enumerate(seq):
        s = OFF if j == 0 else pt(v); e = pt(seq[j + 1][0]) if j + 1 < len(seq) else PH0
        k = {}
        if j == 0: k['opacity'] = kf((0, 0), (.3, 1))
        else:
            k['scale'] = kf((0, 1.12), (.1, .97), (.2, 1))
        if e >= PH0 - .01: k['opacity'] = kf((0, 1), (max(.01, e - s - .25), 1), (e - s, 0))
        add('X-meter', f'ドキドキ {n}', s, e - s, save(meter_img(n), f'meter{n:02d}'), ax=(MX0 + MX1) / 2 / W, ay=(MY0 + MY1) / 2 / H, k=k)
        if j:
            L = canvas(); text(L, (MX1 - 18, MY1 + 34), f'+{n - seq[j - 1][1]}', font(NOTO, 30), anchor='rm', shadow=.6, grad=AMBG)
            add('X-meterp', f'心动 +{n - seq[j - 1][1]}', s, .7, save(L, f'meterp{n:02d}'), k={'opacity': kf((0, 0), (.08, 1), (.5, 1), (.7, 0)), 'y': kf((0, 10), (.7, -24))})
            sfx('u_pop2', s, .12)
    # 选项2 心跳时心动值数字抖动
    for b in BEATS:
        pass

# ---------------- 选项（小 UI + 倒计时条） ----------------
BY0, BY1 = 1540, 1630; BW = 404; BXS = [540 - 14 - BW, 540 + 14]
def choice_imgs(opts, tag):
    f = font(NOTOB, 44); out = {}
    for i, s in enumerate(opts):
        for st in ('n', 'sel', 'dim'):
            L = canvas(); x0 = BXS[i]
            if st == 'sel':
                G = Image.new('L', (W, H), 0); ImageDraw.Draw(G).rounded_rectangle([x0, BY0 + 6, x0 + BW, BY1 + 6], 45, fill=150); G = G.filter(ImageFilter.GaussianBlur(22))
                gl = Image.new('RGBA', (W, H), AMB + (0,)); gl.putalpha(G); L.alpha_composite(gl)
                g = grad_img(BW, BY1 - BY0, [(0, (255, 214, 150)), (1, (240, 146, 60))], horiz=True).convert('RGBA'); g.putalpha(rr_mask(BW, BY1 - BY0, 45)); L.alpha_composite(g, (x0, BY0))
                text(L, (x0 + BW / 2, (BY0 + BY1) / 2 + 1), s, f, (52, 24, 6), anchor='mm', shadow=0)
            else:
                a = .45 if st == 'dim' else 1
                pill(L, (x0, BY0, x0 + BW, BY1), 45, (12, 8, 6, int(150 * a)), (255, 210, 160, int(170 * a)), 2)
                text(L, (x0 + BW / 2, (BY0 + BY1) / 2 + 1), s, f, WH, a=a, anchor='mm', shadow=0)
            out[(i, st)] = save(L, f'{tag}_{i}_{st}')
    # 倒计时条
    L = canvas(); d = ImageDraw.Draw(L); x0, x1, y = BXS[0] + 20, BXS[1] + BW - 20, BY1 + 34
    d.rounded_rectangle([x0, y - 3, x1, y + 3], 3, fill=(255, 255, 255, 70)); out['track'] = save(L, f'{tag}_cdtrack')
    L = canvas(); g = grad_img(x1 - x0, 6, [(0, (255, 214, 150)), (1, (255, 150, 60))], horiz=True).convert('RGBA'); g.putalpha(rr_mask(x1 - x0, 6, 3)); L.alpha_composite(g, (x0, y - 3))
    out['bar'] = save(L, f'{tag}_cdbar'); out['bx'] = (x0, x1, y)
    return out
def shade_bottom():
    a = np.zeros((H, 1), np.float32); yy = np.arange(H, dtype=np.float32)
    a[:, 0] = np.clip((yy - 1250) / 500, 0, 1) ** 1.3 * 150
    L = Image.new('RGBA', (W, H), (6, 4, 3, 0)); L.putalpha(Image.fromarray(np.repeat(a, W, 1).astype(np.uint8))); return save(L, 'shade_bot')
def pointer_imgs():
    L = canvas(); r = 36
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([540 - r - 6, 960 - r, 540 + r + 6, 960 + r + 14], fill=100); g = g.filter(ImageFilter.GaussianBlur(12))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(g); L.alpha_composite(sh)
    d = ImageDraw.Draw(L); d.ellipse([540 - r, 960 - r, 540 + r, 960 + r], fill=(255, 255, 255, 90), outline=(255, 255, 255, 220), width=3)
    d.ellipse([540 - 7, 960 - 7, 540 + 7, 960 + 7], fill=(255, 255, 255, 240))
    R = canvas(); ImageDraw.Draw(R).ellipse([540 - 46, 960 - 46, 540 + 46, 960 + 46], outline=(255, 255, 255, 220), width=4)
    return save(L, 'pointer'), save(R, 'ripple')
DAN1 = ['水あげちゃうの？', '追い返せ！', '入れた時点で負け', '部屋着バレてるｗ', '顔が良すぎる', '1年ぶりは反則', '水で済むわけない']
DAN2 = ['受け入れる一択', '理性どこいった', '突き放せるわけない', '声がずるい', '1年待ってたんでしょ', 'これは負け確', '続きが気になる']
def danmaku(lst, t0, span, lanes, tag, tmax=1e9):
    f = font(NOTOB, 40)
    for i, s in enumerate(lst):
        L = canvas(); hot = i % 3 == 1
        tw = int(f.getlength(s)); y = lanes[i % len(lanes)]
        pill(L, (0, y - 32, tw + 40, y + 30), 31, (10, 7, 5, 70))
        text(L, (20, y + 2), s, f, (255, 214, 160) if hot else WH, a=.92, anchor='lm', shadow=.5)
        st = t0 + i * span / len(lst); dur = 2.3 + (i % 3) * .2
        d2 = min(dur, tmax - st)
        add(f'X-dan{i + 1}', '弹幕 ' + s, st, d2, save(L, f'{tag}{i}'), k={'x': kf((0, 1090), (dur, -tw - 80))})
def choice(opts, t0, cd, tag, pick=None, hes=None):
    """t0 出现；cd 倒计时长；pick=(序号, 点击时刻)；hes=指针犹豫路径 [(t, 序号或中点)]"""
    im = choice_imgs(opts, tag); tend = (pick[1] + .7) if pick else t0 + cd + .05
    for i in range(2):
        k = {'opacity': kf((0, 0), (.18, 1)), 'y': kf((0, 26), (.22, 0, 'ease'))}
        e = pick[1] if pick else tend
        add(f'X-ch{i + 1}', f'选项 {opts[i]}', t0 + i * .08, e - t0 - i * .08, im[(i, 'n')], k=k)
        sfx('u_pop2', t0 + i * .08, .3)
        if pick:
            add(f'X-ch{i + 1}', f'选项 {opts[i]}（{"选中" if i == pick[0] else "未选"}）', pick[1], tend - pick[1], im[(i, 'sel' if i == pick[0] else 'dim')],
                ax=(BXS[i] + BW / 2) / W, ay=(BY0 + BY1) / 2 / H,
                k={'scale': kf((0, .94), (.1, 1.05), (.2, 1)) if i == pick[0] else kf((0, 1)), 'opacity': kf((0, 1), (tend - pick[1] - .15, 1), (tend - pick[1], 0))})
    x0, x1, y = im['bx']
    add('X-cd', '倒计时 轨', t0 + .1, tend - t0 - .1, im['track'], k={'opacity': kf((0, 0), (.15, 1))})
    stop = (pick[1] - t0 - .1) if pick else cd
    add('X-cd2', '倒计时 条', t0 + .1, tend - t0 - .1, im['bar'], ax=x0 / W, ay=y / H,
        k={'scaleX': kf((0, 1), (stop, max(.001, 1 - stop / cd))) if pick else kf((0, 1), (cd, .001)), 'opacity': kf((0, 0), (.15, 1))})
    pf, rf = pointer_imgs()
    cx = lambda i: (BXS[0] + BW / 2 - 540) if i == 0 else ((BXS[1] + BW / 2 - 540) if i == 1 else 0)
    py = (BY0 + BY1) / 2 + 20 - 960
    if pick:
        pi, tp = pick; ps = tp - .65
        add('X-ptr', '指针', ps, tend - ps, pf, k={'x': kf((0, cx(pi) + 160), (.35, cx(pi), 'ease')), 'y': kf((0, py + 260), (.35, py, 'ease')),
                                                    'opacity': kf((0, 0), (.12, 1), (tend - ps - .15, 1), (tend - ps, 0)), 'scale': kf((0, 1), (.6, 1), (.66, .8), (.78, 1))})
        add('X-rip', '点击波纹', tp, .4, rf, k={'x': kf((0, cx(pi))), 'y': kf((0, py)), 'scale': kf((0, .7), (.4, 2.0)), 'opacity': kf((0, .9), (.4, 0))})
        sfx('u_click', tp, .55)
    if hes:
        ps = hes[0][0]; xs = [(0, cx(hes[0][1]) + 160), (.35, cx(hes[0][1]), 'ease')]; ys = [(0, py + 260), (.35, py, 'ease')]
        for t, i in hes[1:]: xs.append((t - ps, cx(i), 'ease')); ys.append((t - ps, py + (8 if i is None else 0), 'ease'))
        add('X-ptr', '指针（犹豫不点）', ps, tend - ps, pf, k={'x': kf(*xs), 'y': kf(*ys), 'opacity': kf((0, 0), (.12, 1))})
    return tend

# ---------------- 定格1：赶他走 / 给他倒水 ----------------
def freeze1():
    im = frame(CUT - .05).convert('RGBA')
    add('V1', '定格1（第一幕末帧）', F1, FZ1, save(im, 'fz1'), ay=.3, k={'scale': kf((0, 1.0), (FZ1, 1.035))})
    add('X-shade', '选项底部压暗', F1 + .05, FZ1 - .05, SHADE, k={'opacity': kf((0, 0), (.2, 1), (FZ1 - .3, 1), (FZ1 - .05, 0))})
    sfx('u_air', F1, .35)
    tp = F1 + 2.15
    choice(('追い返す', '水を出す'), F1 + .15, 2.6, 'c1', pick=(1, tp))
    add('X-flash', '选项1→第二幕 闪', F1 + FZ1 - .1, .3, FLASH, k={'opacity': kf((0, .0), (.1, .5), (.3, 0))})
    sfx('u_flash', F1 + FZ1 - .12, .3)

# ---------------- 定格2：推开他 / 接受他（心跳） ----------------
BEATS = []
def make_beats():
    t = F2 + .15; iv = .9
    while t < PH0 - .25:
        BEATS.append(round(t, 3)); t += iv; iv = max(.34, iv * .86)
def freeze2():
    D = PH0 - F2; im = frame(VSTOP).convert('RGBA')
    sc = [(0, 1.0)]
    for b in BEATS:
        r = b - F2; amp = .035 + .025 * clamp((b - F2) / D)
        sc += [(r, 1.0), (r + .06, 1 + amp), (r + .16, 1.0 + amp * .2), (r + .22, 1 + amp * .65), (r + .36, 1.0)]
    HB[:] = kmerge(sc)
    add('V1', '定格2（贴脸，心跳缩放）', F2, D, save(im, 'fz2'), ay=.42, k={'scale': kmerge(sc)})
    # 心跳暗角（琥珀红边）
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((xx - 540) / 620) ** 2 + ((yy - 900) / 1050) ** 2)
    a = np.clip((r - .55) / .6, 0, 1) ** 1.6
    vg = np.zeros((H, W, 4), np.uint8); vg[..., 0] = 70; vg[..., 1] = 16; vg[..., 2] = 8; vg[..., 3] = (a * 235).astype(np.uint8)
    vgf = save(Image.fromarray(vg, 'RGBA'), 'vignette')
    op = [(0, 0), (.3, .35)]
    for b in BEATS:
        r_ = b - F2; op += [(r_, .35), (r_ + .07, 1.0), (r_ + .2, .55), (r_ + .26, .85), (r_ + .4, .4)]
    add('X-vig', '心跳暗角', F2, D, vgf, k={'opacity': kmerge(op)})
    for b in BEATS: sfx('s_heart', b, .9)
    add('X-shade', '选项底部压暗', O2 - .1, PH0 - O2 + .1, SHADE, k={'opacity': kf((0, 0), (.2, 1))})
    choice(('突き放す', '受け入れる'), O2, PH0 - O2 - .15, 'c2',
           hes=[(O2 + .55, 0), (O2 + 1.15, 1), (O2 + 1.7, 0), (O2 + 2.2, 1), (O2 + 2.6, None)])
    add('X-flash', '选项2 白闪', PH0 - .12, .4, FLASH, k={'opacity': kf((0, 0), (.12, 1), (.4, 0))})
    sfx('u_flash', PH0 - .14, .5)

# ---------------- AI 聊天手机 + 口播 ----------------
CHAT = ['一年ぶりだよね', 'その部屋着、\nまだ着ててくれたんだ', ('img', 18.5), '帰るわけないじゃん']
CHAT_NAME = '蓮'
VO0 = PH0 + .35
VOL = [  # (说话人, chunks(相对口播), end)
    ('M', [('*MiraiMind', .12), ('で、', .95), ('\nまた会えた彼', 1.24)], 2.25),
    ('M', [('キミは、', 3.04), ('*どんな選択', 3.74), ('をする？', 4.30)], 4.75),
    ('M', [('今すぐダウンロードして、', 5.66), ('\n*続きを解放しよう', 7.14)], 8.25),
]
PW, PHH = 600, 1000; PY0 = 120; INS = 14; HDR = 132; INP = 92
def avatar(d):
    im = frame(18.0).crop((290, 330, 790, 830)).resize((d * 2, d * 2), Image.LANCZOS).convert('RGBA')
    im.putalpha(rr_mask(d * 2, d * 2, d)); return im.resize((d, d), Image.LANCZOS)
def wrap(s, f, mw):
    out, cur = [], ''
    for ch in s:
        if f.getlength(cur + ch) > mw and cur and ch not in '、。！？…': out.append(cur); cur = ch
        else: cur += ch
    return out + [cur]
def bubble(s, last):
    f = font(NOTOB, 36); ls = [x for p in s.split('\n') for x in wrap(p, f, 420)]; lh = 50
    w = int(max(f.getlength(l) for l in ls)) + 46; h = lh * len(ls) + 28
    B = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0))
    sh = Image.new('L', B.size, 0); ImageDraw.Draw(sh).rounded_rectangle([8, 12, w + 8, h + 12], 26, fill=110); sh = sh.filter(ImageFilter.GaussianBlur(6))
    shl = Image.new('RGBA', B.size, (0, 0, 0, 0)); shl.putalpha(sh); B.alpha_composite(shl)
    fill = (255, 236, 212) if last else (250, 247, 243)
    d = ImageDraw.Draw(B); d.rounded_rectangle([4, 4, w + 4, h + 4], 26, fill=fill + (255,)); d.rectangle([4, 4, 30, 30], fill=fill + (255,))
    for j, l in enumerate(ls): d.text((27, 18 + j * lh + 35), l, font=f, fill=(120, 58, 10) if last else (26, 20, 16), anchor='ls')
    return B
def photo_msg(v):
    w, h = 300, 400; im = ImageEnhance.Brightness(frame(v).resize((W, H)).crop((60, 40, 1020, 1320))).enhance(1.12).resize((w, h), Image.LANCZOS).convert('RGBA')
    B = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0))
    sh = Image.new('L', B.size, 0); ImageDraw.Draw(sh).rounded_rectangle([8, 12, w + 8, h + 12], 24, fill=110); sh = sh.filter(ImageFilter.GaussianBlur(6))
    shl = Image.new('RGBA', B.size, (0, 0, 0, 0)); shl.putalpha(sh); B.alpha_composite(shl)
    im.putalpha(rr_mask(w, h, 24)); B.alpha_composite(im, (4, 4)); return B
def typing():
    B = Image.new('RGBA', (140, 76), (0, 0, 0, 0)); d = ImageDraw.Draw(B); d.rounded_rectangle([4, 4, 130, 70], 26, fill=(250, 247, 243, 255)); d.rectangle([4, 4, 30, 30], fill=(250, 247, 243, 255))
    return B
def phone_items():
    av = avatar(62); items = []; y = 26; ts = [.5, 2.2, 3.6, 5.4]
    for i, m in enumerate(CHAT):
        b = photo_msg(m[1]) if isinstance(m, tuple) else bubble(m, i == 3)
        items.append({'t': ts[i], 'img': b, 'x': 96, 'y': y, 'av': av, 'kind': 'msg'}); y += b.height + 14
    items.append({'t': 6.6, 'img': typing(), 'x': 96, 'y': y, 'av': av, 'kind': 'typing'})
    return items
def phone_shell():
    S = Image.new('RGBA', (PW + 120, PHH + 120), (0, 0, 0, 0)); o = 60
    g = Image.new('L', S.size, 0); ImageDraw.Draw(g).rounded_rectangle([o - 6, o + 4, o + PW + 6, o + PHH + 14], 78, fill=255); g = g.filter(ImageFilter.GaussianBlur(26))
    gl = Image.new('RGBA', S.size, (255, 160, 70, 0)); gl.putalpha(g.point(lambda v: int(v * .4))); S.alpha_composite(gl)
    d = ImageDraw.Draw(S)
    d.rounded_rectangle([o, o, o + PW, o + PHH], 74, fill=(18, 14, 12, 255), outline=(80, 70, 62, 255), width=3)
    d.rounded_rectangle([o + 4, o + 4, o + PW - 4, o + PHH - 4], 70, outline=(170, 110, 50, 255), width=2)
    return S, o
def screen_bg():
    sw, sh = PW - INS * 2, PHH - INS * 2
    return grad_img(sw, sh, [(0, (40, 28, 20)), (1, (16, 12, 10))]).convert('RGBA'), sw, sh
def header(sw, av):
    Hd = Image.new('RGBA', (sw, HDR), (24, 18, 14, 245)); d = ImageDraw.Draw(Hd)
    d.rounded_rectangle([sw / 2 - 64, 14, sw / 2 + 64, 46], 16, fill=(0, 0, 0, 255))
    Hd.alpha_composite(av.resize((60, 60), Image.LANCZOS), (28, 60))
    d.ellipse([74, 104, 90, 120], fill=(70, 220, 110, 255), outline=(24, 18, 14, 255), width=3)
    d.text((104, 100), CHAT_NAME, font=font(NOTO, 36), fill=(255, 255, 255), anchor='ls')
    d.text((104, 122), 'オンライン', font=font(NOTOB, 20), fill=(150, 220, 160), anchor='ls')
    d.line([(0, HDR - 2), (sw, HDR - 2)], fill=AMB + (255,), width=2)
    return Hd
def inputbar(sw):
    I = Image.new('RGBA', (sw, INP), (24, 18, 14, 245)); d = ImageDraw.Draw(I)
    d.rounded_rectangle([24, 18, sw - 100, INP - 18], 28, fill=(52, 42, 36, 255))
    d.ellipse([sw - 82, 16, sw - 22, INP - 16], fill=AMB + (255,))
    d.polygon([(sw - 62, 34), (sw - 62, INP - 34), (sw - 38, INP / 2)], fill=(60, 30, 8, 255))
    return I
def phone():
    im = frame(19.4).filter(ImageFilter.GaussianBlur(14)); im = ImageEnhance.Brightness(im).enhance(.32)
    a = np.asarray(im).astype(np.float32); a = a * .82 + np.array([70, 36, 10], np.float32) * .18
    add('V1', '聊天 背景（贴脸帧虚化）', PH0, PHD, save(Image.fromarray(a.astype(np.uint8)).convert('RGBA'), 'ph_bg'), k={'scale': kf((0, 1.04), (PHD, 1.1))})
    sfx('s_whoosh', PH0 + .05, .5)
    shell, o = phone_shell(); bg, sw, sh = screen_bg(); items = phone_items()
    hd = header(sw, items[0]['av']); ib = inputbar(sw); vis = sh - HDR - INP; smask = rr_mask(sw, sh, 62)
    tg = []; prev = 0
    for it in items:
        bot = it['y'] + it['img'].height + 24; tgt = max(0, bot - vis); tg.append((it['t'], prev, tgt)); prev = max(prev, tgt)
    def scroll(t):
        s = 0
        for (a_, p0, p1) in tg:
            if t >= a_: s = p0 + (p1 - p0) * ease((t - a_) / .35)
        return s
    n = int(round(PHD * FPS))
    for fi in range(n):
        t = fi / FPS; scr = bg.copy(); sc = scroll(t); C = Image.new('RGBA', (sw, vis), (0, 0, 0, 0))
        for it in items:
            if t < it['t']: continue
            u = t - it['t']; y = it['y'] - sc; k = ease(u / .25); spr = it['img'] if k >= 1 else tint_alpha(it['img'], k)
            _paste(C, spr, it['x'], int(y + (1 - k) * 30))
            _paste(C, it['av'] if k >= 1 else tint_alpha(it['av'], k), 22, int(y + (1 - k) * 30))
            if it['kind'] == 'typing':
                dd = ImageDraw.Draw(C)
                for j in range(3):
                    ph_ = (math.sin((u * 2.4 - j * .22) * 2 * math.pi) + 1) / 2
                    dd.ellipse([it['x'] + 38 + j * 26 - 7, int(y) + 38 - 7 - ph_ * 5, it['x'] + 38 + j * 26 + 7, int(y) + 38 + 7 - ph_ * 5], fill=(150, 120, 96, int(140 + 115 * ph_)))
        scr.alpha_composite(C, (0, HDR)); scr.alpha_composite(hd, (0, 0)); scr.alpha_composite(ib, (0, sh - INP))
        scr.putalpha(ImageChops.multiply(scr.split()[3], smask))
        ph = shell.copy(); ph.alpha_composite(scr, (o + INS, o + INS))
        k = eob(t / .42, 1.6) if t < .42 else 1.0; op = clamp(t / .15)
        L = canvas(); blit(L, ph, 540, PY0 + PHH / 2 + (1 - clamp(t / .42)) * 260, k if k < 1 else 1., op)
        if t > PHD - .3: L = tint_alpha(L, clamp((PHD - t) / .3))
        add('X-phone', '聊天手机（逐帧）', PH0 + t, 1 / FPS, save(L, f'ph{fi:03d}'))
    for it in items: sfx('u_msg', PH0 + it['t'], .28)
    # 口播字幕（下方）
    global MSUBY
    s0 = MSUBY; MSUBY = 1330 + 150
    put_subs(VOL, lambda r: VO0 + r, 'vo', limit=lambda v: EC0)
    MSUBY = s0

# ---------------- 片尾卡 ----------------
END_COPY = ('彼を部屋に入れたの、', '間違いだったかな？')
BTN = '今すぐ無料で話す'
def endcard():
    E0 = EC0; pf, rf = pointer_imgs()
    im = frame(11.9).filter(ImageFilter.GaussianBlur(6)); im = ImageEnhance.Brightness(im).enhance(.5)
    a = np.asarray(im).astype(np.float32); yy = np.arange(H, dtype=np.float32)[:, None, None]
    shade = np.clip((yy - 760) / 600, 0, 1) * .75 + np.clip(1 - yy / 520, 0, 1) * .5
    a = a * (1 - shade) + np.array([16, 10, 6], np.float32) * shade
    add('V1', '片尾 背景', E0, ED, save(Image.fromarray(a.astype(np.uint8)).convert('RGBA'), 'end_bg'), k={'scale': kf((0, 1.0), (ED, 1.06))})
    add('X-flash', '片尾 闪光', E0, .3, FLASH, k={'opacity': kf((0, .6), (.3, 0))})
    sfx('u_flash', E0 - .02, .4)
    add('X-elogo', '片尾 Logo', E0 + .05, ED - .05, save(logo_row(y=330), 'end_logo'), k={'opacity': kf((0, 0), (.25, 1)), 'y': kf((0, -20), (.3, 0))})
    L = canvas(); text(L, (540, 1010), END_COPY[0], font(NOTO, 72), WH, anchor='ms', shadow=.9)
    add('X-ecopy1', '片尾 文案1', E0 + .2, ED - .2, save(L, 'end_copy1'), k={'opacity': kf((0, 0), (.25, 1)), 'y': kf((0, 22), (.3, 0))})
    L = canvas(); f = font(NOTO, 92); s = END_COPY[1]
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text((540, 1150), s, font=f, fill=255, anchor='ms'); gl = Image.new('RGBA', (W, H), AMB + (0,)); gl.putalpha(m.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * .5))); L.alpha_composite(gl)
    text(L, (540, 1150), s, f, anchor='ms', shadow=.9, grad=AMBG, stroke=4, scol=AMB_D)
    add('X-ecopy2', '片尾 文案2', E0 + .4, ED - .4, save(L, 'end_copy2'), ay=1115 / H, k={'opacity': kf((0, 0), (.2, 1)), 'scale': kf((0, 1.22), (.14, .96), (.26, 1))})
    sfx('u_pop2', E0 + .4, .4)
    bx0, by0, bx1, by1 = 180, 1330, 900, 1460; bw, bh = bx1 - bx0, by1 - by0
    L = canvas()
    G = Image.new('L', (W, H), 0); ImageDraw.Draw(G).rounded_rectangle([bx0, by0 + 8, bx1, by1 + 8], radius=65, fill=120)
    G = G.filter(ImageFilter.GaussianBlur(30)); gc = Image.new('RGBA', (W, H), AMB + (0,)); gc.putalpha(G); L.alpha_composite(gc)
    btn = grad_img(bw, bh, [(0, (255, 210, 140)), (.5, (255, 168, 72)), (1, (226, 118, 40))]).convert('RGBA')
    mk = rr_mask(bw, bh, 65); btn.putalpha(mk); L.alpha_composite(btn, (bx0, by0))
    text(L, (540, (by0 + by1) / 2 + 2), BTN, font(NOTO, 56), (52, 22, 4), anchor='mm', shadow=0)
    BS = E0 + .55; TAPS = [1.25, 1.55, 1.85, 2.4, 2.7]
    bsc = [[0, .7], [.18, 1.05], [.28, 1]]
    for tp in TAPS: r = E0 + tp - BS; bsc += [[round(r - .04, 3), 1], [round(r + .04, 3), .94], [round(r + .16, 3), 1]]
    add('X-ebtn', '片尾 下载按钮', BS, END1 - BS, save(L, 'end_btn'), ay=(by0 + by1) / 2 / H, k={'scale': sorted(bsc), 'opacity': kf((0, 0), (.12, 1))})
    sfx('u_pop2', BS, .4)
    bma = np.asarray(mk).astype(np.float32) / 255; yy, xx = np.mgrid[0:bh, 0:bw]
    for j in range(8):
        c = -80 + j * 130; band = np.clip(1 - np.abs((xx + (yy - 65) * .5) - c) / 60, 0, 1) ** 2 * .5
        S = canvas(); s_ = Image.new('RGBA', (bw, bh), (255, 255, 255, 0)); s_.putalpha(Image.fromarray((bma * band * 255).astype(np.uint8))); S.alpha_composite(s_, (bx0, by0))
        fn = save(S, f'end_sheen{j}')
        for st in (E0 + .85, E0 + 2.05): add('X-esheen', '片尾 按钮扫光', st + j / 15, 1 / 15, fn)
    gp = Image.open(ASSET + 'Google_Play_Badge_JA.svg.png').convert('RGBA'); gp = gp.resize((int(gp.width * 88 / gp.height), 88), Image.LANCZOS)
    ios = Image.open(ASSET + 'ios_badge.png').convert('RGBA'); ios = ios.crop(ios.split()[3].getbbox()); ios = ios.resize((int(ios.width * 88 / ios.height), 88), Image.LANCZOS)
    inner = ios.crop((8, 6, ios.width - 8, ios.height - 6))
    nb = Image.new('RGBA', gp.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(nb)
    bd.rounded_rectangle([0, 0, gp.width - 1, gp.height - 1], radius=14, fill=(0, 0, 0, 255), outline=(166, 166, 166, 255), width=2)
    nb.alpha_composite(inner, ((gp.width - inner.width) // 2, (gp.height - inner.height) // 2)); ios = nb
    gap = 28; tot = gp.width + gap + ios.width; x0 = (W - tot) // 2
    Sb = canvas(); Sb.alpha_composite(gp, (x0, 1570)); Sb.alpha_composite(ios, (x0 + gp.width + gap, 1570))
    add('X-ebadge', '片尾 商店标', E0 + .7, ED - .7, save(Sb, 'end_badges'), k={'opacity': kf((0, 0), (.22, 1)), 'y': kf((0, 20), (.28, 0))})
    px, py = bx1 - 100 - 540, (by0 + by1) / 2 + 12 - 960
    P0 = 1.0; sc = [[0, 1]]
    for tp in TAPS: r = tp - P0; sc += [[round(r - .04, 3), 1], [round(r + .03, 3), .8], [round(r + .13, 3), 1]]
    add('X-eptr', '片尾 指针', E0 + P0, ED - P0, pf, k={'x': kf((0, px + 140), (.2, px)), 'y': kf((0, py + 240), (.2, py)), 'opacity': kf((0, 0), (.1, 1)), 'scale': sc})
    for i, tp in enumerate(TAPS):
        add(f'X-erip{i % 2 + 1}', '片尾 点击波纹', E0 + tp, min(.4, ED - tp), rf, k={'x': kf((0, px)), 'y': kf((0, py)), 'scale': kf((0, .7), (.4, 2.0)), 'opacity': kf((0, .9), (.4, 0))})
        sfx('u_click', E0 + tp, .55)

TRACKS = [
    ('X-dan', '弹幕（逐帧·人物遮挡）', 'title'),
    ('X-vig', '心跳暗角', 'title'), ('X-shade', '选项底部压暗', 'title'),
    ('X-intro1', '开场 上屏', 'title'), ('X-intro2', '开场 下屏', 'title'), ('X-intro5', '开场 分隔线', 'title'),
    ('X-intro3', '开场 标签上', 'title'), ('X-intro4', '开场 标签下', 'title'), ('X-intro6', '开场 标题', 'title'), ('X-intro7', '开场 Logo', 'title'),
    ('X-sub1', '字幕1', 'title'), ('X-sub2', '字幕2', 'title'), ('X-sub3', '字幕3', 'title'), ('X-sub4', '字幕4', 'title'),
    ('X-meter', 'ドキドキ 心动值', 'meter'), ('X-meterp', '心动值 +N', 'meter'),
    ('X-ch1', '选项 左', 'choice'), ('X-ch2', '选项 右', 'choice'), ('X-cd', '倒计时 轨', 'choice'), ('X-cd2', '倒计时 条', 'choice'),
    ('X-ptr', '选项 指针', 'choice'), ('X-rip', '选项 波纹', 'choice'),
    ('X-phone', '聊天手机（逐帧）', 'end'),
    ('X-elogo', '片尾 Logo', 'end'), ('X-ecopy1', '片尾 文案1', 'end'), ('X-ecopy2', '片尾 文案2', 'end'),
    ('X-ebtn', '片尾 下载按钮', 'end'), ('X-esheen', '片尾 按钮扫光', 'end'), ('X-ebadge', '片尾 商店标', 'end'),
    ('X-eptr', '片尾 指针', 'end'), ('X-erip1', '片尾 波纹1', 'end'), ('X-erip2', '片尾 波纹2', 'end'),
    ('X-flash', '闪光', 'end'),
]

FLASH = SHADE = None
def build(skip_phone=False):
    global FLASH, SHADE
    os.makedirs(OUT, exist_ok=True)
    FLASH = save(Image.new('RGBA', (W, H), (255, 248, 236, 255)), 'flash'); SHADE = shade_bottom()
    make_beats()
    intro(); meter(); freeze1(); freeze2(); subs(); danmaku_all()
    if not skip_phone: phone()
    endcard()
    meta = {'tracks': TRACKS, 'layers': LAY, 'off': OFF, 'cut': CUT, 'sh2': round(SH2, 4), 'fz1': FZ1, 'f1': round(F1, 4), 'f2': round(F2, 4), 'vstop': VSTOP, 'aend': AEND,
            'ph0': PH0, 'ec0': EC0, 'ed': ED, 'end1': round(END1, 4), 'vo0': VO0, 'sfx': SFX, 'beats': BEATS}
    json.dump(meta, open(os.path.join(PK, 'layers.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('layers', len(LAY), 'files', len({l['file'] for l in LAY}), 'sfx', len(SFX), 'end', END1)

if __name__ == '__main__':
    import sys
    if '--clean' in sys.argv:
        for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))
    build(skip_phone='--nophone' in sys.argv)
