# endcard3 · 三卡片尾板（JP 默认片尾）

样式照 `reference/投放参考/三卡片尾板_参考.webp`（用户指定的默认样式，2026-11-12）。至少 5.0 s（4 下连点最早在片尾 3.7 s 起，点完再留 0.4 s），片尾口播长了自动加长（`plan()` 算），1080×1920，画成图层放进 timeline，不单独出 mp4。本目录 `mmlib.py` 是它依赖的绘图库（字体、Logo、官方商店标）；图层函数用 `$SK/scripts/mmkit/layers.py`。

| 时间（片尾内） | 画面 |
|---|---|
| 0 | 闪白进片尾；深藏青背景 + 光斑（两层慢漂、一层闪烁）；顶部 Logo（图标 + 字标图，第一帧就在） |
| 0–0.5 | 三张角色卡扇形飞入：两侧往期卡（蓝边、外倾 ±9°、0.78 倍），中间本片角色（金边高亮 + 名字），回弹；0.2 s 起卡底「チャット数」胶囊（在卡片底部里面）持续往上跳 |
| 0.5 | 金橙渐变下载按钮（深色字，文字照全量文案按钮）弹入，之后扫光、呼吸 |
| 1.0 起 | 片尾口播 + 文案逐词出现（兼作字幕），末行金色渐变大字 |
| 1.5 | 按钮下方两个官方原版日文商店标（Google Play「で手に入れよう」/ App Store「からダウンロード」），外框一样大 |
| 口播说完后 | 半透明圆圈指针连点 4 下（间隔 0.3 s，波纹 + 按钮回弹）：首次点击 = max(片尾 3.7 s, 口播结束 + 0.15 s)；片尾时长 = max(4.9 s, 末次点击 + 0.4 s, 口播结束 + 1.0 s)，口播说完到结尾 ≥1 s |

## 文案来源
- 片尾口播按 rules/通用.md 取：全量文案写了口播就用，没写就从 `shortdrama-copy/references/投放高效文案.md` 按地区 → 性向取一句**短句**（改写只换屏蔽词和角色名）。
- 片尾展示文案 = 这句口播（逐词出现兼作字幕），长度照参考图「MiraiMindで 彼女を救えるのは あなただけ」，末行金色大字。片尾口播放在片尾 1.0 s，说完到结尾 ≥1 s。不把全量文案的长结尾卡读成口播。
- 补写的文字（聊天数等）进补充清单。

## 用法
直接从 Skill 目录 import，不复制到工程；本片 `gen.py` 片尾处：
```python
sys.path[:0] = [f"{SK}/scripts", f"{SK}/modules/endcard3"]
import endcard3
from mmkit.layers import Layers, kf, snap
L = Layers(f"{OUT}/layers")                         # 全片图层、音频都加在 L.CLIPS / L.AUDIO
…
p = endcard3.plan(E0, 片尾口播开始时间, 片尾口播时长)  # {"dur", "taps"}：片尾时长和 4 下点击时间，按口播长度算
END = snap(E0 + p["dur"]); L.END = END               # 成片总长按它定，不再用 E0 + endcard3.DUR
endcard3.build({"E0": E0, "layers": L,
                "VO4_T": 片尾口播开始时间, "VO4_D": 片尾口播时长, "VO4_W": 片尾口播逐词时间（可选；不给 VO4_D 时取末词结束）,
                "button_text": 全量文案按钮文字,
                "copy": [{"y": 1250, "size": 84, "gold": False, "tokens": [("前半句", 0.0)]},
                         {"y": 1372, "size": 128, "gold": True, "tokens": [("末行关键词", t)]}],   # 金色大字放末行（照参考图）
                "cards": [(左卡图, focusY, 名字, 聊天数, "filler"), (右卡图, …), (本片角色整帧, focusY, 卡片标题, 聊天数, "hero")]})
```
- `build()` 返回实际片尾时长（和 `plan()` 的 dur 一样）。图层、关键帧、1/30 s 吸附、用户音效、指针都用 `mmkit.layers`（`L.add_img / kf / snap / L.us / L.pointer_path`）。
- 旧用法照样能跑：ctx 里不给 `layers`，改给 `add_img / kf / snap / us / pointer_path`（工程 gen.py 里的同名函数）；`endcard3.DUR`（4.9）只是下限，成片总长要用 `build()` 的返回值。
- 文案每行都查出界：普通行按字宽留 60 px，金色末行按 半宽 + 描边 + 光晕、再乘弹入最大缩放 1.1 算，出界直接报错。
- 卡面来源按 rules/通用.md「角色图来源」：两侧取 library/cards.md 状态「可用」的卡，中间用本片原片整帧；名字取全量文案卡片标题。
- 商店标：`mmlib.store_badges()` 读 `mmlib.BADGE_DIR`（默认是 skill 内置的 `assets/官方素材/`，Logo 也从这里读；环境变量 `MM_BADGE_DIR` 只在换商店标时设，见 reference/环境.md）里的官方原版，同高等比缩放，App Store 外框按 Google Play 宽度补齐（边框色、圆角照它自己的原版），原版内容居中。找不到官方商店标文件时 `build()` 直接报错，不跳过。
- 音效用用户音效收集：闪白「进选项、闪白、照相音效」、卡片「回声弹出音效」、按钮/商店标「气泡提示音」、点击「咔嗒清脆点击」。

## 声音注意
- 片尾没有自带 BGM，靠承接段 BGM 延续；BGM 生成后量包络、断了按小节续接，见 rules/通用.md「BGM」。

读完校验口令：灯塔描金27
