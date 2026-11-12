export const meta = {
  name: 'rhtv-charsheet-review',
  description: '人设图独立审核：每张四视图并行派两个审核员——尺度审核员按红线逐条挑错，造型审核员看还原度、改色、新增项、擦边曲线和好看',
  whenToUse: 'rhtv-character-sheet 出图、裁切、自查之后，标待审核之前。args = { images: [{ tag, ref, head, outfit, crops: [8 个裁切路径], persona? }], persona? }；同一角色多张参考图合成一个版本时 ref 用数组',
  phases: [{ title: '审图', detail: '每张图一个尺度审核员 + 一个造型审核员，并行' }],
}

// 用法见 references/审核员.md。
// args.images[i]:
//   tag     版本/轮次标签，如 'v4fix'，只用于显示和结果归档
//   ref     参考图本地路径（字符串）；同一角色的多张参考图合成一个版本时用字符串数组。
//           哪几张合成一个版本、各部分以哪张为准，按用户指定，拿不准先问用户，合成方式写进 outfit
//   head    头部特征逐项清单（直接用提示词「人物」段里那串）
//   outfit  服装说明：参考图服装特点 + 本次有意做的改动（为守红线的改动、改色、没有先例按默认方案出的小件颜色、补全、新增项、去掉的东西）
//   crops   scripts/crops.py 输出的 8 张裁切路径，必须按序号 0-7 排列
//   persona 可选，人设（如「日本学校保健室里成熟妩媚的女老师」）；不填就不审人设项
// 也可以在 args 顶层给 persona，作为所有图的默认值。

// ---------- 尺度红线：总则 SKILL.md「一、尺度红线」原文（用户原话一行 + 执行口径 6 条 + 允许露一行），逐字一致 ----------
// 改总则第一节时必须同步改这里和 references/审核员.md 第 4.1、4.2 节。
const REDLINES = [
  '用户原话：不可以——胸部大于 B、乳沟、正面脖子到肚脐上方露肤、肚脐下方到膝盖上方露肤、光脚；可以——肩部可露、背部可小范围露。',
  '',
  '执行口径：',
  '1. 正面躯干从**脖子根部到肚脐上方**不露皮肤：锁骨、胸口、V 领里的皮肤都算违规。',
  '2. 胸部**不大于 B 罩杯**（重点看侧面）。',
  '3. 没有乳沟，也没有胸部沟线。',
  '4. 没有激凸（衣服上的凸点）。',
  '5. **肚脐下方到膝盖上方**不露皮肤；**薄丝袜不算遮挡**，裙摆必须盖住膝盖上沿，开衩不能露出膝盖以上。',
  '6. 不能光脚，必须穿鞋。',
  '',
  '允许露：用户原话允许的是**肩部、小范围后背**；手臂和膝盖以下的小腿不在禁区内，因此也可以露。',
].join('\n')

// ---------- 用户没定过的情况：总则第一节末尾 ----------
const UNDECIDED = '【用户没定过的情况】例如半透明面料下透出皮肤、用不透明打底裤代替裙子遮挡、后背露出是否还算“小范围”：不要自己判过或不过，记为临界，写明是什么情况、在哪张裁切，由主代理去问用户。'

// ---------- 服装规则：总则第二节优先级 + 第三节（人物与服装） ----------
const OUTFIT_RULES = [
  '- 优先级：红线 > 参考图服装的辨识度 > 擦边加强。',
  '- 服装保留参考图的特点和材质：款式、面料、图案、关键配件保留。为满足红线做的遮挡、加长、补鞋、去危险道具，只做最小修改，不算违规。参考图缺的部分（如只有上半身时的下装和鞋）按服装说明补全，同样守红线和改色规则。',
  '- 改色只改黑色：参考图主体服装里的黑色改成亮色，其他颜色照参考图不改。袜子、鞋、配件按用户确认过的先例，没有先例的以服装说明为准。已确认的先例：v2、v4 通过版带膝下黑色薄丝袜（v4 参考图本来没有丝袜，是新增），用户确认合格。',
  '- 人设靠穿法和道具体现：可以调整穿法、加人设道具，不换掉整套衣服、不加整件外套，除非用户明确要求（以服装说明为准）。与人设冲突的普通道具应去掉。',
  '- 新增要透明：参考图没有的东西（小件、镂空、道具、丝袜、补全的下装或鞋等）可以为擦边或人设加，但都要逐项列出；服装说明里没写、图里却出现的，是模型自己加的，必须指出（additions 里 declared 设为 false）。模型自己加的东西怎么判，见 c、d 两条。',
  '- 目标是合规前提下尽可能擦边：红线是上限，不是变保守的理由。把身材曲线做满，胸控制在 B 以内但保留自然弧度，不压成平板、不穿宽松。擦边优先靠剪裁贴合、姿态和身材曲线；在允许露的部位做小幅露出或加小件可以，但不能改掉服装的款式辨识度。',
  '- 模型固定，不建议换模型。',
].join('\n')

