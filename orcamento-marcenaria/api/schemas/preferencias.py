"""Preferencias Globais de producao -- diretrizes padrao da marcenaria,
usadas pelo agente extrator (persona "MARC", ver prompts/system_extrator.md)
para inferir especificacoes que o desenho nao deixa explicitas (ex: desenho
diz "Armario em MDF Branco" sem dizer o metodo de uniao -- o MARC usa
metodo_uniao daqui e registra o campo em
Modulo.especificacoes_materiais.campos_inferidos, nunca fingindo que veio
do proprio desenho).
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


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
    sarrafo_superior_mm: float = Field(25, description="Sarrafo superior de armarios baixos (regra 1 do MARC)")


class FerragensPadrao(BaseModel):
    marca_corredicas: str = "-"
    marca_dobradicas: str = "-"
    tipo_corredica_padrao: TipoCorredica = TipoCorredica.TELESCOPICA
    dobradica_com_amortecimento: bool = True


class FaixaDobradicasPorAltura(BaseModel):
    """Regra 5 do MARC: quantidade de dobradicas por porta, pela altura
    util do modulo. Avaliar em ordem crescente de altura_maxima_mm, usando
    a primeira faixa em que a altura do modulo couber."""
    altura_maxima_mm: float
    quantidade_dobradicas: int


class RegraApoioPorAmbiente(BaseModel):
    """Regra 4 do MARC: pe plastico em areas molhadas, rodape em MDF em
    areas secas."""
    ambientes_molhados: list[str] = Field(
        default_factory=lambda: ["Cozinha", "Banheiro", "Lavanderia", "Área de Serviço", "Área de Serviço"]
    )
    apoio_area_molhada: TipoApoio = TipoApoio.PE_PLASTICO
    apoio_area_seca: TipoApoio = TipoApoio.RODAPE_MDF


class PreferenciasGlobais(BaseModel):
    """Um registro por usuario/empresa. Persistido em
    storage/preferencias/{usuario_id}.json."""
    usuario_id: str
    espessuras: EspessurasPadrao = Field(default_factory=EspessurasPadrao)
    ferragens: FerragensPadrao = Field(default_factory=FerragensPadrao)
    metodo_uniao: MetodoUniao = MetodoUniao.MINIFIX
    fixacao_fundo: FixacaoFundo = FixacaoFundo.ENCAIXADO_EM_REBAIXO
    acabamento_interno_padrao: str = Field("MDF Branco", description="Usado quando o desenho nao especifica o acabamento/fundo padrao")
    regra_fundo_exposto_forca_cor_caixaria: bool = Field(
        True,
        description="Regra 2 (excecao de estetica) do MARC: em cristaleiras com porta de vidro/aluminio ou "
        "nichos abertos onde o fundo fica exposto, usar o fundo na cor da caixaria em vez do acabamento_interno_padrao",
    )
    regra_apoio_por_ambiente: RegraApoioPorAmbiente = Field(default_factory=RegraApoioPorAmbiente)
    faixas_dobradicas_por_altura: list[FaixaDobradicasPorAltura] = Field(
        default_factory=lambda: [
            FaixaDobradicasPorAltura(altura_maxima_mm=900, quantidade_dobradicas=2),
            FaixaDobradicasPorAltura(altura_maxima_mm=1800, quantidade_dobradicas=4),
            FaixaDobradicasPorAltura(altura_maxima_mm=999_999, quantidade_dobradicas=5),
        ]
    )
    profundidade_padrao_por_tipo_mm: dict[str, float] = Field(
        default_factory=lambda: {"armario_superior": 350, "armario_inferior": 550, "armario_alto": 550},
        description="Fallback de profundidade por tipo de modulo quando o desenho nao cota isso",
    )
