# Agente 19 — Coach

Implementação: `backend/app/studyos/agentes/coach.py`.

## Identidade

Mantém o estudante consistente. Não ensina, não cria cronograma, não gera
exercício, não altera o plano. Abre a fase de acompanhamento.

É o **primeiro agente cuja saída é texto endereçado ao estudante** — e é por
isso que as duas regras mais duras da spec precisaram virar mecanismo, não
instrução.

## Nenhuma mensagem sem dado

> Nunca utilizar mensagens motivacionais genéricas.

Só é verificável se toda mensagem carregar um dado concreto do registro
medido: um número, uma data, um nome de tópico. Uma frase que continuaria
verdadeira com qualquer outro estudante no lugar é genérica por definição.

Toda mensagem passa por `_validar_mensagem` antes de sair. Reprovada, ela é
**recusada** — não reescrita para caber — e vai para `mensagens_recusadas` com
o motivo. Cada mensagem emitida declara em `dados_citados` exatamente o que a
ancora.

```jsonc
{ "tipo": "alerta", "chave": "consistencia_baixa",
  "texto": "Você cumpriu 4 de 10 dias planejados nas últimas 2 semanas. Vale rever se a meta diária cabe na sua rotina antes de tentar recuperar tudo de uma vez.",
  "dados_citados": ["4", "10"], "emitida": true }
```

## Nenhuma mensagem que manipula

> Nunca manipular emocionalmente o estudante.

Culpa, medo e comparação social estão em `TERMOS_MANIPULATIVOS` — "você vai
reprovar", "todo mundo consegue", "está desperdiçando" — e o texto composto
passa pelo mesmo filtro. **Alerta é permitido; ameaça não.** A recusa por
manipulação tem precedência sobre a recusa por genérico: é a mais grave.

## Sem dado, sem estimativa

Consistência é `dias estudados / dias planejados`. Frequência sozinha não é
consistência — estudar 3 dias é ótimo contra uma meta de 3 e ruim contra uma
meta de 10 — então sem denominador o índice sai `null` com a base declarada.

E há um piso: abaixo de **3 dias planejados** na janela, o engajamento sai
`indeterminado`. Chamar de "alto" quem cumpriu o único dia planejado é a mesma
invenção que declarar tendência a partir de duas medições. Nesse caso as
mensagens sobre ritmo também não saem — "mantenha o ritmo" apoiado num dia é
palpite com cara de dado.

| Consistência | Engajamento | Tom |
| --- | --- | --- |
| < 0,40 | `critico` | direto e sem rodeios |
| < 0,65 | `baixo` | objetivo e propositivo |
| < 0,85 | `regular` | objetivo |
| ≥ 0,85 | `alto` | objetivo e de reforço |

O tom muda a forma, nunca o conteúdo: o dado citado é o mesmo em qualquer tom.

## Repetição

Duas defesas, porque repetir tem duas formas:

- **Mesma mensagem outra vez.** `mensagens_enviadas` guarda o que já saiu; uma
  chave repetida dentro de 7 dias é suprimida com o motivo.
- **Mesmo fato com outras palavras.** Uma sequência de 5 dias não vira
  reconhecimento *e* conquista — `COBERTURA_POR_CONQUISTA` liga a conquista à
  mensagem que já conta aquele fato.

## Risco de abandono: um número, não dois

O agente 12 já mede risco de abandono. O coach **não recalcula**: reaproveita o
nível e, quando a frequência agrava o quadro (consistência < 40% ou 3+ dias sem
registro), eleva um degrau e diz por quê. Dois números discordando sobre a
mesma coisa seria pior que um número só.

## Foco e estratégia

O foco do momento sai do ranking de urgência do agente 18; sem mapa de
fraquezas, cai para o erro recorrente do agente 17; sem nenhum dos dois, é
declarado ausente.

A estratégia é escolha de ação, com o agente responsável por executá-la:

