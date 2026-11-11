# shortdrama-copy

**多语言短剧台词本地化工具 v2.1.0**

将中文剧情、角色图或零散台词，改写成适合韩国/日本/欧美市场的短剧文案，输出对照表格，包含标题、分幕、表演指示、台词、UI选项、数值变化和结尾卡。

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
├── SKILL.md                    # 主入口，语言检测与路由
├── core/                       # 共享核心规则（全语言通用）
│   ├── story-structure.md      # 三幕结构、驯化/失败/反转逻辑
│   ├── option-design.md        # 选项设计原则
│   ├── value-progression.md    # 数值变化规则
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
└── references/                 # 参考案例
    ├── korean/
    │   ├── gold-dialogues.md          # 韩语标准案例
    │   └── gold-dialogues-v1.2.md     # 韩语驯化/失败结尾案例
    ├── japanese/
    │   └── gold-dialogues.md          # 日语标准案例
    └── english/
        └── gold-dialogues.md          # 英语标准案例
```

---

## 核心功能

### 1. 剧情结构（全语言通用）

- **驯化结构**：封闭场景 + 主视角掌控权 + 三幕递进（抵抗→动摇→屈服）
- **失败结尾**：冲突→暧昧→失败（错误选项导致翻车）
- **反转结构**：被动→积累证据→反制
- **等待回复**：关键互动中止，角色等待回复（4-5幕递减）

### 2. 选项设计（全语言通用）

- 提问必须有情境
- 选项只保留动词原形
- 敏感词用 ◯◯ 和谐
- 第一幕3个、第二幕3个、第三幕2个

### 3. 数值变化（全语言通用）

- 数值名称开始确定后三幕不可更改
- 驯化结构：-20 → -10 → +90
- 失败结尾：+10 → +50 → -70
- 等待回复：98 → 85 → 65 → 40 → 20

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
| 在MiraiMind中 + 核心动作 | MiraiMind语言前缀 + 本地化标题 |
| **第一幕：幕名（数值名：数字）** | **数值名：数字** |
| **【表演指示】**<br>（角色+表情，角色+语气，角色的手/部位+动作） | <br> |
| 中文台词 | 目标语言台词 |
| **【UI提问】** 提问标题 | **【UI提问（目标语言）】** 本地化提问 |
| ① 选项A<br>② 选项B<br>③ 选项C | ① 本地化A<br>② 本地化B<br>③ 本地化C |
| ... | ... |
| **结尾卡文案** | **结尾卡文案（目标语言）** |
| 剧情陈述<br>点击下载浏览后续 | 本地化陈述<br>本地化下载引导 |
| **卡片标题** | **卡片标题（目标语言）** |
| 动词 + 核心人设 | 本地化标题 |

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

### 4. 产品名称统一

- 中文：**在MiraiMind中**
- 韩语：**MiraiMind에서**
- 日语：**MiraiMindで**
- 英语：**In MiraiMind**

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

### v2.1.0（当前版本）

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
- **等待预设**：`core/waiting-preset.md`

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

- **韩语**：`references/korean/gold-dialogues.md`
- **日语**：`references/japanese/gold-dialogues.md`
- **英语**：`references/english/gold-dialogues.md`

---

## License

MIT
