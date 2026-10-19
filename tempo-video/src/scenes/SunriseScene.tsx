import { AbsoluteFill, useCurrentFrame } from "remotion";
import { C, HEIGHT, WIDTH } from "../config";
import { Camera } from "../components/Camera";
import { Dust } from "../components/Dust";
import { WalkingMan } from "../components/WalkingMan";
import { ease } from "../lib/motion";

const HORIZON = 930;

const hex = (h: string): [number, number, number] => [
  parseInt(h.slice(1, 3), 16),
  parseInt(h.slice(3, 5), 16),
  parseInt(h.slice(5, 7), 16),
];
const mixHex = (a: string, b: string, t: number) => {
  const [r1, g1, b1] = hex(a);
  const [r2, g2, b2] = hex(b);
  return `rgb(${Math.round(r1 + (r2 - r1) * t)},${Math.round(g1 + (g2 - g1) * t)},${Math.round(b1 + (b2 - b1) * t)})`;
};

/** Crista de montanhas: soma de senos determinística. */
const ridge = (seed: number, base: number, amp: number, step = 18) => {
  let d = `M0,${HEIGHT} L0,${base}`;
  for (let x = 0; x <= WIDTH + step; x += step) {
    const y =
      base -
      amp * (0.55 * Math.sin(x * 0.0046 + seed) + 0.3 * Math.sin(x * 0.0121 + seed * 2.3) + 0.15 * Math.sin(x * 0.031 + seed * 4.1) + 0.5);
    d += ` L${x},${y.toFixed(1)}`;
  }
  return `${d} L${WIDTH},${HEIGHT} Z`;
};

