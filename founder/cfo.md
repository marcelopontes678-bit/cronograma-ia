# Nota do CFO: prateleira grossa sob medida (v2)

> Valores em **R$** (a ferramenta imprime "$"). Quase todos os custos são **estimativas**: madeira de 30 mm, corte, suporte reforçado, caixa e frete ainda não foram cotados. A versão anterior (kit 3x60 com galpão) está em `cfo-v1-kit-galpao.md` e `numbers-v1-kit-galpao.json`. Isto não é aconselhamento financeiro, contábil nem jurídico: um contador deve revisar.

**O modelo:**
- Uma prateleira de pinus 100x20x3 cm sob medida a **R$119**, cerca de R$119 por metro. É acima da concorrente de 15 mm (R$45/m) e perto da grossa de 30 mm (R$115 por 150 cm, ~R$77/m).
- Produção em casa, corte na madeireira, venda no Mercado Livre como MEI.
- Custo fixo de R$387 por mês e investimento de R$2.000.
- Volume: de 0,5 a 4 prateleiras por dia.

**O veredito: no preço base, empata e não sobra nada.**
- Cada prateleira custa **R$118,38** e deixa **R$0,62** (1%). O equilíbrio exige 20,8 peças por dia, acima da capacidade de 10.
- O ano 1 fecha em **-R$4.039**. O caixa necessário é de R$6.039, **acima dos R$2.000 que você tem**.
- A R$99, o preço da concorrência, cada peça **perde R$16,98**. **Competir por preço não funciona.**

**O que vira o jogo** (rodado na ferramenta):

| cenário | custo variável | lucro/peça | equilíbrio/dia | margem no plano | ano 1 | caixa |
|---|---:|---:|---:|---:|---:|---:|
| Base R$119 | R$118.38 | R$0.62 (1%) | 20.8 | -2% | R$-4,039 | R$6,039 |
| R$99 (perto da concorrente) | R$115.98 | R$-16.98 (-17%) | nunca | -20% | R$-21,199 | R$23,199 |
| R$139 | R$120.78 | R$18.22 (13%) | 0.7 | 11% | R$13,120 | R$2,114 |
| Suporte a R$5 un. (R$10) | R$108.38 | R$10.62 (9%) | 1.2 | 6% | R$5,711 | R$2,296 |
| Frete R$15 | R$108.38 | R$10.62 (9%) | 1.2 | 6% | R$5,711 | R$2,296 |
| Sem corte terceirizado (você corta) | R$108.38 | R$10.62 (9%) | 1.2 | 6% | R$5,711 | R$2,296 |
| R$119 + suporte R$10 + frete R$15 | R$98.38 | R$20.62 (17%) | 0.6 | 15% | R$15,461 | R$2,078 |
| Volume -20% | R$118.38 | R$0.62 (1%) | 20.8 | -3% | R$-4,160 | R$6,160 |
| R$99 + suporte R$10 + frete R$15 | R$95.98 | R$3.02 (3%) | 4.3 | -0% | R$-1,699 | R$3,699 |

**O que os números dizem:**
1. **Três alavancas valem ~R$10 por peça cada:** suporte a ~R$5 a unidade, frete de R$15 e você mesmo cortando a madeira. Cada uma, sozinha, já deixa o ano 1 positivo (+R$5.711) e o caixa cabe no orçamento (R$2.296).
2. **R$139 sozinho também resolve:** +R$18,22 por peça, equilíbrio em 0,7 peça por dia e ano 1 em +R$13.120. Com o painel, prateleira grossa e sob medida aguentam bem esse preço. **Teste R$119 contra R$139.**
3. **Melhor combinação testada:** R$119 + suporte a R$5 + frete a R$15 → **+R$20,62 por peça (17%)**, ano 1 em **+R$15.461** e caixa de R$2.078.

