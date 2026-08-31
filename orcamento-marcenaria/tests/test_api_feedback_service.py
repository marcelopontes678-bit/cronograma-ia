from unittest.mock import MagicMock, patch

import pytest

from api.schemas.feedback import FeedbackRequest
from api.services.feedback_service import (
    FeedbackInvalidoError,
    desativar_regra,
    listar_regras,
    listar_regras_normalizadas_ativas,
    registrar_feedback,
)


def _resposta_texto(texto):
    bloco = MagicMock()
    bloco.type = "text"
    bloco.text = texto
    resposta = MagicMock()
    resposta.content = [bloco]
    return resposta


class TestRegistrarFeedback:
    def test_normaliza_e_persiste_regra(self, tmp_path):
        req = FeedbackRequest(
            usuario_id="marceneiro_1", job_id="job_001", modulo_id="mod_005",
            instrucao="Sempre que houver porta de vidro reflecta, mude o fundo para a cor da caixa",
        )
        with patch("api.services.feedback_service.Anthropic") as MockAnthropic:
            MockAnthropic.return_value.messages.create.return_value = _resposta_texto(
                "Quando um modulo tiver porta com vidro reflecta, defina a cor do fundo igual a cor da caixa."
            )
            resp = registrar_feedback(req, api_key="fake", dir_storage=tmp_path)

        assert resp.regra.regra_normalizada.startswith("Quando um modulo")
        assert resp.total_regras_ativas_usuario == 1
        assert resp.regra.usuario_id == "marceneiro_1"
        assert resp.regra.origem_job_id == "job_001"

    def test_falha_de_rede_nao_e_mascarada(self, tmp_path):
        req = FeedbackRequest(usuario_id="u1", instrucao="teste")
        with patch("api.services.feedback_service.Anthropic") as MockAnthropic:
            MockAnthropic.return_value.messages.create.side_effect = RuntimeError("timeout")
            with pytest.raises(FeedbackInvalidoError):
                registrar_feedback(req, api_key="fake", dir_storage=tmp_path)


class TestCicloDeVidaDaRegra:
    def _registrar_duas_regras(self, tmp_path):
        ids = []
        for instrucao, normalizada in [
            ("regra 1", "Regra normalizada 1."),
            ("regra 2", "Regra normalizada 2."),
        ]:
            req = FeedbackRequest(usuario_id="u1", instrucao=instrucao)
            with patch("api.services.feedback_service.Anthropic") as MockAnthropic:
                MockAnthropic.return_value.messages.create.return_value = _resposta_texto(normalizada)
                resp = registrar_feedback(req, api_key="fake", dir_storage=tmp_path)
            ids.append(resp.regra.id)
        return ids

    def test_regras_ativas_alimentam_o_vision_extractor(self, tmp_path):
        self._registrar_duas_regras(tmp_path)
        ativas = listar_regras_normalizadas_ativas("u1", tmp_path)
        assert len(ativas) == 2

    def test_desativar_e_soft_delete_preserva_historico(self, tmp_path):
        ids = self._registrar_duas_regras(tmp_path)
        desativar_regra("u1", ids[0], tmp_path)

        ativas = listar_regras_normalizadas_ativas("u1", tmp_path)
        assert len(ativas) == 1

        todas = listar_regras("u1", tmp_path)
        assert len(todas) == 2
        assert sum(1 for r in todas if not r.ativa) == 1

    def test_usuario_sem_regras_retorna_lista_vazia(self, tmp_path):
        assert listar_regras_normalizadas_ativas("usuario_sem_regras", tmp_path) == []

    def test_desativar_regra_inexistente_da_erro_claro(self, tmp_path):
        self._registrar_duas_regras(tmp_path)
        with pytest.raises(FeedbackInvalidoError):
            desativar_regra("u1", "regra_inexistente", tmp_path)

    def test_path_traversal_e_bloqueado(self, tmp_path):
        with pytest.raises(FeedbackInvalidoError):
            listar_regras("../../etc/passwd", tmp_path)
