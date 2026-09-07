from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine
from app.models.base import Base
from app.routers import auth, comercial, empresa, orcamento, producao, projeto, unidade, usuario


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Desenvolvimento: criar tabelas se não existirem
    # Produção: usar somente Alembic
    if settings.ENVIRONMENT == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="SmartFactory Móveis AI",
    version="0.1.0",
    description="ERP vertical para marcenarias e fábricas de móveis planejados",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(empresa.router, prefix=PREFIX)
app.include_router(unidade.router, prefix=PREFIX)
app.include_router(usuario.router, prefix=PREFIX)
app.include_router(projeto.router, prefix=PREFIX)
app.include_router(orcamento.router, prefix=PREFIX)
app.include_router(comercial.router, prefix=PREFIX)
app.include_router(producao.router, prefix=PREFIX)


@app.get("/health", tags=["sistema"])
async def health():
    """Alem do status generico, checa as dependencias do modulo de
    orcamento de marcenaria (nao bloqueiam o resto do ERP no startup --
    e um bounded context especifico, um deploy sem ANTHROPIC_API_KEY
    ainda serve empresas/usuarios/projetos normalmente, so o modulo de
    orcamento fica indisponivel)."""
    checks = {
        "anthropic_api_key_configurada": bool(settings.ANTHROPIC_API_KEY),
        "tabela_precos_encontrada": Path(settings.ORCAMENTO_TABELA_PRECOS).exists(),
        "config_precificacao_encontrada": Path(settings.ORCAMENTO_CONFIG_PRECIFICACAO).exists(),
    }
    status_geral = "ok" if all(checks.values()) else "degradado"
    return JSONResponse(
        status_code=200 if status_geral == "ok" else 503,
        content={"status": status_geral, "version": "0.1.0", "checks": checks},
    )
