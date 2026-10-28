const clamp = (v, a=0, b=1) => Math.max(a, Math.min(b, v));
const ease = x => { x = clamp(x); return x < .5 ? 4*x*x*x : 1 - Math.pow(-2*x+2, 3)/2; };
const out = x => 1 - Math.pow(1 - clamp(x), 3);
const back = x => { x = clamp(x); const c1 = 1.5, c3 = c1 + 1; return 1 + c3*Math.pow(x-1,3) + c1*Math.pow(x-1,2); };
const span = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const win = (t, a, b, f=.35) => Math.min(out(span(t, a, a+f)), 1 - ease(span(t, b-f, b)));  // in/out envelope


const TABLES = {1:[30,156,66,34,"b"],2:[30,114,66,34,"b"],3:[30,72,66,34,"b"],4:[30,30,66,34,"b"],5:[108,114,66,34,"b"],
  6:[108,72,66,34,"b"],7:[108,30,66,34,"b"],8:[186,128,66,62,"g"],9:[194,98,50,24,"j"],10:[186,30,66,62,"g"],11:[264,72,66,34,"b"],12:[264,30,66,34,"b"]};
const K = 2.05;                       // room units -> px before camera
function iso(x, y, z=0) { return [(x - y) * K * 0.866, (x + y) * K * 0.5 - z * K]; }
function poly(pts, fill, stroke) { ctx.beginPath(); pts.forEach((p,i) => i ? ctx.lineTo(p[0],p[1]) : ctx.moveTo(p[0],p[1])); ctx.closePath();
  if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 1.2; ctx.stroke(); } }
function box(x, y, w, h, z0, z1, top, left, right) {
  const a = iso(x,y,z1), b = iso(x+w,y,z1), c = iso(x+w,y+h,z1), d = iso(x,y+h,z1);
  const b0 = iso(x+w,y,z0), c0 = iso(x+w,y+h,z0), d0 = iso(x,y+h,z0);
  poly([d, c, c0, d0], left);  poly([b, c, c0, b0], right);  poly([a, b, c, d], top);
}
/* ---------- THE CAST (original characters, drawn in code) ----------
   Every figure is a spec: skin, outfit, hair or headwear, accessories. Big heads, real eyes that blink
   and look at their phones, blush, and a face that changes when the food lands. */
const SKIN = ["#8d5a3b","#c68b5e","#6b4128","#e0ac7e","#a8714a","#f1c8a0"];
const TOPS = ["#3E6B4F","#C9A227","#2f4a6b","#B23A1E","#e8e0d2","#5b3f6e","#1f6f6a","#d4743a"];
const HAIRS = ["bob","short","hijab","cap","bun","curly","bald","pony"];
const CAST = {
  dad:   {skin:"#a8714a", top:"#2f4a6b", hair:"kufi", beard:true, hc:"#f3ece0"},
  mom:   {skin:"#c68b5e", top:"#1f6f6a", hair:"hijab", hc:"#C9A227"},
  teen:  {skin:"#c68b5e", top:"#B23A1E", hair:"pony", hc:"#1c1612", headphones:true},
  kid:   {skin:"#a8714a", top:"#d4743a", hair:"cowlick", hc:"#1c1612", glasses:true, small:true},
  chef:  {skin:"#8d5a3b", top:"#fbf8f2", hair:"toque", mustache:true, apron:true, hc:"#fff"},
  runner:{skin:"#e0ac7e", top:"#3E6B4F", hair:"bandana", hc:"#B23A1E", apron:true},
};
function crowd(seed) { const r = n => (Math.abs(Math.sin(seed*91.7 + n*13.1)) * 1000) | 0;
  return {skin: SKIN[r(1)%SKIN.length], top: TOPS[r(2)%TOPS.length], hair: HAIRS[r(3)%HAIRS.length],
          hc: ["#1c1612","#4a2f1d","#C9A227","#6b2a1a","#2b2b2b","#7a7a7a"][r(4)%6], beard: r(5)%5===0, glasses: r(6)%6===0}; }
