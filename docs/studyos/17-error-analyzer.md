# Agente 17 — Error Analyzer

Implementação: `backend/app/studyos/agentes/erros.py`.

## Identidade

Transforma erro em inteligência. Não ensina, não gera exercício, não altera o
Plano de Estudos nem o Grafo de Dependências. Consome o
`registro_para_analise` que o agente 16 produz e entrega o Relatório
Inteligente de Erros para os agentes 18, 19, 21, 22 e 23.

## A regra que define o agente

> Nunca assumir a causa de um erro sem evidências.

Isso só é verificável se a causa for **derivada**, não escolhida. A
classificação é uma lista ordenada de regras; cada uma declara a evidência que
a disparou. Erro que não casa com regra nenhuma sai como `indeterminado` — com
a lista do que faltaria para determiná-lo — em vez de receber um tipo
plausível.

### Escala de evidência

| # | Sinal | Evidência | Tipo |
| --- | --- | --- | --- |
| 1 | tipo informado pelo estudante | declaração direta | o que ele disse |
| 2 | questão em branco | resposta ausente | `gestao_do_tempo` |
| 3 | tempo > 2× o previsto | cronometragem da questão | `gestao_do_tempo` |
| 4 | pré-requisito com domínio insuficiente | grafo do 05 + medição do 03 | `conceitual` |
| 5 | domínio insuficiente no próprio tópico | classificação do agente 03 | `conceitual` |
| 6 | tópico marcado como esquecido | agentes 03/12 | `memorizacao` |
| 7 | acerto histórico ≥ 80% no tópico | taxa medida | `atencao` |
| 8 | categoria da questão | taxonomia do agente 09 | inferido |

A regra de maior precedência define a causa. **As outras não são
descartadas**: todas entram em `evidencias`, e as que apontam para outro tipo
entram em `contradicoes`. Se o estudante diz "foi desatenção" num tópico em que
o agente 03 mediu `nao_conhece`, a declaração vence — é evidência direta — mas
a divergência fica registrada para o agente 18 decidir com o quadro inteiro.

## Erro é observado, não deduzido

A fonte forte é a resposta do estudante conferida contra o gabarito do agente
16 (`origem: "resposta conferida contra o gabarito do agente 16"`). A fonte
fraca é o erro que ele mesmo relata.

O que o agente **não** faz é inferir erros de uma taxa de acerto: 30% em
Conjuntos não vira "sete erros em Conjuntos". Sem respostas e sem relato, o
relatório sai vazio, com `lacunas` apontando o que falta.

## Gravidade

Score explicado, cada multiplicador com seu fator:

| Fator | Efeito |
| --- | --- |
| recorrência (≥ 2 ocorrências do par tópico+tipo) | × (1 + 0,3 por ocorrência extra) |
| peso da disciplina no edital | × (1 + peso) |
| tópico é pré-requisito de outros | × (1 + 0,1 por conteúdo bloqueado) |
| erro já considerado resolvido voltou | × 1,4 |

Faixas: < 1,5 baixa · < 2,5 média · < 4,0 alta · ≥ 4,0 crítica. A
`prioridade_de_correcao` é a posição nessa ordem.

O impacto no desempenho é o peso da questão sobre a pontuação máxima do
simulado. Sem pontuação registrada ele fica `null` com a base declarada — não
vira estimativa.

## Duas honestidades no tempo

### Ausência de erro não é erro resolvido

Um par tópico+tipo que sumiu em relação ao relatório anterior só entra em
`erros_resolvidos` se **houve prática nova no tópico** depois daquele
relatório. Sem prática nova ele vai para `sem_nova_evidencia`, que é o que de
fato se sabe.

### A janela da tendência é temporal

A taxa de erro inicial e a recente são separadas **por data**, nunca por
posição na lista. Registros do mesmo dia descrevem o mesmo momento do
estudante; parti-los em "antes" e "depois" compararia tópicos diferentes
fingindo comparar épocas diferentes. Com uma data só, ou com menos de 10
respostas de cada lado, a tendência sai `indeterminada` com o motivo.

## Vocabulário compartilhado com o agente 12

O agente 12 lê `relatorio_de_erros["erros"]` para compor o índice de
dificuldade. As taxonomias são diferentes de propósito, e a tradução mora em
`dificuldade.TIPO_DO_AGENTE_17`:

