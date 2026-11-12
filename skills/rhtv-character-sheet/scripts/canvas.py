#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rhtv-character-sheet 画布操作脚本：在「不在工作台记录里」的 RHTV 画布上建 G2 人设图节点、顺序跑图、改名挪位、删除、查报价。

- 工作台工程里不要用 create / run（生成、采用、记账走 wb gen / wb run / wb adopt，见 references/画布与积分.md）。
  refs / estimate / status 不写画布，两种情况都能用；delete 也能用来删工作台里没被采用的生成节点
  （删除要有用户明确指示或同意，删之前在回复里列出节点）。
- 通过 import rhtv-workbench 的 wb 模块调用 rhtvcli（wb.rh），两个 Skill 必须装在同一个 skills 目录下
  （或用环境变量 RHTV_WORKBENCH_SCRIPTS 指向 wb.py 所在目录）。
- 在 PowerShell 里运行：rhtvcli 在 Git Bash 里会报 INSTALLED_RELEASE_CHANGED。
- run 每派发一个节点前，把节点上已有的输出图地址（before_urls）写进运行记录文件
  （默认 ~/.rhtv-character-sheet/runs.json，--state-file 可改）；写不进去就不派发。
  status 读这个文件排除上一轮的旧图，并且只有节点 data.status 是 finished、又有这一轮的新图时才下载/裁切。
  运行记录只在 run 时更新：节点在 run 之外（网页上、wb run）重跑过时，status 要加 --exclude-url 指定上一轮的 url
  （上一次 run 拿到的地址在 status 输出的 last_run.url 里）。

用法：
  python canvas.py refs     --canvas <画布ID> [--group <分组>] [--node <ID> ...] [--out refs] [--no-download]
  python canvas.py create   --canvas <画布ID> --group <分组> --name <节点名> --prompt-file <文件> --left <参考图节点ID> --x <列x> --y 960
  python canvas.py estimate --canvas <画布ID> --node <ID> [--node <ID> ...]
  python canvas.py run      --canvas <画布ID> --node <ID> [--node <ID> ...] [--tag v1r1 ...] [--crop] [--out <目录>] [--state-file <文件>]
  python canvas.py status   --canvas <画布ID> --node <ID> [--tag ...] [--download | --crop] [--out <目录>] [--exclude-url <URL> ...] [--state-file <文件>]
  python canvas.py update   --canvas <画布ID> --node <ID> [--name <新名>] [--x <x> --y <y>] [--prompt-file <文件>]
  python canvas.py delete   --canvas <画布ID> --node <ID> [--node <ID> ...] [--yes]
输出一律是 JSON（run 每个事件一行）；ok:false 时看 error。
退出码：0 成功；1 失败；2 delete 没加 --yes（只列清单）；4 run/status 有节点还没拿到这一轮的图。
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys, urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).absolute().parent
DEFAULT_MODEL = "image-image-g-2-text-to-image"   # G2 低价渠道版（图生图，最多 10 张参考图）
MAX_LEFT = 10
POINTS_PER_CNY = 100                              # 账单实测：报价 0.1 元 = 扣 10 积分
BILL_URL = "https://www.runninghub.cn/bill-task"
BAD_STATES = {"FAILED", "ERROR", "REJECTED", "CANCELED", "CANCELLED", "NOT_ACCEPTED", "PARTIAL"}
DONE_STATES = {"FINISHED", "SUCCESS", "SUCCEEDED", "COMPLETED", "DONE"}   # 节点 data.status 实测完成时是 finished
PENDING_CODES = {"LOCAL_TIMEOUT", "OUTCOME_UNKNOWN"}
STATE_FILE = Path.home() / ".rhtv-character-sheet" / "runs.json"           # run 记下每个节点跑之前已有的图，status 用来排除旧图
IMG_RE = re.compile(r'https://[^"\s\\]+?\.(?:png|jpe?g|webp)(?:\?[^"\s\\]*)?', re.I)
OUT_RE = re.compile(r'https://[^"\s\\]+?/output/[0-9a-f-]+\.png', re.I)
WB = None                                         # rhtv-workbench 的 wb 模块，main() 里加载


# ---------------------------------------------------------------- 基础
def emit(obj, pretty=False):
    print(json.dumps(obj, ensure_ascii=False, indent=1 if pretty else None, default=str), flush=True)


def die(msg, code=1, **kw):
    emit({"ok": False, "error": msg, **kw}, pretty=True)
    sys.exit(code)


