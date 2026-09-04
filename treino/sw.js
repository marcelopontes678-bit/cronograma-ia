const CACHE = 'treino-v3';
const ASSETS = [
  './',
  './index.html',
  './app.js',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
];
// Fontes externas: melhor-esforço. Ficam fora do addAll atômico acima porque uma
// falha de rede nessa URL (CDN fora do ar, bloqueio momentâneo) não deve impedir
// a instalação do Service Worker com os assets locais que realmente importam.
const EXTERNAL_ASSETS = [
  'https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap'
];

async function installAssets() {
  const c = await caches.open(CACHE);
  await c.addAll(ASSETS);
  await Promise.allSettled(EXTERNAL_ASSETS.map(url => c.add(url)));
  self.skipWaiting();
}

self.addEventListener('install', e => {
  e.waitUntil(installAssets());
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Network-first: sempre tenta buscar a versão mais recente primeiro (o app está em
// desenvolvimento ativo). Só cai pro cache guardado quando o dispositivo está
// offline — assim quem já instalou o app sempre recebe as atualizações ao abrir
// com internet, em vez de ficar preso na versão do dia da instalação.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request)
      .then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return res;
      })
      .catch(() => caches.match(e.request).then(r => r || caches.match('./index.html')))
  );
});
