"""Configuração lida das variáveis de ambiente (12-factor).

Variáveis:
  DATABASE_URL        Postgres em produção; SQLite local por padrão.
  SECRET_KEY          assina os tokens de login. Obrigatória em produção.
  ANTHROPIC_API_KEY   chave da API do Claude (lida pelo SDK).
  PAUTA_MODELO        modelo do Claude (padrão: claude-opus-5-5).
  PAUTA_LIMITE_PLANOS planos gerados por usuário por mês no plano grátis (padrão: 10).
  CORS_ORIGINS        origens extras permitidas, separadas por vírgula.
  AMBIENTE            "producao" liga as checagens de segurança.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from functools import lru_cache


def _normalizar_url_banco(url: str) -> str:
    # Render e Heroku entregam "postgres://"; o SQLAlchemy quer o driver explícito.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


@dataclass(frozen=True)
class Config:
    database_url: str
    secret_key: str
    modelo: str
    limite_planos_mes: int
    cors_origins: list[str] = field(default_factory=list)
    producao: bool = False
    validade_token_horas: int = 24 * 7


@lru_cache
def obter_config() -> Config:
    producao = os.getenv("AMBIENTE", "").lower() in {"producao", "production"}
    secret = os.getenv("SECRET_KEY", "")
    if not secret:
        if producao:
            raise RuntimeError("Defina SECRET_KEY em produção.")
        secret = secrets.token_urlsafe(32)  # dev: tokens valem até reiniciar
    if producao and len(secret) < 32:
        raise RuntimeError("SECRET_KEY precisa ter pelo menos 32 caracteres.")
    return Config(
        database_url=_normalizar_url_banco(os.getenv("DATABASE_URL", "sqlite:///./pauta.db")),
        secret_key=secret,
        modelo=os.getenv("PAUTA_MODELO", "claude-opus-5-5"),
        limite_planos_mes=int(os.getenv("PAUTA_LIMITE_PLANOS", "10")),
        cors_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()],
        producao=producao,
    )
