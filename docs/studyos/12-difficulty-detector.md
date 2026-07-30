# Agente 12 — Difficulty Detector

Implementação: `backend/app/studyos/agentes/dificuldade.py`.

## Identidade

Mede onde o estudante trava. Não ensina, não cria cronograma, não gera conteúdo,
não avalia aprovação, **não altera o Plano de Estudos nem o Grafo de
Dependências**.

Como os agentes 01–06, é inteiramente determinístico: aqui não há conteúdo a
redigir, só medição.

## Nunca assumir dificuldade sem evidência

Conteúdo sem dado medido sai com `indice: null` e `nivel: "indeterminado"` —
nunca "difícil por precaução". Dificuldade suposta viraria reforço desnecessário
lá na frente, e o reforço nem entra na lista sem índice.

## Índice de Dificuldade

Média ponderada dos componentes **que existem** (o peso é renormalizado sobre os
presentes):

| Componente | Peso | Entra quando |
| --- | --- | --- |
| `erro` | 0.45 | há questões medidas (agente 03) |
| `esquecimento` | 0.20 | retenção **abaixo de 0.9** — retenção intacta não é evidência de facilidade |
| `tempo` | 0.20 | há tempo registrado e estimativa na árvore |
| `recorrencia` | 0.15 | há erros registrados no tópico |

O corte de 0.9 na retenção importa: sem ele, um tópico estudado hoje entrava com
`esquecimento = 0` e diluía o sinal de erro — 1/10 de acerto saía como
"difícil" em vez de "crítico".

Faixas: `< 0.20` muito fácil · `< 0.40` fácil · `< 0.60` médio · `< 0.80` difícil
· resto **crítico**. A confiança acompanha o número de componentes (3+ → alta).

## Os quatro tipos de dificuldade

Não são adivinhados. Saem da **categoria da questão errada**, na taxonomia do
agente 09:

| Categoria errada | Tipo revelado |
| --- | --- |
| fixação | memorização |
| compreensão / síntese | conceitual |
| aplicação / desafio | procedimental |
| análise | interpretação |

Um `tipo` declarado no erro tem precedência sobre a categoria. Sem erros
registrados, os tipos ficam vazios e isso é dito em `observacoes`.

## Saída

```jsonc
{
  "recalculado_em": "2026-01-05",
  "resumo_geral": {
    "indice_geral_de_dificuldade": 0.4064, "nivel_geral": "medio",
    "topicos_medidos": 3, "topicos_totais": 4,
    "evolucao": { "disponivel": true, "tendencia": "melhorando", "melhoraram": ["Crase"], "pioraram": [] },
    "tendencia_de_aprendizagem": "melhorando",
    "velocidade_de_aprendizagem": { "razao_tempo_real_sobre_estimado": 1.67, "leitura": "acima do previsto" }
  },
  "disciplinas": [ { "disciplina": "Estatística", "indice_de_dificuldade": 0.8067, "conteudos_criticos": ["Conjuntos"], "conteudos_dominados": [], "conteudos_sem_evidencia": ["Probabilidade"] } ],
  "topicos": [ { "topico": "Conjuntos", "taxa_de_acertos": 0.1, "tempo_medio_de_resolucao_min": 400.0, "frequencia_de_erros": 2, "esquecido": true, "dificuldade": { "indice": 0.8067, "nivel": "critico", "confianca": "alta", "componentes": {...} }, "tipos_de_dificuldade": { "predominante": "procedimental" } } ],
  "padroes_de_erro": [ { "padrao": "erro_repetido_no_topico", "alvo": "Conjuntos", "ocorrencias": 2 } ],
  "sinais_de_sobrecarga": [ { "sinal": "tempo_muito_acima_do_estimado", "severidade": "media" } ],
  "principais_gargalos": [ { "topico": "Conjuntos", "conteudos_bloqueados": 1, "nivel": "critico" } ],
  "conteudos_esquecidos": ["Conjuntos"],
  "risco_de_abandono": { "nivel": "baixo", "fatores": ["3 dia(s) de estudo perdido(s)"] },
  "recomendacoes_de_reforco": [ { "topico": "Conjuntos", "score": 0.678, "acao_sugerida": "reforço imediato", "bloqueia_conteudos": 1, "tipo_predominante": "procedimental" } ],
  "consumido_por": ["13","14","15","17","18","19","21","22","23","24"]
}
```

## Evolução contínua

`relatorio_anterior` (a saída anterior deste mesmo agente) habilita a comparação:
delta por tópico, listas de `melhoraram`/`pioraram` e a tendência geral. Sem ele,
a tendência é `indeterminada` — não inventada.

## Priorização de reforço

`score = índice × peso da prioridade da disciplina × (1 + 0.2 × conteúdos
bloqueados)`. Conteúdo crítico que trava outros sobe na fila; conteúdo sem
índice não entra.

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca assumir dificuldade sem evidências | sem componente medido, `indice: null` e nível `indeterminado` |
| Sempre usar dados históricos | erros, tempos, simulados e relatório anterior entram quando existem |
| Sempre recalcular após novas atividades | a função é pura e recalcula tudo; `recalculado_em` marca a data |
| Nunca alterar Plano ou Grafo | a saída não tem cronograma, nós nem arestas — verificado por teste |
| Nunca ensinar, exercitar ou criar cronograma | nenhuma chave de conteúdo na saída |

## Consumidores

13 · 14 · 15 · 17 · 18 · 19 · 21 · 22 · 23 · 24.
