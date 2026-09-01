from httpx import AsyncClient

from tests.conftest import obter_token


class TestLogin:
    async def test_login_com_credenciais_validas_retorna_jwt(self, client: AsyncClient, empresa_a):
        resp = await client.post("/api/v1/auth/login", json={"email": "admin@a.com", "password": "senhaA123!"})
        assert resp.status_code == 200
        corpo = resp.json()
        assert corpo["token_type"] == "bearer"
        assert corpo["access_token"]
        assert corpo["refresh_token"]

    async def test_login_com_senha_errada_e_rejeitado(self, client: AsyncClient, empresa_a):
        resp = await client.post("/api/v1/auth/login", json={"email": "admin@a.com", "password": "senha_errada"})
        assert resp.status_code in (400, 401)

    async def test_me_sem_token_e_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_com_token_valido_retorna_usuario(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "admin@a.com"
