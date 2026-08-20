# GIBOR — Auditoria Técnica Completa

> Documento gerado em auditoria somente-leitura. Nenhum arquivo de código foi alterado nesta etapa.
> Data: 2026-08-20 · Branch analisada: `claude/strong-workout-app-bkiui9` (sincronizada com `main`)

---

## 1. Stack

O repositório `cronograma-ia` é um **monorepo** que contém **quatro projetos independentes e não conectados entre si**. Apenas um deles é o "GIBOR" (o app de treino que vem sendo evoluído nas últimas sessões e está publicado em produção).

| Projeto | Pasta | Status | Stack |
|---|---|---|---|
| **GIBOR** (app de treino) | `treino/` | ✅ **Ativo, em produção** | HTML + CSS + JavaScript puro (vanilla), sem framework, sem build step |
| Cronograma App (gerador de cronograma via IA) | raiz (`cronograma_app.html`, `index.html`, `manifest.json`, `sw.js`) | 🟡 Legado, publicado via GitHub Pages | HTML/JS puro, chama a API da Anthropic direto do navegador com chave do usuário salva em `localStorage` |
| Backend "SmartFactory" | `backend/` | ⚪ Dormente, não implantado | Python — FastAPI + SQLAlchemy (async) + Alembic + PostgreSQL + JWT (jose) + bcrypt (passlib) |
| Frontend "SmartFactory" | `frontend/` | ⚪ Dormente, não implantado | Next.js (App Router) + TypeScript + Tailwind CSS |
| Wrapper Android | `android/` | 🟡 Ligado ao Cronograma App, não ao GIBOR | Java + WebView, `build-apk.yml` builda via GitHub Actions a cada push em `main` |

**Stack do GIBOR especificamente:**
- **Frontend:** HTML5 + CSS3 (custom properties para tema claro/escuro) + JavaScript ES6+ vanilla — zero dependências, zero bundler, zero `package.json`
- **Persistência:** `localStorage` do navegador (100% client-side, sem rede)
- **PWA:** `manifest.json` + `sw.js` (Service Worker, estratégia network-first)
- **Fontes:** Google Fonts (Bebas Neue, IBM Plex Sans, IBM Plex Mono) carregadas via `<link>` e cacheadas pelo SW
- **Hospedagem/deploy:** Cloudflare Workers (assets estáticos), configurado em `wrangler.jsonc` na raiz apontando para `./treino`
- **URL de produção:** https://cronograma-ia.marcelopontes678.workers.dev

⚠️ **Achado importante:** o backend FastAPI e o frontend Next.js existem no repositório mas modelam um domínio totalmente diferente (empresas, usuários, projetos, unidades — parece um SaaS de gestão industrial/"SmartFactory"). Não há nenhuma linha de código que conecte esses projetos ao GIBOR. Não há Supabase em nenhum lugar do repositório.

---

## 2. Arquitetura

O GIBOR segue uma arquitetura **SPA client-side pura, sem backend**:

```
Navegador
 └─ index.html (shell + CSS embutido)
     └─ app.js (toda a lógica: estado, renderização, regras de negócio)
         └─ localStorage (única fonte de persistência — chave "treino_app_v1")
```

- **Padrão de renderização:** "full re-render por aba". Um único objeto de estado global (`state`) guarda tudo; a função `render()` limpa `#main` e reconstrói a aba ativa inteira a partir do zero a cada mudança (`renderTreinoTab`, `renderHistoricoTab`, `renderExerciciosTab`, `renderPerfilTab`). Não há Virtual DOM nem diffing — é DOM imperativo direto (`document.createElement`, `innerHTML`).
- **Sem roteamento real:** a "navegação" é só uma variável `ui.tab` en memória; não há URLs distintas por tela, `history.pushState` ou deep-linking. Recarregar a página sempre volta pra aba "Treino".
- **Sem componentização formal:** não existem componentes reutilizáveis como classes/módulos — são funções que retornam elementos DOM (`makeEmpty()`, `buildWorkoutSummaryCard()`, `buildInlineRestDivider()`, `renderLineChartSVG()`, `bodyDiagramSVG()`). Funciona, mas não escala bem para telas muito mais complexas.
- **Sem módulos ES (import/export):** tudo roda em um único arquivo global de ~2050 linhas (`app.js`), carregado via `<script src="app.js">` sem `type="module"`. Todas as funções e variáveis (`state`, `ui`, `picker`, `restTimer` etc.) vivem no escopo global do `window`.
- **Sem camada de API:** não existe `fetch()` para nenhum servidor próprio. As únicas chamadas de rede são: fontes do Google Fonts, e as imagens estáticas de exercícios (arquivos locais em `treino/exercises/`).

