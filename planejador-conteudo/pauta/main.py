"""App FastAPI: API em /api/* e a interface (SPA estática) em /.

Rodar local:  uvicorn pauta.main:app --reload
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import Config, obter_config
from .db import criar_engine, criar_fabrica
from .ia import Gerador, GeradorClaude
from .rotas import auth, marcas, planos

ESTATICOS = Path(__file__).parent / "static"


def criar_app(config: Config | None = None, gerador: Gerador | None = None) -> FastAPI:
    config = config or obter_config()
    logging.basicConfig(level=logging.INFO)

    app = FastAPI(title="Pauta — planejador de conteúdo com IA", version="0.1.0", docs_url="/api/docs",
                  openapi_url="/api/openapi.json", redoc_url=None)
    engine = criar_engine(config.database_url)
    app.state.config = config
    app.state.engine = engine
    app.state.fabrica_sessao = criar_fabrica(engine)
    app.state.gerador = gerador or GeradorClaude(config.modelo)

    if config.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_methods=["*"],
            allow_headers=["Authorization", "Content-Type"],
        )

    @app.middleware("http")
    async def cabecalhos_seguranca(request, call_next):
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        return resp

    app.include_router(auth.router)
    app.include_router(marcas.router)
    app.include_router(planos.router)

    @app.get("/api/saude", tags=["infra"])
    def saude():
        return {"ok": True}

    app.mount("/static", StaticFiles(directory=ESTATICOS), name="static")

    @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    def inicio():
        return FileResponse(ESTATICOS / "index.html")

    return app


app = criar_app()
