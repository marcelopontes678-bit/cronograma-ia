# Agente 09 — Exercise Generator

Implementação: `backend/app/studyos/agentes/exercicios.py`.

## Identidade

Gera exercícios do conteúdo **já estudado**. Não ensina conteúdo novo, não cria
cronogramas, não gera simulados completos, não avalia desempenho histórico.

## Onde fica a fronteira entre código e modelo

Mais para o lado do código do que nos agentes 07 e 08. São calculáveis:

| Decisão | Como é calculada |
| --- | --- |
| Quantidade de questões | tempo disponível ÷ custo em minutos da categoria |
| Distribuição por categoria | tabela por nível do estudante |
| Ordem de dificuldade | categorias são ordinais; os slots já saem ordenados |
| Formato de cada questão | tabela categoria → formatos, em rodízio |
| Conceito alvo | rodízio sobre os `pontos_chave` da aula, garantindo cobertura |
| Pontuação e tempo | tabela por categoria |

Ao modelo cabe **enunciado, resposta e explicação**. Nada entra no conjunto sem
os três.

## Portão: só se pratica o que foi estudado

| Situação | Resultado |
| --- | --- |
| Aula do agente 07 `gerada` | liberado |
| Conteúdo `concluido` ou `em_andamento` no grafo (estudo anterior medido) | liberado |
| Conteúdo `bloqueado` por pré-requisito | `bloqueio: conteudo_bloqueado` |
| Conteúdo sem aula e não estudado | `bloqueio: conteudo_nao_estudado` |
| Nada identificado | `bloqueio: conteudo_ausente` |

### A tensão com o agente 03

O agente 03 pede avaliação diagnóstica justamente sobre tópicos **sem
evidência** — que, por definição, ainda não foram estudados. A regra do agente
09 é mais forte que esse pedido, então o bloqueio registra a tensão em vez de
resolvê-la por conta própria:

```jsonc
"pedido_de_diagnostico_pendente": {
  "origem": "03 Knowledge Analyzer",
  "observacao": "Há pedido de avaliação diagnóstica sobre este conteúdo, mas a regra do agente 09 proíbe exercitar conteúdo não estudado. Resolver estudando o conteúdo ou registrando estudo anterior."
}
```

## Categorias, custo e distribuição

| Categoria | Minutos/questão | Pontos | Formatos |
| --- | --- | --- | --- |
| fixação | 1.5 | 1 | completar lacunas, V/F, associação |
| compreensão | 2.0 | 1 | múltipla escolha, resposta curta, V/F |
| aplicação | 3.0 | 2 | resolução de problemas, múltipla escolha |
| análise | 4.0 | 3 | estudo de caso, discursiva |
| síntese | 6.0 | 3 | discursiva, estudo de caso |
| desafio | 8.0 | 5 | resolução de problemas, estudo de caso |

Distribuição do tempo por nível do estudante:

| Nível | fixação | compreensão | aplicação | análise | síntese | desafio |
| --- | --- | --- | --- | --- | --- | --- |
| iniciante | 50% | 35% | 15% | — | — | — |
| básico | 30% | 35% | 25% | 10% | — | — |
| intermediário | 10% | 20% | 35% | 25% | 10% | — |
| avançado | — | 10% | 30% | 30% | 15% | 15% |

Quem está começando não recebe desafio; quem domina não perde tempo com fixação
pura.

O tempo vem, em ordem de precedência: `tempo_disponivel_min` do usuário → bloco
de exercícios do Plano de Estudos (agente 06) → 30 min padrão. Teto de 120 min:
exercício demais vira fadiga.

## Validações na montagem

| Verificação | Resultado |
| --- | --- |
| Questão sem enunciado, resposta ou explicação | vai para `questoes_invalidas` com o motivo, **fora** do conjunto |
| Enunciado repetido | vai para `questoes_duplicadas` com o número da questão igual |
| Conceito dos `pontos_chave` sem questão | aparece em `cobertura_dos_conceitos.descobertos` |
| Slot sem redação | vai para `questoes_pendentes` |

O conjunto só sai com `gerado: true` quando não há pendências nem inválidas.

## Saída

```jsonc
{
  "titulo_da_atividade": "Exercícios — Crase",
  "objetivo": "Dominar Crase no contexto de Português",
  "nivel_de_dificuldade": "medio",
  "tempo_estimado_min": 28.0, "tempo_disponivel_min": 31.8,
  "distribuicao_por_categoria": [ { "categoria": "fixacao", "quantidade": 2, "minutos_estimados": 3.0 } ],
  "exercicios": [{
    "numero": 1, "categoria": "fixacao", "ordem_dificuldade": 1,
    "formato": "completar_lacunas", "enunciado": "…", "alternativas": null,
    "conceito_alvo": "regra geral", "competencia_avaliada": "Recuperar o conceito da memória",
    "tempo_estimado_min": 1.5, "pontos": 1
  }],
  "gabarito": [{
    "numero": 1, "resposta": "…", "explicacao": "…",
    "competencia_avaliada": "Recuperar o conceito da memória",
    "erro_comum_associado": "…", "pontos": 1
  }],
  "pontuacao_sugerida": 17,
  "cobertura_dos_conceitos": { "conceitos": ["…"], "cobertos": ["…"], "descobertos": [], "completa": true },
  "questoes_pendentes": [], "questoes_invalidas": [], "questoes_duplicadas": [],
  "consumido_por": ["10","11","13","16","17","18","21","24"]
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca exercitar conteúdo não estudado | portão exige aula gerada ou conteúdo estudado; `montar` levanta `ConteudoNaoEstudado` |
| Sempre fornecer gabarito e explicações | questão sem os dois é recusada, não entra no conjunto |
| Cobrir todos os conceitos importantes | conceito alvo por rodízio sobre os `pontos_chave`, com relatório de cobertura |
| Evitar perguntas repetidas | enunciados normalizados e comparados; duplicata é descartada |
| Ordem crescente de dificuldade | categorias ordinais; slots emitidos em ordem |
| Balancear quantidade e dificuldade pelo tempo | quantidade derivada do tempo disponível e do custo da categoria |
| Coerência com aula e exemplos | ambos entram no briefing como referência, com precedência da aula |
| Não ensinar, não simular, não avaliar | `proibicoes` no briefing; a saída não tem conteúdo didático nem histórico |

## Consumidores

10 · 11 · 13 · 16 · 17 · 18 · 21 · 24.
