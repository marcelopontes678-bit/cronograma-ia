from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password
from app.database import engine
from app.dependencies import get_db
from app.models.base import Base
from app.models.empresa import Empresa as EmpresaModel
from app.models.unidade import TipoUnidade, Unidade as UnidadeModel
from app.models.usuario import RoleUsuario, Usuario as UsuarioModel
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


@app.post("/_seed-inicial", tags=["sistema"], include_in_schema=False)
async def seed_inicial(token: str, db: AsyncSession = Depends(get_db)):
    """Endpoint temporario para popular a empresa/usuario demo em produção,
    onde não há shell disponível (plano free do Render) para rodar
    scripts/seed.py diretamente. Protegido pelo SECRET_KEY do ambiente
    para não ficar aberto a qualquer um. Remover após o primeiro uso."""
    if token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="token invalido")

    existente = await db.execute(select(EmpresaModel).where(EmpresaModel.cnpj == "11.222.333/0001-81"))
    if existente.scalar_one_or_none():
        return {"status": "ja_existe"}

    empresa_obj = EmpresaModel(
        nome="Marcenaria Demo Ltda",
        nome_fantasia="Demo Móveis",
        cnpj="11.222.333/0001-81",
        email="contato@demodemoveis.com.br",
        telefone="(11) 99999-0000",
        cidade="São Paulo",
        estado="SP",
        dias_funcionamento=["SEG", "TER", "QUA", "QUI", "SEX"],
    )
    db.add(empresa_obj)
    await db.flush()

    fabrica = UnidadeModel(
        empresa_id=empresa_obj.id,
        nome="Fábrica Principal",
        tipo=TipoUnidade.FABRICA,
        codigo="FAB-01",
        cidade="São Paulo",
        estado="SP",
        is_sede=True,
    )
    db.add(fabrica)
    await db.flush()

    admin = UsuarioModel(
        empresa_id=empresa_obj.id,
        unidade_id=fabrica.id,
        nome="Administrador",
        email="admin@demo.com",
        hashed_password=hash_password("admin123!"),
        role=RoleUsuario.ADMIN,
        must_change_password=True,
    )
    db.add(admin)
    await db.commit()

    return {"status": "criado", "email": admin.email}


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
