"""Fixtures compartilhados. engine/ e extractors/ nao sao pacotes Python
formais (sem __init__.py) e os modulos de engine/ se importam entre si com
nomes soltos (ex: 'from tabela_precos import ...'), entao replicamos aqui o
mesmo truque de sys.path que api/services/pricing_service.py ja usa."""
from __future__ import annotations

import sys
from pathlib import Path

DIR_PROJETO = Path(__file__).resolve().parent.parent
DIR_ENGINE = DIR_PROJETO / "engine"
DIR_EXTRACTORS = DIR_PROJETO / "extractors"
DIR_ARQUIVOS_EXEMPLO = Path(__file__).resolve().parent / "arquivos_exemplo"

for _dir in (DIR_PROJETO, DIR_ENGINE, DIR_EXTRACTORS):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

import pytest


@pytest.fixture
def dir_arquivos_exemplo() -> Path:
    return DIR_ARQUIVOS_EXEMPLO


@pytest.fixture
def caminho_quarto_maria_xml() -> Path:
    return DIR_ARQUIVOS_EXEMPLO / "Paula_e_Gabriel__Quarto_Maria.xml"


@pytest.fixture
def caminho_pdf_cozinha() -> Path:
    return DIR_ARQUIVOS_EXEMPLO / "silvana_helio" / "Cozinha_e_Area_Servico.pdf"


@pytest.fixture
def caminho_pdf_banheiro() -> Path:
    return DIR_ARQUIVOS_EXEMPLO / "silvana_helio" / "Banheiro.pdf"


@pytest.fixture
def caminho_dwg_amostra() -> Path:
    return DIR_ARQUIVOS_EXEMPLO / "libredwg_amostra" / "example_2013.dwg"


@pytest.fixture
def caminho_tabela_precos_real() -> Path:
    return DIR_PROJETO / "config" / "tabela_precos_referencia.xlsx"


@pytest.fixture
def caminho_config_precificacao() -> Path:
    return DIR_PROJETO / "config" / "precificacao.json"
