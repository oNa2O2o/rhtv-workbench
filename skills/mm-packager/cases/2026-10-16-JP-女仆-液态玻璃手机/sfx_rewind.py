"""time-rewind sfx (~0.95 s): reversed ethereal swell + tape-scrub chirps rising in pitch + whir, ends on a soft 'tick' stop."""
import numpy as np, wave
SR = 44100; R = np.random.default_rng(9)
w = wave.open('audio/ether_full.wav'); e = np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, 2) / 32768
D = 0.95; n = int(D * SR); t = np.arange(n) / SR
rev = e[::-1][-n:] if len(e) >= n else np.pad(e[::-1], ((n - len(e), 0), (0, 0)))
rev = e[:n][::-1].copy()                                     # reversed head of the swell → sucks inward
out = rev * 0.8
# tape scrub: fast chirps (sped-up reversed blips) accelerating
k = 0.0; pos = 0.0
while pos < D - 0.05:
    gap = 0.075 * (1 - pos / D) + 0.022
    L = int(0.035 * SR); i = int(pos * SR)
    if i + L >= n: break
    tt = np.arange(L) / SR; f0 = 500 + 2600 * (pos / D) ** 1.5
    ch = np.sin(2 * np.pi * (f0 * tt + f0 * 3 * tt * tt / 0.035)) * np.hanning(L) * 0.35
    out[i:i + L, 0] += ch * (0.7 + 0.3 * R.random()); out[i:i + L, 1] += ch * (0.7 + 0.3 * R.random())
    pos += gap
# whir: band noise with rising tremolo
nz = R.standard_normal((n, 2)); y = np.empty_like(nz); s = np.zeros(2)
for i in range(n): s += 0.12 * (nz[i] - s); y[i] = s
trem = 0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(8 + 30 * t / D) / SR)
out += y * trem[:, None] * (t / D)[:, None] * 0.9
env = np.clip(t / 0.08, 0, 1) * (1 - np.clip((t - (D - 0.06)) / 0.06, 0, 1))
out *= env[:, None]
# stop tick
L = int(0.05 * SR); tt = np.arange(L) / SR
tick = np.sin(2 * np.pi * 1400 * tt) * np.exp(-tt * 90)
out = np.concatenate([out, np.zeros((int(0.12 * SR), 2))]); i = n - L // 2; out[i:i + L] += tick[:, None] * 0.6
out = out / np.abs(out).max() * 0.85
o = wave.open('F:/钟海明/2026/2026年10月10日MM-编辑器重构/app/public/audio/lgx-rewind.wav', 'wb')
o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((out * 32767).astype('<i2').tobytes()); print('ok', len(out) / SR)
