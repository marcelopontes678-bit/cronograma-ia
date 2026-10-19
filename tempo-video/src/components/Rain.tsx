import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { rnd } from "../lib/motion";
import { HEIGHT, WIDTH } from "../config";

/** Chuva em camadas (fundo fino/denso, frente grossa/rara). Posição = função do frame. */
export const Rain: React.FC<{ count?: number; opacity?: number; seed?: string; near?: boolean; wind?: number }> = ({
  count = 160,
  opacity = 1,
  seed = "rain",
  near = false,
  wind = 0.16,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", filter: near ? "blur(1.4px)" : undefined }}>
      <svg width={WIDTH} height={HEIGHT} style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: count }).map((_, i) => {
          const r = (k: string) => rnd(`${seed}${k}${i}`);
          const len = near ? 120 + r("l") * 160 : 34 + r("l") * 80;
          const speed = near ? 3100 + r("s") * 1200 : 1500 + r("s") * 1100;
          const cycle = HEIGHT + len * 2;
          const y = ((r("y") * cycle + speed * t) % cycle) - len;
          const x = r("x") * (WIDTH + 400) - 200 + y * wind;
          const a = (near ? 0.12 + r("a") * 0.14 : 0.07 + r("a") * 0.16) * opacity;
          return (
            <line
              key={i}
              x1={x}
              y1={y}
              x2={x - len * wind}
              y2={y - len}
              stroke={`rgba(190,212,232,${a})`}
              strokeWidth={near ? 2.4 : 1.1 + r("w") * 0.6}
              strokeLinecap="round"
            />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
