"""Envelope HTTP para o motor de precificacao existente (engine/calculo_projeto.py
+ engine/orcamento_engine.py). Nao reimplementa a logica de calculo -- so
formata entrada/saida para a API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class OrcamentoRequest(BaseModel):
    job_id: str = Field(..., description="Job de extracao ja CONFIRMADO (status=confirmado) a ser precificado")
    tabela_precos_id: str = Field("default", description="Qual tabela de precos usar, se houver mais de uma")
    faturamento_acumulado: float = Field(..., ge=0)
    custo_hora_mao_de_obra: float = Field(0, ge=0)
    horas_estimadas: float = Field(0, ge=0)


class ItemPendente(BaseModel):
    reference_ou_acabamento: str
    descricao: str
    motivo: str  # SEM_PRECO_CHAPA_NA_TABELA | SEM_PRECO_FITA_NA_TABELA | SEM_PRECO_NA_TABELA


class OrcamentoResponse(BaseModel):
    job_id: str
    divisor_markup: float
    custo_material_total: float
    preco_venda_material: float
    custo_mao_de_obra: float
    total: float
    itens_pendentes: list[ItemPendente] = Field(default_factory=list, description="Nunca precificados com custo zero/estimado -- sempre listados aqui")
