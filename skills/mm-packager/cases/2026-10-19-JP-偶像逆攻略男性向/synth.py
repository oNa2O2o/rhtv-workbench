# Clean tonal BGM + SFX (no noise sources at all → no 沙沙). J-pop 王道進行, music box / EP / pad.
import numpy as np, os
from scipy.io import wavfile
from scipy.signal import fftconvolve
SR = 48000
OUT = 'F:/钟海明/2026/2026年10月19日MM-JP-偶像妄想迭代/包装素材v2/audio/'
os.makedirs(OUT, exist_ok=True)
N = lambda m: 440.0 * 2 ** ((m - 69) / 12)
NAMES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
def m(s):  # 'F#4' → midi
    return 12 * (int(s[-1]) + 1) + NAMES[s[:-1]]

def env(n, a=.005, tau=.6, rel=.05):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / tau)
    r = int(rel * SR); e[-r:] *= np.linspace(1, 0, r)
    return e

def musicbox(f, dur=1.6, v=1):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + .35 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t / .15) + .15 * np.sin(2 * np.pi * f * 5.98 * t) * np.exp(-t / .07)
    return v * s * env(n, .002, .55)

def bell(f, dur=2.0, v=1):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t + 1.2 * np.exp(-t / .25) * np.sin(2 * np.pi * f * 3.5 * t))
    return v * s * env(n, .003, .8)

def ep(f, dur=2.4, v=1):  # FM rhodes
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t + 1.6 * np.exp(-t / .35) * np.sin(2 * np.pi * f * t)) * (1 + .12 * np.sin(2 * np.pi * 4.5 * t))
    return v * s * env(n, .006, 1.3, .3)

def pad(fs, dur, v=1):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for f in fs:
        for d in (-.004, .004): s += np.sin(2 * np.pi * f * (1 + d) * t) + .2 * np.sin(4 * np.pi * f * (1 + d) * t)
    a = np.minimum(1, t / .6) * np.minimum(1, (dur - t) / .6)
    return v * s * a / len(fs) / 2

def bass(f, dur, v=1):
    n = int(dur * SR); t = np.arange(n) / SR
    return v * (np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t)) * env(n, .01, 1.0, .12)

def thump(dur=.35, v=1, f0=110, f1=48):
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-t / .04)) / SR
    return v * np.sin(ph) * env(n, .003, .12)

def put(buf, x, at):
    i = int(at * SR)
    if i >= len(buf): return
    x = x[:len(buf) - i]
    buf[i:i + len(x)] += x if x.ndim == buf.ndim else (np.stack([x, x], 1) if buf.ndim == 2 else x)

def putp(buf, x, at, pan=0):  # stereo with pan
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    put(buf, np.stack([x * l, x * r], 1) * 1.414, at)

def reverb(x, sec=2.2, mix=.28):
    # deterministic, smooth IR from many decaying sine partials (no noise)
    n = int(sec * SR); t = np.arange(n) / SR; rng = np.random.default_rng(3)
    out = np.zeros_like(x)
    for ch in range(2):
        ir = np.zeros(n)
        for k in range(1200):
            d = rng.uniform(.008, sec); g = np.exp(-d / (sec / 5)) * rng.choice([-1, 1])
            ir[int(d * SR)] += g
        ir[0] = 0
        from scipy.signal import butter, lfilter
        b, a = butter(2, 5200 / (SR / 2)); ir = lfilter(b, a, ir)
        ir /= np.sqrt((ir ** 2).sum()) + 1e-9
        out[:, ch] = fftconvolve(x[:, ch], ir)[:len(x)]
    return x * (1 - mix) + out * mix * 1.6

def norm(x, peak=.89):
    return x * peak / (np.abs(x).max() + 1e-9)

def save(name, x, peak=.89, rv=None):
    if x.ndim == 1: x = np.stack([x, x], 1)
    if rv: x = reverb(x, *rv)
    x = norm(x, peak)
    wavfile.write(OUT + name + '.wav', SR, (x * 32767).astype(np.int16)); print('saved', name, round(len(x) / SR, 2))

