# shortdrama-copy

**短剧编剧 · 多语言台词本地化工具 v2.8.0**

把中文剧情想法、角色图或零散台词，写成适合韩国/日本/欧美市场的买量互动短剧：先出 5 个剧情大纲，选定后再写对照表格，包含标题、分幕、表演指示、台词、选项、数值变化和结尾卡。

---

## 使用流程与已读核验（给使用者看）

模型调用本 skill 时必须走 SKILL.md 开头的「执行协议」：

1. 按必读路由表列出要读的文件
2. 每个文件从头读到尾
3. 第一条回复先输出【已读确认】表，写出每个必读文件**最后一行**的读完校验口令
4. 写明结构类型、幕数、数值曲线
5. 先出 5 个大纲，选定后写全文
6. 回复末尾附【自检结果】

**怎么核验模型有没有读完：** 用下表逐个对照它交出的【已读确认】。口令只在每个文件的最后一行，只读开头或截读的模型拿不到。缺一个或对不上，直接让它重读再写。

本次任务需要哪些文件，看 SKILL.md 的「必读路由表」：每次都读的有 7 个，病娇、推拉、等待回复、写全文、口播各自再加对应文件。

<!-- 维护者：修改下列文件时，口令必须保持在文件最后一行；新增必读文件时同步补口令和本表。模型不需要读本 README。 -->

| 文件 | 末尾口令 |
|---|---|
| `core/story-structure.md` | 茶烟走马49 |
| `core/option-design.md` | 潮汐剪烛27 |
| `core/value-progression.md` | 芦笙剪烛13 |
| `core/title-endcard.md` | 芦笙敲钟52 |
| `core/outline-template.md` | 麦浪折柳81 |
| `core/checklist.md` | 海盐补网39 |
| `core/push-pull-structure.md` | 石榴种梅23 |
| `core/waiting-preset.md` | 纸鹤敲钟85 |
| `references/japanese/gold-dialogues.md` | 芦笙折柳30 |
| `references/korean/gold-dialogues.md` | 柿霜折柳75 |
| `references/english/gold-dialogues.md` | 麦浪磨墨68 |
| `references/genres/yandere.md` | 蓑衣拾月19 |
| `references/投放高效文案.md` | 青瓷熬糖38 |
| `languages/japanese/localization-rules.md` | 菱镜吹笙64 |
| `languages/japanese/glossary.md` | 芦笙渡河66 |
| `languages/japanese/grammar.md` | 枫笛渡河67 |
| `languages/japanese/output-template.md` | 雪橇踏歌38 |
| `languages/korean/localization-rules.md` | 松烟磨墨89 |
| `languages/korean/glossary.md` | 茶烟系铃68 |
| `languages/korean/grammar.md` | 樱桥放灯86 |
| `languages/korean/output-template.md` | 柿霜补网73 |
| `languages/english/localization-rules.md` | 灯塔落棋86 |
| `languages/english/glossary.md` | 茶烟系铃14 |
| `languages/english/tone-guide.md` | 霜桥踏歌15 |
| `languages/english/output-template.md` | 灯塔酿酒58 |

---

## 快速开始

### 基本用法

**韩语短剧：**
```
韩语短剧，健身房辣妹反杀主视角
```

**日语短剧：**
```
/jp 写一个职场下属暧昧告白的剧情
```

**英语短剧：**
```
English short drama, gym girl flips the script
```

---

## 支持的语言

| 语言 | 触发方式 | 输出格式 |
|---|---|---|
| 韩语 | `/kr`, `韩语短剧`, `韩中对照` | 韩中对照表格 |
| 日语 | `/jp`, `日语短剧`, `日中对照` | 日中对照表格 |
| 英语 | `/en`, `英语短剧`, `英中对照` | 英中对照表格 |

---

## 文件结构

