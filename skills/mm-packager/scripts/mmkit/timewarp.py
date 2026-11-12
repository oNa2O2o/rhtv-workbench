"""多版本时间映射：gen.py 只按版本1 写规范时间，build() 最后用 TimeWarp 把整条 timeline 换到本版本（rules/工程交付.md「多版本」）。

用法（工程 gen.py）：
    from mmkit.timewarp import TimeWarp
    canon = {"A_END": A_END, "F1_END": F1[1], "B_IN": B_IN, "B_END": snap(27.9), "OFF": OFF, "B1": B1, "F2_END": F2[1]}
    TWP = TimeWarp(CFG, canon, open_hit=0.233)      # CFG = 工程素材/抽帧_版本N/版本配置.json
    vsrc = TWP.vsrc                                   # 规范时间 → 本版本原片时间（取帧用）
    ...
    end_v = TWP.warp(CLIPS, AUDIO, END, SRC)          # 原地改 clips/audio，返回映射后的总长

canon（规范时间，都按版本1）：
    A_END   第一段原片结束 = 选项定格1 起点（成片 = 原片）
    F1_END  选项定格1 结束 = 第二段成片起点
    B_IN    第二段原片入点
    B_END   第二段原片出点
    OFF     第二段 成片 − 原片（缺省 F1_END − B_IN）
    B1      第二段成片结束 = 选项定格2 起点（缺省 snap(F1_END + B_END − B_IN)）
    F2_END  选项定格2 结束
cfg（本版本 版本配置.json）用到的键：A_END、B_IN、B_END（本版本原片秒），A1_MAP / A2_MAP（[[版本1原片秒, 本版本原片秒], …] 锚点）。
没有这些键时恒等映射（版本1 原样不动）。

映射规则：
- 第一段原片：规范 [0, A_END] → 本版本 [0, A_END_v]，中间按 A1_MAP 分段线性
- 选项定格1：整体平移到 A_END_v 起
- 第二段原片：规范原片 [B_IN, B_END] → 本版本原片 [B_IN_v, B_END_v]，中间按 A2_MAP 分段线性
- 选项定格2 及以后：整体平移（本版本第二段结束 − 规范 B1）
- 标了 "_nowarp" 的 clip / audio 不映射（逐词字幕用本版本时间，不映射）；结果时间吸附到 1/30 s
- 名字里含 stretch 关键字的音频（BGM、原片、产品 UI 划卡）随映射拉长，其余音效只平移起点
- 同一 BGM 文件、原本同相位的相邻段映射后保持同相位：靠近结构切点的段锚在切点（in 不变，重拍对齐切点），
  其余段沿用前一段的相位，段内不拉伸错相（见 _bgm_phase）
"""

STRETCH = ("bgm_", "/素材/视频_", "产品UI-划卡_")


def snap(t):
    return round(t * 30) / 30


def _pl(x, pts):
    """分段线性；超出最后一个锚点按斜率 1 外推。"""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1 + 1e-9:
            return y1 if x1 - x0 < 1e-9 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1] + x - pts[-1][0]


