# BGM v2：按选项节奏重排 —— 幕段音乐（人声闪避）/ 选项段：定格撞击 + 倒计时滴答 + 心跳 + 上升音 + 点击爆点 / 片尾
import json, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt
ROOT = 'F:/钟海明/2026/2026年10月26日MM-JP-猫娘报恩/'
SR = 48000
meta = json.load(open(ROOT + '包装素材v1/layers/layers.json', encoding='utf-8'))
END = meta['end0'] + meta['ed']
x, sr = sf.read(ROOT + '包装素材v1/audio/bgm_mg_s7.wav', dtype='float32')
if x.ndim == 1: x = np.stack([x, x], 1)
if sr != SR: x = resample_poly(x, SR, sr, axis=0).astype(np.float32)
v, vsr = sf.read(ROOT + '工作区/voice_clean.wav', dtype='float32')
if v.ndim > 1: v = v.mean(1)
if vsr != SR: v = resample_poly(v, SR, vsr).astype(np.float32)
N = int(END * SR) + SR; out = np.zeros((N, 2), np.float32)
S = lambda t: int(round(t * SR))
def put(sig, t, g=1.0):
    a = S(t); sig = sig if sig.ndim == 2 else np.stack([sig, sig], 1)
    b = min(N, a + len(sig)); out[a:b] += sig[:b - a] * g
def fade(sig, fi, fo):
    sig = sig.copy(); n1, n2 = S(fi), S(fo)
    if n1: sig[:n1] *= np.linspace(0, 1, n1)[:, None]
    if n2: sig[-n2:] *= np.linspace(1, 0, n2)[:, None]
    return sig
def clip(a, b): return x[S(a):S(b)]
def lp(sig, f): return sosfilt(butter(4, f, 'low', fs=SR, output='sos'), sig, axis=0).astype(np.float32)
def env(n, dec): t = np.arange(n) / SR; return np.exp(-t / dec)
rng = np.random.default_rng(1)
def tick(hi=1.0):
    n = S(.05); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 2600 * hi * t) * .6 + np.sin(2 * np.pi * 1300 * hi * t) * .4) * env(n, .008)
    return s.astype(np.float32) * .5
def thump(f0=70, dec=.12, g=1.0):
    n = S(.4); t = np.arange(n) / SR; f = f0 * (1 + 1.5 * np.exp(-t / .02))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, dec) * g).astype(np.float32)
def boom():
    n = S(1.2); t = np.arange(n) / SR; f = 55 * (1 + 2.5 * np.exp(-t / .04))
    low = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .35)
    nz = lp(rng.standard_normal(n).astype(np.float32), 6000) * env(n, .18) * .35
    return (low * .9 + nz).astype(np.float32)
def riser(d):
    n = S(d); t = np.linspace(0, 1, n)
    nz = rng.standard_normal(n).astype(np.float32)
    out_ = np.zeros(n, np.float32); step = S(.05)
    for i in range(0, n, step):   # 逐块升高截止频率
        seg = nz[i:i + step]; f = 400 + 7000 * t[i] ** 2
        out_[i:i + len(seg)] = sosfilt(butter(2, [f * .6, f], 'band', fs=SR, output='sos'), seg)
    tone = np.sin(2 * np.pi * np.cumsum(220 + 660 * t ** 2) / SR) * .25
    return ((out_ * .6 + tone) * t ** 1.6).astype(np.float32)

# ---- 幕段音乐（旧 BGM 的对应段） ----
OLD = {'act1': (0, 8.70), 'ch1': (8.70, 14.70), 'act2': (14.70, 21.9667), 'ch2': (21.9667, 27.9667), 'act3': (27.9667, 39.0333), 'ch3': (39.0333, 43.0333), 'end': (43.0333, 48.0333)}
seg, frz = meta['seg'], meta['frz']
music = np.zeros_like(out)
def mput(sig, t, g=1.0):
    a = S(t); b = min(N, a + len(sig)); music[a:b] += sig[:b - a] * g
for i, (a, b, off) in enumerate(seg):
    oa, ob = OLD[f'act{i + 1}']; m = clip(oa, ob)
    mput(fade(m, .04 if i else .3, .06), a + off)
for i, (s0, D, fr) in enumerate(frz):   # 选项段：悬疑段压低 + 低通
    oa, _ = OLD[f'ch{i + 1}']; m = lp(clip(oa, oa + D), 1400)
    mput(fade(m, .05, .08), s0, .55)
ea, eb = OLD['end']; mput(fade(clip(ea, eb), .02, 1.0), meta['end0'])

# ---- 人声闪避（只压音乐） ----
venv = np.zeros(N, np.float32)
for a, b, off in seg:
    p = v[S(a):S(b)]; o0 = S(a + off); venv[o0:o0 + len(p)] = np.abs(p[:N - o0])
hop = S(.01); fr_ = np.array([venv[i:i + hop].max() for i in range(0, N, hop)])
act = (fr_ > .03).astype(np.float32)
g = np.ones_like(act); cur = 1.0
for i, on in enumerate(act):   # attack 40ms / release 350ms
    tgt = .3 if on else 1.0; k = .25 if tgt < cur else .028; cur += (tgt - cur) * k; g[i] = cur
gain = np.repeat(g, hop)[:N]
music *= gain[:, None]
pk = np.abs(music).max(); music *= .5 / pk
out += music

# ---- 选项节奏元素 ----
ticks = meta['ticks']; ti = 0
for kind, t in ticks:
    if kind == 'start': put(thump(60, .16, .9), t); put(boom(), t, .35)
    elif kind == 'tick': ti += 1; put(tick(1.0 if ti % 2 else .8), t, .55); put(thump(48, .1, .5), t)
    elif kind == 'click': put(boom(), t, .8)
    elif kind == 'end': put(boom(), t, 1.0)
for i, (s0, D, fr) in enumerate(frz):
    rd = (2.0 if i < 2 else D) - .3
    put(riser(rd), s0 + .3, .22)

out = np.tanh(out * 1.1) / np.tanh(1.1)
out = out[:S(END)]; out *= .9 / np.abs(out).max()
n2 = S(.8); out[-n2:] *= np.linspace(1, 0, n2)[:, None]
sf.write(ROOT + '包装素材v1/audio/bgm_v2_选项节奏.wav', out, SR)
print('ok', len(out) / SR, 'peak', np.abs(out).max())