const hash = (a, b=0) => { const x = Math.sin(a*127.1 + b*311.7) * 43758.5453; return x - Math.floor(x); };
function blinkAt(t, seed) { const per = 2.6 + hash(seed)*2.4, ph = (t + hash(seed,1)*per) % per; return ph < .12; }
function char(sx, sy, spec, o={}) {
  const t = o.t || 0, s = (o.scale || 1) * (spec.small ? .82 : 1), seed = o.seed || 1;
  const bob = o.walk ? -Math.abs(Math.sin(t*9 + seed)) * 5 : Math.sin(t*2.1 + seed) * 1.1;
  const happy = o.happy || 0, look = o.look ?? .35;
  ctx.save(); ctx.translate(sx, sy); ctx.scale(s, s);
  ctx.fillStyle = "rgba(0,0,0,.30)"; ctx.beginPath(); ctx.ellipse(0, 2, 15, 5.5, 0, 0, 7); ctx.fill();
  ctx.translate(0, bob);
  // body with soft shading
  const bg = ctx.createLinearGradient(-14, -34, 14, 0); bg.addColorStop(0, spec.top); bg.addColorStop(1, mix(spec.top, "#000000", .28));
  ctx.fillStyle = bg; ctx.beginPath(); ctx.moveTo(-14, 0); ctx.quadraticCurveTo(-16, -30, 0, -32); ctx.quadraticCurveTo(16, -30, 14, 0); ctx.closePath(); ctx.fill();
  if (spec.apron) { ctx.fillStyle = "#fffdf8"; ctx.beginPath(); ctx.roundRect(-8, -24, 16, 22, 4); ctx.fill(); ctx.strokeStyle = "rgba(0,0,0,.12)"; ctx.lineWidth = 1; ctx.stroke(); }
  // arms: holding a phone, a tray, a wok, or waving
  ctx.strokeStyle = mix(spec.top, "#000000", .15); ctx.lineWidth = 6; ctx.lineCap = "round";
  if (o.phone) { ctx.beginPath(); ctx.moveTo(-9, -24); ctx.quadraticCurveTo(-4, -12, 4, -16); ctx.moveTo(9, -24); ctx.quadraticCurveTo(12, -14, 6, -15); ctx.stroke();
    ctx.fillStyle = "#111"; ctx.beginPath(); ctx.roundRect(1, -27, 10, 15, 2); ctx.fill();
    const gl = .7 + .3*Math.sin(t*5 + seed); ctx.fillStyle = `rgba(255,236,180,${gl})`; ctx.fillRect(2.5, -25.5, 7, 12);
    const rg = ctx.createRadialGradient(6, -38, 2, 6, -38, 26); rg.addColorStop(0, `rgba(255,226,150,${.28*gl})`); rg.addColorStop(1, "rgba(255,226,150,0)"); ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(6, -38, 26, 0, 7); ctx.fill(); }
  else if (o.tray) { ctx.beginPath(); ctx.moveTo(10, -24); ctx.lineTo(18, -30); ctx.stroke(); ctx.fillStyle = "#cfc6b8"; ctx.beginPath(); ctx.ellipse(20, -32, 16, 5, 0, 0, 7); ctx.fill();
    plate(16, -36, "#d9a441"); plate(25, -36, "#c27a32"); steam(20, -44, t, seed, 3, .9); }
  else if (o.wok) { const flip = Math.max(0, Math.sin(t*7)); ctx.beginPath(); ctx.moveTo(10, -22); ctx.lineTo(22, -26 - flip*6); ctx.stroke();
    ctx.fillStyle = "#2a2a2a"; ctx.beginPath(); ctx.ellipse(28, -26 - flip*6, 12, 5, -.2, 0, Math.PI); ctx.fill(); ctx.strokeStyle = "#2a2a2a"; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(16, -27-flip*6); ctx.lineTo(8, -30-flip*6); ctx.stroke();
    if (o.fire) { for (let i = 0; i < 6; i++) { const ph = (t*2.2 + i/6) % 1; ctx.strokeStyle = `rgba(214,170,70,${(1-ph)*.95})`; ctx.lineWidth = 2.2;
      ctx.beginPath(); ctx.arc(28 + (i-2.5)*2, -28 - flip*6 - ph*34, 6 + i, Math.PI*1.1, Math.PI*1.6); ctx.stroke(); } } }   // noodles in the air
  else if (o.raise) { const w = Math.sin(t*7) * 2; ctx.beginPath(); ctx.moveTo(10, -24); ctx.quadraticCurveTo(18, -40, 15 + w, -62); ctx.stroke();
    ctx.fillStyle = spec.skin; ctx.beginPath(); ctx.arc(15 + w, -64, 4.5, 0, 7); ctx.fill(); }
  else if (o.bag) { ctx.beginPath(); ctx.moveTo(10, -24); ctx.lineTo(16, -14); ctx.stroke();
    ctx.fillStyle = "#c9a36a"; ctx.beginPath(); ctx.roundRect(11, -14, 16, 18, 2); ctx.fill(); ctx.fillStyle = C.spice; ctx.fillRect(14, -9, 10, 3);
    ctx.strokeStyle = "#8a6a3a"; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(19, -14, 4, Math.PI, 0); ctx.stroke(); }
  else if (o.wave) { const w = Math.sin(t*10) * .5; ctx.beginPath(); ctx.moveTo(10, -24); ctx.lineTo(18 + w*4, -44); ctx.stroke(); }
  else { ctx.beginPath(); ctx.moveTo(-10, -24); ctx.lineTo(-12, -8); ctx.moveTo(10, -24); ctx.lineTo(12, -8); ctx.stroke(); }
  // head
  const hy = -46, hr = 14;
  if (spec.hair === "hijab") { ctx.fillStyle = spec.hc; ctx.beginPath(); ctx.ellipse(0, hy + 2, hr + 4, hr + 6, 0, 0, 7); ctx.fill();
    ctx.fillStyle = mix(spec.hc, "#000000", .18); ctx.beginPath(); ctx.moveTo(-16, hy+8); ctx.quadraticCurveTo(0, hy+26, 16, hy+8); ctx.lineTo(12, hy+20); ctx.quadraticCurveTo(0, hy+30, -12, hy+20); ctx.closePath(); ctx.fill(); }
  const hg = ctx.createRadialGradient(-4, hy - 5, 2, 0, hy, hr + 2); hg.addColorStop(0, mix(spec.skin, "#ffffff", .18)); hg.addColorStop(1, spec.skin);
  ctx.fillStyle = hg; ctx.beginPath(); ctx.arc(0, hy, hr, 0, 7); ctx.fill();
  ctx.fillStyle = spec.skin; ctx.beginPath(); ctx.arc(-hr + 1, hy + 1, 3, 0, 7); ctx.arc(hr - 1, hy + 1, 3, 0, 7); ctx.fill();   // ears
  // hair and headwear
  ctx.fillStyle = spec.hc;
  switch (spec.hair) {
    case "kufi": ctx.beginPath(); ctx.ellipse(0, hy - 9, 12.5, 7, 0, Math.PI, 0); ctx.fill(); ctx.fillRect(-12.5, hy - 10, 25, 3); ctx.strokeStyle = C.gold; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(-12, hy-9); ctx.lineTo(12, hy-9); ctx.stroke(); break;
    case "hijab": ctx.beginPath(); ctx.arc(0, hy - 1, hr + 3, Math.PI*1.02, Math.PI*1.98); ctx.fill(); break;
    case "pony": ctx.beginPath(); ctx.arc(0, hy - 3, hr + 1, Math.PI*1.05, Math.PI*1.95); ctx.fill(); ctx.beginPath(); ctx.ellipse(hr + 3, hy - 4 + Math.sin(t*4+seed)*1.5, 5, 10, .5, 0, 7); ctx.fill(); break;
    case "cowlick": ctx.beginPath(); ctx.arc(0, hy - 3, hr + 1, Math.PI*1.08, Math.PI*1.92); ctx.fill(); ctx.beginPath(); ctx.moveTo(-2, hy-15); ctx.quadraticCurveTo(4, hy-26, 8, hy-18); ctx.quadraticCurveTo(4, hy-20, 2, hy-14); ctx.fill(); break;
    case "toque": ctx.fillStyle = "#fff"; ctx.fillRect(-11, hy - 22, 22, 12); ctx.beginPath(); ctx.arc(-6, hy - 24, 8, 0, 7); ctx.arc(6, hy - 24, 8, 0, 7); ctx.arc(0, hy - 30, 9, 0, 7); ctx.fill(); ctx.strokeStyle = "#e6e0d6"; ctx.lineWidth = 1; ctx.strokeRect(-11, hy - 14, 22, 4); break;
    case "bandana": ctx.beginPath(); ctx.arc(0, hy - 2, hr + 1, Math.PI*1.05, Math.PI*1.95); ctx.fill(); ctx.beginPath(); ctx.moveTo(-hr, hy - 4); ctx.lineTo(-hr - 9, hy + 2 + Math.sin(t*6)*2); ctx.lineTo(-hr - 3, hy - 1); ctx.fill();
      ctx.fillStyle = "#fff"; for (let i = -2; i <= 2; i++) { ctx.beginPath(); ctx.arc(i*5, hy - 10, 1.2, 0, 7); ctx.fill(); } break;
    case "bob": ctx.beginPath(); ctx.arc(0, hy - 2, hr + 2, Math.PI*.95, Math.PI*2.05); ctx.fill(); ctx.fillRect(-hr - 2, hy - 2, 5, 12); ctx.fillRect(hr - 3, hy - 2, 5, 12); break;
    case "short": ctx.beginPath(); ctx.arc(0, hy - 3, hr + .5, Math.PI*1.1, Math.PI*1.9); ctx.fill(); break;
    case "cap": ctx.fillStyle = spec.top === "#C9A227" ? "#2f4a6b" : "#C9A227"; ctx.beginPath(); ctx.arc(0, hy - 4, hr, Math.PI, 0); ctx.fill(); ctx.fillRect(0, hy - 6, 18, 3.5); break;
    case "bun": ctx.beginPath(); ctx.arc(0, hy - 3, hr + 1, Math.PI*1.05, Math.PI*1.95); ctx.fill(); ctx.beginPath(); ctx.arc(0, hy - 18, 6, 0, 7); ctx.fill(); break;
    case "curly": for (let i = 0; i < 7; i++) { ctx.beginPath(); ctx.arc(-12 + i*4, hy - 11 - Math.sin(i)*2, 5, 0, 7); ctx.fill(); } break;
  }
  if (spec.headphones) { ctx.strokeStyle = "#1a1a1a"; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(0, hy - 2, hr + 2, Math.PI*1.1, Math.PI*1.9); ctx.stroke(); ctx.fillStyle = "#C9A227"; ctx.beginPath(); ctx.roundRect(-hr - 4, hy - 4, 6, 10, 3); ctx.roundRect(hr - 2, hy - 4, 6, 10, 3); ctx.fill(); }
  // face
  const lx = look * 3, ly = o.phone ? 2.5 : 0, bl = blinkAt(t, seed);
  if (happy > .5) { ctx.strokeStyle = "#1c1612"; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(-5, hy + 1, 3, Math.PI*1.1, Math.PI*1.9); ctx.moveTo(8, hy + 1); ctx.arc(5, hy + 1, 3, Math.PI*1.1, Math.PI*1.9); ctx.stroke(); }
  else if (bl) { ctx.strokeStyle = "#1c1612"; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-8, hy); ctx.lineTo(-2, hy); ctx.moveTo(2, hy); ctx.lineTo(8, hy); ctx.stroke(); }
  else { ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.ellipse(-5, hy, 3.6, 4.2, 0, 0, 7); ctx.ellipse(5, hy, 3.6, 4.2, 0, 0, 7); ctx.fill();
    ctx.fillStyle = "#1c1612"; ctx.beginPath(); ctx.arc(-5 + lx, hy + ly*.6, 2.1, 0, 7); ctx.arc(5 + lx, hy + ly*.6, 2.1, 0, 7); ctx.fill();
    ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(-4.3 + lx, hy - 1 + ly*.6, .8, 0, 7); ctx.arc(5.7 + lx, hy - 1 + ly*.6, .8, 0, 7); ctx.fill(); }
  if (spec.glasses) { ctx.strokeStyle = "#2a1f16"; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.arc(-5, hy, 5, 0, 7); ctx.moveTo(10, hy); ctx.arc(5, hy, 5, 0, 7); ctx.moveTo(0, hy); ctx.lineTo(0, hy); ctx.stroke(); }
  ctx.fillStyle = "rgba(226,104,90,.38)"; ctx.beginPath(); ctx.ellipse(-8.5, hy + 5.5, 3, 2, 0, 0, 7); ctx.ellipse(8.5, hy + 5.5, 3, 2, 0, 0, 7); ctx.fill();
  if (spec.beard) { ctx.fillStyle = spec.hair === "kufi" ? "#2b1d14" : spec.hc; ctx.beginPath(); ctx.moveTo(-12, hy + 2); ctx.quadraticCurveTo(0, hy + 22, 12, hy + 2); ctx.quadraticCurveTo(0, hy + 10, -12, hy + 2); ctx.fill(); }
  if (spec.mustache) { ctx.fillStyle = "#1c1612"; ctx.beginPath(); ctx.moveTo(0, hy + 6); ctx.quadraticCurveTo(-6, hy + 3, -10, hy + 7); ctx.quadraticCurveTo(-6, hy + 9, 0, hy + 7.5); ctx.quadraticCurveTo(6, hy + 9, 10, hy + 7); ctx.quadraticCurveTo(6, hy + 3, 0, hy + 6); ctx.fill(); }
  ctx.strokeStyle = "#5a2a1a"; ctx.lineWidth = 1.8; ctx.beginPath();
  if (happy > .5 || o.talk) { ctx.fillStyle = "#6b2016"; ctx.ellipse(0, hy + 9, 3.6, 2.6 + (o.talk ? Math.abs(Math.sin(t*14))*1.6 : 1), 0, 0, 7); ctx.fill(); }
  else { ctx.arc(0, hy + 6, 4, Math.PI*.2, Math.PI*.8); ctx.stroke(); }
  ctx.restore();
}
function person(x, y, seed, o={}) { const [sx, sy] = iso(x, y, o.z || 0); char(sx, sy, o.spec || crowd(seed), {...o, seed}); }
function plate(x, y, c) { ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.ellipse(x, y, 7, 3, 0, 0, 7); ctx.fill(); ctx.fillStyle = c; ctx.beginPath(); ctx.ellipse(x, y - 1, 4.6, 2, 0, 0, 7); ctx.fill(); }
/* stateless particles: each one's age comes from time, so any frame renders on its own */
function steam(x, y, t, seed, n=3, a=.7) { for (let i = 0; i < n; i++) { const ph = (t*.5 + i/n + hash(seed,i)) % 1;
  ctx.strokeStyle = `rgba(255,255,255,${a*Math.sin(ph*Math.PI)*.55})`; ctx.lineWidth = 2; ctx.beginPath();
  const bx = x + (i - (n-1)/2) * 4; ctx.moveTo(bx, y); ctx.bezierCurveTo(bx + 4*Math.sin(t*2+i), y - 8 - ph*10, bx - 4, y - 14 - ph*14, bx + 2*Math.sin(t*3+i), y - 20 - ph*18); ctx.stroke(); } }
