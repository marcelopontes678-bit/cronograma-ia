# Agente 21 — Performance Analyzer

Implementação: `backend/app/studyos/agentes/performance.py`.

## Identidade

Transforma o que os outros agentes produziram em indicadores objetivos. Não
ensina, não cria cronograma, não gera exercício, não altera o plano.

É o primeiro agente que **quase não mede nada sozinho**, e essa é a decisão que
o define. Domínio já foi medido pelo 03, dificuldade pelo 12, erro pelo 17,
fragilidade pelo 18, consistência pelo 19, hábito pelo 20. Recalcular qualquer
um desses números aqui produziria uma segunda versão dele — e um painel que
discorda dos próprios relatórios não é painel, é ruído.

O que o agente faz:

1. **Consolida com procedência.** Todo indicador tem `valor`, `base` e
   `origem` — o agente que o produziu. Quem lê o painel consegue voltar até a
   medição.
2. **Calcula só o que ninguém calculou:** o IGP, o progresso curricular, o
   desvio entre planejado e realizado, e a evolução entre janelas.
3. **Nunca preenche lacuna com zero.**

## Índice Geral de Performance

| Componente | Peso | Origem |
| --- | --- | --- |
| domínio | 0,30 | agente 03 |
| acerto | 0,25 | histórico de questões |
| progresso | 0,20 | agente 04 |
| consistência | 0,15 | agente 19 |
| retenção | 0,10 | agente 03 |

Classificação → valor: `avancado` 1,00 · `intermediario` 0,65 · `basico` 0,30
· `nao_conhece` 0,00. É a escala do agente 18 invertida: lá mede fragilidade,
aqui mede performance.

Componente sem dado **não entra** e o peso é redistribuído entre os presentes,
com o fato declarado em `observacoes`. Sem nenhum componente, o IGP sai `null`
e `nivel: "indeterminado"` — zero é uma afirmação sobre o estudante, ausência
de dado não é.

Faixas: < 0,40 `critico` · < 0,60 `abaixo_do_esperado` · < 0,80 `adequado` ·
≥ 0,80 `forte`.

## Um número, um dono

Quando o agente 19 está no fluxo, a consistência do painel **é** a dele. Se ele
não estiver, o painel calcula — pelo mesmo código de `frequencia.py`, nunca por
fórmula própria — e declara isso na origem:

```jsonc
"consistencia": {
  "valor": 0.7,
  "base": "dias estudados sobre dias planejados",
  "origem": "medida pelo painel com o mesmo cálculo do agente 19"
}
```

O mesmo vale para tempo por questão: se houver tempo real registrado ele vence;
se só houver o tempo previsto do simulado, o valor sai com
`origem: "agente 16"` e a base diz **"não medido"**.

## Evolução exige amostra

Semanal (7 dias) e mensal (30 dias), cada janela contra a imediatamente
anterior. Ambas exigem 10 questões de cada lado — abaixo disso a tendência sai
`indeterminada` com a contagem que faltou. Variação de 5 pontos percentuais
para deixar de ser estável.

## Desvio do planejado

Dias planejados até hoje contra dias cumpridos, e horas planejadas contra horas
estudadas. É o insumo do alerta de atraso: aderência abaixo de 85% acende
`atraso_no_cronograma`; abaixo de 50%, com gravidade alta.

## Alertas

Alerta é consequência de número medido, nunca de impressão. Quatro tipos:

| Tipo | Dispara quando |
| --- | --- |
| `queda_de_desempenho` | taxa de acerto caiu entre janelas comparáveis |
| `atraso_no_cronograma` | aderência aos dias abaixo de 85% |
| `conteudo_critico` | agente 18 classificou como crítico ou prioridade máxima |
| `risco_na_nota` | acerto previsto no simulado abaixo da nota de corte + 10% |

O `risco_na_nota` declara explicitamente que **a previsão de desempenho é do
agente 22** — aqui é só a comparação entre dois números que já existem.

## Desempenho por nível

Disciplina → módulo → tópico → microtópico, com a estrutura da Árvore
Curricular e as medições dos agentes 03 e 12 mais o histórico de questões.
Tópico sem medição fica `classificacao: "indeterminado"` e taxa `null` — a
hierarquia mostra o que falta medir, não preenche.

## Saída

