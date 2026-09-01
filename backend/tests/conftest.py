import os

# Precisa ser setado ANTES de qualquer import de app.* -- Settings le
# DATABASE_URL na importacao do modulo (os.environ tem prioridade sobre
# .env no pydantic-settings), entao isso aponta app.database.engine e
# tudo que depende dele pro banco de teste, nunca o de desenvolvimento.
os.environ["DATABASE_URL"] = "postgresql+asyncpg://smartfactory:smartfactory@localhost:5432/smartfactory_test"

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.core.security import hash_password
from app.dependencies import get_db
from app.main import app
from app.models.base import Base
from app.models.empresa import Empresa
from app.models.usuario import RoleUsuario, Usuario

# Engine proprio dos testes, com NullPool: nunca mantem conexao asyncpg viva
# entre checkouts, evitando "attached to a different loop" quando o
# event_loop de sessao do pytest-asyncio troca entre fixtures (o engine
# global de app.database.py mantem pool persistente, pensado pra vida do
# processo do uvicorn, nao pro ciclo de vida de testes).
test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

# Ordem de truncagem respeita FKs (filhas antes das tabelas referenciadas).
_TABELAS_EM_ORDEM_DE_LIMPEZA = [
    "regras_aprendidas",
    "orcamento_jobs",
    "preferencias_globais",
    "refresh_tokens",
    "projetos",
    "usuarios",
    "unidades",
    "empresas",
]


@pytest.fixture(scope="session")
def event_loop():
    """app_engine (async, com pool de conexoes) e importado uma unica vez
    no processo -- precisa que TODOS os testes rodem na mesma event loop,
    senao o pool tenta reusar conexao asyncpg criada numa loop diferente
    ('attached to a different loop')."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _criar_schema():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _limpar_tabelas():
    """Roda depois de cada teste -- garante isolamento entre testes sem
    depender de rollback de transacao (mais simples de acertar com
    AsyncSession + greenlet do que savepoints aninhados)."""
    yield
    async with test_engine.begin() as conn:
        for tabela in _TABELAS_EM_ORDEM_DE_LIMPEZA:
            await conn.execute(text(f"DELETE FROM {tabela}"))


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _criar_empresa_com_admin(
    db_session: AsyncSession, nome_empresa: str, email_admin: str, senha: str
) -> tuple[Empresa, Usuario]:
    empresa = Empresa(
        nome=nome_empresa,
        cnpj=f"{uuid.uuid4().int % 10**14:014d}",
        email=f"contato@{nome_empresa.lower().replace(' ', '')}.com",
    )
    db_session.add(empresa)
    await db_session.flush()

    usuario = Usuario(
        empresa_id=empresa.id,
        nome="Admin",
        email=email_admin,
        hashed_password=hash_password(senha),
        role=RoleUsuario.ADMIN,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(empresa)
    await db_session.refresh(usuario)
    return empresa, usuario


@pytest_asyncio.fixture
async def empresa_a(db_session: AsyncSession) -> tuple[Empresa, Usuario]:
    return await _criar_empresa_com_admin(db_session, "Marcenaria A", "admin@a.com", "senhaA123!")


@pytest_asyncio.fixture
async def empresa_b(db_session: AsyncSession) -> tuple[Empresa, Usuario]:
    return await _criar_empresa_com_admin(db_session, "Marcenaria B", "admin@b.com", "senhaB123!")


async def obter_token(client: AsyncClient, email: str, senha: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": senha})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]