function embers(x, y, t, n, power) { for (let i = 0; i < n; i++) { const ph = (t*1.4 + hash(i, 7)) % 1, dx = (hash(i,3) - .5) * 60;
  ctx.fillStyle = `rgba(255,${150 + hash(i,5)*90|0},60,${(1-ph)*power})`; ctx.beginPath(); ctx.arc(x + dx*ph + Math.sin(t*6+i)*3, y - ph*90*(.6+hash(i,4)), 1.4 + hash(i,2)*1.6, 0, 7); ctx.fill(); } }
function burst(x, y, k, n, colors, spread=180, size=10) { if (k <= 0 || k >= 1) return; for (let i = 0; i < n; i++) {
  const ang = hash(i, 11) * Math.PI * 2, sp = spread * (.4 + .6*hash(i,12)), px = x + Math.cos(ang)*sp*out(k), py = y + Math.sin(ang)*sp*out(k) + 220*k*k;
  ctx.save(); ctx.translate(px, py); ctx.rotate(k * 8 * (hash(i,13) - .5) * 3); ctx.globalAlpha *= (1 - k);
  ctx.fillStyle = colors[i % colors.length]; if (i % 3) ctx.fillRect(-size/2, -size/4, size, size/2); else { ctx.beginPath(); ctx.arc(0, 0, size/2.4, 0, 7); ctx.fill(); }
  ctx.restore(); } }