export const SunriseScene: React.FC<{ duration: number }> = ({ duration }) => {
  const frame = useCurrentFrame();
  // luz: começa quase escuro e "revela" o cenário até o fim da cena
  const L = ease(frame, [4, 128], [0, 1]);
  const sunY = HORIZON + 120 - 190 * ease(frame, [0, 140], [0, 1]);
  const grow = ease(frame, [0, duration], [0, 1]);
  const layer = (k: number) => `translate(540 ${HORIZON}) scale(${1 + k * grow}) translate(-540 ${-HORIZON})`;
  const sway = (i: number) => 5 * Math.sin(frame / 34 + i);

  const grass = Array.from({ length: 46 }).map((_, i) => {
    const x = i * 25 - 20;
    const h = 90 + ((i * 53) % 70);
    const lean = sway(i * 0.6) * (h / 120);
    return `M${x},${HEIGHT} Q${x + lean * 0.4},${HEIGHT - h * 0.6} ${x + 8 + lean},${HEIGHT - h} Q${x + 10 + lean * 0.4},${HEIGHT - h * 0.5} ${x + 18},${HEIGHT} Z`;
  });

  return (
    <AbsoluteFill style={{ background: "#04070a" }}>
      <Camera from={{ scale: 1.0, x: 0, y: 0 }} to={{ scale: 1.1, x: 0, y: -10 }} duration={duration} origin={[540, 1100]} shake={0.55} seed={11}>
        <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
          <defs>
            <linearGradient id="skyS" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor={mixHex("#04070a", "#17303d", L)} />
              <stop offset="0.35" stopColor={mixHex("#070d13", "#3a6074", L)} />
              <stop offset="0.5" stopColor={mixHex("#0d1822", "#e2ac6c", L)} />
              <stop offset="0.56" stopColor={mixHex("#0d1822", "#f7d79a", L)} />
              <stop offset="1" stopColor="#05080b" />
            </linearGradient>
            <radialGradient id="sunGlow">
              <stop offset="0" stopColor="#fffaf0" stopOpacity="1" />
              <stop offset="0.1" stopColor="#fff0cc" stopOpacity="0.95" />
              <stop offset="0.3" stopColor="#ffd08c" stopOpacity="0.45" />
              <stop offset="1" stopColor="#ffa850" stopOpacity="0" />
            </radialGradient>
            <linearGradient id="flare" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="#ffd9a0" stopOpacity="0" />
              <stop offset="0.5" stopColor="#fff2d6" stopOpacity="0.9" />
              <stop offset="1" stopColor="#ffd9a0" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="shadow" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#000" stopOpacity="0.7" />
              <stop offset="1" stopColor="#000" stopOpacity="0" />
            </linearGradient>
            <filter id="fog"><feGaussianBlur stdDeviation="34" /></filter>
          </defs>

          <rect width={WIDTH} height={HEIGHT} fill="url(#skyS)" />

          {/* sol subindo */}
          <g style={{ mixBlendMode: "screen" }} opacity={0.15 + 0.85 * L}>
            <circle cx={540} cy={sunY} r={880} fill="url(#sunGlow)" opacity={0.55 + 0.45 * L} />
            <circle cx={540} cy={sunY} r={74} fill="#fff8e8" />
            <rect x={-80} y={sunY - 3} width={WIDTH + 160} height={6} fill="url(#flare)" opacity={0.2 + 0.5 * L} />
            {Array.from({ length: 11 }).map((_, i) => {
              const a = -75 + i * 15 + 1.5 * Math.sin(frame / 50 + i);
              const tan = Math.tan((a * Math.PI) / 180);
              return <polygon key={i} points={`540,${sunY} ${540 + tan * 1500 - 60},${sunY - 1500} ${540 + tan * 1500 + 60},${sunY - 1500}`} fill={`rgba(255,226,170,${0.06 * L})`} />;
            })}
          </g>

          {/* cordilheiras com perspectiva atmosférica: o cenário é revelado pela luz */}
          <g transform={layer(0.02)}>
            <path d={ridge(1.2, HORIZON - 40, 120)} fill={mixHex("#080d13", "#a38b72", L * 0.9)} />
          </g>
          <ellipse cx={540} cy={HORIZON + 6} rx={820} ry={70} fill={`rgba(255,226,176,${0.38 * L})`} filter="url(#fog)" />
          <g transform={layer(0.05)}>
            <path d={ridge(3.7, HORIZON + 10, 150)} fill={mixHex("#070b10", "#6d6258", L * 0.85)} />
          </g>
          <ellipse cx={540} cy={HORIZON + 80} rx={900} ry={60} fill={`rgba(255,214,160,${0.25 * L})`} filter="url(#fog)" />
          <g transform={layer(0.09)}>
            <path d={ridge(5.9, HORIZON + 90, 130)} fill={mixHex("#05080c", "#3b3a3d", L * 0.8)} />
          </g>
          <g transform={layer(0.14)}>
            <path d={ridge(8.4, HORIZON + 190, 100)} fill={mixHex("#04070a", "#1b1c1f", L * 0.7)} />
          </g>

          {/* colina em primeiro plano + sombra longa do homem em direção à câmera */}
          <g transform={layer(0.2)}>
            <path
              d={`M-40,${HEIGHT} L-40,1380 C220,1296 400,1262 540,1262 C700,1262 860,1300 1120,1380 L1120,${HEIGHT} Z`}
              fill={mixHex("#030507", "#3a2d1e", L * 0.85)}
            />
            <polygon points="520,1308 560,1308 760,1920 330,1920" fill="url(#shadow)" opacity={0.85 * L} />
            <path d={`M-40,${HEIGHT} L-40,1380 C220,1296 400,1262 540,1262`} fill="none" stroke={`rgba(255,214,150,${0.55 * L})`} strokeWidth={2.6} />
            <g transform={`translate(0 ${0.8 * Math.sin(frame / 40)})`}>
              <WalkingMan x={540} y={1312} height={430} phase={0} coat fill="#020304" rim="#ffe2a8" rimOpacity={0.12 + 0.38 * L} />
            </g>
          </g>

          {/* capim em silhueta, balançando ao vento */}
          <g transform={layer(0.34)}>
            {grass.map((d, i) => (
              <path key={i} d={d} fill="#020304" />
            ))}
          </g>
        </svg>
        <Dust count={44} region={[0, 500, WIDTH, 1500]} color="255,226,170" opacity={0.9 * L} size={[1.2, 3.6]} seed="sun" speed={0.5} />
        <Dust count={10} region={[0, 600, WIDTH, 1400]} color="255,214,150" opacity={0.3 * L} size={[12, 30]} blur={10} seed="sunb" speed={0.35} />
      </Camera>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 26%, rgba(0,0,0,0) 74%, rgba(0,0,0,0.55) 100%)" }} />
      {/* leve brilho quente nos realces */}
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 60% 40% at 50% ${(sunY / HEIGHT) * 100}%, rgba(255,214,150,${0.16 * L}) 0%, rgba(255,214,150,0) 70%)`, mixBlendMode: "screen" }} />
      <AbsoluteFill style={{ background: C.black, opacity: ease(frame, [0, 2], [0, 0]) }} />
    </AbsoluteFill>
  );
};
