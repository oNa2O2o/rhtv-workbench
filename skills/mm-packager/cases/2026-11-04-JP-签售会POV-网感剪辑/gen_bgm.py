import sys, os, json, urllib.request
out, ms = sys.argv[1], int(sys.argv[2])
prompt = ("Instrumental only, no vocals. Bright kawaii J-pop / future-bass edit track for a Japanese TikTok fan-cam montage. "
          "Sparkly synth plucks, bouncy 808 kick on every beat, handclaps, glockenspiel and chime ear-candy, sidechained pads, "
          "128 BPM, punchy and catchy, giddy heart-fluttering idol-fan energy, clear strong downbeats every 2 seconds for hard cuts, "
          "instant start with no slow intro, keeps the same energy throughout, ends on a clean hit.")
body = json.dumps({"prompt": prompt, "music_length_ms": ms, "model_id": "music_v2_5",
                   "force_instrumental": True}).encode()
req = urllib.request.Request("https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192", data=body,
                             headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"],
                                      "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=280) as r, open(out, "wb") as f:
        f.write(r.read())
    print("ok", out)
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode("utf-8", "replace")[:800])
