# CFO: Gestori Orçamento

> **Como ler as tabelas abaixo:** a ferramenta escreve "$", mas tudo está em **R$**. Onde ela diz "a day", leia **"clientes pagantes no mês"** (cada linha é um mês, com o número de marcenarias assinando). Fontes de cada número: `cfo-sources.md`. Várias entradas são **estimativas**, marcadas assim.

## Nota do CFO

> **Atualizado em `/founder-ops`:** o imposto passou de 6% para **15,5%**. Software no Simples Nacional cai no Anexo V (15,5% inicial) se a folha, incluindo o pró-labore, ficar abaixo de cerca de 28% da receita (Fator R). Com o Fator R, cai no Anexo III (6%). Confirmar com o contador.

- **A margem:** cada marcenaria a R$ 147 deixa **R$ 81,36** (55%) depois dos custos dela: IA, imposto (Simples Anexo V, 15,5%), taxa de cobrança e banco. Com 50 clientes, a margem de lucro é **49%**.
- **Ponto de equilíbrio:** **7 marcenarias pagantes** cobrem os custos fixos (R$ 495 por mês).
- **Ano 1:** com a rampa estimada (de 2 a 34 clientes), dá **R$ 11.227 de lucro operacional** sobre R$ 31.017 de receita. O dinheiro investido volta no **mês 7**.
- **Caixa necessário:** **R$ 2.502** antes de se pagar.
- **Esse lucro não paga o seu salário.** O pró-labore e o seu tempo de implantação e suporte não estão na conta. Com 34 clientes, o lucro é de cerca de R$ 2.200 por mês.

### A linha a observar: o custo de IA por cliente
É o custo que mais pode mudar, e ele depende de **quanto cada marcenaria usa**. A conta acima supõe 10 orçamentos de 5 páginas por mês (R$ 33,50). Um cliente pesado, com 30 orçamentos de 15 páginas (450 páginas), custaria cerca de **R$ 301 por mês só de IA** (450 × R$ 0,67). Ele daria **prejuízo de cerca de R$ 186 por mês** a R$ 147 (147 − 301 − 22,79 − 7,35 − 2). Os custos por unidade +15% já também reduzem o lucro do ano (ver tabela "What if").
**Por isso o plano precisa de um limite de uso** (por exemplo, até 15 orçamentos ou 75 páginas por mês, com cobrança extra acima disso). E é preciso **medir o custo real**: registrar os tokens de cada chamada da IA no Gestori.

### Três formas de melhorar a margem (rodadas na ferramenta)
1. **Cobrar R$ 197:** a contribuição sobe para R$ 131,36 (67%), o equilíbrio cai para 4 clientes e o lucro do ano 1 vai para **R$ 21.777**. Mas o painel achou R$ 197 "começando a ficar caro" (`pricing.md`).
2. **Baixar o custo de IA:** usar um modelo mais barato para páginas simples ou ler várias páginas por chamada. Se o custo cair à metade (R$ 16,75), a contribuição sobe cerca de R$ 16,75 por cliente (conta direta; não rodei na ferramenta). Testar se a qualidade se mantém.
3. **Não descer para R$ 97:** a contribuição cai para R$ 31,36, o equilíbrio sobe para 16 clientes e o lucro do ano 1 cai para **R$ 677**.

### As condições de dinheiro do conselho (`board.md`)
- "Medir o custo de servidor e de IA por orçamento antes de fixar o preço": **parcialmente atendida.** Há uma estimativa (R$ 0,67 por página, R$ 3,35 por orçamento de 5 páginas), mas ainda falta medir de verdade.
- "5 a 10 marcenarias pagantes": **não atendida.** O equilíbrio exige 7.

Isto não é assessoria financeira, contábil ou tributária. Um contador deve confirmar o enquadramento, os impostos e a estrutura da empresa antes de cobrar.

---

# Unit economics: Gestori Orçamento (SaaS para marcenarias)

Every number below comes from the input file. Nothing is looked up or guessed.

## One assinatura (1 marcenaria por mês)

| line | per assinatura (1 marcenaria por mês) |
| --- | ---: |
| Price | $147.00 |
| IA lendo projetos: 10 orçamentos x 5 páginas por mês (ESTIMATIVA) | -$33.50 |
| Imposto Simples Nacional, Anexo V inicial 15,5% (sem Fator R; ESTIMATIVA, confirmar com contador) | -$22.79 |
| Taxa de cobrança (cartão/Pix/boleto), cerca de 5% (ESTIMATIVA) | -$7.35 |
| Banco de dados e armazenamento extra por cliente (ESTIMATIVA) | -$2.00 |
| **Contribution** (what each assinatura (1 marcenaria por mês) leaves to pay the fixed costs) | **$81.36** (55%) |

## The margin that matters

Fixed costs: $495 a month (Supabase Pro (US$ 25) $129, Render Starter, backend (US$ 7) $36, Domínio, e-mail e ferramentas (ESTIMATIVA) $30, Contador (ESTIMATIVA) $300).

- **Break-even: 7 assinatura (1 marcenaria por mês)s a day.** Below that you lose money every month.
- **Profit margin at your plan** (50 a day): **49%** of every sale, after every cost.

## Year 1, month by month

| month | assinatura (1 marcenaria por mês)s a day | revenue | profit | cumulative (after $2,000 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 2 | $294 | -$332 | -$2,332 |
| 2 | 4 | $588 | -$170 | -$2,502 |
| 3 | 7 | $1,029 | $75 | -$2,427 |
| 4 | 10 | $1,470 | $319 | -$2,109 |
| 5 | 13 | $1,911 | $563 | -$1,546 |
| 6 | 16 | $2,352 | $807 | -$739 |
| 7 | 19 | $2,793 | $1,051 | $312 |
| 8 | 22 | $3,234 | $1,295 | $1,606 |
| 9 | 25 | $3,675 | $1,539 | $3,145 |
| 10 | 28 | $4,116 | $1,783 | $4,929 |
| 11 | 31 | $4,557 | $2,027 | $6,956 |
| 12 | 34 | $4,998 | $2,271 | $9,227 |

- **Year 1 operating profit: $11,227** on $31,017 of revenue.
- After the $2,000 startup spend: $9,227.
- Startup money earned back: month 7.
- Cash you need before it pays for itself: **$2,502**.

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 49% | 7 | $11,227 |
| Price -10% | 43% | 8 | $8,125 |
| Volume -20% | 47% | 7 | $7,794 |
| Unit costs +15% | 42% | 7 | $9,149 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.
