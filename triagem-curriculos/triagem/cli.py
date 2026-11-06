"""Uso:
    python -m triagem --vagas vagas.json --curriculos pasta/ [--saida saida/] [--top 5]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import anthropic

from .ia import MODELO_PADRAO
from .leitura import listar_curriculos
from .modelos import Candidato
from .pipeline import VagasInvalidas, carregar_vagas, triar
from .relatorio import ranking


async def executar(args) -> int:
    try:
        vagas = carregar_vagas(Path(args.vagas))
    except VagasInvalidas as e:
        print(e, file=sys.stderr)
        return 1
    arquivos = listar_curriculos(Path(args.curriculos))
    if not arquivos:
        print(f"Nenhum currículo (.pdf, .docx, .txt, .md) em {args.curriculos}", file=sys.stderr)
        return 1
    saida = Path(args.saida)

    def progresso(feitos: int, total: int, c: Candidato) -> None:
        print(f"  [{feitos}/{total}] {c.arquivo}{'  ⚠ ' + c.erro if c.erro else ''}")

    print(f"Fase 1: analisando {len(arquivos)} currículo(s) para {len(vagas)} vaga(s)...")
    candidatos = await triar(
        vagas, arquivos, saida,
        top=args.top, modelo=args.modelo, concorrencia=args.concorrencia,
        usar_cache=not args.sem_cache, ao_progredir=progresso,
        ao_resumir=lambda: print(f"Fase 2: resumindo os {args.top} melhores de cada vaga..."),
    )

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
