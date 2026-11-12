"""261111-JP-病娇女教师 · 多版本包装：VER=版本N python gen.py → 画图层（1080×1920 透明 PNG）+ 写 timeline_版本N.json。
版本差异只在 工程素材/抽帧_版本N/版本配置.json（字幕逐词时间、两张定格帧、片尾主卡帧、角色名）和 包装素材_产品UI/swipe_版本N.json；
设计、文案、口播、BGM、音效各版本沿用（rules/工程交付.md「多版本」）。
方案：工程素材/方案_版本1.json（三路方案 + 评审 + 合成）。用法：python gen.py → python render.py ../timeline_版本1.json [--still …|--draft]
时间都吸附到 1/30 s（rules/工程交付.md）。"""
import json, math, os, shutil, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops
import numpy as np
import mmlib as m
import endcard3

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
VER = os.environ.get("VER", "版本1")
OUT = f"{P}/包装素材_{VER}"
LAY = f"{OUT}/layers"
FR = f"{P}/工程素材/抽帧_{VER}"
AUD = f"{P}/包装素材_版本1/audio"                 # 声音各版本共用
RES = m.RES
NUM = VER.replace("版本", "")
SRC = f"{P}/素材/视频_{NUM}_1080.mp4"
CFG = json.load(open(f"{FR}/版本配置.json", encoding="utf-8"))
UI_MP4 = f"{P}/包装素材_产品UI/产品UI-划卡_{VER}.mp4"
W, H = 1080, 1920

AMBER, AMBER_HI = m.hexc("F2A65A"), m.hexc("FFD39A")
IVORY, INK = m.hexc("FFF4E6"), m.hexc("1B1215")
CRIMSON, CRIMSON_HI, CRIMSON_DK = m.hexc("E0244A"), m.hexc("FF2E55"), m.hexc("C8143C")
HALO = (27, 18, 21, 150)


def snap(t): return round(t * 30) / 30


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())


# ---------------------------------------------------------------- 时间结构
A_END = snap(12.333)                 # 第一段原片 src 0–12.333
F1 = (A_END, snap(14.933))           # 选项定格1
B_IN = A_END                         # 第二段原片从 src 12.333 起
B0, B1 = F1[1], snap(30.5)           # 成片 14.933–30.5 = src 12.333–27.9
OFF = B0 - B_IN                      # 第二段：成片 = 原片 + 2.6
F2 = (B1, snap(33.1))                # 选项定格2
BR0, UI0 = F2[1], snap(33.4)         # 缩进手机 33.1–33.7，app-ui 33.4 起
BR1 = snap(33.7)
UI_D = dur(UI_MP4)
UI_EV = json.loads(open(f"{P}/包装素材_产品UI/render_{VER}.log", encoding="utf-8").read().strip().splitlines()[-1])["events"]
E0 = snap(UI0 + UI_D - 0.067)        # 片尾闪白峰值，JP 尾板从这里开始
END = snap(E0 + endcard3.DUR)         # 三卡片尾板（默认样式）
VO_T = {"vo1": snap(33.6), "vo2": snap(37.0), "vo3": snap(E0 + 1.0)}     # vo3 =「あなただけを必要とする先生」移到片尾
US = "Z:/创新事业部/AIGC项目视频组/设计师物料总库/音频/音效收集"      # 用户找好的音效（优先用）
VO_D = {k: dur(f"{AUD}/{k}.wav") for k in VO_T}
VOW = json.load(open(f"{AUD}/vo_words.json", encoding="utf-8"))

# ---------------------------------------------------------------- 版本时间映射
# 下面所有时间都按版本1 写（规范时间）。别的版本同一个 3D 运镜，但台词快慢、动作早晚不一样，build() 最后用 TW() 把整条 timeline 映射到本版本：
#   第一段原片：规范 [0, 12.333] → 本版本 [0, A_END]，中间按 CFG["A1_MAP"] 锚点分段线性（[[版本1原片秒, 本版本原片秒], …]）
#   选项定格1：整体平移到 A_END 起
#   第二段原片：规范原片 [12.333, 27.9] → 本版本原片 [B_IN, B_END]，中间按 CFG["A2_MAP"] 锚点分段线性
#   选项定格2 及以后：整体平移 S（= 本版本第二段结束 − 30.5）
# 逐词字幕直接用本版本时间（版本配置.json 的 subs），不映射。版本1 的配置没有这些键 → 恒等映射。
V_A = snap(CFG.get("A_END", A_END)); V_B = snap(CFG.get("B_IN", V_A)); V_E = snap(CFG.get("B_END", 27.9))
V_B0 = snap(V_A + (F1[1] - F1[0])); V_B1 = snap(V_B0 + V_E - V_B); V_S = V_B1 - B1
MAP1 = [(0.0, 0.0)] + [tuple(x) for x in CFG.get("A1_MAP", [])] + [(A_END, V_A)]
MAP2 = [(B_IN, V_B)] + [tuple(x) for x in CFG.get("A2_MAP", [])] + [(snap(27.9), V_E)]


def _pl(x, pts):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1 + 1e-9: return y1 if x1 - x0 < 1e-9 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1] + x - pts[-1][0]


def TW(t):
    """规范成片时间 → 本版本成片时间。"""
    if t <= A_END + 1e-6: return _pl(t, MAP1)
    if t <= F1[1] + 1e-6: return t - A_END + V_A
    if t <= B1 + 1e-6: return _pl(t - OFF, MAP2) - V_B + V_B0
    return t + V_S


def vsrc(t):
    """规范成片时间 t 时，本版本画面对应的原片时间（取帧用）。"""
    if t <= A_END + 1e-6: return TW(t)
    return _pl(t - OFF, MAP2)


STRETCH = ("bgm_", "/素材/视频_", "产品UI-划卡_")      # 这些音频随映射拉长（同一文件连续段）；其余音效只平移起点


BOUNDS = [A_END, F1[1], B1, F2[1]]                      # 结构切点（规范时间）


def _bgm_phase(audio, orig):
    """同一 BGM 文件、原本同相位的相邻段（交叉淡化）映射后要保持同相位，否则交叉处同一首曲子错开叠在一起。
    靠近结构切点的段锚在自己起点（in 不变，音乐重拍对齐切点），前一段的重叠区换成本段相位的尾巴（相位跳变藏在切点的闪白/定格音效下）；
    其余段沿用前一段的相位（连续不跳）。开场段锚在闪白 0.233。版本1 恒等映射时什么都不变。"""
    extra, by = [], {}
    for a in audio:
        if id(a) in orig: by.setdefault(a["src"], []).append(a)
    for items in by.values():
        items.sort(key=lambda a: orig[id(a)][0])
        prev = None
        for a in items:
            st, en, i0 = orig[id(a)]
            if st < 0.233 < en:
                a["in"] = round(i0 + 0.233 - st - (TW(0.233) - TW(st)), 4)
            if prev is not None:
                pst, pen, pi0 = orig[id(prev)]
                if abs((st - i0) - (pst - pi0)) < 0.01 and pen > st - 1e-6:
                    if any(st - 0.8 <= b <= pen + 0.05 for b in BOUNDS):
                        if abs((prev["start"] - prev["in"]) - (a["start"] - a["in"])) > 0.01 and prev["start"] + prev["duration"] > a["start"] + 0.04:
                            extra.append({**prev, "start": a["start"], "duration": round(prev["start"] + prev["duration"] - a["start"], 4),
                                          "in": a["in"], "fadeIn": 0.04, "fadeOut": prev["fadeOut"]})
                            prev["duration"] = round(a["start"] + 0.04 - prev["start"], 4); prev["fadeOut"] = 0.04
                    else:
                        a["in"] = round(a["start"] - (prev["start"] - prev["in"]), 4)
            prev = a
    audio.extend(extra)


