"""Algoritmo de plano de corte 2D (guilhotina com retângulos livres).

Puro (sem I/O): recebe peças e dimensões da chapa, devolve o posicionamento
de cada peça em cada chapa. Heurística: peças ordenadas por maior dimensão,
colocadas no retângulo livre de melhor encaixe (best short side fit); o
espaço restante é dividido em dois cortes de guilhotina.

Convenções:
- x corre ao longo do COMPRIMENTO da chapa; y ao longo da LARGURA.
- veio=True: o veio corre no sentido do comprimento da peça — proibido
  rotacionar.
- kerf: espessura do disco de serra, aplicada como folga entre peças.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PecaCorte:
    """Peça a cortar (uma unidade — expandir quantidades antes)."""

    ref: str
    nome: str
    comprimento_mm: int
    largura_mm: int
    veio: bool = False


@dataclass(frozen=True)
class PecaPosicionada:
    ref: str
    nome: str
    x_mm: int
    y_mm: int
    comprimento_mm: int
    largura_mm: int
    rotacionada: bool


@dataclass
class ChapaCortada:
    indice: int
    pecas: list[PecaPosicionada] = field(default_factory=list)

    def area_ocupada_mm2(self) -> int:
        return sum(p.comprimento_mm * p.largura_mm for p in self.pecas)


@dataclass
class ResultadoCorte:
    chapas: list[ChapaCortada]
    nao_alocadas: list[PecaCorte]


@dataclass
class _RetLivre:
    x: int
    y: int
    comp: int
    larg: int


def _encaixa(rect: _RetLivre, comp: int, larg: int) -> bool:
    return comp <= rect.comp and larg <= rect.larg


def _melhor_encaixe(
    livres: list[_RetLivre], peca: PecaCorte, kerf: int
) -> tuple[int, bool] | None:
    """Retorna (índice do retângulo, rotacionada) com o melhor encaixe.

    Critério: menor sobra no lado mais justo (best short side fit).
    """
    melhor: tuple[int, bool] | None = None
    melhor_score = None

    orientacoes = [(peca.comprimento_mm + kerf, peca.largura_mm + kerf, False)]
    if not peca.veio and peca.comprimento_mm != peca.largura_mm:
        orientacoes.append(
            (peca.largura_mm + kerf, peca.comprimento_mm + kerf, True)
        )

    for i, rect in enumerate(livres):
        for comp, larg, rot in orientacoes:
            if not _encaixa(rect, comp, larg):
                continue
            score = min(rect.comp - comp, rect.larg - larg)
            if melhor_score is None or score < melhor_score:
                melhor_score = score
                melhor = (i, rot)
    return melhor


def _dividir(rect: _RetLivre, comp_usado: int, larg_usado: int) -> list[_RetLivre]:
    """Divide o espaço restante em dois cortes de guilhotina.

    Divide ao longo do eixo com maior sobra, para gerar retângulos
    aproveitáveis maiores.
    """
    sobra_comp = rect.comp - comp_usado
    sobra_larg = rect.larg - larg_usado
    novos: list[_RetLivre] = []

    if sobra_comp >= sobra_larg:
        # Corte vertical: retângulo à direita fica com a altura total
        if sobra_comp > 0:
            novos.append(
                _RetLivre(rect.x + comp_usado, rect.y, sobra_comp, rect.larg)
            )
        if sobra_larg > 0:
            novos.append(
                _RetLivre(rect.x, rect.y + larg_usado, comp_usado, sobra_larg)
            )
    else:
        # Corte horizontal: retângulo acima fica com a largura total
        if sobra_larg > 0:
            novos.append(
                _RetLivre(rect.x, rect.y + larg_usado, rect.comp, sobra_larg)
            )
        if sobra_comp > 0:
            novos.append(
                _RetLivre(rect.x + comp_usado, rect.y, sobra_comp, larg_usado)
            )
    return novos


def empacotar(
    pecas: list[PecaCorte],
    chapa_comprimento_mm: int,
    chapa_largura_mm: int,
    kerf_mm: int = 3,
) -> ResultadoCorte:
    """Distribui as peças em quantas chapas forem necessárias."""
    # A folga do kerf é somada a cada peça; compensar no limite da chapa
    # para que uma peça do tamanho exato da chapa ainda caiba.
    comp_util = chapa_comprimento_mm + kerf_mm
    larg_util = chapa_largura_mm + kerf_mm

    def cabe_na_chapa(p: PecaCorte) -> bool:
        normal = (
            p.comprimento_mm <= chapa_comprimento_mm
            and p.largura_mm <= chapa_largura_mm
        )
        rotacionada = (
            not p.veio
            and p.largura_mm <= chapa_comprimento_mm
            and p.comprimento_mm <= chapa_largura_mm
        )
        return normal or rotacionada

    alocaveis = [p for p in pecas if cabe_na_chapa(p)]
    nao_alocadas = [p for p in pecas if not cabe_na_chapa(p)]

    # Maior dimensão primeiro; desempate por área
    fila = sorted(
        alocaveis,
        key=lambda p: (
            max(p.comprimento_mm, p.largura_mm),
            p.comprimento_mm * p.largura_mm,
        ),
        reverse=True,
    )

    chapas: list[ChapaCortada] = []
    livres_por_chapa: list[list[_RetLivre]] = []

    for peca in fila:
        colocada = False
        for idx, livres in enumerate(livres_por_chapa):
            escolha = _melhor_encaixe(livres, peca, kerf_mm)
            if not escolha:
                continue
            i_rect, rot = escolha
            rect = livres.pop(i_rect)
            comp = (peca.largura_mm if rot else peca.comprimento_mm) + kerf_mm
            larg = (peca.comprimento_mm if rot else peca.largura_mm) + kerf_mm
            chapas[idx].pecas.append(
                PecaPosicionada(
                    ref=peca.ref,
                    nome=peca.nome,
                    x_mm=rect.x,
                    y_mm=rect.y,
                    comprimento_mm=comp - kerf_mm,
                    largura_mm=larg - kerf_mm,
                    rotacionada=rot,
                )
            )
            livres.extend(_dividir(rect, comp, larg))
            colocada = True
            break

        if not colocada:
            # Abrir nova chapa
            nova = ChapaCortada(indice=len(chapas) + 1)
            livres = [_RetLivre(0, 0, comp_util, larg_util)]
            escolha = _melhor_encaixe(livres, peca, kerf_mm)
            # cabe_na_chapa garante encaixe em chapa vazia
            i_rect, rot = escolha  # type: ignore[misc]
            rect = livres.pop(i_rect)
            comp = (peca.largura_mm if rot else peca.comprimento_mm) + kerf_mm
            larg = (peca.comprimento_mm if rot else peca.largura_mm) + kerf_mm
            nova.pecas.append(
                PecaPosicionada(
                    ref=peca.ref,
                    nome=peca.nome,
                    x_mm=rect.x,
                    y_mm=rect.y,
                    comprimento_mm=comp - kerf_mm,
                    largura_mm=larg - kerf_mm,
                    rotacionada=rot,
                )
            )
            livres.extend(_dividir(rect, comp, larg))
            chapas.append(nova)
            livres_por_chapa.append(livres)

    return ResultadoCorte(chapas=chapas, nao_alocadas=nao_alocadas)
