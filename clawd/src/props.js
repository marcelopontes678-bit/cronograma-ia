// Scrap rocket, big booster, fuses, duct tape bands and hand props.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { canLabel, brushedMetal, softDot } from './textures.js';
import { wrenchGeo } from './set.js';

export const R0 = new THREE.Vector3(0.9, 0, 0.0);      // rocket base centre
export const ROCKET_R = 0.22;
export const BOOST_R = 0.28;
export const B0 = new THREE.Vector3(2.35, 0, -0.62);   // booster start
export const B1 = new THREE.Vector3(1.4, 0, -0.06);    // booster taped position

function m(geo, mat) {
  const x = new THREE.Mesh(geo, mat);
  x.castShadow = x.receiveShadow = true;
  return x;
}

export function buildRocket() {
  const g = new THREE.Group(); // pivot at base centre
  const can = new THREE.MeshStandardMaterial({ map: canLabel(9), metalness: 0.55, roughness: 0.45 });
  const tin = new THREE.MeshStandardMaterial({ map: brushedMetal(8, [170, 168, 160]), metalness: 0.85, roughness: 0.35 });
  const red = new THREE.MeshStandardMaterial({ color: 0xb8402c, metalness: 0.3, roughness: 0.5 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x2a2a2e, metalness: 0.6, roughness: 0.5 });
  const body = m(new THREE.CylinderGeometry(ROCKET_R, ROCKET_R, 0.86, 28), can);
  body.position.y = 0.16 + 0.43;
  // rims
  for (const y of [0.16, 1.02]) {
    const rim = m(new THREE.TorusGeometry(ROCKET_R, 0.018, 6, 28), tin);
    rim.rotation.x = Math.PI / 2;
    rim.position.y = y;
    g.add(rim);
  }
  const nose = m(new THREE.ConeGeometry(ROCKET_R * 1.02, 0.42, 28), red);
  nose.position.y = 1.02 + 0.21;
  const tip = m(new THREE.SphereGeometry(0.03, 10, 8), tin);
  tip.position.y = 1.45;
  const nozzle = m(new THREE.CylinderGeometry(ROCKET_R * 0.7, ROCKET_R * 0.9, 0.16, 20, 1, true), dark);
  nozzle.material = dark.clone();
  nozzle.material.side = THREE.DoubleSide;
  nozzle.position.y = 0.08 + 0.0;
  g.add(body, nose, tip, nozzle);
  // fins (bent tin) – none pointing +x so it can lie on its side
  const finShape = new THREE.Shape();
  finShape.moveTo(0, 0); finShape.lineTo(0.2, -0.12); finShape.lineTo(0.2, 0.05); finShape.lineTo(0, 0.38); finShape.closePath();
  const finGeo = new THREE.ExtrudeGeometry(finShape, { depth: 0.025, bevelEnabled: false });
  finGeo.translate(0, 0, -0.0125);
  for (const a of [Math.PI / 3, Math.PI, Math.PI * 5 / 3]) {
    const f = m(finGeo, tin);
    f.position.set(Math.cos(a) * ROCKET_R, 0.14, -Math.sin(a) * ROCKET_R);
    f.rotation.y = a;
    g.add(f);
  }
  // rivets & a dented patch
  for (let i = 0; i < 10; i++) {
    const r = m(new THREE.SphereGeometry(0.018, 6, 4), tin);
    const a = i * 0.63;
    r.position.set(Math.cos(a) * ROCKET_R, 0.3 + (i % 3) * 0.3, Math.sin(a) * ROCKET_R);
    g.add(r);
  }
  const patch = m(new THREE.BoxGeometry(0.16, 0.18, 0.02), tin);
  patch.position.set(0.0, 0.75, ROCKET_R + 0.004);
  patch.rotation.z = 0.2;
  g.add(patch);
  // small loose fin being hammered in shot 1 is the front fin at a=PI*11/6 (faces camera-ish)
  g.userData.nozzleY = 0.0;
  return g;
}

