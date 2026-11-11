// 多版本 timeline 示例（来自五音梗·毒舌講座迭代，旧版案例；只当写法参考）
// 目录和命名按 rules/工程交付.md：读 $P/包装素材_版本N/layers.json（gen.py 输出），写 $P/timeline_版本N.json：
//   视频+原声（素材/视频_N_1080.mp4）、产品 UI mp4（包装素材_产品UI/产品UI-划卡_版本N.mp4 / 产品UI-聊天_版本N.mp4）、图层、BGM 分段闪避、口播、音效。
//   格式见 scripts/render.py 文件头；不写 out，出片路径由 batch.sh 用 --out 给。
// 用法：P=<工程目录> VER=版本2 node to_timeline.mjs（放在 $P/脚本/ 里运行）
// 注意：BGM 闪避的 lvl() 固定 .11/.28、VOF 口播时长、SPEECH 区间都是该片的值；现行闪避做法见 rules/通用.md，按本片重写。
import fs from 'node:fs';
if (!process.env.P) throw new Error('先设置环境变量 P=<工程目录>');
const VER = process.env.VER ?? '';
if (!/^版本\d+$/.test(VER)) throw new Error('先设置环境变量 VER=版本N（如 版本1、版本2）');
const N = VER.slice(2);
const P = process.env.P.replace(/\\/g, '/').replace(/\/?$/, '/'), ROOT = P + `包装素材_${VER}/`;
const meta = JSON.parse(fs.readFileSync(ROOT + 'layers.json', 'utf8'));
import {execFileSync} from 'node:child_process';
const p = {tracks: [{id: 'V1'}, {id: 'A1'}, {id: 'A2'}, {id: 'A3'}], clips: [], media: []};
const imp = async path => { if (!fs.existsSync(path)) throw new Error('missing ' + path); let m = p.media.find(x => x.path === path); if (!m) { const d = +execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]).toString().trim() || 0; m = {id: path, path, duration: d}; p.media.push(m); } return m.id; };
let seq = 0; const id = () => 'c' + Date.now().toString(36) + (seq++).toString(36) + Math.random().toString(36).slice(2, 6);
const TF = (ax = .5, ay = .5) => ({x: 0, y: 0, scale: 1, rotation: 0, opacity: 1, anchorX: ax, anchorY: ay});
const r3 = v => +(+v).toFixed(4);
const kfs = k => Object.fromEntries(Object.entries(k).map(([prop, arr]) => [prop, arr.map(([t, v, e]) => ({t: r3(t), v, ...(e ? {ease: e} : {})}))]));
const dur = m => p.media.find(x => x.id === m).duration;

// ---- 轨道 ----
p.clips = [];
p.tracks = p.tracks.filter(t => !t.id.startsWith('X-') && !/^A[4-9]$/.test(t.id));
const iV = p.tracks.findIndex(t => t.id === 'V1');
p.tracks.splice(iV + 1, 0, ...meta.tracks.map(([tid, name, mt]) => ({id: tid, kind: 'module', moduleType: mt, name, locked: false, hidden: false, muted: false})));
const iA3 = p.tracks.findIndex(t => t.id === 'A3');
p.tracks.splice(iA3 + 1, 0, ...[4, 5, 6, 7, 8].map(i => ({id: `A${i}`, kind: 'audio', name: `A${i} 音效${i - 3}`, locked: false, hidden: false, muted: false})));
for (const t of p.tracks) { t.hidden = false; t.muted = false; if (t.id === 'A3') t.name = 'A3 竹马口播'; if (t.id === 'A2') t.name = 'A2 BGM'; }

// ---- V1 / A1：正片 + 产品UI ----
const vid = await imp(P + `素材/视频_${N}_1080.mp4`);
const shk = {x: [[0, 0]], y: [[0, 0]], scale: [[0, 1]]};
for (const t of meta.shake ?? []) {
  const X = [0, 16, -13, 10, -7, 4, -2, 0], Y = [0, -9, 8, -6, 4, -2, 1, 0];
  shk.scale.push([t - .01, 1], [t, 1.05], [t + .3, 1.05], [t + .45, 1]);
  X.forEach((v, i) => { shk.x.push([t + i / 24, v]); shk.y.push([t + i / 24, Y[i]]); });
}
const seg = (name, mid, start, d, extra = {}) => {
  const lg = 'L' + id();
  p.clips.push({id: id(), trackId: 'V1', type: 'video', name, mediaId: mid, start: r3(start), duration: r3(d), in: 0, speed: 1, linkGroup: lg, transform: TF(), fit: 'cover', ...extra});
  p.clips.push({id: id(), trackId: 'A1', type: 'audio', name: name + ' 声音', mediaId: mid, start: r3(start), duration: r3(d), in: 0, speed: 1, volume: 1, linkGroup: lg, fadeOut: .05});
};
// 转场：结尾推近手机（手机在胸前偏下）
{ const a = meta.push0, b = meta.end0, ez = [.2, .4, .5, .6, .75, .9, 1];
  shk.scale = shk.scale.filter(k => k[0] < a); shk.y = shk.y.filter(k => k[0] < a); shk.x = shk.x.filter(k => k[0] < a);
  shk.scale.push([a, 1]); shk.y.push([a, 0]); shk.x.push([a, 0]);
  ez.forEach((e, i) => { const t = a + (b - a) * (i + 1) / ez.length; const q = e * e; shk.scale.push([t, 1 + .75 * q]); shk.y.push([t, -330 * q]); }); }