# ---------------- BGM ----------------
def bgm(total=32.4):
    BPM = 96; B = 60 / BPM; BAR = 4 * B
    buf = np.zeros((int((total + 3) * SR), 2))
    prog = [('G', ['G3', 'B3', 'D4', 'F#4'], 'G2'), ('A', ['A3', 'C#4', 'E4', 'F#4'], 'A2'), ('F#m', ['F#3', 'A3', 'C#4', 'E4'], 'F#2'), ('Bm', ['B3', 'D4', 'F#4', 'A4'], 'B2')]
    bars = prog * 2 + prog[:3] + [('Em7A', ['E3', 'G3', 'B3', 'D4'], 'E2')]  # 12 bars, bar 12 = ii (→V on beat 3)
    mel = {8: [(0, 'F#5', 1.5), (1.5, 'A5', .5), (2, 'B5', 1), (3, 'A5', 1)],
           9: [(0, 'E5', 1.5), (1.5, 'F#5', .5), (2, 'A5', 2)],
           10: [(0, 'C#5', 1), (1, 'E5', 1), (2, 'F#5', 1), (3, 'E5', 1)],
           11: [(0, 'D5', 1.5), (1.5, 'E5', .5), (2, 'G5', 1), (3, 'A5', 1)]}
    for i, (nm, ch, bs) in enumerate(bars):
        t0 = i * BAR; fs = [N(m(x)) for x in ch]
        if nm == 'Em7A': fs2 = [N(m(x)) for x in ['A3', 'C#4', 'E4', 'G4']]
        # pad
        if nm == 'Em7A':
            putp(buf, pad(fs, BAR / 2 + .3, .16), t0); putp(buf, pad(fs2, BAR / 2 + .3, .16), t0 + BAR / 2)
        else: putp(buf, pad(fs, BAR + .3, .16 if i < 8 else .2), t0)
        # music box arpeggio 8ths (up an octave)
        arp = [0, 1, 2, 3, 2, 1, 2, 3]
        for k, a in enumerate(arp):
            src = fs2 if (nm == 'Em7A' and k >= 4) else fs
            putp(buf, musicbox(src[a] * 2, 1.4, .30 if i < 4 else .24), t0 + k * B / 2, (-.35 if k % 2 else .35))
        # EP chords from bar 5
        if i >= 4:
            for b_, dur in ((0, 1.5), (1.5, 2.5)):
                src = fs2 if (nm == 'Em7A' and b_ >= 1.5) else fs
                for f in src: putp(buf, ep(f, dur * B + .6, .11), t0 + b_ * B, -.1)
        # bass + soft heartbeat thump from bar 5
        if i >= 4:
            putp(buf, bass(N(m(bs)), 2 * B, .32), t0)
            putp(buf, bass(N(m('A2' if nm == 'Em7A' else bs)), 2 * B, .28), t0 + 2 * B)
            for b_ in (0, 2.5): putp(buf, thump(v=.38), t0 + b_ * B)
        if i in mel:
            for b_, n_, d in mel[i]: putp(buf, bell(N(m(n_)), d * B + 1.2, .22), t0 + b_ * B, .15)
    # bar 13: resolve D, sparkle
    t0 = 12 * BAR; D = [N(m(x)) for x in ['D3', 'F#3', 'A3', 'C#4', 'E4']]
    putp(buf, pad(D, 3.0, .22), t0)
    for f in D: putp(buf, ep(f, 3.0, .12), t0)
    putp(buf, bass(N(m('D2')), 3.0, .35), t0)
    for k, n_ in enumerate(['D5', 'E5', 'F#5', 'A5', 'B5', 'D6', 'E6', 'F#6']): putp(buf, musicbox(N(m(n_)), 1.6, .22), t0 + .05 + k * .07, -.6 + k * .17)
    putp(buf, bell(N(m('A5')), 2.5, .2), t0 + .65)
    buf = buf[:int(total * SR)]
    fo = int(.6 * SR); buf[-fo:] *= np.linspace(1, 0, fo)[:, None]
    fi = int(.4 * SR); buf[:fi] *= np.linspace(0, 1, fi)[:, None]
    save('bgm_koi', buf, .8, (2.4, .3))

