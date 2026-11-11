"""ElevenLabs Music：深夜·再会 BGM（温暖暧昧 R&B / lo-fi，琥珀色调）。usage: python music.py <tag>"""
import json, subprocess, sys, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'audio')
tag = sys.argv[1] if len(sys.argv) > 1 else 'A'
NEG = ["vocals", "singing", "choir", "lyrics", "rap", "rock", "metal", "EDM drop", "cute", "kawaii", "happy upbeat", "orchestral epic"]
def ch(text, ms, pos):
    return {"text": text, "duration_ms": ms, "positive_styles": pos, "negative_styles": NEG, "context_adherence": "high"}
plan = {"chunks": [
    ch("[Intro]\nA soft door chime then a warm Rhodes chord swell, late night city, intimate", 3000, ["late night", "rhodes", "warm", "intimate"]),
    ch("[Verse]\nSlow sensual late-night R&B groove: warm Rhodes electric piano, deep soft bass, laid-back brushed drums, vinyl crackle, 82 bpm, nostalgic and flirty", 8000, ["r&b", "rhodes", "sensual", "nostalgic", "laid-back"]),
    ch("[Break]\nDrums stop, a suspended Rhodes chord holds with soft tension, quiet ticking", 3000, ["suspense", "quiet", "suspended chord"]),
    ch("[Verse 2]\nGroove returns slightly fuller, warm bass, soft snaps, dreamy pads, getting closer and more intimate, rising tension toward the end", 12000, ["r&b", "dreamy", "intimate", "building"]),
    ch("[Breakdown]\nAlmost silence: only a very low soft sub pad, breathless anticipation", 4000, ["minimal", "sub pad", "breathless"]),
    ch("[Outro]\nWarm Rhodes R&B groove returns gently under a male voice-over, leaves space for speech, ends with a final warm chord", 12500, ["r&b", "rhodes", "warm", "light drums"]),
]}
body = {"model_id": "music_v2_5", "composition_plan": plan}
json.dump(body, open(os.path.join(D, f'bgm{tag}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
out = os.path.join(D, f'bgm{tag}.mp3')
r = subprocess.run(['elevenlabs.cmd', 'music', 'compose', '--json', '-', '-o', out], input=json.dumps(body, ensure_ascii=False).encode('utf-8'), capture_output=True)
print(r.returncode, r.stdout.decode('utf-8', 'replace')[-500:], r.stderr.decode('utf-8', 'replace')[-800:])
