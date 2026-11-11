# -*- coding: utf-8 -*-
"""伪人义妹敲门 · v2 监控 HUD 包装（重新设计）
- 人脸框：动漫人脸检测（工作区/faces_raw*.json）+ 平滑 + 手工补点（遮挡/低头/阴影脸）
- 字幕：文字识别效果，挂在人脸框下方随框移动；逐字按 ASR 时间浮现（乱码→定字，上浮淡入）
- 所有 UI：广角桶形畸变 + 边缘色散；选项/识别框加扫描线和半透明
- 选项：半透明圆圈指针 → 点击 → 其他选项消失 → 正确项闪烁 → 黑幕过渡
- 无开头标题；片尾重做
用法：python gen.py [check]
"""
import os, sys, json, random, math, subprocess, wave
sys.path.insert(0, 'C:/Users/zhonghaiming5328/cv4')
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(P, '包装素材v2'); TMP = os.path.join(P, '工作区')
VIDEO = os.path.join(P, '素材', '视频 (70).mp4')
W, H = 1080, 1920
LOC = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Fonts')
DOT = os.path.join(LOC, 'DotGothic16-Regular.ttf')
MINB = os.path.join(LOC, 'ZenOldMincho-Bold.ttf')
MINK = os.path.join(LOC, 'ZenOldMincho-Black.ttf')
ASSET = 'F:/钟海明/MM透明尾板/片尾/片尾文件夹/(素材)/图片/'
APPA = 'F:/钟海明/2026/2026年10月10日MM-编辑器重构/app/public/assets/'
Y = (255, 212, 0)
WH = (242, 242, 236)
V = 'a'
REF = (540, 960)
FPS_UI = 15

# ---------------- 时间轴 ----------------
SEG = [(0.0, 9.60, 0.0), (10.35, 19.55, 3.65), (20.15, 29.7167, 7.45)]      # 源起, 源止, 偏移
FRZ = [(9.60, 4.4, 9.55), (23.20, 4.4, 19.50), (37.1667, 4.6, 29.65)]       # 输出起, 时长, 定格源帧
END0, ED = 41.7667, 3.0
END1 = END0 + ED
def o(src):
    for a, b, off in SEG:
        if a - 1e-6 <= src <= b + 1e-6: return src + off
    raise ValueError(src)
def to_src(t):
    for i, (a, b, off) in enumerate(SEG):
        if a + off - 1e-6 <= t < b + off: return 'seg', i, t - off
    for i, (s0, d, fr) in enumerate(FRZ):
        if s0 - 1e-6 <= t < s0 + d: return 'frz', i, fr
    return 'end', None, None
SEG_END_SRC = [s[1] for s in SEG]

T_A0 = 1.0                  # 人脸框出现
T_B0 = 9.0                  # 老人框出现
T_BV = o(19.0)              # 老人框消失 22.65
T_DROP = o(22.7)            # 低头：数值崩坏 30.15
T_SW = o(23.15)             # 标签跳成 84 男性 30.6
GLITCH = [(T_B0, T_B0 + .27), (T_BV, T_BV + .32), (T_DROP, T_SW + .15)]

# ---------------- 基础 ----------------
FONTS = {}
def font(p, s):
    if (p, s) not in FONTS: FONTS[(p, s)] = ImageFont.truetype(p, s)
    return FONTS[(p, s)]
def canvas(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))
def save(im, name):
    fn = f'{name}_{V}' + ('b' if name.startswith('end') else ''); im.save(os.path.join(OUT, fn + '.png'), compress_level=1); return fn
def glow(layer, r, color, strength=1.0):
    a = layer.split()[3].filter(ImageFilter.GaussianBlur(r))
    if strength != 1: a = a.point(lambda v: min(255, int(v * strength)))
    g = Image.new('RGBA', layer.size, color + (0,)); g.putalpha(a); return g
def stack(*ls):
    c = canvas()
    for l in ls: c.alpha_composite(l)
    return c
def text(L, xy, s, f, fill, anchor='la', stroke=0, sf=(0, 0, 0)):
    ImageDraw.Draw(L).text(xy, s, font=f, fill=fill if len(fill) == 4 else fill + (255,), anchor=anchor,
                           stroke_width=stroke, stroke_fill=sf if len(sf) == 4 else sf + (255,))
def readable(T, ycol=Y, ys=.35):
    """文字层：黑色柔影 + 轻微黄光"""
    return stack(glow(T, 5, (0, 0, 0), 1.8), glow(T, 12, ycol, ys), T)

