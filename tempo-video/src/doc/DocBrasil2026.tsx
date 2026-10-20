import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame } from "remotion";
import { SANS } from "../fonts";
import { AUDIO } from "./media";
import { Brasilia } from "./scenes/Brasilia";
import { Candidates } from "./scenes/Candidates";
import { Documents } from "./scenes/Documents";
import { Vote } from "./scenes/Vote";
import { Captions, D, FPS, FilmLook, T, eo, iv, sec } from "./ui";

export const DOC_DURATION = 900;

const CUTS = [T.marks.cut2, T.marks.cut3, T.marks.cut4].map(sec);
const SCENES = [
  { from: 0, C: Brasilia },
  { from: CUTS[0], C: Documents },
  { from: CUTS[1], C: Candidates },
  { from: CUTS[2], C: Vote },
];

/** Corte cinematográfico: a cena nova entra com leve zoom-out; um flash curto + mergulho no preto marca o grave. */
const CutFx: React.FC = () => {
  const f = useCurrentFrame();
  let dip = 0;
  let flash = 0;
  for (const c of CUTS) {
    dip = Math.max(dip, iv(f, [c - 6, c, c + 5], [0, 1, 0]));
    flash = Math.max(flash, iv(f, [c, c + 1, c + 7], [0, 0.28, 0]));
  }
  return (
    <>
      <AbsoluteFill style={{ background: "#000", opacity: dip, pointerEvents: "none" }} />
      <AbsoluteFill style={{ background: D.white, opacity: flash, mixBlendMode: "overlay", pointerEvents: "none" }} />
    </>
  );
};

const SceneIn: React.FC<{ children: React.ReactNode; first: boolean }> = ({ children, first }) => {
  const f = useCurrentFrame();
  const s = first ? 1 : 1.06 - 0.06 * iv(f, [0, 18], [0, 1], eo);
  return <AbsoluteFill style={{ transform: `scale(${s})` }}>{children}</AbsoluteFill>;
};

const Header: React.FC = () => {
  const f = useCurrentFrame();
  const o = iv(f, [6, 20], [0, 1]) * (1 - iv(f, [sec(26.6), sec(27.1)], [0, 1]));
  return (
    <div style={{ position: "absolute", left: 72, right: 72, top: 150, display: "flex", justifyContent: "space-between", fontFamily: SANS, fontSize: 20, fontWeight: 700, letterSpacing: "0.28em", color: D.muted, opacity: o }}>
      <span>
        <span style={{ color: D.green }}>●</span> DOCUMENTÁRIO
      </span>
      <span>BRASIL 2026</span>
    </div>
  );
};

/** Música abaixa enquanto há fala (ducking suave pelos intervalos de T.speech). */
const musicVolume = (f: number) => {
  const t = f / FPS;
  let duck = 0;
  for (const s of T.speech) duck = Math.max(duck, iv(t, [s.start - 0.15, s.start, s.end, s.end + 0.3], [0, 1, 1, 0]));
  const fadeIn = iv(t, [0, 0.8], [0, 1]);
  return AUDIO.musicLevel * fadeIn * (1 - AUDIO.duckDepth * duck);
};

export const DocBrasil2026: React.FC = () => (
  <AbsoluteFill style={{ background: D.black }}>
    {SCENES.map(({ from, C }, i) => {
      const to = i < SCENES.length - 1 ? SCENES[i + 1].from : DOC_DURATION;
      return (
        <Sequence key={i} from={from} durationInFrames={to - from}>
          <SceneIn first={i === 0}>
            <SceneFrame C={C} />
          </SceneIn>
        </Sequence>
      );
    })}
    <Header />
    <Captions />
    <CutFx />
    <FilmLook />
    <Audio src={staticFile(AUDIO.narration)} volume={1} />
    <Audio src={staticFile(AUDIO.music)} volume={musicVolume} />
    <Audio src={staticFile(AUDIO.sfx)} volume={0.9} />
  </AbsoluteFill>
);

/** As cenas calculam o tempo em frames locais a partir do seu próprio início. */
const SceneFrame: React.FC<{ C: React.FC<{ f: number }> }> = ({ C }) => {
  const f = useCurrentFrame();
  return <C f={f} />;
};
