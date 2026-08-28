---
name: orcamento-marcenaria
description: Gera orcamento de marcenaria a partir de projetos em PDF, DWG, SKP (SketchUp) ou XML/DXF do Promob. Detecta o tipo de arquivo, normaliza para uma estrutura unica (ambientes -> modulos -> itens com dimensoes e acabamento), casa cada item com sua tabela de precos e aplica a formula de precificacao (divisor de markup + margem), gerando um orcamento final. Use quando o usuario pedir para orcar um projeto de marcenaria, processar um arquivo do Promob/SketchUp/AutoCAD, ou perguntar sobre precificacao de moveis planejados.
---

# Orcamento de Marcenaria

Pipeline: **detectar tipo de arquivo -> extrair (normalizar) -> precificar -> gerar orcamento final**.

## 1. Deteccao de tipo de arquivo e roteamento

| Extensao / conteudo | Extractor | Status |
|---|---|---|
| `.xml` (exportacao "Listagem_montados" do Promob) | `extractors/extract_promob_xml.py` | Testado com projeto real |
| `.dxf` (Promob ou convertido de DWG) | `extractors/extract_promob_dxf.py` | Testado com DXF real (gerado pelo proprio pipeline DWG->DXF); schema de blocos Promob ainda nao confirmado com um DXF exportado do Promob de verdade |
| `.dwg` | `extractors/convert_dwg.py` (DWG->DXF via LibreDWG `dwg2dxf`, self-hosted; ODA File Converter como fallback) depois `extract_promob_dxf.py` | Testado ponta a ponta com DWG real do usuario (AutoCAD 2018/2019/2020, 30MB, projeto arquitetonico): converteu e extraiu 2455 blocos. IMPORTANTE: exige LibreDWG >= 0.14.8592 -- a 0.13.3 falha em DWG salvo como AC1032 (ver nota no Dockerfile) |
| `.pdf` | `extractors/extract_pdf_plant.py` | Testado com planta real (2 paginas vetoriais) |
| `.skp` | Nao le o binario direto. Pedir ao usuario para exportar `File > Generate Report...` no SketchUp e usar `extractors/extract_skp.py` no CSV/TXT gerado | Codigo escrito, aguardando teste com relatorio real |

Regra de deteccao: olhar a extensao do arquivo recebido.
- `.xml` -> tentar `extract_promob_xml.py` primeiro; se a raiz do XML nao for `<LISTING>` do Promob, avisar o usuario em vez de forcar a extracao.
- `.dxf` -> ir direto para `extract_promob_dxf.py` (quando existir).
- `.dwg` -> rodar `convert_dwg.py` para gerar um `.dxf` temporario, depois `extract_promob_dxf.py`. Nunca tentar ler o `.dwg` binario diretamente.
- `.pdf` -> `extract_pdf_plant.py`. Paginas sem texto vetorial (escaneadas) caem em `precisa_assistencia=True` com uma imagem renderizada para revisao humana - nunca inventar dimensoes por OCR automatico.
- `.skp` -> nunca abrir o binario. Pedir ao usuario o relatorio CSV/TXT do SketchUp (`File > Generate Report...`) e passar para `extract_skp.py`.

## 2. Estrutura unica de dados (saida de qualquer extractor)

Todo extractor normaliza para o mesmo formato logico, mesmo que o schema exato do JSON varie um pouco por extractor (ver `engine/orcamento_engine.py` para as dataclasses `Ambiente`/`Modulo`/`ItemCusto`):

```
Ambiente (ex: "Quarto Maria")
  -> Modulo (ex: "Armario", "Base Linear 18")
       -> ItemCusto (ex: "Chapa MDF 18mm")
            - descricao
            - custo_material (R$, resolvido via tabela de precos por REFERENCE)
            - origem (rastreabilidade: GUID/UNIQUEID, pagina+coordenada, ou linha do CSV)
```