function sparkle(x, y, k, n=8, r=70) { if (k <= 0 || k >= 1) return; for (let i = 0; i < n; i++) { const ang = i/n*Math.PI*2 + hash(i,21), d = r*out(k);
  star(x + Math.cos(ang)*d, y + Math.sin(ang)*d, 9*(1-k) + 3, `rgba(201,162,39,${1-k})`); } }
function star(x, y, r, c) { ctx.fillStyle = c; ctx.beginPath(); for (let i = 0; i < 8; i++) { const rr2 = i % 2 ? r*.35 : r, a = i*Math.PI/4; ctx.lineTo(x + Math.cos(a)*rr2, y + Math.sin(a)*rr2); } ctx.closePath(); ctx.fill(); }
function heart(x, y, s, c) { ctx.fillStyle = c; ctx.beginPath(); ctx.moveTo(x, y + s*.3); ctx.bezierCurveTo(x, y, x - s*.5, y, x - s*.5, y + s*.3); ctx.bezierCurveTo(x - s*.5, y + s*.6, x, y + s*.8, x, y + s); ctx.bezierCurveTo(x, y + s*.8, x + s*.5, y + s*.6, x + s*.5, y + s*.3); ctx.bezierCurveTo(x + s*.5, y, x, y, x, y + s*.3); ctx.fill(); }
function bokeh(t) { for (let i = 0; i < 26; i++) { const x = (hash(i,31)*W + t*(8 + hash(i,32)*14)) % W, y = 560 + hash(i,33)*1300 + Math.sin(t*.6 + i)*20, r = 6 + hash(i,34)*22;
  const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, `rgba(201,162,39,${.10 + .08*Math.sin(t+i)})`); g.addColorStop(1, "rgba(201,162,39,0)"); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); } }

