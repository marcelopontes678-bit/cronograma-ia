/**
 * Gera o orcamento final em .docx (proposta formatada para o cliente) a
 * partir de um JSON com o resultado ja calculado pelo engine Python.
 *
 * Uso: node gerar_orcamento_docx.js dados.json saida.docx
 *
 * Formato esperado do JSON de entrada (ver engine/exportar_resultado_json.py):
 * {
 *   "cliente": "...", "projeto": "...",
 *   "divisor_markup": 2.76, "pct_comissao_vendas_aplicada": 0.05,
 *   "faturamento_acumulado": 100000,
 *   "modulos": [{ "nome": "...", "custo_material": 950, "preco_venda_material": 2622.14,
 *                 "custo_mao_de_obra": 200, "preco_final": 2822.14 }],
 *   "total": 2822.14
 * }
 */
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, BorderStyle,
} = require("docx");

const [, , caminhoJson, caminhoSaida] = process.argv;
if (!caminhoJson || !caminhoSaida) {
  console.error("Uso: node gerar_orcamento_docx.js dados.json saida.docx");
  process.exit(1);
}

const dados = JSON.parse(fs.readFileSync(caminhoJson, "utf-8"));

const moeda = (v) =>
  "R$ " + Number(v).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const LARGURA_TABELA = 9360; // ~6.5in em DXA
const LARGURAS_COLUNAS = [4680, 2340, 2340];

function celula(texto, { negrito = false, corFundo = null, alinhamento = AlignmentType.LEFT, largura } = {}) {
  return new TableCell({
    width: { size: largura, type: WidthType.DXA },
    shading: corFundo ? { type: ShadingType.CLEAR, fill: corFundo } : undefined,
    children: [
      new Paragraph({
        alignment: alinhamento,
        children: [new TextRun({ text: String(texto), bold: negrito })],
      }),
    ],
  });
}

const linhasCabecalho = new TableRow({
  tableHeader: true,
  children: [
    celula("Ambiente / Modulo", { negrito: true, corFundo: "305496", largura: LARGURAS_COLUNAS[0] }),
    celula("Preco Material (R$)", { negrito: true, corFundo: "305496", alinhamento: AlignmentType.RIGHT, largura: LARGURAS_COLUNAS[1] }),
    celula("Preco Final (R$)", { negrito: true, corFundo: "305496", alinhamento: AlignmentType.RIGHT, largura: LARGURAS_COLUNAS[2] }),
  ],
});

const linhasModulos = (dados.modulos || []).map(
  (m) =>
    new TableRow({
      children: [
        celula(m.nome, { largura: LARGURAS_COLUNAS[0] }),
        celula(moeda(m.preco_venda_material), { alinhamento: AlignmentType.RIGHT, largura: LARGURAS_COLUNAS[1] }),
        celula(moeda(m.preco_final), { alinhamento: AlignmentType.RIGHT, largura: LARGURAS_COLUNAS[2] }),
      ],
    })
);

const linhaTotal = new TableRow({
  children: [
    celula("TOTAL GERAL", { negrito: true, corFundo: "D9E1F2", largura: LARGURAS_COLUNAS[0] }),
    celula("", { corFundo: "D9E1F2", largura: LARGURAS_COLUNAS[1] }),
    celula(moeda(dados.total), { negrito: true, corFundo: "D9E1F2", alinhamento: AlignmentType.RIGHT, largura: LARGURAS_COLUNAS[2] }),
  ],
});

const doc = new Document({
  sections: [
    {
      properties: { page: { size: { width: 12240, height: 15840 } } },
      children: [
        new Paragraph({ text: "Orcamento de Marcenaria", heading: HeadingLevel.TITLE }),
        new Paragraph({ text: `Cliente: ${dados.cliente || "-"}` }),
        new Paragraph({ text: `Projeto: ${dados.projeto || "-"}` }),
        new Paragraph({ text: "" }),
        new Table({
          width: { size: LARGURA_TABELA, type: WidthType.DXA },
          columnWidths: LARGURAS_COLUNAS,
          rows: [linhasCabecalho, ...linhasModulos, linhaTotal],
        }),
        new Paragraph({ text: "" }),
        new Paragraph({
          children: [
            new TextRun({
              text: `Markup aplicado: ${dados.divisor_markup.toFixed(4)}x  |  Comissao de vendas: ${(dados.pct_comissao_vendas_aplicada * 100).toFixed(1)}%  |  Faturamento acumulado informado: ${moeda(dados.faturamento_acumulado)}`,
              italics: true,
              size: 18,
              color: "666666",
            }),
          ],
        }),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(caminhoSaida, buffer);
  console.log(`Orcamento docx gerado: ${caminhoSaida}`);
});
