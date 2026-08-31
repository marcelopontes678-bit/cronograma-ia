from datetime import datetime, timezone

import pytest

from api.db import jobs as jobs_db
from api.schemas.extracao import Ambiente, BoundingBox, ExtracaoResultado, Modulo, OrigemModulo, StatusExtracao


def _resultado(job_id, modulos):
    return ExtracaoResultado(
        job_id=job_id, arquivo_origem="x.pdf", status=StatusExtracao.AGUARDANDO_REVISAO,
        ambientes=[Ambiente(nome="Banheiro", modulos=modulos)],
        criado_em=datetime.now(timezone.utc), atualizado_em=datetime.now(timezone.utc),
    )


def _modulo(id_, confianca, origem=OrigemModulo.VISION_AUTOMATICO):
    return Modulo(
        id=id_, nome="Armario", ambiente="Banheiro", quantidade_portas=0, quantidade_gavetas=0,
        material_sugerido="MDF", material_explicito_no_desenho=True, confianca=confianca,
        bounding_boxes=[BoundingBox(pagina=1, x=0, y=0, width=0.1, height=0.1)], origem=origem,
    )


class TestSalvarECarregar:
    def test_roundtrip_preserva_dados(self, tmp_path):
        resultado = _resultado("job_1", [_modulo("m1", 0.9)])
        jobs_db.salvar(resultado, tmp_path)
        carregado = jobs_db.carregar("job_1", tmp_path)
        assert carregado.job_id == "job_1"
        assert carregado.ambientes[0].modulos[0].id == "m1"

    def test_job_inexistente_da_erro_claro(self, tmp_path):
        with pytest.raises(jobs_db.JobNaoEncontradoError):
            jobs_db.carregar("nao_existe", tmp_path)

    def test_job_id_com_path_traversal_e_bloqueado(self, tmp_path):
        with pytest.raises(jobs_db.JobInvalidoError):
            jobs_db.carregar("../../etc/passwd", tmp_path)


class TestAtualizarModulo:
    def test_corrige_modulo_e_marca_confirmado_humano(self, tmp_path):
        jobs_db.salvar(_resultado("job_1", [_modulo("m1", 0.5)]), tmp_path)
        modulo = jobs_db.atualizar_modulo("job_1", "m1", {"largura_mm": 890, "confianca": 1.0}, tmp_path)
        assert modulo.largura_mm == 890
        assert modulo.origem == OrigemModulo.CONFIRMADO_HUMANO

        recarregado = jobs_db.carregar("job_1", tmp_path)
        assert recarregado.ambientes[0].modulos[0].largura_mm == 890

    def test_modulo_inexistente_da_erro_claro(self, tmp_path):
        jobs_db.salvar(_resultado("job_1", [_modulo("m1", 0.5)]), tmp_path)
        with pytest.raises(jobs_db.JobInvalidoError):
            jobs_db.atualizar_modulo("job_1", "nao_existe", {}, tmp_path)


class TestAdicionarModulo:
    def test_adiciona_a_ambiente_existente(self, tmp_path):
        jobs_db.salvar(_resultado("job_1", [_modulo("m1", 0.9)]), tmp_path)
        novo = _modulo("m2", 1.0, origem=OrigemModulo.ADICIONADO_MANUAL)
        jobs_db.adicionar_modulo("job_1", "Banheiro", novo, tmp_path)

        resultado = jobs_db.carregar("job_1", tmp_path)
        assert len(resultado.ambientes[0].modulos) == 2

    def test_cria_ambiente_novo_quando_nao_existe(self, tmp_path):
        jobs_db.salvar(_resultado("job_1", [_modulo("m1", 0.9)]), tmp_path)
        novo = _modulo("m2", 1.0, origem=OrigemModulo.ADICIONADO_MANUAL)
        jobs_db.adicionar_modulo("job_1", "Cozinha", novo, tmp_path)

        resultado = jobs_db.carregar("job_1", tmp_path)
        nomes = [a.nome for a in resultado.ambientes]
        assert "Cozinha" in nomes


class TestConfirmar:
    def test_bloqueia_quando_ha_modulo_de_baixa_confianca_nao_revisado(self, tmp_path):
        jobs_db.salvar(_resultado("job_1", [_modulo("m1", 0.5)]), tmp_path)
        with pytest.raises(jobs_db.ConfirmacaoBloqueadaError):
            jobs_db.confirmar("job_1", tmp_path)

    def test_permite_quando_modulo_baixa_confianca_ja_foi_corrigido(self, tmp_path):
        jobs_db.salvar(_resultado("job_1", [_modulo("m1", 0.5)]), tmp_path)
        jobs_db.atualizar_modulo("job_1", "m1", {"confianca": 1.0}, tmp_path)
        resultado = jobs_db.confirmar("job_1", tmp_path)
        assert resultado.status == StatusExtracao.CONFIRMADO

    def test_baixa_confianca_de_origem_humana_nao_bloqueia(self, tmp_path):
        # um modulo ADICIONADO_MANUAL ou CONFIRMADO_HUMANO com confianca baixa
        # nao deve travar a confirmacao -- so vision_automatico bloqueia
        modulo_manual = _modulo("m1", 0.3, origem=OrigemModulo.ADICIONADO_MANUAL)
        jobs_db.salvar(_resultado("job_1", [modulo_manual]), tmp_path)
        resultado = jobs_db.confirmar("job_1", tmp_path)
        assert resultado.status == StatusExtracao.CONFIRMADO
