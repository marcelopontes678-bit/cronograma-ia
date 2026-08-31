# Orçamento de Marcenaria

Skill/pipeline para gerar orçamento de marcenaria a partir de projetos em
**PDF**, **DWG**, **SketchUp (relatório CSV)** ou **XML/DXF do Promob**, e
um protótipo de API (`api/`) que usa **Claude Vision** — através da persona
**MARC**, um agente especialista em engenharia de marcenaria e leitura de
projetos — para automatizar a leitura de plantas em PDF.

Duas formas de usar este projeto:

1. **Pipeline por linha de comando** (`extractors/` + `engine/`) — testado
   com projetos reais, sem depender de API paga.
2. **API (`api/`)** — protótipo que envia páginas de PDF pro Claude Vision
   para extrair módulos automaticamente, com revisão humana obrigatória
   antes de precificar.

---

## 1. Instalação

```bash
cd orcamento-marcenaria
pip install -r requirements.txt
```

Para o gerador de orçamento em `.docx` (usa `docx-js`, Node):

```bash
npm install
```

### Dependências externas (conversão DWG)

Conversão de `.dwg` para `.dxf` usa o **LibreDWG** (`dwg2dxf`), nunca faz
parsing direto do binário DWG. Instale localmente ou use o `Dockerfile`
(compila a versão `0.14.8592`, testada contra um DWG real de AutoCAD
2018/2019/2020 — versões mais antigas do LibreDWG falham nesse formato):

```bash
docker build -t orcamento-marcenaria .
```

Sem Docker, compile o LibreDWG manualmente (ver comentário no topo do
`Dockerfile` para os comandos exatos) e informe o caminho do binário via
variável de ambiente `DWG2DXF_PATH`.

---

## 2. Pipeline por linha de comando

### 2.1 Extrair um projeto

Escolha o extractor de acordo com o formato de entrada:

| Formato | Comando |
|---|---|
| XML do Promob | `python3 extractors/extract_promob_xml.py <arquivo.xml> --saida output/extracao.json` |
| DXF (Promob ou DWG convertido) | `python3 extractors/extract_promob_dxf.py <arquivo.dxf> --saida output/extracao_dxf.json` |
| DWG | `python3 extractors/convert_dwg.py <arquivo.dwg> --pasta-saida output/dxf_convertido` (depois rode o extractor de DXF acima no resultado) |
| PDF (planta/vista) | `python3 extractors/extract_pdf_plant.py <arquivo.pdf> --saida output/extracao_pdf.json` |
| SketchUp | No SketchUp: `File > Generate Report...` → exporte CSV → `python3 extractors/extract_skp.py <relatorio.csv> --saida output/extracao_skp.json` |

O extractor de PDF só entrega texto + geometria com coordenadas (não
estrutura módulos automaticamente) — veja a seção 4 sobre extração
assistida.

### 2.2 Preencher a tabela de preços

Preços de material **nunca são inventados**. Edite
`config/tabela_precos_referencia.xlsx` (modelo em
`config/tabela_precos_referencia_MODELO.xlsx`) com:

- **Preço Chapa Fechada (R$)** e **Preço Fita de Borda (R$/m)** por
  acabamento (chapas de MDF, unidade M2)
- **Preço Unitário UN (R$)** por referência (ferragens/componentes,
  unidade UN)

O motor agrupa peças pelo **acabamento real** (espessura + nome do
material extraído do código Promob), não pelo código completo da peça —
várias peças do mesmo acabamento cortadas de tipos diferentes de módulo
compartilham a mesma linha de preço.

### 2.3 Ajustar os parâmetros de precificação

`config/precificacao.json` guarda o divisor de markup (% custo fixo +
impostos + comissões + lucro), a comissão de vendas escalonada por
faturamento acumulado, % de perda de corte e área útil da chapa padrão
(2750×1830mm). Edite os valores lá, nunca no código.

### 2.4 Gerar o orçamento final

```bash
python3 engine/gerar_orcamento_xlsx.py output/extracao.json \
  --faturamento-acumulado 100000 \
  --custo-hora 32.25 \
  --horas-estimadas 25 \
  --cliente "Nome do Cliente" \
  --saida output/orcamento_final.xlsx
```

O `.xlsx` gerado é **100% orientado a fórmulas**: células em azul (preço
de chapa/fita/ferragem, %, custo-hora, horas) são editáveis e tudo o
resto recalcula sozinho no Excel — inclusive o **Divisor de Markup**, que
é uma célula fixa e editável (não recalcula automaticamente a partir dos
% de composição, por decisão do usuário).

Para gerar a versão `.docx` (proposta formatada), primeiro exporte o
resultado calculado em JSON (ver `engine/gerar_orcamento_xlsx.py` como
referência de como montar esse JSON) e rode:

```bash
node engine/gerar_orcamento_docx.js output/orcamento_final_dados.json output/orcamento_final.docx
```

---

## 3. API (protótipo com Claude Vision — agente MARC)

Arquitetura completa em [`api/ROTAS.md`](api/ROTAS.md).