# ---------------- SFX ----------------
def sfx():
    def mk(d): return np.zeros((int(d * SR), 2))
    # title: sparkly glissando + soft low pon
    x = mk(1.6)
    for k, n_ in enumerate(['A5', 'B5', 'D6', 'E6', 'F#6', 'A6']): putp(x, musicbox(N(m(n_)), 1.0, .5), k * .045, -.5 + k * .2)
    putp(x, ep(N(m('D4')), 1.4, .6), 0); putp(x, ep(N(m('A4')), 1.4, .4), 0)
    save('sfx_title', x, .8, (1.6, .25))
    # node on (heart pop): "pyon"
    x = mk(.9); n = int(.16 * SR); t = np.arange(n) / SR
    sw = np.sin(2 * np.pi * np.cumsum(650 + 900 * (t / .16) ** .7) / SR) * env(n, .004, .08, .02)
    putp(x, sw * .7, 0); putp(x, musicbox(N(m('E6')), .8, .6), .07); putp(x, musicbox(N(m('A6')), .8, .4), .11)
    save('sfx_heart', x, .75, (1.2, .22))
    # day advance: harp-like ascending chime
    x = mk(1.5)
    for k, n_ in enumerate(['D5', 'F#5', 'A5', 'D6']): putp(x, bell(N(m(n_)), 1.2, .5), k * .09, -.3 + k * .2)
    save('sfx_day', x, .75, (1.6, .25))
    # lock: tonal click + descending "pin...pon" (denied, cute)
    x = mk(1.0); n = int(.03 * SR); t = np.arange(n) / SR
    clk = (np.sin(2 * np.pi * 2600 * t) + .6 * np.sin(2 * np.pi * 1700 * t)) * np.exp(-t / .006)
    putp(x, clk * .8, 0); putp(x, clk * .6, .07)
    putp(x, thump(.25, .6, 260, 140), .07)
    putp(x, bell(N(m('F5')), .7, .38), .12); putp(x, bell(N(m('B4')), .8, .38), .26)
    save('sfx_lock', x, .75, (1.0, .2))
    # bubble appear: soft marimba pon
    x = mk(.6); n = int(.6 * SR); t = np.arange(n) / SR
    mar = (np.sin(2 * np.pi * N(m('A5')) * t) + .3 * np.sin(2 * np.pi * N(m('A5')) * 4 * t) * np.exp(-t / .03)) * env(n, .002, .12)
    putp(x, mar * .7, 0); save('sfx_bubble', x, .6, (.8, .18))
    # monologue: soft "kira" twinkle (2 notes)
    x = mk(1.2); putp(x, musicbox(N(m('F#6')), 1.0, .5), 0, -.3); putp(x, musicbox(N(m('C#7')), 1.0, .35), .08, .3)
    save('sfx_kira', x, .5, (1.4, .3))
    # heartbeat doki-doki ×3
    x = mk(2.4)
    for k in range(3):
        putp(x, thump(.3, 1, 95, 42), k * .75); putp(x, thump(.3, .7, 90, 40), k * .75 + .2)
    save('sfx_doki', x, .85)
    # end shine: rising gliss + chord bell
    x = mk(2.4)
    for k, n_ in enumerate(['D5', 'E5', 'F#5', 'A5', 'B5', 'D6', 'E6', 'F#6', 'A6']): putp(x, musicbox(N(m(n_)), 1.2, .45), k * .035, -.6 + k * .15)
    for n_ in ['D5', 'F#5', 'A5']: putp(x, bell(N(m(n_)), 2.0, .35), .34)
    save('sfx_end', x, .8, (1.8, .28))
    # tap: soft tonal "pi" (rising per tap)
    for i, n_ in enumerate(['A6', 'B6', 'C#7', 'D7']):
        x = mk(.25); n = int(.25 * SR); t = np.arange(n) / SR
        tp = (np.sin(2 * np.pi * N(m(n_)) * t) + .2 * np.sin(2 * np.pi * N(m(n_)) * 2 * t)) * env(n, .001, .045, .02)
        putp(x, tp * .7, 0); putp(x, thump(.12, .25, 300, 160), 0); save(f'sfx_tap{i + 1}', x, .6)

if __name__ == '__main__' and len(__import__('sys').argv) == 1:
    bgm(); sfx()

# ---------------- Apple-style SFX (soft, short, pure sine, no low thumps) ----------------
def tink(f, dur=.5, v=1, tau=.12, a=.003):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + .08 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t / .03)
    return v * s * env(n, a, tau, .03)

def blip(f0, f1, dur=.07, v=1):
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(f0 + (f1 - f0) * (t / dur)) / SR
    return v * np.sin(ph) * np.sin(np.pi * t / dur) ** 1.5

def sfx_apple():
    mk = lambda d: np.zeros((int(d * SR), 2))
    x = mk(.9); putp(x, tink(N(m('E6')), .6, .6), 0, -.2); putp(x, tink(N(m('B6')), .6, .45), .09, .2); save('a_title', x, .32, (1.0, .18))
    x = mk(.4); putp(x, blip(520, 880, .075, .8), 0); putp(x, tink(N(m('A6')), .3, .25, .05), .05); save('a_node', x, .28, (.6, .12))
    x = mk(.9); putp(x, tink(N(m('C#6')), .6, .5), 0, -.15); putp(x, tink(N(m('F#6')), .6, .45), .08, .15); save('a_day', x, .28, (1.0, .18))
    x = mk(.6); putp(x, tink(N(m('F#6')), .5, .45, .09), 0); save('a_kira', x, .16, (.9, .2))
    # unlock: soft double click + rising airy chime
    x = mk(1.4); n = int(.02 * SR); t = np.arange(n) / SR
    clk = np.sin(2 * np.pi * 1800 * t) * np.exp(-t / .004)
    putp(x, clk * .5, 0); putp(x, clk * .4, .06)
    for k, n_ in enumerate(['A5', 'C#6', 'E6', 'A6']): putp(x, tink(N(m(n_)), .8, .45, .18), .12 + k * .06, -.3 + k * .2)
    save('a_unlock', x, .36, (1.2, .22))
    x = mk(1.4)
    for k, n_ in enumerate(['D6', 'F#6', 'A6']): putp(x, tink(N(m(n_)), 1.0, .5, .25), k * .07, -.2 + k * .2)
    save('a_end', x, .3, (1.4, .25))
    x = mk(.12); n = int(.03 * SR); t = np.arange(n) / SR
    tk = (np.sin(2 * np.pi * 2200 * t) + .5 * np.sin(2 * np.pi * 900 * t)) * np.exp(-t / .006)
    putp(x, tk, 0); save('a_tap', x, .22)

if __name__ == '__main__' and 'apple' in __import__('sys').argv: sfx_apple()
