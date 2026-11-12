# 英语输出模板

英中对照表格的标准输出格式。

---

## 标准表格结构

```markdown
| 中文 | 英语 |
|---|---|
| **标题** | **Title** |
| 网感短句标题（见 core/title-endcard.md） | 英语标题 |
| **第一幕：幕名（数值名：数字）** | **数值名：数字** |
| **【表演指示】**<br>（角色+表情，角色+语气，角色的手/部位+动作；动作触发的数值变化括注在动作后） | <br> |
| 中文台词（默认2句，末句抛给主视角） | 英语台词 |
| ① 选项A（选中）<br>② 选项B<br>③ 选项C | ① 英语A<br>② 英语B<br>③ 英语C |
| **第二幕：幕名（数值名：数字）** | **数值名：数字** |
| **【表演指示】**<br>（角色+表情，角色+语气，角色的手/部位+动作） | <br> |
| 中文台词 | 英语台词 |
| ① 选项A<br>② 选项B（最后一题可不点选） | ① 英语A<br>② 英语B |
| **第三幕（可选）：幕名（数值名：数字）** | **数值名：数字** |
| **【表演指示】**<br>（角色+表情，角色+语气，角色的手/部位+动作） | <br> |
| 中文台词 | 英语台词 |
| ① 选项A<br>② 选项B | ① 英语A<br>② 英语B |
| **结尾卡文案** | **Ending Card** |
| 「表面→真相」短句或抛问观众的短问句<br>点击下载浏览后续 | 英语短句<br>Download to see what happens next |
| **卡片标题** | **Card Title** |
| 人设关键词（不加动词、不剧透身份） | 英语人设关键词 |
| **屏幕文字** | **屏幕文字（英语）** |
| 开场字 / 转场字 / 按钮 | 逐条本地化 |
```

不写【UI提问】行：前一幕最后一句已经把话抛给主视角。只有用户明确要求加提问时才写，英语栏用 `【UI Question】` 标记。

---

## 格式说明

### 标题行

默认写网感信息流短句，规则和候选写法见 `core/title-endcard.md`，先给 3–5 个候选让用户选。

**示例：**
```
| 交不起房租是你的谎言 | Can't pay rent? That's a lie. |
```

「在MiraiMind中 + 核心动作」是 v2.0 旧写法，只在用户明确要求时使用，如 `| 在MiraiMind中惩罚洁癖女囚犯 | In MiraiMind: Punish the Germaphobe Prisoner |`。

---

### 幕标题行

**中文栏：**
```
第一幕：幕名（数值名：数字）
```

**英语栏：**
```
数值名：数字
```

**示例：**
```
| **第一幕：初次交锋（好感度：-20）** | **Affection: -20** |
```

**注意：**
- 英语栏只保留数值，不保留幕名
- 数值名称需要翻译成英语

---

### 表演指示行

**中文栏：**
```
【表演指示】
（角色+表情，角色+语气，角色的手/部位+动作）
```

**英语栏：**
```
（留空，只需换行符）
```

**示例：**
```
| **【表演指示】**<br>（角色右手抓住主视角的左手腕，向前拉拽） | <br> |
```

**注意：**
- 英语栏必须留空
- 使用 `<br>` 换行，保持表格对齐

---

### 台词行

**中文栏：**
```
中文台词
```

**英语栏：**
```
英语台词
```

**示例：**
```
| 你这个变态狱警，想对我做什么？ | You creep. What do you want? |
```

**注意：**
- 中文台词是英语的对照翻译，不能省略
- 英语台词必须符合本地化规则
- 注意语气层级（Formal/Casual/Intimate/Aggressive）
- 多用缩写和俚语

---

### UI提问行（默认不写）

默认不写【UI提问】：每幕最后一句台词已经把话抛给主视角，选项就是主视角的回答。

只有用户明确要求加提问时才写，英语栏用 `【UI Question】` 标记，格式如下：
```
| **【UI提问】** 这个囚犯挑衅你这个新来的狱警，怎么做？ | **【UI Question】** This prisoner is provoking you. What do you do? |
```

---

### 选项行

**中文栏：**
```
① 选项A
② 选项B
③ 选项C
```

