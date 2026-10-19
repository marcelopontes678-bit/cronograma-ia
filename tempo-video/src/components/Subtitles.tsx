import { AbsoluteFill, useCurrentFrame } from "remotion";
import { C, FPS, HEIGHT, SAFE, WIDTH } from "../config";
import { SANS } from "../fonts";
import { ease } from "../lib/motion";
import captions from "../data/captions.json";

type Word = { w: string; s: number; e: number };
type Page = { start: number; end: number; words: Word[] };
const PAGES = captions as Page[];

/**
 * Legendas em português sincronizadas palavra a palavra (tempos do Whisper alinhados ao roteiro).
 * Ficam acima da área ocupada pela interface do Reels (SAFE.bottom).
 */
export const Subtitles: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const page = PAGES.find((p) => t >= p.start - 0.1 && t < p.end + 0.32);
  if (!page) return null;
  const inO = ease(t, [page.start - 0.1, page.start + 0.1], [0, 1]);
  const outO = 1 - ease(t, [page.end + 0.12, page.end + 0.32], [0, 1]);
  const dy = ease(t, [page.start - 0.1, page.start + 0.2], [8, 0]);

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 0,
          height: 700,
          background: "linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.5) 62%, rgba(0,0,0,0.6) 100%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: SAFE.side,
          right: SAFE.side,
          bottom: SAFE.bottom + 10,
          textAlign: "center",
          opacity: Math.min(inO, outO),
          transform: `translateY(${dy}px)`,
          fontFamily: SANS,
          fontWeight: 500,
          fontSize: 54,
          lineHeight: 1.28,
          letterSpacing: "0.005em",
          textShadow: "0 2px 18px rgba(0,0,0,0.9), 0 0 3px rgba(0,0,0,0.8)",
        }}
      >
        {page.words.map((w, i) => {
          const active = t >= w.s && t < w.e;
          const spoken = t >= w.e;
          return (
            <span
              key={i}
              style={{
                color: active ? C.goldBright : spoken ? C.ivory : "rgba(239,232,216,0.62)",
                display: "inline-block",
                marginRight: i < page.words.length - 1 ? "0.28em" : 0,
              }}
            >
              {w.w}
            </span>
          );
        })}
      </div>
      <div style={{ position: "absolute", inset: 0, height: HEIGHT, width: WIDTH }} />
    </AbsoluteFill>
  );
};
