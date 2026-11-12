# CHANGELOG

## 3.1.0 (2026-11-12) 病娇女教师复盘：多版本时间映射、音效来源、响度、ASR、新脚本、执行协议
依据：用户 2026-11-12 批准的改动方案（M1–M17、R9–R12），证据来自 RHTV 工作台工程 261111-JP-病娇女教师（案例见 `cases/2026-11-12-JP-B-病娇女教师/`）。

**多版本（M1、R12）**
- `rules/工程交付.md`「多版本」删掉「gen.py 里写 `TM = {版本: {时间…}}`、每个版本手填时间表」的做法，改成：版本1 的 gen.py 只按规范时间写；每个版本一个 `工程素材/抽帧_版本N/版本配置.json`（role、A_END/B_IN/B_END、A1_MAP/A2_MAP、F1/F2/HERO 帧、subs 逐词时间，可选 BAR_POS/F1_UI_DY/F2_UI_DY）；build() 最后用时间映射把整条 timeline 换到本版本；逐词字幕用本版本时间、不映射；BGM 同源段保持相位（靠近结构切点的段锚在切点，其余沿用前一段相位，段内不拉伸）；定格帧 = 切点那一帧。原因：同一份提示词各版本台词快慢差到 1.3 s；映射第一版只平移 BGM 起点，同一首 BGM 在交叉淡化处错开叠在一起。
- 新增 `scripts/mmkit/__init__.py`、`scripts/mmkit/timewarp.py`（从本片 gen.py 的「版本时间映射」TW/vsrc/warp/_bgm_phase 抽出）：`TimeWarp(cfg, canon)` → `.TW(t)`、`.vsrc(t)`、`.warp(clips, audio, end, src_video)`（返回映射后总长）；canon 含 A_END、F1_END、B_IN、B_END、OFF、B1、F2_END；cfg 没有映射键时恒等。
- `scripts/examples/README.md` 里教 TM 表的说明改成指向版本配置.json + timewarp，多版本实例指向新案例。
- 新增 `rules/工程交付.md`「多版本」：并行处理多个版本时各版本临时文件放各自目录（如 `工程素材/抽帧_版本N/_tmp/`），不共用同名临时文件（v3 的代理覆盖过 v2 的临时脚本）。

**开头标题（M2、R9）**
- `rules/通用.md`：第一句台词前出现的字都算标题（标题、开场字、钩子说明字），台词/口播字幕和选项界面的「目标」不算；标题不是必须的；用户说去掉标题就全部去掉，开头只放 Logo；用户说去掉某类元素时按同类全去，汇报时写清删完还剩什么。原因：只删了标题、留着开场字，用户第二次要求才删干净。
- `library/copy.md` 用途说明：「标题/目标 = 开场字」改成「标题 = 第一句台词前的字；目标 = 选项界面，不算标题」。

**音效来源（M3、R10）**
- `rules/通用.md`：音效来源改成 ① 用户音效收集 `$USER_SFX` → ② ElevenLabs 生成；`$RES/sfx` 里的 g26/lgx/liquid/kpop/s_glitch 是本地合成的，不用；不自己合成（原规则把 `$RES/sfx` 当成「用户提供」，本片因此用了合成音效被骂「太雷霆」）。ElevenLabs 音效和 BGM 提示词统一带避开项（雷声、轰鸣、boom、sub bass、低频冲击、爆炸、tink、沙沙、八音盒）；生成后量低频，偏重就高通（UI 短音 300 Hz 双级高通；心跳 70 Hz 高通 + 120 Hz 轻提；BGM 80 Hz 高通 + 150 Hz lowshelf −8 dB 出 `_lite`）。
- `reference/环境.md`：`$USER_SFX` 本机值改成 `Z:/创新事业部/AIGC项目视频组/设计师物料总库/音频/音效收集`（F 盘在这台机器不存在）；取值顺序：环境变量 `MM_USER_SFX` → `<工作台根>/音效收集`（安装器建的，非空才用）→ Z: 设计师物料总库音效收集；`sfx/` 说明改成「现有的是本地合成音效，不用」；依赖表同步。
- `scripts/check_env.py` 改查 `$USER_SFX`，三处都没有音效文件就报错停下，不悄悄退回资源库合成音效；`scripts/qa.py tl` 查到 timeline 引用 `$RES/sfx` 里 g26-/lgx-/liquid-/kpop-/s_glitch 开头的音效就报错。

