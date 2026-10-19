import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, HEIGHT, WIDTH } from "../config";
import { Camera } from "../components/Camera";
import { Dust } from "../components/Dust";
import { ease, flicker, rnd } from "../lib/motion";

// ---------------------------------------------------------------- linha do tempo (segundos locais)
const T = {
  slowWrite: [0, 1.7], // escreve devagar
  lookUp: [1.75, 2.5], // interrompe e olha o relógio
  hold: [2.5, 4.05], // encara o relógio
  down: [4.05, 4.6], // respira e volta ao caderno
  resolve: [4.6, 7.6], // escreve com determinação
};

const PIVOT = { x: 822, y: 1118 }; // base do pescoço
const DESK_Y = 1352;

/** Perfil (voltado para a esquerda). Origem no centro da cabeça. */
const FACE: [number, number][] = [
  [-30, -98], [-50, -74], [-56, -46], [-60, -26], [-79, -2], [-62, 8], [-58, 18], [-64, 27], [-58, 36],
  [-60, 56], [-44, 78], [-16, 84], [18, 80], [44, 70], [70, 44], [84, 6], [86, -34], [70, -76], [40, -98], [6, -106],
];
const FRONT_EDGE = FACE.slice(0, 13);
const pts = (a: [number, number][]) => a.map((p) => p.join(",")).join(" ");

const Clock: React.FC<{ sec: number }> = ({ sec }) => {
  const hand = (len: number, deg: number, w: number, col: string) => (
    <line x1={0} y1={0} x2={len * Math.sin((deg * Math.PI) / 180)} y2={-len * Math.cos((deg * Math.PI) / 180)} stroke={col} strokeWidth={w} strokeLinecap="round" />
  );
  return (
    <g transform="translate(372 1262)">
      {/* pés e sombra */}
      <ellipse cx={0} cy={118} rx={74} ry={13} fill="rgba(0,0,0,0.55)" />
      <path d="M-46,112 L-30,84 L30,84 L46,112 Z" fill="#150f0a" />
      <circle r={80} fill="url(#brassC)" />
      <circle r={68} fill="url(#faceC)" />
      {Array.from({ length: 12 }).map((_, i) => (
        <line key={i} x1={0} y1={-58} x2={0} y2={-64} stroke="#6b5230" strokeWidth={i % 3 === 0 ? 3.4 : 1.8} transform={`rotate(${i * 30})`} />
      ))}
      {hand(36, 305, 5, "#2a2218")}
      {hand(54, 52, 3.6, "#2a2218")}
      {hand(58, sec, 1.6, "#a3262a")}
      <circle r={4.5} fill="#2a2218" />
      <path d="M-50,-44 C-26,-64 18,-66 40,-52" fill="none" stroke="rgba(255,255,255,0.45)" strokeWidth={3} strokeLinecap="round" />
    </g>
  );
};

