// MiraiMind JP 尾板 v4 —— 一镜到底：光点 → 角色网络 → 三角色对比 → 景深螺旋长廊（百万）→ Logo/CTA
// 3D 厚度液态玻璃卡片 + 景深（离焦模糊）。renderFrame(t) 确定性渲染，逐帧导出。
(() => {
const CFG = window.ENDCARD_CONFIG;
const W = 1080, H = 1920, F = 1250, CY = H * .40, SS = 2;   // SS: 超采样倍数
let FZ = 1;   // 镜头焦距冲击（推镜/光速）
const cv = document.getElementById("cv"), ctx = cv.getContext("2d");
const BG = "#060609";
const GRAD = [[0, "#5CE6F6"], [0.38, "#CDF46C"], [0.7, "#F6A3E0"], [1, "#A98BFF"]];
const GRAD_TXT = [[0, "#7DEBFA"], [0.5, "#F2A9E4"], [1, "#B49AFF"]];
const PG = [[0, "#5DD5E8"], [0.5, "#94A6F0"], [1, "#C77DF5"]];
const PAL = ["#5CE6F6", "#CDF46C", "#F6A3E0", "#A98BFF"];

// ---------- utils ----------
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, k) => a + (b - a) * k;
const prog = (t, a, d) => clamp((t - a) / d);
const eio = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
const eout = k => 1 - Math.pow(1 - k, 3);
const eback = k => { const c = 1.6; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
const ss = (a, b, x) => { const k = clamp((x - a) / (b - a)); return k * k * (3 - 2 * k); };
let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const grad = (x0, y0, x1, y1, stops = GRAD) => { const g = ctx.createLinearGradient(x0, y0, x1, y1); stops.forEach(s => g.addColorStop(s[0], s[1])); return g; };
const hex = (h, a) => { const n = parseInt(h.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; };
function loadImg(src) { return new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; }); }
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };

// ---------- card textures：液态玻璃卡（毛玻璃边框 + 内嵌角色图 + 产品同款按钮） ----------
const CW = 540, CH = 960, CR = 78, TH = 44, RIM = 16;
const PILL = { x: 46, w: 448, y: CH - 60 - 64, h: 64 };
function bakeCard(img) {
  const S = 1.5, c = document.createElement("canvas"); c.width = CW * S; c.height = CH * S;
  const g = c.getContext("2d"); g.scale(S, S);
  const r = Math.max(CW / img.width, CH / img.height), w = img.width * r, h = img.height * r;
  // 毛玻璃底：同图放大模糊提亮
  g.save(); g.filter = "blur(22px) brightness(1.35) saturate(1.4)"; g.drawImage(img, (CW - w * 1.15) / 2, (CH - h * 1.15) * .3, w * 1.15, h * 1.15); g.restore();
  g.fillStyle = "rgba(255,255,255,.16)"; g.fillRect(0, 0, CW, CH);
  // 内嵌清晰图
  g.save(); g.beginPath(); g.roundRect(RIM, RIM, CW - RIM * 2, CH - RIM * 2, CR - RIM); g.clip();
  g.drawImage(img, (CW - w) / 2, (CH - h) * .3, w, h);
  const vg = g.createLinearGradient(0, CH * .6, 0, CH); vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, "rgba(0,0,0,.6)");
  g.fillStyle = vg; g.fillRect(0, 0, CW, CH);
  g.restore();
  // 内斜面：左上亮、右下暗
  g.save(); g.beginPath(); g.roundRect(RIM, RIM, CW - RIM * 2, CH - RIM * 2, CR - RIM);
  g.lineWidth = 3; const bg = g.createLinearGradient(0, 0, CW, CH); bg.addColorStop(0, "rgba(255,255,255,.9)"); bg.addColorStop(.45, "rgba(255,255,255,.12)"); bg.addColorStop(1, "rgba(0,0,0,.5)");
  g.strokeStyle = bg; g.stroke(); g.restore();
  // 外缘彩虹色散
  g.save(); g.beginPath(); g.roundRect(1.5, 1.5, CW - 3, CH - 3, CR - 1.5); g.lineWidth = 3;
  const og = g.createLinearGradient(0, 0, CW, CH); GRAD.forEach(s => og.addColorStop(s[0], s[1])); g.strokeStyle = og; g.globalAlpha = .85; g.stroke();
  g.beginPath(); g.roundRect(5, 5, CW - 10, CH - 10, CR - 5); g.lineWidth = 2; g.strokeStyle = "rgba(255,255,255,.35)"; g.stroke(); g.restore();
  // 玻璃上半部弧形反光
  g.save(); g.beginPath(); g.roundRect(0, 0, CW, CH, CR); g.clip();
  const sh = g.createLinearGradient(0, 0, CW * .6, CH * .45); sh.addColorStop(0, "rgba(255,255,255,.18)"); sh.addColorStop(.5, "rgba(255,255,255,.04)"); sh.addColorStop(.51, "rgba(255,255,255,0)");
  g.fillStyle = sh; g.fillRect(0, 0, CW, CH); g.restore();
  // 产品同款渐变按钮
  const p = PILL, pg = g.createLinearGradient(p.x, p.y, p.x + p.w, p.y + p.h); PG.forEach(s => pg.addColorStop(s[0], s[1]));
  g.beginPath(); g.roundRect(p.x, p.y, p.w, p.h, p.h / 2); g.fillStyle = pg; g.fill();
  g.font = "900 29px NJ"; g.letterSpacing = "3px"; g.textAlign = "center"; g.fillStyle = "#1c1c26";
  g.fillText("チャット", CW / 2 + 1.5, p.y + p.h / 2 + 10);
  // 离焦层级
  const lv = [c];
  for (const [sc, b] of [[.3, 6], [.12, 6]]) {
    const d = document.createElement("canvas"); d.width = Math.round(c.width * sc); d.height = Math.round(c.height * sc);
    const dg = d.getContext("2d"); dg.filter = `blur(${b}px)`; dg.drawImage(c, 0, 0, d.width, d.height); lv.push(d);
  }
  return lv;
}

// ---------- assets ----------
const A = {};
async function init() {
  const fl = [["NJ", CFG.fonts.regular, 400], ["NJ", CFG.fonts.medium, 500], ["NJ", CFG.fonts.bold, 700], ["NJ", CFG.fonts.black, 900]];
  for (const [fam, url, wt] of fl) { const f = new FontFace(fam, `url("${url}")`, { weight: String(wt) }); await f.load(); document.fonts.add(f); }
  A.cards = (await Promise.all(CFG.cards.map(loadImg))).map(bakeCard);
  A.icon = await loadImg(CFG.logoIcon); A.word = await loadImg(CFG.logoWord); A.badges = await loadImg(CFG.badges);
  A.grain = document.createElement("canvas"); A.grain.width = 540; A.grain.height = 960;
  const g = A.grain.getContext("2d"), id = g.createImageData(540, 960);
  for (let i = 0; i < id.data.length; i += 4) { const v = rnd() * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; }
  g.putImageData(id, 0, 0);
  buildWorld();
  window.__ready = true;
}

// ---------- world ----------
const HUB = { x: 0, y: -60, z: 3000 };
const HERO_POS = [[-720, -150, 2650, .2], [260, 140, 3350, -.14], [1180, -120, 2750, -.22]];
const EXTRA_POS = [[-1650, -1000, 4300, .3], [950, -1250, 4700, -.25], [-350, 1150, 4500, .15], [2150, 900, 4900, -.3], [-2150, 650, 3700, .28], [450, -700, 5900, -.1], [1900, -1350, 3900, -.2], [-1300, 1500, 5600, .2], [-2550, -250, 5200, .3], [2650, -250, 5500, -.3], [-750, -1700, 5100, .1], [1300, 1700, 5300, -.15], [-2350, -1750, 6300, .25], [2500, 1800, 6100, -.25], [-2900, 1300, 6400, .3], [100, 2100, 6600, 0], [3000, -1100, 6600, -.3], [-1100, -2300, 6900, .15], [1500, -2400, 7000, -.15], [-3100, -600, 7200, .3]];
const TUN = { z0: 2800, step: 300, dth: .74, R: 1300, N: 140 };
let net = [], netLinks = [], tunnel = [], motes = [];
function buildWorld() {
  net = [];
  CFG.heroes.forEach((h, i) => { const p = HERO_POS[i]; net.push({ img: h.card, x: p[0], y: p[1], z: p[2], ry: p[3], hero: i, tint: h.tint, bloom: .55 + i * .22 }); });
  CFG.extras.forEach((c, i) => { const p = EXTRA_POS[i % EXTRA_POS.length]; net.push({ img: c, x: p[0], y: p[1], z: p[2], ry: p[3], hero: -1, bloom: 1.0 + i * .085 }); });
  netLinks = [];
  net.forEach((c, i) => netLinks.push({ a: HUB, b: c, t0: c.bloom - .45 }));
  netLinks.push({ a: net[0], b: net[1], t0: 2.4, chain: 1 }, { a: net[1], b: net[2], t0: 2.6, chain: 1 }, { a: net[3], b: net[0], t0: 2.2 }, { a: net[4], b: net[2], t0: 2.3 }, { a: net[7], b: net[0], t0: 2.5 }, { a: net[6], b: net[1], t0: 2.7 }, { a: net[9], b: net[2], t0: 2.5 }, { a: net[11], b: net[7], t0: 2.6 }, { a: net[12], b: net[6], t0: 2.7 }, { a: net[13], b: net[3], t0: 2.75 }, { a: net[14], b: net[5], t0: 2.8 }, { a: net[15], b: net[8], t0: 2.85 }, { a: net[16], b: net[14], t0: 2.7 }, { a: net[17], b: net[12], t0: 2.75 }, { a: net[18], b: net[5], t0: 2.8 }, { a: net[19], b: net[9], t0: 2.85 }, { a: net[20], b: net[11], t0: 2.9 }, { a: net[21], b: net[6], t0: 2.9 }, { a: net[22], b: net[15], t0: 2.95 });
  seed = 21;
  tunnel = [];
  for (let i = 0; i < TUN.N; i++) {
    const th = i * TUN.dth + .4, R = TUN.R * (1 + (rnd() - .5) * .18);
    const x = Math.cos(th) * R, y = Math.sin(th) * R;
    tunnel.push({ img: (i * 7 + 3) % A.cards.length, x, y, z: TUN.z0 + i * TUN.step, ry: clamp(-x / R * .55, -.55, .55), i });
  }
  net.forEach((c, i) => { tunnel[i].img = c.img; tunnel[i].net = i; });
  seed = 5; motes = [];
  for (let i = 0; i < 260; i++) motes.push({ x: (rnd() * 2 - 1) * 2600, y: (rnd() * 2 - 1) * 2600, z: rnd() * 19000, r: 4 + rnd() * 9, c: PAL[i % 4], ph: rnd() * 6 });
}

