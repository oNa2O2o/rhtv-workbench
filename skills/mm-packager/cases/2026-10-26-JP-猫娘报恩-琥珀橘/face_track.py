# 动漫人脸检测逐帧 → 工作区/faces.json（归一化 cx,cy,w；缺失帧线性插值+平滑）
import sys, os, json, shutil
sys.path.insert(0, 'C:/Users/zhonghaiming5328/cv4')
import cv2, numpy as np
P = 'F:/钟海明/2026/2026年10月26日MM-JP-猫娘报恩'
shutil.copy(P + '/猫娘报恩.mp4', 'C:/Users/zhonghaiming5328/cv4/v85.mp4')
cas = cv2.CascadeClassifier('C:/Users/zhonghaiming5328/cv4/anime.xml')
cap = cv2.VideoCapture('C:/Users/zhonghaiming5328/cv4/v85.mp4'); fps = cap.get(cv2.CAP_PROP_FPS)
raw = []; i = 0
while True:
    ok, fr = cap.read()
    if not ok: break
    g = cv2.equalizeHist(cv2.cvtColor(cv2.resize(fr, None, fx=2, fy=2), cv2.COLOR_BGR2GRAY))
    ds = cas.detectMultiScale(g, scaleFactor=1.05, minNeighbors=4, minSize=(90, 90))
    h, w = g.shape
    f = None
    if len(ds):
        x, y, bw, bh = max(ds, key=lambda d: d[2] * d[3])
        f = [(x + bw / 2) / w, (y + bh / 2) / h, bw / w]
    raw.append(f); i += 1
n = len(raw); idx = [k for k in range(n) if raw[k]]
print('frames', n, 'with face', len(idx))
arr = np.array([raw[k] for k in idx]) if idx else np.zeros((0, 3))
full = np.stack([np.interp(range(n), idx, arr[:, c]) for c in range(3)], 1) if idx else None
# 平滑
k = 7; ker = np.ones(k) / k
sm = np.stack([np.convolve(np.pad(full[:, c], k // 2, mode='edge'), ker, 'valid') for c in range(3)], 1)
json.dump({'fps': fps, 'raw': raw, 'smooth': sm.round(4).tolist()}, open(P + '/工作区/faces.json', 'w'))
for t in range(0, n, 24): print(round(t / fps, 1), raw[t] and [round(v, 3) for v in raw[t]], [round(v, 3) for v in sm[t]])
