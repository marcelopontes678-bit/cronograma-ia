from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_KEY_MARKERS = ("troque", "change", "secret", "example", "dev-key")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            key = self.SECRET_KEY.lower()
            if len(self.SECRET_KEY) < 32 or any(m in key for m in _INSECURE_KEY_MARKERS):
                raise ValueError(
                    "SECRET_KEY insegura para produção. "
                    "Gere uma com: openssl rand -hex 32"
                )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


settings = Settings()