# 广角桶形畸变 + 边缘色散（UI 统一后处理）
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_dx, _dy = _xx - W / 2, _yy - H / 2
_r2 = (_dx * _dx + _dy * _dy) / ((W / 2) ** 2 + (H / 2) ** 2)
def _mk(k): f = 1 + k * _r2; return (W / 2 + _dx * f).astype(np.float32), (H / 2 + _dy * f).astype(np.float32)
MAPS = [_mk(.112), _mk(.100), _mk(.088)]
del _yy, _xx
def fx(im, scan=0.0, alpha=1.0):
    bb = im.getbbox()
    if not bb: return im
    m = 140
    x0, y0, x1, y1 = max(0, bb[0] - m), max(0, bb[1] - m), min(W, bb[2] + m), min(H, bb[3] + m)
    src = np.asarray(im, dtype=np.float32) / 255.
    a = np.ascontiguousarray(src[..., 3])
    cs, al = [], []
    for i in range(3):
        mx, my = MAPS[i]
        two = np.dstack([src[..., i] * a, a])
        r = cv2.remap(two, mx[y0:y1, x0:x1], my[y0:y1, x0:x1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        cs.append(r[..., 0]); al.append(r[..., 1])
    A = np.maximum(np.maximum(al[0], al[1]), al[2])
    sa = np.maximum(A, 1e-4)
    rgb = np.dstack([c / sa for c in cs])
    if scan: A = A * np.where((np.arange(y0, y1) % 4) < 2, 1.0, 1 - scan)[:, None]
    A = A * alpha
    out = np.zeros((H, W, 4), np.float32)
    out[y0:y1, x0:x1] = np.dstack([np.clip(rgb, 0, 1), np.clip(A, 0, 1)])
    return Image.fromarray((out * 255 + .5).astype(np.uint8), 'RGBA')

LAY = []
def add(track, name, start, dur, file, ax=.5, ay=.5, k=None):
    s = round(start * 30 + 1e-6) / 30; e = round((start + dur) * 30 + 1e-6) / 30
    if e - s < 1 / 30 - 1e-6: return
    LAY.append({'track': track, 'name': name, 'start': round(s, 4), 'dur': round(round(e, 4) - round(s, 4), 4), 'file': file,
                'ax': round(ax, 4), 'ay': round(ay, 4), 'k': k or {}})
def kf(*pts): return [[round(p[0], 3), round(p[1], 3)] + ([p[2]] if len(p) > 2 else []) for p in pts]
def fl(*pts): return [[round(t, 3), round(v, 3), 'hold'] for t, v in pts]

# ---------------- 人脸跟踪 ----------------
def build_track():
    r1 = json.load(open(os.path.join(TMP, 'faces_raw.json'))); r2 = json.load(open(os.path.join(TMP, 'faces_raw2.json')))
    n = len(r1); FR = 24.0
    trk = [None] * n; prev = None; pi = -99
    for i in range(n):
        best = None
        for (x, y, w, h) in [tuple(c) for c in r1[i]['f']] + [tuple(c) for c in r2[i]['f']]:
            if w < .2: continue
            c = (x + w / 2, y + h / 2, w, h)
            if prev is not None and i - pi < 12:
                dist = abs(c[0] - prev[0]) + abs(c[1] - prev[1]); ratio = c[2] / prev[2]
                if dist > .1 or not (.75 < ratio < 1.33): continue
                sc = dist
            else: sc = 0
            if best is None or sc < best[0]: best = (sc, c)
        if best: trk[i] = best[1]; prev = best[1]; pi = i
    def clear(a, b):
        for i in range(n):
            if a <= i / FR <= b: trk[i] = None
    def put(t, c): trk[min(n - 1, int(round(t * FR)))] = c
    clear(9.62, 10.3); clear(19.6, 20.2); clear(6.7, 8.85)
    clear(22.55, 23.72); put(23.0, (.35, .52, .40, .24)); put(23.4, (.39, .50, .42, .25))
    clear(24.6, 30.1)
    for t, c in [(24.6, (.385, .475, .44, .25)), (26.8, (.385, .475, .44, .25)), (27.0, (.40, .52, .50, .29)), (27.5, (.40, .56, .60, .34)),
                 (28.0, (.40, .57, .62, .35)), (29.0, (.42, .58, .62, .35)), (29.75, (.42, .58, .62, .35))]: put(t, c)
    # 分幕插值 + 平滑
    res = [None] * n
    for a, b in [(0, 9.65), (10.3, 19.6), (20.1, 30.1)]:
        idx = [i for i in range(n) if a <= i / FR <= b]
        known = [i for i in idx if trk[i] is not None]
        for i in idx:
            pv = [k for k in known if k <= i]; nx = [k for k in known if k >= i]
            if pv and nx:
                p0, p1 = pv[-1], nx[0]; u = 0 if p1 == p0 else (i - p0) / (p1 - p0)
                res[i] = tuple(trk[p0][j] + (trk[p1][j] - trk[p0][j]) * u for j in range(4))
            else: res[i] = trk[(pv or nx)[-1 if pv else 0]]
        sm = {}
        for i in idx:
            win = [res[k] for k in idx if abs(k - i) <= 3]
            sm[i] = tuple(sum(w[j] for w in win) / len(win) for j in range(4))
        for i in idx: res[i] = sm[i]
    return res, FR
TRK, TFR = build_track()
def geo(src):
    i = src * TFR; a = int(math.floor(i)); u = i - a
    a = max(0, min(len(TRK) - 1, a)); b = min(len(TRK) - 1, a + 1)
    A, B = TRK[a], TRK[b]
    if A is None or B is None: A = B = A or B
    return tuple(A[j] + (B[j] - A[j]) * u for j in range(4))
def box_px(src, expand=1.06):
    cx, cy, w, h = geo(src)
    return cx * W, cy * H, w * W * expand, h * H * expand

# ---------------- 字幕（ASR 逐字时间） ----------------
PUN = set('、。？?！!…「」 ，,')
SUBDEF = [
    ((0.3, 3.1), ['お兄ちゃん、りんご買ってきたよ'], False),
    ((3.1, 7.3), ['えへへ、パパとママ、', '明日も帰ってこないよ'], False),
    ((7.3, 9.6), ['入れて'], False),
    ((10.2, 13.5), ['バカお兄ちゃん、脅かさないでよ'], False),
    ((13.5, 15.6), ['もう朝の4時だよ'], False),
    ((15.6, 19.5), ['開けてくれないと、', 'おっきくて丸いの、あげないよ？'], False),
    ((20.1, 23.5), ['暗号は……0.01'], False),
    ((24.0, 27.0), ['お兄ちゃん、正解でしょ？'], False),
    ((27.0, 29.7), ['入れて……くれんかのう'], True),
]
def energy_db():
    w = wave.open(os.path.join(TMP, 'mmvp', 'voice16k.wav')); sr = w.getframerate(); ch = w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch > 1: x = x.reshape(-1, ch).mean(1)
    hop = int(sr * .01); n = len(x) // hop
    return 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12))
def build_subs():
    asr = json.load(open(os.path.join(TMP, 'asr_acts.json'), encoding='utf-8'))
    db = energy_db()
    subs = []
    for li, ((a, b), lines, ghost) in enumerate(SUBDEF):
        toks = [w for w in asr if a <= w['s'] < b]
        ac = []
        for ti, w in enumerate(toks):
            s, e = w['s'], w['e']
            if ti == 0:   # 行首：以能量起点校正（whisper 行首常偏早）
                seg = db[int(max(0, (s - .15)) * 100):int((s + .7) * 100)]
                thr = db[int(a * 100):int(b * 100)].max() - 24
                hit = np.nonzero(seg > thr)[0]
                if len(hit): s = max(s, (int(max(0, (s - .15)) * 100) + hit[0]) / 100.)
                e = max(e, s + .05)
            cs = [c for c in w['w'].strip() if c not in PUN]
            for j, c in enumerate(cs): ac.append(s + (e - s) * j / max(1, len(cs)))
        ac.sort()
        flat = ''.join(lines)
        sc = [i for i, c in enumerate(flat) if c not in PUN]
        times = [None] * len(flat)
        for k, i in enumerate(sc):
            times[i] = ac[min(len(ac) - 1, round(k * (len(ac) - 1) / max(1, len(sc) - 1)))]
        last = times[sc[0]]
        for i in range(len(flat)):
            if times[i] is None: times[i] = last + .03
            last = times[i]
        end = max(w['e'] for w in toks)
        subs.append({'lines': lines, 'times': times, 'start': min(times) - .06, 'end': end, 'ghost': ghost})
    for i, s in enumerate(subs):
        se = min(x for x in SEG_END_SRC if x >= s['end'] - 1e-6)
        nxt = subs[i + 1]['start'] - .1 if i + 1 < len(subs) else 99
        s['hide'] = min(nxt, s['end'] + 1.0, se - .02)
    return subs
SUBS = build_subs()

