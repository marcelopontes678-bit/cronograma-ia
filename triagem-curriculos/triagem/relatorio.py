"""Ranking e relatórios (CSV para planilha, HTML para ler e decidir)."""

from __future__ import annotations

import csv
from datetime import datetime
from html import escape
from pathlib import Path

from .modelos import Candidato, ResumoVagaIA, Vaga


def ranking(vaga: Vaga, candidatos: list[Candidato]) -> tuple[list[Candidato], list[Candidato]]:
    """(aprovados no filtro ordenados por nota, reprovados ordenados por nota)."""
    avaliados = [c for c in candidatos if vaga.id in c.resultados and c.analise and c.analise.e_curriculo]
    chave = lambda c: (-c.resultados[vaga.id].nota, c.arquivo)  # noqa: E731
    aprovados = sorted((c for c in avaliados if c.resultados[vaga.id].aprovado_filtro), key=chave)
    reprovados = sorted((c for c in avaliados if not c.resultados[vaga.id].aprovado_filtro), key=chave)
    return aprovados, reprovados


def salvar_csv(caminho: Path, vagas: list[Vaga], candidatos: list[Candidato]) -> None:
    with caminho.open("w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig: Excel abre acentos certo
        w = csv.writer(f, delimiter=";")
        w.writerow(
            ["vaga", "posicao", "status", "nota", "arquivo", "nome", "email", "telefone",
             "cidade", "anos_experiencia", "obrigatorios_faltando", "resumo_perfil"]
        )
        for vaga in vagas:
            aprovados, reprovados = ranking(vaga, candidatos)
            for pos, c in enumerate(aprovados + reprovados, start=1):
                r = c.resultados[vaga.id]
                ct = c.analise.contato
                w.writerow(
                    [vaga.titulo, pos if r.aprovado_filtro else "", "aprovado" if r.aprovado_filtro else "filtrado",
                     r.nota, c.arquivo, ct.nome, ct.email, ct.telefone, ct.cidade,
                     c.analise.anos_experiencia, " | ".join(r.obrigatorios_faltando), c.analise.resumo_perfil]
                )


CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#1c1c1e;line-height:1.5}
h1{margin-bottom:.2rem}h2{margin-top:3rem;border-bottom:2px solid #e5e5ea;padding-bottom:.3rem}
.sub{color:#6e6e73;margin-top:0}.aviso{background:#fff8e6;border:1px solid #f0d58a;padding:.8rem 1rem;border-radius:8px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1rem}
.card{border:1px solid #e5e5ea;border-radius:10px;padding:1rem}.card h4{margin:.2rem 0}
.nota{font-weight:700;font-size:1.1rem}.tag{display:inline-block;font-size:.8rem;padding:.1rem .5rem;border-radius:99px;background:#eef}
table{border-collapse:collapse;width:100%;font-size:.92rem}th,td{text-align:left;padding:.45rem;border-bottom:1px solid #eee;vertical-align:top}
th{background:#f5f5f7}.sim{color:#1a7f37}.parcial{color:#9a6700}.nao{color:#cf222e}details{margin:.3rem 0}
small{color:#6e6e73}
"""


def _itens(itens) -> str:
    return "".join(
        f"<li class='{i.atendido}'><b>{escape(i.atendido)}</b> — {escape(i.requisito)}"
        f"{' <small>(' + escape(i.evidencia) + ')</small>' if i.evidencia else ''}</li>"
        for i in itens
    )


def _detalhe(c: Candidato, vaga: Vaga) -> str:
    r = c.resultados[vaga.id]
    a = r.avaliacao
    fortes = "".join(f"<li>{escape(p)}</li>" for p in a.pontos_fortes)
    atencao = "".join(f"<li>{escape(p)}</li>" for p in a.pontos_de_atencao)
    return (
        f"<details><summary>ver detalhes</summary>"
        f"<p>{escape(c.analise.resumo_perfil)}</p>"
        f"<b>Obrigatórios</b><ul>{_itens(a.obrigatorios)}</ul>"
        f"<b>Desejáveis</b><ul>{_itens(a.desejaveis)}</ul>"
        f"<b>Pontos fortes</b><ul>{fortes}</ul><b>Pontos de atenção</b><ul>{atencao}</ul></details>"
    )


def _contato(c: Candidato) -> str:
    ct = c.analise.contato
    partes = [p for p in (ct.email, ct.telefone, ct.cidade) if p]
    return escape(" · ".join(partes))


def salvar_html(
    caminho: Path,
    vagas: list[Vaga],
    candidatos: list[Candidato],
    resumos: dict[str, ResumoVagaIA | str],
) -> None:
    total = len(candidatos)
    erros = [c for c in candidatos if c.erro]
    nao_curriculo = [c for c in candidatos if c.analise and not c.analise.e_curriculo]
    partes = [
        "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>Triagem de currículos</title><style>{CSS}</style></head><body>",
        "<h1>Triagem de currículos</h1>",
        f"<p class='sub'>{total} arquivo(s) · {len(vagas)} vaga(s) · gerado em "
        f"{datetime.now():%d/%m/%Y %H:%M}</p>",
        "<p class='aviso'>Esta é uma <b>pré-triagem</b> feita por IA para economizar tempo. "
        "Ela sugere quem entrevistar primeiro; a decisão é sempre de uma pessoa. "
        "Antes de descartar alguém filtrado, confira o motivo na tabela.</p>",
    ]
    for vaga in vagas:
        aprovados, reprovados = ranking(vaga, candidatos)
        partes.append(f"<h2>{escape(vaga.titulo)}</h2>")
        partes.append(
            f"<p class='sub'>{len(aprovados)} passaram no filtro de requisitos obrigatórios · "
            f"{len(reprovados)} filtrados</p>"
        )
        resumo = resumos.get(vaga.id)
        if isinstance(resumo, str):
            partes.append(f"<p class='aviso'>Resumo indisponível: {escape(resumo)}</p>")
        elif resumo:
            partes.append(f"<h3>Quem entrevistar</h3><p>{escape(resumo.visao_geral)}</p><div class='cards'>")
            por_arquivo = {c.arquivo: c for c in aprovados}
            for d in resumo.candidatos:
                c = por_arquivo.get(d.arquivo)
                if not c:
                    continue
                perguntas = "".join(f"<li>{escape(p)}</li>" for p in d.perguntas_entrevista)
                partes.append(
                    f"<div class='card'><span class='nota'>{c.resultados[vaga.id].nota}</span>/100 "
                    f"<h4>{escape(c.analise.contato.nome or c.arquivo)}</h4><small>{_contato(c)}</small>"
                    f"<p>{escape(d.resumo)}</p><p><b>Por que entrevistar:</b> {escape(d.por_que_entrevistar)}</p>"
                    f"<p><b>Confirmar na entrevista:</b> {escape(d.riscos)}</p>"
                    f"<b>Perguntas sugeridas</b><ol>{perguntas}</ol></div>"
                )
            partes.append("</div>")

        partes.append("<h3>Ranking completo</h3><table><tr><th>#</th><th>Candidato</th><th>Nota</th>"
                      "<th>Status</th><th>Análise</th></tr>")
        for pos, c in enumerate(aprovados + reprovados, start=1):
            r = c.resultados[vaga.id]
            status = ("<span class='tag'>aprovado</span>" if r.aprovado_filtro else
                      "<span class='nao'>falta: " + escape("; ".join(r.obrigatorios_faltando)) + "</span>")
            partes.append(
                f"<tr><td>{pos if r.aprovado_filtro else '—'}</td>"
                f"<td><b>{escape(c.analise.contato.nome or '(sem nome)')}</b><br><small>{escape(c.arquivo)}"
                f"<br>{_contato(c)}</small></td><td class='nota'>{r.nota}</td><td>{status}</td>"
                f"<td>{_detalhe(c, vaga)}</td></tr>"
            )
        partes.append("</table>")

    if erros or nao_curriculo:
        partes.append("<h2>Arquivos que precisam de olho humano</h2><ul>")
        for c in erros:
            partes.append(f"<li><b>{escape(c.arquivo)}</b>: {escape(c.erro)}</li>")
        for c in nao_curriculo:
            partes.append(f"<li><b>{escape(c.arquivo)}</b>: a IA não reconheceu como currículo.</li>")
        partes.append("</ul>")
    partes.append("</body></html>")
    caminho.write_text("".join(partes), encoding="utf-8")
