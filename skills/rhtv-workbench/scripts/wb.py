#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rhtv-workbench 排版与进度脚本：把工程的素材和进度按固定格式摆到 RHTV 画布上。

所有 Agent 都通过这个脚本操作画布，保证排版一致。输出一律是 JSON（stdout），ok:false 时看 error。
用法：python wb.py <命令> [参数]，命令列表见 `python wb.py -h` 或 SKILL.md。
"""
import argparse, datetime as dt, glob, json, math, os, re, shutil, struct, subprocess, sys, tempfile, time, zipfile

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HOME = os.path.expanduser("~")
RH_HOME = os.path.join(HOME, ".runninghub-canvas")
CFG_DIR = os.path.join(HOME, ".rhtv-workbench")
CFG_PATH = os.path.join(CFG_DIR, "config.json")
LOG_DIR = os.path.join(CFG_DIR, "logs")
RUN_LOG = os.path.join(LOG_DIR, "运行日志.jsonl")
VERSION = "0.4.0"
CTX = {"cmd": None, "argv": [], "t0": time.time()}

# ---------------------------------------------------------------- 排版常量（画布像素）
LAYOUT = {
    "col_w": {"标题卡": 440, "文案": 600, "提示词": 600, "版本": 460},
    "gap_x": 80,          # 列间距
    "gap_y": 50,          # 列内上下间距
    "row_gap": 320,       # 两个工程（行）之间的距离（分组边框外）
    "media_max_h": 820,   # 图片最大高度（视频按 RHTV 原生：宽 360）
    "text_min_h": 220, "text_max_h": 1800,
    "overview_x": -1300, "overview_w": 1000,
    "row_x": 0, "row_y0": 0,
    "staging_y": -2600,   # 生成节点的临时位置（相对本行，adopt 后会摆进行里）
}
DEFAULTS = {               # 画布生成默认值（setup 时写入 config.json，可改）
    "image_model": "image-image-g-2-text-to-image",
    "video_model": "multimodal-t-video-seedance-2.5-token",
    "video_mode": "multimodal-video",
    "versions_if_unspecified": 2,
}
# 固定槽位：(槽位名, 所在列, 列内顺序)
FIXED_SLOTS = {
    "标题卡": ("标题卡", 0),
    "大纲": ("文案", 0), "全量文案": ("文案", 1), "补充文案": ("文案", 2),
    "分幕提示词": ("提示词", 0), "音色参考": ("提示词", 1), "3D参考": ("提示词", 2),
}
VERSION_SLOTS = ["人设图", "母版", "包装"]   # 每个版本一列，列内从上到下
LOCAL_ONLY = {"成品"}                         # 只放本地，不上画布
STAGES = ["01 文案", "02 提示词·音色·3D", "03 人设图", "04 母版视频", "05 包装", "06 成品交付", "07 复盘"]
LOCAL_DIRS = {"大纲": "01_文案", "全量文案": "01_文案", "补充文案": "05_包装",
              "分幕提示词": "02_提示词", "音色参考": "02_提示词", "3D参考": "02_提示词",
              "人设图": "03_人设图", "母版": "04_母版", "包装": "05_包装", "成品": "06_成品"}
NAME_RE = re.compile(r"^\d{6}-[A-Z]{2,4}-.+$")
MEDIA_EXT = {".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image",
             ".mp4": "video", ".mov": "video", ".webm": "video",
             ".mp3": "audio", ".wav": "audio", ".m4a": "audio", ".aac": "audio"}
TEXT_EXT = {".md", ".txt"}
OK_STATES = {"SUCCESS", "SUCCEEDED", "COMPLETED", "FINISHED", "DONE"}
BAD_STATES = {"FAILED", "ERROR", "REJECTED", "CANCELED", "CANCELLED", "NOT_ACCEPTED", "PARTIAL"}
WARNINGS = []


# ---------------------------------------------------------------- 基础工具
def out(obj, code=0):
    if WARNINGS:
        obj = {**obj, "warnings": WARNINGS}
    write_log(obj, code)
    print(json.dumps(obj, ensure_ascii=False, indent=1))
    sys.exit(code)


def write_log(obj, code, kind=None):
    """每次运行记一条日志（成功/失败/警告），问题排查和复盘用。日志写失败不影响主流程。"""
    if CTX["cmd"] in (None, "log", "report", "rh"):
        return
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        rec = {"time": dt.datetime.now().isoformat(timespec="seconds"), "host": os.environ.get("COMPUTERNAME") or os.uname().nodename,
               "user": os.environ.get("USERNAME") or os.environ.get("USER"), "ver": VERSION, "cmd": CTX["cmd"],
               "argv": CTX["argv"][:12], "ok": code == 0 and obj.get("ok", True) is not False,
               "code": code, "sec": round(time.time() - CTX["t0"], 1),
               "kind": kind or ("ok" if code == 0 else ("pending" if code == 4 else "error"))}
        if code:
            rec["error"] = obj.get("error")
            rec["detail"] = {k: obj[k] for k in obj if k not in ("ok", "error", "warnings")}
        if WARNINGS:
            rec["warnings"] = WARNINGS
        with open(RUN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str)[:20000] + "\n")
    except Exception:
        pass


def fail(msg, **kw):
    out({"ok": False, "error": msg, **kw}, 1)


def warn(msg):
    WARNINGS.append(msg)


def now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def load_json(p, default=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save_json(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def uuid7():
    ms = int(time.time() * 1000)
    rnd = bytearray(os.urandom(10))
    b = ms.to_bytes(6, "big") + bytes([0x70 | (rnd[0] & 0x0F), rnd[1], 0x80 | (rnd[2] & 0x3F)]) + bytes(rnd[3:10])
    h = b.hex()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def read_note(a):
    if getattr(a, "note_file", None):
        with open(a.note_file, encoding="utf-8-sig") as f:
            return f.read().strip()
    if getattr(a, "note", None) == "-":
        return sys.stdin.read().strip()
    return getattr(a, "note", None)


def rh_cmd():
    """直接调 rhTV 自带 node 运行 rhtvcli.mjs，绕开 .cmd 对参数的二次解析（长提示词、换行都安全）。"""
    mjs = os.path.join(RH_HOME, "bin", "rhtvcli.mjs")
    if os.path.exists(mjs):
        reg = load_json(os.path.join(RH_HOME, "installations.json"), {}) or {}
        for e in (reg.get("entries") or {}).values():      # rhTV 记录的 node（可能是用户自己装的 Node）
            n = e.get("node")
            if n and os.path.exists(n):
                return [n, mjs]
        nodes = sorted(glob.glob(os.path.join(RH_HOME, "runtimes", "node-*", "node.exe"))) or \
            sorted(glob.glob(os.path.join(RH_HOME, "runtimes", "node-*", "bin", "node")))
        if nodes:
            return [nodes[-1], mjs]
    for f in ("rhtvcli.cmd", "rhtvcli"):
        if os.path.exists(os.path.join(RH_HOME, "bin", f)):
            return [os.path.join(RH_HOME, "bin", f)]
    exe = shutil.which("rhtvcli")
    if exe:
        return [exe]
    fail("没找到 rhtvcli。先按 references/安装与登录.md 安装 rhTV 客户端并登录。")


def rh_env():
    return {k: v for k, v in os.environ.items() if k not in ("NODE_OPTIONS", "NODE_PATH", "NODE_DEBUG", "NODE_DEBUG_NATIVE")}


TRANSIENT = {"DEPENDENCY_UNAVAILABLE", "RATE_LIMITED", "TOO_MANY_REQUESTS", "SERVICE_UNAVAILABLE", "UPSTREAM_TIMEOUT"}


def rh(*args, check=True, timeout=900, json_flag=True, retry=False):
    """调 rhtvcli，返回解析后的 dict，附 _rc（退出码）。check=True 时失败直接 fail。
    retry=True 只用于可重复执行的操作（移动/查询/改名），遇到服务端临时错误退避重试。"""
    for i in range(5 if retry else 1):
        d = _rh_once(args, check=False, timeout=timeout, json_flag=json_flag)
        if not (retry and d.get("_rc") and err_code(d) in TRANSIENT):
            break
        time.sleep(2 * (i + 1))
    if d.get("_rc") and check:
        fail("rhtvcli 调用失败", args=[str(a) for a in args][:6], result=d)
    return d


def _rh_once(args, check=True, timeout=900, json_flag=True):
    cmd = rh_cmd() + [str(a) for a in args] + (["--json"] if json_flag else [])
    try:
        r = subprocess.run(cmd, capture_output=True, env=rh_env(), timeout=timeout)
    except subprocess.TimeoutExpired:
        d = {"error": {"code": "LOCAL_TIMEOUT", "message": f"本地等待超过 {timeout} 秒"}, "_rc": -1}
        if check:
            fail("rhtvcli 调用超时", args=[str(a) for a in args][:6], result=d)
        return d
    s = r.stdout.decode("utf-8", "replace").strip()
    try:
        d = json.loads(s) if s else {}
    except json.JSONDecodeError:
        lines = [l for l in s.splitlines() if l.strip()]
        try:
            d = json.loads(lines[-1])
        except Exception:
            d = {"raw": s}
    if not isinstance(d, dict):
        d = {"value": d}
    d["_rc"] = r.returncode
    if r.returncode and not d.get("error"):
        d["_stderr"] = r.stderr.decode("utf-8", "replace")[-1500:]
    if r.returncode and check:
        fail("rhtvcli 调用失败", args=[str(a) for a in args][:6], result=d,
             stderr=r.stderr.decode("utf-8", "replace")[-1500:])
    return d


def err_code(d):
    e = d.get("error")
    return (e.get("code") if isinstance(e, dict) else e) or ("RC_%s" % d.get("_rc") if d.get("_rc") else None)


def first(d, key):
    if isinstance(d, dict):
        if key in d and d[key]:
            return d[key]
        for v in d.values():
            r = first(v, key)
            if r:
                return r
    elif isinstance(d, list):
        for v in d:
            r = first(v, key)
            if r:
                return r
    return None


# ---------------------------------------------------------------- 配置 / 周期 / 工程
def cfg():
    c = load_json(CFG_PATH)
    if not c:
        fail("还没配置工作台。先运行：python wb.py setup --designer <设计师名字> --root <本地工作目录>")
    for k, v in (c.get("layout") or {}).items():   # 用户自定义排版参数
        if isinstance(v, dict) and isinstance(LAYOUT.get(k), dict):
            LAYOUT[k].update(v)
        elif k in LAYOUT:
            LAYOUT[k] = v
    if c.get("prefix"):
        warn(f"画布名带测试前缀「{c['prefix']}」，正式使用前运行 setup ... --prefix \"\" 清除")
    return c


def fmt_money(x):
    x = float(x or 0)
    return str(int(round(x))) if abs(x - round(x)) < 0.05 or x >= 100 else f"{x:.1f}"


def canvas_name(c, period):
    flag = "+" if period.get("incomplete") else ""
    return f'{c.get("prefix", "")}{period["key"]}-花费：{fmt_money(period.get("total", 0))}{flag}'


def designer_dir(c):
    return os.path.join(c["root"], c["designer"])


def period_dir(c, period):
    return os.path.join(designer_dir(c), period["key"])


def load_period(c, key=None):
    key = key or c.get("current_period")
    if not key:
        return None
    return load_json(os.path.join(designer_dir(c), key, "画布.json"))


def all_periods(c):
    base = designer_dir(c)
    res = []
    for key in sorted(os.listdir(base) if os.path.isdir(base) else [], reverse=True):
        p = load_json(os.path.join(base, key, "画布.json"))
        if p:
            res.append(p)
    return res


def need_period(c, key=None):
    p = load_period(c, key)
    if not p:
        fail("还没有画布。先用 new 新建一个工程，会自动建画布。" if not key else f"找不到周期 {key}")
    return p


def save_period(c, p):
    save_json(os.path.join(period_dir(c, p), "画布.json"), p)


def proj_dir(c, p, name):
    return os.path.join(period_dir(c, p), name)


def load_proj(c, p, name):
    st = load_json(os.path.join(proj_dir(c, p, name), "工作台.json"))
    if not st:
        fail(f"画布里没有工程「{name}」", 工程=list(p.get("rows", [])))
    return st


def save_proj(c, p, st):
    save_json(os.path.join(proj_dir(c, p, st["name"]), "工作台.json"), st)


def find_proj_period(c, name):
    """在所有周期里找工程（工程可能在上一个周期的画布）。"""
    for p in all_periods(c):
        if name in p.get("rows", []):
            return p
    fail(f"找不到工程「{name}」。用 python wb.py list 看现有工程。")


def canvas_url(c, cid):
    return f'https://rhtv.runninghub.{c.get("site", "cn")}/project/canvas/{cid}'


# ---------------------------------------------------------------- 尺寸
def image_size_stdlib(path):
    with open(path, "rb") as f:
        head = f.read(64 * 1024)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    if head[:2] == b"\xff\xd8":
        i = 2
        while i < len(head) - 9:
            if head[i] != 0xFF:
                i += 1
                continue
            m = head[i + 1]
            if m in (0xC0, 0xC1, 0xC2, 0xC3):
                h, w = struct.unpack(">HH", head[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", head[i + 2:i + 4])[0]
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        if head[12:16] == b"VP8X":
            return 1 + int.from_bytes(head[24:27], "little"), 1 + int.from_bytes(head[27:30], "little")
        if head[12:16] == b"VP8 ":
            w, h = struct.unpack("<HH", head[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if head[12:16] == b"VP8L":
            b = int.from_bytes(head[21:25], "little")
            return 1 + (b & 0x3FFF), 1 + ((b >> 14) & 0x3FFF)
    return None


def media_size(path, kind):
    if kind == "audio":
        return None
    if kind == "image":
        try:
            wh = image_size_stdlib(path)
            if wh and all(wh):
                return wh
        except Exception:
            pass
        try:
            from PIL import Image
            with Image.open(path) as im:
                return im.size
        except Exception:
            warn(f"读不到图片尺寸：{os.path.basename(path)}，按 16:9 摆放")
            return (1920, 1080)
    fp = shutil.which("ffprobe")
    if fp:
        try:
            r = subprocess.run([fp, "-v", "error", "-select_streams", "v:0", "-show_entries",
                                "stream=width,height:stream_tags=rotate", "-of", "json", path], capture_output=True)
            s = json.loads(r.stdout or b"{}").get("streams", [{}])[0]
            w, h = s.get("width"), s.get("height")
            if str(s.get("tags", {}).get("rotate", "0")) in ("90", "270"):
                w, h = h, w
            if w and h:
                return w, h
        except Exception:
            pass
    return None   # 视频读不到时，之后以 RHTV 处理后的尺寸为准


def fit(col_w, wh, kind=None):
    if kind == "audio":
        return col_w, 160
    if not wh:
        return (360, 640) if kind == "video" else (col_w, 160)
    w, h = wh
    a = w / h
    if kind == "video":
        # RHTV 处理完视频后会把节点改回原生尺寸：宽 360、高按比例，这里直接对齐它
        return 360, int(round(360 / a))
    W = col_w
    H = W / a
    if H > LAYOUT["media_max_h"]:
        H = LAYOUT["media_max_h"]
        W = H * a
    return int(W), int(H)


def text_h(text, w):
    cpl = max(8, int((w - 40) / 15))
    lines = 0
    for para in text.split("\n"):
        width = sum(2 if ord(ch) > 0x2E80 else 1 for ch in para) / 2
        lines += max(1, math.ceil(width / cpl))
    return int(min(LAYOUT["text_max_h"], max(LAYOUT["text_min_h"], 70 + lines * 24)))


def col_width(col):
    return LAYOUT["col_w"]["版本" if col.startswith("版本") else col]


# ---------------------------------------------------------------- 画布状态同步（自愈）
def canvas_nodes(p):
    actual, cursor = {}, None
    while True:
        args = ["node", "list", "-p", p["canvas_id"], "--limit", 200]
        if cursor:
            args += ["--cursor", cursor]
        d = rh(*args, retry=True)
        for n in d.get("items", []):
            actual[n["nodeKey"]] = n
        cursor = (d.get("pagination") or {}).get("nextCursor")
        if not cursor:
            break
    return actual


def canvas_groups(p):
    d = rh("group", "list", "-p", p["canvas_id"], "--limit", 200, retry=True)
    return {g.get("groupNodeKey") or g.get("nodeKey"): g for g in d.get("items", []) if isinstance(g, dict)}


def sync_state(c, p, names=None):
    """以画布为准：清掉已被删的节点/分组，视频尺寸跟随 RHTV。返回被清掉的槽位。"""
    nodes = canvas_nodes(p)
    groups = canvas_groups(p)
    dropped = []
    if p.get("overview") and p["overview"] not in nodes:
        p["overview"] = None
    for name in (names or p["rows"]):
        st = load_json(os.path.join(proj_dir(c, p, name), "工作台.json"))
        if not st:
            continue
        for k in list(st["slots"]):
            v = st["slots"][k]
            n = nodes.get(v.get("node"))
            if not n:
                dropped.append(f"{name}/{k}")
                del st["slots"][k]
                continue
            sz = n["data"].get("size") or {}
            pos = n["data"].get("position") or {}
            if v.get("kind") == "video" and sz.get("width"):
                v["w"], v["h"] = fit(0, (sz["width"], sz["height"]), "video")
            # 记下画布上的实际位置/尺寸：重排时只移动不在标准位置的节点
            v["x"], v["y"] = pos.get("x"), pos.get("y")
            v["placed"] = True
            if v.get("kind") != "video" and sz.get("width") and v.get("kind") != "text":
                v["_aw"], v["_ah"] = sz["width"], sz["height"]
        if st.get("group") and st["group"] not in groups:
            st["group"] = None
        save_proj(c, p, st)
    return dropped


# ---------------------------------------------------------------- 排版
def slot_col(slot, version=None):
    if slot in FIXED_SLOTS:
        return FIXED_SLOTS[slot]
    if slot in VERSION_SLOTS:
        return (f"版本{version}", VERSION_SLOTS.index(slot))
    fail(f"未知槽位「{slot}」", 可用=list(FIXED_SLOTS) + VERSION_SLOTS + sorted(LOCAL_ONLY))


def slot_key(slot, version=None):
    return f"v{version}·{slot}" if slot in VERSION_SLOTS else slot


def versions_of(st):
    return sorted({int(v["version"]) for v in st["slots"].values() if v.get("version") and v["slot"] in VERSION_SLOTS})


def columns(st):
    return ["标题卡", "文案", "提示词"] + [f"版本{v}" for v in versions_of(st)]


def compute_layout(st, row_y):
    L = LAYOUT
    x = L["row_x"]
    pos = {}
    bottom = row_y
    for col in columns(st):
        cw = col_width(col)
        items = []
        for k, v in st["slots"].items():
            c_, order = slot_col(v["slot"], v.get("version"))
            if c_ == col:
                items.append((order, k, v))
        items.sort()
        y = row_y
        maxw = 0
        for _, k, v in items:
            pos[k] = (x, y, v["w"], v["h"])
            y += v["h"] + L["gap_y"]
            maxw = max(maxw, v["w"])
        bottom = max(bottom, y - L["gap_y"])
        x += max(cw, maxw) + L["gap_x"]
    return pos, bottom


def relayout_period(c, p, force=False):
    """按顺序重排所有行；行高变化时下面的行整体下移。"""
    y = LAYOUT["row_y0"]
    moved = 0
    for name in p["rows"]:
        st = load_json(os.path.join(proj_dir(c, p, name), "工作台.json"))
        if not st:
            continue
        pos, bottom = compute_layout(st, y)
        changed = False
        for k, (x0, y0, w, h) in pos.items():
            v = st["slots"][k]
            if not v.get("node"):
                continue
            cur = [v.get("x"), v.get("y"), v.get("_aw", v.get("w")), v.get("_ah", v.get("h")), v.get("placed")]
            if force or [round(float(z), 1) if isinstance(z, (int, float)) else z for z in cur] != [x0, y0, w, h, True]:
                d = rh("node", "update", "id:" + v["node"], "-p", p["canvas_id"], "--x", x0, "--y", y0,
                       "--width", w, "--height", h, check=False, retry=True)
                if err_code(d) == "ENTITY_NOT_FOUND":
                    del st["slots"][k]
                    warn(f"{name}/{k} 的节点已不在画布上，已从记录中移除")
                    continue
                if d.get("_rc"):
                    warn(f"{name}/{k} 移动失败：{err_code(d)}")
                    continue
                v.update(x=x0, y=y0, w=w, h=h, placed=True)
                v.pop("_aw", None); v.pop("_ah", None)
                moved += 1
                changed = True
        st["row_y"] = y
        if changed or force or not st.get("group"):
            refit_group(p, st)
        save_proj(c, p, st)
        y = bottom + 60 + LAYOUT["row_gap"] + 90   # 分组下边框 60、上边框 90
    return moved


def refit_group(p, st):
    nodes = [v["node"] for v in st["slots"].values() if v.get("node")]
    if not nodes:
        return
    if st.get("group"):
        args = ["group", "update", "id:" + st["group"], "-p", p["canvas_id"]]
        for n in nodes:
            args += ["--node", "id:" + n]
        d = rh(*args, check=False, retry=True)
        if not d.get("_rc"):
            return
        st["group"] = None          # 分组已失效（被解散/删除），重建
    args = ["group", "create", st["name"], "-p", p["canvas_id"]]
    for n in nodes:
        args += ["--node", "id:" + n]
    d = rh(*args, check=False)
    st["group"] = first(d, "groupNodeKey") or first(d, "newNodeKey")
    if not st["group"]:
        warn(f"{st['name']} 的分组没建成：{err_code(d)}")


# ---------------------------------------------------------------- 节点与文字卡
def node_name(st, slot, version, review=False, rejected=False):
    tag = f"v{version}·{slot}" if version else slot
    lab = st.get("labels", {}).get(str(version)) if version else None
    if lab:
        tag += f"·{lab}"
    s = f"{st['name']}｜{tag}"
    if rejected:
        s += "【打回】"
    elif review:
        s += "【待审核】"
    return s


def text_args(text):
    return ["-u", "content=" + json.dumps([text], ensure_ascii=False)]


def put_text_node(c, p, st, slot, text, version=None, review=False):
    k = slot_key(slot, version)
    col, _ = slot_col(slot, version)
    w = col_width(col)
    h = text_h(text, w)
    name = node_name(st, slot, version, review)
    old = st["slots"].get(k)
    if old and old.get("node") and old.get("kind") == "text":
        d = rh("node", "update", "id:" + old["node"], "-p", p["canvas_id"], "--name", name,
               *text_args(text), "--height", h, check=False)
        if not d.get("_rc"):
            old.update(h=h, name=name, review=review, rejected=False, updated=now())
            return old
        if err_code(d) != "ENTITY_NOT_FOUND":
            fail("更新文字节点失败", slot=k, result=d)
        old = None   # 节点已被删，重建
    d = rh("node", "create", name, "-p", p["canvas_id"], "-t", "text", *text_args(text),
           "--x", LAYOUT["row_x"], "--y", st.get("row_y", 0), "--width", w, "--height", h)
    nk = first(d, "nodeKey")
    st["slots"][k] = {"slot": slot, "version": version, "node": nk, "kind": "text", "w": w, "h": h,
                      "name": name, "review": review, "rejected": False, "updated": now()}
    save_proj(c, p, st)                     # 先记新节点，再删旧节点
    if old and old.get("node"):
        rh("node", "delete", "id:" + old["node"], "-p", p["canvas_id"], check=False)
    return st["slots"][k]


def title_text(st):
    rnd = f"（第{st['round']}轮）" if st.get("round", 1) > 1 else ""
    vs = versions_of(st)
    labels = [f"v{v}{('·' + st.get('labels', {}).get(str(v))) if st.get('labels', {}).get(str(v)) else ''}" for v in vs]
    lines = [st["name"], "", f"进度：{st.get('stage', '')} · {st.get('state', '')}{rnd}"]
    if st.get("skipped"):
        lines.append("跳过：" + "、".join(st["skipped"]))
    waiting = [k for k, v in st["slots"].items() if v.get("review") and not v.get("rejected")]
    rejected = [k for k, v in st["slots"].items() if v.get("rejected")]
    if waiting:
        lines.append("待审核：" + "、".join(waiting))
    if rejected:
        lines.append("打回待改：" + "、".join(rejected))
    lines += [f"版本：{len(vs)} 个" + (f"（{' / '.join(labels)}）" if labels else ""),
              f"花费：{fmt_money(st.get('cost', 0))} 元" + ("（含未报价项）" if st.get("incomplete") else ""),
              f"更新：{now()}"]
    if st.get("note"):
        lines += ["", "最近意见：" + st["note"]]
    return "\n".join(lines)


def refresh_title(c, p, st):
    put_text_node(c, p, st, "标题卡", title_text(st))


def refresh_overview(c, p):
    lines = [f"工程总览 · {p['key']}", f"设计师：{c['designer']}　花费合计：{fmt_money(p.get('total', 0))} 元", ""]
    for name in p["rows"]:
        st = load_json(os.path.join(proj_dir(c, p, name), "工作台.json")) or {}
        lines.append(f"{name}　{st.get('stage', '')} · {st.get('state', '')}　{fmt_money(st.get('cost', 0))} 元")
    text = "\n".join(lines)
    h = text_h(text, LAYOUT["overview_w"])
    if p.get("overview"):
        d = rh("node", "update", "id:" + p["overview"], "-p", p["canvas_id"], *text_args(text), "--height", h, check=False)
        if not d.get("_rc"):
            return
    d = rh("node", "create", "工作台总览", "-p", p["canvas_id"], "-t", "text", *text_args(text),
           "--x", LAYOUT["overview_x"], "--y", LAYOUT["row_y0"], "--width", LAYOUT["overview_w"], "--height", h)
    p["overview"] = first(d, "nodeKey")


def sync_canvas_name(c, p):
    name = canvas_name(c, p)
    if p.get("name") != name:
        rh("project", "update", p["canvas_id"], "--name", name)
        p["name"] = name


def recompute_state(st):
    """按槽位的审核标记推出工程状态。"""
    if any(v.get("rejected") for v in st["slots"].values()):
        return "打回"
    if any(v.get("review") for v in st["slots"].values()):
        return "待审核"
    return None


def commit(c, p, st, title=True):
    """保存工程 → 重排 → 刷新标题卡和总览。所有改动最后都走这里。"""
    save_proj(c, p, st)
    relayout_period(c, p)
    st = load_proj(c, p, st["name"])
    if title:
        refresh_title(c, p, st)
        save_proj(c, p, st)
        relayout_period(c, p)
    refresh_overview(c, p)
    save_period(c, p)
    return st


# ---------------------------------------------------------------- 周期与画布
def ensure_period(c):
    today = dt.date.today()
    p = load_period(c)
    if p and today < dt.date.fromisoformat(p["end"]):      # 结束日当天属于下一个周期
        return p
    start = today
    end = start + dt.timedelta(days=int(c.get("period_days", 28)))
    key = f"{start:%y%m%d}-{end:%y%m%d}"
    old = load_period(c, key)
    if old:
        c["current_period"] = key
        save_json(CFG_PATH, c)
        return old
    p = {"key": key, "start": start.isoformat(), "end": end.isoformat(), "total": 0, "ledger": [], "rows": []}
    name = canvas_name(c, p)
    d = rh("project", "create", name, "--folder-id", c["folder_id"], "-t", "0")
    p["canvas_id"] = first(d, "projectUuid") or first(d, "id")
    p["name"] = name
    p["url"] = canvas_url(c, p["canvas_id"])
    c["current_period"] = key
    save_json(CFG_PATH, c)
    save_period(c, p)
    refresh_overview(c, p)
    save_period(c, p)
    return p


# ---------------------------------------------------------------- 命令：配置与查看
def check_env():
    res = {"rhtvcli": " ".join(rh_cmd())}
    acc = rh("account", check=False)
    data = acc.get("data", acc)
    perms = data.get("allowedActions") or []
    need = ["canvas:read", "canvas:edit", "canvas:create", "canvas:run"]
    res["login"] = all(x in perms for x in need)
    res["missing_permissions"] = [x for x in need if x not in perms]
    res["site"] = data.get("site")
    res["ffprobe"] = bool(shutil.which("ffprobe"))
    try:
        import PIL  # noqa
        res["pillow"] = True
    except Exception:
        res["pillow"] = False
    if not res["ffprobe"]:
        warn("没装 ffprobe：视频尺寸改用 RHTV 处理后的尺寸（可用）。")
    if not res["pillow"]:
        warn("没装 Pillow：preview 不可用，其余功能可用（pip install pillow）。")
    return res, data


def cmd_check(a):
    res, _ = check_env()
    c = load_json(CFG_PATH)
    res["configured"] = bool(c)
    if c:
        cfg()
    ok = res["login"]
    out({"ok": ok, **res, **({} if ok else {"error": "rhtvcli 没登录或权限不全，按 references/安装与登录.md 登录"})}, 0 if ok else 1)


def cmd_setup(a):
    res, data = check_env()
    if not res["login"]:
        fail("rhtvcli 没登录或权限不够。按 references/安装与登录.md 登录后重试。", check=res)
    c = load_json(CFG_PATH, {}) or {}
    c.update(designer=a.designer, root=os.path.abspath(a.root), site=data.get("site", "cn"))
    if a.prefix is not None:
        c["prefix"] = a.prefix
    if a.days:
        c["period_days"] = a.days
    c.setdefault("defaults", dict(DEFAULTS))
    if not c.get("folder_id") or a.designer != c.get("folder_name"):
        fid, page = None, 1
        while page and not fid:
            d = rh("workspace", "list", "-p", page, "-s", 50, "-t", 0, "--folder-id", 0)
            for it in d.get("folders") or d.get("items") or []:
                if it.get("type") == "FOLDER" and it.get("name") == a.designer:
                    fid = it["id"]
                    break
            page = (d.get("pagination") or {}).get("nextPage")
        if not fid:
            d = rh("workspace", "create", a.designer, "-t", 0, "--folder-id", 0)
            fid = first(d, "workspaceId") or first(d, "folderId") or first(d, "id")
            if not fid:
                fail("在 RHTV 建设计师文件夹失败（没拿到文件夹 ID）", result=d)
        c["folder_id"], c["folder_name"] = fid, a.designer
    os.makedirs(designer_dir(c), exist_ok=True)
    save_json(CFG_PATH, c)
    cfg()
    p = load_period(c)
    out({"ok": True, "config": c, "config_path": CFG_PATH, "check": res,
         "current_canvas": p and {"name": p["name"], "url": p["url"], "end": p["end"]}})


def proj_summary(c, p, name):
    st = load_json(os.path.join(proj_dir(c, p, name), "工作台.json")) or {}
    return {"name": name, "stage": st.get("stage"), "state": st.get("state"), "round": st.get("round"),
            "cost": st.get("cost"), "canvas_id": p["canvas_id"], "canvas": p["name"], "url": p["url"],
            "period": p["key"], "versions": versions_of(st) if st else [],
            "slots": {k: {"node": v.get("node"), "kind": v.get("kind"), "review": v.get("review"),
                          "rejected": v.get("rejected")} for k, v in st.get("slots", {}).items()},
            "local": st.get("local")}


def cmd_list(a):
    c = cfg()
    cur = load_period(c)
    rows = []
    for p in all_periods(c):
        for name in p.get("rows", []):
            s = proj_summary(c, p, name)
            s["current_canvas"] = bool(cur and p["key"] == cur["key"])
            if s["current_canvas"] or s["state"] != "已交付" or a.all:
                rows.append(s)
    out({"ok": True, "designer": c["designer"], "canvas": cur and cur["name"], "canvas_id": cur and cur["canvas_id"],
         "url": cur and cur["url"], "period_end": cur and cur["end"], "defaults": c.get("defaults", DEFAULTS),
         "unfinished": [r["name"] for r in rows if r["state"] != "已交付"], "projects": rows})


# ---------------------------------------------------------------- 命令：工程
def cmd_new(a):
    c = cfg()
    if not NAME_RE.match(a.name):
        fail("工程名格式应为 日期-地区-名称，例如 261110-JP-追放された女騎士")
    cur = load_period(c)
    for q in all_periods(c):
        if a.name in q.get("rows", []) and (not cur or q["key"] != cur["key"]):
            fail(f"工程「{a.name}」在画布 {q['name']} 里已经存在", url=q["url"])
    p = ensure_period(c)
    d = proj_dir(c, p, a.name)
    st = load_json(os.path.join(d, "工作台.json"))
    resumed = bool(st)
    if a.name in p["rows"] and st and st["slots"].get("标题卡") and st.get("group"):
        fail(f"工程「{a.name}」已经在画布上", url=p["url"])
    for sub in sorted(set(LOCAL_DIRS.values())):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    if not os.path.exists(os.path.join(d, "修改记录.md")):
        with open(os.path.join(d, "修改记录.md"), "w", encoding="utf-8") as f:
            f.write(f"# {a.name} 修改记录\n\n")
    if not st:
        start = 0
        if a.start:
            start = next((i for i, s in enumerate(STAGES) if s.startswith(a.start.zfill(2))), 0)
        st = {"name": a.name, "created": now(), "slots": {}, "labels": {}, "cost": 0, "round": 1,
              "stage": STAGES[start], "state": "进行中", "skipped": STAGES[:start], "local": d}
    if a.name not in p["rows"]:
        p["rows"].append(a.name)
    save_period(c, p)
    st = commit(c, p, st)
    out({"ok": True, "project": a.name, "resumed": resumed, "stage": st["stage"], "canvas": p["name"],
         "canvas_id": p["canvas_id"], "url": p["url"], "local": d})


def check_slot_args(a):
    if a.slot in VERSION_SLOTS and not a.version:
        fail(f"「{a.slot}」要带 --version N（每个人设图一个版本）")
    if a.slot not in VERSION_SLOTS and (a.version or a.label):
        fail(f"「{a.slot}」是固定槽位，不能带 --version / --label")


def archive(st, slot, src, version=None, new_name=None):
    dst_dir = os.path.join(st["local"], LOCAL_DIRS.get(slot, "其他"))
    os.makedirs(dst_dir, exist_ok=True)
    base = new_name or ((f"v{version}_" if version else "") + os.path.basename(src))
    dst = os.path.join(dst_dir, base)
    if os.path.abspath(dst) != os.path.abspath(src):
        shutil.copy2(src, dst)
    return dst


def cmd_put(a):
    c = cfg()
    p = find_proj_period(c, a.name)
    st = load_proj(c, p, a.name)
    src = os.path.abspath(a.file)
    if not os.path.isfile(src):
        fail(f"文件不存在：{src}")
    if a.slot in LOCAL_ONLY:
        dst = archive(st, a.slot, src)
        out({"ok": True, "project": a.name, "slot": a.slot, "local": dst, "canvas": False})
    check_slot_args(a)
    slot_col(a.slot, a.version)
    ext = os.path.splitext(src)[1].lower()
    if ext not in TEXT_EXT and ext not in MEDIA_EXT:
        fail(f"不支持的文件类型 {ext}")
    sync_state(c, p, [a.name])
    st = load_proj(c, p, a.name)
    if a.label and a.version:
        st.setdefault("labels", {})[str(a.version)] = a.label
    k = slot_key(a.slot, a.version)
    if ext in TEXT_EXT:
        with open(src, encoding="utf-8-sig") as f:
            text = f.read().strip()
        put_text_node(c, p, st, a.slot, text, a.version, a.review)
    else:
        kind = MEDIA_EXT[ext]
        col, _ = slot_col(a.slot, a.version)
        w, h = fit(col_width(col), media_size(src, kind), kind)
        old = st["slots"].get(k)
        name = node_name(st, a.slot, a.version, a.review)
        args = ["upload", name, "-p", p["canvas_id"], "-f", src, "-t", kind,
                "--x", LAYOUT["row_x"], "--y", st.get("row_y", 0)]
        if st.get("group"):
            args += ["-g", "id:" + st["group"]]
        d = rh(*args, timeout=3600)
        nk = first(d, "nodeKey")
        if not nk:
            fail("上传结果里没有节点", result=d)
        rh("node", "update", "id:" + nk, "-p", p["canvas_id"], "--width", w, "--height", h, check=False)
        st["slots"][k] = {"slot": a.slot, "version": a.version, "node": nk, "kind": kind, "w": w, "h": h,
                          "name": name, "review": a.review, "rejected": False, "updated": now()}
        save_proj(c, p, st)
        if old and old.get("node") and old["node"] != nk:
            rh("node", "delete", "id:" + old["node"], "-p", p["canvas_id"], check=False)
    st["slots"][k]["file"] = archive(st, a.slot, src, a.version)
    if a.review:
        st["state"] = "待审核"
    st = commit(c, p, st)
    out({"ok": True, "project": a.name, "slot": k, "node": st["slots"][k]["node"],
         "local": st["slots"][k]["file"], "url": p["url"]})


def download_node(p, nk, dst_dir, base):
    """下载节点产物到 dst_dir，解开 ZIP，按 base 命名。返回文件列表。"""
    tmp = tempfile.mkdtemp(prefix="wb_dl_")
    try:
        d = rh("download", "--node", "id:" + nk, "-p", p["canvas_id"], "--out", tmp, check=False, timeout=1800)
        if d.get("_rc"):
            fail("下载节点产物失败", node=nk, result=d)
        for root, _, fs in os.walk(tmp):
            for f in fs:
                path = os.path.join(root, f)
                if f.lower().endswith(".zip"):
                    with zipfile.ZipFile(path) as z:
                        z.extractall(os.path.join(tmp, "_unzip"))
                    os.remove(path)
        files = []
        for root, _, fs in os.walk(tmp):
            for f in sorted(fs):
                if os.path.splitext(f)[1].lower() in MEDIA_EXT:
                    files.append(os.path.join(root, f))
        if not files:
            fail("下载结果里没有媒体文件", node=nk, result=d)
        os.makedirs(dst_dir, exist_ok=True)
        res = []
        for i, f in enumerate(files):
            name = base + ("" if len(files) == 1 else f"_{i + 1}") + os.path.splitext(f)[1].lower()
            dst = os.path.join(dst_dir, name)
            if os.path.exists(dst):
                old_dir = os.path.join(dst_dir, "_旧版")
                os.makedirs(old_dir, exist_ok=True)
                shutil.move(dst, os.path.join(old_dir, dt.datetime.now().strftime("%m%d%H%M_") + name))
            shutil.move(f, dst)
            res.append(dst)
        return res
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_adopt(a):
    """把画布上已生成的节点（如在画布里跑出的人设图、母版）收进工程的槽位，并下载归档。"""
    c = cfg()
    p = find_proj_period(c, a.name)
    check_slot_args(a)
    sync_state(c, p, [a.name])
    st = load_proj(c, p, a.name)
    if a.label and a.version:
        st.setdefault("labels", {})[str(a.version)] = a.label
    k = slot_key(a.slot, a.version)
    sel = a.node if ":" in a.node else "id:" + a.node
    d = rh("node", "get", sel, "-p", p["canvas_id"], "--include", "outputs")
    item = (d.get("items") or [d])[0]
    nk, kind = item.get("nodeKey"), item.get("type")
    data = item.get("data") or {}
    if kind in ("image", "video", "audio") and not data.get("outputs") and data.get("status") != "finished":
        fail("这个节点还没有产物（还没跑完或失败），先 run / wait 成功再 adopt", node=nk, status=data.get("status"))
    files = []
    if not a.no_download and kind in ("image", "video", "audio"):
        dst_dir = os.path.join(st["local"], LOCAL_DIRS.get(a.slot, "其他"))
        files = download_node(p, nk, dst_dir, f"v{a.version}_{a.slot}" if a.version else a.slot)
    sz = data.get("size") or {}
    wh = (sz.get("width"), sz.get("height")) if sz.get("width") else None
    if files and kind == "image":
        wh = media_size(files[0], "image") or wh
    w, h = fit(col_width(slot_col(a.slot, a.version)[0]), wh, kind)
    old = st["slots"].get(k)
    name = node_name(st, a.slot, a.version, a.review)
    rh("node", "update", "id:" + nk, "-p", p["canvas_id"], "--name", name, "--width", w, "--height", h)
    st["slots"][k] = {"slot": a.slot, "version": a.version, "node": nk, "kind": kind, "w": w, "h": h,
                      "name": name, "review": a.review, "rejected": False, "updated": now(),
                      "file": files[0] if files else None}
    st["pending_nodes"] = [n for n in st.get("pending_nodes", []) if n != nk]
    save_proj(c, p, st)
    if old and old.get("node") and old["node"] != nk:
        rh("node", "delete", "id:" + old["node"], "-p", p["canvas_id"], check=False)
    if a.review:
        st["state"] = "待审核"
    st = commit(c, p, st)
    out({"ok": True, "project": a.name, "slot": k, "node": nk, "local": files, "url": p["url"]})


def cmd_remove(a):
    """删掉工程里的槽位（或整个版本 vN），画布节点和记录一起删；本地文件移到 _旧版。"""
    c = cfg()
    p = find_proj_period(c, a.name)
    st = load_proj(c, p, a.name)
    keys = []
    for t in a.targets:
        t = norm_key(t)
        m = re.fullmatch(r"v(\d+)", t)
        if m:
            keys += [k for k, v in st["slots"].items() if str(v.get("version")) == m.group(1)]
            st.get("labels", {}).pop(m.group(1), None)
        elif t in st["slots"] and t != "标题卡":
            keys.append(t)
        else:
            fail(f"没有槽位「{t}」", 可用=[k for k in st["slots"] if k != "标题卡"] + [f"v{v}" for v in versions_of(st)])
    for k in dict.fromkeys(keys):
        v = st["slots"].pop(k)
        if v.get("node"):
            rh("node", "delete", "id:" + v["node"], "-p", p["canvas_id"], check=False)
        f = v.get("file")
        if f and os.path.exists(f) and not a.keep_local:
            old_dir = os.path.join(os.path.dirname(f), "_旧版")
            os.makedirs(old_dir, exist_ok=True)
            shutil.move(f, os.path.join(old_dir, os.path.basename(f)))
    log(st, f"移除：{'、'.join(dict.fromkeys(keys))}")
    st = commit(c, p, st)
    out({"ok": True, "project": a.name, "removed": list(dict.fromkeys(keys))})


def cmd_stage(a):
    c = cfg()
    p = find_proj_period(c, a.name)
    st = load_proj(c, p, a.name)
    stage = next((s for s in STAGES if s.startswith(a.stage.zfill(2)) or a.stage in s), None)
    if not stage:
        fail("阶段不存在", 可用=STAGES)
    if stage != st.get("stage"):
        st["round"] = 1
        st["note"] = ""
    st["stage"], st["state"] = stage, a.state
    note = read_note(a)
    if note:
        st["note"] = note
    commit(c, p, st)
    out({"ok": True, "project": a.name, "stage": stage, "state": a.state})


def norm_key(t):
    t = t.strip()
    t = re.sub(r"\s*[-:：.．· ]\s*", "·", t)
    if re.match(r"^[vV]\d+", t):
        t = re.sub(r"^[vV](\d+)·?", r"v\1·", t)
    return t.rstrip("·")


def pick_keys(st, slots, version):
    if not slots:
        return [k for k, v in st["slots"].items() if v.get("review") and not v.get("rejected")]
    keys = []
    for s in slots:
        s = norm_key(s)
        if version and s in VERSION_SLOTS:
            s = f"v{version}·{s}"
        if s in st["slots"]:
            keys.append(s)
            continue
        m = re.fullmatch(r"v(\d+)", s)
        if m:
            hit = [k for k, v in st["slots"].items() if str(v.get("version")) == m.group(1)]
        else:
            hit = [k for k, v in st["slots"].items() if v["slot"] == s]
            if len(hit) > 1:
                fail(f"「{s}」有多个版本，写成 v<N>·{s}、v<N>（整列）或加 --version N", 可用=list(st["slots"]))
        if not hit:
            fail(f"没有槽位「{s}」", 可用=list(st["slots"]))
        keys += hit
    return list(dict.fromkeys(keys))


def set_marks(p, st, keys, review=False, rejected=False):
    for k in keys:
        v = st["slots"].get(k)
        if not v or not v.get("node"):
            continue
        name = node_name(st, v["slot"], v.get("version"), review, rejected)
        if name != v.get("name"):
            rh("node", "update", "id:" + v["node"], "-p", p["canvas_id"], "--name", name, check=False)
            v["name"] = name
        v["review"] = review
        v["rejected"] = rejected


def cmd_approve(a):
    c = cfg()
    p = find_proj_period(c, a.name)
    sync_state(c, p, [a.name])
    st = load_proj(c, p, a.name)
    keys = pick_keys(st, a.slots, a.version)
    set_marks(p, st, keys)
    log(st, f"通过（{st['stage']}）：{'、'.join(keys) or '-'}")
    left = recompute_state(st)
    if left:
        st["state"] = left
    else:
        st["state"], st["note"], st["round"] = "通过", "", 1
    commit(c, p, st)
    out({"ok": True, "project": a.name, "approved": keys, "stage": st["stage"], "state": st["state"],
         "still_rejected": [k for k, v in st["slots"].items() if v.get("rejected")],
         "still_waiting": [k for k, v in st["slots"].items() if v.get("review") and not v.get("rejected")]})


def cmd_reject(a):
    c = cfg()
    p = find_proj_period(c, a.name)
    sync_state(c, p, [a.name])
    st = load_proj(c, p, a.name)
    note = read_note(a)
    if not note:
        fail("打回要带用户原话：--note \"...\" 或 --note-file 文件")
    keys = pick_keys(st, a.slots, a.version)
    set_marks(p, st, keys, rejected=True)
    st["round"] = st.get("round", 1) + 1
    st["state"], st["note"] = "打回", note
    log(st, f"打回（{st['stage']}，第{st['round'] - 1}轮）：{'、'.join(keys) or '-'}\n  原话：{note}")
    commit(c, p, st)
    out({"ok": True, "project": a.name, "rejected": keys, "round": st["round"]})


def log(st, text):
    with open(os.path.join(st["local"], "修改记录.md"), "a", encoding="utf-8") as f:
        f.write(f"- {now()} {text}\n")


# ---------------------------------------------------------------- 命令：生成与花费
def cmd_gen(a):
    """在画布上建一个生成节点（提示词从文件读，避免命令行截断）。返回节点 ID，接着用 run。"""
    c = cfg()
    p = find_proj_period(c, a.name)
    st = load_proj(c, p, a.name)
    dfl = c.get("defaults", DEFAULTS)
    model = a.model or (dfl.get("video_model") if a.type == "video" else dfl.get("image_model"))
    with open(a.prompt_file, encoding="utf-8-sig") as f:
        prompt = f.read().strip()
    name = f"{a.name}｜生成·{a.tag or a.type}"
    x = LAYOUT["row_x"] + len(st.get("pending_nodes", [])) * 500
    args = ["node", "create", name, "-p", p["canvas_id"], "-t", a.type, "--model", model,
            "--prompt", prompt, "--x", x, "--y", LAYOUT["staging_y"] + st.get("row_y", 0)]
    mode = a.mode or (dfl.get("video_mode") if a.type == "video" and not a.model else None)
    if mode:
        args += ["--mode", mode]
    for s in a.set or []:
        args += ["-s", s]
    for src in a.left or []:
        k = norm_key(src)
        if k in st["slots"]:
            args += ["--left", "id:" + st["slots"][k]["node"]]
        else:
            args += ["--left", src if ":" in src else "id:" + src]
    d = rh(*args)
    nk = first(d, "nodeKey")
    st.setdefault("pending_nodes", []).append(nk)
    save_proj(c, p, st)
    chk = rh("node", "get", "id:" + nk, "-p", p["canvas_id"], "--include", "params", check=False)
    saved = first(chk, "prompt") or ""
    if saved and len(saved) < len(prompt) * 0.95:
        warn(f"画布上保存的提示词（{len(saved)} 字）比文件（{len(prompt)} 字）短，请核对")
    out({"ok": True, "project": a.name, "node": nk, "model": model, "next": f"run {a.name} --node {nk}"})


def node_done(p, nk):
    d = rh("node", "get", "id:" + nk, "-p", p["canvas_id"], "--include", "outputs", check=False)
    item = (d.get("items") or [d])[0]
    data = item.get("data") or {}
    return data.get("status"), bool(data.get("outputs"))


def book(c, p, st, amount, entry, incomplete):
    st["cost"] = round(float(st.get("cost", 0)) + amount, 3)
    p["total"] = round(float(p.get("total", 0)) + amount, 3)
    if incomplete:
        st["incomplete"] = p["incomplete"] = True
    p["ledger"].append(entry)


def cmd_run(a):
    """在画布上跑一个节点：先报价，再运行等结果；成功才按报价记花费。不需要问用户。"""
    c = cfg()
    p = find_proj_period(c, a.name)
    st = load_proj(c, p, a.name)
    sel = a.node if ":" in a.node else "id:" + a.node
    nk = sel.split(":", 1)[1]
    est = rh("node", "estimate", sel, "-p", p["canvas_id"], "--billing-scope", "personal", check=False)
    amount = sum(float(t.get("amount") or 0) for t in est.get("totals", []) if t.get("currency", "CNY") == "CNY")
    incomplete = est.get("status") != "AVAILABLE" or not est.get("totals") or         any(t.get("coverage") != "COMPLETE" for t in est.get("totals", []))
    if incomplete:
        warn(f"报价不完整（{est.get('status') or err_code(est)}），按 {amount} 元记；交付前到网站核对实际花费，用 cost --add 补记")
    rid = uuid7()
    entry = {"time": now(), "project": a.name, "node": nk, "amount": amount, "runRequestId": rid,
             "estimate": est.get("estimateId"), "estimate_status": est.get("status"), "status": "dispatching"}
    p["ledger"].append(entry)          # 派发前先记 ID，崩了也能按原 ID 查
    save_period(c, p)
    p["ledger"].pop()
    r = rh("node", "run", sel, "-p", p["canvas_id"], "--billing-scope", "personal", "--run-request-id", rid,
           "--timeout", a.timeout, check=False, timeout=int(a.timeout) + 120)
    status = str(r.get("status") or r.get("taskStatus") or (r.get("_rh") or {}).get("outcome") or "").upper()
    task = first(r, "taskId")
    entry.update(task=task, run_status=status)
    nstatus, has_out = node_done(p, nk)
    if not r.get("_rc") and (status in OK_STATES or (nstatus == "finished" and has_out)) and status not in BAD_STATES:
        entry["status"] = "done"
        book(c, p, st, amount, entry, incomplete)
        st = commit(c, p, st)
        out({"ok": True, "project": a.name, "node": nk, "amount": amount, "project_cost": st["cost"],
             "period_total": p["total"], "next": f"adopt {a.name} <槽位> --node {nk} --version N --review"})
    if status in BAD_STATES or (r.get("_rc") and err_code(r) not in ("LOCAL_TIMEOUT", "OUTCOME_UNKNOWN") and not task):
        entry["status"] = "failed"
        p["ledger"].append(entry)
        save_period(c, p)
        out({"ok": False, "project": a.name, "node": nk, "status": status, "error": "运行失败（未记花费）",
             "errorMessage": first(r, "errorMessage"), "code": first(r, "code") or err_code(r)}, 1)
    entry["status"] = "pending"        # 超时 / 结果未知 / 还在跑：超时不取消任务，最终会扣费
    book(c, p, st, amount, entry, incomplete)
    st = commit(c, p, st)
    out({"ok": False, "pending": True, "project": a.name, "node": nk, "taskId": task, "runRequestId": rid,
         "status": status or err_code(r), "error": "还没跑完；用 wait 继续等，不要换 ID 重跑",
         "next": f"wait {a.name} --node {nk}"}, 4)


def cmd_wait(a):
    c = cfg()
    p = find_proj_period(c, a.name)
    nk = a.node.split(":", 1)[-1]
    deadline = time.time() + int(a.timeout)
    status = None
    while time.time() < deadline:
        status, has_out = node_done(p, nk)
        if status == "finished" and has_out:
            for e in p["ledger"]:
                if e.get("node") == nk and e.get("status") == "pending":
                    e["status"] = "done"
            save_period(c, p)
            out({"ok": True, "project": a.name, "node": nk, "status": status,
                 "next": f"adopt {a.name} <槽位> --node {nk} --version N --review"})
        if status in ("failed", "error", "canceled", "cancelled"):
            for e in p["ledger"]:
                if e.get("node") == nk and e.get("status") == "pending":
                    e["status"] = "failed_check_refund"
            save_period(c, p)
            d = rh("node", "get", "id:" + nk, "-p", p["canvas_id"], "--include", "outputs", check=False)
            out({"ok": False, "project": a.name, "node": nk, "status": status, "error": "运行失败",
                 "errorMessage": first(d, "errorMessage")}, 1)
        time.sleep(15)
    out({"ok": False, "pending": True, "project": a.name, "node": nk, "status": status, "error": "还没跑完，再 wait"}, 4)


def cmd_deliver(a):
    """工程交付：成品只放本地 06_成品；更新画布名里的花费。"""
    c = cfg()
    p = find_proj_period(c, a.name)
    st = load_proj(c, p, a.name)
    copied = [archive(st, "成品", os.path.abspath(f)) for f in (a.file or [])]
    out_dir = os.path.join(st["local"], LOCAL_DIRS["成品"])
    os.makedirs(out_dir, exist_ok=True)
    if not [f for f in os.listdir(out_dir) if not f.startswith("_")] and not a.force:
        fail("06_成品 里还没有成品文件。用 --file 带上成品（可多个），或确认无需成品时加 --force")
    st["stage"], st["state"] = "06 成品交付", "已交付"
    for v in st["slots"].values():
        v["review"] = False
    pend = [e for e in p["ledger"] if e.get("project") == a.name and e.get("status") == "pending"]
    if pend:
        warn(f"还有 {len(pend)} 笔运行没确认完成（花费已按报价计入）")
    commit(c, p, st)
    sync_canvas_name(c, p)
    save_period(c, p)
    out({"ok": True, "project": a.name, "canvas": p["name"], "copied": copied, "local": out_dir})


def cmd_cost(a):
    c = cfg()
    p = find_proj_period(c, a.name) if a.name else need_period(c)
    if a.add is not None:
        st = load_proj(c, p, a.name) if a.name else None
        p["total"] = round(float(p.get("total", 0)) + a.add, 3)
        p["ledger"].append({"time": now(), "project": a.name, "amount": a.add, "manual": True, "note": read_note(a)})
        if a.settled:
            p["incomplete"] = False
        if st:
            st["cost"] = round(float(st.get("cost", 0)) + a.add, 3)
            if a.settled:
                st["incomplete"] = False
            commit(c, p, st)
    if a.sync or a.add is not None:
        sync_canvas_name(c, p)
        refresh_overview(c, p)
    save_period(c, p)
    out({"ok": True, "canvas": p["name"], "total": p["total"], "ledger": p["ledger"][-10:]})


# ---------------------------------------------------------------- 命令：排版
def cmd_layout(a):
    c = cfg()
    p = need_period(c, a.period)
    dropped = sync_state(c, p)
    for name in p["rows"]:
        st = load_json(os.path.join(proj_dir(c, p, name), "工作台.json"))
        if st and not st["slots"].get("标题卡"):
            refresh_title(c, p, st)
            save_proj(c, p, st)
    moved = relayout_period(c, p)
    refresh_overview(c, p)
    save_period(c, p)
    known = {p.get("overview")}
    for name in p["rows"]:
        st = load_json(os.path.join(proj_dir(c, p, name), "工作台.json")) or {}
        known |= {v.get("node") for v in st.get("slots", {}).values()}
    orphans = [n["name"] for k, n in canvas_nodes(p).items() if k not in known]
    out({"ok": True, "moved": moved, "dropped_missing": dropped, "orphans": orphans[:50], "url": p["url"]})


def cmd_preview(a):
    """把画布当前排版画成 PNG，用于自查。"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        fail("preview 需要 Pillow：pip install pillow")
    c = cfg()
    p = need_period(c, a.period)
    boxes = [(n["name"], n["type"], n["data"]["position"], n["data"].get("size") or {"width": 300, "height": 200})
             for n in canvas_nodes(p).values()]
    gboxes = [(g.get("name"), g.get("position") or (g.get("data") or {}).get("position"),
               g.get("size") or (g.get("data") or {}).get("size")) for g in canvas_groups(p).values()]
    if not boxes:
        fail("画布上还没有节点")
    xs = [b[2]["x"] for b in boxes] + [g[1]["x"] for g in gboxes if g[1]]
    ys = [b[2]["y"] for b in boxes] + [g[1]["y"] for g in gboxes if g[1]]
    x2 = [b[2]["x"] + b[3]["width"] for b in boxes] + [g[1]["x"] + g[2]["width"] for g in gboxes if g[1] and g[2]]
    y2 = [b[2]["y"] + b[3]["height"] for b in boxes] + [g[1]["y"] + g[2]["height"] for g in gboxes if g[1] and g[2]]
    minx, miny, maxx, maxy = min(xs) - 50, min(ys) - 50, max(x2) + 50, max(y2) + 50
    s = min(1.0, 2400 / (maxx - minx))
    im = Image.new("RGB", (int((maxx - minx) * s), int((maxy - miny) * s)), (24, 24, 27))
    dr = ImageDraw.Draw(im)
    fpath = next((f for f in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf",
                              "/System/Library/Fonts/PingFang.ttc",
                              "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"] if os.path.exists(f)), None)
    font = ImageFont.truetype(fpath, max(10, int(26 * s))) if fpath else ImageFont.load_default()
    T = lambda x, y: (int((x - minx) * s), int((y - miny) * s))
    for name, pos, size in gboxes:
        if pos and size:
            dr.rectangle([T(pos["x"], pos["y"]), T(pos["x"] + size["width"], pos["y"] + size["height"])],
                         outline=(124, 92, 255), width=2)
            dr.text(T(pos["x"] + 20, pos["y"] + 20), name or "", fill=(200, 190, 255), font=font)
    color = {"text": (70, 70, 80), "image": (40, 90, 140), "video": (120, 60, 40), "audio": (40, 110, 70)}
    for name, typ, pos, size in boxes:
        dr.rectangle([T(pos["x"], pos["y"]), T(pos["x"] + size["width"], pos["y"] + size["height"])],
                     fill=color.get(typ, (60, 60, 60)), outline=(230, 230, 230))
        dr.text(T(pos["x"] + 10, pos["y"] + 10), f"{typ}:{name.split('｜')[-1]}", fill=(255, 255, 255), font=font)
    outp = a.out or os.path.join(period_dir(c, p), "排版预览.png")
    im.save(outp)
    out({"ok": True, "png": outp, "nodes": len(boxes), "groups": len(gboxes)})


