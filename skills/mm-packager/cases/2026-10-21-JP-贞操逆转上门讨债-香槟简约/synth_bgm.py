# v3 原创 BGM：暗色 R&B / lo-fi 律动，D 小调，96 BPM，按成片时间轴分段（重做，不用编辑器自带曲）
# 开头 0–3 铺垫+重音 | 第一幕 3–17.6 低频脉冲+拨弦 | 选项 留白悬念 | 第二幕 22–35.8 全律动 | 第三幕 40.2–52.6 律动+铃声旋律 | 片尾 56.4 收束
import numpy as np, os
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, lfilter, sosfilt
SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'audio'); os.makedirs(OUT, exist_ok=True)
TOTAL = 69.0   # v4 时间轴：选项 6.4s（犹豫 2s）/ 第三幕选项 5.4s / 手机聊天 62.0–66.6 / 片尾 66.6–69.0
BPM = 96; B = 60 / BPM; BAR = 4 * B
NM = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11}
def m(s): return 12 * (int(s[-1]) + 1) + NM[s[:-1]]
def hz(x): return 440 * 2 ** (((m(x) if isinstance(x, str) else x) - 69) / 12)
def tt(d): return np.arange(int(d * SR)) / SR
def env(n, a=.005, tau=.5, rel=.04):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / tau)
    r = min(n, int(rel * SR)); e[-r:] *= np.linspace(1, 0, r); return e
def lp(x, f, o=2): return sosfilt(butter(o, f / (SR / 2), output='sos'), x, axis=0)
def hp(x, f, o=2): return sosfilt(butter(o, f / (SR / 2), 'high', output='sos'), x, axis=0)

L = np.zeros((int(TOTAL * SR) + SR * 3, 2))
def put(x, at, pan=0., g=1.):
    if at < 0: x = x[int(-at * SR):]; at = 0
    i = int(at * SR); x = x[:len(L) - i]
    if x.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4); x = np.stack([x * l, x * r], 1) * 1.414
    L[i:i + len(x)] += x * g

# ---------------- 音色 ----------------
def sub(f, d):
    t = tt(d); return (np.sin(2 * np.pi * f * t) + .18 * np.sin(4 * np.pi * f * t)) * env(len(t), .008, .9, .08)
def kick(v=1):
    t = tt(.42); ph = 2 * np.pi * np.cumsum(46 + 120 * np.exp(-t / .03)) / SR
    return v * np.tanh(1.6 * np.sin(ph)) * env(len(t), .001, .16, .05)
def rim(v=1):   # 闷声木质“嗒”（无噪声）
    t = tt(.09); s = np.sin(2 * np.pi * 1650 * t) * np.exp(-t / .012) + .6 * np.sin(2 * np.pi * 620 * t) * np.exp(-t / .02)
    return v * s
_rng = np.random.default_rng(7)
def hat(v=1):   # 极轻闭镲（滤波短噪声，很小声）
    n = int(.05 * SR); s = hp(_rng.standard_normal(n), 7000, 4) * np.exp(-np.arange(n) / SR / .011)
    return v * s * .35
def ep(f, d, v=1):   # FM 电钢
    t = tt(d); s = np.sin(2 * np.pi * f * t + 1.3 * np.exp(-t / .4) * np.sin(2 * np.pi * f * t)) * (1 + .1 * np.sin(2 * np.pi * 4.2 * t))
    return v * s * env(len(t), .006, 1.4, .25)
def pluck(f, v=1):
    t = tt(.6); s = np.sin(2 * np.pi * f * t + .9 * np.exp(-t / .06) * np.sin(2 * np.pi * 2 * f * t))
    return v * s * env(len(t), .002, .16, .05)
def bell(f, d=1.6, v=1):
    t = tt(d); s = np.sin(2 * np.pi * f * t + .8 * np.exp(-t / .3) * np.sin(2 * np.pi * f * 3.5 * t)) + .2 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / .4)
    return v * s * env(len(t), .003, .7, .2)
def pad(notes, d, v=1, att=.8):
    t = tt(d); s = np.zeros(len(t))
    for n in notes:
        f = hz(n)
        for k, dt in enumerate((-.0035, 0, .0035)): s += np.sin(2 * np.pi * f * (1 + dt) * t + k) + .12 * np.sin(4 * np.pi * f * (1 + dt) * t)
    a = np.minimum(1, t / att) * np.minimum(1, (d - t) / .5)
    return v * lp(s, 2400) * a / len(notes) / 3
def boom(v=1):
    t = tt(2.2); ph = 2 * np.pi * np.cumsum(34 + 60 * np.exp(-t / .08)) / SR
    return v * np.sin(ph) * env(len(t), .002, .7, .3)
