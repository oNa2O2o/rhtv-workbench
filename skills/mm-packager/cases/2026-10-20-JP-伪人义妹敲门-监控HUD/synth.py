# -*- coding: utf-8 -*-
"""微恐 BGM + 丝滑音效（纯正弦/滑音合成，无噪声、无硬瞬态、无清脆高音）"""
import os, wave, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', 'audio')); os.makedirs(OUT, exist_ok=True)
SR = 44100
def save(name, x, st=None):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1: x = np.stack([x, x], 1)
    pk = np.max(np.abs(x)) or 1; x = x / pk * .89
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype('<i2').tobytes())
    print('saved', name, round(len(x) / SR, 2))
def T(d): return np.arange(int(d * SR)) / SR
def env(n, a, r, shape=2.0):
    """平滑包络：正弦形起音 a 秒、余弦形收尾 r 秒"""
    e = np.ones(n); A = int(a * SR); R = int(r * SR)
    if A: e[:A] = np.sin(np.linspace(0, np.pi / 2, A)) ** shape
    if R: e[-R:] *= np.cos(np.linspace(0, np.pi / 2, R)) ** shape
    return e
def glide(f0, f1, d, curve='exp'):
    t = T(d); k = t / d
    f = f0 * (f1 / f0) ** k if curve == 'exp' else f0 + (f1 - f0) * k
    return 2 * np.pi * np.cumsum(f) / SR
def tone(ph, harm=(1, .25, .08)):
    return sum(a * np.sin(ph * (i + 1)) for i, a in enumerate(harm))
def lp(x, a=.08):  # 一阶低通，去掉锋利感
    from scipy.signal import lfilter
    return lfilter([a], [1, a - 1], x)

# ---------------- BGM ----------------
def bgm(D=44.8):
    t = T(D); n = len(t); L = np.zeros(n); R = np.zeros(n)
    # 低频 pad：D 小调，左右轻微失谐产生“不安”的拍频
    for f, a in ((73.42, .5), (110.0, .35), (146.83, .28), (174.61, .16)):
        lfo = .75 + .25 * np.sin(2 * np.pi * (.07 + f / 4000) * t)
        L += a * lfo * tone(2 * np.pi * (f - .35) * t, (1, .3, .1))
        R += a * lfo * tone(2 * np.pi * (f + .35) * t, (1, .3, .1))
    pad_env = env(n, 2.0, 1.6, 1)
    # 第三幕（25.6 起）张力层：小二度簇，渐强到 35，选项 3 保持，片尾回落
    k = np.clip((t - 31.0) / 10.0, 0, 1) ** 1.5 * (1 - np.clip((t - 41.9) / 1.2, 0, 1))
    for f, a in ((293.66, .18), (311.13, .15), (587.33, .05)):
        vib = 1 + .003 * np.sin(2 * np.pi * 4.3 * t)
        ph = 2 * np.pi * np.cumsum(f * vib) / SR
        L += a * k * np.sin(ph); R += a * k * np.sin(ph + .6)
    # 走调的摇篮曲：柔起音（120ms）、长尾、轻颤音 → 不清脆
    mel = [(1.2, 69), (2.1, 65), (3.0, 64), (3.9, 62), (5.2, 69), (6.1, 70), (7.0, 69), (7.9, 65),
           (15.4, 69), (16.3, 65), (17.2, 64), (18.1, 62), (19.4, 64), (20.3, 65), (21.2, 64), (22.1, 61),
           (31.9, 62), (33.3, 61), (34.7, 60)]
    for st, m in mel:
        f = 440 * 2 ** ((m - 69) / 12) * .995
        d = 2.4; i0 = int(st * SR); tt = T(d)
        vib = 1 + .006 * np.sin(2 * np.pi * 5.2 * tt)
        ph = 2 * np.pi * np.cumsum(f * vib) / SR
        x = (np.sin(ph) + .18 * np.sin(2 * ph)) * env(len(tt), .12, 1.6, 1.2) * np.exp(-tt * .9) * .22
        x = x[:max(0, min(len(x), n - i0))]
        L[i0:i0 + len(x)] += x * .9; R[i0:i0 + len(x)] += x * 1.0
        j0 = i0 + int(.33 * SR); x2 = x[:max(0, min(len(x), n - j0))] * .35   # 柔回声
        L[j0:j0 + len(x2)] += x2 * .6; R[j0:j0 + len(x2)] += x2
    # 片尾深层涌起
    e0 = int(41.77 * SR); d = D - 41.77; tt = T(d)
    sw = (np.sin(2 * np.pi * 55 * tt) + .5 * np.sin(2 * np.pi * 82.4 * tt)) * env(len(tt), .5, 1.2, 1) * .55
    L[e0:e0 + len(sw)] += sw; R[e0:e0 + len(sw)] += sw
    out = np.stack([L * pad_env, R * pad_env], 1)
    out[:, 0] = lp(out[:, 0], .2); out[:, 1] = lp(out[:, 1], .2)
    save('bgm_horror', out * env(n, .05, 1.0, 1)[:, None])

