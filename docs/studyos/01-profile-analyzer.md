# Agente 01 — Profile Analyzer

Implementação: `backend/app/studyos/agentes/perfil.py`.

## Identidade

Conhece profundamente o estudante. Não cria cronogramas, não ensina, não gera
exercícios. Apenas constrói o perfil que os demais agentes consomem.

## Objetivo

Transformar informações do usuário em um **Perfil Cognitivo Estruturado**.

## Entradas

| Campo | Obrigatório | Formato aceito |
| --- | --- | --- |
| `nome` | não | texto |
| `idade` | sim | número |
| `escolaridade` | sim | texto |
| `objetivo` | sim | texto |
| `exame` (concurso/vestibular/curso) | não | texto |
| `profissao` | sim | texto |
| `rotina` | sim | texto |
| `horas_por_dia` | sim | número |
| `dias_por_semana` | sim | número |
| `data_prova` | não | `YYYY-MM-DD`, `DD/MM/YYYY` ou `date` |
| `experiencia_anterior` | sim | texto |
| `disciplinas_favoritas` | sim | lista ou texto separado por vírgula |
| `disciplinas_dificuldade` | sim | lista ou texto separado por vírgula |
| `preferencia_estudo` | sim | texto |
| `idioma` | não | texto (padrão `pt-BR`) |
| `restricoes` | não | lista ou texto |
| `necessidades_especiais` | não | lista ou texto |

Os campos podem vir soltos em `dados_usuario` ou aninhados em `dados_usuario.perfil`.

## Processamento

1. **Perfil acadêmico** — consolida nome, idade, escolaridade, profissão, objetivo, exame e idioma.
2. **Nível de conhecimento geral** — estimado pela escolaridade, com ajuste de ±1 nível conforme a experiência anterior declarada. Sai com `base` e `confianca`; é ponto de partida, não medição (quem mede é o agente 03).
3. **Tempo real disponível** — `horas_por_dia × dias_por_semana`, multiplicado pelo fator de efetividade.
4. **Riscos** — `prazo_curto`, `data_de_prova_invalida`, `sobrecarga`, `descontinuidade`, `rotina_conflitante`, `concentracao_de_lacunas`, `adaptacao_necessaria`. Cada risco vem com severidade e evidência.
5. **Pontos fortes** — disciplinas de domínio, disponibilidade alta, regularidade, experiência anterior, estilo definido.
6. **Pontos fracos** — disciplinas com dificuldade, disponibilidade baixa, ausência de experiência.
7. **Estilo de aprendizagem** — `visual`, `auditivo`, `leitura_escrita` ou `cinestesico`, por termos declarados. Sem preferência informada, sai `null` — não é inferido.
8. **Carga máxima diária** — `min(horas_por_dia × fator, teto cognitivo)`, convertida em blocos de foco/pausa.

## Constantes declaradas

| Constante | Valor | Uso |
| --- | --- | --- |
| `FATOR_EFETIVIDADE_PADRAO` | 0.85 | desconto de deslocamento, imprevisto e queda de atenção |
| `FATOR_EFETIVIDADE_ROTINA_INTENSA` | 0.70 | aplicado quando rotina/profissão indica alta ocupação |
| `TETO_COGNITIVO_DIARIO_H` | 6.0 | limite de estudo focado por dia |
| `BLOCO_FOCO_MIN` / `BLOCO_PAUSA_MIN` | 50 / 10 | ciclo usado para converter carga em blocos |
| `LIMIAR_RISCO_HORAS_TOTAIS` | 150.0 | abaixo disso, a disponibilidade até a prova vira risco alto |

Toda saída inclui `constantes_aplicadas`, para que nenhum número apareça sem origem.

## Saída

```jsonc
{
  "perfil_academico": { "nome": "...", "idade": 29.0, "escolaridade": "...", "objetivo": "...", "idioma": "pt-BR" },
  "nivel_conhecimento_geral": { "estimativa": "avancado", "base": "...", "confianca": "media" },
  "tempo_disponivel": { "horas_semanais_declaradas": 15.0, "horas_semanais_efetivas": 10.5, "fator_efetividade": 0.7, "calculavel": true },
  "prazo": { "data_prova": "2026-10-01", "dias_restantes": 63, "horas_totais_efetivas": 94.5 },
  "carga_maxima_diaria": { "horas": 2.1, "blocos": 2, "limitado_pelo_teto": false },
  "estilo_aprendizagem": { "predominante": "visual", "pontuacao": { "visual": 2 } },
  "riscos": [ { "risco": "prazo_curto", "severidade": "alta", "evidencia": "94.5h efetivas até a prova (63 dias)" } ],
  "pontos_fortes": ["..."],
  "pontos_fracos": ["..."],
  "lacunas": ["nivel_atual"],
  "completude": 0.91,
  "confiabilidade": "alta",
  "constantes_aplicadas": { "...": "..." }
}
```

## Regra de ouro

Campo não informado nunca vira valor assumido: entra em `lacunas`, derruba a
`completude` e reduz a `confiabilidade`. O agente 24 transforma cada lacuna em
alerta na resposta final.
