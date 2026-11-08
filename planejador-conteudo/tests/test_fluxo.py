from datetime import datetime, timedelta, timezone

from conftest import MARCA, cadastrar

from pauta.modelos import Plano


def _criar_marca(cliente, cab):
    r = cliente.post("/api/marcas", json=MARCA, headers=cab)
    assert r.status_code == 201, r.text
    return r.json()


def test_crud_de_marca(cliente):
    cab = cadastrar(cliente)
    marca = _criar_marca(cliente, cab)
    assert marca["pilares"] == ["Treinos rápidos", "Alimentação", "Bastidores"]

    r = cliente.patch(f"/api/marcas/{marca['id']}", json={"tom_de_voz": "divertido"}, headers=cab)
    assert r.json()["tom_de_voz"] == "divertido" and r.json()["nicho"] == MARCA["nicho"]
    assert len(cliente.get("/api/marcas", headers=cab).json()) == 1

    assert cliente.delete(f"/api/marcas/{marca['id']}", headers=cab).status_code == 204
    assert cliente.get(f"/api/marcas/{marca['id']}", headers=cab).status_code == 404


def test_plataforma_invalida(cliente):
    cab = cadastrar(cliente)
    r = cliente.post("/api/marcas", json={**MARCA, "plataformas": ["orkut"]}, headers=cab)
    assert r.status_code == 422


def test_gerar_plano_editar_e_exportar(cliente, gerador):
    cab = cadastrar(cliente)
    marca = _criar_marca(cliente, cab)

    r = cliente.post(
        f"/api/marcas/{marca['id']}/planos",
        json={"data_inicio": "2026-11-09", "semanas": 2, "posts_por_semana": 3, "foco": "Black Friday"},
        headers=cab,
    )
    assert r.status_code == 202, r.text
    plano_id = r.json()["id"]

    plano = cliente.get(f"/api/planos/{plano_id}", headers=cab).json()
    assert plano["status"] == "pronto", plano
    assert plano["estrategia"] == "Estratégia de teste."
    assert plano["plataformas"] == ["instagram", "tiktok"]  # herdou da marca
    # 6 pedidos + 1 fora do período (mantido, com data ajustada) − 1 em plataforma não pedida
    posts = plano["posts"]
    assert len(posts) == 7
    assert {p["plataforma"] for p in posts} <= {"instagram", "tiktok"}
    assert all("2026-11-09" <= p["data"] <= "2026-11-22" for p in posts)
    assert posts[0]["hashtags"] == ["ia", "conteudo"]

    post_id = posts[0]["id"]
    r = cliente.patch(f"/api/posts/{post_id}", json={"status": "aprovado", "hashtags": ["#novo"]}, headers=cab)
    assert r.json()["status"] == "aprovado" and r.json()["hashtags"] == ["novo"]

    r = cliente.post(f"/api/posts/{post_id}/reescrever", json={"instrucao": "mais polêmico"}, headers=cab)
    assert r.status_code == 200 and r.json()["titulo"] == "Reescrito" and r.json()["status"] == "rascunho"

    filtrados = cliente.get(
        f"/api/marcas/{marca['id']}/posts", params={"de": "2026-11-09", "ate": "2026-11-12", "plataforma": "instagram"},
        headers=cab,
    ).json()
    assert filtrados and all(p["plataforma"] == "instagram" and p["data"] <= "2026-11-12" for p in filtrados)

    csv = cliente.get(f"/api/planos/{plano_id}/csv", headers=cab)
    assert csv.status_code == 200 and "Reescrito" in csv.text and csv.text.startswith("﻿data,")

    assert cliente.delete(f"/api/posts/{post_id}", headers=cab).status_code == 204
    assert len(cliente.get(f"/api/planos/{plano_id}", headers=cab).json()["posts"]) == 6

    eu = cliente.get("/api/auth/eu", headers=cab).json()
    assert eu["planos_usados_mes"] == 1


def test_erro_da_ia_marca_plano_e_nao_conta_no_limite(cliente, gerador):
    cab = cadastrar(cliente)
    marca = _criar_marca(cliente, cab)
    gerador.falhar = True
    r = cliente.post(f"/api/marcas/{marca['id']}/planos", json={"data_inicio": "2026-11-09"}, headers=cab)
    plano = cliente.get(f"/api/planos/{r.json()['id']}", headers=cab).json()
    assert plano["status"] == "erro" and "IA fora do ar" in plano["erro"]
    assert cliente.get("/api/auth/eu", headers=cab).json()["planos_usados_mes"] == 0


def test_limite_mensal(cliente):
    cab = cadastrar(cliente)
    marca = _criar_marca(cliente, cab)
    for _ in range(3):
        assert cliente.post(f"/api/marcas/{marca['id']}/planos", json={"data_inicio": "2026-11-09"}, headers=cab).status_code == 202
    r = cliente.post(f"/api/marcas/{marca['id']}/planos", json={"data_inicio": "2026-11-09"}, headers=cab)
    assert r.status_code == 429


def test_isolamento_entre_usuarios(cliente):
    cab_ana = cadastrar(cliente)
    marca = _criar_marca(cliente, cab_ana)
    plano_id = cliente.post(f"/api/marcas/{marca['id']}/planos", json={"data_inicio": "2026-11-09"}, headers=cab_ana).json()["id"]
    post_id = cliente.get(f"/api/planos/{plano_id}", headers=cab_ana).json()["posts"][0]["id"]

    cab_bia = cadastrar(cliente, "bia@exemplo.com")
    assert cliente.get("/api/marcas", headers=cab_bia).json() == []
    assert cliente.get(f"/api/marcas/{marca['id']}", headers=cab_bia).status_code == 404
    assert cliente.post(f"/api/marcas/{marca['id']}/planos", json={"data_inicio": "2026-11-09"}, headers=cab_bia).status_code == 404
    assert cliente.get(f"/api/planos/{plano_id}", headers=cab_bia).status_code == 404
    assert cliente.patch(f"/api/posts/{post_id}", json={"titulo": "hack"}, headers=cab_bia).status_code == 404
    assert cliente.delete(f"/api/posts/{post_id}", headers=cab_bia).status_code == 404


def test_plano_travado_vira_erro(cliente):
    cab = cadastrar(cliente)
    marca = _criar_marca(cliente, cab)
    plano_id = cliente.post(f"/api/marcas/{marca['id']}/planos", json={"data_inicio": "2026-11-09"}, headers=cab).json()["id"]
    with cliente.app.state.fabrica_sessao() as db:
        plano = db.get(Plano, plano_id)
        plano.status = "gerando"
        plano.criado_em = datetime.now(timezone.utc) - timedelta(minutes=30)
        db.commit()
    assert cliente.get(f"/api/planos/{plano_id}", headers=cab).json()["status"] == "erro"


def test_saude_e_pagina(cliente):
    assert cliente.get("/api/saude").json() == {"ok": True}
    r = cliente.get("/")
    assert r.status_code == 200 and "Pauta" in r.text