def swell(d, v=1, f0=200, f1=1800):   # 音调上扬的柔和铺垫（无噪声）
    t = tt(d); f = f0 * (f1 / f0) ** (t / d); ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + .5 * np.sin(1.5 * ph) + .3 * np.sin(2.01 * ph)
    return v * s * (t / d) ** 2.2 * .25

CH = [('D3', ['F3', 'A3', 'C4', 'E4']), ('Bb2', ['D3', 'F3', 'A3', 'C4']), ('G2', ['Bb2', 'D3', 'F3', 'A3']), ('A2', ['C#3', 'E3', 'G3', 'Bb3'])]

def groove(t0, t1, lvl):
    """lvl 1=第一幕（暗、脉冲） 2=第二幕（全律动） 3=第三幕（暧昧、旋律）"""
    nb = int(np.ceil((t1 - t0) / BAR))
    mel = [('A4', 0), ('C5', 1.5), ('D5', 2), ('F5', 3.5), ('E5', 4), ('D5', 5.5), ('C5', 6), ('A4', 7)]
    for b in range(nb):
        T = t0 + b * BAR; root, ch = CH[b % 4]
        if T >= t1: break
        put(pad(ch, min(BAR + .4, t1 - T + .3), .55 if lvl == 1 else .5), T, 0, .9)
        fr = hz(root)
        for bt, mul, dur in [(0, 1, 1.3), (1.5, 1, .45), (2.5, 2, .5), (3.5, 1, .45)]:
            if T + bt * B < t1: put(sub(fr * mul / 2 if lvl == 1 else fr * mul, dur * B * 1.6), T + bt * B, 0, .85 if lvl == 1 else .7)
        for bt in ([0, 2] if lvl == 1 else [0, 1.75, 2]):
            if T + bt * B < t1: put(kick(), T + bt * B, 0, .55 if lvl == 1 else .75)
        if lvl >= 2:
            for bt in [1, 3]:
                if T + bt * B < t1: put(rim(), T + bt * B, .1, .35)
            for i in range(8):
                if T + i * B / 2 < t1: put(hat(), T + i * B / 2, -.3 + .6 * (i % 2), .5 if i % 2 else .3)
        # 第一幕：八分音符拨弦琶音（压抑的催促感）
        if lvl == 1:
            arp = [ch[0], ch[2], ch[1], ch[3]] * 2
            for i, n in enumerate(arp):
                if T + i * B / 2 < t1: put(pluck(hz(n) * 2), T + i * B / 2, -.4 + .8 * (i % 2), .16)
        if lvl == 2:
            for i, bt in enumerate([0, 2.5]):
                for n in ch: put(ep(hz(n) * 2, 1.4, .09), T + bt * B + i * .012, .2)
        if lvl == 3:
            for i, bt in enumerate([0, 2.5]):
                for n in ch: put(ep(hz(n) * 2, 1.6, .08), T + bt * B, -.2)
            if b % 2 == 0:
                for n, bt in mel:
                    if T + bt * B < t1: put(bell(hz(n), 1.4), T + bt * B, .25, .14)

# ---------------- 鼓组 / 低音 / 主旋律（v5：三幕递进） ----------------
def noise(d): return _rng.standard_normal(int(d * SR))
def kick2(v=1):
    t = tt(.5); ph = 2 * np.pi * np.cumsum(50 + 150 * np.exp(-t / .025)) / SR
    body = np.tanh(2.2 * np.sin(ph)) * env(len(t), .001, .22, .05)
    click = hp(noise(.01), 2000) * np.exp(-np.arange(int(.01 * SR)) / SR / .002) * .5
    body[:len(click)] += click; return v * body
def snare(v=1):
    t = tt(.3); tone = (np.sin(2 * np.pi * 190 * t) + .5 * np.sin(2 * np.pi * 330 * t)) * np.exp(-t / .06)
    nz = lp(hp(noise(.3), 1400), 9000) * np.exp(-t / .11)
    return v * (tone * .6 + nz * .9)
def clap(v=1):
    n = int(.32 * SR); s = np.zeros(n); t = np.arange(n) / SR; nz = lp(hp(noise(.32), 900), 6000)
    for k, dt in enumerate((0, .011, .022)):
        i = int(dt * SR); e = np.exp(-(t[:n - i]) / .006); s[i:] += nz[:n - i] * e * (.7 if k < 2 else 1)
    s += nz * np.exp(-t / .13) * .45; return v * s
def ohat(v=1):
    n = int(.35 * SR); return v * hp(noise(.35), 6500, 4) * np.exp(-np.arange(n) / SR / .13) * .35
