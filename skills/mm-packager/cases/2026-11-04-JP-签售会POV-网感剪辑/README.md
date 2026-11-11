# 案例：JP · 女性向 · 签售会POV（C 网感剪辑，同脚本 5 角色）

> 版式 C ｜ 参考案例（目前唯一的 C 实现）｜ 脚本：本目录的 render_v2.py、render_end_v2.py、make_ui_cfg.py 可复用，但要先改两处才能运行：①常量 `P` 写死原工程，改成 `$P`；②依赖原工程 `工作/scripts/` 里的 render_pov.py、render_end.py（本目录没有，从原工程复制）。assemble_v3.py 的混音用侧链压 BGM，已作废，复用时改成整句平滑压低（rules/通用.md）。

## 本片参数（只属本片，不照搬）
- 地区 JP，女性向；PIL + ffmpeg 直接出片，1080×1920，每条 27.9 s。
- 结构：开场语气 1.15 s（「え、やばい…！」+ 推镜 + 抖动大字）→ 签售会 POV 快切 + 口播大字 → 定格缩进手机 → 划卡 / 聊天（转化承接）→ 尾板 6.8 s（Logo 首帧在顶部、5 张卡扇形飞入、卡底聊天数、主角卡粉色高亮、口播、5.5 s 点击）。
- 口播：克隆音色「日语可爱竹马」逐句生成 t0–t7。
- 工程：`$WORK_ROOT/2026年11月4日MM-JP-女性向-签售会POV`（`工作/{scripts,specs,ui,stills,tmp}`、`导出/`、`成品/`）。角色 A=蓮 B=陽向 C=律 D=奏 E=湊（`specs/chars.json`）。

## 脚本（本目录）
| 文件 | 作用 |
|---|---|
| `render_v2.py <spec> <out> [--stills t1,t2]` | 正片：镜头剪辑、推镜、大字（`shake` 抖动）、顶部 Logo、定格缩进手机、划卡/聊天 UI，输出无声 mp4 |
| `render_end_v2.py <角色> <out> [--stills …]` | 尾板：5 卡扇形 + 聊天数（完整数字千分位，飞入时滚动、之后每 0.28 s 跳涨）+ Logo + 按钮 |
| `assemble_v3.py <spec> <main> <out> <尾板>` | 拼接正片 + 尾板，混口播、音效、BGM 淡出（侧链闪避已作废，见上） |
| `make_ui_cfg.py <主角> <卡1> <卡2> <out>` | 多角色：生成划卡/聊天 UI 配置 |
| `contact_sheet.py` | 拆片联系表（字体写死 `C:/Windows/Fonts/arial.ttf`，非 Windows 要换） |
| `gen_bgm.py <out> <毫秒>` | ElevenLabs music 生成 BGM；prompt 里的 glockenspiel/chime、sidechained pads 和现行 BGM 避开项冲突（rules/通用.md），复用时删掉 |
| `specs/v3_E.json` | 湊版完整 spec（shots / caps / vo / bgFrame / swipe / chat）；其他角色只换 shots 源和 UI |

## 成品
`成品/MM-JP-女性向-签售会POV_{蓮,陽向,律,奏,湊}.mp4`；投放副本 `$UPLOAD_IN/` 同名。

## 修改记录（问题 → 怎么改 → 去向）
- 没验收就放进 `成品/` → 预览只放 `导出/`，验收后才复制到成品和投放目录。已进规则（rules/工程交付.md）；本片预览名 `预览vN_<角色>` 只属本片（现行命名见 rules/工程交付.md）
- 开头直接进叙事太快 → 先加约 1 s 语气词钩子（口播 + 推镜 + 大字）。已进规则（rules/C-网感剪辑.md）
- 抖动大字左侧出画 → 按最大位移算安全边界。已进规则（rules/通用.md）；170 号改 116 号 + 抖动 10 px 只属本片
- 剪辑段和尾板上方空一大块 → 顶部放 Logo；尾板 Logo 第一帧就在，动画只做在卡片上。已进规则（rules/C-网感剪辑.md）
- 聊天数写成「112.3万」→ 用户要完整数字 + 千分位（1,240,994）。只属本片：11-05 起 JP 用「万」或完整数字都可以（rules/JP.md）
- 尾板口播「听着没说完」改了三次，原因是 BGM 和尾板音效盖住末字 → 口播期间压 BGM、降尾板音效，BGM 在末句之后才淡出，用 ASR 核对末字。已进规则（rules/通用.md）
- 之后用户反馈「还没说完」是播放器问题 → 改之前先确认用户看的是哪个文件、用什么播放器。已进规则（rules/通用.md）
- 口播期间用侧链压 BGM → 已作废，改整句平滑压低。已进规则（rules/通用.md）
- 本片没有全量文案，卡片名字/标签/简介是包装自己写的、没给用户确认 → 包装补写的文案出片前列给用户确认（日文附中文）。已进规则（rules/通用.md）；这 5 张卡进 library/cards.md 时字段来源标「包装自写」
