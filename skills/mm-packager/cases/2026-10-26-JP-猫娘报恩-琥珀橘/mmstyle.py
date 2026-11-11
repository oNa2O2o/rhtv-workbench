from PIL import Image, ImageDraw, ImageFont, ImageFilter
APP = 'F:/钟海明/2026/2026年10月10日MM-编辑器重构/app/'
ZM = APP + 'data/fonts/ZenMaruGothic-Black.ttf'
MOCHIY = 'C:/Users/zhonghaiming5328/AppData/Local/Microsoft/Windows/Fonts/MochiyPopOne-Regular.ttf'
NOTO = APP + 'data/fonts/NotoSansJP-Black.ttf'
AMBER = (255, 196, 110)
EMPH = [(255, 236, 190), (255, 190, 105), (240, 140, 60)]
_fc = {}
def F(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

def dm_sprite(txt, amber=False, size=54):
    """弹幕：白/琥珀字 + 深色描边 + 轻投影，返回 RGBA"""
    f = F(ZM, size)
    b = f.getbbox(txt, stroke_width=5)
    w, h = b[2] - b[0] + 24, b[3] - b[1] + 24
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((12 - b[0] + 2, 12 - b[1] + 4), txt, font=f, fill=(0, 0, 0, 120), stroke_width=5, stroke_fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    im.alpha_composite(sh)
    ImageDraw.Draw(im).text((12 - b[0], 12 - b[1]), txt, font=f, fill=AMBER + (255,) if amber else (255, 255, 255, 255),
                            stroke_width=4, stroke_fill=(30, 18, 10, 235))
    return im