# ---------------- 音效 ----------------
def sfx():
    d = .75; ph = glide(380, 1050, d); n = len(ph)
    x = (np.sin(ph) + .5 * np.sin(ph * .5) + .2 * np.sin(ph * 1.003)) * env(n, .25, .4, 1.5)
    save('s_scan', lp(x, .25))
    d = 1.0; ph = glide(200, 470, d); n = len(ph); t = T(d)
    x = (np.sin(ph) + .7 * np.sin(ph * 1.012) + .3 * np.sin(ph * 2)) * env(n, .35, .5, 1.5)
    save('s_ghost', lp(x, .2))
    d = .8; ph = glide(640, 170, d); n = len(ph)
    x = (np.sin(ph) + .4 * np.sin(ph * 1.5)) * env(n, .08, .55, 1.5)
    save('s_drop', lp(x, .18))
    d = .6; ph = glide(170, 360, d); n = len(ph)
    x = (np.sin(ph) + .4 * np.sin(2 * ph)) * env(n, .3, .28, 1.4)
    save('s_panel', lp(x, .15))
    d = .9; t = T(d); n = len(t)
    x = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((293.66, 1), (440, .6), (587.33, .3))) * env(n, .07, .75, 1.3)
    save('s_pick', lp(x, .18))
    d = .6; ph = glide(620, 280, d); n = len(ph); e = np.linspace(0, 1, n) ** 2.2 * env(n, 0, .12, 1)
    x = (np.sin(ph) + .5 * np.sin(ph * 1.01)) * e
    save('s_vanish', lp(x, .2))
    d = 1.3; ph = glide(150, 70, d); n = len(ph); t = T(d)
    x = (np.sin(ph) + .8 * np.sin(ph * 1.06) + .5 * np.sin(ph * 2.01)) * env(n, .2, .8, 1.3)
    save('s_glitch', lp(x, .15))
    d = .4; t = T(d); n = len(t)
    x = (np.sin(2 * np.pi * 262 * t) + .3 * np.sin(2 * np.pi * 392 * t)) * env(n, .08, .3, 1.5)
    save('s_hover', lp(x, .15))
    d = 1.6; t = T(d); n = len(t)
    x = (np.sin(2 * np.pi * 73.4 * t) + .6 * np.sin(2 * np.pi * 110 * t) + .3 * np.sin(2 * np.pi * 146.8 * t)) * env(n, .35, 1.0, 1.3)
    save('s_end', lp(x, .12))
    d = 1.1; ph = glide(220, 330, d); n = len(ph)
    x = (np.sin(ph) + .5 * np.sin(ph * 1.5) + .3 * np.sin(ph * .5)) * env(n, .4, .55, 1.4)
    save('s_title', lp(x, .15))
    d = .35; t = T(d); n = len(t)
    x = np.sin(2 * np.pi * 180 * t) * env(n, .04, .26, 1.5)
    save('s_tap', lp(x, .12))

if __name__ == '__main__':
    bgm(); sfx()
