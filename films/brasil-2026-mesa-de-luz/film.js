// Brasil 2026 — mesa de luz. Tudo em função de t (s). Mundo em mm, y para baixo.
import { clamp, lerp, seg, ss, eo, ei, eio, track, monotone } from '/core/lib.js';
import { createEngine } from './engine.js';
import NAR from './narration-timeline.json' with { type: 'json' };
import TSEL from './assets/tex/tse_lines.json' with { type: 'json' };

const W = innerWidth, H = innerHeight;
export const DUR = 30;
const SIG = '#FF5A1F', INK = '#15171A', PLATE = 'rgba(14,15,17,0.78)';
const D2R = Math.PI / 180;

// ---------- objetos (tamanho real aproximado, mm) ----------
const SLIDE_MOUNT = 7;
const OBJ = [
  { id: 'tse', src: 'assets/tex/tse.png', kind: 0, x: -40, y: -232, r: -1.5, hw: 105, hh: 148.5 },
  { id: 'congresso', src: 'assets/tex/congresso.jpg', kind: 1, x: 128, y: -262, r: 4, inner: [80, 120] },
  { id: 'flavio', src: 'assets/tex/flavio.jpg', kind: 1, x: -61, y: 58, r: -1, inner: [92, 119.5] },
  { id: 'lula', src: 'assets/tex/lula.jpg', kind: 1, x: 61, y: 58, r: 1, inner: [92, 119.5] },
  { id: 'urna', src: 'assets/tex/urna.jpg', kind: 1, x: -6, y: 292, r: -2.5, inner: [150, 100] },
];
for (const o of OBJ) {
  if (o.inner) { o.mount = SLIDE_MOUNT; o.hw = o.inner[0] / 2 + o.mount; o.hh = o.inner[1] / 2 + o.mount; }
  o.rr = o.r * D2R;
}
const byId = Object.fromEntries(OBJ.map(o => [o.id, o]));
const TABLE = [232, 432];

// ponto do objeto (uv 0..1 da imagem) → mundo
function o2w(id, u, v) {
  const o = byId[id], iw = o.inner ? o.inner[0] / 2 : o.hw, ih = o.inner ? o.inner[1] / 2 : o.hh;
  const lx = (u - .5) * 2 * iw, ly = (v - .5) * 2 * ih, c = Math.cos(o.rr), s = Math.sin(o.rr);
  return [o.x + c * lx - s * ly, o.y + s * lx + c * ly];
}
const bandCenter = k => { const b = TSEL.lines[k]; return [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]; };

// ---------- câmera: [t, [x, y, zoom px/mm, roll graus]] ----------
const P_TSE = o2w('tse', .42, (TSEL.lines.c22[1] + TSEL.lines.c13[3]) / 2);
const P_DOME = o2w('congresso', .44, .5);
const P_CONF = o2w('urna', .553, .672);
const tseC = o2w('tse', .5, .42), conC = o2w('congresso', .5, .5), urC = o2w('urna', .5, .5);
const CAM = track([
  [0.0, [P_TSE[0] + 4, P_TSE[1] + 6, 3.35, -2.5]],
  [2.2, [tseC[0], tseC[1] - 8, 2.55, -1.5]],
  [4.6, [tseC[0] + 2, tseC[1] - 4, 2.62, -1.5]],
  [5.9, [conC[0] - 2, conC[1] - 110, 3.05, 3.0]],
  [9.4, [conC[0], conC[1] - 104, 3.18, 3.2]],
  [10.2, [conC[0] - 4, conC[1] - 100, 3.1, 3.0]],
  [12.6, [conC[0] - 10, conC[1] - 92, 3.0, 2.6]],
  [13.6, [0, 182, 4.35, 0]],
  [20.4, [0, 182, 4.42, 0]],
  [21.6, [urC[0], urC[1] - 18, 3.05, -2.0]],
  [23.6, [urC[0] + 3, urC[1] - 14, 3.2, -2.0]],
  [26.6, [P_CONF[0] - 2, P_CONF[1] - 4, 3.75, -2.6]],
  [27.3, [P_CONF[0] - 6, P_CONF[1] - 12, 3.1, -2.2]],
  [28.6, [0, 0, 2.06, 0]],
  [30.0, [0, 0, 2.03, 0]],
]);
const cam = t => { const [x, y, z, r] = CAM(t); return { x, y, z, roll: r * D2R }; };
function w2s(c, w) {
  const dx = (w[0] - c.x) * c.z, dy = (w[1] - c.y) * c.z, cs = Math.cos(c.roll), sn = Math.sin(c.roll);
  return [W / 2 + cs * dx - sn * dy, H / 2 + sn * dx + cs * dy];
}

