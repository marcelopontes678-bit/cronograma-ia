// Assembles the film and exposes renderAt(t). HyperFrames drives it through `hf-seek`.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

import { SHOT, EV, FPS } from './timeline.js';
import { clamp, smooth, lerp, hash1, noise1, EASE } from './util.js';
import { buildClawd, applyPose } from './clawd.js';
import { buildSet, updateDust, CEIL_Y, SKY, MOON_DIR } from './set.js';
import {
  buildRocket, buildBooster, buildFuse, setFuseBurn, buildTapeBand, setTapeProgress, buildMatch,
  buildHandWrench, buildTapeRoll, buildStrip, setStrip, R0, B0, B1, ROCKET_R,
} from './props.js';
import {
  PointLayer, emitSparks, buildFlame, SmokeLayer, smokePuffAt, fireworkBurst, burstEnvelope,
  buildShards, updateShards,
} from './fx.js';
import { clawdPose, rocketTilt, launchY, launchShake, exteriorRocketY, cameraAt, P0 } from './story.js';

const W = 1920, H = 1080;

export function createFilm(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x0b0d16, 0.012);
  const camera = new THREE.PerspectiveCamera(36, W / H, 0.05, 600);

  // ---------- set ----------
  const set = buildSet(scene);

  // ---------- lights ----------
  const hemi = new THREE.HemisphereLight(0x3a4a78, 0x3a2414, 0.9);
  scene.add(hemi);
  // warm bounce fill from the bench toward the faces (no shadows)
  const fill = new THREE.DirectionalLight(0xffb27a, 0.35);
  fill.position.set(1, 2, 8);
  scene.add(fill);

  const lamp = new THREE.SpotLight(0xffbf80, 120, 22, 0.62, 0.75, 1.6);
  lamp.position.copy(set.lampPos);
  lamp.target.position.copy(set.lampTarget);
  lamp.castShadow = true;
  lamp.shadow.mapSize.set(2048, 2048);
  lamp.shadow.radius = 6;
  lamp.shadow.bias = -0.0004;
  lamp.shadow.normalBias = 0.02;
  lamp.shadow.camera.near = 0.5;
  lamp.shadow.camera.far = 20;
  scene.add(lamp, lamp.target);

  const moon = new THREE.DirectionalLight(0x8eaaff, 1.6);
  moon.position.set(SKY.x + MOON_DIR.x * 30, MOON_DIR.y * 30, SKY.z + MOON_DIR.z * 30);
  moon.target.position.set(SKY.x - MOON_DIR.x * CEIL_Y, 0, SKY.z - MOON_DIR.z * CEIL_Y);
  moon.castShadow = true;
  moon.shadow.mapSize.set(2048, 2048);
  moon.shadow.camera.left = -9; moon.shadow.camera.right = 9;
  moon.shadow.camera.top = 9; moon.shadow.camera.bottom = -9;
  moon.shadow.camera.near = 1; moon.shadow.camera.far = 60;
  moon.shadow.radius = 4;
  moon.shadow.bias = -0.0005;
  moon.shadow.normalBias = 0.03;
  scene.add(moon, moon.target);
  // exterior moon fill (roof / neighbours), not shadowed
  const moonExt = new THREE.DirectionalLight(0x8090c0, 0.0);
  moonExt.position.set(-60, 120, -110);
  scene.add(moonExt);

  const sparkLight = new THREE.PointLight(0xffa040, 0, 4, 2);
  scene.add(sparkLight);
  const flameLight = new THREE.PointLight(0xff8a30, 0, 18, 1.6);
  scene.add(flameLight);
  const fwSpot = new THREE.SpotLight(0xffffff, 0, 30, 0.42, 0.9, 1.2);
  fwSpot.position.set(SKY.x, CEIL_Y + 2, SKY.z);
  fwSpot.target.position.set(SKY.x - 0.6, 0, SKY.z + 0.8);
  fwSpot.castShadow = true;
  fwSpot.shadow.mapSize.set(1024, 1024);
  fwSpot.shadow.radius = 5;
  fwSpot.shadow.bias = -0.0005;
  scene.add(fwSpot, fwSpot.target);
  const fwPoint = new THREE.PointLight(0xffffff, 0, 80, 1.2);
  scene.add(fwPoint);

  // ---------- characters & props ----------
  const clawd = buildClawd();
  scene.add(clawd.group);

  const rocket = buildRocket();
  scene.add(rocket);
  const booster = buildBooster();
  scene.add(booster);
  const fuse1 = buildFuse([[0.84, 0.03, 0.18], [0.74, 0.02, 0.48], [0.56, 0.02, 0.74], [0.36, 0.02, 0.97]]);
  scene.add(fuse1.group);
  const fuse2 = buildFuse([[1.5, 0.03, 0.2], [1.63, 0.02, 0.55], [1.75, 0.02, 0.86], [1.92, 0.02, 1.15]], 0x5a4b30);
  scene.add(fuse2.group);
  const tapeA = buildTapeBand(0.36, 0.1);
  const tapeB = buildTapeBand(0.86, 0.1);
  scene.add(tapeA, tapeB);
  const strip = buildStrip();
  scene.add(strip);

  const wrench = buildHandWrench(set.mats.metal);
  clawd.arms.p.hand.add(wrench);
  const match1 = buildMatch();
  const match2 = buildMatch();
  scene.add(match1, match2);
  const tapeRoll = buildTapeRoll();
  scene.add(tapeRoll);

  // ---------- fx ----------
  const sparks = new PointLayer(900);
  scene.add(sparks.points);
  const fw = new PointLayer(9000);
  scene.add(fw.points);
  const smoke = new SmokeLayer(scene, 170);
  const flameR = buildFlame();
  const flameB = buildFlame();
  scene.add(flameR, flameB);
  const shards = buildShards(scene, 46, 77, new THREE.Vector3(SKY.x, CEIL_Y + 0.25, SKY.z), SKY.size * 0.95);

  const bursts = [
    { t0: EV.bursts[0], c: new THREE.Vector3(0.9, 31, 0), colors: [new THREE.Color(1.0, 0.32, 0.12), new THREE.Color(1.0, 0.62, 0.15)], n: 280, speed: 12, size: 0.24, seed: 11 },
    { t0: EV.bursts[1], c: new THREE.Vector3(-5.5, 33, -3), colors: [new THREE.Color(0.15, 0.45, 1.0), new THREE.Color(0.35, 0.75, 1.0)], n: 240, speed: 11, size: 0.22, seed: 23 },
    { t0: EV.bursts[2], c: new THREE.Vector3(6.5, 29, -2), colors: [new THREE.Color(1.0, 0.2, 0.6), new THREE.Color(0.25, 1.0, 0.35)], n: 240, speed: 11, size: 0.22, seed: 37 },
    { t0: EV.bursts[3], c: new THREE.Vector3(1.5, 34, -4), colors: [new THREE.Color(1.0, 0.7, 0.15)], n: 280, speed: 12, size: 0.24, seed: 41 },
    { t0: EV.bursts[4], c: new THREE.Vector3(-3, 31, 2), colors: [new THREE.Color(0.15, 0.9, 0.75), new THREE.Color(0.2, 0.45, 1.0)], n: 240, speed: 11, size: 0.22, seed: 53 },
    { t0: EV.bursts[5], c: new THREE.Vector3(3, 32, 1), colors: [new THREE.Color(1.0, 0.25, 0.2), new THREE.Color(1.0, 0.75, 0.35)], n: 280, speed: 12, size: 0.24, seed: 61 },
  ];

  // burst colours are authored in sRGB (what the eye should see) -> convert to linear
  for (const b of bursts) b.colors.forEach((c) => c.convertSRGBToLinear());

  // ---------- post ----------
  const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, rt);
  composer.setPixelRatio(1);
  composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  const bokeh = new BokehPass(scene, camera, { focus: 4, aperture: 0.0016, maxblur: 0.006 });
  const noDepth = [sparks.points, fw.points, set.beam, set.dust.points, set.glass, flameR, flameB, ...smoke.sprites];
  const bokehRender = bokeh.render.bind(bokeh);
  bokeh.render = (...a) => {
    const vis = noDepth.map((o) => o.visible);
    noDepth.forEach((o) => (o.visible = false));
    bokehRender(...a);
    noDepth.forEach((o, i) => (o.visible = vis[i]));
  };
  composer.addPass(bokeh);
  const blurPass = new ShaderPass({
    uniforms: { tDiffuse: { value: null }, dir: { value: new THREE.Vector2() } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0);} `,
    fragmentShader: `uniform sampler2D tDiffuse; uniform vec2 dir; varying vec2 vUv;
      void main(){ vec4 c = vec4(0.0); for (int i=0;i<16;i++){ float k = float(i)/15.0 - 0.5; c += texture2D(tDiffuse, vUv + dir*k);} gl_FragColor = c/16.0; }`,
  });
  composer.addPass(blurPass);
  composer.addPass(new OutputPass());
  const grade = new ShaderPass({
    uniforms: { tDiffuse: { value: null }, fade: { value: 1 }, seed: { value: 0 }, vig: { value: 0.32 } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0);} `,
    fragmentShader: `uniform sampler2D tDiffuse; uniform float fade; uniform float seed; uniform float vig; varying vec2 vUv;
      float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + seed*0.6180339) * 43758.5453); }
      void main(){ vec3 c = texture2D(tDiffuse, vUv).rgb;
        vec2 d = vUv - 0.5; d.x *= 1.25; float v = 1.0 - vig*smoothstep(0.25, 0.85, length(d));
        c *= v;
        c = mix(c, c*vec3(1.03,1.0,0.97), 0.5); // slight warm print
        c += (h(vUv*vec2(1920.0,1080.0)) - 0.5) * 0.028; // stop-motion film grain
        gl_FragColor = vec4(c*fade, 1.0); }`,
  });
  composer.addPass(grade);

  // ---------- helpers ----------
  const tmpV = new THREE.Vector3();
  const fuse1Burn = (t) => clamp((t - EV.fuse1On) / (EV.fuse1Out - EV.fuse1On));
  const fuse2Burn = (t) => clamp((t - EV.fuse2On) / (EV.ignite - EV.fuse2On));
  const fusePoint = (f, burnt) => f.curve.getPoint(clamp(1 - burnt, 0, 1));

  function poseAndHand(t) {
    applyPose(clawd, clawdPose(t));
    clawd.group.updateMatrixWorld(true);
    return clawd.arms.p.hand.getWorldPosition(new THREE.Vector3());
  }
  // a match held in the hand until `drop`, then falls in an arc to the bench
  function placeMatch(m, t, tOn, tLit, tDrop, tOut) {
    m.visible = t >= tOn;
    if (!m.visible) return;
    const lit = t >= tLit && t < tOut;
    const fl = lit ? (0.85 + 0.15 * Math.sin(t * 47) * Math.sin(t * 13)) * smooth(tLit, tLit + 0.05, t) * (1 - smooth(tOut - 0.1, tOut, t)) : 0;
    m.userData.flame.visible = fl > 0.01;
    m.userData.flame.scale.set(0.16 * (0.8 + 0.4 * fl), 0.3 * fl, 1);
    m.userData.light.intensity = 2.2 * fl;
    m.userData.flareK = fl;
    if (t < tDrop) {
      // attached: copy hand transform (re-pose at t in case another prop re-posed the rig)
      poseAndHand(t);
      const hand = clawd.arms.p.hand;
      hand.updateWorldMatrix(true, false);
      m.position.setFromMatrixPosition(hand.matrixWorld);
      m.quaternion.setFromRotationMatrix(hand.matrixWorld);
    } else {
      // fall from the hand position at tDrop
      const startPos = poseAndHand(tDrop);
      const q = new THREE.Quaternion().setFromRotationMatrix(clawd.arms.p.hand.matrixWorld);
      const dt = t - tDrop;
      const fallT = Math.sqrt((2 * Math.max(0.02, startPos.y - 0.02)) / 9);
      const u = Math.min(dt, fallT);
      m.position.set(startPos.x - 0.25 * u, Math.max(0.02, startPos.y - 4.5 * u * u), startPos.z + 0.1 * u);
      const flat = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0.6, 0));
      m.quaternion.copy(q).slerp(flat, clamp(u / fallT));
    }
  }

  // ---------- the frame ----------
  function renderAt(tIn) {
    const t = clamp(tIn, 0, SHOT.end - 1e-4);
    const exterior = t >= SHOT.s7 && t < SHOT.s8;
    const frame = Math.round(t * FPS);

    // camera
    const cam = cameraAt(t);
    camera.position.set(...cam.pos);
    camera.fov = cam.fov;
    camera.near = exterior ? 0.5 : 0.05;
    camera.updateProjectionMatrix();
    camera.lookAt(...cam.look);
    // handheld micro drift (stop-motion rig wobble)
    camera.rotation.z += noise1(t * 0.6, 77) * 0.004;

    // ---- rocket & booster ----
    const ly = launchY(t);
    const lsh = launchShake(t);
    const tilt = rocketTilt(t);
    let rocketVisible = true;
    if (exterior) {
      const ey = exteriorRocketY(t, CEIL_Y);
      rocket.position.set(R0.x, ey, R0.z);
      rocket.rotation.set(0, 0, 0);
      rocketVisible = t < EV.bursts[0];
    } else {
      const pivot = new THREE.Vector3(R0.x - ROCKET_R * Math.sign(tilt || -1), 0, R0.z);
      const off = R0.clone().sub(pivot).applyAxisAngle(new THREE.Vector3(0, 0, 1), tilt);
      rocket.position.copy(pivot).add(off);
      rocket.position.y += ly;
      rocket.position.x += lsh;
      rocket.rotation.set(0, 0, tilt + lsh * 0.5);
      rocketVisible = ly < 40;
    }
    rocket.visible = rocketVisible;

    const pushU = EASE.out(clamp((t - EV.pushStart) / (EV.pushHit - EV.pushStart)));
    booster.position.copy(B0).lerp(B1, pushU);
    booster.rotation.set(0, 0, 0);
    if (exterior) booster.position.set(B1.x, rocket.position.y, B1.z);
    else { booster.position.y += ly; booster.position.x += lsh; booster.rotation.z = lsh * 0.5; }
    booster.visible = rocketVisible;

    // tape bands
    const tp1 = clamp((t - EV.tape1[0]) / (EV.tape1[1] - EV.tape1[0]));
    const tp2 = clamp((t - EV.tape2[0]) / (EV.tape2[1] - EV.tape2[0]));
    const end1 = setTapeProgress(tapeA, tp1);
    const end2 = setTapeProgress(tapeB, tp2);
    for (const b of [tapeA, tapeB]) {
      b.position.set(exterior ? 0 : lsh, exterior ? rocket.position.y : ly, 0);
      if (!rocketVisible) b.visible = false;
    }

    // fuses
    setFuseBurn(fuse1, fuse1Burn(t));
    fuse1.group.visible = t < SHOT.s3 + 1.0;
    setFuseBurn(fuse2, fuse2Burn(t));
    fuse2.group.visible = t >= SHOT.s5 && !exterior;

    // ---- Clawd ----
    const pose = clawdPose(t);
    applyPose(clawd, pose);
    clawd.group.visible = !exterior;
    clawd.group.updateMatrixWorld(true);
    wrench.visible = t < SHOT.s2;
    wrench.rotation.set(0, 0, -0.25);

    if (t < SHOT.s5) placeMatch(match1, t, SHOT.s2, EV.match1, EV.match1Drop, 4.95);
    else match1.visible = false;
    placeMatch(match2, t, SHOT.s6, EV.match2, EV.match2Drop, 14.95);
    applyPose(clawd, pose);
    clawd.group.updateMatrixWorld(true);

    // tape roll: bench -> hand -> bench
    const handPos = clawd.arms.n.hand.getWorldPosition(new THREE.Vector3());
    const benchA = new THREE.Vector3(2.85, 0.08, -1.25), benchB = new THREE.Vector3(2.7, 0.08, -1.1);
    const inHand = smooth(12.02, 12.14, t) * (1 - smooth(13.34, 13.44, t));
    const benchPos = t < 13 ? benchA : benchB;
    tapeRoll.position.copy(benchPos).lerp(handPos, inHand);
    tapeRoll.rotation.set(lerp(Math.PI / 2, 0, inHand), 0, lerp(0, 0.3, inHand));
    tapeRoll.visible = !exterior && t >= SHOT.s4;
    // strip from roll to the band end while unrolling
    const unrolling1 = t >= EV.tape1[0] && t < EV.tape1Rip, unrolling2 = t >= EV.tape2[0] && t < EV.tape2Rip;
    strip.visible = unrolling1 || unrolling2;
    if (strip.visible) setStrip(strip, handPos.clone().add(new THREE.Vector3(0, -0.12, 0)), unrolling1 ? end1 : end2);

    // ---- fx ----
    sparks.begin();
    smoke.begin();
    fw.begin();

    // fuse 1 sparks + sputter at the base
    const f1 = fuse1Burn(t);
    if (t >= EV.fuse1On && t < 6.62) {
      emitSparks(sparks, t, EV.fuse1On, EV.fuse1Out, (tb) => fusePoint(fuse1, fuse1Burn(tb)).clone().add(new THREE.Vector3(0, 0.02, 0)), { n: 80, seed: 3, speed: 1.1, size: 0.035 });
      if (t > EV.fuse1Out) {
        const base = new THREE.Vector3(R0.x, 0.08, R0.z + 0.05);
        const k = 1 - smooth(6.45, 6.6, t);
        emitSparks(sparks, t, EV.fuse1Out, 6.58, () => base, { n: 50, seed: 9, speed: 1.4, size: 0.03, up: 0.5, intensity: k });
      }
    }
    const sparkOn = t >= EV.fuse1On && t < 6.58 ? 1 : t >= EV.fuse2On && t < EV.ignite ? 1 : 0;
    const sp = t < 10 ? fusePoint(fuse1, Math.min(f1, 0.999)) : fusePoint(fuse2, Math.min(fuse2Burn(t), 0.999));
    sparkLight.position.copy(sp).add(new THREE.Vector3(0, 0.15, 0));
    sparkLight.intensity = sparkOn * (2.2 + 0.8 * Math.sin(t * 53) * Math.sin(t * 31));
    // fuse 2
    if (t >= EV.fuse2On && t < EV.ignite + 0.1) {
      emitSparks(sparks, t, EV.fuse2On, EV.ignite, (tb) => fusePoint(fuse2, fuse2Burn(tb)).clone().add(new THREE.Vector3(0, 0.02, 0)), { n: 80, seed: 5, speed: 1.2, size: 0.035 });
    }
    // match flares
    for (const m of [match1, match2]) {
      if (m.visible && m.userData.flareK > 0.01) {
        const p = m.userData.head.getWorldPosition(tmpV);
        smokePuffAt(smoke, t, (m === match1 ? EV.match1 : EV.match2), p, { n: 3, seed: m === match1 ? 41 : 43, life: 0.9, size: 0.1, rise: 0.4, opacity: 0.25 });
      }
    }
    // failure puff (pfft) + lingering wisps
    smokePuffAt(smoke, t, EV.pfft, new THREE.Vector3(R0.x + 0.05, 0.12, R0.z + 0.1), { n: 10, seed: 7, life: 2.6, size: 0.42, rise: 0.25, spread: 0.3, opacity: 0.55, drift: [0.12, 0, 0.05] });
    smokePuffAt(smoke, t, EV.toppleHit, new THREE.Vector3(R0.x + 0.8, 0.05, R0.z), { n: 6, seed: 8, life: 1.4, size: 0.3, rise: 0.1, spread: 0.6, opacity: 0.18, tint: 0x9a8a78 });
    smokePuffAt(smoke, t, EV.pushHit, new THREE.Vector3(B1.x + 0.3, 0.05, B1.z), { n: 4, seed: 12, life: 1.0, size: 0.25, rise: 0.08, spread: 0.4, opacity: 0.12, tint: 0x9a8a78 });

    // launch: flames, light, exhaust smoke, sparks
    const ign = smooth(EV.ignite, EV.ignite + 0.06, t);
    const flamePow = !exterior ? ign : 0;
    for (const [fl, base, r] of [[flameR, new THREE.Vector3(R0.x, 0.0, R0.z), 0.16], [flameB, new THREE.Vector3(B1.x, 0.0, B1.z), 0.24]]) {
      fl.visible = flamePow > 0.01 && rocketVisible;
      const len = (0.9 + 0.6 * smooth(15.0, 15.3, t)) * (1 + 0.12 * Math.sin(t * 71) * Math.sin(t * 29));
      fl.position.set(base.x + lsh, ly + 0.02, base.z);
      fl.scale.set(r, len, r);
      fl.material.uniforms.time.value = t;
      fl.material.uniforms.power.value = flamePow;
    }
    flameLight.position.set(R0.x + 0.25, ly - 0.2, R0.z + 0.3);
    flameLight.intensity = !exterior && ly < 25 ? ign * (55 + 15 * Math.sin(t * 43)) * (1 - smooth(15.6, 16.0, t) * 0.5) : 0;
    if (!exterior && t >= EV.ignite) {
      // exhaust plume born along the path
      for (let i = 0; i < 70; i++) {
        const tb = EV.ignite + i * 0.014;
        if (tb > t) break;
        const a = t - tb;
        const by = launchY(tb);
        const life = 2.5;
        if (a > life) continue;
        const k = a / life;
        const th = hash1(i, 91) * 6.283;
        const spread = (by < 0.5 ? 1.1 : 0.4) * (1 - Math.exp(-a * 2.5)) * (0.5 + hash1(i, 92));
        smoke.push(R0.x + 0.25 + Math.cos(th) * spread, Math.max(0.15, by - 0.3) + a * 0.35, R0.z + Math.sin(th) * spread * 0.8,
          (0.45 + hash1(i, 93) * 0.4) * (1 + 1.6 * a), 0.55 * (1 - k) * (1 - k) * smooth(0, 0.05, a), th + a * 0.3, 0x9a9aa4);
      }
      emitSparks(sparks, t, EV.ignite, 16.0, (tb) => new THREE.Vector3(R0.x + 0.25, launchY(tb) - 0.15, R0.z), { n: 140, seed: 13, speed: 2.5, size: 0.05, up: -0.2, g: 2, dirBias: new THREE.Vector3(0, -1.6, 0) });
    }
    // exterior: rocket trail sparks + glow, bursts
    if (exterior) {
      if (t < EV.bursts[0]) {
        emitSparks(sparks, t, SHOT.s7, EV.bursts[0], (tb) => new THREE.Vector3(R0.x + 0.25, exteriorRocketY(tb, CEIL_Y) - 0.2, R0.z), { n: 180, seed: 17, speed: 1.2, size: 0.12, life: 0.6, g: 3, dirBias: new THREE.Vector3(0, -2.5, 0) });
        // flame glow on the rocket
        const ry = rocket.position.y;
        sparks.push(R0.x + 0.25, ry - 0.3, R0.z, 1, 0.7, 0.3, 1.6, 0.9);
      }
      for (const b of bursts) fireworkBurst(fw, t, b);
      // smoke from the broken skylight
      smokePuffAt(smoke, t, SHOT.s7 - 0.1, new THREE.Vector3(SKY.x, CEIL_Y + 0.9, SKY.z), { n: 10, seed: 19, life: 2.2, size: 1.4, rise: 1.0, spread: 1.2, opacity: 0.35, tint: 0x6a6a78 });
    }
    sparks.end();
    smoke.end();
    fw.end();
    const scale = H / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)));
    sparks.mat.uniforms.scale.value = scale;
    fw.mat.uniforms.scale.value = scale;

    // shards + glass
    set.glass.visible = t < EV.crash;
    updateShards(shards, t, EV.crash, CEIL_Y + 0.66, 0.012, CEIL_Y);
    set.mullions.forEach((m) => (m.visible = t < EV.crash));

    // ---- firework lighting ----
    let fr = 0, fg = 0, fb = 0, latest = null;
    for (const b of bursts) {
      const e = burstEnvelope(t, b.t0);
      if (e > 0.001) {
        const c = b.colors[0];
        fr += c.r * e; fg += c.g * e; fb += c.b * e;
        if (!latest || b.t0 > latest.t0) latest = b;
      }
    }
    const fwI = Math.max(fr, fg, fb);
    if (fwI > 0) {
      fwSpot.color.setRGB(fr / fwI, fg / fwI, fb / fwI);
      fwPoint.color.copy(fwSpot.color);
    }
    fwSpot.intensity = fwI * 130;
    fwPoint.intensity = exterior ? fwI * 1400 : 0;
    if (latest) fwPoint.position.copy(latest.c);
    set.skyMat.uniforms.flash.value.setRGB(fr * 0.08, fg * 0.08, fb * 0.08);
    // moonbeam picks up the firework colour
    set.beamMat.uniforms.color.value.setRGB(0.44 + fr * 0.5, 0.56 + fg * 0.5, 0.82 + fb * 0.5);
    set.beamMat.uniforms.strength.value = 0.05 + fwI * 0.06;

    // light balance per space
    moonExt.intensity = exterior ? 0.9 : 0;
    lamp.intensity = exterior ? 0 : 120;
    set.interior.visible = true;
    // the lamp head would swing into the upward tilt; it is off-frame before 15.2 s
    set.lamp.visible = !(t > 15.2 && t < SHOT.s7);
    updateDust(set, t);

    // ---- depth of field target ----
    let focusPoint;
    const cp = new THREE.Vector3(...cam.pos);
    const clawdHead = new THREE.Vector3(pose.x, 0.75, pose.z);
    if (t < SHOT.s2) focusPoint = clawdHead.clone().lerp(R0.clone().setY(0.7), 0.4);
    else if (t < SHOT.s3) focusPoint = t < 5.2 ? clawdHead : fusePoint(fuse1, Math.min(f1, 0.999));
    else if (t < SHOT.s4) focusPoint = new THREE.Vector3(R0.x + 0.4, 0.4, R0.z);
    else if (t < SHOT.s5) focusPoint = clawdHead;
    else if (t < SHOT.s6) focusPoint = new THREE.Vector3(1.6, 0.6, -0.2);
    else if (t < SHOT.s7) focusPoint = t < 15.05 ? clawdHead.clone().lerp(new THREE.Vector3(R0.x, 0.6, 0), 0.4) : new THREE.Vector3(R0.x, Math.min(ly + 0.6, 14), 0);
    else if (t < SHOT.s8) focusPoint = new THREE.Vector3(0, 25, 0);
    else focusPoint = clawdHead;
    bokeh.uniforms.focus.value = cp.distanceTo(focusPoint);
    bokeh.uniforms.aperture.value = exterior ? 0.0 : (t > 15.0 && t < SHOT.s7 ? 0.0008 : 0.0018);

    // ---- motion blur from camera angular velocity (whip pans) ----
    const prev = cameraAt(Math.max(0, t - 1 / FPS));
    const fwd = new THREE.Vector3(...cam.look).sub(cp).normalize();
    const fwdPrev = new THREE.Vector3(...prev.look).sub(new THREE.Vector3(...prev.pos)).normalize();
    // project previous forward into current screen space
    const sNow = cp.clone().add(fwd).project(camera);
    const sPrev = cp.clone().add(fwdPrev).project(camera);
    let dx = (sNow.x - sPrev.x) * 0.5, dy = (sNow.y - sPrev.y) * 0.5;
    const sameShot = shotIndex(t) === shotIndex(Math.max(0, t - 1 / FPS));
    if (!sameShot || !isFinite(dx) || !isFinite(dy)) { dx = 0; dy = 0; }
    // only the motivated whip pans smear (shot 4 -> 5 and the tilt-down out of the sky)
    const whipEnv = Math.max(smooth(10.6, 10.75, t) * (1 - smooth(11.05, 11.2, t)), smooth(17.3, 17.42, t) * (1 - smooth(17.62, 17.8, t)));
    const mag = Math.hypot(dx, dy);
    const maxMag = 0.035;
    const k = mag > 0.003 ? Math.min(1, maxMag / mag) * whipEnv : 0;
    blurPass.uniforms.dir.value.set(dx * k, dy * k);
    blurPass.enabled = k > 0.02;

    // ---- grade ----
    const fadeIn = smooth(EV.fadeIn[0], EV.fadeIn[1], t);
    const fadeOut = 1 - smooth(EV.fadeOut[0], EV.fadeOut[1], t);
    grade.uniforms.fade.value = fadeIn * fadeOut;
    grade.uniforms.seed.value = frame % 97;

    composer.render();
  }

  function shotIndex(t) {
    const s = [SHOT.s2, SHOT.s3, SHOT.s4, SHOT.s5, SHOT.s6, SHOT.s7, SHOT.s8];
    let i = 0;
    while (i < s.length && t >= s[i]) i++;
    return i;
  }

  return { renderAt, renderer, scene, camera };
}
