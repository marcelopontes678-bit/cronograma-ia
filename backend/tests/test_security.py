"""Testes de segurança — cada teste prova uma correção da auditoria."""
import uuid

from tests.conftest import SENHA, auth, fazer_login


# ── Autenticação ─────────────────────────────────────────────────────────────

def test_login_ok(client):
    body = fazer_login(client, "admin@a.com")
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_senha_errada(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@a.com", "password": "senha-errada1"},
    )
    assert r.status_code == 401


def test_login_email_inexistente_mesma_resposta(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "naoexiste@x.com", "password": "qualquer123"},
    )
    # Mesma mensagem genérica — não revela se o e-mail existe
    assert r.status_code == 401
    assert r.json()["detail"] == "Credenciais inválidas"


def test_rate_limit_login(client):
    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            json={"email": "admin@a.com", "password": "errada123"},
        )
    r = client.post(
        "/api/v1/auth/login", json={"email": "admin@a.com", "password": SENHA}
    )
    assert r.status_code == 429


def test_rota_protegida_sem_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/projetos").status_code == 401


# ── Rotação e reuso de refresh token ─────────────────────────────────────────

def test_refresh_rotaciona_e_detecta_reuso(client):
    tokens = fazer_login(client, "operador@a.com")
    antigo = tokens["refresh_token"]

    # 1º uso: rotaciona normalmente
    r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": antigo})
    assert r1.status_code == 200
    novo = r1.json()["refresh_token"]
    assert novo != antigo

    # Reuso do token antigo (revogado) = roubo → 401 e revoga TODAS as sessões
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": antigo})
    assert r2.status_code == 401

    # O token novo também deve ter sido revogado em massa
    r3 = client.post("/api/v1/auth/refresh", json={"refresh_token": novo})
    assert r3.status_code == 401


# ── Isolamento multi-tenant ──────────────────────────────────────────────────

def test_gerente_nao_cria_projeto_em_outra_empresa(client, dados, token_gerente_a):
    r = client.post(
        "/api/v1/projetos",
        headers=auth(token_gerente_a),
        json={
            "empresa_id": dados["empresa_b"],
            "codigo": "HACK-001",
            "nome": "Projeto invasor",
        },
    )
    assert r.status_code == 403


def test_gerente_cria_projeto_na_propria_empresa(client, dados, token_gerente_a):
    r = client.post(
        "/api/v1/projetos",
        headers=auth(token_gerente_a),
        json={
            "empresa_id": dados["empresa_a"],
            "codigo": "OP-001",
            "nome": "Projeto legítimo",
        },
    )
    assert r.status_code == 201


def test_gerente_nao_cria_unidade_em_outra_empresa(client, dados, token_gerente_a):
    r = client.post(
        f"/api/v1/empresas/{dados['empresa_b']}/unidades",
        headers=auth(token_gerente_a),
        json={"nome": "Unidade invasora", "tipo": "fabrica"},
    )
    assert r.status_code == 403


def test_gerente_nao_lista_unidades_de_outra_empresa(client, dados, token_gerente_a):
    r = client.get(
        f"/api/v1/empresas/{dados['empresa_b']}/unidades",
        headers=auth(token_gerente_a),
    )
    assert r.status_code == 403


def test_gerente_nao_ve_outra_empresa(client, dados, token_gerente_a):
    r = client.get(
        f"/api/v1/empresas/{dados['empresa_b']}", headers=auth(token_gerente_a)
    )
    assert r.status_code == 403


# ── Controle de acesso a usuários ────────────────────────────────────────────

def test_operador_nao_edita_outro_usuario(client, dados, token_operador_a):
    alvo = dados["ids"]["gerente_a"]
    r = client.put(
        f"/api/v1/usuarios/{alvo}",
        headers=auth(token_operador_a),
        json={"nome": "Nome hackeado"},
    )
    assert r.status_code == 403


def test_usuario_edita_o_proprio_perfil(client, dados, token_operador_a):
    proprio = dados["ids"]["operador_a"]
    r = client.put(
        f"/api/v1/usuarios/{proprio}",
        headers=auth(token_operador_a),
        json={"telefone": "(11) 98888-7777"},
    )
    assert r.status_code == 200
    assert r.json()["telefone"] == "(11) 98888-7777"


def test_usuario_nao_muda_o_proprio_role(client, dados, token_operador_a):
    proprio = dados["ids"]["operador_a"]
    r = client.put(
        f"/api/v1/usuarios/{proprio}",
        headers=auth(token_operador_a),
        json={"role": "admin"},
    )
    assert r.status_code == 403


def test_operador_nao_le_perfil_de_colega(client, dados, token_operador_a):
    alvo = dados["ids"]["gerente_a"]
    r = client.get(f"/api/v1/usuarios/{alvo}", headers=auth(token_operador_a))
    assert r.status_code == 403


def test_operador_nao_lista_usuarios(client, token_operador_a):
    r = client.get("/api/v1/usuarios", headers=auth(token_operador_a))
    assert r.status_code == 403


def test_operador_nao_cria_usuario(client, dados, token_operador_a):
    r = client.post(
        "/api/v1/usuarios",
        headers=auth(token_operador_a),
        json={
            "nome": "Invasor", "email": "invasor@x.com", "role": "admin",
            "empresa_id": dados["empresa_a"], "password": "Senha123!",
        },
    )
    assert r.status_code == 403


# ── Política de senha ────────────────────────────────────────────────────────

def test_senha_curta_rejeitada(client, dados, token_admin):
    r = client.post(
        "/api/v1/usuarios",
        headers=auth(token_admin),
        json={
            "nome": "X", "email": "curta@x.com", "role": "operador",
            "empresa_id": dados["empresa_a"], "password": "abc1",
        },
    )
    assert r.status_code == 422


def test_senha_sem_numeros_rejeitada(client, dados, token_admin):
    r = client.post(
        "/api/v1/usuarios",
        headers=auth(token_admin),
        json={
            "nome": "X", "email": "semnum@x.com", "role": "operador",
            "empresa_id": dados["empresa_a"], "password": "somenteletras",
        },
    )
    assert r.status_code == 422


def test_senha_gigante_rejeitada_sem_erro_500(client, dados, token_admin):
    r = client.post(
        "/api/v1/usuarios",
        headers=auth(token_admin),
        json={
            "nome": "X", "email": "longa@x.com", "role": "operador",
            "empresa_id": dados["empresa_a"], "password": "a1" + "x" * 200,
        },
    )
    assert r.status_code == 422


# ── Limites e headers ────────────────────────────────────────────────────────

def test_limit_maximo_100(client, token_admin):
    r = client.get("/api/v1/projetos?limit=10000", headers=auth(token_admin))
    assert r.status_code == 422


def test_security_headers_presentes(client):
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"


def test_uuid_invalido_retorna_422(client, token_admin):
    r = client.get("/api/v1/projetos/nao-e-uuid", headers=auth(token_admin))
    assert r.status_code == 422