// ---------- lupa: mergulhos ----------
// P mundo; on = presença; lift 0 apoiada / 1 no ar; R raio (px); open 0 lente / 1 fotografia
const DIVES = [
  { P: P_TSE, M: 2.5, R: monotone([[0, 1500], [0.4, 1500], [2.2, 300]]), open: monotone([[0, 1], [0.4, 1], [1.8, 0]]),
    on: t => 1 - seg(t, 2.75, 3.05), lift: t => eo(seg(t, 2.55, 3.0)) },
  { P: P_DOME, M: 2.2, R: () => 290, open: () => 0,
    on: t => seg(t, 5.55, 5.75) * (1 - seg(t, 9.55, 9.8)), lift: t => 1 - eo(seg(t, 5.6, 6.0)) + eo(seg(t, 9.35, 9.75)) },
  { P: P_CONF, M: 2.3, R: monotone([[21.8, 300], [23.6, 300], [24.6, 1800], [26.6, 1800], [27.3, 300]]),
    open: monotone([[23.6, 0], [24.5, 1], [26.6, 1], [27.2, 0]]),
    on: t => seg(t, 21.35, 21.55) * (1 - seg(t, 27.55, 27.8)), lift: t => 1 - eo(seg(t, 21.4, 21.8)) + eo(seg(t, 27.3, 27.7)) },
];
function lensAt(t, c) {
  for (const d of DIVES) {
    const on = d.on(t);
    if (on <= 0) continue;
    const lift = clamp(d.lift(t)), s = w2s(c, d.P);
    return { x: s[0], y: s[1], R: d.R(t) * (1 + .35 * lift), M: d.M, on, lift, open: clamp(d.open(t)), k: .16, P: d.P };
  }
  return { x: 0, y: 0, R: 1, M: 1, on: 0, lift: 0, open: 0, k: .16, P: [0, 0] };
}
// ponto do mundo visto através da lente (para marcas dentro dela)
const thruLens = (c, L, w) => {
  const dx = (w[0] - L.P[0]) * c.z * L.M, dy = (w[1] - L.P[1]) * c.z * L.M, cs = Math.cos(c.roll), sn = Math.sin(c.roll);
  return [L.x + cs * dx - sn * dy, L.y + sn * dx + cs * dy];
};

// ---------- eventos de som (lidos pelo mix.py) ----------
export const EV = [
  { t: 0.0, type: 'hum' },
  { t: 0.4, type: 'rise' },
  { t: 2.6, type: 'lift' }, { t: 2.9, type: 'card' }, { t: 3.6, type: 'tick' }, { t: 3.9, type: 'tick' },
  { t: 5.0, type: 'glide' }, { t: 6.0, type: 'land' }, { t: 6.4, type: 'click' },
  { t: 7.3, type: 'card' }, { t: 7.9, type: 'pen' }, { t: 8.6, type: 'card' }, { t: 9.2, type: 'pen' },
  { t: 9.55, type: 'lift' }, { t: 10.0, type: 'card' },
  ...[10.2, 10.65, 11.1, 11.55, 12.0].map(t => ({ t, type: 'tick' })),
  { t: 12.7, type: 'glide' }, { t: 14.2, type: 'click2' }, { t: 17.2, type: 'pen' }, { t: 17.35, type: 'pen' },
  { t: 20.5, type: 'glide' }, { t: 21.8, type: 'land' }, { t: 23.6, type: 'into' }, { t: 24.6, type: 'room' },
  { t: 25.7, type: 'beep' }, { t: 26.6, type: 'silence' }, { t: 27.15, type: 'off' }, { t: 27.0, type: 'rise' }, { t: 27.4, type: 'pen' },
  { t: 27.4, type: 'final' }, ...[27.7, 27.9, 28.1, 28.3, 28.5].map(t => ({ t, type: 'click' })),
];

