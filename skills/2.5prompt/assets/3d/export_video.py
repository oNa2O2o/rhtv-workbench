import sys, pathlib, subprocess, shutil
from playwright.sync_api import sync_playwright
html = pathlib.Path(sys.argv[1]).resolve(); out = pathlib.Path(sys.argv[2]); mode = sys.argv[3]  # mode: "shots t1,t2,.." or "video"
fps = 24
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 540, "height": 960})
    pg.goto(html.as_uri() + "?clean&export"); pg.wait_for_timeout(1500); assert pg.evaluate("typeof window.setTime") == "function"
    cv = pg.locator("canvas")
    if mode == "video":
        fr = out.parent / (out.stem + "_frames"); shutil.rmtree(fr, ignore_errors=True); fr.mkdir(parents=True)
        dur = pg.evaluate("window.DUR"); n = int(dur * fps)
        for i in range(n):
            pg.evaluate(f"setTime({i / fps})"); cv.screenshot(path=str(fr / f"{i:05d}.png"))
        b.close()
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(fr / "%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(out)], check=True)
        shutil.rmtree(fr)
    else:
        out.mkdir(parents=True, exist_ok=True)
        for t in mode.split(","):
            pg.evaluate(f"setTime({t})"); cv.screenshot(path=str(out / f"t{float(t):05.2f}.png"))
        b.close()
print("done")
