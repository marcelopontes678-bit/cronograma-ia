"""Servidor standalone do StudyOS — sem banco de dados, sem autenticação.

`app/routers/studyos.py` foi desenhado desde o início para não depender de
`DATABASE_URL` nem de nenhuma outra configuração de `app.main` — é a mesma
propriedade que permite `tests/test_studyos_api.py` rodar sem banco. Este
script usa exatamente essa independência para subir só o motor de 24 agentes,
sem precisar do Postgres nem do resto da aplicação.

Uso:

    cd backend
    pip install fastapi "uvicorn[standard]" httpx pydantic
    python run_studyos_standalone.py

Depois abra http://localhost:8000/docs — Swagger interativo para testar
POST /studyos/plano (mostra a ordem de execução sem rodar nada) e
POST /studyos/orquestrar (roda o fluxo completo e devolve a saída real).

Para os agentes 07–11, 13 e 16 responderem com conteúdo redigido por um
modelo de verdade em vez de ficarem `pendente_de_redacao`, exporte
ANTHROPIC_API_KEY antes de rodar. Sem a chave, o motor funciona igual —
determinístico, nunca inventa conteúdo.
"""

import uvicorn
from fastapi import FastAPI

from app.routers.studyos import router as studyos_router

app = FastAPI(
    title="StudyOS",
    description="Motor de planejamento de estudos com 24 agentes — sem banco de dados.",
)
app.include_router(studyos_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
