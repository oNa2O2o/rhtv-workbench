# 静帧预览（v4）：bg_at(T) + 该时刻图层（x/y/opacity 关键帧线性插值；scale/rotation 忽略）
import sys, json, os
args = [a for a in sys.argv[1:]]; sys.argv = sys.argv[:1] + ['fast']
import gen4 as gen
import numpy as np
from PIL import Image
for ci, (vid, s0, D, fr) in enumerate(gen.CH): gen.BLUR[ci] = gen.soft_bg(gen.frame(vid, fr), 20, .66)
meta = json.load(open(os.path.join(gen.OUT, 'layers.json'), encoding='utf-8'))
order = {t[0]: i for i, t in enumerate(meta['tracks'])}
out = args[-1] if args and args[-1].endswith('.jpg') else 'v4_preview.jpg'
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
    c = gen.bg_at(T).convert('RGBA')
    for L in sorted([l for l in meta['layers'] if l['start'] <= T < l['start'] + l['dur']], key=lambda l: order.get(l['track'], -99)):
        im = Image.open(os.path.join(gen.OUT, L['file'] + L.get('ext', '.png'))).convert('RGBA')
        if L['track'] == 'V1': c = im; continue
        t = T - L['start']; x, y, o = val(L['k'], 'x', t, 0), val(L['k'], 'y', t, 0), val(L['k'], 'opacity', t, 1)
        if o < .999:
            a = np.array(im); a[..., 3] = (a[..., 3] * max(0, o)).astype(np.uint8); im = Image.fromarray(a)
        lay = Image.new('RGBA', c.size, (0, 0, 0, 0)); lay.paste(im, (int(round(x)), int(round(y)))); c.alpha_composite(lay)
    ims.append(c.convert('RGB').resize((540, 960)))
S = Image.new('RGB', (540 * len(ims), 960))
for i, im in enumerate(ims): S.paste(im, (i * 540, 0))
S.save(os.path.join(gen.P, '工程素材', '抽帧', out), quality=88)
print('saved', out)