SCR = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモラリルレロワン#%&@?0123456789'
def draw_chars(L, x, y, s, f, t, times, fill=WH, dur=.22, rise=18, scramble=True, anchor='l', newcol=Y, seed=0):
    d = ImageDraw.Draw(L)
    ws = [f.getlength(c) for c in s]
    if anchor == 'c': x -= sum(ws) / 2
    for i, ch in enumerate(s):
        p = (t - times[i]) / dur
        if p > 0:
            p = min(1.0, p); a = int(255 * p ** .6); dy = (1 - p) ** 2 * rise
            g = ch
            if scramble and p < .55 and ch not in PUN and ch not in '.':
                g = random.Random(int(t * 30) * 977 + i * 31 + seed).choice(SCR)
            col = newcol if p < 1 else fill
            d.text((x, y + dy), g, font=f, fill=col + (a,))
        x += ws[i]
    return x

# ---------------- 跟踪层（人脸框A + 老人框B + 字幕），15fps 合成 ----------------
def corners(d, cx, cy, w, h, col, a, arm=None, wid=4):
    arm = arm or max(26, min(70, .2 * min(w, h)))
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    for (x, y, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(x, y + sy * arm), (x, y), (x + sx * arm, y)], fill=col + (a,), width=wid, joint='curve')
def box_layer(L, cx, cy, w, h, alpha, t_loop, appear_k=1.0):
    d = ImageDraw.Draw(L); A = int(255 * alpha)
    s = 1 + .55 * (1 - appear_k) ** 2; w2, h2 = w * s, h * s
    x0, y0, x1, y1 = cx - w2 / 2, cy - h2 / 2, cx + w2 / 2, cy + h2 / 2
    d.rectangle([x0, y0, x1, y1], fill=Y + (int(16 * alpha),), outline=Y + (int(70 * alpha),), width=1)
    corners(d, cx, cy, w2, h2, Y, A)
    # 中心十字
    d.line([(cx - 10, cy), (cx + 10, cy)], fill=Y + (int(110 * alpha),), width=2); d.line([(cx, cy - 10), (cx, cy + 10)], fill=Y + (int(110 * alpha),), width=2)
    # 扫描线（循环）
    fr = (t_loop % 1.6) / 1.6 if appear_k >= 1 else appear_k
    sy = y0 + fr * h2
    for k in range(18):
        yy = sy - k * 3
        if yy < y0: break
        d.line([(x0 + 3, yy), (x1 - 3, yy)], fill=Y + (int((70 if k else 200) * alpha * (1 - k / 18)),), width=2 if k == 0 else 1)
def label_layer(L, x, y, lines, alpha, t, times=None, jitter=0):
    f = font(DOT, 30); d = ImageDraw.Draw(L)
    wmax = max(f.getlength(s) for s in lines) + 30
    hh = 22 + len(lines) * 38
    d.rectangle([x, y, x + wmax, y + hh], fill=(0, 0, 0, int(140 * alpha)))
    d.line([(x, y), (x, y + hh)], fill=Y + (int(255 * alpha),), width=4)
    T = canvas()
    for n, s in enumerate(lines):
        tm = times[n] if times else [-9] * len(s)
        draw_chars(T, x + 16 + jitter, y + 10 + n * 38, s, f, t, tm, fill=Y, newcol=WH, dur=.12, rise=8)
    if alpha < 1: T.putalpha(T.split()[3].point(lambda v: int(v * alpha)))
    L.alpha_composite(T)
    return hh
LA = ['年齢 : @&?%', '性別 : 女性']; LM = ['年齢 : 84', '性別 : 男性']
B_POS = [(T_B0, (.80, .19, .22, .13)), (FRZ[0][0] + FRZ[0][1], (.80, .19, .22, .13)), (o(10.6), (.85, .31, .20, .14)), (T_BV + .5, (.85, .32, .20, .14))]
def b_geo(t):
    for (ta, a), (tb, b) in zip(B_POS, B_POS[1:]):
        if ta <= t <= tb:
            if t < o(10.35) and ta < o(10.35) <= tb: return a     # 段 1+定格 保持
            u = (t - ta) / max(1e-6, tb - ta); return tuple(a[j] + (b[j] - a[j]) * u for j in range(4))
    return B_POS[-1][1]
def flick(t0, t, seq=(1, .15, 1, .35, 1), step=.07):
    k = int((t - t0) / step); return seq[k] if 0 <= k < len(seq) else 1
def render_tracker(t):
    kind, i, src = to_src(t)
    L = canvas()
    rnd = random.Random(int(t * 30))
    # ---- B ----
    if T_B0 <= t < T_BV + .32:
        cx, cy, w, h = b_geo(t); cx *= W; cy *= H; w *= W; h *= H
        cx += rnd.uniform(-1.5, 1.5); cy += rnd.uniform(-1.5, 1.5)
        ak = min(1, (t - T_B0) / .35); al = flick(T_B0, t)
        if t >= T_BV: al = [1, 0, 1, 0, .8][min(4, int((t - T_BV) / .065))]
        if al > 0:
            box_layer(L, cx, cy, w, h, al, t - T_B0, ak)
            tms = [[T_B0 + .25 + j * .05 for j in range(len(s))] for s in LM]
            label_layer(L, cx - w / 2, cy + h / 2 + 10, LM, al, t, tms)
    # ---- A ----
    if t >= T_A0 and kind != 'end':
        gsrc = src
        cx, cy, w, h = box_px(gsrc)
        cx += rnd.uniform(-1.5, 1.5); cy += rnd.uniform(-1.5, 1.5)
        al = flick(T_A0, t) * (.38 if kind == 'frz' else 1)
        ak = min(1, (t - T_A0) / .35)
        box_layer(L, cx, cy, w, h, al, t - T_A0, ak)
        # 标签（框外左上）
        lines, jit = LA, 0
        if T_DROP <= t < T_SW + .15:
            lines = LM if int(t * 15) % 3 == 0 else LA; jit = rnd.uniform(-10, 10)
        elif t >= T_SW: lines = LM
        tms = [[T_A0 + .3 + j * .05 for j in range(len(s))] for s in lines]
        if t >= T_SW: tms = [[T_SW + .15 + j * .05 for j in range(len(s))] for s in lines]
        lx = max(60, min(W - 300, cx - w / 2)); ly = max(330, cy - h / 2 - 108)
        label_layer(L, lx, ly, lines, al, t, tms, jit)
        # 字幕（框下方）
        if kind == 'seg':
            for s in SUBS:
                if s['start'] <= src < s['hide']:
                    f = font(DOT, 46); lh = 62
                    widths = [f.getlength(x) for x in s['lines']]
                    bw = max(widths) + 56; bh = 30 + lh * len(s['lines'])
                    bx = max(70, min(W - 70 - bw, cx - bw / 2)); by = min(cy + h / 2 + 24, 1830 - bh)
                    fa = min(1, (src - s['start']) / .15) * min(1, (s['hide'] - src) / .2)
                    d = ImageDraw.Draw(L)
                    d.rectangle([bx, by, bx + bw, by + bh], fill=(0, 0, 0, int(135 * fa)))
                    for (x, yv, sx, sy) in [(bx, by, 1, 1), (bx + bw, by + bh, -1, -1)]:
                        d.line([(x, yv + sy * 20), (x, yv), (x + sx * 20, yv)], fill=Y + (int(255 * fa),), width=3)
                    T = canvas(); off = 0; endx, endy = bx + 28, by + 14
                    for n, line in enumerate(s['lines']):
                        tm = s['times'][off:off + len(line)]; off += len(line)
                        yv = by + 14 + n * lh
                        if s['ghost']:
                            jx = rnd.uniform(-3, 3)
                            draw_chars(T, bx + 28 + 5 + jx, yv + 3, line, f, src, tm, fill=(200, 25, 35), newcol=(200, 25, 35), seed=7)
                        xe = draw_chars(T, bx + 28, yv, line, f, src, tm)
                        if any(src >= x for x in tm): endx, endy = xe, yv
                    if fa < 1: T.putalpha(T.split()[3].point(lambda v: int(v * fa)))
                    L.alpha_composite(readable(T, Y, .25))
                    if src < s['times'][-1] + .3 and int(t * 15) % 2 == 0:
                        ImageDraw.Draw(L).rectangle([endx + 4, endy + 6, endx + 10, endy + 50], fill=Y + (230,))
    return L
