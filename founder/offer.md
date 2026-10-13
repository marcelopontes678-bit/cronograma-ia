# Oferta: Gestori Orçamento

Método: a lente Offers (`founder-board/lenses.md`, um resumo do framework de *$100M Offers*). Matéria-prima: as objeções do painel (`panel-v1/results.md`), os concorrentes (`competitors.md`), o preço (`pricing.md`) e as condições do conselho (`board.md`).

**Atenção sobre custos:** ainda não existe `numbers.json`. As notas de "custo para entregar" abaixo são **estimativas minhas**, não números do CFO. Rodar `/founder-cfo` antes de prometer a garantia em escala.

## 1. Lista de problemas (nas palavras do comprador)

**Antes de comprar**
1. "E se a IA ler errado o projeto, esquecer peça ou ferragem, e eu só descobrir na obra?" (dito por 15 de 20)
2. "Nunca ouvi ninguém dos grupos de marceneiro falar desse Gestori."
3. "Pagar quase 200 por mês num sistema cheio de coisa que eu não vou usar."
4. "Tem sistema de marcenaria por R$ 50 a 100."
5. "Minha tabela de preço e minha carteira de clientes ficam guardadas onde?"
6. "Se a empresa sumir ou eu quiser sair, levo meus dados comigo?"
7. "Duvido que a IA leia meu arquivo do Promob melhor que o próprio Promob."
8. "Já pago um sistema e minha equipe está acostumada."

**Durante (começar a usar)**
9. "Não tenho tempo para aprender e cadastrar tudo num sistema novo."
10. "Quem migra meus dados do sistema atual?"
11. "Passar minha planilha de preços para dentro, sem configurar tudo sozinho."
12. "Treinar 10, 20 pessoas num sistema novo."
13. "Sistema com CRM, estoque, produção, financeiro: não vou ter tempo de alimentar isso tudo."
14. "Se eu tiver que conferir peça por peça, perco o mesmo tempo."

**Depois (vai durar?)**
15. "Em um mês vira mais uma mensalidade esquecida."
16. "Já testei sistema antes e larguei depois de um mês."
17. "O que acontece se essa empresa pequena fechar?"
18. "O prejuízo de um orçamento errado paga anos dessa mensalidade."

## 2. Soluções, com nota e corte

Valor para o comprador e custo para entregar, de 1 a 5 (custo estimado).

| # | Solução | Resolve | Valor | Custo | Fica? |
|---|---|---|:-:|:-:|:-:|
| A | **Teste com projetos já fechados**: 30 dias grátis, sem cartão, comparando a IA com o que ele cobrou | 1, 7, 14, 18 | 5 | 2 (IA por projeto) | ✅ núcleo |
| B | **Plano só de orçamento**, sem exigir o resto do ERP | 3, 9, 13, 15 | 5 | 1 | ✅ núcleo |
| C | **Alerta de margem no desconto**, com o desconto rateado por item | dor citada por quem compra e por quem recusa | 5 | 1 (já existe) | ✅ núcleo |
| D | **Implantação por vídeo com o fundador** (cadastro da tabela de preço) | 9, 10, 11 | 4 | 3 (tempo do fundador) | ✅ bônus, limitado a 20 |
| E | **Seus dados são seus**: exportar em planilha, cancelar sem multa | 5, 6, 17 | 4 | 2 (**precisa ser construído**) | ✅ bônus |
| F | **Reembolso do primeiro mês pago** | 4, 15, 16 | 3 | 1 | ✅ garantia |
| G | **Preço travado por 12 meses** para os 20 primeiros | 4 | 3 | 1 | ✅ urgência real |
| H | Migração completa a partir de outro sistema | 8, 10, 12 | 4 | 5 (cada sistema é diferente) | ❌ caro demais agora |
| I | Treinamento presencial na fábrica | 12 | 3 | 5 | ❌ |
| J | Depoimentos de marceneiros | 2 | 5 | — | ❌ **não existem ainda**; nunca inventar. Virão dos 20 primeiros. |

## 3. A pilha da oferta

