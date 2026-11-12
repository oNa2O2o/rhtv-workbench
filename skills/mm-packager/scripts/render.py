#!/usr/bin/env python
"""mm-packager 渲染器：timeline.json → mp4（PIL 逐帧合成 + ffmpeg 编码/混音），不依赖编辑器。

用法：
  python render.py timeline.json                 # 出成片
  python render.py timeline.json --draft         # 540x960 校对预览（按半尺寸合成，快）
  python render.py timeline.json --still 3.5 8.2 # 出指定时刻静帧 PNG（看版面）
  可选 --out 覆盖输出路径。出片步骤、命名、时间吸附等规则见 rules/工程交付.md；BGM 闪避规则见 rules/通用.md。
  出片（含 --draft）包在 mmkit/heavy.py 的 heavy_lock("render") 里排队，可用内存不够就等（mmkit 导入失败就不锁）。
  出片后自动用 ebur128 peak=true 量响度和真峰值并打印；真峰值 > -1.0 dBTP 时以退出码 3 结束（--draft 只警告）。

timeline.json 格式（下例数值只是示例，不是默认值或规则；路径按 rules/工程交付.md 的目录，这里以 版本1 为例）：
{
  "size": [1080, 1920], "fps": 30, "duration": 23.4, "out": "$P/导出/<工程名>_预览v1_<角色名>.mp4", "limiter": 0.84,
  "clips": [   // 数组顺序 = 叠放顺序，后面的在上层
    {"type": "video", "src": "$P/素材/视频_1_1080.mp4", "start": 0, "duration": 12.03, "in": 0, "fit": "cover",
     "transform": {"x":0,"y":0,"scale":1,"rotation":0,"opacity":1,"anchorX":.5,"anchorY":.5},
     "keyframes": {"scale": [{"t":11.4,"v":1},{"t":12.0,"v":1.35,"ease":"ease"}]}},
    {"type": "image", "src": "$P/包装素材_版本1/sub0.png", "start": 4.0, "duration": 2.2,
     "keyframes": {"opacity": [{"t":0,"v":0},{"t":0.15,"v":1}]}},
    {"type": "sequence", "src": "$P/包装素材_版本1/intro_%03d.png", "start": 0, "duration": 4.45, "fps": 30},   // 逐帧图层
    {"type": "video", "src": "$P/包装素材_产品UI/产品UI-划卡_版本1.mp4", "start": 12.03, "duration": 5.47}
  ],
  "audio": [
    {"src": "$P/素材/视频_1_1080.mp4", "start": 0, "duration": 12.03, "in": 0, "volume": 1},
    {"src": "$P/包装素材_版本1/audio/bgm.mp3", "start": 0, "duration": 23.4, "in": 0, "fadeOut": 0.6,
     "gain": [[3.75, <不压>], [4.0, <压低>], [6.6, <压低>], [7.3, <不压>]]}   // 一条连续 BGM + 增益曲线（mmkit/audio.py 的 duck_points() 生成）
  ]
}
（src 写实际绝对路径；$P 只是占位，脚本不展开变量。gain 的 <…> 按本片听感定，不写死。）

clips：
- type：video（视频片段）/ image（单张 PNG）/ sequence（逐帧 PNG，src 用 %03d，fps 为序列帧率）。
- start/duration：在成片上的起止（秒）；in：video 从源视频第几秒开始取。
- fit：cover（铺满裁切）/ fill（拉伸到画布）/ contain（完整放下）；缺省 video = cover，image/sequence = fill
  （图层是 1080×1920 透明整画布 PNG，元素已画在最终位置，fill 直接对齐）。
- transform：静态变换；keyframes：按属性给关键帧，覆盖 transform 里的同名属性。
- 关键帧 t 为 clip 内相对秒；属性 x y（像素位移）scale scaleX scaleY rotation（度）opacity；
  ease：缺省/'ease' = smoothstep，'linear' = 线性，'hold' = 保持到下一关键帧（硬闪、数值跳变）。
- 缩放/旋转中心 = anchorX/anchorY（0–1，相对图层）。进度条填充：scaleX 关键帧 + anchorX 设在条的左端。

audio：
- 每条 {src, start, duration, in, volume, fadeIn, fadeOut}；src 可以是视频（取其音轨）。条数不限，同一 src 可拆成多条。
- gain（可选）：[[t, v], …]，t 是成片绝对秒，分段线性（第一个点之前取第一个值，最后一个点之后取最后一个值），和 volume 相乘。
  BGM、产品 UI/尾板 mp4 自带声音的闪避用一条连续 audio + gain，不拆成多段各自 fade（首尾相接各自淡变会在交界出音量凹坑）。
- 全部混音后过 alimiter，limit = "limiter"（缺省 0.84；设 0 或 null 关闭；0.89 编码后真峰值 -0.4 dBTP 不合格）。
- out 可省略，这时必须用 --out 指定。
- 原声怎么对齐、怎么删段、BGM 怎么闪避：做法见 rules/工程交付.md（timeline）和 rules/通用.md（混音与闪避）。
"""
import argparse, contextlib, json, math, os, re, subprocess, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # 同目录的 mmkit
try:
    from mmkit.heavy import heavy_lock
