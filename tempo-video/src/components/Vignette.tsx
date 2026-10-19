import { AbsoluteFill } from "remotion";

/** Vinheta discreta + gradação fria nas sombras e dourada nos realces. */
export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.62 }) => (
  <>
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse 78% 62% at 50% 46%, rgba(0,0,0,0) 0%, rgba(0,0,0,0) 46%, rgba(0,0,0,${strength}) 100%)`,
        pointerEvents: "none",
      }}
    />
    {/* sombras frias */}
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg, rgba(14,38,56,0.30) 0%, rgba(8,20,32,0.10) 55%, rgba(4,10,16,0.34) 100%)",
        mixBlendMode: "soft-light",
        pointerEvents: "none",
      }}
    />
  </>
);
