from httpx import AsyncClient

from tests.conftest import obter_token


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestIsolamentoEntreEmpresas:
    """ADMIN e admin da propria empresa, nunca da plataforma: nao enxerga
    nem altera empresa, usuario ou unidade de outra empresa."""

    async def test_admin_nao_acessa_outra_empresa(self, client: AsyncClient, db_session, empresa_a, empresa_b):
        empresa_a_obj, _ = empresa_a
        empresa_b_obj, _ = empresa_b
        # A fixture gera CNPJ so com digitos; a resposta de /empresas exige o formato com mascara.
        empresa_a_obj.cnpj = "12.345.678/0001-90"
        await db_session.commit()
        h = _auth(await obter_token(client, "admin@a.com", "senhaA123!"))

        assert (await client.get(f"/api/v1/empresas/{empresa_b_obj.id}", headers=h)).status_code == 403
        assert (
            await client.put(f"/api/v1/empresas/{empresa_b_obj.id}", headers=h, json={"nome": "Hackeada"})
        ).status_code == 403
        assert (await client.delete(f"/api/v1/empresas/{empresa_b_obj.id}", headers=h)).status_code == 403

        lista = (await client.get("/api/v1/empresas/", headers=h)).json()
        assert [e["nome"] for e in lista] == ["Marcenaria A"]

    async def test_admin_nao_acessa_usuario_de_outra_empresa(self, client: AsyncClient, empresa_a, empresa_b):
        _, admin_b = empresa_b
        h = _auth(await obter_token(client, "admin@a.com", "senhaA123!"))

        assert (await client.get(f"/api/v1/usuarios/{admin_b.id}", headers=h)).status_code == 403
        assert (
            await client.put(f"/api/v1/usuarios/{admin_b.id}", headers=h, json={"email": "x@a.com"})
        ).status_code == 403
        assert (await client.delete(f"/api/v1/usuarios/{admin_b.id}", headers=h)).status_code == 403

    async def test_nao_cria_unidade_em_outra_empresa(self, client: AsyncClient, empresa_a, empresa_b):
        empresa_b_obj, _ = empresa_b
        h = _auth(await obter_token(client, "admin@a.com", "senhaA123!"))

        resp = await client.post(
            f"/api/v1/empresas/{empresa_b_obj.id}/unidades/", headers=h, json={"nome": "Filial", "tipo": "fabrica"}
        )
        assert resp.status_code == 403

    async def test_nao_admin_so_edita_o_proprio_cadastro(self, client: AsyncClient, empresa_a):
        _, admin_a = empresa_a
        h_admin = _auth(await obter_token(client, "admin@a.com", "senhaA123!"))
        resp = await client.post(
            "/api/v1/usuarios/",
            headers=h_admin,
            json={"nome": "Vis", "email": "vis@a.com", "role": "visualizador", "password": "senhaVis123"},
        )
        assert resp.status_code == 201, resp.text
        vis_id = resp.json()["id"]

        h_vis = _auth(await obter_token(client, "vis@a.com", "senhaVis123"))
        assert (
            await client.put(f"/api/v1/usuarios/{admin_a.id}", headers=h_vis, json={"email": "roubado@a.com"})
        ).status_code == 403
        assert (
            await client.put(f"/api/v1/usuarios/{vis_id}", headers=h_vis, json={"nome": "Vis Novo"})
        ).status_code == 200
