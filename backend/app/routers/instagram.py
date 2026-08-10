from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_role
from app.models.instagram_connection import StatusConexaoInstagram
from app.models.usuario import RoleUsuario, Usuario
from app.schemas.instagram import InstagramConnectResponse, InstagramStatusResponse
from app.services import instagram_service

router = APIRouter(prefix="/instagram", tags=["instagram"])


@router.post("/conectar", response_model=InstagramConnectResponse)
async def conectar_instagram(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(RoleUsuario.ADMIN, RoleUsuario.GERENTE)
    ),
):
    redirect_url, conexao = await instagram_service.iniciar_conexao(
        db, current_user.empresa_id, current_user.id
    )
    return InstagramConnectResponse(redirect_url=redirect_url, status=conexao.status.value)


@router.get("/status", response_model=InstagramStatusResponse)
async def status_instagram(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    conexao = await instagram_service.consultar_status(db, current_user.empresa_id)
    if conexao is None:
        return InstagramStatusResponse(conectado=False)

    return InstagramStatusResponse(
        conectado=conexao.status == StatusConexaoInstagram.ACTIVE,
        status=conexao.status.value,
        connected_at=conexao.updated_at,
    )


@router.delete("/conectar", status_code=204)
async def desconectar_instagram(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(
        require_role(RoleUsuario.ADMIN, RoleUsuario.GERENTE)
    ),
):
    await instagram_service.desconectar(db, current_user.empresa_id)
