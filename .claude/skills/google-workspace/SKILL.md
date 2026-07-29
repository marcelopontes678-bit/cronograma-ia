---
name: google-workspace
description: Conecta e opera o Google Workspace (Gmail, Drive, Calendar, Docs, Sheets, Slides, Forms, Tasks, Chat, Contacts) via o MCP server workspace-mcp. Use quando o usuário pedir para ler/enviar e-mail, buscar ou criar arquivos no Drive, criar/listar eventos de agenda, ler ou editar Docs/Sheets/Slides, gerenciar tarefas ou contatos do Google — ou quando pedir para instalar, configurar, autenticar ou diagnosticar a integração com o Google Workspace.
---

# Google Workspace MCP

Integração deste repositório com o servidor MCP
[`taylorwilsdon/google_workspace_mcp`](https://github.com/taylorwilsdon/google_workspace_mcp),
distribuído no PyPI como o pacote `workspace-mcp`.

A configuração do servidor mora em `.mcp.json` na raiz do repositório. O Claude Code
lê esse arquivo **na inicialização da sessão** — depois de alterá-lo, reinicie a
sessão para que as ferramentas apareçam.

## Fluxo de decisão

| Situação | O que fazer |
|---|---|
| As ferramentas `mcp__google_workspace__*` já estão disponíveis | Use-as direto. Pule para "Usando as ferramentas". |
| O usuário quer instalar/configurar pela primeira vez | Siga "Instalação" abaixo. |
| Ferramenta retorna erro de autenticação / pede login | Siga "Autenticação". |
| Servidor não sobe ou não aparece na sessão | Siga "Diagnóstico". |

## Instalação

O servidor roda via `uvx`, sem instalação permanente. Só é preciso ter o `uv`:

```bash
command -v uvx || curl -LsSf https://astral.sh/uv/install.sh | sh
uvx workspace-mcp --help   # baixa o pacote e valida o ambiente
```

Depois, exporte as credenciais OAuth do Google (veja
`references/setup-google-cloud.md` para obtê-las) no shell que inicia o Claude Code:

```bash
export GOOGLE_OAUTH_CLIENT_ID="....apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="GOCSPX-..."
export USER_GOOGLE_EMAIL="voce@exemplo.com"   # opcional, evita repetir o e-mail
```

Para persistir, coloque os `export` no `~/.bashrc` / `~/.zshrc` ou em um arquivo de
ambiente carregado antes do Claude Code.

**Nunca** escreva client id/secret dentro de `.mcp.json`, do código ou de um commit.
O `.mcp.json` deste repositório usa expansão `${VAR}` justamente para isso.

Reinicie a sessão do Claude Code e aprove o servidor MCP do projeto quando solicitado.

## Autenticação

O `workspace-mcp` usa OAuth 2.0 com refresh automático. Na primeira chamada de
qualquer ferramenta, ele devolve uma URL de autorização do Google:

1. Abra a URL no navegador e conceda os escopos.
2. O Google redireciona para `http://localhost:8000/oauth2callback`.
3. O token fica em `~/.google_workspace_mcp/credentials/` (permissão `0600`) e é
   renovado sozinho depois disso.

Requisitos que costumam falhar:

- O redirect URI `http://localhost:8000/oauth2callback` precisa estar cadastrado
  **exatamente assim** no cliente OAuth do Google Cloud.
- `OAUTHLIB_INSECURE_TRANSPORT=1` é obrigatório porque o redirect é `http://`
  (localhost). Já está no `.mcp.json`.
- Se a porta 8000 estiver ocupada, defina `WORKSPACE_MCP_PORT` **e** cadastre o
  novo redirect URI no Google Cloud.
- Se a tela de consentimento estiver em modo "Testing", adicione o e-mail do
  usuário em "Test users", senão o Google bloqueia o login.

## Usando as ferramentas

As ferramentas chegam como `mcp__google_workspace__<nome>`. A maioria aceita
`user_google_email` — passe o e-mail do usuário, ou defina `USER_GOOGLE_EMAIL` para
omiti-lo.

Regras de uso:

- **Leia antes de escrever.** Busque/liste para confirmar o alvo (ID de arquivo,
  ID de evento, thread de e-mail) antes de qualquer operação destrutiva ou de envio.
- **Confirme envios com o usuário.** Enviar e-mail, criar evento que convida
  terceiros, compartilhar arquivo do Drive e postar no Chat são ações externas e
  irreversíveis — peça confirmação antes, mesmo que a intenção pareça clara.
- **IDs, não nomes.** Docs, Sheets, Slides e Drive operam por file ID. Resolva o
  nome para ID com a busca do Drive primeiro.
- **Peça o mínimo.** Se a tarefa é só leitura, prefira rodar o servidor com
  `--read-only` ou `--permissions gmail:readonly drive:readonly`.

Catálogo de serviços e ferramentas: `references/tools.md`.

## Ajustando o escopo do servidor

Edite os `args` em `.mcp.json`:

```jsonc
// só os serviços usados por este projeto (menos ferramentas = menos contexto)
"args": ["workspace-mcp", "--single-user", "--tools", "calendar", "tasks", "gmail"]

// somente leitura
"args": ["workspace-mcp", "--single-user", "--tool-tier", "core", "--read-only"]

// permissões granulares por serviço
"args": ["workspace-mcp", "--single-user", "--permissions", "gmail:send", "drive:readonly"]
```

Tiers: `core` (essencial, padrão daqui), `extended` (core + gestão),
`complete` (tudo). `--permissions` é mutuamente exclusivo com `--read-only` e `--tools`.

## Diagnóstico

```bash
# o servidor sobe?
GOOGLE_OAUTH_CLIENT_ID=... GOOGLE_OAUTH_CLIENT_SECRET=... uvx workspace-mcp --help

# as variáveis estão no ambiente que iniciou o Claude Code?
env | grep -E 'GOOGLE_OAUTH|USER_GOOGLE_EMAIL'

# o token foi gravado?
ls -l ~/.google_workspace_mcp/credentials/

# forçar novo login: remova o token do usuário e chame qualquer ferramenta de novo
```

| Sintoma | Causa provável |
|---|---|
| Servidor não aparece na sessão | `.mcp.json` alterado sem reiniciar, ou servidor do projeto não aprovado |
| `redirect_uri_mismatch` | URI não cadastrado no cliente OAuth, ou porta diferente de 8000 |
| `access_denied` no consentimento | E-mail fora dos "Test users" da tela de consentimento |
| `insufficient authentication scopes` | API não habilitada no projeto, ou escopo reduzido por `--read-only` |
| `API has not been used in project ...` | Falta habilitar a API do serviço no Google Cloud |

Detalhes de cada API e da tela de consentimento: `references/setup-google-cloud.md`.
