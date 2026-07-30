# Master Orchestrator — StudyOS

Spec canônica do orquestrador. Implementação: `backend/app/studyos/orchestrator.py`.

## Identidade

Coordena agentes especializados. Nunca ensina conteúdo, nunca responde questões,
nunca cria cronogramas e nunca gera exercícios diretamente. Decide quais agentes
executar, em qual ordem e quais podem executar em paralelo.

## Objetivo

Receber uma solicitação do usuário e transformá-la em um fluxo de trabalho
composto por agentes especializados.

## Responsabilidades

1. Interpretar a intenção do usuário.
2. Identificar quais agentes precisam participar.
3. Executar agentes independentes em paralelo.
4. Respeitar dependências entre agentes.
5. Consolidar todos os resultados.
6. Enviar apenas a resposta final ao usuário.

## Regras

| Regra | Onde é garantida no código |
| --- | --- |
| Nunca inventar informações | `RunnerEstrutural` declara lacunas em vez de preencher; agente 01 devolve `null` para campo não informado |
| Nunca pular agentes obrigatórios | `agents.AGENTES_OBRIGATORIOS` + `intents.selecionar_agentes` |
| Nunca executar agente cuja entrada não exista | `graph.ondas_de_execucao` (ordem topológica) + checagem de dependência no `MasterOrchestrator` |
| Priorizar execução paralela | agentes sem dependência entre si caem na mesma onda e rodam via `asyncio.gather` |
| Sempre validar com os verificadores | agente 24 (`validators.validar`) fecha todo fluxo |

## Fluxo

```
objetivo → diagnóstico → planejamento → produção → validação → consolidação → resposta final
```

## Saída

Sempre e apenas quatro blocos:

- `agentes_executados`
- `ordem_execucao`
- `tarefas_realizadas`
- `resultado_consolidado`

## Agentes disponíveis

| # | Agente | Fase | Depende de |
| --- | --- | --- | --- |
| 01 | Profile Analyzer | diagnóstico | — |
| 02 | Goal Analyzer | diagnóstico | 01 |
| 03 | Knowledge Analyzer | diagnóstico | 01, 02 |
| 04 | Curriculum Builder | planejamento | 01, 02, 03 |
| 05 | Dependency Mapper | planejamento | 01, 02, 03, 04 |
| 06 | Roadmap Builder | planejamento | 01, 02, 03, 04, 05 |
| 07 | Lesson Generator | produção | 01, 03, 04, 05, 06 |
| 08 | Example Generator | produção | 01, 03, 07 |
| 09 | Exercise Generator | produção | 01, 03, 04, 05, 06, 07, 08 |
| 10 | Flashcard Generator | produção | 01, 03, 04, 05, 06, 07, 08, 09 |
| 11 | Summary Generator | produção | 01, 03, 04, 05, 06, 07, 08, 09, 10 |
| 12 | Difficulty Detector | tutoria | 01, 02, 03, 04, 05, 06, 09 |
| 13 | Adaptive Teacher | tutoria | 01, 02, 03, 07, 08, 09, 10, 11, 12 |
| 14 | Memory Scheduler | memória | 01, 02, 03, 05, 06, 10, 11, 12, 13 |
| 15 | Revision Planner | memória | 06, 14 |
| 16 | Exam Simulator | avaliação | 04, 09 |
| 17 | Error Analyzer | avaliação | 16 |
| 18 | Weakness Finder | avaliação | 17 |
| 19 | Coach | acompanhamento | 01, 06 |
| 20 | Habit Builder | acompanhamento | 01, 06 |
| 21 | Performance Analyzer | acompanhamento | 17 |
| 22 | Forecast Agent | acompanhamento | 06, 21 |
| 23 | Optimization Agent | acompanhamento | 18, 22 |
| 24 | Validators | validação | todos os executados |

Obrigatórios em qualquer fluxo: **01**, **02** e **24**.

## Workflows por intenção

| Intenção | Agentes pedidos (dependências entram automaticamente) |
| --- | --- |
| `diagnostico` | 01, 02, 03 |
| `criar_plano` | 01–06, 14, 15, 19, 20 |
| `estudar_topico` | 04, 07, 08, 11, 12, 13 |
| `gerar_exercicios` | 04, 09, 12 |
| `revisar` | 10, 11, 14, 15 |
| `simulado` | 09, 16, 17, 18 |
| `analise_desempenho` | 16, 17, 18, 21, 22, 23 |
| `motivacao` | 06, 19, 20 |
| `completo` | 01–23 (fallback quando a intenção não é reconhecida) |