def warp(clips, audio, end):
    end2 = snap(TW(end))
    orig = {id(a): (a["start"], a["start"] + a["duration"], a.get("in", 0)) for a in audio if "bgm_" in a["src"] and not a.get("_nowarp")}
    for c in clips:
        if c.pop("_nowarp", False): continue
        st, en = c["start"], c["start"] + c["duration"]
        s2, e2 = snap(TW(st)), snap(TW(en))
        if c["duration"] >= 1 / 30 - 1e-4: e2 = max(e2, s2 + 1 / 30)
        for ks in c.get("keyframes", {}).values():
            for k in ks: k["t"] = round(TW(st + k["t"]) - s2, 4)
        c["start"], c["duration"] = s2, round((e2 - s2) * 30) / 30
        if c["type"] == "video" and c["src"] == SRC and c.get("in", 0) > 0: c["in"] = V_B
    for a in audio:
        if a.pop("_nowarp", False): continue
        st, en = a["start"], a["start"] + a["duration"]
        a["start"] = round(TW(st), 4)
        if any(k in a["src"] for k in STRETCH): a["duration"] = round(TW(en) - TW(st), 4)
        a["duration"] = round(min(a["duration"], end2 - a["start"]), 4)
        if a["src"] == SRC and a["in"] > 0: a["in"] = V_B
    _bgm_phase(audio, orig)
    return end2


CLIPS, AUDIO = [], []
_n = [0]


def save_layer(img, name):
    _n[0] += 1
    return m.save(img, f"{LAY}/{_n[0]:03d}_{name}.png")


def kf(**props):
    """kf(opacity=[(t,v[,ease])...]) → render.py keyframes（t 为 clip 内相对秒）。"""
    return {k: [dict(t=round(a[0], 4), v=a[1], **({"ease": a[2]} if len(a) > 2 else {})) for a in v] for k, v in props.items()}


def add_img(img, name, start, end, keyframes=None, transform=None):
    start, end = snap(start), snap(end)
    if end - start < 1 / 30 - 1e-4: return
    path = img if isinstance(img, str) else save_layer(img, name)
    c = {"type": "image", "src": path, "start": start, "duration": round((end - start) * 30) / 30, "fit": "fill"}
    if keyframes: c["keyframes"] = keyframes
    if transform: c["transform"] = transform
    CLIPS.append(c)
    return c


def add_audio(src, start, duration=None, vol=1.0, fin=0, fout=0, src_in=0):
    d = dur(src) - src_in if duration is None else duration
    d = min(d, END - start)
    if d <= 0.02: return
    AUDIO.append({"src": src, "start": round(start, 4), "duration": round(d, 4), "in": round(src_in, 4), "volume": vol, "fadeIn": fin, "fadeOut": fout})


def us(name, t, vol, fout=0):
    """用户音效收集里的音效。"""
    add_audio(f"{US}/{name}", snap(t), vol=vol, fout=fout)


def tick(t, vol):
    add_audio(f"{AUD}/tick_soft_hp.wav", snap(t), vol=vol)


def sfx(name, t, vol):
    p = name if os.path.isabs(name) or ":" in name else f"{RES}/sfx/{name}"
    add_audio(p, snap(t), vol=vol)


def fade_kf(d, fin=0.1, fout=0.1, y_in=0):
    k = {"opacity": [(0, 0), (fin, 1), (max(fin, d - fout), 1), (d, 0)]}
    if y_in: k["y"] = [(0, y_in), (fin, 0)]
    return kf(**k)


def pop_kf(d, fin=0.2, fout=0.12, s0=0.6, over=1.15):
    return kf(opacity=[(0, 0), (fin * 0.4, 1), (max(fin, d - fout), 1), (d, 0)],
              scale=[(0, s0), (fin * 0.6, over), (fin, 1.0)])


def frame_path(n):
    return f"{FR}/{n:04d}.jpg"


def frame_img(n):
    return Image.open(frame_path(n)).convert("RGBA")


# ---------------------------------------------------------------- 通用画法
def text_layer(lines, size, font="noto_black", fill=IVORY, stroke=8, halo=True, anchor="mm", glow=None):
    """lines: [(x, y, text)]"""
    img = m.canvas()
    f = m.font(font, size)
    for x, y, t in lines:
        m.draw_text(img, (x, y), t, f, fill, stroke=stroke, stroke_fill=INK, anchor=anchor,
                    shadow=(0, 0, 22, HALO) if halo else None, glow=glow)
    return img


def channel_shift(img, dx):
    r, g, b, a = img.split()
    r = ImageChops.offset(r, dx, 0); b = ImageChops.offset(b, -dx, 0)
    return Image.merge("RGBA", (r, g, b, a))


def pointer_img():
    img = m.canvas()
    sh = m.canvas(); m.disc(sh, 540, 966, 60, (0, 0, 0, 110)); img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    m.disc(img, 540, 960, 54, (27, 18, 21, 90))
    m.ring(img, 540, 960, 57, 3, (27, 18, 21, 210))
    m.ring(img, 540, 960, 52, 5, (255, 255, 255, 235))
    return img


def ripple_img():
    img = m.canvas()
    m.ring(img, 540, 960, 55, 3, (27, 18, 21, 200))
    m.ring(img, 540, 960, 52, 6, (255, 255, 255, 230))
    return img


POINTER, RIPPLE = None, None


def pointer_path(points, start, end, clicks=()):
    """points: [(t, x, y)] 绝对时间；clicks: [t]。指针=半透明圆圈，点击出波纹（rules/B-剧情选择.md）。"""
    global POINTER, RIPPLE
    if POINTER is None:
        POINTER = save_layer(pointer_img(), "pointer"); RIPPLE = save_layer(ripple_img(), "ripple")
    d = end - start
    xs = [(t - start, x - 540) for t, x, y in points]; ys = [(t - start, y - 960) for t, x, y in points]
    sc = [(0, 1.0)]
    for c in clicks:
        c -= start; sc += [(c - 0.06, 1.0), (c, 0.82), (c + 0.12, 1.0)]
    add_img(POINTER, "pointer", start, end, kf(x=xs, y=ys, scale=sorted(sc), opacity=[(0, 0), (0.12, 1), (d - 0.1, 1), (d, 0)]))
    for c in clicks:
        x, y = interp(points, c)
        add_img(RIPPLE, "ripple", c, c + 0.45, kf(scale=[(0, 0.6), (0.45, 2.1, "linear")], opacity=[(0, 0.95), (0.45, 0, "linear")]),
                {"x": x - 540, "y": y - 960})


