# Agente 11 — Summary Generator

Implementação: `backend/app/studyos/agentes/resumos.py`.

## Identidade

Sintetiza conteúdo **já estudado** em resumos de revisão. Não ensina conteúdo
novo, não cria cronogramas, não gera exercícios ou simulados, não avalia
desempenho.

## Duas regras da spec viraram verificação

**"Resumo de 1 minuto" precisa caber em 1 minuto.** O orçamento sai da
velocidade de leitura declarada (200 palavras/min, tolerância 15%): 229 palavras
para o de 1 min, 1150 para o de 5 min. Estourou, a seção é recusada com o tempo
real de leitura no motivo. O resumo completo não tem teto — ele é completo.

**"Nunca remover conceitos essenciais" é conferido.** Cada conceito-chave
precisa aparecer no resumo completo; o que sumir vai para
`conceitos_ausentes_no_resumo` e impede o `gerado: true`.

Há ainda a checagem de **progressão**: 1 min ≤ 5 min ≤ completo. Um "resumo de 1
minuto" maior que o completo é incoerente por construção.

## O que é derivado, não redigido

Copiar em vez de regerar é o que mantém a consistência com o original:

| Item | Origem |
| --- | --- |
| `mapa_mental_textual` | estrutura da Árvore Curricular (agente 04), com o conteúdo atual marcado por `◀` |
| `checklist_de_revisao` | um "Consigo explicar X sem consultar?" por conceito, marcando os de revisão frequente (agente 10) |
| `erros_comuns` | copiados da aula, do contraexemplo (agente 08) e do gabarito (agente 09), **sem reescrita** |
| `conceitos_chave` | pontos-chave da aula + conceitos dos flashcards e exercícios |
| `proximos_conteudos_relacionados` | dependentes e próximo da sequência, do Grafo (agente 05) |

Exemplo real de mapa mental gerado:

```
Português
└── Português — módulo único
    └── Crase
        ├── Regra geral ◀
        │   ├── Antes de femininos
        ├── Exceções
        • fusão de preposição com artigo
        • casos proibidos
```

Esse material existe **mesmo sem redator conectado** — é estrutura, não prosa.

## Seções redigidas pelo modelo

| Chave | Orçamento | Condicional |
| --- | --- | --- |
| `resumo_1min` | 229 palavras | não |
| `resumo_5min` | 1150 palavras | não |
| `resumo_completo` | sem teto | não |
| `definicoes_importantes` | — | não |
| `formulas` | — | **sim** — só quando o conteúdo tem fórmulas |
| `processos_passo_a_passo` | — | não |
| `armadilhas_frequentes` | — | não |

A aplicabilidade de `formulas` é detectada por marcas no conteúdo da aula
(`fórmula`, `equação`, `=`, `teorema`, `cálculo`, `%`) — heurística declarada,
não adivinhação silenciosa.

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca remover conceitos essenciais | conferência de presença no resumo completo |
| Nunca adicionar o que não está na aula | a aula inteira vai no briefing com a regra "sintetizar não é acrescentar"; erros comuns são copiados, não regerados |
| Preservar a sequência lógica | a instrução exige a mesma ordem da aula; o mapa mental vem da árvore |
| Resumos em três níveis | orçamento de palavras por nível, com verificação de progressão |
| Não ensinar, não exercitar, não avaliar | `proibicoes` no briefing e descarte de seções fora da estrutura |
| Nunca resumir conteúdo não estudado | portão compartilhado (`portoes.conteudo_estudado`) |

## Consumidores

13 · 14 · 15 · 16 · 17 · 18 · 21 · 24.