O agente extrator tem a persona **MARC**, um especialista em engenharia de
marcenaria (system prompt em `api/prompts/system_extrator.md`). Além de ler
dimensões e materiais direto do desenho, o MARC aplica diretrizes padrão da
fábrica (`PreferenciasGlobais`) para inferir o que o projeto não deixa
explícito:

- Espessuras de caixaria/porta/fundo/sarrafo superior.
- Método de união (cavilha/minifix/vb35/parafuso direto) e fixação do fundo.
- **Exceção de estética**: em cristaleiras com porta de vidro/alumínio ou
  nichos abertos (fundo exposto), o fundo usa a cor da caixaria em vez do
  acabamento interno padrão.
- Apoio por ambiente: pé plástico em áreas molhadas (cozinha, banheiro,
  lavanderia), rodapé em MDF nas demais.
- Quantidade de dobradiças por porta, pela faixa de altura do módulo.
- Sistemas de abertura diferenciados (basculante com pistão a gás, porta de
  correr) e tipo de corrediça.
- Itens fora do escopo de marcenaria (pedra/mármore, espelho, serralheria,
  estofado, fita de LED) classificados à parte, nunca misturados com os
  módulos de madeira.

Toda vez que uma diretriz padrão é usada em vez de uma especificação do
próprio desenho, o campo entra em
`especificacoes_materiais.campos_inferidos` — nunca fica silenciosamente
implícito que a informação veio do desenho.

### 3.1 Configurar

```bash
export ANTHROPIC_API_KEY="sua-chave-aqui"   # nunca cole a chave no codigo/chat
# opcionais, com defaults sensatos:
export ORCAMENTO_MODELO_CLAUDE="claude-sonnet-5"
export ORCAMENTO_STORAGE_DIR="api/storage"
export ORCAMENTO_TABELA_PRECOS="config/tabela_precos_referencia.xlsx"
export ORCAMENTO_CONFIG_PRECIFICACAO="config/precificacao.json"
```

**Nunca** cole a chave da API direto numa mensagem de chat ou a comite no
git — use variável de ambiente ou um gerenciador de segredos. Se uma
chave já vazou (chat, commit, log), revogue no console da Anthropic e
gere outra.

### 3.2 Rodar

```bash
uvicorn api.main:app --reload
```

Docs interativas em `http://localhost:8000/docs`.

### 3.3 Fluxo de uso (ver `api/ROTAS.md` para o contrato completo de cada rota)

1. `POST /api/v1/jobs` — envia o PDF (`multipart/form-data`, campos
   `arquivo` + `usuario_id`). Retorna `job_id` e dispara a extração via
   Claude Vision (persona MARC) em background.
2. `GET /api/v1/jobs/{job_id}` — poll até o `status` sair de
   `processando`. Cada módulo extraído vem com dimensões, componentes e
   materiais estruturados em sub-objetos (`dimensoes`, `componentes`,
   `especificacoes_materiais`), ferragens sugeridas (`ferragens_sugeridas`),
   itens fora do escopo de marcenaria (`itens_complementares`), `confianca`
   (0-1) e `auditoria_visual` (`pagina_pdf` + `bounding_box` no formato
   `[y_min, x_min, y_max, x_max]`, normalizado 0-1000 — para destacar o
   módulo na página no frontend). Ver o schema completo em
   `api/schemas/extracao.py`.
3. **Revisão obrigatória**: `PATCH /api/v1/jobs/{job_id}/modulos/{id}`
   corrige um módulo (aceita patch parcial, inclusive em subcampos
   aninhados como `dimensoes.largura_mm`); `POST .../modulos` adiciona um
   que a IA não pegou. `POST /api/v1/jobs/{job_id}/confirmar` só libera o
   job quando **nenhum** módulo de origem `vision_automatico` tem
   confiança abaixo de 0.7 — a API responde `409` até isso ser resolvido.
4. `POST /api/v1/orcamentos` — gera o orçamento a partir de um job
   **confirmado**. Só calcula custo de chapa/fita quando você passa
   `fator_area_frontal_para_chapa` (multiplicador de área frontal →
   área real de corte, considerando fundo/laterais/prateleiras) — sem
   esse fator, cada módulo fica pendente e listado em `avisos`, nunca com
   custo estimado silenciosamente.

Preferências Globais (`/usuarios/{id}/preferencias`) e Regras Aprendidas
via feedback (`/usuarios/{id}/feedback`) são injetadas automaticamente no
prompt do extrator nas próximas execuções desse usuário.

### 3.4 Validação com a API real (feita)

`vision_extractor.py` e `feedback_service.py` já foram testados com uma
chamada real à API da Anthropic (não só mockada), contra o PDF real
`tests/arquivos_exemplo/silvana_helio/Banheiro.pdf`. A extração
completa funciona ponta a ponta e produziu um `ExtracaoResultado`
válido com 3 módulos, aplicando corretamente as diretrizes de
engenharia do MARC (método de união/fixação inferidos e registrados em
`campos_inferidos`, granito/vidro/louças classificados fora do escopo
de marcenaria).

