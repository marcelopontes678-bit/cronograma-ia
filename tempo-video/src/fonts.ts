import { loadFont } from "@remotion/fonts";
import { FONT_DATA } from "./generated/fontData";

export const SERIF = "Cormorant Garamond";
export const SANS = "Inter";

/**
 * Cormorant Garamond e Inter (SIL OFL), embutidas como data: URL em src/generated/fontData.ts
 * (gerado por scripts/embed_fonts.py a partir de public/fonts). Sem rede: o carregamento é imediato
 * e o delayRender só segura a renderização até as fontes estarem registradas.
 */
const faces: [string, string, string, "normal" | "italic"][] = [
  [SERIF, "cormorant-garamond-latin-400-normal", "400", "normal"],
  [SERIF, "cormorant-garamond-latin-500-normal", "500", "normal"],
  [SERIF, "cormorant-garamond-latin-600-normal", "600", "normal"],
  [SERIF, "cormorant-garamond-latin-400-italic", "400", "italic"],
  [SERIF, "cormorant-garamond-latin-500-italic", "500", "italic"],
  [SANS, "inter-latin-400-normal", "400", "normal"],
  [SANS, "inter-latin-500-normal", "500", "normal"],
  [SANS, "inter-latin-600-normal", "600", "normal"],
  [SANS, "inter-latin-700-normal", "700", "normal"],
  [SANS, "inter-latin-800-normal", "800", "normal"],
  [SANS, "inter-latin-900-normal", "900", "normal"],
];

export const fontsReady = Promise.all(
  faces.map(([family, key, weight, style]) =>
    loadFont({ family, url: FONT_DATA[key], format: "woff2", weight, style }),
  ),
);