**BGM（M4）**
- `rules/通用.md`「BGM」：ElevenLabs BGM 生成后先量包络，开头静音、中途断档、某段提前结束的部分都不用，只排有声段，断了按小节续接（本片三种都中，复审才发现）。
- `rules/工程交付.md`「自检」加「BGM 全程无空档」；`modules/endcard3/README.md` 的「声音注意」改成引用 rules/通用.md。

**响度（M5）**
- `scripts/render.py`：limiter 缺省 0.89 → 0.84（0.89 编码后真峰值 −0.4 dBTP 不合格；本片 0.84 实测 −1.5 dBTP）；全片渲染后自动跑 ebur128 peak=true 打印 LUFS/dBTP，真峰值 > −1.0 以退出码 3 结束（`--draft` 只警告）。
- `rules/工程交付.md`「自检」改成测真峰值 ≤ −1 dBTP；`reference/环境.md` 排错表 0.89 → 0.84。

**ASR（M6）**
- `scripts/asr.py` 重写：`asr.py <src> [--lang ja] [--out] [--engine scribe|whisper]（默认 scribe，失败自动转 whisper 并说明）[--model medium] [--prompt] [--segments a-b,…] [--energy energy.json] [--threads 2]`；whisper 按 energy.json 的能量段按句切（前后留 0.2–0.3 s），prompt 自动去掉「……」「——」，ffmpeg 先解成 16k 数组再交给 transcribe；去掉 large-v3 默认和降级到 small（small 会幻听）；elevenlabs 调用包在 `heavy_lock("elevenlabs", min_free_gb=0)`，whisper 包在 `heavy_lock("asr")`。
- `rules/工程交付.md`「拆片」、`reference/环境.md`、`SKILL.md` 流程和文件表同步：默认 scribe，whisper medium 离线备选；elevenlabs CLI 调用一律串行（三条 scribe 并发后 OAuth 登录被清，之后 TTS/SFX 全停）。
- `scripts/check_env.py` 加 elevenlabs 登录态检查。

**jp-endcard 旧说法（M7）**
- `rules/JP.md`：17.3 s、自带 BGM/音效两行补上主语「jp-endcard」（用户点名才用）；放进 timeline 那行改成 endcard3 画成图层进 gen.py、jp-endcard 才出 mp4。
- `modules/app-ui/README.md`：片尾改成「JP 默认 modules/endcard3，用户点名才用 jp-endcard」；`rules/工程交付.md` 目录里 `包装素材_尾板/` 注明只有用 jp-endcard 时才有。

**新脚本（M8、M9）**
- `scripts/prep.py --p <05_包装目录> --ver N --src <母版.mp4> [--copy <全量文案.md>] [--around 12.3,27.9] [--force video|frames|energy|asr]`：一条命令拆片（复制 → 高度不足 1920 才放大 → 24 fps 抽帧 → 联系表（格上标秒数和帧号）→ 16k pcm → −35 dB energy.json → 调 asr.py 出 words.json），`--around` 出切点前后候选帧拼图；台词从全量文案读，不写死（由本片 prep_version.py 通用化）。
- `scripts/align_subs.py --p <05_包装目录> --ver N [--template <版本1 版本配置.json>] [--apply]`：全量文案逐字 ↔ ASR 逐字对齐算字幕时间，模板化，不写死句首卡和段结构；不加 `--apply` 写 `版本配置_草稿.json`，不覆盖手调（由本片 make_config.py 通用化）。
- `scripts/qa.py tl <timeline.json> [--base <已验收 timeline.json>]`：1/30 网格、闪断、出画、全屏特效层 z 序压到产品 UI/尾板、BGM 覆盖与同源相位、合成音效引用，`--base` 和已验收版本做结构对比；`qa.py video <成片.mp4>`：规格、真峰值、黑场；有错误退出码 1。
- `scripts/mmkit/heavy.py`：`heavy_lock(name="heavy", min_free_gb=3.0, poll=5)` 上下文管理器（按 name 的文件锁 + 可用内存不够就等并打印）；放大、ASR、全片渲染自动排队，其余步骤可放心并行（本机提交内存常年 28/34 GB，3×放大 + 3×whisper 并行全部内存不够）。
- `SKILL.md` 流程（拆片、timeline → 预览、成片交付）和文件表加上 prep.py、align_subs.py、qa.py、mmkit。

