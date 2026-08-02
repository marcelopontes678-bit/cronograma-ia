import pytest

from app.studyos import acp
from app.studyos.acp import (
    CAMPOS_OBRIGATORIOS,
    CONFIDENCE_DE_FALHA,
    CONFIDENCE_POR_CONFIABILIDADE,
    CONFIDENCE_SEM_DECLARACAO,
    MASTER_ORCHESTRATOR,
    MOTIVOS_DE_REEXECUCAO,
    VERSAO,
    Acao,
    ComunicacaoDireta,
    EntradaPadrao,
    Erro,
    Log,
    MemoriaCompartilhada,
    MemoriaLocal,
    Mensagem,
    MensagemInvalida,
    Prioridade,
    ReexecucaoNaoAutorizada,
    SaidaPadrao,
    Status,
    autorizar_reexecucao,
    confidence_de,
)
from app.studyos.agentes import IMPLEMENTACOES
from app.studyos.orchestrator import MasterOrchestrator

DADOS = {
    "objetivo": "Passar no concurso fiscal",
    "edital": {"Português": {"questoes": 20, "topicos": ["Crase", "Sintaxe"]}},
    "escolaridade": "Superior completo",
    "horas_por_dia": 2,
    "dias_por_semana": 5,
    "data_prova": "2027-01-01",
    "resultados_exercicios": [
        {
            "disciplina": "Português",
            "topico": "Crase",
            "acertos": 9,
            "total": 10,
            "data": "2026-07-01",
        }
    ],
}


def mensagem(**campos):
    base = {
        "workflow_id": "wf-teste",
        "source_agent": MASTER_ORCHESTRATOR,
        "target_agent": "01",
        "action": Acao.REQUEST,
    }
    return Mensagem(**{**base, **campos})


# --------------------------------------------------------------------------- #
# Envelope da mensagem
# --------------------------------------------------------------------------- #


def test_mensagem_traz_os_dez_campos_obrigatorios():
    corpo = mensagem().to_dict()

    assert set(CAMPOS_OBRIGATORIOS) <= set(corpo)
    assert len(CAMPOS_OBRIGATORIOS) == 10
    for campo in CAMPOS_OBRIGATORIOS:
        assert corpo[campo] is not None


def test_mensagem_declara_a_versao_do_protocolo():
    assert mensagem().to_dict()["metadata"]["protocolo"] == f"ACP v{VERSAO}"


def test_message_id_e_unico_por_mensagem():
    assert mensagem().message_id != mensagem().message_id


def test_workflow_id_vazio_e_recusado():
    with pytest.raises(MensagemInvalida):
        mensagem(workflow_id="")


def test_remetente_ou_destinatario_vazio_e_recusado():
    with pytest.raises(MensagemInvalida):
        mensagem(source_agent="")
    with pytest.raises(MensagemInvalida):
        mensagem(target_agent="")


@pytest.mark.parametrize("campo,valor", [
    ("action", "REQUEST"),
    ("status", "PENDING"),
    ("priority", "NORMAL"),
])
def test_valor_fora_do_enum_e_recusado(campo, valor):
    """String crua não vale: o vocabulário é fechado."""
    with pytest.raises(MensagemInvalida):
        mensagem(**{campo: valor})


def test_payload_precisa_ser_objeto():
    with pytest.raises(MensagemInvalida):
        mensagem(payload=["lista"])


def test_vocabulario_completo_do_protocolo():
    assert {p.value for p in Prioridade} == {"LOW", "NORMAL", "HIGH", "CRITICAL"}
    assert {s.value for s in Status} == {
        "PENDING", "RUNNING", "WAITING", "COMPLETED", "FAILED", "CANCELLED"
    }
    assert {a.value for a in Acao} == {
        "REQUEST", "RESPONSE", "UPDATE", "VALIDATION", "RETRY", "ERROR", "FINISH"
    }


# --------------------------------------------------------------------------- #
# Nenhum agente conversa diretamente com outro
# --------------------------------------------------------------------------- #


