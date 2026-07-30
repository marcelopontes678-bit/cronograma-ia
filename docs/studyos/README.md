# StudyOS

Camada de orquestração de agentes de estudo, servida pelo backend FastAPI.

## Estrutura

```
backend/app/studyos/
├── agents.py        # catálogo dos 24 agentes: fase, tarefa, dependências
├── graph.py         # fecho de dependências, ondas de execução, detecção de ciclo
├── intents.py       # classificação da solicitação → workflow
├── runner.py        # contrato de execução + runners (estrutural, delegado)
├── validators.py    # agente 24: validação estrutural do fluxo
├── orchestrator.py  # Master Orchestrator
└── agentes/         # implementações concretas
    ├── comum.py     # coerção de entradas compartilhada
    ├── perfil.py       # agente 01 — Profile Analyzer
    ├── objetivo.py     # agente 02 — Goal Analyzer
    ├── conhecimento.py # agente 03 — Knowledge Analyzer
    ├── curriculo.py    # agente 04 — Curriculum Builder
    ├── dependencias.py # agente 05 — Dependency Mapper
    ├── roadmap.py      # agente 06 — Roadmap Builder
    ├── aula.py         # agente 07 — Lesson Generator
    ├── exemplos.py     # agente 08 — Example Generator
    ├── exercicios.py   # agente 09 — Exercise Generator
    ├── flashcards.py   # agente 10 — Flashcard Generator
    ├── resumos.py      # agente 11 — Summary Generator
    ├── dificuldade.py  # agente 12 — Difficulty Detector
    └── portoes.py      # regras de bloqueio compartilhadas
```

Specs dos agentes: [`00-master-orchestrator.md`](00-master-orchestrator.md),
[`01-profile-analyzer.md`](01-profile-analyzer.md),
[`02-goal-analyzer.md`](02-goal-analyzer.md),
[`03-knowledge-analyzer.md`](03-knowledge-analyzer.md),
[`04-curriculum-builder.md`](04-curriculum-builder.md),
[`05-dependency-mapper.md`](05-dependency-mapper.md),
[`06-roadmap-builder.md`](06-roadmap-builder.md),
[`07-lesson-generator.md`](07-lesson-generator.md),
[`08-example-generator.md`](08-example-generator.md),
[`09-exercise-generator.md`](09-exercise-generator.md),
[`10-flashcard-generator.md`](10-flashcard-generator.md),
[`11-summary-generator.md`](11-summary-generator.md),
[`12-difficulty-detector.md`](12-difficulty-detector.md).

## API

Todas as rotas sob `/api/v1/studyos`. O orquestrador é stateless: não lê banco
nem exige autenticação.

| Método | Rota | O que faz |
| --- | --- | --- |
| `GET` | `/agentes` | catálogo dos 24 agentes |
| `POST` | `/plano` | mostra quais agentes rodariam e em que ordem, sem executar |
| `POST` | `/orquestrar` | executa o fluxo e devolve a resposta consolidada |

```bash
curl -X POST localhost:8000/api/v1/studyos/orquestrar \
  -H 'Content-Type: application/json' \
  -d '{
    "solicitacao": "Monte um cronograma para o ICMS-SP",
    "formato": "markdown",
    "dados_usuario": {
      "idade": 29, "escolaridade": "Superior completo",
      "objetivo": "Passar no ICMS-SP", "profissao": "Analista",
      "rotina": "Trabalho em tempo integral",
      "horas_por_dia": 3, "dias_por_semana": 5, "data_prova": "2026-10-01",
      "experiencia_anterior": "já estudei um ano",
      "disciplinas_favoritas": ["Português"],
      "disciplinas_dificuldade": ["Estatística", "RLM"],
      "preferencia_estudo": "videoaula e mapa mental",
      "edital": {"Português": ["Sintaxe", "Crase"], "RLM": ["Lógica proposicional"]},
      "nota_corte": 70
    }
  }'
```

## Conectando um modelo

Os agentes 01–06 são determinísticos e não precisam de modelo. O agente 07 em
diante produz conteúdo didático: ele monta o briefing e delega a redação a um
**redator**, mantendo as regras (portão de pré-requisitos, estrutura, fontes)
no código.

```python
from app.studyos import MasterOrchestrator
from app.studyos.runner import RunnerEstrutural

def redator(briefing: dict) -> dict:
    return {s["chave"]: chamar_modelo(briefing, s) for s in briefing["secoes"]}

orquestrador = MasterOrchestrator(
    RunnerEstrutural(redatores={"07": redator, "08": redator_de_exemplos})
)
```

Para trocar o motor inteiro — inclusive os agentes determinísticos — injete um
runner próprio:

```python
from app.studyos import MasterOrchestrator, RunnerDelegado

async def gerar(spec, entradas) -> dict:
    ...  # chamada ao modelo com spec.tarefa e entradas
    return {"conteudo": "..."}

orquestrador = MasterOrchestrator(RunnerDelegado(gerar))
```

O grafo, o paralelismo e a validação continuam idênticos — só o motor de geração
muda.

## Testes

```bash
cd backend && python -m pytest tests -q
```
