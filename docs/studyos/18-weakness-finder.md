# Agente 18 — Weakness Finder

Implementação: `backend/app/studyos/agentes/fraquezas.py`.

## Identidade

Diz exatamente **quais conteúdos impedem o estudante de evoluir**, e em que
ordem recuperá-los. Não ensina, não gera exercício, não altera plano nem
currículo.

A pergunta que o separa do 12 e do 17: eles medem o que está difícil e o que
deu errado; aqui a medida é **fragilidade com consequência**. Um tópico mal
dominado que não trava nada e vale 2% do edital é um problema menor que um
tópico igualmente mal dominado que trava outros cinco.

## Índice de Fraqueza

Média ponderada dos sintomas de fragilidade, **amplificada** pelo que o
conteúdo trava no grafo:

| Sintoma | Peso | Origem |
| --- | --- | --- |
| domínio | 0,45 | classificação do agente 03 |
| erro | 0,35 | taxa de acerto medida, ou contagem de erros do agente 17 |
| esquecimento | 0,20 | retenção estimada / marca de esquecido (03 e 12) |

Classificação → valor: `nao_conhece` 1,00 · `basico` 0,70 · `intermediario`
0,35 · `avancado` 0,10.

**Componente ausente não entra como zero** — o peso é redistribuído entre os
presentes, e `indice.confianca` diz quantos sustentaram o número (3+ alta, 2
média, 1 baixa).

### Por que bloqueio amplifica em vez de compor

Travar outros conteúdos não é mais um sintoma de fragilidade: é o que
transforma fragilidade em obstáculo. Como componente da média ele **diluiria**
— um tópico com domínio `nao_conhece` (valor 1,0) e bloqueio parcial (0,2)
sairia *menos* frágil que o mesmo tópico sem bloqueio nenhum, o contrário do
que a identidade do agente afirma.

Então ele entra como fator: `índice × (1 + 0,30 × min(1, travados / 5))`,
saturando em 5 conteúdos travados e limitado a 1,0. O fator aparece na saída
em `indice.amplificador_de_bloqueio`, com a contagem que o gerou.

### Faixas

| Índice | Nível | Ação recomendada |
| --- | --- | --- |
| < 0,25 | `estavel` | manter |
| < 0,50 | `atencao` | revisar |
| < 0,75 | `critico` | reforcar |
| ≥ 0,75 | `prioridade_maxima` | reestudar |

`avancar` é a única ação que não sai do nível: exige domínio `avancado` medido
**e** nenhum sinal de esquecimento. Domínio alto sem retenção não é conteúdo
para deixar para trás.

## Sem evidência não há fraqueza

Conteúdo sem nenhuma medição não recebe índice: vai para
`conteudos_sem_evidencia` com o motivo. Índice zero seria afirmar "está
estável" sobre alguém que ninguém mediu — e o resumo declara quantos ficaram
de fora.

## Maiores fraquezas ≠ mais urgentes

São duas listas porque respondem a duas perguntas. `maiores_fraquezas` ordena
pelo índice. `mais_urgentes` pondera o índice por fatores que **não** entram
nele:

| Fator de urgência | Efeito |
| --- | --- |
| conteúdos que dependem deste | × (1 + 0,15 por dependente, até 5) |
| posição no Plano de Estudos | × (1 + (10 − posição) / 20) |
| reta final (≤ 30 dias) | × 1,25 |

A posição no plano é o que mais separa as listas: dois conteúdos com o mesmo
índice têm urgências diferentes se um deles vem primeiro no cronograma. Só
sessões de **estudo de conteúdo** contam para a posição — exercícios e revisão
do dia apontam para a disciplina inteira, não para o tópico.

## Impacto da recuperação

`impacto_na_aprendizagem.ganho_estimado` combina o índice com o peso da
disciplina no edital e com o que o conteúdo destrava, sempre com os fatores
listados. Sem peso do edital, o impacto sai só do grafo — e a base diz isso.

## O mapa se atualiza

Passando o mapa anterior em `mapa_de_fraquezas_anterior`:

- `resumo_geral.tendencia_de_evolucao` compara o índice geral (variação de 0,05
  para deixar de ser estável);
- cada fraqueza ganha `variacao` com índice e nível anteriores;
- `frequencia_de_esquecimento` **acumula**: ela é contada ao longo dos mapas,
  não deduzida de um retrato só.