def test_mensagem_entre_dois_agentes_e_recusada():
    """A topologia é estrela: uma das pontas é sempre o orquestrador."""
    with pytest.raises(ComunicacaoDireta):
        Mensagem(
            workflow_id="wf-teste",
            source_agent="17",
            target_agent="18",
            action=Acao.RESPONSE,
        )


def test_agente_para_orquestrador_e_valido():
    assert mensagem(source_agent="17", target_agent=MASTER_ORCHESTRATOR)


def test_orquestrador_para_si_mesmo_e_valido():
    """O FINISH sai e chega no orquestrador."""
    assert mensagem(
        source_agent=MASTER_ORCHESTRATOR,
        target_agent=MASTER_ORCHESTRATOR,
        action=Acao.FINISH,
    )


# --------------------------------------------------------------------------- #
# Formato padrão
# --------------------------------------------------------------------------- #


def test_entrada_padrao_tem_os_cinco_campos():
    corpo = EntradaPadrao(agent="07").to_dict()

    assert set(corpo) == {"agent", "input", "context", "constraints", "expected_output"}


def test_saida_padrao_tem_os_sete_campos():
    corpo = SaidaPadrao(agent="07", status=Status.COMPLETED, confidence=0.9).to_dict()

    assert set(corpo) == {
        "agent", "status", "confidence", "result", "recommendations",
        "next_agents", "logs",
    }


@pytest.mark.parametrize("valor", [-0.1, 1.1, 2])
def test_confidence_fora_do_intervalo_e_recusada(valor):
    with pytest.raises(MensagemInvalida):
        SaidaPadrao(agent="07", status=Status.COMPLETED, confidence=valor)


@pytest.mark.parametrize("valor", [0.0, 0.5, 1.0])
def test_confidence_dentro_do_intervalo_e_aceita(valor):
    assert SaidaPadrao(agent="07", status=Status.COMPLETED, confidence=valor)


def test_confidence_sai_com_duas_casas():
    corpo = SaidaPadrao(agent="07", status=Status.COMPLETED, confidence=0.98765).to_dict()
    assert corpo["confidence"] == 0.99


# --------------------------------------------------------------------------- #
# Confidence é derivada, não inventada
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("rotulo,esperado", sorted(CONFIDENCE_POR_CONFIABILIDADE.items()))
def test_confidence_deriva_do_rotulo_do_agente(rotulo, esperado):
    resultado = confidence_de({"confiabilidade": rotulo})

    assert resultado["valor"] == esperado
    assert rotulo in resultado["base"]


def test_confidence_publicada_pelo_agente_tem_precedencia():
    resultado = confidence_de({"confiabilidade": "baixa", "confidence": 0.91})

    assert resultado["valor"] == 0.91
    assert "pelo próprio agente" in resultado["base"]


def test_sem_declaracao_a_confidence_nao_e_alta():
    resultado = confidence_de({})

    assert resultado["valor"] == CONFIDENCE_SEM_DECLARACAO
    assert "ausência não é sinal de qualidade" in resultado["base"]


def test_agente_que_falhou_tem_confidence_zero():
    resultado = confidence_de({"confiabilidade": "alta"}, ok=False)

    assert resultado["valor"] == CONFIDENCE_DE_FALHA
    assert "não há saída sobre a qual ter confiança" in resultado["base"]


def test_nenhuma_nao_e_o_mesmo_que_baixa():
    assert (
        CONFIDENCE_POR_CONFIABILIDADE["nenhuma"]
        < CONFIDENCE_POR_CONFIABILIDADE["baixa"]
    )


def test_todo_agente_declara_confiabilidade():
    """A regra "toda saída deve possuir confidence" vale para os 23."""
    entradas = {"dados_usuario": {"objetivo": "x", "horas_por_dia": 2},
                "saidas_anteriores": {}, "solicitacao": ""}

    for codigo, implementacao in sorted(IMPLEMENTACOES.items()):
        saida = implementacao(entradas)
        assert "confiabilidade" in saida, codigo
        assert saida["confiabilidade"] in CONFIDENCE_POR_CONFIABILIDADE, codigo


# --------------------------------------------------------------------------- #
# Logs e erros
# --------------------------------------------------------------------------- #


