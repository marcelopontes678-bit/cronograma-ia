import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame } from "remotion";
import { DISSOLVE, DURATION, FPS, SAFE, SCENES } from "./config";
import { ClockScene } from "./scenes/ClockScene";
import { StreetScene } from "./scenes/StreetScene";
import { DeskScene } from "./scenes/DeskScene";
import { MontageScene } from "./scenes/MontageScene";
import { SunriseScene } from "./scenes/SunriseScene";
import { Grain } from "./components/Grain";
import { Vignette } from "./components/Vignette";
import { Statement } from "./components/Statement";
import { Subtitles } from "./components/Subtitles";
import { ease } from "./lib/motion";
import { interpolate } from "remotion";
import speech from "./data/speech.json";

const len = (s: { from: number; to: number }) => s.to - s.from;

/** Cena com dissolução: a anterior continua opaca por baixo enquanto esta aparece nos primeiros frames. */
const Scene: React.FC<{ from: number; length: number; first?: boolean; children: React.ReactNode }> = ({
  from,
  length,
  first,
  children,
}) => (
  <Sequence from={from} durationInFrames={length}>
    <FadeIn enabled={!first}>{children}</FadeIn>
  </Sequence>
);

const FadeIn: React.FC<{ enabled: boolean; children: React.ReactNode }> = ({ enabled, children }) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{ opacity: enabled ? ease(frame, [0, DISSOLVE], [0, 1]) : 1 }}>{children}</AbsoluteFill>;
};

/** Música abaixa durante a fala (ataque/soltura suaves) e volta nos intervalos. */
const musicVolume = (frame: number) => {
  const t = frame / FPS;
  let duck = 0;
  for (const w of speech) {
    const lvl = interpolate(t, [w.start - 0.45, w.start - 0.15, w.end + 0.4, w.end + 1.1], [0, 1, 1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    duck = Math.max(duck, lvl);
  }
  const tail = interpolate(t, [29.7, 30], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return 1.0 * (1 - 0.56 * duck) * tail;
};

const SafeAreaGuide: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: SAFE.top, background: "rgba(255,0,0,0.18)" }} />
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: SAFE.bottom, background: "rgba(255,0,0,0.18)" }} />
    <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: SAFE.side, background: "rgba(255,0,0,0.12)" }} />
    <div style={{ position: "absolute", right: 0, top: 0, bottom: 0, width: SAFE.side, background: "rgba(255,0,0,0.12)" }} />
  </AbsoluteFill>
);

export const MainVideo: React.FC<{ showSafeArea?: boolean }> = ({ showSafeArea }) => {
  const frame = useCurrentFrame();
  const fadeOut = ease(frame, [DURATION - 24, DURATION - 1], [0, 1]);

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {/* ------------------------------------------------------------ cenas (0–5, 5–11, 11–18, 18–25, 25–30 s) */}
      <Scene from={SCENES.clock.from} length={len(SCENES.clock) + DISSOLVE} first>
        <ClockScene duration={len(SCENES.clock)} />
      </Scene>
      <Scene from={SCENES.street.from} length={len(SCENES.street) + DISSOLVE}>
        <StreetScene duration={len(SCENES.street)} />
      </Scene>
      <Scene from={SCENES.desk.from} length={len(SCENES.desk) + DISSOLVE}>
        <DeskScene duration={len(SCENES.desk)} />
      </Scene>
      <Scene from={SCENES.montage.from} length={len(SCENES.montage) + DISSOLVE}>
        <MontageScene />
      </Scene>
      <Scene from={SCENES.sunrise.from} length={len(SCENES.sunrise)}>
        <SunriseScene duration={len(SCENES.sunrise)} />
      </Scene>

      {/* ------------------------------------------------------------ pós-produção */}
      <Vignette />
      <Grain />

      {/* ------------------------------------------------------------ texto em tela (tempos em segundos) */}
      <Statement lines={[{ text: "O TEMPO", at: 0.9 }, { text: "NÃO ESPERA.", at: 1.4, gold: true }]} out={4.5} top={500} />
      <Statement lines={[{ text: "CADA DIA", at: 5.9 }, { text: "É IRREPETÍVEL.", at: 6.4, gold: true }]} out={10.5} top={500} />
      <Statement lines={[{ text: "ADIAR TAMBÉM", at: 12.0 }, { text: "É ESCOLHER.", at: 12.5, gold: true }]} out={17.4} top={500} />
      <Statement
        lines={[
          { text: "DISCIPLINA.", at: 20.0 },
          { text: "PROPÓSITO.", at: 21.5 },
          { text: "AÇÃO.", at: 23.0, gold: true },
        ]}
        out={24.7}
        top={560}
        size={78}
      />
      <Statement
        lines={[
          { text: "SEU TEMPO", at: 26.2 },
          { text: "É SUA VIDA.", at: 26.8, gold: true },
          { text: "Comece hoje.", at: 28.2, small: true },
        ]}
        out={29.7}
        top={500}
        size={98}
      />

      <Subtitles />
      {showSafeArea && <SafeAreaGuide />}

      {/* fade final para preto */}
      <AbsoluteFill style={{ background: "#000", opacity: fadeOut, pointerEvents: "none" }} />

      {/* ------------------------------------------------------------ áudio */}
      <Audio src={staticFile("audio/music.mp3")} volume={musicVolume} />
      <Audio src={staticFile("audio/narration.wav")} volume={1} />
    </AbsoluteFill>
  );
};
