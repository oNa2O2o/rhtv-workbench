#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""人设图自查裁切：把一张「角色设定四视图」切成 8 张局部图，给自查和独立审核员逐张放大看。

用法：
    python crops.py <图片路径或URL> <输出目录> [标签] [--quarter | --cuts X1,X2,X3]

    图片路径或URL  本地 png/jpg，或 RH 生成结果的 https 链接（会先下载到输出目录）
    输出目录       不存在会自动创建
    标签           输出文件名前缀，默认取图片文件名（不含扩展名），如 v2r5、v4fix
    --quarter      强制按整图四等分切（素材里的原始做法，q = 宽/4）
    --cuts         手动给三条竖向分界的 x 像素（原图坐标），如 --cuts 1416,2264,2942；
                   必须是三个整数、按从左到右的顺序给、严格递增，且 0 < X1 < X2 < X3 < 图宽，
                   否则报错退出（不会自动排序，避免把写错的数悄悄切成错图）
    默认（都不加）：按白底留白自动找四个视图的分界；找不到就退回 --quarter 的四等分，
                   stderr 的分界模式会写明「自动分界失败」

输出（stdout 每行一个绝对路径，按序号）：
    <标签>_0全图.jpg        整图缩到 1/3
    <标签>_1大特写.jpg      第 1 格头肩大特写，全高，缩到 2/3
    <标签>_2大特写胸口.jpg  第 1 格，高 45%~100%，原尺寸
    <标签>_3正面躯干.jpg    第 2 格（正面全身），高 8%~48%，原尺寸
    <标签>_4侧面躯干.jpg    第 3 格（侧面全身），高 8%~48%，原尺寸
    <标签>_5裙摆膝盖.jpg    第 2 格左边界到图右边缘，高 50%~85%，原尺寸
    <标签>_6鞋.jpg          第 2 格左边界到图右边缘，高 82%~100%，原尺寸
    <标签>_7背面.jpg        第 4 格（背面全身），全高，缩到 2/3
stderr 打印：图片尺寸、分界模式（auto / quarter / cuts）、x 分界 [0, b1, b2, b3, W]。

