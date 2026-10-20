import { AbsoluteFill } from "remotion";
import { HEIGHT, WIDTH } from "../../config";
import { SANS } from "../../fonts";
import { ELECTION } from "../facts";
import { D, Reveal, eo, iv } from "../ui";

const PLINTH_Y = 1180;

/** Ilustração original do Congresso Nacional (silhueta estilizada, vista da Esplanada). */
const Congress: React.FC<{ f: number; mirror?: boolean }> = ({ f, mirror }) => {
  const winOn = (i: number) => ((i * 7919) % 100) / 100 > 0.42;
  const flick = (i: number) => 0.75 + 0.25 * Math.sin(f / (9 + (i % 5)) + i);
  const towers = [492, 588];
  return (
    <g transform={mirror ? `translate(0 ${PLINTH_Y * 2 + 60}) scale(1 -1)` : undefined}>
      <defs>
        <linearGradient id="tw" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#2b3138" />
          <stop offset="0.5" stopColor="#3a424b" />
          <stop offset="1" stopColor="#1b1f24" />
        </linearGradient>
        <radialGradient id="domeG" cx="0.4" cy="0.2" r="0.9">
          <stop offset="0" stopColor="#f4f3ef" />
          <stop offset="1" stopColor="#8d96a1" />
        </radialGradient>
        <linearGradient id="bowlG" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#f4f3ef" />
          <stop offset="1" stopColor="#7d8692" />
        </linearGradient>
      </defs>
      {/* torres gêmeas + passarela */}
      {towers.map((x, ti) => (
        <g key={x}>
          <rect x={x - 38} y={590} width={76} height={PLINTH_Y - 590} fill="url(#tw)" />
          {Array.from({ length: 26 }).map((_, r) =>
            [0, 1, 2].map((c) => {
              const i = ti * 1000 + r * 3 + c;
              return winOn(i) ? <rect key={i} x={x - 30 + c * 22} y={600 + r * 22} width={14} height={8} fill="#ffe7b0" opacity={0.55 * flick(i)} /> : null;
            }),
          )}
        </g>
      ))}
      <rect x={454} y={720} width={172} height={14} fill="#2b3138" />
      {/* plataforma */}
      <rect x={-60} y={PLINTH_Y} width={WIDTH + 120} height={40} fill="#cfd3d8" />
      <rect x={-60} y={PLINTH_Y + 40} width={WIDTH + 120} height={10} fill="#5e6670" />
      {Array.from({ length: 24 }).map((_, i) => (
        <rect key={i} x={i * 48 - 20} y={PLINTH_Y + 50} width={6} height={70} fill="#1d2126" />
      ))}
      {/* cúpula do Senado (convexa, à esquerda) */}
      <path d={`M190,${PLINTH_Y} A 120 78 0 0 1 430,${PLINTH_Y} Z`} fill="url(#domeG)" />
      {/* cuia da Câmara (côncava, à direita) */}
      <path d={`M610,${PLINTH_Y - 95} Q 790,${PLINTH_Y + 40} 970,${PLINTH_Y - 95} L 940,${PLINTH_Y - 95} Q 790,${PLINTH_Y - 20} 640,${PLINTH_Y - 95} Z`} fill="#c7ccd2" />
      <path d={`M640,${PLINTH_Y - 95} Q 790,${PLINTH_Y - 20} 940,${PLINTH_Y - 95} Q 790,${PLINTH_Y - 70} 640,${PLINTH_Y - 95} Z`} fill="#8b939d" />
      <path d={`M700,${PLINTH_Y - 30} L 880,${PLINTH_Y - 30} L 860,${PLINTH_Y} L 720,${PLINTH_Y} Z`} fill="url(#bowlG)" />
    </g>
  );
};