export function buildBooster() {
  const g = new THREE.Group();
  const red = new THREE.MeshStandardMaterial({ color: 0xc0281c, metalness: 0.35, roughness: 0.38 });
  const tin = new THREE.MeshStandardMaterial({ map: brushedMetal(12, [160, 160, 165]), metalness: 0.85, roughness: 0.35 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x222226, metalness: 0.6, roughness: 0.5, side: THREE.DoubleSide });
  const body = m(new THREE.CylinderGeometry(BOOST_R, BOOST_R, 1.0, 30), red);
  body.position.y = 0.2 + 0.5;
  const top = m(new THREE.SphereGeometry(BOOST_R, 30, 12, 0, Math.PI * 2, 0, Math.PI / 2), red);
  top.position.y = 1.2;
  const valve = m(new THREE.CylinderGeometry(0.06, 0.07, 0.14, 12), tin);
  valve.position.y = 1.5;
  const band = m(new THREE.CylinderGeometry(BOOST_R + 0.01, BOOST_R + 0.01, 0.12, 30), tin);
  band.position.y = 0.95;
  const nozzle = m(new THREE.CylinderGeometry(BOOST_R * 0.55, BOOST_R * 0.95, 0.22, 24, 1, true), dark);
  nozzle.position.y = 0.11;
  // warning stripes
  const stripe = m(new THREE.CylinderGeometry(BOOST_R + 0.005, BOOST_R + 0.005, 0.05, 30), new THREE.MeshStandardMaterial({ color: 0xe8c13a, roughness: 0.5 }));
  stripe.position.y = 0.42;
  g.add(body, top, valve, band, nozzle, stripe);
  return g;
}

// Fuse: a curve built from short segments so it can burn down deterministically.
export function buildFuse(points, color = 0x6b5a3a) {
  const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)));
  const N = 48;
  const segs = [];
  const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.95 });
  const g = new THREE.Group();
  const geo = new THREE.CylinderGeometry(0.018, 0.018, 1, 6);
  for (let i = 0; i < N; i++) {
    const a = curve.getPoint(i / N), b = curve.getPoint((i + 1) / N);
    const s = new THREE.Mesh(geo, mat);
    s.position.copy(a).lerp(b, 0.5);
    s.scale.y = a.distanceTo(b) * 1.15;
    s.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
    s.castShadow = true;
    g.add(s);
    segs.push(s);
  }
  return { group: g, curve, segs, N };
}
// burnt: 0..1 fraction burned from the free end (u=1) toward the rocket (u=0)
export function setFuseBurn(f, burnt) {
  f.segs.forEach((s, i) => {
    const u = (i + 0.5) / f.N;
    s.visible = u < 1 - burnt;
  });
}

