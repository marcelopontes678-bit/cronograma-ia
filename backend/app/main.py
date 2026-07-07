from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models.base import Base
from app.routers import auth, empresa, projeto, unidade, usuario

IS_PRODUCTION = settings.ENVIRONMENT == "production"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Desenvolvimento: criar tabelas se não existirem
    # Produção: usar somente Alembic
    if not IS_PRODUCTION:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="SmartFactory Móveis AI",
    version="0.1.0",
    description="ERP vertical para marcenarias e fábricas de móveis planejados",
    lifespan=lifespan,
    # Swagger/OpenAPI desligados em produção
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    if IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )
    return response


PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(empresa.router, prefix=PREFIX)
app.include_router(unidade.router, prefix=PREFIX)
app.include_router(usuario.router, prefix=PREFIX)
app.include_router(projeto.router, prefix=PREFIX)


@app.get("/health", tags=["sistema"])
async def health():
    return {"status": "ok", "version": "0.1.0"}