为什么默认自动找分界：G2 画的头肩大特写格通常占宽度 1/3 以上（实测 v4fix、v2fix、v1i
约 37%~39%），按四等分切时「3正面躯干」只剩半个人、「4侧面躯干」混进正面的手臂。
本说明里的「第 N 格」都指分界之间的区域，不是宽度的 N/4。自动模式先找竖向留白；
大特写的肩/手和正面全身挨在一起时，在挨着的那段里取内容最少的一列切开。
结果仍不对（看 0全图 判断）就用 --cuts 手动指定。只依赖 Pillow 和标准库。
"""
import argparse
import os
import re
import sys
import urllib.parse
import urllib.request

from PIL import Image

LANCZOS = getattr(Image, 'Resampling', Image).LANCZOS


def _utf8_stdout():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8')
        except Exception:
            pass


def _safe_tag(tag):
    tag = re.sub(r'[\\/:*?"<>|\s]+', '_', tag).strip('._')
    return tag or 'sheet'


def load_image(src, outdir, tag):
    """返回 (PIL.Image, 标签)。URL 先下载到输出目录。"""
    if re.match(r'^https?://', src, re.I):
        path = urllib.parse.urlparse(src).path
        stem, ext = os.path.splitext(os.path.basename(path))
        tag = _safe_tag(tag or stem)
        if ext.lower() not in ('.png', '.jpg', '.jpeg', '.webp'):
            ext = '.png'
        local = os.path.join(outdir, tag + ext)
        req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as r, open(local, 'wb') as f:
            f.write(r.read())
        print('已下载原图: ' + os.path.abspath(local), file=sys.stderr)
    else:
        local = src
        if not os.path.isfile(local):
            raise SystemExit('找不到图片: ' + src)
        tag = _safe_tag(tag or os.path.splitext(os.path.basename(local))[0])
    return Image.open(local).convert('RGB'), tag


def detect_bounds(im):
    """按白底留白找四个视图的 x 分界，返回 [0, b1, b2, b3, W]；失败返回 None。"""
    W, H = im.size
    sw = min(W, 960)
    sh = max(1, round(H * sw / W))
    g = im.convert('L').resize((sw, sh), LANCZOS)
    hist = g.histogram()
    bg = max(range(180, 256), key=lambda v: hist[v])
    thr = bg - 20
    if sum(hist[thr:]) < sw * sh * 0.3:  # 背景不够白，不是纯白底版式
        return None
    data = g.tobytes()
    need = max(3, sh // 100)  # 一列里至少 1% 高度是非背景像素才算有内容
    cnt = [sum(1 for v in data[x::sw] if v < thr) for x in range(sw)]

    runs, start = [], None
    for x, c in enumerate([c >= need for c in cnt] + [False]):
        if c and start is None:
            start = x
        elif not c and start is not None:
            runs.append([start, x - 1])
            start = None
    min_w = max(2, sw // 100)
    runs = [r for r in runs if r[1] - r[0] + 1 >= min_w]  # 去掉发丝、边框线这类碎段

    while len(runs) > 4:  # 段太多：合并间隙最小的相邻两段
        gaps = [runs[k + 1][0] - runs[k][1] for k in range(len(runs) - 1)]
        k = min(range(len(gaps)), key=lambda t: gaps[t])
        runs[k:k + 2] = [[runs[k][0], runs[k + 1][1]]]

    while 0 < len(runs) < 4:  # 段太少：最宽那段是两个视图挨在一起，在内容最少的一列切开
        k = max(range(len(runs)), key=lambda t: runs[t][1] - runs[t][0])
        s, e = runs[k]
        w = e - s + 1
        lo, hi = s + w * 15 // 100, e - w * 15 // 100
        if hi <= lo:
            return None
        x = min(range(lo, hi + 1), key=lambda t: cnt[t])
        runs[k:k + 1] = [[s, x - 1], [x + 1, e]]

    if len(runs) != 4 or any(r[1] - r[0] + 1 < sw * 0.05 for r in runs):
        return None
    scale = W / sw
    cuts = [round((runs[k][1] + 1 + runs[k + 1][0]) / 2 * scale) for k in range(3)]
    return [0] + cuts + [W]


def parse_cuts(text):
    """把 --cuts 文本解析成三个整数；格式不对直接报错退出。图宽的检查在读图之后做。"""
    example = '例：--cuts 1416,2264,2942'
    parts = [p.strip() for p in text.split(',')]
    try:
        xs = [int(p) for p in parts]
    except ValueError:
        raise SystemExit('--cuts 格式不对：要三个整数 x 像素、用英文逗号分隔，收到 "%s"。%s'
                         % (text, example))
    if len(xs) != 3:
        raise SystemExit('--cuts 要正好三个分界（四个视图之间的三条竖线），收到 %d 个："%s"。%s'
                         % (len(xs), text, example))
    if not (xs[0] < xs[1] < xs[2]):
        raise SystemExit('--cuts 必须从左到右严格递增（X1 < X2 < X3，不能相等、不能倒序），收到 %s。'
                         '脚本不会自动排序，请先在 0全图 里重新核对三条分界。%s' % (xs, example))
    return xs


def check_cuts(xs, W):
    """读图后检查分界都在图内：0 < X1 < X2 < X3 < W。"""
    if not (0 < xs[0] < xs[1] < xs[2] < W):
        raise SystemExit('--cuts 超出图片范围：要求 0 < X1 < X2 < X3 < 图宽 %d，收到 %s。'
                         '注意 x 是原图像素；在 0全图（原图的 1/3）里量的值要乘 3。' % (W, xs))


def make_crops(im, b, quarter):
    W, H = im.size

    def y(p):
        return H * p // 100

    chest_right = (b[1] + b[1] // 5) if quarter else b[1]  # 四等分时沿用原做法：0~1.2q
    return [
        ('0全图', im.resize((W // 3, H // 3), LANCZOS), 88, None),
        ('1大特写', im.crop((b[0], 0, b[1], H)), 90, 2 / 3),
        ('2大特写胸口', im.crop((b[0], y(45), chest_right, H)), 90, None),
        ('3正面躯干', im.crop((b[1], y(8), b[2], y(48))), 90, None),
        ('4侧面躯干', im.crop((b[2], y(8), b[3], y(48))), 90, None),
        ('5裙摆膝盖', im.crop((b[1], y(50), W, y(85))), 90, None),
        ('6鞋', im.crop((b[1], y(82), W, H)), 90, None),
        ('7背面', im.crop((b[3], 0, W, H)), 90, 2 / 3),
    ]


def main():
    _utf8_stdout()
    ap = argparse.ArgumentParser(description='人设图四视图自查裁切（8 张）')
    ap.add_argument('src', help='图片路径或 https URL')
    ap.add_argument('outdir', help='输出目录')
    ap.add_argument('tag', nargs='?', default=None, help='文件名前缀，默认取图片文件名')
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument('--quarter', action='store_true', help='强制按四等分切')
    grp.add_argument('--cuts', help='手动分界：三个原图 x 像素，逗号分隔、严格递增，0 < X1 < X2 < X3 < 图宽，如 1416,2264,2942')
    a = ap.parse_args()
    xs = parse_cuts(a.cuts) if a.cuts is not None else None  # 先查格式，免得写错还去下载

    os.makedirs(a.outdir, exist_ok=True)
    im, tag = load_image(a.src, a.outdir, a.tag)
    W, H = im.size
    q = W // 4
    b, mode = None, 'quarter'
    if xs is not None:
        check_cuts(xs, W)
        b, mode = [0] + xs + [W], 'cuts'
    elif not a.quarter:
        b = detect_bounds(im)
        mode = 'auto' if b else 'quarter（自动分界失败，已退回四等分，务必看 0全图 核对裁切）'
    if b is None:
        b = [0, q, 2 * q, 3 * q, W]
    print('尺寸 %dx%d  分界模式 %s  x分界 %s' % (W, H, mode, b), file=sys.stderr)

    for name, img, quality, factor in make_crops(im, b, mode.startswith('quarter')):
        if factor:
            img = img.resize((max(1, round(img.width * factor)), max(1, round(img.height * factor))), LANCZOS)
        path = os.path.abspath(os.path.join(a.outdir, '%s_%s.jpg' % (tag, name)))
        img.save(path, quality=quality)
        print(path)


if __name__ == '__main__':
    main()
