# -*- coding: utf-8 -*-
"""贞操逆转+上门讨债 · v3 简约高级（无框排版 + 失焦融入）（noir champagne）
统一风格：真·半透明玻璃（背景实时模糊烘焙）+ 白字柔投影 + 香槟金渐变强调 + 酒红热度
字体：标题/片尾大字 = Shippori Mincho B1 ExtraBold；字幕/UI = Noto Sans JP Black/Bold
- 开头 3 s：模糊定格 → 玻璃胶囊 MiraiMindで → 明朝长标题（金色扫光）→ 3 条玻璃背景条 → 失焦拉回正片
- 字幕：玻璃字幕条挂在脸下方，逐块上浮淡入（15 fps 烘焙，玻璃里是当帧模糊背景）
- 溺愛度：左上玻璃胶囊（爱心 + 数值 + 金→酒红条）
- 选项：背景失焦压暗 → 玻璃提问卡 → 玻璃选项胶囊 → 指针点击 → 其他消失 → 选中金色闪烁 → 数值涨 → 失焦回正片
- 片尾：Logo → 明朝金色标题 + 玻璃文案卡 → 金色按钮 4 连点 → 两个等大商店标
"""
import os, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(P, '包装素材v3'); FR = os.path.join(P, '工程素材', '抽帧')
VIDS = {'A': os.path.join(P, '视频 (71).mp4'), 'B': os.path.join(P, '视频 (73).mp4')}
W, H = 1080, 1920
APP = 'F:/钟海明/2026/2026年10月10日MM-编辑器重构/app/'
NOTO = APP + 'public/fonts/NotoSansJP-Black.otf'
NOTOB = APP + 'public/fonts/NotoSansJP-Bold.otf'
SHIP = 'C:/Windows/Fonts/01_诱惑台词主力_特粗标题_ShipporiMinchoB1-ExtraBold.ttf'
ASSET = 'F:/钟海明/MM透明尾板/片尾/片尾文件夹/(素材)/图片/'
WH = (255, 255, 255); SUB = (238, 230, 218); DARK = (27, 19, 10)
GOLD = [(0, (255, 250, 240)), (.55, (236, 220, 196)), (1, (205, 182, 148))]   # 淡香槟（接近她的银发，融入画面）
EMPH = [(0, (255, 240, 212)), (.55, (238, 204, 146)), (1, (214, 168, 104))]   # 字幕强调词
HEAT = [(0, (242, 223, 180)), (.45, (210, 167, 102)), (.78, (181, 80, 58)), (1, (163, 37, 58))]
V = 'd'
WINE = (156, 28, 52)

# ---------------- 时间轴 ----------------
INTRO = 3.0
SEG = [('A', 0.0, 14.6, 3.0), ('A', 15.8, 29.6, 8.2), ('B', 0.0, 12.4, 44.2)]   # 视频, 源起, 源止, 偏移
CH = [('A', 17.6, 6.4, 14.3), ('A', 37.8, 6.4, 29.5), ('B', 56.6, 5.4, 12.2)]   # 选项定格（犹豫 2 秒）
PH0, PHD = 62.0, 4.6                     # 手机聊天（AI 剧情对话）
FRZ = [('A', 0.0, INTRO, 0.0), CH[0], CH[1], ('B', 56.6, 5.4 + PHD, 12.2)]
MUTE = [('A', 19.36, 20.48)]             # 第二幕推主视角处：模型生成的错误女声 → 静音
CLICK, MRISE = 3.9, 4.9                  # 选项内：点击 / 数值上涨（相对定格起点）
END0, ED = PH0 + PHD, 2.4
END1 = END0 + ED
OUTF = .35   # 选项结束后失焦层淡出时长
def o(vid, src):
    for v, a, b, off in SEG:
        if v == vid and a - 1e-6 <= src <= b + 1e-6: return src + off
    raise ValueError((vid, src))

# ---------------- 基础 ----------------
FONTS = {}
def font(p, s):
    if (p, s) not in FONTS: FONTS[(p, s)] = ImageFont.truetype(p, s)
    return FONTS[(p, s)]
def canvas(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))
def save(im, name):
    fn = f'{name}_{V}'; im.save(os.path.join(OUT, fn + '.png'), compress_level=1); return fn
def save_jpg(im, name):
    fn = f'{name}_{V}'; im.convert('RGB').save(os.path.join(OUT, fn + '.jpg'), quality=92); return fn
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
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
def fl(*pts): return [[round(t, 3), round(v, 3), 'hold'] for t, v in pts]
SFX = []
def sfx(name, t, v): SFX.append([name, round(t, 3), v])

# ---------------- 源帧 / 背景 ----------------
_FC = {}
def frame(vid, src):
    i = int(round(src * 24)); i = max(0, min(i, (720 if vid == 'A' else 312)))
    key = (vid, i)
    if key not in _FC:
        if len(_FC) > 80: _FC.clear()
        im = Image.open(os.path.join(FR, vid, f'{i:04d}.jpg')).convert('RGB').resize((W, 1922), Image.BILINEAR).crop((0, 1, W, 1921))
        _FC[key] = im
    return _FC[key]
def soft_bg(im, blur=30, br=.5, sat=1.15):
    """失焦压暗背景（开头 / 选项 / 片尾用）"""
    b = im.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur / 4)).resize((W, H), Image.BILINEAR)
    b = ImageEnhance.Color(b).enhance(sat); b = ImageEnhance.Brightness(b).enhance(br)
    # 暗角
    y, x = np.mgrid[0:H, 0:W]; r = np.sqrt(((x - W / 2) / (W * .7)) ** 2 + ((y - H / 2) / (H * .62)) ** 2)
    v = np.clip(1 - .45 * np.clip(r - .45, 0, 1), 0, 1)[..., None]
    return Image.fromarray((np.asarray(b).astype(np.float32) * v).astype(np.uint8))
BLUR = {}   # 'intro' / 0,1,2 → 失焦层图
def blur_alpha(T):
    """返回 (失焦层key, alpha)"""
    if T < INTRO + OUTF: return 'intro', (1 if T < 2.75 else clamp(1 - (T - 2.75) / (INTRO + OUTF - 2.75)))
    for ci, (vid, s0, D, fr) in enumerate(CH):
        if s0 <= T < s0 + D: return ci, clamp((T - s0) / .25)
        if ci < 2 and s0 + D <= T < s0 + D + OUTF: return ci, clamp(1 - (T - s0 - D) / OUTF)
    return None, 0
def bg_at(T):
    """成片时间 T 时 V1 + 失焦层 的画面（玻璃折射用）"""
    base = None
    for vid, a, b, off in SEG:
        if a + off - 1e-6 <= T < b + off: base = frame(vid, T - off)
    if base is None:
        for vid, s0, D, fr in FRZ:
            if s0 - 1e-6 <= T < s0 + D: base = frame(vid, fr)
    if base is None: base = frame('B', CH[2][3])
    k, a = blur_alpha(T)
    if k is not None and a > 0: base = Image.blend(base, BLUR[k], a)
    return base

