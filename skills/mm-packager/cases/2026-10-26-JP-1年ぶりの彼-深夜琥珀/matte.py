# 逐帧人物蒙版（rembg birefnet-portrait，GPU）→ 工程素材/人物蒙版/%04d.png（540×960 L）
import os, sys, time
from rembg import new_session, remove
from PIL import Image
P = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
FR = os.path.join(P, '工程素材', '抽帧'); MO = os.path.join(P, '工程素材', '人物蒙版')
s = new_session('u2net_human_seg')
fs = sorted(os.listdir(FR)); t0 = time.time()
for i, f in enumerate(fs):
    o = os.path.join(MO, f.replace('.jpg', '.png'))
    if os.path.exists(o): continue
    im = Image.open(os.path.join(FR, f)).convert('RGB').resize((540, 960), Image.LANCZOS)
    remove(im, session=s, only_mask=True).convert('L').save(o)
    if i % 50 == 0: print(i, round(time.time() - t0, 1), flush=True)
print('done', round(time.time() - t0, 1))
