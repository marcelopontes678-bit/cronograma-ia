import { AbsoluteFill, Sequence, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FPS, HEIGHT, WIDTH } from "../config";
import { SANS } from "../fonts";
import { ease, easeOut } from "../lib/motion";
import timeline from "./data/timeline.json";

export const GREEN = "#22e05a";
export const GREEN_DEEP = "#0d9f3a";
export const T = timeline;
export const sec = (s: number) => Math.round(s * FPS);

// ------------------------------------------------------------------ fundo de linhas onduladas
/** Linhas horizontais que ondulam mais no centro (como um espectro de áudio). */
export const Waves: React.FC<{ opacity?: number }> = ({ opacity = 1 }) => {
  const frame = useCurrentFrame();
  const rows = 36;
  const paths = Array.from({ length: rows }).map((_, i) => {
    const y0 = 20 + i * 54;
    const amp = 20 * Math.exp(-Math.pow((y0 - 900) / 520, 2));
    let d = `M-20,${y0}`;
    for (let x = -20; x <= WIDTH + 20; x += 14) {
      const y = y0 + amp * Math.sin(x * 0.034 + i * 0.5 + frame * 0.075) * Math.sin(x * 0.006 + frame * 0.02 + i);
      d += ` L${x},${y.toFixed(1)}`;
    }
    return <path key={i} d={d} fill="none" stroke="#4a4d52" strokeWidth={2.2} opacity={0.55 + 0.35 * Math.exp(-Math.pow((y0 - 900) / 700, 2))} />;
  });
  return (
    <AbsoluteFill style={{ background: "#050505", opacity }}>
      <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>{paths}</svg>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 70% 40% at 50% 45%, rgba(34,224,90,0.07) 0%, rgba(0,0,0,0) 70%)" }} />
    </AbsoluteFill>
  );
};

/** Meio-tom (bolinhas) usado na cena final. */
export const Halftone: React.FC = () => {
  const frame = useCurrentFrame();
  const dots: React.ReactNode[] = [];
  const step = 30;
  for (let y = 0; y < HEIGHT + step; y += step) {
    for (let x = 0; x < WIDTH + step; x += step) {
      const px = x + (Math.round(y / step) % 2) * (step / 2);
      const d1 = Math.hypot(px - 120, y - 380) / 820;
      const d2 = Math.hypot(px - 980, y - 1560) / 860;
      const k = Math.max(0, 1 - Math.min(d1, d2));
      const r = 1.2 + 9.5 * k * k * (0.88 + 0.12 * Math.sin(frame / 22 + (x + y) * 0.008));
      dots.push(<circle key={`${x}-${y}`} cx={px} cy={y} r={r} fill="#dcdcdc" opacity={0.25 + 0.75 * k} />);
    }
  }
  return (
    <AbsoluteFill style={{ background: "#050505" }}>
      <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>{dots}</svg>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ apresentador "sem rosto" (ilustração própria)
export const Presenter: React.FC<{ x: number; y: number; scale: number; seed?: number }> = ({ x, y, scale, seed = 0 }) => {
  const frame = useCurrentFrame();
  const bob = Math.sin(frame / 9 + seed) * 5;
  const tilt = Math.sin(frame / 21 + seed) * 1.6;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 700, height: 1000, transform: `translate(-50%, 0) scale(${scale}) translateY(${bob}px)`, transformOrigin: "50% 100%" }}>
      <svg width={700} height={1000} viewBox="0 0 700 1000">
        <defs>
          <linearGradient id="shirt" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#d1a047" />
            <stop offset="1" stopColor="#8d6a25" />
          </linearGradient>
          <radialGradient id="mask" cx="0.35" cy="0.3" r="0.9">
            <stop offset="0" stopColor="#ffe36a" />
            <stop offset="0.6" stopColor="#f2b705" />
            <stop offset="1" stopColor="#b98600" />
          </radialGradient>
          <linearGradient id="micG" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#2a2a2e" />
            <stop offset="0.5" stopColor="#58585e" />
            <stop offset="1" stopColor="#1c1c20" />
          </linearGradient>
        </defs>
        {/* ombros / camiseta */}
        <path d="M10,1000 C20,830 120,730 270,700 L430,700 C580,730 680,830 690,1000 Z" fill="url(#shirt)" />
        <path d="M270,700 C300,760 400,760 430,700" fill="none" stroke="#6e5019" strokeWidth={10} />
        <path d="M120,780 C160,860 170,940 160,1000" fill="none" stroke="#7c5c20" strokeWidth={6} opacity={0.5} />
        {/* cabeça com cap (rotaciona de leve) */}
        <g transform={`rotate(${tilt} 350 640)`}>
          <rect x={296} y={560} width={108} height={150} rx={40} fill="#e0a800" />
          <ellipse cx={350} cy={400} rx={175} ry={215} fill="url(#mask)" />
          <ellipse cx={176} cy={420} rx={26} ry={52} fill="#e5ac00" />
          <ellipse cx={524} cy={420} rx={26} ry={52} fill="#e5ac00" />
          {/* dobras do tecido (sem rosto) */}
          <path d="M230,470 C290,500 410,500 470,470" fill="none" stroke="#c99200" strokeWidth={5} opacity={0.55} />
          <path d="M250,360 C300,380 400,380 450,360" fill="none" stroke="#c99200" strokeWidth={4} opacity={0.35} />
          {/* boné */}
          <path d="M172,330 C176,170 270,110 350,110 C430,110 524,170 528,330 C470,300 230,300 172,330 Z" fill="#101114" />
          <path d="M150,335 C250,290 450,290 550,335 C500,360 200,360 150,335 Z" fill="#17181c" />
          <rect x={172} y={236} width={356} height={14} fill={GREEN} opacity={0.9} transform="rotate(-2 350 243)" />
        </g>
        {/* microfone */}
        <g>
          <line x1={80} y1={1000} x2={150} y2={620} stroke="#202024" strokeWidth={16} strokeLinecap="round" />
          <rect x={92} y={470} width={116} height={190} rx={58} fill="url(#micG)" />
          {Array.from({ length: 7 }).map((_, i) => (
            <line key={i} x1={104} y1={500 + i * 24} x2={196} y2={500 + i * 24} stroke="#0c0c0e" strokeWidth={3} opacity={0.7} />
          ))}
        </g>
      </svg>
    </div>
  );
};

