#!/usr/bin/env python
"""环境自检：python check_env.py。缺什么打印什么；必需项全部 OK 退出码 0（可选项缺了只提示）。变量和本机值见 reference/环境.md。"""
import importlib, json, os, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
bad = []
def ok(name, cond, fix, optional=False):
    tag = "OK   " if cond else ("opt  " if optional else "MISS ")
    print(tag + name + ("" if cond else f"  → {fix}"))
    if not cond and not optional: bad.append(name)

def mod(m, pip, optional=False):
    try: importlib.import_module(m); ok(f"python: {m}", True, "")
    except Exception: ok(f"python: {m}", False, f"pip install {pip}", optional)

AUDIO_EXT = (".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac")
SFX_Z = "Z:/创新事业部/AIGC项目视频组/设计师物料总库/音频/音效收集"

def has_audio(d):
    """目录（含子目录）里有没有音效文件，找到第一个就停。"""
    if not d or not os.path.isdir(d): return False
    for _, _, fs in os.walk(d):
        if any(f.lower().endswith(AUDIO_EXT) for f in fs): return True
    return False

def workbench_roots():
    """工作台根：~/.rhtv-workbench/config.json 的 root，和本 Skill 所在 <根>/_系统/… 往上找到的根。"""
    roots = []
    try:
        r = json.load(open(os.path.join(os.path.expanduser("~"), ".rhtv-workbench", "config.json"), encoding="utf-8")).get("root")
        if r: roots.append(r)
    except Exception: pass
    d = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    while os.path.dirname(d) != d:
        if os.path.basename(d) == "_系统": roots.append(os.path.dirname(d)); break
        d = os.path.dirname(d)
    return roots

def user_sfx():
    """$USER_SFX 取值顺序：环境变量 MM_USER_SFX → <工作台根>/音效收集（安装器建的，非空才用）→ Z: 设计师物料总库音效收集。"""
    cands = [("MM_USER_SFX", os.environ.get("MM_USER_SFX"))] + [("工作台根", os.path.join(r, "音效收集")) for r in workbench_roots()] + [("Z: 默认", SFX_Z)]
    return next((d for _, d in cands if has_audio(d)), None), cands

def el_status():
    """elevenlabs CLI 登录态（auth status --format json 里有 logged_in 的方案）；调用经 heavy_lock 串行。"""
    try:
        from mmkit.heavy import heavy_lock
        lock = heavy_lock("elevenlabs", min_free_gb=0)
    except Exception:
        import contextlib; lock = contextlib.nullcontext()
    try:
        with lock:
            r = subprocess.run([shutil.which("elevenlabs"), "auth", "status", "--format", "json"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=60)
        return any(s.get("logged_in") for s in json.loads(r.stdout).get("schemes", [])), "logged_in=false"
    except Exception as e:
        return False, f"查不到登录态（{e.__class__.__name__}）"

ok("ffmpeg / ffprobe", shutil.which("ffmpeg") and shutil.which("ffprobe"), "安装 ffmpeg 并加入 PATH")
for m, pip in [("PIL", "pillow"), ("numpy", "numpy"), ("faster_whisper", "faster-whisper"),
               ("playwright", "playwright（再跑 python -m playwright install chromium）"), ("fontTools", "fonttools")]:
    mod(m, pip)
# 按需：BGM 人声检测/原声分离、抠图
for m, pip in [("soundfile", "soundfile"), ("demucs", "demucs"), ("torch", "torch torchvision（CUDA 版见 reference/环境.md）")]:
    mod(m, pip, optional=True)
ok("Node.js（to_timeline.mjs 一类脚本）", shutil.which("node") is not None, "安装 Node.js", optional=True)

RES = os.environ.get("MM_RES") or "Z:/创新事业部/AIGC项目视频组/mm-packager资源"  # 没设 MM_RES 时用共享盘默认路径
if RES:
    ok("共享资源目录 " + RES, os.path.isdir(RES), "检查共享盘映射，或把 MM_RES 指向本地副本（见 reference/环境.md）")
    for sub in ["fonts", "models", "jp-endcard/assets", "jp-endcard/media", "jp-endcard/prebuilt", "library/cards", "投放参考"]:
        ok(f"  资源/{sub}", os.path.isdir(f"{RES}/{sub}"), "从资源目录同步")
USER_SFX, tried = user_sfx()
ok("用户音效收集 $USER_SFX " + (USER_SFX or ""), USER_SFX is not None,
   "这几处都没有音效文件：" + "；".join(f"{k} {d or '（没设）'}" for k, d in tried)
   + "。设 MM_USER_SFX 指向用户音效收集，或往 <工作台根>/音效收集 放音效；不要退回 $RES/sfx（那里是本地合成音效，不用）")
ok("elevenlabs CLI（口播/BGM/音效/ASR scribe）", shutil.which("elevenlabs") is not None, "npm i -g @elevenlabs/cli 后 elevenlabs auth login")
if shutil.which("elevenlabs"):
    li, why = el_status()
    if li: ok("  elevenlabs 登录态", True, "")
    elif os.environ.get("ELEVENLABS_API_KEY"):
        ok(f"  elevenlabs 登录态：CLI {why}，只有 ELEVENLABS_API_KEY", False, "key 没有 music 权限时 BGM 会失败；跑 elevenlabs auth login", optional=True)
    else:
        ok(f"  elevenlabs 登录态：{why}", False, "跑 elevenlabs auth login（浏览器授权页要用户点确认）；登录丢了口播/BGM/音效/scribe 全停")
chrome = os.environ.get("CHROME", r"C:/Program Files/Google/Chrome/Application/chrome.exe")
ok("Chrome（app-ui / 尾板渲染）" + chrome, os.path.exists(chrome), "安装 Chrome 或设置环境变量 CHROME，见 reference/环境.md")
sys.exit(1 if bad else 0)
