from app.config import Settings


class TestNormalizacaoDatabaseUrl:
    def test_postgres_scheme_vira_asyncpg(self):
        s = Settings(DATABASE_URL="postgres://user:pass@host/db", SECRET_KEY="x")
        assert s.DATABASE_URL == "postgresql+asyncpg://user:pass@host/db"

    def test_postgresql_scheme_vira_asyncpg(self):
        s = Settings(DATABASE_URL="postgresql://user:pass@host/db", SECRET_KEY="x")
        assert s.DATABASE_URL == "postgresql+asyncpg://user:pass@host/db"

    def test_scheme_ja_asyncpg_fica_igual(self):
        s = Settings(DATABASE_URL="postgresql+asyncpg://user:pass@host/db", SECRET_KEY="x")
        assert s.DATABASE_URL == "postgresql+asyncpg://user:pass@host/db"
