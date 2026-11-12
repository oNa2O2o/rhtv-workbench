# app-ui · 剧情后的产品 UI 展示

剧情结束后把观众带进产品界面。1080×1920、30 fps，渲染出带音效的 mp4（无 BGM、无口播）。
什么时候用、卡片文字从哪来、按钮要和产品一致，这些规则见 `rules/通用.md`；本文只写怎么用。

| 模式 | 内容 | 实物参考 |
|---|---|---|
| `swipe` 划卡到详情 | 首页角色卡横滑 3 张 → 停在本片角色 → 点开 → 卡片缩到左上角、详情页弹出（名字、标签、キャラ情報）→ 点「チャットに進む」 | `reference/产品录屏_划卡到详情.mp4`（JP 产品实录）。动效和 `ui` 默认文字都照它；改引擎或核对 UI 时先看这段 |
| `chat` 聊天 | 本片角色的聊天页，消息逐条弹出（文字 / 图片 / 语音条 / 输入中），可模拟用户在输入框打字发送 | 没单独验收过，用前先出静帧给用户看（见 `rules/工程交付.md`） |

本模块不含片尾。JP 片尾默认用 `modules/endcard3`（三卡片尾板），用户点名才用 `modules/jp-endcard`；其他地区自己做（做法见 `rules/通用.md`），接在这段后面。

## 用法
```bash
M="$SK/modules/app-ui/appui.py"
python "$M" stills --config "$P/包装素材_产品UI/swipe_版本1.json" --out "$P/包装素材_产品UI/静帧_版本1" --times 0.4,1.3,3.4,5.5   # 先看静帧
python "$M" render --config "$P/包装素材_产品UI/swipe_版本1.json" --out "$P/包装素材_产品UI/产品UI-划卡_版本1.mp4"
```
- 放进 timeline 见 `rules/工程交付.md`「timeline」。
- 配置里的图片、音效路径写绝对路径，或写 `$RES/…`（运行时换成 `MM_RES`；`$P` 等其他环境变量也会展开，前提是运行时设了）。文件命名见 `rules/工程交付.md`。
- `render` 结束时打印 `duration` 和 `events`（每个音效事件的时间），对 timeline 用。
- 例子 `examples/swipe_floze.json`、`examples/chat_floze.json` 只是格式示例，数值不当参数参考；其中 hero 和 chat 用的是旧版片 floze迭代2（1年ぶりの彼）的图和台词，不作参考。

## swipe 配置
```json
{"template":"swipe",
 "cards":[{"image":"$RES/library/cards/20261103-追放された女騎士.jpg","focusY":0.35,"name":"裏切られた女騎士","tags":["#女騎士"],"intro":"…"}, {…}, {…}],
 "hero":{"image":"$P/工程素材/抽帧_版本1/0300.jpg","focusY":0.35,"name":"…","tags":["…"],"intro":"…","gallery":["…/0444.jpg","…/0200.jpg"]}}
```
- `cards`：前面划走的卡，从 `library/cards.md` 取；`hero`：最后停住的卡，用本片角色。卡片字段的来源和缺字段怎么补见 `rules/通用.md`。
- 卡片 `tags` 原样显示（自己带 `#`）；hero 的 `tags` 不带 `#`，引擎会加。
- `gallery`：详情页「キャラクター」小图，最多 3 张，第 1 张固定是 `hero.image`。
- 名字太长自动缩字号：划卡卡片 100→56，详情页 hero 76→44。标签按词换行，简介按卡宽折行（卡片最多 3 行，详情页最多 4 行）。这只用于产品 UI 卡片，其他画面上的字不缩（见 `rules/通用.md`）。
- `focusY` / `focusX`：图片裁切中心（0–1）。

| 节奏参数（秒） | 默认 | 说明 |
|---|---|---|
| `startAt` | .5 | 第一次划卡前停多久 |
| `firstSwipe` | .8 | 第一张划走用时 |
| `accel` | .78 | 每张比上一张快多少（乘数） |
| `minSwipe` | .38 | 最快一张的用时 |
| `swipeGap` | .12 | 两次划卡间隔 |
| `heroHold` | .8 | 停在 hero 上多久再点 |
| `profileHold` | 2.2 | 详情页停多久再点「チャットに進む」 |
| `tapChat` | true | false = 不点「チャットに進む」 |
| `tail` | .7 | 结尾停留 |
| `scrollUp` | 0 | 详情页打开后整页上滑的像素（带手指上划），用来露出简介 |
| `scrollAt` | .5 | 详情页打开后多久开始上滑（滑 .7 s） |

