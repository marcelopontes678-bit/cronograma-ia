"""Redator real: conecta os agentes 07–11, 13 e 16 a um modelo de verdade.

Até aqui, "redator" era um parâmetro que os testes preenchiam com uma lambda
determinística. Este módulo é a primeira implementação que fala com um modelo
de fato — a API de Mensagens da Anthropic, chamada por HTTP puro (o projeto já
depende de `httpx`; não foi preciso adicionar o SDK).

Quatro decisões estruturais:

* **O redator escreve; o agente continua decidindo.** Nenhuma regra migrou
  para cá. Limite de palavras, exigência de gabarito, recall ativo no
  flashcard, presença literal dos conceitos-chave no resumo — tudo isso
  continua sendo validado por `montar()` em cada agente, do mesmo jeito que
  validava a lambda de teste. Se o modelo devolver algo fora da régua, a saída
  vira `pendente_de_redacao` como sempre virou — nunca "quase certo".
* **A saída é forçada por *tool use*, não por prosa.** Cada redator declara
  uma ferramenta cujo `input_schema` é exatamente a chave que o `montar()` do
  agente espera. Isso elimina o parsing frágil de JSON solto em texto: o que
  volta é o argumento estruturado da chamada de ferramenta.
* **Sem chave de API, não há redator — não um redator falso.** `redatores_reais()`
  devolve `{}` quando `ANTHROPIC_API_KEY` não está configurada. Um dicionário
  vazio é o mesmo que "nenhum redator conectado" para o `RunnerEstrutural`, e o
  motor volta exatamente ao comportamento determinístico que já tinha.
* **Falha de rede é declinada, não inventada.** Erro HTTP, timeout ou resposta
  sem a ferramenta esperada fazem o redator devolver `{}` para aquele agente —
  o mesmo "nada preenchido por invenção" que já valia quando não havia modelo
  nenhum. A falha é registrada em log para quem opera o serviço, não para o
  estudante.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx

from app.studyos.agentes.comum import como_texto

LOGGER = logging.getLogger("studyos.redator")

API_URL = "https://api.anthropic.com/v1/messages"
VERSAO_DA_API = "2023-06-01"

#: Sonnet é o padrão: qualidade suficiente para texto didático estruturado,
#: sem o custo/latência de rodar em opus a cada seção de cada aula. Trocável
#: por variável de ambiente sem tocar em código.
MODELO_PADRAO = "claude-sonnet-5"
MAX_TOKENS_PADRAO = 4096
TIMEOUT_PADRAO_S = 60.0
TENTATIVAS_PADRAO = 2

#: Status HTTP que valem nova tentativa — instabilidade transitória, não erro
#: de payload. 4xx fora do 429 é erro nosso (schema, autenticação); repetir
#: não ajudaria.
STATUS_COM_NOVA_TENTATIVA = (408, 409, 429, 500, 502, 503, 504)

SISTEMA_COMUM = (
    "Você é o redator de conteúdo do StudyOS, um sistema de estudo com 24 "
    "agentes especializados. Você foi acionado por um agente específico para "
    "escrever exatamente o que ele pediu — nada além disso. Responda em "
    "português do Brasil, sempre e apenas através da ferramenta fornecida. "
    "Nunca produza texto fora da chamada de ferramenta."
)


class RespostaSemFerramenta(Exception):
    """O modelo respondeu, mas não usou a ferramenta que foi forçada."""


# --------------------------------------------------------------------------- #
# Configuração e chamada ao modelo
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ConfiguracaoDoRedator:
    """Tudo que uma chamada ao modelo precisa saber."""

    api_key: str
    modelo: str = MODELO_PADRAO
    max_tokens: int = MAX_TOKENS_PADRAO
    timeout_s: float = TIMEOUT_PADRAO_S
    tentativas: int = TENTATIVAS_PADRAO


def configuracao_do_ambiente() -> ConfiguracaoDoRedator | None:
    """Lê a configuração de variáveis de ambiente — `None` se não houver chave.

    Lida diretamente do `os.environ`, não de `app.config.Settings`: o pacote
    `studyos` não depende do resto da aplicação (nem de banco, nem de
    autenticação), e essa independência é o que permite testar o orquestrador
    e a API sem exigir `DATABASE_URL`. Importar `Settings` aqui quebraria isso.
    """
    chave = os.environ.get("ANTHROPIC_API_KEY")
    if not chave:
        return None
    return ConfiguracaoDoRedator(
        api_key=chave,
        modelo=os.environ.get("STUDYOS_REDATOR_MODELO", MODELO_PADRAO),
    )


def _chamar_ferramenta(
    config: ConfiguracaoDoRedator,
    sistema: str,
    usuario: str,
    nome_da_ferramenta: str,
    schema: dict,
) -> dict | None:
    """Uma chamada de ferramenta forçada. `None` em qualquer falha — nunca inventa.

    Não há re-tentativa "silenciosamente infinita": `config.tentativas` é o
    teto, e cada falha fica no log com o motivo, para quem opera o serviço
    diagnosticar sem esse detalhe vazar para o estudante.
    """
    payload = {
        "model": config.modelo,
        "max_tokens": config.max_tokens,
        "system": sistema,
        "messages": [{"role": "user", "content": usuario}],
        "tools": [
            {
                "name": nome_da_ferramenta,
                "description": schema.get("description", nome_da_ferramenta),
                "input_schema": schema,
            }
        ],
        "tool_choice": {"type": "tool", "name": nome_da_ferramenta},
    }
    headers = {
        "x-api-key": config.api_key,
        "anthropic-version": VERSAO_DA_API,
        "content-type": "application/json",
    }

    ultimo_erro: Exception | None = None
    for tentativa in range(1, config.tentativas + 1):
        #: ``raise_for_status()`` levanta ``HTTPStatusError`` — subclasse de
        #: ``HTTPError`` — para *qualquer* 4xx/5xx. Sem esta flag, o ``except``
        #: genérico abaixo repetiria também erro de autenticação ou de schema,
        #: que nova tentativa nunca resolve.
        repetivel = True
        try:
            with httpx.Client(timeout=config.timeout_s) as cliente:
                resposta = cliente.post(API_URL, headers=headers, json=payload)
            if resposta.status_code >= 400:
                repetivel = resposta.status_code in STATUS_COM_NOVA_TENTATIVA
            resposta.raise_for_status()
            corpo = resposta.json()
            return _extrair_ferramenta(corpo, nome_da_ferramenta)
        except (httpx.HTTPError, RespostaSemFerramenta, json.JSONDecodeError) as exc:
            ultimo_erro = exc
            LOGGER.warning(
                "redator: tentativa %s/%s falhou para '%s': %s",
                tentativa, config.tentativas, nome_da_ferramenta, exc,
            )
            if not repetivel:
                break
            if tentativa < config.tentativas:
                time.sleep(min(2 ** tentativa, 8))

    LOGGER.error(
        "redator: '%s' sem resposta utilizável após %s tentativa(s): %s",
        nome_da_ferramenta, config.tentativas, ultimo_erro,
    )
    return None


def _extrair_ferramenta(corpo: dict, nome_da_ferramenta: str) -> dict:
    for bloco in corpo.get("content", []):
        if bloco.get("type") == "tool_use" and bloco.get("name") == nome_da_ferramenta:
            entrada = bloco.get("input")
            if isinstance(entrada, dict):
                return entrada
    raise RespostaSemFerramenta(
        f"resposta sem bloco tool_use de '{nome_da_ferramenta}': "
        f"stop_reason={corpo.get('stop_reason')!r}"
    )


def _texto(descricao: str) -> dict:
    return {"type": "string", "description": descricao}


# --------------------------------------------------------------------------- #
# 07 — Lesson Generator
# --------------------------------------------------------------------------- #


def _ferramenta_aula(briefing: dict) -> dict:
    propriedades: dict[str, Any] = {}
    obrigatorias: list[str] = []
    for secao in briefing["secoes"]:
        chave, instrucao = secao["chave"], f"{secao['etapa']}: {secao['instrucao']}"
        if chave == "pontos_chave":
            propriedades[chave] = {
                "type": "array",
                "items": {"type": "string"},
                "description": instrucao + " Cada item é um termo ou fato, não uma frase.",
            }
        else:
            propriedades[chave] = _texto(instrucao)
        obrigatorias.append(chave)
    return {
        "description": "Escreve a aula completa, seção por seção.",
        "type": "object",
        "properties": propriedades,
        "required": obrigatorias,
        "additionalProperties": False,
    }


def _prompt_aula(briefing: dict) -> str:
    return json.dumps(
        {
            "tarefa": "Escrever a aula abaixo, seção por seção, na estrutura exigida.",
            "titulo": briefing["titulo"],
            "objetivo": briefing["objetivo"],
            "nivel_do_estudante": briefing["nivel_do_estudante"],
            "estilo_de_aprendizagem": briefing["estilo_de_aprendizagem"],
            "pre_requisitos_ja_dominados": briefing["pre_requisitos"],
            "diretrizes": briefing["diretrizes"],
            "proibicoes": briefing["proibicoes"],
        },
        ensure_ascii=False,
    )


def redator_aula(briefing: dict, config: ConfiguracaoDoRedator) -> dict:
    resultado = _chamar_ferramenta(
        config, SISTEMA_COMUM, _prompt_aula(briefing), "escrever_aula", _ferramenta_aula(briefing)
    )
    if resultado is None:
        return {}
    if isinstance(resultado.get("pontos_chave"), list):
        resultado["pontos_chave"] = [str(p) for p in resultado["pontos_chave"]]
    return resultado


# --------------------------------------------------------------------------- #
# 08 — Example Generator
# --------------------------------------------------------------------------- #


def _ferramenta_exemplos(briefing: dict) -> dict:
    propriedades: dict[str, Any] = {
        "observacoes_importantes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Ressalvas curtas sobre os exemplos, se houver alguma.",
        }
    }
    obrigatorias: list[str] = []
    for slot in briefing["slots"]:
        if not slot["aplicavel"]:
            continue
        propriedades[slot["chave"]] = {
            "type": "object",
            "description": f"Nível {slot['nivel']}: {slot['instrucao']}",
            "properties": {
                "enunciado": _texto("O exemplo em si."),
                "por_que_funciona": _texto("Por que este exemplo ilustra o conceito."),
            },
            "required": ["enunciado", "por_que_funciona"],
            "additionalProperties": False,
        }
        obrigatorias.append(slot["chave"])
    return {
        "description": "Escreve o conjunto de exemplos aplicáveis a este conteúdo.",
        "type": "object",
        "properties": propriedades,
        "required": obrigatorias,
        "additionalProperties": False,
    }


def _prompt_exemplos(briefing: dict) -> str:
    return json.dumps(
        {
            "tarefa": "Escrever os exemplos abaixo, consistentes com a teoria de referência.",
            "conceito_abordado": briefing["conceito_abordado"],
            "teoria_de_referencia": briefing["teoria_de_referencia"],
            "nivel_do_estudante": briefing["aula"]["nivel_do_estudante"],
            "diretrizes": briefing["diretrizes"],
            "proibicoes": briefing["proibicoes"],
        },
        ensure_ascii=False,
    )


def redator_exemplos(briefing: dict, config: ConfiguracaoDoRedator) -> dict:
    resultado = _chamar_ferramenta(
        config, SISTEMA_COMUM, _prompt_exemplos(briefing), "escrever_exemplos",
        _ferramenta_exemplos(briefing),
    )
    return resultado if resultado is not None else {}


# --------------------------------------------------------------------------- #
# 09 — Exercise Generator
# --------------------------------------------------------------------------- #


def _ferramenta_exercicios() -> dict:
    return {
        "description": "Escreve a bateria de exercícios, uma entrada por questão.",
        "type": "object",
        "properties": {
            "questoes": {
                "type": "array",
                "description": "Uma questão por slot pedido, na mesma ordem.",
                "items": {
                    "type": "object",
                    "properties": {
                        "numero": {"type": "integer", "description": "O número do slot."},
                        "enunciado": _texto("O enunciado da questão."),
                        "alternativas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Alternativas, se o formato pedir múltipla escolha.",
                        },
                        "resposta": _texto("A resposta correta ou o gabarito esperado."),
                        "explicacao": _texto("Por que essa é a resposta correta."),
                        "erro_comum_alvo": _texto(
                            "O erro comum que esta questão foi desenhada para detectar."
                        ),
                    },
                    "required": ["numero", "enunciado", "resposta", "explicacao"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["questoes"],
        "additionalProperties": False,
    }


def _prompt_exercicios(briefing: dict) -> str:
    return json.dumps(
        {
            "tarefa": "Escrever uma questão para cada slot abaixo, respeitando categoria e formato.",
            "objetivo": briefing["objetivo"],
            "nivel_do_estudante": briefing["nivel_do_estudante"],
            "referencia": briefing["referencia"],
            "slots": briefing["slots"],
            "diretrizes": briefing["diretrizes"],
            "proibicoes": briefing["proibicoes"],
        },
        ensure_ascii=False,
    )


def redator_exercicios(briefing: dict, config: ConfiguracaoDoRedator) -> dict:
    resultado = _chamar_ferramenta(
        config, SISTEMA_COMUM, _prompt_exercicios(briefing), "escrever_exercicios",
        _ferramenta_exercicios(),
    )
    return _por_numero(resultado, "questoes") if resultado is not None else {}


def _por_numero(resultado: dict, chave_da_lista: str) -> dict:
    """Converte `{chave_da_lista: [{"numero": N, ...}, ...]}` em `{N: {...}}`.

    Pedir ao modelo uma lista de objetos com `numero` em vez de um dicionário
    com chaves dinâmicas é o que faz o *tool use* funcionar de forma
    confiável — schemas com chave numérica variável são frágeis. A conversão
    de volta para o formato que `montar()` espera acontece aqui, uma vez só.
    """
    itens = resultado.get(chave_da_lista)
    if not isinstance(itens, list):
        return {}
    por_numero: dict[int, dict] = {}
    for item in itens:
        if not isinstance(item, dict):
            continue
        numero = item.get("numero")
        if not isinstance(numero, int):
            continue
        por_numero[numero] = {k: v for k, v in item.items() if k != "numero"}
    return por_numero


# --------------------------------------------------------------------------- #
# 10 — Flashcard Generator
# --------------------------------------------------------------------------- #


def _ferramenta_flashcards() -> dict:
    return {
        "description": "Escreve o baralho de flashcards, um cartão por slot.",
        "type": "object",
        "properties": {
            "cartoes": {
                "type": "array",
                "description": "Um cartão por slot pedido, na mesma ordem.",
                "items": {
                    "type": "object",
                    "properties": {
                        "numero": {"type": "integer", "description": "O número do slot."},
                        "pergunta": _texto(
                            "A frente do cartão. Para tipos que exigem interrogação "
                            "(todos exceto cloze, verdadeiro_ou_falso, associacao e "
                            "sequencia_logica), termina com '?'. Para cloze, contém '___'."
                        ),
                        "resposta": _texto(
                            "O verso do cartão, em até 25 palavras e uma única ideia."
                        ),
                        "explicacao_complementar": _texto(
                            "Complemento opcional, só se agregar depois da resposta direta."
                        ),
                    },
                    "required": ["numero", "pergunta", "resposta"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["cartoes"],
        "additionalProperties": False,
    }


def _prompt_flashcards(briefing: dict) -> str:
    return json.dumps(
        {
            "tarefa": "Escrever um cartão para cada slot abaixo, seguindo a instrução de cada um.",
            "referencia": briefing["referencia"],
            "limites": briefing["limites"],
            "slots": briefing["slots"],
            "diretrizes": briefing["diretrizes"],
            "proibicoes": briefing["proibicoes"],
        },
        ensure_ascii=False,
    )


def redator_flashcards(briefing: dict, config: ConfiguracaoDoRedator) -> dict:
    resultado = _chamar_ferramenta(
        config, SISTEMA_COMUM, _prompt_flashcards(briefing), "escrever_flashcards",
        _ferramenta_flashcards(),
    )
    return _por_numero(resultado, "cartoes") if resultado is not None else {}


# --------------------------------------------------------------------------- #
# 11 — Summary Generator
# --------------------------------------------------------------------------- #


def _ferramenta_resumos(briefing: dict) -> dict:
    propriedades: dict[str, Any] = {}
    obrigatorias: list[str] = []
    for secao in briefing["secoes"]:
        if not secao["aplicavel"]:
            continue
        chave, instrucao = secao["chave"], secao["instrucao"]
        if secao["limite_palavras"]:
            instrucao += f" Limite rígido: até {secao['limite_palavras']} palavras."
        if chave == "resumo_completo":
            termos = ", ".join(briefing["conceitos_chave"])
            instrucao += (
                f" Precisa citar literalmente, em algum ponto do texto, cada um destes "
                f"termos (maiúscula/minúscula e acento não importam): {termos}."
            )
        propriedades[chave] = _texto(instrucao)
        obrigatorias.append(chave)
    return {
        "description": "Escreve as seções de resumo aplicáveis a este conteúdo.",
        "type": "object",
        "properties": propriedades,
        "required": obrigatorias,
        "additionalProperties": False,
    }


def _prompt_resumos(briefing: dict) -> str:
    return json.dumps(
        {
            "tarefa": (
                "Escrever as seções de resumo abaixo. resumo_1min < resumo_5min < "
                "resumo_completo em quantidade de palavras — cada nível é mais "
                "detalhado que o anterior, nunca mais curto."
            ),
            "objetivo": briefing["objetivo"],
            "conceitos_chave": briefing["conceitos_chave"],
            "fonte": briefing["fonte"],
            "diretrizes": briefing["diretrizes"],
            "proibicoes": briefing["proibicoes"],
        },
        ensure_ascii=False,
    )


def redator_resumos(briefing: dict, config: ConfiguracaoDoRedator) -> dict:
    resultado = _chamar_ferramenta(
        config, SISTEMA_COMUM, _prompt_resumos(briefing), "escrever_resumos",
        _ferramenta_resumos(briefing),
    )
    return resultado if resultado is not None else {}


# --------------------------------------------------------------------------- #
# 13 — Adaptive Teacher
# --------------------------------------------------------------------------- #


def _ferramenta_adaptativo(briefing: dict) -> dict:
    propriedades: dict[str, Any] = {}
    obrigatorias: list[str] = []
    for slot in briefing["slots"]:
        if not slot["aplicavel"]:
            continue
        instrucao = slot["instrucao"]
        if slot.get("quantidade"):
            instrucao += f" Quantidade pedida: {slot['quantidade']}."
        propriedades[slot["chave"]] = _texto(instrucao)
        obrigatorias.append(slot["chave"])
    return {
        "description": "Escreve a experiência de ensino adaptada a este estudante.",
        "type": "object",
        "properties": propriedades,
        "required": obrigatorias,
        "additionalProperties": False,
    }


def _prompt_adaptativo(briefing: dict) -> str:
    return json.dumps(
        {
            "tarefa": "Reescrever o conteúdo pela estratégia e nível abaixo — mesma teoria, nova abordagem.",
            "objetivo_da_sessao": briefing["objetivo_da_sessao"],
            "estrategia_didatica": briefing["estrategia_didatica"],
            "nivel_de_dominio": briefing["nivel_de_dominio"],
            "perfil_de_aprendizagem": briefing["perfil_de_aprendizagem"],
            "sinais_de_confusao": briefing["sinais_de_confusao"],
            "teoria_de_referencia": briefing["teoria_de_referencia"],
            "proibicoes": briefing["proibicoes"],
        },
        ensure_ascii=False,
    )


def redator_adaptativo(briefing: dict, config: ConfiguracaoDoRedator) -> dict:
    resultado = _chamar_ferramenta(
        config, SISTEMA_COMUM, _prompt_adaptativo(briefing), "escrever_experiencia_adaptada",
        _ferramenta_adaptativo(briefing),
    )
    return resultado if resultado is not None else {}


# --------------------------------------------------------------------------- #
# 16 — Exam Simulator
# --------------------------------------------------------------------------- #


def _slots_sem_banco(briefing: dict) -> list[dict]:
    """Só os slots que o banco do agente 09 não cobre — reaproveitar, não regerar.

    `montar()` já tenta o banco antes de aceitar a redação (`_do_banco`); pedir
    ao modelo uma questão que o banco supriria seria regerar o que o agente 16
    promete reaproveitar. Reproduz a mesma chave `topico|dificuldade` e o mesmo
    consumo por ordem que `_do_banco` usa, para a exclusão bater exatamente com
    o que `montar()` vai de fato aproveitar do banco.
    """
    banco = {chave: list(itens) for chave, itens in briefing.get("banco_disponivel", {}).items()}
    usados: set[str] = set()
    pendentes: list[dict] = []
    for slot in briefing["slots"]:
        chave = f"{como_texto(slot['topico'])}|{como_texto(slot['dificuldade'])}"
        coberto = False
        for questao in banco.get(chave, []):
            marca = como_texto(questao["enunciado"])
            if marca not in usados:
                usados.add(marca)
                coberto = True
                break
        if not coberto:
            pendentes.append(slot)
    return pendentes


def _ferramenta_simulado() -> dict:
    return {
        "description": "Escreve as questões do simulado que o banco do agente 09 não cobre.",
        "type": "object",
        "properties": {
            "questoes": {
                "type": "array",
                "description": "Uma questão por slot pedido, na mesma ordem.",
                "items": {
                    "type": "object",
                    "properties": {
                        "numero": {"type": "integer", "description": "O número do slot."},
                        "enunciado": _texto("O enunciado da questão."),
                        "alternativas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Alternativas, se a prova pedir múltipla escolha.",
                        },
                        "resposta": _texto("A resposta correta."),
                        "explicacao": _texto("Por que essa é a resposta correta."),
                    },
                    "required": ["numero", "enunciado", "resposta"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["questoes"],
        "additionalProperties": False,
    }


def _prompt_simulado(briefing: dict, slots: list[dict]) -> str:
    return json.dumps(
        {
            "tarefa": "Escrever uma questão para cada slot abaixo, no grau de dificuldade indicado.",
            "objetivo": briefing["objetivo"],
            "banca": briefing["banca"],
            "correcao": briefing["correcao"],
            "slots": slots,
            "proibicoes": briefing["proibicoes"],
        },
        ensure_ascii=False,
    )


def redator_simulado(briefing: dict, config: ConfiguracaoDoRedator) -> dict:
    pendentes = _slots_sem_banco(briefing)
    if not pendentes:
        # Banco cobre o simulado inteiro: nenhuma chamada ao modelo é necessária.
        return {}
    resultado = _chamar_ferramenta(
        config, SISTEMA_COMUM, _prompt_simulado(briefing, pendentes), "escrever_simulado",
        _ferramenta_simulado(),
    )
    return _por_numero(resultado, "questoes") if resultado is not None else {}


# --------------------------------------------------------------------------- #
# Fábrica pública
# --------------------------------------------------------------------------- #

#: Código do agente → função que recebe o briefing e a configuração e devolve
#: o dicionário redigido — a mesma assinatura que as lambdas de teste sempre
#: tiveram, só que com uma chamada real por trás.
_CONSTRUTORES: dict[str, Callable[[dict, ConfiguracaoDoRedator], dict]] = {
    "07": redator_aula,
    "08": redator_exemplos,
    "09": redator_exercicios,
    "10": redator_flashcards,
    "11": redator_resumos,
    "13": redator_adaptativo,
    "16": redator_simulado,
}


def redatores_reais(
    config: ConfiguracaoDoRedator | None = None,
) -> dict[str, Callable[[dict], dict]]:
    """Monta `{codigo: redator}` pronto para `RunnerEstrutural(redatores=...)`.

    Sem configuração (nenhuma passada e nenhuma em `ANTHROPIC_API_KEY`),
    devolve `{}` — o `RunnerEstrutural` trata isso exatamente como "nenhum
    redator conectado", preservando o motor determinístico como está hoje.
    """
    config = config or configuracao_do_ambiente()
    if config is None:
        return {}
    return {
        codigo: (lambda briefing, _f=funcao: _f(briefing, config))
        for codigo, funcao in _CONSTRUTORES.items()
    }


__all__ = [
    "API_URL",
    "MAX_TOKENS_PADRAO",
    "MODELO_PADRAO",
    "TENTATIVAS_PADRAO",
    "TIMEOUT_PADRAO_S",
    "ConfiguracaoDoRedator",
    "RespostaSemFerramenta",
    "configuracao_do_ambiente",
    "redatores_reais",
]
