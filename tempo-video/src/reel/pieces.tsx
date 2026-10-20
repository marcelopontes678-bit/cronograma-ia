import { AbsoluteFill, spring } from "remotion";
import { HEIGHT, WIDTH } from "../config";
import { SANS, SERIF } from "../fonts";
import { CX, CY, P, ShapeKind, V3, expoIn, expoOut, hash, inOut, iv, lerpPts, project, rotX, rotY, shapePoints, toPath } from "./lib";
import designPoints from "./data/designPoints.json";

const FPS = 30;
const Svg: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} style={{ position: "absolute", inset: 0 }}>
    {children}
  </svg>
);

// =================================================================== 01 · TIMING — o ponto que quica
/** Altura (px acima do centro) e fase do pulo: impactos em 0, 15 e 30 (batidas). */
const hop = (f: number) => {
  const seg = Math.floor(f / 15);
  const u = (f - seg * 15) / 15;
  const H = seg === 0 ? 320 : seg === 1 ? 190 : 0;
  return { y: H * 4 * u * (1 - u), vy: H * 4 * (1 - 2 * u), sinceImpact: f - seg * 15 };
};

export const DotPiece: React.FC<{ f: number }> = ({ f }) => {
  const pop = spring({ frame: f, fps: FPS, config: { damping: 9, stiffness: 260, mass: 0.5 } });
  const grow = iv(f, [31, 45], [0, 1], expoIn);
  const r0 = 28 * pop;
  const ghosts = [6, 4, 2].map((d) => {
    const g = hop(Math.max(0, Math.min(30, f - d)));
    return { y: CY - g.y, a: f < 30 ? 0.12 + (6 - d) * 0.04 : 0 };
  });
  const h = hop(Math.min(30, f));
  // compressão no impacto, estiramento proporcional à velocidade no ar
  const squash = Math.exp(-h.sinceImpact / 2.2) * (f > 2 && f <= 32 ? 1 : 0);
  const stretch = Math.min(0.35, Math.abs(h.vy) / 1400);
  const sx = 1 + 0.4 * squash - stretch * 0.5;
  const sy = 1 - 0.38 * squash + stretch;
  const r = r0 + grow * 2300;
  const cy = CY - h.y;
  return (
    <AbsoluteFill style={{ background: P.ink }}>
      <Svg>
        {ghosts.map((g, i) => (
          <circle key={i} cx={CX} cy={g.y} r={r0} fill={P.paper} opacity={g.a} />
        ))}
        {/* sombra de contato */}
        <ellipse cx={CX} cy={CY + 30} rx={34 * (1 - h.y / 500)} ry={6} fill={P.paper} opacity={0.18 * pop * (1 - grow)} />
        <ellipse cx={CX} cy={cy + r0 * (1 - sy)} rx={r * (grow > 0 ? 1 : sx)} ry={r * (grow > 0 ? 1 : sy)} fill={grow > 0.02 ? P.orange : P.paper} />
      </Svg>
    </AbsoluteFill>
  );
};

// =================================================================== 02 · TIPOGRAFIA CINÉTICA — MOTION → EMOTION
const LETTERS = ["M", "O", "T", "I", "O", "N"];

