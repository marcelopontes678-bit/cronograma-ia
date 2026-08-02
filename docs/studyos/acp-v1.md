# Agent Communication Protocol (ACP) v1.0

Implementação: `backend/app/studyos/acp.py`.
Integração: `backend/app/studyos/orchestrator.py`.

Formato único de comunicação entre os 24 agentes. Nenhum agente cria formato
próprio.

## O que o protocolo formaliza

A topologia já era essa por construção: os agentes do StudyOS nunca se
importaram nem se chamaram — quem lê a saída de um e monta a entrada do
seguinte sempre foi o Master Orchestrator. O ACP transforma isso de convenção
em **invariante verificável**: `Mensagem` exige remetente e destinatário, e
uma mensagem entre dois agentes sem o orquestrador numa das pontas levanta
`ComunicacaoDireta`.

```
Agente  →  Master Orchestrator  →  Próximo agente
```

## Mensagem

Dez campos obrigatórios: `message_id`, `workflow_id`, `source_agent`,
`target_agent`, `timestamp`, `priority`, `status`, `action`, `payload`,
`metadata`.

| Vocabulário | Valores |
| --- | --- |
| `priority` | LOW · NORMAL · HIGH · CRITICAL |
| `status` | PENDING · RUNNING · WAITING · COMPLETED · FAILED · CANCELLED |
| `action` | REQUEST · RESPONSE · UPDATE · VALIDATION · RETRY · ERROR · FINISH |

O vocabulário é **fechado**: string crua no lugar do enum é recusada. Mensagem
fora do protocolo não é corrigida — falta de campo, prioridade inválida,
confidence fora de [0, 1] levantam `MensagemInvalida`. Preencher o que falta
seria inventar procedência.

### Prioridade não é opinião

Ela sai da posição do agente no grafo: obrigatório (01, 02, 24) é `CRITICAL`
porque sem ele não há resposta; agente do qual três ou mais dependem é `HIGH`
porque a fila inteira para atrás dele; agente sem dependentes é `LOW`.

## Formato padrão

```jsonc
// entrada
{ "agent": "09", "input": {...}, "context": {...},
  "constraints": ["conteudo_solicitado"], "expected_output": "..." }

// saída
{ "agent": "09", "status": "COMPLETED", "confidence": 0.9,
  "result": {...}, "recommendations": [...], "next_agents": [...], "logs": [...] }
```

`result` é a saída do agente **sem alteração** — o protocolo transporta, não
reescreve. Há um teste que compara o payload com a saída original por
igualdade.

## Confidence é derivada, não inventada

Todo agente do StudyOS já declara `confiabilidade` como rótulo. O protocolo
pede um número entre 0 e 1, e ele sai de uma tabela sobre o rótulo que o
agente já publicou — nunca de uma segunda avaliação:

| Rótulo do agente | confidence |
| --- | --- |
| alta | 0,90 |
| media | 0,65 |
| baixa | 0,35 |
| indeterminada | 0,20 |
| nenhuma | 0,00 |

`nenhuma` não é o mesmo que `baixa`: é o agente dizendo que não produziu nada
sobre o que ter confiança.

Precedência: um `confidence` numérico publicado pelo agente vence o rótulo; o
rótulo vence o padrão. Sem declaração nenhuma, 0,50 — **ausência de
autoavaliação não é sinal de qualidade**. Agente que falhou tem 0,00, não por
convenção: não há saída sobre a qual ter confiança.

### O que isso obrigou a corrigir

Sete agentes (07–11, 13, 16) não declaravam `confiabilidade` — são os que
dependem de um redator e não medem nada. Em vez de deixar o protocolo arbitrar
0,50 para eles, cada um passou a declarar o seu, derivado do status de
produção que já publicava:

| Status | Confiabilidade |
| --- | --- |
| bloqueado / bloqueada / sem_conteudo | nenhuma |
| pendente_de_redacao / pendente_de_geracao | baixa |
| produzido com lacunas | media |
| produzido sem lacunas | alta |

Agora os 23 agentes produtores declaram confiabilidade — verificado por teste
que percorre o registro inteiro.

## Logs

Cada execução gera um `Log` com o que a spec exige: horário, tempo de
execução, entrada recebida, saída produzida, erros e agentes acionados. O
fluxo devolve `orquestracao.logs` com um por agente executado.

## Erros

Falha registra motivo, agente responsável e impacto, e sai como mensagem
`ERROR` com `replay_solicitado_ao: "master_orchestrator"`. Agente cuja entrada
não existe não é ignorado em silêncio: vira `ERROR`/`CANCELLED` endereçado.

## Reexecução

Só por um dos três motivos previstos:

```python
MOTIVOS_DE_REEXECUCAO = (
    "autorizado_pelo_orquestrador",
    "reprovado_pelo_validator",
    "entradas_alteradas",
)
```

`MasterOrchestrator.reexecutar(fluxo, agentes, motivo)` levanta
`ReexecucaoNaoAutorizada` fora dessa lista — e também quando o motivo é
`reprovado_pelo_validator` mas o validator aprovou. Um agente nunca se
reexecuta por conta própria, e nenhum agente pede reexecução de outro: o
pedido chega ao orquestrador, que autoriza e emite o `RETRY`.

## Memória

**Local**: viva apenas durante a execução do agente. `encerrar()` limpa e
fecha — ler ou escrever depois levanta erro. Sem isso, "memória local" seria
só um nome para estado global.

**Compartilhada**: escrita **só** pelo orquestrador, leitura por todos.
`publicar` de qualquer outro autor levanta `ComunicacaoDireta`, e
`como_dicionario()` devolve cópia, para quem lê não alterar o que o
orquestrador publicou.

> ⚠️ A spec do protocolo chegou truncada nesta seção (*"Memória Compartilhada
> — Som…"*). O comportamento implementado é o único compatível com as regras
> que chegaram inteiras — "nenhum agente pode alterar a saída de outro" e
> "todo fluxo passa pelo Master Orchestrator". Está declarado aqui em vez de
> presumido em silêncio, e é o ponto a confirmar quando a spec completa
> chegar.

## O fluxo em mensagens

```
REQUEST     master_orchestrator → 01        CRITICAL  RUNNING
RESPONSE    01 → master_orchestrator        CRITICAL  COMPLETED
REQUEST     master_orchestrator → 02        CRITICAL  RUNNING
...
VALIDATION  master_orchestrator → 24        CRITICAL  RUNNING
RESPONSE    24 → master_orchestrator        CRITICAL  COMPLETED
FINISH      master_orchestrator → master_orchestrator NORMAL COMPLETED
```

`workflow_id` é o mesmo em toda mensagem e todo log do fluxo — verificado por
teste.

## Regras codificadas

| Regra do protocolo | Como é garantida |
| --- | --- |
| Nenhum agente cria formato próprio | `Mensagem`, `EntradaPadrao` e `SaidaPadrao` são os únicos envelopes |
| Nenhum agente altera a saída de outro | `result` transporta a saída original; teste compara por igualdade |
| Toda saída deve possuir confidence | os 23 agentes produtores declaram confiabilidade — teste percorre o registro |
| Todo erro vai ao Master Orchestrator | `Erro` carrega `replay_solicitado_ao` |
| Todo processamento gera logs | um `Log` por execução, com os seis campos exigidos |
| Nenhum agente conversa diretamente com outro | `ComunicacaoDireta` na validação da mensagem |
| Reexecução só nos três casos | `autorizar_reexecucao` como porteiro |
