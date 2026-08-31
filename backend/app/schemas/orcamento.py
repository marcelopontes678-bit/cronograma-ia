"""Schemas Pydantic do dominio de orcamento de marcenaria. A forma dos
sub-objetos de PreferenciasGlobais e do schema de extracao (Modulo/
Ambiente/AuditoriaVisual) reaproveita o que ja foi validado contra a API
real do Claude (persona MARC) no protótipo standalone orcamento-marcenaria/
api/schemas/{preferencias,extracao}.py -- so troca `usuario_id` por
`empresa_id` em PreferenciasGlobais (diretrizes de producao sao da fabrica,
nao pessoais) e deriva o tenant do usuario autenticado, nunca de um campo
do payload.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.orcamento import StatusOrcamentoJob


class OrigemModulo(str, Enum):
    VISION_AUTOMATICO = "vision_automatico"  # extraido pelo MARC sem edicao
    CONFIRMADO_HUMANO = "confirmado_humano"  # usuario revisou e confirmou/corrigiu
    ADICIONADO_MANUAL = "adicionado_manual"  # usuario adicionou um modulo que o MARC nao pegou


class AuditoriaVisual(BaseModel):
    pagina_pdf: int = Field(..., ge=1)
    bounding_box: list[int] = Field(
        ..., min_length=4, max_length=4,
        description="[y_min, x_min, y_max, x_max], normalizado 0-1000 relativo a pagina",
    )

    @field_validator("bounding_box")
    @classmethod
    def _valores_dentro_de_0_1000(cls, v: list[int]) -> list[int]:
        if any(x < 0 or x > 1000 for x in v):
            raise ValueError("bounding_box deve ter todos os valores entre 0 e 1000")
        return v


class Dimensoes(BaseModel):
    largura_mm: float | None = None
    altura_mm: float | None = None
    profundidade_mm: float | None = None


class Componentes(BaseModel):
    portas: int = 0
    gavetas: int = 0
    prateleiras_internas: int = 0


class EspecificacoesMateriais(BaseModel):
    caixaria: str
    frente: str
    fundo: str
    metodo_uniao: str
    fixacao_fundo: str
    campos_inferidos: list[str] = Field(default_factory=list)


class FerragemSugerida(BaseModel):
    nome: str
    quantidade: int = Field(..., ge=0)


class ItemComplementar(BaseModel):
    nome: str
    tipo: str


class Modulo(BaseModel):
    id: str
    nome: str
    vista_referencia: str = ""
    dimensoes: Dimensoes = Field(default_factory=Dimensoes)
    componentes: Componentes = Field(default_factory=Componentes)
    especificacoes_materiais: EspecificacoesMateriais
    ferragens_sugeridas: list[FerragemSugerida] = Field(default_factory=list)
    itens_complementares: list[ItemComplementar] = Field(default_factory=list)
    auditoria_visual: AuditoriaVisual
    descricao_resumida: str = ""
    confianca: float = Field(..., ge=0, le=1)
    origem: OrigemModulo = OrigemModulo.VISION_AUTOMATICO


class Ambiente(BaseModel):
    nome_ambiente: str
    modulos: list[Modulo] = Field(default_factory=list)


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


class OrcamentoJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    empresa_id: uuid.UUID
    usuario_id: uuid.UUID | None
    projeto_id: uuid.UUID | None
    arquivo_origem: str
    status: StatusOrcamentoJob
    ambientes: list[Ambiente]
    avisos: list[str]
    created_at: datetime
    updated_at: datetime


class ModuloManualCreate(BaseModel):
    """Corpo de POST /jobs/{id}/modulos -- modulo que a IA nao pegou,
    adicionado manualmente pelo usuario apos a revisao."""

    nome_ambiente: str
    modulo: Modulo


class ModuloPatch(BaseModel):
    """Corpo de PATCH /jobs/{id}/modulos/{modulo_id} -- patch parcial,
    merge raso nos subcampos aninhados (dimensoes, componentes,
    especificacoes_materiais, auditoria_visual)."""

    model_config = ConfigDict(extra="allow")


class OrcamentoRequest(BaseModel):
    faturamento_acumulado: float = Field(..., ge=0)
    custo_hora_mao_de_obra: float = 0
    horas_estimadas: float = 0
    fator_area_frontal_para_chapa: float | None = None


class ItemPendente(BaseModel):
    reference_ou_acabamento: str
    descricao: str
    motivo: str


class FeedbackRequest(BaseModel):
    """Correcao em linguagem natural do marceneiro (ex: 'Sempre que houver
    porta de vidro reflecta, mude o fundo para a cor da caixa'), normalizada
    pela LLM numa regra reusavel e injetada no system prompt do MARC nas
    proximas extracoes DESSA empresa."""

    job_id: uuid.UUID | None = None
    modulo_id: str | None = None
    instrucao: str


class RegraAprendidaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    empresa_id: uuid.UUID
    usuario_id: uuid.UUID | None
    instrucao_original: str
    regra_normalizada: str
    origem_job_id: uuid.UUID | None
    origem_modulo_id: str | None
    is_active: bool
    created_at: datetime


class FeedbackResponse(BaseModel):
    regra: RegraAprendidaResponse
    total_regras_ativas_empresa: int


class OrcamentoResponse(BaseModel):
    job_id: uuid.UUID
    divisor_markup: float
    custo_material_total: float
    preco_venda_material: float
    custo_mao_de_obra: float
    total: float
    itens_pendentes: list[ItemPendente] = Field(default_factory=list)
    avisos: list[str] = Field(default_factory=list)
