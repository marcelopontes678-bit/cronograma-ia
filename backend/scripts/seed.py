"""
Script de seed — cria dados iniciais para desenvolvimento.
Uso: docker compose exec backend python scripts/seed.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.models.base import Base
from app.models.empresa import Empresa
from app.models.unidade import TipoUnidade, Unidade
from app.models.usuario import RoleUsuario, Usuario
import app.models  # garante que todos os modelos são importados


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        # Verificar se já existe
        result = await db.execute(select(Empresa).where(Empresa.cnpj == "11.222.333/0001-81"))
        if result.scalar_one_or_none():
            print("Seed já executado. Nenhuma alteração feita.")
            return

        empresa = Empresa(
            nome="Marcenaria Demo Ltda",
            nome_fantasia="Demo Móveis",
            cnpj="11.222.333/0001-81",
            email="contato@demodemoveis.com.br",
            telefone="(11) 99999-0000",
            cidade="São Paulo",
            estado="SP",
            dias_funcionamento=["SEG", "TER", "QUA", "QUI", "SEX"],
        )
        db.add(empresa)
        await db.flush()

        fabrica = Unidade(
            empresa_id=empresa.id,
            nome="Fábrica Principal",
            tipo=TipoUnidade.FABRICA,
            codigo="FAB-01",
            cidade="São Paulo",
            estado="SP",
            is_sede=True,
        )
        db.add(fabrica)
        await db.flush()

        admin = Usuario(
            empresa_id=empresa.id,
            unidade_id=fabrica.id,
            nome="Administrador",
            email="admin@demo.com",
            hashed_password=hash_password("admin123!"),
            role=RoleUsuario.ADMIN,
            must_change_password=True,
        )
        db.add(admin)
        await db.commit()

        print("✓ Seed concluído!")
        print(f"  Empresa: {empresa.nome} (ID: {empresa.id})")
        print(f"  Unidade: {fabrica.nome} (ID: {fabrica.id})")
        print(f"  Usuário ADMIN: {admin.email} / senha: admin123!")
        print("  ATENÇÃO: altere a senha no primeiro login.")


if __name__ == "__main__":
    asyncio.run(seed())
