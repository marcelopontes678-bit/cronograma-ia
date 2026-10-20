import { AbsoluteFill, useCurrentFrame } from "remotion";
import { FPS } from "../config";
import { SANS } from "../fonts";
import { ease } from "../lib/motion";
import { GREEN, GREEN_DEEP, SCREEN, T } from "./parts";

const W = SCREEN.w;
const H = SCREEN.h;

const StatusBar: React.FC<{ dark?: boolean }> = ({ dark = true }) => (
  <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 78, padding: "26px 44px 0", display: "flex", justifyContent: "space-between", fontFamily: SANS, fontWeight: 700, fontSize: 26, color: dark ? "#fff" : "#000" }}>
    <span>9:41</span>
    <span style={{ display: "flex", gap: 10, alignItems: "center" }}>
      <span style={{ width: 30, height: 16, border: "3px solid currentColor", borderRadius: 5, position: "relative" }}>
        <span style={{ position: "absolute", left: 2, top: 2, bottom: 2, width: 18, background: "currentColor", borderRadius: 2 }} />
      </span>
    </span>
  </div>
);

const BrowserBar: React.FC = () => (
  <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 120, background: "#1c1c1e", borderTop: "1px solid #333", display: "flex", justifyContent: "space-around", alignItems: "center", color: "#7a7a80", fontFamily: SANS, fontSize: 36 }}>
    <span>‹</span><span>›</span><span>+</span><span>▢</span><span>···</span>
  </div>
);

/** Anel de toque (dedo) em volta de um ponto. */
export const TapRing: React.FC<{ x: number; y: number; at: number }> = ({ x, y, at }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS - at;
  if (t < -0.25 || t > 0.7) return null;
  const grow = ease(t, [0, 0.5], [0, 1]);
  const dot = ease(t, [-0.25, 0], [0, 1]) * (1 - ease(t, [0.35, 0.7], [0, 1]));
  return (
    <>
      <div style={{ position: "absolute", left: x - 34, top: y - 34, width: 68, height: 68, borderRadius: 40, background: "rgba(255,255,255,0.55)", opacity: dot, transform: `scale(${1 - 0.2 * ease(t, [-0.05, 0.05], [0, 1])})` }} />
      <div style={{ position: "absolute", left: x - 90 * grow, top: y - 90 * grow, width: 180 * grow, height: 180 * grow, borderRadius: 100, border: "5px solid rgba(255,255,255,0.8)", opacity: 1 - grow }} />
    </>
  );
};

// -------------------------------------------------------------- 1) busca no navegador
export const SearchScreen: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const url = "faceless.video";
  const n = Math.round(ease(t, [T.marks.typeUrl - 0.15, T.marks.typeUrl + 0.85], [0, url.length]));
  const rows = [
    ["faceless.video", "Abrir site"],
    ["Faceless — criar vídeos", "faceless.video"],
    ["Painel", "faceless.video/painel"],
    ["Criar uma série", "faceless.video/criar"],
  ];
  return (
    <AbsoluteFill style={{ background: "#0e0e10", fontFamily: SANS }}>
      <StatusBar />
      <div style={{ position: "absolute", left: 28, right: 28, top: 110, height: 78, borderRadius: 20, background: "#2c2c30", display: "flex", alignItems: "center", padding: "0 26px", color: "#fff", fontSize: 34, fontWeight: 500 }}>
        <span style={{ opacity: 0.6, marginRight: 16 }}>⌕</span>
        <span>{url.slice(0, n)}</span>
        <span style={{ width: 3, height: 40, background: "#4aa3ff", marginLeft: 3, opacity: Math.floor(frame / 8) % 2 }} />
      </div>
      {n > 2 && rows.map((r, i) => (
        <div key={i} style={{ position: "absolute", left: 28, right: 28, top: 230 + i * 128, display: "flex", alignItems: "center", gap: 26, opacity: ease(t, [T.marks.typeUrl + 0.1 + i * 0.07, T.marks.typeUrl + 0.3 + i * 0.07], [0, 1]) }}>
          <div style={{ width: 62, height: 62, borderRadius: 31, background: i === 0 ? GREEN_DEEP : "#2c2c30", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 30 }}>{i === 0 ? "◎" : "⌕"}</div>
          <div>
            <div style={{ color: "#fff", fontSize: 32, fontWeight: 600 }}>{r[0]}</div>
            <div style={{ color: "#8e8e93", fontSize: 24 }}>{r[1]}</div>
          </div>
        </div>
      ))}
    </AbsoluteFill>
  );
};

