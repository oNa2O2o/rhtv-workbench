---
name: mm-packager
version: 3.0.0
description: 把一个视频 + 一份全量文案包装成 MM 投放成片。只有两种版式：B 剧情选择（原片剧情 + 选项定格 + 好感度/数值条 → 产品 UI 承接 → 尾板）、C 网感剪辑（语气词钩子 + 原片快切 + 口播大字 → 产品 UI 承接 → 尾板）。包装负责补全口播、标题、目标、重点词、产品 UI 卡片字段、尾板文案，以及字幕/气泡、选项定格、数值条、app-ui 划卡/聊天承接、自做片尾或 JP 尾板，口播/BGM/音效用 ElevenLabs 生成。不用编辑器：PIL 生成图层 → timeline.json → scripts/render.py 出校对预览/成片，验收后交付到工程目录的「成品」；支持多版本（同台词换角色）批量出片。用户说“包装这个视频”“MM 包装”“做 MM-KR/JP/EN/TC 包装”“AI包装”“重新设计包装”“剧情选择”“加选项”“网感剪辑”“迭代版本”“换角色同台词”“无BGM版”“加JP尾板”“接尾板”“划卡承接”“用 v5 编辑器包装/mm-workbench-v5”时使用（旧名 mm-workbench-v5 一律走本 Skill）。
---

# MM 包装（mm-packager）

不用编辑器。每条片子 = 工程目录里的脚本：`gen.py`（PIL 画图层）→ `to_timeline`（写 `timeline.json`）→ `scripts/render.py`（逐帧合成 + ffmpeg 混音出片）。B、C 都这样做，脚本跟着工程走（方便复现和改版）〔2026-11-09〕

变量：`$SK` = 本 Skill 目录，`$RES` = 共享资源目录（环境变量 `MM_RES`），`$P` = 工程目录，`$WORK_ROOT` / `$UPLOAD_IN` 等见 `reference/环境.md`（本机值只写在那里）。

## 分工
- **剧本（shortdrama-copy）给**：分幕、台词、表演指示、选项、数值（名称、触发点、幅度）。这些照全量文案做，不改。
- **包装补**：口播、标题、「目标」、重点词、产品 UI 卡片字段（名字/标签/简介/chat 消息/聊天数）、尾板文案、按钮文字。全量文案里已经写了的直接用，没写的由包装补写。
- 屏幕文字来源、补充文案怎么写、去标点：见 `rules/通用.md`。

## 版式
| 版式 | 结构 | 参考案例 |
|---|---|---|
| **B 剧情选择** | 原片剧情 + 选项定格 + 数值条 → 最后一题可以不点（留钩子）→ 定格缩进手机 + app-ui 划卡/聊天承接 → 尾板 | `cases/2026-11-05-JP-追放された女騎士`、`cases/2026-11-05-JP-上の階のスポーツ女子`、`cases/2026-11-02-JP-命令模式保镖` |
| **C 网感剪辑** | ≤1 s 语气词钩子（口播 + 推镜 + 大字）→ 原片快切 + 口播大字 → 定格缩进手机 → app-ui 承接 → 尾板 | `cases/2026-11-04-JP-签售会POV-网感剪辑` |

版式规则分别在 `rules/B-剧情选择.md`、`rules/C-网感剪辑.md`〔2026-11-04/05〕

## 流程
0. **环境**：`python $SK/scripts/check_env.py`，缺的依赖自己装，交付说明里写装了什么。
1. **拆片**：抽帧 + 联系表 + `scripts/asr.py` 取时间 + 能量核对，先写拆片笔记（做法见 `rules/工程交付.md`）。
2. **定方案**（给用户确认后才动手）：
   - 读 `rules/通用.md` + 版式 `rules/B-剧情选择.md` 或 `rules/C-网感剪辑.md` + 地区 `rules/JP.md`；可选套路看 `library/打法.md`。
   - 给时间表，栏目：标题/钩子、字幕、选项、承接（划卡/聊天）、口播、片尾、BGM/音效。
   - B 标出第一个选项出现时间（要求见 `rules/B-剧情选择.md`）。
   - 每条屏幕文字注明出处：全量文案哪一句，或「包装补充」。
   - **补充文案清单**给用户确认后才做（口播从哪取、清单怎么写见 `rules/通用.md`）。
   - 口播音色让用户选（原片有口播就用同一个音色）。
   - JP 片尾选哪种（见 `rules/JP.md`）。
   - 外部资源（API 等）受阻时，先用视频帧占位把包装做完，不卡整体进度；需要选帧时把原片整帧候选拼成一张，让用户选第几秒。