except Exception:                                                 # 导入失败就不锁
    heavy_lock = None

DEF_TF = {"x": 0, "y": 0, "scale": 1, "scaleX": 1, "scaleY": 1, "rotation": 0, "opacity": 1, "anchorX": .5, "anchorY": .5}


def value_at(keys, t, fb):
    if not keys: return fb
    k = sorted(keys, key=lambda a: a["t"])
    if t <= k[0]["t"]: return k[0]["v"]
    for a, b in zip(k, k[1:]):
        if a["t"] <= t <= b["t"]:
            if a.get("ease") == "hold": return a["v"]
            u = (t - a["t"]) / max(1e-9, b["t"] - a["t"])
            if a.get("ease") != "linear": u = u * u * (3 - 2 * u)
            return a["v"] + (b["v"] - a["v"]) * u
    return k[-1]["v"]


def tf_at(c, lt):
    base = {**DEF_TF, **(c.get("transform") or {})}
    kf = c.get("keyframes") or {}
    return {k: (value_at(kf[k], lt, base[k]) if k in kf else base[k]) for k in base}


def probe(src):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", src], capture_output=True, text=True)
    w, h = r.stdout.strip().split("\n")[0].split(",")[:2]
    return int(w), int(h)


class VideoReader:
    """顺序读取一个视频片段（从 in 开始，按输出 fps 取帧）。fit_to=(fit, W, H)（--draft）时解码时直接缩到画布上的大小。"""
    def __init__(self, src, t_in, fps, dur, fit_to=None):
        self.w, self.h = probe(src)
        vf = f"fps={fps}"
        if fit_to:
            self.w, self.h = fit_size(fit_to[0], self.w, self.h, fit_to[1], fit_to[2])
            vf += f",scale={self.w}:{self.h}"
        self.p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{t_in:.4f}", "-i", src, "-t", f"{dur + 1:.4f}",
                                   "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                                  stdout=subprocess.PIPE, stdin=subprocess.DEVNULL)
        self.n, self.last = -1, None

    def get(self, idx):
        while self.n < idx:
            buf = self.p.stdout.read(self.w * self.h * 4)
            if len(buf) < self.w * self.h * 4: break     # 源视频不够长：停在最后一帧
            self.last = Image.frombuffer("RGBA", (self.w, self.h), buf, "raw", "RGBA", 0, 1); self.n += 1
            if self.n >= idx: break
        return self.last

    def close(self):
        try: self.p.kill()
        except Exception: pass


def fit_size(fit, sw, sh, W, H):
    if fit == "fill": return W, H
    s = max(W / sw, H / sh) if fit == "cover" else min(W / sw, H / sh)
    return round(sw * s), round(sh * s)


def place(canvas, img, c, tf, W, H):
    fw, fh = fit_size(c.get("fit", "cover" if c["type"] == "video" else "fill"), img.width, img.height, W, H)
    if img.size != (fw, fh): img = img.resize((fw, fh), Image.LANCZOS)
    ox, oy = (W - fw) / 2, (H - fh) / 2                       # 适配后居中
    op = max(0., min(1., tf["opacity"]))
    if op <= 0: return
    sx, sy = tf["scale"] * tf["scaleX"], tf["scale"] * tf["scaleY"]
    if abs(sx) < 1e-4 or abs(sy) < 1e-4: return
    ident = abs(sx - 1) < 1e-6 and abs(sy - 1) < 1e-6 and abs(tf["rotation"]) < 1e-6
    if op < 1:
        a = np.asarray(img.getchannel("A"), dtype=np.float32) * op
        img = img.copy(); img.putalpha(Image.fromarray(a.astype(np.uint8)))
    if ident:
        dx, dy = round(ox + tf["x"]), round(oy + tf["y"])
        canvas.alpha_composite(img, (max(0, dx), max(0, dy)), (max(0, -dx), max(0, -dy)))
        return
    # 正变换：p' = A + T + R·S·(p - A)，A 为锚点（画布坐标）；PIL 需要逆变换
    ax, ay = ox + tf["anchorX"] * fw, oy + tf["anchorY"] * fh
    th = math.radians(tf["rotation"]); cs, sn = math.cos(th), math.sin(th)
    tx, ty = ax + tf["x"], ay + tf["y"]
    # 逆：p = A + S^-1 R^-1 (p' - T - A)
    a11, a12 = cs / sx, sn / sx
    a21, a22 = -sn / sy, cs / sy
    # 输入坐标是相对 img 左上角：p_img = p - (ox, oy)
    c0 = ax - ox - (a11 * tx + a12 * ty)
    c1 = ay - oy - (a21 * tx + a22 * ty)
    layer = img.transform((W, H), Image.AFFINE, (a11, a12, c0, a21, a22, c1), resample=Image.BILINEAR)
    canvas.alpha_composite(layer)


