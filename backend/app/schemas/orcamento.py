"""Schemas Pydantic do dominio de orcamento de marcenaria. A forma dos
sub-objetos de PreferenciasGlobais reaproveita o que ja foi validado contra
a API real do Claude (persona MARC) no protótipo standalone
orcamento-marcenaria/api/schemas/preferencias.py -- so troca `usuario_id`
por `empresa_id` (diretrizes de producao sao da fabrica, nao pessoais) e
deriva o tenant do usuario autenticado, nunca de um campo do payload.

Fase 1 desta integracao (ver plano) so cobre PreferenciasGlobais e o
esqueleto de OrcamentoJob (criacao/consulta persistida, sem disparar a
extracao via Vision ainda) -- por isso `ambientes`/`avisos` aqui sao
genericos (list[dict]/list[str]) em vez do schema aninhado completo de
Modulo/Ambiente; a Fase 2 troca isso pelo schema validado quando o
vision_extractor.py for movido para dentro do backend.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.models.orcamento import StatusOrcamentoJob


class MetodoUniao(str, Enum):
    CAVILHA = "cavilha"
    MINIFIX = "minifix"
    VB35 = "vb35"
    PARAFUSO_DIRETO = "parafuso_direto"


class FixacaoFundo(str, Enum):
    ENCAIXADO_EM_REBAIXO = "encaixado_em_rebaixo"
    PARAFUSADO_POR_TRAS = "parafusado_por_tras"


class TipoApoio(str, Enum):
    PE_PLASTICO = "pe_plastico"
    RODAPE_MDF = "rodape_mdf"


class TipoCorredica(str, Enum):
    TELESCOPICA = "telescopica"
    OCULTA = "oculta"
    ROLDANA = "roldana"


class EspessurasPadrao(BaseModel):
    caixa_mm: float = 15
    porta_mm: float = 18
    fundo_mm: float = 6
    prateleira_mm: float = 15
    sarrafo_superior_mm: float = 25


class FerragensPadrao(BaseModel):
    marca_corredicas: str = "-"
    marca_dobradicas: str = "-"
    tipo_corredica_padrao: TipoCorredica = TipoCorredica.TELESCOPICA
    dobradica_com_amortecimento: bool = True


class FaixaDobradicasPorAltura(BaseModel):
    altura_maxima_mm: float
    quantidade_dobradicas: int


class RegraApoioPorAmbiente(BaseModel):
    ambientes_molhados: list[str] = Field(
        default_factory=lambda: ["Cozinha", "Banheiro", "Lavanderia", "Área de Serviço"]
    )
    apoio_area_molhada: TipoApoio = TipoApoio.PE_PLASTICO
    apoio_area_seca: TipoApoio = TipoApoio.RODAPE_MDF


class PreferenciasGlobaisConfig(BaseModel):
    """Corpo que fica em PreferenciasGlobais.configuracao (JSONB) -- sem
    empresa_id, que e coluna propria da tabela."""

    espessuras: EspessurasPadrao = Field(default_factory=EspessurasPadrao)
    ferragens: FerragensPadrao = Field(default_factory=FerragensPadrao)
    metodo_uniao: MetodoUniao = MetodoUniao.MINIFIX
    fixacao_fundo: FixacaoFundo = FixacaoFundo.ENCAIXADO_EM_REBAIXO
    acabamento_interno_padrao: str = "MDF Branco"
    regra_fundo_exposto_forca_cor_caixaria: bool = True
    regra_apoio_por_ambiente: RegraApoioPorAmbiente = Field(default_factory=RegraApoioPorAmbiente)
    faixas_dobradicas_por_altura: list[FaixaDobradicasPorAltura] = Field(
        default_factory=lambda: [
            FaixaDobradicasPorAltura(altura_maxima_mm=900, quantidade_dobradicas=2),
            FaixaDobradicasPorAltura(altura_maxima_mm=1800, quantidade_dobradicas=4),
            FaixaDobradicasPorAltura(altura_maxima_mm=999_999, quantidade_dobradicas=5),
        ]
    )
    profundidade_padrao_por_tipo_mm: dict[str, float] = Field(
        default_factory=lambda: {"armario_superior": 350, "armario_inferior": 550, "armario_alto": 550}
    )


class PreferenciasGlobaisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    empresa_id: uuid.UUID
    configuracao: PreferenciasGlobaisConfig
    created_at: datetime
    updated_at: datetime


class OrcamentoJobCreate(BaseModel):
    arquivo_origem: str
    projeto_id: uuid.UUID | None = None


class OrcamentoJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    empresa_id: uuid.UUID
    usuario_id: uuid.UUID | None
    projeto_id: uuid.UUID | None
    arquivo_origem: str
    status: StatusOrcamentoJob
    ambientes: list[dict]
    avisos: list[str]
    created_at: datetime
    updated_at: datetime