export const TypePiece: React.FC<{ f: number }> = ({ f }) => {
  const eIn = iv(f, [28, 40], [0, 1], expoOut); // entra o "E"
  const size = 218 - 28 * eIn;
  const exit = (i: number) => iv(f, [47 + i * 1.2, 58 + i * 1.2], [0, 1], expoIn);
  const circle = iv(f, [50, 60], [0, 1], expoOut);
  const kicker = iv(f, [8, 20], [0, 1], expoOut);
  const letter = (ch: string, i: number) => {
    const d = f - i * 2.2;
    const drop = spring({ frame: d, fps: FPS, config: { damping: 11, stiffness: 190, mass: 0.6 } });
    // squash "keyframado" no pouso (origem na base)
    const sy = iv(d, [4, 6.5, 9, 13], [1.18, 0.74, 1.08, 1]);
    const sx = 2 - sy;
    const ex = exit(i + 1);
    return (
      <span
        key={i}
        style={{
          display: "inline-block",
          transformOrigin: "50% 100%",
          transform: `translateY(${(1 - drop) * -1100 + ex * 1400}px) rotate(${ex * (i % 2 ? 24 : -18)}deg) scale(${sx}, ${sy})`,
        }}
      >
        {ch}
      </span>
    );
  };
  return (
    <AbsoluteFill style={{ background: P.orange }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 690, textAlign: "center", overflow: "hidden", height: 90 }}>
        <div style={{ fontFamily: SERIF, fontStyle: "italic", fontWeight: 500, fontSize: 76, color: P.ink, transform: `translateY(${(1 - kicker) * 90 + exit(0) * 90}px)` }}>
          motion is
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 790,
          display: "flex",
          justifyContent: "center",
          fontFamily: SANS,
          fontWeight: 900,
          fontSize: size,
          lineHeight: 1,
          letterSpacing: "-0.035em",
          color: P.ink,
        }}
      >
        <span style={{ display: "inline-block", overflow: "hidden", width: `${0.66 * eIn}em` }}>
          <span style={{ display: "inline-block", color: P.paper, transform: `translateX(${(1 - eIn) * -110}%) rotate(${(1 - eIn) * -30}deg) translateY(${exit(0) * 1400}px)` }}>E</span>
        </span>
        {LETTERS.map(letter)}
      </div>
      <Svg>
        <circle cx={CX} cy={CY} r={260 * circle} fill={P.ink} />
      </Svg>
    </AbsoluteFill>
  );
};

// =================================================================== 03 · MORPH
const KEYS: ShapeKind[] = ["circle", "square", "triangle", "star"];
const SHAPES = KEYS.map((k) => shapePoints(k, 260));

/** Forma no instante f: cada batida (15 frames) troca de forma com mola e gira 45°. */
export const morphAt = (f: number) => {
  const step = Math.max(0, Math.min(3, Math.floor(f / 15)));
  const local = f - step * 15;
  let pts = SHAPES[step];
  let rot = step * (Math.PI / 4);
  if (step > 0) {
    const s = spring({ frame: local, fps: FPS, config: { damping: 11, stiffness: 210, mass: 0.6 } });
    pts = lerpPts(SHAPES[step - 1], SHAPES[step], s);
    rot = (step - 1 + s) * (Math.PI / 4);
  }
  return { pts, rot };
};

export const MorphPiece: React.FC<{ f: number; bg?: string }> = ({ f, bg = P.paper }) => {
  const { pts, rot } = morphAt(f);
  const shatter = iv(f, [52, 60], [0, 1], expoIn);
  const orbitA = (f / 60) * Math.PI * 2 * 1.5;
  return (
    <AbsoluteFill style={{ background: bg }}>
      <Svg>
        {/* ecos (onion skin) em laranja: mostram o arco do movimento */}
        {[8, 6, 4, 2].map((d, i) => {
          const e = morphAt(Math.max(0, f - d));
          return <path key={d} d={toPath(e.pts, CX, CY, e.rot)} fill="none" stroke={P.orange} strokeWidth={3} opacity={0.15 + i * 0.12} />;
        })}
        <path d={toPath(pts, CX, CY, rot)} fill={P.ink} opacity={1 - shatter} transform={`translate(${CX} ${CY}) scale(${1 + shatter * 0.12}) translate(${-CX} ${-CY})`} />
        {/* ação secundária: satélite em órbita */}
        <circle cx={CX + Math.cos(orbitA) * 420} cy={CY + Math.sin(orbitA) * 420 * 0.35} r={16} fill={P.orange} opacity={1 - shatter} />
        <ellipse cx={CX} cy={CY} rx={420} ry={147} fill="none" stroke={P.ink} strokeOpacity={0.12 * (1 - shatter)} strokeWidth={2} strokeDasharray="4 10" />
      </Svg>
    </AbsoluteFill>
  );
};

// =================================================================== 04 · PARTÍCULAS → DESIGN
const NP = (designPoints as number[][]).length;
const ang = (x: number, y: number) => Math.atan2(y - CY, x - CX);
const TARGETS = [...(designPoints as number[][])].sort((a, b) => ang(a[0], a[1]) - ang(b[0], b[1]));
const STAR = (() => {
  const s = morphAt(59);
  const pts = shapePoints("star", 260, NP);
  return pts
    .map(([x, y]) => {
      const c = Math.cos(s.rot);
      const sn = Math.sin(s.rot);
      return [CX + x * c - y * sn, CY + x * sn + y * c];
    })
    .sort((a, b) => ang(a[0], a[1]) - ang(b[0], b[1]));
})();

