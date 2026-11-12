import sys, pathlib, math
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True, args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"])
    pg = b.new_page(); errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(pathlib.Path(sys.argv[1]).resolve().as_uri() + "?clean"); pg.wait_for_timeout(1500)
    if errs: print("ERR", errs); sys.exit(1)
    dt = 0.05; dur = pg.evaluate("DUR")
    data = pg.evaluate(f"(() => {{ const r=[]; for (let t=0; t<=DUR+1e-6; t+={dt}) r.push(probe(t)); return r; }})()")
    b.close()
def worst(key, f):
    best=(0,0)
    for i in range(1,len(data)):
        v=f(data[i-1][key],data[i][key])/dt
        if v>best[0]: best=(v,i*dt)
    return best
h = lambda a,b: math.hypot(b[0]-a[0], b[2]-a[2])
vert = lambda a,b: abs(b[1]-a[1])
ang = lambda a,b: abs(b-a)
print("角色水平速度最大 %.2f m/s @%.2fs" % worst("hip", h))
print("角色升降最大 %.2f m/s @%.2fs" % worst("hip", vert))
print("角色转身最大 %.0f °/s @%.2fs" % worst("yaw", ang))
print("镜头水平移动最大 %.2f m/s @%.2fs" % worst("cam", h))
print("镜头升降最大 %.2f m/s @%.2fs" % worst("cam", vert))
print("转头最大 %.0f °/s @%.2fs" % worst("camYaw", ang))
if "tw" in data[0]: print("上半身转向最大 %.0f °/s @%.2fs" % worst("tw", ang))
