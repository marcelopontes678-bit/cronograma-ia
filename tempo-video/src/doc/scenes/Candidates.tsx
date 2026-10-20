import { AbsoluteFill, Img, staticFile } from "remotion";
import { WIDTH } from "../../config";
import { SANS } from "../../fonts";
import { CANDIDATES, PROPOSALS_NOTE } from "../facts";
import { PHOTOS } from "../media";
import { D, Reveal, Stamp, T, eo, iv, sec } from "../ui";

const START = 13;

/** Foto de arquivo licenciada, se fornecida; senão um espaço claramente identificado como pendente. */
const PhotoSlot: React.FC<{ id: "flavio" | "lula"; f: number; initials: string }> = ({ id, f, initials }) => {
  const ph = PHOTOS[id];
  const kb = 1.06 + 0.06 * iv(f, [0, 250], [0, 1]);
  return (
    <div style={{ position: "relative", width: 236, height: 300, overflow: "hidden", borderRadius: 6, background: D.graphite2, border: `2px solid ${D.line}`, flexShrink: 0 }}>
      {ph.file ? (
        <>
          <Img src={staticFile(ph.file)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) contrast(1.05)", transform: `scale(${kb})` }} />
          <div style={{ position: "absolute", left: 8, right: 8, bottom: 6, fontSize: 12, color: "#ddd", textShadow: "0 1px 4px #000" }}>{ph.credit}</div>
        </>
      ) : (
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 14, background: `repeating-linear-gradient(135deg, ${D.graphite2} 0 14px, #1f2226 14px 28px)` }}>
          <div style={{ fontSize: 76, fontWeight: 900, color: "#4a4f56", letterSpacing: "-0.04em" }}>{initials}</div>
          <div style={{ fontSize: 15, fontWeight: 800, letterSpacing: "0.16em", color: D.muted, textAlign: "center", lineHeight: 1.4 }}>
            FOTO DE ARQUIVO
            <br />
            PENDENTE
          </div>
        </div>
      )}
    </div>
  );
};

const Card: React.FC<{ f: number; c: (typeof CANDIDATES)[number]; top: number; from: number }> = ({ f, c, top, from }) => {
  const g = (s: number) => sec(s - START);
  const p = iv(f, [g(13.3), g(13.3) + 16], [0, 1], eo); // mesmo instante para os dois
  const line = (i: number) => iv(f, [g(14.3 + i * 0.35), g(14.3 + i * 0.35) + 10], [0, 1], eo);
  const initials = c.id === "lula" ? "LULA" : "FB";
  return (
    <div
      style={{
        position: "absolute",
        left: 60,
        width: WIDTH - 120,
        top,
        padding: 26,
        display: "flex",
        gap: 26,
        background: "rgba(20,22,25,0.92)",
        border: `1px solid ${D.line}`,
        borderRadius: 10,
        fontFamily: SANS,
        color: D.white,
        transform: `translateX(${(1 - p) * from}px)`,
        opacity: p,
        boxShadow: "0 30px 60px rgba(0,0,0,0.5)",
      }}
    >
      <PhotoSlot id={c.id as "flavio" | "lula"} f={f} initials={initials} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 34, fontWeight: 800, lineHeight: 1.1 }}>{c.name}</div>
        <div style={{ fontSize: 21, color: D.muted, marginTop: 6 }}>
          {c.party} · {c.role}
        </div>
        <div style={{ fontSize: 21, marginTop: 8 }}>
          1º turno: <b style={{ fontVariantNumeric: "tabular-nums" }}>{c.firstRound}</b>
        </div>
        <div style={{ height: 1, background: D.line, margin: "14px 0 12px" }} />
        <div style={{ fontSize: 14, fontWeight: 800, letterSpacing: "0.2em", color: D.yellow, opacity: line(0) }}>HISTÓRICO JUDICIAL VERIFICADO</div>
        <div style={{ fontSize: 21, fontWeight: 700, marginTop: 6, opacity: line(0) }}>{c.caseTitle}</div>
        {c.caseLines.map((l, i) => (
          <div key={l} style={{ fontSize: 21, color: "#c9ccd0", lineHeight: 1.3, opacity: line(i + 1) }}>
            {l}
          </div>
        ))}
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 12, height: 50 }}>
          <Stamp f={f} at={g(T.marks.stamp3)} text={c.status} color={D.white} size={22} rot={-4} blend={false} />
          <span style={{ fontSize: 18, color: D.muted, opacity: line(4) }}>{c.defense}</span>
        </div>
        <div style={{ fontSize: 15, color: "#8a9096", marginTop: 4, opacity: line(4) }}>{c.source}</div>
      </div>
    </div>
  );
};

export const Candidates: React.FC<{ f: number }> = ({ f }) => {
  const g = (s: number) => sec(s - START);
  const scan = (f % 90) / 90;
  return (
    <AbsoluteFill style={{ background: D.black }}>
      {/* fundo: grade de arquivo em movimento lento */}
      <AbsoluteFill style={{ opacity: 0.22, backgroundImage: `linear-gradient(${D.line} 1px, transparent 1px), linear-gradient(90deg, ${D.line} 1px, transparent 1px)`, backgroundSize: "60px 60px", transform: `translateY(${-f * 0.4}px)` }} />
      <AbsoluteFill style={{ background: `linear-gradient(180deg, rgba(255,255,255,0) ${scan * 100 - 6}%, rgba(255,255,255,0.05) ${scan * 100}%, rgba(255,255,255,0) ${scan * 100 + 6}%)` }} />
      <div style={{ position: "absolute", left: 72, right: 72, top: 300, fontFamily: SANS, color: D.white }}>
        <Reveal f={f} at={g(13.05)} dur={14}>
          <div style={{ fontSize: 76, fontWeight: 900, letterSpacing: "-0.03em", lineHeight: 1 }}>
            PROPOSTAS E <span style={{ color: D.yellow }}>HISTÓRICOS</span>
          </div>
        </Reveal>
        <div style={{ fontSize: 19, color: D.muted, marginTop: 14, opacity: iv(f, [g(13.4), g(13.8)], [0, 1]) }}>Candidatos no 2º turno · ordem do 1º turno · mesmo formato para ambos</div>
      </div>
      <Card f={f} c={CANDIDATES[0]} top={470} from={-1100} />
      <Card f={f} c={CANDIDATES[1]} top={880} from={1100} />
      <div style={{ position: "absolute", left: 72, right: 72, top: 1300, fontFamily: SANS, fontSize: 19, color: D.muted, textAlign: "center", opacity: iv(f, [g(18.5), g(19)], [0, 1]) }}>{PROPOSALS_NOTE}</div>
    </AbsoluteFill>
  );
};
