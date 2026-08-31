from pathlib import Path
from unittest.mock import MagicMock, patch

from httpx import AsyncClient

from tests.conftest import obter_token

CAMINHO_PDF_BANHEIRO = Path(__file__).parent / "arquivos_exemplo" / "Banheiro.pdf"


def _materiais(caixaria="MDF Cinza Cobalto Berneck"):
    return {
        "caixaria": caixaria, "frente": caixaria, "fundo": "MDF Branco",
        "metodo_uniao": "minifix", "fixacao_fundo": "encaixado_em_rebaixo", "campos_inferidos": [],
    }


def _resposta_tool_use(ambientes, avisos=None):
    bloco = MagicMock()
    bloco.type = "tool_use"
    bloco.name = "registrar_extracao"
    bloco.input = {"ambientes": ambientes, "avisos": avisos or []}
    resposta = MagicMock()
    resposta.content = [bloco]
    return resposta


def _ambiente_banheiro_mock(confianca_mod1=0.9):
    return [{
        "nome_ambiente": "Banheiro",
        "modulos": [{
            "id": "MOD-001", "nome": "Armario superior", "vista_referencia": "",
            "dimensoes": {"largura_mm": 930, "altura_mm": 1040, "profundidade_mm": 150},
            "componentes": {"portas": 1, "gavetas": 0, "prateleiras_internas": 1},
            "especificacoes_materiais": _materiais(),
            "ferragens_sugeridas": [], "itens_complementares": [],
            "auditoria_visual": {"pagina_pdf": 1, "bounding_box": [400, 100, 700, 400]},
            "descricao_resumida": "", "confianca": confianca_mod1,
        }],
    }]


async def _upload_job(client: AsyncClient, token: str, ambientes=None) -> dict:
    ambientes = ambientes if ambientes is not None else _ambiente_banheiro_mock()
    with patch("app.services.orcamento_vision_extractor.Anthropic") as MockAnthropic:
        MockAnthropic.return_value.messages.create.return_value = _resposta_tool_use(ambientes)
        with open(CAMINHO_PDF_BANHEIRO, "rb") as f:
            resp = await client.post(
                "/api/v1/orcamentos/jobs",
                headers={"Authorization": f"Bearer {token}"},
                files={"arquivo": ("banheiro.pdf", f, "application/pdf")},
            )
    assert resp.status_code == 202, resp.text
    return resp.json()


