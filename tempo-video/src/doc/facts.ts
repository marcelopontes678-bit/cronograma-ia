/**
 * FONTE ÚNICA DE TODO TEXTO FACTUAL EXIBIDO NO VÍDEO.
 *
 * Regras seguidas (ver README-documentario.md):
 *  - Cada alegação tem status jurídico explícito (investigação / denúncia / condenação / anulada / arquivada),
 *    fonte e data. Nada de manchetes, citações ou números inventados.
 *  - Os dois candidatos recebem exatamente o mesmo formato, a mesma quantidade de itens e o mesmo tempo de tela.
 *  - Ordem dos candidatos: classificação no 1º turno (TSE).
 *  - Verificado em 20/10/2026. Antes de publicar, confira de novo nas fontes primárias (TSE, STF, STJ, TJ-RJ):
 *    o 2º turno é em 25/10/2026 e fatos podem mudar.
 */

export type Status = "INVESTIGAÇÃO" | "DENÚNCIA" | "CONDENAÇÃO" | "ANULADA" | "ARQUIVADA";

export const STATUS_LEGEND: { status: Status; meaning: string }[] = [
  { status: "INVESTIGAÇÃO", meaning: "apuração de fatos; não implica culpa" },
  { status: "DENÚNCIA", meaning: "acusação formal do Ministério Público" },
  { status: "CONDENAÇÃO", meaning: "decisão judicial de culpa" },
  { status: "ANULADA", meaning: "decisão sem efeito por vício processual" },
  { status: "ARQUIVADA", meaning: "acusação encerrada sem julgamento" },
];

export const ELECTION = {
  firstRound: "04/10/2026",
  runoff: "25/10/2026",
  results: [
    { name: "Flávio Bolsonaro", party: "PL", pct: "47,03%" },
    { name: "Lula", party: "PT", pct: "45,16%" },
  ],
  source: "Fonte: TSE, 100% das seções totalizadas · conforme imprensa em 05/10/2026",
};

/** Casos gerais da Cena 2 (sem citar números de réus, que variam entre fontes). */
export const CASES = [
  {
    title: "AÇÃO PENAL 470 — “MENSALÃO”",
    lines: ["Julgamento no Supremo Tribunal Federal", "iniciado em 02/08/2012."],
    status: "CONDENAÇÃO" as Status,
    statusNote: "réus condenados pelo STF",
    source: "Fonte: STF · Ação Penal 470",
  },
  {
    title: "OPERAÇÃO LAVA JATO",
    lines: ["Deflagrada pela Polícia Federal", "em 17/03/2014."],
    status: "INVESTIGAÇÃO" as Status,
    statusNote: "origem de múltiplos processos",
    source: "Fonte: Polícia Federal / MPF",
  },
];

/** Cena 3 — mesmo formato para os dois. */
export const CANDIDATES = [
  {
    id: "flavio",
    name: "Flávio Bolsonaro",
    party: "PL",
    role: "Senador pelo RJ desde 2019",
    firstRound: "47,03%",
    caseTitle: "Caso “rachadinha” (Alerj)",
    caseLines: ["Denúncia do MP-RJ em 2020.", "STJ anulou decisões da 1ª instância (09/11/2021).", "Denúncia arquivada a pedido do MP-RJ (TJ-RJ, 16/05/2022)."],
    status: "ARQUIVADA" as Status,
    defense: "Nega irregularidades.",
    source: "Fontes: STJ; TJ-RJ · Estado de Minas, 09/11/2021; Brasil de Fato, 16/05/2022",
  },
  {
    id: "lula",
    name: "Luiz Inácio Lula da Silva",
    party: "PT",
    role: "Presidente da República desde 2023",
    firstRound: "45,16%",
    caseTitle: "Lava Jato (tríplex e Atibaia)",
    caseLines: ["Condenações anuladas por incompetência", "da 13ª Vara de Curitiba (Fachin, 08/03/2021).", "Decisão confirmada pelo Plenário do STF (15/04/2021)."],
    status: "ANULADA" as Status,
    defense: "Nega irregularidades.",
    source: "Fontes: STF · Poder360, 15/04/2021",
  },
];

export const PROPOSALS_NOTE = "Planos de governo: registrados no TSE (DivulgaCandContas)";

export const FINAL_SOURCES = "Fontes: TSE · STF · STJ · TJ-RJ · PF/MPF — verificado em 20/10/2026";
export const DISCLAIMER = "Conteúdo informativo e apartidário.";