class Renderer:
    def __init__(self, tl, scale=1.0):
        self.tl = tl
        self.W, self.H = tl.get("size", [1080, 1920])
        self.fps = tl.get("fps", 30)
        self.clips = tl["clips"]
        self.readers, self.images = {}, {}
        self.scale = scale
        if scale != 1: self.W, self.H = round(self.W * scale), round(self.H * scale)   # --draft：画布按缩小后的尺寸合成

    def img(self, path):
        if path not in self.images:
            if not os.path.isfile(path): sys.exit(f"找不到图片: {path}")
            im = Image.open(path).convert("RGBA")
            if self.scale != 1: im = im.resize((max(1, round(im.width * self.scale)), max(1, round(im.height * self.scale))), Image.LANCZOS)
            self.images[path] = im
        return self.images[path]

    def frame(self, t, idx=None):
        W, H = self.W, self.H
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        for i, c in enumerate(self.clips):
            s, d = c["start"], c["duration"]
            if not (s - 1e-6 <= t < s + d - 1e-6): continue
            lt = t - s
            if c["type"] == "video":
                if idx is None:            # 静帧：单独抽一帧
                    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{c.get('in', 0) + lt * c.get('speed', 1):.4f}",
                                        "-i", c["src"], "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
                    import io; im = Image.open(io.BytesIO(r.stdout)).convert("RGBA")
                else:
                    if i not in self.readers:
                        self.readers[i] = VideoReader(c["src"], c.get("in", 0), self.fps, d,
                                                      (c.get("fit", "cover"), W, H) if self.scale != 1 else None)
                        self.readers[i].base = idx
                    im = self.readers[i].get(idx - self.readers[i].base)
                    if im is None: continue
            elif c["type"] == "sequence":
                n = int(lt * c.get("fps", self.fps) + 1e-6)
                im = self.img(c["src"] % (c.get("first", 0) + n)) if os.path.isfile(c["src"] % (c.get("first", 0) + n)) else None
                if im is None: continue
            else:
                im = self.img(c["src"])
            tf = tf_at(c, lt)
            if self.scale != 1: tf["x"], tf["y"] = tf["x"] * self.scale, tf["y"] * self.scale   # 像素位移跟着缩
            place(canvas, im, c, tf, W, H)
        for k in [k for k, c in enumerate(self.clips) if k in self.readers and t >= c["start"] + c["duration"]]:
            self.readers.pop(k).close()
        return canvas.convert("RGB")


def gain_expr(points, t0=0.0):
    """gain [[t, v], …]（成片绝对秒，分段线性）→ ffmpeg volume 表达式。表达式里的 t 是本条音频内的相对秒，t0 = 本条 start。"""
    pts = sorted(((float(t) - t0, float(v)) for t, v in points), key=lambda p: p[0])   # 只按 t 排（稳定排序），同一时刻的跳变保持原顺序
    e = f"{pts[0][1]:.6g}"
    for (ta, va), (tb, vb) in zip(pts, pts[1:]):
        if abs(vb - va) < 1e-9: continue
        if tb - ta < 1e-6: e += f"+({vb - va:.6g})*gte(t,{ta:.6g})"                          # 同一时刻两个值 = 跳变
        else: e += f"+({vb - va:.6g})*clip((t-({ta:.6g}))/{tb - ta:.6g},0,1)"
    return e