**⚠️ O que estes números não mostram:**
- **O seu trabalho não está na conta.** O "lucro" é o que sobra para pagar você. No melhor cenário, +R$15.461 no ano dá cerca de **R$1.290 por mês** para um trabalho que, com 4 peças por dia, ocupa boa parte do seu tempo. Isso é **abaixo do salário mínimo de R$1.621**. Para valer a pena, o lucro por peça precisa subir (preço de R$139, acabamento tingido, peças maiores) ou você precisa produzir mais por hora. **Cronometre suas horas por peça.**
- **O teto do MEI estoura.** O plano fatura cerca de R$116 mil no ano 1, acima do limite de R$81 mil. Por volta do 7º ou 8º mês você precisa virar ME, e aí o imposto passa a ser percentual sobre a venda e a margem cai. Fale com o contador.
- O frete grátis é obrigatório no Mercado Livre acima de R$79. Uma caixa longa (110 cm) pode custar bem mais que os R$25 estimados. **É a cotação que mais pode mudar o resultado.**

---

# Unit economics: Veio Certo - prateleira grossa de pinus 30 mm sob medida, producao em casa, venda no Mercado Livre (valores em R$)

Every number below comes from the input file. Nothing is looked up or guessed.

## One prateleira 100x20x3 cm

| line | per prateleira 100x20x3 cm |
| --- | ---: |
| Price | $119.00 |
| Pinus 30 mm x 20 cm, 1,15 m com perda (~R$24/m, derivado de R$17/m da tabua de 2,2 cm) [estimativa] | -$27.60 |
| Corte e aparelhamento na madeireira [estimativa, cotar] | -$10.00 |
| 2 suportes invisiveis reforcados p/ 30 mm (R$10 un. varejo) [estimativa sobre preco publico R$8-15] | -$20.00 |
| Lixa, selador, verniz base dagua [estimativa] | -$5.00 |
| Parafusos e buchas (+1 de cada), gabarito [estimativa] | -$3.00 |
| Caixa longa ~110x25x8 + cantoneiras [estimativa] | -$12.00 |
| Comissao ML Classico Casa ~12% [publico, blogs] | -$14.28 |
| Frete gratis pago pelo vendedor, ~3,5 kg [estimativa] | -$25.00 |
| Reserva da garantia: 5% x R$30 [estimativa] | -$1.50 |
| **Contribution** (what each prateleira 100x20x3 cm leaves to pay the fixed costs) | **$0.62** (1%) |

## The margin that matters

Fixed costs: $387 a month (DAS MEI 2026 (R$82,05-87,05) [publico] $87, Energia extra das maquinas em casa [estimativa] $100, Internet e celular [estimativa] $200).

- **Break-even: 21 prateleira 100x20x3 cms a day.** Below that you lose money every month.
- **Profit margin at your plan** (4 a day): **-2%** of every sale, after every cost.
- Capacity: 10 a day.

## Year 1, month by month

| month | prateleira 100x20x3 cms a day | revenue | profit | cumulative (after $2,000 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | $1,785 | -$378 | -$2,378 |
| 2 | 1 | $3,570 | -$368 | -$2,746 |
| 3 | 2 | $5,355 | -$359 | -$3,105 |
| 4 | 2 | $7,140 | -$350 | -$3,455 |
| 5 | 2 | $8,925 | -$340 | -$3,795 |
| 6 | 3 | $10,710 | -$331 | -$4,127 |
| 7 | 3 | $10,710 | -$331 | -$4,458 |
| 8 | 4 | $12,495 | -$322 | -$4,780 |
| 9 | 4 | $12,495 | -$322 | -$5,102 |
| 10 | 4 | $14,280 | -$313 | -$5,414 |
| 11 | 4 | $14,280 | -$313 | -$5,727 |
| 12 | 4 | $14,280 | -$313 | -$6,039 |

- **Year 1 operating profit: -$4,039** on $116,025 of revenue.
- After the $2,000 startup spend: -$6,039.
- Startup money earned back: not within year 1.
- Cash you need before it pays for itself: **$6,039**.

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | -2% | 21 | -$4,039 |
| Price -10% | -14% | never | -$15,642 |
| Volume -20% | -3% | 21 | -$4,160 |
| Unit costs +15% | -17% | never | -$21,353 |

## Red flags

- Break-even needs 21 prateleira 100x20x3 cms a day but capacity is 10.
- Year 1 loses money on operations (-$4,039).
- The startup spend is not earned back within year 1.