// ---------- camera：带时间的 Catmull-Rom（速度连续，一镜到底） ----------
const hero = i => net[i];
function heroShot(i, drift, hold) {
  const c = hero(i), hi = CFG.heroes[i].angle === "high";
  return { p: [c.x + 70 - drift * 50, c.y + (hi ? -430 : 420), c.z - 1330 + drift * 130], t: [c.x, c.y + (hi ? 60 : -60), c.z], r: (i - 1) * .035 * (1 - drift), hold };
}
let KEYS;
function buildKeys() {
  const K = [
    [0.0, { p: [0, -60, 2560], t: [0, -60, 3000], r: 0 }],
    [1.2, { p: [-20, -90, 1900], t: [0, -60, 3000], r: -.02 }],
    [2.95, { p: [-120, -160, -150], t: [-60, -40, 3200], r: -.04 }],
    [3.33, heroShot(0, 0, 1)], [4.3, heroShot(0, 1)],
    [4.53, heroShot(1, 0, 1)], [5.45, heroShot(1, 1)],
    [5.73, heroShot(2, 0, 1)], [6.62, heroShot(2, 1)],
    [8.75, { p: [120, 110, -2400], t: [120, -10, 3900], r: -.05, stop: 1 }],
    [9.45, { p: [260, 30, 2300], t: [0, 0, 11000], r: .06 }],
    [10.3, { p: [-380, 260, 6600], t: [200, -120, 19000], r: .5 }],
    [11.15, { p: [420, -300, 14500], t: [-150, 120, 30000], r: 1.15 }],
    [11.85, { p: [-150, 120, 23000], t: [0, 0, 40000], r: 1.7 }],
    [12.6, { p: [0, 0, 28000], t: [0, 0, 46000], r: 1.95 }],
    [13.3, { p: [0, 0, 28700], t: [0, 0, 46000], r: 2.05 }],
    [17.3, { p: [0, 0, 29800], t: [0, 0, 46000], r: 2.28 }],
  ];
  KEYS = K.map(([t, k]) => ({ t, v: [...k.p, ...k.t, k.r], hold: !!k.hold, stop: !!k.stop }));
}
function camKeys(t) {
  if (!KEYS) buildKeys();
  const n = KEYS.length;
  if (t <= KEYS[0].t) return KEYS[0].v;
  if (t >= KEYS[n - 1].t) return KEYS[n - 1].v;
  let i = 0; while (KEYS[i + 1].t < t) i++;
  const k0 = KEYS[Math.max(0, i - 1)], k1 = KEYS[i], k2 = KEYS[i + 1], k3 = KEYS[Math.min(n - 1, i + 2)];
  const h = k2.t - k1.t, u = (t - k1.t) / h;
  const h00 = 2 * u ** 3 - 3 * u ** 2 + 1, h10 = u ** 3 - 2 * u ** 2 + u, h01 = -2 * u ** 3 + 3 * u ** 2, h11 = u ** 3 - u ** 2;
  // 停留段（hold）首尾用匀速漂移的切线：停在卡上时镜头仍缓慢推进，甩镜段两端自然缓入缓出
  const tan = (ix, j) => {
    const K0 = KEYS[ix], Kp = KEYS[ix - 1], Kn = KEYS[ix + 1];
    if (!Kn || ix === 0 || K0.stop) return 0;
    if (K0.hold) return (Kn.v[j] - K0.v[j]) / (Kn.t - K0.t);
    if (Kp && Kp.hold) return (K0.v[j] - Kp.v[j]) / (K0.t - Kp.t);
    return (Kn.v[j] - Kp.v[j]) / (Kn.t - Kp.t) * .85;
  };
  if (k2.stop) {   // 拉远蓄力段：五次缓动，起步加速度接近 0，不会被“猛拽”
    const S = u ** 3 * (10 - 15 * u + 6 * u * u), G = u * (1 - u) ** 3, G2 = u ** 3 * (u - 1);
    return k1.v.map((_, j) => k1.v[j] + (k2.v[j] - k1.v[j]) * S + tan(i, j) * h * G);
  }
  return k1.v.map((_, j) => {
    const m1 = tan(i, j), m2 = tan(i + 1, j);
    return h00 * k1.v[j] + h10 * h * m1 + h01 * k2.v[j] + h11 * h * m2;
  });
}
// 第三张卡之后整段一条速度曲线（积分得到位置）：拉远蓄力 → 弹弓式回冲（速度直接穿过 0，不停顿）→ 长廊加速 → 平滑减速
const CT0 = 6.62, TL0 = 7.9, PULL = 3300, CB = .9, CA = 650, V1 = 6000, TAU = .32, TD = 11.8, DD = 1.4;
let CTAB = null;
function camVz(t) {
  const f = 1 - ss(TD, TD + DD, t), u = t - TL0;
  const pull = -PULL * ss(CT0, 7.3, t) * (1 - ss(7.6, 8.15, t));
  const fwd = u > 0 ? (V1 * (1 - Math.exp(-u / TAU)) * ss(0, .3, u) + CA * CB * (Math.exp(CB * Math.max(0, t - 8.75)) - 1)) : 0;
  return (146 * (1 - ss(CT0, 6.95, t)) + pull + fwd) * f + 90 * (1 - f);
}
function buildCam() {
  const v0 = camKeys(CT0), dt = 1 / 1200, n = Math.ceil((17.4 - CT0) / dt);
  const zs = new Float64Array(n + 1), rs = new Float64Array(n + 1); zs[0] = v0[2]; rs[0] = v0[6];
  for (let k = 0; k < n; k++) {
    const t = CT0 + (k + .5) * dt, f = 1 - ss(TD, TD + DD, t), u = Math.max(0, t - 8.75);
    const vr = -.12 * ss(CT0, 7.3, t) * (1 - ss(7.9, 8.6, t)) + (.25 * ss(TL0, TL0 + .6, t) + .05 * CB * (Math.exp(CB * u) - 1)) * f + .03 * (1 - f);
    zs[k + 1] = zs[k] + camVz(t) * dt; rs[k + 1] = rs[k] + vr * dt;
  }
  CTAB = { v0, dt, zs, rs };
}
function camAt(t) {
  if (t < CT0) return camKeys(t);
  if (!CTAB) buildCam();
  const { v0, dt, zs, rs } = CTAB, u = t - CT0, fi = Math.min(u / dt, zs.length - 1.001), i = Math.floor(fi), fr = fi - i;
  const z = lerp(zs[i], zs[i + 1], fr), r = lerp(rs[i], rs[i + 1], fr);
  // 侧向：从第三张卡的机位平滑滑到长廊中轴，拉远时略微抬高拉开视野；长廊里缓慢摇摆
  const uL = t - TL0, w = ss(.3, 1.6, uL) * (1 - ss(TD, TD + DD, t)), cen = 1 - ss(CT0, 9.2, t);
  const x = (v0[0] - 56 * Math.min(u, .4)) * cen + 260 * Math.sin(uL * 1.4) * w;
  const y = v0[1] * cen - 260 * Math.sin(Math.PI * ss(CT0, 9.0, t)) + 200 * Math.sin(uL * 1.1 + .7) * w - 200 * Math.sin(.7) * w;
  // 视线：先保持看着卡片群，再平滑转向长廊深处
  const bk = ss(7.3, 9.0, t), tz = z + 10000;
  return [x, y, z, lerp(v0[3] * (1 - ss(CT0, 7.6, t)), x * .3, bk), lerp(v0[4] * (1 - ss(CT0, 7.6, t)), y * .3, bk), lerp(v0[5], tz, bk), r];
}
let CP = [0, 0, 0], CF = [0, 0, 1], CRt = [1, 0, 0], CD = [0, 1, 0], FOCUS = 1300, APER = 26;
function setCam(v) {
  CP = [v[0], v[1], v[2]]; CF = norm(sub([v[3], v[4], v[5]], CP));
  let r = norm(cross([0, 1, 0], CF)), d = cross(CF, r); const cr = Math.cos(v[6]), sr = Math.sin(v[6]);
  CRt = [r[0] * cr + d[0] * sr, r[1] * cr + d[1] * sr, r[2] * cr + d[2] * sr];
  CD = [d[0] * cr - r[0] * sr, d[1] * cr - r[1] * sr, d[2] * cr - r[2] * sr];
}
function proj(x, y, z) {
  const v = [x - CP[0], y - CP[1], z - CP[2]], dz = dot(v, CF), s = F / dz;
  const sf = s * FZ;
  return { x: W / 2 + dot(v, CRt) * sf, y: CY + dot(v, CD) * sf, dz, s: sf };
}
const blurPx = dz => APER * F * Math.abs(1 / FOCUS - 1 / Math.max(dz, 1)) * .6;

