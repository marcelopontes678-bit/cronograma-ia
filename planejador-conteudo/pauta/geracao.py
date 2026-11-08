"""Job de geração de plano.

Hoje roda como BackgroundTask do FastAPI, no mesmo processo. Como todo o estado
fica na tabela `planos` (status pendente → gerando → pronto/erro), dá para trocar
por uma fila (worker separado lendo planos pendentes) sem mudar a API.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from .ia import ErroIA, Gerador, data_do_post
from .modelos import Marca, Plano, Post

log = logging.getLogger("pauta.geracao")


def planos_no_mes(db: Session, usuario_id: str) -> int:
    agora = datetime.now(timezone.utc)
    inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return db.scalar(
        select(func.count(Plano.id)).where(
            Plano.usuario_id == usuario_id, Plano.criado_em >= inicio_mes, Plano.status != "erro"
        )
    ) or 0


def executar_geracao(plano_id: str, gerador: Gerador, fabrica: sessionmaker[Session]) -> None:
    with fabrica() as db:
        plano = db.get(Plano, plano_id)
        if plano is None or plano.status != "pendente":
            return
        plano.status = "gerando"
        plano.modelo = gerador.modelo
        db.commit()
        marca = db.get(Marca, plano.marca_id)

        try:
            resultado, uso = gerador.gerar_plano(marca, plano)
        except ErroIA as e:
            _falhar(db, plano, str(e))
            return
        except Exception:
            log.exception("Erro inesperado gerando o plano %s", plano_id)
            _falhar(db, plano, "Erro inesperado ao gerar o plano. Tente de novo.")
            return

        permitidas = set(plano.plataformas)
        total_dias = plano.semanas * 7
        posts = [p for p in resultado.posts if p.plataforma in permitidas]
        if not posts:
            _falhar(db, plano, "A IA não devolveu posts para as plataformas pedidas. Tente de novo.")
            return

        for ordem, p in enumerate(posts):
            db.add(
                Post(
                    plano_id=plano.id,
                    marca_id=plano.marca_id,
                    data=data_do_post(plano.data_inicio, p.dia, total_dias),
                    ordem=ordem,
                    plataforma=p.plataforma,
                    formato=p.formato,
                    pilar=p.pilar[:120],
                    titulo=p.titulo[:200],
                    gancho=p.gancho,
                    roteiro=p.roteiro,
                    legenda=p.legenda,
                    hashtags=[h.lstrip("#").strip() for h in p.hashtags if h.strip()][:30],
                    cta=p.cta,
                )
            )
        plano.estrategia = resultado.estrategia
        plano.tokens_entrada = uso.entrada
        plano.tokens_saida = uso.saida
        plano.status = "pronto"
        plano.concluido_em = datetime.now(timezone.utc)
        db.commit()


def _falhar(db: Session, plano: Plano, mensagem: str) -> None:
    plano.status = "erro"
    plano.erro = mensagem
    plano.concluido_em = datetime.now(timezone.utc)
    db.commit()


TEMPO_MAXIMO_GERACAO = timedelta(minutes=15)


def expirar_se_travado(db: Session, plano: Plano) -> None:
    """Se o processo caiu no meio da geração, o plano ficaria "gerando" para sempre.

    Checado na leitura (e não na subida do servidor) para funcionar com várias instâncias.
    """
    if plano.status not in ("pendente", "gerando"):
        return
    criado = plano.criado_em if plano.criado_em.tzinfo else plano.criado_em.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - criado > TEMPO_MAXIMO_GERACAO:
        _falhar(db, plano, "A geração foi interrompida. Gere de novo.")
