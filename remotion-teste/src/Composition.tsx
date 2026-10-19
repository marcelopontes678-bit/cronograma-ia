import { AbsoluteFill, Composition, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const MyComposition = () => {
  return (
    <Composition
      id="MyComp"
      component={MyComponent}
      durationInFrames={90}
      fps={30}
      width={1280}
      height={720}
    />
  );
};

export const MyComponent: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 12 } });
  const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0f172a, #4f46e5)",
        justifyContent: "center",
        alignItems: "center",
        color: "white",
        fontFamily: "sans-serif",
      }}
    >
      <div style={{ fontSize: 120, fontWeight: 800, opacity, transform: `scale(${scale})` }}>
        Remotion funciona!
      </div>
    </AbsoluteFill>
  );
};
