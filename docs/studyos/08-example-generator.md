# Agente 08 — Example Generator

Implementação: `backend/app/studyos/agentes/exemplos.py`.

## Identidade

Cria exemplos didáticos do conteúdo que o agente 07 ensinou. Não cria aulas,
não cria cronogramas, não gera exercícios, flashcards ou simulados, não avalia o
estudante.

## O portão deste agente é a teoria

A regra "nunca criar exemplos que contradigam a teoria apresentada" só é
verificável se a teoria existir. Sem aula redigida, não há o que não
contradizer — e o agente não gera:

| Estado da aula (agente 07) | Resultado |
| --- | --- |
| ausente | `bloqueio: aula_ausente` |
| `bloqueada_por_pre_requisito` | `bloqueio: aula_bloqueada_por_pre_requisito`, com os pré-requisitos faltantes |
| `pendente_de_redacao` | `bloqueio: teoria_nao_redigida` |
| `gerada` | exemplos liberados |

Como no agente 07, o portão é aplicado duas vezes: `gerar()` não chama o redator
sem teoria, e `montar()` levanta `TeoriaAusente` se receber exemplos prontos
para uma aula que não existe.

## Slots

| Slot | Nível | Condicional |
| --- | --- | --- |
| `exemplo_introdutorio` | básico | não |
| `exemplo_pratico` | intermediário | não |
| `exemplo_avancado` | avançado | **sim** — "quando aplicável" |
| `exemplo_aplicado_ao_mundo_real` | aplicado | não |
| `analogia` | conceitual | **sim** — "quando útil" |
| `contraexemplo` | diagnóstico | não |

Cada slot redigido vira `{nivel, enunciado, por_que_funciona}`. O redator pode
devolver texto puro — o `por_que_funciona` fica `None` em vez de inventado.

### Quando o exemplo avançado se aplica

Exige **base**: estudante em nível intermediário ou avançado, ou em nível básico
com conteúdo difícil. Para quem ainda não conhece o conteúdo, o caso de exceção
só atrapalha — "clareza em vez de complexidade" vale inclusive quando o conteúdo
em si é difícil. Sem nível medido, o agente não arrisca.

### Quando a analogia é útil

Conteúdo difícil ou estudante iniciante/básico. A instrução exige declarar
**onde a analogia deixa de valer**: analogia sem limite declarado vira erro
futuro.

## Ancoragem na aula

O briefing carrega a teoria como referência obrigatória:

```jsonc
{
  "conceito_abordado": "Dominar Crase no contexto de Português",
  "teoria_de_referencia": {
    "desenvolvimento": "…texto da aula…",
    "pontos_chave": ["…"],
    "erros_comuns": "…",
    "regra": "Todo exemplo deve ser consistente com este desenvolvimento. Em qualquer divergência, a teoria da aula prevalece."
  },
  "slots": [ { "chave": "exemplo_introdutorio", "nivel": "basico", "aplicavel": true, "instrucao": "…" } ],
  "slots_aplicaveis": ["exemplo_introdutorio", "exemplo_pratico", "exemplo_aplicado_ao_mundo_real", "analogia", "contraexemplo"],
  "diretrizes": ["Linguagem de nível basico, igual à da aula.", "Clareza antes de complexidade…", "O contraexemplo deve atacar os erros comuns já listados na aula."],
  "contexto_do_estudante": { "profissao": "Analista tributário", "exame_alvo": "ICMS-SP", "uso": "…nunca forçando a conexão." },
  "proibicoes": ["não criar aulas completas (agente 07)", "não criar exercícios nem questões (agente 09)", "…"]
}
```

O **contraexemplo é orientado pelos `erros_comuns` da própria aula** — em vez de
um contraexemplo genérico, ele ataca o erro que a teoria já identificou. Quando
a aula não traz erros comuns, isso é registrado em `observacoes`.

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca contradizer a teoria apresentada | portão exige aula `gerada`; a teoria vai no briefing com regra de precedência |
| Nunca usar informações sem fundamento | sem redator, slots ficam `None`; nada é preenchido por código |
| Linguagem compatível com o nível | nível herdado da aula, que por sua vez vem da medição do agente 03 |
| Clareza antes de complexidade | exemplo avançado exige base do estudante, mesmo em conteúdo difícil |
| Não criar aulas, exercícios, flashcards ou simulados | `proibicoes` no briefing e descarte de chaves fora dos slots (`slots_ignorados`) |

## Consumidores

09 · 10 · 11 · 13 · 24.