```
shortdrama-copy/
├── SKILL.md                    # 主入口：执行协议、必读路由表、写法原则、语言检测
├── core/                       # 共享核心规则（全语言通用）
│   ├── story-structure.md      # 结构类型判断、幕数与长度
│   ├── option-design.md        # 选项设计原则
│   ├── value-progression.md    # 数值变化规则（单次 30–50、反弹）
│   ├── title-endcard.md        # 网感标题、结尾卡、卡片标题
│   ├── outline-template.md     # 5 个大纲的格式与合格示例
│   ├── checklist.md            # 交付前自检清单
│   ├── push-pull-structure.md  # 推拉/勾引结构
│   └── waiting-preset.md       # 等待回复结构预设
├── languages/                  # 语言特定规则
│   ├── korean/
│   │   ├── localization-rules.md   # 韩语本地化原则
│   │   ├── glossary.md            # 韩中词汇对照
│   │   ├── grammar.md             # 敬语/半语规则
│   │   └── output-template.md     # 韩中对照表格模板
│   ├── japanese/
│   │   ├── localization-rules.md   # 日语本地化原则
│   │   ├── glossary.md            # 日中词汇对照
│   │   ├── grammar.md             # 敬语/常体/方言规则
│   │   └── output-template.md     # 日中对照表格模板
│   └── english/
│       ├── localization-rules.md   # 英语本地化原则
│       ├── glossary.md            # 英中词汇对照
│       ├── tone-guide.md          # 语气/俚语规则
│       └── output-template.md     # 英中对照表格模板
└── references/                 # 参考案例与题材参考
    ├── genres/
    │   └── yandere.md                 # 病娇题材参考
    ├── 投放高效文案.md                 # 看板达标文案库（口播/片尾/标题）
    ├── korean/
    │   ├── gold-dialogues.md          # 韩语案例（v2.0 旧格式，只学语气）
    │   └── gold-dialogues-v1.2.md     # 韩语驯化/失败结尾案例
    ├── japanese/
    │   ├── gold-dialogues.md          # 日语成品案例（结构对所有语言通用）
    │   └── gold-dialogues-legacy.md   # 日语旧格式案例（只学语气，不必读）
    └── english/
        └── gold-dialogues.md          # 英语案例（v2.0 旧格式，只学语气）
```

---

## 核心功能

### 1. 剧情结构（全语言通用）

- **驯化结构**：封闭场景 + 主视角掌控权 + 三幕递进（抵抗→动摇→屈服）
- **失败结尾**：冲突→暧昧→失败（错误选项导致翻车）
- **反转结构**：被动→积累证据→反制
- **等待回复**：关键互动中止，角色等待回复（4-5幕递减）
- **推拉结构**：角色主动勾引，推 → 给台阶邀请 → 征服，停在擦边前
- **病娇 / 危险角色主导**：两幕，甜的表面 → 外部威胁 → 嘴硬说漏被打断

### 2. 选项设计（全语言通用）

- 默认不写【UI提问】，每幕最后一句把话抛给主视角
- 选项写成主视角的回答原话（行动类写动词原形），标出选中项
- 敏感词用 ◯◯ 和谐
- 三幕 3-3-2，两幕 3-2，最后一题可不点选

### 3. 数值变化（全语言通用）

- 默认只设一个数值，名称全片不改
- 单次变化 30–50，每次标出触发点，外部威胁时反弹一次
- 上升型数值结尾停在 99

### 4. 语言特定规则

**韩语：**
- 敬语/半语系统（`-요/-습니다` vs `-어/-야`）
- 职场称谓带敬称（`부장님`, `과장님`）
- 网络俚语（`몰카`, `오버`）

**日语：**
- 敬语系统（`です・ます体` vs `だ・である体`）
- 女性语尾（`〜わよ`, `〜だよ`, `〜ですわ`）
- 方言变体（关西腔、博多腔）

**英语：**
- 语气层级（Formal / Casual / Intimate / Aggressive）
- 缩写俚语（`gonna`, `wanna`, `kinda`）
- 短句打断节奏

---

## 输出格式

### 标准对照表格

| 中文 | 目标语言 |
|---|---|
| **标题** | **标题（目标语言）** |
| 网感短句标题 | 本地化标题 |
| **第一幕：幕名（数值名：数字）** | **数值名：数字** |
| **【表演指示】**<br>（角色+表情，角色+语气，角色的手/部位+动作） | <br> |
| 中文台词（末句抛给主视角） | 目标语言台词 |
| ① 选项A（选中）<br>② 选项B<br>③ 选项C | ① 本地化A<br>② 本地化B<br>③ 本地化C |
| ... | ... |
| **结尾卡文案** | **结尾卡文案（目标语言）** |
| 「表面→真相」短句<br>点击下载浏览后续 | 本地化短句<br>本地化下载引导 |
| **卡片标题** | **卡片标题（目标语言）** |
| 人设关键词 | 本地化人设关键词 |

---

## 使用示例

### 示例1：韩语短剧

**输入：**
```
韩语短剧，健身房辣妹反杀主视角
```

**输出：**
- 加载 `languages/korean/` 规则
- 加载 `core/story-structure.md`（失败结尾结构）
- 生成韩中对照表格

**特点：**
- 使用半语（情侣/朋友关系）
- 短促台词
- 选项用韩语动词原形

### 示例2：日语短剧

**输入：**
```
/jp 职场下属害羞告白
```

**输出：**
- 加载 `languages/japanese/` 规则
- 加载 `core/story-structure.md`
- 生成日中对照表格

**特点：**
- 使用敬体（职场关系）
- 女性语尾（`あたし`, `〜です...`）
- 犹豫结巴语气

### 示例3：英语短剧

**输入：**
```
English short drama, jealous girlfriend
```

**输出：**
- 加载 `languages/english/` 规则
- 加载 `core/story-structure.md`
- 生成英中对照表格