| Situação | Estratégia | Responsável |
| --- | --- | --- |
| engajamento baixo/crítico ou risco alto | reduzir a meta diária até voltar a cumpri-la | 20 |
| há ponto de reforço pendente | concentrar o bloco de reforço nele | 23 |
| resto | manter o ritmo | — |

## Melhor momento de contato

Sai do próximo dia reservado no Plano de Estudos; sem cronograma, do bloco
diário declarado no perfil; sem nenhum dos dois, `null` com a base — o agente
não inventa um horário para falar com alguém.

## Saída

```jsonc
{
  "atualizado_em": "2026-03-14",
  "resumo_geral": {
    "nivel_de_engajamento": "regular", "indice_de_consistencia": 0.7,
    "base_da_consistencia": "7 de 10 dias planejados na janela de 14 dias",
    "risco_de_abandono": { "nivel": "medio", "fatores": ["4 dias sem registro de estudo"],
                           "base": "nível do agente 12 (baixo) ajustado pela frequência observada" },
    "evolucao_recente": { "disponivel": true, "tendencia": "queda",
                          "consistencia_anterior": 0.9, "variacao": -0.2 },
    "janela_de_analise_dias": 14
  },
  "orientacoes": {
    "principal_foco": { "topico": "Conjuntos", "disciplina": "Estatística",
                        "motivo": "2º conteúdo do plano de estudos", "origem": "agente 18" },
    "recomendacao_prioritaria": { "acao": "reestudar", "base": "nível prioridade_maxima no Índice de Fraqueza" },
    "proxima_meta": { "meta": "12.94h em 4 dias na semana 2026-S12", "origem": "agente 06" },
    "estrategia_sugerida": { "estrategia": "concentrar o bloco de reforço em Conjuntos",
                             "base": "2º conteúdo do plano de estudos", "agente_responsavel": "23" },
    "tom_da_comunicacao": { "tom": "objetivo", "base": "nível de engajamento regular",
                            "nota": "o tom muda a forma; o dado citado é o mesmo em qualquer tom" }
  },
  "mensagens": [ /* cada uma com dados_citados e melhor_momento */ ],
  "mensagens_recusadas": [
    { "chave": "foco", "emitida": false, "motivo_da_recusa": "mensagem já enviada nos últimos 7 dias" }
  ],
  "melhor_momento_de_contato": { "momento": "no início do dia de estudo de 2026-03-16",
                                 "base": "próximo dia reservado no Plano de Estudos (agente 06)" },
  "indicadores": {
    "sequencia_de_dias_estudando": { "dias": 3, "base": "dias consecutivos até 2026-03-14" },
    "dias_desde_o_ultimo_estudo": 0,
    "metas_cumpridas": [], "metas_pendentes": [],
    "conquistas": [{ "conquista": "3 dias seguidos de estudo", "tipo": "constancia",
                     "base": "dias consecutivos até 2026-03-14" }],
    "evolucao_da_disciplina": { "disponivel": true, "tendencia": "queda" },
    "revisoes_agendadas": 2
  },
  "consumido_por": ["20","21","22","23","24"]
}
```

Conquista sai do registro, não de cortesia: sequência de dias, meta cumprida,
erro que não reapareceu (agente 17) ou fraqueza que caiu de índice (agente 18)
— cada uma com a base que a sustenta.

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca usar mensagem motivacional genérica | `_validar_mensagem` exige dado citado e barra `TERMOS_GENERICOS` |
| Sempre basear recomendações em dados reais | foco, estratégia e metas vêm dos agentes 06, 17 e 18, com origem declarada |
| Nunca manipular emocionalmente | `TERMOS_MANIPULATIVOS` barra culpa, medo e comparação social |
| Comunicação objetiva e construtiva | alerta propõe ação; o tom vem do engajamento, não do humor |
| Evitar mensagens repetitivas | janela antirrepetição de 7 dias + dedupe do mesmo fato |
| Nunca alterar o Plano de Estudos | a saída não tem cronograma nem sessões — verificado por teste |
| Nunca ensinar nem criar exercícios | nenhum campo carrega conteúdo didático |

## Consumidores

20 · 21 · 22 · 23 · 24.
