# Preço: Gestori

Base: 20 compradores simulados (`panel/results.md`), concorrentes (`competitors.md`) e a curva de preço (`pricing-curve.md`). Os compradores simulados servem para escolher **o que testar**, não provam nada. Valores em R$ por mês.

## O que os compradores disseram (Van Westendorp)

| Ponto | Preço | O que significa |
|---|---:|---|
| Barato demais (PMC) | R$ 77 | Abaixo disso, muitos acham que não presta |
| Menor resistência (OPP) | R$ 79 | Tantos acham barato demais quanto caro demais |
| Indiferença (IPP) | R$ 150 | Tantos acham pechincha quanto acham caro |
| Caro demais (PME) | R$ 300 | Acima disso, muitos não compram |

**Faixa aceitável: R$ 77 a R$ 300.** Medianas das respostas: barato demais R$ 49, pechincha R$ 99, começa a ficar caro **R$ 197**, caro demais R$ 350.

R$ 197 está dentro da faixa, mas exatamente no ponto em que a pessoa típica diz "começa a ficar caro".

## O que os concorrentes cobram
- Sistemas específicos para marcenaria: de R$ 30 a 270 por mês, **mediana em torno de R$ 87** (Calctto R$ 47,90 a 97,90; SisMarcenaria Jotaerre cerca de R$ 57 a 87; WoodOrça+ R$ 49,90 mais R$ 29,90 de IA).
- O concorrente com a mesma promessa (Calcme + meX, orçamento com IA a partir do PDF) **não publica preço**.
- O ERP genérico Omie começa em R$ 309.

## O que o negócio precisa ganhar
**Ainda não dá para calcular.** Não existe `numbers.json`: o custo por cliente (servidor, banco de dados e, principalmente, a IA por orçamento lido) nunca foi medido. Sem isso, não sei a margem em nenhum preço. O `/founder-cfo` resolve; até lá, nenhum preço abaixo de R$ 147 deve ser fixado, porque o custo de IA pode comer a margem.

## 1. O preço recomendado: **R$ 147 por mês** pelo plano principal
- Fica perto do ponto de indiferença (R$ 150) e abaixo do "começa a ficar caro" (R$ 197) da maioria.
- Fica acima da mediana dos concorrentes (R$ 87), o que é sustentável só se o teste provar que a IA acerta. Para os compradores, o preço não foi o que travou: só 1 de 18 recusou por preço; 17 recusaram por costume ou falta de confiança.
- O valor final depende da margem que o `/founder-cfo` calcular.

## 2. A escada de planos
O painel pediu "só o orçamento, sem montar o resto do sistema". Então o produto de entrada é o orçamento, e o ERP vira o degrau seguinte:

| Plano | Preço | O que inclui | Por que subir |
|---|---:|---|---|
| **Orçamento** | R$ 147 | IA que lê PDF, DWG e Promob; motor de preço; desconto rateado com alerta de margem; 1 usuário | Entrada: resolve a dor que o painel mais citou |
| **Oficina** | R$ 247 | Orçamento + CRM, produção, agenda, painel do cliente; até 5 usuários | Quando a equipe precisa acompanhar a obra depois de fechar |
| **Fábrica** | R$ 397 | Tudo + estoque, financeiro, fichas técnicas; usuários ilimitados | Para marcenarias médias, que aceitaram preços mais altos no painel |

## 3. A oferta de lançamento (sem desconto falso)
- **Teste de 30 dias com projetos já fechados:** o marceneiro sobe 2 ou 3 projetos que já orçou e compara o resultado da IA com o que cobrou, peça por peça. Foi o pedido mais repetido do painel.
- **Implantação feita pelo fundador** (cadastro da tabela de preço) grátis para as **20 primeiras marcenarias**, até **31/03/2027**, o que vier primeiro.
- **Preço de fundador travado por 12 meses** para essas 20. É verdadeiro (o preço não sobe para elas) e não ensina ninguém a esperar promoção.
- Sem "de R$ X por R$ Y": nunca houve preço anterior.

## 4. O que testar com marceneiros reais
Dois preços dentro da faixa: **R$ 147 e R$ 197** pelo plano Orçamento.
- **Como testar:** duas mensagens de pré-venda nos grupos de WhatsApp e Facebook de marceneiros e no seu conteúdo, cada uma com um preço e um link de lista de espera ou pré-pagamento (por exemplo, um mês pago adiantado com reembolso garantido).
- **Meta para cada preço** (definir antes de começar): por exemplo, 10 marcenarias pagando em 3 semanas.
- Se nenhuma das duas bater a meta, o problema não é o preço, é a confiança: voltar para o `/founder-offer`.

## 5. Objeções de preço, nas palavras dos compradores (para o marketing responder)
1. "Pagar quase 200 por mês num sistema cheio de coisa que eu não vou usar, e não sei se essa IA lê direito o meu projeto do Promob ou se vou perder mais tempo corrigindo o orçamento do que fazendo na mão." (P015)
2. "Se eu tiver que conferir peça por peça, perco o mesmo tempo e ainda pago R$ 197 todo mês." (P005)
3. "Migrar meus dados e treinar 10, 20 pessoas num sistema novo de uma empresa que eu não conheço, pagando o dobro do que pago hoje." (P002)

São respostas de compradores simulados: servem de pesquisa, nunca de depoimento.

## Próximo passo
`/founder-offer` para montar a oferta (teste com projetos fechados, garantia, implantação) e testar de novo no painel. Depois, `/founder-cfo` para medir o custo por cliente e confirmar a margem em R$ 147.
