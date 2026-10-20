import { AbsoluteFill, Audio, Sequence, spring, staticFile, useCurrentFrame } from "remotion";
import { HEIGHT, WIDTH } from "../config";
import { SANS } from "../fonts";
import { Grain } from "../components/Grain";
import { ClockScene } from "../scenes/ClockScene";
import { TokyoNightOpus } from "../tokyo/TokyoNightOpus";
import { CX, CY, P, expoIn, expoOut, iv } from "./lib";
import { CubePiece, DotPiece, GooPiece, MorphPiece, ParticlesPiece, TypePiece } from "./pieces";

export const REEL_DURATION = 450; // 15 s · 120 BPM · cada seção começa numa batida (múltiplo de 15 frames)

const SECTIONS = [
  { from: 0, label: "01 — TIMING", dark: true },
  { from: 45, label: "02 — TIPOGRAFIA CINÉTICA", dark: false },
  { from: 105, label: "03 — MORPH", dark: false },
  { from: 165, label: "04 — PARTÍCULAS", dark: true },
  { from: 225, label: "05 — 3D", dark: true },
  { from: 285, label: "06 — FLUIDOS", dark: true },
  { from: 345, label: "07 — REPERTÓRIO", dark: false },
  { from: 390, label: "", dark: false },
];

const sectionAt = (f: number) => {
  let s = 0;
  SECTIONS.forEach((x, i) => f >= x.from && (s = i));
  return s;
};

// ---------------------------------------------------------------- HUD (rótulo, timecode, marcas de corte)
const Hud: React.FC<{ f: number }> = ({ f }) => {
  const si = sectionAt(f);
  const s = SECTIONS[si];
  if (!s.label) return null;
  const local = f - s.from;
  const col = s.dark ? P.paper : P.ink;
  const reveal = iv(local, [0, 8], [1, 0], expoOut);
  const sec = Math.floor(f / 30);
  const fr = f % 30;
  const tc = `00:00:${String(sec).padStart(2, "0")}:${String(fr).padStart(2, "0")}`;
  const mark = (x: number, y: number, sx: number, sy: number) => (
    <path d={`M${x},${y + 34 * sy} L${x},${y} L${x + 34 * sx},${y}`} fill="none" stroke={col} strokeWidth={3} opacity={0.6} />
  );
  return (
    <AbsoluteFill style={{ pointerEvents: "none", fontFamily: SANS, color: col }}>
      <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
        {mark(72, 290, 1, 1)}
        {mark(WIDTH - 72, 290, -1, 1)}
        {mark(72, 1480, 1, -1)}
        {mark(WIDTH - 72, 1480, -1, -1)}
      </svg>
      <div style={{ position: "absolute", left: 120, top: 318, height: 36, overflow: "hidden" }}>
        <div style={{ fontWeight: 700, fontSize: 28, letterSpacing: "0.16em", transform: `translateY(${reveal * 40}px)` }}>{s.label}</div>
      </div>
      <div style={{ position: "absolute", right: 120, top: 318, fontWeight: 600, fontSize: 28, letterSpacing: "0.08em", fontVariantNumeric: "tabular-nums", opacity: 0.75 }}>{tc}</div>
      <div style={{ position: "absolute", left: 120, top: 1420, fontWeight: 700, fontSize: 24, letterSpacing: "0.2em", opacity: 0.75 }}>SHOWREEL · 2026</div>
      <div style={{ position: "absolute", right: 120, top: 1420, fontWeight: 700, fontSize: 24, letterSpacing: "0.2em", opacity: 0.75, fontVariantNumeric: "tabular-nums" }}>120 BPM</div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- 07 · REPERTÓRIO (mosaico)
// As cenas embutidas usam o frame GLOBAL do reel: o `from` desloca para o trecho escolhido de cada uma.
const Panel: React.FC<{ i: number; f: number; children: React.ReactNode }> = ({ i, f, children }) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const w = 468;
  const h = 318;
  const x = CX - w - 12 + col * (w + 24);
  const y = 392 + row * (h + 24);
  const pop = spring({ frame: f - i * 3, fps: 30, config: { damping: 13, stiffness: 180, mass: 0.6 } });
  const s = Math.max(w / WIDTH, h / HEIGHT); // conteúdo 1080x1920 cobrindo o painel (corte central)
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h, borderRadius: 30, overflow: "hidden", transform: `scale(${0.6 + 0.4 * pop})`, opacity: pop, background: P.ink, boxShadow: "0 30px 60px rgba(0,0,0,0.25)" }}>
      <div style={{ position: "absolute", left: -(WIDTH * s - w) / 2, top: -(HEIGHT * s - h) / 2, width: WIDTH, height: HEIGHT, transform: `scale(${s})`, transformOrigin: "0 0" }}>{children}</div>
    </div>
  );
};