---

## 3. Estrutura do projeto

### 3.1 Árvore completa (raiz do repositório)

```
cronograma-ia/
├── treino/                      ← GIBOR (o app ativo)
│   ├── index.html                 shell HTML + CSS embutido (~520 linhas)
│   ├── app.js                     toda a lógica (~2050 linhas)
│   ├── manifest.json               PWA manifest ("Gibor - Diário de Musculação")
│   ├── sw.js                       Service Worker (cache "treino-v2", network-first)
│   ├── icon-192.png / icon-512.png ícones do PWA (monograma "G")
│   └── exercises/                  38 pastas, 2 fotos cada (0.jpg/1.jpg) = 76 imagens
│                                    fonte: free-exercise-db (domínio público)
│
├── wrangler.jsonc                 config do Cloudflare Workers → serve ./treino como estático
├── .github/workflows/build-apk.yml  CI que builda o APK Android (aponta pro Cronograma App, não pro GIBOR)
│
├── cronograma_app.html            "Cronograma App" — gerador de cronograma via IA (legado)
├── index.html (raiz)              redireciona pra cronograma_app.html
├── manifest.json / sw.js (raiz)    PWA do Cronograma App (legado)
├── icon-192.png / icon-512.png (raiz)  ícones do Cronograma App (legado)
│
├── backend/                        FastAPI "SmartFactory" (dormente, não relacionado ao GIBOR)
│   ├── app/main.py, routers/, models/, schemas/, services/, core/
│   ├── alembic/                    migrações (1 migração: "initial_schema")
│   └── requirements.txt, Dockerfile, .env.example
│
├── frontend/                       Next.js "SmartFactory" (dormente, não relacionado ao GIBOR)
│   └── src/app/ (login, dashboard, empresa, usuarios, projetos, unidades)
│
├── android/                        Wrapper WebView → aponta pro GitHub Pages do Cronograma App
│
├── docker-compose.yml              orquestra postgres + backend + frontend do SmartFactory
│
├── .agents/skills/, agent/skills/  13 skills de design ("taste-skill") + skill "watch"
└── skills-lock.json
```

### 3.2 Estrutura interna do GIBOR (`treino/app.js`, por região)

| Linhas (aprox.) | Região |
|---|---|
| 1–67 | Dados seed: `SEED_EXERCISES` (38 exercícios), `SEED_ROUTINES` (3 rotinas prontas) |
| 69–107 | Estado e persistência: `defaultState()`, `loadState()`, `saveState()` |
| 109–314 | Utilitários: formatação de data/duração, cálculo de 1RM (Epley), volume, PR, volume semanal por grupo muscular |
| 316–333 | Supersets (agrupamento de exercícios) |
| 335–424 | Gestos: drag-to-reorder e swipe-to-delete (Pointer Events) |
| 426–478 | Toast, modal genérico, navegação/render principal |
| 480–762 | Aba **Treino** (dashboard, rotinas, treino ativo, agrupamento) |
| 764–1032 | Treino ativo: cronômetro, cartão de exercício, séries, calculadora de anilhas, menu de ações (⋮), finalizar treino |
| 1034–1046 | Diálogo de confirmação genérico |
| 1048–1227 | Cronômetro de descanso (rest timer): áudio, vibração, posição embutida vs. barra flutuante |
| 1229–1321 | Seletor de exercícios (modal reutilizado em vários fluxos) |
| 1323–1408 | Aba **Histórico** (lista + detalhe + repetir/excluir treino) |
| 1410–1671 | Aba **Exercícios** (biblioteca, detalhe, demonstração animada, gráfico de progressão SVG) |
| 1673–1703 | Diagrama corporal SVG (usado no editor de rotina) |
| 1705–1829 | Editor de rotinas |
| 1831–1939 | Aba **Perfil** (tema, unidade, timer padrão, export/import/reset de dados) |
| 1941–2032 | Medidas corporais (peso, % gordura, medidas em cm) |
| 2034–2048 | Tema (dark/light/system) e inicialização |