**BGM 闪避改增益曲线（M10）**
- `scripts/render.py` 的 audio 条目支持可选 `gain: [[t, v], …]`（成片绝对秒，分段线性）；没有 gain 字段时输出不变。文件头的 BGM 示例从「首尾相接各自淡变」（交界处出音量凹坑）改成一条连续 audio + gain。
- 新增 `scripts/mmkit/audio.py`：`duck_points(vo_intervals, base, duck, ramp=0.25, merge_gap=0.3)` → `[[t, v], …]`。
- `rules/通用.md`「混音与闪避」BGM 闪避的实现从「拆成多段 audio 用 fade 衔接」改成「一条连续 audio 加 gain 增益曲线」（拆段首尾各自淡变会出音量凹坑；本片产品 UI 音效压低是拆成 5 段补的）。

**规则补（M11）**
- `rules/B-剧情选择.md` 指针那行补「白圈 + 深色外环/投影，压在选项胶囊上也要看得清」（不新增行）。
- `rules/通用.md`：「动画节奏」加画面静止 ≥ 1.5 s 的段（定格、产品 UI 详情页）加慢推；「文案来源与补充」原声和文案对不上那行并进「原声或画面（道具、服装）和文案对不上时不改字，写进补充文案『需要拍板』交用户定，多版本每个版本都查」（选项「白衣を掴む」v1 没穿白大褂、v3 是护士服）；「沟通与改版」加样式在 Skill 里有两个以上对得上时先查 reference/投放参考 和 cases，拿不准出两张候选静帧问一句。
- `rules/工程交付.md`「timeline」加全屏特效层（故障色散、闪白、暗角）不跨出本段、不压到产品 UI/尾板上。
- `reference/投放参考/README.md` 加样式索引（三卡片尾板 → 三卡片尾板_参考.webp → modules/endcard3；主卡长廊尾板 → modules/jp-endcard），登记 三卡片尾板_参考.webp；`modules/jp-endcard/README.md` 标题和「3 张主卡」改叫「主卡长廊」，减少和「三卡片尾板」撞名。

**endcard3（M12、M14、R11）**
- `modules/endcard3/endcard3.py`：新增 `plan(E0, vo_t=None, vo_d=None)` → `{"dur", "taps"}`，首次点击 = max(E0 + 3.7, 口播结束 + 0.15)，总长 = max(4.9, 末次点击 + 0.4 − E0, 口播结束 + 1.0 − E0)（不给口播时也是 5.0 s）；`build(ctx)` 返回实际时长；金色末行也做出界检查；模块常量 `DUR = 4.9` 保留作下限（旧用法兼容）。找不到官方商店标文件时直接报错，不跳过。
- 新增 `scripts/mmkit/layers.py`（add_img/kf/snap/add_audio/us/pointer_path 这类公共函数），endcard3 可直接 import，不再依赖工程代码；`mmlib.py` 的 `BADGE_DIR = os.environ.get("MM_BADGE_DIR", 原 Z: 商店图标目录)`，`MM_BADGE_DIR` 登记进 `reference/环境.md`。

**渲染和模块小修（M15、M16）**
- `scripts/render.py --draft` 真正按半尺寸合成（原来全尺寸合成、只在编码时缩小）；出片包在 `heavy_lock("render")` 里排队（mmkit 导入失败就不锁）。
- `modules/app-ui`：出错时也关掉 headless Chrome（try/finally）。

