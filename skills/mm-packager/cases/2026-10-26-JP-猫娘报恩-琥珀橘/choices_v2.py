# ---------------- 选项 v2：中下方小胶囊 + 倒计时条，无全屏模糊，点击后快速过渡 ----------------
QS = None
OPTS = [['①おやつだよ', '②貧乏ご主人って何？', '③人間でも可愛いね'], ['①行かないで', '②ポケットの中 何？', '③好きにすれば'], ['①もう一本おやつをあげる', '②抱っこして帰る']]
PICK = [0, 1, None]
CLICK = 2.0
HOVER = [[(.55, 2), (1.0, 1), (1.45, 0)], [(.55, 0), (1.0, 2), (1.45, 1)], [(.55, 0), (1.1, 1), (1.7, 0), (2.3, 1), (2.8, 0)]]
OYS = [1215, 1310, 1405]; BAR_Y = 1138; BAR_W = 420; PH = 76
DMQ = [['おやつ一択', '選択肢ひどくて草', 'ご主人の財布事情…', 'wwwww'],
       ['ポケット膨らんでない？', '引き止めろ！', '好きにすればは鬼', 'www'],
       ['何を言いかけたの！？', '抱っこ一択', '続き気になる', 'ここで終わり！？', 'てぇてぇ']]
DM_LANES = [170, 1640, 265, 1735, 360]
TICKS = []   # BGM 同步点：(kind, t)
def pointer_imgs():
    L = canvas(); r = 30
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([540 - r - 5, 960 - r, 540 + r + 5, 960 + r + 12], fill=110); g = g.filter(ImageFilter.GaussianBlur(10))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(g); L.alpha_composite(sh)
    d = ImageDraw.Draw(L); d.ellipse([540 - r, 960 - r, 540 + r, 960 + r], fill=(255, 255, 255, 95), outline=(255, 255, 255, 230), width=3)
    d.ellipse([540 - 7, 960 - 7, 540 + 7, 960 + 7], fill=(255, 255, 255, 245))
    R = canvas(); ImageDraw.Draw(R).ellipse([540 - 40, 960 - 40, 540 + 40, 960 + 40], outline=(255, 255, 255, 230), width=4)
    return save(L, 'pointer'), save(R, 'ripple')
