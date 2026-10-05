// Choreography: every value here is a pure function of t (seconds).
import { SHOT, EV, LAUNCH_ACC } from './timeline.js';
import { key, keyPathLength, clamp, smooth, bump, noise1, EASE, lerp } from './util.js';

const PI = Math.PI;
export const P0 = [-0.2, 0.55]; // Clawd's start AND end mark

// ---------------- Clawd: position + facing ----------------
export const POS = [
  [0.0, P0],
  [2.12, P0],
  [2.42, [-0.45, 0.7], 'out'],           // steps back to admire
  [3.86, [-0.45, 0.7]],
  [4.16, [-0.52, 1.2], 'io'],            // scoots to fuse end
  [4.36, [-0.52, 1.2]],
  [4.78, [-0.9, 0.82], 'out'],           // runs back, cowers
  [10.6, [-0.9, 0.82]],
  [10.98, [1.05, 0.95], 'in2'],          // dash right (whip)
  [11.12, [2.6, 0.45], 'out'],           // arrives at the fallen nose
  [11.45, [1.95, 0.42], 'io'],           // walks in while lifting the rocket up
  [11.6, [2.75, 0.05], 'io'],
  [11.75, [3.08, -1.05], 'io'],          // behind the booster
  [12.05, [2.13, -0.49], 'out'],         // push
  [12.15, [2.45, -0.35], 'out'],         // step aside to tape (beside the booster)
  [14.02, [2.45, -0.35]],
  [14.2, [2.65, 0.65], 'io'],            // around the booster
  [14.36, [1.08, 1.45], 'out'],          // to the new fuse
  [14.52, [1.08, 1.45]],
  [14.72, [0.25, 1.15], 'in2'],          // retreat...
  [14.95, P0, 'out'],                    // ...to the start mark
  [20.0, P0],
];

const ROT = [
  [0.0, 0.55], [2.12, 0.55], [2.42, 0.42], [3.12, 0.42], [3.3, 0.15, 'out'],
  [3.86, 0.25], [4.16, 0.3], [4.36, 0.3], [4.55, -0.6, 'out'], [4.78, 0.45, 'out'],
  [8.45, 0.45], [8.7, 0.3], [10.45, 0.3], [10.62, 1.25, 'out'], [10.98, 1.5],
  [11.12, -1.25, 'out'], [11.45, -1.35], [11.6, -0.2], [11.75, -1.04], [12.05, -1.04], [12.2, 0.27, 'out'],
  [13.95, 0.27], [14.12, 0.3, 'io'], [14.36, 0.35], [14.52, 0.35], [14.62, -1.4, 'out'], [14.88, -1.2],
  [15.05, 0.42, 'out'], [16.0, 0.38], [17.6, 0.22], [20, 0.12],
];

// ---------------- helpers ----------------
const BLINKS = [1.25, 2.18, 3.25, 9.55, 12.72, 13.95, 18.0, 19.25];
function blinkAt(t) {
  let b = 1;
  for (const tb of BLINKS) {
    const w = tb === 9.55 ? 0.2 : 0.09; // slow sad blink
    b = Math.min(b, 1 - bump(t, tb, w) * 0.94);
  }
  return b;
}
const shake = (t, amp, f = 37, seed = 1) => noise1(t * f, seed) * amp;

