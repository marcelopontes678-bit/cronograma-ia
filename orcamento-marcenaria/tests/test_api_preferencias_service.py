import pytest

from api.schemas.preferencias import EspessurasPadrao, PreferenciasGlobais
from api.services.preferencias_service import (
    PreferenciasInvalidasError,
    carregar_preferencias,
    salvar_preferencias,
)


class TestCarregarPreferencias:
    def test_usuario_sem_preferencias_recebe_defaults(self, tmp_path):
        p = carregar_preferencias("usuario_novo", tmp_path)
        assert p.usuario_id == "usuario_novo"
        assert p.espessuras.caixa_mm == 15

    def test_salvar_e_recarregar_preserva_valores_customizados(self, tmp_path):
        p = PreferenciasGlobais(usuario_id="personatto", espessuras=EspessurasPadrao(caixa_mm=18, porta_mm=20))
        caminho = salvar_preferencias(p, tmp_path)
        assert caminho.exists()

        p2 = carregar_preferencias("personatto", tmp_path)
        assert p2.espessuras.caixa_mm == 18
        assert p2.espessuras.porta_mm == 20

    def test_path_traversal_e_bloqueado(self, tmp_path):
        with pytest.raises(PreferenciasInvalidasError):
            carregar_preferencias("../../etc/passwd", tmp_path)

    def test_arquivo_corrompido_da_erro_claro(self, tmp_path):
        (tmp_path / "corrompido.json").write_text("{ isso nao e json valido")
        with pytest.raises(PreferenciasInvalidasError):
            carregar_preferencias("corrompido", tmp_path)

    def test_escrita_atomica_nao_deixa_arquivo_temporario(self, tmp_path):
        salvar_preferencias(PreferenciasGlobais(usuario_id="u1"), tmp_path)
        assert not list(tmp_path.glob(".tmp_pref_*"))
