import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.core.exceptions import not_found
from app.models.producao import AusenciaOperador, TarefaCronograma
from app.models.projeto import Projeto, StatusProducao
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.producao import (
    AusenciaOperadorCreate,
    OperadorUpdate,
    ProjetoProducaoCreate,
    TarefaCronogramaCreate,
    TarefaCronogramaUpdate,
)


async def _get_projeto_do_tenant(
    db: AsyncSession, projeto_id: uuid.UUID, current_user: Usuario
) -> Projeto:
    result = await db.execute(
        select(Projeto).where(Projeto.id == projeto_id, Projeto.is_active.is_(True))
    )
    projeto = result.scalar_one_or_none()
    # Isolamento estrito por empresa_id, sem excecao pra ADMIN -- mesmo
    # padrao de comercial_service.py (mais recente e mais correto que o
    # bypass usado em projeto_service.py/unidade_service.py legados).
    if not projeto or projeto.empresa_id != current_user.empresa_id:
        raise not_found("Projeto")
    return projeto


async def listar_tarefas_do_projeto(
    db: AsyncSession, projeto_id: uuid.UUID, current_user: Usuario
) -> list[TarefaCronograma]:
    await _get_projeto_do_tenant(db, projeto_id, current_user)
    result = await db.execute(
        select(TarefaCronograma).where(
            TarefaCronograma.projeto_id == projeto_id,
            TarefaCronograma.is_active.is_(True),
        )
    )
    tarefas = list(result.scalars().all())
    for tarefa in tarefas:
        set_committed_value(tarefa, "projeto", None)
        set_committed_value(tarefa, "operador", None)
    return tarefas


async def criar_tarefa(
    db: AsyncSession,
    projeto_id: uuid.UUID,
    data: TarefaCronogramaCreate,
    current_user: Usuario,
) -> TarefaCronograma:
    await _get_projeto_do_tenant(db, projeto_id, current_user)
    tarefa = TarefaCronograma(projeto_id=projeto_id, **data.model_dump())
    db.add(tarefa)
    await db.commit()
    await db.refresh(tarefa)
    set_committed_value(tarefa, "projeto", None)
    set_committed_value(tarefa, "operador", None)
    return tarefa


async def _get_tarefa_do_tenant(
    db: AsyncSession, tarefa_id: uuid.UUID, current_user: Usuario
) -> TarefaCronograma:
    result = await db.execute(
        select(TarefaCronograma).where(
            TarefaCronograma.id == tarefa_id, TarefaCronograma.is_active.is_(True)
        )
    )
    tarefa = result.scalar_one_or_none()
    if not tarefa:
        raise not_found("Tarefa")
    await _get_projeto_do_tenant(db, tarefa.projeto_id, current_user)
    return tarefa


async def atualizar_tarefa(
    db: AsyncSession,
    tarefa_id: uuid.UUID,
    data: TarefaCronogramaUpdate,
    current_user: Usuario,
) -> TarefaCronograma:
    tarefa = await _get_tarefa_do_tenant(db, tarefa_id, current_user)

    payload = data.model_dump(exclude_none=True, exclude={"novo_evento_historico"})
    for field, value in payload.items():
        setattr(tarefa, field, value)

    if data.novo_evento_historico:
        tarefa.historico = [*tarefa.historico, data.novo_evento_historico.model_dump()]

    await db.commit()
    await db.refresh(tarefa)
    set_committed_value(tarefa, "projeto", None)
    set_committed_value(tarefa, "operador", None)
    return tarefa


async def deletar_tarefa(
    db: AsyncSession, tarefa_id: uuid.UUID, current_user: Usuario
) -> None:
    tarefa = await _get_tarefa_do_tenant(db, tarefa_id, current_user)
    tarefa.is_active = False
    await db.commit()