def tracker():
    n0 = int(round(T_A0 * FPS_UI)); n1 = int(round(END0 * FPS_UI))
    for n in range(n0, n1):
        t = n / FPS_UI
        f = save(fx(render_tracker(t), scan=.32), f'trk{n:04d}')
        add('X-trk', '识别框+字幕', t, 1 / FPS_UI, f)

# ---------------- 监控 HUD ----------------
def hud():
    L = canvas(); d = ImageDraw.Draw(L); m, a, w = 44, 90, 4
    for (x, y, sx, sy) in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line([(x, y + sy * a), (x, y), (x + sx * a, y)], fill=Y + (255,), width=w, joint='curve')
    for k in range(9):   # 左右刻度
        yy = 700 + k * 65; ln = 22 if k % 4 == 0 else 12
        d.line([(m, yy), (m + ln, yy)], fill=Y + (150,), width=2); d.line([(W - m, yy), (W - m - ln, yy)], fill=Y + (150,), width=2)
    T = canvas(); text(T, (84, 74), 'CAM 01 玄関', font(DOT, 36), Y)
    L.alpha_composite(readable(T, Y, .5))
    add('X-hud', '监控 边角+CAM', 0, END1, save(fx(L), 'hud'), k={'opacity': kf((0, 0), (.25, 1))})
    vg = Image.new('L', (W, H), 0); vd = ImageDraw.Draw(vg)
    for i in range(60):
        k = i / 60; vd.rounded_rectangle([k * 170, k * 280, W - k * 170, H - k * 280], radius=220, outline=int(175 * (1 - k) ** 1.5), width=6)
    vg = vg.filter(ImageFilter.GaussianBlur(60))
    blk = Image.new('RGBA', (W, H), (0, 0, 0, 0)); blk.putalpha(vg)
    sl = canvas(); sd = ImageDraw.Draw(sl)
    for yy in range(0, H, 4): sd.line([(0, yy), (W, yy)], fill=(0, 0, 0, 40), width=2)
    add('X-vig', '监控 暗角扫描线', 0, END1, save(stack(blk, sl), 'vignette'))
    # 滚动光带
    B = canvas(); bd = ImageDraw.Draw(B)
    for k in range(-150, 151):
        bd.line([(0, 960 + k), (W, 960 + k)], fill=(220, 255, 220, int(16 * math.cos(k / 150 * math.pi / 2) ** 2)))
    bf = save(B, 'rollband'); t = 0
    while t < END1 - .05:
        d = min(5.0, END1 - t)
        add('X-roll', '监控 滚动光带', t, d, bf, k={'y': kf((0, -1150, 'linear'), (5.0, 1150))})
        t += 5.0
    t0 = 3 * 3600 + 59 * 60 + 44 - 1
    for s in range(int(math.ceil(END0))):
        tt = t0 + s + (0 if s < 14 else 3)
        C = canvas(); text(C, (W - 84, 78), f'2026/10/20 {tt // 3600:02d}:{tt // 60 % 60:02d}:{tt % 60:02d}', font(DOT, 32), Y, anchor='ra')
        add('X-clock', '时间', s, min(1, END0 - s), save(fx(readable(C, Y, .5)), f'clk{s:02d}'))

# ---------------- 人间度（实时） ----------------
MX, MY = 540, 120
BX0, BX1, BY = 340, 740, 270
def meter_values():
    rnd = random.Random(20); ev = []
    def run(t0, t1, lo, hi, step=(.22, .45)):
        t = t0
        while t < t1 - 1e-3:
            d = rnd.uniform(*step); ev.append((t, min(d, t1 - t), str(rnd.randint(lo, hi)))); t += d
    def ramp(t0, t1, a, b, n):
        for i in range(n): ev.append((t0 + (t1 - t0) * i / n, (t1 - t0) / n, str(round(a + (b - a) * (i + 1) / n))))
    ev.append((0, 1.0, '---'))
    ramp(1.0, 1.6, 0, 100, 8); run(1.6, T_B0, 97, 100)
    ramp(T_B0, 9.6, 100, 74, 6); run(9.6, 14.0, 70, 77)
    ramp(14.0, 14.8, 74, 52, 6); run(14.8, T_BV, 47, 55)
    ramp(T_BV, T_BV + .5, 52, 33, 5); run(T_BV + .5, T_DROP, 30, 36)
    t = T_DROP
    while t < T_DROP + .6: ev.append((t, .067, rnd.choice(['12', '0', '87', '3', '61', '9', '0']))); t += .067
    while t < END0 - 1e-3:
        d = rnd.uniform(.35, .7) if rnd.random() > .25 else .067
        s = '@&?%' if d > .1 else rnd.choice(['84', '0', '4', '#&?%'])
        ev.append((t, min(d, END0 - t), s)); t += d
    return ev
