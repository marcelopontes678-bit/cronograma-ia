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
| `.dxf` (Promob ou convertido de DWG) | `extractors/extract_promob_dxf.py` | **Ainda nao implementado** |
| `.dwg` | `extractors/convert_dwg.py` (DWG->DXF via ODA File Converter) depois `extract_promob_dxf.py` | Codigo escrito, conversao ainda nao testada (ODA instalado so na maquina Windows do usuario) |
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

Os extractors do Promob (XML/DXF) trazem geometria e um codigo `REFERENCE` de material/acabamento, mas **nao trazem preco em R$**. O preco de cada item vem de `config/tabela_precos_referencia.xlsx` (modelo em `tabela_precos_referencia_MODELO.xlsx`), que mapeia `REFERENCE -> preco unitario`. Use `engine/tabela_precos.py::calcular_custo_item` para resolver isso -- um item cuja referencia nao esta na tabela fica marcado `SEM_PRECO_NA_TABELA` e **nunca** entra no orcamento com custo zero ou estimado.

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