def loudness(path):
    """ebur128 peak=true 量成片：返回 (综合响度 LUFS, 真峰值 dBTP)；没有音轨或量不到返回 None。"""
    r = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0", "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    k = r.stderr.rfind("Summary:")
    if r.returncode or k < 0: return None
    s = r.stderr[k:]
    i = re.search(r"I:\s*(-?[\d.]+|-inf)\s*LUFS", s); p = re.search(r"Peak:\s*(-?[\d.]+|-inf)\s*dBFS", s)
    if not (i and p): return None
    num = lambda x: float("-inf") if x == "-inf" else float(x)
    return num(i.group(1)), num(p.group(1))


def audio_args(tl, dur):
    inputs, chains, labels = [], [], []
    for i, a in enumerate(tl.get("audio", [])):
        if not os.path.isfile(a["src"]): sys.exit(f"找不到音频: {a['src']}")
        inputs += ["-i", a["src"]]
        d = min(a["duration"], dur - a["start"])
        if d <= 0: continue
        f = [f"atrim=start={a.get('in', 0):.4f}:duration={d:.4f}", "asetpts=PTS-STARTPTS",
             "aresample=48000", "aformat=channel_layouts=stereo"]
        if a.get("fadeIn"): f.append(f"afade=t=in:d={a['fadeIn']}")
        if a.get("fadeOut"): f.append(f"afade=t=out:st={max(0, d - a['fadeOut']):.4f}:d={a['fadeOut']}")
        f.append(f"volume={a.get('volume', 1)}")
        if a.get("gain"): f += ["asetnsamples=n=256:p=0", f"volume='{gain_expr(a['gain'], a['start'])}':eval=frame"]
        ms = int(round(a["start"] * 1000)); f.append(f"adelay={ms}|{ms}")
        chains.append(f"[{i + 1}:a]{','.join(f)}[a{i}]"); labels.append(f"[a{i}]")
    if not labels: return inputs, None
    lim = tl.get("limiter", .84)
    g = ";".join(chains) + f";{''.join(labels)}amix=inputs={len(labels)}:normalize=0:dropout_transition=0,apad,atrim=duration={dur:.4f}" + \
        (f",alimiter=limit={lim}:level=false" if lim else "") + "[aout]"
    return inputs, g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline"); ap.add_argument("--draft", action="store_true")
    ap.add_argument("--still", nargs="*", type=float); ap.add_argument("--out")
    a = ap.parse_args()
    tl = json.load(open(a.timeline, encoding="utf-8"))
    R = Renderer(tl, 0.5 if a.draft and a.still is None else 1)
    dur = tl.get("duration") or max(c["start"] + c["duration"] for c in tl["clips"])
    out = a.out or tl.get("out") or sys.exit("timeline 没写 out，用 --out 指定输出路径")
    if a.draft and not a.out: out = os.path.splitext(out)[0] + "_draft.mp4"
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if a.still is not None:
        base = os.path.splitext(out)[0]
        for t in a.still:
            p = f"{base}_still_{t:.2f}.png"; R.frame(t).save(p); print(p)
        return
    W, H, fps = R.W, R.H, R.fps                                   # --draft 时已是半尺寸（540x960）
    ain, graph = audio_args(tl, dur)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", *ain]
    if graph: cmd += ["-filter_complex", graph, "-map", "0:v", "-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast" if a.draft else "medium",
            "-crf", "23" if a.draft else "17", "-pix_fmt", "yuv420p", "-t", f"{dur:.4f}", out]
    try: lock = heavy_lock("render") if heavy_lock else contextlib.nullcontext()
    except Exception: lock = contextlib.nullcontext()
    with lock:
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        n = int(round(dur * fps))
        for i in range(n):
            enc.stdin.write(R.frame(i / fps, i).tobytes())
            if i % (fps * 2) == 0: print(f"\r{i}/{n}", end="", file=sys.stderr, flush=True)
        enc.stdin.close(); enc.wait()
        for r in R.readers.values(): r.close()
    print(f"\n{out}")
    if enc.returncode or not graph: sys.exit(enc.returncode)
    lv = loudness(out)
    if lv is None: print("响度：ebur128 没量出结果，手动查"); sys.exit(0)
    print(f"响度 {lv[0]:.1f} LUFS，真峰值 {lv[1]:.1f} dBTP")
    if lv[1] > -1.0:
        print(f"真峰值 {lv[1]:.1f} dBTP 超过 -1.0：降 limiter（缺省 0.84）或降音效/BGM 音量后重出" + ("（--draft 只警告）" if a.draft else ""))
        if not a.draft: sys.exit(3)


if __name__ == "__main__":
    main()
