"""Schemas do resultado de extracao via Claude Vision.

Diferente do extractor Promob (dados exatos de um XML estruturado), a
extracao por Vision e uma INFERENCIA sobre uma imagem -- por isso todo
Modulo carrega confianca e bounding_boxes, e a extracao nunca alimenta
o motor de precificacao diretamente sem confirmacao humana (ver
ExtracaoResultado.status).
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Retangulo de destaque na pagina renderizada, em coordenadas
    normalizadas (0-1) relativas ao tamanho da pagina -- independente
    da resolucao usada para render no frontend."""
    pagina: int = Field(..., ge=1, description="Numero da pagina no PDF original (1-indexed)")
    x: float = Field(..., ge=0, le=1)
    y: float = Field(..., ge=0, le=1)
    width: float = Field(..., ge=0, le=1)
    height: float = Field(..., ge=0, le=1)


class OrigemModulo(str, Enum):
    VISION_AUTOMATICO = "vision_automatico"      # extraido pela LLM sem edicao
    CONFIRMADO_HUMANO = "confirmado_humano"       # usuario revisou e confirmou/corrigiu
    ADICIONADO_MANUAL = "adicionado_manual"       # usuario adicionou um modulo que a IA nao pegou


class Modulo(BaseModel):
    id: str = Field(..., description="ID estavel dentro do job, ex: 'mod_003'")
    nome: str = Field(..., description="Ex: 'Armario Superior', 'Cristaleira'")
    ambiente: str
    largura_mm: float | None = None
    altura_mm: float | None = None
    profundidade_mm: float | None = None
    quantidade_portas: int = 0
    quantidade_gavetas: int = 0
    material_sugerido: str = Field(..., description="Inferido do desenho ou das Preferencias Globais quando nao especificado")
    material_explicito_no_desenho: bool = Field(..., description="False quando o material veio de inferencia via Preferencias Globais, nao do proprio desenho")
    confianca: float = Field(..., ge=0, le=1, description="Confianca da IA nesta leitura (0-1). < 0.7 deve ser destacado para revisao")
    bounding_boxes: list[BoundingBox] = Field(default_factory=list)
    origem: OrigemModulo = OrigemModulo.VISION_AUTOMATICO
    observacoes: str = ""


class Ambiente(BaseModel):
    nome: str
    modulos: list[Modulo] = Field(default_factory=list)


class StatusExtracao(str, Enum):
    PROCESSANDO = "processando"
    AGUARDANDO_REVISAO = "aguardando_revisao"     # extraido, mas tem itens de baixa confianca
    CONFIRMADO = "confirmado"                     # humano revisou -- agora pode ir para o pricing_service
    ERRO = "erro"


class ExtracaoResultado(BaseModel):
    job_id: str
    arquivo_origem: str
    status: StatusExtracao
    ambientes: list[Ambiente] = Field(default_factory=list)
    avisos: list[str] = Field(default_factory=list, description="Ex: 'pagina 9: dois rotulos de acabamento sobrepostos, confirme manualmente'")
    criado_em: datetime
    atualizado_em: datetime
