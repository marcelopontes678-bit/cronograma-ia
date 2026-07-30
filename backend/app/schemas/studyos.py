from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.studyos.intents import Intencao


class OrquestracaoRequest(BaseModel):
    solicitacao: str = Field(
        ...,
        min_length=3,
        max_length=4000,
        description="Pedido do usuário em linguagem natural",
    )
    dados_usuario: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Contexto conhecido do estudante: perfil, tempo_disponivel, objetivo, "
            "prazo, nivel_atual, historico"
        ),
    )
    intencao: Optional[Intencao] = Field(
        None,
        description="Força um workflow específico em vez de classificar o texto",
    )
    formato: str = Field(
        "json", description="'json' para a estrutura completa, 'markdown' para texto"
    )

    @field_validator("formato")
    @classmethod
    def validate_formato(cls, v: str) -> str:
        if v not in ("json", "markdown"):
            raise ValueError("Formato deve ser 'json' ou 'markdown'")
        return v


class AgenteExecutadoResponse(BaseModel):
    codigo: str
    nome: str
    fase: str
    tarefa: str
    onda: int
    status: str
    depende_de: list[str]
    duracao_ms: float
    detalhe: Optional[str] = None


class OndaResponse(BaseModel):
    onda: int
    paralelo: bool
    agentes: list[str]


class TarefaResponse(BaseModel):
    agente: str
    fase: str
    tarefa: str
    status: str


class OrquestracaoResponse(BaseModel):
    agentes_executados: list[AgenteExecutadoResponse]
    ordem_execucao: list[OndaResponse]
    tarefas_realizadas: list[TarefaResponse]
    resultado_consolidado: dict[str, Any]
    resposta_markdown: Optional[str] = None


class AgenteCatalogoResponse(BaseModel):
    codigo: str
    nome: str
    fase: str
    tarefa: str
    depende_de: list[str]
    obrigatorio: bool


class PlanoResponse(BaseModel):
    """Plano de execução sem rodar nenhum agente (dry run)."""

    intencao: str
    workflow: str
    intencao_por_fallback: bool
    agentes_selecionados: list[str]
    ordem_execucao: list[dict[str, Any]]
