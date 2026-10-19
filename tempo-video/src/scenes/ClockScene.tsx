import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, HEIGHT, WIDTH } from "../config";
import { SERIF } from "../fonts";
import { Camera } from "../components/Camera";
import { Dust } from "../components/Dust";
import { ease, flicker } from "../lib/motion";

const CX = 540;
const CY = 1020;
const ROMAN = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"];

const polar = (r: number, deg: number): [number, number] => {
  const a = ((deg - 90) * Math.PI) / 180;
  return [CX + r * Math.cos(a), CY + r * Math.sin(a)];
};

/** Mostrador, ponteiros e aro de latão. `shadow` desenha só as sombras dos ponteiros. */
const ClockArt: React.FC<{ secAngle: number; minAngle: number; hourAngle: number }> = ({
  secAngle,
  minAngle,
  hourAngle,
}) => {
  const hands = (fillHour: string, fillMin: string, fillSec: string, stroke: string) => (
    <>
      <g transform={`translate(${CX} ${CY}) rotate(${hourAngle})`}>
        <path
          d="M0,-262 C34,-196 36,-132 16,-64 L9,46 L-9,46 L-16,-64 C-36,-132 -34,-196 0,-262 Z"
          fill={fillHour}
          stroke={stroke}
          strokeWidth={2}
        />
        <circle cx={0} cy={-178} r={20} fill="none" stroke={stroke} strokeWidth={3} opacity={0.8} />
      </g>
      <g transform={`translate(${CX} ${CY}) rotate(${minAngle})`}>
        <path d="M0,-432 L13,-310 L9,48 L-9,48 L-13,-310 Z" fill={fillMin} stroke={stroke} strokeWidth={2} />
      </g>
      <g transform={`translate(${CX} ${CY}) rotate(${secAngle})`}>
        <rect x={-2.5} y={-486} width={5} height={600} fill={fillSec} />
        <circle cx={0} cy={96} r={17} fill={fillSec} />
        <circle cx={0} cy={-330} r={11} fill={fillSec} />
      </g>
    </>
  );

  return (
    <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <linearGradient id="brass" gradientUnits="userSpaceOnUse" x1={-40} y1={380} x2={1100} y2={1700}>
          <stop offset="0" stopColor="#6c4e1e" />
          <stop offset="0.16" stopColor="#f5d894" />
          <stop offset="0.30" stopColor="#8a6a2c" />
          <stop offset="0.52" stopColor="#2c1f0b" />
          <stop offset="0.74" stopColor="#5a4219" />
          <stop offset="0.9" stopColor="#c59f55" />
          <stop offset="1" stopColor="#2a1d0a" />
        </linearGradient>
        <radialGradient id="dial" cx="0.34" cy="0.30" r="0.95">
          <stop offset="0" stopColor="#1f262e" />
          <stop offset="0.45" stopColor="#0d1116" />
          <stop offset="1" stopColor="#030405" />
        </radialGradient>
        <linearGradient id="goldText" gradientUnits="userSpaceOnUse" x1={0} y1={0} x2={1080} y2={0}>
          <stop offset="0" stopColor="#f6dc9a" />
          <stop offset="0.5" stopColor="#b98f43" />
          <stop offset="1" stopColor="#4d3a18" />
        </linearGradient>
        <linearGradient id="handGold" gradientUnits="userSpaceOnUse" x1={300} y1={0} x2={780} y2={0}>
          <stop offset="0" stopColor="#f3d590" />
          <stop offset="1" stopColor="#7a5a22" />
        </linearGradient>
        <filter id="blur6">
          <feGaussianBlur stdDeviation="7" />
        </filter>
      </defs>

      {/* aro de latão */}
      <circle cx={CX} cy={CY} r={590} fill="none" stroke="url(#brass)" strokeWidth={54} />
      <circle cx={CX} cy={CY} r={617} fill="none" stroke="#0a0705" strokeWidth={3} opacity={0.9} />
      <circle cx={CX} cy={CY} r={563} fill="none" stroke="#f7e1a6" strokeWidth={1.6} opacity={0.5} />
      {/* mostrador */}
      <circle cx={CX} cy={CY} r={562} fill="url(#dial)" />
      <circle cx={CX} cy={CY} r={534} fill="none" stroke="#c9a35a" strokeWidth={1.4} opacity={0.35} />

      {/* trilha dos minutos */}
      {Array.from({ length: 60 }).map((_, i) => {
        const major = i % 5 === 0;
        const [x1, y1] = polar(major ? 500 : 516, i * 6);
        const [x2, y2] = polar(534, i * 6);
        return (
          <line
            key={i}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke="url(#goldText)"
            strokeWidth={major ? 4.5 : 1.8}
            strokeLinecap="round"
            opacity={major ? 0.95 : 0.7}
          />
        );
      })}
      {/* numerais romanos */}
      {ROMAN.map((n, i) => {
        const [x, y] = polar(410, i * 30);
        return (
          <text
            key={n}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="central"
            fontFamily={SERIF}
            fontWeight={500}
            fontSize={n.length > 2 ? 78 : 92}
            fill="url(#goldText)"
            transform={`rotate(${i * 30} ${x} ${y})`}
          >
            {n}
          </text>
        );
      })}
      <text
        x={CX}
        y={CY - 214}
        textAnchor="middle"
        fontFamily={SERIF}
        fontStyle="italic"
        fontSize={34}
        letterSpacing={9}
        fill="url(#goldText)"
        opacity={0.8}
      >
        TEMPUS
      </text>

      {/* sombras dos ponteiros (profundidade) */}
      <g transform="translate(16 24)" opacity={0.6} filter="url(#blur6)">
        {hands("#000", "#000", "#000", "#000")}
      </g>
      {hands("url(#handGold)", "url(#handGold)", "#e4b25b", "#2a1d0a")}
      {/* tampa central */}
      <circle cx={CX} cy={CY} r={27} fill="url(#brass)" stroke="#1a1208" strokeWidth={3} />
      <circle cx={CX - 7} cy={CY - 8} r={7} fill="#fff2c7" opacity={0.7} />
    </svg>
  );
};