def interp(points, t):
    pts = sorted(points)
    if t <= pts[0][0]: return pts[0][1], pts[0][2]
    for a, b in zip(pts, pts[1:]):
        if a[0] <= t <= b[0]:
            u = (t - a[0]) / max(1e-6, b[0] - a[0]); u = u * u * (3 - 2 * u)
            return a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u
    return pts[-1][1], pts[-1][2]


# ---------------------------------------------------------------- 逐词字幕
def subtitle_card(lines, start, end, align="center", x_anchor=540, size=70, key_size=92, fade_out=0.1):
    """lines: [(y, [(text, t_abs, is_key), ...])]。非重点词累加出字；重点词单独一层弹入（放大 + 绯红 + 发光）。"""
    f, fk = m.font("noto_black", size), m.font("noto_black", key_size)
    toks = []                                       # (text, t, key, x_left, y)
    for y, ts in lines:
        widths = [(fk.getlength(t) + 16) if k else f.getlength(t) for t, _, k in ts]   # 重点词左右各留 8 px
        tw = sum(widths)
        x = x_anchor - tw / 2 if align == "center" else (x_anchor - tw if align == "right" else x_anchor)
        assert x >= 40 and x + tw <= W - 40, f"字幕出界 {ts}"
        for (t, tt, k), w in zip(ts, widths):
            toks.append((t, tt, k, x + (8 if k else 0), y, w - (16 if k else 0))); x += w
    order = sorted({tt for _, tt, k, *_ in toks if not k} | {start})
    order = [t for t in order if t < end]
    for i, t0 in enumerate(order):
        t1 = order[i + 1] if i + 1 < len(order) else end
        img = m.canvas(); d = ImageDraw.Draw(img)
        shown = [tk for tk in toks if not tk[2] and tk[1] <= t0 + 1e-6]
        if not shown: continue
        for t, tt, k, x, y, w in shown:
            m.draw_text(img, (x, y), t, f, IVORY, stroke=8, stroke_fill=INK, anchor="lm", shadow=(0, 0, 22, HALO))
        kk = {"opacity": [(t1 - t0 - fade_out, 1), (t1 - t0, 0)]} if i == len(order) - 1 else None
        add_img(img, "sub", t0, t1, kf(**kk) if kk else None)
    for t, tt, k, x, y, w in toks:
        if not k: continue
        img = m.canvas()
        m.draw_text(img, (x, y), t, fk, CRIMSON_HI, stroke=8, stroke_fill=INK, anchor="lm", shadow=(0, 0, 22, HALO), glow=(14, (255, 46, 85, 200)))
        cx, cy = x + w / 2, y
        d = end - tt
        add_img(img, "subkey", tt, end, kf(scale=[(0, 0.7), (0.1, 1.06), (0.2, 1.0)], opacity=[(0, 0), (0.05, 1), (d - fade_out, 1), (d, 0)]),
                {"anchorX": cx / W, "anchorY": cy / H})


def vo_card(key, cards, y=1648):
    """口播逐句字幕：墨色圆角底板 + 2px 琥珀描边（rules/通用.md：口播必须配逐句字幕且有底板）。cards: [(t0_rel, t1_rel, [(text, t_rel)], logo_after_idx)]"""
    t_vo = VO_T[key]
    f = m.font("noto_black", 60)
    for c0, c1, toks, logo_at in cards:
        pieces = []                                  # (kind, content, t_rel, width)
        for i, (t, tr) in enumerate(toks):
            if t == "[LOGO]":
                lw = Image.open(m.LOGO_WORD).convert("RGBA"); lw = lw.crop(lw.getchannel("A").getbbox()); lh = 46
                lw = lw.resize((int(lw.width * lh / lw.height), lh), Image.LANCZOS)
                pieces.append(("logo", lw, tr, lw.width + 16))
            else:
                pieces.append(("t", t, tr, f.getlength(t)))
        tw = sum(p[3] for p in pieces)
        pw = tw + 72
        box = (540 - pw / 2, y - 52, 540 + pw / 2, y + 53)
        plate = m.canvas()
        m.soft_shadow(plate, box, 28, blur=16, color=(0, 0, 0, 110), dy=6)
        m.rrect(plate, box, 28, fill=(27, 18, 21, 184), outline=AMBER, width=2)
        a0, a1 = t_vo + c0, t_vo + c1
        add_img(plate, "voplate", a0, a1, kf(opacity=[(0, 0), (0.1, 1), (a1 - a0 - 0.1, 1), (a1 - a0, 0)]))
        times = sorted({p[2] for p in pieces})
        for i, tr in enumerate(times):
            img = m.canvas(); x = 540 - tw / 2
            for kind, ct, ptr, w in pieces:
                if ptr <= tr + 1e-6:
                    if kind == "t":
                        m.draw_text(img, (x, y), ct, f, IVORY, stroke=0, anchor="lm")
                    else:
                        img.alpha_composite(ct, (int(x + 8), int(y - ct.height / 2)))
                x += w
            s0 = t_vo + tr; s1 = t_vo + times[i + 1] if i + 1 < len(times) else a1
            ops = []
            if i == 0: ops += [(0, 0), (0.1, 1)]
            if i + 1 == len(times): ops += [(s1 - max(s0, a0) - 0.1, 1), (s1 - max(s0, a0), 0)]
            add_img(img, "votext", max(s0, a0), s1, kf(opacity=ops) if ops else None)


# ---------------------------------------------------------------- 数值条
BAR_POS0 = {"P1": (730, 250), "P2": (730, 570), "P3": (730, 430)}
BAR_POS = {**BAR_POS0, **{k: tuple(v) for k, v in CFG.get("BAR_POS", {}).items()}}   # 版本配置可覆盖（某版本某位置压脸时）
DY1, DY2 = CFG.get("F1_UI_DY", 0), CFG.get("F2_UI_DY", 0)                               # 定格1/2 的选项 UI 整体下移（压嘴时）


def bar_img(v, pos, glow=False, glitch=0):
    cx, cy = BAR_POS[pos]
    x0, y0 = cx - 310, cy - 64
    img = m.canvas()
    m.draw_text(img, (x0, y0 + 80), "逃走成功率", m.font("noto_black", 50), IVORY, stroke=6, stroke_fill=INK, anchor="ls", shadow=(0, 0, 14, HALO))
    fp = m.font("noto_black", 56); fn = m.font("mincho", 110)
    pw = fp.getlength("%")
    crimson = v < 40
    numc = CRIMSON_HI if crimson else AMBER_HI
    m.draw_text(img, (x0 + 620, y0 + 88), "%", fp, IVORY, stroke=6, stroke_fill=INK, anchor="rs")
    m.draw_text(img, (x0 + 620 - pw - 6, y0 + 92), str(int(round(v))), fn, numc, stroke=7, stroke_fill=INK, anchor="rs",
                shadow=(0, 0, 14, HALO), glow=(16, numc[:3] + (220,)) if glow else None)
    tb = (x0, y0 + 102, x0 + 620, y0 + 124)
    m.rrect(img, tb, 11, fill=(27, 18, 21, 140), outline=(255, 244, 230, 120), width=2)
    fw = max(22, 620 * v / 100) if v > 0 else 0
    if fw:
        g = m.gradient_rect((int(fw), 22), CRIMSON_DK if crimson else AMBER, CRIMSON_HI if crimson else AMBER_HI)
        mask = Image.new("L", (g.width * 3, 66), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, g.width * 3 - 1, 65), 33, fill=255)
        g.putalpha(mask.resize(g.size, Image.LANCZOS)); img.alpha_composite(g, (x0, y0 + 102))
    if glitch: img = channel_shift(img, glitch)
    return img


