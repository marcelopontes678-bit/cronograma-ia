"""FastAPI app. Rotas descritas em api/ROTAS.md -- este arquivo so amarra
HTTP <-> os services/schemas ja implementados e testados; nenhuma logica
de negocio nova mora aqui."""
from __future__ import annotations

import logging
import shutil
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF
from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from api.config import settings
from api.db import jobs as jobs_db
from api.schemas.extracao import ExtracaoResultado, Modulo, StatusExtracao
from api.schemas.feedback import FeedbackRequest
from api.schemas.orcamento import OrcamentoRequest, OrcamentoResponse
from api.schemas.preferencias import PreferenciasGlobais
from api.services import feedback_service, preferencias_service, pricing_service
from api.services.vision_extractor import ExtracaoVisionError, extrair_de_pdf

logger = logging.getLogger("orcamento_marcenaria.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Falha rapido e alto no startup em vez de subir uma API que so quebra
    # depois, dentro do background task de extracao (ver README secao 3.4) --
    # so roda quando o ASGI lifespan e de fato acionado (uvicorn, ou
    # `with TestClient(app) as client`), nao em testes que instanciam
    # TestClient(app) diretamente sem context manager.
    settings.validar_api_key()
    yield


app = FastAPI(title="Orcamento de Marcenaria - API", version="0.1.0", lifespan=lifespan)


# --------------------------------------------------------------------------
# Upload e extracao
# --------------------------------------------------------------------------

def _rodar_extracao_em_background(job_id: str, caminho_pdf: Path, pasta_trabalho: Path, usuario_id: str) -> None:
    try:
        preferencias = preferencias_service.carregar_preferencias(usuario_id, settings.dir_preferencias)
        regras_ativas = feedback_service.listar_regras_normalizadas_ativas(usuario_id, settings.dir_regras_aprendidas)

        resultado = extrair_de_pdf(
            job_id=job_id,
            caminho_pdf=caminho_pdf,
            pasta_trabalho=pasta_trabalho,
            preferencias=preferencias,
            regras_ativas=regras_ativas,
            api_key=settings.anthropic_api_key,
            modelo=settings.modelo_claude,
        )
    except ExtracaoVisionError as exc:
        logger.exception("job=%s: falha na extracao", job_id)
        resultado = ExtracaoResultado(
            job_id=job_id,
            arquivo_origem=caminho_pdf.name,
            status=StatusExtracao.ERRO,
            avisos=[f"Falha na extracao: {exc}"],
            criado_em=datetime.now(timezone.utc),
            atualizado_em=datetime.now(timezone.utc),
        )

    jobs_db.salvar(resultado, settings.dir_jobs)


@app.post("/api/v1/jobs", status_code=202)
async def criar_job(arquivo: UploadFile, usuario_id: str, background_tasks: BackgroundTasks):
    if arquivo.content_type not in ("application/pdf", "application/octet-stream") and not (arquivo.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Apenas arquivos PDF sao aceitos.")

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    pasta_trabalho = settings.dir_jobs / job_id
    pasta_trabalho.mkdir(parents=True, exist_ok=True)
    caminho_pdf = pasta_trabalho / "original.pdf"

    with open(caminho_pdf, "wb") as f:
        shutil.copyfileobj(arquivo.file, f)

    try:
        doc = fitz.open(str(caminho_pdf))
        total_paginas = len(doc)
        doc.close()
    except Exception as exc:
        raise HTTPException(400, f"Nao foi possivel abrir o PDF: {exc}") from exc

    resultado_inicial = ExtracaoResultado(
        job_id=job_id,
        arquivo_origem=arquivo.filename or "arquivo.pdf",
        status=StatusExtracao.PROCESSANDO,
        criado_em=datetime.now(timezone.utc),
        atualizado_em=datetime.now(timezone.utc),
    )
    jobs_db.salvar(resultado_inicial, settings.dir_jobs)

    background_tasks.add_task(_rodar_extracao_em_background, job_id, caminho_pdf, pasta_trabalho, usuario_id)

    return {"job_id": job_id, "status": "processando", "paginas": total_paginas}


@app.get("/api/v1/jobs/{job_id}", response_model=ExtracaoResultado)
async def obter_job(job_id: str):
    try:
        return jobs_db.carregar(job_id, settings.dir_jobs)
    except jobs_db.JobNaoEncontradoError as exc:
        raise HTTPException(404, str(exc)) from exc
    except jobs_db.JobInvalidoError as exc:
        raise HTTPException(400, str(exc)) from exc


# --------------------------------------------------------------------------
# Revisao humana
# --------------------------------------------------------------------------

@app.patch("/api/v1/jobs/{job_id}/modulos/{modulo_id}", response_model=Modulo)
async def corrigir_modulo(job_id: str, modulo_id: str, patch: dict):
    try:
        return jobs_db.atualizar_modulo(job_id, modulo_id, patch, settings.dir_jobs)
    except jobs_db.JobNaoEncontradoError as exc:
        raise HTTPException(404, str(exc)) from exc
    except jobs_db.JobInvalidoError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/v1/jobs/{job_id}/modulos", status_code=201, response_model=Modulo)
async def criar_modulo(job_id: str, nome_ambiente: str, modulo: Modulo):
    try:
        return jobs_db.adicionar_modulo(job_id, nome_ambiente, modulo, settings.dir_jobs)
    except jobs_db.JobNaoEncontradoError as exc:
        raise HTTPException(404, str(exc)) from exc
    except jobs_db.JobInvalidoError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/v1/jobs/{job_id}/confirmar", response_model=ExtracaoResultado)
async def confirmar_job(job_id: str):
    try:
        return jobs_db.confirmar(job_id, settings.dir_jobs)
    except jobs_db.JobNaoEncontradoError as exc:
        raise HTTPException(404, str(exc)) from exc
    except jobs_db.ConfirmacaoBloqueadaError as exc:
        raise HTTPException(409, str(exc)) from exc


# --------------------------------------------------------------------------
# Preferencias Globais
# --------------------------------------------------------------------------

@app.get("/api/v1/usuarios/{usuario_id}/preferencias", response_model=PreferenciasGlobais)
async def obter_preferencias(usuario_id: str):
    try:
        return preferencias_service.carregar_preferencias(usuario_id, settings.dir_preferencias)
    except preferencias_service.PreferenciasInvalidasError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.put("/api/v1/usuarios/{usuario_id}/preferencias", response_model=PreferenciasGlobais)
async def atualizar_preferencias(usuario_id: str, preferencias: PreferenciasGlobais):
    if preferencias.usuario_id != usuario_id:
        raise HTTPException(400, "usuario_id do corpo nao bate com o da URL.")
    try:
        preferencias_service.salvar_preferencias(preferencias, settings.dir_preferencias)
    except preferencias_service.PreferenciasInvalidasError as exc:
        raise HTTPException(400, str(exc)) from exc
    return preferencias


# --------------------------------------------------------------------------
# Auto-aprendizado / feedback
# --------------------------------------------------------------------------

@app.post("/api/v1/usuarios/{usuario_id}/feedback", status_code=201)
async def registrar_feedback(usuario_id: str, request: FeedbackRequest):
    if request.usuario_id != usuario_id:
        raise HTTPException(400, "usuario_id do corpo nao bate com o da URL.")
    try:
        return feedback_service.registrar_feedback(request, settings.anthropic_api_key, settings.modelo_claude, settings.dir_regras_aprendidas)
    except feedback_service.FeedbackInvalidoError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/v1/usuarios/{usuario_id}/regras")
async def listar_regras(usuario_id: str):
    return feedback_service.listar_regras(usuario_id, settings.dir_regras_aprendidas)


@app.delete("/api/v1/usuarios/{usuario_id}/regras/{regra_id}")
async def desativar_regra(usuario_id: str, regra_id: str):
    try:
        return feedback_service.desativar_regra(usuario_id, regra_id, settings.dir_regras_aprendidas)
    except feedback_service.FeedbackInvalidoError as exc:
        raise HTTPException(404, str(exc)) from exc


# --------------------------------------------------------------------------
# Precificacao
# --------------------------------------------------------------------------

@app.post("/api/v1/orcamentos", response_model=OrcamentoResponse)
async def gerar_orcamento(request: OrcamentoRequest, fator_area_frontal_para_chapa: float | None = None):
    try:
        resultado = jobs_db.carregar(request.job_id, settings.dir_jobs)
    except jobs_db.JobNaoEncontradoError as exc:
        raise HTTPException(404, str(exc)) from exc

    try:
        response, avisos = pricing_service.gerar_orcamento(
            resultado,
            settings.caminho_tabela_precos_padrao,
            settings.caminho_config_precificacao,
            faturamento_acumulado=request.faturamento_acumulado,
            custo_hora_mao_de_obra=request.custo_hora_mao_de_obra,
            horas_estimadas=request.horas_estimadas,
            fator_area_frontal_para_chapa=fator_area_frontal_para_chapa,
        )
    except pricing_service.PrecificacaoInvalidaError as exc:
        raise HTTPException(409, str(exc)) from exc

    if avisos:
        return JSONResponse(status_code=200, content={**response.model_dump(), "avisos": avisos})
    return response


@app.get("/health")
async def health():
    """Checa as dependencias que a API precisa de verdade para funcionar,
    em vez de so responder 200 fixo -- um deploy quebrado (chave faltando,
    tabela de precos nao montada) deve aparecer aqui, nao so quando um
    upload falhar horas depois."""
    checks = {
        "anthropic_api_key_configurada": bool(settings.anthropic_api_key),
        "tabela_precos_encontrada": settings.caminho_tabela_precos_padrao.exists(),
        "config_precificacao_encontrada": settings.caminho_config_precificacao.exists(),
    }
    status = "ok" if all(checks.values()) else "degradado"
    return JSONResponse(status_code=200 if status == "ok" else 503, content={"status": status, "checks": checks})
