# Agente 07 — Lesson Generator

Implementação: `backend/app/studyos/agentes/aula.py`.

## Identidade

Gera a aula de um conteúdo da Árvore Curricular. Não cria cronogramas, não
decide ordem de estudo, não avalia desempenho, não gera exercícios, flashcards
ou simulados.

## Por que este agente é diferente dos seis anteriores

Aula é **conteúdo didático**. Código determinístico não escreve conteúdo
didático sem inventar — e inventar é exatamente o que a regra "nunca utilizar
informações sem fundamento" proíbe. O módulo então separa:

| Camada | Responsável | Por quê |
| --- | --- | --- |
| Portão de pré-requisitos, nível do estudante, estrutura das seções, fontes, coerência | **código** | são regras; não podem depender de um modelo se comportar bem |
| Redação das oito seções | **modelo** (redator) | é conteúdo; sem redator, volta `None` com briefing pronto |

`montar()` revalida o portão **venha a redação de onde vier**: entregar texto
pronto para um conteúdo bloqueado levanta `AulaBloqueada`. Um modelo não
consegue convencer o agente a ensinar fora de ordem.

## Conectando um redator

```python
from app.studyos import MasterOrchestrator
from app.studyos.runner import RunnerEstrutural

def redator(briefing: dict) -> dict:
    # briefing traz nível, seções, fontes, coerência e proibições
    return {secao["chave"]: chamar_modelo(briefing, secao) for secao in briefing["secoes"]}

orquestrador = MasterOrchestrator(RunnerEstrutural(redatores={"07": redator}))
```

Os demais agentes seguem determinísticos: o redator só entra onde há conteúdo a
escrever.

## Portão de pré-requisitos

O status vem do agente 05. Três situações:

| Situação | Resultado |
| --- | --- |
| Nó `bloqueado` por pré-requisito direto | `status: bloqueada_por_pre_requisito`, seções `None`, redator **não é chamado** |
| Nó bloqueado por ancestral | idem, com `pendentes_por_ancestral` preenchido |
| Nó `disponivel` ou `concluido` | aula liberada |

## Nível da linguagem

| Fonte | Nível |
| --- | --- |
| Domínio medido do tópico (agente 03) | `nao_conhece`→iniciante, `basico`→básico, `intermediario`→intermediário, `avancado`→avançado |
| Sem medição: estimativa geral do agente 01 | um nível **abaixo** da estimativa, como folga |
| Sem nada | `iniciante`, confiança `nenhuma` |

Começar abaixo é o erro barato: uma aula fácil demais custa tempo, uma aula
difícil demais custa o conteúdo.

## Briefing entregue ao redator

```jsonc
{
  "no": { "id": "d2.m1.t1", "nome": "Crase", "tipo": "topico", "disciplina": "Português" },
  "bloqueio": null,
  "titulo": "Crase — Português",
  "objetivo": "Dominar Crase no contexto de Português",
  "tempo_estimado_h": 2.5, "nivel_dificuldade": "medio",
  "nivel_do_estudante": { "nivel": "basico", "base": "domínio medido no tópico: basico", "confianca": "alta" },
  "estilo_de_aprendizagem": "visual",
  "pre_requisitos": [],
  "secoes": [ { "chave": "introducao", "etapa": "b. Contextualização", "instrucao": "..." } ],
  "diretrizes": ["Linguagem de nível basico...", "Apoiar as explicações em esquemas..."],
  "fontes": { "materiais_oficiais": ["Gramática oficial da banca"], "restricao": "Não contradizer os materiais oficiais..." },
  "coerencia": { "pode_pressupor": [], "nao_pode_pressupor": ["Conjuntos", "Probabilidade"], "regra": "..." },
  "proibicoes": ["não gerar exercícios (agente 09)", "não gerar flashcards (agente 10)", "..."],
  "proximo_conteudo_recomendado": { "id": "d1.m1.t2", "nome": "Probabilidade" }
}
```

`coerencia` é o que garante a progressão lógica na prática: o redator sabe o que
pode usar como base (concluído) e o que não pode (pendente).

## Seções

Oito, na ordem da spec. O objetivo (4a) é determinístico — vem do
`objetivo_de_aprendizagem` da Árvore Curricular.

| Chave | Etapa da spec |
| --- | --- |
| `introducao` | b. Contextualização |
| `desenvolvimento` | c. Conceitos fundamentais + d. Passo a passo |
| `exemplos` | e. Exemplos práticos |
| `aplicacoes` | f. Aplicações no mundo real |
| `erros_comuns` | g. Erros mais comuns |
| `dicas` | h. Dicas de memorização |
| `resumo` | i. Resumo |
| `pontos_chave` | Termos essenciais, prontos para os agentes 10 e 11 |

Seção fora dessa lista é **descartada** e registrada em `secoes_ignoradas` — se
o redator devolver "exercicios" ou "cronograma", eles não entram na aula.

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca ensinar conteúdo com pré-requisito pendente | portão no `gerar` (redator nem é chamado) e revalidação no `montar` (`AulaBloqueada`) |
| Nunca contradizer materiais oficiais | bibliografia e materiais obrigatórios entram no briefing como restrição explícita |
| Nunca usar informações sem fundamento | sem redator, seção fica `None`; nada é preenchido por código |
| Sempre adaptar a linguagem | nível derivado da medição do agente 03, com estilo do agente 01 virando diretriz de formato |
| Sempre manter progressão lógica | bloco `coerencia` separa o que pode e o que não pode ser pressuposto |
| Não criar exercícios, flashcards, simulados ou cronograma | `proibicoes` no briefing e descarte de seções fora da estrutura |

## Consumidores

08 · 09 · 10 · 11 · 13 · 16 · 24.