def pill_w(txt): return max(380, int(font(ZM, 38).getlength(txt[1:]) + 150))
def pill(txt, y, sel):
    L = canvas(); w = pill_w(txt); x0, x1, y0, y1 = 540 - w // 2, 540 + w // 2, y - PH // 2, y + PH // 2
    S = Image.new('L', (W, H), 0); ImageDraw.Draw(S).rounded_rectangle([x0, y0 + 8, x1, y1 + 8], radius=PH // 2, fill=150 if sel else 120)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(S.filter(ImageFilter.GaussianBlur(14))); L.alpha_composite(sh)
    if sel:
        G = Image.new('L', (W, H), 0); ImageDraw.Draw(G).rounded_rectangle([x0 - 6, y0 - 6, x1 + 6, y1 + 6], radius=PH // 2 + 6, fill=150)
        gc = Image.new('RGBA', (W, H), (255, 170, 80, 0)); gc.putalpha(G.filter(ImageFilter.GaussianBlur(16))); L.alpha_composite(gc)
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([x0, y0, x1, y1], radius=PH // 2, fill=255)
    if sel:
        body = Image.new('RGBA', (W, H), (0, 0, 0, 0)); body.paste(grad_img(w, PH, AMB, horiz=True).convert('RGBA'), (x0, y0)); body.putalpha(m)
    else:
        body = Image.new('RGBA', (W, H), (24, 14, 8, 0)); body.putalpha(m.point(lambda v: int(v * .72)))
    L.alpha_composite(body)
    ImageDraw.Draw(L).rounded_rectangle([x0, y0, x1, y1], radius=PH // 2, outline=(255, 236, 200, 255) if sel else (255, 210, 150, 150), width=2)
    cx, cy = x0 + 44, y
    ImageDraw.Draw(L).ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(255, 250, 240, 255) if sel else (255, 190, 100, 255))
    text(L, (cx, cy + 1), str('①②③'.index(txt[0]) + 1), font(MOCHIY, 28), DARK, anchor='mm', shadow=0)
    text(L, (x0 + 82, cy + 2), txt[1:], font(ZM, 38), DARK if sel else WH, anchor='lm', shadow=0 if sel else .5)
    return L
def bar_img(p):
    """p=剩余比例"""
    L = canvas(); x0 = 540 - BAR_W // 2; d = ImageDraw.Draw(L)
    d.rounded_rectangle([x0, BAR_Y - 5, x0 + BAR_W, BAR_Y + 5], radius=5, fill=(255, 255, 255, 70))
    fw = int(BAR_W * p)
    if fw > 6:
        col = AMB if p > .35 else [(0, (255, 170, 120)), (1, (240, 70, 60))]
        g = grad_img(fw, 10, col, horiz=True).convert('RGBA'); mk = Image.new('L', (fw, 10), 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, fw - 1, 9], radius=5, fill=255)
        G = Image.new('L', (W, H), 0); ImageDraw.Draw(G).rounded_rectangle([x0, BAR_Y - 5, x0 + fw, BAR_Y + 5], radius=5, fill=200)
        gc = Image.new('RGBA', (W, H), (255, 160, 70, 0)); gc.putalpha(G.filter(ImageFilter.GaussianBlur(8))); L.alpha_composite(gc)
        g.putalpha(mk); L.alpha_composite(g, (x0, BAR_Y - 5))
        d.ellipse([x0 + fw - 8, BAR_Y - 8, x0 + fw + 8, BAR_Y + 8], fill=(255, 248, 230, 255))
    return L
def shade_img():
    a = np.clip((np.arange(H) - 900) / 500, 0, 1) ** 1.3 * 150
    L = Image.new('RGBA', (W, H), (16, 8, 2, 0)); L.putalpha(Image.fromarray(np.repeat(a.astype(np.uint8)[:, None], W, 1))); return L
def ptr_pos(opts, idx): return pill_w(opts[idx]) // 2 - 70, OYS[idx] + 14 - 960
def choices(pf, rf):
    ff = flash_file(); shf = save(shade_img(), 'ch_shade')
    for ci, (s0, D, fr) in enumerate(CH):
        last = PICK[ci] is None; pick = PICK[ci]; opts = OPTS[ci]
        TICKS.append(('start', s0))
        add('X-flash', f'选项{ci + 1} 定格闪', s0, .22, ff, k={'opacity': kf((0, .35), (.22, 0))}); sfx('u_flash', s0, .35)
        add('X-cshade', f'选项{ci + 1} 底部压暗', s0, D, shf, k={'opacity': kf((0, 0), (.2, 1), *([(D - .15, 1), (D, 0)] if not last else []))})
        # 倒计时条（15fps 逐帧）
        T0, TOT = .3, (2.7 if not last else D - .3 - .05)
        stop = CLICK if not last else D
        n = int(round((stop - T0) * 15))
        add('X-cbar', f'选项{ci + 1} 倒计时', s0 + .15, T0 - .15, save(bar_img(1), f'ch{ci + 1}_bar_full'), k={'opacity': kf((0, 0), (.12, 1)), 'scale': kf((0, .6), (.15, 1))})
        for j in range(n + 1):
            t = T0 + j / 15; p = clamp(1 - (t - T0) / TOT)
            dur = 1 / 15 if j < n else (D - .15 - t if not last else D - t)
            k = {'opacity': kf((dur - .12, 1), (dur, 0))} if (j == n and not last) else None
            add('X-cbar', f'选项{ci + 1} 倒计时', s0 + t, dur, save(bar_img(p), f'ch{ci + 1}_bar{j:02d}'), k=k)
            if j % 4 == 0 and t < stop - .05: TICKS.append(('tick', s0 + t))
        # 胶囊选项
        for oi, txt in enumerate(opts):
            t0 = s0 + .08 + oi * .07; y = OYS[oi]; fn = save(pill(txt, y, False), f'ch{ci + 1}_o{oi + 1}')
            k = {'scale': kf((0, .8), (.16, 1.04), (.26, 1)), 'opacity': kf((0, 0), (.12, 1))}; dur = s0 + D - t0
            if not last:
                r0 = s0 + CLICK + .03 - t0
                if oi != pick: k['opacity'] = kf((0, 0), (.12, 1), (r0, 1), (r0 + .15, 0)); dur = r0 + .15
                else: k['opacity'] = kf((0, 0), (.12, 1), (r0, 1), (r0 + .01, 0)); dur = r0 + .01
            add(f'X-co{oi + 1}', f'选项{ci + 1} {txt}', t0, dur, fn, ay=y / H, k=k)
        sfx('u_bubble', s0 + .1, .3)
        # 指针
        hv = HOVER[ci]; P0 = .35; px0, py0 = ptr_pos(opts, hv[0][1])
        xs, ys_ = [(0, px0 + 120), (hv[0][0] - P0, px0)], [(0, py0 + 260), (hv[0][0] - P0, py0)]
        for (t, idx), (_, pidx) in zip(hv[1:], hv[:-1]):
            a, b = ptr_pos(opts, pidx), ptr_pos(opts, idx)
            xs += [(t - .22 - P0, a[0]), (t - P0, b[0])]; ys_ += [(t - .22 - P0, a[1]), (t - P0, b[1])]
        if not last:
            end = D - .1 - P0
            add('X-ptr', f'选项{ci + 1} 指针', s0 + P0, end, pf, k={'x': kf(*xs), 'y': kf(*ys_), 'opacity': kf((0, 0), (.1, 1), (end - .12, 1), (end, 0)),
                'scale': kf((CLICK - .08 - P0, 1), (CLICK - P0, .78), (CLICK + .1 - P0, 1))})
            px, py = ptr_pos(opts, pick)
            add('X-prip', f'选项{ci + 1} 点击波纹', s0 + CLICK, .35, rf, k={'x': kf((0, px)), 'y': kf((0, py)), 'scale': kf((0, .7), (.35, 2.0)), 'opacity': kf((0, .9), (.35, 0))})
            y = OYS[pick]; r = D - CLICK - .03
            add('X-cs', f'选项{ci + 1} 选中', s0 + CLICK + .03, r, save(pill(opts[pick], y, True), f'ch{ci + 1}_sel'), ay=y / H,
                k={'scale': kf((0, 1), (.1, 1.1), (.22, 1.02)), 'opacity': kf((0, 1), (r - .13, 1), (r, 0))})
            sfx('u_click', s0 + CLICK - .02, .8); sfx('u_ok', s0 + CLICK + .03, .55)
            TICKS.append(('click', s0 + CLICK))
            add('X-flash', f'选项{ci + 1} 过渡闪', s0 + D - .12, .3, ff, k={'opacity': kf((0, 0), (.1, .45), (.3, 0))})
        else:
            add('X-ptr', f'选项{ci + 1} 指针犹豫', s0 + P0, D - P0, pf, k={'x': kf(*xs, (D - P0, xs[-1][1])), 'y': kf(*ys_, (D - P0, ys_[-1][1])), 'opacity': kf((0, 0), (.1, 1))})
            add('X-flash', '选项3→片尾 闪光', s0 + D - .22, .6, ff, k={'opacity': kf((0, 0), (.2, 1), (.6, 0))}); sfx('u_flash', s0 + D - .2, .7)
            TICKS.append(('end', s0 + D))
        # 选项段弹幕（上方/最下车道，不压选项）
        for j, s in enumerate(DMQ[ci]):
            st = s0 + .05 + j * .38; dur = s0 + D - st
            if dur < .5: continue
            sp = dm_sprite(s, amber=(j % 3 == 1)); L = canvas(); lane = DM_LANES[j % len(DM_LANES)]
            L.alpha_composite(sp, (540 - sp.width // 2, lane - sp.height // 2)); span = 540 + sp.width / 2 + 24
            add(f'X-dm{j + 1}', f'弹幕 {s}', st, dur, save(L, f'ch{ci + 1}_dm{j}'), k={'x': kf((0, span), (3.2, -span)), 'opacity': kf((0, .95))})