// crops.py 的 8 张裁切，序号和含义。
// 四格的竖向分界由 crops.py 按白底留白自动找（头肩大特写格通常占宽度 1/3 以上，不是 1/4）；
// 自动失败时退回四等分或用 --cuts 手动指定，主代理派审核前已看 0 全图核对过裁切。
const CROP_NAMES = [
  '0 全图（整张缩到 1/3）',
  '1 大特写（第 1 格全高，缩到 2/3）',
  '2 大特写胸口（第 1 格，高 45%-100%，原分辨率）',
  '3 正面躯干（第 2 格，高 8%-48%，原分辨率）',
  '4 侧面躯干（第 3 格，高 8%-48%，原分辨率）',
  '5 裙摆膝盖（第 2-4 格，高 50%-85%，原分辨率）',
  '6 鞋（第 2-4 格，高 82%-100%，原分辨率）',
  '7 背面（第 4 格全高，缩到 2/3）',
]

const ITEM = {
  type: 'object',
  properties: {
    item: { type: 'string', description: '编号 + 简称，如「2 胸≤B」「e 擦边曲线」' },
    pass: { type: 'boolean' },
    borderline: { type: 'boolean', description: '临界或拿不准时为 true' },
    evidence: { type: 'string', description: '在哪张裁切（编号）、什么位置、看到了什么；用户没定过的情况以「用户未定：」开头' },
  },
  required: ['item', 'pass', 'borderline', 'evidence'],
}

const CHANGE = {
  type: 'object',
  properties: {
    item: { type: 'string', description: '是什么、在哪个视图，如「膝下黑色薄丝袜（第 2-4 格）」' },
    declared: { type: 'boolean', description: '服装说明里有没有写这项改动' },
    note: { type: 'string', description: '颜色、和人设或改色规则的关系等；没有写「无」' },
  },
  required: ['item', 'declared', 'note'],
}

const SCALE_SCHEMA = {
  type: 'object',
  properties: {
    items: { type: 'array', items: ITEM, minItems: 6, maxItems: 6 },
    cup_estimate: { type: 'string', description: '从侧面格估计的罩杯，如 A、A-B、B、B/C 临界、C' },
    other_concerns: { type: 'string', description: '6 条以外、和用户原话有关的疑点（如后背露出是否还算小范围）；没有写「无」' },
    overall_pass: { type: 'boolean' },
    fix: { type: 'string' },
  },
  required: ['items', 'cup_estimate', 'other_concerns', 'overall_pass', 'fix'],
}

function styleSchema(n) {
  return {
    type: 'object',
    properties: {
      items: { type: 'array', items: ITEM, minItems: n, maxItems: n },
      cup_estimate: { type: 'string', description: '从侧面格估计的罩杯' },
      redline_concerns: { type: 'string', description: '顺带看到的疑似越线处和用户没定过的情况，没有写「无」' },
      additions: { type: 'array', items: CHANGE, description: '生成图里有、参考图里没有的东西' },
      removals: { type: 'array', items: CHANGE, description: '参考图里有、生成图里没有或被改掉的服装部件、配件、道具（改色不算）' },
      overall_pass: { type: 'boolean' },
      fix: { type: 'string' },
    },
    required: ['items', 'cup_estimate', 'redline_concerns', 'additions', 'removals', 'overall_pass', 'fix'],
  }
}

