// Pure, deterministic helpers. Nothing here reads a clock or keeps state between frames.

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (a, b, x) => {
  const t = clamp((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};
// 0 -> 1 -> 0 bump centered at c with half-width w
export const bump = (x, c, w) => {
  const d = Math.abs(x - c) / w;
  return d >= 1 ? 0 : 0.5 + 0.5 * Math.cos(Math.PI * d);
};
// window: 0 before a, ramps to 1 by a+ri, stays, ramps down to 0 from b-ro to b
export const win = (x, a, b, ri = 0.1, ro = 0.1) =>
  Math.min(smooth(a, a + ri, x), 1 - smooth(b - ro, b, x));

export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Stateless hash noise: same (i, seed) always gives the same value in [0,1)
export function hash1(i, seed = 0) {
  let h = Math.imul((i | 0) ^ 0x9e3779b9, 0x85ebca6b) ^ Math.imul(seed | 0, 0xc2b2ae35);
  h ^= h >>> 16;
  h = Math.imul(h, 0x7feb352d);
  h ^= h >>> 15;
  h = Math.imul(h, 0x846ca68b);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
// smooth 1D value noise in [-1, 1]
export function noise1(x, seed = 0) {
  const i = Math.floor(x);
  const f = x - i;
  const u = f * f * (3 - 2 * f);
  return lerp(hash1(i, seed), hash1(i + 1, seed), u) * 2 - 1;
}

export const EASE = {
  lin: (t) => t,
  in: (t) => t * t * t,
  out: (t) => 1 - Math.pow(1 - t, 3),
  io: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  in2: (t) => t * t,
  out2: (t) => 1 - (1 - t) * (1 - t),
  sine: (t) => 0.5 - 0.5 * Math.cos(Math.PI * t),
  outBack: (t) => {
    const c1 = 1.70158, c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  },
  inBack: (t) => {
    const c1 = 1.70158, c3 = c1 + 1;
    return c3 * t * t * t - c1 * t * t;
  },
  outElastic: (t) =>
    t === 0 || t === 1 ? t : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * ((2 * Math.PI) / 3)) + 1,
  step: (t) => (t < 1 ? 0 : 1),
};

// Keyframe track: keys = [[time, value, easeIntoThisKey?], ...] sorted by time.
// value can be a number or an array of numbers.
export function key(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  const last = keys[keys.length - 1];
  if (t >= last[0]) return last[1];
  for (let i = 1; i < keys.length; i++) {
    const k1 = keys[i];
    if (t <= k1[0]) {
      const k0 = keys[i - 1];
      const e = EASE[k1[2] || 'io'];
      const u = e((t - k0[0]) / (k1[0] - k0[0]));
      if (Array.isArray(k0[1])) return k0[1].map((v, j) => lerp(v, k1[1][j], u));
      return lerp(k0[1], k1[1], u);
    }
  }
  return last[1];
}

// Path length travelled along a 2D track up to time t (exact for straight segments).
export function keyPathLength(t, keys) {
  let len = 0;
  for (let i = 1; i < keys.length; i++) {
    const k0 = keys[i - 1], k1 = keys[i];
    const seg = Math.hypot(k1[1][0] - k0[1][0], k1[1][1] - k0[1][1]);
    if (t >= k1[0]) {
      len += seg;
    } else {
      if (t > k0[0]) {
        const e = EASE[k1[2] || 'io'];
        len += seg * e((t - k0[0]) / (k1[0] - k0[0]));
      }
      break;
    }
  }
  return len;
}
