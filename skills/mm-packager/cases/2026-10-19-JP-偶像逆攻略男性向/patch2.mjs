import fs from 'node:fs';
const API = 'http://127.0.0.1:4400/api', F = encodeURIComponent('2026年10月19日MM-JP-偶像妄想迭代');
const call = async (m, u, b) => { const r = await fetch(API + u, {method: m, headers: b ? {'content-type': 'application/json'} : {}, body: b ? JSON.stringify(b) : undefined}); const t = await r.text(); if (!r.ok) throw new Error(m + ' ' + u + ' ' + t); return JSON.parse(t); };
const DIR = 'F:/钟海明/2026/2026年10月19日MM-JP-偶像妄想迭代/包装素材v2/';
const AUD = 'F:/钟海明/2026/2026年10月10日MM-编辑器重构/app/public/audio/';
let {project: p, revision} = await call('GET', `/projects/${F}`);
const imp = async path => { const {media: m} = await call('POST', `/projects/${F}/media`, {sourcePath: path}); const ex = p.media.find(x => x.path === m.path); if (ex) return ex.id; p.media.push(m); return m.id; };
const img = n => imp(DIR + n + '.png');
let seq = 0; const id = () => 'c' + Date.now().toString(36) + (seq++).toString(36) + Math.random().toString(36).slice(2, 6);
const TF = (ax = .5, ay = .5) => ({x: 0, y: 0, scale: 1, rotation: 0, opacity: 1, anchorX: ax, anchorY: ay});
const r3 = v => +v.toFixed(3);
const kf = arr => arr.map(([t, v, ease]) => ({t: r3(t), v, ...(ease ? {ease} : {})}));

// ---- clean old layers ----
const DROP_TRACKS = new Set(['M-title', 'M-end', 'M-cta1', 'M-cta2']);
p.clips = p.clips.filter(c => !DROP_TRACKS.has(c.trackId) && !c.trackId.startsWith('X-') && !(c.trackId === 'V1' && c.type === 'image') && c.trackId !== 'A2' && c.trackId !== 'A3');
p.clips = p.clips.filter(c => !(c.trackId === 'M-bubble' && c.module?.data?.role === 'user'));
p.tracks = p.tracks.filter(t => !DROP_TRACKS.has(t.id) && !t.id.startsWith('X-'));
const iB = p.tracks.findIndex(t => t.id === 'M-bubble');
const newTracks = [];
const track = (tid, name, mt) => { newTracks.push({id: tid, kind: 'module', moduleType: mt, name, locked: false, hidden: false, muted: false}); return tid; };
// order = bottom → top (after video, under bubbles? put above bubbles; bubbles never overlap these regions)
['X-vig:内心 暗角:bubble', 'X-haze:内心 压暗:bubble', 'X-br:内心 括号:bubble', 'X-m1:内心 文字1:bubble', 'X-m2:内心 文字2:bubble', 'X-m3:内心 文字3:bubble', 'X-m4:内心 文字4:bubble',
 'X-mb:进度条 底:meter', 'X-mf:进度条 填充:meter', 'X-o1:进度条 1日目:meter', 'X-o2:进度条 2日目:meter', 'X-o3:进度条 3日目:meter', 'X-uldim:解锁 压暗:meter', 'X-o4:进度条 制限モード:meter', 'X-o5:解锁 开锁:meter', 'X-ulb:解锁 光爆:meter', 'X-title:标题:title',
 'X-esp1:片尾 闪光1:end', 'X-esp2:片尾 闪光2:end', 'X-ehead:片尾 文案:end', 'X-elogo:片尾 Logo:end', 'X-ebtn:片尾 下载按钮:end', 'X-ebadge:片尾 商店标:end', 'X-ehand:片尾 手指:end', 'X-ulw:解锁 白闪转场:end']
  .forEach(s => { const [a, b, c] = s.split(':'); track(a, b, c); });
