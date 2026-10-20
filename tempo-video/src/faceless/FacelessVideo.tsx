import { AbsoluteFill, Audio, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FPS, HEIGHT, WIDTH } from "../config";
import { SANS } from "../fonts";
import { ease, easeOut } from "../lib/motion";
import { StreetScene } from "../scenes/StreetScene";
import { SunriseScene } from "../scenes/SunriseScene";
import { DeskScene } from "../scenes/DeskScene";
import { BackgroundsScreen, ConnectScreen, HeroScreen, PostingScreen, SearchScreen, VoicesScreen } from "./screens";
import { AIBadge, BigCaptions, ClipScreen, GREEN, Halftone, PHONE_H, PHONE_W, PhoneFrame, Presenter, SCREEN, SceneSlide, T, Waves, sec } from "./parts";

export const FACELESS_DURATION = Math.ceil(T.duration * FPS);

const P = T.phrases;
const START = { hook: 0, step1: P[1].start - 0.2, step2: P[2].start - 0.2, step3: P[3].start - 0.2, cta: P[4].start - 0.2 };
const M = T.marks;

/** Posiciona um celular pelo centro-topo, com escala. */
const PhoneAt: React.FC<{ cx: number; top: number; scale: number; rot?: number; glow?: boolean; children: React.ReactNode; opacity?: number }> = ({
  cx,
  top,
  scale,
  rot = 0,
  glow,
  children,
  opacity = 1,
}) => (
  <div style={{ position: "absolute", left: cx - (PHONE_W * scale) / 2, top, width: PHONE_W, height: PHONE_H, transform: `rotate(${rot}deg) scale(${scale})`, transformOrigin: "50% 0%", opacity }}>
    <PhoneFrame glow={glow}>{children}</PhoneFrame>
  </div>
);

/** Troca de tela com rolagem vertical e desfoque de movimento. */
const Swap: React.FC<{ at: number; a: React.ReactNode; b: React.ReactNode }> = ({ at, a, b }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const p = ease(t, [at, at + 0.28], [0, 1]);
  const blur = Math.sin(Math.PI * p) * 11;
  const H = SCREEN.h;
  return (
    <AbsoluteFill>
      {p < 1 && (
        <AbsoluteFill style={{ transform: `translateY(${-p * H}px)`, filter: blur > 0.3 ? `blur(${blur}px)` : undefined }}>{a}</AbsoluteFill>
      )}
      {p > 0 && (
        <AbsoluteFill style={{ transform: `translateY(${(1 - p) * H}px)`, filter: blur > 0.3 ? `blur(${blur}px)` : undefined }}>{b}</AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- cena 1: gancho
const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / FPS;
  const out = ease(t, [M.badge - 0.05, M.badge + 0.35], [0, 1]); // celulares e apresentador saem quando a IA entra
  const pop = (d: number) => spring({ frame: frame - d, fps, config: { damping: 13, stiffness: 110, mass: 0.8 } });
  const tik = ease(t, [M.tiktok - 0.1, M.tiktok + 0.25], [0, 1]);
  const badgeIn = spring({ frame: frame - sec(M.badge), fps, config: { damping: 9, stiffness: 130, mass: 0.7 } });
  return (
    <AbsoluteFill>
      <Waves />
      <div style={{ position: "absolute", inset: 0, transform: `translateY(${-out * 700}px)`, opacity: 1 - out }}>
        <PhoneAt cx={190} top={250 + (1 - pop(2)) * 500} scale={0.5} rot={-9}><ClipScreen from={0}><DeskScene duration={600} /></ClipScreen></PhoneAt>
        <PhoneAt cx={890} top={250 + (1 - pop(8)) * 500} scale={0.5} rot={9}><ClipScreen from={0}><SunriseScene duration={600} /></ClipScreen></PhoneAt>
        <PhoneAt cx={540} top={190 + (1 - pop(5)) * 560 - tik * 20} scale={0.5 + 0.1 * tik} glow={tik > 0.5}><ClipScreen from={0}><StreetScene duration={600} /></ClipScreen></PhoneAt>
      </div>
      <div style={{ position: "absolute", inset: 0, transform: `translateY(${out * 900}px)` }}>
        <Presenter x={420} y={HEIGHT - 1000 * 1.0 + 40 + (1 - pop(0)) * 500} scale={1.0} />
      </div>
      {out > 0 && (
        <div style={{ position: "absolute", left: WIDTH / 2 - 260, top: 380, transform: `scale(${badgeIn}) rotate(${(1 - badgeIn) * -14 - 7}deg)` }}>
          <AIBadge size={520} />
        </div>
      )}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- cena 2: acessar o site
const Step1: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - sec(START.step1) - 4, fps, config: { damping: 14, stiffness: 110, mass: 0.8 } });
  const swapAt = M.tap1 - 1.3;
  return (
    <AbsoluteFill>
      <Waves />
      <PhoneAt cx={WIDTH / 2} top={200 + (1 - pop) * 120} scale={0.9} rot={(1 - pop) * -5} glow>
        <Swap at={swapAt} a={<SearchScreen />} b={<HeroScreen tapAt={M.tap1} />} />
      </PhoneAt>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- cena 3: escolher fundo, fonte e narração
const Step2: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - sec(START.step2) - 4, fps, config: { damping: 14, stiffness: 110, mass: 0.8 } });
  return (
    <AbsoluteFill>
      <Waves />
      <PhoneAt cx={WIDTH / 2} top={200 + (1 - pop) * 120} scale={0.9} rot={(1 - pop) * 5} glow>
        <Swap at={M.voiceList - 0.2} a={<BackgroundsScreen />} b={<VoicesScreen tapAt={M.tap2} />} />
      </PhoneAt>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- cena 4: conectar e deixar a IA postar
const Step3: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - sec(START.step3) - 4, fps, config: { damping: 14, stiffness: 110, mass: 0.8 } });
  const presIn = spring({ frame: frame - sec(START.step3) - 10, fps, config: { damping: 14, stiffness: 90, mass: 0.9 } });
  const swapAt = M.connect + 3.0;
  return (
    <AbsoluteFill>
      <Waves />
      <PhoneAt cx={WIDTH / 2} top={170 + (1 - pop) * 140} scale={0.82} rot={(1 - pop) * -5} glow>
        <Swap
          at={swapAt}
          a={<ConnectScreen />}
          b={
            <PostingScreen>
              <ClipScreen from={sec(swapAt) - 110}><SunriseScene duration={600} /></ClipScreen>
            </PostingScreen>
          }
        />
      </PhoneAt>
      <Presenter x={300} y={HEIGHT - 1000 + 20 + (1 - presIn) * 700} scale={0.5} seed={2} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- cena 5: comentar "IA"
const Bubble: React.FC<{ at: number; children: React.ReactNode; blue?: boolean; x: number; y: number; w?: number }> = ({ at, children, blue, x, y, w }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - sec(at), fps, config: { damping: 10, stiffness: 200, mass: 0.6 } });
  if (frame < sec(at)) return null;
  const bg = blue ? "#0a84ff" : "#e9e9eb";
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: w,
        padding: blue ? "26px 70px 36px" : "34px 46px",
        borderRadius: 70,
        background: bg,
        transform: `scale(${p})`,
        transformOrigin: blue ? "100% 100%" : "0% 100%",
        boxShadow: "0 14px 50px rgba(0,0,0,0.5)",
      }}
    >
      {children}
      <svg width={60} height={50} viewBox="0 0 60 50" style={{ position: "absolute", bottom: 0, [blue ? "right" : "left"]: -14, transform: blue ? undefined : "scaleX(-1)" }}>
        <path d="M0,0 C0,30 20,50 58,50 C34,40 40,18 40,0 Z" fill={bg} />
      </svg>
    </div>
  );
};