seg(`视频_${N}（放大1080）`, vid, 0, meta.end0, {keyframes: kfs(shk)});
seg('产品UI-划卡', await imp(P + `包装素材_产品UI/产品UI-划卡_${VER}.mp4`), meta.sw0, meta.swd);
seg('产品UI-聊天', await imp(P + `包装素材_产品UI/产品UI-聊天_${VER}.mp4`), meta.ch0, meta.chd);

// ---- 图层 ----
for (const L of meta.layers) {
  const mid = await imp(ROOT + L.file + (L.ext ?? '.png'));
  const dd = r3(Math.min(L.dur, meta.end1 - L.start)); if (dd < 1 / 30 - 1e-3) continue;
  p.clips.push({id: id(), trackId: L.track, type: 'image', name: L.name, start: L.start, duration: dd, mediaId: mid, fit: 'fill', transform: TF(L.ax, L.ay), keyframes: kfs(L.k)});
}

// ---- 音频 ----
const AD = ROOT + 'audio/';
const END = r3(meta.end1), V0 = meta.vo0;
const bgm = await imp(AD + 'bgm_beat5.mp3');   // v4：新生成纯音乐（force_instrumental，按时间线）   // 结构：intro 0–4.6 | verse(drop) 4.6–12.3 | build 12.3–16 | outro 16–27.4
// drop 对齐「さっさと」(4.04)：in = 0.56 + t；片尾取曲子最后 3 s（以结尾 hit 收）
const SPEECH = [[.3, 2.4], [2.45, 3.95], [4.0, 5.5], [6.4, 8.0], [8.6, 12.0]];
const VOF = {p1: 2.77, p2: 4.48, p3: 1.58};
for (const [t, f] of meta.vos) SPEECH.push([t - .05, t + VOF[f] + .05]);
const snap = t => Math.round(t * 30) / 30;
const srcIn = t => t;
const lvl = (t, duck) => duck ? .11 : .28;
const cuts = new Set([0, meta.end0, meta.ec0, END]);
for (const [a, b] of SPEECH) { cuts.add(snap(a)); cuts.add(snap(b)); }
const cs = [...cuts].map(r3).sort((a, b) => a - b).filter((v, i, a) => i === 0 || v - a[i - 1] >= 1 / 30 - 1e-4);
for (let i = 0; i + 1 < cs.length; i++) {
  const a = cs[i], b = cs[i + 1], mid = (a + b) / 2;
  const duck = SPEECH.some(([s, e]) => mid > s && mid < e);
  p.clips.push({id: id(), trackId: 'A2', type: 'audio', name: `BGM 甜毒 ${duck ? '规避' : '回升'} ${a.toFixed(2)}`, mediaId: bgm, start: a, duration: r3(b - a), in: r3(srcIn(a)), speed: 1,
    volume: lvl(mid, duck), fadeIn: .06, fadeOut: b >= END - 1e-3 ? .6 : .06});
}
for (const [t, f] of meta.vos) { const vo = await imp(AD + f + '.wav');
  p.clips.push({id: id(), trackId: 'A3', type: 'audio', name: '竹马口播 ' + f, mediaId: vo, start: r3(t), duration: r3(Math.min(dur(vo), END - t)), in: 0, speed: 1, volume: 1}); }
const lanes = {A4: 0, A5: 0, A6: 0, A7: 0, A8: 0}; const cache = {};
for (const [f, s, v] of meta.sfx.sort((a, b) => a[1] - b[1])) {
  const mid = cache[f] ??= await imp(AD + f + '.wav'); const d = Math.min(dur(mid), END - s);
  const lane = Object.keys(lanes).find(k => lanes[k] <= s + 1e-3); if (!lane) { console.warn('drop sfx', f, s); continue; }
  p.clips.push({id: id(), trackId: lane, type: 'audio', name: f, mediaId: mid, start: r3(Math.max(0, s)), duration: r3(d), in: 0, speed: 1, volume: v}); lanes[lane] = s + d;
}
p.clips = p.clips.filter(c => { const ok = c.duration >= 1 / 30 - 1e-3; if (!ok) console.warn('drop short', c.trackId, c.name, c.start, c.duration); return ok; });
{ const used = new Set(p.clips.map(c => c.mediaId)); p.media = p.media.filter(m => used.has(m.id)); }
const order = p.tracks.map(t => t.id);
const vis = p.clips.filter(c => c.type !== 'audio').sort((a, b) => order.indexOf(a.trackId) - order.indexOf(b.trackId));
const tl = {size: [1080, 1920], fps: 30, duration: END,
  clips: vis.map(c => ({type: c.type, src: c.mediaId, start: c.start, duration: c.duration, in: c.in ?? 0, fit: c.fit, transform: c.transform, keyframes: c.keyframes})),
  audio: p.clips.filter(c => c.type === 'audio').map(c => ({src: c.mediaId, start: c.start, duration: c.duration, in: c.in ?? 0, volume: c.volume ?? 1, fadeIn: c.fadeIn ?? 0, fadeOut: c.fadeOut ?? 0}))};
fs.writeFileSync(P + `timeline_${VER}.json`, JSON.stringify(tl, null, 1));
console.log('timeline', vis.length, tl.audio.length, END);
