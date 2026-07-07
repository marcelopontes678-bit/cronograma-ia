"""Testes do plano de corte — algoritmo puro e endpoint."""
from app.core.cutting import PecaCorte, empacotar
from tests.conftest import auth, fazer_login


# ── Algoritmo puro ───────────────────────────────────────────────────────────

def _sem_sobreposicao(chapa):
    """Nenhum par de peças pode se sobrepor."""
    ps = chapa.pecas
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            a, b = ps[i], ps[j]
            separados = (
                a.x_mm + a.comprimento_mm <= b.x_mm
                or b.x_mm + b.comprimento_mm <= a.x_mm
                or a.y_mm + a.largura_mm <= b.y_mm
                or b.y_mm + b.largura_mm <= a.y_mm
            )
            if not separados:
                return False
    return True


def _dentro_da_chapa(chapa, comp, larg):
    return all(
        p.x_mm >= 0 and p.y_mm >= 0
        and p.x_mm + p.comprimento_mm <= comp
        and p.y_mm + p.largura_mm <= larg
        for p in chapa.pecas
    )


def test_pecas_couberam_em_uma_chapa():
    pecas = [
        PecaCorte("1", "Lateral", 700, 350),
        PecaCorte("2", "Lateral", 700, 350),
        PecaCorte("3", "Porta", 696, 396),
        PecaCorte("4", "Porta", 696, 396),
    ]
    r = empacotar(pecas, 2750, 1850, kerf_mm=3)
    assert len(r.chapas) == 1
    assert len(r.chapas[0].pecas) == 4
    assert not r.nao_alocadas
    assert _sem_sobreposicao(r.chapas[0])
    assert _dentro_da_chapa(r.chapas[0], 2750, 1850)


def test_abre_segunda_chapa_quando_necessario():
    # 4 peças de meia chapa cada não cabem em uma só
    pecas = [PecaCorte(str(i), f"Painel {i}", 2700, 900) for i in range(4)]
    r = empacotar(pecas, 2750, 1850, kerf_mm=3)
    assert len(r.chapas) == 2
    assert sum(len(c.pecas) for c in r.chapas) == 4
    for c in r.chapas:
        assert _sem_sobreposicao(c)
        assert _dentro_da_chapa(c, 2750, 1850)


def test_peca_maior_que_chapa_e_reportada():
    pecas = [PecaCorte("1", "Gigante", 3000, 2000)]
    r = empacotar(pecas, 2750, 1850, kerf_mm=3)
    assert not r.chapas
    assert len(r.nao_alocadas) == 1


def test_veio_impede_rotacao():
    # Peça 500×1200 com veio: não pode virar; só encaixa "deitada" numa
    # chapa 1300×600 se rotacionar — logo deve falhar.
    pecas = [PecaCorte("1", "Painel ripado", 500, 1200, veio=True)]
    r = empacotar(pecas, 1300, 600, kerf_mm=3)
    assert not r.chapas
    assert len(r.nao_alocadas) == 1

    # Sem veio, rotaciona e cabe
    pecas = [PecaCorte("1", "Painel", 500, 1200, veio=False)]
    r = empacotar(pecas, 1300, 600, kerf_mm=3)
    assert len(r.chapas) == 1
    assert r.chapas[0].pecas[0].rotacionada is True


def test_peca_do_tamanho_exato_da_chapa_cabe():
    pecas = [PecaCorte("1", "Fundo inteiro", 2750, 1850)]
    r = empacotar(pecas, 2750, 1850, kerf_mm=3)
    assert len(r.chapas) == 1
    assert not r.nao_alocadas


def test_kerf_gera_folga_entre_pecas():
    # Duas peças lado a lado: a segunda deve começar depois do fim da
    # primeira + kerf (independente de rotação).
    pecas = [PecaCorte("1", "A", 1000, 500), PecaCorte("2", "B", 1000, 500)]
    r = empacotar(pecas, 2750, 1850, kerf_mm=10)
    chapa = r.chapas[0]
    na_mesma_linha = sorted(
        (p for p in chapa.pecas if p.y_mm == chapa.pecas[0].y_mm),
        key=lambda p: p.x_mm,
    )
    if len(na_mesma_linha) == 2:
        primeira, segunda = na_mesma_linha
        assert segunda.x_mm >= primeira.x_mm + primeira.comprimento_mm + 10


