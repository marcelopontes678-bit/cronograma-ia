"""Tela web de upload: cadastra vagas, envia currículos e acompanha a triagem.

Rodar:  uvicorn triagem.web:app --port 8000   (ou: python -m triagem.web)

Variáveis de ambiente:
  ANTHROPIC_API_KEY        chave da API do Claude (obrigatória)
  TRIAGEM_SENHA            se definida, pede login (usuário qualquer + esta senha)
  TRIAGEM_EXIGIR_SENHA     "1" = recusa funcionar sem TRIAGEM_SENHA (use em servidor público)
  TRIAGEM_DADOS            pasta onde ficam currículos e relatórios (padrão: dados_web/)
  TRIAGEM_RETENCAO_HORAS   apaga triagens mais antigas que isso (padrão: 24)
  TRIAGEM_MODELO           modelo do Claude (padrão: claude-opus-5-5)

Guarda o estado das triagens em memória: rode com UM processo (sem --workers).
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

import anthropic
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .ia import MODELO_PADRAO
from .leitura import EXTENSOES
from .modelos import Candidato, Vaga
from .pipeline import VagasInvalidas, triar, validar_vagas
from .relatorio import ranking

MAX_ARQUIVOS = 300
MAX_BYTES_ARQUIVO = 10 * 1024 * 1024
MAX_BYTES_TOTAL = 300 * 1024 * 1024
MAX_TOP = 20
PAGINA = Path(__file__).parent / "static" / "index.html"


@dataclass
class Triagem:
    id: str
    pasta: Path
    vagas: list[Vaga]
    total: int
    criada_em: float = field(default_factory=time.time)
    status: str = "na_fila"  # na_fila | analisando | resumindo | concluida | erro
    feitos: int = 0
    com_problema: int = 0
    mensagem: str = ""
    resultado: list[dict] = field(default_factory=list)
    tarefa: asyncio.Task | None = None

    def publico(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "feitos": self.feitos,
            "total": self.total,
            "com_problema": self.com_problema,
            "mensagem": self.mensagem,
            "resultado": self.resultado,
        }


def _resumo_resultado(vagas: list[Vaga], candidatos: list[Candidato], top: int) -> list[dict]:
    saida = []
    for vaga in vagas:
        aprovados, reprovados = ranking(vaga, candidatos)
        saida.append(
            {
                "titulo": vaga.titulo,
                "aprovados": len(aprovados),
                "filtrados": len(reprovados),
                "melhores": [
                    {"nome": c.analise.contato.nome or c.arquivo, "nota": c.resultados[vaga.id].nota}
                    for c in aprovados[:top]
                ],
            }
        )
    return saida


def _nome_seguro(nome: str, usados: set[str]) -> str:
    base = Path(nome or "arquivo").name.replace("\x00", "").strip() or "arquivo"
    base = base[-120:]
    candidato, n = base, 2
    while candidato.lower() in usados:
        stem, ext = os.path.splitext(base)
        candidato, n = f"{stem} ({n}){ext}", n + 1
    usados.add(candidato.lower())
    return candidato


def criar_app(
    pasta_dados: Path | None = None,
    senha: str | None = None,
    retencao_horas: float | None = None,
    modelo: str | None = None,
    exigir_senha: bool | None = None,
) -> FastAPI:
    pasta_dados = Path(pasta_dados or os.environ.get("TRIAGEM_DADOS", "dados_web")).resolve()
    senha = senha if senha is not None else os.environ.get("TRIAGEM_SENHA") or None
    if exigir_senha is None:
        exigir_senha = os.environ.get("TRIAGEM_EXIGIR_SENHA") == "1"
    retencao = 3600 * float(retencao_horas if retencao_horas is not None else os.environ.get("TRIAGEM_RETENCAO_HORAS", 24))
    modelo = modelo or os.environ.get("TRIAGEM_MODELO", MODELO_PADRAO)

    app = FastAPI(title="Triagem de currículos", docs_url=None, redoc_url=None, openapi_url=None)
    triagens: dict[str, Triagem] = {}
    fila = asyncio.Semaphore(1)  # uma triagem por vez; as outras esperam na fila
    basic = HTTPBasic(auto_error=False)

    def autenticar(cred: HTTPBasicCredentials | None = Depends(basic)) -> None:
        if not senha:
            if exigir_senha:
                # Servidor público sem senha: qualquer um gastaria a chave da API. Melhor não abrir.
                raise HTTPException(503, "Configure a variável TRIAGEM_SENHA no servidor para liberar o acesso.")
            return
        if cred is None or not secrets.compare_digest(cred.password.encode(), senha.encode()):
            raise HTTPException(401, "Senha necessária.", headers={"WWW-Authenticate": 'Basic realm="triagem"'})

    def apagar(t: Triagem) -> None:
        if t.tarefa and not t.tarefa.done():
            t.tarefa.cancel()
        shutil.rmtree(t.pasta, ignore_errors=True)
        triagens.pop(t.id, None)

    def limpar_antigas() -> None:
        agora = time.time()
        for t in list(triagens.values()):
            if agora - t.criada_em > retencao and t.status in ("concluida", "erro"):
                apagar(t)

    def obter(id_: str) -> Triagem:
        t = triagens.get(id_)
        if not t:
            raise HTTPException(404, "Triagem não encontrada (pode ter expirado).")
        return t

    async def rodar(t: Triagem, arquivos: list[Path], top: int) -> None:
        async with fila:
            t.status = "analisando"

            def progresso(feitos: int, total: int, c: Candidato) -> None:
                t.feitos = feitos
                if c.erro:
                    t.com_problema += 1

            def resumindo() -> None:
                t.status = "resumindo"

            try:
                candidatos = await triar(
                    t.vagas, arquivos, t.pasta / "saida",
                    top=top, modelo=modelo, ao_progredir=progresso, ao_resumir=resumindo,
                )
            except (anthropic.AuthenticationError, anthropic.PermissionDeniedError):
                t.status, t.mensagem = "erro", "A chave da API do Claude no servidor é inválida ou não tem permissão."
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001 — qualquer falha vira mensagem na tela
                t.status, t.mensagem = "erro", f"Falha inesperada: {e}"
            else:
                if candidatos and all(c.analise is None for c in candidatos):
                    # Nada foi analisado (API fora do ar, rede, cota...): é falha, não um ranking vazio.
                    t.status = "erro"
                    t.mensagem = f"Nenhum currículo pôde ser analisado. Primeiro erro: {candidatos[0].erro}"
                else:
                    t.resultado = _resumo_resultado(t.vagas, candidatos, top)
                    t.status = "concluida"
            finally:
                # Os currículos originais não são mais necessários: apaga já (LGPD).
                shutil.rmtree(t.pasta / "curriculos", ignore_errors=True)

    @app.get("/api/saude")
    async def saude():
        # Sem senha: usado pelo health check do Render. Não expõe nada.
        return {"ok": True}

    @app.get("/", response_class=HTMLResponse, dependencies=[Depends(autenticar)])
    async def pagina():
        return HTMLResponse(PAGINA.read_text(encoding="utf-8"), headers={"Cache-Control": "no-store"})

    @app.post("/api/triagens", dependencies=[Depends(autenticar)])
    async def criar(
        vagas: str = Form(...),
        top: int = Form(5),
        curriculos: list[UploadFile] = File(...),
    ):
        limpar_antigas()
        try:
            lista_vagas = validar_vagas(json.loads(vagas))
        except (json.JSONDecodeError, VagasInvalidas) as e:
            raise HTTPException(400, str(e))
        if not curriculos:
            raise HTTPException(400, "Envie pelo menos um currículo.")
        if len(curriculos) > MAX_ARQUIVOS:
            raise HTTPException(400, f"Máximo de {MAX_ARQUIVOS} currículos por triagem.")
        top = max(0, min(top, MAX_TOP))

        id_ = secrets.token_urlsafe(16)
        pasta = pasta_dados / id_
        destino = pasta / "curriculos"
        destino.mkdir(parents=True)
        usados: set[str] = set()
        salvos: list[Path] = []
        total_bytes = 0
        ignorados: list[str] = []
        try:
            for up in curriculos:
                nome = _nome_seguro(up.filename, usados)
                if Path(nome).suffix.lower() not in EXTENSOES:
                    ignorados.append(nome)
                    continue
                caminho = destino / nome
                tamanho = 0
                with caminho.open("wb") as f:
                    while bloco := await up.read(1024 * 1024):
                        tamanho += len(bloco)
                        total_bytes += len(bloco)
                        if tamanho > MAX_BYTES_ARQUIVO:
                            raise HTTPException(400, f"'{nome}' passa de {MAX_BYTES_ARQUIVO // 1024 // 1024} MB.")
                        if total_bytes > MAX_BYTES_TOTAL:
                            raise HTTPException(400, "O envio passa do limite total de 300 MB.")
                        f.write(bloco)
                salvos.append(caminho)
        except BaseException:
            shutil.rmtree(pasta, ignore_errors=True)
            raise
        if not salvos:
            shutil.rmtree(pasta, ignore_errors=True)
            raise HTTPException(400, "Nenhum arquivo válido. Formatos aceitos: PDF, DOCX, TXT e MD.")

        t = Triagem(id=id_, pasta=pasta, vagas=lista_vagas, total=len(salvos))
        if ignorados:
            t.mensagem = f"{len(ignorados)} arquivo(s) ignorado(s) por formato não suportado."
        triagens[id_] = t
        t.tarefa = asyncio.create_task(rodar(t, salvos, top))
        return t.publico()

    @app.get("/api/triagens/{id_}", dependencies=[Depends(autenticar)])
    async def status(id_: str):
        return obter(id_).publico()

    def arquivo_saida(id_: str, nome: str) -> Path:
        t = obter(id_)
        if t.status != "concluida":
            raise HTTPException(409, "A triagem ainda não terminou.")
        return t.pasta / "saida" / nome

    @app.get("/api/triagens/{id_}/relatorio", dependencies=[Depends(autenticar)])
    async def relatorio(id_: str):
        return FileResponse(
            arquivo_saida(id_, "relatorio.html"),
            media_type="text/html; charset=utf-8",
            headers={
                # O relatório não tem JavaScript: bloqueia qualquer script que um currículo tente injetar.
                "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @app.get("/api/triagens/{id_}/ranking.csv", dependencies=[Depends(autenticar)])
    async def planilha(id_: str):
        return FileResponse(
            arquivo_saida(id_, "ranking.csv"),
            media_type="text/csv; charset=utf-8",
            filename="ranking.csv",
            headers={"Cache-Control": "no-store"},
        )

    @app.delete("/api/triagens/{id_}", dependencies=[Depends(autenticar)])
    async def excluir(id_: str):
        apagar(obter(id_))
        return {"ok": True}

    return app


app = criar_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 8000)))