**读完证明（R11）**
- `SKILL.md` 加「执行协议」：按阶段列必读文件（rules/通用.md、rules/工程交付.md、所用版式文件、地区文件；用到哪个模块读哪个模块 README），开工第一条回复先输出【已读确认】表（文件｜末尾口令），写法照 shortdrama-copy。原因：片尾口播取口播库短句的规则本来就写着，没照做（用户：「三卡片围板展示文案和口播缩短，文案来源好好看skill」）。
- rules/通用.md、rules/B-剧情选择.md、rules/C-网感剪辑.md、rules/JP.md、rules/工程交付.md、modules/endcard3/README.md、modules/app-ui/README.md、modules/jp-endcard/README.md 最后一行各加一句「读完校验口令」，口令各不相同。

**案例和版本（M13、M17）**
- 新增参考案例 `cases/2026-11-12-JP-B-病娇女教师/`：README（版式 B、状态、6 轮预览各改了什么并标去向、多版本做法、本片具体秒数）+ 原样存档 gen.py、audio_gen.py、audio_gen2.py、prep_version.py、make_config.py、endcard3.py（注明已通用化成哪个脚本）；`cases/README.md` 索引和 SKILL.md B 参考案例加上它。
- 官方素材内置：新增 `assets/官方素材/`（MiraiMind 图标、字标，日文 Google Play / App Store 商店标原图，英文商店标合图，用官方原图生成的同尺寸 `badges.png`）。endcard3 的 mmlib、app-ui、jp-endcard 默认都读它，不再从 Z: 资源库或设计师物料总库取；旧 `badges.png` 两个标不一样大、不是官方原图，已替换。jp-endcard 的 prebuilt 画面带旧标，默认配置改为逐帧重渲染。（用户：「官方图片这种通用素材给我内置到放到skill里，还找你妈找，同步更新每一个单独的skill」）
- `SKILL.md` version 3.0.2 → 3.1.0。

## 3.0.2 (2026-11-12) JP 默认片尾改为三卡片尾板（更正 3.0.1）
- 3.0.1 把「三个卡片的尾板」理解成了 `modules/jp-endcard` 的三张主卡，理解错了。用户给了参考图（存为 `reference/投放参考/三卡片尾板_参考.webp`）：顶部 Logo、三张角色卡扇形（中间本片角色金边高亮 + チャット数）、结尾卡文案、金橙渐变下载按钮。
- 新增 `modules/endcard3/`（实现 + README），`rules/JP.md` 改为 JP 片尾默认用它，jp-endcard 只在用户点名要时用；`SKILL.md` 流程和文件表同步。

## 3.0.1 (2026-11-12) JP 片尾默认用尾板模块
- `rules/JP.md`：JP 片尾从「定方案时问用户用尾板模块还是自做片尾」改为默认用 `modules/jp-endcard`（三张主卡），本片角色放进对应主卡位。依据：用户在 261111-JP-病娇女教师 包装审片时要求「最后的尾板我要出三个卡片的形式，改，并且设为默认样式」。
- `SKILL.md` 流程第 2 步同步改写。

## 3.0.0 (2026-11-10) 规则重构
依据：`F:/钟海明/2026年11月10日自动化工作台开发/mm-packager规则迁移清单.md`「〇、最终裁决」。

**结构**
- 目录改成 `rules/`（通用、B-剧情选择、C-网感剪辑、JP、工程交付）+ `library/`（打法、cards、copy）+ `cases/` + `reference/`（环境.md、投放参考/）+ `modules/*/README.md`（只写用法）+ `scripts/`。
- `reference/standards.md` 拆进 rules/ 和 library/打法.md 后删除；`workflow.md` 拆进 SKILL.md 和 rules/工程交付.md 后删除；`reference/layers.md` 的 timeline 格式并进 `scripts/render.py` 文件头后删除。
- 新增 `reference/环境.md`：本机路径改成变量（`$SK`、`$RES`、`$P`、`$WORK_ROOT`、`$UPLOAD_IN`、`$USER_SFX`、`$CHROME` 等），本机值只写在这里。
- 五音梗的 `to_timeline.mjs`、`batch.sh` 移到 `scripts/examples/`，改成新目录和命名，作多版本示例。
- 规则格式统一为一行「做法（原因）〔日期〕」，只写当前有效版本；修改经过只记本文件。

