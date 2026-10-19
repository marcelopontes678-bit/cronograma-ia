import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, HEIGHT, WIDTH } from "../config";
import { Camera } from "../components/Camera";
import { Rain } from "../components/Rain";
import { Dust } from "../components/Dust";
import { WalkingMan } from "../components/WalkingMan";
import { ease, rnd } from "../lib/motion";

// Câmera telefoto (f alto) a 1,65 m do chão, seguindo o homem por trás.
const F = 1500;
const VX = WIDTH / 2;
const VY = 800;
const CAM_H = 1.65;
const SPEED = 1.5; // m/s
const MAN_Z = 6.4; // distância da câmera ao homem
const STREET_HALF = 7.2;
const BAY = 16;

type RGB = [number, number, number];
const FOG: RGB = [30, 45, 58];
const mix = (a: RGB, b: RGB, t: number): RGB => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const rgb = (c: RGB, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;

const proj = (X: number, Y: number, Z: number): [number, number] => [VX + (F * X) / Z, VY + (F * (CAM_H - Y)) / Z];
const poly = (pts: [number, number][]) => pts.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");

export const StreetScene: React.FC<{ duration: number }> = ({ duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const camZ = SPEED * t + 20; // começa um pouco adiante, para os prédios já "estarem lá"

  const els: React.ReactNode[] = [];
  const lampGlows: React.ReactNode[] = [];
  const reflections: React.ReactNode[] = [];

  const firstBay = Math.floor((camZ + 1.5) / BAY);
  // ---- prédios (do fundo para a frente)
  for (let k = firstBay + 13; k >= firstBay - 1; k--) {
    const z0 = k * BAY - camZ;
    const z1 = z0 + BAY - 1.6;
    if (z1 < 1.6) continue;
    const zz0 = Math.max(z0, 1.6);
    for (const side of [-1, 1]) {
      const sd = k * 2 + (side > 0 ? 1 : 0);
      const H = 20 + rnd(`h${sd}`) * 36;
      const dist = Math.max(0, (z0 + z1) / 2);
      const fogT = 1 - Math.exp(-dist / 78);
      const tint = rnd(`t${sd}`);
      const base: RGB = [14 + tint * 10, 19 + tint * 11, 26 + tint * 12];
      const col = mix(base, FOG, fogT);
      const X = side * STREET_HALF;
      els.push(
        <polygon key={`f${sd}`} points={poly([proj(X, 0, zz0), proj(X, H, zz0), proj(X, H, z1), proj(X, 0, z1)])} fill={rgb(col)} />,
      );
      // empena (lado voltado para a rua entre prédios) — dá volume
      if (z0 > 1.6) {
        const nx = side * (STREET_HALF + 4.5 + rnd(`d${sd}`) * 3);
        els.push(
          <polygon
            key={`e${sd}`}
            points={poly([proj(X, 0, z1), proj(X, H, z1), proj(nx, H, z1), proj(nx, 0, z1)])}
            fill={rgb(mix(col, [4, 6, 9], 0.45))}
          />,
        );
      }
      // janelas acesas
      const cols = 4;
      const rows = Math.floor(H / 3.5);
      for (let r = 1; r < rows; r++) {
        for (let cI = 0; cI < cols; cI++) {
          const key = `${sd}w${r}c${cI}`;
          if (rnd(key) > 0.13) continue;
          const warm = rnd(`${key}k`) > 0.35;
          const wz0 = z0 + 0.8 + cI * 3.7;
          const wz1 = wz0 + 2;
          if (wz1 < 1.6) continue;
          const y0 = r * 3.5 + 0.6;
          const y1 = y0 + 1.9;
          const wc: RGB = warm ? [255, 196, 120] : [170, 200, 230];
          const a = (0.28 + rnd(`${key}a`) * 0.5) * (1 - fogT * 0.55);
          els.push(<polygon key={key} points={poly([proj(X, y0, wz0), proj(X, y1, wz0), proj(X, y1, wz1), proj(X, y0, wz1)])} fill={rgb(wc, a)} />);
          // reflexo da janela no asfalto
          if (r < 7 && dist < 120) {
            const [wx, wy] = proj(X * 0.8, 0, (wz0 + wz1) / 2);
            const len = Math.max(30, 1100 / Math.max(6, (wz0 + wz1) / 2) * 2.2);
            reflections.push(
              <rect key={`wr${key}`} x={wx - 5} y={wy} width={10} height={len} fill={rgb(wc, a * 0.45)} />,
            );
          }
        }
      }
    }
  }

  // ---- postes de luz
  for (let j = Math.floor((camZ - 10) / 18); j < Math.floor((camZ + 160) / 18); j++) {
    for (const side of [-1, 1]) {
      const z = (j * 18 + (side > 0 ? 0 : 9)) - camZ;
      if (z < 2.2 || z > 170) continue;
      const X = side * 5.5;
      const [bx, by] = proj(X, 0, z);
      const [tx, ty] = proj(X, 6.8, z);
      const [hx, hy] = proj(X - side * 0.9, 6.8, z);
      const fogT = 1 - Math.exp(-z / 90);
      els.push(
        <g key={`lp${j}${side}`}>
          <line x1={bx} y1={by} x2={tx} y2={ty} stroke={rgb(mix([6, 8, 11], FOG, fogT))} strokeWidth={Math.max(1.5, (F * 0.16) / z)} />
          <line x1={tx} y1={ty} x2={hx} y2={hy} stroke={rgb(mix([6, 8, 11], FOG, fogT))} strokeWidth={Math.max(1.2, (F * 0.1) / z)} />
        </g>,
      );
      const r = Math.min(260, Math.max(9, (F * 2.0) / z));
      const flick = 0.92 + 0.08 * Math.sin(frame / 3 + j * 2 + side);
      lampGlows.push(
        <g key={`lg${j}${side}`} opacity={flick}>
          <circle cx={hx} cy={hy} r={r * 2.4} fill="url(#lampHalo)" />
          <circle cx={hx} cy={hy} r={Math.max(3, r * 0.16)} fill="#fff3d2" />
        </g>,
      );
      // poça de luz + reflexo vertical
      const [gx, gy] = proj(X - side * 0.9, 0, z);
      const pool = Math.min(520, (F * 3.4) / z);
      reflections.push(
        <ellipse key={`pool${j}${side}`} cx={gx} cy={gy + pool * 0.06} rx={pool} ry={pool * 0.16} fill="url(#poolGrad)" />,
        <rect key={`lr${j}${side}`} x={gx - r * 0.12} y={gy} width={r * 0.24} height={Math.min(760, r * 3.4)} fill="url(#streak)" />,
      );
    }
  }

  // ---- faixa tracejada central (movendo-se em direção à câmera)
  const dashes: React.ReactNode[] = [];
  for (let d = Math.floor((camZ + 2) / 9); d < Math.floor((camZ + 140) / 9); d++) {
    const z0 = d * 9 - camZ;
    const z1 = z0 + 3.2;
    if (z1 < 3.4) continue;
    const zz0 = Math.max(3.4, z0);
    const a = 0.30 * (1 - (1 - Math.exp(-z0 / 70)) * 0.8) * Math.min(1, (z0 - 3.4) / 4);
    dashes.push(<polygon key={d} points={poly([proj(-0.14, 0, zz0), proj(0.14, 0, zz0), proj(0.14, 0, z1), proj(-0.14, 0, z1)])} fill={`rgba(190,210,230,${a})`} />);
  }

  // ---- reflexo do homem + ripples no chão
  const phase = (frame / fps) * 0.95;
  const [, manY] = proj(0, 0, MAN_Z);
  const manH = (F * 1.78) / MAN_Z;
  const manX = VX + 4 * Math.sin(frame / 41);

  const ripples = Array.from({ length: 34 }).map((_, i) => {
    const age = ((frame + rnd(`rp${i}`) * 40) % 40) / 40;
    const z = 4 + rnd(`rz${i}`) * 26;
    const x = (rnd(`rx${i}`) - 0.5) * 12;
    const [px, py] = proj(x, 0, z);
    const rr = (10 + age * 54) * (14 / z) * 2.6;
    return <ellipse key={i} cx={px} cy={py} rx={rr} ry={rr * 0.17} fill="none" stroke={`rgba(190,215,235,${0.34 * (1 - age)})`} strokeWidth={1.6} />;
  });

  return (
    <AbsoluteFill style={{ background: "#05070a" }}>
      <Camera from={{ scale: 1.0, x: 0, y: 0 }} to={{ scale: 1.1, x: 0, y: -22 }} duration={duration + 14} origin={[VX, 1000]} shake={0.9} seed={3}>
        <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
          <defs>
            <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#04060a" />
              <stop offset="1" stopColor="#1a2733" />
            </linearGradient>
            <linearGradient id="ground" gradientUnits="userSpaceOnUse" x1="0" y1={VY} x2="0" y2={HEIGHT}>
              <stop offset="0" stopColor="#22323f" />
              <stop offset="0.25" stopColor="#101922" />
              <stop offset="1" stopColor="#05070a" />
            </linearGradient>
            <radialGradient id="lampHalo">
              <stop offset="0" stopColor="#ffd9a0" stopOpacity="0.85" />
              <stop offset="0.18" stopColor="#ffc47a" stopOpacity="0.34" />
              <stop offset="1" stopColor="#ffb860" stopOpacity="0" />
            </radialGradient>
            <linearGradient id="streak" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#ffd9a0" stopOpacity="0.5" />
              <stop offset="1" stopColor="#ffd9a0" stopOpacity="0" />
            </linearGradient>
            <radialGradient id="poolGrad">
              <stop offset="0" stopColor="#ffc47a" stopOpacity="0.22" />
              <stop offset="0.6" stopColor="#ffc47a" stopOpacity="0.07" />
              <stop offset="1" stopColor="#ffc47a" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="vp" cx="0.5" cy="0.5" r="0.5">
              <stop offset="0" stopColor="#ffe3b8" stopOpacity="0.55" />
              <stop offset="0.35" stopColor="#d9b678" stopOpacity="0.2" />
              <stop offset="1" stopColor="#7c9ab5" stopOpacity="0" />
            </radialGradient>
            <filter id="ripple" x="-5%" y="-5%" width="110%" height="110%">
              <feTurbulence type="fractalNoise" baseFrequency={`0.010 ${0.075 + 0.006 * Math.sin(frame / 22)}`} numOctaves={2} seed={4} result="n" />
              <feDisplacementMap in="SourceGraphic" in2="n" scale={34} xChannelSelector="R" yChannelSelector="G" />
              <feGaussianBlur stdDeviation="3.2" />
            </filter>
            <clipPath id="groundClip">
              <rect x="0" y={VY + 4} width={WIDTH} height={HEIGHT - VY} />
            </clipPath>
          </defs>

          <rect width={WIDTH} height={HEIGHT} fill="url(#sky)" />
          {/* brilho no ponto de fuga */}
          <circle cx={VX} cy={VY - 10} r={780} fill="url(#vp)" />

          {/* chão molhado */}
          <polygon points={poly([[0, VY], [WIDTH, VY], [WIDTH, HEIGHT], [0, HEIGHT]])} fill="url(#ground)" />
          {/* calçadas */}
          {[-1, 1].map((s) => (
            <polygon
              key={s}
              points={poly([proj(s * 4.6, 0, 1.6), proj(s * STREET_HALF, 0, 1.6), proj(s * STREET_HALF, 0, 240), proj(s * 4.6, 0, 240)])}
              fill="rgba(8,12,17,0.55)"
            />
          ))}
          {dashes}

          {/* prédios e postes */}
          {els}

          {/* reflexos, poças de luz, ripples e reflexo do homem */}
          <g clipPath="url(#groundClip)">
            <g filter="url(#ripple)" style={{ mixBlendMode: "screen" }}>
              {reflections}
              <g opacity={0.3}>
                <WalkingMan x={manX} y={manY + 6} height={manH * 0.92} phase={phase} mirror fill="#0a0e13" rimOpacity={0.35} />
              </g>
            </g>
            {ripples}
          </g>

          {/* luzes dos postes (aditivas) */}
          <g style={{ mixBlendMode: "screen" }}>{lampGlows}</g>

          {/* bokeh distante */}
          <g filter="blur(7px)" style={{ mixBlendMode: "screen" }}>
            {Array.from({ length: 16 }).map((_, i) => {
              const x = 250 + rnd(`bx${i}`) * 580 + 8 * Math.sin(frame / 60 + i);
              const y = VY - 40 + rnd(`by${i}`) * 120;
              const rr = 8 + rnd(`br${i}`) * 22;
              const kind = rnd(`bk${i}`);
              const col = kind > 0.78 ? "255,90,70" : kind > 0.4 ? "255,206,140" : "190,214,240";
              return <circle key={i} cx={x} cy={y} r={rr} fill={`rgba(${col},${0.25 + rnd(`bo${i}`) * 0.4})`} />;
            })}
          </g>

          {/* homem caminhando */}
          <WalkingMan x={manX} y={manY} height={manH} phase={phase} />
        </svg>

        {/* neblina baixa e chuva */}
        <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(40,58,74,0) 36%, rgba(40,58,74,0.30) 46%, rgba(40,58,74,0) 66%)", mixBlendMode: "screen" }} />
        <Rain count={190} seed="rb" opacity={0.9} />
        <Dust count={24} region={[0, 500, WIDTH, 1500]} color="190,214,240" opacity={0.3} size={[8, 20]} blur={6} seed="sbk" />
        <Rain count={16} seed="rn" near opacity={0.9} wind={0.12} />
      </Camera>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0) 26%, rgba(0,0,0,0) 70%, rgba(0,0,0,0.7) 100%)" }} />
      <AbsoluteFill style={{ background: C.black, opacity: ease(frame, [0, 4], [0, 0]) }} />
    </AbsoluteFill>
  );
};
