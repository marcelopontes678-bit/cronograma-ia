import { AbsoluteFill } from "remotion";
import { HEIGHT, WIDTH } from "../../config";
import { SANS } from "../../fonts";
import { WalkingMan } from "../../components/WalkingMan";
import { DISCLAIMER, FINAL_SOURCES } from "../facts";
import { D, Reveal, T, eo, ei, iv, sec } from "../ui";

const START = 21;

/** Bandeira do Brasil (desenho geométrico) tremulando: faixas verticais deslocadas por uma onda. */
const Flag: React.FC<{ f: number; x: number; y: number; w: number }> = ({ f, x, y, w }) => {
  const h = w * 0.7;
  const slices = 28;
  const sw = w / slices;
  return (
    <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <clipPath id="flagClip">
          <rect x={0} y={0} width={w} height={h} />
        </clipPath>
        <g id="flagArt">
          <rect width={w} height={h} fill="#169b4a" />
          <polygon points={`${w * 0.085},${h / 2} ${w / 2},${h * 0.12} ${w * 0.915},${h / 2} ${w / 2},${h * 0.88}`} fill="#f5cf1f" />
          <circle cx={w / 2} cy={h / 2} r={h * 0.25} fill="#1f3c8f" />
          <path d={`M ${w / 2 - h * 0.25},${h * 0.5} Q ${w / 2},${h * 0.38} ${w / 2 + h * 0.25},${h * 0.55}`} fill="none" stroke="#fff" strokeWidth={h * 0.04} />
        </g>
      </defs>
      <line x1={x} y1={y - 10} x2={x} y2={y + h * 2.6} stroke="#1a1410" strokeWidth={8} />
      {Array.from({ length: slices }).map((_, i) => {
        const u = i / slices;
        const dy = Math.sin(u * 6 - f / 6) * 14 * u;
        const shade = 0.82 + 0.18 * Math.cos(u * 6 - f / 6);
        return (
          <svg key={i} x={x + i * sw} y={y + dy} width={sw + 1} height={h} viewBox={`${i * sw} 0 ${sw + 1} ${h}`} style={{ overflow: "hidden", filter: `brightness(${shade})` }}>
            <use href="#flagArt" />
          </svg>
        );
      })}
    </svg>
  );
};

