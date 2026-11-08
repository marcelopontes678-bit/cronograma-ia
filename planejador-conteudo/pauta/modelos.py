"""Tabelas do banco.

usuarios 1─N marcas 1─N planos 1─N posts
Cada post também guarda marca_id para o calendário consultar direto por marca.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def agora() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(120))
    senha_hash: Mapped[str] = mapped_column(String(255))
    plano: Mapped[str] = mapped_column(String(20), default="gratis")  # gratis | pro
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)

    marcas: Mapped[list[Marca]] = relationship(back_populates="usuario", cascade="all, delete-orphan")


class Marca(Base):
    """Perfil do criador/empresa: o contexto que a IA usa para planejar."""

    __tablename__ = "marcas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    usuario_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    nome: Mapped[str] = mapped_column(String(120))
    nicho: Mapped[str] = mapped_column(String(200))
    publico_alvo: Mapped[str] = mapped_column(Text, default="")
    tom_de_voz: Mapped[str] = mapped_column(String(200), default="")
    objetivo: Mapped[str] = mapped_column(String(200), default="")
    plataformas: Mapped[list[str]] = mapped_column(JSON, default=list)
    pilares: Mapped[list[str]] = mapped_column(JSON, default=list)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)

    usuario: Mapped[Usuario] = relationship(back_populates="marcas")
    planos: Mapped[list[Plano]] = relationship(back_populates="marca", cascade="all, delete-orphan")


class Plano(Base):
    """Um pedido de calendário editorial. A geração roda em segundo plano."""

    __tablename__ = "planos"
    __table_args__ = (Index("ix_planos_status", "status"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    marca_id: Mapped[str] = mapped_column(ForeignKey("marcas.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    semanas: Mapped[int] = mapped_column(Integer)
    posts_por_semana: Mapped[int] = mapped_column(Integer)
    plataformas: Mapped[list[str]] = mapped_column(JSON, default=list)
    foco: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pendente")  # pendente | gerando | pronto | erro
    estrategia: Mapped[str] = mapped_column(Text, default="")
    erro: Mapped[str] = mapped_column(Text, default="")
    modelo: Mapped[str] = mapped_column(String(80), default="")
    tokens_entrada: Mapped[int] = mapped_column(Integer, default=0)
    tokens_saida: Mapped[int] = mapped_column(Integer, default=0)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, index=True)
    concluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    marca: Mapped[Marca] = relationship(back_populates="planos")
    posts: Mapped[list[Post]] = relationship(
        back_populates="plano", cascade="all, delete-orphan", order_by="(Post.data, Post.ordem)"
    )


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (Index("ix_posts_marca_data", "marca_id", "data"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plano_id: Mapped[str] = mapped_column(ForeignKey("planos.id", ondelete="CASCADE"), index=True)
    marca_id: Mapped[str] = mapped_column(ForeignKey("marcas.id", ondelete="CASCADE"))
    data: Mapped[date] = mapped_column(Date)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    plataforma: Mapped[str] = mapped_column(String(30))
    formato: Mapped[str] = mapped_column(String(30))
    pilar: Mapped[str] = mapped_column(String(120), default="")
    titulo: Mapped[str] = mapped_column(String(200))
    gancho: Mapped[str] = mapped_column(Text, default="")
    roteiro: Mapped[str] = mapped_column(Text, default="")
    legenda: Mapped[str] = mapped_column(Text, default="")
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    cta: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="ideia")  # ideia | rascunho | aprovado | publicado
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora, onupdate=agora)

    plano: Mapped[Plano] = relationship(back_populates="posts")
