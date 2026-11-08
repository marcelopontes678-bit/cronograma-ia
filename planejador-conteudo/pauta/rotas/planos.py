from __future__ import annotations

import csv
import io
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Config
from ..deps import (
    marca_do_usuario,
    obter_config_app,
    obter_db,
    obter_gerador,
    plano_do_usuario,
    post_do_usuario,
    usuario_atual,
)
from ..geracao import executar_geracao, expirar_se_travado, planos_no_mes
from ..ia import ErroIA, Gerador
from ..modelos import Plano, Post, Usuario
from ..schemas import PlanoCriar, PlanoResumo, PlanoSaida, PostAtualizar, PostSaida, Reescrever, StatusPost

router = APIRouter(prefix="/api", tags=["planos e posts"])


# --- Planos -------------------------------------------------------------


@router.post("/marcas/{marca_id}/planos", response_model=PlanoResumo, status_code=status.HTTP_202_ACCEPTED)
def criar_plano(
    marca_id: str,
    dados: PlanoCriar,
    request: Request,
    tarefas: BackgroundTasks,
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(obter_db),
    config: Config = Depends(obter_config_app),
    gerador: Gerador = Depends(obter_gerador),
):
    marca = marca_do_usuario(db, usuario, marca_id)
    if usuario.plano == "gratis" and planos_no_mes(db, usuario.id) >= config.limite_planos_mes:
        raise HTTPException(429, f"Você usou os {config.limite_planos_mes} planos do mês no plano grátis.")
    plano = Plano(
        marca_id=marca.id,
        usuario_id=usuario.id,
        data_inicio=dados.data_inicio,
        semanas=dados.semanas,
        posts_por_semana=dados.posts_por_semana,
        plataformas=list(dados.plataformas or marca.plataformas),
        foco=dados.foco.strip(),
    )
    db.add(plano)
    db.commit()
    tarefas.add_task(executar_geracao, plano.id, gerador, request.app.state.fabrica_sessao)
    return plano


@router.get("/marcas/{marca_id}/planos", response_model=list[PlanoResumo])
def listar_planos(marca_id: str, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(obter_db)):
    marca = marca_do_usuario(db, usuario, marca_id)
    planos = db.scalars(select(Plano).where(Plano.marca_id == marca.id).order_by(Plano.criado_em.desc())).all()
    for p in planos:
        expirar_se_travado(db, p)
    return planos


@router.get("/planos/{plano_id}", response_model=PlanoSaida)
def obter_plano(plano_id: str, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(obter_db)):
    plano = plano_do_usuario(db, usuario, plano_id)
    expirar_se_travado(db, plano)
    return plano


@router.delete("/planos/{plano_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_plano(plano_id: str, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(obter_db)):
    db.delete(plano_do_usuario(db, usuario, plano_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/planos/{plano_id}/csv")
def exportar_csv(plano_id: str, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(obter_db)):
    plano = plano_do_usuario(db, usuario, plano_id)
    saida = io.StringIO()
    w = csv.writer(saida)
    w.writerow(["data", "plataforma", "formato", "pilar", "titulo", "gancho", "roteiro", "legenda", "hashtags", "cta", "status"])
    for p in plano.posts:
        w.writerow(
            [p.data.isoformat(), p.plataforma, p.formato, p.pilar, p.titulo, p.gancho, p.roteiro, p.legenda,
             " ".join(f"#{h}" for h in p.hashtags), p.cta, p.status]
        )
    # BOM para o Excel abrir com acentos certos.
    return Response(
        "﻿" + saida.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="plano-{plano.data_inicio.isoformat()}.csv"'},
    )


# --- Posts --------------------------------------------------------------


@router.get("/marcas/{marca_id}/posts", response_model=list[PostSaida])
def listar_posts(
    marca_id: str,
    de: date | None = None,
    ate: date | None = None,
    status_post: StatusPost | None = Query(default=None, alias="status"),
    plataforma: str | None = None,
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(obter_db),
):
    marca = marca_do_usuario(db, usuario, marca_id)
    q = select(Post).where(Post.marca_id == marca.id)
    if de:
        q = q.where(Post.data >= de)
    if ate:
        q = q.where(Post.data <= ate)
    if status_post:
        q = q.where(Post.status == status_post)
    if plataforma:
        q = q.where(Post.plataforma == plataforma)
    return db.scalars(q.order_by(Post.data, Post.ordem).limit(500)).all()


@router.patch("/posts/{post_id}", response_model=PostSaida)
def atualizar_post(
    post_id: str, dados: PostAtualizar, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(obter_db)
):
    post = post_do_usuario(db, usuario, post_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        if valor is None:
            continue
        if campo == "hashtags":
            valor = [h.lstrip("#").strip() for h in valor if h.strip()]
        setattr(post, campo, valor)
    db.commit()
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_post(post_id: str, usuario: Usuario = Depends(usuario_atual), db: Session = Depends(obter_db)):
    db.delete(post_do_usuario(db, usuario, post_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/posts/{post_id}/reescrever", response_model=PostSaida)
def reescrever_post(
    post_id: str,
    dados: Reescrever,
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(obter_db),
    gerador: Gerador = Depends(obter_gerador),
):
    post = post_do_usuario(db, usuario, post_id)
    marca = marca_do_usuario(db, usuario, post.marca_id)
    try:
        novo, _ = gerador.reescrever_post(marca, post, dados.instrucao)
    except ErroIA as e:
        raise HTTPException(502, str(e))
    post.plataforma = novo.plataforma
    post.formato = novo.formato
    post.pilar = novo.pilar[:120]
    post.titulo = novo.titulo[:200]
    post.gancho = novo.gancho
    post.roteiro = novo.roteiro
    post.legenda = novo.legenda
    post.hashtags = [h.lstrip("#").strip() for h in novo.hashtags if h.strip()][:30]
    post.cta = novo.cta
    post.status = "rascunho"
    db.commit()
    return post
