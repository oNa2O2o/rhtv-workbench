// 幂等写入工程：V1 分段（两条视频）+ 定格 + 片尾背景，A1 原声分段，X-* 图层（layers.json），A2 BGM，A3–A6 音效
import fs from 'node:fs';
const FOLDER = '2026年10月21日MM-JP-贞操逆转+上门讨债';
const API = 'http://127.0.0.1:4400/api', F = encodeURIComponent(FOLDER);
const VER = process.env.VER;   // 迭代版本 1|2：图层取 包装素材_版本N，视频换成 迭代素材 里的新角色
const BASE = `F:/钟海明/2026/${FOLDER}/`;
const ROOT = VER ? `${BASE}包装素材_版本${VER}/` : `${BASE}包装素材v3/`;
const call = async (m, u, b) => { const r = await fetch(API + u, {method: m, headers: b ? {'content-type': 'application/json'} : {}, body: b ? JSON.stringify(b) : undefined}); const t = await r.text(); if (!r.ok) throw new Error(m + ' ' + u + ' ' + t); return JSON.parse(t); };
const meta = JSON.parse(fs.readFileSync(ROOT + 'layers.json', 'utf8'));
let {project: p, revision} = await call('GET', `/projects/${F}`);
const imp = async path => { const {media: m} = await call('POST', `/projects/${F}/media`, {sourcePath: path}); const ex = p.media.find(x => x.path === m.path); if (ex) return ex.id; p.media.push(m); return m.id; };
let seq = 0; const id = () => 'c' + Date.now().toString(36) + (seq++).toString(36) + Math.random().toString(36).slice(2, 6);
const TF = (ax = .5, ay = .5) => ({x: 0, y: 0, scale: 1, rotation: 0, opacity: 1, anchorX: ax, anchorY: ay});
const r3 = v => +(+v).toFixed(4);
const kfs = k => Object.fromEntries(Object.entries(k).map(([prop, arr]) => [prop, arr.map(([t, v, e]) => ({t: r3(t), v, ...(e ? {ease: e} : {})}))]));
const VID = {A: 'mmvi89tm04ezx4fx', B: 'mmvi89tx64f0d851'};
if (VER) { const vv = {1: ['迭代素材/版本1/视频 (74).mp4', '迭代素材/版本1/视频 (75).mp4'], 2: ['迭代素材/版本2/视频 (76).mp4', '迭代素材/版本2/视频 (77).mp4']}[VER]; VID.A = await imp(BASE + vv[0]); VID.B = await imp(BASE + vv[1]); }
for (const v of Object.values(VID)) if (!p.media.find(m => m.id === v)) throw new Error('missing video media ' + v);

// ---- 清理 ----
p.clips = [];
p.tracks = p.tracks.filter(t => !t.id.startsWith('X-') && !/^A[4-9]$/.test(t.id));
const iV = p.tracks.findIndex(t => t.id === 'V1');
p.tracks.splice(iV + 1, 0, ...meta.tracks.map(([tid, name, mt]) => ({id: tid, kind: 'module', moduleType: mt, name, locked: false, hidden: false, muted: false})));
const iA3 = p.tracks.findIndex(t => t.id === 'A3');
p.tracks.splice(iA3 + 1, 0, ...[4, 5, 6, 7, 8].map(i => ({id: `A${i}`, kind: 'audio', name: `A${i} 音效${i - 2}`, locked: false, hidden: false, muted: false})));
for (const t of p.tracks) { t.hidden = false; t.muted = false; }

// ---- V1 / A1 ----
meta.seg.forEach(([v, a, b, off], i) => {
  // 静音区（模型生成的错误人声）：视频照常，该段不放原声
  const cuts = (meta.mute ?? []).filter(([mv, ma, mb]) => mv === v && ma < b && mb > a).sort((x, y) => x[1] - y[1]);
  const pieces = []; let cur = a;
  for (const [, ma, mb] of cuts) { if (ma > cur) pieces.push([cur, ma, false]); pieces.push([Math.max(cur, ma), Math.min(b, mb), true]); cur = Math.min(b, mb); }
  if (cur < b) pieces.push([cur, b, false]);
  pieces.forEach(([pa, pb, muted], j) => {
    const lg = muted ? undefined : 'L' + id(), nm = `段${i + 1}${pieces.length > 1 ? '-' + (j + 1) : ''}${muted ? '（静音）' : ''}`;
    p.clips.push({id: id(), trackId: 'V1', type: 'video', name: `视频${v} ${nm}`, mediaId: VID[v], start: r3(pa + off), duration: r3(pb - pa), in: pa, speed: 1, ...(lg ? {linkGroup: lg} : {}), transform: TF(), fit: 'cover'});
    if (!muted) p.clips.push({id: id(), trackId: 'A1', type: 'audio', name: `原声 ${nm}`, mediaId: VID[v], start: r3(pa + off), duration: r3(pb - pa), in: pa, speed: 1, volume: 1, linkGroup: lg, fadeIn: .03, fadeOut: .06});
  });
});
const FN = ['开头', '选项1', '选项2', '选项3+AI聊天'];
meta.frz.forEach(([v, s, d, fr], i) => p.clips.push({id: id(), trackId: 'V1', type: 'freeze', name: `定格 ${FN[i] ?? i}`, mediaId: VID[v], start: s, duration: d, in: fr, transform: TF(), fit: 'cover'}));

// ---- 图层 ----
for (const L of meta.layers) {
  const mid = await imp(ROOT + L.file + (L.ext ?? '.png'));
  p.clips.push({id: id(), trackId: L.track, type: 'image', name: L.name, start: L.start, duration: L.dur, mediaId: mid, fit: 'fill', transform: TF(L.ax, L.ay), keyframes: kfs(L.k)});
}

// ---- 音频 ----
const AD = `${BASE}包装素材v3/audio/`;
const END = meta.end0 + meta.ed;
const bgm = await imp(AD + 'bgm_v5.wav');
if (!VER) p.clips.push({id: id(), trackId: 'A2', type: 'audio', name: 'BGM v5 鼓点递进', mediaId: bgm, start: 0, duration: r3(END), in: 0, speed: 1, volume: .42, fadeIn: .2, fadeOut: .6});
else {
  // 与已交付成品一致：选项段保留悬疑 BGM（取自 bgm_v5 的悬疑段），全片叠加用户配乐 成品/音乐.MP3（音量 1.0，从 0 秒起）
  [[17.6, 0], [37.8, 1], [56.6, 2]].forEach(([src, i]) => { const [, s, d] = meta.frz[i + 1]; const dd = i === 2 ? 5.4 : d;
    p.clips.push({id: id(), trackId: 'A2', type: 'audio', name: `BGM 选项${i + 1}`, mediaId: bgm, start: r3(s), duration: r3(dd), in: src, speed: 1, volume: .42, fadeIn: .15, fadeOut: .35}); });
  if (!p.tracks.find(t => t.id === 'A9')) p.tracks.push({id: 'A9', kind: 'audio', name: 'A9 用户配乐', locked: false, hidden: false, muted: false});
  const mu = await imp(BASE + '成品/音乐.MP3'); const md = p.media.find(x => x.id === mu)?.duration ?? END;
  p.clips.push({id: id(), trackId: 'A9', type: 'audio', name: '用户配乐 音乐.MP3', mediaId: mu, start: 0, duration: r3(Math.min(md, END)), in: 0, speed: 1, volume: 1, fadeOut: md > END ? .8 : 0});
}
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
