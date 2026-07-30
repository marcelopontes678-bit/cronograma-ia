# Agente 04 — Curriculum Builder

Implementação: `backend/app/studyos/agentes/curriculo.py`.

## Identidade

Constrói a **Árvore Curricular Inteligente**. Não ensina, não cria cronogramas,
não responde dúvidas, não gera exercícios.

## Objetivo

Organizar o objetivo em disciplinas → módulos → tópicos → subtópicos →
microtópicos, respeitando a lógica natural do aprendizado.

## Entradas

| Campo | Origem |
| --- | --- |
| Perfil Cognitivo | agente 01 |
| Mapa Estratégico | agente 02 — disciplinas, pesos e prioridades |
| Mapa de Conhecimento | agente 03 — domínio por tópico, esquecimento |
| `edital` | usuário — fonte primária da estrutura |
| `matriz_curricular` | usuário — referência quando não há edital |
| `subtopicos` / `microtopicos` | usuário — `{pai: [filhos]}` |
| `pre_requisitos` | usuário — `{tópico: [pré-requisitos]}` |
| `conteudos_obrigatorios` / `conteudos_opcionais` | usuário |

O edital é lido em quatro formatos: `{disciplina: [tópicos]}`,
`{disciplina: {topicos: [...], peso, questoes}}`,
`{disciplina: {modulos: {módulo: {tópico: [subtópicos]}}}}` e lista de
dicionários com `nome`.

## Como os cinco níveis são preenchidos

| Nível | Vem de | Se não existir |
| --- | --- | --- |
| Disciplina | agente 02 | não há currículo — observação explícita |
| Módulo | `edital.modulos` | disciplina vira **módulo único**, preservando a ordem dos tópicos |
| Tópico | edital / matriz / agente 02 | — |
| Subtópico | aninhamento do edital ou mapa `subtopicos` | entra em `pendencias_de_detalhamento` |
| Microtópico | aninhamento ou mapa `microtopicos` | entra em `pendencias_de_detalhamento` |

Agrupar tópicos em módulos por conta própria seria decidir pedagogia, não
estrutura — por isso o fallback é o módulo único, sinalizado em
`origem: "modulo_unico_por_ausencia_de_modularizacao"`.

## Classificações

**Dificuldade** (5 níveis, a partir do domínio medido pelo agente 03):

| Domínio medido | Grau inicial |
| --- | --- |
| avançado | muito_facil |
| intermediário | facil |
| básico | medio |
| não conhece | dificil |
| indeterminado | medio (confiança baixa) |

Agravos: +1 nível por dificuldade declarada pelo estudante, +1 por tópico com 5
ou mais subtópicos. Esquecimento **não** agrava aqui — o agente 03 já rebaixou a
classificação, e cobrar duas vezes pelo mesmo fato distorceria o grau; o fato
fica registrado em `fatores`.

**Importância** (4 níveis): `essencial` para disciplina de prioridade alta,
`alta` para média, `media` para baixa. Tópico listado em
`conteudos_obrigatorios` sobe para `essencial`; em `conteudos_opcionais` cai
para `baixa` e perde a obrigatoriedade.

**Status**: `dominado` (avançado), `em_andamento` (básico/intermediário),
`nao_iniciado` (não conhece / sem evidência). Sobe na árvore por consolidação —
subtópico só é `dominado` se todos os microtópicos forem.

## Tempo

Soma de baixo para cima. Microtópico 0.5h; subtópico sem microtópicos 1.0h;
tópico sem subtópicos 2.5h — o mesmo valor usado pelos agentes 02 e 03, para
que as três estimativas conversem. `tempo_pendente_h` desconta o que já está
dominado.

## Saída

```jsonc
{
  "objetivo": "Passar no concurso do ICMS-SP",
  "referencia_utilizada": "edital",
  "disciplinas": [{
    "nome": "Português", "importancia": "essencial", "peso": 20.0,
    "tempo_estimado_h": 4.0, "tempo_pendente_h": 3.0, "status": "em_andamento",
    "modulos": [{
      "nome": "Gramática", "ordem_recomendada": 1, "tempo_estimado_h": 2.0,
      "topicos": [{
        "nome": "Crase", "pre_requisitos": [],
        "dificuldade": { "grau": "muito_facil", "fatores": ["domínio medido: avancado"], "confianca": "media" },
        "importancia": "essencial", "obrigatorio": true, "status": "dominado",
        "tempo_estimado_h": 1.0,
        "subtopicos": [{
          "nome": "Casos obrigatórios", "objetivo_de_aprendizagem": "Dominar Casos obrigatórios no contexto de Crase",
          "tempo_estimado_h": 1.0, "status": "dominado",
          "microtopicos": [ { "nome": "Antes de femininos", "status": "dominado", "tempo_estimado_h": 0.5 } ]
        }]
      }]
    }]
  }],
  "totais": { "disciplinas": 2, "modulos": 3, "topicos": 5, "subtopicos": 4, "microtopicos": 2 },
  "tempo_total_estimado_h": 9.0, "tempo_pendente_estimado_h": 8.0,
  "conteudos_obrigatorios": ["..."], "conteudos_opcionais": [],
  "conteudos_dominados": ["Crase"], "conteudos_pendentes": ["..."],
  "pendencias_de_detalhamento": [ { "disciplina": "Português", "topico": "Sintaxe", "nivel_faltante": "microtopicos" } ],
  "integridade": { "topicos_esperados": 5, "topicos_presentes": 5, "faltando": [], "ordem_preservada": true, "ok": true },
  "consumido_por": ["05","06","07","09","10","11","14","15","16","23"]
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca remover conteúdos obrigatórios | bloco `integridade` compara os tópicos esperados do agente 02 com os presentes na árvore e lista o que faltou |
| Nunca alterar a ordem lógica | a ordem de aparição no edital vira `ordem_recomendada`; nenhuma ordenação é aplicada |
| Sempre respeitar o edital | `_fonte_da_disciplina` procura no edital antes da matriz curricular |
| Sem edital, usar referência reconhecida | `matriz_curricular` é aceita como fonte; sem nenhuma das duas, a limitação entra em `observacoes` e `lacunas` |
| Não gerar aulas, exercícios, resumos ou cronograma | a saída não tem texto de conteúdo nem datas — um teste verifica a ausência dessas chaves |

## Consumidores

05 · 06 · 07 · 09 · 10 · 11 · 14 · 15 · 16 · 23.
