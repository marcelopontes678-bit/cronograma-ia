"""Testes do Sprint 2 — engenharia manual (ambientes, módulos, peças, materiais)."""
from tests.conftest import auth, fazer_login


def _token(client, email):
    return fazer_login(client, email)["access_token"]


def _criar_projeto(client, token, empresa_id, codigo):
    r = client.post(
        "/api/v1/projetos",
        headers=auth(token),
        json={"empresa_id": empresa_id, "codigo": codigo, "nome": f"Projeto {codigo}"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ── Materiais ────────────────────────────────────────────────────────────────

def test_gerente_cria_material(client, token_gerente_a):
    r = client.post(
        "/api/v1/materiais",
        headers=auth(token_gerente_a),
        json={
            "nome": "MDF Branco TX 18mm", "codigo": "MDF-18-BR", "tipo": "chapa",
            "espessura_mm": 18, "largura_mm": 1850, "comprimento_mm": 2750,
            "unidade_medida": "un", "preco_unitario": "289.90",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["nome"] == "MDF Branco TX 18mm"


def test_operador_nao_cria_material(client, token_operador_a):
    r = client.post(
        "/api/v1/materiais",
        headers=auth(token_operador_a),
        json={"nome": "Material Invasor", "tipo": "chapa"},
    )
    assert r.status_code == 403


def test_materiais_isolados_por_empresa(client, dados, token_gerente_a):
    # Gerente B cria material na empresa B
    token_b = _token(client, "gerente@b.com")
    r = client.post(
        "/api/v1/materiais",
        headers=auth(token_b),
        json={"nome": "MDF Secreto Empresa B", "tipo": "chapa"},
    )
    assert r.status_code == 201
    material_b = r.json()["id"]

    # Gerente A não vê o material da empresa B na listagem
    lista = client.get("/api/v1/materiais", headers=auth(token_gerente_a)).json()
    assert all(m["id"] != material_b for m in lista)

    # Nem consegue acessar diretamente por ID
    r = client.get(f"/api/v1/materiais/{material_b}", headers=auth(token_gerente_a))
    assert r.status_code == 403


# ── Árvore de engenharia ─────────────────────────────────────────────────────

def test_fluxo_completo_engenharia(client, dados, token_gerente_a):
    projeto_id = _criar_projeto(client, token_gerente_a, dados["empresa_a"], "ENG-001")

    # Material para as peças
    material = client.post(
        "/api/v1/materiais",
        headers=auth(token_gerente_a),
        json={"nome": "MDF Carvalho 15mm", "codigo": "MDF-15-CV", "tipo": "chapa",
              "espessura_mm": 15},
    ).json()

    # Ambiente
    amb = client.post(
        f"/api/v1/projetos/{projeto_id}/ambientes",
        headers=auth(token_gerente_a),
        json={"nome": "Cozinha", "ordem": 1},
    )
    assert amb.status_code == 201, amb.text
    ambiente_id = amb.json()["id"]

    # Módulo (2 unidades do mesmo armário)
    mod = client.post(
        f"/api/v1/ambientes/{ambiente_id}/modulos",
        headers=auth(token_gerente_a),
        json={"nome": "Armário superior 800mm", "largura_mm": 800,
              "altura_mm": 700, "profundidade_mm": 350, "quantidade": 2},
    )
    assert mod.status_code == 201, mod.text
    modulo_id = mod.json()["id"]

    # Peça: 2 laterais de 700x350, fita nos 2 comprimentos
    peca = client.post(
        f"/api/v1/modulos/{modulo_id}/pecas",
        headers=auth(token_gerente_a),
        json={"nome": "Lateral", "material_id": material["id"],
              "comprimento_mm": 700, "largura_mm": 350, "quantidade": 2,
              "fita_c1": True, "fita_c2": True},
    )
    assert peca.status_code == 201, peca.text

    # Resumo: 2 módulos × 2 peças = 4 peças
    resumo = client.get(
        f"/api/v1/projetos/{projeto_id}/engenharia", headers=auth(token_gerente_a)
    ).json()
    assert resumo["total_ambientes"] == 1
    assert resumo["total_modulos"] == 1
    assert resumo["total_pecas"] == 4
    m = resumo["materiais"][0]
    assert m["material_nome"] == "MDF Carvalho 15mm"
    # Área: 0,7m × 0,35m × 4 peças = 0,98 m²
    assert abs(m["area_m2"] - 0.98) < 0.001
    # Fita: 2 lados de 0,7m × 4 peças = 5,6 m
    assert abs(m["fita_borda_m"] - 5.6) < 0.01

    # Árvore completa retorna aninhada
    tree = client.get(
        f"/api/v1/projetos/{projeto_id}/ambientes", headers=auth(token_gerente_a)
    ).json()
    assert tree[0]["modulos"][0]["pecas"][0]["nome"] == "Lateral"


def test_gerente_nao_cria_ambiente_em_projeto_de_outra_empresa(client, dados):
    token_b = _token(client, "gerente@b.com")
    projeto_b = _criar_projeto(client, token_b, dados["empresa_b"], "ENG-B01")

    token_a = _token(client, "gerente@a.com")
    r = client.post(
        f"/api/v1/projetos/{projeto_b}/ambientes",
        headers=auth(token_a),
        json={"nome": "Ambiente invasor"},
    )
    assert r.status_code == 403


def test_gerente_nao_ve_engenharia_de_outra_empresa(client, dados):
    token_b = _token(client, "gerente@b.com")
    projeto_b = _criar_projeto(client, token_b, dados["empresa_b"], "ENG-B02")

    token_a = _token(client, "gerente@a.com")
    r = client.get(
        f"/api/v1/projetos/{projeto_b}/engenharia", headers=auth(token_a)
    )
    assert r.status_code == 403


def test_peca_nao_referencia_material_de_outra_empresa(client, dados):
    # Empresa B cria material
    token_b = _token(client, "gerente@b.com")
    material_b = client.post(
        "/api/v1/materiais",
        headers=auth(token_b),
        json={"nome": "MDF da B", "tipo": "chapa"},
    ).json()["id"]

    # Empresa A monta árvore e tenta usar material da B
    token_a = _token(client, "gerente@a.com")
    projeto_a = _criar_projeto(client, token_a, dados["empresa_a"], "ENG-002")
    ambiente = client.post(
        f"/api/v1/projetos/{projeto_a}/ambientes",
        headers=auth(token_a), json={"nome": "Sala"},
    ).json()["id"]
    modulo = client.post(
        f"/api/v1/ambientes/{ambiente}/modulos",
        headers=auth(token_a), json={"nome": "Painel TV"},
    ).json()["id"]

    r = client.post(
        f"/api/v1/modulos/{modulo}/pecas",
        headers=auth(token_a),
        json={"nome": "Peça X", "material_id": material_b,
              "comprimento_mm": 500, "largura_mm": 300},
    )
    assert r.status_code == 403


def test_operador_nao_edita_engenharia(client, dados, token_gerente_a, token_operador_a):
    projeto_id = _criar_projeto(client, token_gerente_a, dados["empresa_a"], "ENG-003")
    r = client.post(
        f"/api/v1/projetos/{projeto_id}/ambientes",
        headers=auth(token_operador_a),
        json={"nome": "Ambiente do operador"},
    )
    assert r.status_code == 403

    # Mas pode LER a engenharia
    r = client.get(
        f"/api/v1/projetos/{projeto_id}/engenharia", headers=auth(token_operador_a)
    )
    assert r.status_code == 200


def test_dimensoes_invalidas_rejeitadas(client, dados, token_gerente_a):
    projeto_id = _criar_projeto(client, token_gerente_a, dados["empresa_a"], "ENG-004")
    ambiente = client.post(
        f"/api/v1/projetos/{projeto_id}/ambientes",
        headers=auth(token_gerente_a), json={"nome": "Teste"},
    ).json()["id"]
    modulo = client.post(
        f"/api/v1/ambientes/{ambiente}/modulos",
        headers=auth(token_gerente_a), json={"nome": "Mod"},
    ).json()["id"]

    r = client.post(
        f"/api/v1/modulos/{modulo}/pecas",
        headers=auth(token_gerente_a),
        json={"nome": "Peça inválida", "comprimento_mm": 0, "largura_mm": -5},
    )
    assert r.status_code == 422
