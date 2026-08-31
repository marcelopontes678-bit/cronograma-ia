import pytest

from orcamento_engine import (
    Ambiente,
    ItemCusto,
    Modulo,
    calcular_divisor_markup,
    calcular_orcamento,
    calcular_orcamento_projeto,
    carregar_config,
    pct_comissao_vendas,
)


class TestCarregarConfigReal:
    def test_carrega_config_real_do_projeto(self, caminho_config_precificacao):
        config = carregar_config(caminho_config_precificacao)
        m = config["markup"]
        assert m["pct_custo_fixo"] == pytest.approx(0.3377)
        assert m["pct_impostos"] == pytest.approx(0.09)
        assert m["pct_lucro"] == pytest.approx(0.15)
        assert len(m["comissao_vendas_faixas"]) == 4


class TestComissaoVendasEscalonada:
    @pytest.fixture
    def config(self, caminho_config_precificacao):
        return carregar_config(caminho_config_precificacao)

    def test_faixa_ate_150k(self, config):
        assert pct_comissao_vendas(config, 100_000) == pytest.approx(0.05)
        assert pct_comissao_vendas(config, 150_000) == pytest.approx(0.05)

    def test_faixa_150k_a_200k(self, config):
        assert pct_comissao_vendas(config, 150_000.01) == pytest.approx(0.06)
        assert pct_comissao_vendas(config, 200_000) == pytest.approx(0.06)

    def test_faixa_200k_a_500k(self, config):
        assert pct_comissao_vendas(config, 300_000) == pytest.approx(0.07)

    def test_faixa_acima_de_500k(self, config):
        assert pct_comissao_vendas(config, 600_000) == pytest.approx(0.08)

    def test_faturamento_negativo_e_invalido(self, config):
        from orcamento_engine import ConfiguracaoInvalidaError
        with pytest.raises(ConfiguracaoInvalidaError):
            pct_comissao_vendas(config, -1)


class TestCalcularDivisorMarkup:
    def test_formula_bate_com_calculo_manual(self, caminho_config_precificacao):
        config = carregar_config(caminho_config_precificacao)
        divisor = calcular_divisor_markup(config, faturamento_acumulado=100_000)

        m = config["markup"]
        soma = m["pct_custo_fixo"] + m["pct_impostos"] + m["pct_comissao_fabrica"] + 0.05 + m["pct_lucro"]
        esperado = 1 / (1 - soma)
        assert divisor == pytest.approx(esperado)
        assert divisor == pytest.approx(2.760143527463427)  # valor conferido manualmente nesta sessao


class TestCalcularOrcamentoProjeto:
    def test_venda_e_total_batem_com_calculo_manual(self, caminho_config_precificacao):
        config = carregar_config(caminho_config_precificacao)
        resultado = calcular_orcamento_projeto(
            custo_material_total=10155.66,
            config=config,
            faturamento_acumulado=100_000,
            custo_mao_de_obra=806.25,
        )
        assert resultado.preco_venda_material == pytest.approx((10155.66 + 806.25) * resultado.divisor_markup)
        assert resultado.total == pytest.approx(resultado.preco_venda_material)
        # valor recalculado com a mao de obra dentro da base de markup
        # (custo_fabricacao = 10155.66 + 806.25 = 10961.91; 10155.66 aqui e o
        # custo_material_total ja arredondado a 2 casas; a tolerancia cobre
        # esse arredondamento de entrada, nao imprecisao do calculo)
        assert resultado.total == pytest.approx(10961.91 * resultado.divisor_markup, abs=0.02)


class TestCalcularOrcamentoLegadoPorModulo:
    def test_mao_de_obra_entra_na_base_do_markup(self, caminho_config_precificacao):
        config = carregar_config(caminho_config_precificacao)
        ambiente = Ambiente(
            nome="Cozinha",
            modulos=[
                Modulo(
                    nome="Armario",
                    itens=[ItemCusto(descricao="Chapa", custo_material=800.0, origem="teste")],
                    custo_mao_de_obra=200.0,
                )
            ],
        )
        resultado = calcular_orcamento([ambiente], config, faturamento_acumulado=100_000)
        modulo_resultado = resultado.modulos[0]
        assert modulo_resultado.custo_material == 800.0
        assert modulo_resultado.preco_venda_material == pytest.approx(1000.0 * resultado.divisor_markup)
        assert modulo_resultado.preco_final == pytest.approx(modulo_resultado.preco_venda_material)
