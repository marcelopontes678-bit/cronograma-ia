import { AbsoluteFill, Sequence, interpolate, useCurrentFrame } from "remotion";
import { C, HEIGHT, WIDTH } from "../config";
import { SERIF } from "../fonts";
import { Camera } from "../components/Camera";
import { Dust } from "../components/Dust";
import { WalkingMan } from "../components/WalkingMan";
import { ease, flicker, rnd } from "../lib/motion";

/** Planos da montagem, em frames (cada corte é mais curto que o anterior): 54, 42, 36, 30, 27, 21 = 210 */
export const SHOTS = [
  { id: "write-wide", len: 54 },
  { id: "write-close", len: 42 },
  { id: "shoes-low", len: 36 },
  { id: "shoes-close", len: 30 },
  { id: "walk-wide", len: 27 },
  { id: "walk-close", len: 21 },
] as const;

// =============================================================== PLANO A — mãos escrevendo metas
const LINES = [
  { text: "Metas", size: 92, x: 238, y: 770, w: 360, box: false },
  { text: "Acordar às 5h", size: 58, x: 238, y: 900, w: 520, box: true },
  { text: "Treinar todos os dias", size: 58, x: 238, y: 1010, w: 640, box: true },
  { text: "Estudar uma hora", size: 58, x: 238, y: 1120, w: 560, box: true },
  { text: "Concluir o projeto", size: 58, x: 238, y: 1230, w: 580, box: true },
];

/** progresso global 0–1 → linha atual e fração da linha */
const lineProgress = (p: number) => {
  const weights = [0.14, 0.2, 0.24, 0.2, 0.22];
  let acc = 0;
  return weights.map((w) => {
    const f = Math.min(1, Math.max(0, (p - acc) / w));
    acc += w;
    return f;
  });
};

const Hand: React.FC = () => {
  const rim = "rgba(255,207,138,0.55)";
  const finger = (d: string, w: number) => (
    <g>
      <path d={d} stroke={rim} strokeWidth={w + 5} strokeLinecap="round" fill="none" />
      <path d={d} stroke="url(#skinG)" strokeWidth={w} strokeLinecap="round" fill="none" />
    </g>
  );
  return (
    <g>
      <defs>
        <linearGradient id="skinG" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#4a3022" />
          <stop offset="0.6" stopColor="#1a110c" />
          <stop offset="1" stopColor="#0a0605" />
        </linearGradient>
      </defs>
      {/* antebraço e dorso da mão */}
      <polygon points="330,-160 470,-290 1250,-110 1250,330 560,150" fill="url(#skinG)" stroke={rim} strokeWidth={2} />
      <ellipse cx={310} cy={-165} rx={135} ry={92} transform="rotate(-34 310 -165)" fill="url(#skinG)" stroke={rim} strokeWidth={2} />
      {finger("M60,-62 C110,-130 165,-195 215,-238", 42)}
      {finger("M70,-30 C140,-62 200,-96 250,-78", 40)}
      {finger("M82,-80 C126,-102 160,-128 196,-150", 46)}
      {/* caneta */}
      <line x1={0} y1={0} x2={190} y2={-278} stroke="#07080c" strokeWidth={17} strokeLinecap="round" />
      <line x1={112} y1={-164} x2={150} y2={-220} stroke="#d6ad60" strokeWidth={6} strokeLinecap="round" />
      <path d="M-4,4 L14,-14 L4,-26 Z" fill="#cfc4b0" />
    </g>
  );
};