---

## 4. Banco de dados

**Não existe banco de dados no GIBOR.** Toda a persistência é feita via `localStorage` do navegador, sob a chave `"treino_app_v1"`, como um único blob JSON.

### 4.1 "Schema" implícito (formato do objeto `state`)

```js
state = {
  settings: { unit: 'kg'|'lb', restDefault: number, barWeight: number, theme: 'dark'|'light'|'system' },
  exercises: [ { id, name, muscle, equipment, hasImages, instructions[], custom, restOverride? } ],
  routines:  [ { id, name, exercises: [ { exerciseId, targetSets, repsMin?, repsMax? } ] } ],
  workouts:  [ { id, name, date, startedAt, durationSec, notes, exercises: [
                  { uid, exerciseId, groupId?, notes?, sets: [ { uid, weight, reps, rpe, completed, warmup } ] }
              ] } ],
  activeWorkout: null | { ...mesmo formato de um workout, mas em andamento },
  bodyMeasurements: [ { id, date, weight, bodyFat, chest, waist, hips, arm, thigh, calf } ],
}
```

- **Sem relacionamentos reais de banco:** as "relações" são por convenção de string (`we.exerciseId` referencia `exercises[].id`), sem integridade referencial garantida pelo runtime — se um exercício custom for excluído, os workouts antigos continuam guardando o `exerciseId` órfão (o código trata isso com fallback `'Exercício'` na exibição, então não quebra, mas o vínculo se perde).
- **Sem versionamento de schema/migração:** `loadState()` faz um merge raso (`{ ...def.settings, ...parsed.settings }`) para tolerar campos novos, mas não há nenhum mecanismo de migração formal se o formato mudar de forma mais profunda no futuro.
- **Sem índices, sem paginação, sem queries:** tudo é filtrado/ordenado em memória com `.filter()`/`.sort()` do JavaScript a cada render.

### 4.2 APIs

**Não existem APIs no GIBOR.** Não há `fetch()` para nenhum backend. O único I/O de rede são as fontes do Google e as imagens locais de exercícios.

(O backend FastAPI em `backend/` expõe rotas REST — `routers/auth.py`, `empresa.py`, `usuario.py`, `projeto.py`, `unidade.py` — mas são para o domínio "SmartFactory", desconectadas do GIBOR.)

---

## 5. Autenticação

**Não existe autenticação, cadastro, login ou conceito de usuário no GIBOR.** O app é single-user por dispositivo/navegador: quem abre o app vê e edita os dados salvos naquele `localStorage` específico. Não há:
- Login/senha
- Contas de usuário
- Sessões/tokens
- Sincronização entre dispositivos
- Qualquer noção de "quem sou eu" no app

Isso significa também que **não há RLS (Row Level Security) a verificar** — não existe Supabase, nem qualquer banco de dados com controle de acesso por linha, no GIBOR. (O backend "SmartFactory" dormente tem autenticação JWT + bcrypt + RBAC por `empresa_id`, mas é de outro produto, não conectado ao GIBOR — poderia servir de referência de padrão caso o GIBOR ganhe backend no futuro, mas o modelo de dados não se aplica.)

---

## 6. Telas existentes

O GIBOR tem 4 abas principais (bottom nav) + telas de detalhe/modais:

1. **Treino** (`renderTreinoTab`)
   - Dashboard: total de treinos, treinos na semana, volume total
   - Card de volume semanal por grupo muscular (barras)
   - Botão "Começar Treino Vazio"
   - Lista de rotinas salvas (iniciar / editar / excluir)
   - **Sub-tela: Treino Ativo** (`renderActiveWorkout`) — cronômetro, barra de progresso, cartões de exercício com séries editáveis, supersets, drag-to-reorder, cronômetro de descanso embutido

2. **Histórico** (`renderHistoricoTab`)
   - Lista de treinos concluídos (data, duração, séries, volume)
   - **Sub-tela: Detalhe do treino** — resumo (card estilo "Strong"), todas as séries por exercício, repetir treino, excluir

3. **Exercícios** (`renderExerciciosTab`)
   - Biblioteca com busca + filtro por grupo muscular
   - Criar exercício customizado
   - **Sub-tela: Detalhe do exercício** — foto/demonstração animada (2 frames), instruções passo a passo, recorde (PR + 1RM estimado), gráfico de progressão de carga (SVG), histórico de séries, preferência de timer de descanso por exercício

4. **Perfil** (`renderPerfilTab`)
   - Tema (escuro/claro/sistema), unidade (kg/lb), timer padrão, peso padrão da barra
   - Exportar/importar dados (JSON), apagar todos os dados
   - **Sub-tela: Medidas Corporais** — registro de peso corporal, % gordura, medidas (peito/cintura/quadril/braço/coxa/panturrilha), gráfico de progressão de peso

### Modais reutilizáveis
Seletor de exercícios, criar exercício, calculadora de anilhas, menu de ações do exercício (⋮), editor de observação, editor de temporizador (por exercício e geral), substituir exercício, agrupar em superset, finalizar treino, editor de rotina, confirmação genérica, editor de faixa de repetições, editor numérico (stepper).

---

## 7. Componentes reutilizáveis

Não há componentes no sentido de framework (React/Vue), mas há **funções-fábrica de UI reutilizadas em vários pontos**:

- `openModal(html)` / `closeModal()` — sistema de modal genérico (todo modal do app usa isso)
- `makeEmpty(text)` — estado vazio padronizado (ícone + texto)
- `toast(msg)` — notificação temporária
- `confirmDialog(message, onConfirm)` — confirmação padronizada
- `renderLineChartSVG(points, unit)` — gráfico de linha SVG, usado tanto na progressão de carga por exercício quanto na progressão de peso corporal
- `bodyDiagramSVG(activeMuscles)` — diagrama corporal frente/costas, usado no editor de rotina
- `enableDragReorder()` / `enableSwipeToDelete()` — gestos reutilizados em séries, exercícios do treino ativo e exercícios da rotina
- `openExercisePicker()` — seletor de exercícios reaproveitado em: começar treino vazio, adicionar exercício ao treino ativo, substituir exercício, montar rotina
- Sistema de tema via CSS custom properties (`--bg`, `--surface`, `--text`, `--accent` etc.), consumido por toda a folha de estilo

---

## 8. Funcionalidades existentes

- Criar/editar/excluir rotinas de treino, com exercícios, séries-alvo e faixa de repetições
- Iniciar treino vazio ou a partir de rotina; repetir um treino do histórico
- Registrar séries (peso, reps, RPE), marcar como aquecimento, marcar como concluída
- Sugestão de peso/reps ao logar, baseada no **melhor desempenho histórico** naquela posição de série (não apenas o último treino)
- Detecção automática de **PR (recorde pessoal)** por série, com selo 🏆
- Supersets (agrupar exercícios alternados sem descanso)
- Substituir exercício dentro de um treino em andamento
- Observação por exercício dentro do treino
- Cronômetro de descanso configurável (padrão global + override por exercício), com alarme sonoro (Web Audio) + vibração, editável em tempo real, com posição embutida entre séries
- Calculadora de anilhas por lado (kg/lb, considerando peso da barra)
- Drag-to-reorder de exercícios/séries e swipe-to-delete
- Biblioteca de exercícios com fotos reais (free-exercise-db), instruções passo a passo, filtro por grupo muscular e busca
- Exercícios customizados pelo usuário
- Gráfico de progressão de carga por exercício (peso máximo por sessão ao longo do tempo)
- Cálculo de 1RM estimado (fórmula de Epley)
- Volume total e por grupo muscular (últimos 7 dias)
- Resumo do treino ao finalizar (duração, volume, séries, PRs) — igual ao card mostrado no histórico
- Medidas corporais (peso, % gordura, medidas em cm) com gráfico de evolução do peso
- Tema claro/escuro/sistema
- Unidade kg/lb (não converte dados já registrados — documentado na própria UI)
- Exportar/importar backup em JSON; apagar todos os dados
- PWA instalável, funciona offline (Service Worker com fallback), atualiza sozinho (cache network-first)