// ---------- 3D 玻璃卡 ----------
const RING = (() => { // 圆角矩形轮廓（局部坐标）+ 外法线
  const pts = [], w = CW / 2, h = CH / 2, r = CR, seg = 5;
  const corner = (cx, cy, a0) => { for (let k = 0; k <= seg; k++) { const a = a0 + k / seg * Math.PI / 2; pts.push({ x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r, nx: Math.cos(a), ny: Math.sin(a) }); } };
  corner(w - r, -h + r, -Math.PI / 2); corner(w - r, h - r, 0); corner(-w + r, h - r, Math.PI / 2); corner(-w + r, -h + r, Math.PI);
  return pts;
})();
function toWorld(c, lx, ly, lz, sc) {
  const cs = Math.cos(c.ry), sn = Math.sin(c.ry); lx *= sc; ly *= sc; lz *= sc;
  return [c.x + lx * cs - lz * sn, c.y + ly, c.z + lx * sn + lz * cs];
}
function triImg(img, s0, s1, s2, d0, d1, d2) {
  const [u0, v0] = s0, [u1, v1] = s1, [u2, v2] = s2;
  // 轻微外扩，消除三角形接缝
  const cx = (d0.x + d1.x + d2.x) / 3, cy = (d0.y + d1.y + d2.y) / 3, ex = p => { const dx = p.x - cx, dy = p.y - cy, l = Math.hypot(dx, dy) || 1; return [p.x + dx / l * .7, p.y + dy / l * .7]; };
  const [x0, y0] = ex(d0), [x1, y1] = ex(d1), [x2, y2] = ex(d2);
  const den = (u1 - u0) * (v2 - v0) - (u2 - u0) * (v1 - v0); if (Math.abs(den) < 1e-9) return;
  const a = ((d1.x - d0.x) * (v2 - v0) - (d2.x - d0.x) * (v1 - v0)) / den;
  const b = ((d1.y - d0.y) * (v2 - v0) - (d2.y - d0.y) * (v1 - v0)) / den;
  const c = ((d2.x - d0.x) * (u1 - u0) - (d1.x - d0.x) * (u2 - u0)) / den;
  const d = ((d2.y - d0.y) * (u1 - u0) - (d1.y - d0.y) * (u2 - u0)) / den;
  ctx.save(); ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.lineTo(x2, y2); ctx.closePath(); ctx.clip();
  ctx.transform(a, b, c, d, d0.x - a * u0 - c * v0, d0.y - b * u0 - d * v0);
  ctx.drawImage(img, 0, 0); ctx.restore();
}
function drawFace(tex, c, sc, nx, ny) {
  const tw = tex.width, th = tex.height, P = [];
  for (let j = 0; j <= ny; j++) { const row = []; for (let i = 0; i <= nx; i++) { const w = toWorld(c, (i / nx - .5) * CW, (j / ny - .5) * CH, -TH / 2, sc); row.push(proj(w[0], w[1], w[2])); } P.push(row); }
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
    const u0 = i / nx * tw, u1 = (i + 1) / nx * tw, v0 = j / ny * th, v1 = (j + 1) / ny * th;
    triImg(tex, [u0, v0], [u1, v0], [u0, v1], P[j][i], P[j][i + 1], P[j + 1][i]);
    triImg(tex, [u1, v0], [u1, v1], [u0, v1], P[j][i + 1], P[j + 1][i + 1], P[j + 1][i]);
  }
}
// opt: alpha, scale, dim, tint, glow, focusBoost
function drawCard(c, opt = {}) {
  const sc = opt.scale ?? 1, alpha = opt.alpha ?? 1;
  if (alpha <= .004 || sc <= .002) return null;
  const ctr = proj(c.x, c.y, c.z); if (ctr.dz < 160) return null;
  const front = RING.map(p => { const w = toWorld(c, p.x, p.y, -TH / 2, sc); return proj(w[0], w[1], w[2]); });
  if (front.some(p => p.dz < 60)) return null;
  let minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9;
  front.forEach(p => { minx = Math.min(minx, p.x); maxx = Math.max(maxx, p.x); miny = Math.min(miny, p.y); maxy = Math.max(maxy, p.y); });
  if (maxx < -80 || minx > W + 80 || maxy < -80 || miny > H + 80) return null;
  const sw = maxx - minx, shh = maxy - miny, dz = ctr.dz;
  let a = alpha; if (dz < 700) a *= clamp((dz - 160) / 540);
  const bp = blurPx(dz) * (opt.blurMul ?? 1);
  const lv = clamp(bp / 11, 0, 2), big = shh > 70;
  const tint = opt.tint || null;
  ctx.save(); ctx.globalAlpha = a;
  // 投影/背光
  if (big) {
    const gl = ctx.createRadialGradient(ctr.x, ctr.y, 0, ctr.x, ctr.y, shh * .75);
    gl.addColorStop(0, tint ? hex(tint, .32 * (opt.glow ?? .6)) : `rgba(150,130,255,${.14 * (opt.glow ?? .6)})`); gl.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = gl; ctx.fillRect(ctr.x - shh, ctr.y - shh, shh * 2, shh * 2);
  }
  // 厚度：侧面
  if (big) {
    const back = RING.map(p => { const w = toWorld(c, p.x, p.y, TH / 2, sc); return proj(w[0], w[1], w[2]); });
    const cs = Math.cos(c.ry), sn = Math.sin(c.ry), quads = [];
    for (let k = 0; k < RING.length; k++) {
      const k2 = (k + 1) % RING.length, p = RING[k], q = RING[k2];
      const nx = (p.nx + q.nx) / 2, ny = (p.ny + q.ny) / 2, nW = [nx * cs, ny, nx * sn];
      const mid = toWorld(c, (p.x + q.x) / 2, (p.y + q.y) / 2, 0, sc);
      if (dot(nW, sub(CP, mid)) <= 0) continue;
      quads.push({ k, k2, nW, d: (front[k].dz + back[k].dz) / 2 });
    }
    quads.sort((u, v) => v.d - u.d);
    const L = norm([-.5, -.8, -.35]);
    for (const qd of quads) {
      const { k, k2 } = qd, lit = clamp(.35 + .65 * dot(qd.nW, L) * -1 * -1);
      const base = tint || PAL[Math.floor(((k / RING.length) * 4 + .5)) % 4];
      ctx.beginPath(); ctx.moveTo(front[k].x, front[k].y); ctx.lineTo(front[k2].x, front[k2].y); ctx.lineTo(back[k2].x, back[k2].y); ctx.lineTo(back[k].x, back[k].y); ctx.closePath();
      ctx.fillStyle = hex(base, .55 + .25 * lit); ctx.fill();
      ctx.fillStyle = `rgba(255,255,255,${.12 + .5 * lit * lit})`; ctx.fill();
      ctx.strokeStyle = `rgba(255,255,255,${.08 + .3 * lit})`; ctx.lineWidth = .8; ctx.stroke();
    }
    // 后缘细亮线
    ctx.beginPath(); back.forEach((p, i) => i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)); ctx.closePath();
    ctx.strokeStyle = "rgba(255,255,255,.18)"; ctx.lineWidth = 1; ctx.stroke();
  }
  // 正面贴图（按离焦程度混合清晰/模糊层）
  ctx.save();
  ctx.beginPath(); front.forEach((p, i) => i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)); ctx.closePath(); ctx.clip();
  const tex = A.cards[c.img];
  const nx = big ? clamp(Math.ceil(sw / 130), 1, 6) : 1, ny = big ? clamp(Math.ceil(shh / 150), 1, 9) : 1;
  const l0 = Math.min(Math.floor(lv), 2), fr = lv - l0;
  const pick = l => tex[Math.min(2, l + (shh < 220 && l === 0 ? 1 : 0))];
  drawFace(pick(l0), c, sc, nx, ny);
  if (fr > .02 && l0 < 2) { ctx.globalAlpha = a * fr; drawFace(pick(l0 + 1), c, sc, nx, ny); ctx.globalAlpha = a; }
  // 动态玻璃反光：随相机角度滑动
  if (big) {
    const rel = (CP[0] - c.x) / 2400 + c.ry * .9, u = .25 + rel;
    const gx0 = lerp(minx, maxx, u - .5), gx1 = lerp(minx, maxx, u + .5);
    const gg = ctx.createLinearGradient(gx0, miny, gx1, maxy);
    gg.addColorStop(0, "rgba(255,255,255,0)"); gg.addColorStop(.45, "rgba(255,255,255,0)"); gg.addColorStop(.5, "rgba(255,255,255,.16)"); gg.addColorStop(.56, "rgba(255,255,255,0)"); gg.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = gg; ctx.fillRect(minx, miny, sw, shh);
  }
  const fog = clamp((dz - 3500) / 12000, 0, .8) + (opt.dim || 0);
  if (fog > 0) { ctx.fillStyle = `rgba(6,6,9,${clamp(fog, 0, .92)})`; ctx.fillRect(minx, miny, sw, shh); }
  ctx.restore();
  // 正面外缘亮边
  ctx.beginPath(); front.forEach((p, i) => i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)); ctx.closePath();
  ctx.lineWidth = Math.max(.8, 2.2 * ctr.s * sc); ctx.strokeStyle = tint ? hex(tint, .9) : "rgba(255,255,255,.5)"; ctx.globalAlpha = a * (big ? .8 : .5) * clamp(1 - lv * .3); ctx.stroke();
  ctx.restore();
  return { minx, maxx, miny, maxy, dz, cx: ctr.x, cy: ctr.y };
}

// ---------- links ----------
function drawLink(a, b, k, alpha, t, opt = {}) {
  if (k <= 0 || alpha <= 0) return;
  const pa = proj(a.x, a.y, a.z), pb = proj(b.x, b.y, b.z);
  if (pa.dz < 200 || pb.dz < 200) return;
  const ex = lerp(pa.x, pb.x, k), ey = lerp(pa.y, pb.y, k);
  const md = Math.min(pa.dz, pb.dz), fogA = clamp(1 - (md - 2500) / 14000, .08, 1);
  const bl = clamp(blurPx((pa.dz + pb.dz) / 2) / 20);
  ctx.save(); ctx.globalAlpha = alpha * fogA * (.6 - bl * .3);
  ctx.strokeStyle = opt.color || grad(pa.x, pa.y, pb.x, pb.y); ctx.lineWidth = Math.max(.8, (opt.w || 3) * Math.min(pa.s, pb.s) * 1.3 + bl * 2);
  ctx.beginPath(); ctx.moveTo(pa.x, pa.y); ctx.lineTo(ex, ey); ctx.stroke();
  ctx.globalAlpha = alpha * fogA;
  if (opt.pulse !== false && k >= 1) {
    const u = ((t * (opt.speed || .55) + (opt.ph || 0)) % 1 + 1) % 1, px = lerp(pa.x, pb.x, u), py = lerp(pa.y, pb.y, u), rr = 10 + 26 * Math.min(pa.s, pb.s);
    const rg = ctx.createRadialGradient(px, py, 0, px, py, rr); rg.addColorStop(0, "rgba(235,245,255,.95)"); rg.addColorStop(1, "rgba(160,140,255,0)");
    ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(px, py, rr, 0, 7); ctx.fill();
  }
  ctx.restore();
}
function node(p3, r, alpha, col = "#fff") {
  const p = proj(p3.x, p3.y, p3.z); if (p.dz < 120 || alpha <= 0) return;
  const R = Math.max(2, r * p.s);
  ctx.save(); ctx.globalAlpha = alpha;
  const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, R * 5); g.addColorStop(0, hex(col === "#fff" ? "#ffffff" : col, .9)); g.addColorStop(.25, "rgba(190,170,255,.35)"); g.addColorStop(1, "rgba(120,100,255,0)");
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p.x, p.y, R * 5, 0, 7); ctx.fill();
  ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(p.x, p.y, R, 0, 7); ctx.fill(); ctx.restore();
}

