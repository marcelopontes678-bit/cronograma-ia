"""Casa o nome de material em texto livre que o MARC le do PDF (ex: "MDF
Cinza Cobalto Berneck") com uma linha de chapa da tabela de precos.

Por que existe: a tabela de precos e indexada pelo REFERENCE do Promob
(ex: '2.2008.18.Branco.MDF', ver tabela_precos.chave_acabamento), mas a
extracao via Vision so tem o nome do material como aparece no desenho.
Sem esse casamento, todo modulo vindo de PDF caia em "sem preco".

Selecionar, nao gerar: o Claude so ESCOLHE uma das linhas que ja existem
na tabela (por indice), ou responde que nenhuma corresponde -- nunca
escreve um REFERENCE ou um preco. O codigo valida o indice e so aplica
casamentos com confianca >= LIMIAR_CONFIANCA_CASAMENTO; o resto fica
pendente, como qualquer material sem preco, para o marceneiro revisar.

Uma chamada por orcamento (todos os materiais distintos de uma vez), nao
uma por modulo."""
from __future__ import annotations

import json
from dataclasses import dataclass

from anthropic import Anthropic

from app.engine.tabela_precos import PrecoReferencia, chave_acabamento

MODELO_PADRAO = "claude-sonnet-5"
LIMIAR_CONFIANCA_CASAMENTO = 0.8

_SYSTEM_PROMPT = """\
Voce casa nomes de material de marcenaria, como aparecem em projetos \
(texto livre, as vezes abreviado ou com erro de digitacao), com as chapas \
cadastradas na tabela de precos de uma marcenaria.

Para cada material, escolha o indice da chapa da tabela que e o MESMO \
material, ou responda null quando nenhuma for. Criterios:
- Mesma cor/padrao e mesma linha do fabricante. Uma cor parecida NAO e o \
mesmo material: "Cinza Cobalto" nao casa com "Cinza Cristal".
- Fabricante citado no material precisa bater com o da chapa. Material \
sem fabricante pode casar com chapa de qualquer fabricante.
- Variacoes de nome do mesmo acabamento contam como iguais (ex: "Branco" \
e "Branco TX" em MDF branco comum).
- Espessura: se o material citar a espessura, ela precisa bater. Se nao \
citar, prefira a chapa com a espessura padrao de caixaria informada; se \
nao houver chapa nessa espessura, responda null.
- Na duvida entre duas chapas diferentes, responda null em vez de chutar.

`confianca` (0 a 1) e a sua certeza de que a escolha (ou o null) esta \
certa. Um orcamento errado custa dinheiro ao marceneiro; materiais que \
voce deixar null serao revisados por uma pessoa."""

_SCHEMA_RESPOSTA = {
    "type": "object",
    "properties": {
        "casamentos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "indice_material": {"type": "integer"},
                    "indice_chapa": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "confianca": {"type": "number"},
                },
                "required": ["indice_material", "indice_chapa", "confianca"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["casamentos"],
    "additionalProperties": False,
}


class CasamentoMaterialError(Exception):
    pass


@dataclass
class CasamentoMaterial:
    material: str
    chapa: PrecoReferencia | None  # None = nenhuma chapa da tabela corresponde
    confianca: float

    @property
    def aplicavel(self) -> bool:
        return self.chapa is not None and self.confianca >= LIMIAR_CONFIANCA_CASAMENTO


def precisa_casar(material: str, tabela: dict[str, PrecoReferencia]) -> bool:
    """True para nome em texto livre; False se ja e um REFERENCE da tabela
    ou segue o padrao Promob (nesses casos o motor ja sabe precificar)."""
    return bool(material) and material not in tabela and chave_acabamento(material) is None


def chapas_candidatas(tabela: dict[str, PrecoReferencia]) -> list[PrecoReferencia]:
    return [p for p in tabela.values() if p.unidade.upper() == "M2"]


def casar_materiais(
    materiais: list[str],
    candidatas: list[PrecoReferencia],
    espessura_padrao_caixa_mm: float | None,
    api_key: str,
    modelo: str = MODELO_PADRAO,
) -> dict[str, CasamentoMaterial]:
    """Retorna {material: CasamentoMaterial} para cada material da lista.
    Material que o modelo nao devolveu fica com chapa=None (pendente).
    Levanta CasamentoMaterialError em falha de API ou resposta invalida."""
    materiais = list(dict.fromkeys(materiais))
    resultado = {m: CasamentoMaterial(material=m, chapa=None, confianca=0.0) for m in materiais}
    if not materiais or not candidatas:
        return resultado

    entrada = {
        "espessura_padrao_caixaria_mm": espessura_padrao_caixa_mm,
        "chapas_da_tabela": [
            {
                "indice": i,
                "descricao": c.descricao,
                "reference": c.reference,
                "espessura_mm": c.espessura_mm,
                "fornecedor": c.fornecedor,
            }
            for i, c in enumerate(candidatas)
        ],
        "materiais_do_projeto": [{"indice": i, "nome": m} for i, m in enumerate(materiais)],
    }

    client = Anthropic(api_key=api_key)
    resposta = client.messages.create(
        model=modelo,
        max_tokens=8000,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(entrada, ensure_ascii=False, indent=2)}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": _SCHEMA_RESPOSTA}},
    )
    if resposta.stop_reason == "max_tokens":
        raise CasamentoMaterialError("Resposta cortada por max_tokens -- nenhum material foi casado.")
    if resposta.stop_reason == "refusal":
        raise CasamentoMaterialError("O modelo recusou a requisicao -- nenhum material foi casado.")

    texto = "".join(b.text for b in resposta.content if b.type == "text")
    try:
        casamentos = json.loads(texto)["casamentos"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise CasamentoMaterialError(f"Resposta fora do formato esperado: {texto[:500]!r}") from exc

    for c in casamentos:
        i_mat, i_chapa = c.get("indice_material"), c.get("indice_chapa")
        if not isinstance(i_mat, int) or not 0 <= i_mat < len(materiais):
            continue  # indice inventado -- ignora, o material fica pendente
        chapa = candidatas[i_chapa] if isinstance(i_chapa, int) and 0 <= i_chapa < len(candidatas) else None
        confianca = max(0.0, min(1.0, float(c.get("confianca") or 0.0)))
        resultado[materiais[i_mat]] = CasamentoMaterial(material=materiais[i_mat], chapa=chapa, confianca=confianca)

    return resultado
