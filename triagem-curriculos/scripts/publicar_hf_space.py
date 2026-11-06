"""Publica a tela web da triagem num Hugging Face Space (Docker, gratuito).

O Space recebe só o necessário para rodar: Dockerfile, requirements.txt, a
pasta triagem/ e o README do Space (deploy/huggingface/README.md). Nada de
testes, exemplos ou dados.

Uso:
    pip install huggingface_hub
    export HF_TOKEN=hf_...          # token com permissão de escrita
    python scripts/publicar_hf_space.py --space triagem-curriculos

    python scripts/publicar_hf_space.py --pasta /tmp/space   # só monta, não envia

Os segredos NÃO passam por este script: depois de publicar, cadastre
ANTHROPIC_API_KEY e TRIAGEM_SENHA em Settings → Variables and secrets do Space.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVOS = ["Dockerfile", "requirements.txt"]
CARD = RAIZ / "deploy" / "huggingface" / "README.md"


def montar(destino: Path) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    for nome in ARQUIVOS:
        shutil.copy(RAIZ / nome, destino / nome)
    shutil.copy(CARD, destino / "README.md")
    shutil.copytree(
        RAIZ / "triagem",
        destino / "triagem",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    return destino


def publicar(space: str, privado: bool) -> None:
    from huggingface_hub import HfApi

    api = HfApi()
    usuario = api.whoami()["name"]
    repo_id = space if "/" in space else f"{usuario}/{space}"
    api.create_repo(repo_id, repo_type="space", space_sdk="docker", private=privado, exist_ok=True)
    # Não é segredo: só obriga o app a ter senha antes de abrir.
    api.add_space_variable(repo_id, "TRIAGEM_EXIGIR_SENHA", "1")
    with tempfile.TemporaryDirectory() as tmp:
        api.upload_folder(
            repo_id=repo_id,
            repo_type="space",
            folder_path=str(montar(Path(tmp))),
            commit_message="Publica a triagem de currículos",
            delete_patterns=["triagem/**"],  # remove arquivos que deixaram de existir
        )
    dono, nome = repo_id.split("/")
    print(f"Space:          https://huggingface.co/spaces/{repo_id}")
    print(f"Endereço do app: https://{dono}-{nome}.hf.space".lower().replace("_", "-"))
    print("Falta: cadastrar ANTHROPIC_API_KEY e TRIAGEM_SENHA em Settings → Variables and secrets.")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--space", default="triagem-curriculos", help="nome do Space (ou usuario/nome)")
    p.add_argument("--privado", action="store_true", help="Space privado (só quem tem acesso no HF vê)")
    p.add_argument("--pasta", help="só monta os arquivos nesta pasta, sem enviar")
    args = p.parse_args()
    if args.pasta:
        print(f"Montado em {montar(Path(args.pasta))}")
    else:
        publicar(args.space, args.privado)


if __name__ == "__main__":
    main()
