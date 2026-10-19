import { Easing, interpolate, random } from "remotion";

export const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

/** Interpolação clamped com easing suave. */
export const ease = (
  frame: number,
  range: [number, number],
  out: [number, number],
  easing: (t: number) => number = Easing.inOut(Easing.sin),
) =>
  interpolate(frame, range, out, {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing,
  });

export const easeOut = (frame: number, range: [number, number], out: [number, number]) =>
  ease(frame, range, out, Easing.out(Easing.cubic));

export const easeIn = (frame: number, range: [number, number], out: [number, number]) =>
  ease(frame, range, out, Easing.in(Easing.cubic));

/** Tremor de câmera na mão, determinístico (somas de senos). */
export const handheld = (frame: number, amp = 1, seed = 0) => {
  const f = frame + seed * 37;
  return {
    x: amp * (3.2 * Math.sin(f / 23) + 1.6 * Math.sin(f / 9.1 + 1.3)),
    y: amp * (2.6 * Math.sin(f / 19 + 0.7) + 1.2 * Math.sin(f / 7.3)),
    r: amp * (0.07 * Math.sin(f / 31) + 0.03 * Math.sin(f / 11)),
  };
};

/** Cintilação suave de luz (lamparina/vela). */
export const flicker = (frame: number, seed = 0, depth = 0.06) =>
  1 - depth * (0.5 + 0.5 * Math.sin(frame / 5.3 + seed)) * (0.6 + 0.4 * Math.sin(frame / 2.1 + seed * 2));

export const rnd = (seed: string | number) => random(seed);

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
