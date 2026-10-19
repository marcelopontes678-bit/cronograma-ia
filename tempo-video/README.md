# O tempo não espera — vídeo motivacional cinematográfico (Remotion)

Vídeo vertical de **30 s exatos** · **1080 × 1920** · **30 fps** · **900 frames** · H.264 + AAC.

Tema: o tempo é o recurso mais valioso da vida; cada dia perdido não volta. Mensagem final: *"Seu tempo é sua vida. Comece hoje."*

## Como renderizar

```bash
npm install
npm run studio                 # pré-visualização interativa (Remotion Studio)
bash scripts/render.sh         # RECOMENDADO → out/tempo.mp4 (H.264 High, CRF 16, yuv420p, AAC 256 kbps)
npm run render                 # alternativa direta (renderização única)
```

`scripts/render.sh` empacota uma vez, renderiza a sequência de imagens em blocos de 100 frames **com nova tentativa automática**, renderiza o áudio e codifica com o ffmpeg (+1,8 dB de ganho com limitador em −1 dBFS → ≈ −16,6 LUFS). Foi criado porque, em máquinas sem GPU e com várias abas do Chrome, uma aba ocasionalmente trava e derruba uma renderização única de 15 min; no modo em blocos só o bloco afetado é refeito (e os blocos prontos ficam em `out/seq`, então reexecutar continua de onde parou).

Um quadro avulso (útil para revisar um momento): `npx remotion still src/index.ts TempoVideo out/f.png --frame=450`.

Para ver as áreas seguras do Instagram sobrepostas: abra o Studio e ligue a prop `showSafeArea`.

**Sem internet / sem Chrome do Remotion:** o Remotion baixa um Chrome headless na primeira execução. Se a rede bloquear, aponte para um Chrome/Chromium local:

```bash
REMOTION_BROWSER_EXECUTABLE=/caminho/para/chrome-headless-shell bash scripts/render.sh
```

Tempo de renderização: ~12 min em 4 vCPUs sem GPU (900 frames) + ~1 min de codificação. A concorrência (3) e o timeout do `delayRender` (240 s) estão em `remotion.config.ts`.

## Estrutura

```
src/
  index.ts            registerRoot
  Root.tsx            <Composition id="TempoVideo" 1080x1920 · 30 fps · 900 frames>
  MainVideo.tsx       monta cenas, dissoluções, textos, legendas, pós-produção e áudio
  config.ts           FPS, tamanho, áreas seguras, tempos das cenas, paleta
  fonts.ts            carrega Cormorant Garamond e Inter (arquivos locais) com @remotion/fonts
  scenes/
    ClockScene.tsx    0–5 s    relógio analógico em close
    StreetScene.tsx   5–11 s   rua à noite sob chuva (perspectiva 3D calculada por frame)
    DeskScene.tsx     11–18 s  homem à mesa na madrugada
    MontageScene.tsx  18–25 s  6 planos: escrita (2), tênis (2), caminhada em direção à luz (2)
    SunriseScene.tsx  25–30 s  silhueta diante do horizonte, nascer do sol, fade para preto
  components/
    Camera.tsx        zoom/movimento lento + tremor de mão determinístico
    Grain.tsx         granulação de filme (4 quadros de ruído, deslocados a cada frame)
    Vignette.tsx      vinheta discreta + gradação fria nas sombras
    Dust.tsx          partículas suspensas no feixe de luz
    Rain.tsx          chuva em camadas
    WalkingMan.tsx    silhueta masculina com ciclo de passos
    Statement.tsx     frase principal (Cormorant Garamond) — opacidade + 14 px de deslocamento
    Subtitles.tsx     legendas em pt-BR sincronizadas palavra a palavra (Inter)
  data/
    captions.json     páginas de legenda com tempo por palavra (gerado)
    speech.json       janelas de fala — a música abaixa nelas (gerado)
audio/
  build_narration.py  narração (Kokoro, voz pm_alex) + legendas (Whisper) → public/audio/narration.wav
  build_music.py      trilha sintetizada → public/audio/music.mp3
scripts/make_grain.py   quadros de granulação → public/grain/
scripts/embed_fonts.py  public/fonts/*.woff2 → src/generated/fontData.ts
scripts/render.sh       renderização resiliente em blocos + codificação final
public/               fonts/ · audio/ · grain/  (tudo local)
```

## Determinismo