| Agente 17 | Agente 12 |
| --- | --- |
| conceitual | conceitual |
| interpretacao | interpretacao |
| memorizacao | memorizacao |
| calculo | procedimental |
| atencao, estrategia, gestao_do_tempo | — |

Os três últimos não têm equivalente porque **não são dificuldade com o
conteúdo** — são falhas de execução da prova. Traduzi-los inflaria o índice de
dificuldade do tópico: quem acerta 95% em Crase e escorrega numa questão não
tem dificuldade com crase. O agente 12 os conta à parte, em
`erros_nao_atribuiveis_ao_conteudo`.

## Saída

```jsonc
{
  "emitido_em": "2026-01-05",
  "resumo_geral": {
    "total_de_erros": 4, "erros_medidos": 4, "erros_relatados": 0,
    "respostas_analisadas": 30, "taxa_de_erro": 0.1333,
    "base_da_taxa": "erros sobre respostas conferidas contra gabarito",
    "evolucao_da_taxa_de_erro": {
      "disponivel": true, "tendencia": "melhora",
      "taxa_inicial": 0.75, "taxa_recente": 0.1, "variacao": -0.65,
      "corte": "2025-11-01", "base": "20 respostas até 2025-11-01 contra 20 depois"
    },
    "tipos_predominantes": ["conceitual", "atencao"],
    "contagem_por_tipo": { "conceitual": 3, "atencao": 1 }
  },
  "erros": [{
    "id": "e001", "disciplina": "Estatística", "topico": "Conjuntos", "questao": "q018",
    "tipo": "conceitual", "causa_provavel": "domínio insuficiente do próprio conteúdo",
    "evidencias": [{ "evidencia": "agente 03 classificou o tópico como nao_conhece",
                     "aponta_para": "conceitual", "forca": "medida" }],
    "contradicoes": [], "falta_para_determinar": [],
    "frequencia": 3, "recorrente": true,
    "gravidade": { "nivel": "media", "score": 2.133,
                   "fatores": ["3 ocorrências do mesmo tipo no tópico",
                               "disciplina com 33% do edital"] },
    "impacto_no_desempenho": { "pontos_perdidos": 2.0, "fracao_da_pontuacao": 0.0351,
                               "base": "peso da questão sobre 57 pontos do simulado" },
    "conteudo_relacionado": { "topico": "Conjuntos", "disciplina": "Estatística",
                              "pre_requisitos": [], "dominio_medido": "nao_conhece" },
    "tipo_de_dificuldade_no_agente_12": "conceitual",
    "origem": "resposta conferida contra o gabarito do agente 16",
    "prioridade_de_correcao": 1
  }],
  "indicadores": {
    "erros_recorrentes": [{ "topico": "Conjuntos", "tipo": "conceitual", "frequencia": 3,
                            "gravidade": "media", "questoes": ["q018","q022","q014"] }],
    "erros_resolvidos": [], "sem_nova_evidencia": [], "novos_erros": [],
    "base_da_comparacao": "nenhum relatório anterior informado",
    "tendencia_de_melhoria": "melhora",
    "recomendacoes_de_intervencao": [{
      "tipo_de_erro": "conceitual", "ocorrencias": 3, "conteudo_prioritario": "Conjuntos",
      "intervencao": "reestudar o conceito antes de resolver mais questões",
      "agente_responsavel": "07", "ja_agendado_para_revisao": false,
      "gravidade_maxima": "media"
    }]
  },
  "consumido_por": ["12","18","19","21","22","23","24"]
}
```

Um padrão recorrente é **uma linha**, não uma por ocorrência: as três questões
de Conjuntos erradas pelo mesmo motivo são um problema só, com os ids listados.

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca assumir a causa sem evidências | regras ordenadas com evidência declarada; sem sinal, `indeterminado` |
| Sempre usar dados históricos quando disponíveis | evolução por janela temporal e comparação com o relatório anterior |
| Sempre registrar padrões de repetição | frequência por par tópico+tipo e `erros_recorrentes` deduplicado |
| Nunca modificar o Plano de Estudos | a saída não tem cronograma nem blocos — verificado por teste |
| Nunca ensinar conteúdo | nenhum campo carrega enunciado, resposta ou explicação |
| Nunca gerar novos exercícios | o agente só lê o simulado do 16 |
| Nunca alterar o Grafo | o grafo do 05 entra só como leitura de pré-requisitos |

## Consumidores

12 · 18 · 19 · 21 · 22 · 23 · 24.
