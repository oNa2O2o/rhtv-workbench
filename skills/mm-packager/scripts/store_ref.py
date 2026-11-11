"""商店页参考抓取：Google Play 页面整页截图 + 下载商店截图原图。

用法：python store_ref.py <商店链接> <输出目录>
"""
import os, sys, re, time, urllib.request
from playwright.sync_api import sync_playwright

url, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    page = b.new_page(viewport={"width": 1400, "height": 1000}, locale="ja-JP")
    page.goto(url, wait_until="networkidle")
    time.sleep(3)
    page.screenshot(path=os.path.join(out, "商店页_整页.png"), full_page=True)
    srcs = page.eval_on_selector_all(
        "img", "els => els.map(e => [e.src, e.alt, e.naturalWidth, e.naturalHeight])")
    b.close()

urls = []
for src, alt, w, h in srcs:
    if "play-lh.googleusercontent.com" in src and ("スクリーンショット" in (alt or "") or "screenshot" in (alt or "").lower()):
        big = re.sub(r"=[^/]*$", "", src) + "=w1080-h1920"
        if big not in urls:
            urls.append(big)
for i, u in enumerate(urls, 1):
    fn = os.path.join(out, f"商店截图_{i:02d}.png")
    urllib.request.urlretrieve(u, fn)
    print("saved", fn)
print("total", len(urls))
