# CFO: Gestori Orçamento

> **Como ler as tabelas abaixo:** a ferramenta escreve "$", mas tudo está em **R$**. Onde ela diz "a day", leia **"clientes pagantes no mês"** (cada linha é um mês, com o número de marcenarias assinando). Fontes de cada número: `cfo-sources.md`. Várias entradas são **estimativas**, marcadas assim.

## Nota do CFO

- **A margem:** cada marcenaria a R$ 147 deixa **R$ 95,33** (65%) depois dos custos dela: IA, imposto, taxa de cobrança e banco. Com 50 clientes, a margem de lucro é **58%**.
- **Ponto de equilíbrio:** **6 marcenarias pagantes** cobrem os custos fixos (R$ 495 por mês).
- **Ano 1:** com a rampa estimada (de 2 a 34 clientes), dá **R$ 14.175 de lucro operacional** sobre R$ 31.017 de receita. O dinheiro investido volta no **mês 7**.
- **Caixa necessário:** **R$ 2.418** antes de se pagar.
- **Esse lucro não paga o seu salário.** O pró-labore e o seu tempo de implantação e suporte não estão na conta. Com 34 clientes, o lucro é de cerca de R$ 2.700 por mês.

### A linha a observar: o custo de IA por cliente
É o custo que mais pode mudar, e ele depende de **quanto cada marcenaria usa**. A conta acima supõe 10 orçamentos de 5 páginas por mês (R$ 33,50). Um cliente pesado, com 30 orçamentos de 15 páginas (450 páginas), custaria cerca de **R$ 301 por mês só de IA** (450 × R$ 0,67). Ele daria **prejuízo de cerca de R$ 172 por mês** a R$ 147 (147 − 301 − 8,82 − 7,35 − 2). Os custos por unidade +15% já baixam o lucro do ano de R$ 14.175 para R$ 12.539.
**Por isso o plano precisa de um limite de uso** (por exemplo, até 15 orçamentos ou 75 páginas por mês, com cobrança extra acima disso). E é preciso **medir o custo real**: registrar os tokens de cada chamada da IA no Gestori.

### Três formas de melhorar a margem (rodadas na ferramenta)
1. **Cobrar R$ 197:** a contribuição sobe para R$ 145,33 (74%), o equilíbrio cai para 4 clientes e o lucro do ano 1 vai para **R$ 24.725**. Mas o painel achou R$ 197 "começando a ficar caro" (`pricing.md`).
2. **Baixar o custo de IA:** usar um modelo mais barato para páginas simples ou ler várias páginas por chamada. Se o custo cair à metade (R$ 16,75), a contribuição sobe cerca de R$ 16,75 por cliente (conta direta; não rodei na ferramenta). Testar se a qualidade se mantém.
3. **Não descer para R$ 97:** a contribuição cai para R$ 45,33, o equilíbrio sobe para 11 clientes e o lucro do ano 1 cai para **R$ 3.625**.

### As condições de dinheiro do conselho (`board.md`)
- "Medir o custo de servidor e de IA por orçamento antes de fixar o preço": **parcialmente atendida.** Há uma estimativa (R$ 0,67 por página, R$ 3,35 por orçamento de 5 páginas), mas ainda falta medir de verdade.
- "5 a 10 marcenarias pagantes": **não atendida.** O equilíbrio exige 6.

Isto não é assessoria financeira, contábil ou tributária. Um contador deve confirmar o enquadramento, os impostos e a estrutura da empresa antes de cobrar.

---

# Unit economics: Gestori Orçamento (SaaS para marcenarias)

Every number below comes from the input file. Nothing is looked up or guessed.

## One assinatura (1 marcenaria por mês)

| line | per assinatura (1 marcenaria por mês) |
| --- | ---: |
| Price | $147.00 |
| IA lendo projetos: 10 orçamentos x 5 páginas por mês (ESTIMATIVA) | -$33.50 |
| Imposto Simples Nacional, cerca de 6% da mensalidade (ESTIMATIVA) | -$8.82 |
| Taxa de cobrança (cartão/Pix/boleto), cerca de 5% (ESTIMATIVA) | -$7.35 |
| Banco de dados e armazenamento extra por cliente (ESTIMATIVA) | -$2.00 |
| **Contribution** (what each assinatura (1 marcenaria por mês) leaves to pay the fixed costs) | **$95.33** (65%) |

## The margin that matters

Fixed costs: $495 a month (Supabase Pro (US$ 25) $129, Render Starter, backend (US$ 7) $36, Domínio, e-mail e ferramentas (ESTIMATIVA) $30, Contador (ESTIMATIVA) $300).

- **Break-even: 6 assinatura (1 marcenaria por mês)s a day.** Below that you lose money every month.
- **Profit margin at your plan** (50 a day): **58%** of every sale, after every cost.

## Year 1, month by month

| month | assinatura (1 marcenaria por mês)s a day | revenue | profit | cumulative (after $2,000 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 2 | $294 | -$304 | -$2,304 |
| 2 | 4 | $588 | -$114 | -$2,418 |
| 3 | 7 | $1,029 | $172 | -$2,246 |
| 4 | 10 | $1,470 | $458 | -$1,787 |
| 5 | 13 | $1,911 | $744 | -$1,043 |
| 6 | 16 | $2,352 | $1,030 | -$13 |
| 7 | 19 | $2,793 | $1,316 | $1,303 |
| 8 | 22 | $3,234 | $1,602 | $2,906 |
| 9 | 25 | $3,675 | $1,888 | $4,794 |
| 10 | 28 | $4,116 | $2,174 | $6,968 |
| 11 | 31 | $4,557 | $2,460 | $9,428 |
| 12 | 34 | $4,998 | $2,746 | $12,175 |

- **Year 1 operating profit: $14,175** on $31,017 of revenue.
- After the $2,000 startup spend: $12,175.
- Startup money earned back: month 7.
- Cash you need before it pays for itself: **$2,418**.

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 58% | 6 | $14,175 |
| Price -10% | 53% | 7 | $11,073 |
| Volume -20% | 56% | 6 | $10,152 |
| Unit costs +15% | 53% | 6 | $12,539 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.
