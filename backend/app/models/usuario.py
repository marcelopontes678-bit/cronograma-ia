import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.empresa import Empresa
    from app.models.unidade import Unidade


class RoleUsuario(str, enum.Enum):
    ADMIN = "admin"
    GERENTE = "gerente"
    OPERADOR = "operador"
    VISUALIZADOR = "visualizador"


class Usuario(TimestampMixin, Base):
    __tablename__ = "usuarios"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("empresas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    unidade_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("unidades.id", ondelete="SET NULL"),
    )
    nome: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    email: Mapped[str] = mapped_column(sa.String(254), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role: Mapped[RoleUsuario] = mapped_column(
        sa.Enum(RoleUsuario, name="roleusuario", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    telefone: Mapped[str | None] = mapped_column(sa.String(20))
    avatar_url: Mapped[str | None] = mapped_column(sa.String(500))
    last_login_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    must_change_password: Mapped[bool] = mapped_column(
        sa.Boolean, default=False, nullable=False
    )

    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="usuarios")
    unidade: Mapped["Unidade | None"] = relationship(
        "Unidade", back_populates="usuarios"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="usuario", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    user_agent: Mapped[str | None] = mapped_column(sa.String(500))
    ip_address: Mapped[str | None] = mapped_column(sa.String(45))

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="refresh_tokens")
