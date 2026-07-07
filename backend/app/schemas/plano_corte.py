import uuid
from typing import Optional

from pydantic import BaseModel


class PecaPosicionadaOut(BaseModel):
    ref: str
    nome: str
    x_mm: int
    y_mm: int
    comprimento_mm: int
    largura_mm: int
    rotacionada: bool


class ChapaCorteOut(BaseModel):
    indice: int
    aproveitamento_pct: float
    pecas: list[PecaPosicionadaOut]


class PlanoMaterialOut(BaseModel):
    material_id: uuid.UUID
    material_nome: str
    chapa_comprimento_mm: int
    chapa_largura_mm: int
    total_chapas: int
    aproveitamento_medio_pct: float
    chapas: list[ChapaCorteOut]
    nao_alocadas: list[str]


class PecaSemMaterialOut(BaseModel):
    nome: str
    motivo: str


class PlanoCorteOut(BaseModel):
    projeto_id: uuid.UUID
    kerf_mm: int
    total_pecas_alocadas: int
    materiais: list[PlanoMaterialOut]
    pecas_ignoradas: list[PecaSemMaterialOut]
