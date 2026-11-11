# -*- coding: utf-8 -*-
"""v2 合成：正片(无声) + 尾板 + 口播 + BGM + 音效 + UI 音效。
用法: python -I assemble_v2.py spec.json main.mp4 out.mp4
"""
import sys, json, subprocess
P = "F:/钟海明/2026/2026年11月4日MM-JP-女性向-签售会POV"
TAIL = sys.argv[4]
VO = f"{P}/包装素材/音频/vo"
SFXD = "F:/钟海明/音效收集"
S = json.load(open(sys.argv[1], encoding="utf-8")); main, out = sys.argv[2], sys.argv[3]
END, APP, CHAT = S["end"], S["appAt"], S["chatAt"]
TAILD = 6.8; HOLD = 0; TOTAL = END + TAILD + HOLD
vo_at = S.get("vo", [0.10, 3.05, 8.0, 11.75, 13.35, 17.0]) + [END + 0.10]
# 切镜音效
t = 0; cuts = []
for s in S["shots"]:
    if s.get("flash"): cuts.append(t)
    t += s["dur"]
sfx = ([(S["introSfx"], "回声弹出音效.MP3", .55)] if "introSfx" in S else []) + [(c, "进选项、闪白、照相音效.MP3", .35) for c in cuts] + [(S["freezeAt"], "综艺尴尬音效.MP3", .55), (S["shrinkAt"], "回声弹出音效.MP3", .5), (END + .05, "回声弹出音效.MP3", .4), (END + .35, "气泡提示音.MP3", .3), (END + .75, "收钱花钱加分减分清脆响声.MP3", .18), (END + 5.5, "咔嗒清脆点击.MP3", .8)]

inp = ["-i", main, "-i", TAIL, "-i", f"{P}/包装素材/音频/bgm_v1.mp3", "-i", S["swipe"], "-i", S["chat"]]
fl = [f"[0:v]fps=30,format=yuv420p,setsar=1[v0]", f"[1:v]fps=30,scale=1080:1920,format=yuv420p,setsar=1,tpad=stop_mode=clone:stop_duration={HOLD}[v1]",
      "[v0][v1]concat=n=2:v=1:a=0[v]"]
lab = []
fl.append(f"[2:a]atrim=0:{TOTAL},volume=0.30,aresample=48000[bgm0]")
fl.append(f"[3:a]volume=0.8,adelay={int(APP * 1000)}:all=1[ua]"); lab.append("[ua]")
fl.append(f"[4:a]volume=0.8,adelay={int(CHAT * 1000)}:all=1[ub]"); lab.append("[ub]")
k = 5
vlab = []
for i, at in enumerate(vo_at):
    inp += ["-i", f"{VO}/t{i + 1}.wav"]
    fl.append(f"[{k}:a]aresample=48000,volume={1.4 if i == len(vo_at) - 1 else 1.15},adelay={int(at * 1000)}:all=1[vo{i}]"); vlab.append(f"[vo{i}]"); k += 1
if "vo0" in S:
    v0 = S["vo0"]; inp += ["-ss", str(v0["ss"]), "-i", f"{VO}/{v0['file']}"]
    fl.append(f"[{k}:a]aresample=48000,volume=1.25,adelay={int(v0['at'] * 1000)}:all=1[vz]"); vlab.append("[vz]"); k += 1
for j, (at, f, v) in enumerate(sfx):
    inp += ["-i", f"{SFXD}/{f}"]
    fl.append(f"[{k}:a]aresample=48000,volume={v},adelay={int(at * 1000)}:all=1[s{j}]"); lab.append(f"[s{j}]"); k += 1
# 口播总线 → BGM 侧链闪避（说话时 BGM 自动压低），BGM 只在口播结束后淡出
fl.append("".join(vlab) + f"amix=inputs={len(vlab)}:normalize=0,apad,atrim=0:{TOTAL},asplit=2[vox][key]")
fl.append(f"[bgm0][key]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=350:makeup=1,afade=t=out:st={TOTAL - .6}:d=0.6[bgm]")
lab = ["[vox]", "[bgm]"] + lab
fl.append("".join(lab) + f"amix=inputs={len(lab)}:normalize=0,apad,atrim=0:{TOTAL},loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", ";".join(fl), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", str(TOTAL),
                "-movflags", "+faststart", out], check=True)
print("ok", out, TOTAL)
