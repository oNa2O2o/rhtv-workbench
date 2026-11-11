# 动漫人脸检测（lbpcascade_animeface）逐帧跑，输出 工作区/faces_raw.json，并画检测拼图供人工核对
import os, json, cv2, sys
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.abspath(os.path.join(HERE, '..', '..'))
V = os.path.join(P, '素材', '视频 (70).mp4')
cas = cv2.CascadeClassifier('C:/Users/zhonghaiming5328/cv4/anime.xml')
cap = cv2.VideoCapture('C:/Users/zhonghaiming5328/cv4/v70.mp4'); fps = cap.get(cv2.CAP_PROP_FPS)
out = []; i = 0
while True:
    ok, fr = cap.read()
    if not ok: break
    g = cv2.equalizeHist(cv2.cvtColor(cv2.resize(fr, None, fx=2, fy=2), cv2.COLOR_BGR2GRAY))
    ds = cas.detectMultiScale(g, scaleFactor=1.05, minNeighbors=4, minSize=(100, 100))
    h, w = g.shape
    out.append({'t': round(i / fps, 4), 'f': [[round(x / w, 4), round(y / h, 4), round(bw / w, 4), round(bh / h, 4)] for x, y, bw, bh in ds]})
    i += 1
json.dump(out, open(os.path.join(P, '工作区', 'faces_raw.json'), 'w'), indent=0)
n = sum(1 for o in out if o['f'])
print('frames', len(out), 'with face', n)