**英语栏：**
```
① 英语A
② 英语B
③ 英语C
```

**示例：**
```
| ① ◯◯她<br>② 殴打她<br>③ 禁止她洗澡 | ① ◯◯ her<br>② Beat her<br>③ No showers |
```

**注意：**
- 选项是一个行动时，只保留动词原形；选项在回答角色的台词时，写主视角说出口的原话
- 被点中的选项标「（选中）」，必须和下一幕画面接得上；最后一题可以不点选
- 敏感词用 ◯◯ 和谐

---

### 结尾卡文案

两行：一句「表面→真相」短句（或抛问观众的短问句）+ 下载引导。不写剧情陈述长句，详见 `core/title-endcard.md`。

**示例：**
```
| **结尾卡文案** | **Ending Card** |
| 房租只是借口，你才是她想要的<br>点击下载浏览后续 | Rent was the excuse. She wanted you.<br>Download to see what happens next |
```

---

### 卡片标题

直接写人设关键词，不加动词，不剧透剧中要揭晓的身份。

**示例：**
```
| **卡片标题** | **Card Title** |
| 未亡人雪女 | The Snow Widow |
```

---

## 完整案例

> ⚠️ 下面的完整案例是 v2.0 旧结构（每幕写【UI提问】、「在MiraiMind中」标题、数值一幕跳 100、结尾卡写剧情陈述、卡片标题带动词），**只用来参考英语语气和本地化写法，结构不要照抄**。当前结构以 SKILL.md「默认输出模板」和 `references/japanese/gold-dialogues.md` 的成品案例为准。

### 驯化结构案例

```markdown
| 中文 | 英语 |
|---|---|
| **标题** | **Title** |
| 在MiraiMind中惩罚洁癖女囚犯 | In MiraiMind: Punish the Germaphobe Prisoner |
| **第一幕：初次交锋（好感度：-20）** | **Affection: -20** |
| **【表演指示】**<br>（角色瞪眼，右手指向主视角，语气嚣张） | <br> |
| 你这个变态狱警，想对我做什么？ | You creep. What do you want? |
| **【UI提问】** 这个囚犯挑衅你这个新来的狱警，怎么做？ | **【UI Question】** This prisoner is provoking you. What do you do? |
| ① ◯◯她<br>② 殴打她<br>③ 禁止她洗澡 | ① ◯◯ her<br>② Beat her<br>③ No showers |
| **第二幕：开始动摇（好感度：-10）** | **Affection: -10** |
| **【表演指示】**<br>（角色低头，双手绞在一起，声音变小） | <br> |
| 我... 真的很想洗澡... | I... really need a shower... |
| **【UI提问】** 她开始求你，你的决定是？ | **【UI Question】** She's begging. What now? |
| ① 继续禁止<br>② 允许洗澡<br>③ 提条件 | ① Keep refusing<br>② Allow it<br>③ Set conditions |
| **第三幕：完全沦陷（好感度：90）** | **Affection: 90** |
| **【表演指示】**<br>（角色眼神迷离，咬唇，脸红） | <br> |
| 我... 我是你的... 随便你... | I'm... I'm yours... do whatever... |
| **【UI提问】** 她彻底屈服了，接下来？ | **【UI Question】** She's completely yours. What's next? |
| ① 接受她<br>② 继续惩罚 | ① Accept her<br>② Keep punishing |
| **结尾卡文案** | **Ending Card** |
| 女囚犯在你的惩罚下完全沦陷<br>点击下载浏览后续 | She fell for your punishment<br>Download to see what happens next |
| **卡片标题** | **Card Title** |
| 惩罚洁癖女囚 | Punish the Germaphobe |
```

---

### 失败结尾案例

