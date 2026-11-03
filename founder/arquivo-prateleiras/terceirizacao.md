# Cenário: terceirizar a produção e só montar e embalar em casa

Simulado com a ferramenta do CFO (`unit_economics.py`) a partir de `numbers.json`, com estas mudanças:
- **Custo fixo:** só contador (R$400) e internet/celular (R$200), sem galpão nem ajudante.
- **Investimento:** R$2.000 (o orçamento do fundador).
- **Volume:** a mesma rampa de antes, de 0,5 a 5 kits/dia.
- **Custo da terceirização** (corte, furação e acabamento) testado em R$20, R$35 e R$50 por kit. **Nenhum desses valores foi cotado.**

Valores em R$. Comissão (12%) e imposto (6%) recalculados sobre cada preço.

| Preço | Suporte + frete | Terceirizado/kit | Lucro por kit | Kits/dia p/ empatar | Ano 1 | Caixa necessário |
|---|---|---:|---:|---:|---:|---:|
| R$139 | R$48 + R$25 (hoje) | R$20 | -R$40,17 | nunca | -R$52.391 | R$54.391 |
| R$139 | R$24 + R$15 | R$20 | -R$6,17 | nunca | -R$14.141 | R$16.141 |
| R$169 | R$48 + R$25 (hoje) | R$20 | -R$15,57 | nunca | -R$24.716 | R$26.716 |
| **R$169** | **R$24 + R$15** | **R$20** | **+R$18,43** | **1,1** | **+R$13.534** | **R$2.371** |
| R$169 | R$24 + R$15 | R$35 | +R$3,43 | 5,8 | -R$3.341 | R$5.341 |
| R$169 | R$24 + R$15 | R$50 | -R$11,57 | nunca | -R$20.216 | R$22.216 |

**Conclusão:** só fecha a R$169 (sob medida), com suporte a cerca de R$4 a unidade, frete a R$15 e terceirização de no máximo ~R$20 por kit. O kit pronto a R$139 não fecha em nenhuma combinação testada.
