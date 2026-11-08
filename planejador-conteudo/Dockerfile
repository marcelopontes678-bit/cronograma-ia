FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY migrations ./migrations
COPY pauta ./pauta

RUN useradd --create-home app
USER app

EXPOSE 8000
# Aplica as migrações e sobe a API. A API não guarda estado em memória
# (login por JWT, status das gerações no banco), então dá para ter vários workers e instâncias.
CMD ["sh", "-c", "alembic upgrade head && uvicorn pauta.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --workers ${WEB_CONCURRENCY:-2}"]