---

## 9. Problemas encontrados

### Bugs / inconsistências de comportamento
1. **Inconsistência de reseed em `loadState()`** (`app.js:92-93`): se o usuário excluir **todos** os exercícios (array fica `[]`), o app silenciosamente volta a semear os 38 exercícios padrão no próximo carregamento (`parsed.exercises.length` é falso → usa `def.exercises`). Já rotinas (`parsed.routines || def.routines`) **não** têm essa checagem de tamanho — um array vazio de rotinas é respeitado. Comportamento inconsistente entre os dois casos, provavelmente não intencional.
2. **Import de backup com validação fraca** (`app.js:1913`): só checa se `data.exercises` e `data.workouts` existem, sem validar a forma interna. Um JSON malformado (mas com essas duas chaves presentes) pode ser aceito e quebrar telas depois, com erros no console em vez de uma mensagem clara ao usuário.
3. **Service Worker: instalação atômica com dependência externa** (`sw.js:12-14`): `caches.addAll(ASSETS)` inclui a URL do Google Fonts. Se essa requisição falhar (rede instável, bloqueio, mudança de URL da fonte), a instalação **inteira** do SW falha silenciosamente, e o usuário pode ficar preso numa versão antiga do cache sem saber por quê.
4. **Vínculo órfão em exclusão de exercício customizado**: ao excluir um exercício customizado, o histórico é preservado (comportamento correto e documentado na própria confirmação), mas não há nenhuma tela que explique/exiba exercícios "órfãos" de forma diferenciada — aparecem como "Exercício" genérico sem musculatura/equipamento.
5. **Sem tratamento de erro de quota do `localStorage`**: `saveState()` chama `localStorage.setItem` diretamente, sem `try/catch`. Se o armazenamento estourar (dispositivo com pouco espaço, muitos anos de histórico com fotos... embora fotos não fiquem no localStorage, apenas os dados), o app pode quebrar sem aviso ao usuário.

### Riscos de arquitetura
6. **Toda a lógica de negócio roda no navegador, sem nenhuma auditoria/telemetria**: se `saveState()` falhar por qualquer motivo, o usuário só percebe quando reabrir o app e os dados não estarem lá.
7. **CI do Android desalinhado**: `.github/workflows/build-apk.yml` builda a cada push em `main`, mas empacota o **Cronograma App** (legado), não o GIBOR. Isso gasta minutos de CI numa build que não corresponde ao produto atual e pode confundir quem olhar o repositório esperando um APK do GIBOR.

---

## 10. Débitos técnicos

