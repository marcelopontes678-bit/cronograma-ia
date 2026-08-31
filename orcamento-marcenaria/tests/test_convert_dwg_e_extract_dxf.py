import shutil

import pytest

import convert_dwg
import extract_promob_dxf

DWG2DXF_DISPONIVEL = shutil.which("dwg2dxf") is not None


class TestLocalizarConversores:
    def test_dwg2dxf_cai_no_fallback_do_path_quando_caminho_customizado_nao_existe(self, tmp_path, monkeypatch):
        # comportamento pretendido: um --dwg2dxf-path invalido nao devolve
        # None de cara, cai para o shutil.which (PATH) -- so retorna None
        # quando NEM o caminho customizado NEM o PATH tem o binario
        monkeypatch.setattr(convert_dwg.shutil, "which", lambda nome: None)
        assert convert_dwg.localizar_dwg2dxf(str(tmp_path / "nao_existe")) is None

    def test_oda_cai_no_fallback_do_path_quando_caminho_customizado_nao_existe(self, tmp_path, monkeypatch):
        monkeypatch.setattr(convert_dwg.shutil, "which", lambda nome: None)
        assert convert_dwg.localizar_oda_converter(str(tmp_path / "nao_existe")) is None


class TestConverterSemMotorDisponivel:
    def test_erro_claro_quando_nenhum_conversor_encontrado(self, tmp_path, monkeypatch):
        monkeypatch.setattr(convert_dwg, "localizar_dwg2dxf", lambda caminho_informado=None: None)
        monkeypatch.setattr(convert_dwg, "localizar_oda_converter", lambda caminho_informado=None: None)

        arquivo_fake = tmp_path / "projeto.dwg"
        arquivo_fake.write_bytes(b"nao importa, motor nao vai ser chamado")

        with pytest.raises(convert_dwg.ConversorDwgNaoEncontradoError):
            convert_dwg.converter_dwg_para_dxf(arquivo_fake, tmp_path / "saida")

    def test_arquivo_dwg_inexistente_da_erro_antes_de_procurar_motor(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            convert_dwg.converter_dwg_para_dxf(tmp_path / "nao_existe.dwg", tmp_path / "saida")


@pytest.mark.skipif(not DWG2DXF_DISPONIVEL, reason="dwg2dxf (LibreDWG) nao instalado neste ambiente")
class TestConversaoRealComLibreDWG:
    """Usa o dwg2dxf de verdade (LibreDWG 0.14.8592, compilado nesta sessao)
    contra um DWG real (arquivo de teste do proprio LibreDWG, incluido em
    tests/arquivos_exemplo/libredwg_amostra/)."""

    def test_converte_dwg_real_para_dxf_valido(self, caminho_dwg_amostra, tmp_path):
        caminho_dxf = convert_dwg.converter_dwg_para_dxf(caminho_dwg_amostra, tmp_path, timeout_segundos=60)
        assert caminho_dxf.exists()
        conteudo = caminho_dxf.read_text(errors="ignore")
        assert "SECTION" in conteudo
        assert "$ACADVER" in conteudo

    def test_extrai_blocos_geometria_e_textos_do_dxf_convertido(self, caminho_dwg_amostra, tmp_path):
        caminho_dxf = convert_dwg.converter_dwg_para_dxf(caminho_dwg_amostra, tmp_path, timeout_segundos=60)
        resultado = extract_promob_dxf.extrair(caminho_dxf)

        # contagens conferidas manualmente nesta sessao contra o mesmo arquivo
        assert len(resultado.layers) == 5
        assert len(resultado.blocos) == 10
        assert len(resultado.geometrias) == 21
        assert len(resultado.textos) == 3

    def test_blocos_carregam_handle_de_rastreabilidade(self, caminho_dwg_amostra, tmp_path):
        caminho_dxf = convert_dwg.converter_dwg_para_dxf(caminho_dwg_amostra, tmp_path, timeout_segundos=60)
        resultado = extract_promob_dxf.extrair(caminho_dxf)
        assert all(b.origem.startswith("handle=") for b in resultado.blocos)


class TestExtractPromobDxfArquivoInexistente:
    def test_erro_claro(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            extract_promob_dxf.extrair(tmp_path / "nao_existe.dxf")
