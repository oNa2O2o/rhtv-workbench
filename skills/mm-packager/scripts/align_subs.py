#!/usr/bin/env python
"""多版本字幕时间自动对齐：
  python align_subs.py --p <05_包装目录> --ver N [--template <版本1 版本配置.json>] [--apply]
                       [--copy <全量文案.md>] [--role 名字] [--a-end 秒] [--b-in 秒] [--b-end 秒] [--off 秒]
输入：工程素材/抽帧_版本N/{words.json, energy.json}（prep.py 出的）；模板缺省 工程素材/抽帧_版本1/版本配置.json。
底稿：本版本已有 版本配置.json 就用它（分卡、位置、定格帧、映射锚点都保留），没有就用模板；只重算每张卡和每个词的时间。
- 文字（全量文案）逐字 ↔ ASR 逐字做序列对齐（ASR 词内按字数均分，拖长的尾音每字最多算 0.15 s），对不上的字按前后已对齐的字插值；
  「……」「——」这类纯符号词：在卡首跟下一个词（提前 0.13 s），在卡中跟上一个词的结束。
- 句首卡（全量文案每句台词的第一张卡）起点提前到 0.4 s 内的 −35 dB 能量起点。句首按全量文案的台词行算，不写死；
  模板卡片写了 "sent_start": true/false 时以模板为准；全量文案认不出时每张卡都按句首处理（只有前面紧挨停顿的卡会被提前）。
- 卡尾 = min(下一卡起点 − 1 帧, 末字结束 + 0.4, 本段在成片里的结束)。
- 段结构读模板：模板有 A_END（第一段原片结束 = 选项定格1 起点）时按两段原片算：
    成片 = 原片（原片 < A_END）；成片 = 原片 − B_IN + A_END + OFF（第二段；OFF = 选项定格1 时长，模板键 OFF 或 --off）。
  本版本切点：--a-end/--b-in/--b-end > 本版本已有配置 > 按 ASR 估（第一段卡的末字 +0.35；全部末字 +0.2，不超过原片长度；B_IN = A_END）。
  模板没有 A_END 时成片 = 原片（单段，C 版式这类）。
- 默认写 工程素材/抽帧_版本N/版本配置_草稿.json，不动手调过的正式配置；看完对齐表再加 --apply 写 版本配置.json。
"""
import argparse, copy, difflib, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PUNCT = re.compile(r"[\s、。？！?!…—「」『』,.・ー〜~]")
TAIL_MAX = 0.15          # 拖长的尾音每字最多算的秒数
SYM_LEAD = 0.13          # 卡首纯符号词提前量
ONSET_MAX = 0.4          # 句首卡最多提前到的能量起点距离
CARD_TAIL = 0.4          # 末字后卡片多留
FRAME = 0.033
A_PAD, B_PAD = 0.35, 0.2  # 估切点：第一段末字 +0.35，全片末字 +0.2


def snap(t): return round(t * 30) / 30
def clean(s): return PUNCT.sub("", s)


def asr_chars(words):
    ac, at, ae = [], [], []
    for w in words:
        cs = clean(w["w"])
        for i, c in enumerate(cs):
            t0 = w["s"] + (w["e"] - w["s"]) * i / len(cs)
            ac.append(c); at.append(t0); ae.append(min(w["s"] + (w["e"] - w["s"]) * (i + 1) / len(cs), t0 + TAIL_MAX))
    return ac, at, ae


def sentence_starts(subs, lines):
    """全量文案台词行 → 哪些卡是句首卡（卡的第一个字是某行的第一个字）。"""
    if any("sent_start" in c for c in subs):
        return {ci for ci, c in enumerate(subs) if c.get("sent_start")}
    if not lines: return None
    lc, lstart = [], set()
    for ln in lines:
        lstart.add(len(lc)); lc += list(clean(ln))
    cc, cfirst = [], {}
    for ci, c in enumerate(subs):
        cfirst[ci] = len(cc)
        for _, ts in c["lines"]:
            for t in ts: cc += list(clean(t[0]))
    mp = {}
    for a, b, n in difflib.SequenceMatcher(None, cc, lc, autojunk=False).get_matching_blocks():
        for i in range(n): mp[a + i] = b + i
    if len(mp) < 0.8 * max(1, len(cc)): return None
    return {ci for ci, i in cfirst.items() if mp.get(i) in lstart}


