# -*- coding: utf-8 -*-
# 迭代版本分析：抽帧(24fps) / 人脸追踪 / 黑场 / 能量区间 / ASR 词时间戳
# 用法: python analyze_ver.py 1   → 包装素材_版本1/{track.json, asr.json, info.txt}, 工程素材/抽帧_版本1/A|B/%04d.jpg
import sys, os, json, subprocess, numpy as np
sys.path.insert(0, 'C:/Users/zhonghaiming5328/cv4')
import cv2
N = sys.argv[1]
P = 'F:/钟海明/2026/2026年10月21日MM-JP-贞操逆转+上门讨债/'
VER = {'1': {'A': '迭代素材/版本1/视频 (74).mp4', 'B': '迭代素材/版本1/视频 (75).mp4'},
       '2': {'A': '迭代素材/版本2/视频 (76).mp4', 'B': '迭代素材/版本2/视频 (77).mp4'}}[N]
OUT = P + f'包装素材_版本{N}/'; FR = P + f'工程素材/抽帧_版本{N}/'
os.makedirs(OUT, exist_ok=True)
info = open(OUT + 'info.txt', 'w', encoding='utf-8')
def log(*a):
    s = ' '.join(str(x) for x in a); print(s); info.write(s + '\n'); info.flush()

# ---- 抽帧 ----
for k, v in VER.items():
    d = FR + k + '/'; os.makedirs(d, exist_ok=True)
    if not os.path.exists(d + '0000.jpg'):
        subprocess.run(['ffmpeg', '-v', 'error', '-i', P + v, '-q:v', '2', '-start_number', '0', d + '%04d.jpg'], check=True)
    log(k, 'frames', len(os.listdir(d)))

# ---- 黑场 ----
for k, v in VER.items():
    r = subprocess.run(['ffmpeg', '-i', P + v, '-vf', 'blackdetect=d=0.05:pix_th=0.12', '-an', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    log(k, 'black', [l.split('blackdetect')[1].strip() for l in r.stderr.splitlines() if 'black_start' in l])

# ---- 人脸 ----
W0, H0 = 480, 854
det = cv2.FaceDetectorYN.create('C:/Users/zhonghaiming5328/cv4/models/yunet.onnx', '', (W0, H0), score_threshold=0.5, nms_threshold=0.3, top_k=20)
def frames(v):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', P + v, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, H0, W0, 3)
res = {}
for k, v in VER.items():
    F = frames(v); n = len(F); raw = [None] * n; prev = None
    for i in range(n):
        _, faces = det.detect(np.ascontiguousarray(F[i]))
        if faces is None: continue
        best = None
        for f in faces:
            x, y, w, h, s = f[0], f[1], f[2], f[3], f[-1]
            c = np.array([x + w / 2, y + h / 2])
            sc = s + (0 if prev is None else -np.linalg.norm(c - prev) / 400)
            if best is None or sc > best[0]: best = (sc, c, w, h, s)
        if best[4] < .55: continue
        prev = best[1]; raw[i] = (best[1][0] / W0, best[1][1] / H0, best[2] / W0, best[3] / H0)
    for i in range(1, n - 1):
        if raw[i] and raw[i - 1] and raw[i + 1]:
            a, b, c = np.array(raw[i - 1][:2]), np.array(raw[i][:2]), np.array(raw[i + 1][:2])
            if np.linalg.norm(b - a) > .12 and np.linalg.norm(b - c) > .12: raw[i] = None
    idx = [i for i in range(n) if raw[i]]
    arr = np.zeros((n, 4)); has = np.zeros(n, bool)
    for i in idx: arr[i] = raw[i]; has[i] = True
    for j in range(4): arr[:, j] = np.interp(np.arange(n), idx, arr[idx, j])
    sm = arr.copy()
    for j, r in [(0, 3), (1, 3), (2, 6), (3, 6)]:
        pad = np.pad(arr[:, j], r, mode='edge'); sm[:, j] = np.convolve(pad, np.ones(2 * r + 1) / (2 * r + 1), 'valid')
    gaps = []; i = 0
    while i < n:
        if not has[i]:
            j = i
            while j < n and not has[j]: j += 1
            if j - i >= 6: gaps.append((round(i / 24, 2), round(j / 24, 2)))
            i = j
        else: i += 1
    log(k, 'face detected', len(idx), '/', n, 'gaps>=.25s', gaps)
    res[k] = [[round(i / 24, 4)] + [round(float(x), 4) for x in sm[i]] + [bool(has[i])] for i in range(n)]
json.dump(res, open(OUT + 'track.json', 'w', encoding='utf-8'))

# ---- 能量 + ASR ----
SR = 16000
def pcm(v, a, b):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a), '-t', str(b - a), '-i', P + v, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768
def regions(x, a, th=-35):
    hop = int(SR * .02); n = len(x) // hop
    db = np.array([20 * np.log10(np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) + 1e-9) for i in range(n)])
    on = db > th; out = []; i = 0
    while i < n:
        if on[i]:
            j = i
            while j < n and (on[j] or (j + 10 < n and on[j:j + 10].any())): j += 1
            out.append((round(a + i * .02, 2), round(a + j * .02, 2))); i = j
        else: i += 1
    return out
from faster_whisper import WhisperModel
model = WhisperModel('large-v3', device='cuda', compute_type='float16')
asr = {}
for key, vk, a, b in [('a1', 'A', 0, 7.2), ('a1b', 'A', 6.5, 15.2), ('a2', 'A', 15, 30.08), ('b', 'B', 0, 13.056)]:
    x = pcm(VER[vk], a, b)
    log(key, 'energy>-35dB', regions(x, a))
    segs, _ = model.transcribe(x, language='ja', word_timestamps=True, beam_size=5, condition_on_previous_text=False)
    ws = [{'w': w.word, 's': round(float(w.start) + a, 3), 'e': round(float(w.end) + a, 3), 'p': round(float(w.probability), 2)} for s in segs for w in s.words]
    asr[key] = ws
    log(key, ''.join(w['w'] for w in ws))
    log('   ' + ' '.join(f"{w['w']}@{w['s']:.2f}-{w['e']:.2f}" for w in ws))
json.dump(asr, open(OUT + 'asr.json', 'w', encoding='utf-8'), ensure_ascii=False)
