// Particle effects: sparks, flames, smoke, fireworks, glass shards.
// Every particle's state is a closed-form function of (t, particle index, fixed seed).
import * as THREE from 'three';
import { hash1, clamp, smooth } from './util.js';
import { softDot, smokePuff } from './textures.js';

const GLOW = softDot();

export class PointLayer {
  constructor(max, { additive = true, tex = GLOW } = {}) {
    this.max = max;
    const geo = new THREE.BufferGeometry();
    this.pos = new Float32Array(max * 3);
    this.col = new Float32Array(max * 3);
    this.size = new Float32Array(max);
    this.alpha = new Float32Array(max);
    geo.setAttribute('position', new THREE.BufferAttribute(this.pos, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(this.col, 3));
    geo.setAttribute('size', new THREE.BufferAttribute(this.size, 1));
    geo.setAttribute('alpha', new THREE.BufferAttribute(this.alpha, 1));
    geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e5);
    this.mat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending,
      uniforms: { tex: { value: tex }, scale: { value: 1000 } },
      vertexShader: `attribute float size; attribute float alpha; attribute vec3 color;
        varying vec3 vC; varying float vA; uniform float scale;
        void main(){ vC = color; vA = alpha; vec4 mv = modelViewMatrix*vec4(position,1.0);
          gl_PointSize = max(1.0, size*scale/(-mv.z)); gl_Position = projectionMatrix*mv; }`,
      fragmentShader: `uniform sampler2D tex; varying vec3 vC; varying float vA;
        void main(){ vec4 t = texture2D(tex, gl_PointCoord); gl_FragColor = vec4(vC*t.rgb, t.a*vA); }`,
    });
    this.points = new THREE.Points(geo, this.mat);
    this.points.frustumCulled = false;
    this.points.renderOrder = 10;
    this.n = 0;
  }
  begin() { this.n = 0; }
  push(x, y, z, r, g, b, size, a) {
    if (this.n >= this.max || a <= 0.002) return;
    const i = this.n++;
    this.pos[i * 3] = x; this.pos[i * 3 + 1] = y; this.pos[i * 3 + 2] = z;
    this.col[i * 3] = r; this.col[i * 3 + 1] = g; this.col[i * 3 + 2] = b;
    this.size[i] = size; this.alpha[i] = a;
  }
  end() {
    const g = this.points.geometry;
    g.setDrawRange(0, this.n);
    for (const k of ['position', 'color', 'size', 'alpha']) g.attributes[k].needsUpdate = true;
  }
}

// ---- sparks from a moving emitter (fuse tip, rocket nozzle) ----
// emitterAt(time) -> Vector3 ; active window [t0, t1]
export function emitSparks(layer, t, t0, t1, emitterAt, { n = 70, seed = 1, speed = 1.2, life = 0.38, size = 0.05, g = 3.5, up = 0.6, intensity = 1, dirBias = null } = {}) {
  if (t < t0) return;
  for (let i = 0; i < n; i++) {
    const p = life * (0.6 + 0.8 * hash1(i, seed));
    const age = (t - t0 + hash1(i, seed + 1) * p) % p;
    const tb = t - age;
    if (tb < t0 || tb > t1) continue;
    const e = emitterAt(tb);
    const th = hash1(i, seed + 2) * Math.PI * 2;
    const ph = Math.acos(1 - 2 * hash1(i, seed + 3) * (0.5 + 0.5 * up));
    const s = speed * (0.4 + hash1(i, seed + 4));
    let vx = Math.sin(ph) * Math.cos(th) * s, vy = Math.cos(ph) * s, vz = Math.sin(ph) * Math.sin(th) * s;
    if (dirBias) { vx += dirBias.x; vy += dirBias.y; vz += dirBias.z; }
    const x = e.x + vx * age, y = e.y + vy * age - 0.5 * g * age * age, z = e.z + vz * age;
    const k = 1 - age / p;
    const hot = clamp(k * 1.3);
    layer.push(x, Math.max(y, 0.01), z, 1.0, 0.55 + 0.4 * hot, 0.15 + 0.6 * hot * hot, size * (0.5 + k), k * intensity);
  }
  // emitter glow
  if (t <= t1) {
    const e = emitterAt(t);
    const fl = 0.75 + 0.25 * Math.sin(t * 61.0) * Math.sin(t * 23.0);
    layer.push(e.x, e.y, e.z, 1.0, 0.75, 0.35, size * 6 * fl, 0.9 * intensity);
  }
}

