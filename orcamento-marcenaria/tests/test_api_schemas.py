from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from api.schemas.extracao import (
    Ambiente,
    AuditoriaVisual,
    Componentes,
    Dimensoes,
    EspecificacoesMateriais,
    ExtracaoResultado,
    Modulo,
    OrigemModulo,
    StatusExtracao,
)
from api.schemas.feedback import FeedbackRequest, RegraAprendida
from api.schemas.preferencias import PreferenciasGlobais
from api.schemas.orcamento import OrcamentoRequest


def _materiais(**overrides):
    dados = dict(caixaria="MDF Branco", frente="MDF Branco", fundo="MDF Branco", metodo_uniao="minifix", fixacao_fundo="encaixado_em_rebaixo")
    dados.update(overrides)
    return EspecificacoesMateriais(**dados)


def _auditoria():
    return AuditoriaVisual(pagina_pdf=1, bounding_box=[100, 100, 200, 200])


class TestModulo:
    def test_confianca_fora_do_intervalo_e_invalida(self):
        with pytest.raises(ValidationError):
            Modulo(
                id="m1", nome="x", especificacoes_materiais=_materiais(),
                auditoria_visual=_auditoria(), confianca=1.5,
            )

    def test_dimensao_ausente_fica_none_nao_zero(self):
        modulo = Modulo(
            id="m1", nome="x", especificacoes_materiais=_materiais(),
            auditoria_visual=_auditoria(), confianca=0.5,
        )
        assert modulo.dimensoes.largura_mm is None
        assert modulo.origem == OrigemModulo.VISION_AUTOMATICO  # default

    def test_campos_inferidos_default_vazio(self):
        modulo = Modulo(
            id="m1", nome="x", especificacoes_materiais=_materiais(),
            auditoria_visual=_auditoria(), confianca=0.9,
        )
        assert modulo.especificacoes_materiais.campos_inferidos == []
        assert modulo.componentes.portas == 0
        assert modulo.ferragens_sugeridas == []
        assert modulo.itens_complementares == []


class TestAuditoriaVisual:
    def test_bounding_box_fora_de_0_1000_e_invalido(self):
        with pytest.raises(ValidationError):
            AuditoriaVisual(pagina_pdf=1, bounding_box=[100, 100, 200, 1200])

    def test_bounding_box_precisa_ter_4_valores(self):
        with pytest.raises(ValidationError):
            AuditoriaVisual(pagina_pdf=1, bounding_box=[100, 100, 200])

    def test_pagina_deve_ser_positiva(self):
        with pytest.raises(ValidationError):
            AuditoriaVisual(pagina_pdf=0, bounding_box=[0, 0, 10, 10])


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

    def test_ambiente_usa_nome_ambiente(self):
        ambiente = Ambiente(nome_ambiente="Cozinha")
        assert ambiente.modulos == []


class TestPreferenciasGlobais:
    def test_defaults_documentados(self):
        p = PreferenciasGlobais(usuario_id="u1")
        assert p.espessuras.caixa_mm == 15
        assert p.espessuras.porta_mm == 18
        assert p.espessuras.sarrafo_superior_mm == 25
        assert p.metodo_uniao.value == "minifix"
        assert p.fixacao_fundo.value == "encaixado_em_rebaixo"
        assert p.acabamento_interno_padrao == "MDF Branco"
        assert p.regra_fundo_exposto_forca_cor_caixaria is True

    def test_faixas_dobradicas_por_altura_default(self):
        p = PreferenciasGlobais(usuario_id="u1")
        faixas = p.faixas_dobradicas_por_altura
        assert faixas[0].altura_maxima_mm == 900
        assert faixas[0].quantidade_dobradicas == 2
        assert faixas[-1].quantidade_dobradicas == 5

    def test_regra_apoio_por_ambiente_default(self):
        p = PreferenciasGlobais(usuario_id="u1")
        assert "Cozinha" in p.regra_apoio_por_ambiente.ambientes_molhados
        assert p.regra_apoio_por_ambiente.apoio_area_molhada.value == "pe_plastico"
        assert p.regra_apoio_por_ambiente.apoio_area_seca.value == "rodape_mdf"

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
