# Nota do CFO (leia primeiro)

> Valores em **R$**: a ferramenta imprime "$", mas tudo está em reais. Quase todos os custos são **estimativas** (veja `founder/cfo-sources.md`). Troque pelos orçamentos reais e rode de novo. Isto não é aconselhamento financeiro, contábil nem jurídico: um contador deve revisar enquadramento (MEI/Simples), folha e impostos antes de qualquer dinheiro sair.

**Veredito: do jeito que está, cada kit dá prejuízo antes mesmo do aluguel.**

- **A margem:** vendendo o kit a R$139, o custo variável é R$159,17, então cada kit **perde R$20,17**. Com 5 kits por dia, a margem fica em **-54%** e o ano 1 fecha em **-R$122.291** de operação (-R$162.591 contando o investimento). Ponto de equilíbrio: nunca.
- **O lançamento a R$119** perde **R$36,57 por kit**. Os 30 pedidos de lançamento custam cerca de R$1.097 em prejuízo. Dá para pagar isso conscientemente como custo de comprar as primeiras avaliações, mas só se o resto for corrigido.
- **A linha que mais pesa: os 6 suportes invisíveis (R$48, 30% do custo).** Logo depois vêm o frete grátis (R$25, estimado) e a madeira (R$37,40).
- **Caixa:** no modelo atual, a necessidade de caixa não para de crescer (R$162.591 no ano 1). Começar do zero, com galpão (R$3.100) e ajudante (R$4.000), é o que transforma um produto de margem fina num buraco. São R$8.300 por mês de custo fixo contra um produto que hoje não contribui nada.

## Três formas de melhorar (rodadas na ferramenta, não chutadas)

| mudança | contribuição por kit | equilíbrio/dia | ano 1 (operação) |
|---|---:|---:|---:|
| Base (R$139) | -R$20,17 | nunca | -R$122.291 |
| 1. Suporte em atacado a ~R$4 por unidade (R$24 o kit) | +R$3,83 | 72 | -R$95.291 |
| 2. Frete subsidiado caindo para R$15 | -R$10,17 | nunca | -R$111.041 |
| 3. Preço médio R$169 (vender mais sob medida) | +R$4,43 | 62 | -R$94.616 |
| **1 + 2 + 3 juntas (R$169)** | **+R$38,43 (23%)** | **7,2** | **-R$56.366** |
| 1 + 2 a R$189 (tingido) | +R$54,83 (29%) | 5,0 | -R$37.916 |
| **1 + 2 + 3 sem galpão nem ajudante** (fixo R$1.200/mês) | +R$38,43 | **1,0** | **+R$28.834** |

Nos cenários com mudança de preço, a comissão (12%) e o imposto (6%) foram recalculados sobre o novo preço.

O que os números dizem:
1. **Renegocie o suporte primeiro.** É a única mudança que, sozinha, deixa o kit de R$139 no positivo. Peça cotação de atacado (a Desicon vende com frete grátis a partir de 36 unidades) ou troque por um suporte de barra única por prateleira.
2. **O kit pronto de R$139 não paga um galpão.** O dinheiro está no sob medida (R$169) e no tingido (R$189). O sob medida tem mais mão de obra, e isso não está modelado. Meça o tempo real por peça.
3. **Não comece com galpão e funcionário.** Com custo fixo de R$1.200 (oficina em casa ou garagem, só você produzindo), o equilíbrio cai para cerca de 1 kit por dia e o ano 1 fecha positivo na operação (+R$28.834). Ainda falta pagar as máquinas: o resultado depois do investimento é -R$11.466. Valide as vendas primeiro e alugue depois.

**Volume (ramp):** de 0,5 kit/dia no mês 1 até 5/dia no mês 10, 150 por mês no plano. O painel simulado deu 25% de compra no teto, mas isso não diz quantas pessoas veem o anúncio. É a premissa mais frágil, e só os primeiros 30 dias reais vão dizer. Com volume -20% o ano 1 piora menos (porque cada venda dá prejuízo), o que é mais um sinal de que o problema é o custo por kit.

