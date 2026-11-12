"""多版本字幕时间：python make_config.py N [--role 角色名] [--a-end 秒] [--b-end 秒]
以 本版本已有的 版本配置.json（没有就用版本1 的）为底（文字、分卡、位置、重点词、定格帧、映射锚点都保留），只重算每个词的出现时间：
全量文案逐字 ↔ ASR 逐字做序列对齐（ASR 词内按字数均分），对不上的字按前后已对齐的字插值；
句首卡的起点提前到 −35 dB 能量起点（≤0.4 s 内）；卡尾 = min(下一卡起点 −0.033, 末字结束 +0.4)，第一段封顶 12.3、第二段封顶 30.5。
切点：A_END（第一段原片结束 = 选项定格1 起点）、B_END（第二段原片结束），没给就按 ASR：第二句末字 +0.35、第四句末字 +0.2（≤ 28.0）。
成片时间：原片 < A_END → 不变；否则 原片 − B_IN + A_END + 2.6。卡尾封顶：第一段 A_END − 0.033，第二段 = 第二段在成片里的结束。
输出写回 工程素材/抽帧_版本N/版本配置.json（手调过的字幕时间会被覆盖：先跑这个，最后再手调）。"""
import difflib, json, os, re, sys

N = sys.argv[1]
ROLE = sys.argv[sys.argv.index("--role") + 1] if "--role" in sys.argv else f"v{N}"
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
FR = f"{P}/工程素材/抽帧_版本{N}"
BASE = f"{FR}/版本配置.json" if os.path.exists(f"{FR}/版本配置.json") else f"{P}/工程素材/抽帧_版本1/版本配置.json"
T1 = json.load(open(BASE, encoding="utf-8"))
if "--role" not in sys.argv and N != "1" and "抽帧_版本1" not in BASE: ROLE = T1["role"]
W = json.load(open(f"{FR}/words.json", encoding="utf-8"))["words"]
EN = json.load(open(f"{FR}/energy.json", encoding="utf-8"))["segments"]
OFF = 2.6
PUNCT = re.compile(r"[\s、。？！?!…—「」『』,.・ー〜~]")


def snap(t): return round(t * 30) / 30
def clean(s): return PUNCT.sub("", s)


# ASR 逐字时间
ac, at, ae = [], [], []
for w in W:
    cs = clean(w["w"])
    for i, c in enumerate(cs):
        t0 = w["s"] + (w["e"] - w["s"]) * i / len(cs)
        ac.append(c); at.append(t0); ae.append(min(w["s"] + (w["e"] - w["s"]) * (i + 1) / len(cs), t0 + 0.15))   # 拖长的尾音不算

# 文案逐字（按 版本1 的卡/行/词顺序）
toks = []                                    # (card, line, idx, text)
for ci, c in enumerate(T1["subs"]):
    for li, (y, ts) in enumerate(c["lines"]):
        for ti, t in enumerate(ts): toks.append((ci, li, ti, t[0]))
sc, owner = [], []
for k, (_, _, _, txt) in enumerate(toks):
    for ch in clean(txt): sc.append(ch); owner.append(k)
mp = {}
for a, b, n in difflib.SequenceMatcher(None, sc, ac, autojunk=False).get_matching_blocks():
    for i in range(n): mp[a + i] = b + i
known = sorted(mp)


def char_time(i, end=False):
    arr = ae if end else at
    if i in mp: return arr[mp[i]]
    lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
    if lo is None: return arr[mp[hi]]
    if hi is None: return arr[mp[lo]]
    return arr[mp[lo]] + (arr[mp[hi]] - arr[mp[lo]]) * (i - lo) / (hi - lo)


first_char = {}; last_char = {}
for i, k in enumerate(owner): first_char.setdefault(k, i); last_char[k] = i
tok_t = {}
for k in range(len(toks)):
    if k in first_char: tok_t[k] = char_time(first_char[k])
    else:                                      # 「……」「——」：卡首跟下一个词，卡中跟上一个词的结束
        prev = k - 1
        same_card_prev = prev >= 0 and toks[prev][0] == toks[k][0]
        tok_t[k] = char_time(last_char[prev], end=True) if same_card_prev and prev in last_char else None
for k in range(len(toks)):
    if tok_t[k] is None: tok_t[k] = tok_t[k + 1] - 0.13

def arg(k): return float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else None
line2_end = max(char_time(last_char[k], end=True) for k in last_char if toks[k][0] <= 3)
line4_end = max(char_time(last_char[k], end=True) for k in last_char)
A_END = snap(arg("--a-end") or (T1.get("A_END") if "抽帧_版本1" not in BASE else None) or line2_end + 0.35)
B_IN = snap(T1.get("B_IN", A_END)) if "抽帧_版本1" not in BASE else A_END
B_END = snap(arg("--b-end") or (T1.get("B_END") if "抽帧_版本1" not in BASE else None) or min(28.0, line4_end + 0.2))
B1 = snap(A_END + OFF + B_END - B_IN)
def to_out(t_src): return t_src if t_src < A_END - 0.03 else t_src - B_IN + A_END + OFF
SENT_START = {0, 2, 4, 6}                      # 句首卡（文案每句的第一张）
out = json.loads(json.dumps(T1)); out["role"] = ROLE
out["A_END"], out["B_IN"], out["B_END"] = A_END, B_IN, B_END
out["_说明"] = T1["_说明"] + " 本文件由 make_config.py 按本版本 ASR 自动对齐生成，再人工看帧核对。"
starts, ends = [], []
for ci, c in enumerate(out["subs"]):
    ks = [k for k, t in enumerate(toks) if t[0] == ci]
    s0 = tok_t[ks[0]]
    if ci in SENT_START:
        for a, b in EN:
            if a <= s0 + 0.05 and s0 - a <= 0.4 and b > s0: s0 = min(s0, a); break
    lastk = max(k for k in ks if k in last_char)
    starts.append(s0); ends.append(char_time(last_char[lastk], end=True))
for ci, c in enumerate(out["subs"]):
    ks = [k for k, t in enumerate(toks) if t[0] == ci]
    st = snap(to_out(starts[ci]))
    cap = A_END - 0.033 if starts[ci] < A_END - 0.03 else B1
    nxt = snap(to_out(starts[ci + 1])) - 0.033 if ci + 1 < len(starts) else cap
    en = snap(min(nxt, to_out(ends[ci]) + 0.4, cap))
    c["start"], c["end"] = st, en
    for k in ks:
        _, li, ti, _ = toks[k]
        tt = max(st, snap(to_out(tok_t[k])))
        c["lines"][li][1][ti][1] = round(tt, 3)
    c["lines"][0][1][0][1] = st
dst = f"{FR}/版本配置.json" if N != "1" else f"{FR}/版本配置_草稿.json"
json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(dst, f"A_END={A_END} B_IN={B_IN} B_END={B_END}（成片第二段结束 {B1}）；第二句末字 {line2_end:.2f}，第四句末字 {line4_end:.2f}")
for c in out["subs"]:
    print(f"{c['start']:6.3f}-{c['end']:6.3f} ", " | ".join(" ".join(f"{t[0]}@{t[1]}" for t in ts) for _, ts in c["lines"]))
unm = [sc[i] for i in range(len(sc)) if i not in mp]
print("未对齐字:", "".join(unm) or "无", f"({len(unm)}/{len(sc)})")
