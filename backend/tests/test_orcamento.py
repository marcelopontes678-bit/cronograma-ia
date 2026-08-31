from httpx import AsyncClient

from tests.conftest import obter_token


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
    async def test_criar_e_consultar_job(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/v1/orcamentos/jobs", json={"arquivo_origem": "banheiro.pdf"}, headers=headers
        )
        assert resp.status_code == 201
        job = resp.json()
        assert job["status"] == "processando"
        assert job["arquivo_origem"] == "banheiro.pdf"

        resp2 = await client.get(f"/api/v1/orcamentos/jobs/{job['id']}", headers=headers)
        assert resp2.status_code == 200
        assert resp2.json()["id"] == job["id"]

        resp3 = await client.get("/api/v1/orcamentos/jobs", headers=headers)
        assert resp3.status_code == 200
        assert any(j["id"] == job["id"] for j in resp3.json())

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

        job = (
            await client.post(
                "/api/v1/orcamentos/jobs",
                json={"arquivo_origem": "cozinha.pdf"},
                headers={"Authorization": f"Bearer {token_a}"},
            )
        ).json()

        resp = await client.get(
            f"/api/v1/orcamentos/jobs/{job['id']}", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert resp.status_code == 404

        resp_lista = await client.get(
            "/api/v1/orcamentos/jobs", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert all(j["id"] != job["id"] for j in resp_lista.json())