const WritingArt: React.FC<{ progress: number; frame: number }> = ({ progress, frame }) => {
  const fr = lineProgress(progress);
  // linha atual = última com progresso entre 0 e 1 (ou a última completa)
  let cur = 0;
  fr.forEach((f, i) => {
    if (f > 0) cur = i;
  });
  const ln = LINES[cur];
  const tipX = ln.x + (ln.box ? 74 : 0) + ln.w * fr[cur] + 2 * Math.sin(frame * 1.7);
  const tipY = ln.y + 8 + 3 * Math.sin(frame * 2.3) - 12 * Math.sin(Math.min(1, fr[cur]) * Math.PI * 4) * 0.2;
  const lamp = flicker(frame, 0.8, 0.05);
  return (
    <g>
      <defs>
        <linearGradient id="pgr" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f3e5bf" />
          <stop offset="1" stopColor="#8f8168" />
        </linearGradient>
        <radialGradient id="lampLight" cx="0.22" cy="0.18" r="0.9">
          <stop offset="0" stopColor="#ffd9a0" stopOpacity="0.65" />
          <stop offset="0.6" stopColor="#ffb860" stopOpacity="0.1" />
          <stop offset="1" stopColor="#000" stopOpacity="0.7" />
        </radialGradient>
        {LINES.map((l, i) => (
          <clipPath id={`cl${i}`} key={i}>
            <rect x={l.x + (l.box ? 70 : 0)} y={l.y - l.size} width={l.w * fr[i] + 10} height={l.size * 1.5} />
          </clipPath>
        ))}
      </defs>
      {/* tampo da mesa */}
      <rect width={WIDTH} height={HEIGHT} fill="#0d0907" />
      {/* folha levemente girada */}
      <g transform="rotate(-4 540 1000)">
        <rect x={150} y={600} width={820} height={1000} rx={6} fill="rgba(0,0,0,0.55)" transform="translate(16 22)" />
        <rect x={150} y={600} width={820} height={1000} rx={6} fill="url(#pgr)" />
        {Array.from({ length: 11 }).map((_, i) => (
          <line key={i} x1={150} y1={690 + i * 86} x2={970} y2={690 + i * 86} stroke="#6b7d93" strokeOpacity={0.28} strokeWidth={2} />
        ))}
        <line x1={206} y1={600} x2={206} y2={1600} stroke="#b24b4b" strokeOpacity={0.35} strokeWidth={2} />
        {LINES.map((l, i) => (
          <g key={i}>
            {l.box && <rect x={l.x} y={l.y - 40} width={44} height={44} rx={6} fill="none" stroke="#1b2036" strokeOpacity={fr[i] > 0 ? 0.8 : 0} strokeWidth={4} />}
            {l.box && fr[i] >= 1 && <polyline points={`${l.x + 8},${l.y - 18} ${l.x + 19},${l.y - 6} ${l.x + 38},${l.y - 34}`} fill="none" stroke="#9a2f2f" strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" opacity={0.8} />}
            <g clipPath={`url(#cl${i})`}>
              <text x={l.x + (l.box ? 70 : 0)} y={l.y} fontFamily={SERIF} fontStyle="italic" fontWeight={500} fontSize={l.size} fill="#1b2036">
                {l.text}
              </text>
              {i === 0 && <line x1={l.x} y1={l.y + 22} x2={l.x + 300} y2={l.y + 18} stroke="#1b2036" strokeWidth={4} strokeLinecap="round" />}
            </g>
          </g>
        ))}
      </g>
      {/* iluminação da lâmpada */}
      <rect width={WIDTH} height={HEIGHT} fill="url(#lampLight)" style={{ mixBlendMode: "multiply" }} opacity={lamp} />
      <rect width={WIDTH} height={HEIGHT} fill="url(#lampLight)" style={{ mixBlendMode: "screen" }} opacity={0.35 * lamp} />
      {/* mão e caneta seguem a ponta da escrita (rotacionadas junto com a folha) */}
      <g transform={`rotate(-4 540 1000) translate(${tipX} ${tipY})`}>
        <g transform="translate(14 22)" opacity={0.5}>
          <Hand />
        </g>
        <Hand />
      </g>
    </g>
  );
};

const WriteShot: React.FC<{ len: number; close: boolean }> = ({ len, close }) => {
  const frame = useCurrentFrame();
  const p = close ? ease(frame, [0, len], [0.62, 0.98]) : ease(frame, [0, len], [0.06, 0.64]);
  // ponta da caneta (mesmos cálculos de WritingArt) para centralizar a câmera
  const fr = lineProgress(p);
  let cur = 0;
  fr.forEach((f, i) => f > 0 && (cur = i));
  const ln = LINES[cur];
  const tx = ln.x + (ln.box ? 74 : 0) + ln.w * fr[cur];
  const ty = ln.y + 8;
  // coordenadas após rotação da folha (-4° em torno de 540,1000)
  const a = (-4 * Math.PI) / 180;
  const trackX = 540 + (tx - 540) * Math.cos(a) - (ty - 1000) * Math.sin(a);
  const trackY = 1000 + (tx - 540) * Math.sin(a) + (ty - 1000) * Math.cos(a);
  // plano aberto: câmera fixa na folha (mostra a lista inteira); plano fechado: acompanha a ponta da caneta
  const rx = close ? trackX : 560;
  const ry = close ? trackY : 1000;
  const s = close ? ease(frame, [0, len], [2.5, 2.9]) : ease(frame, [0, len], [1.0, 1.1]);
  const cx = close ? WIDTH / 2 + 120 : WIDTH / 2;
  const cy = close ? 980 : 1000;
  const x = cx - s * rx;
  const y = cy - s * ry;
  return (
    <AbsoluteFill style={{ background: "#0d0907" }}>
      <AbsoluteFill style={{ transform: `translate(${x}px, ${y}px) scale(${s})`, transformOrigin: "0 0" }}>
        <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
          <WritingArt progress={p} frame={frame} />
        </svg>
      </AbsoluteFill>
      {close && (
        <AbsoluteFill
          style={{
            backdropFilter: "blur(7px)",
            WebkitBackdropFilter: "blur(7px)",
            WebkitMaskImage: "radial-gradient(circle at 56% 51%, transparent 0, transparent 26%, #000 62%)",
            maskImage: "radial-gradient(circle at 56% 51%, transparent 0, transparent 26%, #000 62%)",
          }}
        />
      )}
      <Dust count={30} region={[0, 300, WIDTH, 1300]} opacity={0.5} size={[1, 3]} seed={close ? "wc" : "ww"} litAt={(px) => Math.max(0, 1 - px / 900)} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 28%, rgba(0,0,0,0) 62%, rgba(0,0,0,0.7) 100%)" }} />
    </AbsoluteFill>
  );
};