export function clawdPose(t) {
  const pos = key(t, POS);
  const p = {
    x: pos[0], z: pos[1], rotY: key(t, ROT),
    hopY: 0, sqY: 1, stretchX: 1, leanX: 0, leanZ: 0, bodyBob: 0,
    legA: 0, legB: 0,
    armPz: -0.15, armPy: 0, armNz: -0.15, armNy: 0,
    eyeX: 0, eyeY: 0, eyeH: 1, eyeW: 1, eyeTilt: 0, eyeSpread: 0, blink: blinkAt(t),
    frown: 0, smile: 0,
  };

  // idle life: breathing + micro sway (never fully still)
  const breath = Math.sin(t * 2 * PI / 1.7);
  p.sqY += breath * 0.012;
  p.leanZ += noise1(t * 0.9, 3) * 0.02;
  p.leanX += noise1(t * 0.7, 4) * 0.015;
  p.armPz += breath * 0.03;
  p.armNz += breath * 0.03;

  // gait from distance travelled
  const len = keyPathLength(t, POS);
  const sp = (keyPathLength(t + 0.02, POS) - keyPathLength(t - 0.02, POS)) / 0.04;
  const moving = clamp(sp / 1.2);
  const ph = len * 2.6 * 2 * PI;
  p.legA = Math.max(0, Math.sin(ph)) * 0.11 * moving;
  p.legB = Math.max(0, -Math.sin(ph)) * 0.11 * moving;
  p.hopY += Math.abs(Math.sin(ph)) * 0.05 * moving;
  p.leanX += 0.12 * moving;                      // lean into the run
  p.armPz += Math.sin(ph) * 0.35 * moving;        // arms flap (overlap)
  p.armNz -= Math.sin(ph) * 0.35 * moving;

  // ---------- SHOT 1: hammering with the wrench ----------
  if (t < SHOT.s2 + 0.2) {
    // arm wind-up -> strike, three times
    const az = key(t, [
      [0.0, 0.15], [0.62, 0.15], [0.8, 0.95, 'out'], [0.95, -0.35, 'in'], [1.1, -0.1, 'out'],
      [1.25, 0.95, 'out'], [1.4, -0.35, 'in'], [1.55, -0.1, 'out'],
      [1.7, 0.95, 'out'], [1.85, -0.35, 'in'], [2.0, -0.05, 'out'], [2.3, -0.3], [3.4, -0.25],
    ]);
    p.armPz = az + breath * 0.03;
    p.armPy = key(t, [[0, 0.35], [2.0, 0.35], [2.3, 0.1]]);
    // body anticipates each strike (lean back on wind-up, forward on hit)
    let hitK = 0;
    for (const h of EV.wrenchHits) hitK += bump(t, h + 0.03, 0.09);
    let wind = 0;
    for (const h of EV.wrenchHits) wind += bump(t, h - 0.14, 0.1);
    p.leanZ += -0.1 * hitK + 0.05 * wind;
    p.sqY += -0.05 * hitK + 0.03 * wind;
    // eyes: focused on the fin (look toward +x and down), slight squint
    p.eyeX += key(t, [[0, 0.06], [2.05, 0.06], [2.15, 0.03], [3.0, 0.03], [3.12, -0.07, 'out'], [3.4, -0.06]]);
    p.eyeY += key(t, [[0, -0.03], [2.05, -0.03], [2.2, 0.06, 'out'], [2.5, 0.0], [3.4, 0.0]]);
    p.eyeH = key(t, [[0, 0.82], [2.05, 0.82], [2.2, 1.12, 'out'], [2.45, 1.0], [2.95, 0.68], [3.15, 0.68], [3.25, 1.0]]);
    // look up at the rocket then the body follows (lean back)
    p.leanX += key(t, [[2.15, 0], [2.4, -0.16, 'out'], [2.5, -0.1]]);
    // proud hop: anticipation squash, stretch, apex, land squash, settle
    p.sqY *= key(t, [[2.45, 1], [2.58, 0.84, 'out'], [2.66, 1.14, 'out'], [2.78, 1.04], [2.9, 1.0], [2.95, 0.8, 'out'], [3.08, 1.04, 'out'], [3.2, 1.0]]);
    p.hopY += key(t, [[2.62, 0], [2.78, 0.32, 'out'], [2.93, 0, 'in2']]);
    p.armNz += bump(t, 2.78, 0.2) * 0.9;
    p.armPz += bump(t, 2.78, 0.2) * 0.6;
    p.smile = bump(t, 3.0, 0.22) * 0.0; // keep mouthless here: eyes carry the pride
  }

  // ---------- SHOT 2: match + fuse + cower ----------
  if (t >= SHOT.s2 - 0.01 && t < SHOT.s4) {
    // flick to strike the match, then reach toward the fuse
    p.armPz = key(t, [
      [3.4, -0.2], [3.62, 0.5, 'out'], [3.75, -0.45, 'in'], [3.86, 0.15, 'out'],
      [4.16, -0.3], [4.22, -0.1], [4.32, -0.95, 'in'], [4.4, -0.7], [4.55, 1.2, 'out'], [4.8, 1.45], [5.8, 1.4],
      [6.62, 1.4], [7.1, 0.5, 'io'], [8.2, -0.1],
    ]) + breath * 0.02;
    p.armPy = key(t, [[3.4, 0.2], [4.16, 0.4], [4.32, 0.55], [4.55, 0.6], [4.8, 0.85], [6.62, 0.85], [7.2, 0.2]]);
    p.armNz = key(t, [[4.36, -0.15], [4.6, 1.2, 'out'], [4.8, 1.45], [6.62, 1.4], [7.15, 0.4, 'io'], [8.2, -0.1]]);
    p.armNy = key(t, [[4.36, 0], [4.8, 0.85], [6.62, 0.85], [7.2, 0.2]]);
    // eyes: on the flame, then the fuse, wide at ignition, squeezed shut while cowering, peek
    p.eyeX += key(t, [[3.4, -0.02], [3.7, 0.05], [4.0, 0.07], [4.3, 0.07], [4.5, 0.02], [5.2, 0.05], [5.8, 0.07]]);
    p.eyeY += key(t, [[3.4, -0.02], [3.7, 0.0], [4.0, -0.05], [4.3, -0.05], [4.45, 0.02], [5.0, 0.0], [6.6, -0.02], [7.6, -0.06]]);
    p.eyeH = key(t, [[3.4, 1.0], [3.72, 1.0], [3.8, 1.18, 'out'], [3.95, 1.05], [4.3, 1.05], [4.36, 1.32, 'out'], [4.62, 1.2],
      [4.8, 0.42, 'out'], [5.25, 0.38], [5.55, 0.7, 'io'], [6.2, 0.75], [6.62, 1.15, 'out'], [7.0, 1.05], [7.55, 1.25, 'out'], [7.9, 1.0], [8.2, 0.95]]);
    // lean: away (anticipation) then into the reach, recoil, cower trembling
    p.leanZ += key(t, [[3.86, 0], [4.12, 0.12, 'out'], [4.32, -0.22, 'in'], [4.4, -0.1], [4.6, 0.1], [4.8, 0.05]]);
    p.leanX += key(t, [[4.2, 0], [4.32, 0.12], [4.5, -0.12, 'out'], [4.8, 0.06], [6.6, 0.06], [6.8, -0.04], [7.6, 0.1, 'out']]);
    p.sqY *= key(t, [[3.72, 1], [3.8, 0.94], [3.9, 1.0], [4.3, 1.0], [4.36, 1.1, 'out'], [4.5, 1.0], [4.8, 0.86, 'out'], [6.55, 0.86], [6.75, 1.04, 'out'], [7.0, 1.0], [7.5, 1.0], [7.58, 0.93], [7.7, 1.0]]);
    const tremble = smooth(4.8, 4.9, t) * (1 - smooth(6.5, 6.7, t));
    p.leanZ += shake(t, 0.025 * tremble, 45, 9);
    p.hopY += Math.abs(shake(t, 0.012 * tremble, 30, 10));
    // flinch at the topple impact
    p.sqY *= 1 - bump(t, EV.toppleHit + 0.04, 0.08) * 0.08;
  }

  // ---------- SHOT 4: frustration -> idea -> dash ----------
  if (t >= SHOT.s4 - 0.3 && t < SHOT.s5) {
    const slump = smooth(8.45, 9.1, t) * (1 - smooth(10.12, 10.3, t));
    // eyes first: look down at the fallen rocket
    p.eyeX += key(t, [[7.9, 0.07], [8.3, 0.08], [8.5, 0.03], [9.9, 0.03], [10.02, 0.1, 'out'], [10.45, 0.1], [10.6, 0.12]]);
    p.eyeY += key(t, [[7.9, -0.06], [8.3, -0.08], [8.6, -0.06], [9.9, -0.06], [10.02, 0.03, 'out'], [10.5, 0.02]]);
    p.eyeH = lerp(1.0, 0.6, slump) * key(t, [[9.95, 1], [10.15, 1], [10.25, 1.38, 'out'], [10.45, 1.25], [10.6, 1.05]]);
    p.eyeTilt = 0.22 * slump;
    p.eyeSpread = -0.02 * slump;
    p.frown = smooth(8.75, 9.1, t) * (1 - smooth(10.1, 10.2, t));
    // body slumps (squash), sigh (inhale/exhale), head down
    const sigh = key(t, [[8.7, 0], [8.95, 1, 'out'], [9.45, -0.6, 'io'], [9.9, 0]]);
    p.sqY *= lerp(1, 0.82, slump) * (1 + 0.05 * sigh);
    p.leanX += 0.18 * slump + 0.04 * sigh;
    p.armPz = lerp(p.armPz, -0.55, slump) + 0.12 * sigh;
    p.armNz = lerp(p.armNz, -0.55, slump) + 0.12 * sigh;
    p.leanZ += Math.sin(t * 2.2) * 0.025 * slump;
    // idea: pop up (stretch), arms up a bit
    const pop = bump(t, 10.27, 0.14);
    p.sqY *= 1 + 0.16 * pop;
    p.hopY += 0.08 * pop;
    p.armPz += 0.9 * pop;
    p.armNz += 0.9 * pop;
    // anticipation for the dash: squash + lean left (away), then stretch into the run
    const ant = bump(t, 10.52, 0.1);
    p.sqY *= 1 - 0.14 * ant;
    p.leanZ += 0.18 * ant;
    p.stretchX = 1 + 0.12 * smooth(10.6, 10.7, t);
  }

  // ---------- SHOT 5: lift rocket, push booster, tape ----------
  if (t >= SHOT.s5 - 0.05 && t < SHOT.s6) {
    p.stretchX = 1 + 0.12 * (1 - smooth(10.98, 11.12, t));
    // lifting: arms up high, stretch, eyes up following the nose
    const lift = smooth(11.1, 11.3, t) * (1 - smooth(11.45, 11.55, t));
    p.armPz = lerp(p.armPz, 1.25, lift);
    p.armNz = lerp(p.armNz, 1.25, lift);
    p.armPy = lerp(0, 0.7, lift);
    p.armNy = lerp(0, 0.7, lift);
    p.sqY *= 1 + 0.1 * lift - 0.1 * bump(t, 11.15, 0.06);
    p.eyeY += 0.05 * lift;
    p.eyeH = 1 + 0.1 * lift;
    p.sqY *= 1 - bump(t, EV.liftUp + 0.03, 0.07) * 0.06;
    // pushing: lean forward, squash, arms forward
    const push = smooth(11.72, 11.8, t) * (1 - smooth(12.05, 12.15, t));
    p.leanX += 0.25 * push;
    p.sqY *= 1 - 0.08 * push;
    p.armPy = lerp(p.armPy, 1.2, push);
    p.armNy = lerp(p.armNy, 1.2, push);
    p.armPz = lerp(p.armPz, 0.1, push);
    p.armNz = lerp(p.armNz, 0.1, push);
    p.eyeH *= 1 - 0.3 * push;
    p.sqY *= 1 - bump(t, EV.pushHit + 0.03, 0.07) * 0.07;
    // taping: +x arm circles forward, body sways with each pull
    const tapeK = Math.max(clamp((t - EV.tape1[0]) / (EV.tape1[1] - EV.tape1[0])) * (t < EV.tape1Rip + 0.05 ? 1 : 0),
      clamp((t - EV.tape2[0]) / (EV.tape2[1] - EV.tape2[0])) * (t > EV.tape2[0] - 0.05 && t < EV.tape2Rip + 0.05 ? 1 : 0));
    const taping = smooth(12.12, 12.2, t) * (1 - smooth(13.3, 13.4, t));
    const circ = Math.sin(tapeK * 2 * PI * 1.0);
    p.armNy = lerp(p.armNy, 0.15 + 0.3 * circ, taping);
    p.armNz = lerp(p.armNz, 0.15 + 0.3 * Math.cos(tapeK * 2 * PI), taping);
    p.armPy = lerp(p.armPy, 0.2, taping);
    p.armPz = lerp(p.armPz, -0.1, taping);
    p.leanZ += 0.08 * circ * taping;
    p.leanX += 0.08 * taping;
    p.eyeX += 0.0;
    p.eyeY += -0.03 * taping;
    p.eyeH = lerp(p.eyeH, 0.85, taping);
    // rip: quick yank back
    for (const r of [EV.tape1Rip, EV.tape2Rip]) {
      const y = bump(t, r + 0.04, 0.08);
      p.armNy -= 0.6 * y;
      p.leanX -= 0.1 * y;
      p.eyeH *= 1 + 0.25 * y;
    }
    // pats + proud nod
    let pat = 0;
    for (const pt of EV.pats) pat += bump(t, pt, 0.07);
    const patWin = smooth(13.35, 13.42, t) * (1 - smooth(13.78, 13.9, t));
    p.armNy = lerp(p.armNy, 0.35, patWin);
    p.armNz = lerp(p.armNz, 0.45 - 0.55 * pat, patWin);
    p.sqY *= 1 - 0.03 * pat;
    const nod = bump(t, 13.85, 0.12);
    p.leanX += 0.12 * nod;
    p.sqY *= 1 + 0.05 * bump(t, 13.95, 0.08);
    p.eyeH *= key(t, [[13.75, 1], [13.85, 0.62], [13.98, 0.62], [14.05, 1]]);
  }

  // ---------- SHOT 6: relight, retreat, launch ----------
  if (t >= SHOT.s6 - 0.05 && t < SHOT.s7 + 0.2) {
    p.armPz = key(t, [[14.0, 0.0], [14.1, 0.6, 'out'], [14.16, -0.3, 'in'], [14.36, -0.5], [14.44, -1.0, 'in'], [14.52, -0.8], [14.68, 1.3, 'out'], [14.95, 1.45], [15.05, 1.2], [15.4, 0.4, 'io'], [16.2, 0.1]]);
    p.armPy = key(t, [[14.0, 0.3], [14.36, 0.45], [14.44, 0.55], [14.7, 0.85], [15.05, 0.85], [15.5, 0.2]]);
    p.armNz = key(t, [[14.5, -0.1], [14.7, 1.3, 'out'], [14.95, 1.45], [15.05, 1.2], [15.45, 0.5, 'io'], [16.2, 0.2]]);
    p.armNy = key(t, [[14.5, 0], [14.75, 0.85], [15.05, 0.85], [15.5, 0.2]]);
    p.eyeX += key(t, [[14.0, -0.02], [14.3, 0.06], [14.45, 0.05], [14.95, 0.07], [15.1, 0.04], [16, 0.03]]);
    p.eyeY += key(t, [[14.0, 0], [14.3, -0.05], [14.45, -0.05], [14.95, 0], [15.1, 0.03], [15.4, 0.08, 'out'], [16, 0.09]]);
    p.eyeH = key(t, [[14.0, 1.0], [14.15, 1.15], [14.3, 1.0], [14.45, 1.3, 'out'], [14.6, 1.1], [14.85, 0.45], [15.0, 0.4], [15.08, 1.35, 'out'], [15.4, 1.25], [16, 1.2]]);
    p.leanZ += key(t, [[14.3, 0], [14.4, 0.1], [14.46, -0.2, 'in'], [14.55, 0]]);
    p.leanX += key(t, [[14.9, 0.05], [15.0, 0.05], [15.08, -0.2, 'out'], [15.35, -0.3, 'io'], [16.0, -0.34]]);
    p.sqY *= key(t, [[14.85, 1], [14.95, 0.86, 'out'], [15.0, 0.86], [15.1, 1.06, 'out'], [15.3, 1.0]]);
    // trembling while waiting for the second ignition
    const tr = smooth(14.9, 14.95, t) * (1 - smooth(15.0, 15.04, t));
    p.leanZ += shake(t, 0.03 * tr, 45, 12);
  }

  // ---------- SHOT 8: wonder + joy, same mark as the start ----------
  if (t >= SHOT.s8 - 0.4) {
    const w = smooth(SHOT.s8 - 0.4, SHOT.s8, t);
    p.leanX = lerp(p.leanX, -0.38 + noise1(t * 0.8, 2) * 0.02, w);
    p.eyeY += lerp(0, 0.1, w);
    p.eyeX += lerp(0, 0.02, w);
    p.eyeH = lerp(p.eyeH, 1.18, w);
    // first a held breath of wonder, then joy at the burst
    const joy = smooth(18.1, 18.3, t);
    p.smile = joy * 0.95;
    p.eyeH *= key(t, [[18.05, 1], [18.15, 1.12], [18.3, 0.78], [18.9, 0.82], [19.2, 0.95]]);
    const hop1 = key(t, [[18.2, 0], [18.33, 0.2, 'out'], [18.46, 0, 'in2'], [18.6, 0.13, 'out'], [18.72, 0, 'in2']]);
    p.hopY += hop1;
    p.sqY *= key(t, [[18.12, 1], [18.2, 0.86], [18.28, 1.1], [18.4, 1.02], [18.46, 0.86], [18.53, 1.08], [18.66, 1.02], [18.72, 0.9], [18.85, 1.02], [19.0, 1]]);
    const wave = smooth(18.2, 18.35, t) * (1 - smooth(19.1, 19.6, t));
    p.armPz = lerp(p.armPz, 1.3 + Math.sin(t * 14) * 0.25, wave);
    p.armNz = lerp(p.armNz, 1.3 + Math.sin(t * 14 + 1.4) * 0.25, wave);
    p.armPy = lerp(p.armPy, 0.2, wave);
    p.armNy = lerp(p.armNy, 0.2, wave);
    p.leanZ += Math.sin(t * 7) * 0.05 * wave;
  }
  return p;
}