**Rastreabilidade obrigatoria**: todo item extraido carrega um campo `origem` apontando de volta ao arquivo original -- GUID/UNIQUEID no XML/DXF do Promob, pagina+coordenada (x0,y0,x1,y1) no PDF, ou numero de linha no CSV do SketchUp. Nunca descartar essa informacao entre a extracao e o calculo.

## 3. Tabela de precos por referencia

Os extractors do Promob (XML/DXF) trazem geometria e um codigo `REFERENCE` de material/acabamento, mas **nao trazem preco em R$**. O preco vem de `config/tabela_precos_referencia.xlsx` (modelo em `tabela_precos_referencia_MODELO.xlsx`).

**Modelo de precificacao (por chapa fechada + fita + ferragem, nao mais peca por peca):**
- Itens de unidade `M2` (pecas de MDF): precificados por **CHAPA FECHADA**. `engine/calculo_projeto.py::calcular_projeto` soma a area (m2) de todas as pecas do mesmo `REFERENCE`, aplica 15% de perda de corte, divide pela area util de uma chapa padrao (2750x1830mm = 5,0325 m2) e arredonda pra cima -> numero de chapas x `preco_chapa_fechada`.
- Fita de borda (mesmo `REFERENCE` da chapa): estimada pelo perimetro fitavel de cada peca (as duas maiores dimensoes; a menor e a espessura) x repeticao, somado em metros x `preco_fita_metro`.
- Itens de unidade `UN` (ferragens/componentes): `preco_unitario_un` x quantidade/repeticao, como antes (`tabela_precos.py::calcular_custo_item_ferragem`).

Referencia sem preco cadastrado fica em `resultado.itens_sem_preco` e **nunca** entra no total com custo zero ou estimado.

`engine/orcamento_engine.py::calcular_orcamento_projeto` aplica o markup sobre o `custo_material_total` agregado do projeto inteiro (chapas+fita+ferragens), nao mais por modulo -- ver tambem a funcao legada `calcular_orcamento` (por modulo/peca) mantida para outras origens de dados que nao tenham essa granularidade M2/UN.

## 4. Precificacao

`config/precificacao.json` guarda todos os parametros (nunca hardcode na engine):
- `pct_custo_fixo`, `pct_impostos`, `pct_comissao_fabrica`, `pct_lucro`: percentuais fixos.
- `comissao_vendas_faixas`: comissao de vendas escalonada por faturamento acumulado (5%/6%/7%/8%), informado manualmente pelo usuario a cada orcamento (`faturamento_acumulado`).
- Montagem: **nao e cobrada separadamente** (`montagem.cobrada_separadamente = false`).
- Mao de obra: somada **depois** do markup, nunca multiplicada por ele.

Formula (`engine/orcamento_engine.py::calcular_orcamento`):
```
divisor_markup = 1 / (1 - (pct_custo_fixo + pct_impostos + pct_comissao_fabrica + pct_comissao_vendas + pct_lucro))
preco_venda_material = custo_material * divisor_markup
preco_final_item = preco_venda_material + custo_mao_de_obra
```

## 5. Gerando o orcamento final (xlsx/docx)

Ainda nao implementado. Quando pedido, gerar a partir do `ResultadoOrcamento` retornado por `calcular_orcamento`, listando por ambiente/modulo: descricao, custo material, preco de venda, mao de obra, preco final, e total geral -- usando as skills `xlsx`/`docx` deste ambiente para a formatacao do arquivo.

## 6. Regras gerais (nunca violar)

- Nunca inventar valores de precificacao -- sempre ler de `config/precificacao.json`.
- Nunca fazer parsing direto de DWG ou SKP binario -- sempre converter (DWG->DXF via ODA) ou pedir exportacao assistida (SKP->relatorio CSV).
- Nunca reportar uma extracao/teste como bem-sucedida sem ter rodado contra um arquivo real do usuario.
- Nunca atribuir custo a um item cuja referencia nao esta na tabela de precos -- sinalizar como pendente.
- Toda extracao deve manter rastreabilidade ate pagina/linha/coordenada/GUID do arquivo original.
