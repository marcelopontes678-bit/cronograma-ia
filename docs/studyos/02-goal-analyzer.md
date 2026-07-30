# Agente 02 — Goal Analyzer

Implementação: `backend/app/studyos/agentes/objetivo.py`.

## Identidade

Compreende exatamente o objetivo do estudante e o transforma em um plano
estruturado de metas. Não ensina, não cria cronogramas, não gera conteúdo.

## Objetivo

Converter o objetivo informado em um **Mapa Estratégico de Aprendizagem**.

## Entradas

| Campo | Obrigatório | Origem |
| --- | --- | --- |
| Perfil Cognitivo Estruturado | sim | saída do agente 01 |
| `objetivo` | sim | usuário |
| `exame` (concurso/vestibular/certificação/curso) | sim | usuário |
| `data_prova` | sim | usuário |
| `edital` | sim | usuário |
| `materias` | sim | usuário |
| `objetivos_secundarios` | não | usuário |
| `categoria` | não | usuário |
| `bibliografia` | não | usuário |
| `materiais_obrigatorios` | não | usuário |
| `nota_corte` | não | usuário |

O `edital` aceita quatro formatos: dicionário `{disciplina: [tópicos]}`,
dicionário `{disciplina: {topicos, peso, questoes}}`, lista de dicionários com
`nome`/`disciplina` e lista de nomes. `materias` segue os mesmos formatos.

## Processamento

1. **Objetivo principal** — texto declarado, sem reescrita.
2. **Objetivos secundários** — do campo próprio, ou separados do objetivo por marcadores explícitos (`;`, "e também", "além de", "e depois").
3. **Categoria** — `concurso_publico`, `enem`, `vestibular`, `faculdade`, `idiomas`, `certificacao`, `desenvolvimento_profissional` ou `aprendizado_livre`. O objetivo declarado é a fonte primária; o texto da solicitação só decide quando o objetivo não basta. Sem termos reconhecidos, sai `null`.
4. **Disciplinas** — por precedência: edital → matérias informadas → disciplinas declaradas no perfil. Cada uma carrega sua `origem`.
5. **Prioridade** — score por peso no edital (0–3), dificuldade declarada (+2), domínio declarado (−1) e volume de tópicos (0–2). `alta` ≥ 4, `media` ≥ 2, senão `baixa`. Cada prioridade lista os `fatores` que a produziram.
6. **Competências necessárias** — catálogo por categoria, marcado com `origem: catalogo_por_categoria`.
7. **Carga total estimada** — `total_de_tópicos × 2.5h`; sem tópicos detalhados, `disciplinas × 30h` com `precisao: baixa`.
8. **Tempo disponível** — vem do agente 01 (horas semanais efetivas e horas totais até a prova).
9. **Restrições de prazo** — `viavel`, `apertado`, `inviavel_no_ritmo_atual` ou `indeterminada`, com déficit em horas e horas semanais necessárias × disponíveis.
10. **Nível mínimo por disciplina** — `alta → avancado`, `media → intermediario`, `baixa → basico`.
11. **Dependências externas** — edital, bibliografia e materiais obrigatórios, cada um com `status` e `acao`.

## Constantes declaradas

| Constante | Valor | Uso |
| --- | --- | --- |
| `HORAS_POR_TOPICO` | 2.5 | primeira passada + fixação por tópico |
| `HORAS_POR_DISCIPLINA_SEM_DETALHE` | 30.0 | disciplina conhecida sem tópicos |
| `MARGEM_VIABILIDADE` | 1.0 | horas disponíveis ≥ carga → viável |
| `MARGEM_APERTADO` | 0.75 | entre 75% e 100% da carga → apertado |

## Saída

```jsonc
{
  "objetivo_principal": "Passar no concurso do ICMS-SP",
  "objetivos_secundarios": ["melhorar redação"],
  "categoria_objetivo": { "categoria": "concurso_publico", "base": "...", "termos": ["concurso", "icms"] },
  "disciplinas": [ { "nome": "Português", "topicos": ["..."], "peso": null, "questoes": 20.0, "origem": "edital" } ],
  "cobertura_das_disciplinas": "edital",
  "competencias_necessarias": [ { "competencia": "interpretação de texto", "origem": "catalogo_por_categoria" } ],
  "prioridade_disciplinas": [ { "disciplina": "Português", "prioridade": "alta", "score": 4.0, "fatores": ["peso no edital (20.0)", "4 tópico(s)"], "nivel_minimo_esperado": "avancado" } ],
  "estimativa_carga_estudo": { "horas_estimadas": 22.5, "total_topicos": 9, "base": "9 tópicos × 2.5h", "precisao": "alta" },
  "tempo_disponivel": { "horas_semanais_efetivas": 10.5, "horas_totais_ate_a_prova": 94.5, "origem": "agente 01 Profile Analyzer" },
  "prazo_final": { "data": "2026-10-01", "dias_restantes": 273, "definido": true },
  "restricoes_de_prazo": { "viabilidade": "viavel", "deficit_horas": 0.0, "horas_semanais_necessarias": 2.5 },
  "requisitos_obrigatorios": [ { "requisito": "edital", "status": "disponivel", "acao": "..." } ],
  "criterios_sucesso": ["Atingir pontuação igual ou superior a 70", "..."],
  "consumido_por": ["04", "05", "06", "16", "21", "22"],
  "observacoes": [], "lacunas": [], "completude": 1.0, "confiabilidade": "alta"
}
```

## Regras codificadas

| Regra da spec | Como é garantida |
| --- | --- |
| Nunca inventar disciplinas não relacionadas ao objetivo | disciplinas só saem de edital, matérias ou perfil; cada uma leva `origem`. Sem fonte, a lista sai vazia com observação explícita |
| Com edital, usá-lo como referência principal | `_disciplinas` testa o edital primeiro e ignora `materias` quando ele existe |
| Sem edital, informar que será preciso matriz curricular equivalente | entra em `observacoes` e no requisito `edital: ausente` |
| Nunca criar cronograma, ensinar ou gerar exercícios | a saída não tem datas, aulas nem questões — só metas, prioridades e critérios |

## Consumidores

04 Curriculum Builder · 05 Dependency Mapper · 06 Roadmap Builder ·
16 Exam Simulator · 21 Performance Analyzer · 22 Forecast Agent.
