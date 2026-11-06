"""Monta uma "caixa de entrada" de teste com currículos públicos da internet.

Fontes (nenhuma expõe pessoas reais):
- teixeira-alberto/RH-curriculos-dataset-v2 (Hugging Face): currículos 100%
  SINTÉTICOS em PT-BR, estilo LinkedIn. Nomes e empresas são gerados.
- opensporks/resumes (Hugging Face, licença CC0): PDFs reais do LiveCareer,
  já anonimizados, em inglês. Servem para testar a leitura de PDF.

Mistura candidatos adequados às vagas de `vagas.teste.json` com perfis
totalmente fora (juiz, engenheiro de ML...), como numa caixa de entrada real,
e grava `gabarito.json` com o perfil de cada arquivo, para conferir o ranking.

Uso:
    pip install pyarrow
    python scripts/baixar_curriculos_teste.py            # grava em teste_real/curriculos
    python -m triagem --vagas vagas.teste.json --curriculos teste_real/curriculos --saida teste_real/saida
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import unicodedata
import urllib.request
from pathlib import Path

HF = "https://huggingface.co/datasets"
PT_PARQUET = f"{HF}/teixeira-alberto/RH-curriculos-dataset-v2/resolve/main/data/train-00000-of-00001.parquet"
LIVECAREER = f"{HF}/opensporks/resumes/resolve/main/data/data"
PDFS = ["ACCOUNTANT/10554236", "BANKING/27120528", "BPO/11183737", "BPO/13964744", "BUSINESS-DEVELOPMENT/10228751"]

# grupo -> (regex no cargo do candidato, quantidade)
GRUPOS = {
    "atendimento": (r"atendente|recepcionista|balconista|vendedor|operador de caixa", 12),
    "admin": (r"^(auxiliar de escrit|auxiliar administrativ|assistente administrativ|auxiliar financeir|"
              r"assistente financeir|auxiliar de contabilidade|analista de departamento pessoal)", 10),
    "vendas": (r"\bSDR\b|inside sales|executivo de vendas|representante comercial|Sales Development", 8),
    "fora": (r"juiz|engenheiro de machine|arquiteto de software|coreografia|instalador|diretor de arte|"
             r"supervisor de explora", 10),
}


def slug(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")[:40]


def baixar(url: str, destino: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as r, destino.open("wb") as f:
        shutil.copyfileobj(r, f)


def main() -> None:
    import pyarrow.parquet as pq

    p = argparse.ArgumentParser()
    p.add_argument("--saida", default="teste_real")
    p.add_argument("--semente", type=int, default=7)
    args = p.parse_args()
    raiz = Path(args.saida)
    pasta = raiz / "curriculos"
    pasta.mkdir(parents=True, exist_ok=True)
    random.seed(args.semente)

    parquet = raiz / "pt.parquet"
    if not parquet.exists():
        print("Baixando currículos sintéticos em PT-BR (~30 MB)...")
        baixar(PT_PARQUET, parquet)
    linhas = []
    for conversa in pq.read_table(parquet).column("conversations").to_pylist():
        d = {m["role"]: m["content"] for m in conversa}
        dados = json.loads(d["assistant"])
        if "Experiência" in d["user"] or "Resumo" in d["user"]:
            linhas.append((d["user"], dados))

    gabarito = {}
    for grupo, (padrao, n) in GRUPOS.items():
        escolhidos = [l for l in linhas if re.search(padrao, l[1].get("headline", ""), re.I)]
        random.shuffle(escolhidos)
        for texto, dados in escolhidos[:n]:
            nome = f"{slug(dados['name'])}.txt"
            if nome in gabarito:
                continue
            (pasta / nome).write_text(texto, encoding="utf-8")
            gabarito[nome] = {"grupo": grupo, "cargo": dados.get("headline", "")}

    print("Baixando PDFs anonimizados (CC0)...")
    for pdf in PDFS:
        nome = f"livecareer_{slug(pdf)}.pdf"
        baixar(f"{LIVECAREER}/{pdf}.pdf", pasta / nome)
        gabarito[nome] = {"grupo": "pdf_ingles", "cargo": pdf.split("/")[0].lower()}

    # Pegadinhas do próprio projeto: tentativa de manipular a IA e arquivo que não é currículo.
    exemplos = Path(__file__).resolve().parent.parent / "exemplos" / "curriculos"
    for nome, grupo in [("diego_rocha.txt", "injecao"), ("lista_compras.txt", "nao_curriculo")]:
        shutil.copy(exemplos / nome, pasta / nome)
        gabarito[nome] = {"grupo": grupo, "cargo": ""}

    (raiz / "gabarito.json").write_text(json.dumps(gabarito, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(gabarito)} arquivos em {pasta}  (gabarito em {raiz / 'gabarito.json'})")


if __name__ == "__main__":
    main()