Board: `founder/board.md` não existe, então não há condições a verificar.

---

# Unit economics: Kit Parede Pronta - marcenaria nova vendendo em marketplaces (valores em R$)

Every number below comes from the input file. Nothing is looked up or guessed.

## One kit (3 prateleiras 60x20 pinus macico)

| line | per kit (3 prateleiras 60x20 pinus macico) |
| --- | ---: |
| Price | $139.00 |
| Pinus aparelhado 20cm, 2,2 m com perda (R$17/m) [publico] | -$37.40 |
| 6 suportes invisiveis 20cm (R$8,00 un.) [publico] | -$48.00 |
| Lixa, selador, verniz [estimativa] | -$6.00 |
| Parafusos, buchas, gabarito impresso [estimativa] | -$4.00 |
| Caixa reforcada, cantoneiras, plastico bolha [estimativa] | -$12.00 |
| Comissao ML Classico Casa ~12% de R$139 [publico, blogs] | -$16.68 |
| Frete gratis pago pelo vendedor, caixa ~5 kg [estimativa] | -$25.00 |
| Imposto Simples Nacional ~6% de R$139 [estimativa] | -$8.34 |
| Reserva da garantia: 5% dos pedidos x R$35 de reposicao [estimativa] | -$1.75 |
| **Contribution** (what each kit (3 prateleiras 60x20 pinus macico) leaves to pay the fixed costs) | **-$20.17** (-15%) |

## The margin that matters

Fixed costs: $8,300 a month (Aluguel galpao 100 m2 [publico, anuncio Sorocaba] $3,100, 1 ajudante de marcenaria com encargos [estimativa] $4,000, Energia das maquinas [estimativa] $600, Contador [estimativa] $400, Internet, celular, software [estimativa] $200).

- **Break-even: never (each unit loses money) kit (3 prateleiras 60x20 pinus macico)s a day.** Below that you lose money every month.
- **Profit margin at your plan** (5 a day): **-54%** of every sale, after every cost.
- Capacity: 20 a day.

## Year 1, month by month

| month | kit (3 prateleiras 60x20 pinus macico)s a day | revenue | profit | cumulative (after $40,300 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | $2,085 | -$8,603 | -$48,903 |
| 2 | 1 | $4,170 | -$8,905 | -$57,808 |
| 3 | 2 | $6,255 | -$9,208 | -$67,015 |
| 4 | 2 | $8,340 | -$9,510 | -$76,526 |
| 5 | 2 | $10,425 | -$9,813 | -$86,338 |
| 6 | 3 | $12,510 | -$10,115 | -$96,454 |
| 7 | 4 | $14,595 | -$10,418 | -$106,871 |
| 8 | 4 | $16,680 | -$10,720 | -$117,592 |
| 9 | 4 | $18,765 | -$11,023 | -$128,615 |
| 10 | 5 | $20,850 | -$11,326 | -$139,940 |
| 11 | 5 | $20,850 | -$11,326 | -$151,266 |
| 12 | 5 | $20,850 | -$11,326 | -$162,591 |

- **Year 1 operating profit: -$122,291** on $156,375 of revenue.
- After the $40,300 startup spend: -$162,591.
- Startup money earned back: not within year 1.
- Cash you need before it pays for itself: **$162,591**.

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | -54% | never | -$122,291 |
| Price -10% | -71% | never | -$137,929 |
| Volume -20% | -64% | never | -$117,753 |
| Unit costs +15% | -71% | never | -$149,151 |

## Red flags

- Each unit loses money before rent and salaries: the price is below the variable cost.
- Break-even needs inf kit (3 prateleiras 60x20 pinus macico)s a day but capacity is 20.
- Year 1 loses money on operations (-$122,291).
- The startup spend is not earned back within year 1.
