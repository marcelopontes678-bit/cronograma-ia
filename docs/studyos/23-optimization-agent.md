# Agente 23 — Optimization Agent

Implementação: `backend/app/studyos/agentes/otimizacao.py`.

## Identidade

Encontra onde o sistema está desperdiçando esforço e propõe a correção. Não
ensina, não cria aula, não gera exercício, não altera o currículo.

## Propor não é executar

A regra mais importante aqui não é sobre o que o agente calcula, e sim sobre o
que ele **não faz**. "Nunca modificar diretamente qualquer agente", "nunca
alterar o cronograma diretamente", "toda alteração deve ser enviada ao Master
Orchestrator para aprovação" viraram três mecanismos:

1. **A saída é um pedido.** Cada otimização carrega
   `aprovacao_necessaria: true` e vira uma entrada em
   `solicitacoes_de_atualizacao`, endereçada ao orquestrador com
   `status: "aguardando_aprovacao"` e a lista de agentes a reexecutar.
2. **A saída não carrega estrutura executável.** Nenhum cronograma, nenhuma
   árvore, nenhuma sessão — só a descrição do que mudar e em qual agente. O
   teste verifica a ausência dessas chaves.
3. **A última observação diz isso em português**: *"Nenhuma alteração foi
   aplicada. Toda otimização é um pedido de aprovação ao Master
   Orchestrator."*

## Sem evidência não há otimização

Cada recomendação nasce de um detector que só dispara com número medido, e
lista `evidencias` com `indicador`, `valor` e `origem`. Detector sem dado fica
calado — e quando o relatório sai vazio, a observação diz por quê:

> Ausência de proposta não é ausência de problema — é ausência de dado que o
> comprove.

### Os oito detectores

| Categoria | Dispara quando | Agentes afetados |
| --- | --- | --- |
| `gargalo` | conteúdo crítico que trava outros (18 + 05) | 06, 15 |
| `desperdicio_de_tempo` | tempo real 30% acima do estimado (12), ou horas além do planejado (21) | 04, 06, 13 |
| `estudo_alem_do_necessario` | conteúdo dominado, de peso baixo, ainda no cronograma | 06 |
| `baixa_retencao` | retenção < 60% **e** sem revisão agendada | 14, 15 |
| `cronograma` | aderência < 70% aos dias planejados | 06, 20 |
| `revisao` | revisão prevista que não virou sessão (15), ou conteúdo fora do ciclo (14) | 06, 14, 15 |
| `estrategia_didatica` | 3+ erros do mesmo tipo (17) | conforme o tipo |
| `aceleracao` | conteúdo pronto para avançar, ou cobertura projetada < 100% (22) | 02, 06 |

O detector de retenção só acusa conteúdo **sem revisão agendada**: apontar
retenção baixa em algo que o agente 15 já marcou para revisar seria pedir o
que já foi feito.

O de estratégia didática mapeia o tipo de erro predominante para uma mudança
de método e para o agente que a executa — erro de cálculo vai para o 08 (mais
exemplos resolvidos), erro de memorização para o 14 (antecipar revisão), erro
conceitual para o 13.

## O ganho é o número do agente 22

Quando a otimização corresponde a uma alavanca que o Forecast Agent já
precificou, o ganho **é** o dele:

| Categoria | Alavanca do agente 22 |
| --- | --- |
| `cronograma` | `melhora_na_consistencia` |
| `gargalo` | `reforco_de_conteudos_criticos` |
| `baixa_retencao` | `aumento_da_retencao` |
| `desperdicio_de_tempo` | `aumento_da_carga_horaria` |

Dois agentes prometendo ganhos diferentes para a mesma ação seria pior que
nenhum número. Categoria sem alavanca correspondente sai com
`impacto_esperado: null` — não com uma estimativa inventada.

E o ganho potencial do resumo é o **maior** entre as alavancas, nunca a soma:
elas se sobrepõem, e somá-las prometeria um ganho que não existe.

## Índice Geral de Eficiência

| Componente | Peso | Origem |
| --- | --- | --- |
| aproveitamento do tempo | 0,30 | agente 21 (horas estudadas / planejadas) |
| eficácia do estudo | 0,30 | agente 21 (taxa de acerto) |
| cobertura das revisões | 0,20 | agente 15 |
| retenção | 0,20 | agente 03 |