// ------------------------------------------------------------------ celular
export const PHONE_W = 600;
export const PHONE_H = 1180;
export const SCREEN = { x: 22, y: 22, w: 556, h: 1136, r: 58 };

export const PhoneFrame: React.FC<{
  children: React.ReactNode;
  glow?: boolean;
  style?: React.CSSProperties;
}> = ({ children, glow, style }) => (
  <div
    style={{
      position: "absolute",
      width: PHONE_W,
      height: PHONE_H,
      borderRadius: 82,
      background: "#0a0a0c",
      border: `6px solid ${glow ? GREEN : "#2b2b30"}`,
      boxShadow: glow ? `0 0 70px rgba(34,224,90,0.55), inset 0 0 0 3px #000` : "0 20px 60px rgba(0,0,0,0.6), inset 0 0 0 3px #000",
      ...style,
    }}
  >
    <div
      style={{
        position: "absolute",
        left: SCREEN.x - 6,
        top: SCREEN.y - 6,
        width: SCREEN.w,
        height: SCREEN.h,
        borderRadius: SCREEN.r,
        overflow: "hidden",
        background: "#111",
      }}
    >
      {children}
    </div>
    <div style={{ position: "absolute", left: PHONE_W / 2 - 62, top: 24, width: 124, height: 34, borderRadius: 20, background: "#000" }} />
  </div>
);

/** Posição de entrada com mola (de baixo + leve rotação). */
export const usePop = (start: number, delay = 0) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - sec(start) - delay, fps, config: { damping: 14, stiffness: 120, mass: 0.8 } });
};

// ------------------------------------------------------------------ vídeo-exemplo dentro do celular
/** Renderiza uma cena 1080x1920 reduzida dentro do visor do celular. */
export const ClipScreen: React.FC<{ from: number; children: React.ReactNode }> = ({ from, children }) => {
  const s = SCREEN.h / HEIGHT; // cobre a altura; as laterais são cortadas
  return (
    <Sequence from={from} layout="none">
      <div
        style={{
          position: "absolute",
          left: -(WIDTH * s - SCREEN.w) / 2,
          top: 0,
          width: WIDTH,
          height: HEIGHT,
          transform: `scale(${s})`,
          transformOrigin: "0 0",
        }}
      >
        {children}
      </div>
    </Sequence>
  );
};