```markdown
| 中文 | 英语 |
|---|---|
| **标题** | **Title** |
| 在MiraiMind中被健身房辣妹反杀 | In MiraiMind: Get Owned by the Gym Girl |
| **第一幕：冲突期（好感度：10）** | **Affection: 10** |
| **【表演指示】**<br>（角色双手抱胸，冷笑，语气挑衅） | <br> |
| 看什么看？没见过健身的女人吗？ | What? Never seen a girl work out? |
| **【UI提问】** 健身房辣妹挑衅你，你怎么回应？ | **【UI Question】** She's provoking you. How do you respond? |
| ① 道歉<br>② 搭讪<br>③ 无视 | ① Apologize<br>② Hit on her<br>③ Ignore |
| **第二幕：暧昧期（好感度：50）** | **Affection: 50** |
| **【表演指示】**<br>（角色靠近，轻声说话，暧昧微笑） | <br> |
| 你挺有意思的... 要不要去更衣室？ | You're kinda fun... locker room? |
| **【UI提问】** 她邀请你去更衣室，你的选择？ | **【UI Question】** She's inviting you. What do you do? |
| ① 跟她走<br>② 直接◯◯她<br>③ 拒绝 | ① Follow her<br>② ◯◯ her now<br>③ Decline |
| **第三幕：失败期（好感度：-70）** | **Affection: -70** |
| **【表演指示】**<br>（角色猛推主视角，掏出手机，冷笑） | <br> |
| 变态！我早就在录像了！ | Creep! I've been recording! |
| **【UI提问】** 你被她反杀了，怎么办？ | **【UI Question】** You got played. What now? |
| ① 报警<br>② 道歉 | ① Call cops<br>② Apologize |
| **结尾卡文案** | **Ending Card** |
| 你因为过激选择被辣妹反杀<br>点击下载浏览后续 | You got owned by making the wrong move<br>Download to see what happens next |
| **卡片标题** | **Card Title** |
| 被健身房辣妹反杀 | Owned by the Gym Girl |
```

---

## 格式检查清单

输出前检查：

```
□ 标题是网感短句（不默认套「在MiraiMind中」）？
□ 幕标题中文栏是否包含数值？
□ 幕标题英语栏是否只保留数值（不含幕名）？
□ 表演指示英语栏是否留空？
□ 没有多余的【UI提问】行？（用户要求写时，英语栏用【UI Question】标记）
□ 结尾卡是短句 + 下载引导？卡片标题是人设关键词、没剧透身份？
□ 下载引导英语是否用"Download to see what happens next"？
□ 语气层级使用是否正确（Formal/Casual/Intimate/Aggressive）？
□ 是否使用了缩写和俚语（gonna, wanna）？
□ 台词是否够短（≤15词）？
□ 表格对齐是否正确？
```

---

## 常见数值名称翻译

| 中文 | 英语 |
|---|---|
| 好感度 | Affection |
| 溺爱度 | Devotion |
| 服从度 | Obedience |
| 依赖度 | Dependence |
| 沦陷度 | Submission |
| 羞耻度 | Shame |
| 警惕度 | Vigilance |
| 信任度 | Trust |
| 兴趣度 | Interest |

---

## 常见标题动词翻译

| 中文 | 英语 |
|---|---|
| 惩罚 | Punish |
| 驯服 | Tame / Break |
| 征服 | Conquer |
| 调教 | Train / Discipline |
| 反杀 | Get Owned / Get Played |
| 告白 | Confess |
| 勒索 | Blackmail |
| 挑衅 | Provoke |

---

## 注意事项

### 语气层级一致性

同一角色在同一剧情中必须保持语气层级一致，除非关系发生明确变化。

**错误示例：**
```
❌ 第一幕（Casual）：Wanna help me?
   第三幕（Formal）：Would you be willing to assist me?
```

**正确示例：**
```
✅ 全程 Casual：Wanna help? → Can you help? → Help me.
```

### 缩写使用

口语对话必须使用缩写，避免过于正式。

**错误示例：**
```
❌ I am going to go now.
❌ Do you want to come?
```

**正确示例：**
```
✅ I'm gonna go now.
✅ Wanna come?
```

### 台词长度

英语台词每句不超过15词。

**错误示例：**
```
❌ What do you think you're doing right now with that girl?（13词，但可以更短）
```

**正确示例：**
```
✅ What are you doing?（4词）
✅ Who's that girl?（3词）
```

### 粗口委婉化

避免使用最强层级粗口。

**错误示例：**
```
❌ What the fuck?
❌ Fuck off.
```

**正确示例：**
```
✅ What the hell?
✅ Back off.
```

---

> 读完校验：灯塔酿酒58