p.tracks.splice(iB + 1, 0, ...newTracks);
const add = async (trackId, name, start, duration, file, extra = {}) => p.clips.push({id: id(), trackId, type: 'image', name, start: r3(start), duration: r3(duration), mediaId: await img(file), fit: 'fill', transform: TF(extra.ax, extra.ay), keyframes: extra.k ?? {}});
const fadeIO = (D, i = .3, o = .35) => kf([[0, 0], [i, 1, 'ease'], [D - o, 1], [D, 0, 'ease']]);

for (const c of p.clips) if (c.type === 'module' && c.module?.templateId === 'bubble/liquid') c.module.params = {...(c.module.params || {}), font: 'ZenMaruGothic-Black', fontSize: 50};
// ---- title 0–3.6 ----
await add('X-title', '标题', 0, 3.6, 'title_b', {ay: 1390 / 1920, k: {opacity: fadeIO(3.6, .22, .35), scale: kf([[0, 1.18], [.32, .97, 'ease'], [.45, 1, 'ease']])}});

// ---- meter ----
const MS = 3.4, ME = 47, MD = ME - MS, NY = 196 / 1920;
const O = 17.042, D3 = 29.1;
await add('X-mb', '进度条 底', MS, MD, 'mt2_base', {k: {opacity: kf([[0, 0], [.35, 1, 'ease']]), y: kf([[0, -30], [.35, 0, 'ease']])}});
await add('X-mf', '进度条 填充', MS, MD, 'mt2_fill', {ax: 180 / 1080, ay: NY, k: {scaleX: kf([[0, 0], [O - MS, 0], [O - MS + .6, .5, 'ease'], [D3 - MS, .5], [D3 - MS + .6, 1, 'ease']])}});
const pop = kf([[0, .3], [.22, 1.18, 'ease'], [.38, 1, 'ease']]);
const ons = [[3.5, 180 / 1080], [O + .6, 420 / 1080], [D3 + .6, 660 / 1080]];
for (const [i, [s, ax]] of ons.entries()) await add(`X-o${i + 1}`, `进度条 ${i + 1}日目`, s, ME - s, `mt2_on${i + 1}`, {ax, ay: NY, k: {scale: pop, opacity: kf([[0, 0], [.12, 1]])}});

const F0 = 45.4, F1 = 45.95, UT = 46.6; // lock flies to centre, unlocks, white-flash cut to end card (47)
const DX = 540 - 900, DY = 960 - 196, SC = 2.7, NA = {ax: 900 / 1080, ay: NY};
const wig = [[UT - .45, 0], [UT - .38, -4], [UT - .31, 4], [UT - .24, -3], [UT - .17, 3], [UT - .1, 0, 'ease']].map(([t, v, e]) => [t - MS, v, e]);
await add('X-uldim', '解锁 压暗', F0, 47 - F0, 'ul_dim', {k: {opacity: kf([[0, 0], [F1 - F0, 1, 'ease']])}});
await add('X-o4', '进度条 制限モード', MS, UT - MS, 'mt2_lock', {...NA, k: {opacity: kf([[0, 0], [.35, 1, 'ease']]), y: kf([[0, -30], [.35, 0, 'ease'], [F0 - MS, 0], [F1 - MS, DY, 'ease']]), x: kf([[F0 - MS, 0], [F1 - MS, DX, 'ease']]), scale: kf([[F0 - MS, 1], [F1 - MS, SC, 'ease']]), rotation: kf(wig)}});
await add('X-o5', '解锁 开锁', UT, 47 - UT, 'mt2_lock_open', {...NA, k: {x: kf([[0, DX]]), y: kf([[0, DY]]), scale: kf([[0, SC], [.12, SC * 1.15, 'ease'], [.3, SC * 1.08, 'ease']])}});
await add('X-ulb', '解锁 光爆', UT, 47 - UT, 'ul_burst2', {k: {scale: kf([[0, .5], [.4, 1.9, 'ease']]), opacity: kf([[0, 0], [.05, 1], [.4, .9]])}});
await add('X-ulw', '解锁 白闪转场', UT + .15, 47.35 - UT - .15, 'ul_white', {k: {opacity: kf([[0, 0], [47 - UT - .15, 1, 'ease'], [47.35 - UT - .15, 0, 'ease']])}});
// ---- inner monologue ----
const LINES = [[17.442, 22.842], [23.342, 28.742], [29.242, 31.842], [32.042, 34.842], [35.242, 38.842], [39.242, 42.842]];
const meta = JSON.parse(fs.readFileSync(DIR + 'mono_meta.json', 'utf8'));
await add('X-vig', '内心 暗角', O + .2, 43.0 - O - .2, 'mono_vignette', {k: {opacity: fadeIO(43.0 - O - .2, .8, .6)}});
for (const [li, [s, e]] of LINES.entries()) {
  const D = e - s, n = meta[li];
  await add('X-haze', `内心 压暗${li + 1}`, s, D, 'mono_haze', {k: {opacity: fadeIO(D, .4, .4)}});
  await add('X-br', `内心 括号${li + 1}`, s, D, `mv2_${li + 1}_br`, {ay: .71, k: {opacity: fadeIO(D, .35, .4), scaleX: kf([[0, .9], [.4, 1, 'ease']])}});
  const step = Math.min(.75, (D * .62 - .2) / n);
  for (let j = 0; j < n; j++) {
    const t0 = .2 + j * step, d = D - t0;
    await add(`X-m${j + 1}`, `内心${li + 1}-${j + 1}`, s + t0, d, `mv2_${li + 1}_${j + 1}`, {k: {opacity: kf([[0, 0], [.4, 1, 'ease'], [d - .4, 1], [d, 0, 'ease']]), y: kf([[0, 18], [.5, 0, 'ease']])}});
  }
}

