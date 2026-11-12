import sys, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image
html = pathlib.Path(sys.argv[1]).resolve(); out = sys.argv[2]; times = [float(x) for x in sys.argv[3].split(",")]; views = sys.argv[4].split(",")
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    rows = []
    for v in views:
        pg = b.new_page(viewport={"width": 540, "height": 960})
        pg.goto(html.as_uri() + "?clean&" + v); pg.wait_for_timeout(1200)
        row = []
        for t in times:
            pg.evaluate(f"setTime({t})"); f = f"{out}_{v}_{t}.png"; pg.locator("canvas").screenshot(path=f); row.append(Image.open(f).resize((180, 320)))
        rows.append(row); pg.close()
    b.close()
W = Image.new("RGB", (180 * len(times), 320 * len(views)), "white")
for r, row in enumerate(rows):
    for c, im in enumerate(row): W.paste(im, (c * 180, r * 320))
W.save(out + ".png")
