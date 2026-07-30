# Agente 06 — Roadmap Builder

Implementação: `backend/app/studyos/agentes/roadmap.py`.

## Identidade

Transforma o Grafo de Aprendizagem em um **Plano de Estudos**. Não ensina, não
gera conteúdo, não responde dúvidas — organiza *quando* cada conteúdo é
estudado.

## Três decisões estruturais

**Só folhas entram na agenda.** Os tempos da árvore se acumulam para cima
(módulo = soma dos tópicos). Agendar pai e filho contaria o mesmo estudo duas
vezes, então as unidades agendáveis são as folhas pendentes do grafo.

**A dependência do agente 05 é intransponível.** Um nó só entra no dia D se
todos os pré-requisitos dele *e dos seus ancestrais* estiverem concluídos ou
integralmente alocados antes de D — inclusive quando um tópico foi partido em
várias sessões: o dependente só começa depois da última parte.

**O que não couber não some.** Conteúdo sem espaço até a prova sai em
`conteudos_nao_alocados` com o déficit em horas e vira risco alto, nunca
descarte silencioso.

## Entradas

| Campo | Origem |
| --- | --- |
| Perfil Cognitivo | agente 01 — carga máxima diária, dias por semana, horas efetivas |
| Mapa Estratégico | agente 02 — prioridade das disciplinas, prazo final |
| Mapa de Conhecimento | agente 03 — o que já está dominado |
| Árvore Curricular | agente 04 — tempos por nó |
| Grafo de Aprendizagem | agente 05 — dependências, status e sequência lógica |
| `data_inicio`, `data_prova`, `dias_da_semana`, `faltas`, `progresso` | usuário |

## Como o dia é montado

A carga diária vem do agente 01 (já limitada pelo teto cognitivo) e é dividida
em três blocos fixos — é assim que as regras "sempre incluir revisão" e "sempre
reservar tempo para exercícios" ficam garantidas por construção:

| Bloco | Fração | Quem gera o conteúdo depois |
| --- | --- | --- |
| Conteúdo novo | 60% | 07 Lesson Generator |
| Exercícios | 25% | 09 Exercise Generator |
| Revisão | 15% | 14 Memory Scheduler (aqui é reserva provisória) |

A cada 14 dias de estudo o bloco de exercícios vira **simulado** (agente 16).

**Fadiga e alternância.** Dentro do dia, a escolha do próximo bloco evita
repetir a disciplina anterior e alterna carga pesada com leve — esses critérios
vêm **antes** da prioridade de propósito: tudo que está elegível será estudado
de qualquer forma, e deixar a prioridade mandar sozinha empilharia a mesma
disciplina em blocos seguidos. A prioridade continua decidindo quem abre o dia
e a ordem global.

Tópico maior que o bloco diário é partido em `parte 1`, `parte 2`, … sem
quebrar dependência.

## Replanejamento

O plano é recalculado por inteiro a cada execução. Os gatilhos detectados
aparecem em `replanejamento.gatilhos_detectados`:

| Gatilho | Efeito |
| --- | --- |
| `faltas` (datas) | os dias saem do cronograma e o conteúdo desliza |
| `progresso` (ids ou nomes) | as unidades saem da fila |
| `data_prova` alterada | o horizonte encurta ou estende |
| `horas_por_dia` / `dias_da_semana` | muda a capacidade diária e os dias ocupados |

## Saída

```jsonc
{
  "resumo_geral": {
    "data_inicio": "2026-01-05", "data_conclusao_prevista": "2026-01-19",
    "data_da_prova": "2026-02-20", "total_horas_planejadas": 21.0,
    "total_horas_semanais": 10.5, "total_horas_diarias": 2.1,
    "dias_de_estudo_por_semana": ["segunda", "terca", "quarta", "quinta", "sexta"]
  },
  "cronograma": [{
    "data": "2026-01-05", "dia_semana": "segunda", "tempo_total_h": 2.11,
    "sessoes": [
      { "tipo": "conteudo", "disciplina": "Estatística", "conteudo": "Conjuntos",
        "objetivo_da_sessao": "Estudar Conjuntos (Estatística)", "tempo_estimado_h": 1.26,
        "prioridade": "media", "dificuldade": "dificil", "no_id": "d1.m1.t1", "parte": "parte 1" },
      { "tipo": "exercicios", "conteudo": "Estatística", "tempo_estimado_h": 0.53, "origem": "09 Exercise Generator" },
      { "tipo": "revisao", "conteudo": "conteúdo do dia", "tempo_estimado_h": 0.32, "origem": "reserva provisória até o agente 14 Memory Scheduler" }
    ]
  }],
  "metas": {
    "diaria": { "horas": 2.1, "blocos": ["conteúdo", "exercícios", "revisão"], "regra": "60% conteúdo, 25% exercícios, 15% revisão" },
    "semanal": [ { "semana": "2026-S02", "horas": 8.4, "dias": 4, "conteudos": ["Conjuntos", "Sintaxe"] } ],
    "mensal": [ { "mes": "2026-01", "horas": 21.0, "dias": 10, "disciplinas": ["Estatística", "Português"] } ]
  },
  "indicadores": {
    "percentual_planejado": 1.0, "percentual_concluido": 0.1,
    "horas_necessarias": 12.5, "horas_planejadas": 12.5, "horas_restantes": 0.0,
    "dias_restantes": 46, "dias_de_estudo_planejados": 10, "risco_de_atraso": "baixo"
  },
  "conteudos_nao_alocados": [],
  "riscos": [ { "risco": "faltas_registradas", "severidade": "media", "evidencia": "1 dia(s) de estudo perdido(s) e replanejado(s)" } ],
  "replanejamento": { "automatico": true, "gatilhos_detectados": ["faltas informadas", "data da prova informada"] },
  "consumido_por": ["07","09","10","11","14","15","16","19","20","21","22","23","24"]
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca violar dependências do agente 05 | pré-requisitos efetivos (do nó + ancestrais) precisam estar concluídos ou 100% alocados antes da alocação |
| Nunca ultrapassar a carga máxima do Perfil | a capacidade diária é `carga_maxima_diaria.horas` do agente 01, e a soma das sessões nunca a excede |
| Nunca deixar dia disponível sem estudo | todo dia da semana marcado como disponível é ocupado enquanto houver conteúdo elegível |
| Sempre incluir revisão | bloco fixo de 15% em todo dia com estudo |
| Sempre reservar exercícios | bloco fixo de 25%, virando simulado a cada 14 dias de estudo |
| Sempre permitir replanejamento | recálculo completo a cada execução, com gatilhos declarados |
| Não ensinar, não gerar aulas nem exercícios | as sessões carregam rótulo, tempo e agente responsável — nunca o conteúdo em si |

## Consumidores

07 · 09 · 10 · 11 · 14 · 15 · 16 · 19 · 20 · 21 · 22 · 23 · 24.
