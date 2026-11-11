"""Figma 投放参考抓取：用独立的 Edge 自动化配置（首次需在弹出的窗口里登录 Figma，之后免登录）。

用法：
  python figma_ref.py login                       # 打开窗口让用户登录，登录完关窗口即可
  python figma_ref.py shot <figma链接> <输出png>   # 打开节点并截图（自动缩放到选中节点）
配置目录：%LOCALAPPDATA%/mmw-figma-profile（不放进同步盘，含登录 cookie）
"""
import os, sys, time
from playwright.sync_api import sync_playwright

PROFILE = os.path.join(os.environ["LOCALAPPDATA"], "mmw-figma-profile")


def ctx(p, headless):
    # Figma(CloudFront) 会拦截 headless（返回“The request could not be satisfied”），
    # 所以始终用有头模式；非登录命令把窗口放到屏幕外，不打扰用户。
    args = ["--disable-blink-features=AutomationControlled"]
    if headless:
        args.append("--window-position=-4000,0")
    return p.chromium.launch_persistent_context(
        PROFILE, channel="msedge", headless=False, args=args,
        viewport={"width": 1600, "height": 1000}, device_scale_factor=2)


def logged_in(page):
    page.goto("https://www.figma.com/files", wait_until="domcontentloaded")
    time.sleep(4)
    return "/login" not in page.url and "signup" not in page.url


def main():
    cmd = sys.argv[1]
    with sync_playwright() as p:
        if cmd == "login":
            c = ctx(p, False)
            page = c.pages[0] if c.pages else c.new_page()
            page.goto("https://www.figma.com/login")
            print("请在弹出的窗口登录 Figma，登录完成后关闭窗口")
            page.wait_for_event("close", timeout=0)
            c.close()
        elif cmd == "check":
            c = ctx(p, True)
            print("LOGGED_IN" if logged_in(c.new_page()) else "NOT_LOGGED_IN")
            c.close()
        elif cmd == "shot":
            url, out = sys.argv[2], sys.argv[3]
            c = ctx(p, True)
            page = c.new_page()
            page.goto(url, wait_until="domcontentloaded")
            if "/login" in page.url:
                print("NOT_LOGGED_IN"); sys.exit(2)
            page.wait_for_selector("canvas", timeout=90000)
            time.sleep(15)  # 等画布和图片加载
            page.keyboard.press("Shift+2")  # 缩放到选中节点
            time.sleep(5)
            page.screenshot(path=out)
            print("saved", out)
            c.close()


if __name__ == "__main__":
    main()