// ---------- legendas: uma por fala medida ----------
const CUES = NAR.speech.map((s, i) => {
  const words = NAR.pages.filter(p => p.start >= s.start - .05 && p.start < s.end).flatMap(p => p.words.map(w => w.w));
  const next = NAR.speech[i + 1];
  return { t0: s.start, t1: next ? Math.max(s.end + .25, next.start - .06) : s.end + .6, text: words.join(' ') };
});
export const SUBS = CUES;

// ---------- desenho 2D ----------
let X, TXT = [];
const font = (w, px, fam) => `${w} ${px}px ${fam}`;
const MONO = '"Plex"', SANS = '"Inter"', SERIF = '"News"';
function text(id, s, x, y, f, col, align = 'left', a = 1, track = 0) {
  if (a <= 0) return;
  X.save(); X.globalAlpha *= a; X.font = f; X.fillStyle = col; X.textAlign = align; X.textBaseline = 'alphabetic';
  if (track) X.letterSpacing = track + 'px';
  X.fillText(s, x, y);
  const m = X.measureText(s), w = m.width, x0 = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
  if (a > .9) TXT.push({ id, text: s, x0, y0: y - m.actualBoundingBoxAscent, x1: x0 + w, y1: y + m.actualBoundingBoxDescent });
  X.restore();
}
function plate(x, y, w, h, a = 1, edge = false) {
  if (a <= 0) return;
  X.save(); X.globalAlpha *= a; X.fillStyle = PLATE;
  X.beginPath(); X.roundRect(x, y, w, h, 6); X.fill();
  if (edge) { X.fillStyle = SIG; X.fillRect(x, y, w, 3); }
  X.restore();
}
function anchor(p, a = 1, ring = 1) {
  if (a <= 0) return;
  X.save(); X.globalAlpha *= a; X.strokeStyle = SIG; X.fillStyle = SIG; X.lineWidth = 2.5;
  X.beginPath(); X.arc(p[0], p[1], 5, 0, 7); X.fill();
  X.beginPath(); X.arc(p[0], p[1], 14 * ring, 0, 7); X.stroke(); X.restore();
}
function leader(a, b, p) {
  if (p <= 0) return;
  X.save(); X.strokeStyle = SIG; X.lineWidth = 2;
  X.beginPath(); X.moveTo(a[0], a[1]); X.lineTo(lerp(a[0], b[0], p), lerp(a[1], b[1], p)); X.stroke(); X.restore();
}
// texto que entra pela lateral (wipe a partir do lado do conector)
function wipe(p, x, y, w, h, fn) {
  if (p <= 0) return;
  X.save(); X.beginPath(); X.rect(x, y, w * eo(p), h); X.clip(); fn(); X.restore();
}
const fadeIO = (t, a, b, fi = .3, fo = .3) => Math.min(seg(t, a, a + fi), 1 - seg(t, b - fo, b));

// risco de caneta circulando uma palavra (veredito)
function penRing(cx, cy, rw, rh, p) {
  if (p <= 0) return;
  X.save(); X.strokeStyle = SIG; X.lineWidth = 3; X.lineCap = 'round';
  X.beginPath();
  const n = 60, end = Math.floor(n * 1.08 * clamp(p));
  for (let i = 0; i <= end; i++) {
    const a = -2.6 + i / n * Math.PI * 2, wob = 1 + .03 * Math.sin(i * .7);
    const x = cx + Math.cos(a) * rw * wob, y = cy + Math.sin(a) * rh * wob - i * .08;
    i ? X.lineTo(x, y) : X.moveTo(x, y);
  }
  X.stroke(); X.restore();
}

function countUp(s, p) {        // "47,03" contando até o valor
  const v = parseFloat(s.replace(',', '.')) * eo(p);
  return v.toFixed(2).replace('.', ',');
}

