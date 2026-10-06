// Verification tool: renders chosen times of the film to PNG (same code path as the
// final render: window.__renderAt(t)), then builds labelled contact sheets with ffmpeg.
//
//   node tools/frames.mjs --out verificacao/r1 --times 0.5,1.2,3.0
//   node tools/frames.mjs --out verificacao/r1 --shots          (6 frames per shot)
//   node tools/frames.mjs --out verificacao/r1 --range 2.4,3.2,0.0667   (sequence)
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';
import { SHOT } from '../src/timeline.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (k, d) => {
  const i = args.indexOf(k);
  return i >= 0 ? args[i + 1] : d;
};
const out = path.resolve(ROOT, opt('--out', 'verificacao/frames'));
fs.mkdirSync(out, { recursive: true });

let times = [];
let groups = [];
if (args.includes('--shots')) {
  const b = [SHOT.s1, SHOT.s2, SHOT.s3, SHOT.s4, SHOT.s5, SHOT.s6, SHOT.s7, SHOT.s8, SHOT.end];
  const per = Number(opt('--per', 6));
  for (let s = 0; s < 8; s++) {
    const g = [];
    for (let k = 0; k < per; k++) {
      const t = b[s] + ((b[s + 1] - b[s]) * (k + 0.5)) / per;
      g.push(+t.toFixed(3));
    }
    groups.push({ name: `plano${s + 1}`, times: g });
  }
} else if (opt('--range')) {
  const [a, b, st] = opt('--range').split(',').map(Number);
  const g = [];
  for (let t = a; t <= b + 1e-6; t += st) g.push(+t.toFixed(4));
  groups.push({ name: opt('--name', 'seq'), times: g });
} else {
  groups.push({ name: opt('--name', 'frames'), times: opt('--times', '0.5').split(',').map(Number) });
}
times = groups.flatMap((g) => g.times);

const mime = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.wav': 'audio/wav', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) {
    res.writeHead(404);
    return res.end();
  }
  res.writeHead(200, { 'Content-Type': mime[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise((r) => server.listen(0, r));
const port = server.address().port;

const chrome = execFileSync('npx hyperframes browser path', { cwd: ROOT, shell: true }).toString().trim().split('\n').pop();
const browser = await puppeteer.launch({
  executablePath: chrome,
  headless: true,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--window-size=1920,1080'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080 });
const errors = [];
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errors.push(m.text()); });
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://localhost:${port}/index.html`, { waitUntil: 'load' });
await page.waitForFunction('window.__clawdReady === true', { timeout: 120000 }).catch(() => {});
if (errors.length) console.log('page messages:\n' + [...new Set(errors)].slice(0, 20).join('\n'));

const t0 = Date.now();
for (const g of groups) {
  const files = [];
  for (const t of g.times) {
    await page.evaluate((tt) => window.__renderAt(tt), t);
    const f = path.join(out, `${g.name}_t${t.toFixed(3).padStart(7, '0')}.png`);
    await page.screenshot({ path: f, clip: { x: 0, y: 0, width: 1920, height: 1080 } });
    files.push(f);
  }
  // contact sheet with time labels
  const cols = Math.min(files.length, Number(opt('--cols', 3)));
  const rows = Math.ceil(files.length / cols);
  const inputs = files.flatMap((f) => ['-i', f]);
  const fl = files.map((_, i) => `[${i}:v]scale=640:-1,drawtext=text='${g.name} t=${g.times[i].toFixed(2)}s':x=10:y=10:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6[v${i}]`).join(';');
  const layout = files.map((_, i) => `${(i % cols) * 640}_${Math.floor(i / cols) * 360}`).join('|');
  const pad = rows * cols - files.length;
  let filter = fl + ';' + files.map((_, i) => `[v${i}]`).join('') + `xstack=inputs=${files.length}:layout=${layout}:fill=black[out]`;
  if (files.length === 1) filter = fl + `;[v0]null[out]`;
  execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...inputs, '-filter_complex', filter, '-map', '[out]', path.join(out, `prancha_${g.name}.png`)]);
  void pad;
  if (!args.includes('--keep')) files.forEach((f) => fs.unlinkSync(f));
}
console.log(`rendered ${times.length} frames in ${((Date.now() - t0) / 1000).toFixed(1)}s -> ${out}`);
await browser.close();
server.close();
