import { AbsoluteFill } from "remotion";
import { HEIGHT, WIDTH } from "../../config";
import { SANS, SERIF } from "../../fonts";
import { CASES, STATUS_LEGEND } from "../facts";
import { D, Reveal, Stamp, T, eo, iv, sec } from "../ui";

const START = 5; // segundos (corte da cena)

/** Folha de papel genérica (sem conteúdo real legível): linhas e tarjas. */
const Sheet: React.FC<{ seed: number }> = ({ seed }) => (
  <div style={{ width: 420, height: 560, background: "#d9d7d0", borderRadius: 4, padding: 34, boxShadow: "0 30px 60px rgba(0,0,0,0.6)" }}>
    {Array.from({ length: 16 }).map((_, i) => {
      const w = 40 + ((seed * 37 + i * 53) % 55);
      const redacted = (seed + i) % 5 === 0;
      return <div key={i} style={{ height: redacted ? 16 : 7, width: `${w}%`, background: redacted ? "#111" : "#9a978f", marginBottom: redacted ? 12 : 21, borderRadius: 2 }} />;
    })}
  </div>
);

const CaseCard: React.FC<{ f: number; c: (typeof CASES)[number]; at: number; stampAt: number; rot: number; x: number }> = ({ f, c, at, stampAt, rot, x }) => {
  const p = iv(f, [at, at + 14], [0, 1], eo);
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: 700,
        width: 446,
        padding: "30px 30px 26px",
        background: D.paper,
        color: D.ink,
        borderRadius: 6,
        fontFamily: SANS,
        boxShadow: "0 40px 80px rgba(0,0,0,0.65)",
        transform: `translateY(${(1 - p) * 520}px) rotate(${rot * (0.4 + 0.6 * p)}deg)`,
        opacity: p,
      }}
    >
      <div style={{ fontSize: 15, fontWeight: 800, letterSpacing: "0.22em", color: "#6c6f74" }}>REGISTRO PÚBLICO</div>
      <div style={{ fontSize: 27, fontWeight: 900, lineHeight: 1.12, marginTop: 10 }}>{c.title}</div>
      <div style={{ height: 2, background: D.ink, opacity: 0.15, margin: "14px 0" }} />
      {c.lines.map((l) => (
        <div key={l} style={{ fontFamily: SERIF, fontSize: 27, lineHeight: 1.25 }}>
          {l}
        </div>
      ))}
      <div style={{ marginTop: 22, height: 60 }}>
        <Stamp f={f} at={stampAt} text={c.status} size={28} rot={-6} />
      </div>
      <div style={{ fontSize: 17, color: "#55595e", marginTop: 6 }}>{c.statusNote}</div>
      <div style={{ fontSize: 15, color: "#6c6f74", marginTop: 12, fontWeight: 600 }}>{c.source}</div>
    </div>
  );
};

export const Documents: React.FC<{ f: number }> = ({ f }) => {
  const g = (s: number) => sec(s - START); // segundos globais → frame local
  const M = T.marks;
  const drift = f / 240;
  const words = ["CORRUPÇÃO.", "RESPONSABILIDADE.", "TRANSPARÊNCIA."];
  const titleUp = iv(f, [g(6.9), g(7.4)], [0, 1], eo);
  return (
    <AbsoluteFill style={{ background: D.graphite }}>
      {/* mesa: papéis em três profundidades (paralaxe) */}
      <AbsoluteFill style={{ filter: "blur(6px)", opacity: 0.45 }}>
        {[0, 1, 2, 3].map((i) => (
          <div key={i} style={{ position: "absolute", left: [-120, 640, 80, 700][i], top: [120, 260, 1240, 1300][i], transform: `rotate(${[-12, 9, 6, -8][i]}deg) translate(${drift * 60 * (i % 2 ? 1 : -1)}px, ${drift * -30}px) scale(0.9)` }}>
            <Sheet seed={i + 3} />
          </div>
        ))}
      </AbsoluteFill>
      <AbsoluteFill style={{ filter: "blur(1.5px)", opacity: 0.6 }}>
        {[0, 1].map((i) => (
          <div key={i} style={{ position: "absolute", left: [600, -60][i], top: [520, 860][i], transform: `rotate(${[14, -10][i]}deg) translate(${drift * 120 * (i ? 1 : -1)}px, ${drift * -60}px) scale(0.75)` }}>
            <Sheet seed={i + 9} />
          </div>
        ))}
      </AbsoluteFill>
      {/* luz de mesa vinda de cima */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 60% 45% at 50% 52%, rgba(255,240,210,0.16), rgba(0,0,0,0) 70%)" }} />

      {/* título em três palavras, depois sobe */}
      <div style={{ position: "absolute", left: 72, right: 72, top: 360 - titleUp * 40, fontFamily: SANS, color: D.white, transform: `scale(${1 - 0.28 * titleUp})`, transformOrigin: "0 0" }}>
        {words.map((w, i) => (
          <Reveal key={w} f={f} at={g(5.2 + i * 0.5)} dur={12}>
            <div style={{ fontSize: 92, fontWeight: 900, letterSpacing: "-0.03em", lineHeight: 1.0, color: i === 2 ? D.yellow : D.white }}>{w}</div>
          </Reveal>
        ))}
      </div>

      <CaseCard f={f} c={CASES[0]} at={g(M.card1)} stampAt={g(M.stamp1)} rot={-3} x={70} />
      <CaseCard f={f} c={CASES[1]} at={g(M.card2)} stampAt={g(M.stamp2)} rot={3} x={WIDTH - 70 - 446} />

      {/* escala de status jurídico: diferença entre investigar, acusar, condenar, anular e arquivar */}
      <div style={{ position: "absolute", left: 50, right: 50, top: 1140, padding: "18px 22px 12px", borderRadius: 8, background: `rgba(7,7,8,${0.82 * iv(f, [g(M.legend[0]) - 4, g(M.legend[0]) + 6], [0, 1])})`, fontFamily: SANS }}>
        <Reveal f={f} at={g(M.legend[0]) - 4} dur={10}>
          <div style={{ fontSize: 18, fontWeight: 800, letterSpacing: "0.24em", color: D.muted, marginBottom: 10 }}>O QUE CADA TERMO SIGNIFICA</div>
        </Reveal>
        {STATUS_LEGEND.map((s, i) => {
          const p = iv(f, [g(M.legend[i]), g(M.legend[i]) + 8], [0, 1], eo);
          return (
            <div key={s.status} style={{ display: "flex", alignItems: "baseline", gap: 18, opacity: p, transform: `translateX(${(1 - p) * -40}px)`, marginBottom: 6 }}>
              <span style={{ width: 210, fontSize: 22, fontWeight: 900, letterSpacing: "0.06em", color: i % 2 ? D.yellow : D.white }}>{s.status}</span>
              <span style={{ fontSize: 22, color: "#c9ccd0" }}>{s.meaning}</span>
            </div>
          );
        })}
      </div>
      <div style={{ position: "absolute", inset: 0, width: WIDTH, height: HEIGHT, pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
