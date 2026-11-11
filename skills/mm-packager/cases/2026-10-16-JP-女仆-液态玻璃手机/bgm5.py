"""Re-fit the MusicGen score (bgm_maid_drama_s11.wav, sections cut on the old timeline) to the v5 timeline."""
import numpy as np, wave
w = wave.open('audio/bgm_maid_drama_s11.wav'); sr = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, 2) / 32768
S = lambda t: int(round(t * sr)); XF = S(0.12)
def xjoin(x, y):
    r = np.linspace(0, 1, XF)[:, None]
    return np.concatenate([x[:-XF], x[-XF:] * (1 - r) + y[:XF] * r, y[XF:]])
def fit(seg, L, loop=(0.3, 0.7)):
    """stretch to L seconds by looping a middle chunk (crossfaded); keeps head + tail intact"""
    n = S(L)
    if len(seg) >= n: return seg[:n]
    a0, b0 = int(len(seg) * loop[0]), int(len(seg) * loop[1])
    head, mid, tail = seg[:b0], seg[a0:b0], seg[b0:]
    out = head
    while len(out) + len(tail) - XF < n + XF: out = xjoin(out, mid)
    if len(tail) > 2 * XF: out = xjoin(out, tail)
    return out[:n]
# old sections (s): title+act1 0-9.07 | ch1 9.07-12.6 | act2a 12.6-15.74 (climax at end) | act2b 15.74-18.1 | ch2 18.1-21.7 | end 21.7-26.2
sec = lambda t0, t1: a[S(t0):S(t1)]
PL = [  # (segment, start, length) on the new output timeline
    (sec(0, 2.0), 0.0, 2.8, (0.45, 0.95)), (sec(2.0, 9.07), 2.8, 7.067, None), (sec(9.07, 12.6), 9.867, 4.4, (0.3, 0.7)),
    (sec(12.6, 15.74), 14.267, 3.473, (0.1, 0.5)), (sec(15.74, 18.1), 17.74, 2.36, None), (sec(18.1, 21.7), 20.1, 8.0, (0.15, 0.85)),
    (sec(21.7, 26.2), 28.9, 5.0, (0.2, 0.6))]
out = np.zeros((S(33.9) + XF * 2, 2))
for seg, st, L, lp_ in PL:
    x = fit(seg, L + XF / sr, lp_ or (0.3, 0.7)).copy() if lp_ or len(seg) < S(L) + XF else seg[:S(L) + XF].copy()
    x = x[:S(L) + XF]
    if st > 0: x[:XF] *= np.linspace(0, 1, XF)[:, None]
    x[-XF:] *= np.linspace(1, 0, XF)[:, None]
    i = S(st); out[i:i + len(x)] += x[:len(out) - i]
t = np.arange(len(out)) / sr
# time-up at 23.1 → bed sinks (-9 dB, muffled) until the end card at 28.1
def lp(x, al):
    y = np.empty_like(x); s = np.zeros(2)
    for i in range(len(x)): s += al * (x[i] - s); y[i] = s
    return y
duck = np.clip((t - 23.2) / 0.3, 0, 1) * (1 - np.clip((t - 28.7) / 0.3, 0, 1))
out = out * (1 - duck)[:, None] + lp(out, 0.06) * duck[:, None] * 10 ** (-9 / 20)
out = out[:S(33.9)]
f = S(1.0); out[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
out = out / np.abs(out).max() * 0.95
o = wave.open('audio/bgm_maid_drama5.wav', 'wb'); o.setnchannels(2); o.setsampwidth(2); o.setframerate(sr); o.writeframes((out * 32767).astype('<i2').tobytes())
print('ok', len(out) / sr)