// =============================================================== PLANO B — tênis tocando o chão ao amanhecer
/** Pé por cinemática inversa de 2 segmentos. Retorna joelho e tornozelo. */
const solveLeg = (hip: [number, number], foot: [number, number], l1: number, l2: number, dir = 1) => {
  const dx = foot[0] - hip[0];
  const dy = foot[1] - hip[1];
  const d = Math.min(l1 + l2 - 1, Math.max(Math.abs(l1 - l2) + 1, Math.hypot(dx, dy)));
  const a = Math.atan2(dy, dx);
  const cosA = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d);
  const ang = a + dir * Math.acos(Math.max(-1, Math.min(1, cosA)));
  return { knee: [hip[0] + l1 * Math.cos(ang), hip[1] + l1 * Math.sin(ang)] as [number, number] };
};

const GROUND = 1280;
const RUN_PERIOD = 26; // frames por passada completa de uma perna

const ShoesArt: React.FC<{ frame: number; slow: number }> = ({ frame, slow }) => {
  const f = frame * slow;
  const hipBase: [number, number] = [470, 560 + 6 * Math.sin((f / RUN_PERIOD) * Math.PI * 4)];
  const legs = [0, 0.5].map((off) => {
    const ph = ((f / RUN_PERIOD + off) % 1 + 1) % 1; // 0–1
    // apoio (0–0.45): pé desliza para trás no chão; balanço (0.45–1): pé sobe e vai à frente
    let fx: number, fy: number, tilt: number;
    if (ph < 0.45) {
      const u = ph / 0.45;
      fx = hipBase[0] + 130 - 300 * u;
      fy = GROUND - 12;
      tilt = 12 - 34 * u;
    } else {
      const u = (ph - 0.45) / 0.55;
      fx = hipBase[0] - 170 + 300 * u;
      fy = GROUND - 12 - Math.sin(u * Math.PI) * 250;
      tilt = -22 + 34 * u - 14 * Math.sin(u * Math.PI);
    }
    const hip: [number, number] = [hipBase[0] + (off ? -10 : 10), hipBase[1]];
    const ankle: [number, number] = [fx, fy - 40];
    const { knee } = solveLeg(hip, ankle, 400, 420, 1);
    return { hip, knee, ankle, tilt, off, ph, fx };
  });
  // perna de trás primeiro
  legs.sort((a, b) => b.ph - a.ph);
  const strike = (off: number) => {
    const ph = ((f / RUN_PERIOD + off) % 1 + 1) % 1;
    return ph; // 0 = momento do toque
  };
  const puffs = [0, 0.5].flatMap((off) => {
    const ph = strike(off);
    const age = ph < 0.35 ? ph / 0.35 : 1;
    if (age >= 1) return [];
    return Array.from({ length: 9 }).map((_, i) => {
      const dir = rnd(`pf${off}${i}`) * 2 - 1.1;
      return (
        <circle
          key={`${off}${i}`}
          cx={470 + 130 - 300 * (ph / 0.45) - 40 + dir * 160 * age}
          cy={GROUND - 20 - 120 * age * (0.4 + rnd(`pv${i}`))}
          r={16 + 46 * age * (0.5 + rnd(`pr${i}`))}
          fill={`rgba(210,190,160,${0.3 * (1 - age)})`}
        />
      );
    });
  });
  const rimC = "rgba(255,190,110,0.8)";
  return (
    <g>
      <defs>
        <linearGradient id="skyB" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0a1219" />
          <stop offset="0.45" stopColor="#1d2f3a" />
          <stop offset="0.62" stopColor="#c88a52" />
          <stop offset="0.67" stopColor="#f0b972" />
          <stop offset="0.7" stopColor="#3a2a22" />
          <stop offset="1" stopColor="#070809" />
        </linearGradient>
        <linearGradient id="asphalt" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#4b4036" />
          <stop offset="0.12" stopColor="#1b1c1f" />
          <stop offset="1" stopColor="#060708" />
        </linearGradient>
        <radialGradient id="sunB">
          <stop offset="0" stopColor="#fff1cf" stopOpacity="1" />
          <stop offset="0.25" stopColor="#ffc880" stopOpacity="0.6" />
          <stop offset="1" stopColor="#ff9a4a" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="shoeG" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#2c3038" />
          <stop offset="1" stopColor="#07080b" />
        </linearGradient>
      </defs>
      <rect width={WIDTH} height={HEIGHT} fill="url(#skyB)" />
      <circle cx={820} cy={1240} r={560} fill="url(#sunB)" style={{ mixBlendMode: "screen" }} />
      {/* silhuetas distantes */}
      <path d={`M0,1262 C140,1210 260,1250 420,1226 C600,1200 760,1250 1080,1222 L1080,1290 L0,1290 Z`} fill="#0b0f13" opacity={0.9} />
      {/* asfalto com faixa passando */}
      <rect y={1270} width={WIDTH} height={HEIGHT - 1270} fill="url(#asphalt)" />
      {Array.from({ length: 5 }).map((_, i) => {
        const x = ((i * 380 - f * 26) % 1900 + 1900) % 1900 - 300;
        return <rect key={i} x={x} y={1305} width={220} height={9} fill="rgba(235,225,205,0.22)" />;
      })}
      <rect y={1264} width={WIDTH} height={12} fill="rgba(255,200,130,0.35)" opacity={0.6} />
      {puffs}
      {/* pernas */}
      {legs.map((L) => {
        const limb = (a: [number, number], b: [number, number], r1: number, r2: number, bulge = 0) => {
          const dx = b[0] - a[0];
          const dy = b[1] - a[1];
          const L = Math.hypot(dx, dy) || 1;
          const nx = -dy / L;
          const ny = dx / L;
          const mx = (a[0] + b[0]) / 2 + nx * bulge;
          const my = (a[1] + b[1]) / 2 + ny * bulge;
          const d = `M ${a[0] + nx * r1},${a[1] + ny * r1} Q ${mx + nx * (r1 + r2) / 2},${my + ny * (r1 + r2) / 2} ${b[0] + nx * r2},${b[1] + ny * r2}
                     L ${b[0] - nx * r2},${b[1] - ny * r2} Q ${mx - nx * (r1 + r2) / 2},${my - ny * (r1 + r2) / 2} ${a[0] - nx * r1},${a[1] - ny * r1} Z`;
          return (
            <>
              <path d={d} fill="#07090c" stroke={rimC} strokeWidth={3} strokeLinejoin="round" />
              <circle cx={a[0]} cy={a[1]} r={r1} fill="#07090c" />
              <circle cx={b[0]} cy={b[1]} r={r2} fill="#07090c" />
            </>
          );
        };
        return (
          <g key={L.off}>
            {limb(L.hip, L.knee, 62, 44, 14)}
            {limb(L.knee, L.ankle, 44, 27, -18)}
            {/* tênis */}
            <g transform={`translate(${L.ankle[0]} ${L.ankle[1] + 8}) rotate(${L.tilt})`}>
              <path d="M-60,-30 C-30,-60 20,-56 46,-34 C90,-28 132,-4 136,30 L136,52 L-62,52 Z" fill="url(#shoeG)" stroke={rimC} strokeWidth={3} />
              <path d="M-62,52 L136,52 L136,66 C60,72 -20,72 -64,66 Z" fill="#0d0e11" stroke="rgba(255,214,150,0.55)" strokeWidth={2.4} />
              <path d="M-20,-30 C8,-4 50,-2 96,12" fill="none" stroke="rgba(214,173,96,0.7)" strokeWidth={5} strokeLinecap="round" />
            </g>
          </g>
        );
      })}
    </g>
  );
};

