"""Converte arquivos DWG para DXF, para depois alimentar o extractor de
geometria Promob (extract_promob_dxf.py).

Este skill NUNCA faz parsing de DWG binario diretamente - o formato DWG e
proprietario da Autodesk e sua leitura direta e proibida pelas regras do
projeto. Toda conversao passa por um conversor DWG->DXF externo.

Dois motores suportados, com deteccao automatica (nesta ordem de preferencia):

1. LIBREDWG (dwg2dxf) - RECOMENDADO PARA MVP SELF-HOSTED
   100% open-source (GPL), sem clique de EULA, compilavel direto num
   Dockerfile do backend -- ideal quando a conversao precisa rodar sozinha
   no servidor, sem depender de uma maquina Windows/humano por conversao.
   Instalacao (Linux, dentro do container do backend):
     git clone https://github.com/LibreDWG/libredwg.git
     cd libredwg && ./autogen.sh && ./configure --disable-bindings && make && make install
   (ou pacote pronto da distro, quando disponivel: apt install libredwg-tools)
   CLI: dwg2dxf [-o saida.dxf] entrada.dwg

2. ODA FILE CONVERTER - alternativa/legado
   Gratuito, da Open Design Alliance, mas exige aceitar EULA manualmente no
   site (nao automatizavel) e rodar via GUI/headless por maquina:
   https://www.opendesign.com/guestfiles/oda_file_converter
   CLI: ODAFileConverter <pasta_entrada> <pasta_saida> <versao> DXF <recursivo> <auditoria>

Para o MVP, priorize o LibreDWG (motor "libredwg") self-hospedado. O ODA
fica como fallback para quem ja tem ele instalado localmente (ex: Windows).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class ConversorDwgNaoEncontradoError(Exception):
    pass


class ConversaoFalhouError(Exception):
    pass


def localizar_dwg2dxf(caminho_informado: str | None = None) -> str | None:
    candidato = caminho_informado or os.environ.get("DWG2DXF_PATH")
    if candidato and Path(candidato).exists():
        return candidato
    return shutil.which("dwg2dxf")


def localizar_oda_converter(caminho_informado: str | None = None) -> str | None:
    candidato = caminho_informado or os.environ.get("ODA_FILE_CONVERTER_PATH")
    if candidato and Path(candidato).exists():
        return candidato
    return shutil.which("ODAFileConverter")


def _converter_com_libredwg(
    caminho_dwg: Path,
    pasta_saida: Path,
    dwg2dxf_exe: str,
    timeout_segundos: int,
) -> Path:
    dxf_esperado = pasta_saida / (caminho_dwg.stem + ".dxf")
    comando = [dwg2dxf_exe, "-o", str(dxf_esperado), str(caminho_dwg)]

    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=timeout_segundos)
    except subprocess.TimeoutExpired as exc:
        raise ConversaoFalhouError(
            f"dwg2dxf (LibreDWG) excedeu o tempo limite ({timeout_segundos}s) convertendo {caminho_dwg.name}."
        ) from exc

    if resultado.returncode != 0 or not dxf_esperado.exists():
        raise ConversaoFalhouError(
            f"Falha ao converter {caminho_dwg.name} com dwg2dxf (LibreDWG). "
            f"returncode={resultado.returncode}\nstdout={resultado.stdout}\nstderr={resultado.stderr}"
        )
    return dxf_esperado


def _converter_com_oda(
    caminho_dwg: Path,
    pasta_saida: Path,
    oda_exe: str,
    versao_dxf: str,
    timeout_segundos: int,
) -> Path:
    with tempfile.TemporaryDirectory() as pasta_entrada_temp:
        pasta_entrada_temp = Path(pasta_entrada_temp)
        shutil.copy(caminho_dwg, pasta_entrada_temp / caminho_dwg.name)

        comando = [
            oda_exe,
            str(pasta_entrada_temp),
            str(pasta_saida),
            versao_dxf,
            "DXF",
            "0",  # nao recursivo
            "1",  # auditoria ligada
        ]

        try:
            resultado = subprocess.run(comando, capture_output=True, text=True, timeout=timeout_segundos)
        except subprocess.TimeoutExpired as exc:
            raise ConversaoFalhouError(
                f"ODA File Converter excedeu o tempo limite ({timeout_segundos}s) convertendo {caminho_dwg.name}."
            ) from exc

        dxf_esperado = pasta_saida / (caminho_dwg.stem + ".dxf")
        if resultado.returncode != 0 or not dxf_esperado.exists():
            raise ConversaoFalhouError(
                f"Falha ao converter {caminho_dwg.name} com ODA File Converter. "
                f"returncode={resultado.returncode}\nstdout={resultado.stdout}\nstderr={resultado.stderr}"
            )
        return dxf_esperado


def converter_dwg_para_dxf(
    caminho_dwg: str | Path,
    pasta_saida: str | Path,
    motor: str = "auto",
    dwg2dxf_path: str | None = None,
    oda_path: str | None = None,
    versao_dxf: str = "ACAD2018",
    timeout_segundos: int = 60,
) -> Path:
    """motor: 'auto' (tenta libredwg, depois oda), 'libredwg' ou 'oda'."""
    caminho_dwg = Path(caminho_dwg)
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    if not caminho_dwg.exists():
        raise FileNotFoundError(f"Arquivo DWG nao encontrado: {caminho_dwg}")

    dwg2dxf_exe = localizar_dwg2dxf(dwg2dxf_path)
    oda_exe = localizar_oda_converter(oda_path)

    if motor in ("auto", "libredwg") and dwg2dxf_exe:
        return _converter_com_libredwg(caminho_dwg, pasta_saida, dwg2dxf_exe, timeout_segundos)

    if motor in ("auto", "oda") and oda_exe:
        return _converter_com_oda(caminho_dwg, pasta_saida, oda_exe, versao_dxf, timeout_segundos)

    raise ConversorDwgNaoEncontradoError(
        "Nenhum conversor DWG->DXF encontrado. Para um MVP self-hosted, instale o LibreDWG "
        "(dwg2dxf) no backend -- veja instrucoes no topo deste arquivo -- e informe o caminho "
        "via --dwg2dxf-path ou variavel DWG2DXF_PATH. Alternativamente, instale o ODA File "
        "Converter (https://www.opendesign.com/guestfiles/oda_file_converter) e informe via "
        "--oda-path ou ODA_FILE_CONVERTER_PATH. Este skill nunca faz parsing de DWG binario "
        "sem essa conversao previa."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Converte um DWG para DXF (LibreDWG dwg2dxf, com fallback para ODA File Converter).")
    parser.add_argument("arquivo_dwg")
    parser.add_argument("--pasta-saida", default="output/dxf_convertido")
    parser.add_argument("--motor", choices=["auto", "libredwg", "oda"], default="auto")
    parser.add_argument("--dwg2dxf-path", default=None)
    parser.add_argument("--oda-path", default=None)
    parser.add_argument("--versao-dxf", default="ACAD2018")
    args = parser.parse_args()

    caminho_dxf = converter_dwg_para_dxf(
        args.arquivo_dwg,
        args.pasta_saida,
        motor=args.motor,
        dwg2dxf_path=args.dwg2dxf_path,
        oda_path=args.oda_path,
        versao_dxf=args.versao_dxf,
    )
    print(f"DXF gerado: {caminho_dxf}")