// ---- flame (cone with flickering shader) ----
export function buildFlame(color = new THREE.Color(1.0, 0.55, 0.15)) {
  const geo = new THREE.ConeGeometry(1, 1, 24, 6, true);
  geo.translate(0, -0.5, 0); // tip at y=-1, base at 0
  const mat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    uniforms: { time: { value: 0 }, color: { value: color }, power: { value: 1 } },
    vertexShader: `varying vec2 vUv; varying vec3 vN; varying vec3 vV; uniform float time;
      void main(){ vUv = uv; vec3 p = position;
        float w = sin(p.y*9.0 + time*40.0)*0.06 + sin(p.y*17.0 - time*63.0)*0.04;
        p.x += w*(-p.y); p.z += w*0.7*(-p.y);
        vec4 mv = modelViewMatrix*vec4(p,1.0); vV = normalize(-mv.xyz); vN = normalize(normalMatrix*normal);
        gl_Position = projectionMatrix*mv; }`,
    fragmentShader: `varying vec2 vUv; varying vec3 vN; varying vec3 vV; uniform vec3 color; uniform float power; uniform float time;
      void main(){ float along = vUv.y; // 0 tip -> 1 base
        float fres = pow(abs(dot(vN, vV)), 1.2);
        vec3 c = mix(color, vec3(1.0,0.95,0.8), smoothstep(0.55,1.0,along)*fres);
        float a = smoothstep(0.0,0.6,along) * fres * power;
        gl_FragColor = vec4(c*a*1.6, a); }`,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.renderOrder = 11;
  return mesh;
}

// ---- smoke (sprites, normal blending) ----
export class SmokeLayer {
  constructor(scene, max = 120) {
    this.sprites = [];
    const tex = smokePuff(31);
    for (let i = 0; i < max; i++) {
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, color: 0x8a8d96, transparent: true, depthWrite: false, opacity: 0 }));
      s.visible = false;
      s.renderOrder = 9;
      scene.add(s);
      this.sprites.push(s);
    }
    this.n = 0;
  }
  begin() { this.n = 0; }
  push(x, y, z, size, opacity, rot, tint = 0x8a8d96) {
    if (this.n >= this.sprites.length || opacity <= 0.003) return;
    const s = this.sprites[this.n++];
    s.visible = true;
    s.position.set(x, y, z);
    s.scale.setScalar(size);
    s.material.opacity = opacity;
    s.material.rotation = rot;
    s.material.color.setHex(tint);
  }
  end() { for (let i = this.n; i < this.sprites.length; i++) this.sprites[i].visible = false; }
}

// a puff = cluster of sprites born at t0 around origin
export function smokePuffAt(smoke, t, t0, origin, { n = 8, seed = 5, life = 2.2, size = 0.35, grow = 0.9, rise = 0.35, spread = 0.25, opacity = 0.5, drift = [0.1, 0, 0], tint } = {}) {
  for (let i = 0; i < n; i++) {
    const a = t - t0 - hash1(i, seed) * 0.15;
    if (a < 0 || a > life) continue;
    const k = a / life;
    const th = hash1(i, seed + 1) * 6.283;
    const r = spread * (0.3 + hash1(i, seed + 2)) * (1 - Math.exp(-a * 3));
    smoke.push(
      origin.x + Math.cos(th) * r + drift[0] * a,
      origin.y + rise * a * (0.6 + hash1(i, seed + 3)) + drift[1] * a,
      origin.z + Math.sin(th) * r + drift[2] * a,
      size * (0.5 + hash1(i, seed + 4) * 0.6) * (1 + grow * a),
      opacity * smooth(0, 0.08, a) * (1 - k) * (1 - k),
      th + a * 0.4 * (hash1(i, seed + 5) - 0.5),
      tint,
    );
  }
}