- **Nenhum teste automatizado** (unitário, integração ou E2E) faz parte do repositório — toda validação até aqui foi manual/Playwright ad hoc por sessão de chat, sem persistir como suíte.
- **Nenhum linter/formatter configurado** (sem ESLint/Prettier) para `treino/`.
- **Arquivo único de 2050 linhas** (`app.js`) sem módulos — qualquer nova feature tende a aumentar ainda mais esse arquivo, dificultando manutenção e revisão de diffs.
- **Sem TypeScript/JSDoc** — nenhuma tipagem, então erros de forma de dados (ex.: campo esperado que não existe) só aparecem em runtime.
- **Performance de leitura O(n) repetida**: funções como `getExercisePR()`, `getExerciseWorkouts()`, `isSetPR()` percorrem `state.workouts` inteiro toda vez que são chamadas, e são chamadas *por card, por série, a cada render*. Com poucos meses de uso isso é imperceptível, mas cresce de forma quadrática (ou pior) conforme o histórico aumenta — vale considerar memoização ou índices quando o volume de treinos crescer.
- **Acessibilidade**: muitos botões usam apenas ícone/emoji sem `aria-label` (ex.: `drag-handle`, `ex-plate-btn`, `set-check`), o que prejudica leitores de tela.
- **Sem CSP (Content Security Policy)** declarada no `index.html` — não é um risco prático hoje (não há inputs perigosos sendo injetados sem `esc()`), mas é uma camada de defesa em profundidade ausente.
- **Monorepo confuso**: a coexistência de 4 produtos não relacionados na mesma raiz do repositório (GIBOR, Cronograma App, backend/frontend SmartFactory, Android) aumenta a chance de alguém mexer no lugar errado, ou de ferramentas de CI/análise se confundirem sobre "qual é o projeto".

---

## 11. Verificação de dados mockados

- Os **38 exercícios seed** (`SEED_EXERCISES`) e as **3 rotinas seed** (`SEED_ROUTINES`) são dados estáticos embutidos no código — isso é esperado e correto para um app sem backend (são o "catálogo padrão" que todo novo usuário recebe, e o usuário pode editar/adicionar livremente por cima). Não é um mock disfarçado de dado real; é o design intencional do produto.
- **Não há dado fake se passando por dado dinâmico** em nenhuma tela — tudo que é exibido (histórico, PRs, gráficos, volume) vem de cálculo real sobre `state.workouts`, que só existe se o usuário efetivamente registrar treinos.
- **Não há chamadas de API "mockadas" esperando um backend futuro** — simplesmente não existe camada de API no GIBOR hoje.

---

## 12. Verificação de RLS / Supabase

Não aplicável: **não há Supabase em nenhuma parte do repositório** (confirmado via busca textual completa). Não há RLS a auditar porque não há banco de dados multi-tenant nem qualquer tabela com controle de acesso por linha no GIBOR. O único banco de dados do monorepo é o PostgreSQL usado pelo backend "SmartFactory" dormente (`docker-compose.yml`, `backend/app/database.py`), que também não usa Supabase — é PostgreSQL "puro" via SQLAlchemy/Alembic, sem nenhuma política RLS definida nas migrações revisadas.

---

## 13. Como o app calcula hoje

### Treino (progressão de carga)
- **1RM estimado:** fórmula de Epley — `peso × (1 + reps / 30)` (`epley1RM`)
- **PR (recorde):** maior peso já levantado numa série válida (concluída, sem ser aquecimento, com peso e reps) para aquele exercício, comparando contra todo o histórico (`getExercisePR`, `isSetPR`)
- **Sugestão ao logar:** não é "IA" — é busca determinística pela **melhor série histórica** na mesma posição (1ª série, 2ª série, etc.) daquele exercício (`getBestPerformance`), usada como placeholder nos campos de reps/peso/RPE
- **Volume:** soma de `peso × reps` de todas as séries concluídas (não-aquecimento) — por treino (`workoutVolume`) e por grupo muscular na semana (`getWeeklyMuscleVolume`)
- **Gráfico de progressão:** maior peso de série concluída por sessão, plotado num SVG simples (sem biblioteca de gráficos)

### Dieta
**Não existe nenhuma funcionalidade de dieta/nutrição no GIBOR hoje.** Não há registro de refeições, calorias, macros, água, ou qualquer dado nutricional. É uma lacuna total de feature, não um cálculo incompleto.

### Evolução geral
- "Evolução" no app atual = as duas coisas acima (progressão de carga por exercício + medidas corporais/peso ao longo do tempo, com gráfico simples de peso corporal). Não há um score de evolução consolidado, nem comparação de período a período (ex.: "este mês vs mês passado"), nem detecção de platô/estagnação.

---

## 14. Integrações existentes

