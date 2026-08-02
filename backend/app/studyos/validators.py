"""Agente 24 — Validators.

Única responsabilidade: auditar o que os outros agentes produziram antes de
qualquer coisa chegar ao estudante. Não ensina, não cria conteúdo, não
modifica resposta, não monta cronograma.

A validação é **estrutural e comparativa, nunca generativa**. Ela não sabe se
uma aula está boa: sabe se a aula que o agente 07 devolveu tem os campos que o
07 promete ter, se o conteúdo dela estava liberado pelo grafo, e se o número
que ela cita bate com o número publicado pelo agente que o mediu. Por isso
roda sempre no motor, mesmo quando os demais agentes estão plugados a um
modelo.

Três decisões estruturais:

* **O validador não toca em nada.** `validar` recebe as saídas e devolve um
  laudo; nenhuma saída é corrigida, completada ou reescrita. Há um teste que
  compara as saídas antes e depois por igualdade profunda — se o validador
  mexer, ele falha.
* **Nada é inventado para tapar buraco.** Campo ausente vira problema
  declarado, não valor padrão. É a mesma regra que os outros 23 agentes
  seguem, aplicada a quem os audita.
* **Contradição entre agentes é o alvo principal.** O sistema inteiro foi
  construído para que cada número tenha um dono só — consistência mora no 19,
  fragilidade no 18, ganho de alavanca no 22. Aqui essas invariantes deixam de
  ser disciplina de implementação e viram verificação em tempo de execução: se
  dois agentes discordarem sobre o mesmo fato, o fluxo é reprovado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.studyos.agents import AGENTES_OBRIGATORIOS, AgentResult, get_agent
from app.studyos.graph import dependencias_efetivas, ondas_de_execucao

# --------------------------------------------------------------------------- #
# Constantes declaradas
# --------------------------------------------------------------------------- #

STATUS_APROVADA = "APROVADA"
STATUS_COM_RESSALVAS = "APROVADA_COM_RESSALVAS"
STATUS_REPROVADA = "REPROVADA"

CATEGORIAS = (
    "estrutural",
    "consistencia",
    "pedagogica",
    "tecnica",
    "qualidade",
    "seguranca",
    "performance",
)

#: Gravidades: a bloqueante reprova o fluxo, a ressalva apenas o marca.
GRAVIDADE_BLOQUEANTE = "bloqueante"
GRAVIDADE_RESSALVA = "ressalva"
GRAVIDADES = (GRAVIDADE_BLOQUEANTE, GRAVIDADE_RESSALVA)

#: Campos que toda saída de agente do StudyOS declara: quem consome aquela
#: saída e o que o agente registrou sobre ela.
CAMPOS_OBRIGATORIOS_COMUNS = ("consumido_por", "observacoes")

#: Status que indicam produção incompleta — não são erro, mas a resposta não
#: pode ser entregue como se estivesse pronta.
STATUS_INCOMPLETOS = ("pendente_de_geracao", "pendente_de_redacao", "bloqueado")

#: Pares de valores que **precisam** bater porque descrevem o mesmo fato. É a
#: tradução em verificação das invariantes que o sistema mantém por construção.
INVARIANTES: tuple[tuple[str, tuple[str, ...], str, tuple[str, ...], str], ...] = (
    (
        "19", ("resumo_geral", "indice_de_consistencia"),
        "21", ("indicadores_de_aprendizagem", "consistencia", "valor"),
        "índice de consistência",
    ),
    (
        "18", ("resumo_geral", "indice_geral_de_fragilidade"),
        "21", ("indicadores_de_aprendizagem", "fragilidade_geral", "valor"),
        "índice geral de fragilidade",
    ),
    (
        "19", ("resumo_geral", "nivel_de_engajamento"),
        "21", ("indicadores_comportamentais", "engajamento", "valor"),
        "nível de engajamento",
    ),
    (
        "21", ("metricas_para_previsao", "taxa_de_acertos"),
        "22", ("estado_observado", "acerto_atual"),
        "taxa de acertos usada na projeção",
    ),
    (
        "21", ("metricas_para_previsao", "aderencia_aos_dias"),
        "22", ("estado_observado", "aderencia"),
        "aderência usada na projeção",
    ),
)


@dataclass
class Problema:
    """Um achado da auditoria, sempre atribuído a um agente."""

    id: str
    categoria: str
    gravidade: str
    descricao: str
    agente: str
    correcao: str
    campo: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "categoria": self.categoria,
            "gravidade": self.gravidade,
            "descricao": self.descricao,
            "agente_responsavel": self.agente,
            "campo": self.campo,
            "correcao_necessaria": self.correcao,
        }


@dataclass
class Validacao:
    """Laudo do fluxo. `aprovado` continua sendo a leitura rápida do status."""

    aprovado: bool
    status: str = STATUS_APROVADA
    verificacoes: list[str] = field(default_factory=list)
    problemas: list[str] = field(default_factory=list)
    alertas: list[str] = field(default_factory=list)
    achados: list[Problema] = field(default_factory=list)
    indices: dict[str, Any] = field(default_factory=dict)
    plano_de_correcao: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "aprovado": self.aprovado,
            "status": self.status,
            "resumo_geral": {
                "status_da_validacao": self.status,
                **self.indices,
                "verificacoes_realizadas": len(self.verificacoes),
                "problemas_encontrados": len(self.achados),
            },
            "verificacoes": self.verificacoes,
            "problemas": self.problemas,
            "alertas": self.alertas,
            "problemas_detalhados": [p.to_dict() for p in self.achados],
            "plano_de_correcao": self.plano_de_correcao,
            "consumido_por": ["Master Orchestrator"],
            "observacoes": [
                "Este agente não altera nenhuma saída: ele audita e devolve o laudo.",
                "Somente respostas aprovadas podem ser entregues ao estudante.",
            ],
        }


# --------------------------------------------------------------------------- #
# Leitura (nunca escrita)
# --------------------------------------------------------------------------- #


def _em(conteudo: Any, caminho: tuple[str, ...]) -> Any:
    """Lê um caminho aninhado sem levantar erro nem criar chave."""
    atual = conteudo
    for chave in caminho:
        if not isinstance(atual, dict) or chave not in atual:
            return None
        atual = atual[chave]
    return atual


def _conteudos(saidas: dict[str, AgentResult]) -> dict[str, dict]:
    return {codigo: r.conteudo for codigo, r in saidas.items() if r.ok and r.conteudo}


def _conteudos_da_arvore(arvore: dict) -> set[str]:
    """Todo nome que a árvore conhece, em qualquer nível.

    O cronograma agenda o nível mais fino que existir — um subtópico é
    conteúdo tão legítimo quanto o tópico que o contém. Conferir só o nível de
    tópico acusaria de fantasma exatamente o detalhamento que o agente 04
    produziu.
    """
    nomes: set[str] = set()
    for disciplina in arvore.get("disciplinas", []):
        nomes.add(disciplina["nome"])
        for modulo in disciplina.get("modulos", []):
            nomes.add(modulo["nome"])
            for topico in modulo.get("topicos", []):
                nomes.add(topico["nome"])
                for subtopico in topico.get("subtopicos", []):
                    nomes.add(subtopico["nome"])
                    for micro in subtopico.get("microtopicos", []):
                        nomes.add(micro["nome"])
    return nomes


def _dependencia_pendente(executados: set[str], selecionados: set[str]) -> bool:
    return any(
        dep not in executados
        for codigo in executados
        for dep in dependencias_efetivas(get_agent(codigo), selecionados)
    )


# --------------------------------------------------------------------------- #
# 1. Estrutural
# --------------------------------------------------------------------------- #


def _validar_estrutura(
    selecionados: set[str], saidas: dict[str, AgentResult], anotar
) -> list[str]:
    verificacoes: list[str] = []
    executados = {codigo for codigo, r in saidas.items() if r.ok}

    faltando = [c for c in AGENTES_OBRIGATORIOS if c != "24" and c not in executados]
    for codigo in faltando:
        anotar(
            "estrutural",
            GRAVIDADE_BLOQUEANTE,
            f"agente obrigatório {codigo} {get_agent(codigo).nome} não foi executado",
            codigo,
            "executar o agente antes de entregar a resposta",
        )
    if not faltando:
        verificacoes.append("Agentes obrigatórios executados")

    incompletas = 0
    for codigo, resultado in sorted(saidas.items()):
        if not resultado.ok:
            anotar(
                "estrutural",
                GRAVIDADE_BLOQUEANTE,
                f"{codigo} {resultado.nome} falhou: {resultado.erro}",
                codigo,
                "reexecutar o agente após corrigir a causa da falha",
            )
            continue
        if not resultado.conteudo:
            anotar(
                "estrutural",
                GRAVIDADE_BLOQUEANTE,
                f"{codigo} {resultado.nome} devolveu saída vazia",
                codigo,
                "reexecutar o agente",
            )
            continue
        if codigo == "24":
            continue
        for campo in CAMPOS_OBRIGATORIOS_COMUNS:
            if campo not in resultado.conteudo:
                incompletas += 1
                anotar(
                    "estrutural",
                    GRAVIDADE_RESSALVA,
                    f"{codigo} {resultado.nome} não declarou o campo '{campo}'",
                    codigo,
                    f"incluir `{campo}` na saída do agente",
                    campo,
                )
    if not incompletas:
        verificacoes.append("Todas as saídas trazem o contrato mínimo de campos")
    return verificacoes


# --------------------------------------------------------------------------- #
# 2. Consistência
# --------------------------------------------------------------------------- #


def _validar_consistencia(
    selecionados: set[str], saidas: dict[str, AgentResult], anotar
) -> list[str]:
    verificacoes: list[str] = []
    executados = {codigo for codigo, r in saidas.items() if r.ok}
    conteudos = _conteudos(saidas)

    for codigo in sorted(executados):
        spec = get_agent(codigo)
        for dep in dependencias_efetivas(spec, selecionados):
            if dep not in executados:
                anotar(
                    "consistencia",
                    GRAVIDADE_BLOQUEANTE,
                    f"{codigo} {spec.nome} rodou sem a entrada de {dep}",
                    codigo,
                    f"executar {dep} antes de {codigo}",
                )
    if not _dependencia_pendente(executados, selecionados):
        verificacoes.append("Toda dependência foi satisfeita antes da execução")

    # As invariantes do sistema: o mesmo fato, medido por um agente só.
    conferidas = divergentes = 0
    for agente_a, caminho_a, agente_b, caminho_b, descricao in INVARIANTES:
        if agente_a not in conteudos or agente_b not in conteudos:
            continue
        valor_a = _em(conteudos[agente_a], caminho_a)
        valor_b = _em(conteudos[agente_b], caminho_b)
        if valor_a is None or valor_b is None:
            continue
        conferidas += 1
        if valor_a != valor_b:
            divergentes += 1
            anotar(
                "consistencia",
                GRAVIDADE_BLOQUEANTE,
                (
                    f"{descricao} diverge: agente {agente_a} publicou {valor_a!r} e "
                    f"agente {agente_b} publicou {valor_b!r}"
                ),
                agente_b,
                f"reaproveitar o valor do agente {agente_a} em vez de recalculá-lo",
                ".".join(caminho_b),
            )
    if conferidas and not divergentes:
        verificacoes.append(
            f"{conferidas} invariante(s) entre agentes conferida(s) sem divergência"
        )

    # O ganho que o 23 propõe tem de ser o que o 22 precificou.
    if "22" in conteudos and "23" in conteudos:
        simulados = {
            s["acao"]: s.get("impacto_na_probabilidade")
            for s in conteudos["22"].get("simulacoes", [])
        }
        for otimizacao in conteudos["23"].get("otimizacoes_recomendadas", []):
            impacto = otimizacao.get("impacto_esperado") or {}
            alavanca = impacto.get("alavanca")
            if alavanca in simulados and impacto.get(
                "ganho_na_probabilidade"
            ) != simulados[alavanca]:
                anotar(
                    "consistencia",
                    GRAVIDADE_BLOQUEANTE,
                    (
                        f"ganho de '{alavanca}' diverge do simulado pelo agente 22 "
                        f"({impacto.get('ganho_na_probabilidade')!r} contra "
                        f"{simulados[alavanca]!r})"
                    ),
                    "23",
                    "usar o impacto simulado pelo agente 22",
                    "otimizacoes_recomendadas.impacto_esperado",
                )
    return verificacoes


# --------------------------------------------------------------------------- #
# 3. Pedagógica
# --------------------------------------------------------------------------- #


def _validar_pedagogia(saidas: dict[str, AgentResult], anotar) -> list[str]:
    verificacoes: list[str] = []
    conteudos = _conteudos(saidas)
    grafo = conteudos.get("05") or {}
    plano = conteudos.get("06") or {}

    for codigo in ("07", "09"):
        if (conteudos.get(codigo) or {}).get("bloqueio"):
            verificacoes.append(
                f"{codigo} bloqueou a produção por pré-requisito pendente, como previsto"
            )

    if not grafo or not plano:
        return verificacoes

    ordem: dict[str, int] = {}
    for dia in plano.get("cronograma", []):
        for sessao in dia.get("sessoes", []):
            if sessao.get("tipo") != "conteudo":
                continue
            nome = sessao.get("conteudo")
            if nome and nome not in ordem:
                ordem[nome] = len(ordem)

    por_id = {no["id"]: no for no in grafo.get("nos", [])}
    violacoes = 0
    for no in grafo.get("nos", []):
        posicao = ordem.get(no["nome"])
        if posicao is None:
            continue
        for pre_id in no.get("pre_requisitos", []):
            pre = por_id.get(pre_id)
            posicao_pre = ordem.get(pre["nome"]) if pre else None
            if posicao_pre is not None and posicao_pre > posicao:
                violacoes += 1
                anotar(
                    "pedagogica",
                    GRAVIDADE_BLOQUEANTE,
                    f"{no['nome']} está agendado antes do pré-requisito {pre['nome']}",
                    "06",
                    "reordenar o cronograma segundo a sequência do grafo",
                    "cronograma",
                )
    if not violacoes and ordem:
        verificacoes.append("Cronograma respeita a ordem de pré-requisitos do grafo")
    return verificacoes


# --------------------------------------------------------------------------- #
# 4. Técnica
# --------------------------------------------------------------------------- #


def _validar_tecnica(saidas: dict[str, AgentResult], anotar) -> list[str]:
    verificacoes: list[str] = []
    conteudos = _conteudos(saidas)
    arvore = conteudos.get("04") or {}
    grafo = conteudos.get("05") or {}

    if grafo:
        if grafo.get("acilico") is False:
            anotar(
                "tecnica",
                GRAVIDADE_BLOQUEANTE,
                "o grafo de dependências contém ciclo não resolvido",
                "05",
                "quebrar o ciclo ou declarar a dependência como opcional",
                "acilico",
            )
        else:
            verificacoes.append("Grafo de dependências acíclico")

        ids = [no["id"] for no in grafo.get("nos", [])]
        duplicados = sorted({i for i in ids if ids.count(i) > 1})
        for duplicado in duplicados:
            anotar(
                "tecnica",
                GRAVIDADE_BLOQUEANTE,
                f"nó duplicado no grafo: {duplicado}",
                "05",
                "gerar identificadores únicos por nó",
                "nos",
            )

        conhecidos = set(ids)
        invalidas = sorted(
            {
                pre
                for no in grafo.get("nos", [])
                for pre in no.get("pre_requisitos", [])
                if pre not in conhecidos
            }
        )
        for referencia in invalidas:
            anotar(
                "tecnica",
                GRAVIDADE_BLOQUEANTE,
                f"pré-requisito aponta para nó inexistente: {referencia}",
                "05",
                "remover a referência ou criar o nó correspondente",
                "pre_requisitos",
            )
        if not duplicados and not invalidas:
            verificacoes.append("Nenhuma referência inválida ou duplicada no grafo")

    if arvore:
        nomes = [
            topico["nome"]
            for disciplina in arvore.get("disciplinas", [])
            for modulo in disciplina.get("modulos", [])
            for topico in modulo.get("topicos", [])
        ]
        for nome in sorted({n for n in nomes if nomes.count(n) > 1}):
            anotar(
                "tecnica",
                GRAVIDADE_RESSALVA,
                f"tópico duplicado na árvore curricular: {nome}",
                "04",
                "consolidar o tópico repetido",
                "disciplinas",
            )

    plano = conteudos.get("06") or {}
    if plano and arvore:
        agendados = {
            sessao.get("conteudo")
            for dia in plano.get("cronograma", [])
            for sessao in dia.get("sessoes", [])
            if sessao.get("tipo") == "conteudo" and sessao.get("conteudo")
        }
        fantasmas = sorted(agendados - _conteudos_da_arvore(arvore))
        for nome in fantasmas:
            anotar(
                "tecnica",
                GRAVIDADE_BLOQUEANTE,
                f"cronograma agenda conteúdo que não existe na árvore: {nome}",
                "06",
                "agendar apenas conteúdos presentes na Árvore Curricular",
                "cronograma",
            )
        if not fantasmas and agendados:
            verificacoes.append("Todo conteúdo agendado existe na Árvore Curricular")
    return verificacoes


# --------------------------------------------------------------------------- #
# 5. Qualidade
# --------------------------------------------------------------------------- #


def _validar_qualidade(saidas: dict[str, AgentResult], anotar) -> list[str]:
    verificacoes: list[str] = []
    incompletos = 0

    for codigo, resultado in sorted(saidas.items()):
        if not resultado.ok or not resultado.conteudo:
            continue
        status = resultado.conteudo.get("status")
        if status in STATUS_INCOMPLETOS:
            incompletos += 1
            anotar(
                "qualidade",
                GRAVIDADE_RESSALVA,
                f"{codigo} {resultado.nome} devolveu status '{status}'",
                codigo,
                "conectar o redator ou liberar o pré-requisito antes de entregar",
                "status",
            )
        bloqueio = resultado.conteudo.get("bloqueio")
        if bloqueio:
            motivo = bloqueio.get("motivo") if isinstance(bloqueio, dict) else bloqueio
            anotar(
                "qualidade",
                GRAVIDADE_RESSALVA,
                f"{codigo} {resultado.nome} não produziu saída: {motivo}",
                codigo,
                "resolver o bloqueio declarado pelo agente",
                "bloqueio",
            )
    if not incompletos:
        verificacoes.append("Nenhuma saída ficou pendente de produção")
    return verificacoes


# --------------------------------------------------------------------------- #
# 6. Segurança — o grupo que caça afirmação sem lastro
# --------------------------------------------------------------------------- #


def _validar_seguranca(saidas: dict[str, AgentResult], anotar) -> list[str]:
    verificacoes: list[str] = []
    conteudos = _conteudos(saidas)
    projecoes = 0

    for codigo, conteudo in sorted(conteudos.items()):
        if codigo == "24":
            continue

        # Texto recusado pelo próprio agente por ser genérico, punitivo ou
        # promessa: recusar é o comportamento correto, mas o laudo registra
        # que houve tentativa.
        for chave in ("mensagens_recusadas", "textos_recusados"):
            recusados = conteudo.get(chave) or []
            if recusados:
                anotar(
                    "seguranca",
                    GRAVIDADE_RESSALVA,
                    (
                        f"{codigo} recusou {len(recusados)} texto(s) antes de emitir; "
                        "o filtro funcionou, mas a origem do texto merece revisão"
                    ),
                    codigo,
                    "revisar o gerador do texto recusado",
                    chave,
                )

        if conteudo.get("confiabilidade") == "baixa":
            anotar(
                "seguranca",
                GRAVIDADE_RESSALVA,
                f"{codigo} declarou confiabilidade baixa",
                codigo,
                "coletar os dados listados em `lacunas` antes de decidir por esta saída",
                "confiabilidade",
            )

        # Previsão sem intervalo é previsão apresentada como certeza.
        for caminho in (
            ("resumo_geral", "probabilidade_de_atingir_o_objetivo"),
            ("resumo_geral", "evolucao_prevista", "cobertura_projetada"),
            ("resumo_geral", "evolucao_prevista", "acerto_projetado"),
        ):
            estimativa = _em(conteudo, caminho)
            if not isinstance(estimativa, dict):
                continue
            projecoes += 1
            if estimativa.get("estimativa") is not None and not estimativa.get(
                "intervalo"
            ):
                anotar(
                    "seguranca",
                    GRAVIDADE_BLOQUEANTE,
                    f"{codigo} publicou projeção sem intervalo de incerteza",
                    codigo,
                    "acompanhar toda estimativa de intervalo e confiança",
                    ".".join(caminho),
                )

        # Recomendação de otimização sem evidência é inferência sem lastro.
        for otimizacao in conteudo.get("otimizacoes_recomendadas", []):
            if not otimizacao.get("evidencias"):
                anotar(
                    "seguranca",
                    GRAVIDADE_BLOQUEANTE,
                    (
                        f"{codigo} recomendou '{otimizacao.get('acao')}' sem evidência "
                        "declarada"
                    ),
                    codigo,
                    "descartar a recomendação ou anexar a evidência que a sustenta",
                    "otimizacoes_recomendadas.evidencias",
                )

        # Causa de erro sem evidência: a regra do agente 17.
        for erro in conteudo.get("erros", []):
            if erro.get("causa_provavel") and not erro.get("evidencias"):
                anotar(
                    "seguranca",
                    GRAVIDADE_BLOQUEANTE,
                    f"{codigo} atribuiu causa a um erro sem evidência",
                    codigo,
                    "classificar como indeterminado quando não houver evidência",
                    "erros.evidencias",
                )

        # Mensagem ao estudante sem dado citado: a regra do agente 19.
        for mensagem in conteudo.get("mensagens", []):
            if isinstance(mensagem, dict) and not mensagem.get("dados_citados"):
                anotar(
                    "seguranca",
                    GRAVIDADE_BLOQUEANTE,
                    f"{codigo} emitiu mensagem sem citar nenhum dado do estudante",
                    codigo,
                    "recusar a mensagem em vez de emiti-la sem dado",
                    "mensagens.dados_citados",
                )

    if projecoes:
        verificacoes.append(f"{projecoes} projeção(ões) conferida(s) quanto ao intervalo")
    return verificacoes


# --------------------------------------------------------------------------- #
# 7. Performance
# --------------------------------------------------------------------------- #


def _validar_performance(
    selecionados: set[str], saidas: dict[str, AgentResult], anotar
) -> list[str]:
    verificacoes: list[str] = []
    executados = {codigo for codigo, r in saidas.items() if r.ok}

    consumidores: dict[str, set[str]] = {}
    for codigo in executados:
        if codigo == "24":
            continue
        for dep in dependencias_efetivas(get_agent(codigo), selecionados):
            consumidores.setdefault(dep, set()).add(codigo)

    # Agente cuja saída é entregue ao orquestrador não é órfão: ele é o fim de
    # uma linha, não um cálculo perdido. Quem declara isso é o próprio agente,
    # em `consumido_por`.
    conteudos = _conteudos(saidas)
    entregaveis = {
        codigo
        for codigo, conteudo in conteudos.items()
        if "Master Orchestrator" in (conteudo.get("consumido_por") or [])
    }
    orfaos = sorted(
        codigo
        for codigo in executados
        if codigo != "24"
        and codigo not in AGENTES_OBRIGATORIOS
        and codigo not in entregaveis
        and not consumidores.get(codigo)
    )
    for codigo in orfaos:
        anotar(
            "performance",
            GRAVIDADE_RESSALVA,
            f"{codigo} {get_agent(codigo).nome} rodou e nenhum agente consumiu a saída",
            codigo,
            "remover o agente do workflow ou declarar quem consome sua saída",
        )
    if not orfaos:
        verificacoes.append("Nenhum agente rodou sem consumidor")
    return verificacoes


# --------------------------------------------------------------------------- #
# Índices e plano de correção
# --------------------------------------------------------------------------- #


def _indices(
    achados: list[Problema], verificacoes: list[str], saidas: dict[str, AgentResult]
) -> dict:
    """Cada índice conta o que foi verificado — nenhum é opinião."""
    total = len(verificacoes) + len(achados)
    por_categoria = {
        categoria: len([a for a in achados if a.categoria == categoria])
        for categoria in CATEGORIAS
    }

    def indice(categorias: tuple[str, ...]) -> float | None:
        if not total:
            return None
        problemas = sum(por_categoria[c] for c in categorias)
        return round(max(0.0, 1 - problemas / total), 4)

    aprovados = [r for r in saidas.values() if r.ok] or []
    com_lacunas = [r for r in aprovados if r.lacunas]

    return {
        "indice_de_qualidade": {
            "valor": indice(("estrutural", "qualidade")),
            "base": "verificações estruturais e de qualidade sem problema",
        },
        "indice_de_consistencia": {
            "valor": indice(("consistencia", "pedagogica", "tecnica")),
            "base": (
                "invariantes entre agentes, ordem de pré-requisitos e integridade "
                "referencial"
            ),
        },
        "indice_de_confiabilidade": {
            "valor": indice(("seguranca",)),
            "base": "afirmações com lastro declarado sobre o total verificado",
        },
        "indice_de_completude": {
            "valor": (
                round(1 - len(com_lacunas) / len(aprovados), 4) if aprovados else None
            ),
            "base": (
                f"{len(com_lacunas)} de {len(aprovados)} saídas declararam lacuna "
                "de informação"
            ),
        },
    }


def _plano_de_correcao(achados: list[Problema], selecionados: set[str]) -> dict:
    """Quem reexecutar, em que ordem e o que precisa mudar para revalidar."""
    bloqueantes = [a for a in achados if a.gravidade == GRAVIDADE_BLOQUEANTE]
    agentes = {a.agente for a in bloqueantes if a.agente in selecionados}
    if not agentes:
        return {
            "agentes_a_reexecutar": [],
            "ordem_de_reexecucao": [],
            "campos_a_corrigir": [],
            "criterios_para_nova_validacao": [],
            "base": "nenhum problema bloqueante: não há reexecução a pedir",
        }

    return {
        "agentes_a_reexecutar": sorted(agentes),
        "ordem_de_reexecucao": [
            sorted(set(onda) & agentes)
            for onda in ondas_de_execucao(agentes)
            if set(onda) & agentes
        ],
        "campos_a_corrigir": sorted(
            {f"{a.agente}.{a.campo}" for a in bloqueantes if a.campo}
        ),
        "criterios_para_nova_validacao": sorted({a.correcao for a in bloqueantes}),
        "base": (
            "ordem topológica dos agentes envolvidos; o Master Orchestrator é quem "
            "decide reexecutar"
        ),
    }


# --------------------------------------------------------------------------- #
# Entrada principal
# --------------------------------------------------------------------------- #


def validar(selecionados: set[str], saidas: dict[str, AgentResult]) -> Validacao:
    """Audita o fluxo executado. Não altera nenhuma saída."""
    achados: list[Problema] = []

    def anotar(
        categoria: str,
        gravidade: str,
        descricao: str,
        agente: str,
        correcao: str,
        campo: str | None = None,
    ) -> None:
        achados.append(
            Problema(
                id=f"v{len(achados) + 1:03d}",
                categoria=categoria,
                gravidade=gravidade,
                descricao=descricao,
                agente=agente,
                correcao=correcao,
                campo=campo,
            )
        )

    verificacoes: list[str] = []
    verificacoes += _validar_estrutura(selecionados, saidas, anotar)
    verificacoes += _validar_consistencia(selecionados, saidas, anotar)
    verificacoes += _validar_pedagogia(saidas, anotar)
    verificacoes += _validar_tecnica(saidas, anotar)
    verificacoes += _validar_qualidade(saidas, anotar)
    verificacoes += _validar_seguranca(saidas, anotar)
    verificacoes += _validar_performance(selecionados, saidas, anotar)

    # Lacunas não invalidam o fluxo: elas são o que os agentes declararam em
    # vez de inventar. Entram como alerta para o orquestrador decidir.
    alertas = [
        f"{codigo} {resultado.nome}: informação ausente do usuário — '{lacuna}'"
        for codigo, resultado in sorted(saidas.items())
        if resultado.ok
        for lacuna in resultado.lacunas
    ]
    if not alertas:
        verificacoes.append("Nenhuma lacuna de informação declarada pelos agentes")

    bloqueantes = [a for a in achados if a.gravidade == GRAVIDADE_BLOQUEANTE]
    ressalvas = [a for a in achados if a.gravidade == GRAVIDADE_RESSALVA]
    status = (
        STATUS_REPROVADA
        if bloqueantes
        else STATUS_COM_RESSALVAS
        if ressalvas
        else STATUS_APROVADA
    )

    return Validacao(
        aprovado=not bloqueantes,
        status=status,
        verificacoes=verificacoes,
        problemas=[a.descricao for a in bloqueantes],
        alertas=alertas + [a.descricao for a in ressalvas],
        achados=achados,
        indices=_indices(achados, verificacoes, saidas),
        plano_de_correcao=_plano_de_correcao(achados, selecionados),
    )


__all__ = [
    "CAMPOS_OBRIGATORIOS_COMUNS",
    "CATEGORIAS",
    "GRAVIDADES",
    "GRAVIDADE_BLOQUEANTE",
    "GRAVIDADE_RESSALVA",
    "INVARIANTES",
    "STATUS_APROVADA",
    "STATUS_COM_RESSALVAS",
    "STATUS_INCOMPLETOS",
    "STATUS_REPROVADA",
    "Problema",
    "Validacao",
    "validar",
]
