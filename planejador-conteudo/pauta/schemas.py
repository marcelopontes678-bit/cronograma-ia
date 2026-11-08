"""Contratos da API (entrada e saída) e o formato que a IA deve devolver."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Plataforma = Literal["instagram", "tiktok", "youtube", "linkedin", "x", "threads"]
Formato = Literal["reels", "carrossel", "post", "story", "short", "video_longo", "thread", "artigo"]
StatusPost = Literal["ideia", "rascunho", "aprovado", "publicado"]

PLATAFORMAS: tuple[str, ...] = Plataforma.__args__  # type: ignore[attr-defined]


def _limpar_lista(valores: list[str], maximo: int) -> list[str]:
    vistos: list[str] = []
    for v in valores:
        v = v.strip()
        if v and v not in vistos:
            vistos.append(v)
    return vistos[:maximo]


# --- Auth ---------------------------------------------------------------


class Cadastro(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)


class Login(BaseModel):
    email: EmailStr
    senha: str = Field(max_length=128)


class Token(BaseModel):
    token: str
    tipo: str = "bearer"


class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome: str
    email: str
    plano: str


class Eu(UsuarioSaida):
    planos_usados_mes: int
    limite_planos_mes: int


# --- Marcas -------------------------------------------------------------


class MarcaBase(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    nicho: str = Field(min_length=1, max_length=200)
    publico_alvo: str = Field(default="", max_length=1000)
    tom_de_voz: str = Field(default="", max_length=200)
    objetivo: str = Field(default="", max_length=200)
    plataformas: list[Plataforma] = Field(default_factory=lambda: ["instagram"], min_length=1)
    pilares: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("pilares")
    @classmethod
    def _pilares(cls, v: list[str]) -> list[str]:
        return _limpar_lista([p[:120] for p in v], 8)


class MarcaCriar(MarcaBase):
    pass


class MarcaAtualizar(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    nicho: str | None = Field(default=None, min_length=1, max_length=200)
    publico_alvo: str | None = Field(default=None, max_length=1000)
    tom_de_voz: str | None = Field(default=None, max_length=200)
    objetivo: str | None = Field(default=None, max_length=200)
    plataformas: list[Plataforma] | None = Field(default=None, min_length=1)
    pilares: list[str] | None = Field(default=None, max_length=8)

    @field_validator("pilares")
    @classmethod
    def _pilares(cls, v: list[str] | None) -> list[str] | None:
        return None if v is None else _limpar_lista([p[:120] for p in v], 8)


class MarcaSaida(MarcaBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    criado_em: datetime


# --- Planos e posts -----------------------------------------------------


class PlanoCriar(BaseModel):
    data_inicio: date
    semanas: int = Field(default=2, ge=1, le=4)
    posts_por_semana: int = Field(default=3, ge=1, le=7)
    plataformas: list[Plataforma] | None = Field(default=None, min_length=1)
    foco: str = Field(default="", max_length=500, description="Lançamento, tema do mês, campanha...")


class PostSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plano_id: str
    data: date
    plataforma: str
    formato: str
    pilar: str
    titulo: str
    gancho: str
    roteiro: str
    legenda: str
    hashtags: list[str]
    cta: str
    status: str
    atualizado_em: datetime


class PostAtualizar(BaseModel):
    data: date | None = None
    plataforma: Plataforma | None = None
    formato: Formato | None = None
    pilar: str | None = Field(default=None, max_length=120)
    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    gancho: str | None = Field(default=None, max_length=2000)
    roteiro: str | None = Field(default=None, max_length=20000)
    legenda: str | None = Field(default=None, max_length=5000)
    hashtags: list[str] | None = Field(default=None, max_length=30)
    cta: str | None = Field(default=None, max_length=1000)
    status: StatusPost | None = None


class Reescrever(BaseModel):
    instrucao: str = Field(min_length=1, max_length=1000)


class PlanoResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    marca_id: str
    data_inicio: date
    semanas: int
    posts_por_semana: int
    plataformas: list[str]
    foco: str
    status: str
    erro: str
    criado_em: datetime
    concluido_em: datetime | None


class PlanoSaida(PlanoResumo):
    estrategia: str
    posts: list[PostSaida]


# --- Saída estruturada da IA -------------------------------------------


class PostIA(BaseModel):
    dia: int = Field(description="Dias a partir da data de início (0 = primeiro dia).")
    plataforma: Plataforma
    formato: Formato
    pilar: str
    titulo: str = Field(description="Título interno curto do conteúdo.")
    gancho: str = Field(description="Primeira frase/cena: o que prende nos 3 primeiros segundos.")
    roteiro: str = Field(description="Roteiro em tópicos ou cenas, pronto para gravar ou montar.")
    legenda: str = Field(description="Legenda completa pronta para publicar, sem as hashtags.")
    hashtags: list[str] = Field(description="De 3 a 8 hashtags, sem o #.")
    cta: str = Field(description="Chamada para ação.")


class PlanoIA(BaseModel):
    estrategia: str = Field(description="3 a 5 frases explicando a lógica do calendário.")
    posts: list[PostIA]