// ---------- seções ----------
function secTSE(t, c, L) {
  // anotação dentro da lente (abertura) e cartão de leitura
  const a = fadeIO(t, 2.75, 5.15, .25, .35);
  const p22 = L.on > 0 ? thruLens(c, L, o2w('tse', TSEL.lines.c22[2], bandCenter('c22')[1])) : w2s(c, o2w('tse', TSEL.lines.c22[2], bandCenter('c22')[1]));
  const ia = 1 - seg(t, 1.6, 2.1);
  if (ia > 0) {
    anchor([p22[0] + 8, p22[1]], ia * seg(t, .2, .5));
    const p13 = thruLens(c, L, o2w('tse', TSEL.lines.c13[2], bandCenter('c13')[1]));
    anchor([p13[0] + 8, p13[1]], ia * seg(t, .35, .65));
  }
  if (a <= 0) return;
  const x = 64, y = 170, w = W - 128, h = 410;
  const s = w2s(c, o2w('tse', TSEL.lines.c22[2] - .02, bandCenter('c22')[1]));
  anchor(s, a);
  leader(s, [s[0], y + h], seg(t, 2.75, 3.0) * a);
  plate(x, y, w, h, a);
  const cp = seg(t, 2.9, 3.6);
  X.save(); X.globalAlpha = a;
  text('l1', '1º TURNO · PRESIDENTE · 04/10/2026', x + 36, y + 58, font(600, 24, SANS), '#C9CCD0', 'left', 1, 2.5);
  wipe(seg(t, 2.85, 3.25), x, y + 70, w, 150, () => {
    text('n1', '47,03%', x + 36, y + 170, font(600, 92, MONO), '#FFFFFF');
    text('c1', 'FLÁVIO BOLSONARO (PL)', x + 420, y + 160, font(600, 30, SANS), '#FFFFFF');
  });
  wipe(seg(t, 3.15, 3.55), x, y + 190, w, 130, () => {
    text('n2', '45,16%', x + 36, y + 282, font(600, 92, MONO), '#FFFFFF');
    text('c2', 'LULA (PT)', x + 420, y + 272, font(600, 30, SANS), '#FFFFFF');
  });
  text('s1', 'TSE · arquivo oficial br-c0001-e006257-u.json', x + 36, y + 342, font(400, 20, MONO), '#9AA0A6');
  text('s2', 'totalização 05/10/2026 12:51 · 100% das seções', x + 36, y + 372, font(400, 20, MONO), '#9AA0A6');
  X.restore();
}

const CASES = [
  { at: 7.3, y: 150, lab: 'AÇÃO PENAL 470 · STF', read: 'CONDENAÇÃO', sub: 'julgamento iniciado em 02/08/2012 · réus condenados', src: 'Fonte: STF, Ação Penal 470' },
  { at: 8.6, y: 392, lab: 'OPERAÇÃO LAVA JATO · POLÍCIA FEDERAL', read: 'INVESTIGAÇÃO', sub: 'deflagrada em 17/03/2014 · originou vários processos', src: 'Fonte: Polícia Federal / MPF' },
];
const LEGEND = [
  ['INVESTIGAÇÃO', 'apuração de fatos; não implica culpa'],
  ['DENÚNCIA', 'acusação formal do Ministério Público'],
  ['CONDENAÇÃO', 'decisão judicial de culpa'],
  ['ANULADA', 'sem efeito por vício processual'],
  ['ARQUIVADA', 'encerrada sem julgamento'],
];
function secCases(t, c, L) {
  const end = 12.75;
  // rótulo do objeto dentro da lente
  if (L.on > 0 && t < 9.7) {
    const p = thruLens(c, L, o2w('congresso', .44, .44));
    const a = fadeIO(t, 6.2, 9.6, .25, .25);
    anchor(p, a);
    leader(p, [p[0], p[1] + 330], seg(t, 6.2, 6.6) * a);
  }
  const la = fadeIO(t, 6.3, end, .25, .4);
  if (la > 0) {
    const s = w2s(c, o2w('congresso', .5, 1.0));
    X.save(); X.globalAlpha = la;
    text('cn', 'CONGRESSO NACIONAL · BRASÍLIA', W / 2, Math.min(s[1] + 70, 1500), font(600, 24, SANS), INK, 'center', 1, 2.5);
    X.restore();
  }
  for (const k of CASES) {
    const a = fadeIO(t, k.at, end, .3, .4);
    if (a <= 0) continue;
    const x = 64, w = W - 128, h = 220, y = k.y;
    plate(x, y, w, h, a);
    X.save(); X.globalAlpha = a;
    text(k.lab, k.lab, x + 32, y + 48, font(600, 22, SANS), '#C9CCD0', 'left', 1, 2.2);
    wipe(seg(t, k.at + .05, k.at + .45), x, y + 60, w, 80, () => text(k.read, k.read, x + 32, y + 120, font(600, 60, MONO), SIG));
    text(k.sub, k.sub, x + 32, y + 162, font(400, 23, SANS), '#E6E7E9');
    text(k.src, k.src, x + 32, y + 196, font(400, 18, MONO), '#9AA0A6');
    X.restore();
    penRing(x + 32 + 210, y + 100, 230, 46, seg(t, k.at + .6, k.at + 1.0) * a);
  }
  const ga = fadeIO(t, 10.0, end, .3, .4);
  if (ga > 0) {
    const x = 64, y = 634, w = W - 128, h = 300;
    plate(x, y, w, h, ga);
    X.save(); X.globalAlpha = ga;
    text('lg', 'O QUE CADA STATUS SIGNIFICA', x + 32, y + 46, font(600, 22, SANS), '#C9CCD0', 'left', 1, 2.2);
    LEGEND.forEach(([s, m], i) => {
      const p = seg(t, 10.2 + i * .45, 10.5 + i * .45);
      wipe(p, x, y + 60 + i * 46, w, 46, () => {
        text('lg' + i, s, x + 32, y + 96 + i * 46, font(600, 26, MONO), i === 2 ? SIG : '#FFFFFF');
        text('lm' + i, m, x + 300, y + 96 + i * 46, font(400, 24, SANS), '#E6E7E9');
      });
    });
    X.restore();
  }
}

