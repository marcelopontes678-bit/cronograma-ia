"""Converte arquivos DWG para DXF usando o ODA File Converter (linha de comando),
para depois alimentar o extractor de geometria Promob (extract_promob_dxf.py).

Este skill NUNCA faz parsing de DWG binario diretamente - o formato DWG e
proprietario da Autodesk e sua leitura direta e proibida pelas regras do
projeto. Toda conversao passa pelo ODA File Converter (gratuito, da Open
Design Alliance), que gera um DXF equivalente.

INSTALACAO DO ODA FILE CONVERTER (manual, obrigatoria antes de usar este script):
  1. Baixe em https://www.opendesign.com/guestfiles/oda_file_converter
     (exige aceitar os termos de uso no site - nao pode ser automatizado).
  2. Instale o pacote para Linux (.deb) ou Windows/Mac conforme seu sistema.
  3. Confirme o caminho do executavel (no Linux normalmente algo como
     /opt/ODA/ODAFileConverter_QT6_lnxX64_.../ODAFileConverter, no Windows
     "C:\\Program Files\\ODA\\...\\ODAFileConverter.exe").
  4. Informe esse caminho via --oda-path ou na variavel de ambiente
     ODA_FILE_CONVERTER_PATH.

Interface de linha de comando do ODA File Converter (documentada pela ODA):
  ODAFileConverter <pasta_entrada> <pasta_saida> <versao_saida> <tipo_saida> <recursivo> <auditoria> [filtro]
  Exemplo: ODAFileConverter ./in ./out ACAD2018 DXF 0 1 "*.dwg"

Este wrapper roda em modo headless (sem interface grafica) chamando o
executavel via subprocess, converte um unico arquivo DWG por vez (copia
para uma pasta temporaria de entrada) e retorna o caminho do DXF gerado.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class ODAConverterNaoEncontradoError(Exception):
    pass


class ConversaoFalhouError(Exception):
    pass


def localizar_oda_converter(caminho_informado: str | None = None) -> str:
    candidato = caminho_informado or os.environ.get("ODA_FILE_CONVERTER_PATH")
    if candidato and Path(candidato).exists():
        return candidato

    candidato_no_path = shutil.which("ODAFileConverter")
    if candidato_no_path:
        return candidato_no_path

    raise ODAConverterNaoEncontradoError(
        "ODA File Converter nao encontrado. Instale manualmente a partir de "
        "https://www.opendesign.com/guestfiles/oda_file_converter e informe o "
        "caminho via --oda-path ou variavel de ambiente ODA_FILE_CONVERTER_PATH. "
        "Este skill nunca faz parsing de DWG binario sem essa conversao previa."
    )


def converter_dwg_para_dxf(
    caminho_dwg: str | Path,
    pasta_saida: str | Path,
    oda_path: str | None = None,
    versao_dxf: str = "ACAD2018",
    timeout_segundos: int = 60,
) -> Path:
    caminho_dwg = Path(caminho_dwg)
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    if not caminho_dwg.exists():
        raise FileNotFoundError(f"Arquivo DWG nao encontrado: {caminho_dwg}")

    oda_exe = localizar_oda_converter(oda_path)

    with tempfile.TemporaryDirectory() as pasta_entrada_temp:
        pasta_entrada_temp = Path(pasta_entrada_temp)
        dwg_copiado = pasta_entrada_temp / caminho_dwg.name
        shutil.copy(caminho_dwg, dwg_copiado)

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
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=timeout_segundos,
            )
        except subprocess.TimeoutExpired as exc:
            raise ConversaoFalhouError(
                f"ODA File Converter excedeu o tempo limite ({timeout_segundos}s) convertendo {caminho_dwg.name}."
            ) from exc

        dxf_esperado = pasta_saida / (caminho_dwg.stem + ".dxf")
        if resultado.returncode != 0 or not dxf_esperado.exists():
            raise ConversaoFalhouError(
                f"Falha ao converter {caminho_dwg.name}. "
                f"returncode={resultado.returncode}\nstdout={resultado.stdout}\nstderr={resultado.stderr}"
            )

        return dxf_esperado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Converte um DWG para DXF via ODA File Converter.")
    parser.add_argument("arquivo_dwg")
    parser.add_argument("--pasta-saida", default="output/dxf_convertido")
    parser.add_argument("--oda-path", default=None)
    parser.add_argument("--versao-dxf", default="ACAD2018")
    args = parser.parse_args()

    caminho_dxf = converter_dwg_para_dxf(
        args.arquivo_dwg,
        args.pasta_saida,
        oda_path=args.oda_path,
        versao_dxf=args.versao_dxf,
    )
    print(f"DXF gerado: {caminho_dxf}")