/* who sits where: [table, seat offsets] - a busy evening, table 5 is our family */
const SEATED = [[2,2],[4,3],[7,2],[10,4],[12,2]];
function seatPos(n, i, cnt) {
  const [x,y,w,h,k] = TABLES[n];
  const side = i % 2, col = Math.floor(i/2), cols = Math.ceil(cnt/2);
  return [x + w*(col+0.5)/Math.max(cols,1), side ? y + h + 8 : y - 8];
}
function food(x, y, n, t) { for (let i = 0; i < n; i++) { const [px,py] = iso(x + 10 + i*16, y + 12, 12);
  ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.ellipse(px, py, 9, 5, 0, 0, 7); ctx.fill();
  ctx.fillStyle = i % 2 ? "#c98a2b" : "#b5652a"; ctx.beginPath(); ctx.ellipse(px, py-1, 6, 3.2, 0, 0, 7); ctx.fill(); } }


function mix(a, b, k) { const pa = parseInt(a.slice(1),16), pb = parseInt(b.slice(1),16);
  const r = Math.round(lerp(pa>>16, pb>>16, k)), g = Math.round(lerp((pa>>8)&255, (pb>>8)&255, k)), bl = Math.round(lerp(pa&255, pb&255, k));
  return "#" + ((1<<24) + (r<<16) + (g<<8) + bl).toString(16).slice(1); }
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function phone(img, cx, cy, w, alpha, opts={}) {
  if (alpha <= 0 || !img) return;
  const h = w * 2.164, x = cx - w/2, y = cy - h/2;
  ctx.save(); ctx.globalAlpha = alpha;
  ctx.shadowColor = "rgba(0,0,0,.55)"; ctx.shadowBlur = 60; ctx.shadowOffsetY = 24;
  rr(x-14, y-14, w+28, h+28, 62); ctx.fillStyle = "#0c0b0a"; ctx.fill(); ctx.shadowColor = "transparent";
  rr(x-14, y-14, w+28, h+28, 62); ctx.strokeStyle = "rgba(201,162,39,.55)"; ctx.lineWidth = 2; ctx.stroke();
  ctx.save(); rr(x, y, w, h, 48); ctx.clip();
  const sy = opts.scroll || 0, ih = img.height * (w / img.width);
  ctx.drawImage(img, x, y - sy * Math.max(0, ih - h), w, ih);
  if (opts.fade && opts.next) { ctx.globalAlpha = alpha * opts.fade; ctx.drawImage(opts.next, x, y, w, opts.next.height * (w / opts.next.width)); }
  ctx.restore();
  rr(cx - 60, y + 12, 120, 30, 15); ctx.fillStyle = "#0c0b0a"; ctx.fill();               // the notch
  if (opts.tap != null && opts.tap >= 0 && opts.tap <= 1) {                              // a finger tap
    const [fx, fy] = [x + w*opts.tx, y + h*opts.ty], k = opts.tap;
    ctx.strokeStyle = `rgba(201,162,39,${1-k})`; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(fx, fy, 18 + 46*k, 0, 7); ctx.stroke();
    ctx.fillStyle = `rgba(255,255,255,${.55*(1-k)})`; ctx.beginPath(); ctx.arc(fx, fy, 20, 0, 7); ctx.fill();
  }
  ctx.restore();
}
function words(str, x, y, font, color, lt, alpha, maxW, lh) {
  ctx.font = font; let cx = x, cy = y;
  str.split(" ").forEach((w, i) => { const ww = ctx.measureText(w + " ").width; if (cx + ctx.measureText(w).width > x + maxW) { cx = x; cy += lh; }
    const k = back(clamp((lt - i*.06) / .42)), a = clamp((lt - i*.06) / .25);
    ctx.globalAlpha = alpha * a; ctx.fillStyle = color; ctx.fillText(w, cx, cy + (1 - k) * 34); cx += ww; });
  ctx.globalAlpha = alpha; return cy;
}
function wrap(s, x, y, maxW, lh) { const words = s.split(" "); let line = "", yy = y;
  for (const w of words) { const test = line ? line + " " + w : w; if (ctx.measureText(test).width > maxW && line) { ctx.fillText(line, x, yy); line = w; yy += lh; } else line = test; }
  ctx.fillText(line, x, yy); }
function pill(text, x, y, bg, fg, font="700 30px Inter", pad=26, h=60) {
  ctx.font = font; const w = ctx.measureText(text).width + pad*2; rr(x - w/2, y - h/2, w, h, h/2); ctx.fillStyle = bg; ctx.fill();
  ctx.fillStyle = fg; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(text, x, y + 1); ctx.textBaseline = "alphabetic"; return w; }
function bell(x, y, t) { ctx.save(); ctx.translate(x, y); ctx.rotate(Math.sin(t*18)*.25); ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.moveTo(-14, 10); ctx.quadraticCurveTo(-14, -16, 0, -16); ctx.quadraticCurveTo(14, -16, 14, 10); ctx.closePath(); ctx.fill(); ctx.beginPath(); ctx.arc(0, 13, 4, 0, 7); ctx.fill(); ctx.restore(); }
