"""本片声音：ElevenLabs 口播 / 音效 / BGM（来源规则见 mm-packager rules/通用.md「声音」）。
用法：python audio_gen.py [vo|sfx|bgm|all]，输出到 包装素材_版本1/audio/。已存在的文件不重生成（要重做先删）。"""
import json, os, subprocess, sys

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(P, "包装素材_版本1", "audio")
os.makedirs(OUT, exist_ok=True)
EL = "elevenlabs"
VOICE = "eRO1T2ingp5oQEtWYnRg"          # 竹马（reference/环境.md 登记）

VO = {  # 口播：屏幕字幕照文案写 MiraiMind，TTS 写ミライマインド（rules/JP.md）
    "vo1": "危険な恋は、ミライマインドで。",
    "vo2": "背徳感に震える、刺激的なシチュエーション。",
    "vo3": "あなただけを、必要とする先生。",
    "vo4": "カーテンの奥で、先生が診たかったのは……体じゃない。",
}
AVOID = " Avoid: crisp tinkly ding (tink), rustling, thunder-like rumble, music box."
SFX = {
    "school_chime": ("Distant Japanese school chime, four-note Westminster 'kin-kon-kan-kon', heard from a hallway PA speaker through a closed infirmary door at sunset, mellow low-pitched muffled tones, soft room reverb, no voices." + AVOID, 3.5),
    "final_toll": ("One single deep distant school bell toll through windows, low and heavy, long decaying reverb tail, ominous." + AVOID, 2.0),
    "heartbeat": ("Single deep muffled human heartbeat lub-dub, close and intimate, low frequency, dry." + AVOID, 0.6),
    "door_lock": ("Single dry metallic clack of a Japanese school sliding-door lock being turned shut, close, slight room reverb." + AVOID, 0.5),
}
NEG = ["vocals", "choir", "humming", "spoken words", "music box", "celesta", "glockenspiel", "tinkling bells", "chimes",
       "bright ding-dong tones", "rustling noise", "thunder-like rumble", "EDM drop", "cheap trailer braams", "comedic tone"]