def load_wb():
    """按本文件位置找同级 Skill rhtv-workbench/scripts/wb.py（先按原路径，再按解析 junction 后的真实路径）。"""
    cands = []
    if os.environ.get("RHTV_WORKBENCH_SCRIPTS"):
        cands.append(Path(os.environ["RHTV_WORKBENCH_SCRIPTS"]))
    for f in (Path(__file__).absolute(), Path(__file__).resolve()):
        cands.append(f.parent.parent.parent / "rhtv-workbench" / "scripts")
    cands = list(dict.fromkeys(cands))
    for c in cands:
        if (c / "wb.py").is_file():
            sys.path.insert(0, str(c))
            import wb  # noqa: E402
            return wb
    die("没找到 rhtv-workbench 的 scripts/wb.py。rhtv-character-sheet 和 rhtv-workbench 必须装在同一个 skills 目录下，"
        "或设置环境变量 RHTV_WORKBENCH_SCRIPTS 指向 wb.py 所在目录。", tried=[str(c) for c in cands])


def rh(*args, **kw):
    """调 rhtvcli，永远不让 wb 直接退出；返回 dict，_rc 非 0 表示失败。"""
    return WB.rh(*args, check=False, **kw)


def failed(d):
    return bool(d.get("_rc"))


def errinfo(d):
    e = d.get("error")
    msg = e.get("message") if isinstance(e, dict) else (e if isinstance(e, str) else None)
    info = {"code": WB.err_code(d), "message": msg or d.get("_stderr") or d.get("raw")}
    if "INSTALLED_RELEASE_CHANGED" in json.dumps(d, ensure_ascii=False):
        info["hint"] = "rhtvcli 不能在 Git Bash 里跑，改在 PowerShell 里运行本脚本"
    return info


def sel(n):
    n = n.strip()
    return n if ":" in n else "id:" + n


def bare(n):
    return n.strip().split(":", 1)[-1]


def num(v):
    return int(round(float(v)))


def rnd(v):
    return int(round(v)) if isinstance(v, (int, float)) else v


def read_prompt(path):
    p = Path(path)
    if not p.is_file():
        die(f"提示词文件不存在：{p.absolute()}")
    text = p.read_text(encoding="utf-8-sig").strip()
    if not text:
        die(f"提示词文件是空的：{p.absolute()}")
    return text


def brief(n):
    data = n.get("data") or {}
    pos, sz = data.get("position") or {}, data.get("size") or {}
    model = data.get("model")              # 上传图为 null；生成节点为 {"modelCode": ..., "mode": ...}
    if isinstance(model, dict):
        model = model.get("modelCode") or model.get("mode") or "?"
    return {"node": n.get("nodeKey"), "name": n.get("name"), "type": n.get("type"),
            "x": rnd(pos.get("x")), "y": rnd(pos.get("y")), "w": rnd(sz.get("width")), "h": rnd(sz.get("height")),
            "group": data.get("groupNodeKey"), "model": model, "status": data.get("status")}


def list_nodes(canvas, ntype=None):
    items, cursor = [], None
    while True:
        args = ["node", "list", "-p", canvas, "--limit", 200]
        if ntype:
            args += ["--type", ntype]
        if cursor:
            args += ["--cursor", cursor]
        d = rh(*args, retry=True)
        if failed(d):
            die("列画布节点失败", canvas=canvas, **errinfo(d))
        items += [n for n in d.get("items", []) if isinstance(n, dict)]
        cursor = (d.get("pagination") or {}).get("nextCursor")
        if not cursor:
            return items


def get_item(canvas, nk, include="content,outputs"):
    d = rh("node", "get", sel(nk), "-p", canvas, "--include", include, retry=True)
    if failed(d):
        return None, d
    items = d.get("items")
    return (items[0] if items else d), d


def find_url(item, prefer_outputs=True):
    """生成节点优先取 outputs 里的图；上传图优先取 content 里的图。"""
    if not item:
        return None
    data = item.get("data") or {}
    parts = (data.get("outputs"), data.get("content")) if prefer_outputs else (data.get("content"), data.get("outputs"))
    for part in parts:
        if part:
            m = IMG_RE.findall(json.dumps(part, ensure_ascii=False))
            if m:
                return m[0]
    if prefer_outputs:
        m = OUT_RE.findall(json.dumps(item, ensure_ascii=False))
        return m[0] if m else None
    m = IMG_RE.findall(json.dumps(item, ensure_ascii=False))
    return m[0] if m else None


