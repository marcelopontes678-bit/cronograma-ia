"""Agent Communication Protocol (ACP) v1.0 — o formato único do StudyOS.

Nenhum agente cria formato próprio. Toda comunicação entre agentes passa por
uma `Mensagem` deste módulo, e toda execução produz um `Log`.

O protocolo formaliza uma topologia que o StudyOS já praticava por construção:
**nenhum agente conversa diretamente com outro**. Os agentes nunca se
importaram nem se chamaram — quem lê a saída de um e monta a entrada do
seguinte sempre foi o Master Orchestrator. O que muda aqui é que isso deixa de
ser convenção e vira invariante verificável: `Mensagem` exige remetente e
destinatário, e há um teste que reprova qualquer mensagem entre dois agentes
sem o orquestrador no caminho.

Duas decisões merecem registro:

* **`confidence` é derivada, não inventada.** Todo agente do StudyOS já
  declara `confiabilidade` como rótulo ("alta", "media", "baixa"). O protocolo
  pede um número entre 0 e 1 — e ele sai de uma tabela declarada sobre o
  rótulo que o agente já publicou, nunca de uma segunda avaliação. Um agente
  que queira ser mais preciso pode publicar `confidence` diretamente, e aí o
  número dele vence.
* **Mensagem inválida não é corrigida, é recusada.** Falta de campo
  obrigatório, prioridade fora da lista, confidence fora de [0, 1] — tudo
  levanta `MensagemInvalida`. Preencher o que falta seria inventar
  procedência.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

VERSAO = "1.0"

#: Identificador do orquestrador nas mensagens. Não é um agente numerado: é o
#: único ponto por onde o fluxo passa.
MASTER_ORCHESTRATOR = "master_orchestrator"


class Prioridade(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Status(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Acao(str, Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    UPDATE = "UPDATE"
    VALIDATION = "VALIDATION"
    RETRY = "RETRY"
    ERROR = "ERROR"
    FINISH = "FINISH"


#: Campos obrigatórios de toda mensagem, na ordem em que a spec os lista.
CAMPOS_OBRIGATORIOS: tuple[str, ...] = (
    "message_id",
    "workflow_id",
    "source_agent",
    "target_agent",
    "timestamp",
    "priority",
    "status",
    "action",
    "payload",
    "metadata",
)

#: Rótulo de confiabilidade que os agentes já publicam → confidence numérica.
#: A tabela existe para o protocolo não pedir uma segunda avaliação do que já
#: foi avaliado: o número é uma leitura do rótulo, não uma opinião nova.
CONFIDENCE_POR_CONFIABILIDADE: dict[str, float] = {
    "alta": 0.90,
    "media": 0.65,
    "baixa": 0.35,
    "indeterminada": 0.20,
    "indeterminado": 0.20,
    # "nenhuma" não é o mesmo que "baixa": é o agente dizendo que não produziu
    # nada sobre o que ter confiança.
    "nenhuma": 0.0,
}

#: Confidence de um agente que não declarou confiabilidade nenhuma. É baixa de
#: propósito: ausência de autoavaliação não é sinal de qualidade.
CONFIDENCE_SEM_DECLARACAO = 0.50

#: Confidence de um agente que falhou. Não é zero por convenção e sim porque
#: não há saída sobre a qual ter confiança.
CONFIDENCE_DE_FALHA = 0.0

#: Situações que autorizam reexecutar um agente. Fora destas três, o pedido é
#: recusado — inclusive quando parte do próprio agente.
MOTIVOS_DE_REEXECUCAO: tuple[str, ...] = (
    "autorizado_pelo_orquestrador",
    "reprovado_pelo_validator",
    "entradas_alteradas",
)


class MensagemInvalida(Exception):
    """Mensagem fora do protocolo. Não é corrigida: é recusada."""


class ComunicacaoDireta(Exception):
    """Dois agentes tentando conversar sem o orquestrador no caminho."""


class ReexecucaoNaoAutorizada(Exception):
    """Pedido de reexecução sem um dos três motivos previstos."""


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# Mensagem
# --------------------------------------------------------------------------- #


@dataclass
class Mensagem:
    """Envelope único de comunicação. Todos os dez campos são obrigatórios."""

    workflow_id: str
    source_agent: str
    target_agent: str
    action: Acao
    status: Status = Status.PENDING
    priority: Prioridade = Prioridade.NORMAL
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: f"msg-{uuid.uuid4().hex[:12]}")
    timestamp: str = field(default_factory=_agora)

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        if not self.workflow_id:
            raise MensagemInvalida("workflow_id é obrigatório")
        if not self.source_agent or not self.target_agent:
            raise MensagemInvalida("source_agent e target_agent são obrigatórios")
        if not isinstance(self.action, Acao):
            raise MensagemInvalida(f"ação fora do protocolo: {self.action!r}")
        if not isinstance(self.status, Status):
            raise MensagemInvalida(f"status fora do protocolo: {self.status!r}")
        if not isinstance(self.priority, Prioridade):
            raise MensagemInvalida(f"prioridade fora do protocolo: {self.priority!r}")
        if not isinstance(self.payload, dict) or not isinstance(self.metadata, dict):
            raise MensagemInvalida("payload e metadata precisam ser objetos")
        # A topologia é estrela: uma das pontas é sempre o orquestrador.
        if MASTER_ORCHESTRATOR not in (self.source_agent, self.target_agent):
            raise ComunicacaoDireta(
                f"{self.source_agent} → {self.target_agent}: nenhum agente conversa "
                "diretamente com outro; todo fluxo passa pelo Master Orchestrator"
            )

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "workflow_id": self.workflow_id,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "timestamp": self.timestamp,
            "priority": self.priority.value,
            "status": self.status.value,
            "action": self.action.value,
            "payload": self.payload,
            "metadata": {"protocolo": f"ACP v{VERSAO}", **self.metadata},
        }


# --------------------------------------------------------------------------- #
# Formato padrão de entrada e saída
# --------------------------------------------------------------------------- #


@dataclass
class EntradaPadrao:
    """O que o orquestrador entrega a um agente."""

    agent: str
    input: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    expected_output: str = ""

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "input": self.input,
            "context": self.context,
            "constraints": self.constraints,
            "expected_output": self.expected_output,
        }


@dataclass
class SaidaPadrao:
    """O que um agente devolve ao orquestrador."""

    agent: str
    status: Status
    confidence: float
    result: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    next_agents: list[str] = field(default_factory=list)
    logs: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.status, Status):
            raise MensagemInvalida(f"status fora do protocolo: {self.status!r}")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise MensagemInvalida(
                f"confidence precisa estar entre 0.00 e 1.00, veio {self.confidence!r}"
            )

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "status": self.status.value,
            "confidence": round(float(self.confidence), 2),
            "result": self.result,
            "recommendations": self.recommendations,
            "next_agents": self.next_agents,
            "logs": self.logs,
        }


def confidence_de(conteudo: dict, ok: bool = True) -> dict:
    """Confidence do agente, derivada do que ele mesmo declarou.

    Precedência: o número que o agente publicou vence o rótulo; o rótulo vence
    o padrão. Em nenhum ponto o protocolo avalia a saída por conta própria —
    ele lê a autoavaliação que já existe.
    """
    if not ok:
        return {
            "valor": CONFIDENCE_DE_FALHA,
            "base": "o agente falhou: não há saída sobre a qual ter confiança",
        }

    declarado = conteudo.get("confidence")
    if isinstance(declarado, (int, float)) and 0.0 <= float(declarado) <= 1.0:
        return {
            "valor": round(float(declarado), 2),
            "base": "confidence publicada pelo próprio agente",
        }

    rotulo = conteudo.get("confiabilidade")
    if isinstance(rotulo, str) and rotulo in CONFIDENCE_POR_CONFIABILIDADE:
        return {
            "valor": CONFIDENCE_POR_CONFIABILIDADE[rotulo],
            "base": f"derivada da confiabilidade '{rotulo}' declarada pelo agente",
        }

    return {
        "valor": CONFIDENCE_SEM_DECLARACAO,
        "base": "o agente não declarou confiabilidade; ausência não é sinal de qualidade",
    }


# --------------------------------------------------------------------------- #
# Logs e erros
# --------------------------------------------------------------------------- #


@dataclass
class Log:
    """Registro obrigatório de uma execução."""

    agent: str
    workflow_id: str
    horario: str
    tempo_de_execucao_ms: float
    entrada_recebida: list[str]
    saida_produzida: list[str]
    erros: list[str] = field(default_factory=list)
    agentes_acionados: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "workflow_id": self.workflow_id,
            "horario": self.horario,
            "tempo_de_execucao_ms": round(self.tempo_de_execucao_ms, 2),
            "entrada_recebida": self.entrada_recebida,
            "saida_produzida": self.saida_produzida,
            "erros": self.erros,
            "agentes_acionados": self.agentes_acionados,
        }


@dataclass
class Erro:
    """Falha registrada com motivo, responsável e impacto."""

    agent: str
    motivo: str
    impacto: str
    workflow_id: str
    replay_solicitado: bool = True

    def to_dict(self) -> dict:
        return {
            "agente_responsavel": self.agent,
            "motivo": self.motivo,
            "impacto": self.impacto,
            "workflow_id": self.workflow_id,
            "replay_solicitado_ao": MASTER_ORCHESTRATOR if self.replay_solicitado else None,
        }


def autorizar_reexecucao(motivo: str) -> str:
    """Porteiro dos três motivos previstos. Fora deles, o pedido é recusado."""
    if motivo not in MOTIVOS_DE_REEXECUCAO:
        raise ReexecucaoNaoAutorizada(
            f"motivo '{motivo}' não autoriza reexecução; previstos: "
            + ", ".join(MOTIVOS_DE_REEXECUCAO)
        )
    return motivo


# --------------------------------------------------------------------------- #
# Memória
# --------------------------------------------------------------------------- #


@dataclass
class MemoriaLocal:
    """Memória de um agente, viva apenas durante a execução dele.

    O `encerrar` é o ponto do protocolo: o que o agente anotou para si morre
    com a execução. Sem isso, "memória local" seria só um nome para estado
    global.
    """

    agent: str
    _dados: dict[str, Any] = field(default_factory=dict)
    _encerrada: bool = False

    def anotar(self, chave: str, valor: Any) -> None:
        if self._encerrada:
            raise MensagemInvalida(
                f"memória local de {self.agent} já foi encerrada com a execução"
            )
        self._dados[chave] = valor

    def ler(self, chave: str, padrao: Any = None) -> Any:
        if self._encerrada:
            raise MensagemInvalida(
                f"memória local de {self.agent} já foi encerrada com a execução"
            )
        return self._dados.get(chave, padrao)

    def encerrar(self) -> None:
        self._dados.clear()
        self._encerrada = True

    @property
    def ativa(self) -> bool:
        return not self._encerrada


class MemoriaCompartilhada:
    """Memória do fluxo: escrita só pelo orquestrador, leitura por todos.

    A spec do protocolo chegou truncada nesta seção. O comportamento aqui é o
    único compatível com as regras que estão inteiras — "nenhum agente pode
    alterar a saída de outro" e "todo fluxo passa pelo Master Orchestrator" —,
    e está declarado em vez de presumido em silêncio: agente escreve na
    memória compartilhada apenas através do orquestrador.
    """

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self._dados: dict[str, Any] = {}

    def publicar(self, autor: str, chave: str, valor: Any) -> None:
        if autor != MASTER_ORCHESTRATOR:
            raise ComunicacaoDireta(
                f"{autor} tentou escrever na memória compartilhada; só o Master "
                "Orchestrator publica"
            )
        self._dados[chave] = valor

    def ler(self, chave: str, padrao: Any = None) -> Any:
        return self._dados.get(chave, padrao)

    def como_dicionario(self) -> dict[str, Any]:
        # Cópia: quem lê não altera o que o orquestrador publicou.
        return dict(self._dados)


__all__ = [
    "CAMPOS_OBRIGATORIOS",
    "CONFIDENCE_DE_FALHA",
    "CONFIDENCE_POR_CONFIABILIDADE",
    "CONFIDENCE_SEM_DECLARACAO",
    "MASTER_ORCHESTRATOR",
    "MOTIVOS_DE_REEXECUCAO",
    "VERSAO",
    "Acao",
    "ComunicacaoDireta",
    "EntradaPadrao",
    "Erro",
    "Log",
    "MemoriaCompartilhada",
    "MemoriaLocal",
    "Mensagem",
    "MensagemInvalida",
    "Prioridade",
    "ReexecucaoNaoAutorizada",
    "SaidaPadrao",
    "Status",
    "autorizar_reexecucao",
    "confidence_de",
]