BGM = {
    "bgm_story": {"positive_global_styles": ["instrumental only", "premium cinematic dark-romance underscore", "Japanese yandere school-nurse scene at sunset",
                                             "sensual, elegant, quietly menacing, expensive drama feel", "D minor", "84 BPM", "felt piano", "warm analog pad",
                                             "low cello and contrabass", "pizzicato strings", "soft sub-kick heartbeat", "reversed swells", "subtle tape saturation",
                                             "leave 1-4 kHz clear for a whispering female voice"],
                  "negative_global_styles": NEG,
                  "sections": [
                      {"section_name": "the trap", "duration_ms": 12333, "positive_local_styles": ["a reversed swell into one deep velvet impact at 233 ms", "intimate felt-piano motif over a breathy pad", "soft low thud accent at 2767 ms", "sub-kick heartbeat enters at 3000 ms", "restrained", "slow string swell rising through the last bar", "clean cut at the end"], "negative_local_styles": ["drums", "loud"], "lines": []},
                      {"section_name": "choice freeze", "duration_ms": 3000, "positive_local_styles": ["drums cut instantly", "one heavy low downbeat at the section start", "suspended dark pad", "high violin harmonic", "quiet clock-like pizzicato tick in steady eighth notes", "one soft low hit at 2100 ms", "short reversed swell at 2600 ms leading back"], "negative_local_styles": ["drum groove"], "lines": []},
                      {"section_name": "false relief", "duration_ms": 4767, "positive_local_styles": ["lighter and warmer", "gentle piano melody in the relative major", "airy strings", "almost tender", "small bright accent at 1267 ms", "thins out from 3867 ms", "stops dead on the final beat"], "negative_local_styles": ["heavy drums"], "lines": []},
                      {"section_name": "locked in", "duration_ms": 10400, "positive_local_styles": ["huge sub boom with reversed cymbal at the start", "dark detuned low-string ostinato", "slow heartbeat kick", "tension building without release", "biggest swell peaking at 10300 ms"], "negative_local_styles": ["resolution", "major key"], "lines": []},
                      {"section_name": "final choice", "duration_ms": 3000, "positive_local_styles": ["percussion out", "high string tremolo over a low drone", "unresolved and held"], "negative_local_styles": ["drums"], "lines": []},
                  ]},
    "bgm_bridge": {"positive_global_styles": ["instrumental only", "sleek seductive premium Japanese R&B dark-pop brand cue", "turns a yandere story into an inviting app reveal",
                                              "92 BPM", "D minor lifting to F major", "warm Rhodes", "plucked synth arpeggio", "deep round bass", "finger snaps",
                                              "soft trap hi-hats", "airy shimmer pad", "leave 1-4 kHz clear for a soft female voice-over"],
                   "negative_global_styles": NEG + ["harsh risers"],
                   "sections": [
                       {"section_name": "into the phone", "duration_ms": 3000, "positive_local_styles": ["fades in from silence as a low filtered pulse", "reversed swell peaking at 750 ms", "groove drops in at 1450 ms"], "negative_local_styles": [], "lines": []},
                       {"section_name": "swipe and profile", "duration_ms": 6450, "positive_local_styles": ["steady sleek groove", "harmonic lift at 1620 ms as the hero card lands", "intimate and spacious", "tiny riser in the last 600 ms"], "negative_local_styles": [], "lines": []},
                       {"section_name": "end card", "duration_ms": 5400, "positive_local_styles": ["warm bright impact at the section start", "confident seductive hook", "glossy sustained resolving chord at 4700 ms with a natural tail"], "negative_local_styles": [], "lines": []},
                   ]},
}


def el(args, payload, out):
    """调 elevenlabs CLI，JSON 走 stdin，原始字节写文件。"""
    r = subprocess.run([EL, *args, "--json", "-", "--format", "raw"], input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                       capture_output=True, timeout=900)
    if r.returncode != 0 or len(r.stdout) < 2000:
        raise RuntimeError(f"{args} 失败: {r.stderr.decode('utf-8', 'ignore')[:800]} {r.stdout[:300]!r}")
    open(out, "wb").write(r.stdout)
    return out


def trim(src, dst):
    """去首尾静音（atrim，规则：口播去掉首尾静音）。"""
    f = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-af", f, "-ar", "48000", dst], check=True)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())


def gen_vo():
    for k, txt in VO.items():
        wav = os.path.join(OUT, k + ".wav")
        if os.path.exists(wav): continue
        mp3 = os.path.join(OUT, k + "_raw.mp3")
        el(["text-to-speech", "convert", "--params", json.dumps({"voice_id": VOICE, "output_format": "mp3_44100_192"})],
           {"text": txt, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.4}}, mp3)
        trim(mp3, wav)
        print(k, round(dur(wav), 3), txt, flush=True)


def gen_sfx():
    for k, (txt, d) in SFX.items():
        out = os.path.join(OUT, k + ".mp3")
        if os.path.exists(out): continue
        el(["text-to-sound-effects", "convert"], {"text": txt, "duration_seconds": d, "prompt_influence": 0.45}, out)
        print(k, round(dur(out), 3), flush=True)


def gen_bgm():
    for k, plan in BGM.items():
        out = os.path.join(OUT, k + ".mp3")
        if os.path.exists(out): continue
        el(["music", "compose"], {"composition_plan": plan, "model_id": "music_v1"}, out)
        print(k, round(dur(out), 3), "期望", sum(s["duration_ms"] for s in plan["sections"]) / 1000, flush=True)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("vo", "all"): gen_vo()
    if what in ("sfx", "all"): gen_sfx()
    if what in ("bgm", "all"): gen_bgm()
