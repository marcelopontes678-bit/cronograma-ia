import { AbsoluteFill, useCurrentFrame } from "remotion";
import { rnd } from "../lib/motion";
import { HEIGHT, WIDTH } from "../config";

/**
 * Partículas suspensas no ar. Posição, tamanho e cintilação saem do índice (determinístico).
 * `region` limita onde nascem; `lit` (0–1) diz quão iluminadas ficam (feixe de luz).
 */
export const Dust: React.FC<{
  count?: number;
  region?: [number, number, number, number]; // x0,y0,x1,y1
  color?: string;
  size?: [number, number];
  speed?: number;
  opacity?: number;
  blur?: number;
  seed?: string;
  litAt?: (x: number, y: number) => number;
}> = ({
  count = 60,
  region = [0, 0, WIDTH, HEIGHT],
  color = "255,222,160",
  size = [1.2, 3.6],
  speed = 1,
  opacity = 0.7,
  blur = 0,
  seed = "d",
  litAt,
}) => {
  const frame = useCurrentFrame();
  const [x0, y0, x1, y1] = region;
  const w = x1 - x0;
  const h = y1 - y0;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", filter: blur ? `blur(${blur}px)` : undefined }}>
      <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: count }).map((_, i) => {
          const r = (k: string) => rnd(`${seed}${k}${i}`);
          const vx = (r("vx") - 0.5) * 9 * speed;
          const vy = (-3 - r("vy") * 9) * speed;
          const px = x0 + ((r("px") * w + vx * frame / 30 * 6 + w * 10) % w);
          const py = y0 + ((r("py") * h + vy * frame / 30 * 6 + h * 10) % h);
          const s = size[0] + r("s") * (size[1] - size[0]);
          const tw = 0.45 + 0.55 * Math.sin(frame / (14 + r("tw") * 20) + r("ph") * 6.28);
          const lit = litAt ? litAt(px, py) : 1;
          const a = opacity * tw * lit;
          if (a < 0.02) return null;
          return <circle key={i} cx={px} cy={py} r={s} fill={`rgba(${color},${a})`} />;
        })}
      </svg>
    </AbsoluteFill>
  );
};
