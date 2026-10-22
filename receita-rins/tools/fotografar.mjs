// Renderiza as 7 cenas (com e sem texto) em PNG 1080×1920.
// node tools/fotografar.mjs  (usa playwright-core; PLAYWRIGHT_CHROME aponta para o Chromium local)
import { chromium } from '/home/user/lemo-opuscar/node_modules/playwright-core/index.mjs';
import path from 'node:path';
const here = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const b = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROME || '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell' });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
for (let n = 1; n <= 7; n++) for (const t of [1, 0]) {
  await p.goto(`file://${here}/tools/cenas.html?cena=${n}&texto=${t}`);
  await p.waitForFunction(() => window.READY === true);
  const f = `${here}/imagens/cena-${n}${t ? '' : '-limpa'}.png`;
  await p.screenshot({ path: f });
  console.log(f);
}
await b.close();
