# Agente 13 — Adaptive Teacher

Implementação: `backend/app/studyos/agentes/adaptativo.py`.

## Identidade

Adapta *como* o conteúdo é ensinado. Não cria cronograma, não define currículo,
não altera o Grafo de Aprendizagem e **não reescreve a teoria oficial da aula**.

## Decisão é código; só a reexplicação precisa de modelo

Estratégia didática, nível de linguagem, ritmo, profundidade, quantidade de
exemplos e analogias, critérios de domínio e a recomendação final saem de
tabelas declaradas sobre os dados dos agentes 01, 03 e 12. Tudo isso existe
**mesmo sem redator conectado** — o que falta é só o texto da explicação.

## Toda adaptação carrega justificativa

Um ajuste sem justificativa não é adaptação, é palpite. Por isso `justificativa`
é campo obrigatório de cada ajuste, com o dado que o motivou:

```
linguagem               = iniciante   ← domínio medido do conteúdo: iniciante
ritmo                   = lento       ← ritmo reduzido por sinal de confusão:
                                        indice_de_dificuldade_alto (índice 71%);
                                        erros_persistentes (2 erros no tópico); …
quantidade_de_analogias = 3           ← 2 do nível + 1 por sinal de confusão de
                                        severidade alta; estilo visual favorece analogia
```

## Estratégia didática

Escolhida pelo tipo de dificuldade que o agente 12 isolou:

| Tipo de dificuldade | Estratégias, em ordem |
| --- | --- |
| conceitual | analogias → comparações → explicação direta |
| procedimental | passo a passo → exemplos progressivos → problemas |
| interpretação | estudos de caso → problemas → comparações |
| memorização | exemplos progressivos → comparações → passo a passo |

Sem tipo isolado, a estratégia vem do nível de domínio. O estilo de aprendizagem
(agente 01) entra como alternativa adicional. **Abordagem já tentada é evitada**:
`estrategias_ja_usadas` remove candidatas da lista — reexplicar do mesmo jeito
que já não funcionou não é reexplicar.

## Sinais de confusão

Só com evidência medida:

| Sinal | Origem | Severidade |
| --- | --- | --- |
| `indice_de_dificuldade_alto` | índice ≥ 0.6 (agente 12) | alta |
| `erros_persistentes` | 2+ erros no tópico | alta |
| `taxa_de_acerto_baixa` | < 50% medido (agente 03) | alta |
| `tempo_acima_do_previsto` | razão > 1.5× | média |
| `conteudo_esquecido` | retenção abaixo do limiar | média |

Sinal de severidade alta aumenta exemplos e analogias em +1 e desacelera o ritmo
um degrau.

## Critérios de domínio e recomendação

Checklist verificável, cada item com `atendido` e `evidencia`:

1. conteúdo retido (não esquecido)
2. domínio medido em nível intermediário ou avançado
3. taxa de acerto ≥ 70%
4. índice de dificuldade < 40%
5. sem erros persistentes
6. sem sinal de confusão de severidade alta

O critério de **retenção** é o que impede um erro sutil: sem ele, conteúdo
esquecido com histórico de 90% de acerto passava por "dominado" e o agente
mandava avançar sobre uma base já perdida.

| Situação | Recomendação |
| --- | --- |
| todos os critérios atendidos | `avancar` |
| conteúdo esquecido | `revisar` |
| índice ≥ 0.6 | `reforcar` |
| 2+ erros no mesmo tópico | `repetir_exercicios` |
| sem medição | `reforcar` (o avanço não pode ser confirmado) |

## Pede, não executa

O agente emite **solicitações** aos responsáveis, nunca age no lugar deles:

```jsonc
"solicitacoes": [
  { "agente": "15 Revision Planner", "pedido": "antecipar revisão de Crase", "motivo": "…" },
  { "agente": "14 Memory Scheduler", "pedido": "encurtar o intervalo de repetição", "motivo": "…" },
  { "agente": "09 Exercise Generator", "pedido": "nova bateria na mesma faixa", "motivo": "…" },
  { "agente": "23 Optimization Agent", "pedido": "realocar tempo de estudo", "motivo": "…" }
]
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca ensinar com pré-requisito pendente | portão no `montar_briefing`; `montar` levanta `PreRequisitoPendente` |
| Nunca alterar o conteúdo conceitual | a teoria entra como referência imutável; blocos fora dos quatro slots são descartados (um `desenvolvimento` devolvido pelo redator não entra) |
| Nunca modificar currículo, grafo ou cronograma | a saída não tem essas chaves — verificado por teste |
| Sempre justificar adaptações com dados | `justificativa` obrigatória em cada ajuste |
| Coerência com o Lesson Generator | aula, exemplos, exercícios, flashcards e resumos entram no briefing como material já produzido |

## Consumidores

14 · 15 · 16 · 17 · 18 · 19 · 21 · 22 · 23 · 24.
