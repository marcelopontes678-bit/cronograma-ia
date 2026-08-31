from tabela_precos import (
    PrecoReferencia,
    calcular_custo_item_ferragem,
    carregar_tabela_precos,
    chave_acabamento,
    indexar_precos_por_acabamento,
)


class TestChaveAcabamento:
    def test_padrao_promob_com_mdf(self):
        assert chave_acabamento("2.2008.18.Duratex.Essencial.Rosa Infinito.MDF") == (18, "Duratex.Essencial.Rosa Infinito")

    def test_padrao_promob_sem_sufixo_material(self):
        assert chave_acabamento("2.0835.18.Duratex.Essencial.Rosa Infinito") == (18, "Duratex.Essencial.Rosa Infinito")

    def test_duas_referencias_de_peca_diferente_mesmo_acabamento_dao_mesma_chave(self):
        # Base Linear e Lateral sao pecas diferentes, mas saem da mesma chapa
        assert chave_acabamento("2.2008.18.Branco.MDF") == chave_acabamento("2.2033.18.Branco.MDF")

    def test_codigo_de_ferragem_nao_bate_no_padrao(self):
        assert chave_acabamento("1.1086.000") is None

    def test_texto_livre_sem_padrao_numerico(self):
        assert chave_acabamento("MDF Cinza Cobalto Berneck") is None


class TestIndexarPrecosPorAcabamento:
    def test_agrupa_referencias_promob_pela_mesma_chave(self):
        tabela = {
            "2.2008.18.Branco.MDF": PrecoReferencia(
                reference="2.2008.18.Branco.MDF", codigo_interno="", descricao="", categoria="",
                espessura_mm=18, unidade="M2", preco_unitario_un=None,
                preco_chapa_fechada=300.0, preco_fita_metro=20.0, fornecedor="",
            ),
        }
        indice = indexar_precos_por_acabamento(tabela)
        assert indice[(18, "Branco")].preco_chapa_fechada == 300.0
        # uma referencia de peca DIFERENTE do mesmo acabamento deve achar o mesmo preco
        assert chave_acabamento("2.2033.18.Branco.MDF") in indice

    def test_fallback_para_referencia_em_texto_livre_nao_e_descartado(self):
        # Regressao: indexar_precos_por_acabamento costumava descartar (via
        # 'continue') qualquer linha cujo REFERENCE nao seguisse o padrao
        # Promob -- isso quebrava silenciosamente qualquer tabela de precos
        # usada pelo pipeline de extracao via Vision (nomes de material em
        # texto livre, sem o codigo numerico do Promob).
        tabela = {
            "MDF Cinza Cobalto Berneck": PrecoReferencia(
                reference="MDF Cinza Cobalto Berneck", codigo_interno="", descricao="", categoria="",
                espessura_mm=None, unidade="M2", preco_unitario_un=None,
                preco_chapa_fechada=450.0, preco_fita_metro=28.0, fornecedor="",
            ),
        }
        indice = indexar_precos_por_acabamento(tabela)
        assert len(indice) == 1
        chave = (0, "MDF Cinza Cobalto Berneck")
        assert chave in indice
        assert indice[chave].preco_chapa_fechada == 450.0

    def test_prefere_entrada_com_preco_de_chapa_preenchido(self):
        tabela = {
            "a": PrecoReferencia("2.9999.18.Teste.MDF", "", "", "", 18, "M2", None, None, None, ""),
            "b": PrecoReferencia("2.8888.18.Teste.MDF", "", "", "", 18, "M2", None, 500.0, 30.0, ""),
        }
        indice = indexar_precos_por_acabamento(tabela)
        assert indice[(18, "Teste")].preco_chapa_fechada == 500.0


class TestCarregarTabelaPrecosReal:
    def test_carrega_tabela_real_do_projeto(self, caminho_tabela_precos_real):
        tabela = carregar_tabela_precos(caminho_tabela_precos_real)
        assert len(tabela) > 0
        # a referencia usada nos testes manuais desta sessao deve estar la
        assert "2.0835.18.Duratex.Essencial.Rosa Infinito" in tabela
        entrada = tabela["2.0835.18.Duratex.Essencial.Rosa Infinito"]
        assert entrada.unidade == "M2"
        assert entrada.preco_chapa_fechada is not None


class TestCalcularCustoItemFerragem:
    def test_item_com_preco_ok(self):
        tabela = {
            "1.1086.000": PrecoReferencia("1.1086.000", "", "", "", None, "UN", 3.5, None, None, ""),
        }
        custo, status = calcular_custo_item_ferragem({"reference": "1.1086.000", "repeticao": 4}, tabela)
        assert status == "OK"
        assert custo == 14.0

    def test_item_sem_preco_fica_pendente(self):
        custo, status = calcular_custo_item_ferragem({"reference": "inexistente", "repeticao": 1}, {})
        assert status == "SEM_PRECO_NA_TABELA"
        assert custo is None

    def test_item_marcado_incluido_na_chapa_tem_custo_zero_explicito(self):
        tabela = {
            "x": PrecoReferencia("x", "", "", "", None, "UN", None, None, None, "", observacoes="entra na chapa de mdf"),
        }
        custo, status = calcular_custo_item_ferragem({"reference": "x", "repeticao": 3}, tabela)
        assert status == "OK_INCLUIDO_NA_CHAPA"
        assert custo == 0.0
