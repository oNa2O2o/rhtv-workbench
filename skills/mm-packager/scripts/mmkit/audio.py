"""音频工具。

duck_points()：口播/台词处压低 BGM（或产品 UI、尾板 mp4 自带的声音）的增益曲线，直接填进 timeline audio 条目的 "gain"
（render.py 文件头有格式）。BGM 用一条连续 audio + gain，不拆成多段各自 fade（首尾相接各自淡变会在交界出音量凹坑）。

    from mmkit.audio import duck_points
    bgm = {"src": BGM, "start": 0, "duration": END, "in": 0, "fadeOut": 0.6,
           "gain": duck_points([(vo_t, vo_t + vo_d) for vo_t, vo_d in VO], base=0.30, duck=0.10)}
"""


def duck_points(vo_intervals, base, duck, ramp=0.25, merge_gap=0.3):
    """vo_intervals：[(开始秒, 结束秒), …]，成片绝对秒（要说完多停一会儿再回升，就把结束秒往后延再传进来）。
    base：不压时的音量；duck：压低时的音量；ramp：压低/回升各用多少秒（压低在开口前完成，回升从说完开始）；
    merge_gap：两句间隔小于它就当一句，中间不回升。
    返回 [[t, v], …]（成片绝对秒，分段线性），没有区间时返回 []（= 不压）。"""
    iv = sorted((float(a), float(b)) for a, b in vo_intervals if b > a)
    merged = []
    for a, b in iv:
        if merged and a - merged[-1][1] < merge_gap: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    if not merged: return []
    pts = [(merged[0][0] - ramp, base), (merged[0][0], duck)]
    for (a0, b0), (a1, b1) in zip(merged, merged[1:]):
        gap = a1 - b0
        if gap >= 2 * ramp:                                   # 来得及回到 base
            pts += [(b0, duck), (b0 + ramp, base), (a1 - ramp, base), (a1, duck)]
        else:                                                 # 回升到一半就要再压：在中点相遇
            mid = (b0 + a1) / 2
            pts += [(b0, duck), (mid, duck + (base - duck) * (mid - b0) / ramp), (a1, duck)]
    b = merged[-1][1]
    pts += [(b, duck), (b + ramp, base)]
    out = []
    for t, v in pts:
        t, v = round(t, 4), round(v, 4)
        if out and abs(out[-1][0] - t) < 1e-9 and abs(out[-1][1] - v) < 1e-9: continue
        out.append([t, v])
    return out
