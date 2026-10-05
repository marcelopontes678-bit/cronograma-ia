// Clawd: chunky terracotta clay block, wider than tall, four short legs in a row,
// two little side arms, two tall dark slit eyes. Mouth only appears for emotion.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { clayBump } from './textures.js';

export const DIM = { W: 1.3, H: 0.82, D: 0.85, LEG: 0.26 };

export function buildClawd() {
  const bump = clayBump(7);
  bump.repeat.set(1.3, 1);
  const clay = new THREE.MeshPhysicalMaterial({
    color: 0xd97757,
    roughness: 0.86,
    metalness: 0,
    bumpMap: bump,
    bumpScale: 1.4,
    sheen: 0.35,
    sheenRoughness: 0.8,
    sheenColor: new THREE.Color(0xffc3a6),
  });
  const clayDark = clay.clone();
  clayDark.color = new THREE.Color(0xc4674a); // legs a touch darker (occluded clay)
  const eyeMat = new THREE.MeshStandardMaterial({ color: 0x1a120f, roughness: 0.38 });

  const group = new THREE.Group();     // world placement + facing
  const rig = new THREE.Group();       // squash/stretch, pivot at feet
  group.add(rig);

  const legs = [];
  const legGeo = new RoundedBoxGeometry(0.17, DIM.LEG + 0.06, 0.3, 2, 0.05);
  for (const x of [-0.48, -0.16, 0.16, 0.48]) {
    const leg = new THREE.Mesh(legGeo, clayDark);
    leg.position.set(x, (DIM.LEG + 0.06) / 2 - 0.0, 0);
    leg.castShadow = leg.receiveShadow = true;
    leg.userData.baseY = leg.position.y;
    rig.add(leg);
    legs.push(leg);
  }

  const bodyPivot = new THREE.Group();
  bodyPivot.position.y = DIM.LEG;
  rig.add(bodyPivot);

  const body = new THREE.Mesh(new RoundedBoxGeometry(DIM.W, DIM.H, DIM.D, 5, 0.14), clay);
  body.position.y = DIM.H / 2;
  body.castShadow = body.receiveShadow = true;
  bodyPivot.add(body);

  // Eyes
  const eyeGeo = new RoundedBoxGeometry(0.1, 0.31, 0.06, 3, 0.035);
  const eyes = [];
  for (const s of [-1, 1]) {
    const pivot = new THREE.Group();
    pivot.position.set(s * 0.27, DIM.H * 0.6, DIM.D / 2 - 0.012);
    const eye = new THREE.Mesh(eyeGeo, eyeMat);
    eye.castShadow = false;
    pivot.add(eye);
    pivot.userData.side = s;
    pivot.userData.base = pivot.position.clone();
    bodyPivot.add(pivot);
    eyes.push(pivot);
  }

  // Mouths (hidden unless emotion needs them)
  const mouthGeo = new THREE.TorusGeometry(0.075, 0.017, 8, 20, Math.PI);
  const frown = new THREE.Mesh(mouthGeo, eyeMat);
  frown.position.set(0, DIM.H * 0.33, DIM.D / 2 + 0.002);
  bodyPivot.add(frown);
  const smile = new THREE.Mesh(mouthGeo, eyeMat);
  smile.rotation.z = Math.PI;
  smile.position.set(0, DIM.H * 0.36, DIM.D / 2 + 0.002);
  bodyPivot.add(smile);

  // Arms
  const armGeo = new RoundedBoxGeometry(0.26, 0.18, 0.24, 3, 0.07);
  const arms = {};
  for (const s of [-1, 1]) {
    const pivot = new THREE.Group();
    pivot.rotation.order = 'YZX';
    pivot.position.set(s * (DIM.W / 2 - 0.02), DIM.H * 0.4, 0.02);
    const arm = new THREE.Mesh(armGeo, clay);
    arm.position.x = s * 0.11;
    arm.castShadow = arm.receiveShadow = true;
    pivot.add(arm);
    const hand = new THREE.Object3D();
    hand.position.set(s * 0.25, 0, 0);
    pivot.add(hand);
    bodyPivot.add(pivot);
    arms[s > 0 ? 'p' : 'n'] = { pivot, hand };
  }

  return { group, rig, legs, bodyPivot, body, eyes, frown, smile, arms, clay };
}

// p: pose object produced by story.js
export function applyPose(c, p) {
  c.group.position.set(p.x, p.y || 0, p.z);
  c.group.rotation.y = p.rotY;

  const sy = p.sqY;
  const sxz = 1 / Math.sqrt(sy);
  c.rig.scale.set(sxz * (p.stretchX || 1), sy, sxz);
  c.rig.position.y = p.hopY;

  c.bodyPivot.rotation.set(p.leanX, 0, p.leanZ);
  c.bodyPivot.position.y = DIM.LEG + (p.bodyBob || 0);

  // legs: alternate pairs lift with gait phase
  c.legs.forEach((leg, i) => {
    const lift = i % 2 === 0 ? p.legA : p.legB;
    leg.position.y = leg.userData.baseY + lift;
    leg.rotation.x = -lift * 1.4;
  });

  for (const e of c.eyes) {
    const s = e.userData.side;
    const b = e.userData.base;
    e.position.set(b.x + p.eyeX + s * (p.eyeSpread || 0), b.y + p.eyeY, b.z);
    e.scale.set(p.eyeW || 1, Math.max(0.06, p.eyeH * p.blink), 1);
    e.rotation.z = -s * p.eyeTilt;
  }

  c.frown.scale.setScalar(Math.max(0.001, p.frown));
  c.frown.visible = p.frown > 0.01;
  c.smile.scale.setScalar(Math.max(0.001, p.smile));
  c.smile.visible = p.smile > 0.01;

  const ap = c.arms.p.pivot, an = c.arms.n.pivot;
  ap.rotation.z = p.armPz;
  ap.rotation.y = -p.armPy;
  an.rotation.z = -p.armNz;
  an.rotation.y = p.armNy;
}