// ---------- 背景 / 光斑 ----------
function background() {
  ctx.fillStyle = BG; ctx.fillRect(0, 0, W, H);
  const g1 = ctx.createRadialGradient(W * .85, H * .12, 0, W * .85, H * .12, 900); g1.addColorStop(0, "rgba(120,100,255,.09)"); g1.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = g1; ctx.fillRect(0, 0, W, H);
  const g2 = ctx.createRadialGradient(W * .1, H * .55, 0, W * .1, H * .55, 800); g2.addColorStop(0, "rgba(80,220,240,.05)"); g2.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = g2; ctx.fillRect(0, 0, W, H);
}
function drawMotes(t, alpha, near) {
  for (const m of motes) {
    const mz = CP[2] - 500 + (((m.z - CP[2] + 500) % 19000) + 19000) % 19000;
    const p = proj(m.x, m.y + Math.sin(t * .5 + m.ph) * 40, mz); if (p.dz < 80) continue;
    const isNear = p.dz < FOCUS * .7; if (isNear !== near) continue;
    const bp = blurPx(p.dz), R = m.r * p.s + bp * .9; if (R < .6 || p.x < -R || p.x > W + R || p.y < -R || p.y > H + R) continue;
    const a = alpha * clamp(.85 / (1 + bp * .12)) * clamp(1 - (p.dz - 9000) / 9000) * (.6 + .4 * Math.sin(t * 2 + m.ph));
    if (a <= .01) continue;
    const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, R); g.addColorStop(0, hex(m.c, a)); g.addColorStop(bp > 4 ? .7 : .3, hex(m.c, a * .5)); g.addColorStop(1, hex(m.c, 0));
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p.x, p.y, R, 0, 7); ctx.fill();
  }
}
function scrim(a, from) {
  if (a <= 0) return;
  const g = ctx.createLinearGradient(0, from, 0, H); g.addColorStop(0, "rgba(6,6,9,0)"); g.addColorStop(.4, `rgba(6,6,9,${.8 * a})`); g.addColorStop(1, `rgba(6,6,9,${.95 * a})`);
  ctx.fillStyle = g; ctx.fillRect(0, from, W, H - from);
}
function finish(t) {
  ctx.save(); ctx.globalAlpha = .05; ctx.globalCompositeOperation = "overlay";
  const ox = Math.floor((t * 977) % 300), oy = Math.floor((t * 613) % 300);
  ctx.drawImage(A.grain, -ox, -oy, W * 1.4, H * 1.4); ctx.restore();
  const v = ctx.createRadialGradient(W / 2, H / 2, H * .3, W / 2, H / 2, H * .75); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.55)");
  ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
}

// ---------- 文字 ----------
function parse(line) { const out = []; line.replace(/\[([^\]]+)\]|([^\[]+)/g, (m, h, n) => out.push({ s: h || n, hl: !!h })); return out; }
// 逐字出现，dur 秒内出完（跟口播语速同步）
function textLine(t, line, o) {
  const segs = parse(line);
  ctx.save(); ctx.font = `${o.weight || 500} ${o.size}px NJ`; if (o.ls) ctx.letterSpacing = o.ls + "px";
  const full = segs.map(s => s.s).join(""), n = [...full].length, tw = ctx.measureText(full).width;
  let x = o.align === "center" ? o.x - tw / 2 : o.x;
  const outK = o.out != null ? 1 - eio(prog(t, o.out, .3)) : 1;
  const stag = o.dur ? o.dur / n : (o.stag ?? .035);
  let ci = 0;
  for (const s of segs) {
    const sw = ctx.measureText(s.s).width, fill = s.hl ? grad(x, o.y - o.size, x + sw, o.y, GRAD_TXT) : (o.color || "#fff");
    let acc = 0;
    for (const ch of s.s) {
      const k = eout(prog(t, o.t0 + ci * stag, .32)), cw = ctx.measureText(ch).width;
      if (k > 0) { ctx.globalAlpha = k * outK * (o.alpha ?? 1); ctx.fillStyle = fill; ctx.fillText(ch, x + acc, o.y + (1 - k) * o.size * .3 - (1 - outK) * 14); }
      acc += cw; ci++;
    }
    if (s.hl) { const k = eio(prog(t, o.t0 + ci * stag, .4)); ctx.globalAlpha = outK * .9 * (o.alpha ?? 1); ctx.fillStyle = grad(x, 0, x + sw, 0, GRAD_TXT); ctx.fillRect(x, o.y + o.size * .2, sw * k, Math.max(2, o.size * .045)); }
    x += sw;
  }
  ctx.restore(); return tw;
}
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function glassPanel(x, y, w, h, r, a = 1) {
  ctx.save(); ctx.globalAlpha *= a;
  rr(x, y, w, h, r); ctx.fillStyle = "rgba(255,255,255,.07)"; ctx.fill();
  ctx.lineWidth = 2; ctx.strokeStyle = grad(x, y, x + w, y + h); ctx.globalAlpha *= .7; ctx.stroke();
  ctx.globalAlpha /= .7; rr(x + 3, y + 3, w - 6, h - 6, r - 3); ctx.lineWidth = 1.2; const g = ctx.createLinearGradient(x, y, x, y + h); g.addColorStop(0, "rgba(255,255,255,.5)"); g.addColorStop(.5, "rgba(255,255,255,0)"); ctx.strokeStyle = g; ctx.stroke();
  ctx.restore();
}
function tagPill(t, label, col, x, y, t0, out) {
  const k = eout(prog(t, t0, .35)), ok = 1 - prog(t, out, .25); if (k <= 0 || ok <= 0) return;
  ctx.save(); ctx.globalAlpha = k * ok; ctx.translate(0, (1 - k) * 16);
  ctx.font = "900 34px NJ"; ctx.letterSpacing = "4px"; const w = ctx.measureText(label).width + 84;
  rr(x, y, w, 70, 35); ctx.fillStyle = "rgba(10,10,16,.62)"; ctx.fill(); ctx.lineWidth = 2.5; ctx.strokeStyle = hex(col, .95); ctx.stroke();
  ctx.fillStyle = col; ctx.beginPath(); ctx.arc(x + 34, y + 35, 8, 0, 7); ctx.fill();
  ctx.fillStyle = "#fff"; ctx.fillText(label, x + 56, y + 47); ctx.restore();
}
function bubble(t, txt, col, x, y, t0, out) {
  const k = eback(prog(t, t0, .4)), ok = 1 - prog(t, out, .25); if (k <= 0 || ok <= 0) return;
  ctx.save(); ctx.globalAlpha = clamp(k) * ok;
  ctx.font = "500 36px NJ";
  const typing = t < t0 + .35, tw = typing ? 96 : ctx.measureText(txt).width, bw = tw + 72, bh = 90;
  const bx = Math.min(x, W - 60 - bw);
  ctx.translate(bx, y); const s = lerp(.85, 1, clamp(k)); ctx.scale(s, s);
  rr(0, 0, bw, bh, 45); ctx.fillStyle = "rgba(16,16,24,.78)"; ctx.fill();
  ctx.lineWidth = 2; ctx.strokeStyle = hex(col, .7); ctx.stroke();
  if (typing) { for (let i = 0; i < 3; i++) { ctx.globalAlpha = (.35 + .65 * (.5 + .5 * Math.sin(t * 12 - i))) * ok; ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(50 + i * 26, bh / 2, 7, 0, 7); ctx.fill(); } }
  else { const n = Math.floor(clamp((t - t0 - .35) / .4) * [...txt].length); ctx.fillStyle = "#fff"; ctx.fillText([...txt].slice(0, Math.max(1, n)).join(""), 36, 58); }
  ctx.restore();
}

// ---------- 时间点 ----------
const VO = CFG.vo;
const HOLD = [[3.2, 4.42], [4.42, 5.6], [5.6, 6.8]];   // 三张对比卡各自的停留区间
const TL = { tunStart: 7.5, morph: 6.9, hand: 8.8, collapse: 11.85, logo: 13.05 };
const morphK = (i, t) => eio(prog(t, TL.morph + (i % 6) * .05, 1.45));

// ---------- 世界绘制 ----------
function radialPush(c, t) { // 进入长廊前，网络卡片向外让出中轴
  const k = eio(prog(t, 8.65, 1.1)); if (k <= 0) return c;
  const r = Math.hypot(c.x, c.y) || 1, tr = Math.max(r, 1700 + (c.hero >= 0 ? 0 : 300));
  const f = lerp(1, tr / r, k);
  return { ...c, x: c.x * f, y: c.y * f };
}
function netCardAt(i, t) {
  const c = net[i], s = tunnel[i], m = morphK(i, t);
  const base = { ...c, y: c.y + Math.sin(t * .7 + i) * 14 * (1 - m) };
  if (c.hero >= 0) base.ry = lerp(c.ry, 0, eio(prog(t, HOLD[c.hero][0] - .25, .5)));
  if (m <= 0) return base;
  return { ...base, x: lerp(base.x, s.x, m), y: lerp(base.y, s.y, m), z: lerp(base.z, s.z, m) - Math.sin(Math.PI * m) * 500, ry: lerp(base.ry, s.ry, m) };
}
const holdW = (h, t) => ss(HOLD[h][0] - .2, HOLD[h][0] + .1, t) * (1 - ss(HOLD[h][1] - .2, HOLD[h][1] + .1, t));
const anyHold = t => ss(3.0, 3.3, t) * (1 - ss(6.5, 7.1, t));
function netCardOpts(i, t, c) {
  const n = net[i], isHero = n.hero >= 0, ap = eio(prog(t, n.bloom, .7)), m = morphK(i, t);
  const fw = isHero ? holdW(n.hero, t) : 0, shown = isHero && t >= HOLD[n.hero][0] - .2;
  const wide = prog(t, 6.75, .4) * (1 - prog(t, 7.4, .9));
  const dz = c.z - CP[2], distA = lerp(1, clamp((15000 - dz) / 4000), m);
  return { ap, alpha: distA * ap * ap, scale: lerp(.6, 1, eout(ap)), tint: shown ? CFG.heroes[n.hero].tint : null,
    glow: lerp(lerp(shown ? .8 : .5, 1, fw), shown ? .6 : .4, m), dim: .3 * anyHold(t) * (1 - fw) + (!isHero ? .35 * wide : 0) };
}
function worldNet(t) {
  const hubA = eout(prog(t, .05, .5)) * (1 - prog(t, 3.2, 1.2) * .6) * (1 - prog(t, 6.9, .6));
  const linkA = 1 - prog(t, 6.9, .8);
  if (linkA > 0) netLinks.forEach((l, i) => {
    const k = eio(prog(t, l.t0 + .3, .55));
    const vis = Math.min(l.a === HUB ? 1 : clamp((t - l.a.bloom) / .35), clamp((t - l.b.bloom) / .35));
    if (vis <= 0) return;
    const a = l.a === HUB ? HUB : netCardAt(net.indexOf(l.a), t), b = netCardAt(net.indexOf(l.b), t);
    const chainHot = l.chain && t > 3.1;
    drawLink(a, b, k, linkA * vis * (chainHot ? 1 : .75), t, { ph: i * .37, w: chainHot ? 5 : 3 });
  });
  node(HUB, 9, hubA);
}
const litAt = i => tunnel[i].net != null ? 7.6 : TL.tunStart + (i - net.length) * .012;
let PT = null;
function logoPoint() { if (!PT) { const c = camAt(TL.logo + .4); PT = [0, 0, c[2] + 4200]; } return PT; }
const absorbAt = i => TL.collapse + ((i * .618) % 1) * .8;
function worldTunnel(t) {
  const col = ss(TL.collapse, TL.collapse + .6, t), P = logoPoint();
  const items = tunnel.map((c, i) => {
    let o = c.net != null ? netCardAt(c.net, t) : c;
    if (t > TL.collapse) {
      const k = clamp((t - absorbAt(i)) / .55), e = k * k;
      if (k > 0) o = { ...o, x: lerp(o.x, P[0], e), y: lerp(o.y, P[1], e), z: lerp(o.z, P[2], e), ry: o.ry * (1 - e), sc: 1 - e * .96, fa: 1 - clamp((e - .82) / .18) };
    }
    return o;
  });
  const turn = Math.round(Math.PI * 2 / TUN.dth);
  for (let i = 0; i < items.length - 1; i++) {
    if (t < 7.5) break;
    const a = items[i], dz = a.z - CP[2]; if (dz < 0 || dz > 14000) continue;
    const lk = clamp((t - Math.max(litAt(i), litAt(i + 1), tunnel[i].net != null ? 7.9 : 0) - .1) / .35), la = 1 - col;
    if (lk <= 0) continue;
    drawLink(a, items[i + 1], lk, la * .9, t, { ph: i * .13, speed: .9, w: 4 });
    if (i + turn < items.length) drawLink(a, items[i + turn], lk, la * .3, t, { pulse: false, w: 2 });
  }
  const order = items.map((c, i) => ({ c, i })).sort((a, b) => b.c.z - a.c.z);
  for (const { c, i } of order) {
    const dz = c.z - CP[2]; if (dz < 150 || dz > 15000) continue;
    if (tunnel[i].net != null) {
      const o = netCardOpts(tunnel[i].net, t, c); if (o.ap <= 0) continue;
      drawCard(c, { ...o, alpha: o.alpha * (c.fa ?? 1), scale: o.scale * (c.sc ?? 1) });
      continue;
    }
    const ap = eout(clamp((t - litAt(i)) / .45)); if (ap <= 0) continue;
    drawCard(c, { alpha: ap * clamp((15000 - dz) / 4000) * (c.fa ?? 1), scale: (c.sc ?? 1) * lerp(.7, 1, ap), glow: .4 });
  }
}


