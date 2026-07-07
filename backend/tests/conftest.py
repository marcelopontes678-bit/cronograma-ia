"""Fixtures de teste — usa o banco smartfactory_test isolado."""
import os

# Configura o ambiente ANTES de importar a aplicação
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://smartfactory:smartfactory@localhost:5432/smartfactory_test"
)
os.environ["SECRET_KEY"] = "chave-de-teste-nao-usar-em-producao-0123456789abcdef"
os.environ["ENVIRONMENT"] = "development"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.core.rate_limit import login_limiter, refresh_limiter
from app.core.security import hash_password
from app.main import app
from app.models.base import Base
from app.models.empresa import Empresa
from app.models.unidade import TipoUnidade, Unidade
from app.models.usuario import RoleUsuario, Usuario

sync_engine = create_engine(settings.sync_database_url)
SyncSession = sessionmaker(bind=sync_engine)

SENHA = "Senha123!"


@pytest.fixture(scope="session")
def dados():
    """Recria o schema e semeia duas empresas com usuários de cada papel."""
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)

    with SyncSession() as s:
        emp_a = Empresa(nome="Empresa A", cnpj="11.111.111/0001-11", email="a@a.com")
        emp_b = Empresa(nome="Empresa B", cnpj="22.222.222/0001-22", email="b@b.com")
        s.add_all([emp_a, emp_b])
        s.flush()

        unid_a = Unidade(
            empresa_id=emp_a.id, nome="Fábrica A", tipo=TipoUnidade.FABRICA, is_sede=True
        )
        s.add(unid_a)
        s.flush()

        hashed = hash_password(SENHA)
        users = {
            "admin": Usuario(
                empresa_id=emp_a.id, nome="Admin Global", email="admin@a.com",
                hashed_password=hashed, role=RoleUsuario.ADMIN,
            ),
            "gerente_a": Usuario(
                empresa_id=emp_a.id, nome="Gerente A", email="gerente@a.com",
                hashed_password=hashed, role=RoleUsuario.GERENTE,
            ),
            "operador_a": Usuario(
                empresa_id=emp_a.id, nome="Operador A", email="operador@a.com",
                hashed_password=hashed, role=RoleUsuario.OPERADOR,
            ),
            "gerente_b": Usuario(
                empresa_id=emp_b.id, nome="Gerente B", email="gerente@b.com",
                hashed_password=hashed, role=RoleUsuario.GERENTE,
            ),
        }
        s.add_all(users.values())
        s.commit()

        return {
            "empresa_a": str(emp_a.id),
            "empresa_b": str(emp_b.id),
            "unidade_a": str(unid_a.id),
            "ids": {k: str(u.id) for k, u in users.items()},
        }


# Escopo de sessão: um único event loop para todas as requisições,
# senão o pool do asyncpg fica preso ao loop do primeiro teste.
@pytest.fixture(scope="session")
def client(dados):
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _reset_limiters():
    login_limiter.reset()
    refresh_limiter.reset()


def fazer_login(client: TestClient, email: str) -> dict:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": SENHA})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture()
def token_admin(client):
    return fazer_login(client, "admin@a.com")["access_token"]


@pytest.fixture()
def token_gerente_a(client):
    return fazer_login(client, "gerente@a.com")["access_token"]


@pytest.fixture()
def token_operador_a(client):
    return fazer_login(client, "operador@a.com")["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