// ---------- 读取并检查 args ----------
let input = args
if (typeof input === 'string') {
  try {
    input = JSON.parse(input)
  } catch (e) {
    throw new Error('args 应是对象 { images: [...] }，收到的是无法解析的字符串')
  }
}
const images = input && Array.isArray(input.images) ? input.images : null
if (!images || images.length === 0) {
  throw new Error('args.images 必须是非空数组：{ images: [{ tag, ref, head, outfit, crops: [8 个裁切路径] }] }')
}
const problems = []
images.forEach((img, i) => {
  const name = (img && img.tag) || `第 ${i} 张`
  if (!img || !img.tag) problems.push(`${name}：缺 tag`)
  if (!img || !img.ref || (Array.isArray(img.ref) && img.ref.length === 0)) problems.push(`${name}：缺 ref（参考图路径）`)
  if (!img || !img.head) problems.push(`${name}：缺 head（头部特征）`)
  if (!img || !img.outfit) problems.push(`${name}：缺 outfit（服装说明）`)
  if (!img || !Array.isArray(img.crops) || img.crops.length !== 8) problems.push(`${name}：crops 必须正好 8 个裁切路径，按 crops.py 序号 0-7 排列`)
})
if (problems.length) throw new Error('args 不合格：\n' + problems.join('\n'))

const DEFAULT_PERSONA = input.persona || ''

function cropLines(img) {
  return img.crops.map((p, i) => `- [${CROP_NAMES[i]}] ${p}`).join('\n')
}

// ---------- 尺度审核员 ----------
function scalePrompt(img) {
  return `你是买量素材的尺度审核员，非常严格：你的职责是挑出违规，不是放行。

用 Read 工具逐张打开下面 8 张图。它们是同一张「角色设定四视图」的整图和局部裁切；四视图从左到右：第 1 格头肩大特写、第 2 格正面全身、第 3 格侧面全身、第 4 格背面全身（四格按留白自动分界，大特写格通常比其他格宽）。8 张都要打开看，只看整图缩略不算审核：
${cropLines(img)}

【尺度红线（用户给的审核线，硬性，按字面执行，不许自己放宽或收紧）】
${REDLINES}

${UNDECIDED}

【每条去哪看、怎么判】
- 第 1 条：看裁切 1、2、3，肚脐以上的腰腹再对照 0。从脖子根部到肚脐上方，锁骨、胸口、V 领开口里只要露出一点皮肤就是 fail；领口要贴到脖子根部。
- 第 2 条：重点看裁切 4（第 3 格侧面），再对照 2、3。看胸部最前点相对下胸围/腰线向前凸出多少。经验参考（以前的审核员用过，不是用户给的标准）：前凸不超过约 0.15 个头长，在 3840 宽的原图上约 40px（裁切 2-6 是原分辨率）。
- 第 3 条：看裁切 2、3，特别是领口和 V 领底部、胸前衣服的褶皱，有没有乳沟或胸部沟线。
- 第 4 条：看裁切 2、3、4，胸点位置的衣服上有没有凸点。挂在胸前的道具（如听诊器的黑色耳塞）正好落在胸点上、看着像凸点、分不清时，判 fail 并写明。
- 第 5 条：看裁切 5、7 和 0，三个全身视图都要看。按红线字面判：裙摆盖住膝盖上沿就过；看得到膝盖骨上缘或更上面的大腿（被丝袜盖着的也算）就 fail；裙摆压在膝盖上沿附近看不清，按拿不准判 fail。找膝盖的经验估计：身高从头顶量到鞋底，膝盖中心约在离地 28% 身高处，膝盖上沿在中心上方一点——这只帮你定位，不是判定线，不要求裙摆低于膝盖中心。开衩顶端在膝盖以下不违反红线；开到膝盖上沿或以上、或看不清顶端在哪，判 fail。
- 第 6 条：看裁切 6，三个全身视图都必须穿鞋。
- 允许露的部位（肩部、小范围后背、手臂、膝盖以下的小腿）露出来不算违规，不要因此判 fail。后背看裁切 7：露出范围大到拿不准还算不算“小范围”，写进 other_concerns，按用户没定过的情况处理。

【输出要求】
- items 正好 6 条，按 1-6 顺序；item 写编号和简称（如「2 胸≤B」）。
- 每条给 pass。拿不准就判 fail：pass 设为 false、borderline 设为 true，并在 evidence 里写为什么拿不准。
- 属于用户没定过的情况：pass 设为 false、borderline 设为 true，evidence 以「用户未定：」开头写清是什么情况。
- evidence 写：在哪张裁切（编号）、什么位置、看到了什么。
- cup_estimate 写你从侧面格估计的罩杯（如 A、A-B、B、B/C 临界、C）。
- other_concerns：6 条以外、和用户原话有关的疑点（例如后背露出是否还算小范围、6 条都套不上的用户没定过的情况），写裁切编号和位置；没有写「无」。
- overall_pass 只有 6 条全部 pass 才为 true。
- fix：没过的条目具体怎么改（哪个视图、哪个部位、改成什么）；用户没定过的条目可以写改法，但注明要等用户定；6 条全过写「无」。
只做审核，不要修改或创建任何文件。`
}

