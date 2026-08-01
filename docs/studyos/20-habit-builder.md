# Agente 20 — Habit Builder

Implementação: `backend/app/studyos/agentes/habitos.py`.
Leitura compartilhada do registro: `backend/app/studyos/agentes/frequencia.py`.

## Identidade

Transforma estudo em rotina sustentável. Não ensina, não cria cronograma, não
gera exercício, não altera o plano.

A diferença entre este agente e o 19: o Coach olha para o **desempenho** e diz
o que fazer com ele; o Habit Builder olha para o **comportamento** e ajusta a
meta até ela ser cumprível.

## Um registro, duas leituras, nenhum número em duplicata

Os dois agentes leem os mesmos dias de estudo. Duas implementações do mesmo
cálculo acabariam divergindo num arredondamento e o sistema falaria dois
números sobre o mesmo estudante — então a leitura mora em `frequencia.py`:
`sessoes_registradas`, `dias_estudados`, `dias_planejados`, `sequencia_ate`,
`melhor_sequencia`, `consistencia`.

As **janelas** são diferentes de propósito: o Coach observa 14 dias, o Habit
Builder 28, porque hábito se mede em semanas. O que não depende da janela — a
sequência atual, por exemplo — é idêntico nos dois, e isso é verificado por
teste.

## A meta é cumprível por construção

> Nunca criar metas incompatíveis com a disponibilidade do estudante.
> Sempre trabalhar com evolução gradual.

A meta diária sai da **mediana** das sessões reais, não da média: um domingo
de cinco horas não define a rotina de ninguém, e é justamente ele que puxaria
a média para uma meta que o estudante nunca mais cumpre.

Sobre essa âncora, o ajuste é uma tabela — não uma opinião:

| Adesão observada | Ajuste |
| --- | --- |
| < 50% | reduz 25% |
| 50% – 80% | mantém até estabilizar |
| ≥ 80% | sobe no máximo 20% |

E dois limites duros: a meta **nunca** passa da disponibilidade declarada
(`horas_por_dia`), e nunca cai abaixo de 10 minutos. Sem sessão com duração
registrada, a meta sai `null` — sem base de comparação ela seria chute.

É aqui que a estratégia "reduzir a meta diária" do agente 19 vira número.

## Nunca punir

> Nunca utilizar punições. Sempre reforçar comportamentos positivos.

Duas garantias:

- **A tabela de reforços não tem variedade punitiva.** `REFORCOS_POSITIVOS`
  contém quatro entradas — marco, constância, retomada, meta cumprida — e a
  retomada é explicitamente "tratar a volta como recomeço, sem cobrança pelo
  intervalo".
- **Todo texto passa por um filtro** antes de sair: `TERMOS_PUNITIVOS` (perda,
  castigo, vergonha, "zerou tudo") somados aos `TERMOS_MANIPULATIVOS` do agente
  19. Recusado, o texto não sai e a recusa fica em `textos_recusados`.

Hábito negativo é descrito como **obstáculo observado**, com contagem e base —
nunca como falha de caráter.

## Padrão precisa de amostra

Nada é afirmado com menos de 3 observações:

- **melhor horário**: a faixa com maior taxa de conclusão entre as que têm
  amostra; sem isso, `melhor_faixa: null` e o motivo declarado;
- **dia de maior falta**: só dias da semana com 3+ ocorrências planejadas;
- **obstáculo**: motivo de interrupção repetido. Ocorrência única é
  `episodico`, não obstáculo.

Para consolidar um hábito: adesão ≥ 80%, ao menos 3 observações, e **14 dias
de observação real** — o intervalo entre a primeira e a última sessão, não o
tamanho da janela. Hábito observado em 8 dias não virou hábito de 28.

## Saída