def align(subs, words, energy, to_out, cap_of, sent_start=None):
    """返回 (新 subs, 诊断)。to_out：原片秒 → 成片秒；cap_of(原片起点) → 这张卡在成片里的封顶。"""
    ac, at, ae = asr_chars(words)
    toks = []                                    # (card, line, idx, text)
    for ci, c in enumerate(subs):
        for li, (_, ts) in enumerate(c["lines"]):
            for ti, t in enumerate(ts): toks.append((ci, li, ti, t[0]))
    sc, owner = [], []
    for k, (_, _, _, txt) in enumerate(toks):
        for ch in clean(txt): sc.append(ch); owner.append(k)
    mp = {}
    for a, b, n in difflib.SequenceMatcher(None, sc, ac, autojunk=False).get_matching_blocks():
        for i in range(n): mp[a + i] = b + i
    if not mp: raise SystemExit("ASR 和文案一个字都对不上：检查 words.json 语言、文案是不是这条片")
    known = sorted(mp)

    def char_time(i, end=False):
        arr = ae if end else at
        if i in mp: return arr[mp[i]]
        lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
        if lo is None: return arr[mp[hi]]
        if hi is None: return arr[mp[lo]]
        return arr[mp[lo]] + (arr[mp[hi]] - arr[mp[lo]]) * (i - lo) / (hi - lo)

    first_char, last_char = {}, {}
    for i, k in enumerate(owner): first_char.setdefault(k, i); last_char[k] = i
    tok_t = {}
    for k in range(len(toks)):
        if k in first_char: tok_t[k] = char_time(first_char[k])
        else:
            prev = k - 1
            same_card_prev = prev >= 0 and toks[prev][0] == toks[k][0]
            tok_t[k] = char_time(last_char[prev], end=True) if same_card_prev and prev in last_char else None
    for k in reversed(range(len(toks))):          # 卡首纯符号词：跟下一个词（倒着填，连续符号也不越界）
        if tok_t[k] is None:
            tok_t[k] = tok_t[k + 1] - SYM_LEAD if k + 1 < len(toks) else char_time(len(sc) - 1, end=True)

    out = copy.deepcopy(subs)
    starts, ends = [], []
    for ci in range(len(out)):
        ks = [k for k, t in enumerate(toks) if t[0] == ci]
        s0 = tok_t[ks[0]]
        if sent_start is None or ci in sent_start:
            for a, b in energy:
                if a <= s0 + 0.05 and s0 - a <= ONSET_MAX and b > s0: s0 = min(s0, a); break
        real = [k for k in ks if k in last_char]
        starts.append(s0); ends.append(char_time(last_char[max(real)], end=True) if real else tok_t[ks[-1]])
    for ci, c in enumerate(out):
        ks = [k for k, t in enumerate(toks) if t[0] == ci]
        st = snap(to_out(starts[ci]))
        cap = cap_of(starts[ci])
        nxt = snap(to_out(starts[ci + 1])) - FRAME if ci + 1 < len(starts) else cap
        en = snap(min(nxt, to_out(ends[ci]) + CARD_TAIL, cap))
        c["start"], c["end"] = st, en
        for k in ks:
            _, li, ti, _ = toks[k]
            c["lines"][li][1][ti][1] = round(max(st, snap(to_out(tok_t[k]))), 3)
        c["lines"][0][1][0][1] = st
    unm = "".join(sc[i] for i in range(len(sc)) if i not in mp)
    last_end = {}                                 # 每张卡所有词里最晚的末字结束（原片秒），估切点用
    for k in last_char: last_end[toks[k][0]] = max(last_end.get(toks[k][0], -1e9), char_time(last_char[k], end=True))
    return out, {"unmatched": unm, "n": len(sc), "src_ends": last_end}


def src_duration(fr):
    pcm = f"{fr}/audio16k.pcm"
    return os.path.getsize(pcm) / 32000 if os.path.exists(pcm) else None