// ---------- 造型审核员 ----------
function styleItems(img, persona) {
  const items = [
    'a 布局：一行四格（第 1 格头肩大特写，严格正脸、闭嘴、看镜头；第 2 格正面全身；第 3 格侧面全身；第 4 格背面全身），三个全身视图头顶到鞋底完整入画、同一比例、同一高度；没有任何文字、标签、信息卡、色板、水印、角标、UI、多余人物、场景家具。第 3 格人朝左还是朝右在 evidence 里注明即可，不因朝向单独判 fail（用户暂未要求修正）',
    `b 头部和参考图一致，四个视图是同一个人：${img.head}`,
    `c 服装保留参考图的特点和材质，款式辨识度还在（对照服装说明）：${img.outfit}。为守红线做的遮挡、加长、补鞋、去危险道具算最小修改，不算没保留；参考图缺的部分按服装说明补全。模型自己加的东西列进 additions，不单凭“是模型自己加的”判本条不过；它改掉了款式辨识度或是整件外套时照常判不过`,
    'd 改色：参考图主体服装里的黑色改成了亮色；其他颜色照参考图没变；袜子、鞋、配件的颜色和服装说明一致（膝下黑色薄丝袜是用户确认过的先例，服装说明写了就不算违规）。服装说明没写、模型自己加在主体服装上的黑色单品，违反只改黑色，判不过；模型自己加的袜子、鞋、配件这类小件，不因颜色判本条不过，列进 additions 并在 note 里写明颜色',
    'e 擦边与身材曲线：腰和胯臀曲线明显，衣服剪裁贴合、不宽松，姿态有曲线；胸在 B 以内但有自然弧度，不是压成平板；整体性感有吸引力，而不是宽松保守。允许露的部位：参考图本来露的应保留，参考图没露的不要求露。鞋跟高低以服装说明为准，不因鞋跟判不过',
    'f 好不好看：搭配是否好看；有没有明显的 AI 畸形（手指、肢体、衣服结构、道具结构错误，例如听诊器两头都是耳塞）',
  ]
  if (persona) {
    items.push(`g 人设能看出来：${persona}。人设靠穿法和道具体现：可以调整穿法、加人设道具，不换掉整套衣服、不加整件外套（服装说明里写明是用户要求的除外）；和人设冲突的普通道具应已去掉`)
  }
  return items
}