const COLS = [
  { id: 'flavio', name: 'Flávio Bolsonaro', role: 'PL · senador pelo RJ', pct: '47,03%', credit: 'foto oficial: Agência Senado',
    title: 'Caso “rachadinha” (Alerj)', lines: ['Denúncia do MP-RJ (2020)', 'STJ anulou decisões da', '1ª instância · 09/11/2021', 'TJ-RJ arquivou a denúncia', 'a pedido do MP-RJ · 16/05/2022'],
    status: 'ARQUIVADA', src: 'Fontes: STJ (5ª Turma); TJ-RJ' },
  { id: 'lula', name: 'Lula', role: 'PT · presidente da República', pct: '45,16%', credit: 'foto oficial: Ricardo Stuckert/PR · CC BY 2.0',
    title: 'Lava Jato (tríplex e Atibaia)', lines: ['Condenações da 13ª Vara', 'de Curitiba anuladas por', 'incompetência · 08/03/2021', 'Plenário do STF confirmou', 'a anulação · 15/04/2021'],
    status: 'ANULADA', src: 'Fonte: STF (HC 193.726)' },
];
function secCols(t, c) {
  const a = fadeIO(t, 13.5, 20.7, .35, .45);
  if (a <= 0) return;
  COLS.forEach((k, i) => {
    const x = i ? W / 2 + 10 : 34, w = W / 2 - 44, cp = seg(t, 14.2, 14.6);
    const bot = w2s(c, o2w(k.id, .5, 1.0));
    const top = Math.max(bot[1] + SLIDE_MOUNT * c.z + 18, 0);
    // etiqueta presa ao retrato
    const tag = w2s(c, o2w(k.id, .5, 1.0));
    X.save(); X.globalAlpha = a;
    text('cr' + i, k.credit, x + w / 2, top + 4 - SLIDE_MOUNT * c.z + 0, font(400, 13, MONO), '#5A5F66', 'center');
    X.restore();
    const y = top + 18, h = 600;
    plate(x, y, w, h, a * cp);
    X.save(); X.globalAlpha = a * cp;
    anchor([tag[0], y], 1);
    text('nm' + i, k.name, x + 26, y + 52, font(600, 34, SANS), '#FFFFFF');
    text('rl' + i, k.role, x + 26, y + 86, font(400, 21, SANS), '#C9CCD0');
    text('pc' + i, '1º turno · ' + k.pct, x + 26, y + 120, font(500, 22, MONO), '#FFFFFF');
    X.fillStyle = '#3A3E44'; X.fillRect(x + 26, y + 142, w - 52, 1.5);
    text('tt' + i, k.title, x + 26, y + 182, font(600, 23, SANS), '#FFFFFF');
    k.lines.forEach((l, j) => {
      const p = seg(t, 14.9 + j * .32, 15.25 + j * .32);
      wipe(p, x, y + 196 + j * 34, w, 36, () => text('ln' + i + j, l, x + 26, y + 222 + j * 34, font(400, 21, SANS), '#E6E7E9'));
    });
    const sp = seg(t, 17.0, 17.25);
    wipe(sp, x, y + 390, w, 70, () => text('st' + i, k.status, x + 26, y + 446, font(600, 44, MONO), SIG));
    text('ng' + i, 'Nega irregularidades.', x + 26, y + 500, font(400, 21, SANS), '#C9CCD0', 'left', seg(t, 17.6, 17.9));
    text('sr' + i, k.src, x + 26, y + 538, font(400, 16, MONO), '#9AA0A6', 'left', seg(t, 17.6, 17.9));
    X.restore();
    penRing(x + 26 + (k.status.length * 13.2), y + 431, k.status.length * 15.5, 38, seg(t, 17.2 + i * .15, 17.6 + i * .15) * a);
  });
}

