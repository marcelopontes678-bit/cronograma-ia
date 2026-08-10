import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import not_found
from app.models.instagram_connection import ConexaoInstagram, StatusConexaoInstagram
from app.services.composio_service import get_composio_client

TOOLKIT = "instagram"

_STATUS_MAP: dict[str, StatusConexaoInstagram] = {
    "INITIALIZING": StatusConexaoInstagram.INITIATED,
    "INITIATED": StatusConexaoInstagram.INITIATED,
    "ACTIVE": StatusConexaoInstagram.ACTIVE,
    "FAILED": StatusConexaoInstagram.FAILED,
    "EXPIRED": StatusConexaoInstagram.EXPIRED,
    "INACTIVE": StatusConexaoInstagram.INACTIVE,
    "REVOKED": StatusConexaoInstagram.REVOKED,
}


async def _get_conexao(
    db: AsyncSession, empresa_id: uuid.UUID
) -> ConexaoInstagram | None:
    result = await db.execute(
        select(ConexaoInstagram).where(ConexaoInstagram.empresa_id == empresa_id)
    )
    return result.scalar_one_or_none()


async def iniciar_conexao(
    db: AsyncSession, empresa_id: uuid.UUID, usuario_id: uuid.UUID
) -> tuple[str | None, ConexaoInstagram]:
    client = get_composio_client()
    request = client.toolkits.authorize(user_id=str(empresa_id), toolkit=TOOLKIT)

    conexao = await _get_conexao(db, empresa_id)
    if conexao is None:
        conexao = ConexaoInstagram(empresa_id=empresa_id)
        db.add(conexao)

    conexao.composio_connected_account_id = request.id
    conexao.status = _STATUS_MAP.get(request.status, StatusConexaoInstagram.INITIATED)
    conexao.conectado_por_id = usuario_id

    await db.commit()
    await db.refresh(conexao)
    return request.redirect_url, conexao


async def consultar_status(
    db: AsyncSession, empresa_id: uuid.UUID
) -> ConexaoInstagram | None:
    conexao = await _get_conexao(db, empresa_id)
    if conexao is None:
        return None

    client = get_composio_client()
    remoto = client.client.connected_accounts.retrieve(
        nanoid=conexao.composio_connected_account_id
    )
    conexao.status = _STATUS_MAP.get(remoto.status, conexao.status)

    await db.commit()
    await db.refresh(conexao)
    return conexao


async def desconectar(db: AsyncSession, empresa_id: uuid.UUID) -> None:
    conexao = await _get_conexao(db, empresa_id)
    if conexao is None:
        raise not_found("Conexão com Instagram")

    client = get_composio_client()
    client.client.connected_accounts.delete(
        nanoid=conexao.composio_connected_account_id, revoke_on_delete=True
    )

    await db.delete(conexao)
    await db.commit()
