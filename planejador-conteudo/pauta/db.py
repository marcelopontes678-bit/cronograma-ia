"""Conexão com o banco (SQLAlchemy 2, síncrono)."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def criar_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)


def criar_fabrica(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def sessao_de(fabrica: sessionmaker[Session]) -> Iterator[Session]:
    db = fabrica()
    try:
        yield db
    finally:
        db.close()