function secUrna(t, c, L) {
  if (L.on <= 0 || t < 22 || t > 27.2) return;
  const a = fadeIO(t, 24.4, 26.9, .35, .3);
  const p = thruLens(c, L, o2w('urna', .553, .672));
  anchor(p, fadeIO(t, 22.1, 26.9, .25, .3));
  if (a <= 0) return;
  const x = 64, y = 200, w = W - 128, h = 170;
  leader(p, [p[0], y + h], seg(t, 24.4, 24.8) * a);
  plate(x, y, w, h, a);
  X.save(); X.globalAlpha = a;
  text('u1', 'URNA ELETRÔNICA · MODELO UE2020', x + 32, y + 52, font(600, 24, SANS), '#C9CCD0', 'left', 1, 2.2);
  wipe(seg(t, 24.5, 24.9), x, y + 60, w, 70, () => text('u2', 'CONFIRMA', x + 32, y + 116, font(600, 56, MONO), SIG));
  text('u3', 'foto: TSE · domínio público', x + 32, y + 150, font(400, 18, MONO), '#9AA0A6');
  X.restore();
}

const INDEX = [
  ['tse', 'TSE', 'br-c0001-e006257-u.json · 05/10/2026'],
  ['congresso', 'CONGRESSO', 'foto Pedro França/Ag. Senado · CC BY 2.0'],
  ['flavio', 'FLÁVIO B.', 'foto oficial · Agência Senado'],
  ['lula', 'LULA', 'foto oficial R. Stuckert/PR · CC BY 2.0'],
  ['urna', 'URNA', 'foto TSE · domínio público'],
];
function secEnd(t, c) {
  if (t < 27.3) return;
  // texto final sobre a mesa: tinta
  const x = 70;
  X.save();
  const r1 = seg(t, 27.4, 27.75), r2 = seg(t, 27.9, 28.25);
  let fz = 80; X.font = font(600, fz, SERIF);
  while (X.measureText('OS FATOS PERMANECEM.').width > W - 2 * x && fz > 40) X.font = font(600, --fz, SERIF);
  wipe(r1, x - 10, 160, W, 120, () => text('f1', 'O PODER PASSA.', x, 250, font(600, fz, SERIF), '#F4F3EF'));
  wipe(r2, x - 10, 262, W, 120, () => text('f2', 'OS FATOS PERMANECEM.', x, 350, font(600, fz, SERIF), SIG));
  X.fillStyle = SIG; X.fillRect(x, 384, (W - 2 * x) * eo(seg(t, 28.2, 28.7)), 4);
  X.restore();
  // índice: cada etiqueta sai do seu objeto e entra na lista
  const ix = 64, iy = 1180, iw = W - 128, rh = 50;
  const pa = seg(t, 27.6, 27.9);
  plate(ix, iy, iw, 80 + INDEX.length * rh, pa);
  X.save(); X.globalAlpha = pa;
  text('ix', 'ÍNDICE DA MESA · FONTES', ix + 28, iy + 46, font(600, 21, SANS), '#C9CCD0', 'left', 1, 2.2);
  X.restore();
  INDEX.forEach(([id, a, b], i) => {
    const p = eio(seg(t, 27.7 + i * .2, 28.15 + i * .2));
    if (p <= 0) return;
    const from = w2s(c, o2w(id, .5, .5)), to = [ix + 28, iy + 92 + i * rh];
    const px = lerp(from[0], to[0], p), py = lerp(from[1], to[1], p);
    if (p < 1) anchor([px, py], 1);
    X.save(); X.globalAlpha = p;
    text('i' + i, a, px, py, font(600, 22, MONO), SIG);
    text('j' + i, b, px + 170, py, font(400, 20, MONO), '#E6E7E9');
    X.restore();
  });
  const sa = seg(t, 28.7, 29.0);
  X.save(); X.globalAlpha = sa;
  text('fs', 'Fontes: TSE · STF · STJ · TJ-RJ · PF/MPF', x, 440, font(500, 22, MONO), '#E6E7E9');
  text('fv', 'verificado em 20/10/2026 · conteúdo informativo e apartidário', x, 474, font(400, 20, MONO), '#9AA0A6');
  X.restore();
}

