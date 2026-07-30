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
    └── perfil.py    # agente 01 — Profile Analyzer
```

Specs dos agentes: [`00-master-orchestrator.md`](00-master-orchestrator.md),
[`01-profile-analyzer.md`](01-profile-analyzer.md).

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
      "preferencia_estudo": "videoaula e mapa mental"
    }
  }'
```

## Conectando um modelo

O runner padrão (`RunnerEstrutural`) roda as implementações concretas e devolve
briefing para os agentes ainda não implementados — ele nunca inventa conteúdo de
estudo. Para plugar um modelo, basta injetar um runner:

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