```jsonc
{
  "atualizado_em": "2026-03-14",
  "resumo_geral": {
    "indice_geral_de_performance": {
      "valor": 0.5398, "nivel": "abaixo_do_esperado", "confianca": "alta",
      "componentes": {
        "dominio":  { "valor": 0.575,  "base": "4 tópicos classificados pelo agente 03", "origem": "agente 03" },
        "acerto":   { "valor": 0.7,    "base": "35 acertos em 50 questões", "origem": "histórico do estudante" },
        "progresso":{ "valor": 0.1667, "base": "1 de 6 tópicos concluídos", "origem": "agente 04" },
        "consistencia": { "valor": 0.7, "origem": "agente 19" }
      },
      "base": "média ponderada de 4 componente(s) medidos; peso redistribuído entre os presentes"
    },
    "percentual_de_progresso": { "percentual": 0.1667, "concluidos": 1, "pendentes": 5, "total": 6 },
    "evolucao_semanal": { "disponivel": false, "tendencia": "indeterminada",
                          "base": "são necessárias 10 questões em cada janela de 7 dias; há 50 e 0" },
    "evolucao_mensal": { ... },
    "tendencia_geral": "indeterminada"
  },
  "indicadores_academicos": {
    "taxa_de_acertos": { "valor": 0.7, "base": "35 acertos em 50 questões", "origem": "histórico do estudante" },
    "taxa_de_erros": { "valor": 0.3, ... },
    "tempo_medio_por_questao_min": { "valor": null, "base": "nenhum tempo de resolução registrado", "origem": null },
    "tempo_total_estudado_h": { "valor": 10.5, "base": "7 sessões registradas" },
    "conteudos_concluidos": { "valor": 1, "origem": "agente 04" },
    "conteudos_pendentes": { "valor": 5, "origem": "agente 04" }
  },
  "indicadores_de_aprendizagem": {
    "retencao_estimada": { ... "origem": "agente 03" },
    "consistencia": { ... "origem": "agente 19" },
    "evolucao_do_conhecimento": { ... "origem": "agente 12" },
    "evolucao_das_dificuldades": { ... "origem": "agente 12" },
    "fragilidade_geral": { ... "origem": "agente 18" },
    "erros_recorrentes": { ... "origem": "agente 17" }
  },
  "indicadores_comportamentais": {
    "frequencia_de_estudo": { ... "origem": "agente 20" },
    "regularidade": { ... "origem": "agente 20" },
    "cumprimento_de_metas": { ... "origem": "agente 19" },
    "evolucao_dos_habitos": { ... "origem": "agente 20" },
    "engajamento": { ... "origem": "agente 19" },
    "revisoes_agendadas": { ... "origem": "agente 15" }
  },
  "desempenho_por_nivel": { "disciplinas": [ /* módulos → tópicos → microtópicos */ ] },
  "desvio_do_planejado": {
    "disponivel": true, "dias_planejados": 10, "dias_cumpridos": 7,
    "aderencia_aos_dias": 0.7, "horas_planejadas": 16.8, "horas_estudadas": 10.5,
    "horas_de_diferenca": -6.3
  },
  "alertas": [
    { "tipo": "atraso_no_cronograma", "gravidade": "media",
      "detalhe": "7 de 10 dias planejados cumpridos (-6.3h em relação ao previsto)" },
    { "tipo": "conteudo_critico", "gravidade": "alta",
      "detalhe": "Conjuntos com índice de fraqueza 0.8687", "base": "classificação do agente 18" }
  ],
  "metricas_para_previsao": {
    "destinatario": "22", "igp": 0.5398, "taxa_de_acertos": 0.7,
    "percentual_de_progresso": 0.1667, "aderencia_aos_dias": 0.7,
    "base": "insumos objetivos para a projeção do agente 22; este agente não projeta desempenho futuro"
  },
  "consumido_por": ["22","23","24"]
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca alterar métricas sem dados | componente sem fonte fica fora do IGP; indicador sem fonte sai `null` com motivo |
| Sempre utilizar dados históricos | evolução por janelas comparáveis e desvio contra o planejado |
| Sempre apresentar indicadores objetivos | todo indicador tem `valor`, `base` e `origem` — verificado por teste |
| Nunca ensinar nem criar exercícios | nenhum campo carrega conteúdo didático |
| Nunca modificar o Plano de Estudos | a saída não tem cronograma nem sessões — verificado por teste |
| Nunca alterar o currículo | a árvore do 04 entra só como estrutura e contagem |

## Consumidores

22 · 23 · 24.