export const DeskScene: React.FC<{ duration: number }> = ({ duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // cabeça: baixa (escrevendo) → sobe (relógio) → baixa
  const headLook = ease(t, [T.lookUp[0], T.lookUp[1]], [0, 1]) - ease(t, [T.down[0], T.down[1]], [0, 1]);
  const headAngle = -19 + 15 * headLook + 1.1 * Math.sin(t * 1.3);
  const breath = Math.sin(t * 1.6) * 2.2 + spring({ frame: frame - Math.round(T.down[0] * fps), fps, config: { damping: 12, stiffness: 80 } }) * 5 * (t > T.down[0] ? 1 : 0) * Math.exp(-(t - T.down[0]) * 1.2);

  // mão escrevendo
  const writing = t < T.slowWrite[1] ? 0.45 : t >= T.down[1] ? 1 : 0;
  const wFreq = t < T.slowWrite[1] ? 5 : 11;
  const wx = writing * (7 * Math.sin(t * wFreq) + 4 * Math.sin(t * wFreq * 0.37));
  const wy = writing * 1.8 * Math.sin(t * wFreq * 1.7);

  // progresso da tinta no caderno
  const ink = Math.min(1, (t < T.slowWrite[1] ? t * 0.1 : 0.17) + Math.max(0, t - T.down[1]) * 0.22);

  const lamp = flicker(frame, 0.4, 0.05);
  const secDeg = (Math.floor(t) % 60) * 6 + 6 * spring({ frame: frame - Math.floor(t) * fps, fps, config: { damping: 6, stiffness: 420, mass: 0.22 } });

  // cone de luz do abajur: eixo do ponto (330,930) até (560,1340)
  const inCone = (x: number, y: number) => {
    const u = (y - 930) / 420;
    if (u < 0 || u > 1.05) return 0;
    const cx = 330 + u * 230;
    const half = 60 + u * 250;
    return Math.max(0, 1 - Math.abs(x - cx) / half) * (1 - u * 0.4);
  };

  const shelf = Array.from({ length: 36 }).map((_, i) => {
    const row = Math.floor(i / 12);
    const col = i % 12;
    const h = 90 + rnd(`bh${i}`) * 70;
    const hue = rnd(`bc${i}`);
    const color = hue > 0.7 ? "#2b2118" : hue > 0.4 ? "#1d2229" : "#22181a";
    return <rect key={i} x={640 + col * 38 + (row % 2) * 6} y={470 + row * 190 + (160 - h)} width={30} height={h} fill={color} />;
  });

  return (
    <AbsoluteFill style={{ background: "#05070a" }}>
      <Camera from={{ scale: 1.0, x: 0, y: 0 }} to={{ scale: 1.2, x: -36, y: -18 }} duration={duration + 14} origin={[700, 1150]} shake={0.7} seed={9}>
        <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
          <defs>
            <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#0a0e13" />
              <stop offset="0.7" stopColor="#0b1016" />
              <stop offset="1" stopColor="#040507" />
            </linearGradient>
            <linearGradient id="deskTop" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#2a1a10" />
              <stop offset="1" stopColor="#0e0906" />
            </linearGradient>
            <radialGradient id="pool" cx="0.42" cy="0.45" r="0.6">
              <stop offset="0" stopColor="#ffcf8a" stopOpacity="0.55" />
              <stop offset="0.5" stopColor="#ffb860" stopOpacity="0.2" />
              <stop offset="1" stopColor="#ffb860" stopOpacity="0" />
            </radialGradient>
            <linearGradient id="cone" x1="0" y1="0" x2="0.6" y2="1">
              <stop offset="0" stopColor="#ffe0a8" stopOpacity="0.55" />
              <stop offset="1" stopColor="#ffc277" stopOpacity="0.05" />
            </linearGradient>
            <linearGradient id="paper" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="#f0e2bd" />
              <stop offset="1" stopColor="#a8987a" />
            </linearGradient>
            <linearGradient id="skinRim" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="#ffd9a0" stopOpacity="0.9" />
              <stop offset="1" stopColor="#ffd9a0" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="shirt" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="#202731" />
              <stop offset="0.5" stopColor="#0d1218" />
              <stop offset="1" stopColor="#06080b" />
            </linearGradient>
            <linearGradient id="brassC" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#f2d595" />
              <stop offset="0.5" stopColor="#7a5a22" />
              <stop offset="1" stopColor="#2a1d0a" />
            </linearGradient>
            <radialGradient id="faceC" cx="0.3" cy="0.3" r="0.9">
              <stop offset="0" stopColor="#f3e8cb" />
              <stop offset="1" stopColor="#a69a7e" />
            </radialGradient>
            <radialGradient id="bulb">
              <stop offset="0" stopColor="#fff6dc" stopOpacity="1" />
              <stop offset="0.25" stopColor="#ffd9a0" stopOpacity="0.55" />
              <stop offset="1" stopColor="#ffb860" stopOpacity="0" />
            </radialGradient>
            <clipPath id="win"><rect x={36} y={330} width={340} height={600} /></clipPath>
            <filter id="b8"><feGaussianBlur stdDeviation="8" /></filter>
            <filter id="b3"><feGaussianBlur stdDeviation="3" /></filter>
            <filter id="b22"><feGaussianBlur stdDeviation="22" /></filter>
          </defs>

          <rect width={WIDTH} height={HEIGHT} fill="url(#wall)" />

          {/* janela com cidade desfocada e luz azulada */}
          <g>
            <rect x={36} y={330} width={340} height={600} fill="#0a1119" />
            <g filter="url(#b8)">
              {Array.from({ length: 16 }).map((_, i) => (
                <circle key={i} cx={70 + rnd(`wx${i}`) * 280} cy={560 + rnd(`wy${i}`) * 340} r={8 + rnd(`wr${i}`) * 20} fill={rnd(`wk${i}`) > 0.5 ? "rgba(255,200,130,0.5)" : "rgba(160,200,235,0.45)"} />
              ))}
            </g>
            <g clipPath="url(#win)">
              {Array.from({ length: 26 }).map((_, i) => {
                const y = 330 + ((rnd(`ry${i}`) * 700 + frame * (9 + rnd(`rs${i}`) * 9)) % 700) - 60;
                const x = 50 + rnd(`rx${i}`) * 320;
                return <line key={i} x1={x} y1={y} x2={x - 2} y2={y + 28 + rnd(`rl${i}`) * 40} stroke="rgba(190,214,236,0.35)" strokeWidth={1.6} strokeLinecap="round" />;
              })}
            </g>
            <rect x={36} y={330} width={340} height={600} fill="none" stroke="#06090d" strokeWidth={14} />
            <line x1={206} y1={330} x2={206} y2={930} stroke="#06090d" strokeWidth={9} />
            <line x1={36} y1={630} x2={376} y2={630} stroke="#06090d" strokeWidth={9} />
            <polygon points="36,330 376,330 760,1100 280,1100" fill="rgba(110,150,190,0.09)" style={{ mixBlendMode: "screen" }} filter="url(#b22)" />
          </g>

          {/* estante desfocada */}
          <g filter="url(#b8)" opacity={0.85}>
            {shelf}
            {[0, 1, 2].map((r) => (
              <rect key={r} x={630} y={470 + r * 190 + 160} width={460} height={10} fill="#120c08" />
            ))}
          </g>

          {/* mesa */}
          <polygon points={`0,${DESK_Y} 780,${DESK_Y} 820,1520 0,1560`} fill="url(#deskTop)" />
          <rect x={0} y={DESK_Y - 4} width={780} height={6} fill="rgba(255,220,160,0.25)" />
          <rect x={0} y={1556} width={WIDTH} height={400} fill="#05060a" />
          <ellipse cx={440} cy={1420} rx={560} ry={150} fill="url(#pool)" style={{ mixBlendMode: "screen" }} opacity={lamp} />

          {/* livro aberto */}
          <g>
            <polygon points="250,1372 405,1352 405,1420 235,1440" fill="url(#paper)" />
            <polygon points="405,1352 560,1372 575,1440 405,1420" fill="url(#paper)" />
            {Array.from({ length: 7 }).map((_, i) => (
              <g key={i} opacity={0.35}>
                <line x1={270} y1={1380 + i * 8.3} x2={392} y2={1362 + i * 8.3} stroke="#3a3326" strokeWidth={1.6} />
                <line x1={420} y1={1362 + i * 8.3} x2={548} y2={1382 + i * 8.3} stroke="#3a3326" strokeWidth={1.6} />
              </g>
            ))}
            <polygon points="235,1440 405,1420 575,1440 575,1452 405,1432 235,1452" fill="#1a110a" />
          </g>

          {/* caderno + tinta */}
          <g>
            <polygon points="560,1378 790,1366 830,1440 585,1462" fill="url(#paper)" opacity={0.95} />
            {[0, 1, 2, 3].map((i) => {
              const p = Math.min(1, Math.max(0, ink * 4 - i));
              const y0 = 1392 + i * 13;
              return (
                <line key={i} x1={600} y1={y0 + 5} x2={600 + 168 * p} y2={y0 - 3 * p + 4} stroke="#1b1a2a" strokeWidth={2.2} strokeLinecap="round" strokeDasharray="9 3 14 4 6 3" opacity={0.8} />
              );
            })}
          </g>

          <Clock sec={secDeg} />

          {/* abajur articulado */}
          <g>
            <ellipse cx={150} cy={1500} rx={96} ry={20} fill="#0a0806" />
            <path d="M150,1494 L212,1040" stroke="#161114" strokeWidth={13} strokeLinecap="round" fill="none" />
            <path d="M212,1040 L326,892" stroke="#161114" strokeWidth={11} strokeLinecap="round" fill="none" />
            <path d="M150,1494 L212,1040" stroke="rgba(255,214,150,0.35)" strokeWidth={2} fill="none" transform="translate(-4 0)" />
            <circle cx={212} cy={1040} r={11} fill="#1d171b" />
            <path d="M286,880 L420,918 L452,806 L312,774 Z" fill="#0c0a0b" stroke="rgba(255,214,150,0.45)" strokeWidth={2} />
          </g>
        </svg>

        {/* cone de luz + brilho da lâmpada */}
        <AbsoluteFill style={{ mixBlendMode: "screen", opacity: lamp }}>
          <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
            <polygon points="296,902 440,930 840,1440 440,1480" fill="url(#cone)" filter="url(#b22)" opacity={0.9} />
            <circle cx={366} cy={904} r={150} fill="url(#bulb)" />
          </svg>
        </AbsoluteFill>
        <Dust count={70} region={[200, 880, 860, 1460]} litAt={inCone} opacity={1} size={[1.2, 3.4]} seed="dk" speed={0.6} />

        {/* homem de perfil (por cima da mesa, atrás do caderno) */}
        <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
          <defs>
            <clipPath id="below"><rect x={0} y={0} width={WIDTH} height={1560} /></clipPath>
          </defs>
          <g clipPath="url(#below)" transform={`translate(0 ${breath})`}>
            {/* encosto da cadeira */}
            <path d="M880,1180 C930,1300 940,1500 930,1700 L1080,1700 L1080,1180 Z" fill="#07090c" />
            {/* tronco */}
            <path
              d="M824,1112 C790,1126 770,1170 764,1240 C760,1320 764,1420 770,1580 L930,1580 C930,1440 922,1300 898,1200 C884,1150 860,1118 824,1112 Z"
              fill="url(#shirt)"
            />
            <path d="M826,1114 C792,1130 772,1176 765,1246" fill="none" stroke="#ffd9a0" strokeOpacity={0.42} strokeWidth={2.6} />
            {/* braço: ombro → cotovelo → pulso (acompanha a escrita) */}
            <path
              d={`M830,1140 C800,1190 770,1260 744,${DESK_Y - 22 + wy} L ${628 + wx},${DESK_Y - 20 + wy} L ${628 + wx},${DESK_Y - 2 + wy} L 752,${DESK_Y + 6} C792,1290 830,1210 862,1160 Z`}
              fill="#10161d"
              stroke="#ffd9a0"
              strokeOpacity={0.28}
              strokeWidth={1.8}
            />
            {/* mão + caneta */}
            <path d={`M${628 + wx},${DESK_Y - 22 + wy} C ${606 + wx},${DESK_Y - 22 + wy} ${590 + wx},${DESK_Y - 12 + wy} ${584 + wx},${DESK_Y - 2 + wy} L ${620 + wx},${DESK_Y + 2 + wy} Z`} fill="#16100c" stroke="#ffd9a0" strokeOpacity={0.5} strokeWidth={1.4} />
            <line x1={598 + wx} y1={DESK_Y - 8 + wy} x2={560 + wx} y2={DESK_Y + 22 + wy} stroke="#0a0a0d" strokeWidth={5} strokeLinecap="round" />
            <circle cx={558 + wx} cy={DESK_Y + 24 + wy} r={2.4} fill="#ffe2a8" />
            {/* pescoço */}
            <path d="M806,1060 L850,1050 L858,1126 L812,1130 Z" fill="#0a0d12" />
            {/* cabeça articulada no pescoço */}
            <g transform={`translate(${PIVOT.x} ${PIVOT.y}) rotate(${headAngle}) translate(-14 -118)`}>
              <polygon points={pts(FACE)} fill="#0b0e13" />
              {/* cabelo */}
              <path d="M-30,-98 C-8,-118 44,-112 72,-82 C90,-52 92,-10 84,6 C70,-26 40,-60 10,-70 C-8,-74 -22,-86 -30,-98 Z" fill="#050608" />
              {/* contra-luz dourada no perfil */}
              <polyline points={pts(FRONT_EDGE)} fill="none" stroke="#ffd9a0" strokeOpacity={0.75} strokeWidth={3.2} strokeLinejoin="round" strokeLinecap="round" />
              <polyline points={pts(FRONT_EDGE)} fill="none" stroke="#ffcf8a" strokeOpacity={0.4} strokeWidth={10} strokeLinejoin="round" filter="url(#b3)" />
              {/* reflexo do relógio no olho */}
              <circle cx={-44} cy={-34} r={2.2} fill="#ffe2a8" opacity={0.55 + 0.4 * headLook} />
            </g>
          </g>
        </svg>

      </Camera>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 24%, rgba(0,0,0,0) 62%, rgba(0,0,0,0.78) 100%)" }} />
    </AbsoluteFill>
  );
};