def meter():
    L = canvas(); d = ImageDraw.Draw(L)
    T = canvas(); text(T, (MX, MY), '人間度', font(DOT, 36), Y, anchor='mt'); L.alpha_composite(readable(T, Y, .4))
    d.rectangle([BX0, BY, BX1, BY + 12], outline=Y + (255,), width=2)
    for i in range(1, 10):
        x = BX0 + (BX1 - BX0) * i / 10; d.line([(x, BY + 14), (x, BY + 22)], fill=Y + (200,), width=2)
    add('X-mlab', '人間度 标签+底条', 0, END0, save(fx(L), 'm_lab'), k={'opacity': kf((0, 0), (.3, 1))})
    F = canvas(); ImageDraw.Draw(F).rectangle([BX0 + 4, BY + 4, BX1 - 4, BY + 8], fill=Y + (255,))
    fill = save(fx(stack(glow(F, 5, Y, 1), F)), 'm_fill')
    ev = meter_values(); cache = {}
    for t, dur, s in ev:
        if s not in cache:
            N = canvas(); text(N, (MX, MY + 46), s, font(DOT, 88), WH, anchor='mt')
            cache[s] = save(fx(readable(N, Y, .7)), 'mn_' + ''.join(c if c.isalnum() else {'@': 'a', '&': 'n', '?': 'q', '%': 'p', '#': 'h', '-': 'd'}[c] for c in s))
        add('X-mnum', '人間度 ' + s, t, dur, cache[s])
    sx = []
    for t, dur, s in ev:
        v = int(s) / 100 if s.isdigit() else (random.Random(int(t * 100)).uniform(.05, .95) if t >= T_DROP else 0)
        sx.append([round(t, 3), round(max(v, .001), 3), 'hold'])
    add('X-mbar', '人間度 填充', 0, END0, fill, ax=(BX0 + 4) / W, ay=(BY + 6) / H, k={'scaleX': sx})

# ---------------- 干扰撕裂 ----------------
def glitches():
    fs = []
    for v in range(3):
        rnd = random.Random(50 + v); G = canvas(); d = ImageDraw.Draw(G)
        for _ in range(9):
            y = rnd.randint(150, 1800); hh = rnd.randint(3, 16); x0 = rnd.randint(-200, 600)
            col = rnd.choice([Y, (80, 255, 255), (255, 60, 90), (255, 255, 255)])
            d.rectangle([x0, y, x0 + rnd.randint(300, 900), y + hh], fill=col + (rnd.randint(50, 120),))
        fs.append(save(G, f'glitch{v}'))
    for a, b in GLITCH:
        t, k = a, 0
        while t < b - 1e-3:
            add('X-glitch', '干扰', t, min(2 / 30, b - t), fs[k % 3]); t += 2 / 30; k += 1

# ---------------- 选项 ----------------
CH = [
    ('義妹のそばに、見えない老人が映った。\nどうする？', ['教える', '黙る', 'カメラを切る'], 0),
    ('老人の枠が消えた。\n開ける前に、どう確かめる？', ['暗号を聞く', 'フードを脱がせる'], 0),
    ('暗号は正解。でもスキャン結果は84歳の男。\n開ける？', ['開ける', '開けない'], None),
]
NUM = '①②③'
QX0, QX1, QY0 = 90, 990, 1150
OH, OG = 100, 18
def pointer_imgs():
    C = canvas(); d = ImageDraw.Draw(C); x, y = REF; r = 34
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 70), outline=(255, 255, 255, 210), width=3)
    d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 255, 255, 200))
    pf = save(stack(glow(C, 10, (255, 255, 255), .5), C), 'ptr')
    R = canvas(); ImageDraw.Draw(R).ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255, 230), width=3)
    return pf, save(R, 'ripple')
def float_seq(track, name, t0, t_end, items, base=None, scan=0.0, tag='fs'):
    """items: (x, y, text, font, times_rel, anchor, fill) 逐字上浮浮现；最后一帧保持到 t_end"""
    last = max(max(it[4]) for it in items) + .25
    n = int(math.ceil(last * FPS_UI))
    for k in range(n + 1):
        t = k / FPS_UI
        T = canvas()
        for (x, y, s, f, tm, anc, fill) in items: draw_chars(T, x, y, s, f, t, tm, fill=fill, anchor=anc, rise=22, dur=.25)
        L = stack(base, readable(T)) if base else readable(T)
        fn = save(fx(L, scan), f'{tag}_{k:02d}')
        add(track, name, t0 + t, (1 / FPS_UI) if k < n else (t_end - t0 - t), fn)
