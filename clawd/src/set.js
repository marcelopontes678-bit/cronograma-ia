// The workshop set (interior), the roof + night sky (exterior) and the base lights.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mulberry32 } from './util.js';
import { woodPlanks, pegboard, brushedMetal, roofShingles, softDot } from './textures.js';

export const CEIL_Y = 14;
export const SKY = { x: 0.9, z: 0.0, size: 3.4 }; // skylight centred above the rocket
export const MOON_DIR = new THREE.Vector3(-0.06, 1, -0.1).normalize();

function mesh(geo, mat, { cast = true, receive = true } = {}) {
  const m = new THREE.Mesh(geo, mat);
  m.castShadow = cast;
  m.receiveShadow = receive;
  return m;
}

function hexNutGeo(r, h, hole) {
  const s = new THREE.Shape();
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2;
    i ? s.lineTo(Math.cos(a) * r, Math.sin(a) * r) : s.moveTo(Math.cos(a) * r, Math.sin(a) * r);
  }
  s.closePath();
  const p = new THREE.Path();
  p.absarc(0, 0, hole, 0, Math.PI * 2, true);
  s.holes.push(p);
  const g = new THREE.ExtrudeGeometry(s, { depth: h, bevelEnabled: true, bevelSize: 0.01, bevelThickness: 0.01, bevelSegments: 1, curveSegments: 12 });
  g.rotateX(-Math.PI / 2);
  return g;
}

function gearGeo(r, teeth, h, hole) {
  const s = new THREE.Shape();
  const n = teeth * 4;
  for (let i = 0; i <= n; i++) {
    const a = (i / n) * Math.PI * 2;
    const rr = i % 4 < 2 ? r : r * 0.82;
    i ? s.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : s.moveTo(Math.cos(a) * rr, Math.sin(a) * rr);
  }
  const p = new THREE.Path();
  p.absarc(0, 0, hole, 0, Math.PI * 2, true);
  s.holes.push(p);
  const g = new THREE.ExtrudeGeometry(s, { depth: h, bevelEnabled: false, curveSegments: 16 });
  g.rotateX(-Math.PI / 2);
  return g;
}

export function wrenchGeo(len, w, t) {
  const s = new THREE.Shape();
  const jaw = w * 1.6;
  s.moveTo(-len / 2, -w / 2);
  s.lineTo(len / 2 - jaw * 0.6, -w / 2);
  s.absarc(len / 2, 0, jaw / 2 + 0.001, -2.4, 2.4, false);
  s.lineTo(len / 2 - jaw * 0.6, w / 2);
  s.lineTo(-len / 2, w / 2);
  s.absarc(-len / 2, 0, w / 2 + 0.001, Math.PI / 2, -Math.PI / 2, false);
  const mouth = new THREE.Path();
  mouth.moveTo(len / 2 + jaw / 2 + 0.02, -jaw * 0.18);
  mouth.lineTo(len / 2 - jaw * 0.05, -jaw * 0.18);
  mouth.lineTo(len / 2 - jaw * 0.05, jaw * 0.18);
  mouth.lineTo(len / 2 + jaw / 2 + 0.02, jaw * 0.18);
  const g = new THREE.ExtrudeGeometry(s, { depth: t, bevelEnabled: true, bevelSize: t * 0.25, bevelThickness: t * 0.25, bevelSegments: 2, curveSegments: 16 });
  g.translate(0, 0, -t / 2);
  return g;
}

