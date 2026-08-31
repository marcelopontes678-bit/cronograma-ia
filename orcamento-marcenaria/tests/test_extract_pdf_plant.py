import pytest

import extract_pdf_plant


class TestExtracaoRealBanheiro:
    def test_todas_paginas_sao_vetoriais(self, caminho_pdf_banheiro):
        paginas = extract_pdf_plant.extrair(caminho_pdf_banheiro)
        assert len(paginas) == 6
        assert all(p.tem_texto_vetorial for p in paginas)
        assert all(not p.precisa_assistencia for p in paginas)

    def test_textos_tem_coordenadas_e_pagina(self, caminho_pdf_banheiro):
        paginas = extract_pdf_plant.extrair(caminho_pdf_banheiro)
        primeira = paginas[0]
        assert primeira.textos
        texto = primeira.textos[0]
        assert texto.pagina == 1
        assert texto.x0 < texto.x1
        assert texto.y0 < texto.y1

    def test_pagina_com_material_de_marcenaria_e_encontrada(self, caminho_pdf_banheiro):
        # pagina 5 (Vista A) tem as anotacoes de MDF lidas manualmente nesta sessao
        paginas = extract_pdf_plant.extrair(caminho_pdf_banheiro)
        pagina_5 = next(p for p in paginas if p.pagina == 5)
        textos_concatenados = " ".join(t.texto for t in pagina_5.textos)
        assert "MDF" in textos_concatenados

    def test_arquivo_inexistente_da_erro_claro(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            extract_pdf_plant.extrair(tmp_path / "nao_existe.pdf")


class TestExtracaoRealCozinha:
    def test_paginas_de_marcenaria_tem_termos_esperados(self, caminho_pdf_cozinha):
        paginas = extract_pdf_plant.extrair(caminho_pdf_cozinha)
        assert len(paginas) == 16
        pagina_9 = next(p for p in paginas if p.pagina == 9)
        textos_concatenados = " ".join(t.texto for t in pagina_9.textos)
        assert "Armário" in textos_concatenados
        assert "MDF" in textos_concatenados
