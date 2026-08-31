"""Schemas do resultado de extracao do agente MARC (Claude Vision, ver
prompts/system_extrator.md). Schema de modulo bem mais rico que a v1:
dimensoes/componentes/materiais aninhados, ferragens sugeridas e itens
complementares (fora do escopo de marcenaria) explicitos, e
auditoria_visual com bounding box no formato [y_min, x_min, y_max, x_max]
normalizado 0-1000 (convencao pedida para o frontend).

Extensao propria (nao fazia parte do schema pedido, mas preserva o
principio central do projeto de nunca deixar dado nao confirmado virar
orcamento): todo Modulo carrega `confianca` (0-1) e `origem` -- a
extracao So sai de aguardando_revisao para confirmado com confirmacao
humana explicita, exatamente como na v1."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class OrigemModulo(str, Enum):
    VISION_AUTOMATICO = "vision_automatico"      # extraido pelo MARC sem edicao
    CONFIRMADO_HUMANO = "confirmado_humano"       # usuario revisou e confirmou/corrigiu
    ADICIONADO_MANUAL = "adicionado_manual"       # usuario adicionou um modulo que o MARC nao pegou


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
    campos_inferidos: list[str] = Field(
        default_factory=list,
        description="Nomes destes campos (ex: 'metodo_uniao') que vieram das Preferencias Globais/regras "
        "do MARC, nao do proprio desenho -- nunca fica vazio silenciosamente quando algo foi inferido.",
    )


class FerragemSugerida(BaseModel):
    nome: str
    quantidade: int = Field(..., ge=0)


class ItemComplementar(BaseModel):
    """Elementos fora do escopo de marcenaria (regra 6 do MARC): pedra,
    espelho, serralheria, estofado, fita de LED, etc."""
    nome: str
    tipo: str


class Modulo(BaseModel):
    id: str = Field(..., description="Ex: 'MOD-001', unico dentro do job")
    nome: str
    vista_referencia: str = ""
    dimensoes: Dimensoes = Field(default_factory=Dimensoes)
    componentes: Componentes = Field(default_factory=Componentes)
    especificacoes_materiais: EspecificacoesMateriais
    ferragens_sugeridas: list[FerragemSugerida] = Field(default_factory=list)
    itens_complementares: list[ItemComplementar] = Field(default_factory=list)
    auditoria_visual: AuditoriaVisual
    descricao_resumida: str = ""

    # extensao propria do skill (ver docstring do modulo)
    confianca: float = Field(..., ge=0, le=1, description="Confianca do MARC nesta leitura (0-1). < 0.7 exige revisao humana antes de confirmar o job")
    origem: OrigemModulo = OrigemModulo.VISION_AUTOMATICO


class Ambiente(BaseModel):
    nome_ambiente: str
    modulos: list[Modulo] = Field(default_factory=list)


class StatusExtracao(str, Enum):
    PROCESSANDO = "processando"
    AGUARDANDO_REVISAO = "aguardando_revisao"     # extraido, mas precisa de revisao humana antes de confirmar
    CONFIRMADO = "confirmado"                     # humano revisou -- agora pode ir para o pricing_service
    ERRO = "erro"


class ExtracaoResultado(BaseModel):
    job_id: str
    projeto_id: str = ""
    arquivo_origem: str
    status: StatusExtracao
    ambientes: list[Ambiente] = Field(default_factory=list)
    avisos: list[str] = Field(default_factory=list, description="Ex: 'pagina 9: dois rotulos de acabamento sobrepostos, confirme manualmente'")
    criado_em: datetime
    atualizado_em: datetime
