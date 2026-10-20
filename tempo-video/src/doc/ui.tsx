import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { HEIGHT, WIDTH } from "../config";
import { SANS } from "../fonts";
import timeline from "./data/timeline.json";

export const D = {
  black: "#070708",
  graphite: "#17191c",
  graphite2: "#24272b",
  line: "#3a3e44",
  white: "#f4f3ef",
  muted: "#9aa0a6",
  green: "#1f9d5b",
  yellow: "#e9c547",
  paper: "#ecebe6",
  ink: "#16181b",
};
export const FPS = 30;
export const T = timeline;
export const sec = (s: number) => Math.round(s * FPS);

export const eo = Easing.bezier(0.16, 1, 0.3, 1);
export const ei = Easing.bezier(0.7, 0, 0.84, 0);
export const io = Easing.bezier(0.65, 0, 0.35, 1);
export const iv = (f: number, i: number[], o: number[], e?: (t: number) => number) =>
  interpolate(f, i, o, { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: e });

/** Câmera lenta: zoom + deslocamento contínuos (cada cena define o seu). */
export const Push: React.FC<{ f: number; len: number; from?: number; to?: number; dx?: number; dy?: number; origin?: string; children: React.ReactNode }> = ({
  f, len, from = 1, to = 1.08, dx = 0, dy = 0, origin = "50% 50%", children,
}) => {
  const p = iv(f, [0, len], [0, 1], io);
  return (
    <AbsoluteFill style={{ transform: `translate(${dx * p}px, ${dy * p}px) scale(${from + (to - from) * p})`, transformOrigin: origin }}>
      {children}
    </AbsoluteFill>
  );
};

/** Texto que sobe por trás de uma máscara (revelação editorial). */
export const Reveal: React.FC<{ f: number; at: number; children: React.ReactNode; style?: React.CSSProperties; dur?: number }> = ({ f, at, children, style, dur = 16 }) => {
  const p = iv(f, [at, at + dur], [0, 1], eo);
  return (
    <div style={{ overflow: "hidden", ...style }}>
      <div style={{ transform: `translateY(${(1 - p) * 105}%)`, opacity: Math.min(1, p * 1.6) }}>{children}</div>
    </div>
  );
};

/** Legendas sincronizadas palavra a palavra (tempos do Whisper alinhados ao roteiro). */
export const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const page = T.pages.find((p) => t >= p.start - 0.08 && t < p.end + 0.25);
  if (!page) return null;
  const o = Math.min(iv(t, [page.start - 0.08, page.start + 0.06], [0, 1]), 1 - iv(t, [page.end + 0.1, page.end + 0.25], [0, 1]));
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 640, background: "linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.55) 60%, rgba(0,0,0,0.7) 100%)" }} />
      <div style={{ position: "absolute", left: 80, right: 80, bottom: 448, textAlign: "center", opacity: o, fontFamily: SANS, fontWeight: 600, fontSize: 50, lineHeight: 1.25, textShadow: "0 2px 16px rgba(0,0,0,0.95)" }}>
        {page.words.map((w, i) => {
          const spoken = t >= w.s;
          return (
            <span key={i} style={{ color: spoken ? D.white : "rgba(244,243,239,0.55)", marginRight: i < page.words.length - 1 ? "0.27em" : 0, display: "inline-block" }}>
              {w.w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Grão + vinheta + leve gradação fria (consistente em todas as cenas). */
export const FilmLook: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 85% 70% at 50% 45%, rgba(0,0,0,0) 40%, rgba(0,0,0,0.72) 100%)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(20,40,55,0.25), rgba(0,0,0,0) 40%, rgba(40,30,10,0.12))", mixBlendMode: "soft-light" }} />
      <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0, opacity: 0.09, mixBlendMode: "overlay" }}>
        <filter id="docGrain">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={f % 30} />
        </filter>
        <rect width={WIDTH} height={HEIGHT} filter="url(#docGrain)" />
      </svg>
    </AbsoluteFill>
  );
};

/** Carimbo de status jurídico (entra com impacto). */
export const Stamp: React.FC<{ f: number; at: number; text: string; color?: string; size?: number; rot?: number; blend?: boolean }> = ({ f, at, text, color = D.ink, size = 34, rot = -8, blend = true }) => {
  const p = iv(f, [at, at + 5], [0, 1], ei);
  if (f < at) return null;
  return (
    <div
      style={{
        display: "inline-block",
        padding: `${size * 0.25}px ${size * 0.55}px`,
        border: `${Math.max(3, size * 0.11)}px solid ${color}`,
        borderRadius: 8,
        color,
        fontFamily: SANS,
        fontWeight: 900,
        fontSize: size,
        letterSpacing: "0.08em",
        transform: `rotate(${rot}deg) scale(${1.9 - 0.9 * p})`,
        opacity: p,
        mixBlendMode: blend ? "multiply" : "normal",
      }}
    >
      {text}
    </div>
  );
};
