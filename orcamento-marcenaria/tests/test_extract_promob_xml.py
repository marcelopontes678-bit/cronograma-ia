import pytest

import extract_promob_xml


class TestExtracaoRealQuartoMaria:
    """Contra o projeto real Paula e Gabriel / Quarto Maria, ja usado
    manualmente durante o desenvolvimento do skill."""

    def test_extrai_um_ambiente(self, caminho_quarto_maria_xml):
        ambientes = extract_promob_xml.extrair(caminho_quarto_maria_xml)
        assert len(ambientes) == 1
        assert ambientes[0].nome == "Projeto - Quarto Maria"

    def test_extrai_20_modulos_e_48_itens(self, caminho_quarto_maria_xml):
        ambientes = extract_promob_xml.extrair(caminho_quarto_maria_xml)
        total_modulos = sum(len(a.modulos) for a in ambientes)
        total_itens = sum(len(m.itens) for a in ambientes for m in a.modulos)
        assert total_modulos == 20
        assert total_itens == 48

    def test_itens_carregam_rastreabilidade(self, caminho_quarto_maria_xml):
        ambientes = extract_promob_xml.extrair(caminho_quarto_maria_xml)
        algum_item = ambientes[0].modulos[0].itens[0]
        assert "GUID=" in algum_item.origem

    def test_dimensoes_em_milimetros_presentes(self, caminho_quarto_maria_xml):
        ambientes = extract_promob_xml.extrair(caminho_quarto_maria_xml)
        itens_m2 = [it for a in ambientes for m in a.modulos for it in m.itens if it.unidade == "M2"]
        assert itens_m2
        for item in itens_m2:
            assert item.largura_mm is not None
            assert item.altura_mm is not None

    def test_arquivo_inexistente_da_erro_claro(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            extract_promob_xml.extrair(tmp_path / "nao_existe.xml")