def test_aproveitamento_razoavel_em_lote_realista():
    # Cozinha típica: mix de laterais, portas, prateleiras e fundos
    pecas = []
    for i in range(6):
        pecas.append(PecaCorte(f"lat{i}", "Lateral", 700, 550))
    for i in range(8):
        pecas.append(PecaCorte(f"pra{i}", "Prateleira", 764, 500))
    for i in range(6):
        pecas.append(PecaCorte(f"por{i}", "Porta", 696, 396))
    r = empacotar(pecas, 2750, 1850, kerf_mm=3)
    assert not r.nao_alocadas
    area_total = sum(c.area_ocupada_mm2() for c in r.chapas)
    area_chapas = len(r.chapas) * 2750 * 1850
    # Heurística deve passar de 50% de aproveitamento nesse mix
    assert area_total / area_chapas > 0.5
    for c in r.chapas:
        assert _sem_sobreposicao(c)
        assert _dentro_da_chapa(c, 2750, 1850)


# ── Endpoint ─────────────────────────────────────────────────────────────────

def _montar_projeto_com_pecas(client, token, empresa_id, codigo):
    material = client.post(
        "/api/v1/materiais", headers=auth(token),
        json={"nome": f"MDF {codigo}", "tipo": "chapa", "espessura_mm": 18,
              "largura_mm": 1850, "comprimento_mm": 2750},
    ).json()["id"]
    projeto = client.post(
        "/api/v1/projetos", headers=auth(token),
        json={"empresa_id": empresa_id, "codigo": codigo, "nome": f"Proj {codigo}"},
    ).json()["id"]
    ambiente = client.post(
        f"/api/v1/projetos/{projeto}/ambientes", headers=auth(token),
        json={"nome": "Cozinha"},
    ).json()["id"]
    modulo = client.post(
        f"/api/v1/ambientes/{ambiente}/modulos", headers=auth(token),
        json={"nome": "Armário", "quantidade": 1},
    ).json()["id"]
    client.post(
        f"/api/v1/modulos/{modulo}/pecas", headers=auth(token),
        json={"nome": "Lateral", "material_id": material,
              "comprimento_mm": 700, "largura_mm": 350, "quantidade": 4},
    )
    return projeto


def test_endpoint_plano_corte(client, dados, token_gerente_a):
    projeto = _montar_projeto_com_pecas(
        client, token_gerente_a, dados["empresa_a"], "PC-001"
    )
    r = client.get(
        f"/api/v1/projetos/{projeto}/plano-corte?kerf_mm=4",
        headers=auth(token_gerente_a),
    )
    assert r.status_code == 200, r.text
    plano = r.json()
    assert plano["kerf_mm"] == 4
    assert plano["total_pecas_alocadas"] == 4
    assert plano["materiais"][0]["total_chapas"] == 1
    assert plano["materiais"][0]["chapas"][0]["aproveitamento_pct"] > 0


def test_plano_corte_isolado_por_empresa(client, dados, token_gerente_a):
    token_b = fazer_login(client, "gerente@b.com")["access_token"]
    projeto_b = _montar_projeto_com_pecas(
        client, token_b, dados["empresa_b"], "PC-B01"
    )
    r = client.get(
        f"/api/v1/projetos/{projeto_b}/plano-corte", headers=auth(token_gerente_a)
    )
    assert r.status_code == 403


def test_peca_sem_material_aparece_como_ignorada(client, dados, token_gerente_a):
    projeto = client.post(
        "/api/v1/projetos", headers=auth(token_gerente_a),
        json={"empresa_id": dados["empresa_a"], "codigo": "PC-002", "nome": "P2"},
    ).json()["id"]
    ambiente = client.post(
        f"/api/v1/projetos/{projeto}/ambientes", headers=auth(token_gerente_a),
        json={"nome": "Sala"},
    ).json()["id"]
    modulo = client.post(
        f"/api/v1/ambientes/{ambiente}/modulos", headers=auth(token_gerente_a),
        json={"nome": "Painel"},
    ).json()["id"]
    client.post(
        f"/api/v1/modulos/{modulo}/pecas", headers=auth(token_gerente_a),
        json={"nome": "Peça órfã", "comprimento_mm": 500, "largura_mm": 300},
    )
    plano = client.get(
        f"/api/v1/projetos/{projeto}/plano-corte", headers=auth(token_gerente_a)
    ).json()
    assert plano["total_pecas_alocadas"] == 0
    assert len(plano["pecas_ignoradas"]) == 1
    assert "sem material" in plano["pecas_ignoradas"][0]["motivo"].lower()