class TestPreferenciasGlobais:
    async def test_get_cria_defaults_quando_nao_existe(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        resp = await client.get("/api/v1/orcamentos/preferencias", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        config = resp.json()["configuracao"]
        assert config["metodo_uniao"] == "minifix"
        assert config["espessuras"]["caixa_mm"] == 15.0

    async def test_put_sem_token_e_401(self, client: AsyncClient):
        resp = await client.put("/api/v1/orcamentos/preferencias", json={})
        assert resp.status_code == 401

    async def test_put_persiste_alteracao(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.put(
            "/api/v1/orcamentos/preferencias",
            json={"acabamento_interno_padrao": "MDF Cinza Cobalto"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["configuracao"]["acabamento_interno_padrao"] == "MDF Cinza Cobalto"

        resp2 = await client.get("/api/v1/orcamentos/preferencias", headers=headers)
        assert resp2.json()["configuracao"]["acabamento_interno_padrao"] == "MDF Cinza Cobalto"

    async def test_isolamento_multi_tenant_preferencias(self, client: AsyncClient, empresa_a, empresa_b):
        """O ponto mais importante de seguranca desta migracao: preferencias
        de uma empresa nunca vazam nem sao editaveis por outra."""
        token_a = await obter_token(client, "admin@a.com", "senhaA123!")
        token_b = await obter_token(client, "admin@b.com", "senhaB123!")

        await client.put(
            "/api/v1/orcamentos/preferencias",
            json={"acabamento_interno_padrao": "Cor da Empresa A"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        resp_b = await client.get(
            "/api/v1/orcamentos/preferencias", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert resp_b.json()["configuracao"]["acabamento_interno_padrao"] != "Cor da Empresa A"
        assert resp_b.json()["empresa_id"] == str(empresa_b[0].id)


class TestOrcamentoJobs:
    async def test_criar_e_consultar_job_com_extracao_mockada(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        job_inicial = await _upload_job(client, token)
        assert job_inicial["status"] == "processando"
        job_id = job_inicial["job_id"]

        # BackgroundTasks roda ate o final antes do ASGITransport devolver a
        # resposta -- ja deve estar aguardando_revisao com o modulo mockado.
        resp2 = await client.get(f"/api/v1/orcamentos/jobs/{job_id}", headers=headers)
        assert resp2.status_code == 200
        job = resp2.json()
        assert job["status"] == "aguardando_revisao"
        assert len(job["ambientes"]) == 1
        assert job["ambientes"][0]["modulos"][0]["nome"] == "Armario superior"

        resp3 = await client.get("/api/v1/orcamentos/jobs", headers=headers)
        assert any(j["id"] == job_id for j in resp3.json())

    async def test_job_inexistente_da_404(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        resp = await client.get(
            "/api/v1/orcamentos/jobs/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_isolamento_multi_tenant_job_da_404_nao_403(self, client: AsyncClient, empresa_a, empresa_b):
        """Job de outra empresa deve dar 404 (nao 403) -- nao revela nem que
        o job existe."""
        token_a = await obter_token(client, "admin@a.com", "senhaA123!")
        token_b = await obter_token(client, "admin@b.com", "senhaB123!")

        job = await _upload_job(client, token_a)

        resp = await client.get(
            f"/api/v1/orcamentos/jobs/{job['job_id']}", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert resp.status_code == 404

    async def test_get_pagina_pdf_retorna_png(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}
        job = await _upload_job(client, token)

        resp = await client.get(f"/api/v1/orcamentos/jobs/{job['job_id']}/paginas/1", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert len(resp.content) > 0
        assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"  # assinatura PNG

    async def test_get_pagina_pdf_inexistente_da_404(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}
        job = await _upload_job(client, token)

        resp = await client.get(f"/api/v1/orcamentos/jobs/{job['job_id']}/paginas/999", headers=headers)
        assert resp.status_code == 404

    async def test_get_pagina_pdf_isolamento_multi_tenant(self, client: AsyncClient, empresa_a, empresa_b):
        token_a = await obter_token(client, "admin@a.com", "senhaA123!")
        token_b = await obter_token(client, "admin@b.com", "senhaB123!")
        job = await _upload_job(client, token_a)

        resp = await client.get(
            f"/api/v1/orcamentos/jobs/{job['job_id']}/paginas/1", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert resp.status_code == 404

        resp_lista = await client.get(
            "/api/v1/orcamentos/jobs", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert all(j["id"] != job["job_id"] for j in resp_lista.json())


class TestRevisaoEConfirmacao:
    async def test_confirmar_com_baixa_confianca_e_bloqueado(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}
        job = await _upload_job(client, token, ambientes=_ambiente_banheiro_mock(confianca_mod1=0.5))

        resp = await client.post(f"/api/v1/orcamentos/jobs/{job['job_id']}/confirmar", headers=headers)
        assert resp.status_code == 409

    async def test_corrigir_modulo_libera_confirmacao(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}
        job = await _upload_job(client, token, ambientes=_ambiente_banheiro_mock(confianca_mod1=0.5))
        job_id = job["job_id"]

        # PDF de 6 paginas / PAGINAS_POR_LOTE=4 default -- 2 lotes, cada um
        # retornando o mesmo modulo mockado -- corrige TODOS os de baixa
        # confianca, nao so o primeiro.
        detalhe = (await client.get(f"/api/v1/orcamentos/jobs/{job_id}", headers=headers)).json()
        modulos = [m for a in detalhe["ambientes"] for m in a["modulos"]]
        assert len(modulos) == 2
        primeiro_modulo_id = modulos[0]["id"]

        resp_patch = await client.patch(
            f"/api/v1/orcamentos/jobs/{job_id}/modulos/{primeiro_modulo_id}",
            json={"confianca": 1.0, "dimensoes": {"largura_mm": 900}},
            headers=headers,
        )
        assert resp_patch.status_code == 200
        assert resp_patch.json()["origem"] == "confirmado_humano"
        assert resp_patch.json()["dimensoes"]["largura_mm"] == 900
        assert resp_patch.json()["dimensoes"]["altura_mm"] == 1040  # patch parcial nao apaga o resto

        # ainda falta o segundo modulo -- confirmar deve continuar bloqueado
        resp_bloqueado = await client.post(f"/api/v1/orcamentos/jobs/{job_id}/confirmar", headers=headers)
        assert resp_bloqueado.status_code == 409

        for m in modulos[1:]:
            await client.patch(
                f"/api/v1/orcamentos/jobs/{job_id}/modulos/{m['id']}", json={"confianca": 1.0}, headers=headers
            )

        resp_confirmar = await client.post(f"/api/v1/orcamentos/jobs/{job_id}/confirmar", headers=headers)
        assert resp_confirmar.status_code == 200
        assert resp_confirmar.json()["status"] == "confirmado"

    async def test_adicionar_modulo_manual(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}
        job = await _upload_job(client, token)

        resp = await client.post(
            f"/api/v1/orcamentos/jobs/{job['job_id']}/modulos",
            headers=headers,
            json={
                "nome_ambiente": "Banheiro",
                "modulo": {
                    "id": "mod_manual_01", "nome": "Prateleira adicional",
                    "dimensoes": {"largura_mm": 600, "altura_mm": 300, "profundidade_mm": 250},
                    "especificacoes_materiais": _materiais(caixaria="MDF Branco"),
                    "auditoria_visual": {"pagina_pdf": 1, "bounding_box": [0, 0, 100, 100]},
                    "confianca": 1.0, "origem": "adicionado_manual",
                },
            },
        )
        assert resp.status_code == 201

        detalhe = (await client.get(f"/api/v1/orcamentos/jobs/{job['job_id']}", headers=headers)).json()
        modulos = [m for a in detalhe["ambientes"] for m in a["modulos"]]
        # PDF de 6 paginas / PAGINAS_POR_LOTE=4 default -- 2 lotes, cada um
        # retornando o modulo mockado -- + 1 manual = 3.
        assert len(modulos) == 3
        assert any(m["id"] == "mod_manual_01" for m in modulos)


class TestOrcamentoPricing:
    async def test_orcamento_sem_fator_de_area_nao_inventa_custo(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}
        job = await _upload_job(client, token)
        job_id = job["job_id"]

        detalhe = (await client.get(f"/api/v1/orcamentos/jobs/{job_id}", headers=headers)).json()
        modulo_id = detalhe["ambientes"][0]["modulos"][0]["id"]
        await client.patch(
            f"/api/v1/orcamentos/jobs/{job_id}/modulos/{modulo_id}", json={"confianca": 1.0}, headers=headers
        )
        await client.post(f"/api/v1/orcamentos/jobs/{job_id}/confirmar", headers=headers)

        resp = await client.post(
            f"/api/v1/orcamentos?job_id={job_id}",
            json={"faturamento_acumulado": 100_000, "custo_hora_mao_de_obra": 30, "horas_estimadas": 5},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        corpo = resp.json()
        assert corpo["custo_material_total"] == 0.0
        assert corpo["custo_mao_de_obra"] == 150.0

    async def test_orcamento_job_nao_confirmado_da_409(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}
        job = await _upload_job(client, token)

        resp = await client.post(
            f"/api/v1/orcamentos?job_id={job['job_id']}",
            json={"faturamento_acumulado": 100_000},
            headers=headers,
        )
        assert resp.status_code == 409


class TestFeedback:
    async def test_ciclo_completo_de_feedback(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.services.orcamento_feedback_service.Anthropic") as MockAnthropic:
            bloco = MagicMock()
            bloco.type = "text"
            bloco.text = "Quando um modulo tiver porta com vidro reflecta, defina a cor do fundo igual a cor da caixa."
            MockAnthropic.return_value.messages.create.return_value = MagicMock(content=[bloco])
            resp = await client.post(
                "/api/v1/orcamentos/feedback",
                json={"instrucao": "Sempre que houver porta de vidro reflecta, mude o fundo para a cor da caixa"},
                headers=headers,
            )
        assert resp.status_code == 201, resp.text
        regra_id = resp.json()["regra"]["id"]

        resp2 = await client.get("/api/v1/orcamentos/regras", headers=headers)
        assert len(resp2.json()) == 1

        resp3 = await client.delete(f"/api/v1/orcamentos/regras/{regra_id}", headers=headers)
        assert resp3.status_code == 200
        assert resp3.json()["is_active"] is False
