"""Registro dos agentes especializados do StudyOS.

O Master Orchestrator não ensina nem produz conteúdo: ele apenas conhece
os agentes, suas dependências e a fase do fluxo em que cada um atua.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Fase(str, Enum):
    """Fases do fluxo canônico do StudyOS."""

    DIAGNOSTICO = "diagnostico"
    PLANEJAMENTO = "planejamento"
    PRODUCAO = "producao"
    TUTORIA = "tutoria"
    MEMORIA = "memoria"
    AVALIACAO = "avaliacao"
    ACOMPANHAMENTO = "acompanhamento"
    VALIDACAO = "validacao"


#: Ordem em que as fases podem ser executadas (usada só para ordenação estável
#: da saída — as dependências reais são o que governa a execução).
ORDEM_FASES: tuple[Fase, ...] = (
    Fase.DIAGNOSTICO,
    Fase.PLANEJAMENTO,
    Fase.PRODUCAO,
    Fase.TUTORIA,
    Fase.MEMORIA,
    Fase.AVALIACAO,
    Fase.ACOMPANHAMENTO,
    Fase.VALIDACAO,
)


@dataclass(frozen=True)
class AgentSpec:
    """Definição estática de um agente especializado."""

    codigo: str
    nome: str
    fase: Fase
    tarefa: str
    depende_de: tuple[str, ...] = ()
    #: Campos que o agente lê do contexto inicial (não das saídas de outros agentes).
    entradas_do_usuario: tuple[str, ...] = ()
    #: Agente terminal: recebe automaticamente a saída de todos os demais agentes
    #: executados no fluxo (caso dos Validators).
    agrega_tudo: bool = False

    @property
    def id(self) -> str:
        """Identificador estável no formato ``01-profile-analyzer``."""
        slug = self.nome.lower().replace(" ", "-")
        return f"{self.codigo}-{slug}"


# --------------------------------------------------------------------------- #
# Catálogo dos 24 agentes
# --------------------------------------------------------------------------- #

PROFILE_ANALYZER = AgentSpec(
    codigo="01",
    nome="Profile Analyzer",
    fase=Fase.DIAGNOSTICO,
    tarefa=(
        "Construir o Perfil Cognitivo Estruturado: perfil acadêmico, nível geral, "
        "tempo real disponível, riscos, pontos fortes e fracos, estilo de "
        "aprendizagem e carga máxima diária"
    ),
    entradas_do_usuario=(
        "nome",
        "idade",
        "escolaridade",
        "objetivo",
        "exame",
        "profissao",
        "rotina",
        "horas_por_dia",
        "dias_por_semana",
        "data_prova",
        "experiencia_anterior",
        "disciplinas_favoritas",
        "disciplinas_dificuldade",
        "preferencia_estudo",
        "idioma",
        "restricoes",
        "necessidades_especiais",
    ),
)

GOAL_ANALYZER = AgentSpec(
    codigo="02",
    nome="Goal Analyzer",
    fase=Fase.DIAGNOSTICO,
    tarefa=(
        "Converter o objetivo em Mapa Estratégico de Aprendizagem: categoria, "
        "disciplinas, prioridades, competências, carga estimada, prazo e "
        "critérios de sucesso"
    ),
    # O Mapa Estratégico usa o Perfil Cognitivo como entrada (tempo e prazo).
    depende_de=("01",),
    entradas_do_usuario=(
        "objetivo",
        "objetivos_secundarios",
        "exame",
        "categoria",
        "data_prova",
        "edital",
        "materias",
        "bibliografia",
        "materiais_obrigatorios",
        "nota_corte",
    ),
)

KNOWLEDGE_ANALYZER = AgentSpec(
    codigo="03",
    nome="Knowledge Analyzer",
    fase=Fase.DIAGNOSTICO,
    tarefa=(
        "Construir o Mapa de Conhecimento Estruturado: domínio por tópico com "
        "base em evidência prática, lacunas, pré-requisitos ausentes, tópicos "
        "esquecidos, esforço por tópico e Índice Geral de Conhecimento"
    ),
    depende_de=("01", "02"),
    entradas_do_usuario=(
        "historico",
        "resultados_simulados",
        "resultados_exercicios",
        "questionario_diagnostico",
        "ultimo_contato",
        "subtopicos",
        "pre_requisitos",
    ),
)

CURRICULUM_BUILDER = AgentSpec(
    codigo="04",
    nome="Curriculum Builder",
    fase=Fase.PLANEJAMENTO,
    tarefa=(
        "Montar a Árvore Curricular Inteligente — disciplina, módulo, tópico, "
        "subtópico e microtópico — com dificuldade, importância, tempo estimado "
        "e status de domínio por item"
    ),
    depende_de=("01", "02", "03"),
    entradas_do_usuario=(
        "edital",
        "matriz_curricular",
        "bibliografia",
        "subtopicos",
        "microtopicos",
        "pre_requisitos",
        "conteudos_obrigatorios",
        "conteudos_opcionais",
    ),
)

DEPENDENCY_MAPPER = AgentSpec(
    codigo="05",
    nome="Dependency Mapper",
    fase=Fase.PLANEJAMENTO,
    tarefa=(
        "Construir o Grafo de Aprendizagem: DAG de pré-requisitos com ondas de "
        "estudo paralelo, caminho crítico, nós bloqueadores, profundidade e "
        "sequência lógica ideal"
    ),
    depende_de=("01", "02", "03", "04"),
    entradas_do_usuario=("pre_requisitos",),
)

ROADMAP_BUILDER = AgentSpec(
    codigo="06",
    nome="Roadmap Builder",
    fase=Fase.PLANEJAMENTO,
    tarefa=(
        "Construir o Plano de Estudos: cronograma diário com sessões de "
        "conteúdo, exercícios e revisão, metas diárias/semanais/mensais, "
        "indicadores e risco de atraso"
    ),
    depende_de=("01", "02", "03", "04", "05"),
    entradas_do_usuario=(
        "data_inicio",
        "data_prova",
        "dias_da_semana",
        "faltas",
        "progresso",
        "historico",
    ),
)

LESSON_GENERATOR = AgentSpec(
    codigo="07",
    nome="Lesson Generator",
    fase=Fase.PRODUCAO,
    tarefa="Produzir as aulas de cada tópico do roadmap",
    depende_de=("06",),
)

EXAMPLE_GENERATOR = AgentSpec(
    codigo="08",
    nome="Example Generator",
    fase=Fase.PRODUCAO,
    tarefa="Gerar exemplos resolvidos para cada aula",
    depende_de=("07",),
)

EXERCISE_GENERATOR = AgentSpec(
    codigo="09",
    nome="Exercise Generator",
    fase=Fase.PRODUCAO,
    tarefa="Gerar exercícios calibrados por aula e nível",
    depende_de=("07",),
)

FLASHCARD_GENERATOR = AgentSpec(
    codigo="10",
    nome="Flashcard Generator",
    fase=Fase.PRODUCAO,
    tarefa="Extrair flashcards atômicos das aulas",
    depende_de=("07",),
)

SUMMARY_GENERATOR = AgentSpec(
    codigo="11",
    nome="Summary Generator",
    fase=Fase.PRODUCAO,
    tarefa="Produzir resumos e sínteses por tópico",
    depende_de=("07",),
)

DIFFICULTY_DETECTOR = AgentSpec(
    codigo="12",
    nome="Difficulty Detector",
    fase=Fase.TUTORIA,
    tarefa="Estimar dificuldade percebida por tópico a partir do nível e dos exercícios",
    depende_de=("03", "09"),
)

ADAPTIVE_TEACHER = AgentSpec(
    codigo="13",
    nome="Adaptive Teacher",
    fase=Fase.TUTORIA,
    tarefa="Reescrever a explicação nos pontos de maior dificuldade",
    depende_de=("07", "12"),
)

MEMORY_SCHEDULER = AgentSpec(
    codigo="14",
    nome="Memory Scheduler",
    fase=Fase.MEMORIA,
    tarefa="Definir os intervalos de repetição espaçada dos flashcards",
    depende_de=("06", "10"),
)

REVISION_PLANNER = AgentSpec(
    codigo="15",
    nome="Revision Planner",
    fase=Fase.MEMORIA,
    tarefa="Encaixar as revisões no roadmap sem estourar a carga diária",
    depende_de=("06", "14"),
)

EXAM_SIMULATOR = AgentSpec(
    codigo="16",
    nome="Exam Simulator",
    fase=Fase.AVALIACAO,
    tarefa="Montar simulados com peso proporcional à grade",
    depende_de=("04", "09"),
)

ERROR_ANALYZER = AgentSpec(
    codigo="17",
    nome="Error Analyzer",
    fase=Fase.AVALIACAO,
    tarefa="Classificar os erros do simulado por causa raiz",
    depende_de=("16",),
)

WEAKNESS_FINDER = AgentSpec(
    codigo="18",
    nome="Weakness Finder",
    fase=Fase.AVALIACAO,
    tarefa="Consolidar os erros em pontos fracos priorizados",
    depende_de=("17",),
)

COACH = AgentSpec(
    codigo="19",
    nome="Coach",
    fase=Fase.ACOMPANHAMENTO,
    tarefa="Traduzir o plano em orientação de execução e ritmo",
    depende_de=("01", "06"),
)

HABIT_BUILDER = AgentSpec(
    codigo="20",
    nome="Habit Builder",
    fase=Fase.ACOMPANHAMENTO,
    tarefa="Converter o roadmap em rotina e gatilhos diários",
    depende_de=("01", "06"),
)

PERFORMANCE_ANALYZER = AgentSpec(
    codigo="21",
    nome="Performance Analyzer",
    fase=Fase.ACOMPANHAMENTO,
    tarefa="Medir desempenho e aderência contra o planejado",
    depende_de=("17",),
)

FORECAST_AGENT = AgentSpec(
    codigo="22",
    nome="Forecast Agent",
    fase=Fase.ACOMPANHAMENTO,
    tarefa="Projetar a chegada ao objetivo no ritmo atual",
    depende_de=("06", "21"),
)

OPTIMIZATION_AGENT = AgentSpec(
    codigo="23",
    nome="Optimization Agent",
    fase=Fase.ACOMPANHAMENTO,
    tarefa="Propor ajustes de plano a partir da projeção e dos pontos fracos",
    depende_de=("18", "22"),
)

VALIDATORS = AgentSpec(
    codigo="24",
    nome="Validators",
    fase=Fase.VALIDACAO,
    tarefa="Validar cobertura, consistência e ausência de invenção em todas as saídas",
    agrega_tudo=True,
)


AGENTES: dict[str, AgentSpec] = {
    spec.codigo: spec
    for spec in (
        PROFILE_ANALYZER,
        GOAL_ANALYZER,
        KNOWLEDGE_ANALYZER,
        CURRICULUM_BUILDER,
        DEPENDENCY_MAPPER,
        ROADMAP_BUILDER,
        LESSON_GENERATOR,
        EXAMPLE_GENERATOR,
        EXERCISE_GENERATOR,
        FLASHCARD_GENERATOR,
        SUMMARY_GENERATOR,
        DIFFICULTY_DETECTOR,
        ADAPTIVE_TEACHER,
        MEMORY_SCHEDULER,
        REVISION_PLANNER,
        EXAM_SIMULATOR,
        ERROR_ANALYZER,
        WEAKNESS_FINDER,
        COACH,
        HABIT_BUILDER,
        PERFORMANCE_ANALYZER,
        FORECAST_AGENT,
        OPTIMIZATION_AGENT,
        VALIDATORS,
    )
}

#: Agentes obrigatórios em qualquer fluxo: diagnóstico mínimo + validação.
#: O orquestrador nunca pula estes agentes.
AGENTES_OBRIGATORIOS: tuple[str, ...] = ("01", "02", "24")


def get_agent(codigo: str) -> AgentSpec:
    try:
        return AGENTES[codigo]
    except KeyError:
        raise KeyError(f"Agente desconhecido: {codigo!r}") from None


@dataclass
class AgentResult:
    """Saída de um agente já executado."""

    codigo: str
    nome: str
    fase: Fase
    tarefa: str
    conteudo: dict
    #: Campos que o agente não pôde preencher por falta de informação do usuário.
    lacunas: list[str] = field(default_factory=list)
    erro: str | None = None

    @property
    def ok(self) -> bool:
        return self.erro is None