const ShoesShot: React.FC<{ len: number; close: boolean }> = ({ len, close }) => {
  const frame = useCurrentFrame();
  const s = close ? ease(frame, [0, len], [1.9, 2.15]) : ease(frame, [0, len], [1.0, 1.08]);
  return (
    <AbsoluteFill style={{ background: "#070809" }}>
      <Camera from={{ scale: s, x: close ? -130 : 0, y: close ? -330 : 0 }} to={{ scale: s, x: close ? -170 : 0, y: close ? -330 : -14 }} duration={len} origin={[540, 1280]} shake={1.4} seed={close ? 4 : 2}>
        <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
          <ShoesArt frame={frame + (close ? 9 : 0)} slow={close ? 0.7 : 1} />
        </svg>
        <Dust count={28} region={[0, 900, WIDTH, 1500]} opacity={0.5} size={[1.4, 4]} color="255,214,160" seed={close ? "sc" : "sw"} speed={2} />
      </Camera>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 70%, rgba(0,0,0,0.6) 100%)" }} />
      {close && <AbsoluteFill style={{ backdropFilter: "blur(5px)", WebkitBackdropFilter: "blur(5px)", WebkitMaskImage: "linear-gradient(180deg,#000 0%,transparent 30%,transparent 72%,#000 100%)", maskImage: "linear-gradient(180deg,#000 0%,transparent 30%,transparent 72%,#000 100%)" }} />}
    </AbsoluteFill>
  );
};