- **Nome:** Gestori Orçamento, com o **Teste dos Projetos Fechados**.
- **Núcleo (o resultado):** você manda o projeto e recebe o orçamento montado, com módulos e peças, para revisar. Quando dá desconto, você sabe na hora se algum ambiente ficou sem margem. Só o orçamento, sem cadastrar o resto do sistema.
- **Bônus 1, implantação com o fundador:** cadastro da tabela de preços por vídeo. Mata "não tenho tempo para cadastrar tudo".
- **Bônus 2, seus dados são seus:** exportação em planilha e cancelamento sem multa. Mata "e se a empresa sumir?".
- **Garantia:** o teste de 30 dias é grátis e sem cartão. Depois, se o primeiro mês pago (R$ 147) não valer a pena, o valor é devolvido. Custo no pior caso: R$ 147 por cliente que pedir.
- **Urgência verdadeira:** a implantação com o fundador e o preço travado por 12 meses valem só para as 20 primeiras marcenarias, até 31/03/2027. É real: o fundador não tem tempo para fazer mais de 20 implantações.
- **Preço:** R$ 147 por mês (ver `pricing.md`).

**Antes de vender, falta construir:**
- A **exportação completa em planilha** (clientes, preços, orçamentos). Hoje o Gestori só exporta o orçamento item a item.
- O **plano só de orçamento** no sistema (acesso limitado aos módulos de orçamento).
- **Retirar da tela de login** a frase "Mais de 300 marcenarias já usam o Gestori" (condição do conselho).

## 4. Equação de valor (antes e depois, de 1 a 10)

| Elemento | Antes (pitch v1) | Depois | O que mudou |
|---|:-:|:-:|---|
| Resultado dos sonhos (orçar rápido sem perder margem) | 7 | 8 | O núcleo foi descrito como resultado, e o alerta de margem foi para a frente |
| Probabilidade percebida de dar certo | 2 | 6 | Teste com os próprios projetos fechados e reembolso. Sobe pouco porque ainda não há prova de terceiros |
| Tempo até o resultado | 5 | 7 | O primeiro orçamento sai no teste, sem configurar o ERP |
| Esforço e sacrifício | 3 | 7 | Só orçamento, implantação feita pelo fundador e dados exportáveis |

## 5. Novo teste no painel
O mesmo painel (semente 400972, os mesmos 20 compradores) viu a nova oferta (`pitch.md`). O painel antigo está em `panel-v1/`.

| | Antes (pitch v1, R$ 197, ERP completo) | Depois (Gestori Orçamento, R$ 147) |
|---|:-:|:-:|
| Compram | **2 de 20 (10%)** | **6 de 20 (30%)** |
| Não compram por costume | 9 | 8 |
| Não compram por falta de confiança | 8 | **4** |
| Não compram por preço | 1 | 1 |

**O que mudou:**
- **A objeção de confiança caiu pela metade.** O teste com projetos já fechados convenceu 4 compradores que antes recusavam por desconfiança (P013, P014, P018, e P011 que recusava por costume). O argumento que os converteu foi o alerta de margem, que o Promob não dá: *"o Promob me dá preço mas não me avisa quando a margem de um ambiente foi pro chão"* (P003).
- **Ganhou entre quem usa planilha (3 de 5 compram)**, e não mais só entre os curiosos de IA.
- **O costume não mudou.** Quem já orça no Promob ou paga outro sistema continua dizendo que é "fazer o mesmo trabalho duas vezes". E um comprador que antes comprava (P009) desistiu, pelo mesmo motivo. Para esse grupo, o Gestori só serve se **substituir** o sistema atual (importar a tabela de preço dele) ou se **mostrar o prejuízo** do desconto num projeto já fechado.
- **Nova objeção:** onde ficam guardados a tabela de preço e os clientes, e quem tem acesso (P014, P018). A oferta fala em exportar, mas não diz onde os dados ficam. Responder isso no pitch.
- **O preço aceito caiu** com a oferta só de orçamento: faixa de R$ 50 a 245, ponto de indiferença em R$ 100 (antes R$ 77 a 300, indiferença R$ 150). Vendendo menos coisas, os compradores valorizam menos. R$ 147 continua dentro da faixa, mas acima da indiferença.

**Leitura honesta:** 30% é o teto, não a previsão. Compradores simulados tendem a concordar, e vários "sim" dependem de o teste acertar os projetos fechados. O resultado real vai depender da **taxa de acerto da IA em projetos de outras marcenarias**, que ainda não foi medida.

## Próximos passos
1. `/founder-cfo`: medir o custo de IA por orçamento e confirmar se R$ 147 dá margem, inclusive com o custo do teste grátis e do reembolso.
2. Antes de vender: construir a exportação completa, o plano só de orçamento e o "raio-x do desconto" (mostrar quanto o desconto custou num projeto já fechado); dizer no pitch onde os dados ficam guardados.
3. `/founder-marketing`: começar pelos donos que usam planilha e já perderam dinheiro com desconto.