**特点：**
- Casual 语气（情侣关系）
- 短句打断（`What?`, `Why?`）
- 缩写俚语（`gonna`, `wanna`）

---

## 核心原则

### 1. 本地化优于翻译

```
目标语言母语者自然会说的话 > 符合角色身份 > 保留中文原意 > 字面对应
```

### 2. 台词必须短

- 韩语/日语：每句≤20字中文，每幕≤3句
- 英语：每句≤15词，每幕≤3句

### 3. 文化差异主动替换

| 场景 | 韩语 | 日语 | 英语 |
|---|---|---|---|
| 心机女 | `여우 같은 애` | `小悪魔` | `homewrecker` |
| 职场上司 | `부장님` | `部長` | `Director` |
| 偷拍 | `몰카` | `盗撮` | `creepshot` |

### 4. 产品名称与标题

- 产品名统一写 **MiraiMind**，不缩写成 MM
- 标题默认写网感信息流短句，不强制套「在MiraiMind中」

---

## FAQ

### Q1：如何显式指定语言？

在请求中添加 `/kr`, `/jp`, `/en` 或明确说"韩语短剧"、"日语短剧"、"英语短剧"。

### Q2：不指定语言会发生什么？

自动检测。中文输入默认韩语，英文输入默认英语，日文输入默认日语。

### Q3：可以混用多种语言吗？

一次只能生成一种目标语言的对照表格。如需多语言版本，请分别调用。

### Q4：旧的韩语案例还能用吗？

完全兼容。所有韩语相关功能保持不变，案例已迁移到 `references/korean/`。

### Q5：等待回复结构什么时候用？

当用户要求"忘记回复"、"已读不回"、"关键剧情中断"、"角色等待几天"时启用。

---

## 版本历史

### v2.8.0（当前版本）

- 新增执行协议：必读路由表 → 完整读取 → 【已读确认】口令核验 → 定结构 → 大纲先行 → 【自检结果】
- 新增 `core/outline-template.md`、`core/checklist.md`、`references/genres/yandere.md`（病娇题材参考）
- 清理与新规则冲突的旧写法（UI提问、在MiraiMind中标题、动词+人设卡片标题、数值一次跳 100）
- 日语旧格式案例移到 `gold-dialogues-legacy.md`

v2.2.0–v2.7.0 的改动见 SKILL.md「版本历史」。

### v2.1.0

- 新增推拉/勾引结构规则（core/push-pull-structure.md）
- 新增标题/结尾卡规则（core/title-endcard.md），取消「在MiraiMind中」强制标题
- 日语：网感标题、未亡人/人妻语气规则，新增「未亡人雪女」标准案例

### v2.0.0

- 完全重构：支持韩语/日语/英语三种目标语言
- 模块化设计：共享核心规则 + 语言特定规则
- 自动语言检测与路由
- 统一输出模板结构，语言特定细节独立管理
- 保留所有 v1.4.1 核心功能（驯化结构、失败结尾、等待预设）

### v1.4.1（韩语专用版本）

- 新增等待回复结构预设
- 台词长度硬性限制
- 产品名称规范（MiraiMind）
- 统一韩中对照表格格式

---

## 参考文档

### 核心规则（全语言通用）

- **剧情结构**：`core/story-structure.md`
- **选项设计**：`core/option-design.md`
- **数值变化**：`core/value-progression.md`
- **标题与结尾卡**：`core/title-endcard.md`
- **大纲模板**：`core/outline-template.md`
- **自检清单**：`core/checklist.md`
- **推拉结构**：`core/push-pull-structure.md`
- **等待预设**：`core/waiting-preset.md`

### 题材参考

- **病娇**：`references/genres/yandere.md`

### 韩语规则

- **本地化**：`languages/korean/localization-rules.md`
- **词汇表**：`languages/korean/glossary.md`
- **语法**：`languages/korean/grammar.md`
- **模板**：`languages/korean/output-template.md`

### 日语规则

- **本地化**：`languages/japanese/localization-rules.md`
- **词汇表**：`languages/japanese/glossary.md`
- **语法**：`languages/japanese/grammar.md`
- **模板**：`languages/japanese/output-template.md`

### 英语规则

- **本地化**：`languages/english/localization-rules.md`
- **词汇表**：`languages/english/glossary.md`
- **语气**：`languages/english/tone-guide.md`
- **模板**：`languages/english/output-template.md`

### 参考案例

- **日语成品案例（结构通用）**：`references/japanese/gold-dialogues.md`
- **日语旧格式案例**：`references/japanese/gold-dialogues-legacy.md`
- **韩语**：`references/korean/gold-dialogues.md`
- **英语**：`references/english/gold-dialogues.md`
- **投放高效文案**：`references/投放高效文案.md`

---

## License

MIT