BAR_CACHE = {}


def bar_path(v, pos, glow=False, glitch=0):
    k = (round(v, 2), pos, glow, glitch)
    if k not in BAR_CACHE:
        BAR_CACHE[k] = save_layer(bar_img(v, pos, glow, glitch), f"bar{int(v)}{pos}{'g' if glow else ''}{'x' if glitch else ''}")
    return BAR_CACHE[k]


def bar_static(v, pos, a, b, fin=0.0, fout=0.0, slide=False, extra_kf=None, tf=None):
    d = snap(b) - snap(a)
    k = {}
    if fin or fout:
        k["opacity"] = [(0, 0 if fin else 1), (fin, 1), (max(fin, d - fout), 1), (d, 0 if fout else 1)]
    if slide: k["y"] = [(0, -30), (fin, 0)]
    if extra_kf: k.update(extra_kf)
    add_img(bar_path(v, pos), "bar", a, b, kf(**k) if k else None, tf)
    if v < 40:                                          # 低值绯红慢脉动；1% 每 0.5 s 故障闪
        n = int(d / 0.5) + 1
        ops = [(0, 0)] + [(i * 0.5 + 0.25, 0.75 if i % 2 == 0 else 0.15) for i in range(n)]
        if fin or fout:
            ops = [(t, v2 * (1 if fin <= t <= d - fout else 0)) for t, v2 in ops]
        gk = {"opacity": ops}
        if extra_kf: gk.update(extra_kf)
        add_img(bar_path(v, pos, glow=True), "barglow", a, b, kf(**gk), tf)
        if v <= 1:
            t = a + 0.5
            while t < b - 0.1:
                add_img(bar_path(v, pos, glitch=7), "barglitch", t, t + 1 / 30, None, tf)
                t += 0.5


def bar_roll(v0, v1, pos, t, length, txt, txt_size, txt_col, txt_y):
    t = snap(t)
    txt_y += BAR_POS[pos][1] - BAR_POS0[pos][1]          # 条位置被版本配置覆盖时，±N 弹字跟着走
    n = max(2, int(round(length * 30)))
    for i in range(n):
        u = (i + 1) / n; u = 1 - (1 - u) ** 2
        add_img(bar_path(v0 + (v1 - v0) * u, pos, glow=True), "barroll", t + i / 30, t + (i + 1) / 30)
    # ±N 弹出（条上方）：按字面半宽 + 描边 8 + glow 18、最大回弹 1.15 算安全边界，任何一帧都不出画
    img = m.canvas()
    hw = m.font("mincho", txt_size).getlength(txt) / 2
    cx = min(BAR_POS[pos][0] + 165, 1060 - (hw + 26) * 1.15)
    assert cx - (hw + 26) * 1.15 >= 20 and txt_y - (txt_size / 2 + 26) * 1.15 >= 20, "±N 出画"
    m.draw_text(img, (cx, txt_y), txt, m.font("mincho", txt_size), txt_col, stroke=8, stroke_fill=INK, anchor="mm",
                shadow=(0, 0, 18, HALO), glow=(18, txt_col[:3] + (220,)))
    add_img(img, "delta", t, t + 1.1, kf(scale=[(0, 0.5), (0.14, 1.15), (0.28, 1.0)], opacity=[(0, 0), (0.06, 1), (0.85, 1), (1.1, 0)], y=[(0.6, 0), (1.1, -24)]),
            {"anchorX": cx / W, "anchorY": txt_y / H})
    return t + n / 30


# ---------------------------------------------------------------- 选项 UI
def pill(img, box, lines, size, selected=False):
    x0, y0, x1, y1 = box
    r = min(85, (y1 - y0) / 2)
    m.soft_shadow(img, box, r, blur=18, color=(0, 0, 0, 110), dy=8)
    if selected:
        g = m.gradient_rect((int(x1 - x0), int(y1 - y0)), CRIMSON_HI, CRIMSON_DK)
        mask = Image.new("L", (g.width * 3, g.height * 3), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, g.width * 3 - 1, g.height * 3 - 1), r * 3, fill=255)
        g.putalpha(mask.resize(g.size, Image.LANCZOS)); img.alpha_composite(g, (int(x0), int(y0)))
        m.rrect(img, box, r, outline=IVORY, width=3)
        col = IVORY
    else:
        m.rrect(img, box, r, fill=(255, 244, 230, 235), outline=CRIMSON, width=3)
        col = INK
    f = m.font("noto_black", size)
    n = len(lines); lh = size * (0.98 if n > 1 else 1.0)
    cy = (y0 + y1) / 2
    for i, t in enumerate(lines):
        m.draw_text(img, ((x0 + x1) / 2, cy + (i - (n - 1) / 2) * lh), t, f, col, stroke=0, anchor="mm")
    return img


def target_img(y):
    img = m.canvas()
    ft = m.font("noto_black", 46); fl = m.font("noto_black", 40)
    txt = "保健室から脱出せよ"
    tw = ft.getlength(txt); lw = fl.getlength("目標") + 36
    x1 = 1040; xt = x1 - tw
    lab = (xt - 14 - lw, y - 30, xt - 14, y + 30)
    m.rrect(img, lab, 30, fill=CRIMSON_HI)
    m.draw_text(img, ((lab[0] + lab[2]) / 2, y), "目標", fl, IVORY, anchor="mm")
    m.draw_text(img, (x1, y), txt, ft, IVORY, stroke=6, stroke_fill=INK, anchor="rm", shadow=(0, 0, 14, HALO))
    return img


def dim_img(y_from, alpha=0.6, ramp=110):
    img = m.canvas(); a = np.zeros((H, W), np.uint8)
    for y in range(y_from, H):
        u = min(1, (y - y_from) / ramp); a[y, :] = int(255 * alpha * u)
    im = Image.new("RGBA", (W, H), INK[:3] + (0,)); im.putalpha(Image.fromarray(a))
    return im


