"""Entrypoint da função serverless — mesmo app do `run_studyos_standalone.py`,
empacotado no formato que o runtime Python da Vercel espera (`app` no topo do
módulo, ASGI). Roteado para todo o tráfego por `vercel.json`.

Não depende de `DATABASE_URL` nem de nenhuma configuração do resto da
aplicação — só o motor de 24 agentes do StudyOS. Para os agentes 07–11, 13 e
16 responderem com conteúdo redigido por um modelo de verdade em vez de
ficarem `pendente_de_redacao`, configure `ANTHROPIC_API_KEY` nas variáveis de
ambiente do projeto na Vercel.
"""

from fastapi import FastAPI

from app.routers.studyos import router as studyos_router

app = FastAPI(
    title="StudyOS",
    description="Motor de planejamento de estudos com 24 agentes — sem banco de dados.",
)
app.include_router(studyos_router)
