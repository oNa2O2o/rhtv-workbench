"""列出 Figma 页面名，并对名字含关键词的页面截总览图（Shift+1、隐藏 UI）。
用法：python _figma_pages.py <url> <outdir> [关键词1 关键词2 ...]（不给关键词=只列名）
"""
import sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import figma_ref
url, outdir, kws = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(outdir, exist_ok=True)
with sync_playwright() as p:
    c = figma_ref.ctx(p, True)
    page = c.new_page()
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_selector("canvas", timeout=120000)
    time.sleep(25)
    names = page.eval_on_selector_all('[data-testid="page-row"], [class*="pages_panel"] [class*="row"]', 'els=>els.map(e=>e.innerText.trim()).filter(Boolean)')
    if not names:
        names = page.eval_on_selector_all('[role="treeitem"]', 'els=>els.map(e=>e.innerText.trim()).filter(Boolean)')
    with open(os.path.join(outdir, "_pages.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(names))
    print(len(names), "pages")
    for n in names:
        if not any(k in n for k in kws):
            continue
        page.get_by_text(n, exact=True).first.click(); time.sleep(20)
        page.keyboard.press("Control+Backslash"); time.sleep(2)
        page.keyboard.press("Shift+1"); time.sleep(10)
        safe = "".join(ch if ch not in '\\/:*?"<>|' else "_" for ch in n)
        page.screenshot(path=os.path.join(outdir, "page_" + safe + ".png"))
        print("shot", n)
        page.keyboard.press("Control+Backslash"); time.sleep(2)
    c.close()
