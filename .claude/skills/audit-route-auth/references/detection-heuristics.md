# Heurísticas de detecção por framework

Um handler está **protegido** se a identidade do chamador é verificada antes da lógica de negócio — no próprio handler ou em qualquer camada acima dele. Antes de marcar algo como ausente, verifique as três camadas: handler → router → app.

## FastAPI (esta base de código)

Rotas em `backend/app/routers/`, primitivas em `backend/app/dependencies.py`.

Protegido quando:

```python
current_user: Usuario = Depends(get_current_user)                          # identidade
current_user: Usuario = Depends(require_role(RoleUsuario.ADMIN))           # identidade + papel
```

Também protegido, mesmo sem nada na assinatura do handler:

```python
router = APIRouter(prefix="/x", dependencies=[Depends(get_current_user)])  # nível de router
app.include_router(x.router, dependencies=[Depends(get_current_user)])     # nível de app
```

Suspeito de estar desprotegido:

- Assinatura só com `db: AsyncSession = Depends(get_db)` e parâmetros de path/body.
- `current_user` declarado mas nunca usado **e** o service não recebe `current_user` — a identidade é verificada, mas o escopo do dado talvez não. Isso normalmente é `low`/`medium`, não `high`: a auth existe.
- `require_role` mais permissivo que rotas equivalentes no mesmo arquivo (ex.: `DELETE` aberto a `GERENTE` quando `PUT` exige `ADMIN`) → inconsistência de autorização.
- Rota aninhada em `/empresas/{empresa_id}/...` cujo service não valida que `current_user` pertence àquela empresa → risco de acesso cross-tenant.

Público por design: `POST /auth/login`, `POST /auth/register`, refresh de token, `GET /health`.

## Express / Fastify

Protegido: `router.get('/x', requireAuth, handler)`, `router.use(requireAuth)` antes das rotas no mesmo arquivo, ou `app.use('/api', requireAuth)` no bootstrap.

Atenção à **ordem**: um `router.use(requireAuth)` declarado *depois* de uma rota não protege essa rota. Isso é achado real.

## NestJS

Protegido: `@UseGuards(AuthGuard)` no handler ou na classe do controller; guard global via `APP_GUARD`. Com guard global, `@Public()` / `@SkipAuth()` é o que abre a rota — procure por esse decorator para achar as exceções.

## Next.js (App Router / route handlers)

Protegido: checagem de sessão dentro do handler (`await auth()`, `getServerSession`, validação de token) com early-return `401`. `middleware.ts` com `matcher` cobrindo o path também protege — leia o matcher antes de concluir.

Cuidado: `layout.tsx` protegendo a UI **não** protege um route handler em `app/api/**`.

## Regras gerais anti-falso-positivo

1. Auth ausente no arquivo ≠ auth ausente na aplicação. Sempre suba até o bootstrap (`main.py`, `app.ts`, `middleware.ts`).
2. Um wrapper com nome diferente (`current_user_dep`, `authed`) pode ser auth. Siga a definição em vez de casar por nome.
3. Endpoints deliberadamente públicos não são achados. Webhook com verificação de assinatura conta como autenticado.
4. Sem evidência de linha, não há achado.
