# Operação: Kit Parede Pronta (modelo enxuto em casa)

Modelo assumido (conversa de 2026-11-03):
- Um marceneiro com 20+ anos de experiência e orçamento de R$2.000.
- **Corte e aparelhamento terceirizados na madeireira.**
- Em casa: furação do pino com gabarito, lixa, selador e verniz à base d'água, conferência com foto e embalagem.
- Venda no Mercado Livre primeiro, conforme a condição do conselho (um produto e um canal por 90 dias, com foco no sob medida).

A cidade ainda não foi informada, então os fornecedores locais aparecem como "como achar". Os padrões de qualidade estão em `founder/quality-spec.md`.

## 1. O ciclo de cada dia

Os passos que o cliente vê estão marcados com 👁.

1. **8h00 — Pedidos:** abrir o Mercado Livre, separar os pedidos do dia (kit pronto × sob medida) e responder perguntas de quem ainda não comprou. 👁
2. **Sob medida:** confirmar a medida por escrito no chat, com o vão medido em 3 pontos e a data total de entrega. 👁
3. **Receber madeira** (quando chegar lote): conferir umidade no higrômetro, medula, empeno e esquadro, e devolver o que estiver fora do padrão.
4. **Furação** dos pinos com gabarito e conferência da altura dos dois lados.
5. **Lixa** (80 → 120 → 180) e **selador** em todas as faces, topos e furos.
6. **Verniz ou tingido**, 2 a 3 demãos, respeitando a secagem. É o gargalo do dia: as peças de hoje viram o envio de amanhã.
7. **Conferência:** checklist e foto do kit embalado, enviada ao cliente pelo chat. 👁
8. **Embalar:** separadores, cantoneiras, saquinho de ferragens fixado (com 1 peça extra de cada) e cartão pedindo foto da prateleira instalada.
9. **Etiqueta e postagem** até o horário de coleta ou agência do Mercado Livre. 👁
10. **Pós-venda:** responder mensagens e abrir reposição se alguém reclamar, com prazo de 2 dias úteis. 👁
11. **Fim do dia:** anotar no controle os kits feitos, o tempo gasto e a madeira usada.

**Capacidade (estimativa a medir):** com uma pessoa, a secagem do verniz limita mais do que a mão de obra. Cronometre os 10 primeiros kits. O CFO usou 5 kits/dia como plano e 20 como capacidade, mas a capacidade da casa provavelmente é menor.

## 2. Fornecedores

