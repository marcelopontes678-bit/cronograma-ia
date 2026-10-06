// Runs src/audio.js (Web Audio API, OfflineAudioContext) inside headless Chrome and
// saves the result as assets/soundtrack.wav. Deterministic: same seed -> same file.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : 'text/html' });
  fs.createReadStream(p).pipe(res);
});
await new Promise((r) => server.listen(0, r));
const chrome = execFileSync('npx hyperframes browser path', { cwd: ROOT, shell: true }).toString().trim().split('\n').pop();
const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage();
page.on('pageerror', (e) => console.error(e));
page.on('console', (m) => console.log('[page]', m.text()));
const stem = process.argv[2] || 'mix';
await page.goto(`http://localhost:${server.address().port}/tools/audio.html?stem=${stem}`);
await page.waitForFunction('window.__wav !== undefined', { timeout: 300000 });
const b64 = await page.evaluate(() => window.__wav);
fs.mkdirSync(path.join(ROOT, 'assets'), { recursive: true });
const out = stem === 'mix' ? path.join(ROOT, 'assets', 'soundtrack.wav') : path.join(ROOT, 'verificacao', `stem_${stem}.wav`);
fs.writeFileSync(out, Buffer.from(b64, 'base64'));
console.log('wrote', out, fs.statSync(out).size, 'bytes');
await browser.close();
server.close();