function stylePrompt(img, items) {
  const refs = [].concat(img.ref)
  return `你是买量素材的造型审核员。先用 Read 工具打开参考图（有多张时每张都打开：它们是同一个角色的参考图，按用户指定合成一个版本，哪部分以哪张为准见服装说明）：
${refs.map((p) => `- ${p}`).join('\n')}
再逐张打开生成的「角色设定四视图」整图和局部裁切（四视图从左到右：第 1 格头肩大特写、第 2 格正面全身、第 3 格侧面全身、第 4 格背面全身；四格按留白自动分界，大特写格通常比其他格宽）：
${cropLines(img)}

用户要的是：在尺度合规的前提下尽可能擦边的角色。下面的尺度红线是硬性上限。你不负责逐条判红线（另有尺度审核员），但你的任何修改建议都不能违反它：
${REDLINES}

${UNDECIDED}

服装规则：
${OUTFIT_RULES}

请逐条判断：
${items.join('\n')}

【输出要求】
- items 按上面顺序，每条一项，共 ${items.length} 条；item 写字母和简称（如「e 擦边曲线」）。
- 每条给 pass 和 evidence（在哪张图、什么位置、看到了什么）。拿不准时 borderline 设为 true，并在 evidence 里写为什么拿不准；pass 按你的实际判断给，造型项不因拿不准就判不过。
- cup_estimate：你从侧面格估计的罩杯（尺度审核员会独立再判一次）。
- redline_concerns：顺带看到的疑似越线处和用户没定过的情况（写裁切编号和位置）；没有写「无」。
- additions：生成图里有、参考图里没有的东西，逐项列出（小件、镂空、道具、丝袜、补全的下装或鞋等），每项写是什么、在哪个视图、服装说明里写没写（declared）；没有就给空数组。
- removals：参考图里有、生成图里没有或被改掉的服装部件、配件、道具（改色不算），逐项列出，写明服装说明里写没写要去掉（declared）；没有就给空数组。
- overall_pass 只有全部条目通过才为 true。
- fix：具体怎么改，尽量写成能直接加进提示词的措辞。每条建议都必须在红线内：不能建议解开领口、露锁骨或胸口、开 V 领、放大胸部、裙子改短到膝上、开衩到膝上、露大腿、光脚；也不要建议换模型。想加强擦边，优先从剪裁贴合、姿态、身材曲线入手；也可以在允许露的部位（肩部、小范围后背、手臂、膝盖以下的小腿）做小幅露出或加小件，但不能改掉参考图服装的款式辨识度，并写明这是新增。某项改进只有越线或改掉服装辨识度才做得到时，写「红线内无法改进」。全部通过写「无」。
只做审核，不要修改或创建任何文件。`
}

// ---------- 结果校正 ----------
const isNone = (s) => !s || /^\s*(无|没有|none)?\s*[。.]?\s*$/i.test(String(s))
const isUndecided = (it) => String(it.evidence || '').includes('用户未定')

// 尺度项：拿不准一律判不过（对内）。脚本硬性兜底。
function normalizeScale(r, tag) {
  if (!r) return null
  const notes = []
  r.items.forEach((it) => {
    if (isUndecided(it) && (it.pass || !it.borderline)) {
      it.pass = false
      it.borderline = true
      notes.push(`「${it.item}」是用户没定过的情况，按临界记为不过`)
    } else if (it.borderline && it.pass) {
      it.pass = false
      notes.push(`「${it.item}」标了临界却判 pass，按「尺度项拿不准判不过」改为 fail`)
    }
  })
  if (r.items.length !== 6) notes.push(`items 应为 6 条，实际 ${r.items.length} 条，整体按不过处理`)
  const all = r.items.length === 6 && r.items.every((it) => it.pass)
  if (r.overall_pass !== all) {
    notes.push(`overall_pass 与逐条结果不一致，按逐条结果改为 ${all}`)
    r.overall_pass = all
  }
  if (notes.length) log(`尺度:${tag} 校正：${notes.join('；')}`)
  r.script_notes = notes
  return r
}

// 造型项：拿不准不强制判不过，borderline 原样保留，在 summary 里如实列出。
function normalizeStyle(r, tag, n) {
  if (!r) return null
  const notes = []
  if (!Array.isArray(r.additions)) r.additions = []
  if (!Array.isArray(r.removals)) r.removals = []
  if (r.items.length !== n) notes.push(`items 应为 ${n} 条，实际 ${r.items.length} 条，整体按不过处理`)
  const all = r.items.length === n && r.items.every((it) => it.pass)
  if (r.overall_pass !== all) {
    notes.push(`overall_pass 与逐条结果不一致，按逐条结果改为 ${all}`)
    r.overall_pass = all
  }
  if (notes.length) log(`造型:${tag} 校正：${notes.join('；')}`)
  r.script_notes = notes
  return r
}

function emptySummary(missing) {
  return {
    scale_pass: null,
    style_pass: null,
    cup: { scale: null, style: null },
    scale_failed: [],
    scale_borderline: [],
    user_undecided: [],
    scale_other_concerns: null,
    style_failed: [],
    style_borderline: [],
    style_redline_concerns: null,
    disputes: [],
    additions: [],
    undeclared_additions: [],
    removals: [],
    undeclared_removals: [],
    missing,
  }
}

