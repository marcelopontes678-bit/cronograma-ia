# Nota do CFO: tábua de corte end grain (v3)

> Valores em **R$** (a ferramenta imprime "$"). A maior parte dos custos é **estimativa**:
> - **madeira nobre:** a ~R$6.000/m³, com o dobro do volume final para cobrir a perda. Não achei preço público de marfim e muiracatiara, então é o primeiro número a cotar;
> - **frete** e **embalagem**;
> - **tempo por tábua:** 3,5 h, com produção em lote.
>
> Têm fonte pública: cola Titebond III, frasco de óleo, comissão do ML e DAS do MEI.
>
> Versões anteriores: `cfo-v1-kit-galpao.md` (kit e galpão) e `cfo-v2-prateleira-grossa.md`. Isto não é aconselhamento financeiro, contábil nem jurídico.

**Modelo:** tábua 40x30x4 a **R$249** de lançamento, R$349 depois. Produção em casa, venda no ML como MEI, custo fixo de R$387/mês, investimento de R$2.000. Volume de 0,3 a 2 tábuas/dia, com capacidade de 3/dia.

**Veredito: é o primeiro modelo que fecha.**
- Cada tábua custa **R$165,64** e deixa **R$83,36 (33%)**.
- Equilíbrio: **0,15 tábua/dia** (cerca de 5 por mês).
- Margem no plano: **31%**. Ano 1: **+R$35.619** de operação, com R$120.267 de receita.
- Os R$2.000 voltam no **3º mês**. O caixa necessário é **R$2.000**, ou seja, cabe no seu orçamento.

**Cenários** (rodados na ferramenta; a comissão é recalculada pelo preço):

| cenário | lucro por tábua | equilíbrio/dia | ano 1 (operação) | contribuição/mês (2 tábuas × 22 dias úteis) | por hora (3,5 h/tábua) |
|---|---:|---:|---:|---:|---:|
| Base R$249 (lançamento) | R$83.36 (33%) | 0.15 | R$35,619 | R$3,668 | R$24/h |
| R$349 (preço cheio) | R$171.36 (49%) | 0.08 | R$78,123 | R$7,540 | R$49/h |
| Madeira mais cara (R$90) | R$53.36 (21%) | 0.24 | R$21,129 | R$2,348 | R$15/h |
| Frete R$35 | R$73.36 (29%) | 0.18 | R$30,789 | R$3,228 | R$21/h |
| Frete R$15 | R$93.36 (37%) | 0.14 | R$40,449 | R$4,108 | R$27/h |
| Volume -20% | R$83.36 (33%) | 0.15 | R$27,566 | R$3,668 | R$24/h |
| R$249 + madeira R$90 + frete R$35 (pior caso) | R$43.36 (17%) | 0.30 | R$16,299 | R$1,908 | R$12/h |
| R$349 + madeira R$90 + frete R$35 | R$131.36 (38%) | 0.10 | R$58,803 | R$5,780 | R$38/h |

**O que os números dizem:**
1. **O preço é a maior alavanca.** A R$349, o lucro por tábua sobe para R$171 (49%) e o ano 1 para +R$78.123. O painel mostrou que a renda alta aceita esse valor. **Teste R$249 contra R$349.**
2. **A madeira é a linha a vigiar.** Se custar R$90 por tábua em vez de R$60, o lucro cai para R$53. Cote marfim e muiracatiara antes de tudo. **Use sobras de outros trabalhos sempre que der.**
3. **Mesmo no pior caso testado** (R$249, madeira a R$90, frete a R$35), sobram R$43 por tábua e o ano fecha positivo (+R$16.299).

