"""Motor de calculo de orcamento de marcenaria.

Recebe a estrutura de dados normalizada (ambientes -> modulos -> itens de
custo de material) e aplica a formula de precificacao lida de
config/precificacao.json. Nao contem nenhum valor de precificacao hardcoded.

Formula:
    divisor_markup = 1 / (1 - (pct_custo_fixo + pct_impostos +
                                pct_comissao_fabrica + pct_comissao_vendas +
                                pct_lucro))
    preco_venda_material = custo_material * divisor_markup
    preco_final_item = preco_venda_material + custo_mao_de_obra

Mao de obra e somada depois do markup, nao e multiplicada por ele.
Montagem nao e cobrada como componente separado (config.montagem.cobrada_separadamente).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


class ConfiguracaoInvalidaError(Exception):
    pass


@dataclass
class ItemCusto:
    """Um item de custo de material dentro de um modulo (ex: chapa, ferragem)."""
    descricao: str
    custo_material: float
    origem: str = ""  # rastreabilidade: pagina/linha/coordenada do arquivo original


@dataclass
class Modulo:
    nome: str
    itens: list[ItemCusto] = field(default_factory=list)
    custo_mao_de_obra: float = 0.0

    @property
    def custo_material_total(self) -> float:
        return sum(item.custo_material for item in self.itens)


@dataclass
class Ambiente:
    nome: str
    modulos: list[Modulo] = field(default_factory=list)


def carregar_config(caminho_config: str | Path) -> dict:
    caminho_config = Path(caminho_config)
    if not caminho_config.exists():
        raise ConfiguracaoInvalidaError(f"Arquivo de configuracao nao encontrado: {caminho_config}")
    with open(caminho_config, "r", encoding="utf-8") as f:
        config = json.load(f)

    markup = config.get("markup")
    if not markup:
        raise ConfiguracaoInvalidaError("Config sem secao 'markup'.")
    for chave in ("pct_custo_fixo", "pct_impostos", "pct_comissao_fabrica", "pct_lucro"):
        if chave not in markup:
            raise ConfiguracaoInvalidaError(f"Config 'markup' sem chave obrigatoria: {chave}")
    if "comissao_vendas_faixas" not in markup or not markup["comissao_vendas_faixas"]:
        raise ConfiguracaoInvalidaError("Config 'markup' sem 'comissao_vendas_faixas'.")

    return config


def pct_comissao_vendas(config: dict, faturamento_acumulado: float) -> float:
    """Seleciona o percentual de comissao de vendas pela faixa de faturamento acumulado.

    faturamento_acumulado e informado manualmente pelo usuario no momento do
    orcamento (config.faturamento_acumulado.fonte == 'entrada_manual').
    """
    if faturamento_acumulado < 0:
        raise ConfiguracaoInvalidaError("faturamento_acumulado nao pode ser negativo.")

    faixas = config["markup"]["comissao_vendas_faixas"]
    for faixa in faixas:
        limite = faixa["ate"]
        if limite is None or faturamento_acumulado <= limite:
            return faixa["pct"]
    # nao deveria chegar aqui se a ultima faixa tem "ate": null
    return faixas[-1]["pct"]


def calcular_divisor_markup(config: dict, faturamento_acumulado: float) -> float:
    m = config["markup"]
    pct_comissao = pct_comissao_vendas(config, faturamento_acumulado)
    soma_pct = (
        m["pct_custo_fixo"]
        + m["pct_impostos"]
        + m["pct_comissao_fabrica"]
        + pct_comissao
        + m["pct_lucro"]
    )
    if soma_pct >= 1:
        raise ConfiguracaoInvalidaError(
            f"Soma dos percentuais de markup ({soma_pct:.4f}) >= 1: divisor ficaria infinito/negativo."
        )
    return 1.0 / (1.0 - soma_pct)


@dataclass
class ResultadoModulo:
    nome: str
    custo_material: float
    preco_venda_material: float
    custo_mao_de_obra: float
    preco_final: float


@dataclass
class ResultadoOrcamento:
    divisor_markup: float
    pct_comissao_vendas_aplicada: float
    modulos: list[ResultadoModulo]

    @property
    def total(self) -> float:
        return sum(m.preco_final for m in self.modulos)


def calcular_orcamento(
    ambientes: list[Ambiente],
    config: dict,
    faturamento_acumulado: float,
) -> ResultadoOrcamento:
    """Aplica a formula de precificacao a cada modulo de cada ambiente."""
    divisor = calcular_divisor_markup(config, faturamento_acumulado)
    pct_comissao = pct_comissao_vendas(config, faturamento_acumulado)

    resultados: list[ResultadoModulo] = []
    for ambiente in ambientes:
        for modulo in ambiente.modulos:
            custo_material = modulo.custo_material_total
            preco_venda_material = custo_material * divisor
            preco_final = preco_venda_material + modulo.custo_mao_de_obra
            resultados.append(
                ResultadoModulo(
                    nome=f"{ambiente.nome} - {modulo.nome}",
                    custo_material=custo_material,
                    preco_venda_material=preco_venda_material,
                    custo_mao_de_obra=modulo.custo_mao_de_obra,
                    preco_final=preco_final,
                )
            )

    return ResultadoOrcamento(
        divisor_markup=divisor,
        pct_comissao_vendas_aplicada=pct_comissao,
        modulos=resultados,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Teste manual do orcamento_engine com um ambiente conhecido.")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parent.parent / "config" / "precificacao.json"))
    parser.add_argument("--faturamento-acumulado", type=float, required=True)
    args = parser.parse_args()

    config = carregar_config(args.config)

    ambiente_teste = Ambiente(
        nome="Cozinha",
        modulos=[
            Modulo(
                nome="Armario Superior",
                itens=[
                    ItemCusto(descricao="Chapa MDF 18mm", custo_material=800.0, origem="teste manual"),
                    ItemCusto(descricao="Ferragens", custo_material=150.0, origem="teste manual"),
                ],
                custo_mao_de_obra=200.0,
            ),
        ],
    )

    resultado = calcular_orcamento([ambiente_teste], config, args.faturamento_acumulado)
    print(f"Divisor de markup: {resultado.divisor_markup:.4f}")
    print(f"Comissao de vendas aplicada: {resultado.pct_comissao_vendas_aplicada:.2%}")
    for m in resultado.modulos:
        print(f"  {m.nome}: material R${m.custo_material:.2f} -> venda R${m.preco_venda_material:.2f} "
              f"+ mao de obra R${m.custo_mao_de_obra:.2f} = R${m.preco_final:.2f}")
    print(f"TOTAL: R${resultado.total:.2f}")
