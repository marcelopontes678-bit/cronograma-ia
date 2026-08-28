"""Auto-aprendizado: o marceneiro corrige uma leitura da IA em linguagem
natural (ex: "Sempre que houver porta de vidro reflecta, mude o fundo
para a cor da caixa"); isso e normalizado pela LLM em uma regra reusavel
e injetado no system prompt do Agente Extrator nas proximas execucoes
DESSE usuario.

Design consciente: a regra fica em linguagem natural (nao em codigo),
porque e isso que o prompt do extrator consome -- nao precisa de um
motor de regras separado, so precisa ser persistida e injetada.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    usuario_id: str
    job_id: str | None = Field(None, description="Job onde a correcao foi feita, para rastreabilidade")
    modulo_id: str | None = Field(None, description="Modulo especifico corrigido, se aplicavel")
    instrucao: str = Field(..., description='Texto livre do marceneiro, ex: "Sempre que houver porta de vidro reflecta, mude o fundo para a cor da caixa"')


class RegraAprendida(BaseModel):
    id: str
    usuario_id: str
    instrucao_original: str
    regra_normalizada: str = Field(..., description="Reescrita pela LLM em forma de instrucao de sistema, ex: 'Quando um modulo tiver porta com vidro reflecta, defina a cor do fundo igual a cor da caixa.'")
    origem_job_id: str | None = None
    origem_modulo_id: str | None = None
    ativa: bool = True
    criado_em: datetime


class FeedbackResponse(BaseModel):
    regra: RegraAprendida
    total_regras_ativas_usuario: int
