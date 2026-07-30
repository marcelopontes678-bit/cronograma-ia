---
name: audit-route-auth
description: Audita arquivos de rotas em busca de verificações de autenticação/autorização ausentes, usando um agente auditor por arquivo e um verificador independente que confirma cada achado antes do relatório final. Use quando o usuário pedir auditoria de auth nas rotas, revisão de endpoints desprotegidos, ou invocar /audit-route-auth.
---

# Auditoria de autenticação nas rotas

Workflow de 5 fases: **descobrir → mapear convenções → auditar em paralelo (1 agente por arquivo) → verificar de forma independente → relatar**.

A regra central: **nenhum achado entra no relatório final sem passar pelo verificador.** O auditor propõe; o verificador decide.

## Argumentos

`/audit-route-auth [caminho] [--max N]`

- `caminho` — diretório de rotas. Default: `src/routes`.
- `--max N` — teto de arquivos analisados. Default: **20**. Nunca exceda esse teto sem o usuário pedir.

## Fase 1 — Descoberta

1. Se o `caminho` existir, use-o. Se não existir, descubra os diretórios de rotas reais do repositório antes de desistir:

   ```bash
   find . \( -name node_modules -o -name .git -o -name dist -o -name build -o -name .next -o -name venv -o -name __pycache__ \) -prune \
     -o -type d \( -name routes -o -name routers -o -name controllers -o -name endpoints -o -name api \) -print
   ```

   Nesta base de código (`cronograma-ia`) as rotas ficam em `backend/app/routers/`.

2. Liste os arquivos de rota do diretório escolhido, em ordem alfabética (determinística), excluindo `__init__.py`, `index.*` que só reexportam, arquivos de teste e `*.d.ts`.

3. Aplique o teto: se houver mais de `N` arquivos, analise os `N` primeiros e **registre explicitamente os que ficaram de fora** — isso vai para a seção "Cobertura" do relatório. Nunca finja cobertura total.

4. Se a lista final estiver vazia, pare e informe o usuário. Não invente arquivos.

## Fase 2 — Mapa de convenções de auth (obrigatório, antes de qualquer agente)

Sem esta fase os auditores geram falsos positivos em massa. Leia você mesmo (não delegue) as primitivas de auth do projeto e monte um **mapa de convenções** curto:

- Onde está a checagem de identidade? (ex.: `backend/app/dependencies.py` → `get_current_user`)
- Onde está a checagem de papel/permissão? (ex.: `require_role(...)`)
- Existe proteção aplicada *fora* do arquivo de rota — middleware global, `dependencies=[...]` no `APIRouter`/`include_router`, guard de app, `beforeEach`? Rotas cobertas por proteção global **não são achados**.
- Quais rotas são legitimamente públicas por design? (login, registro, refresh token, healthcheck, webhooks com verificação de assinatura própria)

Consulte `references/detection-heuristics.md` para os padrões por framework.

Registre o mapa em `/tmp/route-auth-audit/conventions.md`. Ele é passado **na íntegra** para todo auditor e todo verificador — os dois lados precisam julgar contra as mesmas convenções.

## Fase 3 — Auditoria em paralelo (um agente por arquivo)

Dispare **um agente `route-auth-auditor` por arquivo**, todos na mesma mensagem para rodarem em paralelo. Um agente por arquivo, sem agrupar — o isolamento é o que mantém a análise focada e as evidências rastreáveis.

Cada prompt de auditor contém: o caminho absoluto do arquivo, o mapa de convenções inline, e a instrução de retornar **só** o JSON do schema abaixo.

```json
{
  "file": "backend/app/routers/projeto.py",
  "findings": [
    {
      "id": "projeto-1",
      "line": 42,
      "handler": "delete_projeto",
      "http": "DELETE /projetos/{projeto_id}",
      "claim": "Handler não declara nenhuma dependência de autenticação; nenhum get_current_user ou require_role na assinatura.",
      "impact": "Qualquer requisição não autenticada pode excluir um projeto de qualquer empresa.",
      "severity": "high",
      "evidence": "linhas 38-46"
    }
  ]
}
```

`severity`: `high` (escrita/destrutiva ou dado de outro tenant sem auth) · `medium` (leitura de dado sensível sem auth) · `low` (auth presente mas autorização mais fraca que rotas equivalentes).

Se um auditor retornar `findings: []`, registre e siga. Nem todo arquivo tem problema.

## Fase 4 — Verificação independente

Para **cada** achado (não por arquivo — por achado), dispare um agente `route-auth-verifier`. Pode paralelizar, agrupando por arquivo se o volume for grande, mas cada achado precisa de um veredito próprio.

A independência é o ponto da fase, então:

- Passe **apenas** `file`, `line`, `handler`, `http` e `claim`. **Não** passe `impact`, `severity` nem `evidence` — o verificador tem que reconstruir isso do código, não herdar a conclusão do auditor.
- O verificador relê o arquivo do zero e checa também as camadas *externas* (middleware, `dependencies=` no router, `include_router`) antes de confirmar.
- Se o mesmo achado foi levantado por dois auditores, verifique uma vez e deduplique.

Veredito de cada verificador:

```json
{
  "id": "projeto-1",
  "verdict": "CONFIRMED",
  "reason": "Assinatura em backend/app/routers/projeto.py:38-46 tem apenas db=Depends(get_db). O APIRouter (linha 14) não define dependencies=, e main.py:42 inclui o router sem dependências. Nenhuma camada protege este handler.",
  "corrected_severity": "high"
}
```

`verdict`: `CONFIRMED` (o problema existe) · `REJECTED` (falso positivo — explique a proteção encontrada) · `RECLASSIFIED` (existe, mas com severidade ou natureza diferente; preencha `corrected_severity`).

Use a severidade do verificador quando ela divergir da do auditor. Em `REJECTED`, o motivo é obrigatório e vai para o apêndice do relatório.

## Fase 5 — Relatório final

Monte o relatório com `references/report-template.md`, salvando em `/tmp/route-auth-audit/report.md` (ou onde o usuário pedir).

Regras não negociáveis:

- **Só `CONFIRMED` e `RECLASSIFIED` entram na tabela de achados.** `REJECTED` vai para o apêndice "Falsos positivos descartados", com o motivo.
- A seção **Cobertura** declara: arquivos encontrados, analisados, e — nominalmente — os pulados pelo teto.
- Todo achado cita `arquivo:linha`.
- Se nada for confirmado, diga isso claramente. Um relatório limpo é um resultado válido; não promova achados fracos para preencher espaço.
- Não corrija o código nesta execução. A auditoria entrega o relatório; a correção é um pedido separado.