export const ParticlesPiece: React.FC<{ f: number }> = ({ f }) => (
  <AbsoluteFill style={{ background: P.ink }}>
    <Svg>
      {STAR.map((s, i) => {
        const tgt = TARGETS[i];
        const h1 = hash(i, 1);
        const h2 = hash(i, 2);
        // A) explosão radial com redemoinho
        const ex = iv(f, [0, 16], [0, 1], expoOut);
        const a0 = ang(s[0], s[1]) + (h1 - 0.5) * 1.4 + ex * (h2 - 0.5) * 2;
        const dist = (260 + h2 * 700) * ex;
        let x = s[0] + Math.cos(a0) * dist;
        let y = s[1] + Math.sin(a0) * dist;
        // B) converge para a palavra, com atraso por partícula e trajetória curva
        const delay = h1 * 9;
        const c = iv(f, [14 + delay, 40 + delay * 0.5], [0, 1], inOut);
        const bend = Math.sin(Math.PI * c) * (h2 - 0.5) * 260;
        x = x + (tgt[0] - x) * c + bend;
        y = y + (tgt[1] - y) * c;
        // C) cintila parado; D) é sugada para o centro
        const jitter = f > 45 && f < 53 ? Math.sin(f * 0.9 + i) * 1.2 : 0;
        const suck = iv(f, [52 + h1 * 3, 60], [0, 1], expoIn);
        x = x + (CX - x) * suck + jitter;
        y = y + (CY - y) * suck;
        const orange = h2 > 0.82 || suck > 0.5;
        return <circle key={i} cx={x} cy={y} r={3.4 + (c > 0.98 ? 0.6 : 0)} fill={orange ? P.orange : P.paper} />;
      })}
    </Svg>
  </AbsoluteFill>
);

// =================================================================== 05 · 3D — cubo de cubos
type Face = { pts: [number, number][]; z: number; color: string };
const FACES: { n: V3; v: V3[] }[] = [
  { n: [0, 0, -1], v: [[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1]] },
  { n: [0, 0, 1], v: [[-1, -1, 1], [-1, 1, 1], [1, 1, 1], [1, -1, 1]] },
  { n: [-1, 0, 0], v: [[-1, -1, -1], [-1, 1, -1], [-1, 1, 1], [-1, -1, 1]] },
  { n: [1, 0, 0], v: [[1, -1, -1], [1, -1, 1], [1, 1, 1], [1, 1, -1]] },
  { n: [0, 1, 0], v: [[-1, 1, -1], [1, 1, -1], [1, 1, 1], [-1, 1, 1]] },
  { n: [0, -1, 0], v: [[-1, -1, -1], [-1, -1, 1], [1, -1, 1], [1, -1, -1]] },
];
const L: V3 = (() => {
  const v: V3 = [-0.5, 0.75, -0.55];
  const m = Math.hypot(...v);
  return [v[0] / m, v[1] / m, v[2] / m];
})();
const shade = (hex: string, k: number) => {
  const n = parseInt(hex.slice(1), 16);
  const r = ((n >> 16) & 255) * k;
  const g = ((n >> 8) & 255) * k;
  const b = (n & 255) * k;
  return `rgb(${Math.min(255, r) | 0},${Math.min(255, g) | 0},${Math.min(255, b) | 0})`;
};

