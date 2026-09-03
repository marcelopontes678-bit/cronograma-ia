from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DIR_BACKEND = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str

    @field_validator("DATABASE_URL")
    @classmethod
    def normaliza_scheme_asyncpg(cls, v: str) -> str:
        # Provedores de hosting (Render, Railway, Heroku...) entregam a
        # connection string como postgres:// ou postgresql:// -- o driver
        # async exige o scheme postgresql+asyncpg:// explicito.
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"

    # Dominio de orcamento de marcenaria (agente MARC / Claude Vision)
    ANTHROPIC_API_KEY: str = ""
    ORCAMENTO_MODELO_CLAUDE: str = "claude-sonnet-5"
    ORCAMENTO_STORAGE_DIR: str = str(_DIR_BACKEND / "storage" / "orcamentos")
    ORCAMENTO_TABELA_PRECOS: str = str(_DIR_BACKEND / "config" / "tabela_precos_referencia.xlsx")
    ORCAMENTO_CONFIG_PRECIFICACAO: str = str(_DIR_BACKEND / "config" / "precificacao.json")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

    def validar_anthropic_api_key(self) -> None:
        if not self.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY nao configurada. Defina a variavel de ambiente antes de "
                "iniciar a API -- nunca coloque a chave direto no codigo ou em arquivo versionado."
            )


settings = Settings()
