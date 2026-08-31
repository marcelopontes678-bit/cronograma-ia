"""Testa extract_skp.py contra um CSV sintetico (sanity check apenas -- o
usuario nao tem acesso ao SketchUp nesta sessao para gerar um relatorio
'File > Generate Report' real, entao isto NAO substitui um teste contra
um relatorio real quando ele existir)."""
import pytest

import extract_skp


@pytest.fixture
def relatorio_sintetico(tmp_path):
    caminho = tmp_path / "relatorio_sanity.csv"
    caminho.write_text(
        "Name,Length,Width,Height,Count,Material\n"
        'Porta Armario,600,18,720,2,"MDF Branco"\n'
        'Prateleira,580,300,18,4,"MDF Branco"\n',
        encoding="utf-8",
    )
    return caminho


class TestExtracaoSintetica:
    def test_extrai_dois_itens(self, relatorio_sintetico):
        itens = extract_skp.extrair(relatorio_sintetico)
        assert len(itens) == 2

    def test_dimensoes_e_quantidade_batem_com_o_csv(self, relatorio_sintetico):
        itens = extract_skp.extrair(relatorio_sintetico)
        porta = next(i for i in itens if i.nome == "Porta Armario")
        assert porta.comprimento_mm == 600
        assert porta.largura_mm == 18
        assert porta.altura_mm == 720
        assert porta.quantidade == 2
        assert porta.material == "MDF Branco"

    def test_origem_referencia_linha_do_arquivo(self, relatorio_sintetico):
        itens = extract_skp.extrair(relatorio_sintetico)
        assert "linha=2" in itens[0].origem


class TestRelatorioInvalido:
    def test_arquivo_inexistente(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            extract_skp.extrair(tmp_path / "nao_existe.csv")

    def test_sem_coluna_de_nome_reconhecivel(self, tmp_path):
        caminho = tmp_path / "sem_nome.csv"
        caminho.write_text("ColunaX,ColunaY\nA,B\n", encoding="utf-8")
        with pytest.raises(extract_skp.RelatorioSkpInvalidoError):
            extract_skp.extrair(caminho)

    def test_aliases_de_coluna_em_portugues(self, tmp_path):
        caminho = tmp_path / "relatorio_pt.csv"
        caminho.write_text(
            "Nome,Comprimento,Largura,Altura,Quantidade,Material\n"
            'Gaveta,400,300,150,3,"MDF Cinza"\n',
            encoding="utf-8",
        )
        itens = extract_skp.extrair(caminho)
        assert len(itens) == 1
        assert itens[0].quantidade == 3