| Insumo | Opções | Preço público | Mínimo e prazo | Pendente |
|---|---|---|---|---|
| Pinus seco aparelhado 20 cm | Madeireira local (corte no comprimento); [Beija-Flor Madeiras](https://www.beijaflormadeiras.com.br/tabua-de-20-pinus-aparelhada/); [Leroy Merlin](https://www.leroymerlin.com.br/tabua-de-20-pinus-aparelhada_1570817377) | R$44,90 e R$58,37 por 3 m (~R$15–19,50/m) | Sem mínimo no varejo | **Cotar** corte no comprimento por kit e confirmar que é seco em estufa |
| Suporte invisível 20 cm | [MFL Acessórios](https://www.mflacessorios.com.br/suporte-metalico-invisivel-para-prateleira-20cm-ferro-38); [Desicon](https://www.desicon.com.br/suporte-invisivel-20-cm-preta) | R$7,60–9,55 a unidade | Desicon: frete grátis a partir de 36 un. | **Cotar atacado** (100+ un.) ou calcular o custo de fabricar pino e chapa |
| Caixa de papelão onda dupla (BC) ~70x25x15 | Fabricante de caixa sob medida da região; lojas de caixa no ML, como [GP Caixas](https://www.mercadolivre.com.br/loja/gp-caixas-de-papelao) | Não achei essa medida. Referência: caixas de onda dupla 40x30x30 de ~R$15 a R$30 a unidade ([busca ML](https://lista.mercadolivre.com.br/caixa-de-papelao-onda-dupla)) | Fabricantes costumam ter mínimo | **Cotar** com medida, onda BC e quantidade (50 un.) |
| Selador e verniz à base d'água | Loja de tintas local ou home center | — | — | Medir o rendimento por kit |
| Parafusos, buchas, cantoneiras, plástico | Distribuidor de ferragens local | — | — | Comprar em caixa fechada |
| Higrômetro de madeira | Home center ou ML | — | — | Compra única, entra no orçamento inicial |

**Frete:** é o maior custo ainda sem cotação, estimado em R$25. Simule com a caixa e o peso reais no simulador de custos do vendedor no Mercado Livre e atualize `numbers.json`.

## 3. Pessoas

- **Mês 1 (0,5–1 kit/dia):** só você.
  - Produção: 2 a 3 manhãs por semana.
  - Atendimento: 30 min por dia, de segunda a sábado.
  - Postagem: dia sim, dia não.
- **Plano (5 kits/dia):** ainda só você, em tempo integral.
  - **Produção:** segunda a sexta, de manhã.
  - **Verniz e secagem:** à tarde.
  - **Embalagem e postagem:** final da tarde.
  - **Atendimento:** duas janelas por dia (8h e 17h).
- **Quando contratar:** só quando a medição mostrar que você não dá conta e a margem real permitir. O CFO considerou um ajudante a R$4.000/mês com encargos (estimativa). Encargos de folha ficam para o contador.

## 4. Rotinas (SOPs)

**A. Abrir o dia (10 min)**
1. Ver os pedidos novos e o prazo de postagem de cada um.
2. Ver as mensagens e responder as perguntas de pré-venda primeiro (elas viram venda).
3. Conferir se as peças de ontem secaram e separar o que pode ser embalado hoje.

**B. Pedido sob medida**
1. Pedir no chat a medida do vão em 3 pontos (em cima, no meio e embaixo) e o tipo de parede.
2. Responder por escrito: medida final (a menor das 3), acabamento, data de postagem e data prevista de entrega.
3. Só começar a produzir depois do "ok" do cliente.
4. Cortar ou receber a peça, furar, conferir a medida com trena e anotar.

**C. Embalar e enviar**
1. Seguir o checklist: 3 prateleiras, pinos, parafusos e buchas (+1 de cada), gabarito, cartão.
2. Cada prateleira embrulhada, com separadores e cantoneiras.
3. Fotografar a caixa aberta com tudo dentro e enviar ao cliente pelo chat.
4. Fechar, etiquetar e postar.

**D. Reclamação**
1. Responder em até 4 horas úteis, com educação e sem discutir.
2. Pedir uma foto do problema.
3. Peça quebrada ou faltando: enviar a reposição em até 2 dias úteis, sem pedir devolução.
4. Medida errada por culpa nossa: refazer. Medida errada informada pelo cliente: oferecer refazer a preço de custo.
5. Registrar a causa no controle. Se a mesma causa aparecer 2 vezes, mudar o processo.

**E. Fechamento semanal (sexta, 30 min)**
1. Contar o estoque de madeira, suportes, caixas e ferragens.
2. Repor o que fica abaixo de 2 semanas de uso.
3. Anotar vendas, tempo por kit, reclamações e avaliações da semana.
4. Teste de carga do lote, se fecharam 50 peças.

## 5. Ferramentas

- **Mercado Livre e Mercado Pago:** venda e recebimento. Comissão do Clássico em Casa de cerca de 12% ([fonte](https://ecommercenapratica.com/blog/comissao-mercado-livre/), confirmar no simulador oficial).
- **Nota fiscal:** como MEI, pelo emissor gratuito do governo. Se precisar de integração, o Bling custa a partir de ~R$55/mês no plano Cobalto, segundo um [guia de 2026](https://gosmarter.com.br/?p=6032) (confirmar na página oficial). Comece sem ele e contrate só quando o volume pedir.
- **Controle:** uma planilha simples com pedidos, tempo por kit, custos, estoque e reclamações.

## 6. Registro, impostos e seguros

Confirme cada item com o órgão oficial ou com um contador. As regras mudam e variam por cidade. Isto não é aconselhamento jurídico nem tributário.

- [ ] **MEI:** confirme no [Portal do Empreendedor](https://www.gov.br/empresas-e-negocios/pt-br/empreendedor) qual ocupação de marceneiro é permitida e se ela recolhe ICMS e/ou ISS. O DAS em 2026 fica entre R$82,05 e R$87,05/mês, com base no salário mínimo de R$1.621 ([fonte](https://soubrasilia.com/servicos/mei/)).
- [ ] ⚠️ **Teto do MEI: R$81 mil/ano**, cerca de R$6.750/mês ([fonte](https://triviumcontabil.com.br/mei-em-2026-regras-custos-e-limites/)). O plano do CFO (5 kits/dia a R$169) daria uns R$25 mil/mês, muito acima disso. **No ritmo do plano, o MEI estoura por volta do 3º ou 4º mês.** Combine com o contador a passagem para ME no Simples, e saiba que o imposto muda: o CFO estimou 6%.
- [ ] **Alvará e uso do imóvel:** marcenaria em casa gera ruído e pó. Confira com a prefeitura (zoneamento e alvará do MEI) e com o condomínio, se houver.
- [ ] **CDC:** 7 dias de arrependimento em compra online e garantia legal de produto durável. A garantia de 12 meses vem por cima disso.
- [ ] **Seguro:** opcional no começo. Avalie seguro das ferramentas e responsabilidade civil quando o volume crescer.

## 7. Riscos

| # | Risco | Chance | Impacto | Plano |
|---|---|---|---|---|
| 1 | Suporte continua a ~R$8 a unidade e o kit dá prejuízo | Alta | Alto | Cotar atacado ou fabricar. Até resolver, vender só sob medida a R$169+ |
| 2 | Frete real acima de R$25 | Média | Alto | Simular antes de anunciar, reduzir dimensões da caixa e embutir parte no preço |
| 3 | Madeira da madeireira úmida ou com medula, que empena depois | Média | Alto | Conferir lote com higrômetro, devolver fora do padrão e ter 2 madeireiras |
| 4 | Poucas vendas no começo (loja sem avaliações) | Alta | Alto | Lançamento para os 30 primeiros, cartão pedindo foto e responder pré-venda rápido |
| 5 | Erro de medida no sob medida | Média | Médio | Confirmação por escrito em 3 pontos e conferência com trena antes de embalar |
| 6 | Chegar quebrado | Média | Médio | Teste de queda antes de lançar e reposição em 2 dias úteis |
| 7 | Avaliação negativa logo no começo | Média | Alto | Responder em público com a solução e corrigir a causa |
| 8 | Você doente ou sem tempo, e os pedidos atrasam | Baixa a média | Alto | Prazo de postagem com folga e pausar o anúncio se precisar |
| 9 | Estourar o teto do MEI sem perceber | Média (se vender bem) | Médio | Acompanhar o faturamento mensal e falar com o contador ao passar de R$5 mil/mês |
| 10 | Vizinho ou prefeitura reclamando do barulho | Baixa a média | Médio | Furação e lixa em horário comercial e confirmar o zoneamento antes |

## Perguntas em aberto

- Em que cidade você está? Define a madeireira, a caixa e o frete.
- Que máquinas você já tem: furadeira de bancada, lixadeira orbital, compressor ou pistola?
- Quanto custa o corte no comprimento na madeireira e o suporte no atacado (ou fabricado)?
- Qual é o frete real da caixa?
- Quanto tempo leva cada kit (medir nos 10 primeiros)?

**O CFO deve rodar de novo** depois das cotações, com o modelo enxuto e o imposto do MEI no lugar dos 6%. O `numbers.json` atual ainda é o cenário com galpão e ajudante.
