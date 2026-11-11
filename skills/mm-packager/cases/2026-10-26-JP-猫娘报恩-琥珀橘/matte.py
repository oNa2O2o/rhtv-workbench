# 逐帧抠出角色（猫/猫娘）遮罩 → 工作区/mask/%04d.png（源 24fps，480×854），BiRefNet_lite（torch CUDA）
import subprocess, os, numpy as np, torch
from PIL import Image
from transformers import AutoModelForImageSegmentation
from torchvision import transforms
P = 'F:/钟海明/2026/2026年10月26日MM-JP-猫娘报恩'
V = P + '/猫娘报恩.mp4'
D = P + '/工作区/mask'; os.makedirs(D, exist_ok=True)
W, H = 480, 854
model = AutoModelForImageSegmentation.from_pretrained('ZhengPeng7/BiRefNet_lite', trust_remote_code=True).cuda().eval().half()
tf = transforms.Compose([transforms.Resize((1024, 1024)), transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-nostdin', '-i', V, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
i = 0
with torch.no_grad():
    while True:
        b = pr.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        im = Image.frombuffer('RGB', (W, H), b)
        x = tf(im).unsqueeze(0).cuda().half()
        m = model(x)[-1].sigmoid()[0, 0].float().cpu().numpy()
        Image.fromarray((m * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).save(f'{D}/{i:04d}.png')
        i += 1
        if i % 100 == 0: print(i, flush=True)
print('done', i)