// ---------- 文案层 ----------
const TX = 96;
function chrome(t, a) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  ctx.drawImage(A.icon, 96, 96, 56, 56);
  const wh = 40, ww = 1240 * wh / 172; ctx.drawImage(A.word, 80, 114, 1240, 172, 170, 124 - wh / 2, ww, wh); ctx.restore();   // 用提供的 Logo 字标图，不手打文字
}
function captions(t) {
  const c = CFG.copy;
  if (t < 3.6) {
    const [p1, p2] = VO[0].parts, out = 2.85;
    textLine(t, c.l1[0], { x: TX, y: 1500, size: 54, weight: 400, color: "rgba(255,255,255,.82)", t0: p1[0], dur: (p1[1] - p1[0]) * .75, out });
    textLine(t, c.l1[1], { x: TX, y: 1630, size: 104, weight: 900, t0: p2[0], dur: (p2[1] - p2[0]) * .6, out });
  }
  // ② 三个类型逐个替换 → みんな、あなたに夢中
  const P = VO[1].parts;
  if (t > 3.1 && t < 9.2) {
    for (let i = 0; i < 3; i++) {
      const h = CFG.heroes[i], out = i < 2 ? P[i + 1][0] - .32 : P[3][0] - .32;
      if (t < P[i][0] - .05 || t > out + .35) continue;
      textLine(t, c.l2[i], { x: TX, y: 1600, size: 100, weight: 900, color: "#fff", t0: P[i][0], dur: (P[i][1] - P[i][0]) * .55, out });
      // 类型色条
      const k = eout(prog(t, P[i][0], .3)), ok = 1 - prog(t, out, .25);
      ctx.save(); ctx.globalAlpha = k * ok; ctx.fillStyle = h.tint; ctx.fillRect(TX, 1460, 90 * k, 6);
      ctx.font = "700 30px NJ"; ctx.letterSpacing = "6px"; ctx.fillText(h.tag, TX + 110, 1474); ctx.restore();
    }
    textLine(t, c.l2[3], { x: TX, y: 1610, size: 92, weight: 900, t0: P[3][0], dur: (P[4][1] - P[3][0]) * .6, out: 8.6 });
  }
  // ③ 百万 counter
  if (t > 8.8 && t < 13.2) {
    const [p1, p2] = VO[2].parts, out = 12.55;
    const k = ss(9.05, 12.2, GT), n = Math.round(c.counter * (k < 1 ? Math.pow(k, 2.2) : 1));
    const ok = 1 - prog(t, out, .3), ki = eout(prog(t, 8.95, .35));
    if (ki > 0 && ok > 0) {
      ctx.save(); ctx.globalAlpha = ki * ok;
      const pk = k >= 1 ? eback(prog(t, 12.2, .35)) : 0, sc = 1 + .06 * Math.sin(Math.PI * clamp(pk));
      ctx.translate(TX, 1400); ctx.scale(sc, sc);
      ctx.font = "900 150px NJ"; ctx.letterSpacing = "-4px";
      const str = n.toLocaleString("en-US"), w = ctx.measureText(str).width;
      ctx.fillStyle = grad(0, -160, 760, 0, GRAD_TXT); ctx.fillText(str, -6, 0);
      if (pk > 0) { ctx.font = "900 120px NJ"; ctx.globalAlpha = clamp(pk) * ok; ctx.fillText("+", w + 6, -10 - (1 - clamp(pk)) * 24); }
      ctx.restore();
    }
    textLine(t, c.l3[0], { x: TX, y: 1520, size: 58, weight: 500, color: "rgba(255,255,255,.88)", t0: p1[0], dur: (p1[1] - p1[0]) * .7, out });
    textLine(t, c.l3[1], { x: TX, y: 1640, size: 84, weight: 900, t0: p2[0], dur: (p2[1] - p2[0]) * .6, out });
  }
}
// 角色回复气泡：挂在卡片 3D 坐标上，随卡片透视缩放，台词点到即弹出（不加载）
function cardUI(t) {
  const P = VO[1].parts;
  CFG.heroes.forEach((h, i) => {
    const t0 = P[i][0] + .05, out = 7.0;
    if (t < t0 || t > out + .3) return;
    const c = netCardAt(i, t);
    const an = proj(c.x - CW / 2 + 34, c.y + CH / 2 - 170, c.z - TH / 2 - 30);
    if (an.dz < 200) return;
    const k = eback(prog(t, t0, .32)), ok = 1 - prog(t, out, .3);
    const bs = clamp(an.s * 1.25, .5, 1.1) * lerp(.6, 1, clamp(k));
    ctx.save(); ctx.globalAlpha = clamp(k * 1.5) * ok;
    ctx.translate(an.x, an.y); ctx.scale(bs, bs);
    ctx.font = "700 40px NJ"; const tw = ctx.measureText(h.chat).width, bw = tw + 76, bh = 138;
    // 背光
    ctx.shadowColor = hex(h.tint, .55); ctx.shadowBlur = 40;
    rr(0, -bh, bw, bh, 34); ctx.fillStyle = "rgba(12,12,20,.9)"; ctx.fill(); ctx.shadowBlur = 0;
    ctx.lineWidth = 3; ctx.strokeStyle = h.tint; ctx.stroke();
    rr(4, -bh + 4, bw - 8, bh - 8, 30); const hl = ctx.createLinearGradient(0, -bh, 0, 0); hl.addColorStop(0, "rgba(255,255,255,.35)"); hl.addColorStop(.5, "rgba(255,255,255,0)"); ctx.strokeStyle = hl; ctx.lineWidth = 1.5; ctx.stroke();
    // 尾巴
    ctx.beginPath(); ctx.moveTo(34, -2); ctx.lineTo(30, 26); ctx.lineTo(64, -2); ctx.closePath(); ctx.fillStyle = "rgba(12,12,20,.9)"; ctx.fill();
    ctx.fillStyle = h.tint; ctx.beginPath(); ctx.arc(46, -bh + 38, 8, 0, 7); ctx.fill();
    ctx.font = "700 26px NJ"; ctx.letterSpacing = "4px"; ctx.fillText(h.tag, 64, -bh + 47);
    ctx.font = "700 40px NJ"; ctx.letterSpacing = "0px"; ctx.fillStyle = "#fff"; ctx.fillText(h.chat, 38, -32);
    ctx.restore();
    // 弹出光圈
    const rk = prog(t, t0, .45);
    if (rk > 0 && rk < 1) { ctx.save(); ctx.globalAlpha = (1 - rk) * .8 * ok; ctx.strokeStyle = h.tint; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(an.x + 30 * bs, an.y, 20 + 120 * eout(rk) * bs, 0, 7); ctx.stroke(); ctx.restore(); }
  });
}
// 对比卡到位时的外框光环
function heroRing(c, i, t) {
  const t0 = VO[1].parts[i][0] - .05, k = prog(t, t0, .55); if (k <= 0 || k >= 1) return;
  const grow = 1 + .1 * eout(k), pts = RING.map(p => { const w = toWorld(c, p.x * grow, p.y * grow, -TH / 2 - 2, 1); return proj(w[0], w[1], w[2]); });
  if (pts.some(p => p.dz < 120)) return;
  const col = CFG.heroes[i].tint;
  ctx.save(); ctx.globalAlpha = (1 - k) * .85; ctx.strokeStyle = col; ctx.lineWidth = 3 + 5 * (1 - k); ctx.lineJoin = "round";
  ctx.shadowColor = col; ctx.shadowBlur = 26;
  ctx.beginPath(); pts.forEach((p, j) => j ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)); ctx.closePath(); ctx.stroke(); ctx.restore();
}

