"""Casa acabamentos em texto livre (extracao Vision) com linhas JA existentes
na tabela de precos, usando uma pergunta Choice do TypeSafe (modelo Jev).

Problema: `tabela_precos.chave_acabamento()` so entende o REFERENCE numerico
do Promob. Um material como "MDF Duratex Rosa Infinito 18mm" vindo do
Vision cai no fallback `(0, texto)` e nunca acha preco, mesmo a tabela tendo
a chapa. Aqui o modelo SELECIONA entre os acabamentos cadastrados -- nunca
gera preco. Sem candidato, sem confianca suficiente ou com erro de rede, o
acabamento continua pendente (SEM_PRECO_*), como antes.

O codigo decide: filtra candidatos por espessura, aplica o limiar e so
entao grava o alias. Alias e so a chave de agrupamento de
`calcular_projeto`; o preco continua vindo da tabela.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.engine.tabela_precos import (
    PrecoReferencia,
    chave_acabamento,
    indexar_precos_por_acabamento,
)

logger = logging.getLogger(__name__)

CHAVE_PERGUNTA = "acabamento"
OPCAO_NENHUM = "NENHUM"
# Os dois limiares sao pontos de partida -- calibrar com orcamentos reais
# (docs.typesafe.ai/confidence). Errar o casamento muda o preco, entao o
# limiar e alto de proposito.
LIMIAR_CONFIANCA_PADRAO = 0.7
LIMIAR_PROBABILIDADE_PADRAO = 0.6

ChaveAcabamento = tuple[int, str]


class ClienteSystemOne(Protocol):
    def system_one(self, *, state: Any, questions: Any) -> Any: ...


@dataclass
class CasamentoAcabamento:
    original: ChaveAcabamento
    escolhido: ChaveAcabamento | None
    confianca: float | None
    aceito: bool
    motivo: str


@dataclass
class ResultadoCasamento:
    aliases: dict[ChaveAcabamento, ChaveAcabamento] = field(default_factory=dict)
    casamentos: list[CasamentoAcabamento] = field(default_factory=list)

    def avisos(self) -> list[str]:
        """Texto para o orcamentista conferir -- todo alias aplicado e
        auditavel; sugestoes recusadas viram pendencia a revisar."""
        avisos = []
        for c in self.casamentos:
            origem = _rotulo(c.original)
            if c.aceito and c.escolhido:
                avisos.append(
                    f"Acabamento '{origem}' casado com '{_rotulo(c.escolhido)}' "
                    f"(confianca {c.confianca:.2f}) -- confira."
                )
            elif c.escolhido:
                avisos.append(
                    f"Acabamento '{origem}': melhor candidato '{_rotulo(c.escolhido)}' "
                    f"nao aceito ({c.motivo}); permanece sem preco."
                )
        return avisos


def _rotulo(chave: ChaveAcabamento) -> str:
    espessura, nome = chave
    return f"{espessura}mm {nome}" if espessura else nome


def _espessura_no_texto(texto: str) -> int | None:
    m = re.search(r"(\d{1,2})\s*mm", texto, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def _acabamentos_sem_preco(
    ambientes_json: list[dict],
    indice: dict[ChaveAcabamento, PrecoReferencia],
) -> dict[ChaveAcabamento, str]:
    """Acabamentos M2 usados no projeto e sem linha com preco de chapa na
    tabela. Retorna {chave: texto original}."""
    pendentes: dict[ChaveAcabamento, str] = {}
    for ambiente in ambientes_json:
        for modulo in ambiente["modulos"]:
            for item in modulo["itens"]:
                if item.get("unidade") != "M2":
                    continue
                ref = item.get("reference")
                if not ref:
                    continue
                chave = chave_acabamento(ref) or (0, ref)
                preco = indice.get(chave)
                if preco is None or preco.preco_chapa_fechada is None:
                    pendentes.setdefault(chave, ref)
    return pendentes


def _candidatos(
    indice: dict[ChaveAcabamento, PrecoReferencia],
    espessura: int | None,
) -> dict[str, ChaveAcabamento]:
    """Acabamentos cadastrados com preco de chapa, indexados pelo rotulo
    que o modelo ve. Espessura mencionada no texto restringe a lista:
    18mm nunca casa com 15mm."""
    candidatos: dict[str, ChaveAcabamento] = {}
    for chave, preco in indice.items():
        if preco.preco_chapa_fechada is None or chave[0] == 0:
            continue
        if espessura is not None and chave[0] != espessura:
            continue
        candidatos[_rotulo(chave)] = chave
    return candidatos


def resolver_acabamentos(
    ambientes_json: list[dict],
    tabela: dict[str, PrecoReferencia],
    cliente: ClienteSystemOne,
    limiar_confianca: float = LIMIAR_CONFIANCA_PADRAO,
    limiar_probabilidade: float = LIMIAR_PROBABILIDADE_PADRAO,
) -> ResultadoCasamento:
    from typesafe_sdk import Choice  # import tardio: modulo carrega sem o SDK

    resultado = ResultadoCasamento()
    indice = indexar_precos_por_acabamento(tabela)

    for chave, texto in _acabamentos_sem_preco(ambientes_json, indice).items():
        candidatos = _candidatos(indice, _espessura_no_texto(texto))
        if not candidatos:
            continue

        criterios: dict[str, str | None] = {rotulo: None for rotulo in candidatos}
        criterios[OPCAO_NENHUM] = (
            "Nenhum candidato e o mesmo material: cor/linha diferente, ou o "
            "texto e vago demais. Na duvida entre cores parecidas, escolha esta."
        )
        pergunta = Choice(
            instructions=(
                "Qual acabamento cadastrado corresponde ao material descrito em "
                "`material_projeto`? Considere fabricante, linha e nome da cor; "
                "ignore diferencas de maiusculas, abreviacoes e ordem das palavras. "
                "Cores diferentes (ex.: Rosa vs Grafite) NAO sao o mesmo material."
            ),
            criteria=criterios,
        )

        try:
            resposta = cliente.system_one(
                state={"material_projeto": texto},
                questions={CHAVE_PERGUNTA: pergunta},
            )
            resposta_escolha = resposta.choices[CHAVE_PERGUNTA]
        except Exception:  # falha de rede/API nunca derruba o orcamento
            logger.warning("Casamento de acabamento falhou para %r", texto, exc_info=True)
            resultado.casamentos.append(
                CasamentoAcabamento(chave, None, None, False, "servico indisponivel")
            )
            continue

        escolha = resposta_escolha.choice
        confianca = float(resposta_escolha.confidence)
        prob = float(resposta_escolha.probabilities.get(escolha, 0.0))

        if escolha == OPCAO_NENHUM or escolha not in candidatos:
            resultado.casamentos.append(
                CasamentoAcabamento(chave, None, confianca, False, "nenhum candidato")
            )
            continue

        escolhido = candidatos[escolha]
        if confianca < limiar_confianca or prob < limiar_probabilidade:
            resultado.casamentos.append(
                CasamentoAcabamento(
                    chave, escolhido, confianca, False,
                    f"confianca {confianca:.2f}, probabilidade {prob:.2f}",
                )
            )
            continue

        resultado.aliases[chave] = escolhido
        resultado.casamentos.append(
            CasamentoAcabamento(chave, escolhido, confianca, True, "ok")
        )

    return resultado
