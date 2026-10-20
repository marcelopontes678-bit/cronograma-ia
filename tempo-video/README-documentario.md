# Documentário Político — Brasil 2026 (30 s, vertical)

Composição Remotion `DocBrasil2026`: 1080×1920, 30 fps, 900 frames, MP4 H.264 + AAC.

## Instalação

```bash
cd tempo-video
npm install
# Chrome: se o download automático do Remotion estiver bloqueado, aponte para um Chrome/headless-shell local
export REMOTION_BROWSER_EXECUTABLE=/caminho/para/chrome-headless-shell
```

## Pré-visualizar e renderizar

```bash
npx remotion studio                       # escolha "DocBrasil2026"
npx tsc --noEmit                          # verificação de tipos

# render direto
npx remotion render src/index.ts DocBrasil2026 out/documentario.mp4 --codec=h264

# render em blocos com novas tentativas automáticas (mais robusto em máquinas lentas)
COMP=DocBrasil2026 TOTAL=900 OUT=out/doc OUTNAME=documentario bash scripts/render.sh
```

## Estrutura

| Arquivo | Função |
|---|---|
| `src/doc/DocBrasil2026.tsx` | Composição principal: cenas, cortes (5 s, 13 s, 21 s), cabeçalho, legendas, grão, mixagem com ducking |
| `src/doc/scenes/Brasilia.tsx` | Cena 1 (0–5 s): Congresso à noite (ilustração original), resultado do 1º turno |
| `src/doc/scenes/Documents.tsx` | Cena 2 (5–13 s): registros públicos e legenda de status jurídico |
| `src/doc/scenes/Candidates.tsx` | Cena 3 (13–21 s): fichas idênticas dos dois candidatos |
| `src/doc/scenes/Vote.tsx` | Cena 4 (21–30 s): eleitores, bandeira ao pôr do sol, urna, texto final |
| `src/doc/facts.ts` | **Fonte única de todo texto factual** (status, fonte e data de cada item) |
| `src/doc/media.ts` | Recursos substituíveis (fotos e áudio) |
| `src/doc/ui.tsx` | Paleta, legendas, câmera, revelações, carimbo, grão/vinheta |
| `src/doc/data/timeline.json` | Tempos das palavras, das falas e das marcas de som (gerado) |
| `audio/build_doc.py` | Gera narração, trilha, efeitos e `timeline.json` |

## Áudio (substituível)

Os arquivos em `public/doc/` foram **gerados neste projeto**. Não são gravações humanas nem trilha comercial:

- `narration.wav`: voz sintética Kokoro TTS (`pm_alex`, pt-BR), acelerada 1,32× para caber em 30 s.
- `bed.mp3`: trilha de suspense sintetizada por código (drone, tique-taque, ostinato, pad, pausa, acorde final).
- `sfx.mp3`: graves nos cortes, carimbos, papel e bipes da urna, também sintetizados.

**Para usar narração humana ou trilha licenciada:**

1. Substitua o arquivo mantendo o nome, ou mude o caminho em `src/doc/media.ts`.
2. Se a nova narração tiver outro ritmo, regenere os tempos das legendas:
   ```bash
   python -I audio/build_doc.py   # requer kokoro-onnx, numpy, scipy, soundfile e ffmpeg
   ```
   O script usa transcrição Whisper (`npx hyperframes transcribe`) e alinha as palavras ao texto literal do roteiro.
3. Ajuste o volume da música e a profundidade do ducking em `AUDIO.musicLevel` e `AUDIO.duckDepth`.

## Fotos de arquivo (PENDENTES)

O ambiente de produção não tinha acesso a bancos de imagens: Wikimedia, Agência Brasil e Agência Senado estavam bloqueados. Por isso o vídeo mostra um espaço identificado como **"FOTO DE ARQUIVO PENDENTE"** e não usa nenhuma imagem inventada ou gerada por IA de pessoas reais.

Para incluir fotos oficiais:

1. Baixe fotos oficiais com licença verificada. Agência Brasil e Agência Senado costumam usar CC BY; confira cada imagem.
2. Salve as fotos em `public/doc/fotos/`, por exemplo `flavio.jpg` e `lula.jpg`.
3. Em `src/doc/media.ts`, preencha `file: "doc/fotos/flavio.jpg"` e `credit: "Foto: Fulano/Agência Senado (CC BY)"`.

Use fotos de contexto equivalente para os dois: retrato oficial com retrato oficial.

## Checagem de fatos (verificada em 20/10/2026)

| Alegação no vídeo | Status | Fonte e data |
|---|---|---|
| 1º turno em 04/10/2026: Flávio Bolsonaro (PL) 47,03%, Lula (PT) 45,16% | Resultado oficial (TSE, 100% das seções) | CNN Brasil e Portal de Prefeitura, 05/10/2026 |
| 2º turno em 25/10/2026 | Calendário TSE | idem |
| AP 470 "Mensalão": julgamento iniciado no STF em 02/08/2012 | CONDENAÇÃO (réus condenados) | STF, AP 470 |
| Lava Jato: deflagrada pela PF em 17/03/2014 | INVESTIGAÇÃO (deu origem a múltiplos processos) | PF/MPF |
| Flávio: denúncia do MP-RJ (2020) no caso "rachadinha" | DENÚNCIA → ARQUIVADA | Estado de Minas, 09/11/2021 |
| STJ (5ª Turma) anulou decisões da 1ª instância em 09/11/2021 | ANULADA | Estado de Minas, 09/11/2021 |
| TJ-RJ (Órgão Especial) arquivou a denúncia a pedido do MP-RJ em 16/05/2022 | ARQUIVADA | Brasil de Fato e TNH1, 16/05/2022 |
| Lula: condenações (tríplex e Atibaia) anuladas por incompetência da 13ª Vara de Curitiba (Fachin, 08/03/2021) | ANULADA | Poder360 e Gazeta do Povo |
| Plenário do STF confirmou a anulação em 15/04/2021 | ANULADA | Poder360, 15/04/2021 |

Critérios editoriais:

- Cada item exibe o status jurídico explícito. A legenda da cena 2 explica a diferença entre investigação, denúncia, condenação, anulação e arquivamento.
- Ambos os candidatos recebem o mesmo formato, a mesma quantidade de linhas e a mesma entrada na tela. A ordem segue o 1º turno.
- Os dois negam irregularidades; isso aparece nas fichas.
- **Ficou de fora:**
  - O número exato de condenados no Mensalão, porque as fontes divergem entre 24 e 25.
  - Alegações sobre o "caso Master", porque há decisões judiciais conflitantes sobre o conteúdo.
- Não há manchetes, citações, estatísticas ou documentos inventados. Os "papéis" do fundo são texturas genéricas, sem texto legível.

**Antes de publicar:** confira de novo nas fontes primárias (TSE, STF, STJ, TJ-RJ). O 2º turno é em 25/10/2026 e o cenário pode mudar. Se mudar, atualize `src/doc/facts.ts`, inclusive a data de verificação em `FINAL_SOURCES`.

## Observações visuais

- O Congresso Nacional é uma **ilustração estilizada original**, não uma foto. Mostra a cúpula do Senado (convexa) e a da Câmara (côncava), mas a posição esquerda/direita não foi confirmada em fonte primária.
- A urna é um desenho neutro: a tela não mostra número de candidato e a confirmação termina em "FIM".
- O texto final aparece depois de uma pausa dramática de cerca de 0,9 s sem narração (marca `finalText` = 27,4 s).
