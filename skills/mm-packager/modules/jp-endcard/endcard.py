"""MM-JP 尾板模块（一镜到底 3D 卡片 + 女王02 口播 + 钢琴弦乐，17.3 s，1080×1920）。

用法：
  python endcard.py render  --out <out.mp4> [--config cfg.json]
  python endcard.py stills  --out <dir> --times 1.0,7.5,13.2 [--config cfg.json]   # 改配置后先看静帧

- 画面没改（不传 --config、或只改 "mix"）→ 取 prebuilt/default.mp4 的定稿画面（不重编码），按当前 mix 重新混音，几秒出。
  加 --legacy-mix 则原样复制 prebuilt（10-27 验收时的侧链混音）。
- 改了角色图 → 重新逐帧渲染（约 30 分钟，建议后台跑）。
- 出来的 mp4 写进包装 timeline.json（V 片段 + 同源音频），见 README.md。
- 混音：口播期间 BGM 按整句平滑压低（duck_expr，参数在配置 "mix"），不用侧链。
配置格式见 README.md。
"""
import argparse, base64, functools, hashlib, json, os, shutil, subprocess, sys, threading, urllib.parse, urllib.request, random, string, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
RES = (os.environ.get("MM_RES") or "Z:/创新事业部/AIGC项目视频组/mm-packager资源").replace("\\", "/")
ENGINE, MEDIA = f"{HERE}/engine", f"{RES}/jp-endcard/media"
ASSETS = f"{RES}/jp-endcard/assets"
OFFICIAL = f"{os.path.dirname(os.path.dirname(HERE))}/assets/官方素材"   # 官方 Logo、商店标 skill 内置，优先用它
OLD_BADGES_MD5 = "9cb8d11c933ef9e05cbf83139111ecdf"   # prebuilt/default.mp4 渲染时用的旧商店标（两个不一样大，非官方原图）
DEFAULT = json.load(open(f"{HERE}/config.default.json", encoding="utf-8"))
PREBUILT = f"{RES}/jp-endcard/prebuilt/default.mp4"
CHROME = os.environ.get("CHROME", r"C:/Program Files/Google/Chrome/Application/chrome.exe")   # 环境变量 CHROME 可覆盖，见 reference/环境.md
TAG = "JP尾板"

# ---------------- 配置 ----------------
def build_config(user):
    """user 配置（见 README）→ 引擎配置 + 需要额外提供的本地图片 {虚拟路径: 绝对路径}"""
    cfg = json.loads(json.dumps(DEFAULT)); files = {}
    if not user: return cfg, files
    def add_img(p):
        p = os.path.abspath(p).replace("\\", "/")
        if not os.path.isfile(p): sys.exit(f"找不到图片: {p}")
        key = "work/" + hashlib.sha1(open(p, "rb").read()).hexdigest()[:12] + os.path.splitext(p)[1].lower()
        files[key] = p; cfg["cards"].append(key); return len(cfg["cards"]) - 1
    if isinstance(user.get("mix"), dict): cfg["mix"] = {**cfg.get("mix", {}), **user["mix"]}
    if user.get("replaceAllCards"):
        cfg["cards"] = []; cfg["extras"] = []
    added = [add_img(p) for p in user.get("addCards", [])]
    if "heroes" in user:
        if len(user["heroes"]) != 3: sys.exit("heroes 必须正好 3 个（害羞/高冷/成熟 三张对比卡）")
        hs = []
        for h, d in zip(user["heroes"], DEFAULT["heroes"]):
            card = h.get("card")
            if isinstance(card, str): card = add_img(card)
            if card is None: card = d["card"]
            hs.append({"card": card, "tag": h.get("tag", d["tag"]), "chat": h.get("chat", d["chat"]),
                       "tint": h.get("tint", d["tint"]), "angle": h.get("angle", d["angle"])})
        cfg["heroes"] = hs
    # 新加的卡优先出现在开场角色网里（网最多 20 张配角，超出部分只在长廊里出现）
    hero_ids = {h["card"] for h in cfg["heroes"]}
    pool = [i for i in added if i not in hero_ids] + [i for i in cfg["extras"] if i not in hero_ids and i < len(cfg["cards"])]
    if len(pool) < 20: pool += [i for i in range(len(cfg["cards"])) if i not in hero_ids and i not in pool]
    cfg["extras"] = pool[:20]
    if len(cfg["cards"]) < 8: sys.exit("角色图至少 8 张（3 张主卡 + 配角）")
    return cfg, files

