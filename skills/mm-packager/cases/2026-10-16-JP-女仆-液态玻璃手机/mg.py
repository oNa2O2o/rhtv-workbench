"""MusicGen-stereo-large score for 女仆 v3. Sections are chained by audio-prompt continuation so the piece stays coherent.
usage: python mg.py  -> audio/mg_<name>.wav per section + audio/bgm_maid_drama.wav (assembled to the output timeline)"""
import os, sys, numpy as np, torch, wave
from transformers import AutoProcessor, MusicgenForConditionalGeneration
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')
M = 'facebook/musicgen-stereo-large'
proc = AutoProcessor.from_pretrained(M)
model = MusicgenForConditionalGeneration.from_pretrained(M, torch_dtype=torch.float16).to('cuda')
SR = model.config.audio_encoder.sampling_rate  # 32000
torch.manual_seed(int(sys.argv[1]) if len(sys.argv) > 1 else 11)

BASE = 'high-end cinematic J-pop film score, polished modern production, wide stereo, emotional anime drama soundtrack'
SECTIONS = [  # (name, seconds, prompt) — durations match the output timeline (title 0-2, act1 2-9.07, choice1 -12.6, act2 -18.1 slap 15.74, choice2 -21.7, end -25.9)
    ('act1', 9.07, f'{BASE}, opens with a dramatic orchestral hit, then elegant grand piano and lush strings over tight cinematic drums, deep kick and snare, jealous tension building, minor key, 100 bpm'),
    ('ch1', 3.53, f'{BASE}, suspenseful pause, sustained high strings tremolo, ticking percussion, low piano pulse, waiting for an answer, minor key'),
    ('act2a', 3.14, f'{BASE}, dark intense dramatic build, heavy taiko and cinematic drums, aggressive staccato strings, fast crescendo rising to a huge climax hit, minor key'),
    ('act2b', 2.36, f'{BASE}, stunned aftermath after a shock, drums stop, low cello drone, sub bass boom fading, minor key'),
    ('ch2', 3.6, f'{BASE}, tense standoff, heartbeat sub bass pulse, dissonant held strings, sparse piano notes, minor key'),
    ('end', 4.5, f'{BASE}, emotional bittersweet finale, soaring strings and piano with full drums, cinematic and beautiful, ends with a final chord'),
]
PROMPT_TAIL = 3.0  # seconds of previous audio fed as continuation prompt

def gen(prompt, seconds, prev=None):
    kw = dict(do_sample=True, guidance_scale=3.5, max_new_tokens=int(seconds * 50) + 6)
    if prev is None:
        inp = proc(text=[prompt], padding=True, return_tensors='pt')
    else:
        tail = prev[:, -int(PROMPT_TAIL * SR):]
        inp = proc(text=[prompt], audio=[tail], sampling_rate=SR, padding=True, return_tensors='pt')
    inp = {k: (v.to('cuda').half() if v.dtype.is_floating_point else v.to('cuda')) for k, v in inp.items()}
    with torch.no_grad():
        a = model.generate(**inp, **kw)[0].float().cpu().numpy()  # (2, n)
    if prev is not None:
        a = a[:, int(PROMPT_TAIL * SR):]  # drop the echoed prompt
    return a[:, :int(seconds * SR)]

def save(n, a):
    a = a / (np.abs(a).max() + 1e-9) * 0.89
    with wave.open(os.path.join(D, n), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a.T * 32767).astype('<i2').tobytes())

full = None
for name, sec, pr in SECTIONS:
    seg = gen(pr, sec, full)
    print(name, seg.shape, flush=True)
    save(f'mg_{name}.wav', seg)
    full = seg if full is None else np.concatenate([full, seg], 1)
save(f'bgm_maid_drama_s{sys.argv[1] if len(sys.argv) > 1 else 11}.wav', full)
print('done', full.shape[1] / SR)