- **Google Fonts** (`fonts.googleapis.com`) — carregamento de tipografia, cacheado pelo Service Worker
- **free-exercise-db** (GitHub, domínio público) — origem das 76 fotos de exercícios, já baixadas e versionadas localmente em `treino/exercises/` (não é uma integração em tempo de execução, é um asset estático já incorporado)
- **Web Audio API** — geração do bipe do alarme de descanso (sem áudio externo)
- **Vibration API** (`navigator.vibrate`) — feedback tátil ao fim do descanso
- **Service Worker / Cache API** — funcionamento offline

Não há integração com: nenhuma IA/LLM, nenhum backend próprio, nenhum provedor de autenticação, nenhuma rede social, nenhuma wearable/health API (Apple Health, Google Fit), nenhum serviço de pagamento.

---

## 15. Pontos onde a IA pode agregar valor real

Ordenados por impacto vs. esforço de implementação, considerando que hoje **tudo roda client-side sem backend**:

1. **Sugestão inteligente de progressão de carga** (baixo esforço, alto impacto): hoje a sugestão é só "repita seu melhor histórico". Uma IA (ou mesmo uma heurística mais elaborada) poderia sugerir *quanto aumentar* com base em tendência recente, RPE reportado e faixa de reps alvo da rotina — evoluindo o que já existe em `getBestPerformance`, sem precisar de backend (pode rodar como lógica local).
2. **Geração de rotina personalizada por IA** (esforço médio): usuário descreve objetivo/equipamento/dias disponíveis, IA monta uma rotina usando o catálogo de exercícios existente (`state.exercises`) — reaproveita 100% do editor de rotina já existente.
3. **Resumo/insights de treino em linguagem natural** (esforço médio): ao final de um treino ou da semana, gerar um texto curto ("você bateu 2 PRs, seu volume de peito caiu 15% essa semana...") usando os dados já calculados (`getWeeklyMuscleVolume`, `countWorkoutPRs`).
4. **Detecção de platô/estagnação** (esforço médio): analisar a série histórica de 1RM estimado por exercício e sinalizar quando não há progresso há N sessões, sugerindo variação (deload, mudança de exercício, ajuste de reps).
5. **Registro por linguagem natural** ("supino 80kg x8 x3" vira 3 séries preenchidas automaticamente) — reduz fricção de digitação, especialmente no celular durante o treino.
6. **Modo dieta assistido por IA** (esforço alto, feature nova do zero): como não existe nada de nutrição hoje, dá pra desenhar do zero já pensando em IA — ex.: descrever refeição em texto/foto e a IA estima macros, ou gerar plano alimentar a partir de objetivo + peso + rotina de treino.
7. **Análise de forma via câmera** (esforço muito alto, incerto): visão computacional para dar feedback de execução do movimento — tecnicamente ambicioso, exigiria modelo especializado e provavelmente backend; citar como possibilidade de longo prazo, não como próximo passo.

⚠️ Importante: itens 1–5 podem ser implementados **sem precisar de backend**, chamando uma API de LLM diretamente do cliente (como o próprio `cronograma_app.html` legado já faz com a Anthropic) — mas isso expõe a chave de API no navegador, então o caminho recomendado de verdade é um pequeno backend/proxy (serverless, ex. Cloudflare Worker de função, não apenas assets estáticos) que guarda a chave server-side. Isso é abordado no plano de evolução abaixo.

---

## 16. Plano de evolução do GIBOR

Princípio geral: **evoluir, não reescrever**. O app atual funciona bem, está em produção, e sua arquitetura simples (vanilla JS + localStorage) é uma escolha válida para o estágio atual. A evolução proposta é incremental, em camadas, preservando 100% da identidade visual e das funcionalidades atuais.

