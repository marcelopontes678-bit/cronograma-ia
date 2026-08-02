# Agente 24 — Validators

Implementação: `backend/app/studyos/validators.py`.

## Identidade

Audita o que os outros agentes produziram antes de qualquer coisa chegar ao
estudante. Não ensina, não cria conteúdo, não modifica resposta, não monta
cronograma. Fecha todo fluxo — é um dos três agentes obrigatórios.

A validação é **estrutural e comparativa, nunca generativa**. Ela não sabe se
uma aula está boa: sabe se a aula que o agente 07 devolveu tem os campos que o
07 promete ter, se o conteúdo dela estava liberado pelo grafo, e se o número
que ela cita bate com o número publicado pelo agente que o mediu.

## O validador não toca em nada

`validar` recebe as saídas e devolve um laudo. Nenhuma saída é corrigida,
completada ou reescrita — nem quando falta um campo obrigatório. Há um teste
que compara as saídas antes e depois por igualdade profunda: se o validador
mexer, ele falha.

Campo ausente vira problema declarado, não valor padrão. É a mesma regra que
os outros 23 agentes seguem, aplicada a quem os audita.

## Contradição entre agentes é o alvo principal

O sistema inteiro foi construído para que cada número tenha um dono só —
consistência mora no 19, fragilidade no 18, ganho de alavanca no 22. Aqui
essas invariantes deixam de ser disciplina de implementação e viram
**verificação em tempo de execução**:

| Fato | Dono | Quem repete |
| --- | --- | --- |
| índice de consistência | 19 | 21 |
| índice geral de fragilidade | 18 | 21 |
| nível de engajamento | 19 | 21 |
| taxa de acertos da projeção | 21 | 22 |
| aderência da projeção | 21 | 22 |
| ganho de cada alavanca | 22 | 23 |

Se dois agentes discordarem sobre o mesmo fato, o fluxo é **reprovado** e a
correção aponta para quem deveria ter reaproveitado o valor. Ausência de um
dos lados não é divergência: a invariante simplesmente não é conferida.

## Os oito grupos

| # | Grupo | O que confere |
| --- | --- | --- |
| 1 | estrutural | agentes obrigatórios, falhas de execução, contrato mínimo de campos |
| 2 | consistência | dependências satisfeitas e invariantes entre agentes |
| 3 | pedagógica | cronograma respeita a ordem de pré-requisitos do grafo |
| 4 | técnica | ciclos, nós duplicados, referências inválidas, conteúdo agendado fora da árvore |
| 5 | qualidade | saídas com `status` pendente ou `bloqueio` declarado |
| 6 | segurança | projeção sem intervalo, recomendação sem evidência, causa de erro sem evidência, mensagem sem dado citado |
| 7 | performance | agente que rodou sem ninguém consumir a saída |
| 8 | final | APROVADA · APROVADA_COM_RESSALVAS · REPROVADA |

O grupo de segurança é o que caça afirmação sem lastro — ele reexecuta, do
lado de fora, as mesmas regras que os agentes 17, 19, 22 e 23 aplicam por
dentro. Se um deles falhar em cumprir a própria regra, o laudo pega.

### Duas sutilezas

- **Um subtópico é conteúdo tão legítimo quanto o tópico que o contém.**
  Conferir só o nível de tópico acusaria de fantasma exatamente o detalhamento
  que o agente 04 produziu.
- **Agente cuja saída é entregue ao orquestrador não é órfão.** Quem declara
  isso é o próprio agente, em `consumido_por` — é o fim de uma linha, não um
  cálculo perdido.

## Gravidade e status

| Gravidade | Efeito |
| --- | --- |
| `bloqueante` | reprova o fluxo; a resposta não vai ao estudante |
| `ressalva` | aprova com marca; entra em `alertas` |

Lacuna declarada por um agente **não** é problema: é o agente sendo honesto
sobre o que não recebeu. Vira alerta para o orquestrador decidir.

## Índices

| Índice | Como é contado |
| --- | --- |
| qualidade | verificações estruturais e de qualidade sem problema |
| consistência | invariantes, ordem de pré-requisitos e integridade referencial |
| confiabilidade | afirmações com lastro sobre o total verificado |
| completude | saídas sem lacuna declarada sobre o total |

Nenhum é opinião: cada um conta o que foi verificado.

## Plano de correção

Quando há bloqueante, o laudo diz quem reexecutar, em que ordem e o que
corrigir:

```jsonc
"plano_de_correcao": {
  "agentes_a_reexecutar": ["01", "02", "03", "04"],
  "ordem_de_reexecucao": [["01"], ["02"], ["03"], ["04"]],
  "campos_a_corrigir": ["06.cronograma"],
  "criterios_para_nova_validacao": ["reordenar o cronograma segundo a sequência do grafo"],
  "base": "ordem topológica dos agentes envolvidos; o Master Orchestrator é quem decide reexecutar"
}
```

Quem falhou **e** quem rodou sem a entrada dele voltam juntos. Reexecutar só o
agente que falhou deixaria de pé saídas produzidas sem a entrada dele —
corretas por acidente, no melhor caso.

## Saída

```jsonc
{
  "aprovado": true,
  "status": "APROVADA_COM_RESSALVAS",
  "resumo_geral": {
    "status_da_validacao": "APROVADA_COM_RESSALVAS",
    "indice_de_qualidade": { "valor": 0.6, "base": "..." },
    "indice_de_consistencia": { "valor": 1.0, "base": "..." },
    "indice_de_confiabilidade": { "valor": 0.88, "base": "..." },
    "indice_de_completude": { "valor": 0.42, "base": "14 de 24 saídas declararam lacuna de informação" },
    "verificacoes_realizadas": 11, "problemas_encontrados": 14
  },
  "verificacoes": [
    "Agentes obrigatórios executados",
    "Toda dependência foi satisfeita antes da execução",
    "3 invariante(s) entre agentes conferida(s) sem divergência",
    "Cronograma respeita a ordem de pré-requisitos do grafo",
    "Grafo de dependências acíclico",
    "Todo conteúdo agendado existe na Árvore Curricular",
    "3 projeção(ões) conferida(s) quanto ao intervalo"
  ],
  "problemas": [], "alertas": [...],
  "problemas_detalhados": [{
    "id": "v001", "categoria": "qualidade", "gravidade": "ressalva",
    "descricao": "07 Lesson Generator devolveu status 'pendente_de_redacao'",
    "agente_responsavel": "07", "campo": "status",
    "correcao_necessaria": "conectar o redator ou liberar o pré-requisito antes de entregar"
  }],
  "plano_de_correcao": { ... },
  "consumido_por": ["Master Orchestrator"],
  "observacoes": [
    "Este agente não altera nenhuma saída: ele audita e devolve o laudo.",
    "Somente respostas aprovadas podem ser entregues ao estudante."
  ]
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca alterar diretamente a saída de outro agente | teste compara as saídas antes e depois por igualdade profunda |
| Nunca inventar informações para corrigir problemas | campo ausente vira achado, nunca valor padrão |
| Toda inconsistência reportada ao orquestrador | `consumido_por: ["Master Orchestrator"]` e `plano_de_correcao` |
| Validação baseada só em evidências disponíveis | invariante com um lado ausente não é conferida |
| Somente respostas aprovadas vão ao estudante | `aprovado` e `status` no topo do laudo |

## Consumidores

Master Orchestrator.
