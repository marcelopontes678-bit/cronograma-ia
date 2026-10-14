from types import SimpleNamespace

from app.engine.calculo_projeto import calcular_projeto
from app.engine.casamento_material import OPCAO_NENHUM, resolver_acabamentos
from app.engine.tabela_precos import PrecoReferencia


def _preco(reference, chapa=300.0, fita=2.0, espessura=18):
    return PrecoReferencia(
        reference=reference, codigo_interno="", descricao="", categoria="MDF",
        espessura_mm=espessura, unidade="M2", preco_unitario_un=None,
        preco_chapa_fechada=chapa, preco_fita_metro=fita, fornecedor="",
    )


ROSA = "2.2008.18.Duratex.Essencial.Rosa Infinito.MDF"
GRAFITE = "2.2009.18.Duratex.Essencial.Grafite.MDF"
ROSA_15 = "2.2010.15.Duratex.Essencial.Rosa Infinito.MDF"
TABELA = {r: _preco(r, espessura=int(r.split(".")[2])) for r in (ROSA, GRAFITE, ROSA_15)}
TEXTO = "MDF Duratex Rosa Infinito 18mm"


def _projeto(referencia):
    item = {"unidade": "M2", "reference": referencia, "quantidade": 2.0, "repeticao": 1,
            "largura_mm": 1000, "altura_mm": 2000, "profundidade_mm": 500}
    return [{"nome": "Quarto", "modulos": [{"nome": "Quarto", "itens": [item]}]}]


class ClienteFake:
    """Imita TypeSafeClient.system_one devolvendo a escolha programada."""

    def __init__(self, escolha, confianca=0.95, prob=None, erro=None):
        self.escolha, self.confianca, self.erro = escolha, confianca, erro
        self.prob = confianca if prob is None else prob
        self.chamadas = []

    def system_one(self, *, state, questions):
        self.chamadas.append((state, questions))
        if self.erro:
            raise self.erro
        resp = SimpleNamespace(
            choice=self.escolha, confidence=self.confianca,
            probabilities={self.escolha: self.prob},
        )
        return SimpleNamespace(choices={"acabamento": resp})


def test_texto_livre_casa_e_passa_a_ter_preco():
    ambientes = _projeto(TEXTO)
    assert calcular_projeto(ambientes, TABELA).itens_sem_preco  # antes: pendente

    cliente = ClienteFake("18mm Duratex.Essencial.Rosa Infinito")
    casamento = resolver_acabamentos(ambientes, TABELA, cliente)
    assert casamento.aliases == {(0, TEXTO): (18, "Duratex.Essencial.Rosa Infinito")}

    resultado = calcular_projeto(ambientes, TABELA, aliases_acabamento=casamento.aliases)
    assert not resultado.itens_sem_preco
    assert resultado.chapas[0].preco_chapa == 300.0  # preco vem da tabela
    assert casamento.avisos()  # auditavel


def test_espessura_do_texto_filtra_candidatos():
    cliente = ClienteFake("NENHUM")
    resolver_acabamentos(_projeto(TEXTO), TABELA, cliente)
    criterios = cliente.chamadas[0][1]["acabamento"].criteria
    assert set(criterios) == {
        "18mm Duratex.Essencial.Rosa Infinito", "18mm Duratex.Essencial.Grafite", OPCAO_NENHUM,
    }


def test_nenhum_candidato_mantem_pendente():
    casamento = resolver_acabamentos(_projeto(TEXTO), TABELA, ClienteFake(OPCAO_NENHUM))
    assert not casamento.aliases


def test_baixa_confianca_nao_aplica_e_avisa():
    cliente = ClienteFake("18mm Duratex.Essencial.Grafite", confianca=0.4)
    casamento = resolver_acabamentos(_projeto(TEXTO), TABELA, cliente)
    assert not casamento.aliases
    assert "nao aceito" in casamento.avisos()[0]


def test_erro_do_servico_nao_derruba():
    casamento = resolver_acabamentos(_projeto(TEXTO), TABELA, ClienteFake("x", erro=RuntimeError("rede")))
    assert not casamento.aliases


def test_acabamento_ja_precificado_nao_chama_o_modelo():
    cliente = ClienteFake("NENHUM")
    resolver_acabamentos(_projeto(ROSA), TABELA, cliente)
    assert cliente.chamadas == []