function summarize(scale, style) {
  const missing = []
  if (!scale) missing.push('尺度审核员')
  if (!style) missing.push('造型审核员')
  const s = emptySummary(missing)
  if (scale) {
    s.scale_pass = scale.overall_pass
    s.cup.scale = scale.cup_estimate
    s.scale_failed = scale.items.filter((it) => !it.pass).map((it) => it.item)
    s.scale_borderline = scale.items.filter((it) => it.borderline).map((it) => it.item)
    s.user_undecided = scale.items.filter(isUndecided).map((it) => `${it.item}：${it.evidence}`)
    s.scale_other_concerns = scale.other_concerns
  }
  if (style) {
    s.style_pass = style.overall_pass
    s.cup.style = style.cup_estimate
    s.style_failed = style.items.filter((it) => !it.pass).map((it) => it.item)
    s.style_borderline = style.items.filter((it) => it.borderline).map((it) => it.item)
    s.style_redline_concerns = style.redline_concerns
    s.additions = style.additions.map((a) => a.item)
    s.undeclared_additions = style.additions.filter((a) => !a.declared).map((a) => `${a.item}（${a.note}）`)
    s.removals = style.removals.map((a) => a.item)
    s.undeclared_removals = style.removals.filter((a) => !a.declared).map((a) => `${a.item}（${a.note}）`)
  }
  // 两人对尺度意见相左：对内按不过处理，由主代理按 references/审核员.md 第 6 节处理。
  // 胸的相左按罩杯字母粗判（造型估计里出现 C 及以上算“超 B”），只是提醒，以主代理对比 cup 为准。
  if (scale && style) {
    const chest = scale.items[1]
    const styleSaysOver = /[C-F]/.test(String(style.cup_estimate || ''))
    if (chest && chest.pass === styleSaysOver) {
      s.disputes.push(`胸：尺度审核员判${chest.pass ? '过' : '不过'}（估 ${scale.cup_estimate}），造型审核员估 ${style.cup_estimate}`)
    }
    if (scale.overall_pass && !isNone(style.redline_concerns)) {
      s.disputes.push(`尺度审核员 6 条全过，造型审核员指出疑似越线：${style.redline_concerns}`)
    }
  }
  return s
}

// ---------- 主流程 ----------
phase('审图')
log(`共 ${images.length} 张图，每张派 2 个审核员`)

const results = await pipeline(images, (img) => {
  const persona = img.persona || DEFAULT_PERSONA
  const items = styleItems(img, persona)
  return parallel([
    () => agent(scalePrompt(img), { label: `尺度:${img.tag}`, phase: '审图', schema: SCALE_SCHEMA }),
    () => agent(stylePrompt(img, items), { label: `造型:${img.tag}`, phase: '审图', schema: styleSchema(items.length) }),
  ]).then(([scaleRaw, styleRaw]) => {
    const scale = normalizeScale(scaleRaw, img.tag)
    const style = normalizeStyle(styleRaw, img.tag, items.length)
    const summary = summarize(scale, style)
    const word = (v) => (v === null ? '缺失' : v ? '过' : '不过')
    log(`${img.tag}：尺度 ${word(summary.scale_pass)}（胸 ${summary.cup.scale || '-'}）/ 造型 ${word(summary.style_pass)}（胸 ${summary.cup.style || '-'}）`)
    if (summary.user_undecided.length) log(`${img.tag}：有用户没定过的情况，需要问用户：${summary.user_undecided.join('；')}`)
    if (summary.disputes.length) log(`${img.tag}：两个审核员对尺度意见相左`)
    if (summary.undeclared_additions.length) log(`${img.tag}：服装说明里没写的新增（模型自己加的，按 审核员.md 第 6 节处理）：${summary.undeclared_additions.join('；')}`)
    if (summary.missing.length) log(`${img.tag}：${summary.missing.join('、')}没有返回结果，需要重跑这张`)
    return { tag: img.tag, scale, style, summary }
  })
})

// 不静默丢图：pipeline 某张整体失败时也保留一条记录
return images.map((img, i) => results[i] || {
  tag: img.tag,
  scale: null,
  style: null,
  summary: emptySummary(['尺度审核员', '造型审核员']),
})