### Camada 1 — Consolidação (sem features novas visíveis ao usuário)
- Adicionar `try/catch` e feedback ao usuário em `saveState()` (proteção contra estouro de quota do `localStorage`)
- Corrigir a inconsistência de reseed de exercícios vazios vs. rotinas vazias em `loadState()`
- Reforçar validação do import de JSON (schema mínimo antes de aceitar)
- Remover a URL do Google Fonts do `caches.addAll` atômico do SW (cachear separadamente, sem travar a instalação)
- Desligar ou redirecionar o `build-apk.yml` para não empacotar o app errado (ou empacotar o GIBOR, se um APK fizer sentido)

### Camada 2 — Backend mínimo (habilita tudo que vem depois)
- Introduzir um backend leve (ex.: Cloudflare Worker com função, não apenas assets estáticos) cuja única responsabilidade inicial é **proxyar chamadas de IA** com segurança (chave de API do lado servidor)
- Ainda sem banco de dados nem autenticação — o `localStorage` continua sendo a fonte de verdade dos dados do usuário; o backend só processa, não persiste
- Esse passo é o pré-requisito técnico para as features de IA da Camada 3

### Camada 3 — IA aplicada ao treino (usa o backend da Camada 2)
- Sugestão inteligente de progressão de carga (item 1 da seção 15)
- Geração de rotina personalizada por IA (item 2)
- Resumo/insights pós-treino em linguagem natural (item 3)
- Detecção de platô (item 4)

### Camada 4 — Dieta (feature nova)
- Modelo de dados novo (`state.meals` / `state.nutritionGoals`), seguindo o mesmo padrão local-first já usado para treino
- Registro manual de refeições/macros como base (sem IA) primeiro, para validar a necessidade
- Camada de IA por cima (estimar macros por descrição/foto) só depois de validado o registro manual

### Camada 5 — Conta e sincronização (opcional, decisão de produto)
- Só se o usuário quiser sincronizar entre dispositivos ou não perder dados ao trocar de celular
- Aí sim entraria autenticação real e um banco de dados de fato (Postgres/Supabase), com o `localStorage` virando cache local em vez de única fonte de verdade
- É a mudança de maior risco/esforço do plano — recomendo tratá-la como decisão separada, não como parte automática da evolução de IA

---

## 17. Ordem de implementação recomendada

1. **Camada 1** (consolidação) — baixo risco, pode ser feito em qualquer momento, inclusive em paralelo com o resto
2. **Camada 2** (backend mínimo de IA) — desbloqueia tudo daqui pra frente
3. **Camada 3, item 1** (sugestão inteligente de progressão) — maior impacto percebido pelo usuário com menor esforço, reaproveita tela e dados já existentes
4. **Camada 3, item 3** (resumo/insights pós-treino) — reaproveita o card de resumo que já existe, só adiciona um texto gerado
5. **Camada 3, item 2** (geração de rotina por IA) — reaproveita o editor de rotina existente
6. **Camada 3, item 4** (detecção de platô) — depende de mais histórico acumulado para ser útil, pode vir depois
7. **Camada 4** (dieta, começando pelo registro manual) — feature nova maior, mais independente do resto
8. **Camada 5** (conta/sync) — só entra na fila se/quando virar prioridade de produto

---

## Resumo executivo

O GIBOR é um PWA de treino **100% client-side**, sem backend, sem banco de dados e sem autenticação — todos os dados vivem no `localStorage` do dispositivo. É uma base sólida, funcional e já validada em produção, mas com débitos técnicos típicos de um app que cresceu por iteração rápida num único arquivo (sem testes, sem módulos, sem tipagem). Não há dieta implementada hoje — é lacuna total, não bug. Não há Supabase/RLS a auditar porque não há banco de dados multi-tenant no GIBOR. O repositório também carrega três outros projetos não relacionados (Cronograma App legado, backend/frontend "SmartFactory" dormentes, wrapper Android do app legado) que não afetam o GIBOR mas confundem a leitura do repositório.

O caminho de evolução recomendado é incremental: primeiro consolidar o que existe, depois introduzir um backend mínimo só para viabilizar IA com segurança, então aplicar IA às features de treino já existentes (que têm o maior retorno com o menor esforço), e só depois considerar dieta (feature nova) e conta/sincronização (mudança arquitetural maior, a ser decidida separadamente).
