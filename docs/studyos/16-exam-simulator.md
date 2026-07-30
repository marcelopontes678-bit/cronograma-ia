# Agente 16 — Exam Simulator

Implementação: `backend/app/studyos/agentes/simulado.py`.

## Identidade

Monta simulados que **medem o nível atual**. Não ensina, não explica durante a
prova, não cria cronograma e não altera o Plano de Estudos. Abre a fase de
avaliação: o que ele registra é o insumo dos agentes 17, 18 e 21.

## A exceção do diagnóstico

O agente 09 registra uma pendência quando o agente 03 pede avaliação
diagnóstica: exercício não pode cobrir conteúdo não estudado. A spec do 16
resolve essa tensão — "nunca gerar questões sobre conteúdos ainda não
estudados, **salvo em simulados diagnósticos**".

É a única porta pela qual o StudyOS avalia o que ainda não ensinou, e ela é
explícita nos dois sentidos:

- `formato != diagnostico` → tópico não estudado vai para `conteudos_excluidos`
  com o motivo; se **nada** sobrar, o simulado é bloqueado
  (`motivo: "sem_conteudo_elegivel"`) e a ação sugerida é o próprio diagnóstico.
- `formato == diagnostico` → o não estudado entra e a saída declara quantos
  tópicos entraram por essa exceção.

O portão é aplicado duas vezes: em `montar_briefing()` e de novo em `montar()`,
que levanta `ConteudoNaoEstudado` se receber questões para um briefing
bloqueado.

## Formatos

| Formato | Questões padrão | fácil / médio / difícil |
| --- | --- | --- |
| `diagnostico` | 20 | 40 / 40 / 20 |
| `parcial` | 30 | 30 / 50 / 20 |
| `disciplina` | 20 | 30 / 50 / 20 |
| `assunto` | 10 | 30 / 50 / 20 |
| `completo` | 60 | 25 / 50 / 25 |
| `revisao_final` | 40 | 20 / 50 / 30 |

Nenhum formato é monocromático — "sempre variar os níveis de dificuldade" é
regra da spec, então a mistura é uma constante declarada, não uma escolha do
redator.

### Como o formato é escolhido

Na ordem, com a base registrada em `formato.base`:

1. `tipo_de_simulado` informado pelo usuário;
2. agente 03 pediu diagnóstica **e** não há nenhuma medição prática → `diagnostico`;
3. faltam 30 dias ou menos para a prova → `revisao_final`;
4. `disciplina_alvo` informada → `disciplina`; `assunto_alvo` → `assunto`;
5. padrão → `parcial`.

`completo` e `revisao_final` usam o total de questões declarado no edital
quando ele existe, em vez do padrão do formato.

## Distribuição das questões

O peso da disciplina vem do edital (agente 02). Dentro dele, os tópicos entram
por ordem de prioridade, em rodízio — o mais cobrado volta primeiro na roda e
por isso aparece mais vezes.

| Fator da prioridade | Efeito no score |
| --- | --- |
| peso da disciplina no edital | × (1 + peso) |
| índice de dificuldade (agente 12) | × (1 + índice) |
| erros registrados (agente 12) | × (1 + 0,15 por erro) |
| reta final (≤ 30 dias) | × 1,2 |

Peso e tempo previsto derivam da dificuldade do slot:

| Dificuldade | Peso | Minutos |
| --- | --- | --- |
| fácil | 1 | 1,5 |
| médio | 2 | 2,5 |
| difícil | 3 | 4,0 |

## Duas decisões estruturais

### O caderno do estudante não carrega resposta

"Nunca fornecer dicas antes da conclusão" só é verificável se a resposta viver
em outro lugar. `caderno_de_questoes` tem enunciado, alternativas e peso;
`gabarito` tem resposta, explicação e competência. São blocos separados, com
paridade de `id` verificada por teste.

### Questão já existente é reaproveitada, não regerada

O banco do agente 09 já tem enunciado, resposta e explicação — regerar
arriscaria contradizê-lo. O redator só é chamado para o que falta.

O reaproveitamento exige **tópico e grau de dificuldade iguais** aos da lista de
origem: o agente 09 calibra a lista inteira num nível só, e uma questão fácil
ocupando slot difícil falsearia peso e tempo previsto.

Sem banco e sem redator, o simulado sai com `status: "pendente_de_redacao"` e
`questoes_pendentes` preenchido — nunca com questão inventada.

## Correção