Toda animação é função do frame atual (`useCurrentFrame`, `useVideoConfig`, `interpolate`, `spring`). A aleatoriedade usa `random(seed)` do Remotion. O código **não** usa `Math.random`, `Date`, `requestAnimationFrame`, timers, transições ou animações CSS — o mesmo frame sempre gera a mesma imagem.

## Roteiro, tempos e sincronia

| Cena | Tempo | Narração | Texto na tela |
|---|---|---|---|
| 1 | 0–5 s | "O tempo está passando. Mesmo quando você não faz nada." | O TEMPO NÃO ESPERA. |
| 2 | 5–11 s | "Cada dia que você desperdiça é um pedaço da sua vida que não volta." | CADA DIA É IRREPETÍVEL. |
| 3 | 11–18 s | "Você pode continuar adiando o que precisa fazer… ou começar a construir aquilo que deseja ser." | ADIAR TAMBÉM É ESCOLHER. |
| 4 | 18–25 s | "Não espere sentir vontade. Discipline seus passos. Honre o tempo que ainda tem." | DISCIPLINA. PROPÓSITO. AÇÃO. |
| 5 | 25–30 s | "Porque, no fim, sua vida será a soma daquilo que decidiu fazer com o tempo." | SEU TEMPO É SUA VIDA. · Comece hoje. |

* **Legendas**: cada palavra recebe início/fim do Whisper (`hyperframes transcribe`, modelo `base`, `--language pt`); o texto exibido é o do roteiro (corrige erros de reconhecimento). Quebras de página são manuais (marcador `|` em `build_narration.py`).
* **Áreas seguras do Instagram** (`SAFE` em `config.ts`): 270 px no topo, 440 px embaixo, 72 px nas laterais. Frases principais ficam entre y ≈ 330 e 670; legendas terminam em y = 1470.
* **Mensagem sem áudio**: as cinco frases em tela, em sequência, contam a história completa.

## Direção de som

* **Narração**: Kokoro (`pm_alex`, pt-BR) com tom 7% mais grave, EQ, compressão e sala curta; frases posicionadas à mão com pausas e ganho crescente (0,80 → 1,06).
* **Trilha** (síntese própria em Python, sem amostras): 0–8 s só o relógio (um tique por segundo, no mesmo instante em que o ponteiro "bate" no vídeo); a partir de 8 s entram drone, pad em Lá menor e piano grave; pulsação de 60 bpm a partir de 12 s; clímax entre 22 e 27 s (riser, oitavas no piano, pulsação forte); em 27 s um impacto grave e uma nota de piano (Lá) sustentada com decaimento natural até o fim.
* **Mix**: a música baixa ~56% durante a fala (ataque/soltura suaves, em `MainVideo.tsx → musicVolume`).

Para regenerar o áudio (precisa de Python 3 com `numpy scipy soundfile kokoro-onnx`, `ffmpeg` e os modelos do Kokoro):

```bash
MODELS_DIR=/pasta/com/kokoro-v1.0.onnx-e-voices-v1.0.bin python audio/build_narration.py
python audio/build_music.py
python scripts/make_grain.py
```

## Origem dos recursos (nada externo)

* **Imagens/vídeo**: nenhuma foto ou vídeo. Todas as cenas são desenhadas em SVG/CSS dentro do próprio Remotion (relógio, rua em perspectiva, mesa, mãos, tênis, caminho, montanhas), com luz, névoa, partículas, granulação e câmera simulados. O resultado é **cinematográfico e estilizado, não fotorrealista**.
* **Fontes**: Cormorant Garamond e Inter, ambas SIL Open Font License (pacotes `@fontsource/*`; arquivos em `public/fonts`, com as licenças, e embutidas em `src/generated/fontData.ts` para a renderização não depender de rede).
* **Áudio**: narração gerada localmente com Kokoro (Apache-2.0) e trilha sintetizada por `audio/build_music.py`. Não há músicas, efeitos ou vozes de terceiros.

## Para aproximar do fotorrealismo

O briefing pede fotografia ultrarrealista; sem acervo licenciado de imagens e vídeos isso não é possível apenas com código. Se você tiver plates (vídeos/fotos licenciados ou gerados por uma ferramenta sua) para cada cena, coloque-os em `public/` e use-os como camada de fundo das cenas — a câmera, o grão, a vinheta, os textos, as legendas e o áudio continuam valendo.
