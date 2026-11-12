"""图层公共函数：工程 gen.py 和模块（如 modules/endcard3）共用，不再从工程代码里拷。
图层规则见 rules/工程交付.md「图层」「timeline」：1080×1920 透明整画布 PNG，元素画在最终位置，时间吸附到 1/30 s。

    import sys; sys.path.insert(0, f"{SK}/scripts")
    from mmkit.layers import Layers, kf, snap
    L = Layers(f"{P}/包装素材_版本1/layers", end=END)        # end：成片总长，音频不超过它（可后设 L.END）
    L.add_img(img, "logo", 0, 1.467, kf(opacity=[(0, 0), (0.12, 1)]), {"anchorX": 0.5})
    L.us("咔嗒清脆点击.MP3", 14.433, 0.7)                    # 用户音效收集 $USER_SFX 里的音效
    L.pointer_path([(12.7, 540, 1453), (14.433, 545, 1070)], 12.7, 14.767, clicks=[14.433])
    tl = {"size": [1080, 1920], "fps": 30, "duration": END, "clips": L.CLIPS, "audio": L.AUDIO, ...}
"""
import json, os, subprocess
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS = 1080, 1920, 30
_SK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # mm-packager 目录
US_DEFAULT = "Z:/创新事业部/AIGC项目视频组/设计师物料总库/音频/音效收集"


def snap(t):
    """吸附到 1/30 s。"""
    return round(t * FPS) / FPS


def kf(**props):
    """kf(opacity=[(t, v[, ease]), …]) → render.py 的 keyframes（t 为 clip 内相对秒）。"""
    return {k: [dict(t=round(a[0], 4), v=a[1], **({"ease": a[2]} if len(a) > 2 else {})) for a in v] for k, v in props.items()}


def dur(p):
    """媒体文件时长（秒）。"""
    if not os.path.isfile(p): raise FileNotFoundError(f"找不到文件：{p}")
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout.strip())


def _has_audio(d):
    if not d or not os.path.isdir(d): return False
    for _, _, fs in os.walk(d):
        if any(f.lower().endswith((".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac")) for f in fs): return True
    return False


def user_sfx_dir():
    """$USER_SFX（和 check_env.py 同一顺序）：环境变量 MM_USER_SFX → <工作台根>/音效收集 → Z: 设计师物料总库音效收集，取第一个里面有音效文件的。
    三处都没有就报错，不退回 $RES/sfx（那里是本地合成音效，不用）。"""
    cands = [os.environ.get("MM_USER_SFX")]
    try:
        cands.append(json.load(open(os.path.join(os.path.expanduser("~"), ".rhtv-workbench", "config.json"), encoding="utf-8")).get("root", "") + "/音效收集")
    except Exception: pass
    p = _SK.replace("\\", "/")
    if "/_系统/" in p: cands.append(p.split("/_系统/")[0] + "/音效收集")       # 安装在 <工作台根>/_系统/skills/ 下
    cands.append(US_DEFAULT)
    for d in cands:
        if _has_audio(d): return d.replace("\\", "/")
    raise FileNotFoundError("找不到用户音效收集：" + "、".join(d for d in cands if d) + " 里都没有音效文件；设 MM_USER_SFX 指向用户音效收集")


def interp(points, t):
    """points: [(t, x, y)]，按 smoothstep 插值出 t 时刻的 (x, y)（和 render.py 关键帧缺省缓动一致）。"""
    pts = sorted(points)
    if t <= pts[0][0]: return pts[0][1], pts[0][2]
    for a, b in zip(pts, pts[1:]):
        if a[0] <= t <= b[0]:
            u = (t - a[0]) / max(1e-6, b[0] - a[0]); u = u * u * (3 - 2 * u)
            return a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u
    return pts[-1][1], pts[-1][2]


