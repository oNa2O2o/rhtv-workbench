// 幂等写入工程：V1 分段 + 定格 + 片尾背景，A1 原声分段，X-* 图层（layers.json），A2 BGM，A3–A6 音效
import fs from 'node:fs';
const FOLDER = '2026年10月20日MM-JP-伪人义妹敲门';
const API = 'http://127.0.0.1:4400/api', F = encodeURIComponent(FOLDER);
const ROOT = `F:/钟海明/2026/${FOLDER}/包装素材v2/`;
const call = async (m, u, b) => { const r = await fetch(API + u, {method: m, headers: b ? {'content-type': 'application/json'} : {}, body: b ? JSON.stringify(b) : undefined}); const t = await r.text(); if (!r.ok) throw new Error(m + ' ' + u + ' ' + t); return JSON.parse(t); };
const meta = JSON.parse(fs.readFileSync(ROOT + 'layers.json', 'utf8'));
let {project: p, revision} = await call('GET', `/projects/${F}`);
const imp = async path => { const {media: m} = await call('POST', `/projects/${F}/media`, {sourcePath: path}); const ex = p.media.find(x => x.path === m.path); if (ex) return ex.id; p.media.push(m); return m.id; };
let seq = 0; const id = () => 'c' + Date.now().toString(36) + (seq++).toString(36) + Math.random().toString(36).slice(2, 6);
const TF = (ax = .5, ay = .5) => ({x: 0, y: 0, scale: 1, rotation: 0, opacity: 1, anchorX: ax, anchorY: ay});
const r3 = v => +(+v).toFixed(4);
const kfs = k => Object.fromEntries(Object.entries(k).map(([prop, arr]) => [prop, arr.map(([t, v, e]) => ({t: r3(t), v, ...(e ? {ease: e} : {})}))]));
const VID = p.media.find(m => m.kind === 'video').id;

// ---- 清理 ----
p.clips = [];
p.tracks = p.tracks.filter(t => !t.id.startsWith('X-') && !/^A[4-6]$/.test(t.id));
const iV = p.tracks.findIndex(t => t.id === 'V1');
p.tracks.splice(iV + 1, 0, ...meta.tracks.map(([tid, name, mt]) => ({id: tid, kind: 'module', moduleType: mt, name, locked: false, hidden: false, muted: false})));
const iA3 = p.tracks.findIndex(t => t.id === 'A3');
p.tracks.splice(iA3 + 1, 0, ...[4, 5, 6].map(i => ({id: `A${i}`, kind: 'audio', name: `A${i} 音效${i - 2}`, locked: false, hidden: false, muted: false})));
for (const t of p.tracks) { t.hidden = false; t.muted = false; }

// ---- V1 / A1 ----
meta.seg.forEach(([a, b, off], i) => {
  const lg = 'L' + id();
  p.clips.push({id: id(), trackId: 'V1', type: 'video', name: `视频 段${i + 1}`, mediaId: VID, start: r3(a + off), duration: r3(b - a), in: a, speed: 1, linkGroup: lg, transform: TF(), fit: 'cover'});
  p.clips.push({id: id(), trackId: 'A1', type: 'audio', name: `原声 段${i + 1}`, mediaId: VID, start: r3(a + off), duration: r3(b - a), in: a, speed: 1, volume: 1, linkGroup: lg, fadeIn: .03, fadeOut: .06});
});
meta.frz.forEach(([s, d, fr], i) => p.clips.push({id: id(), trackId: 'V1', type: 'freeze', name: `定格 选项${i + 1}`, mediaId: VID, start: s, duration: d, in: fr, transform: TF(), fit: 'cover'}));

// ---- 图层 ----
for (const L of meta.layers) {
  const mid = await imp(ROOT + L.file + '.png');
  p.clips.push({id: id(), trackId: L.track, type: 'image', name: L.name, start: L.start, duration: L.dur, mediaId: mid, fit: 'fill', transform: TF(L.ax, L.ay), keyframes: kfs(L.k)});
}

// ---- 音频 ----
const AD = ROOT + 'audio/';
const END = meta.end0 + meta.ed;
const bgm = await imp(AD + 'bgm_horror.wav');
p.clips.push({id: id(), trackId: 'A2', type: 'audio', name: 'BGM 微恐', mediaId: bgm, start: 0, duration: r3(END), in: 0, speed: 1, volume: .55, fadeIn: .3, fadeOut: .6});
const sfx = meta.sfx;
const lanes = {A3: 0, A4: 0, A5: 0, A6: 0};
for (const [f, s, v] of sfx.sort((a, b) => a[1] - b[1])) {
  const mid = await imp(AD + f + '.wav'); const md = p.media.find(x => x.id === mid)?.duration ?? 1;
  const d = Math.min(md, END - s); if (d <= .05) continue;
  const lane = Object.keys(lanes).find(k => lanes[k] <= s + 1e-3) ?? (() => { throw new Error('lanes full @' + s); })();
  p.clips.push({id: id(), trackId: lane, type: 'audio', name: f, mediaId: mid, start: r3(s), duration: r3(d), in: 0, speed: 1, volume: v}); lanes[lane] = s + d;
}
{ const used = new Set(p.clips.map(c => c.mediaId)); p.media = p.media.filter(m => used.has(m.id)); }
const r = await call('PUT', `/projects/${F}`, {project: p, revision});
console.log('ok', r.revision, 'clips', p.clips.length, 'tracks', p.tracks.length, 'media', p.media.length, 'end', END);
