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
const DROP_SECONDS = 15.14; // drop da trilha (trilha30.mp3), onde ocorre o corte
const BPM = 136;
const TOTAL_SECONDS = 30;
const IMAGE_ASPECT = 1672 / 940;

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
  const imageHeight = width / IMAGE_ASPECT; // imagem completa, encaixada na largura
  const beat = (60 / BPM) * fps;
  const sinceBeat = frame % beat;
  // pulso discreto a cada batida
  const pulse = interpolate(sinceBeat, [0, beat * 0.5], [0.012, 0], {
    ...clamp,
    easing: Easing.bezier(0.2, 0.8, 0.3, 1),
  });
  const settle = 24;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill
        style={{
          // corte seco no drop: entra ampliado e desfocado, depois assenta
          scale: interpolate(frame, [0, settle], [2.4, 1], {
            ...clamp,
            easing: Easing.bezier(0.1, 0.7, 0.3, 1),
          }),
          filter: `blur(${interpolate(frame, [0, settle], [16, 0], clamp)}px)`,
        }}
      >
        <CanvasImage
          name="Fundo"
          src={staticFile("sala.png")}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "blur(40px) brightness(0.45)",
            scale: 1.3,
          }}
        />
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <CanvasImage
            name="Sala"
            src={staticFile("sala.png")}
            style={{
              width,
              height: imageHeight,
              scale: 1 + interpolate(frame, [0, durationInFrames], [0, 0.05], clamp) + pulse,
            }}
          />
        </AbsoluteFill>
      </AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: 60,
          right: 60,
          bottom: 110,
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
      <Audio name="Trilha" src={staticFile("trilha30.mp3")} />
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