def countdown(y, t0, t1, t_red, start, end):
    base = m.canvas(); m.rrect(base, (60, y, 1020, y + 12), 6, fill=(27, 18, 21, 150))
    add_img(base, "cdtrack", start, end, fade_kf(end - start, 0.1, 0.12))
    fa, fr = m.canvas(), m.canvas()
    m.rrect(fa, (60, y, 1020, y + 12), 6, fill=AMBER); m.rrect(fr, (60, y, 1020, y + 12), 6, fill=CRIMSON_HI)
    sx = [(0, 1.0), (t0 - start, 1.0), (t1 - start, 0.0, "linear")]
    tf = {"anchorX": 60 / W, "anchorY": (y + 6) / H}
    add_img(fa, "cdfill", start, end, kf(scaleX=sx, opacity=[(0, 0), (0.1, 1), (t_red - start, 1), (t_red - start + 0.05, 0)]), tf)
    bl = [(t_red - start, 0), (t_red - start + 0.03, 1)]
    t = t_red - start + 0.12
    while t < t1 - start:
        bl += [(t, 0.45), (t + 0.06, 1)]; t += 0.12
    bl += [(end - start - 0.1, 1), (end - start, 0)]
    add_img(fr, "cdred", start, end, kf(scaleX=sx, opacity=bl), tf)