// -------------------------------------------------------------- 2) página inicial com botão
export const HeroScreen: React.FC<{ tapAt: number }> = ({ tapAt }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const press = ease(t, [tapAt - 0.05, tapAt + 0.05], [0, 1]) * (1 - ease(t, [tapAt + 0.2, tapAt + 0.45], [0, 1]));
  return (
    <AbsoluteFill style={{ background: "#070907", fontFamily: SANS }}>
      <div style={{ position: "absolute", left: -140, top: 120, width: 420, height: 700, background: "radial-gradient(circle, rgba(34,224,90,0.5), rgba(0,0,0,0) 70%)", filter: "blur(20px)" }} />
      <StatusBar />
      <div style={{ position: "absolute", left: 40, right: 40, top: 200, textAlign: "center", color: "#fff", fontWeight: 900, fontSize: 68, lineHeight: 1.05, letterSpacing: "-0.02em" }}>
        Crie contas<br />sem rosto<br /><span style={{ color: GREEN }}>com um clique</span>
      </div>
      <div style={{ position: "absolute", left: 60, right: 60, top: 520, textAlign: "center", color: "#9aa39d", fontSize: 25, lineHeight: 1.35 }}>
        Use IA para criar e postar vídeos personalizados todos os dias.
      </div>
      <div style={{ position: "absolute", left: W / 2 - 160, top: 640, width: 320, height: 84, borderRadius: 14, background: GREEN, display: "flex", alignItems: "center", justifyContent: "center", color: "#04210e", fontWeight: 800, fontSize: 28, letterSpacing: "0.04em", transform: `scale(${1 - 0.07 * press})`, boxShadow: `0 0 ${30 + 30 * press}px rgba(34,224,90,0.7)` }}>
        COMEÇAR GRÁTIS
      </div>
      {[0, 1, 2].map((i) => (
        <div key={i} style={{ position: "absolute", left: 40 + i * 168, top: 800, width: 150, height: 250, borderRadius: 18, background: ["linear-gradient(160deg,#1c3a6e,#e0603a)", "linear-gradient(160deg,#2a2f3a,#b5a642)", "linear-gradient(160deg,#102a4a,#f08a3c)"][i] }} />
      ))}
      <BrowserBar />
      <TapRing x={W / 2} y={682} at={tapAt} />
    </AbsoluteFill>
  );
};

// -------------------------------------------------------------- 3) fundos de vídeo
export const BackgroundsScreen: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const sel = ease(t, [T.marks.bgList + 0.25, T.marks.bgList + 0.4], [0, 1]);
  const opts = ["Motivacional", "Histórias", "Filosofia", "Curiosidades"];
  return (
    <AbsoluteFill style={{ background: "#0c0c0e", fontFamily: SANS }}>
      <StatusBar />
      <div style={{ position: "absolute", left: 36, top: 130, color: "#fff", fontWeight: 800, fontSize: 46 }}>Tipo de série</div>
      {opts.map((o, i) => (
        <div key={o} style={{ position: "absolute", left: 36, right: 36, top: 210 + i * 86, height: 70, borderRadius: 14, background: i === 0 ? `rgba(34,224,90,${0.12 + 0.1 * sel})` : "#1a1a1e", border: `2px solid ${i === 0 ? GREEN : "#2a2a2e"}`, color: "#fff", fontSize: 28, fontWeight: 600, display: "flex", alignItems: "center", padding: "0 24px", justifyContent: "space-between" }}>
          <span>{o}</span>
          {i === 0 && <span style={{ color: GREEN }}>✓</span>}
        </div>
      ))}
      <div style={{ position: "absolute", left: 36, top: 590, color: "#fff", fontWeight: 800, fontSize: 40 }}>Fundos de vídeo</div>
      <div style={{ position: "absolute", left: 36, top: 645, color: "#8e8e93", fontSize: 22 }}>Gerado por IA ou gameplay</div>
      <div style={{ position: "absolute", left: 36, top: 700, width: 232, height: 300, borderRadius: 20, background: "radial-gradient(circle at 50% 40%, #1fd45a, #08451e)", border: `4px solid ${GREEN}`, boxShadow: "0 0 30px rgba(34,224,90,0.5)", display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 14 }}>
        <div style={{ fontSize: 70, fontWeight: 900, color: "#fff", letterSpacing: "-0.04em" }}>IA</div>
        <div style={{ color: "#fff", fontWeight: 700, fontSize: 22 }}>Gerado por IA ✦</div>
      </div>
      <div style={{ position: "absolute", left: 288, top: 700, width: 232, height: 300, borderRadius: 20, background: "linear-gradient(160deg,#b0402a,#f0a040,#314a8a)", display: "flex", alignItems: "flex-end", padding: 18, color: "#fff", fontWeight: 700, fontSize: 22 }}>
        Gameplay
      </div>
    </AbsoluteFill>
  );
};