// ---------- 转场特效 ----------
function hubBurst(t) {
  const k = prog(t, .25, .9); if (k <= 0 || k >= 1) return;
  const p = proj(HUB.x, HUB.y, HUB.z);
  ctx.save();
  ctx.globalAlpha = (1 - k) * .9; ctx.lineWidth = 3 + 8 * (1 - k); ctx.strokeStyle = grad(p.x - 400, p.y, p.x + 400, p.y);
  ctx.beginPath(); ctx.arc(p.x, p.y, 20 + 900 * eout(k), 0, 7); ctx.stroke();
  const f = 1 - prog(t, .25, .35); if (f > 0) { const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, 700); g.addColorStop(0, `rgba(255,255,255,${.55 * f})`); g.addColorStop(1, "rgba(160,140,255,0)"); ctx.globalAlpha = 1; ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  ctx.restore();
}
const WHIPS = [[2.95, 3.33], [4.3, 4.53], [5.45, 5.73]];
function speedLines(t) {
  let w = 0, dir = 1;
  WHIPS.forEach(([a, b], i) => { const k = prog(t, a - .05, b - a + .1); if (k > 0 && k < 1) { w = Math.max(w, Math.sin(Math.PI * k)); dir = i === 0 ? 1 : 1; } });
  if (w <= .01) return;
  seed = 31 + Math.floor(t * 30); ctx.save(); ctx.globalCompositeOperation = "lighter";
  for (let i = 0; i < 46; i++) {
    const y = rnd() * H, len = 300 + rnd() * 900, x = rnd() * (W + len) - len, th = 1 + rnd() * 3, col = PAL[i % 4];
    const g = ctx.createLinearGradient(x, 0, x + len, 0); g.addColorStop(0, hex(col, 0)); g.addColorStop(.7, hex(col, .5 * w)); g.addColorStop(1, hex("#ffffff", 0));
    ctx.fillStyle = g; ctx.fillRect(x, y, len, th);
  }
  ctx.restore();
}
function warpStreaks(t) {
  const k = prog(t, 8.5, 1.3); if (k <= 0 || k >= 1) return;
  const w = Math.sin(Math.PI * k); seed = 77; ctx.save(); ctx.globalCompositeOperation = "lighter";
  for (let i = 0; i < 90; i++) {
    const a = rnd() * Math.PI * 2, r0 = 120 + rnd() * 500, sp = .6 + rnd() * .8;
    const ph = (k * 2.4 * sp + rnd()) % 1, ra = r0 + ph * 1400, rb = ra + 120 + 600 * ph * w;
    const x0 = W / 2 + Math.cos(a) * ra, y0 = CY + Math.sin(a) * ra, x1 = W / 2 + Math.cos(a) * rb, y1 = CY + Math.sin(a) * rb;
    const g = ctx.createLinearGradient(x0, y0, x1, y1), col = PAL[i % 4]; g.addColorStop(0, hex(col, 0)); g.addColorStop(1, hex(col, .7 * w * ph));
    ctx.strokeStyle = g; ctx.lineWidth = 1.5 + 3 * ph; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
  }
  ctx.restore();
}
function shockwave(t) {
  const d = t - TL.logo; if (d < 0 || d > 1.4) return;
  ctx.save(); ctx.globalCompositeOperation = "lighter";
  // 中心光爆（只在 Logo 周围，不闪全屏）
  const b = Math.exp(-d * 5), g = ctx.createRadialGradient(W / 2, CY, 0, W / 2, CY, 520 + 300 * d);
  g.addColorStop(0, `rgba(255,250,255,${.75 * b})`); g.addColorStop(.3, `rgba(185,160,255,${.45 * b})`); g.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // 放射光束
  seed = 515;
  for (let i = 0; i < 14; i++) {
    const a = i / 14 * Math.PI * 2 + rnd() * .3 + d * .25, len = (700 + 700 * rnd()) * eout(clamp(d / .5)), wA = .06 + .05 * rnd();
    const al = .35 * Math.exp(-d * 3) * (.6 + .4 * rnd()), col = PAL[i % 4];
    ctx.save(); ctx.translate(W / 2, CY); ctx.rotate(a);
    const lg = ctx.createLinearGradient(0, 0, len, 0); lg.addColorStop(0, hex("#ffffff", al)); lg.addColorStop(.4, hex(col, al * .7)); lg.addColorStop(1, hex(col, 0));
    ctx.fillStyle = lg; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(len, -len * wA); ctx.lineTo(len, len * wA); ctx.closePath(); ctx.fill(); ctx.restore();
  }
  // 两道柔光环
  [[0, 1300, 12], [.08, 900, 6]].forEach(([dl, R0, lw]) => {
    const k = clamp((d - dl) / .9); if (k <= 0 || k >= 1) return;
    ctx.globalAlpha = (1 - k) * .6; ctx.lineWidth = lw * (1 - k) + 1; ctx.strokeStyle = grad(0, CY - 600, W, CY + 600);
    ctx.beginPath(); ctx.arc(W / 2, CY, 60 + R0 * eout(k), 0, 7); ctx.stroke();
  });
  ctx.globalAlpha = 1;
  // 火花粒子：向外飞散、减速、拖尾
  seed = 616;
  for (let i = 0; i < 90; i++) {
    const a = rnd() * Math.PI * 2, sp = 500 + 1300 * rnd(), life = .6 + .7 * rnd(), k = d / life; if (k >= 1) continue;
    const dist = sp * (1 - Math.exp(-d * 3.2)) / 3.2 * 3, r0 = 60 + 20 * rnd();
    const x = W / 2 + Math.cos(a) * (r0 + dist), y = CY + Math.sin(a) * (r0 + dist), tail = 30 + 120 * Math.exp(-d * 4);
    const col = PAL[i % 4], al = (1 - k) * (.6 + .4 * rnd());
    const lg = ctx.createLinearGradient(x, y, x - Math.cos(a) * tail, y - Math.sin(a) * tail); lg.addColorStop(0, hex(i % 3 ? col : "#ffffff", al)); lg.addColorStop(1, hex(col, 0));
    ctx.strokeStyle = lg; ctx.lineWidth = 2 + 3 * rnd(); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - Math.cos(a) * tail, y - Math.sin(a) * tail); ctx.stroke();
  }
  ctx.restore();
}
const TOG_ON = 14.0;
function toggleSweep(t) {
  const k = prog(t, TOG_ON, .6); if (k <= 0 || k >= 1) return;
  const x = lerp(-500, W + 500, eio(k));
  ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.translate(x, H / 2); ctx.rotate(-.35);
  const g = ctx.createLinearGradient(-260, 0, 260, 0); g.addColorStop(0, "rgba(120,200,255,0)"); g.addColorStop(.5, `rgba(220,200,255,${.35 * Math.sin(Math.PI * k)})`); g.addColorStop(1, "rgba(255,160,230,0)");
  ctx.fillStyle = g; ctx.fillRect(-260, -1600, 520, 3200); ctx.restore();
}
function endGlow(t) { // 开关打开后背景提亮一档
  const k = eout(prog(t, TOG_ON + .1, .8)); if (k <= 0) return;
  const g = ctx.createRadialGradient(W / 2, 900, 0, W / 2, 900, 1300); g.addColorStop(0, `rgba(140,120,255,${.16 * k})`); g.addColorStop(.6, `rgba(90,200,240,${.05 * k})`); g.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}