const Cta: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const typing = t > M.bubbleIA + 0.35 && t < M.bubbleLink + 0.05;
  return (
    <AbsoluteFill>
      <Halftone />
      <Bubble at={M.bubbleIA} blue x={WIDTH - 90 - 330} y={430}>
        <div style={{ color: "#fff", fontFamily: SANS, fontWeight: 600, fontSize: 150, letterSpacing: "-0.02em" }}>IA</div>
      </Bubble>
      {typing && (
        <div style={{ position: "absolute", left: 70, top: 790, width: 210, height: 100, borderRadius: 50, background: "#e9e9eb", display: "flex", alignItems: "center", justifyContent: "center", gap: 14 }}>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{ width: 22, height: 22, borderRadius: 11, background: "#8e8e93", opacity: 0.4 + 0.6 * Math.max(0, Math.sin(frame / 4 - i * 0.9)) }} />
          ))}
        </div>
      )}
      <Bubble at={M.bubbleLink} x={70} y={760} w={760}>
        <div style={{ fontFamily: SANS, fontWeight: 500, fontSize: 52, color: "#0a66d8", textDecoration: "underline", textUnderlineOffset: 8 }}>https://faceless.video/</div>
      </Bubble>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- áudio
const bedVolume = (frame: number) => {
  const t = frame / FPS;
  let duck = 0;
  for (const w of T.speech) {
    duck = Math.max(duck, interpolate(t, [w.start - 0.25, w.start - 0.05, w.end + 0.15, w.end + 0.6], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  }
  const tail = interpolate(t, [T.duration - 0.7, T.duration], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return 0.62 * (1 - 0.66 * duck) * tail;
};

const capY = (t: number) => {
  if (t < M.badge - 0.05) return 880;
  if (t < START.step1) return 1130;
  if (t < START.step3) return 1400;
  if (t < START.cta) return 1290;
  return 1330;
};

export const FacelessVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const fadeIn = ease(frame, [0, 4], [1, 0]);
  const fadeOut = ease(frame, [FACELESS_DURATION - 12, FACELESS_DURATION - 1], [0, 1]);
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <SceneSlide from={START.hook} to={START.step1} first><Hook /></SceneSlide>
      <SceneSlide from={START.step1} to={START.step2}><Step1 /></SceneSlide>
      <SceneSlide from={START.step2} to={START.step3}><Step2 /></SceneSlide>
      <SceneSlide from={START.step3} to={START.cta}><Step3 /></SceneSlide>
      <SceneSlide from={START.cta} to={T.duration} last><Cta /></SceneSlide>

      <BigCaptions yAt={capY} />
      <AbsoluteFill style={{ background: "#000", opacity: Math.max(fadeIn, fadeOut), pointerEvents: "none" }} />

      <Audio src={staticFile("faceless/narration.wav")} volume={1} />
      <Audio src={staticFile("faceless/bed.mp3")} volume={bedVolume} />
      <Audio src={staticFile("faceless/sfx.mp3")} volume={0.8} />
    </AbsoluteFill>
  );
};

void easeOut;