async def listar_projetos_producao(
    db: AsyncSession, current_user: Usuario
) -> list[tuple[Projeto, list[TarefaCronograma]]]:
    result = await db.execute(
        select(Projeto).where(
            Projeto.empresa_id == current_user.empresa_id,
            Projeto.status_producao.is_not(None),
            Projeto.is_active.is_(True),
        )
    )
    projetos = list(result.scalars().all())
    if not projetos:
        return []

    projeto_ids = [p.id for p in projetos]
    result = await db.execute(
        select(TarefaCronograma).where(
            TarefaCronograma.projeto_id.in_(projeto_ids),
            TarefaCronograma.is_active.is_(True),
        )
    )
    tarefas = list(result.scalars().all())
    for tarefa in tarefas:
        set_committed_value(tarefa, "projeto", None)
        set_committed_value(tarefa, "operador", None)

    tarefas_por_projeto: dict[uuid.UUID, list[TarefaCronograma]] = {}
    for tarefa in tarefas:
        tarefas_por_projeto.setdefault(tarefa.projeto_id, []).append(tarefa)

    return [(p, tarefas_por_projeto.get(p.id, [])) for p in projetos]


async def criar_projeto_producao(
    db: AsyncSession, data: ProjetoProducaoCreate, current_user: Usuario
) -> Projeto:
    codigo = f"OP-{uuid.uuid4().hex[:8].upper()}"
    projeto = Projeto(
        empresa_id=current_user.empresa_id,
        criado_por_id=current_user.id,
        codigo=codigo,
        status_producao=StatusProducao.BACKLOG,
        **data.model_dump(),
    )
    db.add(projeto)
    await db.commit()
    await db.refresh(projeto)
    return projeto


async def listar_operadores(db: AsyncSession, current_user: Usuario) -> list[Usuario]:
    result = await db.execute(
        select(Usuario).where(
            Usuario.empresa_id == current_user.empresa_id,
            Usuario.role == RoleUsuario.OPERADOR,
            Usuario.is_active.is_(True),
        )
    )
    return list(result.scalars().all())


async def atualizar_perfil_operador(
    db: AsyncSession, usuario_id: uuid.UUID, data: OperadorUpdate, current_user: Usuario
) -> Usuario:
    result = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id, Usuario.is_active.is_(True))
    )
    usuario = result.scalar_one_or_none()
    if not usuario or usuario.empresa_id != current_user.empresa_id:
        raise not_found("Usuário")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(usuario, field, value)

    await db.commit()
    await db.refresh(usuario)
    return usuario


async def listar_ausencias(db: AsyncSession, current_user: Usuario) -> list[AusenciaOperador]:
    result = await db.execute(
        select(AusenciaOperador)
        .join(Usuario, Usuario.id == AusenciaOperador.usuario_id)
        .where(Usuario.empresa_id == current_user.empresa_id, AusenciaOperador.is_active.is_(True))
    )
    return list(result.scalars().all())


async def criar_ausencia(
    db: AsyncSession, data: AusenciaOperadorCreate, current_user: Usuario
) -> AusenciaOperador:
    result = await db.execute(
        select(Usuario).where(Usuario.id == data.usuario_id, Usuario.is_active.is_(True))
    )
    usuario = result.scalar_one_or_none()
    if not usuario or usuario.empresa_id != current_user.empresa_id:
        raise not_found("Usuário")

    ausencia = AusenciaOperador(**data.model_dump())
    db.add(ausencia)
    await db.commit()
    await db.refresh(ausencia)
    return ausencia


async def deletar_ausencia(
    db: AsyncSession, ausencia_id: uuid.UUID, current_user: Usuario
) -> None:
    result = await db.execute(
        select(AusenciaOperador).where(
            AusenciaOperador.id == ausencia_id, AusenciaOperador.is_active.is_(True)
        )
    )
    ausencia = result.scalar_one_or_none()
    if not ausencia:
        raise not_found("Ausência")

    result = await db.execute(select(Usuario).where(Usuario.id == ausencia.usuario_id))
    usuario = result.scalar_one_or_none()
    if not usuario or usuario.empresa_id != current_user.empresa_id:
        raise not_found("Ausência")

    ausencia.is_active = False
    await db.commit()
