from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import credentials_exception
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_token_hash,
    refresh_token_expires_at,
    verify_password,
)
from app.models.usuario import RefreshToken, Usuario
from app.schemas.auth import TokenResponse


async def login(db: AsyncSession, email: str, password: str) -> TokenResponse:
    result = await db.execute(
        select(Usuario).where(Usuario.email == email, Usuario.is_active.is_(True))
    )
    usuario = result.scalar_one_or_none()

    if not usuario or not verify_password(password, usuario.hashed_password):
        raise credentials_exception

    await db.execute(
        update(Usuario)
        .where(Usuario.id == usuario.id)
        .values(last_login_at=datetime.now(timezone.utc))
    )

    access_token = create_access_token(
        subject=str(usuario.id),
        email=usuario.email,
        role=usuario.role.value,
        empresa_id=str(usuario.empresa_id),
    )
    raw_refresh, token_hash = create_refresh_token()

    db.add(
        RefreshToken(
            usuario_id=usuario.id,
            token_hash=token_hash,
            expires_at=refresh_token_expires_at(),
        )
    )
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_access_token(db: AsyncSession, raw_refresh: str) -> TokenResponse:
    token_hash = get_token_hash(raw_refresh)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    rt = result.scalar_one_or_none()
    if not rt:
        raise credentials_exception

    user_result = await db.execute(
        select(Usuario).where(Usuario.id == rt.usuario_id, Usuario.is_active.is_(True))
    )
    usuario = user_result.scalar_one_or_none()
    if not usuario:
        raise credentials_exception

    access_token = create_access_token(
        subject=str(usuario.id),
        email=usuario.email,
        role=usuario.role.value,
        empresa_id=str(usuario.empresa_id),
    )
    # Rotacionar refresh token
    rt.revoked_at = datetime.now(timezone.utc)
    raw_new, new_hash = create_refresh_token()
    db.add(
        RefreshToken(
            usuario_id=usuario.id,
            token_hash=new_hash,
            expires_at=refresh_token_expires_at(),
        )
    )
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_new,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def logout(db: AsyncSession, raw_refresh: str) -> None:
    token_hash = get_token_hash(raw_refresh)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt = result.scalar_one_or_none()
    if rt:
        rt.revoked_at = datetime.now(timezone.utc)
        await db.commit()