// =============================================================== PLANO C — silhueta caminhando em direção à luz
const PathArt: React.FC<{ frame: number }> = ({ frame }) => {
  const t = frame / 30;
  const phase = t * 0.95;
  const VY = 880;
  const rays = Array.from({ length: 9 }).map((_, i) => {
    const a = -52 + i * 13 + 2 * Math.sin(frame / 40 + i);
    return <polygon key={i} points={`540,${VY} ${540 + Math.tan((a - 5) * Math.PI / 180) * 1400},${VY - 1400} ${540 + Math.tan((a + 5) * Math.PI / 180) * 1400},${VY - 1400}`} fill="rgba(255,236,196,0.07)" />;
  });
  return (
    <g>
      <defs>
        <linearGradient id="skyC" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0a1218" />
          <stop offset="0.5" stopColor="#274250" />
          <stop offset="0.7" stopColor="#d6b27c" />
          <stop offset="1" stopColor="#0c0f12" />
        </linearGradient>
        <radialGradient id="sunC">
          <stop offset="0" stopColor="#ffffff" stopOpacity="1" />
          <stop offset="0.12" stopColor="#fff0cf" stopOpacity="0.85" />
          <stop offset="0.4" stopColor="#ffd08c" stopOpacity="0.3" />
          <stop offset="1" stopColor="#ffb860" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="pathG" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#f3d9a8" />
          <stop offset="0.2" stopColor="#6a6258" />
          <stop offset="1" stopColor="#0a0b0c" />
        </linearGradient>
      </defs>
      <rect width={WIDTH} height={HEIGHT} fill="url(#skyC)" />
      <g style={{ mixBlendMode: "screen" }}>{rays}</g>
      <circle cx={540} cy={VY - 10} r={900} fill="url(#sunC)" style={{ mixBlendMode: "screen" }} />
      {/* colinas e árvores */}
      <path d={`M0,${VY} L0,${VY - 140} C120,${VY - 190} 200,${VY - 100} 330,${VY - 60} L330,${VY} Z`} fill="#0d171c" />
      <path d={`M1080,${VY} L1080,${VY - 170} C960,${VY - 150} 860,${VY - 90} 750,${VY - 56} L750,${VY} Z`} fill="#0d171c" />
      {/* caminho em perspectiva */}
      <polygon points={`525,${VY} 555,${VY} 1500,${HEIGHT} -420,${HEIGHT}`} fill="url(#pathG)" />
      <polygon points={`0,${VY} 525,${VY} -420,${HEIGHT} 0,${HEIGHT}`} fill="#070b0d" />
      <polygon points={`1080,${VY} 555,${VY} 1500,${HEIGHT} 1080,${HEIGHT}`} fill="#070b0d" />
      {/* névoa */}
      <ellipse cx={540} cy={VY + 40} rx={760} ry={90} fill="rgba(255,230,190,0.28)" filter="blur(40px)" />
      {/* homem */}
      <WalkingMan x={540 + 3 * Math.sin(frame / 31)} y={1230} height={440} phase={phase} coat={false} fill="#050709" rim="#ffe2a8" rimOpacity={0.75} />
    </g>
  );
};