# ================================================================ 生成
def build():
    if os.path.isdir(LAY): shutil.rmtree(LAY)              # 规则：重出图层先清旧图
    os.makedirs(LAY, exist_ok=True)

    # ---------- 底层画面 ----------
    shake_a = {"scale": [(0, 1.0), (0.233, 1.04), (0.6, 1.0)],
               "x": [(0.233 + i / 30, v) for i, v in enumerate([0, 6, -5, 4, -3, 2, -1, 0])],
               "y": [(0.233 + i / 30, v) for i, v in enumerate([0, -4, 4, -3, 2, -1, 1, 0])]}
    CLIPS.append({"type": "video", "src": SRC, "start": 0, "duration": A_END, "in": 0, "fit": "cover", "keyframes": kf(**shake_a)})
    add_img(frame_path(CFG["F1_FRAME"]), "freeze1", F1[0], F1[1])
    lt = snap(20.1) - B0
    shake_b = {"x": [(lt + i / 30, v) for i, v in enumerate([0, 10, -9, 7, -6, 4, -3, 2, 0])],
               "y": [(lt + i / 30, v) for i, v in enumerate([0, -7, 6, -5, 4, -2, 2, -1, 0])]}
    CLIPS.append({"type": "video", "src": SRC, "start": B0, "duration": round(B1 - B0, 4), "in": B_IN, "fit": "cover", "keyframes": kf(**shake_b)})
    beats = [30.6, 31.233, 31.767, 32.2, 32.567, 32.867]
    hb = [(0, 1.0)]
    for b in beats:
        bt = snap(b) - F2[0]; k = 0.32 if b < 32.8 else 0.18
        hb += [(bt, 1.0), (bt + 0.06, 1.025 if b < 32.8 else 1.02), (bt + k, 1.0)]
    hb += [(F2[1] - F2[0] - 0.034, 1.0)]
    hb = sorted({round(t, 4): v for t, v in hb}.items())
    HB_TF = {"anchorX": 0.5, "anchorY": 760 / H}
    add_img(frame_path(CFG["F2_FRAME"]), "freeze2", F2[0], F2[1], kf(scale=hb), HB_TF)

    # ---------- 开场：Logo + 标题（帘幕合拢）+ 开场字 ----------
    for i, t in enumerate([0.233, 0.267, 0.3, 0.333, 0.367]):
        n = int(round(vsrc(t) * 24)) + 1
        img = channel_shift(frame_img(n), [9, 7, 5, 3, 2][i])
        s = 1.04 - 0.04 * min(1, (t - 0.233) / 0.367)
        add_img(img, "ca", t, t + 1 / 30, transform={"scale": s})
    flash = Image.new("RGBA", (W, H), (255, 252, 246, 255))
    FLASH = save_layer(flash, "flash")
    add_img(FLASH, "flash", 0.2, 0.4, kf(opacity=[(0, 0), (0.033, 0.85), (0.1, 0.6), (0.2, 0)]))
    logo = m.canvas(); m.paste_logo(logo, 540, 195, height=100)
    add_img(logo, "logo", 0, 1.467, kf(scale=[(0, 1.2), (0.25, 1.0)], opacity=[(0, 0), (0.12, 1), (1.3, 1), (1.467, 0)], y=[(1.3, 0), (1.467, -40)]),
            {"anchorX": 0.5, "anchorY": 245 / H})
    # 扫光（Logo 区域内斜向亮带，8 帧）
    lg = logo.getchannel("A")
    for i in range(8):
        band = Image.new("L", (W, H), 0); dd = ImageDraw.Draw(band)
        x = 250 + i * 80
        dd.polygon([(x, 180), (x + 60, 180), (x - 20, 310), (x - 80, 310)], fill=170)
        band = ImageChops.multiply(band.filter(ImageFilter.GaussianBlur(8)), lg)
        sh = Image.new("RGBA", (W, H), (255, 255, 255, 0)); sh.putalpha(band)
        add_img(sh, "logoshine", 0.3 + i / 30, 0.3 + (i + 1) / 30)
    us("进选项、闪白、照相音效.MP3", 0.233, 0.45)       # 开场闪白（拉帘瞬间）

    # ---------- 数值条 ----------
    for i in range(6):                                    # 入场：从上方滑入 + 填充 0→45
        u = (i + 1) / 6
        add_img(bar_path(45 * u, "P1"), "barfill", 1.767 + i / 30, 1.767 + (i + 1) / 30, transform={"y": -30 * (1 - u), "opacity": min(1, 0.3 + u)})
    bar_static(45, "P1", 1.967, 2.767)
    te = bar_roll(45, 15, "P1", 2.767, 0.35, "−30", 100, CRIMSON_HI, 125)
    bar_static(15, "P1", te, 6.6, fout=0.133)
    bar_static(15, "P1", 8.833, 16.2, fin=0.134, fout=0.1)
    bar_static(15, "P2", 16.333, 16.6, fin=0.1)
    te = bar_roll(15, 50, "P2", 16.6, 0.4, "+35", 100, AMBER_HI, 445)
    bar_static(50, "P2", te, 17.7, fout=0.1)
    bar_static(50, "P3", 17.767, 20.1, fin=0.1)
    te = bar_roll(50, 1, "P3", 20.1, 0.5, "−49", 180, CRIMSON_HI, 265)
    bar_static(1, "P3", te, 22.433, fout=0.1)
    bar_static(1, "P1", 22.5, 24.767, fin=0.1, fout=0.1)
    bar_static(1, "P1", 26.3, F2[0], fin=0.1)
    bar_static(1, "P1", F2[0], F2[1], fout=0.133, extra_kf={"scale": hb}, tf=HB_TF)
    us("收钱花钱加分减分清脆响声.MP3", 2.767, 0.6)
    us("收钱花钱加分减分清脆响声.MP3", 16.6, 0.5); us("正确提示音.MP3", 16.6, 0.45)

    # ---------- 台词字幕（逐词，文字照全量文案，去「。」「、」）----------
    n0c, n0a = len(CLIPS), len(AUDIO)
    for c in CFG["subs"]:                                  # 逐词字幕：文字照全量文案，时间取本版本 ASR（版本配置.json），不走 TW 映射
        subtitle_card([(y, [tuple(t) for t in toks]) for y, toks in c["lines"]], c["start"], c["end"], align=c.get("align", "center"),
                      x_anchor=c.get("x_anchor", 540), size=c.get("size", 70), key_size=c.get("key_size", 92))
    for c in CLIPS[n0c:] + AUDIO[n0a:]: c["_nowarp"] = True

    # ---------- 选项定格1（点①）----------
    s1, e1 = F1
    add_img(dim_img(880 + DY1), "dim1", s1, e1, kf(opacity=[(0, 0), (0.1, 1), (e1 - s1 - 0.166, 1), (e1 - s1, 0)]))
    add_img(target_img(935 + DY1), "target1", 12.4, 14.933, kf(opacity=[(0, 0), (0.05, 1), (0.15, 0.25), (0.25, 1), (0.35, 0.25), (0.45, 1), (0.55, 0.25), (0.65, 1),
                                                                (2.367, 1), (2.533, 0)], scale=[(0, 0.8), (0.12, 1.05), (0.2, 1.0)]),
            {"anchorX": 780 / W, "anchorY": (935 + DY1) / H})
    boxes1 = [((60, 980, 1020, 1160), ["どこも悪くないです", "帰ります"]), ((60, 1174, 1020, 1354), ["なんでカーテン", "閉めるんですか"]),
              ((60, 1368, 1020, 1538), ["離れてください"])]
    boxes1 = [((a, b + DY1, c, d + DY1), l) for (a, b, c, d), l in boxes1]
    for i, (box, lines) in enumerate(boxes1):
        t0 = 12.4 + i * 0.067
        cy = (box[1] + box[3]) / 2
        img = pill(m.canvas(), box, lines, 80)
        tf = {"anchorX": 0.5, "anchorY": cy / H}
        if i == 0:
            add_img(img, "opt", t0, 14.467, kf(scale=[(0, 0.85), (0.1, 1.04), (0.18, 1.0)], opacity=[(0, 0), (0.06, 1)]), tf)
            sel = pill(m.canvas(), box, lines, 80, selected=True)
            d = 14.933 - 14.467
            add_img(sel, "optsel", 14.467, 14.933, kf(opacity=[(0, 1), (0.08, 0.35), (0.16, 1), (0.24, 0.35), (0.3, 1), (d - 0.166, 1), (d, 0)],
                                                       scale=[(0, 1.0), (0.05, 1.05), (0.15, 1.0)]), tf)
        else:
            d = 14.567 - t0
            add_img(img, "opt", t0, 14.567, kf(scale=[(0, 0.85), (0.1, 1.04), (0.18, 1.0), (d - 0.134, 1.0), (d, 0.6)],
                                             opacity=[(0, 0), (0.06, 1), (d - 0.134, 1), (d, 0)]), tf)
        us("气泡提示音.MP3", t0, 0.4)
    countdown(1558 + DY1, 12.633, 14.633, 14.033, 12.633, 14.567)
    c1 = [(12.7, 540, 1453), (13.133, 540, 1264), (13.6, 560, 1070), (13.75, 530, 1075), (13.9, 552, 1068), (14.0, 600, 1165), (14.2, 545, 1075), (14.433, 545, 1070)]
    c1 = [(t, x, y + DY1) for t, x, y in c1]
    pointer_path(c1, 12.7, 14.767, clicks=[14.433])
    us("进选项、闪白、照相音效.MP3", 12.333, 0.55)
    for k in range(6): tick(12.633 + 0.25 * k, 0.35)
    for k in range(3): tick(14.033 + 0.125 * k, 0.45)
    us("咔嗒清脆点击.MP3", 14.433, 0.7)

    # ---------- 钟声拟声字 / 落锁 ----------
    word = "キーンコーンカーンコーン"
    fo = m.font("noto_black", 68)
    ws = [fo.getlength(c) for c in word]; x = 540 - sum(ws) / 2
    for i, (c, wv) in enumerate(zip(word, ws)):
        img = m.canvas(); m.draw_text(img, (x + wv / 2, 585), c, fo, IVORY, stroke=7, stroke_fill=INK, anchor="mm", shadow=(0, 0, 16, HALO))
        t0 = 19.2 + i * 0.017; d = 20.2 - t0
        ys = [(j * 0.1, 8 * math.sin(j * 0.9 + i * 0.7)) for j in range(int(d / 0.1) + 1)]
        add_img(img, "chime", t0, 20.2, kf(opacity=[(0, 0), (0.067, 1), (d - 0.1, 1), (d, 0)], y=ys))
        x += wv
    gc = m.canvas()
    m.draw_text(gc, (545, 752), "ガチャッ", m.font("noto_black", 120), CRIMSON_HI, stroke=10, stroke_fill=INK, anchor="mm",
                shadow=(0, 0, 20, HALO), glow=(18, (255, 46, 85, 210)))
    add_img(gc, "gachat", 20.1, 20.9, kf(scale=[(0, 0.5), (0.1, 1.15), (0.2, 1.0)], opacity=[(0, 0), (0.04, 1), (0.65, 1), (0.8, 0)],
                                         x=[(i / 30, v) for i, v in enumerate([0, 9, -8, 7, -5, 4, -2, 0])]), {"anchorX": 545 / W, "anchorY": 752 / H})
    # −49 暴击：红暗角闪 + 故障色散 2 帧
    vg = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((xx - 540) / 540.0) ** 2 + ((yy - 960) / 960.0) ** 2)
    vg = np.clip((dist - 0.55) / 0.6, 0, 1) * 255
    red = Image.new("RGBA", (W, H), CRIMSON[:3] + (0,)); red.putalpha(Image.fromarray(vg.astype(np.uint8)))
    add_img(red, "redvig", 20.1, 20.6, kf(opacity=[(0, 0), (0.05, 0.75), (0.5, 0)]))
    for i in range(2):
        n = int(round(vsrc(20.1 + i / 30) * 24)) + 1
        c = add_img(channel_shift(frame_img(n), 12 - 5 * i), "glitch", 20.1 + i / 30, 20.1 + (i + 1) / 30)
        CLIPS.remove(c); CLIPS.insert(4 + i, c)
    add_audio(f"{AUD}/school_chime.mp3", 19.2, vol=0.5, fout=0.6)
    add_audio(f"{AUD}/door_lock.mp3", 20.1, vol=0.8)      # ElevenLabs 生成的门锁声（资源库 g26 系列是本地合成，不用）
    us("收钱花钱加分减分清脆响声.MP3", 20.1, 0.6)

    # ---------- 选项定格2（不点，心跳）----------
    s2, e2 = F2
    add_img(dim_img(1150 + DY2), "dim2", s2, e2, kf(opacity=[(0, 0), (0.1, 1), (e2 - s2 - 0.133, 1), (e2 - s2, 0)]))
    vig = Image.new("RGBA", (W, H), INK[:3] + (0,)); vig.putalpha(Image.fromarray((np.clip((dist - 0.45) / 0.7, 0, 1) * 200).astype(np.uint8)))
    vk = [(0, 0)]
    for b in beats:
        bt = snap(b) - s2; vk += [(bt, 0.35), (bt + 0.08, 0.9), (bt + 0.32, 0.4)]
    vk += [(e2 - s2 - 0.1, 0.4), (e2 - s2, 0)]
    add_img(vig, "vig2", s2, e2, kf(opacity=vk))
    add_img(target_img(1245 + DY2), "target2", 30.567, 33.1, kf(opacity=[(0, 0), (0.05, 1), (0.15, 0.25), (0.25, 1), (0.35, 0.25), (0.45, 1), (0.55, 0.25), (0.65, 1),
                                                                   (2.4, 1), (2.533, 0)], scale=[(0, 0.8), (0.12, 1.05), (0.2, 1.0)]),
            {"anchorX": 780 / W, "anchorY": (1245 + DY2) / H})
    boxes2 = [((60, 1295 + DY2, 1020, 1465 + DY2), ["カーテンを開けて逃げる"]), ((60, 1481 + DY2, 1020, 1651 + DY2), ["白衣を掴む"])]
    for i, (box, lines) in enumerate(boxes2):
        t0 = 30.567 + i * 0.066; d = 33.1 - t0
        cy = (box[1] + box[3]) / 2
        add_img(pill(m.canvas(), box, lines, 80), "opt2", t0, 33.1,
                kf(scale=[(0, 0.85), (0.1, 1.04), (0.18, 1.0)], opacity=[(0, 0), (0.06, 1), (d - 0.133, 1), (d, 0)]), {"anchorX": 0.5, "anchorY": cy / H})
        us("气泡提示音.MP3", t0, 0.4)
    countdown(1671 + DY2, 30.667, 32.667, 32.067, 30.667, 33.1)
    c2 = [(30.733, 760, 1700), (30.833, 545, 1385), (31.3, 545, 1570), (31.767, 548, 1382), (32.2, 545, 1566), (32.45, 560, 1560), (32.7, 538, 1572), (32.95, 552, 1564)]
    c2 = [(t, x, y + DY2) for t, x, y in c2]
    pointer_path(c2, 30.733, 33.1)
    add_audio(f"{AUD}/final_bell.mp3", 30.5, vol=0.6, fout=0.4)
    us("进选项、闪白、照相音效.MP3", 30.5, 0.35)
    for i, b in enumerate(beats): add_audio(f"{AUD}/heartbeat_soft_hp.wav", snap(b), vol=round(0.4 + 0.05 * i, 2))
    for k in range(6): tick(30.667 + 0.25 * k, 0.3)
    for k in range(5): tick(32.067 + 0.125 * k, 0.4)

    # ---------- 承接：定格缩进手机 + app-ui ----------
    SCR = (140, 130, 940, 1550)                 # 0.74 屏：799×1421，中心 (540,840)
    bg = Image.open(frame_path(CFG["F2_FRAME"])).convert("RGBA").filter(ImageFilter.GaussianBlur(40))
    grad = m.gradient_rect((W, H), (116, 232, 208, 255), (187, 160, 255, 255), horizontal=False); grad.putalpha(90)
    bg.alpha_composite(grad)
    fz_rgb = Image.open(frame_path(CFG["F2_FRAME"])).convert("RGB")
    tmp = f"{OUT}/_ui_frames"; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", UI_MP4, "-t", "0.34", "-vf", "fps=30", f"{tmp}/%03d.png"], check=True)
    seq_dir = f"{LAY}/bridge"; os.makedirs(seq_dir, exist_ok=True)
    nfr = int(round((BR1 - BR0) * 30))
    for i in range(nfr):
        t = BR0 + i / 30
        u = min(1, (t - BR0) / (BR1 - BR0)); e = u * u * (3 - 2 * u)
        s = 1 - 0.26 * e; cy = 960 - 120 * e
        fr = bg.copy()
        fz = ImageEnhance.Color(fz_rgb).enhance(1 - 0.2 * e).convert("RGBA")
        content = fz
        if t >= UI0:
            ui = Image.open(f"{tmp}/{int((t - UI0) * 30) + 1:03d}.png").convert("RGBA")
            content = Image.blend(fz, ui, min(1, (t - UI0) / (BR1 - UI0)))
        cw, ch = int(W * s), int(H * s)
        sc = content.resize((cw, ch), Image.LANCZOS)
        x0, y0 = int(540 - cw / 2), int(cy - ch / 2)
        bw = int(14 * e); r = int(60 * e) + 1
        m.soft_shadow(fr, (x0 - bw, y0 - bw, x0 + cw + bw, y0 + ch + bw), r + bw, blur=30, color=(0, 0, 0, int(140 * e)), dy=16)
        if bw: m.rrect(fr, (x0 - bw, y0 - bw, x0 + cw + bw, y0 + ch + bw), r + bw, fill=(255, 255, 255, 255))
        mask = Image.new("L", (cw * 2, ch * 2), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw * 2 - 1, ch * 2 - 1), r * 2, fill=255)
        sc.putalpha(mask.resize((cw, ch), Image.LANCZOS)); fr.alpha_composite(sc, (x0, y0))
        fr.save(f"{seq_dir}/{i:03d}.png")
    shutil.rmtree(tmp, ignore_errors=True)
    # app-ui 视频（缩到 0.74 放进屏内）+ 屏外遮罩（模糊背景挖洞 + 白边 + 投影）
    PUSH0, PUSH1 = 37.9 - UI0, 41.0 - UI0                 # 详情页静止段慢推（底边不动，不压口播底板）

    def vy(s_): return 590 - 960 * s_
    CLIPS.append({"type": "video", "src": UI_MP4, "start": UI0, "duration": round(min(UI_D, END - UI0) * 30) / 30, "in": 0, "fit": "cover",
                  "transform": {"scale": 0.74, "y": vy(0.74)},
                  "keyframes": kf(scale=[(PUSH0, 0.74), (PUSH1, 0.77)], y=[(PUSH0, vy(0.74)), (PUSH1, vy(0.77))])})
    ov = bg.copy()
    m.soft_shadow(ov, (SCR[0] - 14, SCR[1] - 14, SCR[2] + 14, SCR[3] + 14), 74, blur=30, color=(0, 0, 0, 140), dy=16)
    m.rrect(ov, (SCR[0] - 14, SCR[1] - 14, SCR[2] + 14, SCR[3] + 14), 74, fill=(255, 255, 255, 255))
    hole = Image.new("L", (W * 2, H * 2), 255)
    ImageDraw.Draw(hole).rounded_rectangle((SCR[0] * 2, SCR[1] * 2, SCR[2] * 2 - 1, SCR[3] * 2 - 1), 120, fill=0)
    ov.putalpha(ImageChops.multiply(ov.getchannel("A"), hole.resize((W, H), Image.LANCZOS)))
    k1 = 0.77 / 0.74
    add_img(ov, "phonemask", BR1, E0 + 0.1, kf(scale=[(37.9 - BR1, 1.0), (41.0 - BR1, k1)], y=[(37.9 - BR1, 0), (41.0 - BR1, 590 - 590 * k1)]))
    CLIPS.append({"type": "sequence", "src": f"{seq_dir}/%03d.png", "start": BR0, "duration": round(BR1 - BR0, 4), "fps": 30})
    UI_DUCK = True                                         # 口播期间压低产品 UI 自带音效（rules/通用.md）
    us("科技感空灵音效.MP3", BR0, 0.4, fout=0.6)
    # 口播字幕（手机下方）
    w1 = VOW["vo1"]; w2 = VOW["vo2"]; w3 = VOW["vo3"]
    vo_card("vo1", [(0, VO_D["vo1"] + 0.15, [("危険な", 0.0), ("恋は", 0.54), ("[LOGO]", 0.92), ("で", 1.48)], None)])
    vo_card("vo2", [(0, 1.8, [("背徳感に", 0.0), ("震える", 1.14)], None), (1.833, min(VO_D["vo2"] + 0.15, VO_T["vo3"] - VO_T["vo2"]), [("刺激的な", 1.84), ("シチュエーション", 2.64)], None)])
    for k in ("vo1", "vo2", "vo3"): add_audio(f"{AUD}/{k}.wav", VO_T[k], vol=1.0)

    # ---------- 片尾：三卡片尾板（用户指定的默认样式）----------
    endcard3.build({"E0": E0, "add_img": add_img, "kf": kf, "snap": snap, "us": us, "CLIPS": CLIPS, "pointer_path": pointer_path,
                    "VO4_T": VO_T["vo3"], "VO4_W": VOW["vo3"], "button_text": "今すぐ無料で話す",
                    "copy": [{"y": 1250, "size": 84, "gold": False, "tokens": [("あなただけを", 0.0)]},
                             {"y": 1372, "size": 128, "gold": True, "tokens": [("必要とする先生", 1.1)]}],     # 末行金色大字（参考图）
                    "cards": [(f"{RES}/library/cards/20261103-追放された女騎士.jpg", 0.35, "裏切られた女騎士", 987265, "filler"),
                              (f"{RES}/library/cards/20261028-学妹辣妹二争一-1.jpg", 0.30, "レイナ", 1059130, "filler"),
                              (frame_path(CFG["HERO_FRAME"]), CFG.get("HERO_FOCUS", 0.30), "保健室の先生", 1231846, "hero")]})

    add_img(FLASH, "flash2", E0 - 0.067, E0 + 0.2, kf(opacity=[(0, 0), (0.067, 1), (0.267, 0)]))

    # ---------- 原声 ----------
    add_audio(SRC, 0, duration=A_END, vol=1.0, fout=0.03)
    add_audio(SRC, B0, duration=round(B1 - B0, 4), vol=1.0, src_in=B_IN, fin=0.03, fout=0.05)

    # ---------- BGM：整句平滑压低（分段 + 重叠交叉淡化，不用侧链）----------
    def bgm_env(src, at, plats, first_fin, last_fout):
        """plats: [(t0, t1, level[, ramp_before])]；相邻段在 [t0-ramp, t0] 重叠交叉淡化（同源同相位 → 增益平滑过渡）。"""
        for i, p in enumerate(plats):
            a, b, lv = p[:3]; rin = p[3] if len(p) > 3 else 0
            nxt = plats[i + 1] if i + 1 < len(plats) else None
            rout = nxt[3] if nxt else last_fout
            st = a - rin; en = b + (rout if nxt else 0)
            add_audio(src, round(st, 4), duration=round(en - st, 4), vol=lv, fin=round(rin if i else first_fin, 3), fout=round(rout, 3), src_in=round(st - at, 4))

    HI, LO = 0.30, 0.10
    # 开头：文件 0–1.25 s 是静音，借文件 5.567 起（5.80 s 重拍落在 0.233 闪白上）铺 0–2.65
    add_audio(f"{AUD}/bgm_story_lite.mp3", 0, duration=2.65, vol=HI, fin=0.03, fout=0.25, src_in=5.567)
    bgm_env(f"{AUD}/bgm_story_lite.mp3", 0, [(2.65, 12.26, LO, 0.25), (12.96, 22.40, HI, 0.7), (22.65, 30.77, LO, 0.25),
                                         (31.30, 31.80, HI, 0.53)], 0.25, 0.05)
    # 故事 BGM 在 31.80 断（生成结果只到这里）：重放 final choice 开头 1.3 s 接到 33.1 缩进手机
    add_audio(f"{AUD}/bgm_story_lite.mp3", 31.78, duration=1.32, vol=HI, fin=0.03, fout=0.1, src_in=30.48)
    # 产品 UI 音效分段压低
    bgm_env(UI_MP4, UI0, [(33.4, 33.5, 0.9), (33.6, VO_T["vo1"] + VO_D["vo1"] + 0.1, 0.22, 0.1), (VO_T["vo1"] + VO_D["vo1"] + 0.2, VO_T["vo2"] - 0.15, 0.9, 0.1),
                          (VO_T["vo2"] - 0.05, VO_T["vo2"] + VO_D["vo2"] + 0.1, 0.22, 0.1), (VO_T["vo2"] + VO_D["vo2"] + 0.2, UI0 + UI_D, 0.9, 0.1)], 0, 0)
    vo_end = VO_T["vo3"] + VO_D["vo3"] + 0.5
    # 承接 BGM：文件 11.1 s 后没声（end card 段只生成了 1.65 s），43.47 起按小节续接文件 5.90 s 起的律动
    bgm_env(f"{AUD}/bgm_bridge_lite.mp3", 32.35, [(32.35, 33.35, HI), (33.6, 43.47, LO, 0.25)], 0.5, 0.05)
    bgm_env(f"{AUD}/bgm_bridge_lite.mp3", 43.47 - 5.90, [(43.47, vo_end, LO), (vo_end + 0.5, END, HI, 0.5)], 0.05, 0.6)

    # ---------- 版本时间映射 → 写 timeline ----------
    end_v = warp(CLIPS, AUDIO, END)
    tl = {"size": [W, H], "fps": 30, "duration": end_v, "limiter": 0.84,
          "out": f"{P}/导出/MM-JP-病娇女教师_预览_{CFG['role']}.mp4", "clips": CLIPS, "audio": AUDIO}
    json.dump(tl, open(f"{P}/timeline_{VER}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tw = lambda x: round(TW(x), 3)
    meta = {"A_END": tw(A_END), "F1": [tw(F1[0]), tw(F1[1])], "B_src": [V_B, V_E], "B": [tw(B0), tw(B1)], "F2": [tw(F2[0]), tw(F2[1])], "BR0": tw(BR0), "UI0": tw(UI0),
            "UI_D": UI_D, "UI_EV": [[e, tw(UI0 + t)] for e, t in UI_EV], "E0": tw(E0), "END": end_v,
            "VO": {k: [tw(VO_T[k]), tw(VO_T[k] + VO_D[k])] for k in VO_T}, "events": {"−30": tw(2.767), "+35": tw(16.6), "chime": tw(19.2), "−49 lock": tw(20.1)},
            "clips": len(CLIPS), "audio": len(AUDIO)}
    json.dump(meta, open(f"{OUT}/timing.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    build()
