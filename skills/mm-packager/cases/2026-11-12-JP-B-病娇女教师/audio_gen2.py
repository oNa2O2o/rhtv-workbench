"""第二轮声音：用户嫌「音效太雷霆」→ 合成的 g26/lgx 全部不用，用户音效收集优先，缺的用 ElevenLabs 生成（提示词写死避开低频轰鸣）；
BGM 做低频衰减。输出到 包装素材_版本1/audio/。"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audio_gen import el, dur, OUT

AVOID = (" Avoid: thunder, thunder-like rumble, boom, sub bass, deep low-frequency impact, explosion, crisp tinkly ding (tink),"
         " rustling, music box.")
SFX2 = {
    "tick_soft": ("A single soft quiet clock tick, light wooden click, close and dry, very short, no ringing tail." + AVOID, 0.5),
    "heartbeat_soft": ("A single gentle soft human heartbeat lub-dub, light and intimate, mid-low warm thump, not boomy, quick decay." + AVOID, 0.6),
    "final_bell": ("One single mellow mid-pitched Japanese school chime note heard through a window, soft, gentle attack, short natural decay, no low drone." + AVOID, 1.6),
    "card_swipe": ("A soft quick smartphone card swipe, light airy flick of a finger on glass, subtle and clean." + AVOID, 0.5),
}

for k, (txt, d) in SFX2.items():
    out = os.path.join(OUT, k + ".mp3")
    if os.path.exists(out): continue
    el(["text-to-sound-effects", "convert"], {"text": txt, "duration_seconds": d, "prompt_influence": 0.5}, out)
    print(k, round(dur(out), 3), flush=True)

# BGM 低频衰减：80 Hz 高通 + 150 Hz 低架 −8 dB（压掉 sub boom，保留旋律）
for b in ("bgm_story", "bgm_bridge"):
    src, dst = os.path.join(OUT, b + ".mp3"), os.path.join(OUT, b + "_lite.mp3")
    if os.path.exists(dst): continue
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-af", "highpass=f=80:poles=2,lowshelf=f=150:g=-8", "-b:a", "256k", dst], check=True)
    print(b, "→", os.path.basename(dst), flush=True)

# 高通版（压掉超低频「雷霆」感）：滴答、划卡 300 Hz×2；心跳 70 Hz 高通 + 120 Hz 轻提
HP = {"tick_soft": "highpass=f=300:poles=2,highpass=f=300:poles=2", "card_swipe": "highpass=f=300:poles=2,highpass=f=300:poles=2",
      "heartbeat_soft": "highpass=f=70:poles=2,equalizer=f=120:t=q:w=1:g=3"}
for k, af in HP.items():
    src, dst = os.path.join(OUT, k + ".mp3"), os.path.join(OUT, k + "_hp.wav")
    if os.path.exists(dst): continue
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-af", af, dst], check=True)
    print(k, "→", os.path.basename(dst), flush=True)
