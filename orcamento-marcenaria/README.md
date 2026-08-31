# Orçamento de Marcenaria

Skill/pipeline por linha de comando para gerar orçamento de marcenaria a
partir de projetos em **PDF**, **DWG**, **SketchUp (relatório CSV)** ou
**XML/DXF do Promob** (`extractors/` + `engine/`), testado com projetos
reais, sem depender de API paga.

A extração via **Claude Vision** (persona **MARC**, agente especialista em
engenharia de marcenaria) e a precificação multiusuário em produção vivem
agora no backend do SmartFactory (`../backend/`, ver
`../backend/app/routers/orcamento.py`) — o protótipo de API que existia
aqui (`api/`) foi removido depois que essa integração alcançou paridade
funcional. Este diretório ficou só com o pipeline CLI.

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

O `Dockerfile` também sobe a API (seção 3) via `uvicorn` — o `docker build`
acima gera uma imagem pronta para `docker run -p 8000:8000 --env-file .env
orcamento-marcenaria` (ver `.env.example` para as variáveis).

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

## 3. Extração via Claude Vision (agora no backend do SmartFactory)

O protótipo de API que existia aqui (`api/`) foi removido — a extração via
Claude Vision (persona **MARC**), a precificação e o auto-aprendizado por
feedback foram movidos para `../backend/` (rotas em
`../backend/app/routers/orcamento.py`), multiusuário, autenticado via JWT
e persistido em Postgres. Veja o README do backend para configurar/rodar.

Duas observações técnicas que continuam valendo (encontradas validando a
extração contra a API real da Anthropic, não são hipotéticas):

- Às vezes o modelo serializa o objeto `{"ambientes": [...], "avisos": [...]}`
  inteiro como uma **string** dentro do próprio campo `ambientes`, em
  vez de popular o array direto (provavelmente por causa da
  profundidade do schema aninhado) — `_normalizar_input_ferramenta()`
  em `orcamento_vision_extractor.py` detecta e desembrulha esse formato.
- O `bounding_box` retornado às vezes estoura levemente o range 0-1000
  (é uma estimativa visual, não uma cota exata) — `_dict_para_modulo()`
  faz *clamp* do valor ao range válido e adiciona um aviso pedindo
  conferência manual, em vez de descartar o módulo inteiro.

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
- **Via Claude Vision**: use o módulo de orçamento do backend (seção 3),
  que faz exatamente isso de forma automatizada, com bounding boxes e
  confiança por módulo para orientar a revisão.

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
├── tests/arquivos_exemplo/   # arquivos reais usados para testar os extractors
├── output/                    # resultados gerados (json, xlsx, docx)
└── Dockerfile                  # LibreDWG + Python + Node, self-hosted
```

A extração via Claude Vision, precificação multiusuário e telas de
orçamento vivem em `../backend/` e `../frontend/` (fora deste diretório).

## 6. Testes

```bash
pytest
```

54 testes cobrindo o pipeline CLI (`engine/`, `extractors/`), rodando
contra dados reais sempre que possível — o XML/PDF do projeto Quarto
Maria, um DWG real convertido via LibreDWG (`dwg2dxf`, pulado
automaticamente se não estiver instalado). Os testes do módulo de
orçamento (extração via Vision, precificação, feedback) agora vivem em
`../backend/tests/`.

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
