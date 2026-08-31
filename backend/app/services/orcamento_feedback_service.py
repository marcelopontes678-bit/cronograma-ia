"""Auto-aprendizado: o marceneiro corrige uma leitura do MARC em linguagem
natural (ex: "Sempre que houver porta de vidro reflecta, mude o fundo
para a cor da caixa"); isso e normalizado pela LLM em uma regra reusavel
e injetado no system prompt do agente extrator nas proximas execucoes
DESSA empresa.

Design consciente: a regra fica em linguagem natural (nao em codigo),
porque e isso que o prompt do extrator consome -- nao precisa de um motor
de regras separado, so precisa ser persistida e injetada. Diferente do
protótipo standalone (arquivo JSON por usuario), aqui e Postgres, uma
tabela por empresa/usuario, com soft delete via `is_active`."""
from __future__ import annotations

import asyncio
import uuid

from anthropic import Anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import not_found
from app.models.orcamento import RegraAprendida
from app.models.usuario import Usuario
from app.schemas.orcamento import FeedbackRequest

MODELO_PADRAO = "claude-sonnet-5"

_SYSTEM_PROMPT_NORMALIZACAO = """\
Voce reescreve uma correcao informal de um marceneiro sobre a leitura de \
projetos de marcenaria (feita por um extrator de IA) numa REGRA DE SISTEMA \
reusavel, objetiva e sem ambiguidade -- para ser injetada no prompt de um \
agente extrator em execucoes futuras.

Regras de estilo:
- Uma frase imperativa, comecando com "Quando..." ou "Sempre que...".
- Sem referencia a um projeto/modulo especifico (generalize).
- Sem inventar excecoes ou condicoes que o usuario nao mencionou.
- Se a instrucao do usuario for ambigua ou nao fizer sentido como regra \
geral, responda exatamente com a instrucao original sem reescrever \
(nao tente adivinhar a intencao).

Responda APENAS com a regra reescrita, sem explicacoes."""


class FeedbackInvalidoError(Exception):
    pass


def _normalizar_instrucao_via_llm_sync(instrucao: str, api_key: str, modelo: str) -> str:
    client = Anthropic(api_key=api_key)
    resposta = client.messages.create(
        model=modelo,
        max_tokens=300,
        system=_SYSTEM_PROMPT_NORMALIZACAO,
        messages=[{"role": "user", "content": instrucao}],
    )
    blocos_texto = [b.text for b in resposta.content if b.type == "text"]
    if not blocos_texto:
        raise FeedbackInvalidoError(f"Claude nao retornou texto ao normalizar a instrucao: {resposta.content}")
    return "".join(blocos_texto).strip()


async def registrar_feedback(
    db: AsyncSession,
    current_user: Usuario,
    request: FeedbackRequest,
    api_key: str,
    modelo: str = MODELO_PADRAO,
) -> tuple[RegraAprendida, int]:
    """Chama o Claude via asyncio.to_thread -- o SDK e sincrono, e rodar
    direto aqui bloquearia o event loop pro resto das requisicoes."""
    try:
        regra_normalizada = await asyncio.to_thread(
            _normalizar_instrucao_via_llm_sync, request.instrucao, api_key, modelo
        )
    except FeedbackInvalidoError:
        raise
    except Exception as exc:  # falha de rede/API -- nao mascarar
        raise FeedbackInvalidoError(f"empresa={current_user.empresa_id}: falha ao normalizar instrucao via LLM: {exc}") from exc

    nova_regra = RegraAprendida(
        empresa_id=current_user.empresa_id,
        usuario_id=current_user.id,
        instrucao_original=request.instrucao,
        regra_normalizada=regra_normalizada,
        origem_job_id=request.job_id,
        origem_modulo_id=request.modulo_id,
    )
    db.add(nova_regra)
    await db.commit()
    await db.refresh(nova_regra)

    total_ativas = await _contar_regras_ativas(db, current_user)
    return nova_regra, total_ativas


async def _contar_regras_ativas(db: AsyncSession, current_user: Usuario) -> int:
    result = await db.execute(
        select(RegraAprendida).where(
            RegraAprendida.empresa_id == current_user.empresa_id,
            RegraAprendida.is_active.is_(True),
        )
    )
    return len(result.scalars().all())


async def listar_regras(db: AsyncSession, current_user: Usuario) -> list[RegraAprendida]:
    """Todas as regras (ativas e desativadas), para o marceneiro revisar."""
    result = await db.execute(
        select(RegraAprendida)
        .where(RegraAprendida.empresa_id == current_user.empresa_id)
        .order_by(RegraAprendida.created_at.desc())
    )
    return list(result.scalars().all())


async def listar_regras_normalizadas_ativas(db: AsyncSession, empresa_id: uuid.UUID) -> list[str]:
    """Usado por orcamento_service.py para montar o system prompt do MARC
    -- so o texto das regras ativas, na ordem em que foram criadas."""
    result = await db.execute(
        select(RegraAprendida)
        .where(RegraAprendida.empresa_id == empresa_id, RegraAprendida.is_active.is_(True))
        .order_by(RegraAprendida.created_at.asc())
    )
    return [r.regra_normalizada for r in result.scalars().all()]


async def desativar_regra(db: AsyncSession, current_user: Usuario, regra_id: uuid.UUID) -> RegraAprendida:
    """Soft delete -- nunca remove do historico, so marca is_active=False."""
    result = await db.execute(select(RegraAprendida).where(RegraAprendida.id == regra_id))
    regra = result.scalar_one_or_none()
    if not regra or regra.empresa_id != current_user.empresa_id:
        raise not_found("Regra aprendida")

    regra.is_active = False
    await db.commit()
    await db.refresh(regra)
    return regra
