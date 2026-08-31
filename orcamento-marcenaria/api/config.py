"""Configuracao da API. Le tudo de variaveis de ambiente -- nunca
hardcoded, mesmo principio que o resto do projeto (ex: precificacao.json
nunca teve valor de markup no codigo)."""
from __future__ import annotations

import os
from pathlib import Path

_DIR_API = Path(__file__).resolve().parent
_DIR_PROJETO = _DIR_API.parent


class Settings:
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    modelo_claude: str = os.environ.get("ORCAMENTO_MODELO_CLAUDE", "claude-sonnet-5")

    dir_storage: Path = Path(os.environ.get("ORCAMENTO_STORAGE_DIR", str(_DIR_API / "storage")))
    dir_jobs: Path = dir_storage / "jobs"
    dir_preferencias: Path = dir_storage / "preferencias"
    dir_regras_aprendidas: Path = dir_storage / "regras_aprendidas"

    caminho_tabela_precos_padrao: Path = Path(
        os.environ.get("ORCAMENTO_TABELA_PRECOS", str(_DIR_PROJETO / "config" / "tabela_precos_referencia.xlsx"))
    )
    caminho_config_precificacao: Path = Path(
        os.environ.get("ORCAMENTO_CONFIG_PRECIFICACAO", str(_DIR_PROJETO / "config" / "precificacao.json"))
    )

    def validar_api_key(self) -> None:
        if not self.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY nao configurada. Defina a variavel de ambiente antes de "
                "iniciar a API -- nunca coloque a chave direto no codigo ou em arquivo versionado."
            )


settings = Settings()