export function buildSet(scene) {
  const rnd = mulberry32(1234);
  const set = { interior: new THREE.Group(), exterior: new THREE.Group() };
  scene.add(set.interior, set.exterior);
  const I = set.interior, E = set.exterior;

  const metal = new THREE.MeshStandardMaterial({ map: brushedMetal(5), metalness: 0.85, roughness: 0.38 });
  const darkMetal = new THREE.MeshStandardMaterial({ map: brushedMetal(6, [70, 70, 76]), metalness: 0.8, roughness: 0.5 });
  const rust = new THREE.MeshStandardMaterial({ color: 0x7a4a2c, metalness: 0.4, roughness: 0.8 });
  const brass = new THREE.MeshStandardMaterial({ color: 0xb08a3e, metalness: 0.9, roughness: 0.35 });
  const redPaint = new THREE.MeshStandardMaterial({ color: 0x9e2b22, metalness: 0.2, roughness: 0.5 });
  const wood = new THREE.MeshStandardMaterial({ map: woodPlanks(3), roughness: 0.78 });
  const darkWood = new THREE.MeshStandardMaterial({ color: 0x3a2618, roughness: 0.9 });
  const rubber = new THREE.MeshStandardMaterial({ color: 0x1d1d22, roughness: 0.75 });
  const yellow = new THREE.MeshStandardMaterial({ color: 0xc89a2a, roughness: 0.55 });
  const wall = new THREE.MeshStandardMaterial({ color: 0x40372f, roughness: 0.95 });
  set.mats = { metal, darkMetal, rust, brass, redPaint, wood, rubber, yellow };

  // ---------- Workbench ----------
  const bench = mesh(new THREE.BoxGeometry(18, 0.6, 5.2), wood);
  bench.position.set(0, -0.3, -0.2);
  I.add(bench);
  // floor far below + bench legs (only seen in the wide shot)
  const floor = mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ color: 0x1e1a17, roughness: 1 }), { cast: false });
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -9;
  I.add(floor);
  for (const x of [-8, 8]) for (const z of [-2.4, 2.0]) {
    const leg = mesh(new THREE.BoxGeometry(0.6, 9, 0.6), darkWood);
    leg.position.set(x, -4.8, z);
    I.add(leg);
  }

  // ---------- Walls & ceiling ----------
  const back = mesh(new THREE.PlaneGeometry(30, 24), new THREE.MeshStandardMaterial({ map: pegboard(11), roughness: 0.9 }), { cast: false });
  back.position.set(0, 3, -2.8);
  back.material.map.repeat.set(6, 4.8);
  I.add(back);
  for (const s of [-1, 1]) {
    const side = mesh(new THREE.PlaneGeometry(14, 30), wall, { cast: false });
    side.position.set(s * 10, 2, 4);
    side.rotation.y = -s * Math.PI / 2;
    I.add(side);
  }
  const front = mesh(new THREE.PlaneGeometry(30, 30), wall, { cast: false });
  front.position.set(0, 2, 16);
  front.rotation.y = Math.PI;
  I.add(front);

  // ceiling with skylight hole (4 slabs around the opening)
  const ceilMat = new THREE.MeshStandardMaterial({ color: 0x2c2620, roughness: 1 });
  const hs = SKY.size / 2, T = 0.35;
  const ceilParts = [
    [SKY.x, SKY.z - hs - 10, 40, 20],   // back slab
    [SKY.x, SKY.z + hs + 10, 40, 20],   // front slab
    [SKY.x - hs - 10, SKY.z, 20, SKY.size],
    [SKY.x + hs + 10, SKY.z, 20, SKY.size],
  ];
  for (const [x, z, w, d] of ceilParts) {
    const slab = mesh(new THREE.BoxGeometry(w, T, d), ceilMat);
    slab.position.set(x, CEIL_Y + T / 2, z);
    I.add(slab);
  }
  // rafters
  for (let i = -3; i <= 3; i++) {
    const r = mesh(new THREE.BoxGeometry(0.4, 0.6, 30), darkWood);
    r.position.set(SKY.x + i * 2.6 + (i === 0 ? 2 : 0), CEIL_Y - 0.3, 4);
    if (Math.abs(r.position.x - SKY.x) > hs + 0.3) I.add(r);
  }
  // skylight frame + mullions + glass
  const frameMat = new THREE.MeshStandardMaterial({ color: 0x2a2d33, metalness: 0.6, roughness: 0.5 });
  const skyFrame = new THREE.Group();
  for (const s of [-1, 1]) {
    const a = mesh(new THREE.BoxGeometry(SKY.size + 0.3, 0.5, 0.15), frameMat);
    a.position.set(0, 0, s * hs);
    const b = mesh(new THREE.BoxGeometry(0.15, 0.5, SKY.size + 0.3), frameMat);
    b.position.set(s * hs, 0, 0);
    skyFrame.add(a, b);
  }
  const mull = mesh(new THREE.BoxGeometry(0.08, 0.12, SKY.size), frameMat);
  const mull2 = mesh(new THREE.BoxGeometry(SKY.size, 0.12, 0.08), frameMat);
  skyFrame.add(mull, mull2);
  skyFrame.position.set(SKY.x, CEIL_Y + 0.2, SKY.z);
  scene.add(skyFrame);
  set.mullions = [mull, mull2];
  const glassMat = new THREE.MeshStandardMaterial({
    color: 0x9fc4dd, transparent: true, opacity: 0.18, roughness: 0.05, metalness: 0.1, side: THREE.DoubleSide, depthWrite: false,
  });
  set.glassMat = glassMat;
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(SKY.size, SKY.size), glassMat);
  glass.rotation.x = -Math.PI / 2;
  glass.position.set(SKY.x, CEIL_Y + 0.25, SKY.z);
  scene.add(glass);
  set.glass = glass;

  // ---------- Desk lamp (left) ----------
  const lamp = new THREE.Group();
  const lampMat = new THREE.MeshStandardMaterial({ color: 0x2f4a3a, metalness: 0.5, roughness: 0.45 });
  const base = mesh(new THREE.CylinderGeometry(0.9, 1.0, 0.18, 40), lampMat);
  base.position.y = 0.09;
  lamp.add(base);
  const p0 = new THREE.Vector3(0, 0.18, 0), p1 = new THREE.Vector3(0.5, 3.6, 0.2), p2 = new THREE.Vector3(1.9, 4.4, 0.55);
  for (const [a, b] of [[p0, p1], [p1, p2]]) {
    const len = a.distanceTo(b);
    for (const off of [-0.09, 0.09]) {
      const rod = mesh(new THREE.CylinderGeometry(0.04, 0.04, len, 10), metal);
      rod.position.copy(a).lerp(b, 0.5);
      rod.position.z += off;
      rod.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
      lamp.add(rod);
    }
    const joint = mesh(new THREE.CylinderGeometry(0.11, 0.11, 0.3, 16), lampMat);
    joint.rotation.x = Math.PI / 2;
    joint.position.copy(b);
    lamp.add(joint);
  }
  // spring
  const springPts = [];
  for (let i = 0; i <= 120; i++) {
    const u = i / 120, a = u * Math.PI * 2 * 14;
    springPts.push(new THREE.Vector3(0.25 + Math.cos(a) * 0.05, 0.8 + u * 2.0, 0.1 + Math.sin(a) * 0.05));
  }
  lamp.add(mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(springPts), 240, 0.012, 5), metal));
  const shade = new THREE.Group();
  const shadeOuter = mesh(new THREE.ConeGeometry(0.85, 1.1, 36, 1, true), lampMat);
  shadeOuter.material = lampMat.clone();
  shadeOuter.material.side = THREE.DoubleSide;
  shade.add(shadeOuter);
  const cap = mesh(new THREE.SphereGeometry(0.32, 20, 12), lampMat);
  cap.position.y = 0.5;
  shade.add(cap);
  const bulbMat = new THREE.MeshStandardMaterial({ color: 0xffe2b0, emissive: 0xffb860, emissiveIntensity: 2.6 });
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.28, 20, 12), bulbMat);
  bulb.position.y = -0.25;
  shade.add(bulb);
  shade.position.copy(p2);
  lamp.add(shade);
  set.lamp = lamp;
  lamp.position.set(-3.5, 0, 1.3);
  lamp.rotation.y = 0.9;
  I.add(lamp);
  // orient shade toward the work area
  const lampTarget = new THREE.Vector3(0.3, 0, 0.5);
  lamp.updateMatrixWorld(true);
  const shadeWorld = p2.clone().applyMatrix4(lamp.matrixWorld);
  const dirToTarget = lampTarget.clone().sub(shadeWorld).normalize();
  const localDir = dirToTarget.clone().applyQuaternion(lamp.quaternion.clone().invert());
  shade.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), localDir);
  set.lampPos = shadeWorld.clone().add(dirToTarget.clone().multiplyScalar(0.2));
  set.lampTarget = lampTarget;
  set.bulbMat = bulbMat;

  // ---------- Hanging tools on pegboard ----------
  const hangWrench = mesh(wrenchGeo(3.2, 0.32, 0.08), metal);
  hangWrench.rotation.z = 1.3;
  hangWrench.position.set(-1.6, 3.8, -2.7);
  I.add(hangWrench);
  // hammer
  const hammer = new THREE.Group();
  const hHandle = mesh(new THREE.CylinderGeometry(0.12, 0.14, 3.2, 12), new THREE.MeshStandardMaterial({ color: 0x8a5a32, roughness: 0.7 }));
  const hHead = mesh(new THREE.BoxGeometry(1.3, 0.38, 0.38), darkMetal);
  hHead.position.y = 1.6;
  hammer.add(hHandle, hHead);
  hammer.position.set(1.6, 4.0, -2.55);
  hammer.rotation.z = -0.15;
  I.add(hammer);
  // saw
  const saw = new THREE.Group();
  const blade = new THREE.Shape();
  blade.moveTo(0, 0); blade.lineTo(3.4, 0.25); blade.lineTo(3.4, 0.75); blade.lineTo(0, 1.2); blade.closePath();
  const sawBlade = mesh(new THREE.ExtrudeGeometry(blade, { depth: 0.02, bevelEnabled: false }), metal);
  const sawHandle = mesh(new RoundedBoxGeometry(0.9, 1.3, 0.18, 2, 0.15), new THREE.MeshStandardMaterial({ color: 0x6b3a22, roughness: 0.7 }));
  sawHandle.position.set(-0.35, 0.6, 0);
  saw.add(sawBlade, sawHandle);
  saw.position.set(4.2, 3.0, -2.7);
  saw.rotation.z = -0.4;
  I.add(saw);
  // pliers
  const pliers = new THREE.Group();
  for (const s of [-1, 1]) {
    const h = mesh(new THREE.BoxGeometry(0.16, 1.8, 0.1), redPaint);
    h.position.set(s * 0.18, -0.6, 0);
    h.rotation.z = s * 0.12;
    const j = mesh(new THREE.BoxGeometry(0.12, 0.8, 0.1), darkMetal);
    j.position.set(s * 0.04, 0.6, 0);
    pliers.add(h, j);
  }
  pliers.position.set(-4.4, 4.6, -2.7);
  I.add(pliers);
  // coil of wire on a peg
  const coil = mesh(new THREE.TorusGeometry(0.7, 0.12, 10, 40), new THREE.MeshStandardMaterial({ color: 0xa8552c, metalness: 0.7, roughness: 0.35 }));
  coil.position.set(-0.1, 6.0, -2.65);
  I.add(coil);
  // shelf with jars/cans
  const shelf = mesh(new THREE.BoxGeometry(8, 0.15, 1.0), darkWood);
  shelf.position.set(1.5, 7.2, -2.3);
  I.add(shelf);
  for (let i = 0; i < 7; i++) {
    const r = 0.25 + rnd() * 0.25, h = 0.6 + rnd() * 0.8;
    const can = mesh(new THREE.CylinderGeometry(r, r, h, 24), i % 3 === 0 ? rust : i % 3 === 1 ? metal : yellow);
    can.position.set(-2 + i * 1.1, 7.27 + h / 2, -2.25);
    I.add(can);
  }

  // ---------- Bench clutter ----------
  // big screwdriver
  const sd = new THREE.Group();
  const sdHandle = mesh(new THREE.CylinderGeometry(0.28, 0.24, 1.6, 8), new THREE.MeshStandardMaterial({ color: 0xc23b2b, roughness: 0.4 }));
  const sdShaft = mesh(new THREE.CylinderGeometry(0.06, 0.06, 2.2, 10), metal);
  sdShaft.position.y = 1.9;
  sd.add(sdHandle, sdShaft);
  sd.rotation.set(0, 0, Math.PI / 2);
  sd.rotation.y = 0.5;
  sd.position.set(-2.4, 0.28, 1.4);
  I.add(sd);
  // big wrench on bench (behind work area)
  const bw = mesh(wrenchGeo(3.0, 0.3, 0.1), metal);
  bw.rotation.set(-Math.PI / 2, 0, 0.25);
  bw.position.set(-1.0, 0.07, -1.7);
  I.add(bw);
  // vise (right)
  const vise = new THREE.Group();
  const vb = mesh(new THREE.BoxGeometry(1.6, 0.9, 1.2), new THREE.MeshStandardMaterial({ color: 0x2f5d7c, metalness: 0.4, roughness: 0.5 }));
  vb.position.y = 0.45;
  const vj = mesh(new THREE.BoxGeometry(1.8, 0.7, 0.3), darkMetal);
  vj.position.set(0, 1.1, 0.35);
  const vj2 = vj.clone();
  vj2.position.z = -0.35;
  const vs = mesh(new THREE.CylinderGeometry(0.08, 0.08, 2.4, 10), metal);
  vs.rotation.x = Math.PI / 2;
  vs.position.set(0, 0.8, 1.1);
  vise.add(vb, vj, vj2, vs);
  vise.position.set(5.6, 0, -1.2);
  vise.rotation.y = -0.4;
  I.add(vise);
  // paint can + brushes (right back)
  const paint = mesh(new THREE.CylinderGeometry(0.75, 0.75, 1.4, 30), metal);
  paint.position.set(3.8, 0.7, -2.0);
  I.add(paint);
  const paintLid = mesh(new THREE.CylinderGeometry(0.77, 0.77, 0.08, 30), redPaint);
  paintLid.position.set(3.8, 1.42, -2.0);
  I.add(paintLid);
  // pencil + ruler (front)
  const pencil = mesh(new THREE.CylinderGeometry(0.07, 0.07, 2.2, 6), yellow);
  pencil.rotation.set(0, 0.3, Math.PI / 2);
  pencil.position.set(2.8, 0.07, 1.6);
  I.add(pencil);
  const ruler = mesh(new THREE.BoxGeometry(4.5, 0.03, 0.45), new THREE.MeshStandardMaterial({ color: 0xcfc29a, roughness: 0.6 }));
  ruler.position.set(-4.2, 0.015, 0.4);
  ruler.rotation.y = 0.2;
  I.add(ruler);
  // spool of thread
  const spool = new THREE.Group();
  const spoolCore = mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.6, 20), new THREE.MeshStandardMaterial({ color: 0x3f7a6a, roughness: 0.8 }));
  const spoolTop = mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.08, 20), darkWood);
  spoolTop.position.y = 0.34;
  const spoolBot = spoolTop.clone();
  spoolBot.position.y = -0.34;
  spool.add(spoolCore, spoolTop, spoolBot);
  spool.position.set(-2.6, 0.38, -0.6);
  I.add(spool);

  // scattered nuts, washers, gears, bolts, avoiding the action zone
  const nutGeo = hexNutGeo(0.14, 0.09, 0.06);
  const gearG1 = gearGeo(0.38, 12, 0.08, 0.1);
  const gearG2 = gearGeo(0.25, 9, 0.07, 0.07);
  const washerGeo = new THREE.TorusGeometry(0.1, 0.035, 6, 18);
  washerGeo.rotateX(Math.PI / 2);
  const boltGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.5, 8);
  const inAction = (x, z) => x > -1.6 && x < 3.5 && z > -1.5 && z < 1.6;
  let placed = 0;
  while (placed < 42) {
    const x = -6 + rnd() * 12.5, z = -2.3 + rnd() * 4.1;
    if (inAction(x, z)) continue;
    const kind = rnd();
    let m;
    if (kind < 0.35) { m = mesh(nutGeo, rnd() < 0.5 ? metal : brass); m.position.set(x, 0.01, z); }
    else if (kind < 0.55) { m = mesh(washerGeo, metal); m.position.set(x, 0.035, z); }
    else if (kind < 0.7) { m = mesh(rnd() < 0.5 ? gearG1 : gearG2, rnd() < 0.5 ? brass : darkMetal); m.position.set(x, 0.0, z); }
    else { m = mesh(boltGeo, darkMetal); m.rotation.z = Math.PI / 2; m.position.set(x, 0.05, z); }
    m.rotation.y = rnd() * Math.PI * 2;
    I.add(m);
    placed++;
  }
  // a few close pieces just at the edge of the action zone (foreground texture)
  for (const [x, z, g, mtl] of [[-1.3, 1.5, nutGeo, brass], [2.9, 1.25, gearG2, brass], [3.2, -1.3, nutGeo, metal], [-1.4, -1.2, gearG1, darkMetal], [0.4, 1.7, washerGeo, metal]]) {
    const m = mesh(g, mtl);
    m.position.set(x, g === washerGeo ? 0.035 : 0.01, z);
    m.rotation.y = x * 3.1;
    I.add(m);
  }
  // wires
  const wireMat = new THREE.MeshStandardMaterial({ color: 0x2b2b2b, roughness: 0.6 });
  for (let w = 0; w < 2; w++) {
    const pts = [];
    for (let i = 0; i < 7; i++) pts.push(new THREE.Vector3(-6 + w * 9 + i * 0.6, 0.04, 1.0 + Math.sin(i * 1.3 + w) * 0.5 - w * 2.6));
    I.add(mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 60, 0.04, 6), w ? new THREE.MeshStandardMaterial({ color: 0x8b2e22, roughness: 0.6 }) : wireMat));
  }

  // ---------- Exterior: roof, chimney, neighbours ----------
  const roofMat = new THREE.MeshStandardMaterial({ map: roofShingles(21), roughness: 0.9 });
  const roofParts = [
    [SKY.x, SKY.z - hs - 15, 60, 30],
    [SKY.x, SKY.z + hs + 15, 60, 30],
    [SKY.x - hs - 15, SKY.z, 30, SKY.size],
    [SKY.x + hs + 15, SKY.z, 30, SKY.size],
  ];
  for (const [x, z, w, d] of roofParts) {
    const r = mesh(new THREE.BoxGeometry(w, 0.3, d), roofMat);
    r.position.set(x, CEIL_Y + 0.5, z);
    E.add(r);
  }
  // skylight curb outside
  for (const s of [-1, 1]) {
    const a = mesh(new THREE.BoxGeometry(SKY.size + 0.8, 0.6, 0.4), frameMat);
    a.position.set(SKY.x, CEIL_Y + 0.9, SKY.z + s * (hs + 0.2));
    const b = mesh(new THREE.BoxGeometry(0.4, 0.6, SKY.size + 0.8), frameMat);
    b.position.set(SKY.x + s * (hs + 0.2), CEIL_Y + 0.9, SKY.z);
    E.add(a, b);
  }
  const brick = new THREE.MeshStandardMaterial({ color: 0x5a3328, roughness: 0.95 });
  const chimney = mesh(new THREE.BoxGeometry(2, 5, 2), brick);
  chimney.position.set(-7, CEIL_Y + 3, -6);
  E.add(chimney);
  const neighbourMat = new THREE.MeshStandardMaterial({ color: 0x101320, roughness: 1 });
  const winMat = new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0xffb860, emissiveIntensity: 1.6 });
  for (let i = 0; i < 9; i++) {
    const w = 8 + rnd() * 10, h = 10 + rnd() * 18;
    const b = mesh(new THREE.BoxGeometry(w, h, 8), neighbourMat, { cast: false });
    const ang = -2.4 + i * 0.32;
    b.position.set(Math.cos(ang) * 70, CEIL_Y - 6 + h / 2, Math.sin(ang) * 70);
    b.lookAt(0, b.position.y, 0);
    E.add(b);
    for (let k = 0; k < 3; k++) {
      if (rnd() < 0.45) continue;
      const wm = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 1.6), winMat);
      wm.position.set(-w / 3 + k * (w / 3), h / 2 - 3 - rnd() * 6, 4.05);
      b.add(wm);
    }
  }

  // ---------- Sky dome, stars, moon ----------
  const skyMat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    uniforms: { flash: { value: new THREE.Color(0, 0, 0) } },
    vertexShader: `varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0);} `,
    fragmentShader: `varying vec3 vP; uniform vec3 flash;
      void main(){ float h = clamp(vP.y,0.0,1.0);
        vec3 horizon = vec3(0.10,0.13,0.26); vec3 zen = vec3(0.012,0.018,0.05);
        vec3 c = mix(horizon, zen, pow(h,0.55)) + flash*(0.35+0.65*h);
        gl_FragColor = vec4(c,1.0);}`,
  });
  const sky = new THREE.Mesh(new THREE.SphereGeometry(200, 32, 16), skyMat);
  scene.add(sky);
  set.skyMat = skyMat;
  // stars
  const starPos = [], starCol = [];
  for (let i = 0; i < 1400; i++) {
    const u = rnd(), v = rnd();
    const th = u * Math.PI * 2, y = 0.05 + v * 0.95;
    const r = Math.sqrt(1 - y * y);
    starPos.push(Math.cos(th) * r * 190, y * 190, Math.sin(th) * r * 190);
    const b = 0.35 + rnd() * 0.65;
    starCol.push(b, b, b * (0.9 + rnd() * 0.2));
  }
  const starGeo = new THREE.BufferGeometry();
  starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos, 3));
  starGeo.setAttribute('color', new THREE.Float32BufferAttribute(starCol, 3));
  const stars = new THREE.Points(starGeo, new THREE.PointsMaterial({ size: 2.2, sizeAttenuation: false, vertexColors: true, map: softDot(), transparent: true, depthWrite: false, fog: false }));
  scene.add(stars);
  // visual moon (placed where it composes in the exterior shot)
  const moon = new THREE.Mesh(new THREE.SphereGeometry(5, 32, 16), new THREE.MeshBasicMaterial({ color: 0xe8eef8, fog: false }));
  moon.position.set(-95, 88, -92);
  scene.add(moon);
  const moonGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: softDot('rgba(200,215,255,0.7)', 'rgba(150,170,230,0.18)'), color: 0xaabbee, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }));
  moonGlow.scale.setScalar(40);
  moonGlow.position.copy(moon.position);
  scene.add(moonGlow);

  // ---------- Moonbeam (fake volumetric shaft + dust) ----------
  const beamLen = CEIL_Y / MOON_DIR.y;
  const beamGeo = new THREE.BoxGeometry(SKY.size * 0.98, beamLen, SKY.size * 0.98, 1, 1, 1);
  beamGeo.translate(0, -beamLen / 2, 0);
  const beamMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    uniforms: { color: { value: new THREE.Color(0x6f8fd0) }, strength: { value: 0.06 } },
    vertexShader: `varying float vH; varying vec3 vN; varying vec3 vV; varying vec2 vXZ;
      void main(){ vH = position.y; vXZ = position.xz; vec4 mv = modelViewMatrix*vec4(position,1.0); vV = normalize(-mv.xyz); vN = normalize(normalMatrix*normal); gl_Position = projectionMatrix*mv; }`,
    fragmentShader: `varying float vH; varying vec3 vN; varying vec3 vV; varying vec2 vXZ; uniform vec3 color; uniform float strength;
      void main(){ float f = smoothstep(${(-beamLen).toFixed(2)}, ${(-beamLen * 0.15).toFixed(2)}, vH)*0.55 + 0.45;
        float face = pow(abs(dot(vN,vV)), 1.5);
        float e = min(abs(vXZ.x), abs(vXZ.y)) / ${(SKY.size * 0.49).toFixed(3)};
        float soft = 1.0 - smoothstep(0.0, 1.0, e); // soft falloff toward the shaft's edges
        gl_FragColor = vec4(color*strength*f*face*soft*1.6, 1.0);} `,
  });
  const beam = new THREE.Mesh(beamGeo, beamMat);
  beam.position.set(SKY.x, CEIL_Y, SKY.z);
  beam.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), MOON_DIR);
  beam.renderOrder = 5;
  scene.add(beam);
  set.beam = beam;
  set.beamMat = beamMat;

  const dustN = 260;
  const dustBase = new Float32Array(dustN * 4);
  for (let i = 0; i < dustN; i++) {
    dustBase[i * 4] = (rnd() - 0.5) * SKY.size * 0.9;
    dustBase[i * 4 + 1] = rnd() * 7.5;
    dustBase[i * 4 + 2] = (rnd() - 0.5) * SKY.size * 0.9;
    dustBase[i * 4 + 3] = rnd() * 100;
  }
  const dustGeo = new THREE.BufferGeometry();
  dustGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(dustN * 3), 3));
  const dust = new THREE.Points(dustGeo, new THREE.PointsMaterial({ size: 0.035, color: 0xaabbe0, map: softDot(), transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending }));
  scene.add(dust);
  set.dust = { points: dust, base: dustBase, n: dustN };

  return set;
}

export function updateDust(set, t) {
  const { points, base, n } = set.dust;
  const pos = points.geometry.attributes.position.array;
  for (let i = 0; i < n; i++) {
    const ph = base[i * 4 + 3];
    const y = (base[i * 4 + 1] + t * 0.08 + Math.sin(ph + t * 0.3) * 0.1) % 7.5;
    // follow the beam slant: x/z shift with height
    const k = y / MOON_DIR.y;
    pos[i * 3] = SKY.x + base[i * 4] + Math.sin(ph * 1.7 + t * 0.4) * 0.12 + MOON_DIR.x * k - MOON_DIR.x * CEIL_Y / MOON_DIR.y;
    pos[i * 3 + 1] = y + 0.2;
    pos[i * 3 + 2] = SKY.z + base[i * 4 + 2] + Math.cos(ph + t * 0.35) * 0.12 + MOON_DIR.z * k - MOON_DIR.z * CEIL_Y / MOON_DIR.y;
  }
  points.geometry.attributes.position.needsUpdate = true;
}
