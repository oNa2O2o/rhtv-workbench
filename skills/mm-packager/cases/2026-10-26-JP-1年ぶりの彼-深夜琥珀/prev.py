# 静帧预览：原片帧 + 该时刻图层（x/y/opacity/scale 关键帧线性插值，以 ax/ay 为缩放中心）
import sys, json, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen
args = sys.argv[1:]
meta = json.load(open(os.path.join(gen.P, '包装素材v1', 'layers.json'), encoding='utf-8'))
order = {t[0]: i for i, t in enumerate(meta['tracks'])}
out = args[-1] if args[-1].endswith('.jpg') else 'prev.jpg'
ts = [float(x) for x in args if not x.endswith('.jpg')]
def val(k, prop, t, d):
    a = k.get(prop)
    if not a: return d
    if t <= a[0][0]: return a[0][1]
    for p, q in zip(a, a[1:]):
        if p[0] <= t <= q[0]: return p[1] if (len(p) > 2 and p[2] == 'hold') else p[1] + (q[1] - p[1]) * (t - p[0]) / max(1e-6, q[0] - p[0])
    return a[-1][1]
ims = []
for T in ts:
    v = (T - gen.OFF) if gen.OFF <= T < gen.F1 else ((T - gen.SH2) if gen.F1 + gen.FZ1 <= T < gen.F2 else None)
    c = gen.frame(v).convert('RGBA') if v is not None else None
    for L in sorted([l for l in meta['layers'] if l['start'] <= T < l['start'] + l['dur']], key=lambda l: -1 if l['track'] == 'V1' else order.get(l['track'], -99)):
        im = Image.open(os.path.join(gen.P, '包装素材v1', L['file'] + L.get('ext', '.png'))).convert('RGBA')
        if L['track'] == 'V1': c = im; continue
        t = T - L['start']; x, y, o, s = val(L['k'], 'x', t, 0), val(L['k'], 'y', t, 0), val(L['k'], 'opacity', t, 1), val(L['k'], 'scale', t, 1)
        if abs(s - 1) > 1e-3:
            ax, ay = L['ax'] * 1080, L['ay'] * 1920
            big = im.resize((int(1080 * s), int(1920 * s)), Image.BILINEAR)
            lay = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); lay.paste(big, (int(ax - ax * s), int(ay - ay * s))); im = lay
        if o < .999:
            a = np.array(im); a[..., 3] = (a[..., 3] * max(0, o)).astype(np.uint8); im = Image.fromarray(a)
        lay = Image.new('RGBA', c.size, (0, 0, 0, 0)); lay.paste(im, (int(round(x)), int(round(y)))); c.alpha_composite(lay)
    ims.append(c.convert('RGB').resize((432, 768)))
S = Image.new('RGB', (432 * len(ims), 768))
for i, im in enumerate(ims): S.paste(im, (i * 432, 0))
S.save(os.path.join('C:/mmview', out), quality=88)
print('saved', out)
