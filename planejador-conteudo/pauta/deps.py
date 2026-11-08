"""Dependências do FastAPI: sessão do banco, usuário logado, gerador de IA e checagem de dono."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import Config
from .ia import Gerador
from .modelos import Marca, Plano, Post, Usuario
from .seguranca import ler_token

_bearer = HTTPBearer(auto_error=False)


def obter_config_app(request: Request) -> Config:
    return request.app.state.config


def obter_db(request: Request) -> Iterator[Session]:
    db = request.app.state.fabrica_sessao()
    try:
        yield db
    finally:
        db.close()


def obter_gerador(request: Request) -> Gerador:
    return request.app.state.gerador


def usuario_atual(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(obter_db),
    config: Config = Depends(obter_config_app),
) -> Usuario:
    erro = HTTPException(status.HTTP_401_UNAUTHORIZED, "Faça login de novo.", {"WWW-Authenticate": "Bearer"})
    if cred is None:
        raise erro
    usuario_id = ler_token(cred.credentials, config.secret_key)
    usuario = db.get(Usuario, usuario_id) if usuario_id else None
    if usuario is None:
        raise erro
    return usuario


# Tudo que não é do usuário responde 404 (não revela que o recurso existe).


def marca_do_usuario(db: Session, usuario: Usuario, marca_id: str) -> Marca:
    marca = db.get(Marca, marca_id)
    if marca is None or marca.usuario_id != usuario.id:
        raise HTTPException(404, "Marca não encontrada.")
    return marca


def plano_do_usuario(db: Session, usuario: Usuario, plano_id: str) -> Plano:
    plano = db.get(Plano, plano_id)
    if plano is None or plano.usuario_id != usuario.id:
        raise HTTPException(404, "Plano não encontrado.")
    return plano


def post_do_usuario(db: Session, usuario: Usuario, post_id: str) -> Post:
    post = db.get(Post, post_id)
    if post is None or post.plano.usuario_id != usuario.id:
        raise HTTPException(404, "Post não encontrado.")
    return post