export const ClockScene: React.FC<{ duration: number }> = ({ duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ponteiro dos segundos: "bate" a cada segundo com um leve repique (mesmo instante do tique do áudio)
  const n = Math.floor(frame / fps);
  const since = frame - n * fps;
  const snap = spring({ frame: since, fps, config: { damping: 6, stiffness: 420, mass: 0.22 } });
  const secAngle = 42 + 6 * (n - 1) + 6 * snap;
  const minAngle = 252 + (frame / fps) * 0.1;
  const hourAngle = 291 + (frame / fps) * (0.1 / 12);

  const lamp = flicker(frame, 1.7, 0.07);
  const breathe = 0.82 + 0.18 * Math.sin(frame / 38);

  // pontos de poeira só aparecem dentro do feixe (vindo da esquerda, descendo para o relógio)
  const inBeam = (x: number, y: number) => {
    const axisY = 640 + x * 0.42; // eixo do feixe
    const d = Math.abs(y - axisY) / (260 + x * 0.25);
    return Math.max(0, 1 - d) * Math.max(0, 1 - x / 980);
  };

  return (
    <AbsoluteFill style={{ background: "#030405" }}>
      <Camera from={{ scale: 1.0, x: 0, y: 0 }} to={{ scale: 1.34, x: -18, y: -26 }} duration={150} origin={[CX, CY - 40]} shake={0.8}>
        <ClockArt secAngle={secAngle} minAngle={minAngle} hourAngle={hourAngle} />
        {/* profundidade de campo: bordas desfocadas */}
        <AbsoluteFill
          style={{
            filter: "blur(13px)",
            WebkitMaskImage: `radial-gradient(circle at ${CX}px ${CY - 40}px, transparent 0, transparent 30%, #000 58%)`,
            maskImage: `radial-gradient(circle at ${CX}px ${CY - 40}px, transparent 0, transparent 30%, #000 58%)`,
          }}
        >
          <ClockArt secAngle={secAngle} minAngle={minAngle} hourAngle={hourAngle} />
        </AbsoluteFill>

        {/* feixe de luz lateral dourada atravessando o ar */}
        <AbsoluteFill style={{ mixBlendMode: "screen", opacity: 0.75 * breathe * lamp }}>
          <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0, filter: "blur(34px)" }}>
            <defs>
              <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0.5">
                <stop offset="0" stopColor="#ffd28a" stopOpacity="0.55" />
                <stop offset="0.6" stopColor="#ffc46e" stopOpacity="0.16" />
                <stop offset="1" stopColor="#ffc46e" stopOpacity="0" />
              </linearGradient>
            </defs>
            <polygon points="-60,330 -60,980 900,1210 980,760" fill="url(#beam)" />
          </svg>
        </AbsoluteFill>
        <Dust count={85} region={[0, 380, 900, 1300]} litAt={inBeam} opacity={0.95} size={[1.3, 3.8]} seed="clk" />
        <Dust count={14} region={[0, 300, 1080, 1500]} opacity={0.35} size={[10, 26]} blur={9} seed="clkb" litAt={(x) => Math.max(0, 1 - x / 1000)} color="255,214,150" />
      </Camera>

      {/* luz lateral e queda de sombra */}
      <AbsoluteFill
        style={{
          background: "linear-gradient(82deg, rgba(255,190,100,0.34) 0%, rgba(255,190,100,0.10) 32%, rgba(255,190,100,0) 58%)",
          mixBlendMode: "screen",
          opacity: lamp,
        }}
      />
      <AbsoluteFill style={{ background: "linear-gradient(270deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.55) 30%, rgba(0,0,0,0) 62%)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.78) 0%, rgba(0,0,0,0) 28%, rgba(0,0,0,0) 62%, rgba(0,0,0,0.82) 100%)" }} />
      {/* reflexo no vidro */}
      <AbsoluteFill style={{ mixBlendMode: "screen", opacity: ease(frame, [0, 60], [0, 1]) }}>
        <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
          <defs>
            <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#fff2d0" stopOpacity="0.22" />
              <stop offset="1" stopColor="#fff2d0" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d="M130,760 C220,420 520,300 800,380 C560,420 330,560 250,900 Z" fill="url(#glass)" filter="blur(6px)" />
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: C.black, opacity: ease(frame, [0, 22], [1, 0]) }} />
    </AbsoluteFill>
  );
};
