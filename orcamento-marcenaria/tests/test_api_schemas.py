from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from api.schemas.extracao import Ambiente, BoundingBox, ExtracaoResultado, Modulo, OrigemModulo, StatusExtracao
from api.schemas.feedback import FeedbackRequest, RegraAprendida
from api.schemas.preferencias import PreferenciasGlobais
from api.schemas.orcamento import OrcamentoRequest


class TestModulo:
    def _bbox(self):
        return BoundingBox(pagina=1, x=0.1, y=0.1, width=0.2, height=0.2)

    def test_confianca_fora_do_intervalo_e_invalida(self):
        with pytest.raises(ValidationError):
            Modulo(
                id="m1", nome="x", ambiente="a", quantidade_portas=0, quantidade_gavetas=0,
                material_sugerido="MDF", material_explicito_no_desenho=True,
                confianca=1.5, bounding_boxes=[self._bbox()],
            )

    def test_dimensao_ausente_fica_none_nao_zero(self):
        modulo = Modulo(
            id="m1", nome="x", ambiente="a", quantidade_portas=0, quantidade_gavetas=0,
            material_sugerido="MDF", material_explicito_no_desenho=False,
            confianca=0.5, bounding_boxes=[self._bbox()],
        )
        assert modulo.largura_mm is None
        assert modulo.origem == OrigemModulo.VISION_AUTOMATICO  # default


class TestBoundingBoxNormalizado:
    def test_coordenadas_fora_de_0_1_sao_invalidas(self):
        with pytest.raises(ValidationError):
            BoundingBox(pagina=1, x=1.2, y=0, width=0.1, height=0.1)

    def test_pagina_deve_ser_positiva(self):
        with pytest.raises(ValidationError):
            BoundingBox(pagina=0, x=0, y=0, width=0.1, height=0.1)


class TestExtracaoResultado:
    def test_status_gate_existe_com_valores_esperados(self):
        assert {s.value for s in StatusExtracao} == {"processando", "aguardando_revisao", "confirmado", "erro"}

    def test_ambientes_default_vazio(self):
        resultado = ExtracaoResultado(
            job_id="j1", arquivo_origem="a.pdf", status=StatusExtracao.PROCESSANDO,
            criado_em=datetime.now(timezone.utc), atualizado_em=datetime.now(timezone.utc),
        )
        assert resultado.ambientes == []
        assert resultado.avisos == []


class TestPreferenciasGlobais:
    def test_defaults_documentados(self):
        p = PreferenciasGlobais(usuario_id="u1")
        assert p.espessuras.caixa_mm == 15
        assert p.espessuras.porta_mm == 18
        assert p.metodo_uniao.value == "cavilha"
        assert p.acabamento_interno_padrao == "MDF Branco"

    def test_serializa_e_desserializa_sem_perder_dados(self):
        p = PreferenciasGlobais(usuario_id="u1")
        p.espessuras.caixa_mm = 18
        json_str = p.model_dump_json()
        p2 = PreferenciasGlobais.model_validate_json(json_str)
        assert p2.espessuras.caixa_mm == 18


class TestFeedbackSchemas:
    def test_feedback_request_minimo(self):
        req = FeedbackRequest(usuario_id="u1", instrucao="teste")
        assert req.job_id is None
        assert req.modulo_id is None

    def test_regra_aprendida_exige_campos_obrigatorios(self):
        with pytest.raises(ValidationError):
            RegraAprendida(id="r1", usuario_id="u1")  # falta instrucao_original, regra_normalizada, criado_em


class TestOrcamentoRequest:
    def test_faturamento_negativo_e_invalido(self):
        with pytest.raises(ValidationError):
            OrcamentoRequest(job_id="j1", faturamento_acumulado=-1)

    def test_defaults_de_mao_de_obra_sao_zero(self):
        req = OrcamentoRequest(job_id="j1", faturamento_acumulado=100_000)
        assert req.custo_hora_mao_de_obra == 0
        assert req.horas_estimadas == 0
