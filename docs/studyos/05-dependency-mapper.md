# Agente 05 — Dependency Mapper

Implementação: `backend/app/studyos/agentes/dependencias.py`.

## Identidade

Transforma a Árvore Curricular em um **Grafo de Aprendizagem**. Não ensina, não
cria cronogramas, não gera exercícios, não responde dúvidas.

## Objetivo

Construir um DAG onde cada conteúdo só possa ser estudado depois de seus
pré-requisitos.

## De onde vêm as arestas — e de onde não vêm

| Relação | Vira aresta? | Por quê |
| --- | --- | --- |
| Pré-requisito declarado (`pre_requisitos` do usuário ou do agente 04) | **sim** | é a única dependência que existe de fato |
| Ordem dos tópicos no edital | **não** | ordem é ordem, não dependência; virar aresta destruiria todo o paralelismo |
| Contenção (módulo contém tópico) | **não** | é estrutura; vira `contido_em`, e o bloqueio do pai desce como `bloqueado_por_ancestral` |
| Nome parecido / proximidade temática | **não** | seria dependência inventada |

Pré-requisito declarado que não corresponde a nenhum nó **não vira aresta**:
entra em `dependencias_nao_resolvidas` com o motivo. Auto-dependência é
descartada do mesmo jeito.

A ordem do edital não desaparece — ela sobrevive como critério de desempate na
`sequencia_logica`: o grafo manda no *quando pode*, o edital manda no *qual
antes*.

## Processamento

1. **Achatamento** — todos os cinco níveis viram nós com ID hierárquico (`d1.m2.t3.s1.u2`).
2. **Resolução de arestas** — por nome, preferindo mesmo tipo e mesma disciplina.
3. **Eliminação de ciclos** — cada ciclo é quebrado removendo a aresta que mais avança *contra* a ordem do currículo; a remoção sai registrada em `ciclos_eliminados` com o ciclo completo.
4. **Ondas** — níveis do DAG: tudo na mesma onda pode ser estudado em paralelo.
5. **Profundidade** — índice da onda do nó.
6. **Dependentes transitivos** — quantos conteúdos ficam presos atrás de cada nó.
7. **Status** — `concluido` (dominado no agente 03), `bloqueado` (pré-requisito ou ancestral pendente), `disponivel`.
8. **Caminhos** — cadeias maximais de pré-requisitos, ordenadas por tempo acumulado; a mais longa é o caminho crítico.
9. **Sequência lógica** — ordem topológica, desempate pela ordem curricular, excluindo o que já está dominado.

## Paralelismo

`pode_ser_estudado_em_paralelo` só é verdadeiro quando existe outro nó **do
mesmo tipo**, na **mesma onda**, **sem relação de contenção** e ainda não
concluído. Dizer que um tópico roda "em paralelo com o módulo que o contém"
seria contar o mesmo conteúdo duas vezes.

## Saída

```jsonc
{
  "nos": [{
    "id": "d1.m1.t2", "nome": "Probabilidade", "tipo": "topico",
    "disciplina": "Estatística", "contido_em": "d1.m1", "ordem_curricular": 4,
    "dificuldade": "medio", "importancia": "essencial", "obrigatorio": true,
    "tempo_estimado_h": 2.5,
    "pre_requisitos": ["d1.m1.t1"], "dependentes": ["d1.m1.t3"],
    "dependentes_transitivos": 1, "profundidade": 1,
    "pode_ser_estudado_em_paralelo": false, "paralelo_com": [],
    "status": "bloqueado", "bloqueado_por": ["d1.m1.t1"], "bloqueado_por_ancestral": [],
    "ignoravel_no_planejamento": false
  }],
  "totais": { "nos": 9, "arestas": 2, "concluidos": 1, "disponiveis": 6, "bloqueados": 2 },
  "ondas_de_estudo": [ { "onda": 1, "paralelo": true, "nos": ["d1", "d1.m1", "d1.m1.t1", "..."] } ],
  "caminho_principal": { "tempo_h": 7.5, "nomes": ["Conjuntos", "Probabilidade", "Distribuições"] },
  "caminhos_alternativos": [],
  "nos_criticos": [ { "nome": "Conjuntos", "dependentes_transitivos": 2 } ],
  "nos_independentes": ["d2.m1.t2"],
  "conteudos_opcionais": [], "conteudos_ignoraveis": ["d2.m1.t1"],
  "sequencia_logica": [ { "ordem": 1, "nome": "Conjuntos", "onda": 1, "tempo_estimado_h": 2.5 } ],
  "ciclos_eliminados": [ { "nomes": "Conjuntos → Distribuições", "ciclo": ["Conjuntos", "Distribuições", "Probabilidade"], "motivo": "dependência circular; mantida a ordem do currículo" } ],
  "dependencias_nao_resolvidas": [ { "nome": "Sintaxe", "pre_requisito": "Fonologia", "motivo": "nome não encontrado na Árvore Curricular" } ],
  "profundidade_maxima": 2, "acilico": true,
  "consumido_por": ["06","07","09","10","11","14","15","16","23","24"]
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca criar dependências inexistentes | aresta só a partir de pré-requisito declarado e resolvido; o resto vira `dependencias_nao_resolvidas` |
| Nunca permitir ciclos | detecção por DFS e remoção da aresta contrária ao currículo, com registro; `acilico: true` é verificado nas ondas |
| Nunca alterar a estrutura curricular | a árvore é lida, nunca reescrita; os IDs preservam a hierarquia e a ordem |
| Sempre respeitar a ordem lógica | ordem curricular é o desempate da sequência e o critério de quebra de ciclo |
| Sempre identificar estudo paralelo | ondas do DAG + `paralelo_com` por nó |
| Nunca gerar cronograma, aula ou exercício | a saída não tem datas nem conteúdo — teste verifica a ausência dessas chaves |

## Consumidores

06 · 07 · 09 · 10 · 11 · 14 · 15 · 16 · 23 · 24.