def visual(cfg):
    """去掉只影响声音的 mix，剩下的决定画面。"""
    return {k: v for k, v in cfg.items() if k != "mix"}

def cfg_hash(cfg, files):
    """画面哈希（不含 mix），可用来给自定义渲染结果命名。"""
    h = hashlib.sha1(json.dumps(visual(cfg), sort_keys=True).encode())
    for k in sorted(files): h.update(open(files[k], "rb").read())
    h.update(open(f"{ENGINE}/endcard.js", "rb").read())
    return h.hexdigest()[:10]

def is_default(cfg, files):
    """画面和定稿一致（mix 不算）。"""
    # 现在商店标换成 skill 内置的官方原版（两个同尺寸），旧 prebuilt 画面里还是旧标 → 不再当定稿复用，要逐帧重渲染
    if hashlib.md5(open(asset_file("badges.png"), "rb").read()).hexdigest() != OLD_BADGES_MD5: return False
    return not files and json.dumps(visual(cfg), sort_keys=True) == json.dumps(visual(DEFAULT), sort_keys=True)


def asset_file(name):
    """assets/<name>：skill 内置官方素材优先，没有再用共享资源目录。"""
    p = f"{OFFICIAL}/{name}"
    return p if os.path.exists(p) else f"{ASSETS}/{name}"

# ---------------- 渲染 ----------------
def serve(cfg, files):
    js = ("window.ENDCARD_CONFIG = " + json.dumps(cfg, ensure_ascii=False) + ";").encode("utf-8")
    class H(SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            path = urllib.parse.unquote(self.path.split("?")[0]).lstrip("/")
            if path == "config.js":
                self.send_response(200); self.send_header("Content-Type", "application/javascript; charset=utf-8"); self.send_header("Content-Length", str(len(js))); self.end_headers(); self.wfile.write(js); return
            if path.startswith("assets/") and path not in files: files[path] = asset_file(path[7:])
            if path in files:
                b = open(files[path], "rb").read(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
            return super().do_GET()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=ENGINE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}/index.html"

def open_page(p, url):
    b = p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None, args=["--disable-gpu-vsync"])
    pg = b.new_page(viewport={"width": 540, "height": 960})
    pg.goto(url); pg.wait_for_function("window.__ready || window.__err", timeout=120000)
    err = pg.evaluate("window.__err")
    if err: sys.exit("引擎初始化失败: " + err)
    return b, pg

def render_stills(cfg, files, outdir, times):
    from playwright.sync_api import sync_playwright
    os.makedirs(outdir, exist_ok=True); url = serve(cfg, files)
    with sync_playwright() as p:
        b, pg = open_page(p, url)
        for t in times:
            d = pg.evaluate(f"window.grabFrame({t}, 4)")
            open(f"{outdir}/t{t:05.2f}.png", "wb").write(base64.b64decode(d.split(",", 1)[1]))
        b.close()
    print("stills ->", outdir)

def render_silent(cfg, files, out):
    from playwright.sync_api import sync_playwright
    url = serve(cfg, files); fps = cfg["fps"]; n = int(round(cfg["duration"] * fps))
    with sync_playwright() as p:
        b, pg = open_page(p, url)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "png", "-i", "-",
                               "-vf", "scale=out_range=tv:out_color_matrix=bt709,format=yuv420p", "-c:v", "libx264", "-crf", "14", "-preset", "medium", out], stdin=subprocess.PIPE)
        t0 = time.time()
        for i in range(n):
            d = pg.evaluate(f"window.grabFrame({i / fps}, 4)")
            ff.stdin.write(base64.b64decode(d.split(",", 1)[1]))
            if i % 30 == 0: print(f"frame {i}/{n}  {time.time() - t0:.0f}s", flush=True)
        ff.stdin.close(); ff.wait(); b.close()