**⚠️ O que estes números não mostram:**
- **O seu trabalho não está na conta.** A 3,5 h por tábua, o lucro por hora fica em **~R$24/h a R$249** e **~R$49/h a R$349**. Para comparar: a prateleira grossa dava perto de zero. No plano de 2 tábuas/dia, são cerca de 7 h/dia de bancada. **Cronometre as 5 primeiras tábuas:** se passar de 5 h cada, o preço precisa subir.
- **O teto do MEI estoura.** São R$120 mil de receita no ano 1, acima do limite de R$81 mil. Por volta do 8º mês você precisa virar ME, e o imposto passa a ser percentual sobre a venda. Fale com o contador.
- **A demanda é sazonal (Natal e Dia dos Pais),** e a rampa não modela isso. O ano real terá picos e vales.
- **Regras para utensílio de cozinha:** confirme as exigências da Anvisa e do Inmetro para tábua de madeira em contato com alimento antes de vender.

---

# Unit economics: Veio Certo - tabua de corte end grain 40x30x4 (marfim + muiracatiara), producao em casa, venda no Mercado Livre (valores em R$)

Every number below comes from the input file. Nothing is looked up or guessed.

## One tabua end grain 40x30x4

| line | per tabua end grain 40x30x4 |
| --- | ---: |
| Price | $249.00 |
| Madeira nobre: ~0,01 m3 com perda (2x o volume final) a ~R$6.000/m3 [estimativa, cotar] | -$60.00 |
| Cola Titebond III ~50 g (R$110,94 por 1,05 kg) [publico] | -$5.30 |
| Lixas (topo consome muita lixa) [estimativa] | -$8.00 |
| Oleo mineral + cera alimentar no acabamento [estimativa] | -$4.00 |
| Frasco de oleo 100 ml para o cliente (R$8,56 farmacia) [publico] | -$8.56 |
| 4 pes antiderrapantes [estimativa] | -$4.00 |
| Embalagem de presente (caixa kraft + cartao) [estimativa] | -$10.00 |
| Caixa de envio e protecao [estimativa] | -$6.00 |
| Comissao ML Classico Casa ~12% [publico, blogs] | -$29.88 |
| Frete gratis pago pelo vendedor, ~4,5 kg [estimativa] | -$25.00 |
| Reserva garantia (3% x R$80) + atraso de Natal (5% x R$50 no ano) [estimativa] | -$4.90 |
| **Contribution** (what each tabua end grain 40x30x4 leaves to pay the fixed costs) | **$83.36** (33%) |

## The margin that matters

Fixed costs: $387 a month (DAS MEI 2026 [publico] $87, Energia extra das maquinas [estimativa] $100, Internet e celular [estimativa] $200).

- **Break-even: 1 tabua end grain 40x30x4s a day.** Below that you lose money every month.
- **Profit margin at your plan** (2 a day): **31%** of every sale, after every cost.
- Capacity: 3 a day.

## Year 1, month by month

| month | tabua end grain 40x30x4s a day | revenue | profit | cumulative (after $2,000 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | $2,241 | $363 | -$1,637 |
| 2 | 0 | $3,735 | $863 | -$773 |
| 3 | 1 | $5,976 | $1,614 | $840 |
| 4 | 1 | $7,470 | $2,114 | $2,954 |
| 5 | 1 | $8,964 | $2,614 | $5,568 |
| 6 | 2 | $11,205 | $3,364 | $8,932 |
| 7 | 2 | $11,205 | $3,364 | $12,296 |
| 8 | 2 | $11,205 | $3,364 | $15,661 |
| 9 | 2 | $13,446 | $4,114 | $19,775 |
| 10 | 2 | $14,940 | $4,615 | $24,390 |
| 11 | 2 | $14,940 | $4,615 | $29,004 |
| 12 | 2 | $14,940 | $4,615 | $33,619 |

- **Year 1 operating profit: $35,619** on $120,267 of revenue.
- After the $2,000 startup spend: $33,619.
- Startup money earned back: month 3.
- Cash you need before it pays for itself: **$2,000**.

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 31% | 1 | $35,619 |
| Price -10% | 23% | 1 | $23,592 |
| Volume -20% | 30% | 1 | $27,566 |
| Unit costs +15% | 21% | 1 | $23,618 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.