Componente sem dado não entra e o peso é redistribuído. Sem componente
nenhum, o índice sai `null` com o motivo.

Faixas: < 0,40 `baixa` · < 0,65 `moderada` · < 0,85 `boa` · ≥ 0,85 `alta`.

## Plano de execução

As otimizações são ordenadas por gravidade e, dentro dela, por ganho
estimado. Cada passo traz critério de sucesso e a métrica que valida:

```jsonc
{
  "id": "o001", "ordem": 1,
  "acao": "reduzir a carga diária até a aderência voltar a subir",
  "agentes_afetados": ["06", "20"],
  "depende_de": [],
  "criterio_de_sucesso": "aderencia_aos_dias melhora na próxima medição",
  "metrica_de_validacao": { "metrica": "aderencia_aos_dias", "medida_por": "21" }
}
```

Duas otimizações que mexem no mesmo agente são **encadeadas**: a segunda
depende da primeira. Aplicadas juntas, o efeito de cada uma deixaria de ser
atribuível — e a métrica de validação perderia o sentido.

## Saída

```jsonc
{
  "emitido_em": "2026-03-14",
  "resumo_geral": {
    "indice_geral_de_eficiencia": {
      "valor": 0.5732, "nivel": "moderada", "confianca": "media",
      "componentes": {
        "aproveitamento_do_tempo": { "valor": 0.4464, "base": "7.5h estudadas de 16.8h planejadas", "origem": "agente 21" },
        "eficacia_do_estudo": { "valor": 0.7, "base": "taxa de acerto de 70%", "origem": "agente 21" }
      }
    },
    "ganho_potencial_estimado": { "estimativa": 0.0445, "origem": "agente 22",
                                  "base": "maior ganho entre as alavancas já precificadas pelo agente 22; ganhos não são somados porque as alavancas se sobrepõem" },
    "gargalos_identificados": [],
    "oportunidades_encontradas": 2,
    "distribuicao_por_categoria": { "cronograma": 1, "aceleracao": 1 }
  },
  "otimizacoes_recomendadas": [{
    "id": "o001", "categoria": "cronograma", "prioridade": 1, "gravidade": "alta",
    "problema": "apenas 50% dos dias planejados foram cumpridos: a carga diária não cabe na rotina",
    "evidencias": [
      { "indicador": "aderencia_aos_dias", "valor": 0.5, "origem": "agente 21" },
      { "indicador": "meta_diaria_min", "valor": 55.0, "origem": "agente 20" }
    ],
    "acao": "reduzir a carga diária até a aderência voltar a subir",
    "impacto_esperado": { "ganho_na_probabilidade": 0.0445, "alavanca": "melhora_na_consistencia", "origem": "agente 22" },
    "agentes_afetados": ["06", "20"],
    "aprovacao_necessaria": true
  }],
  "analise_de_impacto": { /* tempo, retenção, desempenho, riscos — cada um com base */ },
  "plano_de_execucao": { "passos": [...], "agentes_envolvidos": ["06","20"] },
  "solicitacoes_de_atualizacao": [{
    "id": "o001", "destinatario": "Master Orchestrator",
    "agentes_a_reexecutar": ["06", "20"],
    "mudanca_solicitada": "reduzir a carga diária até a aderência voltar a subir",
    "status": "aguardando_aprovacao",
    "base": "este agente não modifica nenhum outro: a alteração só acontece se o orquestrador aprovar e reexecutar os agentes"
  }],
  "consumido_por": ["24", "Master Orchestrator"]
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca modificar diretamente qualquer agente | a saída só contém pedidos; `aprovacao_necessaria` em todas |
| Nunca alterar o cronograma diretamente | nenhuma chave de cronograma na saída — verificado por teste |
| Nunca alterar o currículo | a árvore do 04 entra só como leitura |
| Toda otimização baseada em evidências objetivas | detector sem número não dispara; evidência sem valor é descartada antes de virar recomendação |
| Toda alteração enviada ao orquestrador | `solicitacoes_de_atualizacao` com `status: "aguardando_aprovacao"` |
| Nunca ensinar nem criar exercícios | nenhum campo carrega conteúdo didático |
| Nunca alterar dados históricos | o agente só lê saídas de outros agentes |

## Consumidores

24 · Master Orchestrator.