// -------------------------------------------------------------- 4) vozes + criar série
export const VoicesScreen: React.FC<{ tapAt: number }> = ({ tapAt }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const voices = [["Onyx", "masculina"], ["Echo", "masculina"], ["Nova", "feminina"]];
  const choose = ease(t, [T.marks.voiceList + 0.3, T.marks.voiceList + 0.45], [0, 1]);
  const press = ease(t, [tapAt - 0.05, tapAt + 0.05], [0, 1]) * (1 - ease(t, [tapAt + 0.2, tapAt + 0.45], [0, 1]));
  return (
    <AbsoluteFill style={{ background: "#0c0c0e", fontFamily: SANS }}>
      <StatusBar />
      <div style={{ position: "absolute", left: 36, top: 130, color: "#fff", fontWeight: 800, fontSize: 46 }}>Narração</div>
      {voices.map((v, i) => (
        <div key={v[0]} style={{ position: "absolute", left: 36, right: 36, top: 220 + i * 120, height: 96, borderRadius: 18, background: i === 0 ? `rgba(34,224,90,${0.1 + 0.1 * choose})` : "#17171a", border: `2px solid ${i === 0 && choose > 0.5 ? GREEN : "#26262a"}`, display: "flex", alignItems: "center", padding: "0 26px", gap: 22 }}>
          <div style={{ width: 40, height: 40, borderRadius: 20, border: `4px solid ${i === 0 && choose > 0.5 ? GREEN : "#555"}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
            {i === 0 && choose > 0.5 && <div style={{ width: 18, height: 18, borderRadius: 9, background: GREEN }} />}
          </div>
          <div style={{ color: "#fff", fontSize: 32, fontWeight: 700 }}>{v[0]}</div>
          <div style={{ color: "#8e8e93", fontSize: 24 }}>({v[1]})</div>
          <div style={{ marginLeft: "auto", color: GREEN, fontSize: 22, fontWeight: 700 }}>▶ ouvir</div>
        </div>
      ))}
      <div style={{ position: "absolute", left: 36, top: 610, color: "#fff", fontWeight: 800, fontSize: 40 }}>Fonte da legenda</div>
      <div style={{ position: "absolute", left: 36, right: 36, top: 676, height: 96, borderRadius: 18, background: "#17171a", border: "2px solid #26262a", color: "#fff", fontSize: 40, fontWeight: 900, display: "flex", alignItems: "center", padding: "0 26px" }}>
        MOTIVACIONAL
      </div>
      <div style={{ position: "absolute", left: W / 2 - 190, top: 880, width: 380, height: 92, borderRadius: 16, background: GREEN, color: "#04210e", fontWeight: 800, fontSize: 30, letterSpacing: "0.04em", display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${1 - 0.07 * press})`, boxShadow: `0 0 ${30 + 30 * press}px rgba(34,224,90,0.7)` }}>
        CRIAR SÉRIE
      </div>
      <TapRing x={W / 2} y={926} at={tapAt} />
    </AbsoluteFill>
  );
};

// -------------------------------------------------------------- 5) conectar plataforma
export const ConnectScreen: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const tiles = [
    ["TikTok", "#101010", "♪"],
    ["YouTube", "#d62020", "▶"],
    ["Instagram", "#b53ab0", "◎"],
    ["E-mail", "#2c6df0", "@"],
  ];
  const sel = ease(t, [T.marks.tiktokTile, T.marks.tiktokTile + 0.25], [0, 1]);
  const done = ease(t, [T.marks.tiktokTile + 0.5, T.marks.tiktokTile + 0.7], [0, 1]);
  return (
    <AbsoluteFill style={{ background: "#0b0b0d", fontFamily: SANS }}>
      <StatusBar />
      <div style={{ position: "absolute", left: 36, right: 36, top: 130, color: "#fff", fontWeight: 800, fontSize: 48, lineHeight: 1.1 }}>
        Conecte sua primeira plataforma
      </div>
      <div style={{ position: "absolute", left: 36, right: 36, top: 262, color: "#8e8e93", fontSize: 23, lineHeight: 1.35 }}>
        Conecte TikTok, YouTube, Instagram ou e-mail para começar.
      </div>
      {tiles.map((tl, i) => {
        const col = i % 2;
        const row = Math.floor(i / 2);
        const isTik = i === 0;
        return (
          <div key={tl[0]} style={{ position: "absolute", left: 36 + col * 250, top: 360 + row * 260, width: 234, height: 236, borderRadius: 22, background: "#16161a", border: `3px solid ${isTik && sel > 0.4 ? GREEN : "#2a2a2e"}`, boxShadow: isTik && sel > 0.4 ? "0 0 36px rgba(34,224,90,0.5)" : undefined, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 20, transform: `scale(${isTik ? 1 + 0.04 * sel : 1})` }}>
            <div style={{ width: 96, height: 96, borderRadius: 26, background: tl[1], color: "#fff", fontSize: 54, fontWeight: 900, display: "flex", alignItems: "center", justifyContent: "center", border: "2px solid #333" }}>{tl[2]}</div>
            <div style={{ color: "#fff", fontWeight: 700, fontSize: 28 }}>{tl[0]}</div>
          </div>
        );
      })}
      <div style={{ position: "absolute", left: 36, right: 36, top: 900, height: 84, borderRadius: 16, background: "rgba(34,224,90,0.14)", border: `2px solid ${GREEN}`, color: GREEN, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: 30, opacity: done, transform: `translateY(${(1 - done) * 18}px)` }}>
        ✓ TikTok conectado
      </div>
    </AbsoluteFill>
  );
};

// -------------------------------------------------------------- 6) postagens automáticas
export const PostingScreen: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const rows = [["Hoje · 18:00", "Postado ✓", GREEN], ["Amanhã · 18:00", "Agendado", "#8e8e93"], ["Depois · 18:00", "Agendado", "#8e8e93"]];
  return (
    <AbsoluteFill style={{ background: "#0b0b0d", fontFamily: SANS }}>
      <StatusBar />
      <div style={{ position: "absolute", left: 36, top: 124, color: "#fff", fontWeight: 800, fontSize: 42 }}>Piloto automático</div>
      <div style={{ position: "absolute", left: 36, top: 190, width: 220, height: 390, borderRadius: 18, overflow: "hidden", border: `3px solid ${GREEN}` }}>
        <div style={{ position: "absolute", inset: 0 }}>{children}</div>
      </div>
      <div style={{ position: "absolute", left: 280, right: 30, top: 200, display: "flex", flexDirection: "column", gap: 16 }}>
        {rows.map((r, i) => (
          <div key={i} style={{ opacity: ease(t, [T.marks.connect + 3 + i * 0.5, T.marks.connect + 3.3 + i * 0.5], [0, 1]), height: 118, borderRadius: 16, background: "#17171a", border: "2px solid #26262a", padding: "16px 18px" }}>
            <div style={{ color: "#fff", fontSize: 24, fontWeight: 700 }}>{r[0]}</div>
            <div style={{ color: r[2] as string, fontSize: 24, fontWeight: 700, marginTop: 10 }}>{r[1]}</div>
          </div>
        ))}
      </div>
      <div style={{ position: "absolute", left: 36, right: 36, top: 660, height: 150, borderRadius: 18, background: "rgba(34,224,90,0.12)", border: `2px solid ${GREEN}`, color: "#fff", fontSize: 30, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center", lineHeight: 1.2 }}>
        Um vídeo novo<br />todos os dias
      </div>
    </AbsoluteFill>
  );
};
