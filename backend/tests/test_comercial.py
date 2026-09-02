from httpx import AsyncClient

from tests.conftest import obter_token


class TestClientes:
    async def test_criar_e_listar_cliente(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/v1/comercial/clientes",
            headers=headers,
            json={
                "nome": "João Silva",
                "email": "joao@example.com",
                "telefone": "11999990000",
                "origem": "indicacao",
                "status": "lead",
                "data_entrada": "2026-09-01",
                "data_ultima_atualizacao": "2026-09-01",
            },
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["nome"] == "João Silva"

        resp_lista = await client.get("/api/v1/comercial/clientes", headers=headers)
        assert resp_lista.status_code == 200
        assert len(resp_lista.json()) == 1

    async def test_isolamento_multi_tenant_clientes(self, client: AsyncClient, empresa_a, empresa_b):
        token_a = await obter_token(client, "admin@a.com", "senhaA123!")
        token_b = await obter_token(client, "admin@b.com", "senhaB123!")

        await client.post(
            "/api/v1/comercial/clientes",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "nome": "Cliente A",
                "email": "clientea@example.com",
                "telefone": "11900000000",
                "data_entrada": "2026-09-01",
                "data_ultima_atualizacao": "2026-09-01",
            },
        )
        resp_b = await client.get(
            "/api/v1/comercial/clientes", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert resp_b.json() == []

    async def test_atualizar_cliente_de_outra_empresa_da_404(
        self, client: AsyncClient, empresa_a, empresa_b
    ):
        token_a = await obter_token(client, "admin@a.com", "senhaA123!")
        token_b = await obter_token(client, "admin@b.com", "senhaB123!")

        resp_criar = await client.post(
            "/api/v1/comercial/clientes",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "nome": "Cliente A",
                "email": "clientea@example.com",
                "telefone": "11900000000",
                "data_entrada": "2026-09-01",
                "data_ultima_atualizacao": "2026-09-01",
            },
        )
        cliente_id = resp_criar.json()["id"]

        resp = await client.put(
            f"/api/v1/comercial/clientes/{cliente_id}",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"status": "contato"},
        )
        assert resp.status_code == 404


class TestOrcamentosComerciais:
    async def test_criar_orcamento_calcula_total_a_partir_de_subtotal_e_desconto(
        self, client: AsyncClient, empresa_a
    ):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/v1/comercial/orcamentos",
            headers=headers,
            json={
                "cliente_nome": "Maria Souza",
                "data_criacao": "2026-09-01",
                "data_validade": "2026-09-30",
                "itens": [],
                "subtotal": 1000.0,
                "desconto": 150.0,
                "margem_media": 35.0,
                "parcelas": [],
            },
        )
        assert resp.status_code == 201, resp.text
        corpo = resp.json()
        assert corpo["total"] == 850.0
        assert corpo["numero"].startswith("ORC-2026-")
        assert corpo["status"] == "rascunho"

    async def test_atualizar_status_orcamento(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        resp_criar = await client.post(
            "/api/v1/comercial/orcamentos",
            headers=headers,
            json={
                "cliente_nome": "Maria Souza",
                "data_criacao": "2026-09-01",
                "data_validade": "2026-09-30",
            },
        )
        orcamento_id = resp_criar.json()["id"]

        resp = await client.patch(
            f"/api/v1/comercial/orcamentos/{orcamento_id}/status",
            headers=headers,
            json={"status": "aprovado"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "aprovado"


class TestFichasTecnicas:
    async def test_criar_ficha_custo_total_e_derivado(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/v1/comercial/fichas",
            headers=headers,
            json={
                "nome": "Armário 2 portas",
                "categoria": "armario",
                "custo_materiais": 500.0,
                "custo_mao_obra": 200.0,
            },
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["custo_total"] == 700.0


class TestEstoque:
    async def test_registrar_movimentacao_atualiza_quantidade_atual(
        self, client: AsyncClient, empresa_a
    ):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        resp_item = await client.post(
            "/api/v1/comercial/estoque",
            headers=headers,
            json={
                "codigo": "MDF-15",
                "nome": "MDF Branco 15mm",
                "categoria": "madeira",
                "unidade": "chapa",
                "quantidade_atual": 10,
                "quantidade_minima": 5,
            },
        )
        item_id = resp_item.json()["id"]

        resp_entrada = await client.post(
            f"/api/v1/comercial/estoque/{item_id}/movimentacoes",
            headers=headers,
            json={"tipo": "entrada", "quantidade": 5, "referencia": "NF-001"},
        )
        assert resp_entrada.status_code == 201, resp_entrada.text

        resp_saida = await client.post(
            f"/api/v1/comercial/estoque/{item_id}/movimentacoes",
            headers=headers,
            json={"tipo": "saida", "quantidade": 3, "referencia": "OS-042"},
        )
        assert resp_saida.status_code == 201

        resp_lista = await client.get("/api/v1/comercial/estoque", headers=headers)
        item_atualizado = resp_lista.json()[0]
        assert float(item_atualizado["quantidade_atual"]) == 12.0  # 10 + 5 - 3
        assert len(item_atualizado["movimentacoes"]) == 2

    async def test_movimentacao_em_item_de_outra_empresa_da_404(
        self, client: AsyncClient, empresa_a, empresa_b
    ):
        token_a = await obter_token(client, "admin@a.com", "senhaA123!")
        token_b = await obter_token(client, "admin@b.com", "senhaB123!")

        resp_item = await client.post(
            "/api/v1/comercial/estoque",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"codigo": "X", "nome": "Item A", "categoria": "madeira", "unidade": "un"},
        )
        item_id = resp_item.json()["id"]

        resp = await client.post(
            f"/api/v1/comercial/estoque/{item_id}/movimentacoes",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"tipo": "entrada", "quantidade": 1},
        )
        assert resp.status_code == 404


class TestFinanceiro:
    async def test_listar_lancamentos_vazio_por_padrao(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        resp = await client.get(
            "/api/v1/comercial/lancamentos", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert resp.json() == []