**分工（裁决〇，推翻原裁决 2(8)(9)）**
- shortdrama-copy 不改：剧本只出分幕、台词、表演指示、选项、数值（名称/触发/幅度）。
- 包装补全口播、标题、目标、重点词、产品 UI 卡片字段、尾板文案；屏幕文字 = 全量文案 + 包装补充文案，补充文案出片前列给用户（日文附中文）确认。
- 口播直接读 `shortdrama-copy/references/投放高效文案.md`，不搬不复制；去标点在包装渲染时做，不回写全量文案。

**裁决 1–16**
1. 气泡/输入框字号 64–76，B、C 通用；app-ui 产品气泡 56 号例外。
2. 片尾 ≤ 10 s 只管自做片尾，JP 尾板模块除外。
3. 尺度标准移出包装：角色图只取原片整帧、卡面库、工作台 02 已审核人设图；包装不生图、不改图、不做尺度审核。删 jp-endcard README 尺度句；cards.md 卡面来源去掉「生图」。
4. 不加弹幕：弹幕规则、打法、文案、案例做法全部删除（v1.1.0「可选打法新增人物身后弹幕」等历史条目作废）。
5. 音效：用户提供的优先（`$RES/sfx`、`$USER_SFX` 都算），没有再用 ElevenLabs sound-effects 生成；app-ui 音效改为从配置读取（保留现有默认值）；避开项清单（tink、沙沙、雷声感、八音盒）写进提示词；不加思考音效；丝滑音效只限微恐。
6. BGM 必须 ElevenLabs music 生成；JP 尾板自带 BGM/音效作例外保留；无 BGM 版只在用户要求时出。
7. BGM 闪避：B、C、JP 尾板都用整句平滑压低，不用侧链，不写死压到 0.1。endcard.py 去掉 sidechaincompress，改为按分句时间生成音量包络（提前压、句后停留、慢回升、短停顿不回升）；默认出片改为定稿画面 + 新混音，旧侧链定稿用 `--legacy-mix` 取。
8. 版式只有 B、C；参考案例 B = 追放された女騎士、上の階のスポーツ女子、命令模式保镖，C = 签售会POV；其余 7 个案例标「旧版·不作参考」。
9. 每张划卡必须有名字和简介，缺了由包装补写；旧版片的角色卡不再当陪衬卡。
10. 选项点完约 0.5 s 回剧情；删「回复气泡至少停约 1.3 s」。
11. 旧版来的打法（巴掌特效、倒带进片尾、表情进度条、失败重试、锁钩子）保留做法、删案例链接，进 library/打法.md；删「3·2·1 每个停 1 s」；保留「内心独白不做气泡」。
12. 命名：成品 `<工程名>_<角色名>`；预览 `<工程名>_预览vN_<角色名>`；投放副本沿用 xmp-upload；多版本同一工程内 `包装素材_版本N`（原 `包装素材vN` 停用）。
13. 「抖动大字按最大位移算边界」「口播时压 BGM、末句后留 ≥ 1 s」升为通用。
14. layers.md、workflow.md、standards.md 迁完删除；copy.md 留包装；TC 触发词保留；JP 片尾不固定加免责声明；cards.md 里推断的性向改「待确认」；jp-endcard 内置 27 张卡标「来源未知」。
15. B「最后一题可不点」不写死；「剧情 BGM 鼓点按幕递进」降为打法，不固定三幕；「脚本直接出片」是通用做法；聊天数/热度数字 B、C 通用。
16. 环境：rembg 的 CUDA 会崩；BiRefNet_lite 在 torch CUDA fp16 跑通过；本机路径改变量；三个 .py 优先读 `MM_RES`，没设时回落到 Z: 默认路径。

