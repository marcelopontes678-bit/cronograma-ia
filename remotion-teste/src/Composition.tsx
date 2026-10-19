import {
  AbsoluteFill,
  Composition,
  Easing,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PROJETO_DURATION, ProjetoMarcenaria } from "./ProjetoMarcenaria";

const FONT = "Helvetica, Arial, sans-serif";

export const MyComposition = () => {
  return (
    <>
    <Composition
      id="ProjetoMarcenaria"
      component={ProjetoMarcenaria}
      durationInFrames={PROJETO_DURATION}
      fps={30}
      width={720}
      height={1280}
    />
    <Composition
      id="Reels"
      component={Reels}
      durationInFrames={450}
      fps={30}
      width={1080}
      height={1920}
    />
    </>
  );
};

const Background: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${135 + frame * 0.2}deg, #0f172a, #4f46e5 70%, #22d3ee)`,
      }}
    />
  );
};

const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ justifyContent: "center", padding: "100px 80px", fontFamily: FONT, color: "white" }}>
      <div
        style={{
          fontSize: 56,
          fontWeight: 700,
          color: "#22d3ee",
          letterSpacing: 6,
          opacity: interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        IA + NEGÓCIOS
      </div>
      <div
        style={{
          fontSize: 130,
          fontWeight: 900,
          lineHeight: 1.05,
          marginTop: 30,
          opacity: interpolate(frame, [10, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          translate: interpolate(frame, [10, 1 * fps], ["0px 80px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        3 jeitos de usar IA para empreender mais rápido
      </div>
    </AbsoluteFill>
  );
};

const Tip: React.FC<{ n: string; title: string; text: string }> = ({ n, title, text }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ justifyContent: "center", padding: "100px 80px", fontFamily: FONT, color: "white" }}>
      <div
        style={{
          fontSize: 360,
          fontWeight: 900,
          lineHeight: 1,
          color: "#22d3ee",
          scale: interpolate(frame, [0, 20], [0.4, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          transformOrigin: "left center",
        }}
      >
        {n}
      </div>
      <div
        style={{
          fontSize: 100,
          fontWeight: 800,
          lineHeight: 1.1,
          opacity: interpolate(frame, [10, 28], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: 54,
          marginTop: 36,
          lineHeight: 1.3,
          opacity: interpolate(frame, [25, 45], [0, 0.9], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

const Cta: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "100px 80px", fontFamily: FONT, color: "white", textAlign: "center" }}>
      <div
        style={{
          fontSize: 120,
          fontWeight: 900,
          lineHeight: 1.1,
          scale: interpolate(frame, [0, 20], [0.7, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        Siga para mais conteúdo sobre IA
      </div>
      <div
        style={{
          fontSize: 54,
          marginTop: 40,
          color: "#22d3ee",
          opacity: interpolate(frame, [20, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        Salve este vídeo para depois
      </div>
    </AbsoluteFill>
  );
};

export const Reels: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      <Background />
      <Sequence name="Gancho" from={0} durationInFrames={3 * fps}>
        <Hook />
      </Sequence>
      <Sequence name="Dica 1" from={3 * fps} durationInFrames={4 * fps}>
        <Tip n="1" title="Automatize tarefas repetitivas" text="Respostas, planilhas e relatórios em minutos, não horas." />
      </Sequence>
      <Sequence name="Dica 2" from={7 * fps} durationInFrames={4 * fps}>
        <Tip n="2" title="Crie conteúdo em escala" text="Roteiros, ideias e edições com ajuda da IA." />
      </Sequence>
      <Sequence name="Dica 3" from={11 * fps} durationInFrames={2 * fps}>
        <Tip n="3" title="Valide ideias rápido" text="Teste o mercado antes de investir." />
      </Sequence>
      <Sequence name="CTA" from={13 * fps} durationInFrames={2 * fps}>
        <Cta />
      </Sequence>
    </AbsoluteFill>
  );
};
