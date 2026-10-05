// Procedural textures drawn once at setup with a fixed seed (deterministic).
import * as THREE from 'three';
import { mulberry32 } from './util.js';

function canvas(w, h) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  return [c, c.getContext('2d')];
}

function tex(c, { srgb = false, repeat = [1, 1] } = {}) {
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat[0], repeat[1]);
  t.anisotropy = 4;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// Value-noise field painted as soft blobs (cheap, tileable enough for our use).
function blobs(ctx, w, h, rnd, n, rMin, rMax, aMin, aMax, light) {
  for (let i = 0; i < n; i++) {
    const x = rnd() * w, y = rnd() * h;
    const r = rMin + rnd() * (rMax - rMin);
    const a = aMin + rnd() * (aMax - aMin);
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    const v = light ? 255 : 0;
    g.addColorStop(0, `rgba(${v},${v},${v},${a})`);
    g.addColorStop(1, `rgba(${v},${v},${v},0)`);
    ctx.fillStyle = g;
    for (const dx of [-w, 0, w]) for (const dy of [-h, 0, h]) {
      ctx.save();
      ctx.translate(dx, dy);
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }
}

// Clay: soft lumps, finger smudges and tiny pits. Used as bump + roughness.
export function clayBump(seed = 7) {
  const rnd = mulberry32(seed);
  const [c, ctx] = canvas(512, 512);
  ctx.fillStyle = '#808080';
  ctx.fillRect(0, 0, 512, 512);
  blobs(ctx, 512, 512, rnd, 220, 20, 70, 0.04, 0.1, true);
  blobs(ctx, 512, 512, rnd, 220, 20, 70, 0.04, 0.1, false);
  // thumb smudges: short curved strokes
  ctx.lineCap = 'round';
  for (let i = 0; i < 40; i++) {
    const x = rnd() * 512, y = rnd() * 512, r = 14 + rnd() * 26, a0 = rnd() * 6.28;
    ctx.strokeStyle = `rgba(${rnd() < 0.5 ? 255 : 0},${0},${0},0)`;
    for (let k = 0; k < 4; k++) {
      const v = rnd() < 0.5 ? 255 : 0;
      ctx.strokeStyle = `rgba(${v},${v},${v},0.06)`;
      ctx.lineWidth = 3 + rnd() * 4;
      ctx.beginPath();
      ctx.arc(x, y, r + k * 4, a0, a0 + 1 + rnd());
      ctx.stroke();
    }
  }
  // pits
  for (let i = 0; i < 900; i++) {
    const v = rnd() < 0.7 ? 40 : 220;
    ctx.fillStyle = `rgba(${v},${v},${v},${0.15 + rnd() * 0.25})`;
    ctx.beginPath();
    ctx.arc(rnd() * 512, rnd() * 512, 0.6 + rnd() * 1.6, 0, 6.28);
    ctx.fill();
  }
  return tex(c);
}

export function woodPlanks(seed = 3) {
  const rnd = mulberry32(seed);
  const [c, ctx] = canvas(1024, 1024);
  const plankH = 128;
  for (let p = 0; p < 1024 / plankH; p++) {
    const base = [118 + rnd() * 30, 78 + rnd() * 20, 46 + rnd() * 14];
    ctx.fillStyle = `rgb(${base[0]},${base[1]},${base[2]})`;
    ctx.fillRect(0, p * plankH, 1024, plankH);
    // grain lines
    for (let g = 0; g < 70; g++) {
      const y0 = p * plankH + rnd() * plankH;
      const dark = rnd() < 0.6;
      ctx.strokeStyle = dark ? `rgba(40,20,8,${0.08 + rnd() * 0.18})` : `rgba(255,220,170,${0.05 + rnd() * 0.08})`;
      ctx.lineWidth = 0.6 + rnd() * 2.2;
      ctx.beginPath();
      const amp = 1 + rnd() * 5, f = 0.003 + rnd() * 0.01, ph = rnd() * 6;
      for (let x = 0; x <= 1024; x += 16) {
        const y = y0 + Math.sin(x * f + ph) * amp;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    // knots
    if (rnd() < 0.5) {
      const kx = rnd() * 1024, ky = p * plankH + 30 + rnd() * 68;
      for (let r = 18; r > 2; r -= 3) {
        ctx.strokeStyle = `rgba(50,25,10,${0.15})`;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.ellipse(kx, ky, r * 2.2, r, 0, 0, 6.28);
        ctx.stroke();
      }
    }
    // seam
    ctx.fillStyle = 'rgba(20,10,4,0.75)';
    ctx.fillRect(0, p * plankH, 1024, 3);
    // stains, scratches
    blobs(ctx, 1024, 1024, rnd, 6, 30, 90, 0.05, 0.12, false);
  }
  for (let i = 0; i < 120; i++) {
    ctx.strokeStyle = `rgba(255,230,200,${0.04 + rnd() * 0.06})`;
    ctx.lineWidth = 0.8;
    const x = rnd() * 1024, y = rnd() * 1024, l = 10 + rnd() * 60, a = rnd() * 6.28;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l);
    ctx.stroke();
  }
  return tex(c, { srgb: true, repeat: [3, 1.2] });
}

export function pegboard(seed = 11) {
  const rnd = mulberry32(seed);
  const [c, ctx] = canvas(1024, 1024);
  ctx.fillStyle = '#6e5238';
  ctx.fillRect(0, 0, 1024, 1024);
  blobs(ctx, 1024, 1024, rnd, 60, 40, 140, 0.04, 0.09, false);
  blobs(ctx, 1024, 1024, rnd, 40, 40, 140, 0.03, 0.06, true);
  const step = 64;
  for (let y = step / 2; y < 1024; y += step) {
    for (let x = step / 2; x < 1024; x += step) {
      ctx.fillStyle = '#1a120c';
      ctx.beginPath();
      ctx.arc(x, y, 7, 0, 6.28);
      ctx.fill();
      ctx.fillStyle = 'rgba(255,220,180,0.10)';
      ctx.beginPath();
      ctx.arc(x + 1, y + 2, 7, 0.2, 2.9);
      ctx.fill();
    }
  }
  return tex(c, { srgb: true, repeat: [3, 2] });
}

export function brushedMetal(seed = 5, tint = [150, 150, 155]) {
  const rnd = mulberry32(seed);
  const [c, ctx] = canvas(256, 256);
  ctx.fillStyle = `rgb(${tint[0]},${tint[1]},${tint[2]})`;
  ctx.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 400; i++) {
    const v = rnd() < 0.5 ? 255 : 0;
    ctx.strokeStyle = `rgba(${v},${v},${v},${0.03 + rnd() * 0.06})`;
    ctx.lineWidth = 0.5 + rnd();
    const y = rnd() * 256;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(256, y + (rnd() - 0.5) * 4);
    ctx.stroke();
  }
  blobs(ctx, 256, 256, rnd, 12, 10, 40, 0.05, 0.15, false); // grime
  return tex(c, { srgb: true });
}

// Can label for the scrap rocket: faded stripes and a stamped star
export function canLabel(seed = 9) {
  const rnd = mulberry32(seed);
  const [c, ctx] = canvas(512, 256);
  ctx.fillStyle = '#c9c4b8';
  ctx.fillRect(0, 0, 512, 256);
  ctx.fillStyle = '#2f5d7c';
  ctx.fillRect(0, 70, 512, 60);
  ctx.fillStyle = '#d9b44a';
  ctx.fillRect(0, 140, 512, 14);
  ctx.fillStyle = '#9b3d2e';
  ctx.fillRect(0, 160, 512, 30);
  // star
  ctx.fillStyle = '#efe6cf';
  ctx.beginPath();
  for (let i = 0; i < 10; i++) {
    const r = i % 2 ? 12 : 28, a = -Math.PI / 2 + (i * Math.PI) / 5;
    ctx.lineTo(256 + Math.cos(a) * r, 100 + Math.sin(a) * r);
  }
  ctx.fill();
  blobs(ctx, 512, 256, rnd, 30, 10, 50, 0.08, 0.2, false); // wear
  for (let i = 0; i < 200; i++) {
    ctx.fillStyle = `rgba(90,60,30,${rnd() * 0.25})`;
    ctx.fillRect(rnd() * 512, rnd() * 256, 1 + rnd() * 3, 1 + rnd() * 3);
  }
  const t = tex(c, { srgb: true });
  t.wrapT = THREE.ClampToEdgeWrapping;
  return t;
}

export function roofShingles(seed = 21) {
  const rnd = mulberry32(seed);
  const [c, ctx] = canvas(512, 512);
  ctx.fillStyle = '#2b2a33';
  ctx.fillRect(0, 0, 512, 512);
  const rowH = 32;
  for (let r = 0; r < 512 / rowH; r++) {
    const off = (r % 2) * 24;
    for (let x = -48; x < 512; x += 48) {
      const v = 34 + rnd() * 22;
      ctx.fillStyle = `rgb(${v},${v - 2},${v + 6})`;
      ctx.fillRect(x + off + 1, r * rowH + 1, 46, rowH - 3);
      ctx.fillStyle = 'rgba(0,0,0,0.5)';
      ctx.fillRect(x + off + 1, r * rowH + rowH - 4, 46, 3);
    }
  }
  return tex(c, { srgb: true, repeat: [6, 6] });
}

// Soft radial sprite (smoke / glow)
export function softDot(inner = 'rgba(255,255,255,1)', mid = 'rgba(255,255,255,0.35)') {
  const [c, ctx] = canvas(128, 128);
  const g = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, inner);
  g.addColorStop(0.4, mid);
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export function smokePuff(seed = 31) {
  const rnd = mulberry32(seed);
  const [c, ctx] = canvas(256, 256);
  for (let i = 0; i < 26; i++) {
    const a = rnd() * 6.28, d = rnd() * 60;
    const x = 128 + Math.cos(a) * d, y = 128 + Math.sin(a) * d, r = 30 + rnd() * 50;
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, 'rgba(255,255,255,0.22)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 256, 256);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