class TimeWarp:
    def __init__(self, cfg, canon, stretch=STRETCH, bgm_key="bgm_", open_hit=None):
        """stretch：随映射拉长的音频路径关键字；bgm_key：要保持同源相位的音频路径关键字；
        open_hit：开场重拍对齐的规范时间（如开场闪白 0.233），跨过它的 BGM 段让重拍仍落在映射后的这一刻；None 不处理。"""
        cfg = cfg or {}
        self.A_END = canon["A_END"]
        self.F1_END = canon["F1_END"]
        self.B_IN = canon.get("B_IN", self.A_END)
        self.B_END = canon["B_END"]
        self.OFF = canon.get("OFF", self.F1_END - self.B_IN)
        self.B1 = canon.get("B1", snap(self.F1_END + self.B_END - self.B_IN))
        self.F2_END = canon["F2_END"]
        self.stretch, self.bgm_key, self.open_hit = tuple(stretch), bgm_key, open_hit

        self.V_A = snap(cfg.get("A_END", self.A_END))
        self.V_B = snap(cfg.get("B_IN", self.V_A))
        self.V_E = snap(cfg.get("B_END", self.B_END))
        self.V_B0 = snap(self.V_A + (self.F1_END - self.A_END))
        self.V_B1 = snap(self.V_B0 + self.V_E - self.V_B)
        self.V_S = self.V_B1 - self.B1
        self.MAP1 = [(0.0, 0.0)] + [tuple(x) for x in cfg.get("A1_MAP", [])] + [(self.A_END, self.V_A)]
        self.MAP2 = [(self.B_IN, self.V_B)] + [tuple(x) for x in cfg.get("A2_MAP", [])] + [(self.B_END, self.V_E)]
        self.BOUNDS = [self.A_END, self.F1_END, self.B1, self.F2_END]     # 结构切点（规范时间）

    def TW(self, t):
        """规范成片时间 → 本版本成片时间。"""
        if t <= self.A_END + 1e-6: return _pl(t, self.MAP1)
        if t <= self.F1_END + 1e-6: return t - self.A_END + self.V_A
        if t <= self.B1 + 1e-6: return _pl(t - self.OFF, self.MAP2) - self.V_B + self.V_B0
        return t + self.V_S

    def vsrc(self, t):
        """规范成片时间 t 时，本版本画面对应的原片时间（取帧用）。"""
        if t <= self.A_END + 1e-6: return self.TW(t)
        return _pl(t - self.OFF, self.MAP2)

    def _bgm_phase(self, audio, orig):
        """同一 BGM 文件、原本同相位的相邻段（交叉淡化）映射后要保持同相位，否则交叉处同一首曲子错开叠在一起。
        靠近结构切点的段锚在自己起点（in 不变，音乐重拍对齐切点），前一段的重叠区换成本段相位的尾巴（相位跳变藏在切点的闪白/定格音效下）；
        其余段沿用前一段的相位（连续不跳）。跨过 open_hit 的段让重拍仍落在映射后的 open_hit。恒等映射时什么都不变。"""
        TW, oh = self.TW, self.open_hit
        extra, by = [], {}
        for a in audio:
            if id(a) in orig: by.setdefault(a["src"], []).append(a)
        for items in by.values():
            items.sort(key=lambda a: orig[id(a)][0])
            prev = None
            for a in items:
                st, en, i0 = orig[id(a)]
                if oh is not None and st < oh < en:
                    a["in"] = round(i0 + oh - st - (TW(oh) - TW(st)), 4)
                if prev is not None:
                    pst, pen, pi0 = orig[id(prev)]
                    if abs((st - i0) - (pst - pi0)) < 0.01 and pen > st - 1e-6:
                        if any(st - 0.8 <= b <= pen + 0.05 for b in self.BOUNDS):
                            if abs((prev["start"] - prev["in"]) - (a["start"] - a["in"])) > 0.01 and prev["start"] + prev["duration"] > a["start"] + 0.04:
                                extra.append({**prev, "start": a["start"], "duration": round(prev["start"] + prev["duration"] - a["start"], 4),
                                              "in": a["in"], "fadeIn": 0.04, "fadeOut": prev["fadeOut"]})
                                prev["duration"] = round(a["start"] + 0.04 - prev["start"], 4); prev["fadeOut"] = 0.04
                        else:
                            a["in"] = round(a["start"] - (prev["start"] - prev["in"]), 4)
                prev = a
        audio.extend(extra)

    def warp(self, clips, audio, end, src_video):
        """把整条 timeline（clips、audio，原地修改）从规范时间换到本版本，返回映射后的总长。
        src_video：本版本原片路径（第二段原片的 in 换成本版本 B_IN）。"""
        TW = self.TW
        end2 = snap(TW(end))
        orig = {id(a): (a["start"], a["start"] + a["duration"], a.get("in", 0)) for a in audio if self.bgm_key in a["src"] and not a.get("_nowarp")}
        for c in clips:
            if c.pop("_nowarp", False): continue
            st, en = snap(c["start"]), snap(c["start"] + c["duration"])   # 先吸附到帧网格：同一时刻不同算法的浮点误差会让半帧处一个舍一个入，空出 1 帧（v2/v4 +35 前数值条闪断）
            s2, e2 = snap(TW(st)), snap(TW(en))
            if c["duration"] >= 1 / 30 - 1e-4: e2 = max(e2, s2 + 1 / 30)
            for ks in c.get("keyframes", {}).values():
                for k in ks: k["t"] = round(TW(st + k["t"]) - s2, 4)
            c["start"], c["duration"] = s2, round((e2 - s2) * 30) / 30
            if c["type"] == "video" and c["src"] == src_video and c.get("in", 0) > 0: c["in"] = self.V_B
        for a in audio:
            if a.pop("_nowarp", False): continue
            st, en = a["start"], a["start"] + a["duration"]
            a["start"] = round(TW(st), 4)
            if any(k in a["src"] for k in self.stretch): a["duration"] = round(TW(en) - TW(st), 4)
            a["duration"] = round(min(a["duration"], end2 - a["start"]), 4)
            if a["src"] == src_video and a["in"] > 0: a["in"] = self.V_B
        self._bgm_phase(audio, orig)
        return end2
