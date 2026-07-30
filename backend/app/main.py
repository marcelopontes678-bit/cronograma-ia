from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models.base import Base
from app.routers import auth, empresa, projeto, studyos, unidade, usuario


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
app.include_router(studyos.router, prefix=PREFIX)


@app.get("/health", tags=["sistema"])
async def health():
    return {"status": "ok", "version": "0.1.0"}