def choices():
    pf, rf = pointer_imgs()
    G = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(G)
    for yy in range(H): gd.line([(0, yy), (W, yy)], fill=int(60 + 150 * min(1, max(0, (yy - 850) / 350))))
    DM = Image.new('RGBA', (W, H), (0, 0, 0, 0)); DM.putalpha(G); dimf = save(DM, 'c_dim')
    SW = canvas(); sd = ImageDraw.Draw(SW)
    for k in range(30): sd.line([(QX0, 960 - k * 2), (QX1, 960 - k * 2)], fill=Y + (int((230 if k == 0 else 60) * (1 - k / 30)),), width=3 if k == 0 else 2)
    swf = save(SW, 'c_sweep')
    for ci, (q, opts, pick) in enumerate(CH):
        s0, D, _ = FRZ[ci]
        add('X-cdim', f'选项{ci + 1} 压暗', s0, D, dimf, k={'opacity': kf((0, 0), (.35, 1))})
        ql = q.split('\n'); fq = font(DOT, 42); qh = 40 + len(ql) * 58
        Q = canvas(); d = ImageDraw.Draw(Q)
        d.rectangle([QX0, QY0, QX1, QY0 + qh], fill=(0, 0, 0, 125))
        d.line([(QX0, QY0), (QX0, QY0 + qh)], fill=Y + (255,), width=6)
        d.line([(QX0, QY0), (QX0 + 170, QY0)], fill=Y + (255,), width=3); d.line([(QX1 - 170, QY0 + qh), (QX1, QY0 + qh)], fill=Y + (255,), width=3)
        add('X-cq', f'选项{ci + 1} 提问底', s0, D, save(fx(Q, .35), f'c{ci + 1}_qbg'), ax=.5, ay=(QY0 + qh / 2) / H,
            k={'opacity': kf((0, 0), (.2, 1)), 'scaleY': kf((0, .05), (.28, 1))})
        items, base_t = [], .3
        for n, s in enumerate(ql):
            items.append((QX0 + 36, QY0 + 22 + n * 58, s, fq, [base_t + j * .04 for j in range(len(s))], 'l', WH)); base_t += len(s) * .04
        float_seq('X-cqt', f'选项{ci + 1} 提问字', s0, s0 + D, items, scan=.2, tag=f'c{ci + 1}_qt')
        oy0 = QY0 + qh + 28
        oc = []
        for oi, s in enumerate(opts):
            y0 = oy0 + oi * (OH + OG); oc.append(y0 + OH / 2)
            def opt(fill_a, border, bw, numc, txtc, fillc=(0, 0, 0)):
                O = canvas(); d = ImageDraw.Draw(O)
                d.rectangle([QX0, y0, QX1, y0 + OH], fill=fillc + (fill_a,), outline=border, width=bw)
                T = canvas(); text(T, (QX0 + 40, y0 + OH // 2), NUM[oi], font(DOT, 50), numc, anchor='lm')
                text(T, (QX0 + 118, y0 + OH // 2), s, font(DOT, 48), txtc, anchor='lm')
                O.alpha_composite(readable(T, Y, .3) if txtc != (0, 0, 0) else T); return O
            base = save(fx(opt(105, Y + (200,), 2, Y, WH), .35), f'c{ci + 1}_o{oi + 1}')
            hov = save(fx(stack(glow(opt(60, Y + (255,), 4, Y, Y, Y), 14, Y, .8), opt(60, Y + (255,), 4, Y, Y, Y)), .3), f'c{ci + 1}_h{oi + 1}')
            sel = save(fx(stack(glow(opt(170, Y + (255,), 4, (0, 0, 0), (0, 0, 0), Y), 18, Y, 1), opt(170, Y + (255,), 4, (0, 0, 0), (0, 0, 0), Y)), .3), f'c{ci + 1}_s{oi + 1}')
            st = .55 + oi * .12
            intro = [(0, 0), (st, 0), (st + .3, 1)]
            if pick is not None:
                ok = intro + ([] if oi == pick else [(2.55, 1), (2.85, 0)])
                add(f'X-co{oi + 1}', f'选项{ci + 1}-{oi + 1}', s0, D, base, k={'opacity': kf(*ok), 'x': kf((0, -50), (st, -50), (st + .35, 0))})
                if oi == pick:
                    add('X-ch', f'选项{ci + 1} 悬停', s0 + 1.9, .5, hov, k={'opacity': kf((0, 0), (.12, 1))})
                    bl = fl((0, 1), (.5, .12), (.65, 1), (.8, .12), (.95, 1), (1.1, .12), (1.25, 1))
                    add('X-cs', f'选项{ci + 1} 选中闪烁', s0 + 2.4, D - 2.4, sel, ax=.5, ay=(y0 + OH / 2) / H,
                        k={'opacity': bl, 'scale': kf((0, 1.04), (.18, 1))})
            else:
                add(f'X-co{oi + 1}', f'选项{ci + 1}-{oi + 1}', s0, D, base, k={'opacity': kf(*intro), 'x': kf((0, -50), (st, -50), (st + .35, 0))})
                for a, b in ([(1.8, 2.35), (3.5, 4.0)] if oi == 0 else [(2.7, 3.2)]):
                    add('X-ch', f'选项3 犹豫{oi + 1}', s0 + a, b - a, hov, k={'opacity': kf((0, 0), (.1, 1), (b - a - .1, 1), (b - a, 0))})
        add('X-csw', f'选项{ci + 1} 扫描线', s0 + .5, .8, swf, k={'y': kf((0, QY0 - 960, 'linear'), (.7, oc[-1] + OH / 2 - 960)), 'opacity': kf((0, 0), (.08, 1), (.6, 1), (.8, 0))})
        # 指针
        tx = QX1 - 160
        def P(x, y): return x - REF[0], y - REF[1]
        if pick is not None:
            path = [(1.2, (960, 1880)), (1.9, (tx, oc[pick])), (2.2, (tx + 10, oc[pick] - 4)), (2.4, (tx + 6, oc[pick]))]
            pd = 2.8; clicks = [2.4]
        else:
            path = [(1.2, (960, 1880)), (1.8, (tx, oc[0])), (2.3, (tx - 8, oc[0] + 3)), (2.7, (tx - 20, oc[1])), (3.2, (tx - 26, oc[1] + 2)),
                    (3.5, (tx - 10, oc[0])), (3.62, (tx - 2, oc[0] + 2)), (3.74, (tx - 14, oc[0] - 1)), (3.86, (tx - 4, oc[0] + 1)), (3.98, (tx - 12, oc[0]))]
            pd = D; clicks = []
        xs = [[0, P(*path[0][1])[0]]] + [[t, P(*p)[0]] for t, p in path]
        ys = [[0, P(*path[0][1])[1]]] + [[t, P(*p)[1]] for t, p in path]
        sc = [[0, 1]]
        for c in clicks: sc += [[c - .05, 1], [c + .05, .78], [c + .2, 1]]
        po = kf((0, 0), (1.2, 0), (1.35, 1)) + ([[2.6, 1], [2.8, 0]] if pick is not None else [])
        add('X-ptr', f'选项{ci + 1} 指针', s0, pd, pf, k={'x': xs, 'y': ys, 'scale': sc, 'opacity': po})
        for c in clicks:
            px, py = P(tx + 6, oc[pick])
            add('X-prip', f'选项{ci + 1} 点击波纹', s0 + c, .5, rf, k={'x': kf((0, px)), 'y': kf((0, py)), 'scale': kf((0, 1), (.45, 2.4)), 'opacity': kf((0, 1), (.45, 0))})
    # 黑幕
    BK = save(Image.new('RGBA', (W, H), (0, 0, 0, 255)), 'black')
    for ci, (s0, D, _) in enumerate(FRZ):
        if ci < 2: add('X-black', f'黑幕{ci + 1}', s0 + 3.8, .95, BK, k={'opacity': kf((0, 0), (.5, 1), (.6, 1), (.95, 0))})
        else: add('X-black', '黑幕 片尾', s0 + 3.9, 1.1, BK, k={'opacity': kf((0, 0), (.5, 1), (.7, 1), (1.1, 0))})
    return pf, rf

# ---------------- 片尾 ----------------
def endcard(pf, rf):
    src_t = 29.3
    fr = os.path.join(TMP, 'frames', 'end_src2.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(src_t), '-i', VIDEO, '-frames:v', '1', fr], check=True)
    S = 1.1; iw, ih = int(1080 * S), int(1921 * S)
    im = Image.open(fr).convert('RGB').resize((iw, ih), Image.LANCZOS)
    cx, cy, w, h = geo(src_t)
    offx = int(max(W - iw, min(0, 540 - cx * iw))); FY = 660; offy = int(FY - cy * ih)
    bg = Image.new('RGB', (W, H), (0, 0, 0)); bg.paste(im, (offx, offy))
    bg = ImageEnhance.Brightness(bg).enhance(.5)
    m = Image.new('L', (W, H), 0); md = ImageDraw.Draw(m)
    for yy in range(H): md.line([(0, yy), (W, yy)], fill=int(255 * max(0, min(1, (1380 - yy) / 420))))
    bg = Image.composite(bg, Image.new('RGB', (W, H), (0, 0, 0)), m)
    sl = ImageDraw.Draw(bg)
    for yy in range(0, H, 4): sl.line([(0, yy), (W, yy)], fill=(0, 0, 0), width=1)
    bgf = 'end_bg_' + V + 'b'; bg.save(os.path.join(OUT, bgf + '.png'))
    add('V1', '片尾 背景', END0, ED, bgf, k={'scale': kf((0, 1.0), (ED, 1.05))})
    fcx = offx + cx * iw; bw, bh = w * iw * .72, h * ih * .72
    # 人脸框（静态，扫描线循环）
    Bx = canvas(); d = ImageDraw.Draw(Bx)
    d.rectangle([fcx - bw / 2, FY - bh / 2, fcx + bw / 2, FY + bh / 2], fill=Y + (14,), outline=Y + (70,), width=1)
    corners(d, fcx, FY, bw, bh, Y, 255, arm=80, wid=5)
    add('X-ebox', '片尾 人脸框', END0 + .15, ED - .15, save(fx(Bx, .3), 'end_box'), ax=fcx / W, ay=FY / H,
        k={'scale': kf((0, 1.4), (.35, 1)), 'opacity': fl((0, 0), (.05, 1), (.12, .2), (.19, 1), (.26, .4), (.33, 1))})
    Ln = canvas(); d = ImageDraw.Draw(Ln)
    for k in range(20): d.line([(fcx - bw / 2 + 4, 960 - k * 3), (fcx + bw / 2 - 4, 960 - k * 3)], fill=Y + (int((210 if k == 0 else 70) * (1 - k / 20)),), width=2 if k == 0 else 1)
    lf = save(Ln, 'end_scan'); top, bot = FY - bh / 2 - 960, FY + bh / 2 - 960
    ys = []
    t = 0
    while t < ED: ys += [[round(t, 3), round(top, 1), 'linear'], [round(t + 1.17, 3), round(bot, 1), 'hold']]; t += 1.2
    add('X-escan', '片尾 扫描线', END0 + .5, ED - .5, lf, k={'y': ys})
    Lb = canvas(); label_layer(Lb, max(60, fcx - bw / 2), FY - bh / 2 - 108, LM, 1, 99)
    add('X-elab', '片尾 标签', END0 + .45, ED - .45, save(fx(Lb), 'end_label'), k={'opacity': fl((0, 0), (.06, 1), (.12, .1), (.2, 1), (.26, .3), (.32, 1))})
    # Logo
    icon = Image.open(ASSET + 'LOGO-256x256-圆角.png').convert('RGBA').resize((92, 92), Image.LANCZOS)
    wm = Image.open(APPA + 'product-logo.png').convert('RGBA'); wm = wm.resize((int(wm.width * 44 / wm.height), 44), Image.LANCZOS)
    rw = 92 + 20 + wm.width; x0 = (W - rw) // 2; y0 = 112
    Lg = canvas(); Lg.alpha_composite(icon, (x0, y0)); Lg.alpha_composite(wm, (x0 + 112, y0 + 24))
    add('X-elogo', '片尾 Logo', END0 + .2, ED - .2, save(fx(stack(glow(Lg, 14, (0, 0, 0), 1), Lg)), 'end_logo'), k={'opacity': kf((0, 0), (.3, 1)), 'y': kf((0, -20), (.35, 0))})
    # 文案 + 卡片标题（逐字上浮）
    c1, c2 = '二人だけの暗号を、彼女は答えた', 'でも、スキャン結果は彼女じゃない'
    t1 = [j * .028 for j in range(len(c1))]; t2 = [.42 + j * .028 for j in range(len(c2))]
    float_seq('X-ehead', '片尾 文案', END0 + .45, END1, [(W / 2, 1010, c1, font(MINB, 44), t1, 'c', WH), (W / 2, 1070, c2, font(MINB, 44), t2, 'c', WH)], tag='end_copy')
    h1, h2 = 'ニセモノ義妹を', '見破れ'
    ht1 = [j * .05 for j in range(len(h1))]; ht2 = [.4 + j * .1 for j in range(len(h2))]
    def hl_items(): return [(W / 2, 1150, h1, font(MINK, 92), ht1, 'c', WH), (W / 2, 1250, h2, font(MINK, 150), ht2, 'c', Y)]
    # 卡片标题：红青错位（色散加强）
    last = max(ht2) + .25; n = int(math.ceil(last * FPS_UI)); TS = END0 + 1.0
    for k in range(n + 1):
        t = k / FPS_UI; T = canvas()
        for (x, y, s, f, tm, anc, fill) in hl_items(): draw_chars(T, x, y, s, f, t, tm, fill=fill, anchor=anc, rise=26, dur=.25)
        a = T.split()[3]
        R = Image.new('RGBA', (W, H), (255, 40, 60, 0)); R.putalpha(a.point(lambda v: int(v * .7)))
        Cn = Image.new('RGBA', (W, H), (40, 230, 255, 0)); Cn.putalpha(a.point(lambda v: int(v * .7)))
        Lh = canvas(); Lh.alpha_composite(R, (-6, 0)); Lh.alpha_composite(Cn, (6, 0))
        Lh = stack(glow(T, 8, (0, 0, 0), 2), Lh, glow(T, 16, Y, .35), T)
        add('X-ecard', '片尾 卡片标题', TS + t, (1 / FPS_UI) if k < n else (END1 - TS - t), save(fx(Lh), f'end_card_{k:02d}'))
    # 按钮
    bx0, by0, bx1, by1 = 190, 1470, 890, 1590
    Bt = canvas(); d = ImageDraw.Draw(Bt)
    d.rectangle([bx0, by0, bx1, by1], fill=(0, 0, 0, 150), outline=Y + (255,), width=3)
    for (x, yv, sx, sy) in [(bx0 - 10, by0 - 10, 1, 1), (bx1 + 10, by0 - 10, -1, 1), (bx0 - 10, by1 + 10, 1, -1), (bx1 + 10, by1 + 10, -1, -1)]:
        d.line([(x, yv + sy * 26), (x, yv), (x + sx * 26, yv)], fill=Y + (255,), width=4)
    T = canvas(); text(T, ((bx0 + bx1) // 2, (by0 + by1) // 2), 'ダウンロードして続きを見る', font(MINB, 48), Y, anchor='mm')
    Bt = stack(glow(Bt, 14, Y, .5), Bt, readable(T, Y, .6))
    BS = END0 + 1.35; TAPS = [1.8, 2.1, 2.4, 2.7]
    bsc = [[0, .7], [.22, 1.05], [.35, 1]]
    for tp in TAPS: r = END0 + tp - BS; bsc += [[round(r - .05, 3), 1], [round(r + .04, 3), .95], [round(r + .18, 3), 1]]
    add('X-ebtn', '片尾 下载按钮', BS, END1 - BS, save(fx(Bt, .2), 'end_btn'), ay=(by0 + by1) / 2 / H, k={'scale': bsc, 'opacity': kf((0, 0), (.12, 1))})
    gp = Image.open(ASSET + 'Google_Play_Badge_JA.svg.png').convert('RGBA'); gp = gp.resize((int(gp.width * 88 / gp.height), 88), Image.LANCZOS)
    ios = Image.open(ASSET + 'ios_badge.png').convert('RGBA'); ios = ios.crop(ios.split()[3].getbbox()); ios = ios.resize((int(ios.width * 88 / ios.height), 88), Image.LANCZOS)
    inner = ios.crop((8, 6, ios.width - 8, ios.height - 6))
    nb = Image.new('RGBA', gp.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(nb)
    bd.rounded_rectangle([0, 0, gp.width - 1, gp.height - 1], radius=14, fill=(0, 0, 0, 255), outline=(166, 166, 166, 255), width=2)
    nb.alpha_composite(inner, ((gp.width - inner.width) // 2, (gp.height - inner.height) // 2)); ios = nb
    gap = 28; tot = gp.width + gap + ios.width; x0 = (W - tot) // 2
    Sb = canvas(); Sb.alpha_composite(gp, (x0, 1650)); Sb.alpha_composite(ios, (x0 + gp.width + gap, 1650))
    add('X-ebadge', '片尾 商店标', END0 + 1.5, ED - 1.5, save(fx(Sb), 'end_badges'), k={'opacity': kf((0, 0), (.25, 1)), 'y': kf((0, 20), (.3, 0))})
    # 圆圈指针点击按钮
    tx, ty = bx1 - 120, (by0 + by1) / 2
    px, py = tx - REF[0], ty - REF[1]
    sc = [[0, 1]]
    for tp in TAPS: r = tp - 1.55; sc += [[round(r - .05, 3), 1], [round(r + .04, 3), .78], [round(r + .16, 3), 1]]
    add('X-eptr', '片尾 指针', END0 + 1.55, ED - 1.55, pf, k={'x': kf((0, px + 160), (.22, px)), 'y': kf((0, py + 220), (.22, py)), 'opacity': kf((0, 0), (.15, 1)), 'scale': sc})
    for i, tp in enumerate(TAPS):
        add(f'X-erip{i % 2 + 1}', '片尾 点击波纹', END0 + tp, min(.45, ED - tp), rf, k={'x': kf((0, px)), 'y': kf((0, py)), 'scale': kf((0, 1), (.45, 2.3)), 'opacity': kf((0, 1), (.45, 0))})
    return [END0 + t for t in TAPS]

TRACKS = [
    ('X-vig', '监控 暗角扫描线', 'title'), ('X-roll', '监控 滚动光带', 'title'),
    ('X-trk', '识别框+字幕（逐帧）', 'meter'),
    ('X-hud', '监控 边角+CAM', 'title'), ('X-clock', '监控 时间', 'title'),
    ('X-mlab', '人間度 标签+底条', 'meter'), ('X-mbar', '人間度 填充', 'meter'), ('X-mnum', '人間度 数字', 'meter'),
    ('X-cdim', '选项 压暗', 'choice'), ('X-cq', '选项 提问底', 'choice'), ('X-cqt', '选项 提问字', 'choice'),
    ('X-co1', '选项 ①', 'choice'), ('X-co2', '选项 ②', 'choice'), ('X-co3', '选项 ③', 'choice'),
    ('X-ch', '选项 悬停', 'choice'), ('X-cs', '选项 选中闪烁', 'choice'), ('X-csw', '选项 扫描线', 'choice'),
    ('X-ptr', '选项 圆圈指针', 'choice'), ('X-prip', '选项 点击波纹', 'choice'),
    ('X-glitch', '干扰撕裂', 'title'),
    ('X-ebox', '片尾 人脸框', 'end'), ('X-escan', '片尾 扫描线', 'end'), ('X-elab', '片尾 标签', 'end'), ('X-elogo', '片尾 Logo', 'end'),
    ('X-ehead', '片尾 文案', 'end'), ('X-ecard', '片尾 卡片标题', 'end'), ('X-ebtn', '片尾 下载按钮', 'end'), ('X-ebadge', '片尾 商店标', 'end'),
    ('X-eptr', '片尾 指针', 'end'), ('X-erip1', '片尾 波纹1', 'end'), ('X-erip2', '片尾 波纹2', 'end'),
    ('X-black', '黑幕过渡', 'end'),
]

def check():
    ts = [1.5, 4.5, 6.0, 7.5, 8.5, 9.5, 11.0, 14.5, 17.5, 20.5, 21.5, 23.0, 24.0, 25.0, 26.0, 27.5, 28.5, 29.5]
    tiles = []
    for t in ts:
        p = os.path.join(TMP, 'frames', f'f{t:05.2f}.png')
        im = Image.open(p).convert('RGB').resize((W, H)); d = ImageDraw.Draw(im)
        cx, cy, w, h = box_px(t); d.rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], outline=(255, 255, 0), width=6)
        d.text((20, 20), str(t), fill=(255, 0, 0), font=font(DOT, 60)); tiles.append(im.resize((270, 480)))
    Sh = Image.new('RGB', (270 * 6, 480 * 3))
    for i, im in enumerate(tiles): Sh.paste(im, ((i % 6) * 270, (i // 6) * 480))
    Sh.save(os.path.join(TMP, 'track_check.jpg'))
    for s in SUBS: print(round(s['start'], 2), round(s['hide'], 2), s['lines'][0], [round(x, 2) for x in s['times'][:4]])

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == 'check': check(); sys.exit()
    hud(); meter(); glitches(); pf, rf = choices(); taps = endcard(pf, rf); tracker()
    sfx = [['s_scan', T_A0, .5], ['s_ghost', T_B0, .7], ['s_drop', T_B0 + .15, .4], ['s_vanish', T_BV, .6], ['s_glitch', T_DROP, .75], ['s_scan', T_SW, .5]]
    for ci, (s0, D, _) in enumerate(FRZ):
        sfx.append(['s_panel', s0, .55])
        if ci < 2: sfx += [['s_hover', s0 + 1.9, .4], ['s_pick', s0 + 2.4, .55], ['s_vanish', s0 + 2.55, .3], ['s_drop', s0 + 3.8, .45]]
        else: sfx += [['s_hover', s0 + 1.8, .4], ['s_hover', s0 + 2.7, .4], ['s_hover', s0 + 3.5, .4], ['s_drop', s0 + 3.9, .5]]
    sfx += [['s_end', END0, .6]] + [['s_tap', t, .35] for t in taps]
    meta = {'tracks': TRACKS, 'layers': LAY, 'seg': SEG, 'frz': FRZ, 'end0': END0, 'ed': ED, 'sfx': sfx,
            'timeline': {'act2': o(10.35), 'act3': o(20.15), 'frz': FRZ, 'end0': END0, 'end1': END1}}
    json.dump(meta, open(os.path.join(OUT, 'layers.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('layers', len(LAY), 'files', len({l['file'] for l in LAY}))
