FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY triagem ./triagem

# Usuário sem privilégios; currículos e relatórios ficam em /tmp (apagados a cada deploy/reinício).
RUN useradd --create-home app
USER app
ENV TRIAGEM_DADOS=/tmp/triagem

EXPOSE 8000
# Um processo só: o andamento das triagens fica em memória.
CMD ["sh", "-c", "uvicorn triagem.web:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