/** Urna eletrônica (desenho original, tela neutra: nenhum número de candidato). */
const Urna: React.FC<{ f: number; confirmAt: number }> = ({ f, confirmAt }) => {
  const pressed = iv(f, [confirmAt - 3, confirmAt, confirmAt + 4], [0, 1, 0]);
  const fim = f >= confirmAt + 2;
  const keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", ""];
  const fingerP = iv(f, [confirmAt - 18, confirmAt], [0, 1], eo) * (1 - iv(f, [confirmAt + 4, confirmAt + 12], [0, 1], eo));
  return (
    <div style={{ position: "absolute", left: 90, top: 560, width: 900, height: 700, borderRadius: 26, background: "linear-gradient(180deg, #d8d4ca, #b9b4a8)", boxShadow: "0 50px 100px rgba(0,0,0,0.7)", fontFamily: SANS }}>
      {/* tela */}
      <div style={{ position: "absolute", left: 40, top: 50, width: 470, height: 360, background: fim ? "#f2f2ec" : "#e9eadf", border: "10px solid #3b3a37", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
        {fim ? (
          <div style={{ fontSize: 130, fontWeight: 900, color: "#222", letterSpacing: "0.05em" }}>FIM</div>
        ) : (
          <>
            <div style={{ fontSize: 22, color: "#333", letterSpacing: "0.1em" }}>SEU VOTO PARA</div>
            <div style={{ fontSize: 40, fontWeight: 800, color: "#222", marginTop: 6 }}>PRESIDENTE</div>
            <div style={{ display: "flex", gap: 12, marginTop: 26 }}>
              {[0, 1].map((i) => (
                <div key={i} style={{ width: 54, height: 70, border: "3px solid #333" }} />
              ))}
            </div>
          </>
        )}
      </div>
      {/* teclado */}
      <div style={{ position: "absolute", right: 40, top: 50, width: 330, height: 600, background: "#2c2b29", borderRadius: 12, padding: 22 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
          {keys.map((k, i) => (
            <div key={i} style={{ height: 82, borderRadius: 8, background: k ? "#1a1a1a" : "transparent", color: "#fff", fontSize: 40, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center" }}>
              {k}
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: 10, marginTop: 18 }}>
          <div style={{ flex: 1, height: 70, borderRadius: 8, background: "#f1f1ee", fontSize: 15, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center" }}>BRANCO</div>
          <div style={{ flex: 1, height: 70, borderRadius: 8, background: "#e8823a", fontSize: 15, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center" }}>CORRIGE</div>
          <div style={{ flex: 1.2, height: 84, marginTop: -14, borderRadius: 8, background: "#2aa04f", fontSize: 15, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${1 - 0.08 * pressed})`, boxShadow: `0 0 ${30 * pressed}px rgba(42,160,79,0.9)` }}>CONFIRMA</div>
        </div>
      </div>
      {/* dedo (silhueta) */}
      <div style={{ position: "absolute", left: 760, top: 480 + (1 - fingerP) * 420, width: 70, height: 300, borderRadius: 35, background: "linear-gradient(90deg, #2a1f1a, #4a3a30)", opacity: iv(fingerP, [0, 0.35], [0, 1]), transform: "rotate(-12deg)" }} />
    </div>
  );
};

export const Vote: React.FC<{ f: number }> = ({ f }) => {
  const g = (s: number) => sec(s - START);
  const M = T.marks;
  const toUrna = iv(f, [g(24.1), g(24.6)], [0, 1], eo);
  const pause = iv(f, [g(26.6), g(27.1)], [0, 1], ei); // escurece: pausa dramática
  const final = M.finalText;
  const sunset = `linear-gradient(180deg, #1b1430 0%, #4a2a3a 30%, #c46a3c 58%, #f0a85a 66%, #2a1a14 70%, #0d0a09 100%)`;
  return (
    <AbsoluteFill style={{ background: D.black }}>
      {/* plano 1: eleitores ao entardecer e bandeira */}
      <AbsoluteFill style={{ opacity: 1 - toUrna, transform: `scale(${1 + iv(f, [0, g(24.6)], [0, 0.08])})` }}>
        <AbsoluteFill style={{ background: sunset }} />
        <div style={{ position: "absolute", left: -100, right: -100, top: 900, height: 420, background: "radial-gradient(ellipse 45% 40% at 55% 50%, rgba(255,200,130,0.55), rgba(0,0,0,0) 70%)" }} />
        <Flag f={f} x={640} y={330} w={330} />
        <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
          <rect x={0} y={1290} width={WIDTH} height={630} fill="#0d0a09" />
          {/* prédio da seção eleitoral */}
          <rect x={60} y={1010} width={420} height={280} fill="#120d0b" />
          <rect x={210} y={1150} width={110} height={140} fill="#ffcf8a" opacity={0.85} />
          {Array.from({ length: 6 }).map((_, i) => {
            const speed = 0.9 + (i % 3) * 0.12;
            const x = 1180 - ((f * (2.4 + (i % 2) * 0.6) + i * 190) % 1250);
            return <WalkingMan key={i} x={x} y={1292} height={300 + (i % 3) * 30} phase={(f / 30) * speed + i * 0.3} coat={i % 2 === 0} fill="#0a0706" rim="#ffbf7a" rimOpacity={0.5} />;
          })}
        </svg>
      </AbsoluteFill>
      {/* plano 2: a urna */}
      <AbsoluteFill style={{ opacity: toUrna * (1 - pause), background: "#0c0d0f", transform: `scale(${1.04 - 0.04 * toUrna + iv(f, [g(24.6), g(26.6)], [0, 0.05])})` }}>
        <AbsoluteFill style={{ background: "radial-gradient(ellipse 60% 40% at 50% 45%, rgba(255,240,210,0.12), rgba(0,0,0,0) 70%)" }} />
        <Urna f={f} confirmAt={g(M.confirm)} />
      </AbsoluteFill>
      {/* texto final, depois da pausa */}
      <div style={{ position: "absolute", left: 72, right: 72, top: 700, fontFamily: SANS, color: D.white }}>
        <Reveal f={f} at={g(final)} dur={14}>
          <div style={{ fontSize: 110, fontWeight: 900, letterSpacing: "-0.035em", lineHeight: 0.98 }}>O PODER PASSA.</div>
        </Reveal>
        <Reveal f={f} at={g(final + 0.5)} dur={14}>
          <div style={{ fontSize: 110, fontWeight: 900, letterSpacing: "-0.035em", lineHeight: 0.98, color: D.yellow }}>OS FATOS PERMANECEM.</div>
        </Reveal>
        <div style={{ height: 4, width: `${iv(f, [g(final + 0.9), g(final + 1.5)], [0, 100], eo)}%`, background: `linear-gradient(90deg, ${D.green}, ${D.yellow})`, marginTop: 30 }} />
        <div style={{ fontSize: 20, color: D.muted, marginTop: 22, opacity: iv(f, [g(final + 1.1), g(final + 1.5)], [0, 1]) }}>{FINAL_SOURCES}</div>
        <div style={{ fontSize: 20, color: D.muted, marginTop: 6, opacity: iv(f, [g(final + 1.1), g(final + 1.5)], [0, 1]) }}>{DISCLAIMER}</div>
      </div>
    </AbsoluteFill>
  );
};
