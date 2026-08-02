# Agente 22 — Forecast Agent

Implementação: `backend/app/studyos/agentes/previsao.py`.

## Identidade

Projeta a evolução do estudante a partir do que já foi medido. Não ensina, não
cria cronograma, não gera exercício, não altera o plano.

## Nenhuma previsão como certeza

> Nunca apresentar previsões como certezas.

Isso não é um aviso no rodapé — é a forma de todo número:

```jsonc
"acerto_projetado": {
  "estimativa": 0.875,
  "intervalo": [0.725, 1.0],
  "confianca": "media",
  "base": "acerto de 72% extrapolado por 6.1 meses com amortecimento de 50%, limitado ao teto de +15%",
  "natureza": "estimativa"
}
```

O intervalo **alarga quando os dados encolhem**: ±8 pontos com confiança alta,
±15 com média, ±25 com baixa. É assim que a incerteza aparece no número em vez
de aparecer só no texto.

E a confiança nasce da quantidade de insumo, **não do resultado projetado** —
uma previsão ruim com muitos dados é mais confiável que uma boa com poucos.

Além disso, todo texto passa por um filtro de `TERMOS_DE_CERTEZA` — "vai
passar", "garantido", "com certeza". Previsão que promete deixa de ser
previsão.

## Um modelo só

Cenários e alavancas não são histórias diferentes: são a mesma função
`_projetar` chamada com o estado alterado por um delta declarado. Assim o
cenário otimista **não pode** contradizer o esperado — os dois saem da mesma
conta, e a diferença entre eles é exatamente o delta que está na saída.

| Cenário | Delta aplicado |
| --- | --- |
| otimista | aderência +15pp, acerto +5pp |
| esperado | **nenhum** |
| pessimista | aderência −15pp, acerto −5pp |

O cenário esperado é o estado como está — nenhuma correção "de bom senso"
embutida. Verificado por teste: a probabilidade do cenário esperado é
idêntica à PAO do resumo.

### O modelo

- **Cobertura**: avança no ritmo observado, descontado pela aderência. Quem
  cumpre 60% dos dias avança 60% do ritmo.
- **Acerto**: extrapola a variação mensal medida, com amortecimento de 50% **e
  teto de ±15 pontos**.

O teto foi a correção que o smoke test forçou. Uma janela em que o estudante
saltou 25 pontos, extrapolada por seis meses, chegava a 100% de acerto — e um
modelo que projeta gabaritar a prova não está prevendo, está torcendo. Pior:
a saturação zerava o impacto de todas as alavancas, escondendo justamente o
que o agente 23 precisa ver.

## Probabilidade de Atingimento do Objetivo

| Componente | Peso |
| --- | --- |
| cobertura projetada | 0,35 |
| acerto projetado vs. nota de corte | 0,35 |
| aderência | 0,20 |
| retenção | 0,10 |

Componente sem dado não entra e o peso é redistribuído. Abaixo de **dois**
componentes a PAO sai `None` com a lista do que falta — um número bonito
apoiado em nada é pior que a ausência dele.

Faixas: < 0,35 `baixa` · < 0,60 `moderada` · < 0,80 `boa` · ≥ 0,80 `alta`.

## Alavancas

Cada mudança simulável é o mesmo modelo com um delta declarado:

| Alavanca | Delta |
| --- | --- |
| aumento da carga horária | ritmo × 1,25 |
| melhora na consistência | aderência +20pp |
| reforço de conteúdos críticos | acerto +8pp |
| aumento da retenção | retenção +15pp |

O impacto de cada uma é a diferença entre a PAO resultante e a atual. Alavanca
cujo dado-base não foi medido devolve `impacto_na_probabilidade: null` com
`"o dado que esta alavanca move não foi medido"` — não uma estimativa
inventada.

A `prioridade_maxima` é a alavanca de maior ganho simulado, com o número
junto. E a recomendação declara `executor: "23"`: este agente estima impacto,
quem reorganiza o plano é o Optimization Agent.

## Saída

```jsonc
{
  "emitido_em": "2026-03-14",
  "aviso": "Todos os números deste relatório são estimativas calculadas a partir dos dados disponíveis até a data de emissão. Não são garantia de resultado e mudam quando novos dados chegam.",
  "resumo_geral": {
    "probabilidade_de_atingir_o_objetivo": {
      "estimativa": 0.8097, "intervalo": [0.6597, 0.9597], "confianca": "media",
      "nivel": "alta", "natureza": "estimativa",
      "componentes": { "cobertura": {...}, "acerto": {...}, "aderencia": {...} }
    },
    "tendencia_geral": "melhora",
    "evolucao_prevista": {
      "cobertura_projetada": { "estimativa": 1.0, "intervalo": [0.85, 1.0], ... },
      "acerto_projetado": { "estimativa": 0.875, ... },
      "data_alvo": "2026-09-01", "dias_restantes": 183
    },
    "nivel_de_confianca": "media",
    "base_da_confianca": "quantidade de componentes medidos e existência de tendência mensal; confiança não depende do resultado projetado"
  },
  "cenarios": {
    "otimista":   { "delta_aplicado": {...}, "probabilidade": {...},
                    "condicoes_necessarias": ["aderência subir 15% em relação à atual", "taxa de acerto subir 5%"],
                    "principais_riscos": [...] },
    "esperado":   { "condicoes_necessarias": ["manter o comportamento atual"], ... },
    "pessimista": { ... }
  },
  "fatores_positivos": [{ "fator": "1 conteúdo(s) já dominado(s)", "base": "Crase", "origem": "agente 04" }],
  "fatores_de_risco": [{ "risco": "Conjuntos com índice de fraqueza 0.8687", "tipo": "conteudo_critico",
                         "gravidade": "alta", "base": "classificação do agente 18", "origem": "agente 21" }],
  "simulacoes": [
    { "acao": "melhora_na_consistencia", "delta_aplicado": { "aderencia": 0.2 },
      "probabilidade_resultante": 0.8542, "impacto_na_probabilidade": 0.0445,
      "base": "mesma projeção com o estado alterado pelo delta declarado" },
    { "acao": "aumento_da_retencao", "impacto_na_probabilidade": null,
      "base": "o dado que esta alavanca move não foi medido" }
  ],
  "recomendacoes": {
    "prioridade_maxima": { "acao": "melhora_na_consistencia", "impacto_estimado": 0.0445,
                           "base": "maior ganho entre as alavancas simuladas" },
    "acoes_recomendadas": [...], "riscos_a_mitigar": [...],
    "executor": "23",
    "base": "este agente recomenda e estima impacto; quem reorganiza o plano é o agente 23"
  },
  "estado_observado": { /* o ponto de partida, com a origem de cada campo */ },
  "consumido_por": ["23","24"]
}
```

`estado_observado` fica na saída de propósito: é o insumo exato que gerou a
projeção, então qualquer número do relatório pode ser reconferido.

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca apresentar previsões como certezas | toda projeção tem intervalo, confiança e `natureza: "estimativa"`; textos passam por `TERMOS_DE_CERTEZA` |
| Sempre informar que são estimativas | `aviso` no topo e como primeira observação |
| Nunca utilizar dados inexistentes | componente sem dado fica fora da PAO; alavanca sem base declara que não simula |
| Sempre recalcular com dados novos | a projeção deriva do estado; mudou o estado, mudou a previsão — verificado por teste |
| Nunca alterar o Plano de Estudos | a saída não tem cronograma; a execução é declarada como do agente 23 |
| Nunca ensinar nem criar exercícios | nenhum campo carrega conteúdo didático |

## Consumidores

23 · 24.
