import { Audio, Video } from "@remotion/media";
import {
  AbsoluteFill,
  CanvasImage,
  Easing,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// Estrutura copiada do vídeo modelo: timelapse do processo em tela cheia
// -> corte para o render final com barra de progresso, tudo sobre a trilha.
const SOURCE_SECONDS = 92; // exclui a vinheta do CapCut no fim do vídeo original
const PROCESS_SECONDS = 13.5;
const TOTAL_SECONDS = 23;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Process: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // zoom-through: entra na tela do notebook, onde o projeto está sendo modelado
  const t0 = PROCESS_SECONDS * fps - 20;
  const t1 = PROCESS_SECONDS * fps;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill
        style={{
          transformOrigin: "47% 54%",
          scale: interpolate(frame, [0, t0, t1], [1.25, 1.3, 7], {
            ...clamp,
            easing: Easing.bezier(0.7, 0, 1, 0.6),
          }),
          filter: `blur(${interpolate(frame, [t0, t1], [0, 22], clamp)}px)`,
          opacity: interpolate(frame, [t1 - 6, t1], [1, 0], clamp),
        }}
      >
        <Video
          name="Processo"
          src={staticFile("processo.mp4")}
          objectFit="cover"
          playbackRate={SOURCE_SECONDS / PROCESS_SECONDS}
          trimAfter={SOURCE_SECONDS * fps}
          muted
          style={{ position: "absolute", width: "100%", height: "100%" }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const IMAGE_W = (1672 / 940) * 1280; // altura da imagem encaixada em 1280px

const Reveal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width } = useVideoConfig();
  const t0 = 0; // entra enquanto o processo ainda está em zoom
  const t1 = 28;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill
        style={{
          opacity: interpolate(frame, [t0, t0 + 8], [0, 1], clamp),
          filter: `blur(${interpolate(frame, [t0, t1], [22, 0], clamp)}px)`,
          scale: interpolate(frame, [t0, t1 + 15, durationInFrames], [3.6, 1.1, 1.2], {
            ...clamp,
            easing: Easing.bezier(0.1, 0.7, 0.3, 1),
          }),
        }}
      >
        <CanvasImage
          name="Sala"
          src={staticFile("sala.png")}
          style={{
            position: "absolute",
            top: 0,
            height: 1280,
            width: IMAGE_W,
            left: interpolate(frame, [t0, durationInFrames], [-596, -1234], {
              ...clamp,
              easing: Easing.bezier(0.45, 0, 0.55, 1),
            }),
          }}
        />
      </AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: 60,
          right: 60,
          bottom: 90,
          height: 6,
          borderRadius: 3,
          backgroundColor: "rgba(255,255,255,0.3)",
          opacity: interpolate(frame, [t1, t1 + 10], [0, 1], clamp),
        }}
      >
        <div
          style={{
            height: "100%",
            borderRadius: 3,
            backgroundColor: "white",
            width: interpolate(frame, [t1, durationInFrames - fps], [0, width - 120], clamp),
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

export const ProjetoMarcenaria: React.FC = () => {
  const { fps, durationInFrames } = useVideoConfig();
  const cut = PROCESS_SECONDS * fps;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio
        name="Trilha"
        src={staticFile("trilha.mp3")}
        volume={(f) => interpolate(f, [durationInFrames - fps, durationInFrames], [1, 0], clamp)}
      />
      <Sequence name="Processo" from={0} durationInFrames={cut}>
        <Process />
      </Sequence>
      <Sequence name="Render final" from={cut - 12} durationInFrames={durationInFrames - cut + 12}>
        <Reveal />
      </Sequence>
    </AbsoluteFill>
  );
};

export const PROJETO_DURATION = TOTAL_SECONDS * 30;