def test_log_registra_tudo_que_a_spec_pede():
    corpo = Log(
        agent="07",
        workflow_id="wf-teste",
        horario="2026-08-02T10:00:00+00:00",
        tempo_de_execucao_ms=12.345,
        entrada_recebida=["01", "03"],
        saida_produzida=["aula"],
        agentes_acionados=["08"],
    ).to_dict()

    assert set(corpo) == {
        "agent", "workflow_id", "horario", "tempo_de_execucao_ms",
        "entrada_recebida", "saida_produzida", "erros", "agentes_acionados",
    }
    assert corpo["tempo_de_execucao_ms"] == 12.35


def test_erro_registra_motivo_responsavel_impacto_e_replay():
    corpo = Erro(
        agent="09",
        motivo="conteúdo não estudado",
        impacto="a fase de produção fica incompleta",
        workflow_id="wf-teste",
    ).to_dict()

    assert corpo["agente_responsavel"] == "09"
    assert corpo["motivo"] and corpo["impacto"]
    assert corpo["replay_solicitado_ao"] == MASTER_ORCHESTRATOR


# --------------------------------------------------------------------------- #
# Reexecução
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("motivo", MOTIVOS_DE_REEXECUCAO)
def test_motivos_previstos_autorizam(motivo):
    assert autorizar_reexecucao(motivo) == motivo


def test_motivo_fora_da_lista_e_recusado():
    with pytest.raises(ReexecucaoNaoAutorizada):
        autorizar_reexecucao("o agente quis")


async def test_reexecucao_pede_autorizacao_e_registra_retry():
    orquestrador = MasterOrchestrator()
    fluxo = await orquestrador.orquestrar("diagnóstico", dados_usuario=DADOS)

    nova = await orquestrador.reexecutar(
        fluxo, {"03"}, "autorizado_pelo_orquestrador"
    )

    assert nova.mensagens[0].action is Acao.RETRY
    assert nova.mensagens[0].payload["agentes"] == ["03"]
    assert nova.mensagens[0].payload["motivo"] == "autorizado_pelo_orquestrador"


async def test_reexecucao_sem_motivo_previsto_e_recusada():
    orquestrador = MasterOrchestrator()
    fluxo = await orquestrador.orquestrar("diagnóstico", dados_usuario=DADOS)

    with pytest.raises(ReexecucaoNaoAutorizada):
        await orquestrador.reexecutar(fluxo, {"03"}, "porque sim")


async def test_retry_por_reprovacao_exige_reprovacao_de_fato():
    """Sem reprovação do validator, esse motivo não vale."""
    orquestrador = MasterOrchestrator()
    fluxo = await orquestrador.orquestrar("diagnóstico", dados_usuario=DADOS)
    assert fluxo.validacao.aprovado is True

    with pytest.raises(ReexecucaoNaoAutorizada):
        await orquestrador.reexecutar(fluxo, {"03"}, "reprovado_pelo_validator")


# --------------------------------------------------------------------------- #
# Memória
# --------------------------------------------------------------------------- #


def test_memoria_local_morre_com_a_execucao():
    memoria = MemoriaLocal(agent="07")
    memoria.anotar("rascunho", "x")

    assert memoria.ler("rascunho") == "x"
    memoria.encerrar()

    assert memoria.ativa is False
    with pytest.raises(MensagemInvalida):
        memoria.ler("rascunho")
    with pytest.raises(MensagemInvalida):
        memoria.anotar("outro", "y")


def test_memoria_compartilhada_so_e_escrita_pelo_orquestrador():
    memoria = MemoriaCompartilhada("wf-teste")
    memoria.publicar(MASTER_ORCHESTRATOR, "intencao", "diagnostico")

    assert memoria.ler("intencao") == "diagnostico"
    with pytest.raises(ComunicacaoDireta):
        memoria.publicar("17", "intencao", "outra")


def test_leitura_da_memoria_compartilhada_nao_altera_o_original():
    memoria = MemoriaCompartilhada("wf-teste")
    memoria.publicar(MASTER_ORCHESTRATOR, "chave", "valor")

    copia = memoria.como_dicionario()
    copia["chave"] = "alterado"

    assert memoria.ler("chave") == "valor"


