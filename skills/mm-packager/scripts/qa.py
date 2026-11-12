#!/usr/bin/env python
"""mm-packager 自检：timeline 秒级自检 + 成片自检。只读，不改任何文件。

用法：
  python qa.py tl timeline.json [--base 已验收的timeline.json]   # 几秒到十几秒，不渲染
  python qa.py video 成片.mp4
有「错误」时退出码 1；只有「警告」时退出码 0。

qa.py tl 查：
- 1/30 网格：clip 的 start、duration 不在 1/30 s 网格上（rules/工程交付.md「timeline」）。
- 闪断：一个画面元素结束后隔 1–2 帧，同一位置又出现（两端都不透明），中间没有同位置的层接上 → 画面闪一下。
- 出画：图层的 alpha 外框（alpha > 64）套上 transform 和各关键帧的缩放、位移、旋转后超出画布。
  静止时就贴着画布边的图层只报警告（可能是有意出血，如尾板两侧的卡）；铺满整个画布的层不查。
- 全屏特效层 z 序：从剧情段跨进产品 UI/尾板段、又叠在产品 UI/尾板 clip 上面的全屏图片层（故障色散、闪白、暗角）。
  产品 UI/尾板 clip = src 带「产品UI」「尾板」，或 endcard3 的 ec_ 图层。
- BGM 覆盖：BGM（文件名带 bgm，或尾板 mp4 自带）在 0–duration 里的空档；in+duration 超出文件长度的部分不算覆盖。
- 同源相位：同一个 BGM 文件的两条在时间上重叠 ≥ 0.3 s 时 (in − start) 必须相等，否则同一首曲子错开叠在一起
  （更短的重叠是按小节续接的交叉淡化，不报）。
- 合成音效：引用了 $RES/sfx 里 g26-/lgx-/liquid-/kpop-/s_glitch 开头的本地合成音效（rules/通用.md「音效来源」）。
- --base：和已验收版本的 timeline 做结构对比（图层组、叠放顺序、音频条目；版本号、视频序号、帧号不算差异），差异报警告，时间差只打印。
qa.py video 查：ffprobe 规格（1080×1920、H.264、yuv420p、有音轨）、ebur128 真峰值 ≤ -1.0 dBTP（同时打印 LUFS）、blackdetect 黑场。
"""
import argparse, json, math, os, re, subprocess, sys
from collections import Counter, defaultdict
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import tf_at, fit_size, loudness          # 和渲染同一套变换、适配、响度算法

FR = 1 / 30
SYNTH_SFX = ("g26-", "lgx-", "liquid-", "kpop-", "s_glitch")
ERR, WARN = [], []


def err(msg): ERR.append(msg)
def warn(msg): WARN.append(msg)


def group(c):
    """图层组名：文件名去掉序号前缀和扩展名（gen.py 的 add_img 存成 NNN_name.png）。"""
    return re.sub(r"^\d+_", "", os.path.splitext(os.path.basename(c["src"]))[0])


def fmt(t): return f"{t:.3f}"


# ---------------------------------------------------------------- 图层几何
_info = {}


def probe_wh(src):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", src],
                       capture_output=True, text=True)
    w, h = r.stdout.strip().split("\n")[0].split(",")[:2]
    return int(w), int(h)