// ---------------- rocket ----------------
export function rocketTilt(t) {
  let a = 0;
  if (t >= EV.toppleStart && t < SHOT.s5) {
    a = key(t, [
      [7.0, 0], [7.12, 0.07, 'out'], [7.22, -0.04, 'io'], [7.55, -PI / 2, 'in2'], [7.66, -PI / 2 + 0.14, 'out'],
      [7.78, -PI / 2, 'in2'], [7.86, -PI / 2 + 0.035, 'out'], [7.94, -PI / 2, 'in2'],
    ]);
  } else if (t >= SHOT.s5 && t < 12) {
    a = key(t, [[11.1, -PI / 2], [11.45, 0, 'io'], [11.53, 0.06, 'out'], [11.62, -0.025], [11.72, 0]]);
  }
  // failure shudder
  const sh = smooth(6.3, 6.4, t) * (1 - smooth(6.9, 6.98, t));
  a += shake(t, 0.05 * sh, 55, 21);
  return a;
}
export function launchY(t) {
  if (t < EV.liftoff) return 0;
  const d = t - EV.liftoff;
  return 0.5 * LAUNCH_ACC * d * d;
}
export function launchShake(t) {
  const pre = smooth(14.88, 15.0, t);
  return shake(t, 0.035 * pre * (1 - smooth(15.4, 15.6, t)), 60, 31);
}
// exterior shot: cheat the climb so it reads (emerges, rises, bursts at the apex)
export function exteriorRocketY(t, ceilY) {
  const u = clamp((t - SHOT.s7) / (EV.bursts[0] - SHOT.s7));
  return ceilY + 0.2 + (31 - ceilY) * EASE.out2(u);
}