def cmd_log(a):
    """记录 / 查看问题。Agent 遇到任何卡住、报错、绕路、规则不清的情况都要记一条。"""
    os.makedirs(LOG_DIR, exist_ok=True)
    if a.problem or a.fixed:
        rec = {"time": dt.datetime.now().isoformat(timespec="seconds"), "host": os.environ.get("COMPUTERNAME"),
               "user": os.environ.get("USERNAME"), "ver": VERSION, "cmd": "log",
               "kind": "fixed" if a.fixed else "problem", "ok": bool(a.fixed),
               "problem": a.problem or a.fixed, "stage": a.stage, "project": a.project}
        with open(RUN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        out({"ok": True, "logged": rec, "log": RUN_LOG})
    recs = []
    for path in sorted(glob.glob(os.path.join(LOG_DIR, "*.jsonl"))):
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if a.all or not r.get("ok", True) or r.get("warnings") or r.get("kind") in ("problem", "fixed", "fail"):
                    r["_file"] = os.path.basename(path)
                    recs.append(r)
    recs.sort(key=lambda r: r.get("time", ""))
    out({"ok": True, "log_dir": LOG_DIR, "count": len(recs), "items": recs[-a.tail:]})


def cmd_report(a):
    """把日志、安装报告、环境信息打包成 zip（不含账号凭据），发给工作台维护者。"""
    os.makedirs(LOG_DIR, exist_ok=True)
    desk = os.path.join(HOME, "Desktop")
    dst = a.out or os.path.join(desk if os.path.isdir(desk) else HOME,
                                f"rhtv-workbench-日志-{os.environ.get('COMPUTERNAME', 'pc')}-{dt.datetime.now():%m%d%H%M}.zip")
    env = {"ver": VERSION, "python": sys.version, "platform": sys.platform, "host": os.environ.get("COMPUTERNAME"),
           "rhtvcli": None, "ffprobe": shutil.which("ffprobe"), "ffmpeg": shutil.which("ffmpeg"),
           "elevenlabs": shutil.which("elevenlabs"), "chrome_env": os.environ.get("CHROME"), "MM_RES": os.environ.get("MM_RES")}
    try:
        env["rhtvcli"] = " ".join(rh_cmd())
        env["account"] = {k: v for k, v in (rh("account", check=False).get("data") or {}).items()
                          if k in ("site", "accessMode", "allowedActions", "idleExpiresAt")}
    except SystemExit:
        pass
    except Exception as e:
        env["rhtvcli_error"] = str(e)
    c = load_json(CFG_PATH) or {}
    safe_cfg = {k: v for k, v in c.items() if k not in ("token", "secret")}
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for path in glob.glob(os.path.join(LOG_DIR, "*")):
            z.write(path, "logs/" + os.path.basename(path))
        z.writestr("环境.json", json.dumps(env, ensure_ascii=False, indent=1, default=str))
        z.writestr("config.json", json.dumps(safe_cfg, ensure_ascii=False, indent=1))
        for p in all_periods(c) if c else []:
            z.writestr(f"画布/{p['key']}.json", json.dumps({k: v for k, v in p.items()}, ensure_ascii=False, indent=1))
    out({"ok": True, "report": dst})


def cmd_rh(a):
    """透传 rhtvcli（不经 .cmd，长参数安全）。例：wb.py rh model search video --type video"""
    r = subprocess.run(rh_cmd() + a.args, env=rh_env())
    sys.exit(r.returncode)


# ---------------------------------------------------------------- 入口
def main():
    ap = argparse.ArgumentParser(prog="wb.py", description="rhtv-workbench：RHTV 画布排版与进度")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("check", help="检查 rhtvcli、登录、依赖")
    s = sp.add_parser("setup", help="配置设计师、本地工作目录、RHTV 文件夹")
    s.add_argument("--designer", required=True); s.add_argument("--root", required=True)
    s.add_argument("--prefix", help="画布名前缀（只用于测试，正式用 --prefix \"\"）"); s.add_argument("--days", type=int, help="周期天数，默认 28")
    s = sp.add_parser("list", help="列出工程和进度（含上个周期没交付的）"); s.add_argument("--all", action="store_true")
    s = sp.add_parser("new", help="新建工程（一行）；失败后可原样重跑"); s.add_argument("name")
    s.add_argument("--from", dest="start", help="从第几阶段开始，如 05")
    s = sp.add_parser("put", help="把本地文件放进槽位（文字/图/视频/音频），同时归档本地；成品只归档")
    s.add_argument("name"); s.add_argument("slot"); s.add_argument("file")
    s.add_argument("--version", type=int); s.add_argument("--label", help="版本说明，如 银发")
    s.add_argument("--review", action="store_true", help="标记为待审核")
    s = sp.add_parser("gen", help="在画布上建生成节点（提示词走文件）")
    s.add_argument("name"); s.add_argument("--type", choices=["image", "video"], required=True)
    s.add_argument("--prompt-file", required=True); s.add_argument("--model"); s.add_argument("--mode")
    s.add_argument("--left", action="append", help="输入：槽位名（如 v1·人设图）或节点 ID，可多个")
    s.add_argument("--set", action="append", help="模型参数 KEY=VALUE（按 model schema）"); s.add_argument("--tag")
    s = sp.add_parser("run", help="在画布上跑节点，成功后记花费"); s.add_argument("name"); s.add_argument("--node", required=True)
    s.add_argument("--timeout", default="1800")
    s = sp.add_parser("wait", help="继续等 run 返回 pending 的节点"); s.add_argument("name"); s.add_argument("--node", required=True)
    s.add_argument("--timeout", default="1800")
    s = sp.add_parser("adopt", help="把画布上已生成的节点收进槽位并下载归档")
    s.add_argument("name"); s.add_argument("slot"); s.add_argument("--node", required=True)
    s.add_argument("--version", type=int); s.add_argument("--label"); s.add_argument("--review", action="store_true")
    s.add_argument("--no-download", action="store_true")
    s = sp.add_parser("remove", help="删掉槽位或整个版本（如 v3）"); s.add_argument("name"); s.add_argument("targets", nargs="+")
    s.add_argument("--keep-local", action="store_true")
    for nm, hp in (("approve", "设计师通过"), ("reject", "设计师打回")):
        s = sp.add_parser(nm, help=hp); s.add_argument("name"); s.add_argument("slots", nargs="*")
        s.add_argument("--version", type=int)
        if nm == "reject":
            s.add_argument("--note"); s.add_argument("--note-file")
    s = sp.add_parser("stage", help="更新进度"); s.add_argument("name"); s.add_argument("stage"); s.add_argument("state")
    s.add_argument("--note"); s.add_argument("--note-file")
    s = sp.add_parser("deliver", help="工程交付：成品归档本地，更新画布名花费"); s.add_argument("name")
    s.add_argument("--file", action="append"); s.add_argument("--force", action="store_true")
    s = sp.add_parser("cost", help="查看/补记花费，同步画布名"); s.add_argument("--name"); s.add_argument("--add", type=float)
    s.add_argument("--note"); s.add_argument("--note-file"); s.add_argument("--sync", action="store_true")
    s.add_argument("--settled", action="store_true", help="已到网站核对过实际花费")
    s = sp.add_parser("layout", help="按标准格式重排画布（也会清理失效记录）"); s.add_argument("--period")
    s = sp.add_parser("preview", help="把排版画成 PNG 自查"); s.add_argument("--out"); s.add_argument("--period")
    s = sp.add_parser("rh", help="透传 rhtvcli"); s.add_argument("args", nargs=argparse.REMAINDER)
    s = sp.add_parser("log", help="记录问题（--problem）/ 记录已解决（--fixed）/ 查看问题日志")
    s.add_argument("--problem"); s.add_argument("--fixed"); s.add_argument("--stage"); s.add_argument("--project")
    s.add_argument("--tail", type=int, default=30); s.add_argument("--all", action="store_true")
    s = sp.add_parser("report", help="把日志打包成 zip 发给维护者"); s.add_argument("--out")
    sp.add_parser("version", help="显示版本")
    CTX["argv"] = sys.argv[1:]
    a = ap.parse_args()
    CTX["cmd"] = a.cmd
    if a.cmd == "version":
        out({"ok": True, "version": VERSION, "path": os.path.abspath(__file__)})
    try:
        globals()["cmd_" + a.cmd](a)
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        fail(f"{type(e).__name__}: {e}", trace=traceback.format_exc()[-1500:])


if __name__ == "__main__":
    main()
