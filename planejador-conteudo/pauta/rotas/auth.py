from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import Config
from ..deps import obter_config_app, obter_db, usuario_atual
from ..geracao import planos_no_mes
from ..modelos import Usuario
from ..schemas import Cadastro, Eu, Login, Token
from ..seguranca import HASH_FALSO, conferir_senha, criar_token, gerar_hash

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/cadastro", response_model=Token, status_code=status.HTTP_201_CREATED)
def cadastrar(dados: Cadastro, db: Session = Depends(obter_db), config: Config = Depends(obter_config_app)):
    usuario = Usuario(email=dados.email.lower(), nome=dados.nome.strip(), senha_hash=gerar_hash(dados.senha))
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Já existe uma conta com este e-mail.")
    return Token(token=criar_token(usuario.id, config.secret_key, config.validade_token_horas))


@router.post("/login", response_model=Token)
def login(dados: Login, db: Session = Depends(obter_db), config: Config = Depends(obter_config_app)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == dados.email.lower()))
    ok = conferir_senha(dados.senha, usuario.senha_hash if usuario else HASH_FALSO)
    if not usuario or not ok:
        raise HTTPException(401, "E-mail ou senha incorretos.")
    return Token(token=criar_token(usuario.id, config.secret_key, config.validade_token_horas))


@router.get("/eu", response_model=Eu)
def eu(
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(obter_db),
    config: Config = Depends(obter_config_app),
):
    return Eu(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        plano=usuario.plano,
        planos_usados_mes=planos_no_mes(db, usuario.id),
        limite_planos_mes=config.limite_planos_mes,
    )
