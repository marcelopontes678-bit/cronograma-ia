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
// -> corte no drop da música para o render final com barra de progresso.
const SOURCE_SECONDS = 92; // exclui a vinheta do CapCut no fim do vídeo original
const DROP_SECONDS = 11.17; // drop da trilha original, onde a imagem aparece
const TOTAL_SECONDS = 23; // duração da trilha original
const IMAGE_ASPECT = 1672 / 940;
const IMAGE_HEIGHT = 1280; // imagem encaixada na altura, com panorâmica horizontal

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Process: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const zoomStart = durationInFrames - 18;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill
        style={{
          // zoom-through: afasta o enquadramento no início e mergulha na tela do notebook
          transformOrigin: "47% 54%",
          scale: interpolate(frame, [0, zoomStart, durationInFrames], [1, 1.08, 3.2], {
            ...clamp,
            easing: Easing.bezier(0.7, 0, 1, 0.6),
          }),
          filter: `blur(${interpolate(frame, [zoomStart, durationInFrames], [0, 16], clamp)}px)`,
        }}
      >
        <Video
          name="Processo"
          src={staticFile("processo.mp4")}
          objectFit="cover"
          playbackRate={SOURCE_SECONDS / DROP_SECONDS}
          trimAfter={SOURCE_SECONDS * fps}
          muted
          style={{ position: "absolute", width: "100%", height: "100%" }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Reveal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width } = useVideoConfig();
  const imageWidth = IMAGE_HEIGHT * IMAGE_ASPECT;
  const settle = 28;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill
        style={{
          // corte seco no drop: entra ampliado e desfocado, depois assenta
          filter: `blur(${interpolate(frame, [0, settle], [16, 0], clamp)}px)`,
          scale: interpolate(frame, [0, settle + 15, durationInFrames], [3.6, 1.1, 1.2], {
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
            height: IMAGE_HEIGHT,
            width: imageWidth,
            // panorâmica da TV até a mesa
            left: interpolate(frame, [0, durationInFrames], [-596, -1234], {
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
          opacity: interpolate(frame, [settle, settle + 10], [0, 1], clamp),
        }}
      >
        <div
          style={{
            height: "100%",
            borderRadius: 3,
            backgroundColor: "white",
            width: interpolate(frame, [settle, durationInFrames - fps], [0, width - 120], clamp),
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

export const ProjetoMarcenaria: React.FC = () => {
  const { fps, durationInFrames } = useVideoConfig();
  const cut = Math.round(DROP_SECONDS * fps);
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Audio name="Trilha" src={staticFile("trilha.mp3")} />
      <Sequence name="Processo" from={0} durationInFrames={cut}>
        <Process />
      </Sequence>
      <Sequence name="Render final" from={cut} durationInFrames={durationInFrames - cut}>
        <Reveal />
      </Sequence>
    </AbsoluteFill>
  );
};

export const PROJETO_DURATION = TOTAL_SECONDS * 30;