export const CubePiece: React.FC<{ f: number; bg?: string; fly?: boolean }> = ({ f, bg = P.blue, fly = true }) => {
  const appear = spring({ frame: f, fps: FPS, config: { damping: 12, stiffness: 120, mass: 0.8 } });
  const spread =
    1 +
    0.95 * spring({ frame: f - 30, fps: FPS, config: { damping: 10, stiffness: 150, mass: 0.7 } }) -
    0.95 * spring({ frame: f - 45, fps: FPS, config: { damping: 14, stiffness: 160, mass: 0.7 } });
  const out = fly ? iv(f, [52, 60], [0, 1], expoIn) : 0;
  const yaw = (30 + f * 3.1) * (Math.PI / 180);
  const pitch = (-26 + 6 * Math.sin(f / 14)) * (Math.PI / 180);
  const unit = 1.45 * appear;
  const faces: Face[] = [];
  for (let ix = -1; ix <= 1; ix++)
    for (let iy = -1; iy <= 1; iy++)
      for (let iz = -1; iz <= 1; iz++) {
        const idx = (ix + 1) * 9 + (iy + 1) * 3 + (iz + 1);
        const color = ix === 0 && iz === 0 ? P.orange : iy === 1 ? P.paper : idx % 2 ? P.paper : "#cfd6ff";
        const c: V3 = [ix * spread * (1 + out * 2.5), iy * spread * (1 + out * 2.5), iz * spread * (1 + out * 2.5)];
        const hs = 0.46 * (1 - out * 0.6);
        for (const fc of FACES) {
          const nR = rotX(rotY(fc.n, yaw), pitch);
          if (nR[2] >= 0) continue; // face de costas para a câmera
          const vr = fc.v.map((v) => rotX(rotY([(c[0] + v[0] * hs) * unit, (c[1] + v[1] * hs) * unit, (c[2] + v[2] * hs) * unit], yaw), pitch));
          const lit = 0.38 + 0.72 * Math.max(0, -(nR[0] * L[0] + nR[1] * L[1] + nR[2] * L[2]) * -1 + 0.2);
          faces.push({ pts: vr.map((v) => project(v)), z: vr.reduce((s, v) => s + v[2], 0) / 4, color: shade(color, Math.min(1.08, lit)) });
        }
      }
  faces.sort((a, b) => b.z - a.z);
  return (
    <AbsoluteFill style={{ background: bg }}>
      <Svg>
        <ellipse cx={CX} cy={CY + 470} rx={420 * appear} ry={70 * appear} fill="#000" opacity={0.22 * (1 - out)} />
        {faces.map((fc, i) => (
          <polygon key={i} points={fc.pts.map((p) => p.join(",")).join(" ")} fill={fc.color} stroke={P.ink} strokeWidth={2.4} strokeLinejoin="round" opacity={1 - out * 0.9} />
        ))}
      </Svg>
    </AbsoluteFill>
  );
};

// =================================================================== 06 · FLUIDOS — metaballs
export const GooPiece: React.FC<{ f: number; flood?: boolean; id?: string }> = ({ f, flood = true, id = "goo" }) => {
  const t = f / FPS;
  const enter = iv(f, [0, 14], [0, 1], expoOut);
  const fl = flood ? iv(f, [44, 60], [0, 1], expoIn) : 0;
  const blobs = Array.from({ length: 7 }).map((_, i) => {
    const a = i * 0.9 + t * (1.1 + i * 0.13);
    const rx = 230 + 60 * Math.sin(t * 2 + i);
    const ry = 330 + 80 * Math.cos(t * 1.7 + i * 2);
    const sx = (i % 2 ? -1 : 1) * 900;
    const sy = (i - 3) * 380;
    return {
      x: CX + sx * (1 - enter) + Math.cos(a) * rx * enter,
      y: CY + sy * (1 - enter) + Math.sin(a * 1.3) * ry * enter,
      r: 95 + 35 * Math.sin(t * 3 + i * 1.7),
    };
  });
  return (
    <AbsoluteFill style={{ background: P.ink }}>
      <Svg>
        <defs>
          <filter id={id} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="26" result="b" />
            <feColorMatrix in="b" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 34 -14" />
          </filter>
        </defs>
        <g filter={`url(#${id})`}>
          {blobs.map((b, i) => (
            <circle key={i} cx={b.x} cy={b.y} r={b.r} fill={P.orange} />
          ))}
          <circle cx={CX} cy={CY} r={150 + 2300 * fl + 18 * Math.sin(t * 4)} fill={P.orange} />
        </g>
        <g filter={`url(#${id})`}>
          {[0, 1, 2].map((i) => (
            <circle key={i} cx={CX + Math.cos(t * 2.4 + i * 2.1) * 120} cy={CY + Math.sin(t * 2.4 + i * 2.1) * 120} r={46} fill={P.paper} opacity={1 - fl} />
          ))}
        </g>
      </Svg>
    </AbsoluteFill>
  );
};
