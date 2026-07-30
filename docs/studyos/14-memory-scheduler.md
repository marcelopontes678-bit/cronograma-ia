# Agente 14 — Memory Scheduler

Implementação: `backend/app/studyos/agentes/memoria.py`.

## Identidade

Decide *quando* cada conteúdo volta. Não ensina, não cria conteúdo, não gera
exercícios e **não altera o cronograma principal** — o plano de revisões é uma
camada à parte, que o agente 15 encaixa depois.

Determinístico de ponta a ponta: repetição espaçada é algoritmo, não redação.

## Retenção

`retenção = 0.5 ^ (dias sem contato / meia-vida)`.

A meia-vida base é **30 dias — a mesma do agente 03, de propósito**: os dois
precisam concordar sobre o que "esquecido" significa. Ela é modulada por:

| Fator | Multiplicador |
| --- | --- |
| Domínio avançado / intermediário / básico / não conhece | 1.5 / 1.0 / 0.7 / 0.4 |
| Dificuldade muito fácil → crítica (agente 12) | 1.3 · 1.1 · 1.0 · 0.8 · 0.6 |
| 2+ erros registrados | 0.8 |

A base do cálculo sai na saída: `30d × 0.4 (domínio nao_conhece) × 0.8
(dificuldade dificil) × 0.8 (2 erros)`.

Risco de esquecimento pela retenção: `≥0.80` baixo · `≥0.60` médio · `≥0.40`
alto · resto **crítico**. Sem data de contato registrada, a retenção fica `null`
e o risco `indeterminado` — com a razão declarada em `observacoes`.

## Escada de repetição espaçada

Intervalos `1, 3, 7, 15, 30, 60` dias. **Acerto avança um degrau; erro volta ao
começo** — conteúdo que falhou precisa reconstruir o espaçamento, não continuar
de onde parou.

O intervalo da escada é **cortado** quando a retenção prevista cairia abaixo de
80% antes dele:

```
intervalo: degrau 5 da escada (30d), cortado para 9d porque a retenção
           cairia abaixo de 80% antes disso
```

Revisar cedo demais custa tempo; revisar tarde demais custa o conteúdo. O corte
é o que faz a regra "sempre priorizar retenção de longo prazo" valer contra a
escada.

## Método recomendado

| Situação | Método |
| --- | --- |
| retenção < 30% | `reestudo_da_aula` |
| dificuldade de memorização | `flashcards` |
| dificuldade procedimental | `exercicios` |
| dificuldade conceitual | `leitura_do_resumo` |
| dificuldade de interpretação | `questoes_comentadas` |
| manutenção | `flashcards` → resumo → questões |

**Só recomenda o que existe**: sem flashcards do agente 10 ou resumo do agente
11, esses métodos saem da lista e a ausência é registrada. Cada método tem custo
declarado em minutos (flashcards 5, resumo 8, questões 12, exercícios 15,
reestudo 25).

## Nenhuma revisão é removida

O teto diário vem do bloco de revisão do agente 06 (ou de
`maximo_revisoes_por_dia`), limitado a 8. Quando um dia estoura, as revisões
excedentes são **remanejadas** para o dia seguinte, com registro:

```jsonc
"remanejadas": [ { "topico": "Sintaxe", "de": "2026-01-05", "para": "2026-01-06", "motivo": "limite de 3 revisões por dia" } ]
```

O calendário agrupa por dia **e por disciplina** — trocar de assunto custa
atenção.

## Integração com o agente 13

Quando o Adaptive Teacher pede encurtar o intervalo (`solicitacoes` dirigidas ao
agente 14), o intervalo é reduzido pela metade e o ajuste fica registrado em
`intervalo.ajuste`. É o único caminho pelo qual outro agente influencia este
calendário — e ainda assim por pedido, não por escrita direta.

## Saída

```jsonc
{
  "resumo_geral": { "total_de_conteudos_monitorados": 3, "indice_medio_de_retencao": 0.5883, "risco_medio_de_esquecimento": 0.4117, "teto_de_revisoes_por_dia": 6 },
  "conteudos": [{
    "id": "rev-conjuntos", "disciplina": "Estatística", "topico": "Conjuntos",
    "ultima_revisao": "2025-11-16", "proxima_revisao": "2026-01-05",
    "intervalo_atual_dias": 1, "intervalo": { "degrau": 1, "da_escada": 1, "pelo_esquecimento": 3, "ajuste": "revisão já vencida, agendada para hoje" },
    "meia_vida": { "dias": 7.7, "base": "30d × 0.4 (domínio nao_conhece) × 0.8 (dificuldade dificil) × 0.8 (2 erros)" },
    "nivel_de_retencao": 0.0111, "risco_de_esquecimento": "critico",
    "prioridade": "alta", "score_de_prioridade": 5.85,
    "metodo_recomendado": "reestudo_da_aula", "minutos_estimados": 25,
    "revisoes_realizadas": 1, "acertos_consecutivos": 0
  }],
  "calendario": [ { "data": "2026-01-05", "total_de_revisoes": 2, "minutos_estimados": 30, "grupos": [ { "disciplina": "Estatística", "conteudos": ["Conjuntos", "Probabilidade"], "metodos": ["flashcards", "reestudo_da_aula"] } ] } ],
  "nao_elegiveis": [], "remanejadas": [],
  "indicadores": { "conteudos_dominados": ["Crase"], "conteudos_em_consolidacao": ["Probabilidade"], "conteudos_criticos": ["Conjuntos"], "tendencia_de_retencao": "indeterminada" },
  "consumido_por": ["15","16","17","18","19","21","22","23","24"]
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca revisar conteúdo não estudado | elegibilidade exige status estudado, medição ou histórico; o resto vai para `nao_elegiveis` |
| Nunca remover revisão obrigatória | excesso é remanejado para o dia seguinte, com registro em `remanejadas` |
| Sempre recalcular após novas evidências | a função é pura; `recalculado_em` marca a data |
| Sempre priorizar retenção de longo prazo | o intervalo é cortado pela previsão de esquecimento |
| Sempre considerar o histórico individual | escada, última revisão e meia-vida saem do histórico do estudante |
| Nunca alterar o cronograma principal | a saída não tem cronograma, sessões nem metas — verificado por teste |

## Consumidores

15 · 16 · 17 · 18 · 19 · 21 · 22 · 23 · 24.
