# Clawd — "Decolagem"

Curta de animação 3D de 20 s com Clawd, o mascote do Claude Code.
Feito em **Three.js**, renderizado com **HyperFrames** em MP4 1920×1080 a 30 fps, com todo
o áudio (trilha e efeitos) **sintetizado pela Web Audio API**: nenhum arquivo de áudio ou sample.

▶ Vídeo final: [`final/clawd.mp4`](final/clawd.mp4)
📋 Storyboard e decisões de direção: [`STORYBOARD.md`](STORYBOARD.md)

## Estrutura

```
clawd/
├── index.html            composição HyperFrames (canvas WebGL + <audio> da trilha)
├── src/
│   ├── timeline.js       tempos de cortes e eventos, compartilhados por imagem e som
│   ├── story.js          coreografia: poses de Clawd, foguete e câmera (funções puras de t)
│   ├── clawd.js          o personagem (bloco de argila terracota #D97757, rig de squash/stretch)
│   ├── set.js            oficina, luminária, claraboia, telhado, céu, feixe de luar
│   ├── props.js          foguete de sucata, propulsor, pavios, fita adesiva, fósforos
│   ├── fx.js             faíscas, chamas, fumaça, fogos de artifício, cacos de vidro
│   ├── textures.js       texturas procedurais (argila, madeira, pegboard…) com semente fixa
│   ├── main.js           renderer, luzes, pós-processamento (DOF, blur de chicote, grão) e renderAt(t)
│   ├── audio.js          trilha pizzicato + efeitos, 100% Web Audio API (OfflineAudioContext)
│   └── util.js           easing, keyframes, PRNG/hash determinísticos
├── assets/soundtrack.wav áudio gerado por src/audio.js
├── tools/
│   ├── frames.mjs        renderiza quadros/pranchas de verificação (mesmo caminho do render final)
│   ├── render-audio.mjs  executa src/audio.js no Chrome headless e grava o WAV
│   └── audio.html
├── verificacao/
│   ├── pranchas/         6 quadros por plano (prancha_plano1…8.png)
│   ├── sequencias/       sequências dos movimentos principais (golpes, pulo, tombo, ideia, decolagem, alegria)
│   ├── audio_onda_espectro.png
│   └── final_*.png       conferência do MP4 final
├── final/clawd.mp4
└── vendor/               three.js r186 (local, sem rede no render)
```

## Como reproduzir

```bash
cd clawd
npm install
npx hyperframes browser ensure
node tools/render-audio.mjs                       # gera assets/soundtrack.wav (Web Audio)
node tools/frames.mjs --out verificacao/pranchas --shots   # pranchas de verificação
npx hyperframes render -o final/clawd.mp4 -q delivery -f 30 -w 4
```

## Determinismo

* Cada quadro é calculado só a partir do tempo: o HyperFrames dispara `hf-seek` e a cena chama
  `renderAt(t)`. Não há `requestAnimationFrame`, relógio nem estado acumulado entre quadros.
* Partículas (faíscas, fogos, fumaça, cacos) usam fórmulas fechadas em função de `t` e do índice,
  com hash de semente fixa. Texturas e áudio usam um PRNG (`mulberry32`) com semente fixa.
* Até a física simples (queda dos fósforos, pouso dos cacos) é resolvida analiticamente.
