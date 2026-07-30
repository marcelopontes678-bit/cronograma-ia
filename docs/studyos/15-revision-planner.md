# Agente 15 — Revision Planner

Implementação: `backend/app/studyos/agentes/revisao.py`.

## Identidade

Transforma o calendário do agente 14 em sessões executáveis. Não ensina, não
cria conteúdo, não gera exercícios e **não modifica o Plano de Estudos
principal** — ele ocupa o bloco de revisão que o agente 06 já reservou.

A diferença entre os dois agentes de memória: o **14 decide quando** cada
conteúdo volta; o **15 decide como aquele dia vira sessão** — quantas, de que
tipo, em que ordem e com qual critério de conclusão.

## Tipos de sessão

| Risco de esquecimento (agente 14) | Tipo | Complemento |
| --- | --- | --- |
| baixo | `rapida` | — |
| médio / indeterminado | `aprofundada` | autoexplicação |
| alto / crítico | `critica` | explicação ativa |

Explicação ativa e autoexplicação são os dois métodos que **só existem em
sessão**: o agente 14 não os agenda, o 15 os aplica sobre o método que o 14 já
escolheu.

## Critério de conclusão por método

Cada sessão declara o que fecha a revisão de verdade:

| Método | Critério |
| --- | --- |
| flashcards | acertar 90% dos cartões sem consultar |
| leitura do resumo | reproduzir os pontos-chave de memória |
| questões comentadas | justificar a resposta de cada questão, certa ou errada |
| exercícios | resolver sem consultar e conferir o gabarito |
| reestudo da aula | explicar o conceito em voz alta sem olhar |
| explicação ativa | explicar como se estivesse ensinando outra pessoa |
| autoexplicação | escrever com as próprias palavras por que cada passo funciona |

## Carga: três tetos

| Teto | Valor | Por quê |
| --- | --- | --- |
| Minutos por sessão | 45 | acima disso a atenção cai mais do que rende |
| Conteúdos críticos por sessão | 2 | três reestudos seguidos não cabem na mesma cabeça |
| Mínimo por sessão | 10 min | bloco menor vira anexo da sessão anterior |

Dentro da sessão, pesados e leves são **intercalados**: a prioridade decide
*quem entra*, a intercalação decide *em que ordem se estuda*.

## O que não cabe é adiado, não descartado

Quando o bloco de revisão do dia esgota, o excedente **passa para o próximo dia
com bloco livre** — o mesmo mecanismo de remanejamento do agente 14. Só depois
de percorrer o horizonte é que o conteúdo vira `conteudos_nao_alocados`, e
ainda assim declarado.

O corte do dia segue a ordem de prioridade do Memory Scheduler: sai o de menor
prioridade, nunca o primeiro da fila.

### O conteúdo que nunca caberia

Um método que custa mais que o bloco inteiro do dia (reestudo de 25 min contra
um bloco de 23) nunca caberia em dia nenhum — e adiá-lo para sempre seria
honesto e inútil. Ele entra assim mesmo, sozinho, com o estouro declarado:

```jsonc
"excede_o_bloco_do_dia": {
  "minutos_necessarios": 28.0,
  "minutos_disponiveis": 23.0,
  "motivo": "o método exigido custa mais que o bloco de revisão do dia; adiar indefinidamente seria pior"
}
```

## Saída

```jsonc
{
  "resumo_geral": {
    "numero_total_de_sessoes": 4, "tempo_total_de_revisao_min": 70.0,
    "conteudos_prioritarios": ["Conjuntos"], "conteudos_criticos": ["Conjuntos", "Probabilidade"],
    "origem_do_tempo_disponivel": "bloco de revisão do Plano de Estudos (agente 06)",
    "periodo": { "inicio": "2026-01-05", "fim": "2026-01-07" }
  },
  "sessoes": [{
    "id": "sessao-2026-01-05-01", "data": "2026-01-05", "tipo": "critica", "duracao_min": 28.0,
    "objetivo": "Recuperar Conjuntos, em risco alto de esquecimento",
    "conteudos": [ { "topico": "Conjuntos", "metodo": "reestudo_da_aula", "minutos": 28.0, "risco_de_esquecimento": "critico", "prioridade": "alta" } ],
    "metodos_de_revisao": ["reestudo_da_aula", "explicacao_ativa"],
    "materiais_necessarios": ["aula do agente 07", "nenhum — a explicação é oral"],
    "criterios_de_conclusao": [ { "metodo": "reestudo_da_aula", "criterio": "explicar o conceito em voz alta sem olhar o material" } ],
    "meta": { "conteudos_a_revisar": 1, "minutos": 28.0, "resultado_esperado": "reconstruir o raciocínio completo do zero" },
    "equilibrio": { "pesados": 1, "leves": 0 }
  }],
  "conteudos_adiados": [ { "topico": "Sintaxe", "de": "2026-01-05", "prevista_em": "2026-01-05", "motivo": "tempo de revisão do dia esgotado (31 min disponíveis)" } ],
  "conteudos_nao_alocados": [],
  "indicadores": {
    "cobertura_das_revisoes": 1.0, "conteudos_em_sessao": 4, "conteudos_monitorados": 4,
    "distribuicao_por_disciplina": { "Estatística": 2, "Português": 2 },
    "equilibrio_de_dificuldade": { "pesados": 2, "leves": 2, "proporcao_pesados": 0.5 },
    "tempo_medio_por_sessao_min": 17.5, "percentual_planejado": 1.0,
    "sessoes_por_tipo": { "rapida": 1, "aprofundada": 1, "critica": 2 }
  },
  "replanejamento": { "houve_replanejamento": false, "base": "nenhum plano de sessões anterior informado" },
  "consumido_por": ["16","17","18","19","21","22","23","24"]
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca revisar conteúdo não estudado | herdado do agente 14: o que ele não elegeu não chega aqui |
| Sempre respeitar as prioridades do Memory Scheduler | ordenação e corte por `prioridade` + `score_de_prioridade` do 14 |
| Sempre adaptar ao tempo disponível | limite por dia vindo do agente 06 ou de `tempo_revisao_min` |
| Sempre evitar sessões longas demais | teto de 45 min e de 2 críticos por sessão |
| Nunca modificar o Plano de Estudos nem a Árvore | a saída não tem cronograma, disciplinas nem nós — verificado por teste |
| Atualizar quando houver mudança | `sessoes_anteriores` habilita o diff de novas, removidas e alteradas |

## Consumidores

16 · 17 · 18 · 19 · 21 · 22 · 23 · 24.