const Range: React.FC<{ f: number }> = ({ f }) => {
  const collapse = iv(f, [33, 45], [0, 1], expoIn);
  return (
    <AbsoluteFill style={{ background: P.orange }}>
      <AbsoluteFill style={{ transform: `scale(${1 - collapse}) rotate(${collapse * 25}deg)`, transformOrigin: `${CX}px ${CY}px` }}>
        <Panel i={0} f={f}>
          <Sequence from={345 - 150} layout="none">
            <TokyoNightOpus embedded />
          </Sequence>
        </Panel>
        <Panel i={1} f={f}>
          <Sequence from={345 - 70} layout="none">
            <ClockScene duration={150} />
          </Sequence>
        </Panel>
        <Panel i={2} f={f}>
          <MorphPiece f={18 + ((f * 1.6) % 40)} />
        </Panel>
        <Panel i={3} f={f}>
          <CubePiece f={20 + f} fly={false} bg={P.blue} />
        </Panel>
        <Panel i={4} f={f}>
          <GooPiece f={14 + f} flood={false} id="gooMini" />
        </Panel>
        <Panel i={5} f={f}>
          <TypePiece f={42} />
        </Panel>
      </AbsoluteFill>
      <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
        <circle cx={CX} cy={CY} r={28 * collapse} fill={P.ink} />
      </svg>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- 08 · ASSINATURA
const End: React.FC<{ f: number }> = ({ f }) => {
  const dot = spring({ frame: f, fps: 30, config: { damping: 10, stiffness: 240, mass: 0.5 } });
  const line = iv(f, [6, 18], [0, 1], expoOut);
  const word = "CLAUDE";
  const sub = iv(f, [20, 32], [0, 1], expoOut);
  const period = spring({ frame: f - 34, fps: 30, config: { damping: 8, stiffness: 300, mass: 0.4 } });
  return (
    <AbsoluteFill style={{ background: P.paper, fontFamily: SANS, color: P.ink }}>
      {/* o ponto do início volta (fecha o ciclo) e vira a linha-base */}
      <div style={{ position: "absolute", left: CX - Math.max(28, 410 * line), top: CY + 40 - 7, width: Math.max(56, 820 * line), height: line > 0 ? 14 : 56, marginTop: line > 0 ? 0 : -21, borderRadius: 28, background: P.ink, transform: `scale(${line > 0 ? 1 : dot})` }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: CY - 210, height: 240, overflow: "hidden", display: "flex", justifyContent: "center", alignItems: "flex-end" }}>
        {Array.from(word).map((c, i) => {
          const u = iv(f, [10 + i * 1.6, 24 + i * 1.6], [0, 1], expoOut);
          return (
            <span key={i} style={{ display: "inline-block", fontWeight: 900, fontSize: 210, lineHeight: 1, letterSpacing: "-0.04em", transform: `translateY(${(1 - u) * 240}px)` }}>
              {c}
            </span>
          );
        })}
        <span style={{ display: "inline-block", width: 52, height: 52, borderRadius: 26, background: P.orange, marginLeft: 10, marginBottom: 18, transform: `scale(${period})` }} />
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: CY + 90, textAlign: "center", opacity: sub, transform: `translateY(${(1 - sub) * 20}px)` }}>
        <div style={{ fontWeight: 800, fontSize: 40, letterSpacing: "0.42em", marginRight: "-0.42em" }}>MOTION DESIGN</div>
        <div style={{ fontWeight: 500, fontSize: 28, letterSpacing: "0.04em", marginTop: 26, opacity: 0.7 }}>100% código · React + Remotion · 450 quadros</div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- montagem
export const Showreel: React.FC = () => {
  const f = useCurrentFrame();
  const si = sectionAt(f);
  const local = f - SECTIONS[si].from;
  return (
    <AbsoluteFill style={{ background: P.ink }}>
      {si === 0 && <DotPiece f={local} />}
      {si === 1 && <TypePiece f={local} />}
      {si === 2 && <MorphPiece f={local} />}
      {si === 3 && <ParticlesPiece f={local} />}
      {si === 4 && <CubePiece f={local} />}
      {si === 5 && <GooPiece f={local} />}
      {si === 6 && <Range f={local} />}
      {si === 7 && <End f={local} />}
      <Hud f={f} />
      <Grain opacity={0.07} />
      <Audio src={staticFile("reel/track.mp3")} volume={0.85} />
    </AbsoluteFill>
  );
};

void expoOut;
