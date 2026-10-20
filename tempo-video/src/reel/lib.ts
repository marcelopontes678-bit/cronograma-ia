import { Easing, interpolate } from "remotion";

/** Paleta restrita: tinta, papel, laranja-sinal e azul elétrico. */
export const P = { ink: "#0E0E10", paper: "#F3EFE6", orange: "#FF4A1C", blue: "#2D5BFF" };
export const CX = 540;
export const CY = 960;

export const expoOut = Easing.bezier(0.16, 1, 0.3, 1);
export const expoIn = Easing.bezier(0.7, 0, 0.84, 0);
export const inOut = Easing.bezier(0.83, 0, 0.17, 1);

/** interpolate com clamp e easing (atalho). */
export const iv = (f: number, inR: number[], outR: number[], easing?: (t: number) => number) =>
  interpolate(f, inR, outR, { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing });

/** Aleatório determinístico simples (hash do índice). */
export const hash = (i: number, s = 0) => {
  const x = Math.sin(i * 127.1 + s * 311.7) * 43758.5453;
  return x - Math.floor(x);
};

// ------------------------------------------------------------------ morph de formas
type V = [number, number];

/** Interseção do raio (a partir do centro, ângulo th) com um polígono estrelado em torno do centro. */
const rayRadius = (verts: V[], th: number) => {
  const dx = Math.cos(th);
  const dy = Math.sin(th);
  let best = Infinity;
  for (let i = 0; i < verts.length; i++) {
    const [ax, ay] = verts[i];
    const [bx, by] = verts[(i + 1) % verts.length];
    const ex = bx - ax;
    const ey = by - ay;
    const den = dx * ey - dy * ex;
    if (Math.abs(den) < 1e-9) continue;
    const t = (ax * ey - ay * ex) / den;
    const u = (ax * dy - ay * dx) / den;
    if (t > 0 && u >= -1e-6 && u <= 1 + 1e-6) best = Math.min(best, t);
  }
  return best;
};

const regular = (n: number, r: number, rot: number, inner?: number): V[] =>
  Array.from({ length: inner ? n * 2 : n }).map((_, i) => {
    const a = rot + (i * Math.PI * 2) / (inner ? n * 2 : n);
    const rr = inner && i % 2 ? inner : r;
    return [Math.cos(a) * rr, Math.sin(a) * rr];
  });

export type ShapeKind = "circle" | "square" | "triangle" | "star";

/** Amostra a forma em N pontos com o MESMO ângulo inicial: assim o morph é ponto a ponto. */
export const shapePoints = (kind: ShapeKind, R: number, n = 240): V[] => {
  const verts: Record<Exclude<ShapeKind, "circle">, V[]> = {
    square: regular(4, R * 1.12, Math.PI / 4),
    triangle: regular(3, R * 1.22, -Math.PI / 2),
    star: regular(5, R * 1.22, -Math.PI / 2, R * 0.52),
  };
  return Array.from({ length: n }).map((_, i) => {
    const th = -Math.PI / 2 + (i * Math.PI * 2) / n;
    const r = kind === "circle" ? R : rayRadius(verts[kind], th);
    return [Math.cos(th) * r, Math.sin(th) * r];
  });
};

export const lerpPts = (a: V[], b: V[], t: number): V[] => a.map((p, i) => [p[0] + (b[i][0] - p[0]) * t, p[1] + (b[i][1] - p[1]) * t]);
export const toPath = (pts: V[], cx: number, cy: number, rot = 0) => {
  const c = Math.cos(rot);
  const s = Math.sin(rot);
  return "M" + pts.map(([x, y]) => `${(cx + x * c - y * s).toFixed(1)},${(cy + x * s + y * c).toFixed(1)}`).join("L") + "Z";
};

// ------------------------------------------------------------------ 3D mínimo
export type V3 = [number, number, number];
export const rotY = ([x, y, z]: V3, a: number): V3 => [x * Math.cos(a) + z * Math.sin(a), y, -x * Math.sin(a) + z * Math.cos(a)];
export const rotX = ([x, y, z]: V3, a: number): V3 => [x, y * Math.cos(a) - z * Math.sin(a), y * Math.sin(a) + z * Math.cos(a)];
export const project = ([x, y, z]: V3, F = 1250, dist = 9, cx = CX, cy = CY): [number, number] => {
  const zc = z + dist;
  return [cx + (x * F) / zc, cy - (y * F) / zc];
};
