import { AbsoluteFill, useCurrentFrame } from "remotion";
import { C, FPS, HEIGHT, SAFE, WIDTH } from "../config";
import { SANS, SERIF } from "../fonts";
import { ease, easeOut } from "../lib/motion";

export type StatementLine = { text: string; at: number; gold?: boolean; small?: boolean };

/**
 * Frase principal da cena (Cormorant Garamond). Entra com opacidade + 14 px de deslocamento vertical,
 * sai antes do corte. Tempos em segundos globais. `top` = posição (px) do centro do bloco.
 */
export const Statement: React.FC<{
  lines: StatementLine[];
  out: number;
  top?: number;
  size?: number;
  rule?: boolean;
}> = ({ lines, out, top = 480, size, rule = true }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const maxChars = Math.max(...lines.filter((l) => !l.small).map((l) => l.text.length));
  const fontSize = size ?? Math.min(92, Math.floor((WIDTH - SAFE.side * 2 - 40) / (maxChars * 0.78)));
  const first = lines[0].at;
  const fadeOut = 1 - ease(t, [out, out + 0.55], [0, 1]);
  if (t < first - 0.1 || fadeOut <= 0) return null;
  const ruleW = easeOut(t, [first - 0.1, first + 0.8], [0, 1]);

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* sombra suave atrás do texto para legibilidade em qualquer cena */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: top - 260,
          height: 520,
          background: "radial-gradient(ellipse 60% 50% at 50% 50%, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0) 100%)",
          opacity: fadeOut,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: SAFE.side,
          right: SAFE.side,
          top,
          transform: "translateY(-50%)",
          textAlign: "center",
          opacity: fadeOut,
        }}
      >
        {rule && (
          <div
            style={{
              width: 96 * ruleW,
              height: 2,
              background: `linear-gradient(90deg, transparent, ${C.gold}, transparent)`,
              margin: "0 auto 34px",
            }}
          />
        )}
        {lines.map((l, i) => {
          const o = easeOut(t, [l.at, l.at + 0.75], [0, 1]);
          const dy = easeOut(t, [l.at, l.at + 0.9], [14, 0]);
          return (
            <div
              key={i}
              style={{
                opacity: o,
                transform: `translateY(${dy}px)`,
                fontFamily: l.small ? SANS : SERIF,
                fontWeight: l.small ? 500 : 500,
                fontSize: l.small ? Math.round(fontSize * 0.42) : fontSize,
                letterSpacing: l.small ? "0.34em" : "0.14em",
                textTransform: l.small ? "uppercase" : "none",
                lineHeight: l.small ? 1.2 : 1.12,
                marginTop: l.small ? 40 : 0,
                color: l.gold ? C.goldBright : C.ivory,
                textShadow: "0 2px 28px rgba(0,0,0,0.85), 0 0 2px rgba(0,0,0,0.6)",
                whiteSpace: "nowrap",
              }}
            >
              {l.text}
            </div>
          );
        })}
      </div>
      <div style={{ position: "absolute", inset: 0, height: HEIGHT }} />
    </AbsoluteFill>
  );
};
