export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const DURATION = 900; // 30 s exatos

/** Áreas seguras do Instagram Reels (px em 1080x1920). */
export const SAFE = { top: 270, bottom: 440, side: 72 };

/** Início/fim de cada cena em frames (0–5, 5–11, 11–18, 18–25, 25–30 s). */
export const SCENES = {
  clock: { from: 0, to: 150 },
  street: { from: 150, to: 330 },
  desk: { from: 330, to: 540 },
  montage: { from: 540, to: 750 },
  sunrise: { from: 750, to: 900 },
} as const;

/** Frames de sobreposição na dissolução entre cenas. */
export const DISSOLVE = 14;

export const C = {
  black: "#040506",
  charcoal: "#0c0f13",
  slate: "#171d24",
  steel: "#2b3744",
  fog: "#1b2833",
  cool: "#8fa6bd",
  gold: "#d6ad60",
  goldBright: "#f1d08a",
  goldDeep: "#8a6325",
  ivory: "#efe8d8",
};

export const sec = (s: number) => Math.round(s * FPS);