def output_urls(item):
    """生成节点 outputs 里的全部图片地址（去重保序）。"""
    if not item:
        return []
    outs = (item.get("data") or {}).get("outputs")
    found = IMG_RE.findall(json.dumps(outs, ensure_ascii=False)) if outs else []
    if not found:
        found = OUT_RE.findall(json.dumps(item, ensure_ascii=False))
    return list(dict.fromkeys(found))


def download(url, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r, open(dst, "wb") as f:
        shutil.copyfileobj(r, f)
    return dst


def url_ext(url, default=".png"):
    return os.path.splitext(url.split("?", 1)[0])[1].lower() or default


def thumb(src, dst, box=(900, 1300)):
    """存一张缩略图方便查看；没装 Pillow 就跳过。返回 (缩略图路径, 原图宽高)。"""
    try:
        from PIL import Image
        im = Image.open(src)
        size = im.size
        im = im.convert("RGB")
        im.thumbnail(box)
        im.save(dst, quality=90)
        return str(dst), size
    except Exception:
        return None, None


def run_crops(png, out_dir, tag):
    """调用同目录的 crops.py：python crops.py <图片> <输出目录> <标签>（默认自动找四个视图的分界）。"""
    cp = HERE / "crops.py"
    if not cp.is_file():
        return {"ok": False, "error": f"没找到 {cp}，跳过裁切"}
    cmd = [sys.executable, str(cp), str(png), str(out_dir), tag]
    r = subprocess.run(cmd, capture_output=True)
    res = {"ok": r.returncode == 0, "cmd": " ".join(f'"{c}"' for c in cmd),
           "files": [l for l in r.stdout.decode("utf-8", "replace").splitlines() if l.strip()]}
    info = r.stderr.decode("utf-8", "replace").strip()[-800:]
    if info:
        res["info"] = info          # 尺寸、分界模式；退回四等分时务必看 0全图 核对
    if r.returncode:
        res["error"] = "裁切失败：手动跑 crops.py（可加 --quarter 或 --cuts x1,x2,x3）"
    return res


def quote(canvas, nk):
    """官方报价（CNY）换算积分。报价 0 / 免费额度 ≠ 没花钱。"""
    est = rh("node", "estimate", sel(nk), "-p", canvas, "--billing-scope", "personal")
    if failed(est):
        return {"node": bare(nk), "ok": False, **errinfo(est)}
    totals = [t for t in est.get("totals") or [] if isinstance(t, dict)]
    cny = sum(float(t.get("amount") or 0) for t in totals if (t.get("currency") or "CNY") == "CNY")
    other = [t for t in totals if (t.get("currency") or "CNY") != "CNY"]
    free = any(isinstance(x, dict) and x.get("usedFreeLimit") for x in est.get("details") or [])
    complete = est.get("status") == "AVAILABLE" and bool(totals) and all(t.get("coverage") == "COMPLETE" for t in totals)
    pts = round(cny * POINTS_PER_CNY)
    r = {"node": bare(nk), "ok": True, "cny": cny, "points": pts, "free_quota": free,
         "complete": complete, "status": est.get("status")}
    if other:
        r["other_currency"] = other
    if free or pts == 0:
        r["note"] = "报价 0 / 用了免费额度：不等于没花钱，实际扣分到 bill-task 核对；不要对用户说“花费 0”"
    elif not complete:
        r["note"] = "报价不完整：实际扣分到 bill-task 核对"
    return r


def check_saved(canvas, nk, prompt=None):
    """建/改节点后读回参数：提示词是否被截断、比例和分辨率是否生效。"""
    chk = rh("node", "get", sel(nk), "-p", canvas, "--include", "params", retry=True)
    if failed(chk):
        return {"checked": False, **errinfo(chk)}
    res = {"checked": True, "aspectRatio": WB.first(chk, "aspectRatio"), "resolution": WB.first(chk, "resolution")}
    if prompt is not None:
        saved = WB.first(chk, "prompt") or ""
        res["prompt_chars"] = {"file": len(prompt), "saved": len(saved)}
        if not saved or len(saved) < len(prompt) * 0.95:
            res["warning"] = "画布上保存的提示词比文件短（或读不到），请核对"
    return res


# ---------------------------------------------------------------- 子命令
def cmd_refs(a):
    """列出画布上的图片节点（按分组、x、y 排序），下载参考图（上传图）到 --out。"""
    rows = [brief(n) for n in list_nodes(a.canvas, "image")]
    if a.group:
        rows = [r for r in rows if r["group"] == bare(a.group)]
    want = [bare(n) for n in a.node or []]
    if want:
        missing = [n for n in want if n not in {r["node"] for r in rows}]
        rows = [r for r in rows if r["node"] in want]
        if missing:
            die("这些节点不在画布的图片节点里（或不在 --group 里）", missing=missing)
    rows.sort(key=lambda r: (str(r["group"]), r["x"] if isinstance(r["x"], (int, float)) else 0,
                             r["y"] if isinstance(r["y"], (int, float)) else 0))
    for r in rows:
        r["kind"] = "生成节点" if r["model"] else "上传图"
    res = {"ok": True, "canvas": a.canvas, "count": len(rows), "nodes": rows}
    targets = rows if want else [r for r in rows if not r["model"]]
    if a.no_download:
        emit(res, pretty=True)
        return
    if not want and not a.group and len(targets) > 20:
        res["download_skipped"] = f"上传图有 {len(targets)} 张，太多：加 --group <分组> 或 --node <ID> 指定再下载"
        emit(res, pretty=True)
        return
    out = Path(a.out).absolute()
    got = []
    for r in targets:
        item, d = get_item(a.canvas, r["node"])
        url = find_url(item, prefer_outputs=bool(r["model"])) if item else None
        if not url:
            got.append({"node": r["node"], "ok": False, "error": "节点里没找到图片地址", **(errinfo(d) if failed(d) else {})})
            continue
        try:
            dst = download(url, out / (r["node"] + url_ext(url)))
        except Exception as e:
            got.append({"node": r["node"], "ok": False, "error": f"下载失败：{e}", "url": url})
            continue
        small, size = thumb(dst, out / (r["node"] + "_s.jpg"))
        got.append({"node": r["node"], "ok": True, "file": str(dst), "thumb": small, "size": size, "url": url})
    res.update(out=str(out), downloaded=got)
    emit(res, pretty=True)


def cmd_create(a):
    """建一个 G2 人设图生成节点（不运行），并读回参数、给出报价。"""
    prompt = read_prompt(a.prompt_file)
    if len(a.left) > MAX_LEFT:
        die(f"G2 低价版最多 {MAX_LEFT} 张参考图，现在给了 {len(a.left)} 个 --left")
    args = ["node", "create", a.name, "-p", a.canvas, "-t", "image", "--model", a.model, "--prompt", prompt,
            "-s", f'aspectRatio="{a.aspect}"', "-s", f'resolution="{a.resolution}"']
    for src in a.left:
        args += ["--left", sel(src)]
    if a.group:
        args += ["-g", a.group]
    args += ["--x", num(a.x), "--y", num(a.y)]
    d = rh(*args)
    nk = WB.first(d, "nodeKey")
    if failed(d) or not nk:
        die("建节点失败（没有派发任何生成，不扣分）", name=a.name, **errinfo(d))
    res = {"ok": True, "node": nk, "name": a.name, "x": num(a.x), "y": num(a.y), "model": a.model,
           "left": [bare(s) for s in a.left], "saved": check_saved(a.canvas, nk, prompt)}
    if not a.no_estimate:
        res["estimate"] = quote(a.canvas, nk)
    res["next"] = f"run --canvas {a.canvas} --node {nk}"
    emit(res, pretty=True)


def cmd_estimate(a):
    items = [quote(a.canvas, n) for n in a.node]
    oks = [i for i in items if i.get("ok")]
    bad = [i["node"] for i in items if not i.get("ok")]
    res = {"ok": not bad, "canvas": a.canvas, "items": items,
           "total_points": sum(i["points"] for i in oks),
           "free_quota_count": sum(1 for i in oks if i["free_quota"]),
           "bill": BILL_URL,
           "note": f"1 元 = {POINTS_PER_CNY} 积分换算；total_points 是报价合计（免费额度按 0 计），"
                   f"另按单价口径（次数 × 10 积分）一起报；实际扣分以账单为准（Canvas 行 0 分，旁边模型行才是扣分）"}
    if bad:
        res["failed"] = bad
        res["error"] = ("这些节点报价失败，total_points 没算它们：按单价口径估，并把 code 原文告诉用户"
                        "（MODEL_INPUT_REQUIRED 一般是节点缺输入图，先查 --left 有没有接上，未验证）")
    emit(res, pretty=True)
    sys.exit(1 if bad else 0)


def save_and_crop(a, url, tag):
    out = Path(a.out).absolute()
    res = {}
    try:
        png = download(url, out / (tag + url_ext(url)))
        res["file"] = str(png)
    except Exception as e:
        return {"download_error": str(e)}
    if a.crop:
        res["crops"] = run_crops(png, out, tag)
    return res


# ---------------------------------------------------------------- 运行记录（区分这一轮的新图和上一轮的旧图）
def now_str():
    return datetime.datetime.now().isoformat(timespec="seconds")


def state_path(a):
    return Path(getattr(a, "state_file", None) or STATE_FILE).expanduser().absolute()


def load_runs(path):
    """返回 (记录 dict, 错误信息)。文件不存在不算错。"""
    try:
        d = json.loads(path.read_text(encoding="utf-8-sig"))
        return (d if isinstance(d, dict) else {}), None
    except FileNotFoundError:
        return {}, None
    except Exception as e:
        return {}, f"运行记录文件读不了：{e}"


def save_run(path, canvas, nk, rec, merge=False):
    """写入/更新某个节点最近一次派发的记录。返回错误信息，成功返回 None。"""
    try:
        runs, err = load_runs(path)
        if err:
            return err
        key = f"{canvas}/{nk}"
        runs[key] = {**runs.get(key, {}), **rec} if merge else rec
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(runs, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, path)
        return None
    except Exception as e:
        return f"运行记录文件写不进去：{e}"


def node_state(item):
    return str(((item or {}).get("data") or {}).get("status") or "").upper()


def cmd_run(a):
    """顺序跑节点。每跑一个前检查停止标记文件；跑完打印 taskId 和输出 URL。不并行，不自动重试。"""
    tags = a.tag or []
    if tags and len(tags) != len(a.node):
        die("--tag 的个数要和 --node 一样（按顺序对应）")
    stop = Path(a.stop_file).absolute()
    if stop.exists():
        die(f"停止标记 {stop} 已存在（上一批被叫停过）。确认要继续跑，先删掉它再运行。")
    nodes = [bare(n) for n in a.node]
    spath = state_path(a)
    emit({"event": "start", "started_at": now_str(), "pid": os.getpid(), "stop_file": str(stop),
          "state_file": str(spath), "nodes": nodes,
          "how_to_stop": f"跑完当前节点后停：New-Item -ItemType File '{stop}'；"
                         f"立刻停：Stop-Process -Id {os.getpid()}（已派发的那一个仍会在服务器跑完并扣分）"})
    done, bad, pending, est_pts, free_runs = [], [], [], 0, 0
    not_dispatched = []
    for i, nk in enumerate(nodes):
        if stop.exists():
            not_dispatched = nodes[i:]
            emit({"event": "stopped", "stop_file": str(stop), "not_dispatched": not_dispatched})
            break
        tag = tags[i] if tags else nk
        before, bd = get_item(a.canvas, nk, "outputs")
        if not before:
            emit({"event": "failed", "node": nk, "tag": tag, "dispatched": False, **errinfo(bd),
                  "note": "跑之前读不到这个节点，没有派发（不扣分）。把 code 和 message 原文告诉用户，不要自动重试"})
            bad.append(nk)
            continue
        before_urls = output_urls(before)           # 同一节点重出时，用来区分这一轮的新图和上一轮的旧图
        q = quote(a.canvas, nk)
        rid = WB.uuid7()
        werr = save_run(spath, a.canvas, nk, {"canvas": a.canvas, "node": nk, "tag": tag, "runRequestId": rid,
                                               "dispatched_at": now_str(), "before_urls": before_urls,
                                               "result": "dispatched"})
        if werr:
            not_dispatched = nodes[i:]
            emit({"event": "stopped", "error": werr, "state_file": str(spath), "not_dispatched": not_dispatched,
                  "note": "运行记录读写失败，之后的 status 会分不出新旧图，所以没有派发（不扣分）。"
                          "把 error 告诉用户；修好记录文件，或用 --state-file 换一个可写的新路径再跑"})
            break
        emit({"event": "dispatch", "node": nk, "tag": tag, "runRequestId": rid, "old_urls": len(before_urls),
              "estimate_points": q.get("points"), "free_quota": q.get("free_quota")})
        r = rh("node", "run", sel(nk), "-p", a.canvas, "--billing-scope", "personal", "--run-request-id", rid,
               "--timeout", str(a.timeout), timeout=a.timeout + 120)
        task = r.get("taskId") or WB.first(r, "taskId")
        status = str(r.get("status") or r.get("taskStatus") or "").upper()
        code = WB.err_code(r) if failed(r) else None
        item, _ = get_item(a.canvas, nk)
        nst = node_state(item)
        urls = output_urls(item)
        new = [u for u in urls if u not in set(before_urls)]
        ev = {"node": nk, "tag": tag, "taskId": task, "status": status or code, "node_status": nst.lower() or None,
              "runRequestId": rid, "url": None}
        if status in BAD_STATES or (failed(r) and code not in PENDING_CODES and not task):
            ev.update(event="failed", errorMessage=WB.first(r, "errorMessage") or WB.first(item or {}, "errorMessage"),
                      **errinfo(r), note="运行失败。不要自动重试；把 errorMessage 和 code 原文告诉用户")
            bad.append(nk)
        elif not failed(r) and new and nst in DONE_STATES:
            ev.update(event="done", url=new[0])
            if len(new) > 1:
                ev["new_urls"] = new
            if a.crop or a.download:
                ev.update(save_and_crop(a, new[0], tag))
            done.append(nk)
        else:
            ev.update(event="pending", note="还没拿到这一轮的新图：不要换 ID 重跑；稍后用 status 子命令查（已派发的任务会扣分）")
            if urls and not new:
                ev["note"] += "；节点上只有跑之前就有的图，不是这次的结果"
            elif new and nst not in DONE_STATES:
                ev["note"] += f"；节点状态是 {nst.lower() or '读不到'}，不是 finished"
            pending.append(nk)
        werr = save_run(spath, a.canvas, nk, {"result": ev["event"], "taskId": task, "url": ev["url"],
                                               "checked_at": now_str()}, merge=True)
        if werr:
            ev["state_file_warning"] = werr
        if ev["event"] != "failed" and q.get("ok"):
            est_pts += q["points"]
            free_runs += 1 if q["free_quota"] else 0
        emit(ev)
    emit({"event": "summary", "ok": not bad and not pending, "done": done, "failed": bad, "pending": pending,
          "not_dispatched": not_dispatched, "estimate_points": est_pts, "free_quota_runs": free_runs, "bill": BILL_URL,
          "note": "积分按报价预估（报价 0/免费额度的另外核对）；实际扣分以 bill-task 为准，未核对就对用户说未核对"})
    sys.exit(1 if bad else (4 if pending else 0))


def cmd_status(a):
    """只读：查节点状态和这一轮的输出图。生成节点只有 data.status=finished、并且有排除旧图之后的新图时，才下载/裁切。"""
    tags = a.tag or []
    if tags and len(tags) != len(a.node):
        die("--tag 的个数要和 --node 一样（按顺序对应）")
    spath = state_path(a)
    runs, serr = load_runs(spath)
    manual = set(a.exclude_url or [])
    rows = []
    for i, n in enumerate(a.node):
        nk = bare(n)
        tag = tags[i] if tags else nk
        item, d = get_item(a.canvas, nk)
        if not item:
            rows.append({"node": nk, "ok": False, "ready": False, "state": "error", **errinfo(d)})
            continue
        r = brief(item)
        r["ok"] = True
        if not r["model"]:                          # 上传图 / 参考图：不跑生成，没有完成状态，有图就算拿到
            r["url"] = find_url(item, prefer_outputs=False)
            r["ready"], r["state"] = bool(r["url"]), "upload"
            if r["url"] and (a.download or a.crop):
                r.update(save_and_crop(a, r["url"], tag))
            rows.append(r)
            continue
        st = node_state(item)
        urls = output_urls(item)
        rec = runs.get(f"{a.canvas}/{nk}") or {}
        old = set(rec.get("before_urls") or []) | manual
        new = [u for u in urls if u not in old]
        r.update(url=None, old_urls_excluded=len(urls) - len(new))
        if rec:
            r["last_run"] = {k: rec.get(k) for k in ("tag", "runRequestId", "taskId", "dispatched_at", "checked_at",
                                                     "result", "url")}
        elif not manual and not serr:
            r["note"] = ("本机运行记录里没有这个节点（不是在本机用 canvas.py run 跑的）：分不出新旧图。"
                         "这个节点重跑过的话，加 --exclude-url <上一轮的 url> 再查")
        if serr and not manual:
            r.update(ready=False, state="unknown", candidates=urls,
                     warning="运行记录文件读不了，分不出这一轮的新图和上一轮的旧图：没下载、没裁切。"
                             "修好或删掉记录文件，或用 --exclude-url <上一轮的 url> 再查")
        elif st in BAD_STATES:
            r.update(ready=False, state="failed", errorMessage=WB.first(item, "errorMessage"),
                     warning="节点运行失败：没下载、没裁切。把 errorMessage 原文告诉用户，不要自动重试")
        elif st not in DONE_STATES:
            r.update(ready=False, state="pending",
                     warning=f"节点状态是 {st.lower() or '读不到'}，不是 finished：没下载、没裁切。过一会儿再查，不要换 ID 重跑")
        elif not new:
            r.update(ready=False, state="pending",
                     warning=("节点是 finished，但输出里只有上一轮的旧图（已排除）：这一轮的图还没出来，没下载、没裁切，过一会儿再查"
                              if urls else "节点是 finished，但没找到输出图片地址：没下载、没裁切"))
        elif not rec and not manual and len(new) > 1:
            r.update(ready=False, state="unknown", candidates=new,
                     warning="节点上有多张输出图，又没有运行记录，分不出哪张是这一轮的：没下载、没裁切。用 --exclude-url 排除旧图后再查")
        else:
            r.update(ready=True, state="done", url=new[0])
            if len(new) > 1:
                r["new_urls"] = new
                r["warning"] = "这一轮有多张新图，取了第一张，核对一下"
            if rec.get("url") and new[0] == rec.get("url"):
                # 运行记录只在 cv run 时更新：节点之后在网页上或用 wb run 重跑过，这里不会知道
                r["note"] = ("这张就是上次 cv run 拿到的图（last_run.url）。节点之后如果在 cv run 之外"
                             "（网页上、wb run）重跑过，它就是旧图：加 --exclude-url <这个地址> 再查")
            if a.download or a.crop:
                r.update(save_and_crop(a, new[0], tag))
        rows.append(r)
    failed_nodes = [r["node"] for r in rows if r["state"] in ("error", "failed") or r.get("download_error")]
    waiting = [r["node"] for r in rows if not r["ready"] and r["node"] not in failed_nodes]
    res = {"ok": not failed_nodes and not waiting, "canvas": a.canvas, "state_file": str(spath),
           "ready": [r["node"] for r in rows if r["ready"]], "failed": failed_nodes, "not_ready": waiting, "nodes": rows}
    if serr:
        res["state_file_error"] = serr
    if failed_nodes or waiting:
        res["error"] = "有节点没拿到这一轮的图（看各节点的 warning），这些节点没下载、没裁切"
    emit(res, pretty=True)
    sys.exit(1 if failed_nodes else (4 if waiting else 0))


def cmd_update(a):
    if (a.x is None) != (a.y is None):
        die("--x 和 --y 要一起给")
    args = ["node", "update", sel(a.node), "-p", a.canvas]
    prompt = None
    if a.name:
        args += ["--name", a.name]
    if a.x is not None:
        args += ["--x", num(a.x), "--y", num(a.y)]
    if a.prompt_file:
        prompt = read_prompt(a.prompt_file)
        args += ["--prompt", prompt]
    if len(args) == 5:
        die("没有要改的：--name / --x --y / --prompt-file 至少给一个")
    d = rh(*args, retry=True)
    if failed(d):
        die("更新节点失败", node=bare(a.node), **errinfo(d))
    res = {"ok": True, "node": bare(a.node), "name": a.name,
           "x": num(a.x) if a.x is not None else None, "y": num(a.y) if a.y is not None else None}
    if prompt is not None:
        res["saved"] = check_saved(a.canvas, a.node, prompt)
    emit(res, pretty=True)


def cmd_delete(a):
    """删除生成节点。没有 --yes 只列出要删的节点（退出码 2）；没有模型的节点（参考图/上传图/文字卡）一律不删。"""
    plan, refused, missing = [], [], []
    for n in a.node:
        nk = bare(n)
        item, d = get_item(a.canvas, nk, "outputs")
        if not item:
            missing.append({"node": nk, **errinfo(d)})
            continue
        r = brief(item)
        (plan if r["model"] else refused).append(r)
    res = {"canvas": a.canvas, "delete": plan, "missing": missing,
           "refused": [{**r, "reason": "没有模型 = 上传的参考图/上传图/文字卡，本脚本不删"} for r in refused]}
    if not a.yes:
        emit({"ok": False, **res, "error": "没有加 --yes，只列清单、没删。删除要有用户的明确指示（如“只留合格的”）或明确同意，"
                                           "并且删之前在回复里列出上面 delete 里的节点名和 ID；两样都满足再加 --yes 运行"},
             pretty=True)
        sys.exit(2)
    deleted, errors = [], []
    for r in plan:
        d = rh("node", "delete", sel(r["node"]), "-p", a.canvas)
        (errors.append({"node": r["node"], **errinfo(d)}) if failed(d) else deleted.append(r["node"]))
    emit({"ok": not errors, **res, "deleted": deleted, "errors": errors}, pretty=True)
    sys.exit(1 if errors else 0)


# ---------------------------------------------------------------- 入口
def main():
    global WB
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--canvas", required=True, help="画布 ID（RHTV project ID）")
    ap = argparse.ArgumentParser(prog="canvas.py", description="rhtv-character-sheet：不在工作台记录里的画布操作")
    sp = ap.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("refs", parents=[common], help="列出图片节点并下载参考图（只读）")
    s.add_argument("--group", help="只看这个分组（工程那一行）")
    s.add_argument("--node", action="append", help="只看/只下载这些节点，可多个")
    s.add_argument("--out", default="refs", help="下载目录，默认 ./refs")
    s.add_argument("--no-download", action="store_true", help="只列不下载")

    s = sp.add_parser("create", parents=[common], help="建 G2 低价版四视图节点（不运行）")
    s.add_argument("--group", help="节点所属分组（工程那一行的 groupNodeKey）")
    s.add_argument("--name", required=True, help="节点名，如 <工程名>｜v1·人设图【生成中】")
    s.add_argument("--prompt-file", required=True, help="UTF-8 提示词文件")
    s.add_argument("--left", action="append", required=True, help="输入图节点 ID（参考图或上一张生成图），可多个，最多 10")
    s.add_argument("--x", type=float, required=True); s.add_argument("--y", type=float, required=True)
    s.add_argument("--model", default=DEFAULT_MODEL)
    s.add_argument("--aspect", default="16:9"); s.add_argument("--resolution", default="4k")
    s.add_argument("--no-estimate", action="store_true")

    s = sp.add_parser("estimate", parents=[common], help="报价并换算积分（只读）")
    s.add_argument("--node", action="append", required=True)

    s = sp.add_parser("run", parents=[common], help="顺序跑一个或多个节点（会扣积分）")
    s.add_argument("--node", action="append", required=True)
    s.add_argument("--tag", action="append", help="每个节点的文件名标签（如 v2r3），个数与 --node 相同")
    s.add_argument("--timeout", type=int, default=600, help="单个节点等待秒数，默认 600")
    s.add_argument("--download", action="store_true", help="下载输出图到 --out")
    s.add_argument("--crop", action="store_true", help="下载并调用 scripts/crops.py 裁切 8 张自查图")
    s.add_argument("--out", default=".", help="下载/裁切目录，默认当前目录")
    s.add_argument("--stop-file", default="STOP", help="停止标记文件，默认当前目录的 STOP")
    s.add_argument("--state-file", help=f"运行记录文件（记下跑之前已有的图），默认 {STATE_FILE}")

    s = sp.add_parser("status", parents=[common],
                      help="查节点状态和这一轮的输出图；finished 且有新图才下载/裁切（只读画布）")
    s.add_argument("--node", action="append", required=True)
    s.add_argument("--tag", action="append")
    s.add_argument("--download", action="store_true"); s.add_argument("--crop", action="store_true")
    s.add_argument("--out", default=".")
    s.add_argument("--exclude-url", action="append", help="当作旧图排除的输出地址（上一轮的 url），可多个")
    s.add_argument("--state-file", help=f"run 写的运行记录文件，默认 {STATE_FILE}")

    s = sp.add_parser("update", parents=[common], help="改名 / 挪位 / 换提示词")
    s.add_argument("--node", required=True)
    s.add_argument("--name"); s.add_argument("--x", type=float); s.add_argument("--y", type=float)
    s.add_argument("--prompt-file")

    s = sp.add_parser("delete", parents=[common], help="删除生成节点（要 --yes；不删参考图）")
    s.add_argument("--node", action="append", required=True)
    s.add_argument("--yes", action="store_true",
                   help="用户已明确指示（如“只留合格的”）或明确同意删除，且已在回复里列出要删的节点")

    a = ap.parse_args()
    if os.environ.get("MSYSTEM"):
        print(f"警告：检测到 Git Bash（MSYSTEM={os.environ['MSYSTEM']}）。rhtvcli 在 Git Bash 里会报 "
              "INSTALLED_RELEASE_CHANGED，请改在 PowerShell 里运行。", file=sys.stderr)
    WB = load_wb()
    globals()["cmd_" + a.cmd](a)


if __name__ == "__main__":
    main()
