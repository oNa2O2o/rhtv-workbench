#!/usr/bin/env python
"""环境自检：python check_env.py。缺什么打印什么；必需项全部 OK 退出码 0（可选项缺了只提示）。变量和本机值见 reference/环境.md。"""
import importlib, os, shutil, sys

bad = []
def ok(name, cond, fix, optional=False):
    tag = "OK   " if cond else ("opt  " if optional else "MISS ")
    print(tag + name + ("" if cond else f"  → {fix}"))
    if not cond and not optional: bad.append(name)

def mod(m, pip, optional=False):
    try: importlib.import_module(m); ok(f"python: {m}", True, "")
    except Exception: ok(f"python: {m}", False, f"pip install {pip}", optional)

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
    ok("  资源/sfx（用户提供的音效，可以没有）", os.path.isdir(f"{RES}/sfx"), "没有就用 ElevenLabs 生成，见 rules/通用.md", optional=True)
ok("elevenlabs CLI（口播/BGM/音效/备用 ASR）", shutil.which("elevenlabs") is not None, "npm i -g @elevenlabs/cli 后 elevenlabs auth login")
chrome = os.environ.get("CHROME", r"C:/Program Files/Google/Chrome/Application/chrome.exe")
ok("Chrome（app-ui / 尾板渲染）" + chrome, os.path.exists(chrome), "安装 Chrome 或设置环境变量 CHROME，见 reference/环境.md")
sys.exit(1 if bad else 0)