// ---- end card ----
const E = 47, ED = 2.3, END = E + ED;
await add('V1', '片尾 背景', E, ED, 'end_bg_b', {ay: .35, k: {scale: kf([[0, 1], [ED, 1.07]])}});
const tw = (ph) => kf([[0, 0], [.3, 1], [.9 + ph, .35], [1.5 + ph, 1], [2.1 + ph, .4], [2.7 + ph, 1], [3.3, .5]]);
await add('X-esp1', '片尾 闪光1', E + .6, ED - .6, 'end_spark1', {k: {opacity: tw(0)}});
await add('X-esp2', '片尾 闪光2', E + .9, ED - .9, 'end_spark2', {k: {opacity: tw(.3)}});
await add('X-ehead', '片尾 文案', E + .25, ED - .25, 'end_headline_b', {ay: 1320 / 1920, k: {opacity: kf([[0, 0], [.18, 1]]), scale: kf([[0, 1.35], [.34, .95, 'ease'], [.5, 1, 'ease']])}});
await add('X-elogo', '片尾 Logo', E + .45, ED - .45, 'end_logo_b', {k: {opacity: kf([[0, 0], [.3, 1, 'ease']]), y: kf([[0, -30], [.35, 0, 'ease']])}});
const em = JSON.parse(fs.readFileSync(DIR + 'end_meta.json', 'utf8'));
const BS = E + .6, HS = E + .85, TAPS = [0.3, 0.62, 0.94, 1.26];
const bscale = [[0, .5], [.25, 1.08, 'ease'], [.4, 1, 'ease']];
for (const t of TAPS) { const r = HS + t - BS; bscale.push([r - .06, 1], [r + .04, .94, 'ease'], [r + .2, 1, 'ease']); }
await add('X-ebtn', '片尾 下载按钮', BS, END - BS, 'end_button', {ay: 1601 / 1920, k: {scale: kf(bscale), opacity: kf([[0, 0], [.15, 1]])}});
await add('X-ebadge', '片尾 商店标', E + .7, END - E - .7, 'end_badges_c', {k: {opacity: kf([[0, 0], [.3, 1, 'ease']]), y: kf([[0, 30], [.35, 0, 'ease']])}});
const hsc = [[0, 1]]; for (const t of TAPS) hsc.push([t - .08, 1], [t, .86, 'ease'], [t + .16, 1, 'ease']);
await add('X-ehand', '片尾 手指', HS, END - HS, 'end_hand', {ax: em.tapX / 1080, ay: em.tapY / 1920, k: {opacity: kf([[0, 0], [.2, 1]]), x: kf([[0, 80], [.22, 0, 'ease']]), y: kf([[0, 90], [.22, 0, 'ease']]), scale: kf(hsc)}});