function endUI(t) {
  const c = CFG.copy, cx = W / 2;
  const ak = prog(t, TL.collapse + .1, TL.logo - TL.collapse - .1), lk = eout(clamp(ak * 1.6));
  if (lk > 0) {
    const y = lerp(CY, 560, eio(prog(t, TL.logo + .45, .7)));
    const g = ctx.createRadialGradient(cx, y, 0, cx, y, 560); g.addColorStop(0, `rgba(150,130,255,${(.3 + .25 * suckK(t)) * lk})`); g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g; ctx.fillRect(0, y - 600, W, 1200);
    const sz = 230 * lerp(.08, 1, eio(ak)), TR = TL.logo, dR = t - TR;
    let sx = 1, sy = 1;
    if (dR < 0) { const q = suckK(t), pre = 1 - .3 * ss(TR - .35, TR, t); sx = pre * (1 + .07 * q * Math.sin(t * 37)); sy = pre * (1 - .07 * q * Math.sin(t * 37)); }
    else { const e = Math.exp(-dR * 4.2), s0 = 1 - .3 * e * Math.cos(dR * 15), j = .16 * e * Math.sin(dR * 15); sx = s0 * (1 + j); sy = s0 * (1 - j); }
    ctx.save(); ctx.globalAlpha = clamp(lk * 1.4); ctx.shadowColor = "rgba(169,139,255,.7)"; ctx.shadowBlur = 70;
    ctx.translate(cx, y); ctx.scale(sx, sy); ctx.drawImage(A.icon, -sz / 2, -sz / 2, sz, sz); ctx.restore();
    // Logo 玻璃扫光
    const gk = prog(t, TL.logo + .45, .6);
    if (gk > 0 && gk < 1) { ctx.save(); ctx.beginPath(); ctx.roundRect(cx - sz / 2, y - sz / 2, sz, sz, sz * .22); ctx.clip(); const sx = cx - sz + gk * sz * 2; const gg = ctx.createLinearGradient(sx - 50, y - sz / 2, sx + 50, y + sz / 2); gg.addColorStop(0, "rgba(255,255,255,0)"); gg.addColorStop(.5, "rgba(255,255,255,.6)"); gg.addColorStop(1, "rgba(255,255,255,0)"); ctx.fillStyle = gg; ctx.fillRect(cx - sz / 2, y - sz / 2, sz, sz); ctx.restore(); }
    const wk = eout(prog(t, TL.logo + .7, .5)), ww = 520, wh = ww * A.word.height / A.word.width;
    ctx.save(); ctx.globalAlpha = wk; ctx.drawImage(A.word, cx - ww / 2, 735 - wh / 2 + (1 - wk) * 20, ww, wh); ctx.restore();
  }
  // 無制限モード：只做动画，不读不写「制限、一切なし」
  const tk = eout(prog(t, TL.logo + .9, .45));
  if (tk > 0) {
    const bw = 540, bh = 108, bx = cx - bw / 2, by = 880, on = eio(prog(t, TOG_ON, .35));
    ctx.save(); ctx.globalAlpha = tk; ctx.translate(0, (1 - tk) * 24);
    glassPanel(bx, by, bw, bh, 54);
    ctx.font = "700 38px NJ"; ctx.letterSpacing = "2px"; ctx.fillStyle = "#fff"; ctx.fillText(c.toggle, bx + 50, by + 68);
    const sw = 136, sh = 70, sx = bx + bw - sw - 22, sy = by + (bh - sh) / 2;
    rr(sx, sy, sw, sh, 35); ctx.fillStyle = "rgba(255,255,255,.14)"; ctx.fill();
    ctx.save(); ctx.globalAlpha = tk * on; rr(sx, sy, sw, sh, 35); ctx.fillStyle = grad(sx, sy, sx + sw, sy + sh, PG); ctx.fill(); ctx.restore();
    const kx = lerp(sx + 35, sx + sw - 35, on);
    ctx.shadowColor = "rgba(0,0,0,.4)"; ctx.shadowBlur = 10; ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(kx, sy + 35, 28, 0, 7); ctx.fill();
    ctx.shadowBlur = 0; ctx.font = "700 20px NJ"; ctx.globalAlpha = tk * on; ctx.fillStyle = "#0b0b10"; ctx.fillText("ON", sx + 22, sy + 43);
    ctx.restore();
    const rk = prog(t, TOG_ON + .1, .6);
    if (rk > 0 && rk < 1) { ctx.save(); ctx.globalAlpha = (1 - rk) * .9; ctx.strokeStyle = grad(bx, by, bx + bw, by + bh); ctx.lineWidth = 3; rr(bx - rk * 50, by - rk * 50, bw + rk * 100, bh + rk * 100, 54 + rk * 50); ctx.stroke(); ctx.restore(); }
  }
  const [q1, q2] = VO[3].parts;
  textLine(t, c.l5[0], { x: cx, y: 1190, size: 52, weight: 400, align: "center", color: "rgba(255,255,255,.8)", t0: q1[0], dur: (q1[1] - q1[0]) * .7 });
  textLine(t, c.l5[1], { x: cx, y: 1320, size: 100, weight: 900, align: "center", t0: q2[0], dur: (q2[1] - q2[0]) * .55 });
  // CTA：光线擦出
  const ctaT = q2[1] - .15, ck = prog(t, ctaT, .5);
  if (ck > 0) {
    const bw = 680, bh = 128, bx = cx - bw / 2, by = 1500, ek = eio(ck);
    const TP = ctaT + 1.0, bt = t - TP;   // 点击按钮：按下压缩 → 松开弹性回弹
    const press = bt < 0 ? 1 - .075 * ss(-.12, 0, bt) : 1 - .075 * Math.exp(-bt * 8) * Math.cos(bt * 24);
    const pulse = (1 + .015 * Math.sin((t - ctaT - .8) * 6) * (t > ctaT + .8 && t < TP - .2 ? 1 : 0)) * press;
    ctx.save(); ctx.translate(cx, by + bh / 2); ctx.scale(pulse, pulse); ctx.translate(-cx, -(by + bh / 2));
    ctx.save(); ctx.beginPath(); ctx.rect(bx - 40, by - 60, (bw + 80) * ek, bh + 120); ctx.clip();
    ctx.shadowColor = "rgba(169,139,255,.55)"; ctx.shadowBlur = 50;
    rr(bx, by, bw, bh, 64); ctx.fillStyle = grad(bx, by, bx + bw, by + bh, PG); ctx.fill(); ctx.shadowBlur = 0;
    ctx.save(); rr(bx, by, bw, bh, 64); ctx.clip();
    const sp = ((t - ctaT - .7) % 1.6) / 1.0; if (t > ctaT + .7 && sp < 1) { const sx = bx - 200 + sp * (bw + 400); const g = ctx.createLinearGradient(sx - 90, 0, sx + 90, 0); g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(.5, "rgba(255,255,255,.3)"); g.addColorStop(1, "rgba(255,255,255,0)"); ctx.fillStyle = g; ctx.fillRect(bx, by, bw, bh); }
    ctx.restore();
    rr(bx + 4, by + 4, bw - 8, bh - 8, 60); const hl = ctx.createLinearGradient(0, by, 0, by + bh); hl.addColorStop(0, "rgba(255,255,255,.6)"); hl.addColorStop(.5, "rgba(255,255,255,0)"); ctx.strokeStyle = hl; ctx.lineWidth = 2; ctx.stroke();
    ctx.font = "900 48px NJ"; ctx.letterSpacing = "4px"; ctx.textAlign = "center"; ctx.fillStyle = "#1c1c26"; ctx.fillText(c.cta, cx - 16, by + 81);
    ctx.fillText("›", bx + bw - 86 + Math.sin(t * 6) * 5, by + 80);
    // 点击瞬间：按钮内白光 + 水波纹
    if (bt > 0 && bt < .7) {
      ctx.save(); rr(bx, by, bw, bh, 64); ctx.clip(); ctx.globalCompositeOperation = "lighter";
      ctx.fillStyle = `rgba(255,255,255,${.22 * Math.exp(-bt * 7)})`; ctx.fillRect(bx, by, bw, bh);
      const rk = eout(clamp(bt / .55)), tx = cx + 235, ty = by + bh / 2;
      const rg = ctx.createRadialGradient(tx, ty, 0, tx, ty, 40 + 720 * rk); rg.addColorStop(0, "rgba(255,255,255,0)"); rg.addColorStop(.82, `rgba(255,255,255,${.5 * (1 - rk)})`); rg.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = rg; ctx.fillRect(bx, by, bw, bh); ctx.restore();
    }
    ctx.restore();
    if (ck < 1) { // 擦出的光边
      const ex = bx - 40 + (bw + 80) * ek; const g = ctx.createLinearGradient(ex - 30, 0, ex + 30, 0); g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(.5, "rgba(255,255,255,.95)"); g.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = g; ctx.fillRect(ex - 30, by - 50, 60, bh + 100);
    }
    ctx.restore();
  }
  ctaClick(t, ctaT + 1.0, 1500, 128, 680);
  const bk = eout(prog(t, ctaT + .45, .5));
  if (bk > 0) { const bw = 600, bh = bw * A.badges.height / A.badges.width; ctx.save(); ctx.globalAlpha = bk; ctx.drawImage(A.badges, cx - bw / 2, 1700 + (1 - bk) * 16, bw, bh); ctx.restore(); }
}

// 点击：触控光标移入 → 按下 → 外扩光环 + 火花
function ctaClick(t, TP, by, bh, bw) {
  const cx = W / 2, tx = cx + 235, ty = by + bh / 2, bt = t - TP;
  // 外扩光环与火花（按钮外）
  if (bt > 0 && bt < 1.2) {
    ctx.save(); ctx.globalCompositeOperation = "lighter";
    [[0, 1, 4], [.1, .7, 2]].forEach(([dl, amp, lw]) => {
      const k = clamp((bt - dl) / .8); if (k <= 0 || k >= 1) return;
      const e = eout(k), g = 70 * e * amp + 6;
      ctx.globalAlpha = (1 - k) * .85; ctx.lineWidth = lw * (1 - k) + 1; ctx.strokeStyle = grad(cx - bw / 2, by, cx + bw / 2, by + bh, PG);
      rr(cx - bw / 2 - g, by - g, bw + 2 * g, bh + 2 * g, 64 + g); ctx.stroke();
    });
    const gl = ctx.createRadialGradient(cx, ty, 0, cx, ty, 520); gl.addColorStop(0, `rgba(200,170,255,${.35 * Math.exp(-bt * 4)})`); gl.addColorStop(1, "rgba(0,0,0,0)");
    ctx.globalAlpha = 1; ctx.fillStyle = gl; ctx.fillRect(0, ty - 600, W, 1200);
    seed = 909;
    for (let i = 0; i < 26; i++) {
      const a = -Math.PI / 2 + (rnd() - .5) * Math.PI * 1.9, sp = 240 + 420 * rnd(), life = .5 + .5 * rnd(), k = bt / life; if (k >= 1) continue;
      const d = sp * (1 - Math.exp(-bt * 5)) / 5 * 4, x = tx + Math.cos(a) * (30 + d), y = ty + Math.sin(a) * (30 + d) * .8, r = (3 + 4 * rnd()) * (1 - k);
      const col = PAL[i % 4]; ctx.globalAlpha = (1 - k);
      const g2 = ctx.createRadialGradient(x, y, 0, x, y, r * 4); g2.addColorStop(0, "#ffffff"); g2.addColorStop(.35, hex(col, .8)); g2.addColorStop(1, hex(col, 0));
      ctx.fillStyle = g2; ctx.beginPath(); ctx.arc(x, y, r * 4, 0, 7); ctx.fill();
    }
    ctx.restore();
  }
  // 触控光标
  const ik = eout(prog(t, TP - .65, .5)), ok = 1 - prog(t, TP + .35, .35);
  if (ik <= 0 || ok <= 0) return;
  const mx = lerp(tx + 230, tx, eio(prog(t, TP - .65, .55))), my = lerp(ty + 380, ty, eio(prog(t, TP - .65, .55)));
  const ps = bt < 0 ? 1 - .25 * ss(-.12, 0, bt) : 1 - .25 * Math.exp(-bt * 10);
  ctx.save(); ctx.globalAlpha = ik * ok; ctx.translate(mx, my); ctx.scale(ps, ps);
  ctx.shadowColor = "rgba(0,0,0,.35)"; ctx.shadowBlur = 24;
  ctx.fillStyle = "rgba(255,255,255,.38)"; ctx.beginPath(); ctx.arc(0, 0, 46, 0, 7); ctx.fill(); ctx.shadowBlur = 0;
  ctx.lineWidth = 4; ctx.strokeStyle = "rgba(255,255,255,.95)"; ctx.stroke();
  ctx.fillStyle = "rgba(255,255,255,.95)"; ctx.beginPath(); ctx.arc(0, 0, 16, 0, 7); ctx.fill();
  ctx.restore();
}