默认 3 张卡总长约 7.2 s。

`ui`：覆盖产品按钮/标签文字。默认值是 JP 产品原文（照录屏）：`chat:"チャット"`、`chatGo:"チャットに進む"`、`tabs:["キャラ情報","シナリオ","アルバム","グループ"]`、`intro:"紹介"`、`chara:"キャラクター"`、`nav:["ホーム","検索","","チャット","マイ"]`。其他地区要换成该地区产品里的实际文字（见 `rules/通用.md`）。

## chat 配置
```json
{"template":"chat","bg":{"image":"…","focusY":0.4,"blur":0,"dim":0.15},"name":"…","status":"","avatar":{"image":"…","focusY":0.3},
 "placeholder":"","chips":[],"fontSize":56,
 "messages":[{"t":0.6,"from":"char","text":"…"},
             {"t":1.6,"from":"char","type":"image","image":"…/0444.jpg","w":520,"h":700},
             {"t":2.9,"from":"char","text":"…","typing":0.6,"voice":6},
             {"t":4.0,"from":"user","text":"…","typeDur":1.2},
             {"t":6.2,"from":"char","text":"","typing":1.4}],"tail":0.4,"duration":6.0}
```
- `bg.blur`：背景模糊（像素，0 = 不模糊）；`bg.dim`：背景压暗（0–1）。
- `t`：消息出现时间。`typing`：出现前先显示几秒「…」；`text` 为空只写 `typing` 就一直停在「输入中」。
- `voice`：语音条秒数，消息里加一条紫色语音胶囊，显示 `N''`，播放进度按这个秒数走。
- `from:"user"` 配 `typeDur`：先在输入框逐字打出来，再点发送。
- `fontSize` 默认 56，照产品界面（气泡 64–76 的通用字号不管这里，见 `rules/通用.md`）。
- `status`、`placeholder`、`chips` 没有来源就留空。

## 音效
默认音效（`appui.py` 里的 `SFX`）：

| 事件 | 默认文件（`$RES/jp-endcard/media/audio/`） | 音量 |
|---|---|---|
| `swipe` 划卡 | 无文件，粉噪滤波合成的轻划声（裁决 5 保留的现有默认值） | .22 |
| `click` 点击 | sfx_click_1.mp3 | .7 |
| `open` 打开详情 | sfx_toggle_2.mp3 | .35 |
| `hero` 停在 hero | sfx_toggle_2.mp3 | .4 |
| `flash` 闪光 | sfx_intro_2.mp3 | .45 |
| `message` 收到消息 | sfx_message_1.mp3 | .32 |
| `send` 发送 | sfx_click_1.mp3 | .35 |

上表是按裁决 5 保留的现有默认值（含合成的 swipe 声），只当占位。正式片按 `rules/通用.md` 的音效来源准备文件，用配置的 `sfx` 字段换掉默认值（swipe 也用 `sfx.swipe` 换）：
```json
"sfx": {"click": {"file": "$P/包装素材_版本1/audio/click.mp3", "volume": 0.6},
        "message": "$P/包装素材_版本1/audio/msg.mp3",
        "open": {"volume": 0.25},
        "swipe": null}
```
- 值可以是文件路径（音量沿用默认）、`{"file","volume"}`（只写 `volume` 就只改音量）、`null`（这个事件不出声）。
- 裸文件名（不带目录）在 `$RES/jp-endcard/media/audio/` 里找。文件不存在时在逐帧渲染前就报错。
- 也可以全部设 `null` 出无声版，音效另放进 timeline。

## 改引擎须知
- 图片圆角用引擎里的 `masked(pathFn, drawFn)`（先画到单独一层，再用带平滑的 fill 做 destination-in），不用 `clip()`（canvas 的 clip 边缘不平滑，2 倍超采样也消不掉锯齿）〔2026-11-02〕
- 「チャット」「チャットに進む」按钮是青 #74E8D0 → 蓝 #70B4FF → 淡紫 #BBA0FF 的渐变胶囊配深色字，改的时候不要偏离产品〔2026-11-02〕
- 内部按 `ss` 倍绘制（默认 2）再缩小。
- 字体复用 `$RES/jp-endcard/assets`；Logo、商店标用 skill 内置的 `assets/官方素材/`（`badges.png` 是两个官方标同尺寸的合图）；Chrome 路径读环境变量 `CHROME`，没设就用 `appui.py` 里的默认路径（见 `reference/环境.md`）。

读完校验口令：芦苇划桨54