// ---- audio ----
const AD = 'F:/钟海明/2026/2026年10月19日MM-JP-偶像妄想迭代/包装素材v2/audio/';
p.clips = p.clips.filter(c => !/^A[3-6]$/.test(c.trackId));
p.tracks = p.tracks.filter(t => !/^A[4-6]$/.test(t.id));
for (const t of p.tracks) if (t.id === 'A2' || t.id === 'A3') t.muted = false;
const iA3 = p.tracks.findIndex(t => t.id === 'A3');
p.tracks.splice(iA3 + 1, 0, {id: 'A4', kind: 'audio', name: 'A4 音效2', locked: false, hidden: false, muted: false}, {id: 'A5', kind: 'audio', name: 'A5 音效3', locked: false, hidden: false, muted: false}, {id: 'A6', kind: 'audio', name: 'A6 音效4', locked: false, hidden: false, muted: false});
// original sound: drop amusement-park part of video2 (repeats part 1)
const a1 = p.clips.find(c => c.trackId === 'A1' && c.start === 0) ?? p.clips.find(c => c.trackId === 'A1');
p.clips = p.clips.filter(c => c.trackId !== 'A1');
const CUT0 = O, CUT1 = O + 6;
p.clips.push({...a1, id: id(), start: 0, in: 0, duration: CUT0});
p.clips.push({...a1, id: id(), start: CUT1, in: CUT1, duration: r3(47 - CUT1), linkGroup: undefined, volume: .35});
// bubble template sounds off (thinking = 沙沙), replaced by clean pon
const bubStarts = p.clips.filter(c => c.type === 'module' && c.module?.templateId === 'bubble/liquid').map(c => c.start);
// BGM
const bgm = await imp(AD + 'bgm_koi.wav');
p.clips.push({id: id(), trackId: 'A2', type: 'audio', name: 'BGM 恋爱八音盒', mediaId: bgm, start: O, duration: r3(Math.min(32.4, END - O)), in: 0, speed: 1, volume: .7, fadeIn: .4, fadeOut: .5});
for (const c of p.clips) if (c.type === 'module' && c.module?.templateId === 'bubble/liquid') c.module.params = {...c.module.params, sounds: {thinking: null}};
const sfx = [['a_title', 0.02, .6], ['a_node', 3.5, .55],
  ['a_day', O, .5], ['a_node', O + .6, .55], ['a_day', D3, .5], ['a_node', D3 + .6, .55],
  ...LINES.map(([s]) => ['a_kira', s, .35]), ['a_unlock', UT - .03, .85], ['a_end', E + .05, .55], ...TAPS.map(t => ['a_tap', HS + t, .6])];
const lanes = {A3: 0, A4: 0, A5: 0, A6: 0};
for (const [f, s, v] of sfx.sort((a, b) => a[1] - b[1])) {
  const mid = await imp(AD + f + '.wav'); const md = p.media.find(x => x.id === mid)?.duration ?? 1;
  const d = Math.min(md, END - s); if (d <= .05) continue;
  const lane = Object.keys(lanes).find(k => lanes[k] <= s + 1e-3) ?? (() => { throw new Error('lanes full @' + s); })();
  p.clips.push({id: id(), trackId: lane, type: 'audio', name: f, mediaId: mid, start: r3(s), duration: r3(d), in: 0, speed: 1, volume: v}); lanes[lane] = s + d;
}
const r = await call('PUT', `/projects/${F}`, {project: p, revision});
console.log('ok', r.revision, p.clips.length, p.tracks.length);