def main(argv=None):
    ap = argparse.ArgumentParser(description="多版本字幕时间自动对齐（默认写草稿）")
    ap.add_argument("--p", required=True, help="05_包装目录")
    ap.add_argument("--ver", required=True)
    ap.add_argument("--template", help="版本1 版本配置.json（缺省 工程素材/抽帧_版本1/版本配置.json）")
    ap.add_argument("--apply", action="store_true", help="写正式 版本配置.json（缺省写 版本配置_草稿.json）")
    ap.add_argument("--copy", help="全量文案.md（缺省 $P/全量文案.md；用来认句首卡）")
    ap.add_argument("--lang", default="ja")
    ap.add_argument("--role")
    ap.add_argument("--a-end", type=float); ap.add_argument("--b-in", type=float); ap.add_argument("--b-end", type=float)
    ap.add_argument("--off", type=float, help="选项定格1 时长（第二段 成片 − 原片 的规范偏移）")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    P, N = a.p.replace("\\", "/").rstrip("/"), str(a.ver)
    FR = f"{P}/工程素材/抽帧_版本{N}"
    TPL_P = a.template or f"{P}/工程素材/抽帧_版本1/版本配置.json"
    TPL = json.load(open(TPL_P, encoding="utf-8"))
    OWN_P = f"{FR}/版本配置.json"
    own = json.load(open(OWN_P, encoding="utf-8")) if os.path.exists(OWN_P) and os.path.abspath(OWN_P) != os.path.abspath(TPL_P) else None
    base = own or TPL
    words = json.load(open(f"{FR}/words.json", encoding="utf-8"))["words"]
    energy = json.load(open(f"{FR}/energy.json", encoding="utf-8"))["segments"]

    from prep import dialogue_lines
    lines = dialogue_lines(a.copy or f"{P}/全量文案.md", a.lang)
    sent = sentence_starts(base["subs"], lines)
    print("句首卡：", sorted(sent) if sent is not None else "全量文案没认出台词行，每张卡都按句首处理")

    two = "A_END" in TPL or a.a_end is not None
    out = copy.deepcopy(base)
    out["role"] = a.role or (own.get("role") if own else None) or f"v{N}"
    if two:
        OFF = a.off if a.off is not None else TPL.get("OFF")
        if OFF is None: raise SystemExit("模板有 A_END 但没有 OFF（选项定格1 时长 = 第二段成片起点 − B_IN）：加 --off 或在模板里写 OFF")
        # 先用估的切点跑一遍拿到逐字原片时间，再定本版本切点
        tA = snap(TPL["A_END"]) if "A_END" in TPL else snap(a.a_end)
        seg1 = {ci for ci, c in enumerate(TPL["subs"]) if c["start"] < tA - 0.03}
        _, diag = align(base["subs"], words, energy, lambda t: t, lambda t: 1e9, sent)
        ends = diag["src_ends"]
        dur = src_duration(FR)
        line1_end = max((ends[ci] for ci in seg1), default=None)
        all_end = max(ends.values())
        A_END = snap(a.a_end if a.a_end is not None else (own or {}).get("A_END") or (line1_end + A_PAD if line1_end is not None else tA))
        B_IN = snap(a.b_in if a.b_in is not None else (own or {}).get("B_IN", A_END))
        B_END = snap(a.b_end if a.b_end is not None else (own or {}).get("B_END") or (min(dur, all_end + B_PAD) if dur else all_end + B_PAD))
        B1 = snap(A_END + OFF + B_END - B_IN)

        def to_out(t): return t if t < A_END - 0.03 else t - B_IN + A_END + OFF
        def cap_of(t): return A_END - FRAME if t < A_END - 0.03 else B1
        out["A_END"], out["B_IN"], out["B_END"] = A_END, B_IN, B_END
        head = f"A_END={A_END:.3f} B_IN={B_IN:.3f} B_END={B_END:.3f}（成片第二段结束 {B1:.3f}；OFF={OFF}）；第一段末字 {line1_end}，全部末字 {all_end:.2f}，原片长 {dur}"
    else:
        def to_out(t): return t
        def cap_of(t): return 1e9
        head = "单段：成片 = 原片"
    subs, diag = align(base["subs"], words, energy, to_out, cap_of, sent)
    out["subs"] = subs
    note = "本文件由 align_subs.py 按本版本 ASR 自动对齐生成，再人工看帧核对。"
    if note not in out.get("_说明", ""): out["_说明"] = (out.get("_说明", "") + " " + note).strip()
    dst = f"{FR}/版本配置.json" if a.apply else f"{FR}/版本配置_草稿.json"
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(dst); print(head)
    for c in subs:
        print(f"{c['start']:6.3f}-{c['end']:6.3f} ", " | ".join(" ".join(f"{t[0]}@{t[1]}" for t in ts) for _, ts in c["lines"]))
    print("未对齐字:", diag["unmatched"] or "无", f"({len(diag['unmatched'])}/{diag['n']})")


if __name__ == "__main__":
    main()
