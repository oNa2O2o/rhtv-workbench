import numpy as np, wave, os
SR = 44100; R = np.random.default_rng(7)
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')
def save(n, x, peak=0.9):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    if x.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(os.path.join(D, n), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype('<i2').tobytes())
def t(d): return np.arange(int(d * SR)) / SR
def lp(x, a):  # one-pole lowpass
    y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y
def env(n, a, r): e = np.ones(n); A = int(a * SR); Rr = int(r * SR); e[:A] = np.linspace(0, 1, A) ** 2; e[-Rr:] *= np.linspace(1, 0, Rr) ** 2; return e

# 1) soft censor: rounded "pi" — sine 740 Hz + soft octave, gentle 25 ms attack / 90 ms release, slight vibrato. No square harmonics.
x = t(0.44); f = 740 * (1 + 0.006 * np.sin(2 * np.pi * 6 * x))
ph = 2 * np.pi * np.cumsum(f) / SR
cen = (np.sin(ph) + 0.18 * np.sin(2 * ph)) * env(len(x), 0.025, 0.09)
save('censor_soft.wav', cen, 0.5)

# 2) slap: skin smack = very short broadband burst (bandpassed noise 1-6k) + body thump 140 Hz + room tail
n = int(0.6 * SR); s = np.zeros(n)
nb = R.standard_normal(int(0.05 * SR)); nb = nb - lp(nb, 0.12); nb = lp(nb, 0.55)
nb *= np.exp(-np.arange(len(nb)) / (0.008 * SR)); s[:len(nb)] += nb * 1.0
x = t(0.18); s[:len(x)] += 0.7 * np.sin(2 * np.pi * (180 * np.exp(-x * 18) + 90) * x) * np.exp(-x * 28)
tail = R.standard_normal(n) * np.exp(-np.arange(n) / (0.09 * SR)) * 0.08; s += lp(tail, 0.3)
save('slap_real.wav', s, 0.95)

# 3) glass shatter: crack transient + dense random tinkles (inharmonic damped partials 2.5-11 kHz) falling over ~1.1 s + low thud
n = int(1.6 * SR); g = np.zeros((n, 2))
cr = R.standard_normal(int(0.03 * SR)); cr = cr - lp(cr, 0.3); cr *= np.exp(-np.arange(len(cr)) / (0.004 * SR))
g[:len(cr)] += cr[:, None]
x = t(0.25); th = 0.5 * np.sin(2 * np.pi * 70 * x) * np.exp(-x * 20); g[:len(x)] += th[:, None]
for k in range(260):
    st = int((0.004 + (R.random() ** 1.8) * 1.1) * SR)
    d = 0.03 + R.random() * 0.22; m = int(d * SR)
    if st + m >= n: continue
    xx = np.arange(m) / SR; amp = (0.5 + R.random()) * np.exp(-st / SR * 2.2)
    sig = sum(np.sin(2 * np.pi * (2500 + R.random() * 8500) * xx * r) * w for r, w in ((1, 1), (2.76, .4), (5.4, .2)))
    sig = sig * np.exp(-xx / (d * 0.22)) * amp
    pan = R.random(); g[st:st + m, 0] += sig * (1 - pan); g[st:st + m, 1] += sig * pan
    if R.random() < 0.3:  # grit
        gr = R.standard_normal(m // 3); gr = gr - lp(gr, 0.5); g[st:st + len(gr)] += (gr * np.exp(-np.arange(len(gr)) / (0.003 * SR)) * amp * 0.5)[:, None]
save('shatter_real.wav', g, 0.9)

# 4) screen crack (phone glass splintering, quieter): crackle cluster 0-120 ms
n = int(0.4 * SR); c = np.zeros(n)
for k in range(40):
    st = int((R.random() ** 2) * 0.14 * SR); m = int(0.006 * SR)
    b = R.standard_normal(m); b = b - lp(b, 0.4); c[st:st + m] += b * np.exp(-np.arange(m) / (0.0015 * SR)) * (1 - st / n)
save('crack_real.wav', c, 0.7)
print('ok')