```jsonc
{
  "atualizado_em": "2026-03-22",
  "resumo_geral": {
    "indice_de_consistencia": 0.7,
    "base_da_consistencia": "7 de 10 dias planejados na janela de 28 dias",
    "sequencia_atual": { "dias": 0, "base": "último estudo em 2026-03-10, há 4 dias" },
    "melhor_sequencia_historica": { "dias": 5, "inicio": "2026-03-02", "fim": "2026-03-06" },
    "frequencia": { "semanal": { "dias": 2 }, "mensal": { "dias": 7 } },
    "janela_de_observacao_dias": 28,
    "engajamento_do_agente_19": "regular"
  },
  "habitos_positivos": {
    "consolidados": [{ "habito": "estudar no período da manha", "adesao": 1.0,
                       "observacoes": 6, "dias_observados": 15,
                       "base": "6 sessões nessa faixa, 100% concluídas" }],
    "em_formacao": [{ "habito": "estudar nos dias planejados", "adesao": 0.7,
                      "falta_para_consolidar": "adesão de 80% por 14 dias" }],
    "criterio": "consolidado: adesão ≥ 80% com ao menos 3 observações em 14 dias"
  },
  "habitos_negativos": {
    "principais_obstaculos": [{ "obstaculo": "sono", "ocorrencias": 2,
                                "base": "motivo de interrupção registrado mais de uma vez" }],
    "comportamentos_recorrentes": [{ "comportamento": "sexta planejada sem estudo",
                                     "ocorrencias": 3, "taxa": 0.75 }],
    "situacoes_de_risco": [{ "situacao": "4 dias sem estudo registrado",
                             "base": "limite de 2 dias para risco de quebra de rotina" }]
  },
  "plano_de_acao": {
    "habito_prioritario": { "habito": "estudar nos dias planejados",
                            "motivo": "adesão de 70%; adesão de 80% por 14 dias",
                            "origem": "hábito em formação mais próximo de consolidar" },
    "meta_diaria": { "minutos": 55.0, "ajuste": "mantida",
                     "fatores": ["mediana de 7 sessões registradas",
                                 "adesão de 70%: meta mantida até estabilizar em 80%"],
                     "disponibilidade": { "minutos": 120.0, "base": "2h/dia declaradas pelo estudante" } },
    "meta_semanal": { "minutos": 275.0, "dias": 5, "base": "meta diária × 5 dias de estudo por semana" },
    "proximo_marco": { "marco": "3 dias seguidos", "faltam": 3, "melhor_ja_alcancada": 5,
                       "reforco": "registrar o marco alcançado no próprio painel de progresso" },
    "estrategia_de_manutencao": {
      "acao": "encurtar a sessão até ela voltar a ser concluída todo dia",
      "base": "limite de 2 dias para risco de quebra de rotina",
      "reforcos": ["tratar a volta como recomeço, sem cobrança pelo intervalo",
                   "confirmar a meta cumprida no dia em que ela foi cumprida"]
    }
  },
  "indicadores": {
    "taxa_de_adesao": 0.7,
    "evolucao_da_consistencia": { "disponivel": true, "tendencia": "estavel",
                                  "adesao_atual": 0.7, "adesao_anterior": 0.71 },
    "tendencia_comportamental": "estavel",
    "probabilidade_de_manutencao": { "probabilidade": 0.6, "confianca": "media",
                                     "fatores": ["adesão de 70% na janela",
                                                 "1 situação(ões) de risco em aberto"],
                                     "base": "adesão observada ajustada por sequência, tendência e situações de risco; é projeção comportamental, não previsão de desempenho" },
    "interrupcoes": { "total": 3, "recorrentes": [...], "episodicos": [...] },
    "padroes_por_dia": { "dias_de_maior_falta": [...] }
  },
  "textos_recusados": [],
  "consumido_por": ["21","22","23","24"]
}
```

`probabilidade_de_manutencao` é projeção comportamental com a conta à mostra —
adesão ajustada por sequência, tendência e riscos abertos — nunca um número
solto. Sem adesão medida ela é `null`.

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca criar metas incompatíveis com a disponibilidade | teto em `horas_por_dia`; excesso vira `ajuste: "limitada pela disponibilidade"` |
| Sempre trabalhar com evolução gradual | passo máximo de 20%, e só com adesão ≥ 80% |
| Nunca utilizar punições | `TERMOS_PUNITIVOS` + tabela de reforços sem variedade punitiva |
| Sempre reforçar comportamentos positivos | todo plano sai com reforços; retomada explicitamente sem cobrança |
| Sempre utilizar dados históricos | meta, hábitos e padrões saem do registro; sem registro, nada é afirmado |
| Nunca alterar o Plano de Estudos | a saída não tem cronograma nem sessões — verificado por teste |
| Nunca ensinar nem criar exercícios | nenhum campo carrega conteúdo didático |

## Consumidores

21 · 22 · 23 · 24.