def canvas():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def save(img, path):
    """存图层；同名旧图先删（rules/工程交付.md：重出图层先清旧图）。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path): os.remove(path)
    img.save(path)
    return path


def _ring(img, cx, cy, r, width, color, ss=3):
    big = Image.new("RGBA", (int(2 * r + 2 * width + 4) * ss,) * 2, (0, 0, 0, 0))
    o = (width + 2) * ss
    ImageDraw.Draw(big).ellipse((o, o, o + 2 * r * ss, o + 2 * r * ss), outline=color, width=width * ss)
    img.alpha_composite(big.resize((big.width // ss, big.height // ss), Image.LANCZOS), (int(cx - r - width - 2), int(cy - r - width - 2)))
    return img


def _disc(img, cx, cy, r, color, ss=3):
    big = Image.new("RGBA", (int(2 * r + 4) * ss,) * 2, (0, 0, 0, 0))
    ImageDraw.Draw(big).ellipse((2 * ss, 2 * ss, (2 + 2 * r) * ss, (2 + 2 * r) * ss), fill=color)
    img.alpha_composite(big.resize((big.width // ss, big.height // ss), Image.LANCZOS), (int(cx - r - 2), int(cy - r - 2)))
    return img


def pointer_img():
    """点击指针：半透明圆圈，白环 + 深色外环 + 投影，压在浅色选项胶囊上也看得清（rules/B-剧情选择.md）。画在画布中心 (540, 960)。"""
    img = canvas()
    sh = canvas(); _disc(sh, 540, 966, 60, (0, 0, 0, 110)); img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    _disc(img, 540, 960, 54, (27, 18, 21, 90))
    _ring(img, 540, 960, 57, 3, (27, 18, 21, 210))
    _ring(img, 540, 960, 52, 5, (255, 255, 255, 235))
    return img


def ripple_img():
    """点击波纹：白环 + 深色外环。画在画布中心。"""
    img = canvas()
    _ring(img, 540, 960, 55, 3, (27, 18, 21, 200))
    _ring(img, 540, 960, 52, 6, (255, 255, 255, 230))
    return img


class Layers:
    """一条片子的图层和音频清单（timeline 的 clips / audio）。CLIPS 顺序 = 叠放顺序，后加的在上层。"""

    def __init__(self, lay_dir, end=None, us_dir=None):
        self.LAY = lay_dir.replace("\\", "/")
        self.END = end                    # 成片总长：add_audio 截到这里；None = 不截
        self.US = (us_dir or user_sfx_dir()).replace("\\", "/")
        self.CLIPS, self.AUDIO = [], []
        self._n = 0
        self._pointer = None

    def save_layer(self, img, name):
        """存成 <LAY>/NNN_name.png（序号递增，qa.py 按去掉序号的 name 分组）。"""
        self._n += 1
        return save(img, f"{self.LAY}/{self._n:03d}_{name}.png")

    def add_img(self, img, name, start, end, keyframes=None, transform=None):
        """加一张图层（PIL 图或已有 PNG 路径），start/end 为成片绝对秒，吸附到 1/30；不足一帧不加。返回 clip。"""
        start, end = snap(start), snap(end)
        if end - start < 1 / FPS - 1e-4: return None
        path = img if isinstance(img, str) else self.save_layer(img, name)
        c = {"type": "image", "src": path, "start": start, "duration": round((end - start) * FPS) / FPS, "fit": "fill"}
        if keyframes: c["keyframes"] = keyframes
        if transform: c["transform"] = transform
        self.CLIPS.append(c)
        return c

    def add_audio(self, src, start, duration=None, vol=1.0, fin=0, fout=0, src_in=0):
        """加一条音频；duration 缺省 = 文件剩余长度，超过 END 的部分截掉。"""
        d = dur(src) - src_in if duration is None else duration
        if self.END is not None: d = min(d, self.END - start)
        if d <= 0.02: return None
        a = {"src": src, "start": round(start, 4), "duration": round(d, 4), "in": round(src_in, 4), "volume": vol, "fadeIn": fin, "fadeOut": fout}
        self.AUDIO.append(a)
        return a

    def us(self, name, t, vol, fout=0):
        """用户音效收集（$USER_SFX）里的音效，起点吸附到 1/30。"""
        return self.add_audio(f"{self.US}/{name}", snap(t), vol=vol, fout=fout)

    def pointer_path(self, points, start, end, clicks=()):
        """指针按 points [(t, x, y)]（成片绝对秒、画布坐标）移动，clicks [t] 处按下回弹并出波纹。"""
        if self._pointer is None:
            self._pointer = (self.save_layer(pointer_img(), "pointer"), self.save_layer(ripple_img(), "ripple"))
        pointer, ripple = self._pointer
        d = end - start
        xs = [(t - start, x - 540) for t, x, y in points]; ys = [(t - start, y - 960) for t, x, y in points]
        sc = [(0, 1.0)]
        for c in clicks:
            c -= start; sc += [(c - 0.06, 1.0), (c, 0.82), (c + 0.12, 1.0)]
        self.add_img(pointer, "pointer", start, end, kf(x=xs, y=ys, scale=sorted(sc), opacity=[(0, 0), (0.12, 1), (d - 0.1, 1), (d, 0)]))
        for c in clicks:
            x, y = interp(points, c)
            self.add_img(ripple, "ripple", c, c + 0.45, kf(scale=[(0, 0.6), (0.45, 2.1, "linear")], opacity=[(0, 0.95), (0.45, 0, "linear")]),
                         {"x": x - 540, "y": y - 960})