const WalkShot: React.FC<{ len: number; close: boolean }> = ({ len, close }) => (
  <AbsoluteFill style={{ background: "#0c0f12" }}>
    <Camera
      from={{ scale: close ? 2.0 : 1.0, x: 0, y: close ? 120 : 0 }}
      to={{ scale: close ? 2.25 : 1.12, x: 0, y: close ? 90 : -20 }}
      duration={len}
      origin={[540, close ? 840 : 1000]}
      shake={1.1}
      seed={close ? 6 : 5}
    >
      <PathFrame close={close} />
    </Camera>
    <Dust count={26} region={[0, 400, WIDTH, 1300]} color="255,236,200" opacity={0.6} size={[1.4, 4.2]} seed={close ? "pc" : "pw"} speed={0.7} />
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 72%, rgba(0,0,0,0.55) 100%)" }} />
  </AbsoluteFill>
);

const PathFrame: React.FC<{ close: boolean }> = ({ close }) => {
  const frame = useCurrentFrame();
  return (
    <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
      <PathArt frame={frame + (close ? 14 : 0)} />
    </svg>
  );
};

// =============================================================== cena completa
export const MontageScene: React.FC = () => {
  let at = 0;
  return (
    <AbsoluteFill style={{ background: C.black }}>
      {SHOTS.map((shot) => {
        const from = at;
        at += shot.len;
        return (
          <Sequence key={shot.id} from={from} durationInFrames={shot.len + (shot.id === "walk-close" ? 14 : 0)}>
            <ShotFlash len={shot.len}>
              {shot.id === "write-wide" && <WriteShot len={shot.len} close={false} />}
              {shot.id === "write-close" && <WriteShot len={shot.len} close />}
              {shot.id === "shoes-low" && <ShoesShot len={shot.len} close={false} />}
              {shot.id === "shoes-close" && <ShoesShot len={shot.len} close />}
              {shot.id === "walk-wide" && <WalkShot len={shot.len} close={false} />}
              {shot.id === "walk-close" && <WalkShot len={shot.len} close />}
            </ShotFlash>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

/** Entrada do plano: escurece nos 3 primeiros frames + pequeno pulso de luz (corte elegante). */
const ShotFlash: React.FC<{ len: number; children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      {children}
      <AbsoluteFill style={{ background: "#000", opacity: ease(frame, [0, 3], [0.85, 0]) }} />
      <AbsoluteFill style={{ background: "rgba(255,214,150,1)", mixBlendMode: "screen", opacity: interpolate(frame, [2, 4, 8], [0, 0.12, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }} />
    </AbsoluteFill>
  );
};