**从规则文件挪来的修改经过**
- 重点元素尺寸从「至少 ×2」改为具体范围（2026-11-02）；气泡字号 50 作废，改 64–76（2026-11-02）。
- 片尾约 2.3 s 改为 ≤ 10 s（2026-10-22），再限定为只管自做片尾（2026-11-10）。
- 删掉「片尾必须亮」，背景亮度按题材定（2026-10-20）。
- 选项去掉「小尺寸」（2026-10-30）；全屏失焦被「只压暗下半屏」替代（2026-10-27）。
- 好感度变化时机三次改动：每句台词都变（2026-10-22）→ 基本只在选择时变（2026-10-30）→ 选项和剧情关键事件处都可变、对齐画面动作（2026-11-05）。
- BGM 固定 0.2、原声压低到 0.35 删掉（2026-10-27），改整句平滑压低（2026-11-05）。
- 否决 GM 音色 / MIDI+SoundFont 合成和 MusicGen 本地生成（2026-10-22 起），现在 BGM 只用 ElevenLabs。
- 「苹果风格清脆音效」被「丝滑音效」替代（2026-10-20），现在丝滑只限微恐。
- 下面 2026-10-27 那条 `endcard.py attach` 已作废（2.0.0 去掉 attach，只 render）。

**模块验收记录（从 README 挪来）**
- app-ui `swipe` 划卡到详情：2026-11-02 用户验收，照 `modules/app-ui/reference/产品录屏_划卡到详情.mp4` 做；同日用户指出圆角锯齿，改用 `masked()` 不用 `clip()`。`chat` 模式未单独验收。
- jp-endcard：2026-10-27 用户验收定稿 v19A（17.3 s，女王02 口播 + 钢琴弦乐 + 音效）；制作过程和 v1–v19 历史版本在 `$WORK_ROOT/2026年10月26日MM-JP-尾板制作/`。
- jp-endcard 混音：sidechaincompress 改为整句平滑包络（参数在 `config.default.json` 的 `mix`）；`$RES/jp-endcard/prebuilt/default.mp4` 仍是 10-27 的侧链混音，未重做，默认出片只取它的画面。新混音需用户试听验收。

## 2.0.1 (2026-11-10) 补漏
- app-ui 示例配置改指向共享卡面库（原指向本机 floze 工程）。
- jp-endcard README 去掉 attach/--replace-from/A2 等编辑器说法，改为 render + timeline 用法。
- standards 里 V1/A1/模板气泡等编辑器术语改成通用说法。
- xmp-upload 里指向 mm-workbench-v5 的地方改为 mm-packager。

## 2.0.0 (2026-11-09) 改名 mm-packager，去掉编辑器
- 由 mm-workbench-v5 迁移而来（旧仓库 oNa2O2o/mm-workbench-v5 停止维护）。
- 去掉编辑器依赖（mmw / REST / open_editor / qa_v5 / build_v5 / 模板路线）：新增 `scripts/render.py`（timeline.json → mp4/静帧，clip 模型与编辑器一致，毒舌 _3 实测与编辑器成品同响度、PSNR 均值 36）。
- 本地依赖集成：字体、音效、模型、JP 尾板素材、投放参考、卡面库放共享目录 `Z:/创新事业部/AIGC项目视频组/mm-packager资源`（`MM_RES` 可覆盖）；新增 `scripts/asr.py`、`scripts/check_env.py`；app-ui / jp-endcard 去掉 attach，只 render。
- 新增 `library/cards.md`（往期 19 个素材 23 张卡：名字/简介/标签/卡面）、`library/copy.md`（往期包装文案）。
- 硬规则新增：承接转场、口播字幕底板、BGM 每次新生成且剧情/承接分开纯音乐、每张划卡有名字简介、多版本隔离且引用画面取原始素材。
- 新案例 `cases/2026-11-05-JP-五音梗-毒舌講座-迭代/`。