// ---------------- camera ----------------
// returns {pos:[x,y,z], look:[x,y,z], fov, focus}
export function cameraAt(t) {
  if (t < SHOT.s2) {
    const u = t / SHOT.s2;
    return {
      pos: key(t, [[0, [-3.4, 3.4, 8.2]], [3.4, [-1.05, 1.6, 4.25], 'out2']]),
      look: key(t, [[0, [0.1, 1.0, 0]], [3.4, [0.25, 0.75, 0.25], 'out2']]),
      fov: 36, focus: null, u,
    };
  }
  if (t < SHOT.s3) {
    return {
      pos: key(t, [[3.4, [1.55, 1.45, 4.9]], [5.2, [1.35, 1.35, 4.6]], [5.8, [1.3, 0.62, 2.05], 'in2']]),
      look: key(t, [[3.4, [-0.1, 0.55, 0.8]], [5.2, [0.0, 0.5, 0.8]], [5.8, [0.78, 0.18, 0.35], 'in2']]),
      fov: 36, focus: null,
    };
  }
  if (t < SHOT.s4) {
    return {
      pos: key(t, [[5.8, [2.15, 0.52, 2.15]], [8.2, [2.3, 0.6, 2.35], 'sine']]),
      look: key(t, [[5.8, [1.05, 0.48, 0.05]], [7.3, [1.2, 0.42, 0.0]], [8.2, [1.35, 0.3, 0.0], 'sine']]),
      fov: 34, focus: null,
    };
  }
  if (t < SHOT.s5) {
    // close on Clawd, slow push-in during the sadness, whip right with the dash
    const whip = EASE.in2(clamp((t - 10.62) / (SHOT.s5 - 10.62)));
    const base = key(t, [[8.2, [-0.2, 1.15, 4.3]], [10.0, [-0.45, 1.05, 3.6], 'sine']]);
    const look0 = key(t, [[8.2, [-0.1, 0.62, 0.6]], [10.0, [-0.45, 0.66, 0.7], 'sine'], [10.3, [-0.2, 0.68, 0.7]]]);
    const look1 = [2.4, 0.7, 0.4];
    return {
      pos: [base[0] + whip * 0.5, base[1], base[2]],
      look: look0.map((v, i) => lerp(v, look1[i], whip)),
      fov: 34, focus: null,
    };
  }
  if (t < SHOT.s6) {
    // settle out of the whip
    const s = EASE.out(clamp((t - SHOT.s5) / 0.4));
    const pos = key(t, [[10.9, [2.0, 1.5, 4.2]], [12.1, [2.35, 1.4, 4.0], 'sine'], [14.0, [2.2, 1.35, 3.9], 'sine']]);
    const look = key(t, [[10.9, [1.9, 0.6, 0.0]], [12.1, [1.8, 0.55, -0.25]], [14.0, [1.7, 0.6, -0.2], 'sine']]);
    look[0] += (1 - s) * -1.6;
    return { pos, look, fov: 36, focus: null };
  }
  if (t < SHOT.s7) {
    const ry = launchY(t);
    const follow = smooth(15.0, 15.25, t);
    const pos = key(t, [[14.0, [0.9, 1.35, 5.0]], [14.6, [0.45, 1.2, 4.8]], [15.0, [1.4, 1.1, 4.6]], [15.4, [3.0, 1.6, 5.0]], [16.0, [3.6, 2.3, 5.6], 'io']]);
    const lookY = lerp(0.65, Math.min(ry + 0.7, 15.5), follow);
    const look = [lerp(key(t, [[14.0, 1.35], [14.6, 0.8], [15.0, 0.6]]), 0.9, follow), lookY, lerp(0.5, 0.05, follow)];
    return { pos, look, fov: lerp(36, 46, smooth(15.1, 15.7, t)), focus: null };
  }
  if (t < SHOT.s8) {
    const tilt = EASE.in2(clamp((t - 17.3) / (SHOT.s8 - 17.3)));
    const pos = key(t, [[16.0, [10.5, 16.2, 15.5]], [17.6, [9.2, 16.8, 13.8], 'sine']]);
    const lookUp = key(t, [[16.0, [0.9, 19.5, 0]], [16.7, [0.9, 27, 0], 'io'], [17.3, [0.4, 28.5, 0]]]);
    const lookDown = [0.9, 14.5, 0];
    return { pos, look: lookUp.map((v, i) => lerp(v, lookDown[i], tilt)), fov: 44, focus: null };
  }
  // ending: crane down from high to Clawd's face, keep drifting
  const u = clamp((t - SHOT.s8) / (SHOT.end - SHOT.s8));
  return {
    pos: key(t, [[17.6, [0.15, 5.4, 3.2]], [19.0, [-0.55, 1.75, 3.15], 'out2'], [20.0, [-0.75, 1.45, 3.3], 'lin']]),
    look: key(t, [[17.6, [-0.15, 0.55, 0.45]], [19.0, [-0.2, 0.95, 0.35], 'out2'], [20, [-0.2, 1.0, 0.3], 'lin']]),
    fov: 36, focus: null, u,
  };
}