# --------------------------------------------------------------------------- #
# Integração: o fluxo real fala o protocolo
# --------------------------------------------------------------------------- #


async def test_fluxo_emite_request_e_response_para_cada_agente():
    fluxo = await MasterOrchestrator().orquestrar("diagnóstico", dados_usuario=DADOS)

    executados = [e.codigo for e in fluxo.execucoes if e.status == "concluido"]
    pedidos = [
        m for m in fluxo.mensagens if m.action in (Acao.REQUEST, Acao.VALIDATION)
    ]
    respostas = [m for m in fluxo.mensagens if m.action is Acao.RESPONSE]

    assert {m.target_agent for m in pedidos} >= set(executados)
    assert {m.source_agent for m in respostas} >= set(executados)


async def test_toda_mensagem_do_fluxo_passa_pelo_orquestrador():
    fluxo = await MasterOrchestrator().orquestrar(
        "quero o plano completo", dados_usuario=DADOS
    )

    for msg in fluxo.mensagens:
        assert MASTER_ORCHESTRATOR in (msg.source_agent, msg.target_agent)
        msg.validar()


async def test_workflow_id_e_o_mesmo_em_tudo():
    fluxo = await MasterOrchestrator().orquestrar("diagnóstico", dados_usuario=DADOS)

    assert fluxo.workflow_id
    assert {m.workflow_id for m in fluxo.mensagens} == {fluxo.workflow_id}
    assert {log.workflow_id for log in fluxo.logs} == {fluxo.workflow_id}


async def test_cada_execucao_gera_um_log():
    fluxo = await MasterOrchestrator().orquestrar("diagnóstico", dados_usuario=DADOS)
    executados = [e for e in fluxo.execucoes if e.status in ("concluido", "falhou")]

    assert len(fluxo.logs) == len(executados)
    for log in fluxo.logs:
        assert log.horario
        assert log.tempo_de_execucao_ms >= 0
        assert isinstance(log.saida_produzida, list)


async def test_fluxo_termina_com_finish():
    fluxo = await MasterOrchestrator().orquestrar("diagnóstico", dados_usuario=DADOS)
    ultima = fluxo.mensagens[-1]

    assert ultima.action is Acao.FINISH
    assert ultima.source_agent == ultima.target_agent == MASTER_ORCHESTRATOR
    assert ultima.payload["status_da_validacao"] == fluxo.validacao.status


async def test_toda_execucao_publica_confidence():
    fluxo = await MasterOrchestrator().orquestrar(
        "quero o plano completo", dados_usuario=DADOS
    )

    for execucao in fluxo.execucoes:
        assert 0.0 <= execucao.confidence <= 1.0
        assert execucao.base_da_confidence
        assert execucao.to_dict()["confidence"] == round(execucao.confidence, 2)


async def test_agente_obrigatorio_tem_prioridade_critical():
    fluxo = await MasterOrchestrator().orquestrar("diagnóstico", dados_usuario=DADOS)
    pedidos = {m.target_agent: m for m in fluxo.mensagens if m.action is Acao.REQUEST}

    assert pedidos["01"].priority is Prioridade.CRITICAL
    assert pedidos["02"].priority is Prioridade.CRITICAL


async def test_agente_ignorado_gera_mensagem_de_erro():
    """Entrada indisponível vira ERROR endereçado, não silêncio."""
    fluxo = await MasterOrchestrator().orquestrar(
        "quero exercícios", dados_usuario={"objetivo": "x"}
    )
    erros = [m for m in fluxo.mensagens if m.action is Acao.ERROR]

    if erros:
        for msg in erros:
            assert msg.status in (acp.Status.FAILED, acp.Status.CANCELLED)
            assert msg.payload["motivo"]
            assert msg.payload["agente_responsavel"]


async def test_saida_do_agente_no_payload_e_a_mesma_do_fluxo():
    """O protocolo transporta a saída; não a reescreve."""
    fluxo = await MasterOrchestrator().orquestrar("diagnóstico", dados_usuario=DADOS)

    for msg in fluxo.mensagens:
        if msg.action is not Acao.RESPONSE:
            continue
        codigo = msg.source_agent
        assert msg.payload["result"] == fluxo.saidas[codigo].conteudo
