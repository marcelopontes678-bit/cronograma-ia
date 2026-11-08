# Pauta: planejador de conteúdo com IA

MVP de SaaS para criadores e pequenas empresas: cadastre a marca (nicho, público, tom de voz, pilares) e receba um calendário editorial de 1 a 4 semanas. Cada post vem com **gancho, roteiro, legenda, hashtags e CTA**. Depois é possível editar, pedir ajustes à IA, acompanhar o status (ideia → publicado) e exportar para CSV.

Stack: **FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL · Claude (saída estruturada) · JS puro**.

A arquitetura completa (sistema, banco, endpoints, interface e plano de crescimento) está em [docs/ARQUITETURA.md](docs/ARQUITETURA.md).

## Rodar local

```bash
cd planejador-conteudo
pip install -r requirements-dev.txt
export ANTHROPIC_API_KEY=sk-ant-...      # sem ela o app abre, mas a geração dá erro
alembic upgrade head                     # cria pauta.db (SQLite)
uvicorn pauta.main:app --reload
```

Abra http://localhost:8000 (interface) ou http://localhost:8000/api/docs (API).

Com Postgres, igual à produção:

```bash
ANTHROPIC_API_KEY=sk-ant-... docker compose up --build
```

## Testes

```bash
pytest                                                          # SQLite
TEST_DATABASE_URL=postgresql+psycopg://user:senha@host/db pytest  # Postgres (banco vazio)
```

## Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./pauta.db` | Aceita `postgres://...` (formato do Render) |
| `SECRET_KEY` | aleatória em dev | Assina os logins. **Obrigatória em produção** (32+ caracteres) |
| `ANTHROPIC_API_KEY` | — | Chave da API do Claude |
| `PAUTA_MODELO` | `claude-opus-5-5` | Modelo usado na geração |
| `PAUTA_LIMITE_PLANOS` | `10` | Planos por mês no plano grátis |
| `AMBIENTE` | — | `producao` liga as checagens de segurança |
| `CORS_ORIGINS` | — | Só se outro domínio for consumir a API |
| `WEB_CONCURRENCY` | `2` | Workers do uvicorn no container |

## Deploy no Render

O `render.yaml` da raiz do repositório já tem o serviço `pauta` e o banco `pauta-db`. No painel do Render, sincronize o Blueprint e preencha `ANTHROPIC_API_KEY`. `SECRET_KEY` é gerada sozinha e as migrações rodam a cada deploy.

> O plano grátis de Postgres do Render tem limites (quantidade de bancos e expiração). Confira no painel. Se já houver um banco grátis em uso, troque `plan: free` do `pauta-db` por um plano pago.
