// 幂等写入工程：V1 弹幕烘焙视频分段 + 原视频定格 + 片尾背景，A1 原声，X-* 图层，A2 BGM，A3–A8 音效
import fs from 'node:fs';
const FOLDER = '2026年10月26日MM-JP-猫娘报恩';
const API = 'http://127.0.0.1:4400/api', F = encodeURIComponent(FOLDER);
const BASE = `F:/钟海明/2026/${FOLDER}/`, ROOT = `${BASE}包装素材v1/`, LAYD = `${ROOT}layers/`, AD = `${ROOT}audio/`;
const call = async (m, u, b) => { const r = await fetch(API + u, {method: m, headers: b ? {'content-type': 'application/json'} : {}, body: b ? JSON.stringify(b) : undefined}); const t = await r.text(); if (!r.ok) throw new Error(m + ' ' + u + ' ' + t); return JSON.parse(t); };
const meta = JSON.parse(fs.readFileSync(LAYD + 'layers.json', 'utf8'));
let {project: p, revision} = await call('GET', `/projects/${F}`);
const imp = async path => { const {media: m} = await call('POST', `/projects/${F}/media`, {sourcePath: path}); const ex = p.media.find(x => x.path === m.path); if (ex) return ex.id; p.media.push(m); return m.id; };
let seq = 0; const id = () => 'c' + Date.now().toString(36) + (seq++).toString(36) + Math.random().toString(36).slice(2, 6);
const TF = (ax = .5, ay = .5) => ({x: 0, y: 0, scale: 1, rotation: 0, opacity: 1, anchorX: ax, anchorY: ay});
const r3 = v => +(+v).toFixed(4);
const kfs = k => Object.fromEntries(Object.entries(k).map(([prop, arr]) => [prop, arr.map(([t, v, e]) => ({t: r3(t), v, ...(e ? {ease: e} : {})}))]));
const VB = await imp(ROOT + '猫娘报恩_弹幕_人声增强.mp4');   // 遮罩弹幕已烘焙
const VO = await imp(BASE + '猫娘报恩.mp4');         // 原视频（定格用）

p.clips = [];
p.tracks = p.tracks.filter(t => !t.id.startsWith('X-') && !/^A[4-9]$/.test(t.id));
const iV = p.tracks.findIndex(t => t.id === 'V1');
p.tracks.splice(iV + 1, 0, ...meta.tracks.map(([tid, name, mt]) => ({id: tid, kind: 'module', moduleType: mt, name, locked: false, hidden: false, muted: false})));
const iA3 = p.tracks.findIndex(t => t.id === 'A3');
p.tracks.splice(iA3 + 1, 0, ...[4, 5, 6, 7, 8].map(i => ({id: `A${i}`, kind: 'audio', name: `A${i} 音效${i - 2}`, locked: false, hidden: false, muted: false})));
for (const t of p.tracks) { t.hidden = false; t.muted = false; }

meta.seg.forEach(([a, b, off], i) => {
  const lg = 'L' + id(), nm = `第${i + 1}幕`;
  p.clips.push({id: id(), trackId: 'V1', type: 'video', name: `${nm}（遮罩弹幕+人声增强）`, mediaId: VB, start: r3(a + off), duration: r3(b - a), in: a, speed: 1, linkGroup: lg, transform: TF(), fit: 'cover'});
  p.clips.push({id: id(), trackId: 'A1', type: 'audio', name: `原声 ${nm}`, mediaId: VB, start: r3(a + off), duration: r3(b - a), in: a, speed: 1, volume: 1, linkGroup: lg, fadeIn: .03, fadeOut: .06});
});
meta.frz.forEach(([s, d, fr], i) => p.clips.push({id: id(), trackId: 'V1', type: 'freeze', name: `定格 选项${i + 1}`, mediaId: VO, start: s, duration: d, in: fr, transform: TF(), fit: 'cover'}));

for (const L of meta.layers) {
  const mid = await imp(LAYD + L.file + (L.ext ?? '.png'));
  p.clips.push({id: id(), trackId: L.track, type: 'image', name: L.name, start: L.start, duration: L.dur, mediaId: mid, fit: 'fill', transform: TF(L.ax, L.ay), keyframes: kfs(L.k)});
}

const END = meta.end0 + meta.ed;
const bgm = await imp(AD + 'bgm_v2_选项节奏.wav');
p.clips.push({id: id(), trackId: 'A2', type: 'audio', name: 'BGM v2（选项节奏+人声闪避）', mediaId: bgm, start: 0, duration: r3(END), in: 0, speed: 1, volume: .6, fadeIn: 0, fadeOut: .3});
const lanes = {A3: 0, A4: 0, A5: 0, A6: 0, A7: 0, A8: 0};
for (const [f, s, v] of meta.sfx.sort((a, b) => a[1] - b[1])) {
  const mid = await imp(AD + f + '.wav'); const md = p.media.find(x => x.id === mid)?.duration ?? 1;
  const d = Math.min(md, END - s); if (d <= .05) continue;
  const lane = Object.keys(lanes).find(k => lanes[k] <= s + 1e-3) ?? (() => { throw new Error('lanes full @' + s); })();
  p.clips.push({id: id(), trackId: lane, type: 'audio', name: f, mediaId: mid, start: r3(s), duration: r3(d), in: 0, speed: 1, volume: v}); lanes[lane] = s + d;
}
{ const used = new Set(p.clips.map(c => c.mediaId)); p.media = p.media.filter(m => used.has(m.id)); }
const r = await call('PUT', `/projects/${F}`, {project: p, revision});
console.log('ok', r.revision, 'clips', p.clips.length, 'tracks', p.tracks.length, 'media', p.media.length, 'end', END);
