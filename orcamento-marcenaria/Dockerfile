# Backend MVP do skill orcamento-marcenaria: extractors (Python) + gerador
# de docx (Node) + LibreDWG (dwg2dxf) compilado no build, para converter
# DWG->DXF sem depender de instalacao manual/EULA em nenhuma maquina.
FROM python:3.11-slim-bookworm AS libredwg-build

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential autoconf automake libtool pkg-config \
    texinfo ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Pinned em uma tag estavel do LibreDWG (ajuste a versao conforme necessario).
# IMPORTANTE: 0.13.3 falha ao ler DWG salvos como AutoCAD 2018/2019/2020
# (AC1032, secoes comprimidas) -- testado com um DWG real do usuario, so
# funcionou a partir da 0.14.8592. Nao volte para uma versao mais antiga
# sem testar contra um DWG real nesse formato.
ARG LIBREDWG_VERSION=0.14.8592
RUN git clone --depth 1 --branch ${LIBREDWG_VERSION} https://github.com/LibreDWG/libredwg.git /tmp/libredwg \
    && cd /tmp/libredwg \
    && ./autogen.sh \
    && ./configure --disable-bindings --disable-python --disable-static \
    && make -j"$(nproc)" \
    && make install \
    && ldconfig


FROM python:3.11-slim-bookworm

# dwg2dxf compilado no estagio anterior + libs runtime que ele precisa.
COPY --from=libredwg-build /usr/local/bin/dwg2dxf /usr/local/bin/dwg2dxf
COPY --from=libredwg-build /usr/local/lib/ /usr/local/lib/
RUN ldconfig

# Node (para o gerador de orcamento .docx via docx-js).
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt package.json ./
RUN pip install --no-cache-dir -r requirements.txt \
    && npm install --omit=dev

COPY . .

ENV DWG2DXF_PATH=/usr/local/bin/dwg2dxf

EXPOSE 8000

# Sobe a API FastAPI (api/main.py). Requer ANTHROPIC_API_KEY no ambiente --
# o startup falha rapido e alto se faltar (ver api/main.py e .env.example).
# Os extractors do pipeline CLI continuam disponiveis dentro do container
# via `docker exec`, ex: python extractors/extract_promob_xml.py <arquivo>.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
