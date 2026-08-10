import enum
import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario


class StatusConexaoInstagram(str, enum.Enum):
    INITIATED = "initiated"
    ACTIVE = "active"
    FAILED = "failed"
    EXPIRED = "expired"
    INACTIVE = "inactive"
    REVOKED = "revoked"


class ConexaoInstagram(TimestampMixin, Base):
    __tablename__ = "conexoes_instagram"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("empresas.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    conectado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
    )
    composio_connected_account_id: Mapped[str] = mapped_column(
        sa.String(64), nullable=False
    )
    status: Mapped[StatusConexaoInstagram] = mapped_column(
        sa.Enum(
            StatusConexaoInstagram,
            name="statusconexaoinstagram",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=StatusConexaoInstagram.INITIATED,
    )

    empresa: Mapped["Empresa"] = relationship(
        "Empresa", back_populates="conexao_instagram"
    )
    conectado_por: Mapped["Usuario | None"] = relationship("Usuario")
