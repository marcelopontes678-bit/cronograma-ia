// Legendas: mesmas falas que o filme queima na imagem (uma por fala medida).
import fs from 'node:fs';
const here = new URL('..', import.meta.url).pathname;
const N = JSON.parse(fs.readFileSync(here + 'narration-timeline.json', 'utf8'));
const cues = N.speech.map((s, i) => {
  const words = N.pages.filter(p => p.start >= s.start - .05 && p.start < s.end).flatMap(p => p.words.map(w => w.w));
  const next = N.speech[i + 1];
  return { t0: s.start, t1: next ? Math.max(s.end + .25, next.start - .06) : s.end + .6, text: words.join(' ') };
});
console.log(JSON.stringify(cues, null, 1));