def duck_expr(cfg):
    """口播整句平滑压低：按 cfg["vo"] 的分句时间段生成 BGM 音量包络（ffmpeg volume 表达式）。
    句前 duckFade 秒开始压到 duckLevel → 句末后停 duckHold 秒 → 再用 duckRelease 秒慢慢回升。
    相邻两句间隔 < max(duckMergeGap, duckFade+duckHold+duckRelease) 就并成一段，句间停顿不回升。"""
    m = cfg.get("mix") or {}
    lv = float(m.get("duckLevel", .35)); fd = float(m.get("duckFade", .25))
    hold = float(m.get("duckHold", .4)); rel = float(m.get("duckRelease", .7))
    gap = max(float(m.get("duckMergeGap", 1.4)), fd + hold + rel)
    segs = []
    for s, e in sorted(p for v in cfg.get("vo", []) for p in v.get("parts", [])):
        if segs and s - segs[-1][1] < gap: segs[-1][1] = max(segs[-1][1], e)
        else: segs.append([s, e])
    if not segs or lv >= 1: return None
    w = "0"   # w(t) ∈ [0,1]：1 = 完全压低
    for s, e in segs:
        tri = f"clip((t-{s - fd:.3f})/{fd},0,1)*clip(({e + hold + rel:.3f}-t)/{rel},0,1)"
        w = tri if w == "0" else f"max({w},{tri})"
    return f"1-{1 - lv:.3f}*({w})"

def mix_and_encode(silent, out, cfg=DEFAULT, copy_video=False):
    """定稿混音（v19A）：BGM 钢琴弦乐 → 卡片吸入时收尾钢琴弦乐倒放吸气 → 回弹时正放；口播期间按整句平滑压低音乐（duck_expr）；消息/开关/点击音效。"""
    A, VD = f"{MEDIA}/audio", f"{MEDIA}/vo"
    DUR, COL, TR = 17.3, 11.85, 13.05; SW = TR - COL
    VO = [("001.mp3", .30), ("002.mp3", 3.25), ("003.mp3", 9.00), ("005.mp3", 13.45)]
    inputs, fl = ["-i", silent], []
    def add(p): inputs.extend(["-i", p]); return len(inputs) // 2 - 1
    g = "if(lt(t,2.8),8,if(lt(t,3.8),8-14*(t-2.8),if(lt(t,4.8),-6+6*(t-3.8),0)))"
    b = add(f"{A}/bgm_C_piano_strings.mp3")
    fl.append(f"[{b}:a]aresample=48000,volume=0.62,volume='pow(10,({g})/20)':eval=frame,afade=t=out:st={COL+.05}:d=0.65,atrim=0:{COL+.75}[bed]")
    s = add(f"{A}/sting_C_soft1.mp3")
    fl.append(f"[{s}:a]aresample=48000,atrim=start=2.85,asetpts=PTS-STARTPTS,atempo=0.75,aecho=0.8:0.7:120|260:0.25|0.15,afade=t=in:st=0:d=0.02,volume=1.4,apad=pad_dur=1,afade=t=out:st={DUR-TR-1.0:.2f}:d=1.0,adelay={int(TR*1000)}:all=1[st0]")
    r = add(f"{A}/sting_C_soft1.mp3")
    fl.append(f"[{r}:a]aresample=48000,atrim=start=2.9:duration={SW*.75:.3f},asetpts=PTS-STARTPTS,atempo=0.75,aecho=0.8:0.7:120|260:0.25|0.15,areverse,afade=t=in:st=0:d={SW*.5:.3f}:curve=exp,volume=1.6,adelay={int(COL*1000)}:all=1[rv]")
    fl.append("[st0][rv]amix=inputs=2:normalize=0[st]")
    vl = []
    for i, (f, at) in enumerate(VO):
        n = add(f"{VD}/{f}"); fl.append(f"[{n}:a]aresample=48000,adelay={int(at*1000)}:all=1[v{i}]"); vl.append(f"[v{i}]")
    fl.append("".join(vl) + f"amix=inputs={len(vl)}:normalize=0,volume=1.6,apad=whole_dur={DUR}[vo]")
    duck = duck_expr(cfg)
    fl.append("[bed][st]amix=inputs=2:normalize=0" + (f",volume='{duck}':eval=frame" if duck else "") + "[mus]")
    SFX = [("sfx_intro_2.mp3", 0.0, .55), ("sfx_message_1.mp3", 3.30, .3), ("sfx_message_1.mp3", 4.49, .3), ("sfx_message_1.mp3", 5.67, .3),
           ("sfx_toggle_2.mp3", 13.98, .35), ("sfx_click_1.mp3", 16.61, .8)]
    sl = []
    for j, (p, at, gg) in enumerate(SFX):
        n = add(f"{A}/{p}"); fl.append(f"[{n}:a]aresample=48000,lowpass=f=10000,volume={gg},adelay={int(at*1000)}:all=1[s{j}]"); sl.append(f"[s{j}]")
    fl.append("".join(sl) + f"amix=inputs={len(sl)}:normalize=0[sfx]")
    fl.append(f"[vo][mus][sfx]amix=inputs=3:normalize=0:dropout_transition=0,apad,atrim=0:{DUR},alimiter=limit=0.89,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[a]")
    venc = ["-c:v", "copy"] if copy_video else [
        "-vf", "setsar=1,format=yuv420p", "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-preset", "slow", "-crf", "16",
        "-maxrate", "12M", "-bufsize", "24M", "-g", "30", "-bf", "2", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]", *venc,
                    "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-t", str(DUR), out], check=True)

