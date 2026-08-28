"""Preferencias Globais de producao -- diretrizes padrao da marcenaria,
usadas pela LLM para inferir especificacoes que o desenho nao deixa
explicitas (ex: desenho diz "Armario em MDF Branco" sem dizer a
espessura da caixa -- a IA usa espessura_caixa_mm daqui e marca
material_explicito_no_desenho=False no Modulo resultante).
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class MetodoUniao(str, Enum):
    CAVILHA = "cavilha"
    PARAFUSO_MINIFIX = "parafuso_minifix"
    COLA_ENCAIXE = "cola_encaixe"


class EspessurasPadrao(BaseModel):
    caixa_mm: float = 15
    porta_mm: float = 18
    fundo_mm: float = 6
    prateleira_mm: float = 15


class FerragensPadrao(BaseModel):
    marca_corredicas: str = "-"
    marca_dobradicas: str = "-"
    tipo_corredica_padrao: str = Field("telescopica", description="telescopica | oculta | roldana")
    dobradica_com_amortecimento: bool = True


class PreferenciasGlobais(BaseModel):
    """Um registro por usuario/empresa. Persistido em
    storage/preferencias_globais.json (ou por usuario, se multi-tenant)."""
    usuario_id: str
    espessuras: EspessurasPadrao = Field(default_factory=EspessurasPadrao)
    ferragens: FerragensPadrao = Field(default_factory=FerragensPadrao)
    metodo_uniao: MetodoUniao = MetodoUniao.CAVILHA
    acabamento_interno_padrao: str = Field("MDF Branco", description="Usado quando o desenho nao especifica o acabamento interno")
    profundidade_padrao_por_tipo_mm: dict[str, float] = Field(
        default_factory=lambda: {"armario_superior": 350, "armario_inferior": 550, "armario_alto": 550},
        description="Fallback de profundidade por tipo de modulo quando o desenho nao cota isso",
    )