## v1.5.0 — 2026-11-05
- standards §0.3：角色出镜后进度条才出现、才变化。
- standards §7：口播音色定方案时给用户选。
- standards §8：截图用原片整帧，低分辨率不裁剪放大，挑表情平静的帧；生图 API 不可用时拼原片候选帧让用户选第几秒。
- standards §10：热度数字可以用「万」（撤销「不用万」）。
- 硬规则 2：「复制到输入」的目录和命名。
- 新增案例 `cases/2026-11-05-JP-上の階のスポーツ女子/`。

## v1.4.0 — 2026-11-05
- （补充，不升版本）新增 **C 直接渲染路线**（网感剪辑、不用编辑器）：SKILL 路线表、workflow §C、standards §10 与 §9 一行，新增案例 `cases/2026-11-04-JP-签售会POV-网感剪辑/`。
- 硬规则新增「沟通」13–14：日语全部附中文；用户给过的信息直接用不再问。
- standards：好感度在选项和剧情关键事件处变化（对齐画面）；尺寸表新增 B 路线选项胶囊（字 84、高 173、宽 ≤ 1000）；§1 新增只参考指定部分、引用画面取原始素材、外部资源受阻先占位；§6 产品 UI 卡片字段齐全不出界；§7 BGM 整句平滑压低、剧情与尾板两首 BGM。
- workflow：成品统一转 H.264 yuv420p；交付自检加卡片字段和数值对齐。
- modules/app-ui：名字自动缩字号、标签按词换行、简介收窄。
- 新增案例 `cases/2026-11-05-JP-追放された女騎士/`。

## v1.3.0 — 2026-11-04
- standards §0：重点元素尺寸与位置给出具体范围（输入框/气泡字号 64–76、输入框高 130–160、选项 UI y 960–1440、脸低时下移 ≤1630；进度条留头顶跟头，头顶上方 200–280 px；数字/+N 字号），替代“至少 ×2”；§3 气泡字号改为见 §0。
- 硬规则 2：「成品」只放最新一版，旧版移到归档。硬规则 5：用户口头给的中文字段先改成目标语言地道说法。
- 新增案例 `cases/2026-11-02-JP-命令模式保镖/`。

## （未提交，已过时）— 2026-10-27
- 新增可选模块 `modules/jp-endcard/`：MM-JP 通用尾板（定稿 v19A，17.3 s）。`endcard.py attach` 一条命令接到工程末尾（V1 画面 + A1 声音同 linkGroup，A2 BGM 截断淡出，幂等，`--replace-from` 替换旧片尾）；`stills`/`render` 支持换 3 张主卡和追加角色图（逐帧渲染约 30 分钟，按配置哈希缓存）。不改编辑器源码。
- SKILL「可选模块」表、workflow §4a 第 7 步 / §B 定方案：JP 素材片尾先问用户是否用尾板模块。

## v1.2.0 — 2026-10-27
- standards §7：人声清晰优先——BGM 闪避、原声混音乐时先人声分离；选项段 BGM 跟定格/倒计时/点击节奏。
- standards §4b：定格总长约 2.5–3.2 s、点完约 0.5 s 回剧情、犹豫 1.5–2 s；B 路线选项默认无提问 + 中下方小胶囊 + 倒计时条、不全屏失焦。
- workflow 排错：动漫抠图 BiRefNet_lite CUDA；动漫人脸手动锚点。
- 新增案例 `cases/2026-10-26-JP-猫娘报恩-琥珀橘/`。

## v1.1.0 — 2026-10-27
- 硬规则 3：只在出图/视频时展示，其他产物不开目录；新增 `scripts/open_dir.ps1`，目录已打开就不重复开。
- standards：截图/头像挑角色最好看的一帧；可选打法新增人物身后弹幕、最后一题心跳、片尾口播手机屏。
- custom-layers：逐帧图层可行、定格变换要同步到蒙版/跟脸；torch CUDA 崩溃改 CPU rembg。
- workflow 排错：whisper 段错误改 ElevenLabs scribe_v2；ElevenLabs 音乐分段 ≥3000ms。
- 新增案例 `cases/2026-10-26-JP-1年ぶりの彼-深夜琥珀/`。

## v1.0.0
- 初版（未打版本号前的状态）。
