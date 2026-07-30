# Agente 10 — Flashcard Generator

Implementação: `backend/app/studyos/agentes/flashcards.py`.

## Identidade

Converte conteúdo **já estudado** em flashcards de recuperação ativa. Não ensina
conteúdo novo, não cria cronogramas, não gera simulados, não avalia desempenho.

## Três regras da spec viraram recusa, não conselho

| Regra | Verificação |
| --- | --- |
| Uma ideia por cartão | resposta acima de 25 palavras, ou com marca de enumeração (`;`, "e também", "além disso", "por outro lado") → recusada |
| Recuperação ativa | frente que não é pergunta, lacuna, afirmação a julgar nem tarefa de ordenar/parear → recusada |
| Nada sobre conteúdo não estudado | mesmo portão do agente 09 (`portoes.conteudo_estudado`) |

Um cloze sem o marcador `___` também é recusado — cloze sem lacuna não é cloze.
Pergunta repetida é descartada apontando o cartão original.

## O que é calculado

| Campo | Origem |
| --- | --- |
| Conceitos | `pontos_chave` da aula + `conceito_alvo` dos exercícios do agente 09 |
| Tipo | rodízio sobre os sete formatos da spec |
| Dificuldade | domínio medido do tópico (agente 03): avançado/intermediário → fácil, básico → médio, não conhece → difícil |
| Prioridade | importância do tópico na Árvore Curricular (agente 04) |
| Revisão frequente | difícil **ou** prioridade alta **ou** tópico esquecido |
| Tempo médio de resposta | tabela por tipo (cloze 8s … sequência lógica 25s) |
| Disciplina / módulo / tópico / subtópico | subindo a cadeia de contenção do grafo |
| Tags | localização + tipo + conceito |
| ID | `fc-<id-do-nó>-<nn>` |

Ao modelo cabem **pergunta e resposta**. A marcação `revisao_frequente` é o que
o agente 14 Memory Scheduler consome para definir os intervalos.

## Saída

```jsonc
{
  "flashcards": [{
    "id": "fc-d1-m1-t1-01",
    "disciplina": "Português", "modulo": "Português — módulo único",
    "topico": "Crase", "subtopico": null,
    "tipo": "conceito_definicao",
    "pergunta": "O que é fusão de preposição com artigo?",
    "resposta": "resposta curta e única",
    "explicacao_complementar": null,
    "conceito": "fusão de preposição com artigo",
    "nivel_dificuldade": "dificil", "prioridade": "alta",
    "revisao_frequente": true, "tempo_medio_resposta_s": 12,
    "tags": ["Português", "…", "Crase", "conceito_definicao", "…"]
  }],
  "resumo": {
    "total": 3,
    "distribuicao_por_dificuldade": { "dificil": 3 },
    "distribuicao_por_disciplina": { "Português": 3 },
    "conceitos_cobertos": ["…"], "conceitos_descobertos": ["casos proibidos"],
    "marcados_para_revisao_frequente": 3, "tempo_total_estimado_s": 26
  },
  "cartoes_pendentes": [], "cartoes_invalidos": [], "cartoes_duplicados": [],
  "consumido_por": ["11","13","14","15","17","18","21","24"]
}
```

`conceitos_descobertos` mostra o que ficou sem cartão — inclusive quando um
cartão foi recusado, como acontece no exemplo acima.

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca criar flashcards de conteúdo não estudado | portão compartilhado; `montar` levanta `ConteudoNaoEstudado` |
| Nunca mais de um conceito por cartão | limite de palavras + detecção de enumeração na resposta |
| Sempre favorecer recuperação ativa | frente precisa exigir recall; validação por tipo de cartão |
| Linguagem clara e objetiva | resposta limitada a 25 palavras |
| Nunca substituir a aula pelos flashcards | consta nas `proibicoes` e na regra da referência |
| Não criar cronogramas, simulados nem avaliar | `proibicoes` no briefing; a saída só tem cartões e resumo |

## Consumidores

11 · 13 · 14 · 15 · 17 · 18 · 21 · 24.
