# Agente 03 — Knowledge Analyzer

Implementação: `backend/app/studyos/agentes/conhecimento.py`.

## Identidade

Mede com precisão o conhecimento atual **antes** de o plano existir. Não ensina,
não cria cronogramas, não gera resumos, aulas, questões ou flashcards.

## Objetivo

Construir o **Mapa de Conhecimento Estruturado** para cada disciplina do objetivo.

## Hierarquia de evidência

A regra "nunca assumir conhecimento sem evidências" é o eixo do módulo. Cada
fonte tem um papel fixo:

| Fonte | Classifica domínio? | Papel |
| --- | --- | --- |
| Simulado (`resultados_simulados`) | **sim**, peso 1.0 | evidência prática |
| Questionário diagnóstico (`questionario_diagnostico`) | **sim**, peso 1.0 | evidência prática |
| Exercícios (`resultados_exercicios`, `historico`) | **sim**, peso 0.8 | evidência prática |
| Percepção do estudante (`disciplinas_favoritas` / `disciplinas_dificuldade`) | **não** | pesa na dificuldade estimada, nunca no domínio |
| Histórico de estudo em texto | **não** | registra contato, não mede domínio |

Sem evidência prática, o tópico fica `indeterminado` e o agente **solicita** uma
avaliação diagnóstica — sem gerar as questões, que são responsabilidade do 09.

## Entradas

| Campo | Origem | Formato |
| --- | --- | --- |
| Perfil Cognitivo | agente 01 | — |
| Mapa Estratégico | agente 02 | fornece as disciplinas e as prioridades |
| `resultados_simulados`, `resultados_exercicios`, `questionario_diagnostico`, `historico` | usuário | lista de `{disciplina, topico, acertos, total, data}` ou `{disciplina, topico, percentual, amostra}` |
| `ultimo_contato` | usuário | `{tópico ou disciplina: data}` |
| `subtopicos` | usuário | `{tópico: [subtópicos]}` |
| `pre_requisitos` | usuário | `{tópico: [pré-requisitos]}` |

Evidência sem `topico` vale no nível da disciplina. Evidência de disciplina fora
do objetivo é registrada em `evidencias_consideradas.fora_do_escopo` e **não**
entra no cálculo.

## Processamento

1. **Disciplinas** — exatamente as do agente 02.
2. **Tópicos e subtópicos** — tópicos do edital; subtópicos só se informados. Nada é inferido.
3. **Avaliação diagnóstica** — solicitada (escopo + questões sugeridas), nunca gerada.
4. **Classificação por tópico** — `avancado` ≥ 85%, `intermediario` ≥ 60%, `basico` ≥ 35%, abaixo disso `nao_conhece`; com menos de 5 questões, `indeterminado`.
5. **Percentual por disciplina** — média dos tópicos **com evidência**, com `cobertura_diagnostica` explícita.
6. **Lacunas** — tópicos desconhecidos, parciais e sem evidência, listados separadamente.
7. **Pré-requisitos ausentes** — pré-requisito em nível baixo, sem medição, ou fora do escopo. Sem mapa informado, nada é inventado: a detecção fica com o agente 05.
8. **Tópicos esquecidos** — retenção `0.5 ^ (dias / 30)`; abaixo de 0.5, o tópico é marcado e **rebaixado um nível**, com a justificativa no campo `base`.
9. **Esforço por tópico** — `2.5h × fator` (1.0 não conhece · 0.7 básico · 0.4 intermediário · 0.15 avançado · 1.0 indeterminado).
10. **IGC** — média das disciplinas medidas, ponderada pela prioridade do agente 02. Confiança `alta` só com cobertura ≥ 80% e todas as disciplinas medidas.

## Constantes declaradas

| Constante | Valor |
| --- | --- |
| `FAIXA_AVANCADO` / `FAIXA_INTERMEDIARIO` / `FAIXA_BASICO` | 0.85 / 0.60 / 0.35 |
| `MINIMO_QUESTOES_POR_TOPICO` | 5 |
| `PESO_EVIDENCIA` | simulado 1.0 · diagnóstico 1.0 · exercício 0.8 |
| `RETENCAO_MEIA_VIDA_DIAS` / `LIMIAR_ESQUECIMENTO` | 30 / 0.5 |
| `HORAS_BASE_POR_TOPICO` | 2.5 |
| `COBERTURA_MINIMA_CONFIAVEL` / `COBERTURA_ALTA_CONFIANCA` | 0.5 / 0.8 |
| `QUESTOES_SUGERIDAS_POR_TOPICO` | 5 |

## Saída

```jsonc
{
  "indice_geral_de_conhecimento": { "valor": 0.15, "percentual": "15%", "confianca": "media", "cobertura_diagnostica_media": 0.58, "disciplinas_medidas": 2, "disciplinas_totais": 2 },
  "disciplinas": [{
    "disciplina": "Português",
    "percentual_dominio": 0.3,
    "base_do_percentual": "2 de 3 tópicos com evidência prática",
    "cobertura_diagnostica": 0.67, "confiavel": true,
    "topicos_dominados": [], "topicos_parcialmente_dominados": ["Crase"],
    "topicos_desconhecidos": ["Sintaxe"], "topicos_sem_evidencia": ["Interpretação"],
    "topicos_esquecidos": ["Crase", "Sintaxe"],
    "pre_requisitos_ausentes": [],
    "grau_dificuldade": { "grau": "dificil", "percepcao_de_dificuldade": false },
    "prioridade_estudo": { "prioridade": "alta", "score": 2.1 },
    "esforco_estimado_h": 4.5,
    "topicos": [ { "topico": "Crase", "classificacao": "intermediario", "confianca": "media", "base": "10 questões com 90% de acerto ponderado; rebaixado de 'avancado' por 122 dias sem contato (retenção estimada 6%)", "esquecido": true, "esforco_estimado_h": 1.0 } ]
  }],
  "avaliacao_diagnostica": { "necessaria": true, "escopo": [ { "disciplina": "Português", "topicos": ["Interpretação"], "questoes_sugeridas": 5 } ], "executor": "09 Exercise Generator (o agente 03 não gera questões)" },
  "resumo": { "pontos_fortes": [], "pontos_fracos": ["..."], "riscos_de_aprendizagem": [ { "risco": "pre_requisito_ausente", "severidade": "alta", "evidencia": "..." } ], "recomendacoes_para_planejamento": ["..."] },
  "evidencias_consideradas": { "total": 3, "por_tipo": { "simulado": 2, "exercicio": 1 }, "fora_do_escopo": [] },
  "esforco_total_estimado_h": 9.75,
  "consumido_por": ["04","05","06","12","14","15","17","18","21","22","23"]
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca assumir conhecimento sem evidências | classificação só sai de `resultados_*`; sem eles, tudo fica `indeterminado` |
| Sem dados, solicitar avaliação diagnóstica | `avaliacao_diagnostica.necessaria` com escopo por disciplina e tópico |
| Percepção não é prova de domínio | favoritas/dificuldades entram só em `grau_dificuldade`, com `percepcao_de_dificuldade` explícito |
| Considerar resultados práticos quando existirem | `PESO_EVIDENCIA` privilegia simulado e diagnóstico sobre exercício |
| Nunca gerar questões, flashcards, aulas ou cronograma | a saída tem contagem de questões sugeridas, nunca as questões; sem datas nem conteúdo |

## Consumidores

04 · 05 · 06 · 12 · 14 · 15 · 17 · 18 · 21 · 22 · 23.
