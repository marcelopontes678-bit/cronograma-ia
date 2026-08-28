/**
 * Gera o orcamento final em .docx (proposta formatada para o cliente) a
 * partir de um JSON com o resultado ja calculado pelo engine Python
 * (modelo chapa fechada + fita de borda + ferragens).
 *
 * Uso: node gerar_orcamento_docx.js dados.json saida.docx
 *
 * Formato esperado do JSON de entrada (ver __main__ deste arquivo /
 * gerar_orcamento_xlsx.py):
 * {
 *   "cliente": "...", "projeto": "...",
 *   "divisor_markup": 2.76, "pct_comissao_vendas_aplicada": 0.05,
 *   "faturamento_acumulado": 100000,
 *   "chapas": [{ "acabamento": "18mm Branco", "num_chapas": 3, "preco_chapa": 334.9, "custo_chapas": 1004.7 }],
 *   "fitas": [{ "acabamento": "18mm Branco", "metros_total": 74.2, "preco_fita_metro": 26.9, "custo_fita": 1997.27 }],
 *   "ferragens": [{ "descricao": "Suporte", "custo": 19.8 }],
 *   "custo_material_total": 10155.66, "preco_venda_material": 28031.09,
 *   "custo_mao_de_obra": 806.25, "total": 28837.34
 * }
 */
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType,
} = require("docx");

const [, , caminhoJson, caminhoSaida] = process.argv;
if (!caminhoJson || !caminhoSaida) {
  console.error("Uso: node gerar_orcamento_docx.js dados.json saida.docx");
  process.exit(1);
}

const dados = JSON.parse(fs.readFileSync(caminhoJson, "utf-8"));

const moeda = (v) =>
  "R$ " + Number(v).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function celula(texto, { negrito = false, corFundo = null, alinhamento = AlignmentType.LEFT, largura, italico = false } = {}) {
  return new TableCell({
    width: { size: largura, type: WidthType.DXA },
    shading: corFundo ? { type: ShadingType.CLEAR, fill: corFundo } : undefined,
    children: [
      new Paragraph({
        alignment: alinhamento,
        children: [new TextRun({ text: String(texto), bold: negrito, italics: italico })],
      }),
    ],
  });
}

function secaoTabela(titulo, larguras, headers, linhas) {
  const larguraTotal = larguras.reduce((a, b) => a + b, 0);
  const linhaCabecalho = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) =>
      celula(h, { negrito: true, corFundo: "305496", alinhamento: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, largura: larguras[i] })
    ),
  });
  const linhasTabela = linhas.map(
    (valores) =>
      new TableRow({
        children: valores.map((v, i) => celula(v, { alinhamento: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, largura: larguras[i] })),
      })
  );
  return [
    new Paragraph({ text: titulo, heading: HeadingLevel.HEADING_2 }),
    new Table({ width: { size: larguraTotal, type: WidthType.DXA }, columnWidths: larguras, rows: [linhaCabecalho, ...linhasTabela] }),
    new Paragraph({ text: "" }),
  ];
}

const seqChapas = secaoTabela(
  "Chapas de MDF",
  [4680, 1560, 1560, 1560],
  ["Acabamento", "Num Chapas", "Preco/Chapa", "Custo"],
  (dados.chapas || []).map((c) => [c.acabamento, String(c.num_chapas), moeda(c.preco_chapa), moeda(c.custo_chapas)])
);

const seqFitas = secaoTabela(
  "Fita de Borda",
  [4680, 1560, 1560, 1560],
  ["Acabamento", "Metros", "Preco/Metro", "Custo"],
  (dados.fitas || []).map((f) => [f.acabamento, f.metros_total.toFixed(2), moeda(f.preco_fita_metro), moeda(f.custo_fita)])
);

const seqFerragens = secaoTabela(
  "Ferragens / Componentes",
  [7020, 2340],
  ["Descricao", "Custo"],
  (dados.ferragens || []).map((fe) => [fe.descricao, moeda(fe.custo)])
);

const linhasResumo = [
  ["Custo Material Total", moeda(dados.custo_material_total)],
  ["Preco Venda Material (x Markup)", moeda(dados.preco_venda_material)],
  ["Mao de Obra", moeda(dados.custo_mao_de_obra)],
];
const tabelaResumo = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [7020, 2340],
  rows: [
    ...linhasResumo.map(
      ([label, valor]) =>
        new TableRow({ children: [celula(label, { largura: 7020 }), celula(valor, { largura: 2340, alinhamento: AlignmentType.RIGHT })] })
    ),
    new TableRow({
      children: [
        celula("TOTAL GERAL", { negrito: true, corFundo: "D9E1F2", largura: 7020 }),
        celula(moeda(dados.total), { negrito: true, corFundo: "D9E1F2", largura: 2340, alinhamento: AlignmentType.RIGHT }),
      ],
    }),
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
        ...seqChapas,
        ...seqFitas,
        ...seqFerragens,
        new Paragraph({ text: "Resumo", heading: HeadingLevel.HEADING_2 }),
        tabelaResumo,
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