function subtitles(t) {
  const c = CUES.find(k => t >= k.t0 - .05 && t < k.t1);
  if (!c) return;
  const a = Math.min(seg(t, c.t0 - .05, c.t0 + .08), 1 - seg(t, c.t1 - .1, c.t1));
  X.save(); X.font = font(600, 40, SANS);
  const lines = wrap(c.text, W - 200);
  const lh = 54, h = lines.length * lh + 34, w = Math.max(...lines.map(l => X.measureText(l).width)) + 64;
  const y = 1640 - h;
  plate(W / 2 - w / 2, y, w, h, a, true);
  X.globalAlpha = a;
  lines.forEach((l, i) => text('sub' + i, l, W / 2, y + 17 + 41 + i * lh, font(600, 40, SANS), '#FFFFFF', 'center'));
  X.restore();
}
function wrap(s, max) {
  const out = []; let cur = '';
  for (const w of s.split(' ')) { const n = cur ? cur + ' ' + w : w; if (X.measureText(n).width > max && cur) { out.push(cur); cur = w; } else cur = n; }
  if (cur) out.push(cur);
  return out;
}

// ---------- estado da imagem ----------
let E, SC;
function picture(t) {
  const c = cam(t), L = lensAt(t, c);
  const band22 = TSEL.lines.c22, band13 = TSEL.lines.c13;
  const objs = OBJ.map((o, i) => {
    const r = { x: o.x, y: o.y, r: o.rr, hw: o.hw, hh: o.hh, su: SC[i][0], sv: SC[i][1], kind: o.kind, mount: o.mount || 0, op: 1 };
    if (o.id === 'tse') { r.band = [band22[0], band22[1], Math.max(band22[2], band13[2]), band13[3]]; r.bandOn = 1 - seg(t, 4.8, 5.6); }
    return r;
  });
  E.draw({ cam: c, on: 1 - .86 * ss(seg(t, 26.9, 27.7)), table: TABLE, objs, lens: L, vig: .2 });
  return { c, L };
}

export async function init() {
  const g = document.getElementById('g'), o = document.getElementById('o');
  g.width = o.width = W; g.height = o.height = H;
  const gl = g.getContext('webgl2', { preserveDrawingBuffer: true, antialias: true });
  E = createEngine(gl, W, H);
  X = o.getContext('2d');
  const imgs = await Promise.all(OBJ.map(ob => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = ob.src; })));
  SC = E.upload(imgs);
  await Promise.all([font(400, 20, MONO), font(500, 20, MONO), font(600, 20, MONO), font(400, 20, SANS), font(600, 20, SANS), font(600, 20, SERIF)].map(f => document.fonts.load(f, 'ÁÇÕ%º')));
}

export function render(t) {
  t = clamp(t, 0, DUR - 1e-6);
  const { c, L } = picture(t);
  X.clearRect(0, 0, W, H); TXT = [];
  secTSE(t, c, L);
  secCases(t, c, L);
  secCols(t, c);
  secUrna(t, c, L);
  secEnd(t, c);
  subtitles(t);
}
export const texts = t => { render(t); return TXT.slice(); };
