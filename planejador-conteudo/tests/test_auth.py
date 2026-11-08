from conftest import cadastrar

from pauta.seguranca import conferir_senha, gerar_hash


def test_hash_de_senha():
    h = gerar_hash("minha-senha")
    assert conferir_senha("minha-senha", h)
    assert not conferir_senha("outra", h)
    assert not conferir_senha("x", "lixo")


def test_cadastro_login_e_eu(cliente):
    cab = cadastrar(cliente)
    eu = cliente.get("/api/auth/eu", headers=cab).json()
    assert eu["email"] == "ana@exemplo.com"
    assert eu["planos_usados_mes"] == 0 and eu["limite_planos_mes"] == 3

    r = cliente.post("/api/auth/login", json={"email": "ANA@exemplo.com", "senha": "senha-forte-123"})
    assert r.status_code == 200 and r.json()["token"]


def test_email_duplicado_e_senha_errada(cliente):
    cadastrar(cliente)
    r = cliente.post("/api/auth/cadastro", json={"nome": "X", "email": "ana@exemplo.com", "senha": "12345678"})
    assert r.status_code == 409
    assert cliente.post("/api/auth/login", json={"email": "ana@exemplo.com", "senha": "errada"}).status_code == 401
    assert cliente.post("/api/auth/login", json={"email": "nao@existe.com", "senha": "x"}).status_code == 401


def test_validacoes_de_cadastro(cliente):
    assert cliente.post("/api/auth/cadastro", json={"nome": "A", "email": "invalido", "senha": "12345678"}).status_code == 422
    assert cliente.post("/api/auth/cadastro", json={"nome": "A", "email": "a@b.com", "senha": "curta"}).status_code == 422


def test_rotas_exigem_login(cliente):
    assert cliente.get("/api/marcas").status_code == 401
    assert cliente.get("/api/marcas", headers={"Authorization": "Bearer token-falso"}).status_code == 401