# ---------------- 玻璃 ----------------
_MK = {}
def rr_mask(w, h, r, width=None):
    key = (w, h, r, width)
    if key not in _MK:
        S = 4; m = Image.new('L', (w * S, h * S), 0); d = ImageDraw.Draw(m)
        if width: d.rounded_rectangle([S // 2, S // 2, w * S - S // 2 - 1, h * S - S // 2 - 1], radius=r * S, outline=255, width=int(width * S))
        else: d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=r * S, fill=255)
        _MK[key] = m.resize((w, h), Image.LANCZOS)
    return _MK[key]
_RIM = {}
def rim_alpha(w, h):
    if (w, h) not in _RIM:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        lt = 1 - (x / w * .45 + y / h * .55)                 # 左上受光
        rb = (x / w * .5 + y / h * .5)                        # 右下反光
        a = .16 + .78 * np.clip(lt, 0, 1) ** 2.2 + .32 * np.clip(rb - .55, 0, 1) / .45
        _RIM[(w, h)] = np.clip(a, 0, 1)
    return _RIM[(w, h)]
def glass(L, bg, box, r, a=1.0, tint=(14, 12, 16), ta=.2, blur=22, bright=.86, sat=1.3, shadow=.22, fill=None, rimk=.7):
    """真玻璃：背景模糊 + 着色 + 顶部高光 + 受光边 + 柔投影；fill=渐变图（选中/按钮）"""
    x0, y0, x1, y1 = [int(round(v)) for v in box]; w, h = x1 - x0, y1 - y0
    if w < 4 or h < 4 or a <= 0.003: return
    m = rr_mask(w, h, r)
    if shadow:
        pad = 60; sm = Image.new('L', (w + pad * 2, h + pad * 2), 0); sm.paste(m, (pad, pad))
        sm = sm.filter(ImageFilter.GaussianBlur(22)); sm = sm.point(lambda v: int(v * shadow * a))
        sh = Image.new('RGBA', sm.size, (0, 0, 0, 0)); sh.putalpha(sm)
        L.alpha_composite(sh, (x0 - pad, y0 - pad + 14)) if x0 - pad >= 0 and y0 - pad + 14 >= 0 else _paste(L, sh, x0 - pad, y0 - pad + 14)
    if fill is None:
        p = blur * 3; X0, Y0, X1, Y1 = max(0, x0 - p), max(0, y0 - p), min(W, x1 + p), min(H, y1 + p)
        reg = bg.crop((X0, Y0, X1, Y1))
        sm_ = reg.resize((max(1, reg.width // 2), max(1, reg.height // 2)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur / 2)).resize(reg.size, Image.BILINEAR)
        sm_ = ImageEnhance.Color(sm_).enhance(sat); sm_ = ImageEnhance.Brightness(sm_).enhance(bright)
        reg = sm_.crop((x0 - X0, y0 - Y0, x0 - X0 + w, y0 - Y0 + h))
        if reg.size != (w, h): reg = reg.resize((w, h))
        arr = np.asarray(reg).astype(np.float32)
        arr = arr * (1 - ta) + np.array(tint, np.float32) * ta
    else:
        arr = np.asarray(fill.resize((w, h)).convert('RGB')).astype(np.float32)
    yy = np.arange(h, dtype=np.float32)[:, None, None]
    sheen = np.clip(1 - yy / (h * .55), 0, 1) ** 1.6 * (.16 if fill is None else .30)
    arr = arr + (255 - arr) * sheen
    pan = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
    pan.putalpha(m.point(lambda v: int(v * a)))
    _paste(L, pan, x0, y0)
    # 受光边
    rm = np.asarray(rr_mask(w, h, r, width=2.2)).astype(np.float32) / 255 * rim_alpha(w, h) * rimk * a
    rim = Image.new('RGBA', (w, h), (255, 255, 255, 0)); rim.putalpha(Image.fromarray((rm * 255).astype(np.uint8)))
    _paste(L, rim, x0, y0)
def _paste(L, im, x, y):
    """可越界的 alpha 合成"""
    bx0, by0 = max(0, x), max(0, y); bx1, by1 = min(W, x + im.width), min(H, y + im.height)
    if bx1 <= bx0 or by1 <= by0: return
    L.alpha_composite(im.crop((bx0 - x, by0 - y, bx1 - x, by1 - y)), (bx0, by0))

def text(L, xy, s, f, fill=WH, a=1.0, anchor='ls', shadow=.55, grad=None):
    """白字/金字 + 柔投影"""
    if a <= 0.003: return
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text(xy, s, font=f, fill=255, anchor=anchor)
    bb = m.getbbox()
    if not bb: return
    if shadow:
        pad = 24; c = m.crop((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)).filter(ImageFilter.GaussianBlur(7))
        sh = Image.new('RGBA', c.size, (0, 0, 0, 0)); sh.putalpha(c.point(lambda v: int(v * shadow * a)))
        _paste(L, sh, bb[0] - pad, bb[1] - pad + 4)
    c = m.crop(bb)
    if grad: col = grad_img(c.width, c.height, grad).convert('RGBA')
    else: col = Image.new('RGBA', c.size, fill + (255,))
    col.putalpha(c.point(lambda v: int(v * a))); _paste(L, col, bb[0], bb[1])

# ---------------- 人脸轨迹 ----------------
TRK = {}
_tj = json.load(open(os.path.join(P, '包装素材v1', 'track.json'), encoding='utf-8'))
for k, rows in _tj.items():
    TRK['A' if '71' in k else 'B'] = np.array([[r[0], r[1], r[2], r[3], r[4], 1.0 if r[5] else 0.0] for r in rows], np.float64)
def face(vid, t, win=.35):
    a = TRK[vid]; m = (np.abs(a[:, 0] - t) <= win) & (a[:, 5] > 0)
    if not m.any():
        ok = np.where(a[:, 5] > 0)[0]; i = ok[np.argmin(np.abs(a[ok, 0] - t))]; return a[i, 1:5]
    wt = 1 - np.abs(a[m, 0] - t) / (win + 1e-3)
    return (a[m, 1:5] * wt[:, None]).sum(0) / wt.sum()

# ---------------- 文案（只来自 全量文案.md） ----------------
LINES = {
    'A': [
        [('おーい、', .28), ('\n*集金の', 1.75), ('時間だ。', 2.2)], 2.78,
        [('今月の', 3.7), ('分は', 4.1), ('\nちゃんと', 4.4), ('*用意', 4.76), ('しているか？', 5.02)], 5.66,
        [('今から', 7.0), ('*3つ', 7.72), ('\n数えるから、', 8.14)], 8.94,
        [('それまでに', 9.3), ('\n出てこなきゃ', 9.72), ('このドア、', 10.22), ('\n*蹴破るからな。', 10.7)], 11.7,
        [('はぁ、', 16.45), ('\n出るなら', 17.6), ('最初から', 18.0), ('\n*出ろよ。', 18.64)], 19.3,
        [('やっぱり', 21.58), ('\n*用意できて', 21.98), ('\nなかったのか？', 22.44)], 23.35,
        [('じゃあ、', 25.14), ('\n*どうすんの？', 25.62)], 26.64,
        [('言っておくけど', 27.3), ('\n後日とかは', 27.88), ('\n*なしだからな。', 28.74)], 29.58,
    ],
    'B': [
        [('あ、', .82), ('*いいこと', 1.55), ('\n思いついた。', 2.36)], 3.1,
        [('*聞きたいか？', 3.3)], 4.02,
        [('私の', 6.1), ('*嫁', 6.9), ('になるってのは', 7.14), ('\n……', 7.78), ('どうだ？', 7.96)], 8.7,
        [('さぁ、', 9.35), ('\n自分で', 10.3), ('*決めな。', 10.94)], 11.8,
    ]}
COUNT = [('3', 12.92, 14.0), ('2', 14.04, 14.6)]
QS = [('貞操逆転世界で、女の借金取りが', 'ドアを蹴破ろうとしている。どうする?'),
      ('女の借金取りに詰め寄られた。', '金のないあなたはどうする?'),
      ('借金のカタに「嫁になれ」と迫られた。', 'あなたの決断は?')]
OPTS = [['①ドアを開ける', '②痴女だと叫ぶ', '③居留守を使う'],
        ['①土下座する', '②逃げる', '③何もしない'],
        ['①そんな美味しい話が？', '②きっぱり断る！']]
INTRO_TAG = 'MiraiMindで'
GOAL_TAG, GOAL = '目標', '貞操を守り抜け'
DM = [   # 选项弹幕（日本网感吐槽）
    ['ドア蹴破る女ｗｗｗ', '貞操逆転きたあああ', '居留守一択だろ', '開けたら食われるぞ', '痴女って叫ぶの草', '取り立て美人すぎん？', 'ここで開けるのが男', 'ｗｗｗｗｗｗ'],
    ['土下座しかねぇ', '逃げても無駄やろ', '壁ドンされたい人生だった', '金ないのリアルすぎ', 'これはご褒美では？', '何もしないは草', '８８８８８８', '貞操の危機ｗｗ'],
    ['そんな美味しい話が！？', '嫁（男）ｗｗｗ', '即答しろ', '断る理由なくて草', '貞操守れｗｗ', '結婚おめでとう', 'ここで切るな！！']]
PH_CAP = 'AIキャラとのストーリーチャット'
PH_NAME = '借金取り'
PH_HIST = ['私の嫁になるってのは……どうだ？', 'さぁ、自分で決めな。']
PH_NEW = 'で、返事は？♡'
END_TAG = '貞操逆転世界'
END_COPY = ('貞操逆転世界に転移したら', '借金取りが来た、どうする！')
BTN = 'ダウンロードして続きを見る'
AWK, ENDF, PHF = 16.45, 11.0, 9.0

# ---------------- 迭代版本（VER=1|2：同台词不同角色） ----------------
VER = os.environ.get('VER')
if VER:
    import importlib.util as _u
    _s = _u.spec_from_file_location('ver_cfg', os.path.join(HERE, 'ver_cfg.py')); _m = _u.module_from_spec(_s); _s.loader.exec_module(_m)
    C = _m.CFG[VER]
    OUT = os.path.join(P, f'包装素材_版本{VER}'); FR = os.path.join(P, '工程素材', f'抽帧_版本{VER}')
    VIDS = {k: os.path.join(P, v) for k, v in C['vids'].items()}
    _D = [6.4, 6.4, 5.4]; _t = INTRO; SEG, CH = [], []
    for _i, (_v, _a, _b) in enumerate(C['seg']):
        _b = round(_a + round((_b - _a) * 30) / 30, 4)   # 段长对齐 1/30，保证片尾等图层与 V1 接缝一致
        SEG.append((_v, _a, _b, round(_t - _a, 4))); _t = round(_t + _b - _a, 4)
        CH.append(('A' if _i < 2 else 'B', _t, _D[_i], C['frz'][_i])); _t = round(_t + _D[_i], 4)
    PH0 = round(CH[2][1] + 5.4, 4); END0 = round(PH0 + PHD, 4); END1 = END0 + ED
    FRZ = [('A', 0.0, INTRO, 0.0), CH[0], CH[1], ('B', CH[2][1], 5.4 + PHD, CH[2][3])]
    MUTE = C['mute']; LINES = C['lines']; COUNT = C['count']; AWK, ENDF, PHF = C['awk'], C['endf'], C['phf']
    _tj = json.load(open(os.path.join(OUT, 'track.json'), encoding='utf-8'))
    TRK = {k: np.array([[r[0], r[1], r[2], r[3], r[4], 1.0 if r[5] else 0.0] for r in rows], np.float64) for k, rows in _tj.items()}
    _FC.clear()

# ---------------- 开头（无框：纯排版） ----------------
NOTOM = APP + 'public/fonts/NotoSansJP-Medium.otf'
def hair(L, x0, x1, y, a=.8, w=2, fade=True, stops=None):
    n = int(x1 - x0); g = grad_img(n, w, stops or [(0, (205, 182, 148)), (.5, (255, 250, 240)), (1, (205, 182, 148))], horiz=True).convert('RGBA')
    al = (np.clip(1 - np.abs(np.linspace(-1, 1, n)), 0, 1) ** .5 if fade else np.ones(n)) * 255 * a
    g.putalpha(Image.fromarray(np.repeat(al.astype(np.uint8)[None], w, 0))); _paste(L, g, int(x0), int(y))
def intro_v3():
    bgi = BLUR['intro']; bgf = save(bgi.convert('RGBA'), 'intro_blur')
    add('X-iblur', '开头 失焦背景', 0, INTRO + OUTF, bgf, k={'scale': kf((0, 1.06), (INTRO + OUTF, 1.0)), 'opacity': kf((0, 1), (2.75, 1), (INTRO + OUTF, 0))})
    out = lambda st: kf((0, 0), (.3, 1), (2.72 - st, 1), (2.98 - st, 0))
    # MiraiMindで：小字 + 两侧细线
    f = font(NOTOB, 32); tw = f.getlength(INTRO_TAG); y = 640
    L = canvas(); text(L, (540, y), INTRO_TAG, f, SUB, anchor='mm', shadow=.4)
    hair(L, 540 - tw / 2 - 110, 540 - tw / 2 - 24, y, .9, fade=False, stops=[(0, (205, 182, 148)), (1, (255, 250, 240))])
    hair(L, 540 + tw / 2 + 24, 540 + tw / 2 + 110, y, .9, fade=False, stops=[(0, (255, 250, 240)), (1, (205, 182, 148))])
    add('X-itag', '开头 MiraiMindで', .12, INTRO - .12, save(L, 'intro_tag'), ay=y / H, k={'opacity': out(.12), 'y': kf((0, 16), (.4, 0))})
    sfx('u_end', .05, .4)
    f1 = font(SHIP, 112); f2 = font(SHIP, 168)
    L = canvas(); s1a, s1b = '貞操逆転', '世界に'; w1 = f1.getlength(s1a + s1b); x = 540 - w1 / 2
    text(L, (x, 820), s1a, f1, anchor='ls', grad=GOLD, shadow=.7); text(L, (x + f1.getlength(s1a), 820), s1b, f1, WH, anchor='ls', shadow=.7)
    t1 = save(L, 'intro_t1')
    L = canvas(); text(L, (540, 1010), '転移する', f2, WH, anchor='ms', shadow=.7); t2 = save(L, 'intro_t2')
    add('X-ititle1', '开头 标题1', .3, INTRO - .3, t1, ay=780 / H, k={'opacity': out(.3), 'y': kf((0, 30), (.5, 0)), 'scale': kf((0, 1.05), (.5, 1))})
    add('X-ititle2', '开头 标题2', .52, INTRO - .52, t2, ay=950 / H, k={'opacity': out(.52), 'y': kf((0, 30), (.5, 0)), 'scale': kf((0, 1.08), (.5, 1))})
    sfx('u_pop', .32, .3); sfx('u_pop', .54, .4)
    tm = Image.new('L', (W, H), 0); dm = ImageDraw.Draw(tm)
    dm.text((x, 820), s1a + s1b, font=f1, fill=255, anchor='ls'); dm.text((540, 1010), '転移する', font=f2, fill=255, anchor='ms')
    tma = np.asarray(tm).astype(np.float32) / 255; yy, xx = np.mgrid[0:H, 0:W]
    for j in range(9):
        c = -300 + j * 200; band = np.clip(1 - np.abs((xx + (yy - 880) * .45) - c) / 90, 0, 1) ** 2
        S = Image.new('RGBA', (W, H), (255, 250, 236, 0)); S.putalpha(Image.fromarray((tma * band * 200).astype(np.uint8)))
        add('X-isheen', '开头 标题扫光', 1.0 + j / 15, 1 / 15, save(S, f'intro_sheen{j}'))
    L = canvas(); hair(L, 300, 780, 1082, .9); add('X-iline', '开头 分割线', .8, INTRO - .8, save(L, 'intro_line'), ay=1083 / H, k={'opacity': out(.8), 'scale': kf((0, .2), (.45, 1))})
    f = font(NOTOB, 42)
    for i, s in enumerate(CARDS):
        y = 1180 + i * 84; st = 1.05 + i * .38
        L = canvas(); text(L, (540, y), s, f, WH if i < 2 else None, anchor='mm', shadow=.55, grad=EMPH if i == 2 else None)
        add(f'X-icard{i + 1}', f'开头 背景{i + 1}', st, INTRO - st, save(L, f'intro_card{i + 1}'), ay=y / H, k={'opacity': out(st), 'y': kf((0, 24), (.4, 0))})
        sfx('u_bubble', st, .35)
    sfx('s_whoosh', 2.72, .45)

# ---------------- 字幕（无框：白字柔影 + 指向人脸的小箭头，跟脸移动） ----------------
MARK_H = 16
def layout(chunks):
    rows, cur = [], []
    for i, (s, t) in enumerate(chunks):
        if s.startswith('\n') and cur: rows.append(cur); cur = []
        cur.append(i)
    rows.append(cur)
    items = []
    for s, t in chunks:
        s = s.lstrip('\n'); emph = s.startswith('*'); s = s.lstrip('*')
        items.append({'s': s, 't': t, 'emph': emph, 'f': font(NOTO if emph else NOTOB, 70 if emph else 56)})
    RH = 84; y = 960 + MARK_H + 22; maxw = 0
    for r in rows:
        tw = sum(items[i]['f'].getlength(items[i]['s']) for i in r); x = 540 - tw / 2
        for i in r: items[i]['xy'] = (x, y + 60); x += items[i]['f'].getlength(items[i]['s'])
        y += RH; maxw = max(maxw, tw)
    return items, maxw, y - 960
def sub_text(L, it):
    """白字：大范围柔光晕 + 贴身柔影（亮背景也能读，不用描边和框）"""
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text(it['xy'], it['s'], font=it['f'], fill=255, anchor='ls')
    bb = m.getbbox(); pad = 40; c = m.crop((bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad))
    for r, a in [(16, .38), (4, .55)]:
        h_ = c.filter(ImageFilter.GaussianBlur(r)); sh = Image.new('RGBA', c.size, (8, 6, 10, 0)); sh.putalpha(h_.point(lambda v: int(min(255, v * a * 1.6))))
        _paste(L, sh, bb[0] - pad, bb[1] - pad + 3)
    if it['emph']:   # 重点词：香槟柔光
        g_ = c.filter(ImageFilter.GaussianBlur(14)); gc = Image.new('RGBA', c.size, (236, 178, 110, 0)); gc.putalpha(g_.point(lambda v: int(min(255, v * .75))))
        _paste(L, gc, bb[0] - pad, bb[1] - pad)
    text(L, it['xy'], it['s'], it['f'], WH, anchor='ls', shadow=0, grad=EMPH if it['emph'] else None)
def marker():
    L = canvas(); g = Image.new('L', (W, H), 0)
    tri = [(540, 960), (540 - 13, 960 + MARK_H), (540 + 13, 960 + MARK_H)]
    ImageDraw.Draw(g).polygon([(x, y + 3) for x, y in tri], fill=150); g = g.filter(ImageFilter.GaussianBlur(5))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(g); L.alpha_composite(sh)
    S = 4; big = Image.new('L', (W * S // 8, 80 * S), 0)
    ImageDraw.Draw(L).polygon(tri, fill=(255, 255, 255, 240))
    return save(L, 'sub_marker')
def path_k(vid, off, t0, dur, bw, bh):
    xs, ys = [], []; n = max(1, int(math.ceil(dur / .2)))
    for j in range(n + 1):
        tt_ = min(dur, j * .2); cx, cy, fw, fh = face(vid, t0 + tt_ - off)
        x = min(max(cx * W, 50 + bw / 2), 1030 - bw / 2) - 540
        y = min((cy + fh / 2) * H + 22 - 960, 1700 - bh - 960)
        xs.append([round(tt_, 3), round(x, 1)]); ys.append([round(tt_, 3), round(y, 1)])
    return xs, ys
def subs():
    mk = marker()
    for (vid, a, b, off) in SEG:
        arr = LINES[vid]; pairs = [(arr[i], arr[i + 1]) for i in range(0, len(arr), 2)]
        pairs = [(c, e) for c, e in pairs if a <= c[0][1] < b]
        for li, (chunks, end) in enumerate(pairs):
            nxt = pairs[li + 1][0][0][1] if li + 1 < len(pairs) else b
            t0 = chunks[0][1]; hide = min(nxt - .1, end + .9, b - .05)
            items, bw, bh = layout(chunks); tag = f'sub_{vid}{int(t0 * 100):04d}'
            def lay(track, name, s0, fn, pivot=None):
                S = s0 + off; D = hide - s0; xs, ys = path_k(vid, off, S, D, bw, bh)
                k = {'x': xs, 'y': ys, 'opacity': kf((0, 0), (.18, 1), (max(.19, D - .15), 1), (D, 0))}
                ax = ay = .5
                if pivot:   # 重点词弹入：以词中心缩放
                    ax, ay = pivot[0] / W, pivot[1] / H
                    k['scale'] = kf((0, 1.45), (.12, .94), (.22, 1.03), (.32, 1))
                add(track, name, S, D, fn, ax=ax, ay=ay, k=k)
            lay('X-sub0', '字幕 箭头', t0, mk)
            for i, it in enumerate(items):
                L = canvas(); sub_text(L, it); bb = L.getbbox()
                lay(f'X-sub{i + 1}', '字幕 ' + it['s'], it['t'], save(L, f'{tag}_{i}'), ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2) if it['emph'] else None)
                if it['emph']: sfx('u_pop', it['t'] + off, .22)
            if not (vid == 'A' and abs(t0 - AWK) < .01): sfx('u_bubble', t0 + off, .2)
    sfx('u_awk', o('A', AWK), .55)
    for s, a, b in COUNT:
        L = canvas(); cy = 1380
        ring = Image.new('L', (W, H), 0); ImageDraw.Draw(ring).ellipse([540 - 150, cy - 150, 540 + 150, cy + 150], outline=255, width=3)
        rc = Image.new('RGBA', (W, H), (236, 220, 196, 0)); rc.putalpha(ring.point(lambda v: int(v * .7))); L.alpha_composite(rc)
        text(L, (540, cy + 8), s, font(SHIP, 250), anchor='mm', grad=GOLD, shadow=.75)
        S = o('A', a); D = b - a
        add('X-count', '倒数 ' + s, S, D, save(L, 'count_' + s), ay=cy / H,
            k={'scale': kf((0, 1.3), (.25, 1.0), (D, .97)), 'opacity': kf((0, 0), (.12, 1), (max(.13, D - .1), 1), (D, 0))})
        sfx('u_pop', S, .4)

# ---------------- 溺愛度（无框：心形 + 明朝数字 + 发光细线） ----------------
def heart_poly(hx, hy, r):
    return [(hx + r * 16 * math.sin(a) ** 3 / 16, hy - r * (13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)) / 16) for a in np.linspace(0, 2 * math.pi, 90)]
def meter_vals():
    nodes = [(INTRO, 10)]
    for (vid, s0, D, fr), v in zip(CH[:2], [45, 90]): nodes.append((s0 + MRISE, v))
    return nodes
def meter_at(T):
    nodes = meter_vals(); v = nodes[0][1]; glow = 0
    for i in range(1, len(nodes)):
        t, nv = nodes[i]; pv = nodes[i - 1][1]
        if T >= t:
            p = clamp((T - t) / .7); p = p * p * (3 - 2 * p); v = pv + (nv - pv) * p
            if T - t < 1.0: glow = max(glow, 1 - (T - t))
    return v, glow
MX, MY = 58, 120
def meter_frame(T):
    A = ease((T - INTRO) / .45); dy = -16 * (1 - A)
    v, glow = meter_at(T); L = canvas()
    hx, hy = MX + 18, MY + 42 + dy
    if glow > 0:
        G = Image.new('L', (W, H), 0); ImageDraw.Draw(G).ellipse([hx - 50, hy - 50, hx + 50, hy + 50], fill=int(170 * glow))
        G = G.filter(ImageFilter.GaussianBlur(16)); gc = Image.new('RGBA', (W, H), (214, 120, 90, 0)); gc.putalpha(G); L.alpha_composite(gc)
    hm = Image.new('L', (W, H), 0); ImageDraw.Draw(hm).polygon(heart_poly(hx, hy, 17 * (1 + .15 * glow)), fill=255)
    bb = hm.getbbox(); c = hm.crop(bb)
    sh = c.filter(ImageFilter.GaussianBlur(5)); s_ = Image.new('RGBA', c.size, (0, 0, 0, 0)); s_.putalpha(sh.point(lambda q: int(q * .5 * A))); _paste(L, s_, bb[0], bb[1] + 3)
    col = grad_img(c.width, c.height, HEAT).convert('RGBA'); col.putalpha(c.point(lambda q: int(q * A))); _paste(L, col, bb[0], bb[1])
    text(L, (MX + 48, MY + 54 + dy), '溺愛度', font(NOTOB, 30), SUB, a=A, shadow=.6)
    text(L, (MX + 372, MY + 62 + dy), str(int(round(v))), font(SHIP, 66), WH, a=A, anchor='rs', shadow=.6)
    bx0, bx1, by = MX, MX + 372, int(MY + 86 + dy)
    tr = Image.new('RGBA', (bx1 - bx0, 3), (255, 255, 255, int(60 * A))); _paste(L, tr, bx0, by)
    fw = int((bx1 - bx0) * v / 100)
    if fw > 2:
        g = grad_img(bx1 - bx0, 3, HEAT, horiz=True).crop((0, 0, fw, 3)).convert('RGBA'); g.putalpha(int(255 * A))
        gl = Image.new('L', (fw + 40, 43), 0); gl.paste(255, (20, 20, 20 + fw, 23)); gl = gl.filter(ImageFilter.GaussianBlur(7))
        gc = Image.new('RGBA', gl.size, (226, 150, 110, 0)); gc.putalpha(gl.point(lambda q: int(q * (.5 + .5 * glow) * A))); _paste(L, gc, bx0 - 20, by - 20)
        _paste(L, g, bx0, by)
        d = ImageDraw.Draw(L); ex = bx0 + fw; d.ellipse([ex - 4, by - 3, ex + 4, by + 5], fill=(255, 240, 225, int(255 * A)))
    return L
def meter():
    ks = set()
    for a, b in [(INTRO, INTRO + .5)] + [(s0 + MRISE, s0 + MRISE + 1.0) for (_, s0, _, _) in CH[:2]]:
        for k in range(int(round(a * 15)), int(round(b * 15)) + 1): ks.add(k)
    ks = sorted(ks)
    for i, k in enumerate(ks):
        T = k / 15; T1 = ks[i + 1] / 15 if i + 1 < len(ks) and ks[i + 1] == k + 1 else None
        if T1 is None:   # 静止段：保持到下一个变化或片尾
            nx = [q for q in ks if q > k]; T1 = nx[0] / 15 if nx else PH0
        add('X-meter', '溺愛度', T, T1 - T, save(meter_frame(T), f'meter_{k:04d}'))
    for (vid, s0, D, fr) in CH[:2]: sfx('u_coin', s0 + MRISE, .55)

# ---------------- 选项（无框：明朝序号 + 文字 + 细线） ----------------
def pointer_imgs():
    L = canvas(); r = 40
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([540 - r - 6, 960 - r, 540 + r + 6, 960 + r + 14], fill=110); g = g.filter(ImageFilter.GaussianBlur(12))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(g); L.alpha_composite(sh)
    d = ImageDraw.Draw(L); d.ellipse([540 - r, 960 - r, 540 + r, 960 + r], fill=(255, 255, 255, 95), outline=(255, 255, 255, 220), width=3)
    d.ellipse([540 - 8, 960 - 8, 540 + 8, 960 + 8], fill=(255, 255, 255, 240))
    R = canvas(); ImageDraw.Draw(R).ellipse([540 - 50, 960 - 50, 540 + 50, 960 + 50], outline=(255, 255, 255, 220), width=4)
    return save(L, 'pointer'), save(R, 'ripple')
OY = {3: [900, 1050, 1200], 2: [960, 1110]}
OX0, OX1 = 150, 930
def opt_img(bg, txt, y, sel):
    L = canvas()
    if sel:   # 选中：一条极淡的横向光带 + 香槟色文字与发光细线
        band = np.clip(1 - np.abs(np.linspace(-1, 1, OX1 - OX0 + 160)), 0, 1) ** .8
        vb = np.clip(1 - np.abs(np.linspace(-1, 1, 130)), 0, 1) ** 1.5
        a = (vb[:, None] * band[None] * 46).astype(np.uint8)
        b_ = Image.new('RGBA', (OX1 - OX0 + 160, 130), (255, 236, 205, 0)); b_.putalpha(Image.fromarray(a)); _paste(L, b_, OX0 - 80, int(y - 65))
        G = Image.new('L', (W, 60), 0); ImageDraw.Draw(G).rectangle([OX0, 28, OX1, 31], fill=255); G = G.filter(ImageFilter.GaussianBlur(8))
        gc = Image.new('RGBA', (W, 60), (236, 200, 150, 0)); gc.putalpha(G.point(lambda q: int(q * .9))); _paste(L, gc, 0, int(y + 50 - 28))
        hair(L, OX0, OX1, y + 50, 1, w=2, fade=False, stops=EMPH)
    else:
        hair(L, OX0, OX1, y + 50, .5, w=2, fade=True, stops=[(0, (255, 255, 255)), (1, (255, 255, 255))])
    num, s = txt[0], txt[1:]
    n = str('①②③'.index(num) + 1)
    text(L, (OX0 + 22, y + 20), n, font(SHIP, 64), None, anchor='ls', shadow=.5, grad=GOLD if not sel else EMPH)
    text(L, (OX0 + 96, y + 18), s, font(NOTOB, 52), WH, anchor='ls', shadow=.55, grad=EMPH if sel else None)
    return L
def question(ci):
    q1, q2 = QS[ci]; L = canvas()
    hair(L, 500, 580, 560, 1, w=2, fade=False, stops=GOLD)
    text(L, (540, 640), q1, font(NOTOB, 42), SUB, anchor='mm', shadow=.6)
    text(L, (540, 710), q2, font(NOTOB, 46), WH, anchor='mm', shadow=.6)
    return L
def choices_v3(pf, rf):
    flashf = save(Image.new('RGBA', (W, H), (255, 255, 255, 255)), 'flash')
    for ci, (vid, s0, D, fr) in enumerate(CH):
        bgi = BLUR[ci]; last = ci == 2
        bf = save(bgi.convert('RGBA'), f'ch{ci + 1}_blur')
        add('X-cblur', f'选项{ci + 1} 失焦', s0, D + (0 if last else OUTF), bf,
            k={'opacity': kf((0, 0), (.25, 1)) if last else kf((0, 0), (.25, 1), (D, 1), (D + OUTF, 0))})
        add('X-flash', f'选项{ci + 1} 闪光', s0, .3, flashf, k={'opacity': kf((0, .55), (.3, 0))})
        sfx('u_flash', s0, .6)
        ex = lambda st: [(D - .28 - st, 1), (D - .02 - st, 0)] if not last else []
        L = question(ci)
        add('X-cq', f'选项{ci + 1} 提问', s0 + .15, D - .15, save(L, f'ch{ci + 1}_q'), ay=660 / H,
            k={'opacity': kf((0, 0), (.25, 1), *ex(.15)), 'y': kf((0, 34), (.35, 0)), 'scale': kf((0, .96), (.35, 1))})
        sfx('u_bubble', s0 + .18, .45)
        opts = OPTS[ci]; ys = OY[len(opts)]; pick = 0 if not last else None
        for oi, (txt, y) in enumerate(zip(opts, ys)):
            t0 = s0 + .4 + oi * .14; fn = save(opt_img(bgi, txt, y, False), f'ch{ci + 1}_o{oi + 1}')
            k = {'y': kf((0, 40), (.32, 0)), 'opacity': kf((0, 0), (.2, 1), *ex(t0 - s0))}
            if pick is not None and oi != pick:
                r0 = s0 + 2.0 - t0; k['opacity'] = kf((0, 0), (.2, 1), (r0, 1), (r0 + .28, 0)); k['scale'] = kf((r0, 1), (r0 + .28, .94))
            if pick is not None and oi == pick:
                r0 = s0 + 2.05 - t0; k['opacity'] = kf((0, 0), (.2, 1), (r0 + .05, 1), (r0 + .1, 0))
            add(f'X-co{oi + 1}', f'选项{ci + 1} {txt}', t0, (s0 + 2.05 + .1 - t0) if (pick is not None and oi == pick) else s0 + D - t0, fn, ay=y / H, k=k)
            sfx('u_bubble', t0 + .04, .25)
        if pick is not None:
            y = ys[pick]; sf = save(opt_img(bgi, opts[pick], y, True), f'ch{ci + 1}_sel')
            add('X-cs', f'选项{ci + 1} 选中', s0 + 2.05, D - 2.05, sf, ay=y / H,
                k={'scale': kf((0, 1), (.14, 1.06), (.32, 1.03)), 'opacity': kf((0, .2), (.1, 1), (.25, .55), (.4, 1), (.55, .6), (.7, 1), (D - 2.05 - .28, 1), (D - 2.05 - .02, 0))})
            px, py = 880 - 540, y + 12 - 960
            add('X-ptr', f'选项{ci + 1} 指针', s0 + 1.15, 1.35, pf, k={'x': kf((0, px + 160), (.4, px)), 'y': kf((0, py + 380), (.4, py)),
                'opacity': kf((0, 0), (.15, 1), (1.05, 1), (1.35, 0)), 'scale': kf((.68, 1), (.74, .8), (.86, 1))})
            add('X-prip', f'选项{ci + 1} 点击波纹', s0 + 1.89, .45, rf, k={'x': kf((0, px)), 'y': kf((0, py)), 'scale': kf((0, .7), (.45, 2.2)), 'opacity': kf((0, .9), (.45, 0))})
            sfx('u_click', s0 + 1.87, .8); sfx('u_ok', s0 + 2.05, .7)
            sfx('s_whoosh', s0 + D - .15, .45)
        else:
            p1, p2 = (880 - 540, ys[0] + 12 - 960), (880 - 540, ys[1] + 12 - 960)
            add('X-ptr', f'选项{ci + 1} 指针犹豫', s0 + 1.15, D - 1.15, pf,
                k={'x': kf((0, p1[0] + 160), (.4, p1[0]), (1.0, p1[0]), (1.3, p2[0] - 30), (1.8, p2[0] - 30), (2.1, p1[0] + 20), (D - 1.15, p1[0] + 20)),
                   'y': kf((0, p1[1] + 380), (.4, p1[1]), (1.0, p1[1]), (1.3, p2[1]), (1.8, p2[1]), (2.1, p1[1]), (D - 1.15, p1[1])),
                   'opacity': kf((0, 0), (.15, 1))})
            add('X-flash', '选项3→片尾 闪光', s0 + D - .22, .6, flashf, k={'opacity': kf((0, 0), (.2, 1), (.6, 0))})
            sfx('u_flash', s0 + D - .2, .7)

# ---------------- 片尾 ----------------
def endcard(pf, rf):
    im = frame('B', ENDF)
    b = im.filter(ImageFilter.GaussianBlur(3)); b = ImageEnhance.Brightness(b).enhance(.62)
    a = np.asarray(b).astype(np.float32); yy = np.arange(H, dtype=np.float32)[:, None, None]
    shade = np.clip((yy - 700) / 700, 0, 1) * .78 + np.clip(1 - yy / 420, 0, 1) * .5
    a = a * (1 - shade) + np.array([10, 9, 8], np.float32) * shade
    bgi = Image.fromarray(a.astype(np.uint8))
    add('V1', '片尾 背景', END0, ED, save(bgi.convert('RGBA'), 'end_bg'), k={'scale': kf((0, 1.0), (ED, 1.05))})
    sfx('u_end', END0, .5)
    # Logo
    icon = Image.open(ASSET + 'LOGO-256x256-圆角.png').convert('RGBA').resize((96, 96), Image.LANCZOS)
    wm = Image.open(APP + 'public/assets/product-logo.png').convert('RGBA'); wm = wm.resize((int(wm.width * 46 / wm.height), 46), Image.LANCZOS)
    rw = 96 + 22 + wm.width; x0 = (W - rw) // 2; y0 = 150
    Lg = canvas(); Lg.alpha_composite(icon, (x0, y0)); Lg.alpha_composite(wm, (x0 + 118, y0 + 25))
    add('X-elogo', '片尾 Logo', END0 + .08, ED - .08, save(Lg, 'end_logo'), k={'opacity': kf((0, 0), (.25, 1)), 'y': kf((0, -20), (.3, 0))})
    # 标题（明朝金）
    L = canvas(); text(L, (540, 1080), END_TAG, font(SHIP, 136), anchor='ms', grad=GOLD, shadow=.8)
    add('X-ecard', '片尾 卡片标题', END0 + .2, ED - .2, save(L, 'end_title'), ay=1020 / H,
        k={'opacity': kf((0, 0), (.22, 1)), 'scale': kf((0, 1.12), (.3, 1)), 'y': kf((0, 20), (.3, 0))})
    sfx('u_pop', END0 + .2, .5)
    # 玻璃文案卡
    f = font(NOTO, 52); tw = max(f.getlength(s) for s in END_COPY); bw = tw + 120
    L = canvas()
    hair(L, 420, 660, 1150, .9); text(L, (540, 1212), END_COPY[0], font(NOTOB, 50), WH, anchor='mm', shadow=.7); text(L, (540, 1282), END_COPY[1], font(NOTOB, 50), WH, anchor='mm', shadow=.7)
    add('X-ehead', '片尾 文案', END0 + .38, ED - .38, save(L, 'end_copy'), ay=1230 / H, k={'y': kf((0, 30), (.3, 0)), 'opacity': kf((0, 0), (.22, 1))})
    # 金色按钮
    bx0, by0, bx1, by1 = 150, 1400, 930, 1536
    L = canvas()
    G = Image.new('L', (W, H), 0); ImageDraw.Draw(G).rounded_rectangle([bx0, by0 + 6, bx1, by1 + 6], radius=70, fill=90)
    G = G.filter(ImageFilter.GaussianBlur(30)); gc = Image.new('RGBA', (W, H), (226, 180, 110, 0)); gc.putalpha(G); L.alpha_composite(gc)
    glass(L, bgi, (bx0, by0, bx1, by1), 68, fill=grad_img(10, 10, GOLD, horiz=True), shadow=.35, rimk=.5)
    text(L, (540, (by0 + by1) / 2 + 2), BTN, font(NOTO, 52), DARK, anchor='mm', shadow=0)
    BS = END0 + .62; TAPS = [1.2, 1.5, 1.8, 2.1]
    bsc = [[0, .7], [.18, 1.04], [.28, 1]]
    for tp in TAPS: r = END0 + tp - BS; bsc += [[round(r - .04, 3), 1], [round(r + .04, 3), .95], [round(r + .16, 3), 1]]
    add('X-ebtn', '片尾 下载按钮', BS, END1 - BS, save(L, 'end_btn'), ay=(by0 + by1) / 2 / H, k={'scale': bsc, 'opacity': kf((0, 0), (.12, 1))})
    sfx('u_bubble', BS, .45)
    # 按钮扫光（循环两次）
    bm = rr_mask(bx1 - bx0, by1 - by0, 70); bma = np.asarray(bm).astype(np.float32) / 255
    yy, xx = np.mgrid[0:by1 - by0, 0:bx1 - bx0]
    for j in range(8):
        c = -80 + j * 130; band = np.clip(1 - np.abs((xx + (yy - 70) * .5) - c) / 60, 0, 1) ** 2 * .55
        S = canvas(); s_ = Image.new('RGBA', (bx1 - bx0, by1 - by0), (255, 255, 255, 0)); s_.putalpha(Image.fromarray((bma * band * 255).astype(np.uint8))); S.alpha_composite(s_, (bx0, by0))
        fn = save(S, f'end_sheen{j}')
        for st in (END0 + .9, END0 + 1.62):
            add('X-esheen', '片尾 按钮扫光', st + j / 15, 1 / 15, fn, ay=(by0 + by1) / 2 / H, k={'scale': bsc and [[0, 1]]})
    # 商店标（等大）
    gp = Image.open(ASSET + 'Google_Play_Badge_JA.svg.png').convert('RGBA'); gp = gp.resize((int(gp.width * 88 / gp.height), 88), Image.LANCZOS)
    ios = Image.open(ASSET + 'ios_badge.png').convert('RGBA'); ios = ios.crop(ios.split()[3].getbbox()); ios = ios.resize((int(ios.width * 88 / ios.height), 88), Image.LANCZOS)
    inner = ios.crop((8, 6, ios.width - 8, ios.height - 6))
    nb = Image.new('RGBA', gp.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(nb)
    bd.rounded_rectangle([0, 0, gp.width - 1, gp.height - 1], radius=14, fill=(0, 0, 0, 255), outline=(166, 166, 166, 255), width=2)
    nb.alpha_composite(inner, ((gp.width - inner.width) // 2, (gp.height - inner.height) // 2)); ios = nb
    gap = 28; tot = gp.width + gap + ios.width; x0 = (W - tot) // 2
    Sb = canvas(); Sb.alpha_composite(gp, (x0, 1620)); Sb.alpha_composite(ios, (x0 + gp.width + gap, 1620))
    add('X-ebadge', '片尾 商店标', END0 + .8, ED - .8, save(Sb, 'end_badges'), k={'opacity': kf((0, 0), (.22, 1)), 'y': kf((0, 20), (.28, 0))})
    # 指针连点
    px, py = bx1 - 90 - 540, (by0 + by1) / 2 + 10 - 960
    P0 = 1.0; sc = [[0, 1]]
    for tp in TAPS: r = tp - P0; sc += [[round(r - .04, 3), 1], [round(r + .03, 3), .8], [round(r + .13, 3), 1]]
    add('X-eptr', '片尾 指针', END0 + P0, ED - P0, pf, k={'x': kf((0, px + 140), (.18, px)), 'y': kf((0, py + 240), (.18, py)), 'opacity': kf((0, 0), (.1, 1)), 'scale': sc})
    for i, tp in enumerate(TAPS):
        add(f'X-erip{i % 2 + 1}', '片尾 点击波纹', END0 + tp, min(.4, ED - tp), rf, k={'x': kf((0, px)), 'y': kf((0, py)), 'scale': kf((0, .7), (.4, 2.0)), 'opacity': kf((0, .9), (.4, 0))})
        sfx('u_click', END0 + tp, .55)

# ======================================================================
# v4：开头特效重做（逐帧烘焙） / 目标 / 选项犹豫 + 弹幕 / AI 聊天手机（试玩广告 UI）
# ======================================================================
FPS = 30
def blit(dst, spr, cx, cy, sc=1., a=1.):
    if a <= .003 or sc <= .01: return
    s = spr if abs(sc - 1) < 1e-3 else spr.resize((max(1, int(spr.width * sc)), max(1, int(spr.height * sc))), Image.BILINEAR)
    if a < .999:
        arr = np.array(s); arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8); s = Image.fromarray(arr)
    _paste(dst, s, int(round(cx - s.width / 2)), int(round(cy - s.height / 2)))
def crop_spr(L):
    bb = L.getbbox(); return L.crop(bb), (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
def tint(spr, rgb, a=1.):
    arr = np.array(spr); arr[..., 0], arr[..., 1], arr[..., 2] = rgb; arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8); return Image.fromarray(arr)
def glow_of(spr, rgb, r, a=1., pad=60):
    m = Image.new('L', (spr.width + pad * 2, spr.height + pad * 2), 0); m.paste(spr.split()[3], (pad, pad))
    m = m.filter(ImageFilter.GaussianBlur(r)); g = Image.new('RGBA', m.size, rgb + (0,)); g.putalpha(m.point(lambda v: int(min(255, v * a)))); return g
def eob(x, s=1.7):
    x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def disc(r, rgb, soft=.6):
    n = int(r * 4) + 4; g = Image.new('L', (n, n), 0); ImageDraw.Draw(g).ellipse([n / 2 - r, n / 2 - r, n / 2 + r, n / 2 + r], fill=255)
    g = g.filter(ImageFilter.GaussianBlur(max(.5, r * soft))); s = Image.new('RGBA', (n, n), rgb + (0,)); s.putalpha(g); return s
def logo_row(icon_h=112, wm_h=46, de=True, y=600):
    icon = Image.open(ASSET + 'LOGO-256x256-圆角.png').convert('RGBA').resize((icon_h, icon_h), Image.LANCZOS)
    wm = Image.open(APP + 'public/assets/product-logo.png').convert('RGBA'); wm = wm.resize((int(wm.width * wm_h / wm.height), wm_h), Image.LANCZOS)
    fd = font(NOTOB, 52); dw = fd.getlength('で') + 14 if de else 0
    tot = icon_h + 24 + wm.width + dw; x = 540 - tot / 2
    L = canvas(); sh = glow_of(icon, (0, 0, 0), 10, .55, 30); _paste(L, sh, int(x) - 30, int(y - icon_h / 2) - 30 + 6)
    L.alpha_composite(icon, (int(x), int(y - icon_h / 2))); x2 = x + icon_h + 24
    _paste(L, glow_of(wm, (0, 0, 0), 6, .5, 20), int(x2) - 20, int(y - wm_h / 2) - 20 + 3)
    L.alpha_composite(wm, (int(x2), int(y - wm_h / 2)))
    if de: text(L, (x2 + wm.width + 14, y + 19), 'で', fd, WH, anchor='ls', shadow=.5)
    return L

# ---------------- 开头（30fps 逐帧：光斑 / 金尘 / Logo 冲击环 / 逐字色散砸入 / 冲击闪白震屏 + 火花 + 速度线 + 横向光晕 / 扫光 / 目标 HUD 闪烁 / 推镜出场） ----------------
def intro():
    N = int(round(INTRO * FPS)); rng = np.random.default_rng(7)
    bg0 = soft_bg(frame('A', 0.0), 30, .5)
    logo, lcx, lcy = crop_spr(logo_row())
    halo = disc(120, (255, 214, 160), .7)
    f1, f2 = font(SHIP, 112), font(SHIP, 172); s1, s2 = '貞操逆転世界に', '転移する'
    w1 = f1.getlength(s1); x1 = 540 - w1 / 2; Y1, Y2 = 850, 1050
    chars = []
    for i, ch in enumerate(s1):
        L = canvas(); text(L, (x1 + f1.getlength(s1[:i]), Y1), ch, f1, WH, anchor='ls', shadow=.75, grad=GOLD if i < 4 else None); chars.append(crop_spr(L))
    L = canvas(); text(L, (540, Y2), s2, f2, WH, anchor='ms', shadow=.75); t2 = crop_spr(L)
    tm = Image.new('L', (W, H), 0); dm_ = ImageDraw.Draw(tm); dm_.text((x1, Y1), s1, font=f1, fill=255, anchor='ls'); dm_.text((540, Y2), s2, font=f2, fill=255, anchor='ms')
    tma = np.asarray(tm).astype(np.float32) / 255
    # 目标
    ft = font(NOTOB, 42); tw = ft.getlength(GOAL_TAG) + 56
    L = canvas(); ImageDraw.Draw(L).rounded_rectangle([540 - tw / 2, 1190, 540 + tw / 2, 1258], radius=10, fill=WINE + (245,))
    text(L, (540, 1225), GOAL_TAG, ft, WH, anchor='mm', shadow=0); gtag = crop_spr(L)
    L = canvas(); text(L, (540, 1372), GOAL, font(SHIP, 104), WH, anchor='ms', shadow=.8); gtxt = crop_spr(L)
    gglow = glow_of(gtxt[0], (232, 52, 82), 26, 1.1)
    GC = (540, (1176 + 1400) / 2)
    # 粒子
    dust = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(-60, -15), rng.uniform(-10, 10), rng.uniform(1.5, 5), rng.uniform(0, 6.3)) for _ in range(60)]
    dspr = {r: disc(r, (255, 228, 186)) for r in (2, 3, 4, 5)}
    IMP = 1.0; CX, CY = 540, 995
    sparks = [(rng.uniform(0, 6.283), rng.uniform(500, 1400), rng.uniform(.45, .8)) for _ in range(46)]
    rays = [(a + rng.uniform(-.04, .04), rng.uniform(.8, 1.2)) for a in np.linspace(0, 6.283, 56, endpoint=False)]
    qy, qx = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32)
    fy = np.arange(CY - 120, CY + 120, dtype=np.float32)[:, None]; fx = np.arange(W, dtype=np.float32)[None]
    flare = (np.exp(-((fy - CY) / 5) ** 2) * np.exp(-((fx - 540) / 420) ** 2) + .35 * np.exp(-((fy - CY) / 38) ** 2) * np.exp(-((fx - 540) / 300) ** 2))[..., None] * np.array([255, 226, 190], np.float32)
    for fi in range(N):
        T = fi / FPS; age = T - IMP
        shk = 18 * (1 - age / .4) ** 2 if 0 <= age < .4 else 0
        sx, sy = shk * math.sin(age * 95), shk * math.cos(age * 71)
        pe = eio((T - 2.6) / .4)
        z = 1.12 - .08 * eio(T / 2.6) + .14 * pe
        bgr = bg0.resize((int(W * z), int(H * z)), Image.BILINEAR)
        ox, oy = (bgr.width - W) / 2 - sx, (bgr.height - H) / 2 - sy
        fr_ = bgr.crop((int(ox), int(oy), int(ox) + W, int(oy) + H)).convert('RGBA')
        ov = canvas()
        for (x0, y0, vy, vx, r, ph) in dust:
            yy_ = (y0 + vy * T) % H; xx_ = x0 + vx * T; a = .2 + .6 * abs(math.sin(ph + T * 2.4))
            blit(ov, dspr[min(5, max(2, int(round(r))))], xx_, yy_, 1, a * clamp(T / .3))
        # Logo
        if T >= .08:
            p = (T - .08) / .4
            blit(ov, halo, lcx, lcy, .6 + .5 * eio(p), .55 * clamp(p * 3) * (1 - .5 * eio((T - .6) / .6)))
            blit(ov, logo, lcx, lcy, .45 + .55 * eob(p), clamp(p * 3))
        # 冲击环（Logo / 标题）
        rl = canvas(); dr = ImageDraw.Draw(rl)
        for t0, cx, cy, r0, r1, w_ in [(.14, lcx, lcy, 70, 520, 4), (IMP, CX, CY, 120, 900, 6)]:
            q = (T - t0) / .55
            if 0 <= q < 1:
                r = r0 + (r1 - r0) * ease(q); dr.ellipse([cx - r, cy - r * .92, cx + r, cy + r * .92], outline=(255, 236, 206, int(220 * (1 - q) ** 1.5)), width=max(1, int(w_ * (1 - q) + 1)))
        # 速度线 + 火花
        q = age / .42
        if 0 <= q < 1:
            for a, k in rays:
                ri = 300 + 950 * ease(q) * k; ro = ri + 260 * (1 - q)
                dr.line([CX + math.cos(a) * ri, CY + math.sin(a) * ri * 1.2, CX + math.cos(a) * ro, CY + math.sin(a) * ro * 1.2], fill=(255, 238, 210, int(190 * (1 - q))), width=3)
        if age >= 0:
            for a, v, life in sparks:
                if age < life:
                    px = CX + math.cos(a) * v * age; py = CY + math.sin(a) * v * age * .8 + 700 * age * age
                    ln = v * .03; vx_, vy_ = math.cos(a), math.sin(a) * .8 + 1400 * age / v
                    nn = math.hypot(vx_, vy_) + 1e-6
                    dr.line([px, py, px - vx_ / nn * ln, py - vy_ / nn * ln], fill=(255, 240, 214, int(255 * (1 - age / life))), width=3)
        ov.alpha_composite(rl)
        # 标题一行：逐字色散砸入
        for i, (spr, cx, cy) in enumerate(chars):
            p = (T - (.34 + i * .06)) / .2
            if p < 0: continue
            sc = 1 + 1.0 * (1 - ease(p)); a = clamp(p * 2.5); d = 26 * (1 - ease(p))
            if d > .6:
                blit(ov, tint(spr, (255, 50, 80), .6), cx + d, cy, sc, a); blit(ov, tint(spr, (60, 210, 255), .6), cx - d, cy, sc, a)
            blit(ov, spr, cx, cy, sc, a)
        # 「転移する」砸下
        p = (T - (IMP - .12)) / .12
        if p >= 0:
            spr, cx, cy = t2
            sc = 1 + 1.5 * (1 - clamp(p)) ** 2 if p < 1 else 1 + .05 * math.exp(-age * 7) * math.cos(age * 28)
            d = 30 * math.exp(-max(0, age) * 9) if p >= 1 else 0
            if d > .6:
                blit(ov, tint(spr, (255, 50, 80), .55), cx + d, cy, sc, 1); blit(ov, tint(spr, (60, 210, 255), .55), cx - d, cy, sc, 1)
            blit(ov, spr, cx, cy, sc, clamp(p * 2))
        # 目标 HUD
        if T >= 1.6:
            pb = ease((T - 1.6) / .3); hw, hh = 400 * (.25 + .75 * pb), 128 * (.25 + .75 * pb); L_ = 46
            bl = canvas(); db = ImageDraw.Draw(bl); col = (236, 220, 196, int(235 * pb))
            for sx_, sy_ in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                X, Y = GC[0] + sx_ * hw, GC[1] + sy_ * hh
                db.line([X, Y, X - sx_ * L_, Y], fill=col, width=4); db.line([X, Y, X, Y - sy_ * L_], fill=col, width=4)
            ov.alpha_composite(bl)
            blink = 1.0
            for t_on in (2.16, 2.30):
                if t_on <= T < t_on + .07: blink = .15
            gp = clamp((T - 1.84) / .3)
            if T >= 1.72:
                spr, cx, cy = gtag; blit(ov, spr, cx, cy, .7 + .3 * eob((T - 1.72) / .25), clamp((T - 1.72) / .12) * blink)
            if gp > 0:
                spr, cx, cy = gtxt
                flash = max([math.exp(-(T - t_) * 9) for t_ in (2.23, 2.37) if T >= t_] + [0])
                blit(ov, gglow, cx, cy, 1, (.45 + .55 * flash) * gp * blink)
                cw = max(1, int(spr.width * ease(gp))); part = spr.crop((0, 0, cw, spr.height))
                d = 12 * (1 - gp)
                if d > .6:
                    blit(ov, tint(part, (255, 50, 80), .6), cx - spr.width / 2 + cw / 2 + d, cy, 1, 1); blit(ov, tint(part, (60, 210, 255), .6), cx - spr.width / 2 + cw / 2 - d, cy, 1, 1)
                blit(ov, part, cx - spr.width / 2 + cw / 2, cy, 1, blink)
        # 出场：推镜放大 + 淡出
        if pe > 0:
            s_ = 1 + .3 * pe; big = ov.resize((int(W * s_), int(H * s_)), Image.BILINEAR)
            ov = big.crop((int((big.width - W) / 2), int((big.height - H) / 2), int((big.width - W) / 2) + W, int((big.height - H) / 2) + H))
            arr = np.array(ov); arr[..., 3] = (arr[..., 3] * (1 - pe)).astype(np.uint8); ov = Image.fromarray(arr)
        _paste(fr_, ov, int(round(sx)), int(round(sy)))
        arr = np.asarray(fr_.convert('RGB')).astype(np.float32)
        # 光斑（暖色漏光，斜向划过）
        lk = .32 * math.sin(math.pi * clamp(T / 1.7)) + .25 * pe
        if lk > .01:
            cxq, cyq = (-200 + 1500 * clamp(T / 1.7)) / 4, (200 + 1200 * clamp(T / 1.7)) / 4
            blob = np.exp(-(((qx - cxq) ** 2 + (qy - cyq) ** 2) / (2 * 150 ** 2)))
            bi = np.asarray(Image.fromarray((blob * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32)[..., None] / 255
            arr += bi * lk * np.array([255, 178, 112], np.float32)
        # 标题扫光
        if 1.28 <= T < 1.78:
            c = -200 + (T - 1.28) / .5 * 1500
            yy_, xx_ = np.mgrid[700:1100, 0:W].astype(np.float32)
            band = np.clip(1 - np.abs((xx_ + (yy_ - 950) * .45) - c) / 80, 0, 1) ** 2
            arr[700:1100] += (band * tma[700:1100] * .75)[..., None] * np.array([255, 246, 228], np.float32)
        # 横向光晕
        if 0 <= age < .7:
            arr[CY - 120:CY + 120] += flare * math.exp(-age / .2) * .9
        fl_ = (.32 * math.exp(-age / .08) if age >= 0 else 0) + .9 * eio((T - 2.78) / .2)
        if fl_ > .005: arr += (255 - arr) * min(1, fl_)
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        add('X-intro', '开头 逐帧', T, 1 / FPS, save_jpg(im, f'intro_{fi:03d}'), ext='.jpg')
    flashf = save(Image.new('RGBA', (W, H), (255, 255, 255, 255)), 'flash')
    add('X-flash', '开头→第一幕 闪白', INTRO, .3, flashf, k={'opacity': kf((0, .75), (.3, 0))})
    sfx('u_end', .02, .35); sfx('u_pop', .1, .4)
    for i in range(0, 7, 2): sfx('u_bubble', .34 + i * .06, .18)
    sfx('u_pop', IMP - .02, .65); sfx('u_ok', 1.74, .5); sfx('u_click', 2.16, .35); sfx('u_click', 2.30, .35); sfx('s_whoosh', 2.62, .5)

# ---------------- 目标条（选项内闪烁强调） ----------------
GY = 432
def goal_row():
    ft, fg = font(NOTOB, 36), font(NOTO, 56); tw = ft.getlength(GOAL_TAG) + 40; gw = fg.getlength(GOAL); tot = tw + 20 + gw; x0 = 540 - tot / 2
    L = canvas(); ImageDraw.Draw(L).rounded_rectangle([x0, GY - 29, x0 + tw, GY + 29], radius=8, fill=WINE + (245,))
    text(L, (x0 + tw / 2, GY + 1), GOAL_TAG, ft, WH, anchor='mm', shadow=0)
    text(L, (x0 + tw + 20, GY + 2), GOAL, fg, WH, anchor='lm', shadow=.7)
    G = canvas(); g = glow_of(L.crop(L.getbbox()), (232, 52, 82), 18, 1.2); bb = L.getbbox(); _paste(G, g, bb[0] - 60, bb[1] - 60)
    return save(L, 'goal_row'), save(G, 'goal_glow')
def goal_layers(s0, D, ex_t):
    gf, gg = GOAL_FILES
    blink = [(0, 0), (.06, 1), (.13, .1), (.2, 1), (.27, .1), (.34, 1)]
    k = {'opacity': kf(*blink, *ex_t), 'scale': kf((0, 1.25), (.18, .97), (.3, 1))}
    add('X-cgoal', '目标', s0 + .12, D - .12, gf, ay=GY / H, k=k)
    pts = [(0, 0), (.06, 1), (.13, 0), (.2, 1), (.27, 0), (.34, 1)]; t = .34
    while t < D - .4: pts += [(t + .45, .25), (t + .9, .9)]; t += .9
    pts = [p for p in pts if p[0] < D - .12 - .05]
    add('X-cgoalg', '目标 闪烁光', s0 + .12, D - .12, gg, ay=GY / H, k={'opacity': kf(*pts, *ex_t)})

# ---------------- 弹幕 ----------------
DM_LANES = [292, 1350, 1440, 1530, 1620, 1710]
DM_ORDER = [1, 3, 0, 4, 2, 5, 1, 3]
def danmaku():
    f = font(NOTO, 50)
    for ci, (vid, s0, D, fr) in enumerate(CH):
        for i, s in enumerate(DM[ci]):
            st = s0 + .6 + i * .55
            if st > s0 + D - 1.0: break
            y = DM_LANES[DM_ORDER[i % len(DM_ORDER)]]; col = (246, 222, 180) if i % 3 == 1 else WH
            L = canvas(); ImageDraw.Draw(L).text((540, 960), s, font=f, fill=col + (255,), anchor='mm', stroke_width=4, stroke_fill=(14, 10, 12, 235))
            tw = f.getlength(s); span = 540 + tw / 2 + 24; dur = 4.0
            cut = min(dur, s0 + D - .02 - st)
            op = kf((0, .95)) if cut >= dur - 1e-3 else kf((0, .95), (max(0, cut - .2), .95), (cut, 0))
            add(f'X-dm{i % 8 + 1}', f'弹幕 {s}', st, cut, save(L, f'dm{ci + 1}_{i}'), k={'x': kf((0, span), (dur, -span)), 'y': kf((0, y - 960)), 'opacity': op})

# ---------------- 选项（指针犹豫 2 秒 + 目标 + 弹幕） ----------------
HOVER = [[(1.0, 1), (1.7, 2), (2.45, 0), (3.05, 1), (3.45, 0)],    # 第一幕 → 点①
         [(1.0, 2), (1.7, 1), (2.4, 2), (3.0, 0), (3.4, 1), (3.7, 0)],   # 第二幕 → 点①
         [(1.0, 0), (1.8, 1), (2.6, 0), (3.3, 1), (4.0, 0), (4.6, 1)]]   # 第三幕：来回犹豫不点
def ptr_pos(ys, idx): return (880 - 540 - 26 * (idx % 2), ys[idx] + 12 - 960)
def ptr_path(ys, hov):
    x0, y0 = ptr_pos(ys, hov[0][1]); xs = [(0, x0 + 170)]; yy_ = [(0, y0 + 400)]
    for j in range(1, 7):
        q = eio(j / 6); xs.append((.4 * j / 6, x0 + 170 * (1 - q))); yy_.append((.4 * j / 6, y0 + 400 * (1 - q)))
    t0 = hov[0][0] - .4; px, py = x0, y0
    for (t, idx) in hov[1:]:
        nx, ny = ptr_pos(ys, idx); a = t - t0 - .32
        xs.append((a, px)); yy_.append((a, py))
        for j in range(1, 7):
            q = eio(j / 6); xs.append((a + .32 * j / 6, px + (nx - px) * q)); yy_.append((a + .32 * j / 6, py + (ny - py) * q))
        px, py = nx, ny
    return kf(*xs), kf(*yy_)
def choices(pf, rf):
    flashf = save(Image.new('RGBA', (W, H), (255, 255, 255, 255)), 'flash')
    for ci, (vid, s0, D, fr) in enumerate(CH):
        bgi = BLUR[ci]; last = ci == 2
        bf = save(bgi.convert('RGBA'), f'ch{ci + 1}_blur')
        add('X-cblur', f'选项{ci + 1} 失焦', s0, (END0 - s0) if last else D + OUTF, bf,
            k={'opacity': kf((0, 0), (.25, 1)) if last else kf((0, 0), (.25, 1), (D, 1), (D + OUTF, 0))})
        add('X-flash', f'选项{ci + 1} 闪光', s0, .3, flashf, k={'opacity': kf((0, .55), (.3, 0))})
        sfx('u_flash', s0, .6)
        ex = lambda st: [(D - .28 - st, 1), (D - .02 - st, 0)] if not last else []
        goal_layers(s0, D, ex(.12))
        L = question(ci)
        add('X-cq', f'选项{ci + 1} 提问', s0 + .2, D - .2, save(L, f'ch{ci + 1}_q'), ay=660 / H,
            k={'opacity': kf((0, 0), (.25, 1), *ex(.2)), 'y': kf((0, 34), (.35, 0)), 'scale': kf((0, .96), (.35, 1))})
        sfx('u_bubble', s0 + .22, .45)
        opts = OPTS[ci]; ys = OY[len(opts)]; pick = 0 if not last else None
        for oi, (txt, y) in enumerate(zip(opts, ys)):
            t0 = s0 + .45 + oi * .14; fn = save(opt_img(bgi, txt, y, False), f'ch{ci + 1}_o{oi + 1}')
            k = {'y': kf((0, 40), (.32, 0)), 'opacity': kf((0, 0), (.2, 1), *ex(t0 - s0))}
            if pick is not None and oi != pick:
                r0 = s0 + CLICK + .1 - t0; k['opacity'] = kf((0, 0), (.2, 1), (r0, 1), (r0 + .28, 0)); k['scale'] = kf((r0, 1), (r0 + .28, .94))
            if pick is not None and oi == pick:
                r0 = s0 + CLICK + .15 - t0; k['opacity'] = kf((0, 0), (.2, 1), (r0 + .05, 1), (r0 + .1, 0))
            add(f'X-co{oi + 1}', f'选项{ci + 1} {txt}', t0, (s0 + CLICK + .25 - t0) if (pick is not None and oi == pick) else s0 + D - t0, fn, ay=y / H, k=k)
            sfx('u_bubble', t0 + .04, .25)
        xs, yy_ = ptr_path(ys, HOVER[ci])
        P0 = s0 + HOVER[ci][0][0] - .4
        if pick is not None:
            y = ys[pick]; sf = save(opt_img(bgi, opts[pick], y, True), f'ch{ci + 1}_sel'); SS = s0 + CLICK + .15
            add('X-cs', f'选项{ci + 1} 选中', SS, s0 + D - SS, sf, ay=y / H,
                k={'scale': kf((0, 1), (.14, 1.06), (.32, 1.03)), 'opacity': kf((0, .2), (.1, 1), (.25, .55), (.4, 1), (.55, .6), (.7, 1), (s0 + D - SS - .28, 1), (s0 + D - SS - .02, 0))})
            cr = s0 + CLICK - P0; pd = cr + .5
            add('X-ptr', f'选项{ci + 1} 指针（犹豫）', P0, pd, pf, k={'x': xs, 'y': yy_,
                'opacity': kf((0, 0), (.15, 1), (pd - .3, 1), (pd, 0)), 'scale': kf((cr - .08, 1), (cr, .8), (cr + .12, 1))})
            px, py = ptr_pos(ys, pick)
            add('X-prip', f'选项{ci + 1} 点击波纹', s0 + CLICK + .02, .45, rf, k={'x': kf((0, px)), 'y': kf((0, py)), 'scale': kf((0, .7), (.45, 2.2)), 'opacity': kf((0, .9), (.45, 0))})
            sfx('u_click', s0 + CLICK, .8); sfx('u_ok', s0 + CLICK + .15, .7)
            sfx('s_whoosh', s0 + D - .15, .45)
        else:
            add('X-ptr', f'选项{ci + 1} 指针犹豫', P0, s0 + D - P0, pf, k={'x': xs, 'y': yy_, 'opacity': kf((0, 0), (.15, 1))})
            add('X-flash', '选项3→AI聊天 闪光', s0 + D - .22, .6, flashf, k={'opacity': kf((0, 0), (.2, 1), (.6, 0))})
            sfx('u_flash', s0 + D - .2, .7)

# ---------------- AI 剧情对话：手机（MiraiMind 对话试玩广告 UI，编辑器 lgx 同款规格） ----------------
PR = (90, 560, 900, 1330); BZ = 16
SX0, SY0 = PR[0] + BZ, PR[1] + BZ; SW_, SH_ = PR[2] - 2 * BZ, PR[3] - 2 * BZ
FS_, LH_, PX_, PY_, GAP_, SIDE_ = 38, 54, 30, 22, 22, 26
def mask4(w, h, rads):
    S = 4; m = Image.new('L', (w * S, h * S), 255); d = ImageDraw.Draw(m)
    for r, sx_, sy_ in [(rads[0], 0, 0), (rads[1], 1, 0), (rads[2], 1, 1), (rads[3], 0, 1)]:
        R = r * S; x0 = 0 if sx_ == 0 else w * S - R; y0 = 0 if sy_ == 0 else h * S - R
        d.rectangle([x0, y0, x0 + R - 1, y0 + R - 1], fill=0)
        cx = R if sx_ == 0 else w * S - R; cy = R if sy_ == 0 else h * S - R
        d.ellipse([cx - R, cy - R, cx + R - 1, cy + R - 1], fill=255)
    return m.resize((w, h), Image.LANCZOS)
def lgx(L, scene, x0, y0, w, h, rads, k=2.4, tr=.25, tint_=None, fill=(255, 255, 255, .04), shadow=.2, photo=None):
    """液态玻璃（lgx.css 近似）：背景模糊 + 着色 + 四边内高光 + 内暗边 + 45° 角光（左下/右上）+ 投影"""
    x0, y0 = int(round(x0)), int(round(y0)); m = mask4(w, h, rads); ma = np.asarray(m).astype(np.float32) / 255
    if shadow:
        pad = int(30 * k / 2.4) + 20; sm = Image.new('L', (w + pad * 2, h + pad * 2), 0); sm.paste(m, (pad, pad))
        sm = sm.filter(ImageFilter.GaussianBlur(8 * k / 2)); s_ = Image.new('RGBA', sm.size, (0, 0, 0, 0)); s_.putalpha(sm.point(lambda v: int(v * shadow)))
        _paste(L, s_, x0 - pad, y0 - pad + int(4 * k))
    if photo is not None: arr = np.asarray(photo.resize((w, h), Image.LANCZOS).convert('RGB')).astype(np.float32)
    else:
        reg = scene.crop((x0, y0, x0 + w, y0 + h)).convert('RGB').filter(ImageFilter.GaussianBlur(2 * k)); arr = np.asarray(reg).astype(np.float32) * .9
        if tint_ is not None:
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); g = np.clip((xx / w + yy / h) / 2, 0, 1)[..., None]
            c0, c1 = np.array(tint_[0][:3], np.float32), np.array(tint_[1][:3], np.float32); a0, a1 = tint_[0][3], tint_[1][3]
            col = c0 * (1 - g) + c1 * g; al = a0 * (1 - g) + a1 * g; arr = arr * (1 - al) + col * al
        arr = arr * (1 - fill[3]) + np.array(fill[:3], np.float32) * fill[3]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g45 = (xx / w + (1 - yy / h)) / 2; corner = np.clip(np.maximum(1 - g45 / tr, (g45 - (1 - tr)) / tr), 0, 1)
    def band(o, i, blur):
        a = np.asarray(m.filter(ImageFilter.MinFilter(o)) if o > 1 else m).astype(np.float32); b = np.asarray(m.filter(ImageFilter.MinFilter(i))).astype(np.float32)
        return np.asarray(Image.fromarray(np.clip(a - b, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255
    odd = lambda v: int(v) // 2 * 2 + 1
    dark = band(1, odd(4 * k), k * .9) * .55
    rim = band(1, odd(2.2 * k), .5 * k * .6)
    inner = band(odd(3 * k), odd(7 * k), 1.2 * k) * (.35 + .7 * corner)
    haze = corner ** 1.3 * .72 * np.asarray(m.filter(ImageFilter.GaussianBlur(3 * k))).astype(np.float32) / 255
    arr = arr * (1 - dark[..., None]); white = np.clip(rim * .95 + inner + haze, 0, 1)[..., None]
    arr = arr + (255 - arr) * white
    pan = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA'); pan.putalpha(m)
    pd_ = int(4 * k); mb = Image.new('L', (w + pd_ * 2, h + pd_ * 2), 0); mb.paste(m, (pd_, pd_))
    og = np.clip(np.asarray(mb.filter(ImageFilter.MaxFilter(odd(1.4 * k)))).astype(np.float32) - np.asarray(mb).astype(np.float32), 0, 255)
    og = np.asarray(Image.fromarray(og.astype(np.uint8)).filter(ImageFilter.GaussianBlur(.9 * k))).astype(np.float32) * .55
    ogi = Image.new('RGBA', mb.size, (255, 255, 255, 0)); ogi.putalpha(Image.fromarray(og.astype(np.uint8))); _paste(L, ogi, x0 - pd_, y0 - pd_)
    _paste(L, pan, x0, y0)
def nbox(L, scene, x0, y0, w, h, rads, a=.6, tintc=(18, 14, 11), blur=16, border=.7, photo=None, shadow=.4, sheen=.07):
    """全片统一风格（noir champagne）：暖黑半透明 + 顶部微光 + 香槟金细描边 + 柔投影"""
    x0, y0 = int(round(x0)), int(round(y0)); m = mask4(w, h, rads)
    if shadow:
        pad = 40; sm = Image.new('L', (w + pad * 2, h + pad * 2), 0); sm.paste(m, (pad, pad)); sm = sm.filter(ImageFilter.GaussianBlur(16))
        s_ = Image.new('RGBA', sm.size, (0, 0, 0, 0)); s_.putalpha(sm.point(lambda v: int(v * shadow))); _paste(L, s_, x0 - pad, y0 - pad + 10)
    if photo is not None: arr = np.asarray(photo.resize((w, h), Image.LANCZOS).convert('RGB')).astype(np.float32)
    else:
        reg = scene.crop((x0, y0, x0 + w, y0 + h)).convert('RGB').filter(ImageFilter.GaussianBlur(blur))
        arr = np.asarray(reg).astype(np.float32) * (1 - a) + np.array(tintc, np.float32) * a
        yy = np.arange(h, dtype=np.float32)[:, None, None]; arr = arr + (255 - arr) * np.clip(1 - yy / (h * .5), 0, 1) ** 2 * sheen
    pan = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA'); pan.putalpha(m); _paste(L, pan, x0, y0)
    ring = np.clip(np.asarray(m).astype(np.float32) - np.asarray(m.filter(ImageFilter.MinFilter(3))).astype(np.float32), 0, 255)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); lit = .55 + .45 * np.clip(1 - (xx / w * .4 + yy / h * .6), 0, 1)
    col = np.asarray(grad_img(w, h, GOLD, horiz=True)).astype(np.uint8)
    rg = Image.fromarray(col).convert('RGBA'); rg.putalpha(Image.fromarray((ring * lit * border).astype(np.uint8))); _paste(L, rg, x0, y0)
def bub_size(s):
    f = font(NOTO, FS_); return int(f.getlength(s)) + PX_ * 2, LH_ + PY_ * 2
def bubble(L, scene, x, y, s):
    w, h = bub_size(s)
    nbox(L, scene, x, y, w, h, (40, 40, 40, 10), a=.5, tintc=(30, 23, 18), blur=10, border=.55, shadow=.3)
    f = font(NOTO, FS_); m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text((x + PX_, y + PY_ + LH_ / 2 + 1), s, font=f, fill=255, anchor='lm')
    bb = m.getbbox(); c = m.crop((bb[0] - 12, bb[1] - 12, bb[2] + 12, bb[3] + 12))
    for r, a, dy in [(1.5, .9, 1), (3, .8, 2)]:
        sh = Image.new('RGBA', c.size, (0, 0, 0, 0)); sh.putalpha(c.filter(ImageFilter.GaussianBlur(r)).point(lambda v: int(v * a))); _paste(L, sh, bb[0] - 12, bb[1] - 12 + dy)
    col = Image.new('RGBA', c.size, WH + (0,)); col.putalpha(c); _paste(L, col, bb[0] - 12, bb[1] - 12)
    return w, h
def comp(scene, L):
    s = scene.copy(); s.alpha_composite(L); return s
def phone_scene(pf):
    scene = BLUR[2].convert('RGBA')
    x0, y0, w, h = PR
    # 机身
    P = canvas()
    sm = Image.new('L', (W, H), 0); ImageDraw.Draw(sm).rounded_rectangle([x0, y0 + 40, x0 + w, y0 + h + 40], radius=76, fill=140); sm = sm.filter(ImageFilter.GaussianBlur(45))
    s_ = Image.new('RGBA', (W, H), (0, 0, 0, 0)); s_.putalpha(sm); P.alpha_composite(s_)
    nbox(P, scene, x0, y0, w, h, (76, 76, 76, 76), a=.45, tintc=(22, 17, 13), blur=26, border=.95, shadow=0, sheen=.1)
    # 屏幕
    sw, sh = SW_, SH_; scr = np.zeros((sh, sw, 4), np.float32)
    t = np.linspace(0, 1, sh)[:, None]; al = np.interp(t, [0, .3, .7, 1], [.60, .46, .54, .80])
    scr[..., 0], scr[..., 1], scr[..., 2] = 10, 8, 7; scr[..., 3] = al * 255
    S_ = Image.fromarray(scr.astype(np.uint8), 'RGBA'); sm_ = mask4(sw, sh, (62, 62, 62, 62)); S_.putalpha(Image.fromarray((np.asarray(S_.split()[3]).astype(np.float32) * np.asarray(sm_) / 255).astype(np.uint8)))
    _paste(P, S_, SX0, SY0)
    d = ImageDraw.Draw(P)
    d.rounded_rectangle([540 - 84, SY0 + 30, 540 + 84, SY0 + 74], radius=22, fill=(5, 5, 7, 255), outline=(255, 255, 255, 26), width=2)
    # 头部：头像 + 名字 + 在线绿点（居中）
    cx_, cy_, fw_, fh_ = face('B', ENDF); src = frame('B', ENDF); r_ = fw_ * W * .95
    av = src.crop((int(cx_ * W - r_), int(cy_ * H - r_ * 1.05), int(cx_ * W + r_), int(cy_ * H + r_ * .95))).resize((96, 96), Image.LANCZOS).convert('RGBA')
    av.putalpha(mask4(96, 96, (26, 26, 26, 26)))
    fn_ = font(SHIP, 46); nw = fn_.getlength(PH_NAME); bw = 96 + 22 + nw; hx = 540 - bw / 2; hy = SY0 + 92 + 4
    g = glow_of(av, (0, 0, 0), 9, .45, 30); _paste(P, g, int(hx) - 30, hy - 30 + 6); P.alpha_composite(av, (int(hx), hy))
    text(P, (hx + 118, hy + 40), PH_NAME, fn_, WH, anchor='lm', shadow=.8)
    dg = disc(9, (236, 200, 150), .9); blit(P, dg, hx + 126, hy + 80, 1, .8); d.ellipse([hx + 120, hy + 74, hx + 132, hy + 86], fill=(240, 214, 170, 255))
    text(P, (hx + 142, hy + 81), 'online', font(NOTOB, 22), SUB, anchor='lm', shadow=.5)
    ring_ = Image.new('RGBA', (100, 100), (0, 0, 0, 0)); ImageDraw.Draw(ring_).rounded_rectangle([0, 0, 99, 99], radius=28, outline=(236, 220, 196, 200), width=2); P.alpha_composite(ring_, (int(hx) - 2, hy - 2))
    hair(P, SX0 + 40, SX0 + sw - 40, SY0 + 204, .8)
    # 历史消息（来自第三幕台词）
    y = SY0 + 214 + 20; bx = SX0 + SIDE_
    for s in PH_HIST:
        _, bh = bubble(P, comp(scene, P), bx, y, s); y += bh + GAP_
    sc1 = comp(scene, P)
    # 新消息：图片 → 文字
    IMGW, IMGH = 405, 540
    ph = frame('B', PHF); fx, fy, ffw, ffh = face('B', PHF)
    cw_ = ffw * W * 2.9; chh = cw_ * IMGH / IMGW; cxp, cyp = fx * W, fy * H + ffh * H * .7
    phc = ph.crop((int(cxp - cw_ / 2), int(cyp - chh * .42), int(cxp + cw_ / 2), int(cyp + chh * .58)))
    yi = y; Li = canvas(); nbox(Li, sc1, bx, yi, IMGW, IMGH, (40, 40, 40, 10), photo=phc, border=.8, shadow=.4)
    y2 = yi + IMGH + GAP_
    Lt = canvas(); bubble(Lt, comp(sc1, Li), bx, y2, PH_NEW)
    def dots_frames(yd):
        out = []
        for j in range(8):
            Ld = canvas(); nbox(Ld, sc1, bx, yd, 150, 84, (40, 40, 40, 10), a=.5, tintc=(30, 23, 18), blur=10, border=.55, shadow=.3)
            dd = ImageDraw.Draw(Ld); fr_i = j * 2
            for i in range(3):
                s = max(0, math.sin(fr_i * .45 - i * 1.05)); cx = bx + 75 + (i - 1) * 29; cy = yd + 42 - 7 * s
                dd.ellipse([cx - 8.5, cy - 8.5, cx + 8.5, cy + 8.5], fill=(240, 220, 190, int(255 * .9 * (.45 + .55 * s))))
            out.append(save(Ld, f'ph_dots{int(yd)}_{j}'))
        return out
    # 标题（手机上方）
    C = canvas(); lr = logo_row(76, 32, False, 330); C.alpha_composite(lr)
    fcap = font(SHIP, 56); text(C, (540, 462), PH_CAP, fcap, anchor='mm', shadow=.85, grad=GOLD)
    cw2 = fcap.getlength(PH_CAP) / 2
    hair(C, 540 - cw2 - 10, 540 + cw2 + 10, 512, .8)
    # ---- 时间轴 ----
    T0 = PH0 + .12; EN = 16 / FPS
    ys_, rs_, ss_, os_ = [], [], [], []
    for j in range(17):
        tt_ = j / FPS; e = eob(tt_ / EN)
        ys_.append((tt_, (1 - min(e, 1.2)) * 900)); rs_.append((tt_, (1 - clamp(e)) * -6)); ss_.append((tt_, .9 + .1 * min(e, 1.1))); os_.append((tt_, clamp(tt_ * FPS / 6)))
    ay = (PR[1] + PR[3]) / H
    add('X-phone', 'AI聊天 手机', T0, END0 - T0, save(P, 'ph_body'), ay=ay, k={'y': kf(*ys_), 'rotation': kf(*rs_), 'scale': kf(*ss_), 'opacity': kf(*os_)})
    add('X-pcap', 'AI聊天 标题', PH0 + .05, END0 - PH0 - .05, save(C, 'ph_cap'), ay=400 / H, k={'opacity': kf((0, 0), (.3, 1)), 'y': kf((0, 24), (.4, 0)), 'scale': kf((0, 1.06), (.4, 1))})
    sfx('s_whoosh', PH0 + .1, .5); sfx('u_end', PH0 + .05, .3)
    pop = lambda: {'scale': kf((0, .8), (3 / FPS, .97), (6 / FPS, 1.04), (9 / FPS, 1)), 'opacity': kf((0, 0), (5 / FPS, 1))}
    for (td, tm_, yb, hb, fn, nm) in [(PH0 + .85, PH0 + 1.45, yi, IMGH, save(Li, 'ph_img'), '图片'), (PH0 + 2.15, PH0 + 2.75, y2, LH_ + PY_ * 2, save(Lt, 'ph_msg'), PH_NEW)]:
        fr = dots_frames(yb)
        n = int(round((tm_ - td) * 15))
        for j in range(n): add('X-pdots', 'AI聊天 输入中', td + j / 15, 1 / 15, fr[j % 8], ax=bx / W, ay=(yb + 84) / H, k=(pop() if j == 0 else None))
        add('X-pmsg1' if nm == '图片' else 'X-pmsg2', 'AI聊天 ' + nm, tm_, END0 - tm_, fn, ax=bx / W, ay=(yb + hb) / H, k=pop())
        sfx('u_msg', tm_, .7)
    add('X-flash', 'AI聊天→片尾 闪光', END0 - .18, .5, save(Image.new('RGBA', (W, H), (255, 255, 255, 255)), 'flash'), k={'opacity': kf((0, 0), (.18, .9), (.5, 0))})

TRACKS = [
    ('X-sub0', '字幕0（跟脸）', 'title'), ('X-sub1', '字幕1（跟脸）', 'title'), ('X-sub2', '字幕2（跟脸）', 'title'), ('X-sub3', '字幕3（跟脸）', 'title'), ('X-sub4', '字幕4（跟脸）', 'title'), ('X-sub5', '字幕5（跟脸）', 'title'), ('X-count', '倒数', 'title'),
    ('X-cblur', '选项 失焦', 'choice'), ('X-cgoalg', '目标 闪烁光', 'choice'), ('X-cgoal', '目标', 'choice'), ('X-cq', '选项 提问', 'choice'),
    ('X-co1', '选项 ①', 'choice'), ('X-co2', '选项 ②', 'choice'), ('X-co3', '选项 ③', 'choice'), ('X-cs', '选项 选中', 'choice'),
] + [(f'X-dm{i}', f'弹幕{i}', 'choice') for i in range(1, 9)] + [
    ('X-ptr', '选项 指针', 'choice'), ('X-prip', '选项 点击波纹', 'choice'),
    ('X-meter', '溺愛度', 'meter'),
    ('X-pcap', 'AI聊天 标题', 'end'), ('X-phone', 'AI聊天 手机', 'end'), ('X-pdots', 'AI聊天 输入中', 'end'), ('X-pmsg1', 'AI聊天 图片', 'end'), ('X-pmsg2', 'AI聊天 消息', 'end'),
    ('X-elogo', '片尾 Logo', 'end'), ('X-ecard', '片尾 标题', 'end'), ('X-ehead', '片尾 文案', 'end'),
    ('X-ebtn', '片尾 下载按钮', 'end'), ('X-esheen', '片尾 按钮扫光', 'end'), ('X-ebadge', '片尾 商店标', 'end'),
    ('X-eptr', '片尾 指针', 'end'), ('X-erip1', '片尾 波纹1', 'end'), ('X-erip2', '片尾 波纹2', 'end'),
    ('X-intro', '开头（逐帧特效）', 'title'), ('X-flash', '闪光', 'end'),
]

if __name__ == '__main__':
    import sys
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith('.png') or f.endswith('.jpg'): os.remove(os.path.join(OUT, f))
    for ci, (vid, s0, D, fr) in enumerate(CH): BLUR[ci] = soft_bg(frame(vid, fr), 20, .66)
    pf, rf = pointer_imgs()
    GOAL_FILES = goal_row()
    only = [a for a in sys.argv[1:] if a != 'fast']
    if not only or 'intro' in only: intro()
    if not only or 'choices' in only: choices(pf, rf); danmaku()
    if not only or 'phone' in only: phone_scene(pf)
    if not only or 'end' in only: endcard(pf, rf)
    if not only and 'fast' not in sys.argv: subs(); meter()
    meta = {'tracks': TRACKS, 'layers': LAY, 'seg': SEG, 'frz': FRZ, 'mute': MUTE, 'end0': END0, 'ed': ED, 'sfx': SFX, 'bgmVol': .5, 'bgm': 'bgm_v4.wav'}
    json.dump(meta, open(os.path.join(OUT, 'layers.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('layers', len(LAY), 'files', len({l['file'] for l in LAY}), 'sfx', len(SFX), 'end', END1)