// ---- fireworks ----
export function fireworkBurst(layer, t, b) {
  const tau = t - b.t0;
  if (tau < 0 || tau > 2.6) return;
  const k = 1.5, g = b.g ?? 2.4;
  for (let i = 0; i < b.n; i++) {
    const u = hash1(i, b.seed), v = hash1(i, b.seed + 1);
    const th = u * Math.PI * 2, z = 1 - 2 * v, r = Math.sqrt(1 - z * z);
    const s = b.speed * (0.82 + 0.3 * hash1(i, b.seed + 2));
    const dx = r * Math.cos(th), dy = z, dz = r * Math.sin(th);
    const col = b.colors[i % b.colors.length];
    for (let tr = 0; tr < 3; tr++) {
      const tt = tau - tr * 0.05;
      if (tt < 0) continue;
      const d = (s * (1 - Math.exp(-k * tt))) / k;
      const x = b.c.x + dx * d, y = b.c.y + dy * d - 0.5 * g * tt * tt, zz = b.c.z + dz * d;
      let a = (1 - smooth(1.1, 2.2, tt)) * (1 - tr * 0.24);
      if (tt > 0.9) a *= 0.55 + 0.45 * hash1(i * 7 + tr, Math.floor(t * 30) + b.seed); // twinkle
      const white = Math.exp(-tt * 6);
      layer.push(x, y, zz, col.r + white * 0.5, col.g + white * 0.5, col.b + white * 0.5, b.size * (1 - tr * 0.25) * (1 + white), a * (tr === 0 ? 0.95 : tr === 1 ? 0.3 : 0.14));
    }
  }
  // core flash
  const f = Math.exp(-tau * 9);
  layer.push(b.c.x, b.c.y, b.c.z, 1, 0.85, 0.6, b.size * 12 * f, f * 0.7);
}
export function burstEnvelope(t, t0) {
  const tau = t - t0;
  if (tau < 0) return 0;
  return Math.exp(-tau * 3.2) * (tau < 0.04 ? tau / 0.04 : 1);
}

// ---- glass shards ----
export function buildShards(scene, n, seed, origin, size) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0, 0.18, 0.02, 0.05, 0.05, 0.0, 0.2], 3));
  geo.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({ color: 0xcfe6ff, metalness: 0.2, roughness: 0.05, transparent: true, opacity: 0.55, side: THREE.DoubleSide, emissive: 0x223344 });
  const list = [];
  for (let i = 0; i < n; i++) {
    const m = new THREE.Mesh(geo, mat);
    const s = 0.6 + hash1(i, seed) * 1.4;
    m.scale.setScalar(s);
    m.userData = {
      p0: new THREE.Vector3(origin.x + (hash1(i, seed + 1) - 0.5) * size, origin.y, origin.z + (hash1(i, seed + 2) - 0.5) * size),
      v: new THREE.Vector3((hash1(i, seed + 3) - 0.5) * 5, hash1(i, seed + 4) < 0.3 ? -1 - hash1(i, seed + 5) * 3 : 3 + hash1(i, seed + 5) * 9, (hash1(i, seed + 6) - 0.5) * 5),
      spin: new THREE.Vector3(hash1(i, seed + 7) * 12, hash1(i, seed + 8) * 12, hash1(i, seed + 9) * 12),
    };
    m.visible = false;
    scene.add(m);
    list.push(m);
  }
  return list;
}
export function updateShards(list, t, t0, roofY, benchY, ceilY) {
  const g = 12;
  for (const m of list) {
    const tau = t - t0;
    if (tau < 0) { m.visible = false; continue; }
    const { p0, v, spin } = m.userData;
    const floorY = v.y > 0 ? roofY : benchY;
    // solve landing time: p0.y + v.y τ - g/2 τ² = floorY
    const A = -0.5 * g, B = v.y, C = p0.y - floorY;
    const tl = (-B - Math.sqrt(B * B - 4 * A * C)) / (2 * A);
    const tt = Math.min(tau, tl);
    const x = p0.x + v.x * tt, z = p0.z + v.z * tt;
    const y = p0.y + v.y * tt - 0.5 * g * tt * tt;
    // shards going up land on the roof only if outside the opening; keep it simple: they land where they are
    m.position.set(x, y, z);
    if (tau < tl) m.rotation.set(spin.x * tt, spin.y * tt, spin.z * tt);
    else m.rotation.set(-Math.PI / 2 + 0.05, spin.y * tl, 0);
    m.visible = true;
  }
}