// Duct tape band around rocket+booster (stadium path), revealed progressively.
export function buildTapeBand(y, height = 0.1) {
  const rc = ROCKET_R + 0.012, rb = BOOST_R + 0.012;
  const cR = new THREE.Vector2(R0.x, R0.z), cB = new THREE.Vector2(B1.x, B1.z);
  // build outline points of convex hull of two circles (sampled), CCW starting at front
  const pts = [];
  const dir = cB.clone().sub(cR).normalize();
  const nrm = new THREE.Vector2(-dir.y, dir.x);
  const base = Math.atan2(nrm.y, nrm.x);
  const S = 40;
  // rocket half (around back side)
  for (let i = 0; i <= S; i++) {
    const a = base + (i / S) * Math.PI;
    pts.push(new THREE.Vector2(cR.x + Math.cos(a) * rc, cR.y + Math.sin(a) * rc));
  }
  for (let i = 0; i <= S; i++) {
    const a = base + Math.PI + (i / S) * Math.PI;
    pts.push(new THREE.Vector2(cB.x + Math.cos(a) * rb, cB.y + Math.sin(a) * rb));
  }
  pts.push(pts[0].clone());
  const n = pts.length;
  const pos = new Float32Array(n * 2 * 3), uv = new Float32Array(n * 2 * 2), idx = [];
  for (let i = 0; i < n; i++) {
    const p = pts[i];
    pos.set([p.x, y - height / 2, p.y, p.x, y + height / 2, p.y], i * 6);
    uv.set([i / (n - 1), 0, i / (n - 1), 1], i * 4);
    if (i < n - 1) {
      const a = i * 2;
      idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({ color: 0xa9adb3, metalness: 0.35, roughness: 0.55, side: THREE.DoubleSide });
  const band = new THREE.Mesh(geo, mat);
  band.castShadow = true;
  band.userData.total = idx.length;
  band.userData.pts = pts;
  band.userData.y = y;
  return band;
}
export function setTapeProgress(band, u) {
  const tris = Math.floor((band.userData.total / 6) * u) * 6;
  band.geometry.setDrawRange(0, tris);
  band.visible = tris > 0;
  const pts = band.userData.pts;
  const i = Math.min(pts.length - 1, Math.floor((pts.length - 1) * u));
  return new THREE.Vector3(pts[i].x, band.userData.y, pts[i].y);
}

export function buildMatch() {
  const g = new THREE.Group();
  const stick = m(new THREE.BoxGeometry(0.5, 0.035, 0.035), new THREE.MeshStandardMaterial({ color: 0xd8b98a, roughness: 0.8 }));
  stick.position.x = 0.25;
  const head = m(new THREE.SphereGeometry(0.035, 10, 8), new THREE.MeshStandardMaterial({ color: 0x8c1e16, roughness: 0.7 }));
  head.position.x = 0.5;
  head.scale.set(1.3, 1, 1);
  const flame = new THREE.Sprite(new THREE.SpriteMaterial({ map: softDot('rgba(255,240,200,1)', 'rgba(255,140,40,0.5)'), color: 0xffb060, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  flame.position.set(0.53, 0.07, 0);
  flame.scale.set(0.16, 0.28, 1);
  const light = new THREE.PointLight(0xff9a40, 0, 3, 2);
  light.position.set(0.53, 0.08, 0);
  g.add(stick, head, flame, light);
  g.userData = { flame, light, head };
  return g;
}

export function buildHandWrench(metal) {
  const w = m(wrenchGeo(0.9, 0.09, 0.035), metal);
  // grip at the handle end
  w.position.x = 0.38;
  const g = new THREE.Group();
  g.add(w);
  return g;
}

export function buildTapeRoll() {
  const g = new THREE.Group();
  const shape = new THREE.Shape();
  shape.absarc(0, 0, 0.2, 0, Math.PI * 2, false);
  const hole = new THREE.Path();
  hole.absarc(0, 0, 0.12, 0, Math.PI * 2, true);
  shape.holes.push(hole);
  const roll = m(new THREE.ExtrudeGeometry(shape, { depth: 0.14, bevelEnabled: true, bevelSize: 0.01, bevelThickness: 0.01, bevelSegments: 1, curveSegments: 28 }),
    new THREE.MeshStandardMaterial({ color: 0xa9adb3, metalness: 0.35, roughness: 0.5 }));
  roll.geometry.translate(0, 0, -0.07);
  const core = m(new THREE.CylinderGeometry(0.12, 0.12, 0.145, 24, 1, true), new THREE.MeshStandardMaterial({ color: 0x8b6b45, roughness: 0.9, side: THREE.DoubleSide }));
  core.rotation.x = Math.PI / 2;
  g.add(roll, core);
  return g;
}

// thin strip between two world points (tape from roll to band)
export function buildStrip() {
  const geo = new THREE.PlaneGeometry(1, 0.08);
  geo.translate(0.5, 0, 0);
  const s = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0xb8bcc2, metalness: 0.3, roughness: 0.5, side: THREE.DoubleSide }));
  return s;
}
export function setStrip(s, a, b) {
  const d = b.clone().sub(a);
  const len = d.length();
  s.position.copy(a);
  s.scale.set(Math.max(0.001, len), 1, 1);
  s.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), d.normalize());
}

export { RoundedBoxGeometry };
