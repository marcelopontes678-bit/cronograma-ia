"""Modelos de dados da triagem.

Divisão de responsabilidades (importante pra confiança no resultado):
- A IA só LÊ o currículo e diz, requisito por requisito, se ele é atendido
  ("sim" / "parcial" / "nao") e qual trecho do currículo prova isso.
- A NOTA e o FILTRO são calculados aqui, em código, de forma determinística.
  Assim 200 currículos são medidos pela mesma régua, e qualquer nota pode ser
  explicada linha a linha para o candidato ou para o dono da empresa.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Atendimento = Literal["sim", "parcial", "nao"]


# ---------------------------------------------------------------- entrada


class Vaga(BaseModel):
    id: str
    titulo: str
    descricao: str = ""
    # Sem estes o candidato é filtrado (eliminatórios).
    obrigatorios: list[str] = Field(default_factory=list)
    # Somam pontos, mas não eliminam.
    desejaveis: list[str] = Field(default_factory=list)


# ------------------------------------------------- saída estruturada da IA


class ItemRequisito(BaseModel):
    requisito: str
    atendido: Atendimento
    evidencia: str = Field(
        description="Trecho ou fato do currículo que sustenta a resposta. Vazio se 'nao'."
    )


class AvaliacaoVagaIA(BaseModel):
    vaga_id: str
    obrigatorios: list[ItemRequisito]
    desejaveis: list[ItemRequisito]
    pontos_fortes: list[str]
    pontos_de_atencao: list[str]


class Contato(BaseModel):
    nome: str
    email: str
    telefone: str
    cidade: str


class AnaliseCurriculoIA(BaseModel):
    e_curriculo: bool = Field(description="False se o arquivo não for um currículo.")
    contato: Contato
    anos_experiencia: float = Field(description="Total estimado de anos de experiência profissional.")
    resumo_perfil: str = Field(description="2 a 3 frases, objetivas, sobre o perfil profissional.")
    avaliacoes: list[AvaliacaoVagaIA]


class CandidatoDestaque(BaseModel):
    arquivo: str
    resumo: str
    por_que_entrevistar: str
    riscos: str
    perguntas_entrevista: list[str]


class ResumoVagaIA(BaseModel):
    visao_geral: str
    candidatos: list[CandidatoDestaque]


# ----------------------------------------------- resultado calculado aqui


PESO_OBRIGATORIOS = 70
PESO_DESEJAVEIS = 30
VALOR = {"sim": 1.0, "parcial": 0.5, "nao": 0.0}


class ResultadoVaga(BaseModel):
    vaga_id: str
    aprovado_filtro: bool
    nota: int  # 0 a 100
    obrigatorios_faltando: list[str]
    avaliacao: AvaliacaoVagaIA


def _media(itens: list[ItemRequisito]) -> float | None:
    if not itens:
        return None
    return sum(VALOR[i.atendido] for i in itens) / len(itens)


def calcular_resultado(avaliacao: AvaliacaoVagaIA) -> ResultadoVaga:
    """Nota 0-100: 70% obrigatórios + 30% desejáveis ("parcial" vale meio ponto).

    Filtro: qualquer obrigatório com "nao" elimina o candidato daquela vaga.
    Se a vaga não tem um dos grupos, o peso inteiro vai pro outro.
    """
    faltando = [i.requisito for i in avaliacao.obrigatorios if i.atendido == "nao"]
    m_obr = _media(avaliacao.obrigatorios)
    m_des = _media(avaliacao.desejaveis)
    if m_obr is None and m_des is None:
        nota = 0.0
    elif m_obr is None:
        nota = m_des * 100
    elif m_des is None:
        nota = m_obr * 100
    else:
        nota = m_obr * PESO_OBRIGATORIOS + m_des * PESO_DESEJAVEIS
    return ResultadoVaga(
        vaga_id=avaliacao.vaga_id,
        aprovado_filtro=not faltando,
        nota=round(nota),
        obrigatorios_faltando=faltando,
        avaliacao=avaliacao,
    )


class Candidato(BaseModel):
    arquivo: str
    erro: str | None = None
    analise: AnaliseCurriculoIA | None = None
    resultados: dict[str, ResultadoVaga] = Field(default_factory=dict)
