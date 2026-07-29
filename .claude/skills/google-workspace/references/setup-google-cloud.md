# Setup do Google Cloud para o workspace-mcp

Passo a passo para obter `GOOGLE_OAUTH_CLIENT_ID` e `GOOGLE_OAUTH_CLIENT_SECRET`.

## 1. Projeto

1. Acesse https://console.cloud.google.com/
2. Crie um projeto (ou selecione um existente).

## 2. Habilitar as APIs

Em **APIs & Services → Library**, habilite apenas as APIs dos serviços que você vai
usar. Cada ferramenta falha com `API has not been used in project ...` se a API dela
estiver desabilitada.

| Serviço | API a habilitar |
|---|---|
| Gmail | Gmail API |
| Drive | Google Drive API |
| Calendar | Google Calendar API |
| Docs | Google Docs API |
| Sheets | Google Sheets API |
| Slides | Google Slides API |
| Forms | Google Forms API |
| Tasks | Google Tasks API |
| Chat | Google Chat API |
| Contacts | People API |
| Custom Search | Custom Search API |
| Apps Script | Apps Script API |

## 3. Tela de consentimento OAuth

Em **APIs & Services → OAuth consent screen**:

- **User type**: `External` para contas `@gmail.com`; `Internal` se for Google Workspace
  da organização (aí não há aprovação de app nem lista de testadores).
- Preencha nome do app, e-mail de suporte e e-mail do desenvolvedor.
- Com o app em **Testing**, adicione cada conta que vai usar em **Test users**.
  Sem isso o login retorna `access_denied`.
- Os escopos não precisam ser listados aqui: o servidor os solicita em tempo de
  execução conforme o tier/permissões configurados.

## 4. Credenciais OAuth

Em **APIs & Services → Credentials → Create Credentials → OAuth client ID**:

- **Application type**: `Web application` (recomendado — permite cadastrar o redirect
  URI explicitamente). `Desktop app` também funciona, como cliente público com PKCE.
- **Authorized redirect URIs**: adicione exatamente

  ```
  http://localhost:8000/oauth2callback
  ```

  Se você mudar `WORKSPACE_MCP_PORT`, cadastre o URI com a nova porta.
- Copie o **Client ID** e o **Client secret**.

Em vez das variáveis de ambiente, também é possível baixar o JSON e apontar
`GOOGLE_CLIENT_SECRET_PATH` para ele — mas nesse caso o arquivo **não** pode ser
commitado.

## 5. Chat (apenas se for usar as ferramentas de Chat)

Em **Google Chat API → Configuration**, preencha nome do app, URL do avatar e
descrição, e salve. Sem essa configuração as ferramentas de Chat falham.

## Variáveis de ambiente

Obrigatórias:

| Variável | Uso |
|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | Client ID do OAuth |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Client secret (omita em cliente público com PKCE) |
| `OAUTHLIB_INSECURE_TRANSPORT=1` | Necessário porque o redirect é `http://localhost` |

Úteis:

| Variável | Uso |
|---|---|
| `USER_GOOGLE_EMAIL` | E-mail padrão; dispensa passar `user_google_email` em cada chamada |
| `GOOGLE_OAUTH_REDIRECT_URI` | Sobrescreve o redirect URI |
| `GOOGLE_CLIENT_SECRET_PATH` | Caminho para um `client_secret.json` |
| `WORKSPACE_MCP_PORT` | Porta do servidor (padrão `8000`) |
| `WORKSPACE_MCP_HOST` | Host de bind |
| `WORKSPACE_EXTERNAL_URL` | URL externa quando atrás de proxy reverso |
| `WORKSPACE_MCP_CREDENTIALS_DIR` | Onde gravar os tokens |
| `WORKSPACE_ATTACHMENT_DIR` | Onde salvar anexos baixados |
| `WORKSPACE_MCP_TOOLS` / `WORKSPACE_MCP_TOOL_TIER` | Equivalentes a `--tools` / `--tool-tier` |
| `WORKSPACE_MCP_READ_ONLY` | Equivalente a `--read-only` |
| `WORKSPACE_MCP_PERMISSIONS` | Equivalente a `--permissions` |
| `GOOGLE_PSE_API_KEY` / `GOOGLE_PSE_ENGINE_ID` | Credenciais do Custom Search |
| `MCP_ENABLE_OAUTH21` | Modo OAuth 2.1 multiusuário (deploy HTTP) |

## Onde ficam os dados no disco

| Conteúdo | Caminho padrão |
|---|---|
| Tokens OAuth | `~/.google_workspace_mcp/credentials/` (`0600`) |
| Logs | `~/.google_workspace_mcp/logs/` |
| Anexos baixados | `~/.workspace-mcp/attachments/` |

Nenhum desses caminhos fica dentro do repositório. Se você mudar
`WORKSPACE_MCP_CREDENTIALS_DIR` para algo dentro do projeto, adicione ao `.gitignore`
— são credenciais de longa duração.

## Modo HTTP (opcional)

Para rodar como servidor HTTP em vez de stdio:

```bash
export MCP_ENABLE_OAUTH21=true
uvx workspace-mcp --transport streamable-http
```

E aponte o cliente para `http://localhost:8000/mcp/`.