def produce(user, out, legacy_mix=False):
    """按配置得到尾板成片 out。画面没改时复用定稿画面只重混音（legacy_mix=True 原样复制定稿）。返回 out。"""
    cfg, files = build_config(user)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    if is_default(cfg, files):
        if legacy_mix:
            shutil.copyfile(PREBUILT, out); print("定稿画面 + 10-27 侧链混音（原样复制）", out); return out
        mix_and_encode(PREBUILT, out, cfg, copy_video=True)
        json.dump(cfg, open(out[:-4] + "_引擎配置.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("定稿画面 + 整句平滑混音", out); return out
    if legacy_mix: sys.exit("--legacy-mix 只能用在画面没改的配置上")
    silent = out[:-4] + "_无声.mp4"
    print("自定义配置 → 逐帧渲染（约 30 分钟）"); render_silent(cfg, files, silent)
    mix_and_encode(silent, out, cfg); os.remove(silent)
    json.dump(cfg, open(out[:-4] + "_引擎配置.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-f", "null", "-"], check=True)
    print("done", out); return out

def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    a1 = sp.add_parser("render"); a1.add_argument("--out", required=True); a1.add_argument("--config")
    a1.add_argument("--legacy-mix", action="store_true", help="画面没改时原样复制定稿（10-27 侧链混音）")
    a3 = sp.add_parser("stills"); a3.add_argument("--out", required=True); a3.add_argument("--times", default="1.0,3.6,5.0,6.2,7.6,9.5,12.6,13.3,16.8"); a3.add_argument("--config")
    a = ap.parse_args()
    user = json.load(open(a.config, encoding="utf-8")) if a.config else None
    if a.cmd == "render": produce(user, os.path.abspath(a.out).replace("\\", "/"), a.legacy_mix)
    elif a.cmd == "stills": cfg, files = build_config(user); render_stills(cfg, files, a.out, [float(x) for x in a.times.split(",")])

if __name__ == "__main__": main()
