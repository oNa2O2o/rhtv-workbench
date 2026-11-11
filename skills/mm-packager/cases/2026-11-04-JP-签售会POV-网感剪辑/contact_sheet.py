import sys, os, glob
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
fs = sorted(glob.glob(os.path.join(src, "*.png")))
cols, cell = 12, 150
rows = (len(fs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell, rows * cell), "white")
d = ImageDraw.Draw(sheet)
f = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
for i, p in enumerate(fs):
    try:
        im = Image.open(p).convert("RGBA"); im.thumbnail((cell - 8, cell - 24))
        bg = Image.new("RGBA", im.size, "white"); bg.alpha_composite(im)
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.paste(bg.convert("RGB"), (x + 4, y + 20))
        d.text((x + 4, y + 1), os.path.basename(p)[:3], fill="red", font=f)
    except Exception as e:
        pass
sheet.save(out, quality=88)