// ---------- 百万长廊：冲刺特效 ----------
const RUSH = t => ss(9.3, 10.0, t) * (.55 + .45 * ss(10.6, 11.8, t)) * (1 - ss(11.8, 12.9, t));          // 冲刺强度
const GATES = Array.from({ length: 11 }, (_, k) => 6200 + k * 2350);       // 光环门
function gateRings(t) {
  const r = RUSH(t); if (r <= .01) return;
  ctx.save(); ctx.globalCompositeOperation = "lighter";
  GATES.forEach((gz, k) => {
    const c = proj(0, 0, gz); if (c.dz < 60 || c.dz > 16000) return;
    const rad = 1750 * c.s, a = r * clamp((16000 - c.dz) / 6000) * clamp(c.dz / 900);
    if (rad > 4000 || a <= .01) return;
    const col = PAL[k % 4], col2 = PAL[(k + 2) % 4];
    ctx.lineWidth = Math.max(2, 70 * c.s); ctx.strokeStyle = hex(col, .55 * a);
    ctx.shadowColor = col; ctx.shadowBlur = 40;
    ctx.beginPath(); ctx.arc(c.x, c.y, rad, 0, 7); ctx.stroke();
    ctx.lineWidth = Math.max(1, 18 * c.s); ctx.strokeStyle = hex("#ffffff", .7 * a); ctx.beginPath(); ctx.arc(c.x, c.y, rad, 0, 7); ctx.stroke();
    // 门上的刻度光点
    ctx.shadowBlur = 0; ctx.fillStyle = hex(col2, .9 * a);
    for (let j = 0; j < 24; j++) { const an = j / 24 * Math.PI * 2 + t * .8 * (k % 2 ? 1 : -1); ctx.beginPath(); ctx.arc(c.x + Math.cos(an) * rad * 1.06, c.y + Math.sin(an) * rad * 1.06, Math.max(1.5, 22 * c.s), 0, 7); ctx.fill(); }
  });
  ctx.restore();
}
function gateFlash(t) { // 穿过光环门的一瞬间闪白
  const r = RUSH(t); if (r <= .01) return;
  let f = 0; GATES.forEach(gz => { const dz = gz - CP[2]; f += Math.exp(-(((dz + 150) / 550) ** 2)); });
  f = clamp(f) * r; if (f < .01) return;
  const g = ctx.createRadialGradient(W / 2, CY, 100, W / 2, CY, 1500); g.addColorStop(0, `rgba(255,255,255,${.1 * f})`); g.addColorStop(.6, `rgba(190,170,255,${.32 * f})`); g.addColorStop(1, `rgba(120,220,255,${.5 * f})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function rushStreaks(t) { // 持续的径向光速线，强度随速度
  const r = RUSH(t); if (r <= .01) return;
  seed = 900 + Math.floor(t * 30); ctx.save(); ctx.globalCompositeOperation = "lighter";
  for (let i = 0; i < 140; i++) {
    const a = rnd() * Math.PI * 2, r0 = 160 + rnd() * 1300, len = (250 + rnd() * 1100) * r, col = PAL[i % 4];
    const x0 = W / 2 + Math.cos(a) * r0, y0 = CY + Math.sin(a) * r0, x1 = W / 2 + Math.cos(a) * (r0 + len), y1 = CY + Math.sin(a) * (r0 + len);
    const g = ctx.createLinearGradient(x0, y0, x1, y1); g.addColorStop(0, hex(col, 0)); g.addColorStop(1, hex(i % 5 ? col : "#ffffff", (.25 + rnd() * .5) * r));
    ctx.strokeStyle = g; ctx.lineWidth = 1 + rnd() * 4 * r; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
  }
  ctx.restore();
}
function zoomBlur(t) { // 画面自叠放大 = 径向变焦模糊
  const r = RUSH(t) * .7 + .45 * suckK(t); if (r <= .02) return;
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  const w = cv.width, h = cv.height, cx = w / 2, cy = CY * SS;
  [[1.035, .32], [1.075, .2], [1.12, .12]].forEach(([sc, a]) => {
    const k = 1 + (sc - 1) * r * (suckK(t) > .01 ? -1 : 1); ctx.globalAlpha = a * r;
    ctx.drawImage(cv, cx - cx * k, cy - cy * k, w * k, h * k);
  });
  ctx.restore();
}
function vignetteRush(t) {
  const r = RUSH(t); if (r <= .01) return;
  const g = ctx.createRadialGradient(W / 2, CY, 500, W / 2, CY, 1500); g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(1, `rgba(3,3,8,${.55 * r})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}

const suckK = t => { const k = prog(t, TL.collapse, TL.logo + .2 - TL.collapse); return k > 0 && k < 1 ? Math.sin(Math.PI * k) : 0; };
function suckIn(t) {
  const K = prog(t, TL.collapse, TL.logo - TL.collapse); if (K <= 0 || K >= 1) return;
  seed = 4242; ctx.save(); ctx.globalCompositeOperation = "lighter";
  for (let i = 0; i < 110; i++) {
    const a = rnd() * Math.PI * 2, st = rnd() * .35, col = PAL[i % 4];
    const k = clamp((K - st) / .65); if (k <= 0 || k >= 1) continue;
    const e = k * k, ra = 1700 * (1 - e) + 30, rb = ra + 200 + 700 * (1 - e) * (.5 + rnd());
    const x0 = W / 2 + Math.cos(a) * ra, y0 = CY + Math.sin(a) * ra, x1 = W / 2 + Math.cos(a) * rb, y1 = CY + Math.sin(a) * rb;
    const g = ctx.createLinearGradient(x0, y0, x1, y1); g.addColorStop(0, hex(i % 5 ? col : "#ffffff", .8 * Math.sin(Math.PI * k))); g.addColorStop(1, hex(col, 0));
    ctx.strokeStyle = g; ctx.lineWidth = 1.5 + 3 * rnd(); ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
  }
  const core = (K < .92 ? ss(0, .92, K) : 1 - ss(.92, 1, K)) * (.55 + .12 * Math.sin(t * 31)), g = ctx.createRadialGradient(W / 2, CY, 0, W / 2, CY, 180 + 260 * K);
  g.addColorStop(0, `rgba(230,220,255,${.5 * core})`); g.addColorStop(.35, `rgba(170,150,255,${.35 * core})`); g.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

// ---------- 主循环 ----------
const pulseAt = (t, t0, d) => { const k = prog(t, t0, d); return k > 0 && k < 1 ? Math.sin(Math.PI * k) * (1 - k * .3) : 0; };
function renderFrame(t, layer = "all") {
  ctx.setTransform(SS, 0, 0, SS, 0, 0);
  // 焦距冲击：「展開」推一下；三张卡到位轻推；进长廊时广角拉伸（光速感）
  const P2 = VO[1].parts;
  FZ = 1 + .07 * pulseAt(t, VO[0].parts[1][0] - .05, .55) + .035 * (pulseAt(t, P2[0][0], .45) + pulseAt(t, P2[1][0], .45) + pulseAt(t, P2[2][0], .45))
         + .05 * ss(7.4, 8.45, t) * (1 - ss(8.45, 8.8, t)) - .2 * pulseAt(t, 8.6, 1.2) - .22 * RUSH(t) + .06 * suckK(t) + .05 * (t > TL.logo ? Math.exp(-(t - TL.logo) * 4) * Math.sin((t - TL.logo) * 15) : 0);
  { const v = camAt(t).slice(), r = RUSH(t); if (r > 0) { v[0] += Math.sin(t * 3.1) * 50 * r; v[1] += Math.cos(t * 2.6) * 35 * r; v[6] += Math.sin(t * 2.2) * .02 * r; } setCam(v); }
  const hold = HOLD.findIndex(h => t >= h[0] && t < h[1]);
  let fTarget;
  if (t < 1.2) fTarget = lerp(440, 1100, ss(0, 1.2, t));
  else if (t < 3.0) fTarget = lerp(1100, 3000, ss(1.2, 3.0, t));
  else if (t < 6.75) { const h = hold >= 0 ? hold : 2; const c = net[h]; fTarget = proj(c.x, c.y, c.z).dz; }
  else if (t < 9.0) fTarget = lerp(proj(net[2].x, net[2].y, net[2].z).dz, proj(0, 0, 3600).dz, ss(6.75, 8.0, t));
  else fTarget = lerp(proj(0, 0, 3600).dz, 2700, ss(9.0, 9.6, t));
  FOCUS = fTarget; APER = 26 + 14 * ss(8.3, 9.1, t) * (1 - ss(12.2, 12.9, t));
  if (layer === "ui") { ctx.clearRect(0, 0, W, H); drawUI(t); return; }
  background();
  endGlow(t);
  drawMotes(t, 1, false);
  worldNet(t);
  worldTunnel(t);
  drawMotes(t, 1, true);
  hubBurst(t); speedLines(t); warpStreaks(t); rushStreaks(t);
  zoomBlur(t); vignetteRush(t); suckIn(t);
  const capA = t < 12.7 ? 1 : 1 - prog(t, 12.7, .4);
  scrim(capA, 1080);
  if (t < 13.0) cardUI(t);   // 气泡挂在卡上，跟卡一起做运动模糊
  shockwave(t);
  toggleSweep(t);
  if (layer === "all") drawUI(t);
  finish(t);
}
// 文字/气泡/Logo/按钮：单独一层，只在整帧时刻画一次（不做运动模糊，保证清晰无重影）
function drawUI(t) {
  if (t < 13.0) captions(t);
  endUI(t);
  chrome(t, eout(prog(t, .6, .6)) * (1 - prog(t, TL.logo - .3, .3)));
}
// 输出：2x 超采样缩到 1080，多子帧平均做运动模糊，PNG 无损
const OUT = document.createElement("canvas"); OUT.width = W; OUT.height = H;
const octx = OUT.getContext("2d"); octx.imageSmoothingEnabled = true; octx.imageSmoothingQuality = "high";
const HALF = document.createElement("canvas"); HALF.width = W * SS / 2 * 1; HALF.height = H * SS / 2;
let GT = 0; // 整帧时间：计数数字不参与运动模糊，保持清晰
function grab(t, n = 4, shutter = .55) {
  GT = t;
  // 自适应子帧：镜头越快子帧越多，甩镜/冲刺时拖影连续不成重影
  { const d = shutter / CFG.fps, c0 = camAt(Math.max(0, t - d / 2)), c1 = camAt(t + d / 2);
    const mv = Math.hypot(c1[0] - c0[0], c1[1] - c0[1], c1[2] - c0[2]) + 600 * Math.abs(c1[6] - c0[6]);
    const ang = Math.hypot(c1[3] - c0[3], c1[4] - c0[4], c1[5] - c0[5]) / 6;
    n = Math.max(n, Math.min(24, Math.round(4 + (mv + ang) / 25))); }
  for (let k = 0; k < n; k++) {
    const tt = Math.max(0, t + ((k + .5) / n - .5) * shutter / CFG.fps);
    renderFrame(tt, "scene");
    octx.globalAlpha = 1 / (k + 1); octx.drawImage(cv, 0, 0, W, H);
  }
  octx.globalAlpha = 1;
  renderFrame(t, "ui"); octx.drawImage(cv, 0, 0, W, H);
}
window.renderFrame = t => { GT = t; renderFrame(t); };
window.grabFrame = (t, n = 4) => { grab(t, n); return OUT.toDataURL("image/png"); };
window.camZ = t => camAt(t)[2]; window.camAt = camAt; window.GATES = GATES; window.BLOOMS = net.map(c => c.bloom);
init().catch(e => { window.__err = String(e && e.stack || e); });
})();
