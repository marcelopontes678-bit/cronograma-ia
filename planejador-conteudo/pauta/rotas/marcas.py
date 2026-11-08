from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..deps import marca_do_usuario, obter_db, usuario_atual
from ..modelos import Marca, Usuario
from ..schemas import MarcaAtualizar, MarcaCriar, MarcaSaida

router = APIRouter(prefix="/api/marcas", tags=["marcas"])

MAX_MARCAS = 20


@router.get("", response_model=list[MarcaSaida])
def listar(usuario: Usuario = Depends(usuario_atual), db: Session = Depends(obter_db)):
    return db.scalars(select(Marca).where(Marca.usuario_id == usuario.id).order_by(Marca.criado_em)).all()


@router.post("", response_model=MarcaSaida, status_code=status.HTTP_201_CREATED)
def criar(dados: MarcaCriar, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(obter_db)):
    total = db.scalar(select(func.count(Marca.id)).where(Marca.usuario_id == usuario.id)) or 0
    if total >= MAX_MARCAS:
        raise HTTPException(400, f"Limite de {MAX_MARCAS} marcas por conta.")
    marca = Marca(usuario_id=usuario.id, **dados.model_dump())
    db.add(marca)
    db.commit()
    return marca


@router.get("/{marca_id}", response_model=MarcaSaida)
def obter(marca_id: str, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(obter_db)):
    return marca_do_usuario(db, usuario, marca_id)


@router.patch("/{marca_id}", response_model=MarcaSaida)
def atualizar(
    marca_id: str, dados: MarcaAtualizar, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(obter_db)
):
    marca = marca_do_usuario(db, usuario, marca_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        if valor is not None:
            setattr(marca, campo, valor)
    db.commit()
    return marca


@router.delete("/{marca_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(marca_id: str, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(obter_db)):
    db.delete(marca_do_usuario(db, usuario, marca_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