def layer_info(c):
    """返回 (宽, 高, alpha 外框或 None, 1/8 尺寸 alpha 数组或 None)；找不到文件返回 None。"""
    src = c["src"]
    if c["type"] == "sequence":
        src = src % c.get("first", 0)
    if src in _info: return _info[src]
    if not os.path.isfile(src):
        _info[src] = None
    elif c["type"] == "video":
        w, h = probe_wh(src); _info[src] = (w, h, (0, 0, w, h), None)
    else:
        im = Image.open(src)
        a = im.convert("RGBA").getchannel("A")
        bb = a.point(lambda v: 255 if v > 64 else 0).getbbox()
        small = np.asarray(a.resize((max(1, a.width // 8), max(1, a.height // 8)), Image.BOX))
        _info[src] = (im.width, im.height, bb, small)
        im.close()
    return _info[src]


def box_at(c, info, lt, W, H):
    """clip 在 clip 内相对秒 lt 时，alpha 外框在画布上的外接框 (x0, y0, x1, y1) 和不透明度。算法同 render.place。"""
    iw, ih, bb, _ = info
    tf = tf_at(c, lt)
    fw, fh = fit_size(c.get("fit", "cover" if c["type"] == "video" else "fill"), iw, ih, W, H)
    ox, oy = (W - fw) / 2, (H - fh) / 2
    kx, ky = fw / iw, fh / ih
    sx, sy = tf["scale"] * tf["scaleX"], tf["scale"] * tf["scaleY"]
    ax, ay = ox + tf["anchorX"] * fw, oy + tf["anchorY"] * fh
    th = math.radians(tf["rotation"]); cs, sn = math.cos(th), math.sin(th)
    xs, ys = [], []
    for px, py in ((bb[0], bb[1]), (bb[2], bb[1]), (bb[0], bb[3]), (bb[2], bb[3])):
        dx, dy = (ox + px * kx - ax) * sx, (oy + py * ky - ay) * sy
        xs.append(ax + tf["x"] + cs * dx - sn * dy); ys.append(ay + tf["y"] + sn * dx + cs * dy)
    return (min(xs), min(ys), max(xs), max(ys)), max(0., min(1., tf["opacity"]))


def rest_box(c, info, W, H):
    """不加 transform/关键帧时（图层画好的位置）在画布上的外框。"""
    iw, ih, bb, _ = info
    fw, fh = fit_size(c.get("fit", "cover" if c["type"] == "video" else "fill"), iw, ih, W, H)
    ox, oy = (W - fw) / 2, (H - fh) / 2
    return ox + bb[0] * fw / iw, oy + bb[1] * fh / ih, ox + bb[2] * fw / iw, oy + bb[3] * fh / ih


def sample_times(c):
    d = c["duration"]
    ts = {0.0, max(0.0, d - FR)}
    for ks in (c.get("keyframes") or {}).values():
        for k in ks:
            if 0 <= k["t"] < d: ts.add(float(k["t"]))
    return sorted(ts)


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0


# ---------------------------------------------------------------- timeline 各项检查
def check_grid(clips):
    bad = []
    for i, c in enumerate(clips):
        for k in ("start", "duration"):
            v = c[k] * 30
            if abs(v - round(v)) > 0.01: bad.append(f"clip {i} {group(c)} {k}={c[k]}")
    if bad: err(f"1/30 网格：{len(bad)} 处不在网格上（相邻片段会有半帧缝），例：" + "；".join(bad[:5]))


def check_flash_gap(clips, W, H):
    items = []
    for i, c in enumerate(clips):
        info = layer_info(c)
        if info and info[2]: items.append((i, c, info))
    by_start = sorted(items, key=lambda x: x[1]["start"])
    starts = [x[1]["start"] for x in by_start]
    import bisect
    found, seen = [], set()
    for i, a, ia in items:
        ta = a["start"] + a["duration"]
        lo = bisect.bisect_left(starts, ta + FR - 1e-3); hi = bisect.bisect_right(starts, ta + 2 * FR + 1e-3)
        if lo >= hi: continue
        boxa, opa = box_at(a, ia, max(0.0, a["duration"] - FR), W, H)
        if opa < 0.99: continue
        for j, b, ib in by_start[lo:hi]:
            if j == i: continue
            boxb, opb = box_at(b, ib, 0.0, W, H)
            if opb < 0.99 or iou(boxa, boxb) < 0.5: continue
            tb = b["start"]
            gap = [ta + n * FR for n in range(round((tb - ta) * 30))]
            def filled(t):                               # 这一帧有同位置、不透明的层接上
                for k, cc, ic in items:
                    if k in (i, j) or not (cc["start"] - 1e-6 <= t < cc["start"] + cc["duration"] - 1e-6): continue
                    boxc, opc = box_at(cc, ic, t - cc["start"], W, H)
                    if opc >= 0.99 and iou(boxa, boxc) >= 0.5: return True
                return False
            miss = [t for t in gap if not filled(t)]
            if miss and (j, round(miss[0] * 30)) not in seen:
                seen.add((j, round(miss[0] * 30)))
                found.append(f"{fmt(miss[0])} 起 {group(a)}（{fmt(ta)} 结束）→ {group(b)}（{fmt(tb)} 开始）中间空 {len(miss)} 帧")
            if miss: break                               # 同一个 A 只报一次
    for f in found: err(f"闪断：{f}")


def check_out_of_frame(clips, W, H):
    errs, warns = defaultdict(list), defaultdict(list)
    for i, c in enumerate(clips):
        if c["type"] == "video": continue
        info = layer_info(c)
        if not info or not info[2]: continue
        r = rest_box(c, info, W, H)
        tl_, tt, tr, tb = r[0] <= 1, r[1] <= 1, r[2] >= W - 1, r[3] >= H - 1
        if (tl_ and tr) or (tt and tb): continue        # 铺满整宽或整高的层（背景、遮罩、暗角）不查
        worst, at = 0.0, None
        for lt in sample_times(c):
            box, op = box_at(c, info, lt, W, H)
            if op <= 0.05: continue
            ex = max(-box[0], -box[1], box[2] - W, box[3] - H)
            if ex > worst: worst, at = ex, c["start"] + lt
        if tl_ or tt or tr or tb: warns[group(c)].append((c["start"], worst))
        elif worst > 1: errs[group(c)].append((at, worst))
    for g, v in errs.items():
        at, ex = max(v, key=lambda x: x[1])
        err(f"出画：{g} 共 {len(v)} 条，最严重 {fmt(at)} s 超出画布 {ex:.0f} px（按缩放/位移/旋转后的外框算）")
    for g, v in warns.items():
        ex = max(x[1] for x in v)
        warn(f"贴边：{g} 共 {len(v)} 条，图层画好时就贴着画布边（{fmt(v[0][0])} s 起）" + (f"，动画时再超出 {ex:.0f} px" if ex > 1 else "")
             + "；有意出血（如尾板两侧的卡）可以不管，否则是出画")


def is_ui(c):
    s = c["src"].replace("\\", "/")
    return "产品UI" in s or "尾板" in s or group(c).startswith("ec_")


def check_fx_z(clips, W, H):
    ui = [(i, c) for i, c in enumerate(clips) if is_ui(c)]
    if not ui: return
    seg0 = min(c["start"] for _, c in ui)
    for i, c in enumerate(clips):
        if c["type"] != "image" or is_ui(c): continue
        s, e = c["start"], c["start"] + c["duration"]
        if not (s < seg0 - 1e-6 and e > seg0 + FR - 1e-6): continue
        info = layer_info(c)
        if not info or not info[2]: continue
        r = rest_box(c, info, W, H)
        if not (r[0] <= 1 and r[1] <= 1 and r[2] >= W - 1 and r[3] >= H - 1): continue   # 只看全屏层
        over = [u for j, u in ui if j < i and min(e, u["start"] + u["duration"]) - max(s, u["start"]) >= FR - 1e-6]
        if over:
            err(f"全屏特效层 z 序：{group(c)}（{fmt(s)}–{fmt(e)}）从剧情段跨进产品 UI/尾板段（{fmt(seg0)} 起），"
                f"叠在 {', '.join(sorted({group(u) for u in over})[:4])} 上面")


_dur = {}


def media_dur(src):
    if src not in _dur:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True)
        try: _dur[src] = float(r.stdout.strip())
        except ValueError: _dur[src] = None
    return _dur[src]


def check_bgm(audio, dur):
    bgm = [a for a in audio if is_bgm(a)]
    if not bgm:
        print("信息  BGM 覆盖：timeline 里没有 BGM 条目（无 BGM 版？），跳过"); return
    iv = []
    for a in bgm:
        fd = media_dur(a["src"])
        if fd is None: err(f"BGM 覆盖：读不到 {a['src']}"); continue
        d = min(a["duration"], fd - a.get("in", 0))
        if d < a["duration"] - 0.05:
            warn(f"BGM 覆盖：{os.path.basename(a['src'])} {fmt(a['start'])} 起这条 in+duration 超出文件 {a['duration'] - max(0, d):.2f} s（超出部分没声音）")
        if d > 0: iv.append((a["start"], a["start"] + d))
    iv.sort()
    t, gaps = 0.0, []
    for s, e in iv:
        if s - t >= 0.1: gaps.append((t, s))
        t = max(t, e)
    if dur - t >= 0.1: gaps.append((t, dur))
    for s, e in gaps: err(f"BGM 覆盖：{fmt(s)}–{fmt(e)} 没有 BGM（{e - s:.2f} s）")


def is_bgm(a):
    return ("bgm" in os.path.basename(a["src"]).lower() or "尾板" in a["src"]) and a.get("volume", 1) > 0


def check_phase(audio):
    by = defaultdict(list)
    for a in audio:
        if is_bgm(a): by[a["src"]].append(a)
    for src, items in by.items():
        items = sorted(items, key=lambda a: a["start"])
        for x in range(len(items)):
            for y in range(x + 1, len(items)):
                a, b = items[x], items[y]
                ov = min(a["start"] + a["duration"], b["start"] + b["duration"]) - max(a["start"], b["start"])
                if ov < 0.3: continue
                dp = (b.get("in", 0) - b["start"]) - (a.get("in", 0) - a["start"])
                if abs(dp) > 0.01:
                    err(f"同源相位：{os.path.basename(src)} 两条在 {fmt(max(a['start'], b['start']))} 起重叠 {ov:.2f} s，相位差 {dp:+.3f} s（同一首曲子错开叠在一起）")


def check_synth_sfx(tl):
    hits = []
    for a in tl.get("audio", []) + tl.get("clips", []):
        p = a["src"].replace("\\", "/")
        if os.path.basename(os.path.dirname(p)).lower() == "sfx" and os.path.basename(p).lower().startswith(SYNTH_SFX):
            hits.append(f"{os.path.basename(p)}（{fmt(a['start'])} s）")
    if hits: err(f"合成音效：引用了 $RES/sfx 里的本地合成音效 {', '.join(hits)}；换用户音效收集 $USER_SFX，没有再用 ElevenLabs 生成")


def vnorm(name):
    """对比基准时去掉版本差异：版本N、视频_N、纯数字的帧号。"""
    name = re.sub(r"版本\d+", "版本N", re.sub(r"视频_\d+", "视频_N", name))
    return "<帧号>" if name.isdigit() else name


def check_base(tl, base):
    def keys(t):
        return [(c["type"], vnorm(group(c))) for c in t["clips"]]
    k1, k0 = keys(tl), keys(base)
    c1, c0 = Counter(k1), Counter(k0)
    only1 = sorted(set(c1) - set(c0)); only0 = sorted(set(c0) - set(c1))
    if only1: warn(f"对比基准：基准里没有的图层组 {', '.join(g for _, g in only1[:8])}")
    if only0: warn(f"对比基准：比基准少了图层组 {', '.join(g for _, g in only0[:8])}")
    cnt = [f"{g} {c0[k]}→{c1[k]}" for k in sorted(set(c1) & set(c0)) for g in [k[1]] if c1[k] != c0[k]]
    if cnt: warn(f"对比基准：图层组条数不同 {'；'.join(cnt[:8])}" + (f" 等 {len(cnt)} 组" if len(cnt) > 8 else ""))
    common = set(c1) & set(c0)
    f1 = list(dict.fromkeys(k for k in k1 if k in common)); f0 = list(dict.fromkeys(k for k in k0 if k in common))
    if f1 != f0:
        n = next(i for i, (a, b) in enumerate(zip(f1, f0)) if a != b)
        warn(f"对比基准：叠放顺序变了，第一处：基准是 {f0[n][1]}，现在是 {f1[n][1]}")
    a1 = Counter(vnorm(os.path.basename(a["src"])) for a in tl.get("audio", [])); a0 = Counter(vnorm(os.path.basename(a["src"])) for a in base.get("audio", []))
    ad = [f"{k} {a0[k]}→{a1[k]}" for k in sorted(set(a1) | set(a0)) if a1[k] != a0[k]]
    if ad: warn(f"对比基准：音频条目不同 {'；'.join(ad[:8])}")
    # 时间差（只打印）：同组第 n 条配对
    seen, idx0 = Counter(), defaultdict(list)
    for c in base["clips"]: idx0[(c["type"], vnorm(group(c)))].append(c)
    diffs = []
    for c in tl["clips"]:
        k = (c["type"], vnorm(group(c))); n = seen[k]; seen[k] += 1
        if n < len(idx0[k]):
            b = idx0[k][n]
            diffs.append((max(abs(c["start"] - b["start"]), abs(c["duration"] - b["duration"])), group(c), b["start"], c["start"]))
    mx = max(diffs) if diffs else (0, "", 0, 0)
    same = not (only1 or only0 or cnt or ad or f1 != f0) and mx[0] < 1e-3 and \
        abs(tl.get("duration", 0) - base.get("duration", 0)) < 1e-3
    print(f"信息  对比基准：时长 {base.get('duration', 0):.3f} → {tl.get('duration', 0):.3f} s；配对图层最大时间差 {mx[0]:.3f} s"
          + (f"（{mx[1]}：{mx[2]:.3f} → {mx[3]:.3f}）" if mx[0] >= 1e-3 else "") + ("；和基准一致" if same else ""))


def cmd_tl(a):
    tl = json.load(open(a.timeline, encoding="utf-8"))
    W, H = tl.get("size", [1080, 1920])
    dur = tl.get("duration") or max(c["start"] + c["duration"] for c in tl["clips"])
    clips, audio = tl["clips"], tl.get("audio", [])
    missing = sorted({c["src"] for c in clips if layer_info(c) is None})
    if missing: err(f"找不到图层文件 {len(missing)} 个，例：{missing[0]}")
    check_grid(clips)
    check_flash_gap(clips, W, H)
    check_out_of_frame(clips, W, H)
    check_fx_z(clips, W, H)
    check_bgm(audio, dur)
    check_phase(audio)
    check_synth_sfx(tl)
    if a.base: check_base(tl, json.load(open(a.base, encoding="utf-8")))
    return report(f"qa tl {os.path.basename(a.timeline)}（{len(clips)} 个 clip、{len(audio)} 条音频、{dur:.3f} s）")


# ---------------------------------------------------------------- 成片
def cmd_video(a):
    f = a.video
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,pix_fmt,r_frame_rate",
                        "-show_entries", "format=duration", "-of", "json", f], capture_output=True, text=True, encoding="utf-8")
    info = json.loads(r.stdout or "{}")
    vs = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    aus = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    if not vs: err("规格：没有视频流"); return report(f"qa video {os.path.basename(f)}")
    v = vs[0]; d = float(info.get("format", {}).get("duration", 0) or 0)
    print(f"信息  规格：{v.get('width')}×{v.get('height')} {v.get('codec_name')} {v.get('pix_fmt')} {v.get('r_frame_rate')} fps，{d:.3f} s，音轨 {len(aus)} 条")
    if (v.get("width"), v.get("height")) != (1080, 1920): err(f"规格：尺寸 {v.get('width')}×{v.get('height')}，不是 1080×1920")
    if v.get("codec_name") != "h264": err(f"规格：编码 {v.get('codec_name')}，不是 H.264")
    if v.get("pix_fmt") != "yuv420p": err(f"规格：像素格式 {v.get('pix_fmt')}，不是 yuv420p（yuvj420p 用户打不开）")
    if not aus: err("规格：没有音轨")
    else:
        lv = loudness(f)
        if lv is None: err("响度：ebur128 没量出结果")
        else:
            print(f"信息  响度 {lv[0]:.1f} LUFS，真峰值 {lv[1]:.1f} dBTP")
            if lv[1] > -1.0: err(f"真峰值 {lv[1]:.1f} dBTP 超过 -1.0（降 limiter 或音量后重出）")
    r = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", f, "-map", "0:v:0", "-vf", "blackdetect=d=0.1:pix_th=0.10",
                        "-an", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    for m in re.finditer(r"black_start:\s*([\d.]+)\s+black_end:\s*([\d.]+)", r.stderr):
        err(f"黑场：{float(m.group(1)):.3f}–{float(m.group(2)):.3f} s（黑屏会被当成坏片）")
    return report(f"qa video {os.path.basename(f)}")


def report(title):
    for m in ERR: print(f"错误  {m}")
    for m in WARN: print(f"警告  {m}")
    print(f"{title}：错误 {len(ERR)}，警告 {len(WARN)}" + ("，通过" if not ERR else ""))
    return 1 if ERR else 0


def main():
    ap = argparse.ArgumentParser(description="mm-packager 自检")
    sp = ap.add_subparsers(dest="cmd", required=True)
    t = sp.add_parser("tl", help="timeline 秒级自检"); t.add_argument("timeline"); t.add_argument("--base", help="已验收版本的 timeline.json，做结构对比")
    v = sp.add_parser("video", help="成片自检"); v.add_argument("video")
    a = ap.parse_args()
    sys.exit(cmd_tl(a) if a.cmd == "tl" else cmd_video(a))


if __name__ == "__main__":
    main()
