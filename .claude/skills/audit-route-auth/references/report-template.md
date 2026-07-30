# Auditoria de autenticação nas rotas

**Diretório:** `<caminho>` · **Data:** `<YYYY-MM-DD>` · **Commit:** `<sha curto>`

## Resumo

`<N>` achados confirmados em `<M>` arquivos: `<A>` high, `<B>` medium, `<C>` low.
`<K>` candidatos foram descartados pelo verificador (apêndice).

## Cobertura

| | |
|---|---|
| Arquivos de rota encontrados | `<total>` |
| Analisados | `<n>` (teto: `<max>`) |
| Pulados pelo teto | `<lista nominal, ou "nenhum">` |

## Convenções de auth do projeto

- Identidade: `<primitiva>` em `<arquivo:linha>`
- Autorização: `<primitiva>` em `<arquivo:linha>`
- Proteção global: `<middleware / dependencies= / nenhuma>`
- Públicas por design: `<lista>`

## Achados confirmados

| # | Severidade | Rota | Local | Problema |
|---|---|---|---|---|
| 1 | high | `DELETE /projetos/{id}` | `arquivo:linha` | `<uma linha>` |

### 1. `<título>` — `<severidade>`

- **Rota:** `<método e path>`
- **Local:** `arquivo:linha` (handler `<nome>`)
- **Problema:** `<o que falta>`
- **Impacto:** `<o que um chamador não autenticado consegue fazer>`
- **Veredito do verificador:** `CONFIRMED` / `RECLASSIFIED` — `<motivo, citando as camadas checadas>`
- **Correção sugerida:** `<mudança mínima>`

## Apêndice — Falsos positivos descartados

| Candidato | Local | Motivo da rejeição |
|---|---|---|
| `<claim>` | `arquivo:linha` | `<proteção encontrada pelo verificador>` |
