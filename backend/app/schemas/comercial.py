"""Schemas Pydantic do dominio comercial (CRM, orcamentos comerciais,
fichas tecnicas, estoque, financeiro) -- os nomes de campo espelham
exatamente as colunas que o Supabase schema.sql do gestori ja usava
(snake_case), pra minimizar mudanca no mapeamento client-side em
src/lib/services.ts (so troca a fonte de `supabase.from(...)` pra
`api.get(...)`, sem remapear os campos)."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------
# CRM / Clientes
# --------------------------------------------------------------------------

class ClienteBase(BaseModel):
    nome: str
    empresa_cliente: str | None = None
    email: str
    telefone: str
    origem: str = "outro"
    status: str = "lead"
    valor_estimado: float = 0
    data_entrada: str
    data_ultima_atualizacao: str
    observacoes: str = ""
    responsavel_id: uuid.UUID | None = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: str | None = None
    empresa_cliente: str | None = None
    email: str | None = None
    telefone: str | None = None
    origem: str | None = None
    status: str | None = None
    valor_estimado: float | None = None
    data_ultima_atualizacao: str | None = None
    observacoes: str | None = None
    responsavel_id: uuid.UUID | None = None


class ClienteResponse(ClienteBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# Orcamentos comerciais
# --------------------------------------------------------------------------

class ItemOrcamentoComercial(BaseModel):
    id: str
    descricao: str
    quantidade: float
    unidade: str
    custo_unitario: float = Field(alias="custoUnitario")
    margem_pct: float = Field(alias="margemPct")
    preco_unitario: float = Field(alias="precoUnitario")
    total: float

    model_config = ConfigDict(populate_by_name=True)


class ParcelaOrcamentoComercial(BaseModel):
    numero: int
    vencimento: str
    valor: float
    pago: bool = False


class OrcamentoComercialCreate(BaseModel):
    cliente_id: uuid.UUID | None = None
    cliente_nome: str
    status: str = "rascunho"
    data_criacao: str
    data_validade: str
    itens: list[dict] = Field(default_factory=list)
    subtotal: float = 0
    desconto: float = 0
    margem_media: float = 0
    parcelas: list[dict] = Field(default_factory=list)
    observacoes: str = ""
    fichas_tecnicas_ids: list[str] = Field(default_factory=list)


class OrcamentoComercialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    numero: str
    cliente_id: uuid.UUID | None
    cliente_nome: str
    status: str
    data_criacao: str
    data_validade: str
    itens: list[dict]
    subtotal: float
    desconto: float
    total: float
    margem_media: float
    parcelas: list[dict]
    observacoes: str
    fichas_tecnicas_ids: list[str]


class OrcamentoComercialStatusUpdate(BaseModel):
    status: str


# --------------------------------------------------------------------------
# Fichas tecnicas
# --------------------------------------------------------------------------

class FichaTecnicaCreate(BaseModel):
    nome: str
    categoria: str
    descricao: str = ""
    tempo_producao_horas: float = 0
    custo_materiais: float = 0
    custo_mao_obra: float = 0
    insumos: list[dict] = Field(default_factory=list)
    imagem_url: str | None = None
    versao: int = 1


class FichaTecnicaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    categoria: str
    descricao: str
    tempo_producao_horas: float
    custo_materiais: float
    custo_mao_obra: float
    custo_total: float
    insumos: list[dict]
    imagem_url: str | None
    versao: int
    updated_at: datetime


# --------------------------------------------------------------------------
# Estoque
# --------------------------------------------------------------------------

class MovimentacaoEstoqueCreate(BaseModel):
    tipo: str
    quantidade: float
    referencia: str = ""


class MovimentacaoEstoqueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tipo: str
    quantidade: float
    referencia: str
    usuario_id: uuid.UUID | None
    created_at: datetime


class ItemEstoqueCreate(BaseModel):
    codigo: str
    nome: str
    categoria: str
    unidade: str
    quantidade_atual: float = 0
    quantidade_minima: float = 0
    quantidade_reservada: float = 0
    custo_unitario: float = 0
    fornecedor: str = ""
    localizacao: str = ""


class ItemEstoqueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    codigo: str
    nome: str
    categoria: str
    unidade: str
    quantidade_atual: float
    quantidade_minima: float
    quantidade_reservada: float
    custo_unitario: float
    fornecedor: str
    localizacao: str
    movimentacoes: list[MovimentacaoEstoqueResponse] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Financeiro
# --------------------------------------------------------------------------

class LancamentoFinanceiroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tipo: str
    categoria: str
    descricao: str
    valor: float
    data: str
    status: str
    orcamento_id: uuid.UUID | None
