import json
import math

from calculo_projeto import (
    AREA_UTIL_CHAPA_M2_PADRAO,
    PCT_PERDA_CORTE_PADRAO,
    _perimetro_fitavel_m,
    calcular_projeto,
)
from tabela_precos import PrecoReferencia, carregar_tabela_precos


class TestPerimetroFitavel:
    def test_usa_as_duas_maiores_dimensoes(self):
        # espessura (menor dimensao) nao entra no perimetro
        perimetro = _perimetro_fitavel_m(largura_mm=930, altura_mm=1040, profundidade_mm=18)
        assert perimetro == (2 * (1040 + 930)) / 1000

    def test_dimensao_ausente_vira_zero(self):
        perimetro = _perimetro_fitavel_m(largura_mm=None, altura_mm=500, profundidade_mm=300)
        assert perimetro == (2 * (500 + 300)) / 1000


class TestCalcularProjetoComTabelaSintetica:
    def _ambientes_json(self):
        return [
            {
                "nome": "Cozinha",
                "modulos": [
                    {
                        "nome": "Armario",
                        "itens": [
                            {
                                "descricao": "Lateral", "reference": "2.2033.18.Branco.MDF", "unidade": "M2",
                                "largura_mm": 600, "altura_mm": 2000, "profundidade_mm": 18,
                                "quantidade": 1.2, "repeticao": 2, "origem": "teste",
                            },
                            {
                                "descricao": "Dobradica", "reference": "1.1086.000", "unidade": "UN",
                                "largura_mm": None, "altura_mm": None, "profundidade_mm": None,
                                "quantidade": 1, "repeticao": 6, "origem": "teste",
                            },
                        ],
                    }
                ],
            }
        ]

    def _tabela(self, com_preco_chapa=True, com_preco_ferragem=True):
        return {
            "2.2033.18.Branco.MDF": PrecoReferencia(
                "2.2033.18.Branco.MDF", "", "", "", 18, "M2", None,
                340.0 if com_preco_chapa else None,
                26.0 if com_preco_chapa else None, "",
            ),
            "1.1086.000": PrecoReferencia(
                "1.1086.000", "", "", "", None, "UN",
                3.5 if com_preco_ferragem else None, None, None, "",
            ),
        }

    def test_agrega_chapa_fita_e_ferragem_com_precos_disponiveis(self):
        resultado = calcular_projeto(self._ambientes_json(), self._tabela())

        assert len(resultado.chapas) == 1
        chapa = resultado.chapas[0]
        assert chapa.acabamento == "18mm Branco"
        assert chapa.area_total_m2 == 1.2 * 2  # quantidade x repeticao
        area_com_perda = chapa.area_total_m2 * (1 + PCT_PERDA_CORTE_PADRAO)
        assert chapa.area_com_perda_m2 == area_com_perda
        assert chapa.num_chapas == math.ceil(area_com_perda / AREA_UTIL_CHAPA_M2_PADRAO)
        assert chapa.custo_chapas == chapa.num_chapas * 340.0

        assert len(resultado.fitas) == 1
        fita = resultado.fitas[0]
        perimetro_por_peca = _perimetro_fitavel_m(600, 2000, 18)
        assert fita.metros_total == perimetro_por_peca * 2  # repeticao
        assert fita.custo_fita == fita.metros_total * 26.0

        assert len(resultado.ferragens) == 1
        assert resultado.ferragens[0].custo == 3.5 * 6

        assert not resultado.itens_sem_preco
        esperado = chapa.custo_chapas + fita.custo_fita + resultado.ferragens[0].custo
        assert resultado.custo_material_total == esperado

    def test_sem_preco_de_chapa_fica_pendente_sem_custo_zero(self):
        resultado = calcular_projeto(self._ambientes_json(), self._tabela(com_preco_chapa=False))
        assert not resultado.chapas
        assert not resultado.fitas
        motivos = [m for _, _, m in resultado.itens_sem_preco]
        assert "SEM_PRECO_CHAPA_NA_TABELA" in motivos
        assert "SEM_PRECO_FITA_NA_TABELA" in motivos

    def test_sem_preco_de_ferragem_fica_pendente(self):
        resultado = calcular_projeto(self._ambientes_json(), self._tabela(com_preco_ferragem=False))
        assert not resultado.ferragens
        assert any(m == "SEM_PRECO_NA_TABELA" for _, _, m in resultado.itens_sem_preco)


class TestCalcularProjetoDadosReais:
    """Regressao contra o projeto real Quarto Maria (Paula e Gabriel),
    extraido e precificado nesta mesma sessao de trabalho."""

    def test_agrupamento_por_acabamento_bate_com_calculo_independente(self, caminho_quarto_maria_xml, caminho_tabela_precos_real):
        import extract_promob_xml
        from dataclasses import asdict

        ambientes = extract_promob_xml.extrair(caminho_quarto_maria_xml)
        ambientes_json = [asdict(a) for a in ambientes]

        tabela = carregar_tabela_precos(caminho_tabela_precos_real)
        resultado = calcular_projeto(ambientes_json, tabela)

        # recalculo independente (sem usar calculo_projeto.py) da area total
        # por acabamento, para conferir que o agrupamento bate
        from tabela_precos import chave_acabamento
        from collections import defaultdict

        area_por_chave = defaultdict(float)
        for amb in ambientes_json:
            for mod in amb["modulos"]:
                for it in mod["itens"]:
                    if it["unidade"] != "M2":
                        continue
                    chave = chave_acabamento(it["reference"]) or (0, it["reference"])
                    area_por_chave[chave] += it["quantidade"] * it["repeticao"]

        for chapa in resultado.chapas:
            espessura_txt, nome = chapa.acabamento.split("mm ", 1) if "mm " in chapa.acabamento else (None, chapa.acabamento)
            # confirma que a area total batida bate com alguma chave recalculada independentemente
            candidatos = [v for k, v in area_por_chave.items() if k[1] == nome]
            assert candidatos, f"acabamento {chapa.acabamento!r} nao encontrado no recalculo independente"
            assert any(abs(chapa.area_total_m2 - v) < 1e-9 for v in candidatos)

        # total de material deve ser positivo (ha precos reais cadastrados)
        assert resultado.custo_material_total > 0