Dois problemas reais de robustez foram encontrados e corrigidos a
partir dessa validação (não eram hipotéticos — só apareceram contra a
API de verdade):

- Às vezes o modelo serializa o objeto `{"ambientes": [...], "avisos": [...]}`
  inteiro como uma **string** dentro do próprio campo `ambientes`, em
  vez de popular o array direto (provavelmente por causa da
  profundidade do schema aninhado). `_normalizar_input_ferramenta()`
  detecta e desembrulha esse formato, registrando um aviso explícito.
- O `bounding_box` retornado às vezes estoura levemente o range 0-1000
  (é uma estimativa visual, não uma cota exata). `_dict_para_modulo()`
  agora faz *clamp* do valor ao range válido e adiciona um aviso
  pedindo conferência manual daquele destaque, em vez de descartar o
  módulo inteiro com um erro de validação.

Ainda vale conferir antes de um uso mais intenso em produção:

- Custo/tempo por página em lotes maiores — ajuste `PAGINAS_POR_LOTE`
  em `api/services/vision_extractor.py` se necessário.
- Se o `bounding_box` (já dentro do range, sem o clamp) corresponde
  visualmente à posição real do módulo na página renderizada — isso
  exige comparar contra a imagem, o que não foi verificado nesta
  validação.

---

## 4. Extração assistida (PDF sem estrutura Promob)

Quando o PDF não tem uma lista de materiais estruturada (só anotações
soltas ao lado de vistas/elevações — caso comum em projetos de
arquitetura/design de interiores, diferente da exportação do Promob), a
extração automática por texto+geometria não é confiável o suficiente pra
gerar orçamento sem revisão. Duas opções:

- **Manual**: renderize a página como imagem
  (`extractors/extract_pdf_plant.py` já faz isso pra páginas escaneadas)
  e leia visualmente os módulos, confirmando com o cliente/usuário antes
  de montar a lista de módulos.
- **Via API**: use o pipeline do Claude Vision (seção 3), que faz
  exatamente isso de forma automatizada, com bounding boxes e confiança
  por módulo para orientar a revisão.

Em qualquer um dos casos, a conversão de **área frontal** (largura ×
altura de um módulo) para **área real de chapa** (considerando fundo,
laterais e prateleiras internas) exige um fator multiplicador que só o
marceneiro sabe informar — nunca é assumido automaticamente.

---

## 5. Estrutura de pastas

```
orcamento-marcenaria/
├── extractors/          # Promob (XML/DXF), DWG->DXF, PDF, SketchUp
├── engine/               # calculo_projeto.py, orcamento_engine.py,
│                         # tabela_precos.py, geradores de xlsx/docx
├── config/               # precificacao.json, tabela_precos_referencia.xlsx
├── api/                  # protótipo FastAPI + Claude Vision
│   ├── main.py            # rotas
│   ├── config.py          # settings via variavel de ambiente
│   ├── schemas/            # Pydantic (extracao, preferencias, feedback, orcamento)
│   ├── services/            # vision_extractor, pricing_service, etc
│   ├── db/jobs.py            # armazenamento de jobs (arquivo JSON)
│   ├── prompts/                # system prompt + JSON Schema de saida
│   ├── storage/                  # dados persistidos (jobs, preferencias, regras)
│   └── ROTAS.md                    # contrato de cada rota
├── tests/arquivos_exemplo/   # arquivos reais usados para testar os extractors
├── output/                    # resultados gerados (json, xlsx, docx)
└── Dockerfile                  # LibreDWG + Python + Node, self-hosted
```

## 6. Testes

```bash
pytest
```

120 testes cobrindo o pipeline CLI (`engine/`, `extractors/`) e a API
(`api/`), rodando contra dados reais sempre que possível — o XML/PDF do
projeto Quarto Maria, um DWG real convertido via LibreDWG (`dwg2dxf`,
pulado automaticamente se não estiver instalado). Por padrão, esses 120
testes mockam a chamada à API da Anthropic na fronteira do SDK
(`anthropic.Anthropic`), já que não é desejável gastar crédito de API a
cada execução da suíte automatizada. A extração via Vision e o
`feedback_service.py` já foram validados **manualmente** contra a API
real ao menos uma vez (ver seção 3.4) — essa validação real não faz
parte da suíte `pytest` e precisa ser repetida sempre que o
`schema_saida.json` ou o `system_extrator.md` mudarem de forma
relevante.

## 7. Princípios do projeto (não violar)

- Nunca inventar preço, dimensão ou área — item sem dado real fica
  sinalizado como pendência, nunca com valor estimado silenciosamente.
- Nunca fazer parsing direto de DWG ou SKP binário — sempre converter
  (LibreDWG) ou pedir exportação assistida (relatório do SketchUp).
- Nunca reportar uma extração como testada sem ter rodado contra um
  arquivo real.
- Toda extração mantém rastreabilidade até página/linha/coordenada/GUID
  do arquivo original.
- Extração automatizada (Vision) sempre passa por confirmação humana
  antes de virar orçamento.
