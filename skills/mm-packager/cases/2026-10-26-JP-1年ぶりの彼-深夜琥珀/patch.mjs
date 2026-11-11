// 幂等写入工程：V1/A1 原片两段 + 定格/开场/聊天/片尾背景(V1 图片)，X-* 图层（layers.json），A2 BGM，A3 片尾口播，A4–A8 音效
import fs from 'node:fs';
const FOLDER = '2026年10月26日MM-JP-floze迭代2';
const API = 'http://127.0.0.1:4400/api', F = encodeURIComponent(FOLDER);
const ROOT = `F:/钟海明/2026/${FOLDER}/包装素材v1/`;
const call = async (m, u, b) => { const r = await fetch(API + u, {method: m, headers: b ? {'content-type': 'application/json'} : {}, body: b ? JSON.stringify(b) : undefined}); const t = await r.text(); if (!r.ok) throw new Error(m + ' ' + u + ' ' + t); return JSON.parse(t); };
const meta = JSON.parse(fs.readFileSync(ROOT + 'layers.json', 'utf8'));
let {project: p, revision} = await call('GET', `/projects/${F}`);
const imp = async path => { const {media: m} = await call('POST', `/projects/${F}/media`, {sourcePath: path}); const ex = p.media.find(x => x.path === m.path); if (ex) return ex.id; p.media.push(m); return m.id; };
let seq = 0; const id = () => 'c' + Date.now().toString(36) + (seq++).toString(36) + Math.random().toString(36).slice(2, 6);
const TF = (ax = .5, ay = .5) => ({x: 0, y: 0, scale: 1, rotation: 0, opacity: 1, anchorX: ax, anchorY: ay});
const r4 = v => +(+v).toFixed(4);
const snap = v => r4(Math.round(v * 30) / 30);
const kfs = k => Object.fromEntries(Object.entries(k).map(([prop, arr]) => [prop, arr.map(([t, v, e]) => ({t: r4(t), v, ...(e ? {ease: e} : {})}))]));
const VID = p.media.find(m => m.kind === 'video');
const dur = m => p.media.find(x => x.id === m).duration;

// ---- 清理 ----
p.clips = [];
p.tracks = p.tracks.filter(t => !t.id.startsWith('X-') && !/^A[4-9]$/.test(t.id));
const iV = p.tracks.findIndex(t => t.id === 'V1');
p.tracks.splice(iV + 1, 0, ...meta.tracks.map(([tid, name, mt]) => ({id: tid, kind: 'module', moduleType: mt, name, locked: false, hidden: false, muted: false})));
const iA3 = p.tracks.findIndex(t => t.id === 'A3');
p.tracks.splice(iA3 + 1, 0, ...[4, 5, 6, 7, 8].map(i => ({id: `A${i}`, kind: 'audio', name: `A${i} 音效${i - 3}`, locked: false, hidden: false, muted: false})));
for (const t of p.tracks) { t.hidden = false; t.muted = false; if (t.id === 'A3') t.name = 'A3 片尾口播'; if (t.id === 'A2') t.name = 'A2 BGM'; }

// ---- V1 / A1：原片两段（中间是选项1定格） ----
const S1 = snap(meta.off), E1 = r4(meta.f1);
const S2 = snap(meta.f1 + meta.fz1), E2 = r4(meta.f2);
const lg1 = 'L' + id(), lg2 = 'L' + id();
p.clips.push({id: id(), trackId: 'V1', type: 'video', name: '原片 第一幕', mediaId: VID.id, start: S1, duration: r4(E1 - S1), in: 0, speed: 1, linkGroup: lg1, transform: TF(), fit: 'cover'});
p.clips.push({id: id(), trackId: 'A1', type: 'audio', name: '原声 第一幕', mediaId: VID.id, start: S1, duration: r4(E1 - S1), in: 0, speed: 1, volume: 1, linkGroup: lg1, fadeOut: .05});
p.clips.push({id: id(), trackId: 'V1', type: 'video', name: '原片 第二三幕', mediaId: VID.id, start: S2, duration: r4(E2 - S2), in: meta.cut, speed: 1, linkGroup: lg2, transform: TF(), fit: 'cover'});
const A1E = snap(meta.aend + meta.sh2);
p.clips.push({id: id(), trackId: 'A1', type: 'audio', name: '原声 第二三幕（定格2下继续）', mediaId: VID.id, start: S2, duration: r4(A1E - S2), in: meta.cut, speed: 1, volume: 1, fadeOut: .08});

// ---- 图层 ----
for (const L of meta.layers) {
  const mid = await imp(ROOT + L.file + (L.ext ?? '.png'));
  p.clips.push({id: id(), trackId: L.track, type: 'image', name: L.name, start: L.start, duration: L.dur, mediaId: mid, fit: 'fill', transform: TF(L.ax, L.ay), keyframes: kfs(L.k)});
}

// ---- 音频 ----
const AD = ROOT + 'audio/';
const END = r4(meta.end1);
const bgm = await imp(AD + 'bgmA.mp3'); const BL = dur(bgm);
const segs = [[0, meta.off, .45, '开场'], [meta.off, meta.f1, .2, '第一幕'], [meta.f1, meta.f1 + meta.fz1, .4, '选项1'], [meta.f1 + meta.fz1, meta.f2, .2, '第二三幕'],
  [meta.f2, meta.ph0, .3, '选项2 心跳'], [meta.ph0, meta.ec0, .16, '聊天口播（压低）'], [meta.ec0, Math.min(END, BL), .45, '片尾']];
for (const [a, b, v, nm] of segs) { const s0 = snap(a), s1 = b >= END - 1e-3 ? r4(b) : snap(b); if (s1 - s0 < .04) continue;
  p.clips.push({id: id(), trackId: 'A2', type: 'audio', name: 'BGM ' + nm, mediaId: bgm, start: s0, duration: r4(s1 - s0), in: s0, speed: 1, volume: v, ...(nm === '片尾' ? {fadeOut: .6} : {})}); }
const vo = await imp(AD + 'vo_end_a.mp3');
p.clips.push({id: id(), trackId: 'A3', type: 'audio', name: '片尾口播（成熟日语男）', mediaId: vo, start: snap(meta.vo0), duration: r4(Math.min(dur(vo), meta.ec0 - snap(meta.vo0))), in: 0, speed: 1, volume: 1});
const lanes = {A4: 0, A5: 0, A6: 0, A7: 0, A8: 0}; const cache = {};
for (const [f, s, v] of meta.sfx.sort((a, b) => a[1] - b[1])) {
  const mid = cache[f] ??= await imp(AD + f + '.wav'); const st = snap(Math.max(0, s)); const d = r4(Math.min(dur(mid), END - st));
  const lane = Object.keys(lanes).find(k => lanes[k] <= st + 1e-3); if (!lane) { console.warn('drop sfx', f, s); continue; }
  p.clips.push({id: id(), trackId: lane, type: 'audio', name: f, mediaId: mid, start: st, duration: d, in: 0, speed: 1, volume: v}); lanes[lane] = st + d;
}
// 清掉未引用的 media
const used = new Set(p.clips.map(c => c.mediaId)); p.media = p.media.filter(m => used.has(m.id) || m.kind === 'video');
const r = await call('PUT', `/projects/${F}`, {project: p, revision});
console.log('ok', r.revision, 'clips', p.clips.length, 'end', END, 'bgm', BL);