3. **图层**：工程里的 `gen.py` 出 1080×1920 透明 PNG（规格见 `rules/工程交付.md`）。
4. **承接 / 片尾**：先看 `reference/投放参考/README.md` 和 `modules/app-ui/reference/产品录屏_划卡到详情.mp4`；划卡/聊天用 `modules/app-ui`，JP 尾板用 `modules/jp-endcard`，自做片尾按 `rules/通用.md`；承接转场默认做法见 `library/打法.md`。
5. **声音**：口播用 voice skill，BGM 用 music skill，音效用 sound-effects skill（都是 ElevenLabs）；音效来源先后、闪避、音量见 `rules/通用.md`。
6. **timeline → 预览**：写 `timeline.json`（格式见 `scripts/render.py` 文件头）→ `render.py --still` 看版面 → `--draft` 出校对预览 → 打开给用户 → 改，循环。
7. **成片交付**：验收后不带参数出 1080×1920 成片，自检后放 `成品/`（命名、自检、交付说明见 `rules/工程交付.md`）。
8. **复盘**：写案例、本片卡进卡面库、新规则写回对应文件（见下方「复盘写回哪里」）。

用户当次要求优先于规则。

## 地区
触发词含 KR / JP / EN / TC。目前只有 `rules/JP.md`；其他地区先按 `rules/通用.md` 做。

## 文件
| 文件 | 内容 / 何时读 |
|---|---|
| `rules/通用.md` | 所有片子都守的规则，每次读 |
| `rules/B-剧情选择.md` / `rules/C-网感剪辑.md` | 版式规则（只写范围值），按版式读 |
| `rules/JP.md` | JP 字体、写法、尾板模块、商店页参考 |
| `rules/工程交付.md` | 目录、命名、拆片、图层、timeline、出片、自检、交付、多版本 |
| `library/打法.md` | 可选套路（承接转场、分屏开场、心跳、HUD 等），按需选 |
| `library/cards.md` | 已审核卡面库（往期素材的卡片：名字/简介/标签/卡面），划卡陪衬卡从这里取 |
| `library/copy.md` | 往期包装文案 |
| `cases/` | 本片参数和修改记录（见下） |
| `reference/环境.md` | 变量定义、本机示例、Windows 注意事项、排错表 |
| `reference/投放参考/` | 产品 UI（Figma）、商店页截图；做承接/片尾前看 README |
| `modules/app-ui/README.md` | 划卡 `swipe` / 聊天 `chat` 承接的用法；`reference/产品录屏_划卡到详情.mp4` 是 JP 产品实录 |
| `modules/jp-endcard/README.md` | JP 尾板（17.3 s）的用法 |
| `scripts/render.py` | timeline → mp4 / 静帧；文件头是 timeline.json 格式说明 |
| `scripts/asr.py`、`check_env.py`、`figma_ref.py`、`store_ref.py` | 逐词时间、环境自检、产品 UI 截图、商店页截图 |
| `scripts/open_dir.ps1` | 打开目录（只能在 Windows PowerShell 用） |
| `scripts/examples/` | 多版本 timeline + 批量出片示例（`to_timeline.mjs`、`batch.sh`） |
| `CHANGELOG.md` | 版本历史和规则的修改经过 |

## cases/
- 新案例目录名 `<日期>-<地区>-<版式>-<标题>`；已有目录不改名，版式看 `cases/README.md` 索引表。README 顶部写版式（B / C / 旧版）、状态、哪些脚本能直接跑。
- 只放本片参数和修改记录，每条修改标「已进规则（文件名）」或「只属本片」。
- 数值、文案、路径不照搬（每片素材、脸的位置都不一样）。
- 旧模板案例标「旧版·不作参考」。

## 复盘写回哪里
| 内容 | 写到 |
|---|---|
| 所有片子通用 | `rules/通用.md` |
| 只关版式 | `rules/B-剧情选择.md` 或 `rules/C-网感剪辑.md` |
| 只关地区 | `rules/JP.md`（新地区新建 `rules/<地区>.md`） |
| 工程、命名、出片、交付 | `rules/工程交付.md` |
| 可选套路 | `library/打法.md` |
| 本片卡片 / 包装文案 | `library/cards.md` / `library/copy.md` |
| 只属本片 | `cases/<本片>/README.md` |
| 剧本本身的问题（分幕、台词、选项、数值） | 告诉用户，由 shortdrama-copy 处理，本 Skill 不改它 |

规则格式：一行「做法（原因）〔日期〕」；有新版本就直接替换旧那行，不留删除线和「替代某条」；修改经过只记 `CHANGELOG.md`。原因不清楚写「（原因待补）」，不编。
