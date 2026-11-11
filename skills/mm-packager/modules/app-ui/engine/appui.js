// MM 产品 UI 模板引擎：chat（聊天界面）/ swipe（划卡选角色）。1080×1920，按时间 t 确定性绘制。
// 所有屏幕文字只来自 config（空字符串 = 不画）。
(() => {
const C = window.APPUI_CONFIG, W = 1080, H = 1920;
const SS = C.ss || 2;                                  // 超采样抗锯齿：内部按 SS 倍绘制再缩小
const out = document.getElementById('cv'), og = out.getContext('2d');
const cv = document.createElement('canvas'); cv.width = W * SS; cv.height = H * SS; let g = cv.getContext('2d');
// 抗锯齿遮罩：canvas clip() 边缘不做抗锯齿 → 图片圆角一律先画到图层，再用 fill（有抗锯齿）做 destination-in
const LAY = document.createElement('canvas'); LAY.width = W * SS; LAY.height = H * SS; const lg = LAY.getContext('2d');
function masked(pathFn, drawFn) {
  const main = g, m = main.getTransform();
  lg.setTransform(1, 0, 0, 1, 0, 0); lg.globalCompositeOperation = 'source-over'; lg.globalAlpha = 1; lg.filter = 'none'; lg.shadowBlur = 0; lg.clearRect(0, 0, LAY.width, LAY.height);
  lg.setTransform(m); g = lg;
  try { lg.save(); drawFn(); lg.restore(); lg.globalCompositeOperation = 'destination-in'; lg.globalAlpha = 1; lg.fillStyle = '#000'; pathFn(); lg.fill(); }
  finally { g = main; }
  main.save(); main.setTransform(1, 0, 0, 1, 0, 0); main.shadowBlur = 0; main.shadowColor = 'transparent'; main.filter = 'none'; main.drawImage(LAY, 0, 0); main.restore();
  lg.globalCompositeOperation = 'source-over';
}
const IMG = {}, FONT = '"MMJP", "Noto Sans JP", sans-serif';
const BRAND = ['#47D7FF', '#8F5BFF'];            // 品牌 青→紫
const INK = '#1E1730';

// ---------- 工具 ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, p) => a + (b - a) * p;
const eo = x => 1 - Math.pow(1 - clamp(x), 3);
const eio = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const eob = (x, s = 1.6) => { x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1; };
const seg = (t, a, d) => clamp((t - a) / d);
function rr(x, y, w, h, r) {
  const R = typeof r === 'number' ? [r, r, r, r] : r;
  g.beginPath(); g.moveTo(x + R[0], y);
  g.arcTo(x + w, y, x + w, y + h, R[1]); g.arcTo(x + w, y + h, x, y + h, R[2]);
  g.arcTo(x, y + h, x, y, R[3]); g.arcTo(x, y, x + w, y, R[0]); g.closePath();
}
function grad(x0, y0, x1, y1, stops) { const q = g.createLinearGradient(x0, y0, x1, y1); stops.forEach((c, i) => q.addColorStop(i / (stops.length - 1), c)); return q; }
function font(sz, wt = 700) { g.font = `${wt} ${sz}px ${FONT}`; }
function cover(img, x, y, w, h, fy = .35, fx = .5) {
  if (!img) { g.fillStyle = '#2a2140'; g.fillRect(x, y, w, h); return; }
  const s = Math.max(w / img.width, h / img.height), sw = w / s, sh = h / s;
  g.drawImage(img, clamp(img.width * fx - sw / 2, 0, img.width - sw), clamp(img.height * fy - sh / 2, 0, img.height - sh), sw, sh, x, y, w, h);
}
const NOHEAD = '、。，．・！？!?…」』）)〉》ー〜~ぁぃぅぇぉっゃゅょァィゥェォッャュョ♡';
function wrap(text, maxW) {
  const out = [];
  for (const para of String(text).split('\n')) {
    let line = '';
    const chars = [...para];
    for (let i = 0; i < chars.length; i++) {
      const ch = chars[i], test = line + ch;
      if (g.measureText(test).width > maxW && line && !NOHEAD.includes(ch)) { out.push(line); line = ch; }
      else line = test;
    }
    out.push(line);
  }
  return out;
}
function shadowText(s, x, y, blur = 18, col = 'rgba(0,0,0,.55)') { g.save(); g.shadowColor = col; g.shadowBlur = blur; g.shadowOffsetY = 3; g.fillText(s, x, y); g.restore(); }

function statusBar(a = 1, col = '#fff') {
  g.save(); g.globalAlpha *= a; g.fillStyle = col; font(40, 700); g.textAlign = 'left'; g.textBaseline = 'middle';
  if (col === '#fff') shadowText('9:41', 86, 66, 10); else g.fillText('9:41', 86, 66);
  // 信号 / wifi / 电池
  for (let i = 0; i < 4; i++) { rr(820 + i * 15, 76 - 8 - i * 6, 10, 10 + i * 6, 2); g.fill(); }
  g.lineWidth = 5; g.strokeStyle = col; g.lineCap = 'round';
  for (let i = 0; i < 3; i++) { g.beginPath(); g.arc(912, 82, 8 + i * 9, -Math.PI * .75, -Math.PI * .25); g.stroke(); }
  rr(950, 52, 62, 30, 9); g.lineWidth = 3; g.stroke(); rr(955, 57, 46, 20, 5); g.fill(); rr(1015, 61, 5, 12, 2); g.fill();
  g.restore();
}
function touch(x, y, a, press = 0) {       // 触控点：白色圆点 + 按下缩小
  if (a <= 0) return;
  g.save(); g.globalAlpha *= a;
  const r = 44 * (1 - .18 * press);
  g.shadowColor = 'rgba(0,0,0,.35)'; g.shadowBlur = 24;
  g.fillStyle = 'rgba(255,255,255,.78)'; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
  g.shadowBlur = 0; g.lineWidth = 5; g.strokeStyle = 'rgba(255,255,255,.95)'; g.beginPath(); g.arc(x, y, r + 8, 0, 7); g.stroke();
  g.restore();
}
function ripple(x, y, p, col = '255,255,255') {
  if (p <= 0 || p >= 1) return;
  g.save(); g.lineWidth = 8 * (1 - p); g.strokeStyle = `rgba(${col},${.9 * (1 - p)})`;
  g.beginPath(); g.arc(x, y, 50 + 130 * eo(p), 0, 7); g.stroke(); g.restore();
}
function heart(cx, cy, s) {
  g.beginPath(); g.moveTo(cx, cy + s * .35);
  g.bezierCurveTo(cx - s * 1.1, cy - s * .35, cx - s * .45, cy - s * 1.05, cx, cy - s * .45);
  g.bezierCurveTo(cx + s * .45, cy - s * 1.05, cx + s * 1.1, cy - s * .35, cx, cy + s * .35); g.closePath();
}
function cross(cx, cy, s, lw) { g.lineWidth = lw; g.lineCap = 'round'; g.beginPath(); g.moveTo(cx - s, cy - s); g.lineTo(cx + s, cy + s); g.moveTo(cx + s, cy - s); g.lineTo(cx - s, cy + s); g.stroke(); }
function gradText(s, x, y, w) { g.fillStyle = grad(x - w / 2, y, x + w / 2, y, BRAND); g.fillText(s, x, y); }

// ======================= CHAT =======================
function drawChat(t) {
  const c = C, fs = c.fontSize || 56, lh = Math.round(fs * 1.42), pad = Math.round(fs * .62);
  const enter = eo(seg(t, 0, c.enterDur ?? .5));
  const INPUT_Y = c.inputY ?? 1470, LIST_BOTTOM = INPUT_Y - 150 - (c.chips && c.chips.length ? 90 : 0);
  // 背景
  g.save();
  if (c.bg?.blur) g.filter = `blur(${c.bg.blur * SS}px)`;
  const zs = 1.06 - .06 * enter;
  g.translate(W / 2, H / 2); g.scale(zs, zs); g.translate(-W / 2, -H / 2);
  cover(IMG[c.bg?.image], -20, -20, W + 40, H + 40, c.bg?.focusY ?? .35);
  g.restore(); g.filter = 'none';
  g.fillStyle = `rgba(10,6,24,${c.bg?.dim ?? .18})`; g.fillRect(0, 0, W, H);
  g.fillStyle = grad(0, 0, 0, 380, ['rgba(10,6,24,.62)', 'rgba(10,6,24,0)']); g.fillRect(0, 0, W, 380);
  g.fillStyle = grad(0, H * .42, 0, H, ['rgba(12,8,30,0)', 'rgba(12,8,30,.72)', 'rgba(12,8,30,.86)']); g.fillRect(0, H * .42, W, H * .58);

  g.save(); g.globalAlpha = enter; g.translate(0, 80 * (1 - enter));
  statusBar();
  // 顶栏：返回 / 头像 / 名字 / 在线 / 右侧图标
  g.strokeStyle = '#fff'; g.lineWidth = 7; g.lineCap = 'round'; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(84, 158); g.lineTo(60, 182); g.lineTo(84, 206); g.stroke();
  const av = IMG[c.avatar?.image || c.bg?.image];
  masked(() => { g.beginPath(); g.arc(170, 182, 52, 0, 7); }, () => cover(av, 118, 130, 104, 104, c.avatar?.focusY ?? .25, c.avatar?.focusX ?? .5));
  g.lineWidth = 4; g.strokeStyle = grad(118, 130, 222, 234, BRAND); g.beginPath(); g.arc(170, 182, 54, 0, 7); g.stroke();
  g.fillStyle = '#3BE07A'; g.beginPath(); g.arc(208, 220, 13, 0, 7); g.fill(); g.lineWidth = 4; g.strokeStyle = '#fff'; g.stroke();
  if (c.name) { g.fillStyle = '#fff'; font(54, 900); g.textAlign = 'left'; g.textBaseline = 'middle'; shadowText(c.name, 250, c.status ? 160 : 182); }
  if (c.status) { font(34, 500); g.fillStyle = 'rgba(255,255,255,.85)'; shadowText(c.status, 250, 212, 10); }
  // 右：电话 + 更多
  g.fillStyle = 'rgba(255,255,255,.22)'; g.beginPath(); g.arc(880, 182, 46, 0, 7); g.fill(); g.beginPath(); g.arc(990, 182, 46, 0, 7); g.fill();
  g.strokeStyle = '#fff'; g.lineWidth = 6;
  g.beginPath(); g.moveTo(864, 164); g.quadraticCurveTo(860, 204, 898, 202); g.stroke();
  g.fillStyle = '#fff'; for (let i = -1; i <= 1; i++) { g.beginPath(); g.arc(990 + i * 17, 182, 6, 0, 7); g.fill(); }
  g.restore();

  // ---- 消息流 ----
  const msgs = (c.messages || []).filter(m => !(m.from === 'user' && t < m.t));
  const items = [];
  for (const m of c.messages || []) {
    if (m.from !== 'user' && m.typing && t >= m.t - m.typing && t < m.t) items.push({ kind: 'typing', m, p: seg(t, m.t - m.typing, .22) });
    if (t >= m.t) items.push({ kind: 'msg', m, p: seg(t, m.t, .32) });
  }
  const MAXW = c.bubbleMaxW || 780;
  font(fs, 700);
  const lay = items.map(it => {
    const m = it.m;
    if (it.kind === 'typing') return { ...it, w: 210, h: 120 };
    if (m.type === 'image') { const iw = m.w || 560, ih = m.h || 700; return { ...it, w: iw, h: ih }; }
    font(fs, 700);
    const lines = m.text ? wrap(m.text, MAXW - pad * 2) : [];
    let w = Math.max(0, ...lines.map(l => g.measureText(l).width)) + pad * 2, h = lines.length * lh + pad * 1.5;
    if (m.voice) { w = Math.max(w, 340); h += 100; }
    if (!lines.length) h = m.voice ? 120 : 0;
    return { ...it, lines, w, h };
  });
  let y = LIST_BOTTOM; const GAP = 30;
  for (let i = lay.length - 1; i >= 0; i--) {
    const L = lay[i];
    // typing 指示消失时（消息出现）不占位
    const grow = L.kind === 'typing' ? eo(L.p) * (t < L.m.t ? 1 : 0) : eo(L.p);
    y -= (L.h + GAP) * grow; L.y = y; L.grow = grow;
  }
  const TOPY = c.listTop ?? 270;
  g.save(); g.globalAlpha = enter; g.beginPath(); g.rect(0, TOPY, W, H - TOPY); g.clip();
  for (const L of lay) {
    if (L.grow <= 0.001) continue;
    const m = L.m, isUser = m.from === 'user';
    const x = isUser ? W - 54 - L.w : 54;
    const fade = clamp((L.y + L.h * .5 - TOPY) / 200);      // 顶部淡出（列表区以上裁掉）
    const pop = eob(L.p, 1.4);
    g.save(); g.globalAlpha *= fade * clamp(L.p * 2.2);
    const ox = isUser ? x + L.w : x, oy = L.y + L.h;
    g.translate(ox, oy); g.scale(lerp(.6, 1, pop), lerp(.6, 1, pop)); g.translate(-ox, -oy);
    if (L.kind === 'typing') {
      g.fillStyle = 'rgba(255,255,255,.9)'; rr(x, L.y, L.w, L.h, [16, 48, 48, 48]); g.fill();
      for (let k = 0; k < 3; k++) { const b = Math.sin((t * 7) - k * .9); g.fillStyle = `rgba(143,91,255,${.45 + .4 * Math.max(0, b)})`; g.beginPath(); g.arc(x + 60 + k * 45, L.y + 60 - 10 * Math.max(0, b), 13, 0, 7); g.fill(); }
    } else if (m.type === 'image') {
      g.shadowColor = 'rgba(0,0,0,.35)'; g.shadowBlur = 30;
      rr(x, L.y, L.w, L.h, 44); g.fillStyle = '#fff'; g.fill(); g.shadowBlur = 0;
      masked(() => rr(x + 8, L.y + 8, L.w - 16, L.h - 16, 38), () => cover(IMG[m.image], x + 8, L.y + 8, L.w - 16, L.h - 16, m.focusY ?? .3, m.focusX ?? .5));
    } else {
      g.shadowColor = 'rgba(0,0,0,.28)'; g.shadowBlur = 26; g.shadowOffsetY = 6;
      if (isUser) { g.fillStyle = grad(x, L.y, x + L.w, L.y + L.h, ['rgba(62,48,120,.94)', 'rgba(36,26,70,.94)']); rr(x, L.y, L.w, L.h, [48, 16, 48, 48]); }
      else { g.fillStyle = 'rgba(255,255,255,.92)'; rr(x, L.y, L.w, L.h, [16, 48, 48, 48]); }
      g.fill(); g.shadowBlur = 0; g.shadowOffsetY = 0;
      let ty = L.y + pad * .75;
      if (m.voice) {      // 紫色语音胶囊
        const vw = 300, vh = 76, vx = x + pad, vy = ty + 4;
        g.fillStyle = grad(vx, vy, vx + vw, vy, ['#9B6BFF', '#C38BFF']); rr(vx, vy, vw, vh, 38); g.fill();
        g.fillStyle = '#fff'; g.beginPath(); g.moveTo(vx + 34, vy + 22); g.lineTo(vx + 34, vy + 54); g.lineTo(vx + 60, vy + 38); g.closePath(); g.fill();
        const play = clamp((t - m.t - .2) / (m.voice || 3));
        for (let k = 0; k < 9; k++) { const hh = 12 + 22 * Math.abs(Math.sin(k * 1.7 + (play > 0 && play < 1 ? t * 9 : 0))); g.globalAlpha *= 1; g.fillStyle = k / 9 < play ? '#fff' : 'rgba(255,255,255,.55)'; rr(vx + 82 + k * 17, vy + 38 - hh / 2, 8, hh, 4); g.fill(); }
        font(34, 700); g.fillStyle = '#fff'; g.textAlign = 'right'; g.textBaseline = 'middle'; g.fillText(`${Math.round(m.voice)}''`, vx + vw - 24, vy + 39);
        ty += 100;
      }
      font(fs, 700); g.textAlign = 'left'; g.textBaseline = 'top'; g.fillStyle = isUser ? '#fff' : INK;
      L.lines.forEach((ln, k) => g.fillText(ln, x + pad, ty + k * lh + (lh - fs) * .35));
    }
    g.restore();
  }
  g.restore();

  // ---- 底部：功能胶囊 + 输入框 ----
  g.save(); g.globalAlpha = enter; g.translate(0, 120 * (1 - enter));
  if (c.chips && c.chips.length) {
    font(38, 700); let cx = 54;
    for (const s of c.chips) { const w = g.measureText(s).width + 70; g.fillStyle = 'rgba(255,255,255,.2)'; rr(cx, INPUT_Y - 112, w, 82, 41); g.fill(); g.strokeStyle = 'rgba(255,255,255,.45)'; g.lineWidth = 2; g.stroke(); g.fillStyle = '#fff'; g.textAlign = 'left'; g.textBaseline = 'middle'; g.fillText(s, cx + 35, INPUT_Y - 70); cx += w + 20; }
  }
  // 当前输入中的用户消息
  let typing = null;
  for (const m of c.messages || []) if (m.from === 'user' && m.typeDur && t >= m.t - m.typeDur - .1 && t < m.t + .05) typing = m;
  const IH = 128;
  g.shadowColor = 'rgba(0,0,0,.3)'; g.shadowBlur = 30;
  g.fillStyle = 'rgba(255,255,255,.95)'; rr(54, INPUT_Y, 830, IH, IH / 2); g.fill(); g.shadowBlur = 0;
  // 灯泡
  g.strokeStyle = '#8F5BFF'; g.lineWidth = 6; g.beginPath(); g.arc(124, INPUT_Y + 56, 22, Math.PI * .8, Math.PI * 2.2); g.stroke();
  g.beginPath(); g.moveTo(112, INPUT_Y + 84); g.lineTo(136, INPUT_Y + 84); g.moveTo(115, INPUT_Y + 96); g.lineTo(133, INPUT_Y + 96); g.stroke();
  font(44, 700); g.textAlign = 'left'; g.textBaseline = 'middle';
  if (typing) {
    const p = clamp((t - (typing.t - typing.typeDur)) / (typing.typeDur * .82));
    const chars = [...typing.text.replace(/\n/g, '')]; let s = chars.slice(0, Math.round(chars.length * p)).join('');
    g.save(); rr(170, INPUT_Y, 690, IH, 0); g.clip();
    const tw = g.measureText(s).width; const off = Math.max(0, tw - 660);
    g.fillStyle = INK; g.fillText(s, 176 - off, INPUT_Y + IH / 2);
    if (Math.floor(t * 2.4) % 2 === 0 && t < typing.t - .2) { g.fillStyle = '#8F5BFF'; g.fillRect(180 - off + tw, INPUT_Y + 36, 5, 56); }
    g.restore();
  } else if (c.placeholder) { g.fillStyle = 'rgba(30,23,48,.42)'; g.fillText(c.placeholder, 176, INPUT_Y + IH / 2); }
  // 右侧：发送（输入中）或 +
  const sx = 960, sy = INPUT_Y + IH / 2;
  const sending = typing ? clamp((t - (typing.t - typing.typeDur)) / .25) : 0;
  g.fillStyle = sending ? grad(sx - 64, sy, sx + 64, sy, BRAND) : 'rgba(255,255,255,.95)';
  const press = typing ? Math.max(0, 1 - Math.abs(t - (typing.t - .08)) / .1) : 0;
  g.beginPath(); g.arc(sx, sy, 64 * (1 - .1 * press), 0, 7); g.fill();
  g.strokeStyle = sending ? '#fff' : '#8F5BFF'; g.lineWidth = 8; g.lineCap = 'round';
  if (sending) { g.beginPath(); g.moveTo(sx, sy + 26); g.lineTo(sx, sy - 24); g.moveTo(sx - 22, sy - 4); g.lineTo(sx, sy - 26); g.lineTo(sx + 22, sy - 4); g.stroke(); }
  else { g.beginPath(); g.moveTo(sx - 24, sy); g.lineTo(sx + 24, sy); g.moveTo(sx, sy - 24); g.lineTo(sx, sy + 24); g.stroke(); }
  g.restore();
  // 触控：点击发送
  for (const m of c.messages || []) if (m.from === 'user' && m.typeDur) {
    const a = clamp((t - (m.t - .55)) / .2) * (1 - clamp((t - (m.t + .25)) / .2));
    touch(sx + 40 * (1 - clamp((t - (m.t - .55)) / .35)), sy + 60 * (1 - eo(clamp((t - (m.t - .55)) / .35))), a, press);
    ripple(sx, sy, (t - (m.t - .08)) / .45);
  }
  if (c.tap) for (const tp of c.tap) { touch(tp.x, tp.y, clamp((t - tp.t + .4) / .2) * (1 - clamp((t - tp.t - .3) / .2)), Math.max(0, 1 - Math.abs(t - tp.t) / .1)); ripple(tp.x, tp.y, (t - tp.t) / .45); }
}

// ======================= SWIPE（照产品录屏：首页横滑卡片 → 点卡片 → 角色详情页） =======================
// 产品按钮/标签文字（来自产品录屏，可在 config.ui 覆盖）
const UI = Object.assign({ chat: 'チャット', chatGo: 'チャットに進む', tabs: ['キャラ情報', 'シナリオ', 'アルバム', 'グループ'],
  intro: '紹介', chara: 'キャラクター', nav: ['ホーム', '検索', '', 'チャット', 'マイ'] }, C.ui || {});
const BTN = ['#74E8D0', '#70B4FF', '#BBA0FF'];             // 产品「チャット」按钮渐变
const HC = { x: 70, y: 150, w: 940, h: 1500, r: 64, gap: 34 };   // 首页卡片
const TH = { x: 34, y: 262, w: 460, h: 600, r: 40, rot: -3 };   // 详情页左上缩略卡
const SHEET_Y = 950;
function swipePlan(c) {
  const n = (c.cards || []).length; let t = c.startAt ?? .5; const plan = [];
  for (let i = 0; i < n; i++) { const d = Math.max(c.minSwipe ?? .38, (c.firstSwipe ?? .8) * Math.pow(c.accel ?? .78, i)); plan.push({ i, t0: t, d }); t += d + (c.swipeGap ?? .12); }
  const heroAt = t, tapAt = heroAt + (c.heroHold ?? .8), openAt = tapAt + .12, openDur = .6;
  const profAt = openAt + openDur, chatTapAt = c.tapChat === false ? null : profAt + (c.profileHold ?? 2.2);
  const end = (chatTapAt ?? profAt + (c.profileHold ?? 2.2)) + (c.tail ?? .7);
  return { plan, heroAt, tapAt, openAt, openDur, profAt, chatTapAt, end };
}
function btnGrad(x, y, w, h) { return grad(x, y + h, x + w, y, BTN); }
function pillButton(x, y, w, h, label, fsz, press = 0, glow = 0) {
  g.save(); const cx = x + w / 2, cy = y + h / 2; g.translate(cx, cy); g.scale(1 - .05 * press, 1 - .05 * press); g.translate(-cx, -cy);
  if (glow) { g.shadowColor = `rgba(120,170,255,${.55 * glow})`; g.shadowBlur = 40; }
  g.fillStyle = btnGrad(x, y, w, h); rr(x, y, w, h, h / 2); g.fill(); g.shadowBlur = 0;
  if (label) { font(fsz, 700); g.fillStyle = INK; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(label, cx, cy + 2); }
  g.restore();
}
function starIcon(cx, cy, r, fill, stroke) {
  g.beginPath(); for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5, rr2 = k % 2 ? r * .5 : r; g.lineTo(cx + rr2 * Math.cos(a), cy + rr2 * Math.sin(a)); } g.closePath();
  g.lineJoin = 'round'; if (fill) { g.fillStyle = fill; g.fill(); } if (stroke) { g.strokeStyle = stroke; g.lineWidth = 6; g.stroke(); }
}
// 首页卡片内容（底部文字 + チャット 按钮）
function homeCardFace(cd, x, y, w, h, r, ui = 1) {
  masked(() => rr(x, y, w, h, r), () => {
  cover(IMG[cd.image], x, y, w, h, cd.focusY ?? .3, cd.focusX ?? .5);
  if (ui > 0) {
    g.globalAlpha = ui;
    g.fillStyle = grad(0, y + h * .45, 0, y + h, ['rgba(20,14,30,0)', 'rgba(20,14,30,.55)', 'rgba(20,14,30,.88)']); g.fillRect(x, y + h * .45, w, h * .55);
    const bx = x + 56, bw = w - 112, bh = 150, by = y + h - 56 - bh;
    pillButton(bx, by, bw, bh, UI.chat, 54);
    let ly = by - 60; g.textAlign = 'left'; g.textBaseline = 'alphabetic';
    if (cd.intro) { font(42, 500); const ls = wrap(cd.intro, bw).slice(0, 3); ly -= (ls.length - 1) * 60; g.fillStyle = '#fff'; ls.forEach((l, k) => shadowText(l, bx, ly + k * 60, 8)); ly -= 90; }
    if (cd.tags && cd.tags.length) {        // 标签胶囊：自动换行，从下往上
      font(38, 500); const rows = [[]]; let rw = 0;
      for (const s of cd.tags) { const tw = g.measureText(s).width + 56; if (rw + tw > bw && rows[rows.length - 1].length) { rows.push([]); rw = 0; } rows[rows.length - 1].push([s, tw]); rw += tw + 18; }
      for (let k = rows.length - 1; k >= 0; k--) { let tx = bx; for (const [s, tw] of rows[k]) { g.fillStyle = 'rgba(255,255,255,.2)'; rr(tx, ly - 52, tw, 74, 37); g.fill(); g.fillStyle = '#fff'; g.fillText(s, tx + 28, ly - 2); tx += tw + 18; } ly -= 92; }
      ly += 10;
    }
    if (cd.name) { let fs = 100; font(fs, 700); while (fs > 56 && g.measureText(cd.name).width > bw - 110) { fs -= 2; font(fs, 700); } g.fillStyle = '#fff'; shadowText(cd.name, bx, ly - 14, 18); }
    starIcon(x + w - 96, ly - 50, 34, 'rgba(255,255,255,.85)');
    g.fillStyle = 'rgba(255,255,255,.75)'; for (let k = 0; k < 3; k++) { g.beginPath(); g.arc(x + w - 110 + k * 22, y + 72, 6, 0, 7); g.fill(); }
  }
  });
}
function navBar(a) {
  if (a <= 0) return;
  g.save(); g.globalAlpha *= a; const y = 1690;
  g.fillStyle = '#fff'; g.fillRect(0, y, W, H - y);
  const xs = [150, 345, 540, 735, 930];
  for (let k = 0; k < 5; k++) {
    const x = xs[k], cy = y + 82, on = k === 0, col = on ? '#111' : '#9a9aa6';
    g.strokeStyle = col; g.fillStyle = col; g.lineWidth = 7; g.lineCap = 'round'; g.lineJoin = 'round';
    if (k === 2) { g.fillStyle = grad(x - 64, cy - 64, x + 64, cy + 64, ['#74E8D0', '#70B4FF', '#9F8BFF']); rr(x - 66, cy - 60, 132, 132, 40); g.fill(); g.fillStyle = INK; const s = 30; g.beginPath(); g.moveTo(x, cy + 6 - s); g.quadraticCurveTo(x + 4, cy + 2, x + s, cy + 6); g.quadraticCurveTo(x + 4, cy + 10, x, cy + 6 + s); g.quadraticCurveTo(x - 4, cy + 10, x - s, cy + 6); g.quadraticCurveTo(x - 4, cy + 2, x, cy + 6 - s); g.fill(); continue; }
    if (k === 0) { rr(x - 30, cy - 30, 60, 60, 16); g.stroke(); starIcon(x + 26, cy - 28, 14, '#111'); }
    if (k === 1) { g.beginPath(); g.arc(x - 6, cy - 6, 26, 0, 7); g.stroke(); g.beginPath(); g.moveTo(x + 14, cy + 14); g.lineTo(x + 32, cy + 32); g.stroke(); }
    if (k === 3) { g.beginPath(); g.ellipse(x, cy - 4, 34, 28, 0, 0, 7); g.stroke(); g.beginPath(); g.moveTo(x - 18, cy + 20); g.lineTo(x - 26, cy + 34); g.lineTo(x - 4, cy + 24); g.stroke(); g.fillStyle = '#FF5A4E'; g.beginPath(); g.arc(x + 30, cy - 30, 11, 0, 7); g.fill(); }
    if (k === 4) { g.beginPath(); g.arc(x, cy - 14, 18, 0, 7); g.stroke(); g.beginPath(); g.arc(x, cy + 40, 32, Math.PI * 1.15, Math.PI * 1.85); g.stroke(); g.fillStyle = '#FF5A4E'; g.beginPath(); g.arc(x + 28, cy - 32, 11, 0, 7); g.fill(); }
    if (UI.nav[k]) { font(30, on ? 700 : 500); g.fillStyle = col; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(UI.nav[k], x, cy + 66); }
  }
  g.fillStyle = '#222'; rr(W / 2 - 140, H - 26, 280, 10, 5); g.fill();
  g.restore();
}
function circleBtn(cx, cy, kind, a) {
  g.save(); g.globalAlpha *= a; g.fillStyle = 'rgba(70,60,70,.5)'; g.beginPath(); g.arc(cx, cy, 56, 0, 7); g.fill();
  g.strokeStyle = '#fff'; g.fillStyle = '#fff'; g.lineWidth = 7; g.lineCap = 'round'; g.lineJoin = 'round';
  if (kind === 'x') cross(cx, cy, 20, 8);
  if (kind === 'star') { g.fillStyle = 'rgba(255,255,255,.75)'; rr(cx - 30, cy - 30, 60, 60, 18); g.fill(); starIcon(cx, cy + 2, 18, 'rgba(70,60,70,.9)'); }
  if (kind === 'share') { g.beginPath(); g.moveTo(cx - 24, cy + 22); g.quadraticCurveTo(cx - 22, cy - 8, cx + 8, cy - 8); g.lineTo(cx + 8, cy - 24); g.lineTo(cx + 30, cy - 2); g.lineTo(cx + 8, cy + 18); g.lineTo(cx + 8, cy + 4); g.quadraticCurveTo(cx - 12, cy + 4, cx - 24, cy + 22); g.fill(); }
  if (kind === 'more') for (let k = -1; k <= 1; k++) { g.beginPath(); g.arc(cx + k * 20, cy, 7, 0, 7); g.fill(); }
  g.restore();
}
function profileInfo(hero, a, sx) {      // 详情页右上：名字 / 标签 / 简介
  if (a <= 0) return;
  g.save(); g.globalAlpha *= a; g.translate(sx, 0);
  const x = 540, w = 500; let y = 330; g.textAlign = 'left'; g.textBaseline = 'alphabetic';
  if (hero.name) { let fs = 76; font(fs, 700); while (fs > 44 && g.measureText(hero.name).width > w - 40) { fs -= 2; font(fs, 700); } g.fillStyle = '#fff'; shadowText(hero.name, x, y, 10); const nw = g.measureText(hero.name).width; g.strokeStyle = 'rgba(255,255,255,.8)'; g.lineWidth = 6; g.lineCap = 'round'; g.beginPath(); g.moveTo(x + nw + 28, y - 46); g.lineTo(x + nw + 44, y - 30); g.lineTo(x + nw + 28, y - 14); g.stroke(); y += 76; }
  if (hero.tags && hero.tags.length) { font(38, 700); g.fillStyle = '#fff'; { const rows = ['']; for (const s of hero.tags.map(s => '#' + s)) { const tt = rows[rows.length - 1] ? rows[rows.length - 1] + ' ' + s : s; if (g.measureText(tt).width > w && rows[rows.length - 1]) rows.push(s); else rows[rows.length - 1] = tt; } rows.slice(0, 2).forEach(l => { shadowText(l, x, y, 8); y += 54; }); } y += 20; }
  if (hero.intro) { font(34, 500); g.fillStyle = 'rgba(255,255,255,.72)'; const ls = wrap(hero.intro, w - 20); ls.slice(0, 4).forEach((l, k) => { g.fillText(k === 3 && ls.length > 4 ? l.slice(0, -1) + '…' : l, x, y); y += 50; }); }
  g.restore();
}
function sheet(hero, y0, a, t, P) {
  if (a <= 0) return;
  g.save(); g.globalAlpha *= a;
  g.shadowColor = 'rgba(0,0,0,.25)'; g.shadowBlur = 40; g.fillStyle = '#fff'; rr(0, y0, W, H - y0 + 60, [64, 64, 0, 0]); g.fill(); g.shadowBlur = 0;
  // tabs
  font(40, 700); g.textBaseline = 'middle'; g.textAlign = 'left'; let tx = 64;
  UI.tabs.forEach((s, k) => { if (!s) return; font(40, k ? 500 : 700); g.fillStyle = k ? '#9a9aa6' : '#111'; g.fillText(s, tx, y0 + 92); tx += g.measureText(s).width + 82; });
  let y = y0 + 170;
  const sec = (title, h, body) => {
    g.fillStyle = '#EEF4FF'; rr(52, y, W - 104, h, 44); g.fill();
    font(44, 700); const tw = g.measureText(title).width; g.fillStyle = 'rgba(110,225,240,.55)'; g.fillRect(86, y + 62, tw + 10, 30);
    g.fillStyle = '#111'; g.textAlign = 'left'; g.textBaseline = 'middle'; g.fillText(title, 90, y + 70);
    body(y + 130); y += h + 40;
  };
  if (hero.intro) { font(38, 500); const ls = wrap(hero.intro, W - 270).slice(0, 4); sec(UI.intro, 170 + ls.length * 58, by => { g.fillStyle = '#7c7c88'; g.textBaseline = 'top'; ls.forEach((l, k) => g.fillText(l, 90, by + k * 58 - 10)); }); }
  const thumbs = [hero.image, ...(hero.gallery || [])].slice(0, 3);
  sec(UI.chara, 520, by => thumbs.forEach((im, k) => { const tx2 = 90 + k * 290; masked(() => rr(tx2, by, 256, 340, 28), () => cover(IMG[im], tx2, by, 256, 340, im === hero.image ? hero.focusY ?? .3 : .3, .5)); }));
  g.restore();
  // 底部「チャットに進む」
  const bw = W - 108, bh = 160, bx = 54, by = H - 70 - bh;
  const press = P.chatTapAt != null ? Math.max(0, 1 - Math.abs(t - P.chatTapAt) / .1) : 0;
  g.save(); g.globalAlpha *= a; g.fillStyle = grad(0, by - 80, 0, by, ['rgba(255,255,255,0)', '#fff']); g.fillRect(0, by - 80, W, H - by + 80);
  pillButton(bx, by, bw, bh, UI.chatGo, 56, press, .6 + .4 * Math.sin(t * 5)); g.restore();
}
function drawSwipe(t) {
  const c = C, cards = c.cards || [], hero = c.hero || {}, P = swipePlan(c), all = [...cards, hero];
  // 横滑位置 pos（0..n）
  let pos = 0; for (const s of P.plan) pos += eio(seg(t, s.t0 + s.d * .2, s.d * .8));
  const cur = Math.min(all.length - 1, Math.round(pos));
  const op = eio(seg(t, P.openAt, P.openDur));       // 打开详情 0→1
  // 详情页上滑（可选 scrollUp px，scrollAt 秒=详情页打开后多久开始滑，默认 0 不滑）
  const SCR = (c.scrollUp || 0) * eio(seg(t, P.profAt + (c.scrollAt ?? .5), .7));
  // 背景：首页淡灰模糊 → 详情页暗色模糊
  g.save(); g.filter = `blur(${50 * SS}px)`; cover(IMG[all[cur].image], -100, -100, W + 200, H + 200, .3); g.restore(); g.filter = 'none';
  g.fillStyle = `rgba(236,234,242,${.72 * (1 - op)})`; g.fillRect(0, 0, W, H);
  g.fillStyle = `rgba(60,48,62,${.55 * op})`; g.fillRect(0, 0, W, H);
  const enter = eo(seg(t, 0, .4));
  g.save(); g.globalAlpha = enter;
  // 卡片
  const step = HC.w + HC.gap;
  for (let i = 0; i < all.length; i++) {
    const off = (i - pos) * step; if (Math.abs(off) > W) continue;
    const isHero = i === all.length - 1, sc = 1 - .05 * Math.min(1, Math.abs(i - pos));
    let x = HC.x + off, y = HC.y, w = HC.w, h = HC.h, r = HC.r, rot = 0;
    if (isHero && op > 0) { x = lerp(HC.x, TH.x, op); y = lerp(HC.y, TH.y, op) - SCR; w = lerp(HC.w, TH.w, op); h = lerp(HC.h, TH.h, op); r = lerp(HC.r, TH.r, op); rot = TH.rot * op; }
    else if (op > 0) { g.globalAlpha = enter * (1 - op); }
    const tapPress = isHero ? Math.max(0, 1 - Math.abs(t - P.tapAt) / .12) : 0;
    const cx = x + w / 2, cy = y + h / 2; g.save(); g.translate(cx, cy); g.rotate(rot * Math.PI / 180); g.scale(sc * (1 - .03 * tapPress), sc * (1 - .03 * tapPress)); g.translate(-cx, -cy);
    g.shadowColor = 'rgba(30,20,40,.35)'; g.shadowBlur = 40; g.shadowOffsetY = 14; g.fillStyle = '#222'; rr(x, y, w, h, r); g.fill(); g.shadowBlur = 0; g.shadowOffsetY = 0;
    homeCardFace(all[i], x, y, w, h, r, isHero ? 1 - clamp(op * 2.5) : 1);
    g.restore(); g.globalAlpha = enter;
  }
  statusBar(1, op > .5 ? '#fff' : '#111');
  navBar(1 - clamp(op * 2));
  // 详情页
  if (op > 0) {
    const pa = clamp((op - .6) / .4);
    circleBtn(100, 172, 'x', pa); circleBtn(780, 172, 'star', pa); circleBtn(900, 172, 'share', pa); circleBtn(1020, 172, 'more', pa);
    g.save(); g.translate(0, -SCR); profileInfo(hero, pa, 80 * (1 - pa)); g.restore();
    sheet(hero, lerp(H + 40, SHEET_Y, eo(seg(t, P.openAt + .12, P.openDur))) - SCR, 1, t, P);
    if (c.scrollUp) { const s0 = P.profAt + (c.scrollAt ?? .5), a = clamp((t - s0 + .2) / .15) * (1 - clamp((t - s0 - .75) / .15)), mv = eio(seg(t, s0, .7)); touch(W / 2 + 120, 1500 - c.scrollUp * mv, a, a > .5 ? 1 : 0); }
  }
  // 触控：横滑拖动
  for (const s of P.plan) {
    const a = clamp((t - s.t0 + .12) / .12) * (1 - clamp((t - s.t0 - s.d * .85) / .12));
    const drag = eio(seg(t, s.t0 + s.d * .1, s.d * .75));
    touch(820 - 560 * drag, 1060 - 30 * Math.sin(drag * Math.PI), a, a > .5 ? 1 : 0);
  }
  // 触控：点卡片
  { const a = clamp((t - (P.tapAt - .35)) / .15) * (1 - clamp((t - (P.tapAt + .2)) / .15)); const mv = eo(clamp((t - (P.tapAt - .35)) / .3));
    touch(600 + 80 * (1 - mv), 760 + 120 * (1 - mv), a, Math.max(0, 1 - Math.abs(t - P.tapAt) / .1)); ripple(600, 760, (t - P.tapAt) / .5); }
  // 触控：点「チャットに進む」
  if (P.chatTapAt != null) { const bx = W / 2 + 230, by = H - 150; const a = clamp((t - (P.chatTapAt - .4)) / .15) * (1 - clamp((t - (P.chatTapAt + .3)) / .2)); const mv = eo(clamp((t - (P.chatTapAt - .4)) / .3));
    touch(bx + 60 * (1 - mv), by - 140 * (1 - mv), a, Math.max(0, 1 - Math.abs(t - P.chatTapAt) / .1)); ripple(bx, by, (t - P.chatTapAt) / .5, '120,170,255'); }
  g.restore();
}

// ---------- 时长 / 音效时间点（给 python 混音用） ----------
function timeline() {
  const ev = [];
  if (C.template === 'chat') {
    for (const m of C.messages || []) {
      if (m.from === 'user') { ev.push(['send', m.t - .08]); if (m.typeDur) ev.push(['type', m.t - m.typeDur, m.typeDur * .82]); }
      else ev.push(['message', m.t]);
    }
    const last = Math.max(0, ...(C.messages || []).map(m => m.t));
    return { duration: C.duration || +(last + (C.tail ?? 1.6)).toFixed(3), events: ev };
  }
  const P = swipePlan(C);
  for (const s of P.plan) ev.push(['swipe', s.t0 + s.d * .45]);
  ev.push(['click', P.tapAt]); ev.push(['open', P.openAt]);
  if (P.chatTapAt != null) ev.push(['click', P.chatTapAt]);
  const dur = P.end;
  return { duration: C.duration || +dur.toFixed(3), events: ev };
}

function draw(t) {
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.filter = 'none'; g.fillStyle = '#000'; g.fillRect(0, 0, W * SS, H * SS); g.setTransform(SS, 0, 0, SS, 0, 0);
  if (C.template === 'chat') drawChat(t); else drawSwipe(t);
}
window.grabFrame = t => { draw(t); og.imageSmoothingEnabled = true; og.imageSmoothingQuality = 'high'; og.drawImage(cv, 0, 0, W, H); return out.toDataURL('image/png'); };
window.timeline = timeline;

(async () => {
  try {
    const f = new FontFace('MMJP', `url(${C.fonts.black})`, { weight: '900' }), f2 = new FontFace('MMJP', `url(${C.fonts.bold})`, { weight: '700' }), f3 = new FontFace('MMJP', `url(${C.fonts.medium})`, { weight: '500' });
    for (const x of [f, f2, f3]) document.fonts.add(await x.load());
    const paths = new Set(Object.values(C.assets || {}));
    const walk = o => { if (!o || typeof o !== 'object') return; for (const [k, v] of Object.entries(o)) { if ((k === 'image' || k === 'bg') && typeof v === 'string') paths.add(v); else if (k === 'gallery' && Array.isArray(v)) v.forEach(x => paths.add(x)); else walk(v); } };
    walk(C);
    await Promise.all([...paths].map(p => new Promise((res, rej) => { const im = new Image(); im.onload = () => { IMG[p] = im; res(); }; im.onerror = () => rej('图片加载失败 ' + p); im.src = p; })));
    for (const [k, v] of Object.entries(C.assets || {})) IMG[k] = IMG[v];
    window.__ready = true;
  } catch (e) { window.__err = String(e); }
})();
})();
