// Entire soundtrack synthesized with the Web Audio API (OfflineAudioContext).
// No samples or audio files: oscillators, filters, envelopes and seeded noise only.
// Event times come from timeline.js, the same file the 3D scene reads.
import { EV, DURATION, LAUNCH_ACC } from './timeline.js';
import { mulberry32 } from './util.js';

const SR = 48000;

export async function renderSoundtrack({ stem = 'mix' } = {}) {
  const ctx = new OfflineAudioContext(2, SR * DURATION, SR);
  const rnd = mulberry32(2024);

  // ---------- buses ----------
  const master = ctx.createGain();
  master.gain.value = 0.9;
  const comp = ctx.createDynamicsCompressor();
  comp.threshold.value = -10;
  comp.knee.value = 8;
  comp.ratio.value = 4;
  comp.attack.value = 0.004;
  comp.release.value = 0.15;
  master.connect(comp).connect(ctx.destination);

  const music = ctx.createGain();   // music sits well under the effects
  const MUS = stem === 'sfx' ? 0 : 0.16;
  music.gain.value = MUS;
  // ducking: the music steps back under the key actions so they read clearly
  for (const [a, b] of [[4.25, 6.45], [12.1, 13.4], [10.1, 10.45]]) {
    music.gain.setValueAtTime(MUS, a - 0.08);
    music.gain.linearRampToValueAtTime(MUS * 0.6, a);
    music.gain.setValueAtTime(MUS * 0.6, b);
    music.gain.linearRampToValueAtTime(MUS, b + 0.15);
  }
  music.connect(master);
  const sfx = ctx.createGain();
  sfx.gain.value = stem === 'music' ? 0 : 0.85;
  sfx.connect(master);

  // small-room reverb from a synthesized impulse response
  const ir = ctx.createBuffer(2, SR * 1.4, SR);
  for (let c = 0; c < 2; c++) {
    const d = ir.getChannelData(c);
    for (let i = 0; i < d.length; i++) d[i] = (rnd() * 2 - 1) * Math.pow(1 - i / d.length, 3.2);
  }
  const verb = ctx.createConvolver();
  verb.buffer = ir;
  const verbGain = ctx.createGain();
  verbGain.gain.value = 0.22;
  verb.connect(verbGain).connect(master);

  // ---------- noise sources ----------
  const white = ctx.createBuffer(1, SR * 4, SR);
  {
    const d = white.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = rnd() * 2 - 1;
  }
  const brown = ctx.createBuffer(1, SR * 4, SR);
  {
    const d = brown.getChannelData(0), w = white.getChannelData(0);
    let last = 0;
    for (let i = 0; i < d.length; i++) {
      last = (last + 0.02 * w[i]) / 1.02;
      d[i] = last * 3.5;
    }
  }
  function noise(t, dur, buf = white) {
    const s = ctx.createBufferSource();
    s.buffer = buf;
    s.loop = true;
    s.start(t, rnd() * 3, dur + 0.05);
    return s;
  }

  // connects src -> [nodes...] -> gain(env) -> panner -> bus (+ reverb send)
  function chain(src, nodes, { bus = sfx, pan = 0, send = 0.3 } = {}) {
    let n = src;
    for (const x of nodes) n = n.connect(x);
    const g = ctx.createGain();
    g.gain.value = 0;
    n.connect(g);
    const p = ctx.createStereoPanner();
    p.pan.value = pan;
    g.connect(p).connect(bus);
    if (send > 0) {
      const sg = ctx.createGain();
      sg.gain.value = send;
      p.connect(sg).connect(verb);
    }
    return g.gain;
  }
  const filt = (type, freq, Q = 1) => {
    const f = ctx.createBiquadFilter();
    f.type = type;
    f.frequency.value = freq;
    f.Q.value = Q;
    return f;
  };
  // percussive envelope
  function perc(param, t, peak, attack, decay) {
    param.setValueAtTime(0, t);
    param.linearRampToValueAtTime(peak, t + attack);
    param.setTargetAtTime(0, t + attack, decay / 3);
  }
  // sustained envelope
  function hold(param, t, dur, peak, a = 0.02, r = 0.08) {
    param.setValueAtTime(0, t);
    param.linearRampToValueAtTime(peak, t + a);
    param.setValueAtTime(peak, t + Math.max(a, dur - r));
    param.linearRampToValueAtTime(0, t + dur);
  }
  const osc = (type, f, t, dur) => {
    const o = ctx.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(f, t);
    o.start(t);
    o.stop(t + dur + 0.05);
    return o;
  };
  const mtof = (m) => 440 * Math.pow(2, (m - 69) / 12);

  // =====================================================================
  //  MUSIC — synthesized pizzicato strings, 120 BPM, constant tempo
  // =====================================================================
  function pizz(t, midi, vel = 0.5, pan = 0, ring = 1) {
    const f = mtof(midi);
    const dec = (midi < 52 ? 0.55 : midi < 64 ? 0.4 : 0.3) * ring;
    const lp = filt('lowpass', 4500, 1.2);
    lp.frequency.setValueAtTime(Math.min(9000, f * 9), t);
    lp.frequency.setTargetAtTime(Math.max(300, f * 1.6), t + 0.005, 0.05);
    const body = filt('peaking', 420, 1.5);
    body.gain.value = 4;
    const g1 = chain(osc('triangle', f, t, dec * 2.5), [lp, body], { bus: music, pan, send: 0.35 });
    perc(g1, t, vel, 0.004, dec);
    const g2 = chain(osc('sawtooth', f * 1.003, t, dec * 2), [filt('lowpass', Math.min(8000, f * 5), 0.7)], { bus: music, pan, send: 0.35 });
    perc(g2, t, vel * 0.22, 0.003, dec * 0.6);
    // finger pluck transient
    const gc = chain(noise(t, 0.03), [filt('bandpass', Math.min(6000, f * 4), 2)], { bus: music, pan, send: 0 });
    perc(gc, t, vel * 0.25, 0.001, 0.015);
  }
  const chord = (t, notes, vel, pan = 0.15) => notes.forEach((n, i) => pizz(t + i * 0.008, n, vel, pan));
  const C = [60, 64, 67], F = [60, 65, 69], G7 = [59, 62, 65], Am = [57, 60, 64], G = [59, 62, 67], Fm = [60, 65, 68];

  // bass + off-beat chords per section
  const bassLine = [
    // [t, midi]
    [0, 48], [0.5, 43], [1.0, 48], [1.5, 43],
    [2.0, 41], [2.5, 48], [3.0, 41], [3.5, 48],
    [4.0, 43], [4.5, 50], [5.0, 43], [5.5, 50],
    [6.0, 41],
    [8.0, 45], [9.0, 40], [9.5, 45],
    [10.5, 48], [11.0, 43], [11.5, 48],
    [12.0, 41], [12.5, 48], [13.0, 43], [13.5, 50],
    [16.65, 36], [17.0, 48], [17.5, 43], [18.0, 41], [18.5, 48], [19.0, 36],
  ];
  for (const [t, m] of bassLine) pizz(t, m, 0.55, -0.2);
  const offbeats = (a, b, notes, vel = 0.32) => { for (let t = a + 0.25; t < b; t += 0.5) chord(t, notes, vel); };
  offbeats(0, 2, C); offbeats(2, 4, F); offbeats(4, 5.8, G7, 0.26);
  offbeats(10.5, 12, C); offbeats(12, 13, F); offbeats(13, 14, G);
  offbeats(17, 18, C); offbeats(18, 19, F);
  // melody
  const mel = [
    [0.0, 76], [0.5, 79], [0.75, 76], [1.0, 72], [1.25, 74], [1.5, 76], [1.75, 79],
    [2.0, 81], [2.5, 77], [2.75, 81], [3.0, 84], [3.25, 81], [3.5, 79], [3.75, 77],
    [4.0, 74, 0.35], [4.5, 74, 0.35], [5.0, 74, 0.4], [5.25, 76, 0.4], [5.5, 77, 0.45], [5.75, 77, 0.45], [6.0, 77, 0.3], [6.25, 77, 0.22],
    [8.5, 72, 0.32], [9.0, 71, 0.3], [9.5, 69, 0.3],
    [10.15, 72, 0.45], [10.2, 76, 0.45], [10.25, 79, 0.48], [10.3, 84, 0.5], [10.35, 88, 0.5],
    [11.0, 79], [11.25, 76], [11.5, 72], [11.75, 76],
    [12.0, 81, 0.4], [12.25, 79, 0.4], [12.5, 77, 0.4], [12.75, 81, 0.4], [13.0, 83, 0.4], [13.25, 79, 0.4], [13.5, 86, 0.45], [13.75, 83, 0.45],
    [17.0, 76], [17.25, 79], [17.5, 84], [17.75, 79], [18.0, 81], [18.25, 84], [18.5, 81], [18.75, 77],
  ];
  for (const [t, m, v] of mel) pizz(t, m, v ?? 0.5, 0.25);
  // build-up before the launch: repeated G pedal + climbing line, crescendo, then silence
  for (let i = 0; i < 8; i++) {
    const t = 14.0 + i * 0.125;
    pizz(t, 43, 0.35 + i * 0.06, -0.2);
    pizz(t, [62, 64, 66, 67, 69, 71, 72, 74][i], 0.3 + i * 0.05, 0.25);
  }
  // celebration: big strum at the first burst, final rolled chord that rings out
  chord(16.65, [48, 55, 60, 64, 67, 72], 0.6);
  [48, 55, 64, 67, 72, 76].forEach((n, i) => pizz(19.0 + i * 0.03, n, 0.55, (i - 2.5) * 0.12, 2.2));
  pizz(19.55, 84, 0.3, 0.3, 2);

  // =====================================================================
  //  SOUND EFFECTS
  // =====================================================================
  // metallic clank: inharmonic partials + click
  function clank(t, base = 520, vel = 0.6, pan = 0, decay = 0.35) {
    const ratios = [1, 2.32, 3.86, 5.41, 6.9];
    ratios.forEach((r, i) => {
      const g = chain(osc('sine', base * r * (1 + (rnd() - 0.5) * 0.01), t, decay * 2), [], { pan, send: 0.4 });
      perc(g, t, vel / (1 + i * 0.6), 0.001, decay / (1 + i * 0.35));
    });
    const gn = chain(noise(t, 0.05), [filt('bandpass', base * 4, 1.5)], { pan, send: 0.2 });
    perc(gn, t, vel * 0.6, 0.001, 0.03);
  }
  // soft thud (clay landing / pat)
  function thud(t, vel = 0.5, f0 = 150, pan = 0) {
    const o = osc('sine', f0, t, 0.25);
    o.frequency.exponentialRampToValueAtTime(f0 * 0.4, t + 0.15);
    const g = chain(o, [], { pan, send: 0.15 });
    perc(g, t, vel, 0.003, 0.12);
    const gn = chain(noise(t, 0.08, brown), [filt('lowpass', 500)], { pan, send: 0.1 });
    perc(gn, t, vel * 0.8, 0.002, 0.06);
  }
  // match strike: scratch + ignition whoosh
  function matchStrike(t, pan = 0) {
    const sc = filt('bandpass', 2500, 1.2);
    sc.frequency.setValueAtTime(1800, t - 0.12);
    sc.frequency.linearRampToValueAtTime(4500, t);
    const g = chain(noise(t - 0.12, 0.16), [sc], { pan, send: 0.2 });
    g.setValueAtTime(0, t - 0.12);
    g.linearRampToValueAtTime(0.7, t - 0.02);
    g.linearRampToValueAtTime(0, t + 0.03);
    const wl = filt('lowpass', 900);
    wl.frequency.setValueAtTime(400, t);
    wl.frequency.linearRampToValueAtTime(2200, t + 0.08);
    wl.frequency.linearRampToValueAtTime(700, t + 0.5);
    const gw = chain(noise(t, 0.6), [wl], { pan, send: 0.25 });
    perc(gw, t, 0.85, 0.02, 0.35);
    crackle(t, t + 0.4, 25, 0.12, pan);
  }
  // sparse crackle (tiny clicks), deterministic thanks to the seeded rnd
  function crackle(a, b, rate, vel, pan = 0, lo = 2000, hi = 7000) {
    const n = Math.floor((b - a) * rate);
    for (let i = 0; i < n; i++) {
      const t = a + rnd() * (b - a);
      const g = chain(noise(t, 0.01), [filt('bandpass', lo + rnd() * (hi - lo), 3)], { pan: pan + (rnd() - 0.5) * 0.3, send: 0.1 });
      perc(g, t, vel * (0.4 + rnd() * 0.8), 0.0005, 0.006 + rnd() * 0.01);
    }
  }
  // fuse hiss
  function fuseHiss(a, b, vel, pan0, pan1) {
    const hp = filt('highpass', 4200, 0.7);
    const bp = filt('peaking', 7000, 1);
    bp.gain.value = 6;
    const g = chain(noise(a, b - a), [hp, bp], { pan: pan0, send: 0.15 });
    g.setValueAtTime(0, a);
    g.linearRampToValueAtTime(vel, a + 0.06);
    // irregular flutter
    for (let t = a + 0.06; t < b; t += 0.05) g.linearRampToValueAtTime(vel * (0.6 + rnd() * 0.5), t);
    g.linearRampToValueAtTime(0, b + 0.05);
    crackle(a, b, 45, 0.18, (pan0 + pan1) / 2, 2500, 8000);
  }
  // disappointing fizzle + sad trombone
  function pfft(t) {
    const lp = filt('lowpass', 1400, 0.8);
    lp.frequency.setValueAtTime(1400, t);
    lp.frequency.exponentialRampToValueAtTime(180, t + 0.45);
    const g = chain(noise(t, 0.6), [lp], { send: 0.2 });
    perc(g, t, 0.55, 0.01, 0.4);
  }
  function sadTrombone(t) {
    const notes = [[0, 196, 0.26], [0.28, 185, 0.26], [0.56, 174.6, 0.26], [0.84, 164.8, 0.95]];
    for (const [dt, f, dur] of notes) {
      const s = t + dt;
      const o = osc('sawtooth', f, s, dur);
      if (dur > 0.5) {
        // wobble on the last, long note
        const lfo = osc('sine', 6, s + 0.2, dur);
        const lg = ctx.createGain();
        lg.gain.value = 0;
        lg.gain.setValueAtTime(0, s + 0.2);
        lg.gain.linearRampToValueAtTime(f * 0.03, s + 0.45);
        lfo.connect(lg).connect(o.frequency);
        o.frequency.setValueAtTime(f, s);
        o.frequency.linearRampToValueAtTime(f * 0.94, s + dur);
      }
      const wah = filt('lowpass', 500, 4);
      wah.frequency.setValueAtTime(350, s);
      wah.frequency.linearRampToValueAtTime(1300, s + 0.08);
      wah.frequency.linearRampToValueAtTime(600, s + dur);
      const g = chain(o, [wah], { bus: sfx, send: 0.35 });
      hold(g, s, dur, 0.16, 0.03, 0.1);
    }
  }
  function sigh(t) {
    const bp = filt('bandpass', 700, 1.5);
    bp.frequency.setValueAtTime(800, t);
    bp.frequency.exponentialRampToValueAtTime(260, t + 0.9);
    const g = chain(noise(t, 1.0), [bp], { send: 0.3 });
    g.setValueAtTime(0, t);
    g.linearRampToValueAtTime(0.2, t + 0.25);
    g.linearRampToValueAtTime(0, t + 1.0);
  }
  function ding(t) {
    const f = 1046.5;
    [[1, 0.35, 1.4], [2.76, 0.12, 0.8], [5.4, 0.06, 0.4], [2, 0.08, 1.0]].forEach(([r, v, d]) => {
      const g = chain(osc('sine', f * r, t, d * 2), [], { pan: 0.2, send: 0.6 });
      perc(g, t, v, 0.002, d);
    });
  }
  function whoosh(a, dur, f0, f1, vel, pan0 = -0.4, pan1 = 0.6) {
    const bp = filt('bandpass', f0, 1.2);
    bp.frequency.setValueAtTime(f0, a);
    bp.frequency.exponentialRampToValueAtTime(f1, a + dur);
    const s = noise(a, dur);
    const g = chain(s, [bp], { pan: pan0, send: 0.2 });
    g.setValueAtTime(0, a);
    g.linearRampToValueAtTime(vel, a + dur * 0.6);
    g.linearRampToValueAtTime(0, a + dur);
  }
  // stick-slip scrape (pushing metal across wood)
  function scrape(a, b, vel, f = 900) {
    const bp = filt('bandpass', f, 2.5);
    const g = chain(noise(a, b - a), [bp], { send: 0.2 });
    g.setValueAtTime(0, a);
    for (let t = a; t < b; t += 0.045) {
      g.linearRampToValueAtTime(vel * (0.3 + rnd() * 0.9), t + 0.01);
      g.linearRampToValueAtTime(vel * 0.15, t + 0.035);
    }
    g.linearRampToValueAtTime(0, b);
  }
  // duct tape unrolling: dense sticky clicks with rising rate + band noise
  function tapeUnroll(a, b) {
    const bp = filt('bandpass', 3800, 1.4);
    const g = chain(noise(a, b - a), [bp], { pan: 0.25, send: 0.15 });
    g.setValueAtTime(0, a);
    let t = a;
    while (t < b) {
      const u = (t - a) / (b - a);
      const period = 1 / (70 + 90 * u);
      g.linearRampToValueAtTime(0.95 * (0.5 + rnd() * 0.5), t + period * 0.15);
      g.linearRampToValueAtTime(0.12, t + period * 0.9);
      t += period;
    }
    g.linearRampToValueAtTime(0, b + 0.02);
  }
  function tapeRip(t) {
    const hp = filt('highpass', 900, 0.7);
    hp.frequency.setValueAtTime(700, t);
    hp.frequency.exponentialRampToValueAtTime(4000, t + 0.12);
    const g = chain(noise(t, 0.16), [hp], { pan: 0.25, send: 0.2 });
    g.setValueAtTime(0, t);
    g.linearRampToValueAtTime(0.6, t + 0.008);
    g.setTargetAtTime(0, t + 0.03, 0.035);
    crackle(t, t + 0.1, 220, 0.25, 0.25, 1500, 6000);
  }
  // launch: whoomp + roar that opens up + rising whistle
  function launch(t) {
    const o = osc('sine', 110, t, 0.9);
    o.frequency.exponentialRampToValueAtTime(38, t + 0.6);
    const gw = chain(o, [], { send: 0.3 });
    perc(gw, t, 0.9, 0.005, 0.5);
    const lp = filt('lowpass', 300, 0.7);
    lp.frequency.setValueAtTime(250, t);
    lp.frequency.linearRampToValueAtTime(2600, t + 0.35);
    lp.frequency.linearRampToValueAtTime(1400, t + 1.0);
    lp.frequency.linearRampToValueAtTime(700, t + 1.6);
    const gr = chain(noise(t, 1.8, brown), [lp], { send: 0.35 });
    gr.setValueAtTime(0, t);
    gr.linearRampToValueAtTime(1.0, t + 0.08);
    gr.setValueAtTime(1.0, t + 0.7);
    gr.linearRampToValueAtTime(0.35, t + 1.0); // cut to exterior: the rocket is further away
    gr.linearRampToValueAtTime(0.0, t + 1.65);
    const hs = filt('bandpass', 1800, 0.8);
    const gh = chain(noise(t, 1.0), [hs], { send: 0.2 });
    gh.setValueAtTime(0, t);
    gh.linearRampToValueAtTime(0.35, t + 0.1);
    gh.linearRampToValueAtTime(0.0, t + 1.0);
    const rumble = osc('sine', 46, t, 1.2);
    const grm = chain(rumble, [], { send: 0 });
    hold(grm, t, 1.1, 0.4, 0.05, 0.4);
    crackle(t, t + 1.0, 80, 0.25, 0, 1500, 6000);
    // rising whistle as it climbs into the sky (exterior)
    const w = osc('sine', 700, t + 1.0, 0.7);
    w.frequency.setValueAtTime(700, t + 1.0);
    w.frequency.exponentialRampToValueAtTime(2300, t + 1.62);
    const gws = chain(w, [], { pan: 0.1, send: 0.4 });
    hold(gws, t + 1.0, 0.64, 0.12, 0.05, 0.05);
    void LAUNCH_ACC;
  }
  function glass(t) {
    const g = chain(noise(t, 0.3), [filt('highpass', 2500, 0.7)], { send: 0.4 });
    perc(g, t, 0.55, 0.002, 0.16);
    for (let i = 0; i < 26; i++) {
      const s = t + Math.pow(rnd(), 1.6) * 0.7;
      const f = 2800 + rnd() * 5200;
      const gp = chain(osc('sine', f, s, 0.3), [], { pan: (rnd() - 0.5) * 1.4, send: 0.5 });
      perc(gp, s, 0.06 + rnd() * 0.08, 0.001, 0.05 + rnd() * 0.12);
    }
  }
  // firework: boom + crackle; `inside` muffles it (heard through the roof)
  function firework(t, vel, pan, inside = false) {
    const lp = filt('lowpass', inside ? 500 : 1800, 0.7);
    const o = osc('sine', 75, t, 1.2);
    o.frequency.exponentialRampToValueAtTime(32, t + 0.7);
    const go = chain(o, [], { pan, send: 0.5 });
    perc(go, t, vel * 0.9, 0.004, 0.7);
    const gn = chain(noise(t, 1.0, brown), [lp], { pan, send: 0.6 });
    perc(gn, t, vel * 1.2, 0.003, 0.45);
    const n = inside ? 40 : 90;
    for (let i = 0; i < n; i++) {
      const s = t + 0.25 + Math.pow(rnd(), 0.8) * 1.3;
      const g = chain(noise(s, 0.015), [filt('bandpass', inside ? 1200 + rnd() * 1500 : 2500 + rnd() * 5000, 2.5)], { pan: pan + (rnd() - 0.5) * 0.9, send: 0.35 });
      perc(g, s, vel * (inside ? 0.12 : 0.22) * (0.4 + rnd()), 0.0005, 0.008);
    }
  }
  // night crickets (very quiet room tone)
  function crickets(a, b) {
    for (let t = a + 0.3; t < b; t += 0.9 + rnd() * 0.6) {
      for (let k = 0; k < 3; k++) {
        const s = t + k * 0.06;
        const g = chain(osc('sine', 4600 + rnd() * 200, s, 0.05), [], { pan: 0.7, send: 0.6 });
        perc(g, s, 0.018, 0.005, 0.03);
      }
    }
  }

  // ---------- cue sheet (all from the shared timeline) ----------
  crickets(0, 14.8);
  crickets(17.6, 20);
  EV.wrenchHits.forEach((t, i) => clank(t, [560, 600, 530][i], 0.55, 0.15));
  thud(EV.hopLand, 0.35, 140, -0.1);
  matchStrike(EV.match1, -0.1);
  fuseHiss(EV.fuse1On, EV.fuse1Out, 0.16, 0.1, 0.2);
  crackle(EV.fuse1Out, EV.pfft, 60, 0.25, 0.2, 1500, 6000); // sputter
  pfft(EV.pfft);
  sadTrombone(EV.pfft + 0.1);
  clank(EV.toppleHit, 300, 0.55, 0.3, 0.5);
  thud(EV.toppleHit, 0.45, 120, 0.3);
  clank(EV.toppleBounce, 340, 0.25, 0.35, 0.3);
  crackle(EV.toppleBounce, EV.toppleBounce + 0.3, 30, 0.1, 0.35, 800, 3000); // small roll rattle
  sigh(EV.sigh);
  ding(EV.idea);
  whoosh(EV.dash - 0.02, 0.35, 500, 2500, 0.3);
  scrape(11.12, 11.42, 0.12, 1200);
  clank(EV.liftUp, 420, 0.45, 0.2, 0.35);
  scrape(EV.pushStart, EV.pushHit, 0.22, 850);
  clank(EV.pushHit, 380, 0.5, 0.25, 0.4);
  tapeUnroll(EV.tape1[0], EV.tape1[1]);
  tapeRip(EV.tape1Rip);
  tapeUnroll(EV.tape2[0], EV.tape2[1]);
  tapeRip(EV.tape2Rip);
  EV.pats.forEach((t) => { clank(t, 260, 0.35, 0.2, 0.2); thud(t, 0.45, 180, 0.2); });
  matchStrike(EV.match2, 0.1);
  fuseHiss(EV.fuse2On, EV.ignite, 0.18, 0.2, 0.15);
  launch(EV.ignite);
  glass(EV.crash);
  EV.bursts.forEach((t, i) => firework(t, i < 3 ? [1.0, 0.8, 0.8][i] : 0.75, [0, -0.45, 0.45, 0.1, -0.35, 0.3][i], i >= 3));
  thud(18.46, 0.22, 170, -0.1);
  thud(18.72, 0.18, 170, -0.1);

  return ctx.startRendering();
}

export function encodeWAV(buffer) {
  const ch = buffer.numberOfChannels, len = buffer.length, sr = buffer.sampleRate;
  const data = new DataView(new ArrayBuffer(44 + len * ch * 2));
  const w = (o, s) => [...s].forEach((c, i) => data.setUint8(o + i, c.charCodeAt(0)));
  w(0, 'RIFF'); data.setUint32(4, 36 + len * ch * 2, true); w(8, 'WAVE'); w(12, 'fmt ');
  data.setUint32(16, 16, true); data.setUint16(20, 1, true); data.setUint16(22, ch, true);
  data.setUint32(24, sr, true); data.setUint32(28, sr * ch * 2, true); data.setUint16(32, ch * 2, true);
  data.setUint16(34, 16, true); w(36, 'data'); data.setUint32(40, len * ch * 2, true);
  const chans = [...Array(ch)].map((_, c) => buffer.getChannelData(c));
  let o = 44;
  for (let i = 0; i < len; i++) {
    for (let c = 0; c < ch; c++) {
      const v = Math.max(-1, Math.min(1, chans[c][i]));
      data.setInt16(o, v < 0 ? v * 0x8000 : v * 0x7fff, true);
      o += 2;
    }
  }
  return new Uint8Array(data.buffer);
}
