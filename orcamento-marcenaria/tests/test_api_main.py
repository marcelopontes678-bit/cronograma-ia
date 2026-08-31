from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import api.config as config_module
from api.main import app


@pytest.fixture
def client(tmp_path):
    """Isola cada teste num storage proprio, sobrescrevendo os diretorios
    do Settings (usados dinamicamente pelas rotas a cada chamada)."""
    config_module.settings.dir_storage = tmp_path
    config_module.settings.dir_jobs = tmp_path / "jobs"
    config_module.settings.dir_preferencias = tmp_path / "preferencias"
    config_module.settings.dir_regras_aprendidas = tmp_path / "regras_aprendidas"
    return TestClient(app)


def _resposta_tool_use(ambientes, avisos=None):
    bloco = MagicMock()
    bloco.type = "tool_use"
    bloco.name = "registrar_extracao"
    bloco.input = {"ambientes": ambientes, "avisos": avisos or []}
    resposta = MagicMock()
    resposta.content = [bloco]
    return resposta


AMBIENTE_BANHEIRO_MOCK = [{
    "nome": "Banheiro",
    "modulos": [
        {
            "nome": "Armario superior", "largura_mm": 930, "altura_mm": 1040, "profundidade_mm": 150,
            "quantidade_portas": 1, "quantidade_gavetas": 0, "material_sugerido": "MDF Cinza Cobalto Berneck",
            "material_explicito_no_desenho": True, "confianca": 0.9,
            "bounding_box": {"pagina": 5, "x": 0.1, "y": 0.4, "width": 0.3, "height": 0.3}, "observacoes": "",
        },
        {
            "nome": "Armario inferior", "largura_mm": None, "altura_mm": 610, "profundidade_mm": 580,
            "quantidade_portas": 2, "quantidade_gavetas": 4, "material_sugerido": "MDF Verde Floresta Duratex",
            "material_explicito_no_desenho": True, "confianca": 0.5,
            "bounding_box": {"pagina": 5, "x": 0.1, "y": 0.7, "width": 0.3, "height": 0.2}, "observacoes": "largura ilegivel",
        },
    ],
}]


def _fazer_upload(client, caminho_pdf_banheiro):
    with patch("api.services.vision_extractor.Anthropic") as MockAnthropic:
        MockAnthropic.return_value.messages.create.return_value = _resposta_tool_use(AMBIENTE_BANHEIRO_MOCK)
        with open(caminho_pdf_banheiro, "rb") as f:
            r = client.post(
                "/api/v1/jobs", params={"usuario_id": "u_teste"},
                files={"arquivo": ("banheiro.pdf", f, "application/pdf")},
            )
    return r


class TestHealth:
    def test_health(self, client):
        assert client.get("/health").status_code == 200


class TestPreferencias:
    def test_get_usuario_novo_retorna_defaults(self, client):
        r = client.get("/api/v1/usuarios/u_teste/preferencias")
        assert r.status_code == 200
        assert r.json()["espessuras"]["caixa_mm"] == 15

    def test_put_salva_e_reflete_no_get(self, client):
        prefs = client.get("/api/v1/usuarios/u_teste/preferencias").json()
        prefs["espessuras"]["caixa_mm"] = 18
        r = client.put("/api/v1/usuarios/u_teste/preferencias", json=prefs)
        assert r.status_code == 200

        r2 = client.get("/api/v1/usuarios/u_teste/preferencias")
        assert r2.json()["espessuras"]["caixa_mm"] == 18

    def test_usuario_id_divergente_e_rejeitado(self, client):
        prefs = client.get("/api/v1/usuarios/u_teste/preferencias").json()
        r = client.put("/api/v1/usuarios/outro_usuario/preferencias", json=prefs)
        assert r.status_code == 400


class TestUploadEExtracao:
    def test_upload_dispara_extracao_em_background(self, client, caminho_pdf_banheiro):
        r = _fazer_upload(client, caminho_pdf_banheiro)
        assert r.status_code == 202
        assert r.json()["paginas"] == 6
        assert r.json()["job_id"].startswith("job_")

    def test_poll_apos_extracao_mostra_modulos(self, client, caminho_pdf_banheiro):
        job_id = _fazer_upload(client, caminho_pdf_banheiro).json()["job_id"]
        r = client.get(f"/api/v1/jobs/{job_id}")
        assert r.status_code == 200
        resultado = r.json()
        assert resultado["status"] == "aguardando_revisao"
        modulos = [m for amb in resultado["ambientes"] for m in amb["modulos"]]
        assert len(modulos) == 4  # 6 paginas / 2 por lote (default) -- mock repete os 2 modulos por lote

    def test_job_inexistente_da_404(self, client):
        assert client.get("/api/v1/jobs/job_nao_existe").status_code == 404