def crash(v=1):
    n = int(2.0 * SR); return v * hp(noise(2.0), 3500, 2) * np.exp(-np.arange(n) / SR / .7) * .3
def tom(f, v=1):
    t = tt(.35); ph = 2 * np.pi * np.cumsum(f * (1 + .6 * np.exp(-t / .04))) / SR
    return v * np.tanh(1.5 * np.sin(ph)) * np.exp(-t / .16)
def b808(f, d, v=1, drive=2.0):
    t = tt(d); ph = 2 * np.pi * np.cumsum(f * (1 + .25 * np.exp(-t / .03))) / SR
    return v * np.tanh(drive * np.sin(ph)) / np.tanh(drive) * env(len(t), .003, max(.2, d * .9), .05)
def saw(f, d, v=1, cut=3200):
    t = tt(d); s = sum(np.sin(2 * np.pi * f * k * t * (1 + .002 * (-1) ** k)) / k for k in range(1, 14))
    return v * lp(s, cut) * env(len(t), .01, d * .8, .08) * .35
def riser(d, v=1):
    n = int(d * SR); t = np.arange(n) / SR; s = hp(noise(d), 800, 2) * (t / d) ** 2.5
    return v * s * .4 + v * swell(d, .7, 300, 3000)[:n]
def roll(t_end, beats=1.0, v=.6):   # 军鼓加花：16 分 → 32 分
    t = t_end - beats * B; k = 0
    while t < t_end - 1e-3:
        p = 1 - (t_end - t) / (beats * B); put(snare(v * (.4 + .6 * p)), t, .15 * (-1) ** k, .55); k += 1
        t += B / 4 if p < .5 else B / 8
def fill_toms(t_end):
    for i, f in enumerate([220, 180, 140, 110]): put(tom(f, .8), t_end - B + i * B / 4, -.4 + .27 * i, .6)

LEAD = [('D5', 0, .5), ('F5', .5, .5), ('A5', 1, 1), ('G5', 2, .5), ('F5', 2.5, .5), ('E5', 3, 1),
        ('D5', 4, .5), ('E5', 4.5, .5), ('F5', 5, 1), ('A5', 6, .75), ('C6', 6.75, .5), ('A5', 7.25, .75)]
def drive(t0, t1, lvl):
    """lvl1 第一幕 半拍压迫；lvl2 第二幕 全律动+拍手+16分镲+加花；lvl3 第三幕 高潮：密集kick、镲片滚奇、锯齿主旋律、每2小节强音镲"""
    nb = int(np.ceil((t1 - t0) / BAR)); put(crash(.9 if lvl > 1 else .6), t0, 0, 1)
    for b in range(nb):
        T = t0 + b * BAR; root, ch = CH[b % 4]
        if T >= t1: break
        ok = lambda bt: T + bt * B < t1 - .02
        last_bar = T + BAR >= t1 - 1e-3
        put(pad(ch, min(BAR + .4, t1 - T + .3), .5 if lvl == 1 else .42), T, 0, .8)
        fr = hz(root)
        kicks = {1: [0, 2.5], 2: [0, .75, 2, 2.5], 3: [0, .75, 1.5, 2, 2.5, 3.5]}[lvl]
        for bt in kicks:
            if ok(bt): put(kick2(), T + bt * B, 0, {1: .85, 2: .95, 3: 1.0}[lvl])
        for bt in ([2] if lvl == 1 else [1, 3]):
            if ok(bt):
                put(snare(), T + bt * B, .05, {1: .6, 2: .7, 3: .8}[lvl])
                if lvl >= 2: put(clap(), T + bt * B, -.1, .45 if lvl == 2 else .6)
        step = .5 if lvl == 1 else .25
        for i in range(int(4 / step)):
            bt = i * step
            if not ok(bt): continue
            acc = 1 if i % 2 == 0 else .55
            if lvl == 3 and b % 2 == 1 and bt >= 3: put(hat(.9), T + bt * B, .3, .55); put(hat(.7), T + (bt + step / 2) * B, -.3, .45)
            else: put(hat(), T + bt * B, -.3 + .6 * (i % 2), (.55 if lvl > 1 else .45) * acc)
        if lvl >= 2:
            for bt in [1.5, 3.5]:
                if ok(bt): put(ohat(), T + bt * B, .35, .5)
        if lvl == 3 and b % 2 == 0: put(crash(.55), T, -.2, .8)
        if last_bar: roll(min(t1, T + BAR), 1.0 if lvl < 3 else 2.0, .7); put(riser(min(BAR, t1 - T), .8 if lvl == 3 else .55), T, 0, .6)
        elif b % 4 == 3 and lvl >= 2: fill_toms(T + BAR)
        bass = {1: [(0, 1.4), (2.5, 1.2)], 2: [(0, .7), (.75, .6), (2, .45), (2.5, .9), (3.5, .45)], 3: [(0, .45), (.75, .5), (1.5, .45), (2, .45), (2.5, .7), (3.5, .45)]}[lvl]
        for bt, d in bass:
            if ok(bt): put(b808(fr / 2 if lvl == 1 else fr, d * B * 1.2, 1, 1.6 + .8 * lvl), T + bt * B, 0, {1: .7, 2: .62, 3: .66}[lvl])
        if lvl == 1:
            arp = [ch[0], ch[2], ch[1], ch[3]] * 2
            for i, n in enumerate(arp):
                if ok(i / 2): put(pluck(hz(n) * 2), T + i * B / 2, -.4 + .8 * (i % 2), .18)
        if lvl >= 2:
            for bt in ([0, 1.5, 2.5] if lvl == 2 else [0, .75, 1.5, 2.5, 3.25]):
                if ok(bt):
                    for n in ch: put(ep(hz(n) * 2, .6, .08), T + bt * B, .2)
        if lvl == 3:
            bb = (b % 2) * 4
            for n, bt, d in LEAD:
                if bb <= bt < bb + 4 and ok(bt - bb): put(saw(hz(n), d * B * 1.1, .6), T + (bt - bb) * B, -.15, .5)
            if b % 2 == 0:
                for n, bt in [('A5', 0), ('D6', 1.5), ('F5', 3)]:
                    if ok(bt): put(bell(hz(n), 1.2), T + bt * B, .3, .1)