`padrao_de_baixo_desempenho` exige repetição — duas medições abaixo de 60% de
acerto. Uma medição ruim é uma medição.

## Saída

```jsonc
{
  "atualizado_em": "2026-01-05",
  "resumo_geral": {
    "indice_geral_de_fragilidade": 0.4096, "conteudos_avaliados": 4,
    "conteudos_criticos": 1, "conteudos_sem_evidencia": 0,
    "distribuicao_por_nivel": { "estavel": 1, "atencao": 2, "prioridade_maxima": 1 },
    "tendencia_de_evolucao": { "disponivel": true, "tendencia": "melhora",
                               "indice_anterior": 0.52, "variacao": -0.11 },
    "principais_areas_de_risco": [
      { "disciplina": "Estatística", "indice_medio": 0.5942,
        "conteudos_criticos": 1, "conteudos_medidos": 2 }
    ]
  },
  "fraquezas": [{
    "id": "w001", "disciplina": "Estatística", "modulo": "Estatística — módulo único",
    "topico": "Conjuntos", "indice_de_fraqueza": 0.8615,
    "indice": {
      "componentes": { "dominio": { "valor": 1.0, "base": "domínio medido pelo agente 03: nao_conhece" },
                       "erro":    { "valor": 0.7, "base": "10 questões, 30% de acerto" } },
      "amplificador_de_bloqueio": null, "confianca": "media"
    },
    "nivel_de_prioridade": "prioridade_maxima",
    "frequencia_de_erros": 3, "erros_recorrentes": 3,
    "tipos_de_erro": { "conceitual": 3 },
    "competencias": { "Aplicar o conceito em situação típica da prova": 3 },
    "frequencia_de_esquecimento": 0,
    "base_do_esquecimento": "nenhuma observação de esquecimento",
    "conteudos_dependentes_afetados": [],
    "padrao_de_baixo_desempenho": null, "medicoes_no_historico": 1,
    "impacto_na_aprendizagem": { "ganho_estimado": 0.2872, "conteudos_destravados": 0,
                                 "esforco_estimado_h": 2.5,
                                 "fatores": ["disciplina com 33% do edital"] },
    "urgencia": { "score": 1.2061, "fatores": ["2º conteúdo do plano de estudos"] },
    "recomendacao": { "acao": "reestudar", "base": "nível prioridade_maxima no Índice de Fraqueza",
                      "ja_agendado_para_revisao": false }
  }],
  "conteudos_sem_evidencia": [],
  "ranking": {
    "maiores_fraquezas": [{ "posicao": 1, "topico": "Conjuntos", "indice_de_fraqueza": 0.8615 }],
    "mais_urgentes":     [{ "posicao": 1, "topico": "Conjuntos", "score_de_urgencia": 1.2061 }],
    "competencias_mais_comprometidas": [
      { "competencia": "Aplicar o conceito em situação típica da prova",
        "erros": 3, "topicos": ["Conjuntos"] }
    ],
    "base_das_listas": "maiores fraquezas ordenam pelo índice; mais urgentes ponderam o índice pelo grafo, pela posição no plano e pelo prazo da prova"
  },
  "recomendacoes": {
    "reestudar": [{ "topico": "Conjuntos", "indice_de_fraqueza": 0.8615 }],
    "revisar":   [{ "topico": "Sintaxe",   "indice_de_fraqueza": 0.3731 }],
    "avancar":   [{ "topico": "Crase",     "base": "domínio avançado medido e nenhum sinal de esquecimento" }]
  },
  "consumido_por": ["19","21","22","23","24"]
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca classificar fraqueza sem evidências | sem componente medido não há índice; vai para `conteudos_sem_evidencia` |
| Sempre utilizar dados históricos | `padrao_de_baixo_desempenho` e a comparação com o mapa anterior |
| Sempre considerar dependências do grafo | amplificador do índice, fator de urgência e `conteudos_dependentes_afetados` |
| Nunca modificar o Plano de Estudos | a saída não tem cronograma nem sessões — verificado por teste |
| Nunca ensinar nem criar exercícios | nenhum campo carrega enunciado ou conteúdo didático |
| Nunca alterar o currículo | a árvore do 04 entra só como localização (disciplina/módulo) |

## Consumidores

19 · 21 · 22 · 23 · 24.