class TestFluxoDeRevisaoEConfirmacao:
    def test_confirmar_sem_revisar_e_bloqueado(self, client, caminho_pdf_banheiro):
        job_id = _fazer_upload(client, caminho_pdf_banheiro).json()["job_id"]
        r = client.post(f"/api/v1/jobs/{job_id}/confirmar")
        assert r.status_code == 409

    def test_corrigir_todos_os_modulos_de_baixa_confianca_libera_confirmacao(self, client, caminho_pdf_banheiro):
        job_id = _fazer_upload(client, caminho_pdf_banheiro).json()["job_id"]
        modulos = [m for amb in client.get(f"/api/v1/jobs/{job_id}").json()["ambientes"] for m in amb["modulos"]]

        for m in modulos:
            if m["confianca"] < 0.7:
                r = client.patch(f"/api/v1/jobs/{job_id}/modulos/{m['id']}", json={"largura_mm": 890, "confianca": 1.0})
                assert r.status_code == 200
                assert r.json()["origem"] == "confirmado_humano"

        r = client.post(f"/api/v1/jobs/{job_id}/confirmar")
        assert r.status_code == 200
        assert r.json()["status"] == "confirmado"

    def test_adicionar_modulo_manual(self, client, caminho_pdf_banheiro):
        job_id = _fazer_upload(client, caminho_pdf_banheiro).json()["job_id"]
        r = client.post(f"/api/v1/jobs/{job_id}/modulos", params={"nome_ambiente": "Banheiro"}, json={
            "id": "mod_manual_01", "nome": "Prateleira adicional", "ambiente": "Banheiro",
            "largura_mm": 600, "altura_mm": 300, "profundidade_mm": 250,
            "quantidade_portas": 0, "quantidade_gavetas": 0, "material_sugerido": "MDF Branco",
            "material_explicito_no_desenho": False, "confianca": 1.0, "bounding_boxes": [],
            "origem": "adicionado_manual", "observacoes": "",
        })
        assert r.status_code == 201


class TestFeedbackERegras:
    def test_ciclo_completo_de_feedback(self, client):
        with patch("api.services.feedback_service.Anthropic") as MockAnthropic:
            bloco = MagicMock(); bloco.type = "text"
            bloco.text = "Quando um modulo tiver porta com vidro reflecta, defina a cor do fundo igual a cor da caixa."
            MockAnthropic.return_value.messages.create.return_value = MagicMock(content=[bloco])
            r = client.post("/api/v1/usuarios/u_teste/feedback", json={
                "usuario_id": "u_teste",
                "instrucao": "Sempre que houver porta de vidro reflecta, mude o fundo para a cor da caixa",
            })
        assert r.status_code == 201
        regra_id = r.json()["regra"]["id"]

        r2 = client.get("/api/v1/usuarios/u_teste/regras")
        assert len(r2.json()) == 1

        r3 = client.delete(f"/api/v1/usuarios/u_teste/regras/{regra_id}")
        assert r3.status_code == 200


class TestOrcamento:
    def test_orcamento_sem_fator_de_area_nao_inventa_custo(self, client, caminho_pdf_banheiro):
        job_id = _fazer_upload(client, caminho_pdf_banheiro).json()["job_id"]
        modulos = [m for amb in client.get(f"/api/v1/jobs/{job_id}").json()["ambientes"] for m in amb["modulos"]]
        for m in modulos:
            if m["confianca"] < 0.7:
                client.patch(f"/api/v1/jobs/{job_id}/modulos/{m['id']}", json={"largura_mm": 890, "confianca": 1.0})
        client.post(f"/api/v1/jobs/{job_id}/confirmar")

        r = client.post("/api/v1/orcamentos", json={
            "job_id": job_id, "faturamento_acumulado": 100_000,
            "custo_hora_mao_de_obra": 30, "horas_estimadas": 5,
        })
        assert r.status_code == 200
        assert r.json()["custo_material_total"] == 0.0
        assert r.json()["custo_mao_de_obra"] == 150.0

    def test_orcamento_job_inexistente_da_404(self, client):
        r = client.post("/api/v1/orcamentos", json={"job_id": "job_nao_existe", "faturamento_acumulado": 100_000})
        assert r.status_code == 404
