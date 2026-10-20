import { AbsoluteFill, Audio, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FPS, HEIGHT, WIDTH } from "../config";
import { Camera } from "../components/Camera";
import { Dust } from "../components/Dust";
import { Grain } from "../components/Grain";
import { Rain } from "../components/Rain";
import { WalkingMan } from "../components/WalkingMan";
import { ease, rnd } from "../lib/motion";
import { JP } from "../fonts";

export const TOKYO_OPUS_DURATION = 300; // 10 s
const TOKYO_DURATION = TOKYO_OPUS_DURATION;

// ---- câmera: telefoto baixa (1,3 m), seguindo o homem por trás
const F = 1450;
const VX = WIDTH / 2;
const CAM_H = 1.3;
const SPEED = 1.2; // m/s
const MAN_Z = 6.2;
const HALF = 5.2; // meia-largura da viela
const FACE = 6.2; // posição X das fachadas
const BAY = 12;

const NEON = ["#ff2d95", "#19e6ff", "#ffb02e", "#8b5cff", "#ff3b3b", "#39ff9a", "#ff2d95", "#19e6ff"];

type RGB = [number, number, number];
const FOG: RGB = [40, 22, 58];
const mix = (a: RGB, b: RGB, t: number): RGB => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const rgb = (c: RGB, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
const poly = (p: [number, number][]) => p.map((q) => `${q[0].toFixed(1)},${q[1].toFixed(1)}`).join(" ");

type Neon = { kind: "blade" | "strip" | "shop"; side: number; z0: number; z1: number; y0: number; y1: number; color: string; bars: number[]; idx: number };

/** Letreiros de uma "baia" (trecho de fachada), sempre os mesmos para o mesmo índice. */
const neonsFor = (k: number, side: number): Neon[] => {
  const out: Neon[] = [];
  const sd = k * 2 + (side > 0 ? 1 : 0);
  const base = k * BAY;
  const nBlades = 1 + Math.floor(rnd(`nb${sd}`) * 3);
  for (let i = 0; i < nBlades; i++) {
    const z0 = base + 1 + (i + 0.15 + rnd(`bz${sd}${i}`) * 0.6) * ((BAY - 2.5) / nBlades);
    const h = 2.6 + rnd(`bh${sd}${i}`) * 4.2;
    const y0 = 2.8 + rnd(`by${sd}${i}`) * 9;
    out.push({
      kind: "blade", side, z0, z1: z0, y0, y1: y0 + h, idx: sd * 10 + i,
      color: NEON[Math.floor(rnd(`bc${sd}${i}`) * NEON.length)],
      bars: Array.from({ length: 4 + Math.floor(rnd(`bb${sd}${i}`) * 3) }).map((_, j) => 0.35 + rnd(`bl${sd}${i}${j}`) * 0.6),
    });
  }
  // luz de loja no térreo + tubo horizontal
  const shopC = NEON[Math.floor(rnd(`sc${sd}`) * NEON.length)];
  out.push({ kind: "shop", side, z0: base + 0.8, z1: base + BAY - 0.8, y0: 0.3, y1: 3.0, color: shopC, bars: [], idx: sd * 10 + 7 });
  out.push({ kind: "strip", side, z0: base + 0.8, z1: base + BAY - 0.8, y0: 3.3, y1: 3.3, color: shopC, bars: [], idx: sd * 10 + 8 });
  return out;
};

/** Letreiros verticais em japonês (Noto Sans JP 900, só os glifos usados). */
const WORDS = ["ラーメン", "居酒屋", "カラオケ", "ホテル", "焼鳥", "薬局", "喫茶", "24時間", "寿司", "バー", "酒場", "営業", "新宿", "東京"];

export const TokyoNightOpus: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  // TILT de abertura: a câmera começa olhando a poça (horizonte acima do quadro) e sobe até o homem
  const VY = interpolate(t, [0, 0.6, 4.2], [-420, -420, 840], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2) });
  const proj = (X: number, Y: number, Z: number): [number, number] => [VX + (F * X) / Z, VY + (F * (CAM_H - Y)) / Z];
  // steadicam: avanço + deriva lateral lenta
  const camZ = SPEED * t + 30;
  const camX = 0.35 * Math.sin(t * 0.55);
  const P = (X: number, Y: number, Z: number) => proj(X - camX, Y, Z);

  const buildings: React.ReactNode[] = [];
  const neonLit: React.ReactNode[] = [];
  const reflect: React.ReactNode[] = [];
  const glow: React.ReactNode[] = [];
  const spill: React.ReactNode[] = [];
  const flares: React.ReactNode[] = [];
  const lanterns: React.ReactNode[] = [];

  const firstBay = Math.floor((camZ + 1.5) / BAY);
  for (let k = firstBay + 13; k >= firstBay - 1; k--) {
    const z0 = k * BAY - camZ;
    const z1 = z0 + BAY - 0.8;
    if (z1 < 1.6) continue;
    const zz0 = Math.max(z0, 1.6);
    for (const side of [-1, 1]) {
      const sd = k * 2 + (side > 0 ? 1 : 0);
      const H = 24 + rnd(`h${sd}`) * 40;
      const dist = Math.max(0, (z0 + z1) / 2);
      const fogT = 1 - Math.exp(-dist / 70);
      const tint = rnd(`t${sd}`);
      const col = mix([13 + tint * 10, 12 + tint * 8, 24 + tint * 14], FOG, fogT);
      const X = side * FACE;
      buildings.push(<polygon key={`f${sd}`} points={poly([P(X, 0, zz0), P(X, H, zz0), P(X, H, z1), P(X, 0, z1)])} fill={rgb(col)} />);
      if (z0 > 1.6) {
        const nx = side * (FACE + 3.5 + rnd(`d${sd}`) * 3);
        buildings.push(<polygon key={`e${sd}`} points={poly([P(X, 0, z1), P(X, H, z1), P(nx, H, z1), P(nx, 0, z1)])} fill={rgb(mix(col, [4, 3, 9], 0.5))} />);
      }
      // janelas acesas (poucas)
      for (let r = 3; r < Math.floor(H / 3.4); r++) {
        for (let c = 0; c < 3; c++) {
          const key = `${sd}w${r}c${c}`;
          if (rnd(key) > 0.1) continue;
          const wz0 = z0 + 1 + c * 3.5;
          if (wz0 + 1.8 < 1.6) continue;
          const y0 = r * 3.4 + 0.6;
          const wc: RGB = rnd(`${key}k`) > 0.5 ? [255, 214, 160] : [175, 210, 255];
          buildings.push(<polygon key={key} points={poly([P(X, y0, wz0), P(X, y0 + 1.8, wz0), P(X, y0 + 1.8, wz0 + 1.8), P(X, y0, wz0 + 1.8)])} fill={rgb(wc, 0.4 * (1 - fogT * 0.6))} />);
        }
      }

      // ---- letreiros
      for (const n of neonsFor(k, side)) {
        const nz0 = n.z0 - camZ;
        const nz1 = n.z1 - camZ;
        if (nz1 < 1.8 || nz0 > 190) continue;
        const near = 1 - Math.min(1, Math.max(0, nz0) / 190);
        const flick = 0.82 + 0.18 * Math.sin(frame / (4 + (n.idx % 5)) + n.idx);
        const on = (n.idx % 11 === 3 ? (Math.sin(frame / 6 + n.idx) > -0.3 ? 1 : 0.25) : 1) * flick;
        if (n.kind === "blade") {
          const xo = side * FACE;
          const xi = side * (FACE - 1.0);
          const quad = (yy0: number, yy1: number): [number, number][] => [P(xo, yy0, nz0), P(xi, yy0, nz0), P(xi, yy1, nz0), P(xo, yy1, nz0)];
          buildings.push(<polygon key={`bp${n.idx}${k}`} points={poly(quad(n.y0, n.y1))} fill="#0a0912" />);
          const rows = n.bars.length;
          const bh = (n.y1 - n.y0) / rows;
          const word = WORDS[n.idx % WORDS.length];
          const useText = nz0 < 75;
          if (useText) {
            const chars = Array.from(word);
            const ch = (n.y1 - n.y0) / chars.length;
            const [tx] = P((xo + xi) / 2, 0, nz0);
            const fs = (F * Math.min(ch * 0.82, 0.8)) / nz0;
            chars.forEach((c, j) => {
              const [, ty] = P(0, n.y1 - (j + 0.5) * ch, nz0);
              neonLit.push(
                <text key={`tx${n.idx}${k}${j}`} x={tx} y={ty} textAnchor="middle" dominantBaseline="central" fontFamily={JP} fontWeight={900} fontSize={fs} fill={n.color} opacity={on}>
                  {c}
                </text>,
              );
            });
          }
          n.bars.forEach((len, j) => {
            const yy = n.y0 + (j + 0.5) * bh;
            const a: [number, number] = P(xo - side * 0.08, yy, nz0);
            const b: [number, number] = P(xo - side * (0.08 + 0.78 * len), yy, nz0);
            if (!useText) neonLit.push(<line key={`bl${n.idx}${k}${j}`} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={n.color} strokeWidth={Math.max(1.6, (F * bh * 0.45) / nz0)} strokeLinecap="round" opacity={on} />);
            const ra = P(xo - side * 0.08, -yy, nz0);
            const rb = P(xo - side * (0.08 + 0.78 * len), -yy, nz0);
            reflect.push(<line key={`br${n.idx}${k}${j}`} x1={ra[0]} y1={ra[1]} x2={rb[0]} y2={rb[1]} stroke={n.color} strokeWidth={Math.max(2, (F * bh * 0.6) / nz0)} strokeLinecap="round" opacity={on * 0.7 * (0.5 + near)} />);
          });
          neonLit.push(<polygon key={`bo${n.idx}${k}`} points={poly(quad(n.y0, n.y1))} fill="none" stroke={n.color} strokeWidth={Math.max(1.4, 60 / nz0)} opacity={on * 0.9} />);
          const [cx, cy] = P((xo + xi) / 2, (n.y0 + n.y1) / 2, nz0);
          glow.push(<circle key={`bg${n.idx}${k}`} cx={cx} cy={cy} r={Math.min(340, (F * 2.8) / nz0)} fill={`url(#gl${NEON.indexOf(n.color)})`} opacity={0.85 * on * (0.35 + near)} />);
          if (nz0 < 40 && nz0 > 4 && n.idx % 3 === 0) {
            flares.push(<rect key={`fl${n.idx}${k}`} x={cx - 420} y={cy - 2} width={840} height={4} fill={n.color} opacity={0.22 * on} />);
          }
        } else if (n.kind === "strip") {
          const a = P(side * FACE, n.y0, Math.max(1.8, nz0));
          const b = P(side * FACE, n.y0, nz1);
          neonLit.push(<line key={`st${n.idx}${k}`} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={n.color} strokeWidth={Math.max(2, 120 / Math.max(2, nz0))} strokeLinecap="round" opacity={on} />);
          const ra = P(side * FACE, -n.y0, Math.max(1.8, nz0));
          const rb = P(side * FACE, -n.y0, nz1);
          reflect.push(<line key={`sr${n.idx}${k}`} x1={ra[0]} y1={ra[1]} x2={rb[0]} y2={rb[1]} stroke={n.color} strokeWidth={Math.max(3, 200 / Math.max(2, nz0))} opacity={0.5 * on} />);
        } else {
          const zz = Math.max(1.8, nz0);
          buildings.push(<polygon key={`sh${n.idx}${k}`} points={poly([P(side * FACE, n.y0, zz), P(side * FACE, n.y1, zz), P(side * FACE, n.y1, nz1), P(side * FACE, n.y0, nz1)])} fill={n.color} opacity={0.2 * on} />);
          // mancha de luz no chão ("neon no chão")
          const gx = side * (FACE - 4.6);
          spill.push(<polygon key={`sp${n.idx}${k}`} points={poly([P(side * FACE, 0, zz), P(gx, 0, zz), P(gx, 0, nz1), P(side * FACE, 0, nz1)])} fill={n.color} opacity={0.5 * on} />);
          // lanternas (chōchin) em algumas lojas
          if (n.idx % 2 === 1 && nz0 > 2.5) {
            for (let j = 0; j < 4; j++) {
              const lz = nz0 + 1.2 + j * 2.3;
              const [lx, ly] = P(side * (FACE - 0.7), 2.5, lz);
              lanterns.push(<circle key={`ln${n.idx}${k}${j}`} cx={lx} cy={ly} r={Math.max(3, (F * 0.28) / lz)} fill="#ff3b30" opacity={0.95 * on} />);
              lanterns.push(<circle key={`lg${n.idx}${k}${j}`} cx={lx} cy={ly} r={Math.max(10, (F * 1.0) / lz)} fill="#ff3b30" opacity={0.16} />);
            }
          }
        }
      }
    }
  }

  // ---- faixa de pedestres (listras brancas que correm em direção à câmera)
  const zebra: React.ReactNode[] = [];
  for (let c = Math.floor((camZ + 2) / 30); c < Math.floor((camZ + 150) / 30); c++) {
    for (let i = -5; i <= 5; i++) {
      const zA = c * 30 - camZ;
      const zB = zA + 3.6;
      if (zB < 2) continue;
      const zz = Math.max(2, zA);
      const x0 = i * 0.95 - 0.34;
      const x1 = i * 0.95 + 0.34;
      const a = 0.45 * Math.exp(-zA / 90) * Math.min(1, (zA - 2) / 4 + 0.2);
      zebra.push(<polygon key={`z${c}${i}`} points={poly([P(x0, 0, zz), P(x1, 0, zz), P(x1, 0, zB), P(x0, 0, zB)])} fill={`rgba(225,230,255,${a})`} />);
    }
  }

  // ---- fios elétricos atravessando a rua
  const wires: React.ReactNode[] = [];
  for (let w = Math.floor((camZ + 3) / 17); w < Math.floor((camZ + 120) / 17); w++) {
    const z = w * 17 - camZ;
    if (z < 3) continue;
    for (let j = 0; j < 2; j++) {
      const hgt = 7.6 + j * 1.1 + rnd(`w${w}${j}`) * 0.8;
      const pts: [number, number][] = [];
      for (let s = 0; s <= 10; s++) {
        const u = s / 10;
        pts.push(P(-FACE + u * 2 * FACE, hgt - 0.9 * Math.sin(Math.PI * u), z + j * 0.5));
      }
      wires.push(<polyline key={`w${w}${j}`} points={poly(pts)} fill="none" stroke="#05040a" strokeWidth={Math.max(1, 60 / z)} opacity={0.9} />);
    }
  }

  // ---- vapor de bueiro
  const steam: React.ReactNode[] = [];
  for (const [vx, vzWorld] of [[-2.4, 52], [2.0, 74], [-1.6, 96]] as [number, number][]) {
    const vz = vzWorld - camZ;
    if (vz < 2.5 || vz > 90) continue;
    for (let i = 0; i < 9; i++) {
      const age = ((frame + i * 7 + vzWorld) % 63) / 63;
      const [sx, sy] = P(vx + 0.5 * Math.sin(age * 3 + i), 0.2 + age * 3.2, vz);
      const rr = (F * (0.35 + age * 1.1)) / vz;
      steam.push(<circle key={`st${vzWorld}${i}`} cx={sx} cy={sy} r={rr} fill="#e9d8ff" opacity={0.13 * Math.sin(Math.PI * age)} />);
    }
    const [gx, gy] = P(vx, 0, vz);
    steam.push(<ellipse key={`vent${vzWorld}`} cx={gx} cy={gy} rx={(F * 0.45) / vz} ry={(F * 0.07) / vz} fill="#07060c" />);
  }

  // ---- o homem
  const phase = t * 0.95;
  const [, manY] = proj(0, 0, MAN_Z);
  const manH = (F * 1.78) / MAN_Z;
  const manX = VX + 5 * Math.sin(frame / 37);

  const ripples = Array.from({ length: 26 }).map((_, i) => {
    const age = ((frame + rnd(`rp${i}`) * 36) % 36) / 36;
    const z = 3.5 + rnd(`rz${i}`) * 22;
    const x = (rnd(`rx${i}`) - 0.5) * 9;
    const [px, py] = P(x, 0, z);
    const rr = (10 + age * 50) * (13 / z) * 2.4;
    return <ellipse key={i} cx={px} cy={py} rx={rr} ry={rr * 0.16} fill="none" stroke={`rgba(200,225,255,${0.34 * (1 - age)})`} strokeWidth={1.6} />;
  });

  // zoom lento + leve rotação, como um dolly de cinema
  return (
    <AbsoluteFill style={{ background: "#05030a" }}>
      <AbsoluteFill style={{ filter: "url(#ca)" }}>
        <Camera from={{ scale: 1.0, x: 0, y: 14 }} to={{ scale: 1.13, x: 0, y: -26, rot: -0.5 }} duration={TOKYO_DURATION} origin={[VX, 1000]} shake={1.0} seed={21}>
          <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
            <defs>
              <linearGradient id="skyT" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor="#04020a" />
                <stop offset="1" stopColor="#241238" />
              </linearGradient>
              <linearGradient id="groundT" gradientUnits="userSpaceOnUse" x1="0" y1={VY} x2="0" y2={HEIGHT}>
                <stop offset="0" stopColor="#3a2150" />
                <stop offset="0.22" stopColor="#140c22" />
                <stop offset="1" stopColor="#04030a" />
              </linearGradient>
              <radialGradient id="vpT">
                <stop offset="0" stopColor="#ffd2f0" stopOpacity="0.6" />
                <stop offset="0.3" stopColor="#c43cff" stopOpacity="0.22" />
                <stop offset="1" stopColor="#19e6ff" stopOpacity="0" />
              </radialGradient>
              {NEON.map((c, i) => (
                <radialGradient key={i} id={`gl${i}`}>
                  <stop offset="0" stopColor={c} stopOpacity="0.55" />
                  <stop offset="0.45" stopColor={c} stopOpacity="0.14" />
                  <stop offset="1" stopColor={c} stopOpacity="0" />
                </radialGradient>
              ))}
              <linearGradient id="fadeRef" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor="#fff" stopOpacity="1" />
                <stop offset="1" stopColor="#fff" stopOpacity="0.15" />
              </linearGradient>
              <mask id="refMask">
                <rect x="0" y={VY} width={WIDTH} height={HEIGHT - VY} fill="url(#fadeRef)" />
              </mask>
              <filter id="neonGlow" x="-10%" y="-10%" width="120%" height="120%">
                <feGaussianBlur stdDeviation="7" result="b" />
                <feGaussianBlur stdDeviation="22" result="b2" />
                <feMerge>
                  <feMergeNode in="b2" />
                  <feMergeNode in="b" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
              <filter id="rippleT" x="-5%" y="-5%" width="110%" height="110%">
                <feTurbulence type="fractalNoise" baseFrequency={`0.012 ${0.07 + 0.006 * Math.sin(frame / 20)}`} numOctaves={2} seed={8} result="n" />
                <feDisplacementMap in="SourceGraphic" in2="n" scale={38} xChannelSelector="R" yChannelSelector="G" />
                <feGaussianBlur stdDeviation="4" />
              </filter>
              <clipPath id="gClip"><rect x="0" y={VY + 2} width={WIDTH} height={HEIGHT - VY} /></clipPath>
            </defs>

            <rect width={WIDTH} height={HEIGHT} fill="url(#skyT)" />
            <circle cx={VX} cy={VY - 10} r={820} fill="url(#vpT)" opacity={1} />
            <circle cx={VX} cy={VY - 10} r={380} fill="url(#vpT)" opacity={0.7} />
            <polygon points={poly([[0, VY], [WIDTH, VY], [WIDTH, HEIGHT], [0, HEIGHT]])} fill="url(#groundT)" />
            <g filter="blur(26px)" opacity={0.5} style={{ mixBlendMode: "screen" }}>{spill}</g>
            {zebra}
            {buildings}
            {wires}

            {/* reflexos dos letreiros no asfalto molhado */}
            <g clipPath="url(#gClip)">
              <g mask="url(#refMask)">
                <g filter="url(#rippleT)" style={{ mixBlendMode: "screen" }}>
                  {reflect}
                  <g opacity={0.35}>
                    <WalkingMan x={manX} y={manY + 6} height={manH * 0.92} phase={phase} mirror umbrella fill="#0b0a14" rimOpacity={0.4} rim="#19e6ff" />
                  </g>
                </g>
              </g>
              {ripples}
            </g>

            {/* neon aceso (com brilho) */}
            <g filter="url(#neonGlow)" style={{ mixBlendMode: "screen" }}>{neonLit}</g>
            <g style={{ mixBlendMode: "screen" }}>{glow}</g>
            <g style={{ mixBlendMode: "screen" }}>{lanterns}</g>
            <g filter="blur(2.5px)" style={{ mixBlendMode: "screen" }}>{flares}</g>

            {/* bokeh de luzes distantes */}
            <g filter="blur(8px)" style={{ mixBlendMode: "screen" }}>
              {Array.from({ length: 22 }).map((_, i) => {
                const x = 200 + rnd(`bx${i}`) * 680 + 10 * Math.sin(frame / 55 + i);
                const y = VY - 60 + rnd(`by${i}`) * 140;
                const rr = 9 + rnd(`br${i}`) * 26;
                return <circle key={i} cx={x} cy={y} r={rr} fill={NEON[i % NEON.length]} opacity={0.2 + rnd(`bo${i}`) * 0.4} />;
              })}
            </g>

            <g filter="blur(14px)">{steam}</g>

            {/* homem de guarda-chuva, contra-luz ciano/magenta */}
            <g style={{ filter: "drop-shadow(-3px 0 1px rgba(255,45,149,0.7)) drop-shadow(3px 0 1px rgba(25,230,255,0.7))" }}>
              <WalkingMan x={manX} y={manY} height={manH} phase={phase} umbrella fill="#06050c" rim="#9ff3ff" rimOpacity={0.28} />
            </g>
          </svg>

          <AbsoluteFill style={{ background: `linear-gradient(180deg, rgba(60,20,90,0) ${((VY - 170) / HEIGHT) * 100}%, rgba(120,40,160,0.22) ${((VY + 10) / HEIGHT) * 100}%, rgba(60,20,90,0) ${((VY + 360) / HEIGHT) * 100}%)`, mixBlendMode: "screen" }} />
          <Rain count={150} seed="tr" opacity={0.7} wind={0.1} />
          <Dust count={22} region={[0, 500, WIDTH, 1500]} color="255,160,230" opacity={0.28} size={[8, 18]} blur={6} seed="tb" />
          <Rain count={14} seed="tn" near opacity={0.8} wind={0.1} />
          {/* bokeh em primeiro plano, fora de foco */}
          <AbsoluteFill style={{ filter: "blur(16px)", mixBlendMode: "screen", pointerEvents: "none" }}>
            <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
              {Array.from({ length: 7 }).map((_, i) => (
                <circle key={i} cx={(i % 2 ? 60 : WIDTH - 60) + 40 * Math.sin(frame / 70 + i)} cy={500 + i * 160 + 30 * Math.cos(frame / 60 + i)} r={70 + rnd(`fb${i}`) * 80} fill={NEON[(i * 3) % NEON.length]} opacity={0.12} />
              ))}
            </svg>
          </AbsoluteFill>
        </Camera>
      </AbsoluteFill>

      {/* filtro de aberração cromática (nas bordas da lente) */}
      <svg width={0} height={0} style={{ position: "absolute" }}>
        <defs>
          <filter id="ca" x="0" y="0" width="100%" height="100%" colorInterpolationFilters="sRGB">
            <feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="r" />
            <feOffset in="r" dx="-2.2" dy="0" result="ro" />
            <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="g" />
            <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="b" />
            <feOffset in="b" dx="2.2" dy="0" result="bo" />
            <feBlend in="ro" in2="g" mode="screen" result="rg" />
            <feBlend in="rg" in2="bo" mode="screen" />
          </filter>
        </defs>
      </svg>

      {/* gradação: sombras azul-petróleo, realces magenta; vinheta e grão */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(10,50,80,0.28) 0%, rgba(0,0,0,0) 50%, rgba(90,10,70,0.22) 100%)", mixBlendMode: "soft-light" }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 80% 64% at 50% 46%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.7) 100%)" }} />
      <Grain opacity={0.13} />
      <AbsoluteFill style={{ background: "#000", opacity: Math.max(ease(frame, [0, 14], [1, 0]), ease(frame, [TOKYO_DURATION - 18, TOKYO_DURATION - 1], [0, 1])) }} />

      <Audio src={staticFile("tokyo/ambience.mp3")} volume={(f) => interpolate(f, [0, 12, TOKYO_DURATION - 24, TOKYO_DURATION - 1], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
    </AbsoluteFill>
  );
};

void FPS;