export const Brasilia: React.FC<{ f: number }> = ({ f }) => {
  const p = iv(f, [0, 165], [0, 1]);
  // paralaxe: céu quase parado, prédio aproxima, primeiro plano corre mais
  const sky = `translate(0 ${p * -8}px) scale(${1 + p * 0.02})`;
  const mid = `scale(${1 + p * 0.1})`;
  const fg = `translate(0 ${p * 30}px) scale(${1 + p * 0.18})`;
  const resultsIn = iv(f, [84, 100], [0, 1], eo);
  return (
    <AbsoluteFill style={{ background: D.black }}>
      <AbsoluteFill style={{ transform: sky, transformOrigin: "50% 60%" }}>
        <AbsoluteFill style={{ background: "linear-gradient(180deg, #030407 0%, #08101a 45%, #1b2230 62%, #3a2f2a 70%, #0a0b0d 74%)" }} />
        <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
          {Array.from({ length: 70 }).map((_, i) => {
            const x = (i * 157.3) % WIDTH;
            const y = (i * 97.7) % 820;
            return <circle key={i} cx={x} cy={y} r={i % 9 === 0 ? 1.8 : 1} fill="#fff" opacity={0.2 + 0.4 * Math.abs(Math.sin(f / 20 + i))} />;
          })}
        </svg>
        {/* brilho da cidade no horizonte */}
        <div style={{ position: "absolute", left: -200, right: -200, top: 1020, height: 260, background: "radial-gradient(ellipse 50% 50% at 50% 50%, rgba(255,190,120,0.25), rgba(0,0,0,0) 70%)" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ transform: mid, transformOrigin: "50% 62%" }}>
        <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
          <defs>
            <filter id="poolRipple">
              <feTurbulence type="fractalNoise" baseFrequency={`0.006 ${0.05 + 0.004 * Math.sin(f / 18)}`} numOctaves={2} seed={3} />
              <feDisplacementMap in="SourceGraphic" scale="18" xChannelSelector="R" yChannelSelector="G" />
              <feGaussianBlur stdDeviation="2" />
            </filter>
          </defs>
          {/* holofotes de baixo para cima */}
          {[300, 540, 790].map((x, i) => (
            <polygon key={i} points={`${x - 30},${PLINTH_Y} ${x + 30},${PLINTH_Y} ${x + 120},560 ${x - 120},560`} fill="rgba(200,215,235,0.05)" />
          ))}
          <Congress f={f} />
          {/* espelho d'água */}
          <rect x={0} y={PLINTH_Y + 120} width={WIDTH} height={HEIGHT} fill="#05070a" />
          <g filter="url(#poolRipple)" opacity={0.42}>
            <Congress f={f} mirror />
          </g>
          <rect x={0} y={PLINTH_Y + 120} width={WIDTH} height={HEIGHT} fill="url(#poolFade)" />
          <defs>
            <linearGradient id="poolFade" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#05070a" stopOpacity="0.1" />
              <stop offset="0.5" stopColor="#05070a" stopOpacity="0.9" />
            </linearGradient>
          </defs>
        </svg>
      </AbsoluteFill>
      {/* primeiro plano: postes da Esplanada fora de foco */}
      <AbsoluteFill style={{ transform: fg, transformOrigin: "50% 80%", filter: "blur(5px)" }}>
        <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
          {[-1, 1].map((s) =>
            [0, 1, 2].map((k) => {
              const x = 540 + s * (360 + k * 170);
              const y = 1380 - k * 70;
              return (
                <g key={`${s}${k}`}>
                  <rect x={x - 4} y={y} width={8} height={600} fill="#0b0c0e" />
                  <circle cx={x} cy={y} r={26 - k * 5} fill="#ffd9a0" opacity={0.85} />
                  <circle cx={x} cy={y} r={90 - k * 20} fill="#ffd9a0" opacity={0.12} />
                </g>
              );
            }),
          )}
        </svg>
      </AbsoluteFill>

      {/* título + dados reais do 1º turno (no lugar de manchetes) */}
      <div style={{ position: "absolute", left: 72, right: 72, top: 330, fontFamily: SANS, color: D.white }}>
        <Reveal f={f} at={10}>
          <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: "0.32em", color: D.muted }}>ELEIÇÃO PRESIDENCIAL</div>
        </Reveal>
        <Reveal f={f} at={16} style={{ marginTop: 8 }}>
          <div style={{ fontSize: 150, fontWeight: 900, letterSpacing: "-0.04em", lineHeight: 0.95 }}>
            BRASIL <span style={{ color: D.yellow }}>2026</span>
          </div>
        </Reveal>
        <div style={{ height: 4, width: `${iv(f, [24, 46], [0, 100], eo)}%`, background: `linear-gradient(90deg, ${D.green}, ${D.yellow})`, marginTop: 22 }} />
        <div style={{ marginTop: 26, padding: "18px 24px 20px", background: "rgba(7,7,8,0.78)", border: `1px solid ${D.line}`, borderRadius: 8, backdropFilter: "blur(6px)", opacity: resultsIn, transform: `translateY(${(1 - resultsIn) * 16}px)` }}>
          <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: "0.18em", color: D.muted }}>1º TURNO · {ELECTION.firstRound}</div>
          {ELECTION.results.map((r, i) => (
            <div key={r.name} style={{ display: "flex", justifyContent: "space-between", fontSize: 34, fontWeight: 600, marginTop: 10 }}>
              <span>
                {r.name} <span style={{ color: D.muted, fontWeight: 500 }}>({r.party})</span>
              </span>
              <span style={{ fontVariantNumeric: "tabular-nums" }}>{r.pct}</span>
            </div>
          ))}
          <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: "0.18em", color: D.yellow, marginTop: 14 }}>2º TURNO · {ELECTION.runoff}</div>
          <div style={{ fontSize: 18, color: D.muted, marginTop: 8 }}>{ELECTION.source}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
