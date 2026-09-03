from httpx import AsyncClient

from tests.conftest import obter_token


async def _criar_projeto_producao(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(
        "/api/v1/producao/projetos",
        headers=headers,
        json={"nome": "Cozinha Planejada — Cliente Teste", "prioridade": 3},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestProjetosProducao:
    async def test_criar_e_listar_projeto(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        projeto_id = await _criar_projeto_producao(client, headers)

        resp_lista = await client.get("/api/v1/producao/projetos", headers=headers)
        assert resp_lista.status_code == 200
        assert len(resp_lista.json()) == 1
        assert resp_lista.json()[0]["id"] == projeto_id
        assert resp_lista.json()[0]["status_producao"] == "backlog"
        assert resp_lista.json()[0]["tarefas"] == []

    async def test_isolamento_multi_tenant_projetos(
        self, client: AsyncClient, empresa_a, empresa_b
    ):
        token_a = await obter_token(client, "admin@a.com", "senhaA123!")
        token_b = await obter_token(client, "admin@b.com", "senhaB123!")

        await _criar_projeto_producao(client, {"Authorization": f"Bearer {token_a}"})

        resp_b = await client.get(
            "/api/v1/producao/projetos", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert resp_b.json() == []

    async def test_projeto_sem_status_producao_nao_aparece_na_listagem(
        self, client: AsyncClient, empresa_a
    ):
        """Projetos comerciais criados via /projetos/ (fora do Kanban de
        producao) tem status_producao NULL por padrao -- nao devem
        poluir a listagem de producao."""
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        await client.post(
            "/api/v1/projetos/",
            headers=headers,
            json={"nome": "Projeto Comercial", "codigo": "PRJ-001"},
        )

        resp = await client.get("/api/v1/producao/projetos", headers=headers)
        assert resp.json() == []


class TestTarefasCronograma:
    async def test_criar_atualizar_e_listar_tarefa(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}
        projeto_id = await _criar_projeto_producao(client, headers)

        resp_criar = await client.post(
            f"/api/v1/producao/projetos/{projeto_id}/tarefas",
            headers=headers,
            json={
                "nome": "Corte MDF",
                "duracao_dias": 2,
                "data_inicio": "2026-09-10",
                "data_fim": "2026-09-11",
            },
        )
        assert resp_criar.status_code == 201, resp_criar.text
        tarefa_id = resp_criar.json()["id"]
        assert resp_criar.json()["status"] == "nao_iniciada"
        assert resp_criar.json()["historico"] == []

        resp_att = await client.put(
            f"/api/v1/producao/tarefas/{tarefa_id}",
            headers=headers,
            json={
                "status": "em_andamento",
                "percentual_concluido": 40,
                "novo_evento_historico": {
                    "id": "evt1",
                    "data": "2026-09-10T10:00:00",
                    "acao": "iniciada",
                    "usuario": "Admin",
                },
            },
        )
        assert resp_att.status_code == 200, resp_att.text
        assert resp_att.json()["status"] == "em_andamento"
        assert resp_att.json()["percentual_concluido"] == 40
        assert len(resp_att.json()["historico"]) == 1
        assert resp_att.json()["historico"][0]["acao"] == "iniciada"

        resp_lista = await client.get(
            f"/api/v1/producao/projetos/{projeto_id}/tarefas", headers=headers
        )
        assert len(resp_lista.json()) == 1

        resp_projetos = await client.get("/api/v1/producao/projetos", headers=headers)
        assert len(resp_projetos.json()[0]["tarefas"]) == 1

    async def test_deletar_tarefa(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}
        projeto_id = await _criar_projeto_producao(client, headers)

        resp_criar = await client.post(
            f"/api/v1/producao/projetos/{projeto_id}/tarefas",
            headers=headers,
            json={
                "nome": "Montagem",
                "data_inicio": "2026-09-10",
                "data_fim": "2026-09-10",
            },
        )
        tarefa_id = resp_criar.json()["id"]

        resp_del = await client.delete(f"/api/v1/producao/tarefas/{tarefa_id}", headers=headers)
        assert resp_del.status_code == 204

        resp_lista = await client.get(
            f"/api/v1/producao/projetos/{projeto_id}/tarefas", headers=headers
        )
        assert resp_lista.json() == []

    async def test_isolamento_multi_tenant_tarefas(
        self, client: AsyncClient, empresa_a, empresa_b
    ):
        token_a = await obter_token(client, "admin@a.com", "senhaA123!")
        token_b = await obter_token(client, "admin@b.com", "senhaB123!")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        projeto_id = await _criar_projeto_producao(client, headers_a)

        resp = await client.post(
            f"/api/v1/producao/projetos/{projeto_id}/tarefas",
            headers=headers_b,
            json={"nome": "Invasão", "data_inicio": "2026-09-10", "data_fim": "2026-09-10"},
        )
        assert resp.status_code == 404


class TestOperadores:
    async def test_listar_operadores_so_da_empresa(self, client: AsyncClient, empresa_a, empresa_b):
        token_a = await obter_token(client, "admin@a.com", "senhaA123!")
        headers_a = {"Authorization": f"Bearer {token_a}"}

        resp_criar = await client.post(
            "/api/v1/usuarios/",
            headers=headers_a,
            json={
                "nome": "João Operador",
                "email": "joao.op@a.com",
                "role": "operador",
                "password": "senhaSegura123!",
            },
        )
        assert resp_criar.status_code == 201, resp_criar.text

        resp = await client.get("/api/v1/producao/operadores", headers=headers_a)
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["nome"] == "João Operador"

        token_b = await obter_token(client, "admin@b.com", "senhaB123!")
        resp_b = await client.get(
            "/api/v1/producao/operadores", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert resp_b.json() == []

    async def test_atualizar_perfil_operador(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        resp_criar = await client.post(
            "/api/v1/usuarios/",
            headers=headers,
            json={
                "nome": "Maria Operadora",
                "email": "maria.op@a.com",
                "role": "operador",
                "password": "senhaSegura123!",
            },
        )
        usuario_id = resp_criar.json()["id"]

        resp = await client.put(
            f"/api/v1/producao/operadores/{usuario_id}",
            headers=headers,
            json={
                "especialidades": ["Corte", "Usinagem"],
                "cor": "#3b82f6",
                "capacidade_diaria": 8,
                "dias_trabalho": [1, 2, 3, 4, 5],
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["especialidades"] == ["Corte", "Usinagem"]
        assert resp.json()["capacidade_diaria"] == 8


class TestAusencias:
    async def test_criar_listar_e_deletar_ausencia(self, client: AsyncClient, empresa_a):
        token = await obter_token(client, "admin@a.com", "senhaA123!")
        headers = {"Authorization": f"Bearer {token}"}

        resp_op = await client.post(
            "/api/v1/usuarios/",
            headers=headers,
            json={
                "nome": "Pedro Operador",
                "email": "pedro.op@a.com",
                "role": "operador",
                "password": "senhaSegura123!",
            },
        )
        usuario_id = resp_op.json()["id"]

        resp = await client.post(
            "/api/v1/producao/ausencias",
            headers=headers,
            json={
                "usuario_id": usuario_id,
                "data_inicio": "2026-09-15",
                "data_fim": "2026-09-16",
                "motivo": "Atestado médico",
            },
        )
        assert resp.status_code == 201, resp.text
        ausencia_id = resp.json()["id"]

        resp_lista = await client.get("/api/v1/producao/ausencias", headers=headers)
        assert len(resp_lista.json()) == 1

        resp_del = await client.delete(
            f"/api/v1/producao/ausencias/{ausencia_id}", headers=headers
        )
        assert resp_del.status_code == 204

        resp_lista2 = await client.get("/api/v1/producao/ausencias", headers=headers)
        assert resp_lista2.json() == []
