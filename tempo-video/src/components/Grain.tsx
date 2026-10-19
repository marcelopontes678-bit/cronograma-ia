import { AbsoluteFill, staticFile, useCurrentFrame } from "remotion";
import { rnd } from "../lib/motion";

/** Granulação de filme: 4 quadros de ruído, trocados e deslocados a cada frame (determinístico). */
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.11 }) => {
  const frame = useCurrentFrame();
  const tile = frame % 4;
  const ox = Math.floor(rnd(`gx${frame}`) * 512);
  const oy = Math.floor(rnd(`gy${frame}`) * 512);
  return (
    <AbsoluteFill
      style={{
        backgroundImage: `url(${staticFile(`grain/grain${tile}.png`)})`,
        backgroundSize: "512px 512px",
        backgroundPosition: `${ox}px ${oy}px`,
        mixBlendMode: "overlay",
        opacity,
        pointerEvents: "none",
      }}
    />
  );
};
