"""Uso:
    python -m triagem --vagas vagas.json --curriculos pasta/ [--saida saida/] [--top 5]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import anthropic
from pydantic import TypeAdapter

from .ia import MODELO_PADRAO, Triador
from .leitura import Documento, ler, listar_curriculos
from .modelos import Candidato, Vaga
from .relatorio import ranking, salvar_csv, salvar_html


def carregar_vagas(caminho: Path) -> list[Vaga]:
    vagas = TypeAdapter(list[Vaga]).validate_python(json.loads(caminho.read_text(encoding="utf-8")))
    if not vagas:
        raise SystemExit("O arquivo de vagas está vazio.")
    ids = [v.id for v in vagas]
    if len(ids) != len(set(ids)):
        raise SystemExit("Há vagas com o mesmo id.")
    return vagas


async def executar(args) -> int:
    vagas = carregar_vagas(Path(args.vagas))
    arquivos = listar_curriculos(Path(args.curriculos))
    if not arquivos:
        print(f"Nenhum currículo (.pdf, .docx, .txt, .md) em {args.curriculos}", file=sys.stderr)
        return 1
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    triador = Triador(
        vagas,
        modelo=args.modelo,
        concorrencia=args.concorrencia,
        pasta_cache=None if args.sem_cache else saida / ".cache",
    )

    print(f"Fase 1: analisando {len(arquivos)} currículo(s) para {len(vagas)} vaga(s)...")
    feitos = 0

    async def um(caminho: Path) -> Candidato:
        nonlocal feitos
        try:
            doc = ler(caminho)
        except Exception as e:  # arquivo corrompido não pode derrubar os outros 199
            doc = None
            c = Candidato(arquivo=caminho.name, erro=f"Não foi possível ler o arquivo: {e}")
        if doc is not None:
            c = await triador.analisar(doc)
        feitos += 1
        print(f"  [{feitos}/{len(arquivos)}] {caminho.name}{'  ⚠ ' + c.erro if c.erro else ''}")
        return c

    candidatos = await asyncio.gather(*(um(p) for p in arquivos))

    print(f"Fase 2: resumindo os {args.top} melhores de cada vaga...")
    resumos: dict = {}

    async def resumo(vaga: Vaga):
        aprovados, _ = ranking(vaga, candidatos)
        if not aprovados or args.top <= 0:
            return
        try:
            resumos[vaga.id] = await triador.resumir_vaga(vaga, aprovados[: args.top])
        except Exception as e:
            resumos[vaga.id] = str(e)

    await asyncio.gather(*(resumo(v) for v in vagas))

    salvar_csv(saida / "ranking.csv", vagas, candidatos)
    salvar_html(saida / "relatorio.html", vagas, candidatos, resumos)

    print("\nResultado:")
    for vaga in vagas:
        aprovados, reprovados = ranking(vaga, candidatos)
        print(f"  {vaga.titulo}: {len(aprovados)} aprovados no filtro, {len(reprovados)} filtrados")
        for pos, c in enumerate(aprovados[: args.top], start=1):
            print(f"    {pos}. {c.analise.contato.nome or c.arquivo} — {c.resultados[vaga.id].nota}/100")
    com_erro = sum(1 for c in candidatos if c.erro)
    if com_erro:
        print(f"  ⚠ {com_erro} arquivo(s) com problema — veja o fim do relatório.")
    print(f"\nRelatório: {saida / 'relatorio.html'}\nPlanilha:  {saida / 'ranking.csv'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="triagem", description="Triagem de currículos com IA para empresas sem RH.")
    p.add_argument("--vagas", required=True, help="JSON com as vagas (veja vagas.exemplo.json)")
    p.add_argument("--curriculos", required=True, help="Pasta com os currículos (.pdf, .docx, .txt, .md)")
    p.add_argument("--saida", default="saida", help="Pasta de saída (padrão: saida/)")
    p.add_argument("--top", type=int, default=5, help="Quantos melhores resumir por vaga (padrão: 5)")
    p.add_argument("--modelo", default=MODELO_PADRAO, help=f"Modelo do Claude (padrão: {MODELO_PADRAO})")
    p.add_argument("--concorrencia", type=int, default=5, help="Currículos analisados ao mesmo tempo (padrão: 5)")
    p.add_argument("--sem-cache", action="store_true", help="Reanalisa tudo, ignorando o cache")
    args = p.parse_args(argv)
    try:
        return asyncio.run(executar(args))
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
        print(f"Erro de autenticação na API do Claude: confira a ANTHROPIC_API_KEY. ({e})", file=sys.stderr)
        return 2