// ------------------------------------------------------------------ selo "IA" (ícone próprio)
export const AIBadge: React.FC<{ size?: number }> = ({ size = 520 }) => {
  const frame = useCurrentFrame();
  const pulse = 1 + 0.025 * Math.sin(frame / 6);
  return (
    <div style={{ width: size, height: size, transform: `scale(${pulse})` }}>
      <svg width={size} height={size} viewBox="0 0 520 520">
        <defs>
          <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#3df27a" />
            <stop offset="1" stopColor="#0a9b36" />
          </linearGradient>
          <filter id="glowF" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="22" />
          </filter>
        </defs>
        <rect x={50} y={50} width={420} height={420} rx={110} fill={GREEN} opacity={0.55} filter="url(#glowF)" />
        <rect x={50} y={50} width={420} height={420} rx={110} fill="url(#bg)" />
        <rect x={50} y={50} width={420} height={420} rx={110} fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth={5} />
        {/* cantos de enquadramento */}
        {[
          "M120,170 L120,120 L170,120",
          "M350,120 L400,120 L400,170",
          "M120,350 L120,400 L170,400",
          "M400,350 L400,400 L350,400",
        ].map((d) => (
          <path key={d} d={d} fill="none" stroke="#fff" strokeWidth={16} strokeLinecap="round" strokeLinejoin="round" />
        ))}
        <text x={260} y={318} textAnchor="middle" fontFamily={SANS} fontWeight={900} fontSize={190} fill="#fff" letterSpacing={-4}>
          IA
        </text>
        {/* faíscas */}
        <path d="M388,150 l10,24 l24,10 l-24,10 l-10,24 l-10,-24 l-24,-10 l24,-10 Z" fill="#fff" />
      </svg>
    </div>
  );
};

// ------------------------------------------------------------------ legendas gigantes (uma palavra/grupo por vez)
export const BigCaptions: React.FC<{ yAt: (t: number) => number }> = ({ yAt }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / FPS;
  const idx = T.captions.findIndex((c) => t >= c.s - 0.02 && t < c.hold);
  if (idx < 0) return null;
  const c = T.captions[idx];
  const text = c.text.toUpperCase();
  const size = Math.min(188, Math.floor(980 / (text.length * 0.66)));
  const pop = spring({ frame: frame - Math.round((c.s - 0.02) * fps), fps, config: { damping: 11, stiffness: 260, mass: 0.5 } });
  const scale = 0.72 + 0.28 * pop;
  const rot = (idx % 2 ? 1 : -1) * (1 - pop) * 3;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: 50,
          right: 50,
          top: yAt(t),
          transform: `translateY(-50%) scale(${scale}) rotate(${rot}deg)`,
          textAlign: "center",
          fontFamily: SANS,
          fontWeight: 900,
          fontSize: size,
          lineHeight: 1,
          letterSpacing: "-0.02em",
          color: c.hl ? GREEN : "#fff",
          WebkitTextStroke: `${Math.round(size * 0.1)}px #000`,
          paintOrder: "stroke fill",
          textShadow: "0 8px 30px rgba(0,0,0,0.7)",
          whiteSpace: "nowrap",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

/** Transição "whip": a cena entra deslizando com desfoque e a anterior sai para o lado. */
export const SceneSlide: React.FC<{ from: number; to: number; first?: boolean; last?: boolean; children: React.ReactNode }> = ({
  from,
  to,
  first,
  last,
  children,
}) => {
  const frame = useCurrentFrame();
  const f0 = sec(from);
  const f1 = sec(to);
  const W = 9;
  if (frame < f0 || frame > f1 + W) return null;
  const pin = first ? 1 : easeOut(frame, [f0, f0 + W], [0, 1]);
  const pout = last ? 0 : ease(frame, [f1, f1 + W], [0, 1]);
  const x = (1 - pin) * 1100 - pout * 1100;
  const blur = ((1 - pin) + pout) * 16;
  return (
    <AbsoluteFill style={{ transform: `translateX(${x}px)`, filter: blur > 0.3 ? `blur(${blur}px)` : undefined }}>
      {children}
    </AbsoluteFill>
  );
};