def suspense(t0, d, chord):
    """选项留白：只留延音和弦 + 每拍轻敲 + 结尾上扬"""
    put(pad(chord, d + .3, .7, att=.3), t0, 0, .85)
    put(sub(hz('A1'), d), t0, 0, .5)
    for i in range(int(d / B)): put(rim(.6), t0 + i * B, .3 * (-1) ** i, .22)
    put(swell(min(1.4, d), .9), t0 + d - min(1.4, d), 0, .6)

# ---------------- 编排（对齐成片时间轴） ----------------
put(pad(['D3', 'A3', 'F4', 'E4'], 3.4, .8, att=.2), 0, 0, .8)
put(swell(.9, .6, 160, 900), .05)
put(boom(1.0), 1.0); put(sub(hz('D1') * 2, 1.9), 1.0, 0, .75)   # 标题「転移する」砸下
put(bell(hz('A5'), 1.6), 1.75, .2, .12); put(bell(hz('D5'), 1.6), 1.9, -.2, .1)   # 目标出现
put(swell(.6, .8, 300, 2400), 2.4)
drive(3.0, 17.6, 1); put(boom(.7), 3.0)
suspense(17.6, 6.4, ['A2', 'E3', 'G3', 'D4'])
drive(24.0, 37.8, 2); put(boom(.7), 24.0)
suspense(37.8, 6.4, ['A2', 'E3', 'G3', 'C#4'])
drive(44.2, 56.6, 3); put(boom(.8), 44.2)
suspense(56.6, 5.4, ['Bb2', 'F3', 'A3', 'D4'])
drive(62.0, 66.6, 2); put(boom(.6), 62.0)   # 手机聊天
put(boom(.9), 66.6); put(pad(['D3', 'A3', 'C4', 'E4', 'F4'], 2.6, .8, att=.05), 66.6, 0, .9)
put(bell(hz('A5'), 2.2), 66.6, .2, .16); put(bell(hz('D5'), 2.2), 66.75, -.2, .14)

# ---------------- 混响 / 母带 ----------------
def reverb(x, sec=2.0, mix=.22):
    n = int(sec * SR); rng = np.random.default_rng(3); out = np.zeros_like(x)
    for c in range(2):
        ir = np.zeros(n)
        for k in range(1500):
            d = rng.uniform(.01, sec); ir[int(d * SR)] += np.exp(-d / (sec / 5)) * rng.choice([-1, 1])
        ir = lfilter(*butter(2, 4500 / (SR / 2)), ir); ir /= np.sqrt((ir ** 2).sum()) + 1e-9
        out[:, c] = fftconvolve(x[:, c], ir)[:len(x)]
    return x * (1 - mix) + out * mix * 1.5
X = reverb(L)[:int(TOTAL * SR)]
X = hp(X, 28)
fo = int(.6 * SR); X[-fo:] *= np.linspace(1, 0, fo)[:, None]
X = np.tanh(X / (np.abs(X).max() + 1e-9) * 1.3) / np.tanh(1.3) * .89
wavfile.write(os.path.join(OUT, 'bgm_v5.wav'), SR, (X * 32767).astype(np.int16))
print('ok', X.shape[0] / SR)
