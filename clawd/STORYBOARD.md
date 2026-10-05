# Clawd — "Decolagem" · Storyboard

Curta 3D de 20 s · 1920×1080 · 30 fps · Three.js + HyperFrames · áudio 100% Web Audio API.

Todos os tempos abaixo vivem em `src/timeline.js` e são lidos **pela cena e pelo áudio**,
então cada efeito sonoro cai exatamente no quadro da ação correspondente.

## Mundo e escala

Tudo acontece em cima de uma bancada de oficina, à noite. Clawd tem o tamanho de um brinquedo
(≈10 cm), então ferramentas reais parecem gigantes ao redor dele e o personagem sempre ocupa
boa parte do quadro. Uma claraboia fica exatamente acima do foguete: é por ali que entra a luz
fria da lua e é por ali que o foguete vai sair. Uma luminária articulada à esquerda dá a luz
quente principal.

Posição de partida de Clawd: `P0` (ao lado esquerdo do foguete). Ele termina o filme no mesmo `P0`.

## Planos

| # | Tempo | Plano / câmera | O espectador precisa entender | Ordem dos acontecimentos | Por que corta |
|---|-------|----------------|-------------------------------|--------------------------|---------------|
| 1 | 0,0–3,4 s | Plano geral → médio. A câmera já entra em movimento (dolly-in) saindo do escuro. | É noite numa oficina; Clawd está construindo um foguetinho de sucata. | Fade-in já em movimento → 3 batidas de chave inglesa no foguete (antecipação antes de cada golpe, clank) → Clawd recua, olha o foguete de baixo para cima → pulinho de orgulho (squash/stretch) → os olhos procuram o fósforo. | O olhar de Clawd para o lado motiva o corte para a ação de acender. |
| 2 | 3,4–5,8 s | Médio lateral. Push-in rápido no final seguindo a faísca. | Ele acende o pavio e se protege, ansioso. | Risca o fósforo (chama) → antecipação (inclina para trás) → encosta no pavio → o pavio chia e solta faíscas → Clawd corre para trás, se encolhe com os braços na frente, olhos apertados → espia. | A câmera acompanha a faísca correndo pelo pavio — corte por movimento. |
| 3 | 5,8–8,2 s | Close baixo no foguete. | O foguete falha. | A faísca chega à base → engasga, treme → "pfft" patético de fumaça → balança (antecipação) → tomba com aceleração → quica e para. | O som/impacto do tombo motiva o corte para a reação. |
| 4 | 8,2–10,9 s | Close frontal em Clawd, push-in lento durante a tristeza (mais tempo na emoção). | Clawd fica frustrado… e tem uma ideia. | Olhos descem até o foguete caído antes do corpo → o corpo murcha (squash), braços caem, olhos encurtam e inclinam, aparece uma boquinha triste → suspiro, respiração → os olhos desviam para o propulsor vermelho → olhos se arregalam, boca some, o corpo estica (ideia, "ding") → antecipação → dispara para a direita. | Chicote de câmera seguindo a corrida de Clawd. |
| 5 | 10,9–14,0 s | Médio, câmera assentando do chicote. | Ele conserta com um propulsor maior e fita adesiva. | Levanta o foguete caído (clank) → empurra o propulsor até encostar (arrasto + clank) → duas voltas de fita (fita desenrolando + rasgo) → dois tapinhas e aceno de orgulho. | Ação concluída; corte para a nova tentativa. |
| 6 | 14,0–16,0 s | Médio baixo → tilt para cima acompanhando o foguete. | Desta vez funciona e o foguete atravessa a claraboia. | Acende o pavio do propulsor rapidamente → recua para `P0` e se protege → tremor (antecipação) → ignição com clarão e rugido → decolagem acelerando; a luz da chama ilumina Clawd → o foguete estoura o vidro da claraboia. | Movimento contínuo de baixo para cima, continuado do lado de fora. |
| 7 | 16,0–17,6 s | Exterior, telhado e céu estrelado; tilt para cima. | O foguete explode em fogos no céu. | O foguete sai da claraboia com cacos de vidro → sobe → 3 explosões (terracota/dourado, azul, rosa/verde) com estalos. | Tilt rápido para baixo: corte por movimento de volta ao interior. |
| 8 | 17,6–20,0 s | Interior, grua descendo do alto até Clawd. | Final: Clawd no mesmo lugar do início, olhando para cima, iluminado pelos fogos. | A luz colorida dos fogos entra pela claraboia e pulsa sobre ele e a bancada → sorrisinho, pulinhos de alegria, braços para cima → respira, pisca → fade-out ainda em movimento. | Fim em movimento (grua + fade), sem congelar. |

## Regras de atuação aplicadas

* **Olhos primeiro**: em toda mudança de intenção os olhos se movem 0,1–0,25 s antes do corpo
  (procura do fósforo, olhar para o foguete caído, descoberta do propulsor, olhar para o céu).
* **Antecipação** antes de cada golpe, pulo, corrida, ignição e queda do foguete.
* **Squash & stretch** sutil no corpo (volume preservado: `scaleXZ = 1/√scaleY`).
* **Overlap**: braços e balanço do corpo atrasam em relação ao deslocamento; pernas batem
  em pares alternados proporcionalmente à distância percorrida.
* **Nunca imóvel**: respiração, micro-balanço e piscadas contínuos durante as pausas.
* Ações rápidas (golpes, corrida, fita) e tempo maior para emoções (frustração ≈ 1,8 s, final ≈ 2,4 s).

## Luz

* Luminária: SpotLight quente (≈2900 K) com sombra suave — luz principal sobre Clawd.
* Lua: DirectionalLight fria pela claraboia + feixe volumétrico com poeira em suspensão.
* Chama do foguete e faíscas: PointLights laranja.
* Fogos: SpotLight descendo pela claraboia com a cor de cada explosão + luzes no telhado.
* Profundidade de campo discreta (BokehPass) focada em Clawd/foguete, vinheta e grão leve.

## Som

* Trilha: pizzicato sintetizado (cordas dedilhadas) a 120 BPM constante; harmonia muda com a
  emoção (maior → menor na falha → arpejo ascendente na ideia → final em dó maior).
  A música é mantida ~-12 dB abaixo dos efeitos e sai de cena no lançamento.
* Efeitos sintetizados: clank metálico (parciais inarmônicas), riscar do fósforo, chiado do
  pavio com crepitação, "pfft" + trombone triste, tombo, "ding" da ideia, corrida, arrasto,
  fita desenrolando/rasgando, tapinhas, rugido do lançamento, vidro quebrando, estouros e
  crepitação dos fogos.
