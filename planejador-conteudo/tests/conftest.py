from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi.testclient import TestClient

from pauta.config import Config
from pauta.ia import ErroIA, Uso
from pauta.main import criar_app
from pauta.schemas import PlanoIA, PostIA

RAIZ = Path(__file__).resolve().parent.parent


class GeradorFalso:
    """Devolve um plano previsível; registra as chamadas."""

    modelo = "falso"

    def __init__(self):
        self.falhar = False
        self.chamadas = 0

    def gerar_plano(self, marca, plano):
        self.chamadas += 1
        if self.falhar:
            raise ErroIA("IA fora do ar")
        total = plano.semanas * plano.posts_por_semana
        posts = [
            PostIA(
                dia=i * 2,
                plataforma=plano.plataformas[i % len(plano.plataformas)],
                formato="reels",
                pilar=(marca.pilares or ["Geral"])[0],
                titulo=f"Post {i + 1}",
                gancho="Gancho",
                roteiro="- cena 1\n- cena 2",
                legenda="Legenda",
                hashtags=["#ia", "conteudo"],
                cta="Comente",
            )
            for i in range(total)
        ]
        # Um post numa plataforma não pedida e outro fora do período: o app deve tratar.
        posts.append(posts[0].model_copy(update={"plataforma": "linkedin" if "linkedin" not in plano.plataformas else "x"}))
        posts.append(posts[0].model_copy(update={"dia": 999, "titulo": "Fora do período"}))
        return PlanoIA(estrategia="Estratégia de teste.", posts=posts), Uso(100, 200)

    def reescrever_post(self, marca, post, instrucao):
        return (
            PostIA(dia=0, plataforma=post.plataforma, formato="carrossel", pilar=post.pilar, titulo="Reescrito",
                   gancho=instrucao, roteiro="novo", legenda="nova", hashtags=["x"], cta="cta"),
            Uso(10, 20),
        )


@pytest.fixture
def url_banco(tmp_path):
    """SQLite temporário por padrão; TEST_DATABASE_URL=postgresql+psycopg://... roda no Postgres."""
    url = os.getenv("TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'teste.db'}"
    cfg = AlembicConfig(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")  # testa as migrações de verdade
    yield url
    command.downgrade(cfg, "base")  # e o caminho de volta


@pytest.fixture
def gerador() -> GeradorFalso:
    return GeradorFalso()


@pytest.fixture
def cliente(url_banco, gerador) -> TestClient:
    config = Config(database_url=url_banco, secret_key="segredo-de-teste-com-mais-de-32-bytes", modelo="falso", limite_planos_mes=3)
    return TestClient(criar_app(config, gerador))


def cadastrar(cliente: TestClient, email: str = "ana@exemplo.com") -> dict:
    r = cliente.post("/api/auth/cadastro", json={"nome": "Ana", "email": email, "senha": "senha-forte-123"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


MARCA = {
    "nome": "Ana Fit",
    "nicho": "treino em casa para mulheres 30+",
    "publico_alvo": "mulheres sem tempo para academia",
    "tom_de_voz": "próximo e motivador",
    "objetivo": "vender consultoria online",
    "plataformas": ["instagram", "tiktok"],
    "pilares": ["Treinos rápidos", "Alimentação", "Bastidores", " Treinos rápidos "],
}