`penalidade_por_erro` aceita número (`0.25`) ou confirmação (`true`, `"sim"`).
A confirmação sem valor cai em `PENALIDADE_PADRAO = 1.0` — erro anula acerto, a
convenção mais comum — e a saída declara a origem:

```jsonc
"criterios_de_correcao": {
  "penalidade_por_erro": 1.0,
  "origem_da_penalidade": "usuário confirmou que há desconto, sem informar o valor"
}
```

Ler "sim" como zero transformaria "tem penalidade" em "não tem" no silêncio.

## Embaralhamento reproduzível

Ordem das questões e das alternativas saem de `random.Random(semente)`, com
`SEMENTE_PADRAO = 20260101`. Mesma semente, mesmo caderno — o simulado pode ser
reaplicado e comparado.

## Saída

```jsonc
{
  "gerado": true,
  "status": "gerado",
  "resumo_geral": {
    "tipo_de_simulado": "disciplina", "base_do_formato": "informado pelo usuário",
    "objetivo": "Medir o domínio da disciplina selecionada",
    "numero_de_questoes": 20, "tempo_previsto_min": 50.0,
    "distribuicao_por_disciplina": { "Português": 20 },
    "distribuicao_por_dificuldade": { "facil": 6, "medio": 10, "dificil": 4 },
    "banca": "FGV", "semente_do_embaralhamento": 20260101
  },
  "caderno_de_questoes": [{
    "id": "q013", "numero": 1, "disciplina": "Português", "topico": "Sintaxe",
    "grau_de_dificuldade": "medio", "enunciado": "...",
    "alternativas": ["D","B","A","C"], "peso": 2
  }],
  "questoes": [{
    "id": "q013", "disciplina": "Português", "topico": "Sintaxe",
    "grau_de_dificuldade": "medio", "competencia_avaliada": "Aplicar o conceito em situação típica da prova",
    "peso": 2, "minutos_previstos": 2.5, "origem": "banco do agente 09",
    "conteudo_estudado": true, "prioridade": { "score": 1.7, "fatores": ["peso 67% no edital"] }
  }],
  "gabarito": [{
    "id": "q013", "resposta_correta": "A", "explicacao": "...",
    "competencia_avaliada": "Aplicar o conceito em situação típica da prova", "peso": 2
  }],
  "criterios_de_correcao": {
    "pontuacao_maxima": 38, "peso_por_dificuldade": { "facil": 1, "medio": 2, "dificil": 3 },
    "penalidade_por_erro": 0.0, "origem_da_penalidade": "nenhum desconto informado",
    "regra": "Sem desconto por erro; questão em branco vale zero", "nota_de_corte": null
  },
  "estatisticas_previstas": {
    "acerto_previsto": 0.575, "pontuacao_prevista": 21.85, "pontuacao_maxima": 38,
    "base": "domínio medido pelo agente 03 por tópico; projeção para os agentes 21 e 22 comparar com o resultado real",
    "confianca": "media"
  },
  "registro_para_analise": {
    "destinatarios": ["17","18","21"],
    "por_questao": [{ "id": "q013", "topico": "Sintaxe", "disciplina": "Português",
                      "dificuldade": "medio", "competencia": "...", "dominio_medido": "basico", "peso": 2 }]
  },
  "questoes_pendentes": [], "questoes_invalidas": [], "conteudos_excluidos": [],
  "consumido_por": ["17","18","19","21","22","23","24"]
}
```

`estatisticas_previstas` é **projeção, não gabarito**: sai do domínio medido
pelo agente 03, existe para os agentes 21 e 22 compararem previsto com real, e
declara `confianca: "baixa"` quando todo o domínio é indeterminado.

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca gerar questões sobre conteúdo não estudado | portão de elegibilidade em `montar_briefing()`, revalidado em `montar()` |
| Salvo em simulados diagnósticos | `FORMATO_DIAGNOSTICO` é a única exceção, e ela é declarada em `observacoes` |
| Sempre variar os níveis de dificuldade | `MISTURA_POR_FORMATO`, sem formato monocromático |
| Sempre respeitar o peso do edital | distribuição por `_pesos_por_disciplina` (agente 02) |
| Nunca fornecer dicas antes da conclusão | resposta e explicação vivem fora do caderno |
| Sempre fornecer gabarito e critério de correção | `gabarito` + `criterios_de_correcao`; questão sem resposta é recusada |
| Nunca inventar questão | sem banco e sem redator, sai `pendente_de_redacao` |
| Simulado reproduzível | `random.Random(semente)` com semente declarada na saída |

## Consumidores

17 · 18 · 19 · 21 · 22 · 23 · 24.
