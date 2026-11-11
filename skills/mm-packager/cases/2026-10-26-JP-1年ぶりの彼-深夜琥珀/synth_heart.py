# 心跳 lub-dub 合成（低频正弦脉冲 + 轻微失真）
import numpy as np, wave, os
sr = 44100; D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'audio')
def thump(f0, dur, amp):
    t = np.arange(int(sr * dur)) / sr; f = f0 * (1 + 1.2 * np.exp(-t * 40))
    ph = 2 * np.pi * np.cumsum(f) / sr; env = (1 - np.exp(-t * 400)) * np.exp(-t * 18)
    return amp * np.tanh(1.6 * np.sin(ph) * env)
x = np.zeros(int(sr * .5)); a = thump(52, .28, .95); b = thump(46, .26, .7)
x[:len(a)] += a; o = int(sr * .17); x[o:o + len(b)] += b
x = x / np.max(np.abs(x)) * .9; s = (np.stack([x, x], 1) * 32767).astype(np.int16)
w = wave.open(os.path.join(D, 's_heart.wav'), 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(s.tobytes()); w.close(); print('ok')
