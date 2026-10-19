import { AbsoluteFill, useCurrentFrame } from "remotion";
import { ease, handheld } from "../lib/motion";
import { HEIGHT, WIDTH } from "../config";

type Pose = { scale: number; x: number; y: number; rot?: number };

/**
 * Câmera virtual: move/amplia o conteúdo ao longo de `duration` frames, com tremor de mão sutil.
 * `origin` é o ponto (px) em torno do qual o zoom acontece.
 */
export const Camera: React.FC<{
  from: Pose;
  to: Pose;
  duration: number;
  origin?: [number, number];
  shake?: number;
  seed?: number;
  children: React.ReactNode;
}> = ({ from, to, duration, origin = [WIDTH / 2, HEIGHT / 2], shake = 1, seed = 0, children }) => {
  const frame = useCurrentFrame();
  const t = (a: number, b: number) => ease(frame, [0, duration], [a, b]);
  const h = handheld(frame, shake, seed);
  const scale = t(from.scale, to.scale);
  const x = t(from.x, to.x) + h.x;
  const y = t(from.y, to.y) + h.y;
  const rot = t(from.rot ?? 0, to.rot ?? 0) + h.r;
  return (
    <AbsoluteFill
      style={{
        transform: `translate(${x}px, ${y}px) rotate(${rot}deg) scale(${scale})`,
        transformOrigin: `${origin[0]}px ${origin[1]}px`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
