# Kit Parede Pronta (nome de trabalho) · Business plan

**Verdict: Not yet**

- ✗ Each kit (3 prateleiras 60x20 pinus macico) LOSES $20.17 before fixed costs.
- ✗ Year 1 operating LOSS: $122,291.
- ✗ Break-even is never reached kit (3 prateleiras 60x20 pinus macico)s a day against a capacity of 20.
- ✗ 2 of 20 simulated buyers buy (10%, the bar is 25%).

| key number | |
| --- | ---: |
| Price | $139.00 a kit (3 prateleiras 60x20 pinus macico) |
| Profit margin at plan | -54% per kit (3 prateleiras 60x20 pinus macico) |
| Break-even | never kit (3 prateleiras 60x20 pinus macico)s a day |
| Year 1 operating profit | $-122,291 |
| Startup spend | $40,300 |
| Cash needed before it pays for itself | $162,591 |
| Startup money earned back | not in year 1 |
| Buyer panel | 2 buy · 18 pass |

## The idea

- O que é: uma marcenaria nova que fabrica prateleiras e nichos em madeira maciça e vende pelos marketplaces brasileiros (Mercado Livre, Shopee e, depois, Elo7 e MadeiraMadeira).
- Para quem: brasileiros de 25 a 45 anos montando ou decorando apartamento, que compram móveis pequenos pelo celular em marketplaces.
- O que vende e a que preço: kit com 3 prateleiras flutuantes 60x20 em pinus maciço, R$139 (lançamento a R$119 nos 30 primeiros pedidos ou até 31/12/2026); sob medida até 120 cm a R$169; sob medida com acabamento tingido a R$189.
- Onde e como: online, com envio pelos Correios ou transportadora do marketplace; postagem em 1 dia útil; sob medida em 7 dias úteis.
- Orçamento e restrições: o fundador é marceneiro há mais de 20 anos. Orçamento disponível: R$2.000. Antes ele disse que começa do zero (sem oficina nem máquinas); falta confirmar quais máquinas e que espaço já tem. Os custos são estimativas até chegarem orçamentos reais.
- Padrão de qualidade: `founder/quality-spec.md`.

## Summary

**Veredito: Not yet (ainda não).** Três das quatro checagens falham por causa do custo, não da demanda. O que precisa mudar, em ordem:

1. **Custo por kit** (`/founder-cfo`). O kit de R$139 custa R$159,17 para produzir e entregar e **perde R$20,17 por venda**. O item mais caro são os 6 suportes invisíveis (R$48). Cote no atacado ou troque o tipo de suporte.
2. **Estrutura** (`/founder-ops` + `/founder-cfo`). Galpão e ajudante somam R$8.300 por mês de custo fixo, contra um produto que hoje não contribui nada. Comece produzindo em casa ou numa garagem.
3. **Mix de preço** (`/founder-pricing`). O dinheiro está no sob medida (R$169) e no tingido (R$189), não no kit pronto.

**O negócio:** uma marcenaria nova vendendo prateleiras em madeira maciça de pinus pelo Mercado Livre e pela Shopee. O público são pessoas de 25 a 45 anos decorando apartamento pelo celular. A oferta é o *Kit Parede Pronta*: foto do kit do cliente antes do envio, reposição sem devolver a peça e acabamento à escolha.

**Os três números (plano a R$139, 5 kits/dia):**
- Contribuição por kit: **-R$20,17 (-15%)**. Margem no plano: **-54%**.
- Ponto de equilíbrio: **nunca**, porque cada venda perde dinheiro.
- Ano 1: **-R$122.291** de operação e -R$162.591 depois do investimento de R$40.300.

Com suporte a ~R$4, frete a R$15, preço médio de R$169 e sem galpão nem ajudante (custo fixo de R$1.200/mês), a ferramenta dá **+R$38,43 por kit, equilíbrio em ~1 kit/dia e +R$28.834 no ano 1** de operação. Esse cenário ainda não é o plano: ele depende de uma cotação de suporte que ainda não existe.

**O que o painel disse:**
- Com o pitch original (R$149), compraram **2 de 20 (10%)**. Esse é o número que o compilador usa, e ele fica abaixo da meta de 25%.
- Com o Kit Parede Pronta a R$119 (`founder/panel-v2/`), compraram **5 de 20 (25%)**. Mas R$119 perde R$36,57 por kit, e o preço mudou junto com a oferta.
- Nas duas rodadas o principal motivo de recusa foi o mesmo: **loja nova sem avaliações** (14 e 11 recusas). O preço veio bem atrás (3 em cada rodada).
- O conselho (`/founder-board`) não rodou, então não há com o que comparar.

**Concorrência:** existe uma lacuna real entre o MDF de R$60–72 e a madeira de R$246 ou mais. As reclamações mais comuns do setor são peça faltando e produto chegando quebrado. Isso é problema de processo e embalagem, e a oferta resolve as duas.

**Maior risco:** confiança. Ninguém compra de loja sem avaliações, e cada avaliação inicial custa prejuízo. O plano é vender os 30 primeiros a preço de lançamento, pedir foto da prateleira instalada e não oferecer nada em troca de nota positiva. O custo desses 30 é de cerca de R$1.100 a R$119, ou zero se o custo for corrigido antes.

**Para começar:** no modelo atual, o caixa necessário passa de R$162 mil, o que é inviável. No modelo enxuto, ele cai para cerca de R$41 mil, quase todo em máquinas e caução. Quem já tiver as máquinas precisa de bem menos. O primeiro teste real (`/founder-launch`): anunciar o kit no Mercado Livre com 10 a 20 unidades e medir visitas, conversão e reclamações.

**Esta semana:** pedir **cotação de atacado do suporte invisível 20 cm** (Desicon, MFL ou distribuidor) e **simular o frete real** da caixa no Mercado Livre. São os dois números que decidem se o kit dá lucro.

_O painel são compradores simulados e os números são projeções a partir de estimativas. Orçamentos e clientes reais confirmam tudo isso. Isto não é aconselhamento financeiro, jurídico nem tributário: um contador deve revisar enquadramento, folha e impostos._

## What the board said

**Votação: 2 FUND IF, 1 PASS. Nota média: 3,7 de 10.**
- Ofertas: 4 (FUND IF)
- Produto: 4 (FUND IF)
- Monopólio: 3 (PASS)

Os memos completos estão em `founder/board/`. As lentes são resumos de frameworks publicados, não a opinião dos autores.

### Riscos levantados por mais de um membro

1. **Cada kit perde R$20,17** (os 3 membros). O cenário que dá lucro depende de um suporte a ~R$4 que ninguém cotou ainda.
2. **Loja nova sem avaliações** (Ofertas e Monopólio, e Produto pela ótica da experiência). Foi o motivo nº 1 das recusas nas duas rodadas do painel.
3. **O sob medida é o único sinal real de demanda** (Produto e Monopólio). Os dois compradores do primeiro painel compraram porque precisavam de medida exata.

### Onde discordam

- **Ofertas** acha que o problema tem conserto pela oferta e pelo preço. Pergunta por que cobrar R$139 se o painel aceitava até R$160–190, e quer testar a mesma oferta a dois preços.
- **Produto** quer cortar: um produto e um canal por 90 dias. Três produtos, quatro marketplaces e uma oficina que ainda não existe é coisa demais.
- **Monopólio** dá PASS: não há nada que impeça uma cópia em seis meses (nem tecnologia, nem rede, nem marca), e o negócio depende inteiramente dos marketplaces. Uma margem melhor não muda isso.

### Condições (checklist para o resto do pack)

- [ ] Cotação real de suporte e frete que deixe a **margem por kit positiva** no preço praticado, com garantias incluídas → `/founder-cfo` (Ofertas, Produto e Monopólio)
- [ ] **Sem galpão nem ajudante** até haver volume → `/founder-ops`, `/founder-cfo` (Produto)
- [ ] **Um produto e um canal por 90 dias**, provavelmente o sob medida no Mercado Livre → `/founder-launch` (Produto e Monopólio)
- [ ] Medir o **tempo real de produção** do sob medida → `/founder-ops` (Produto)
- [ ] **Testar a mesma oferta a dois preços** para separar o efeito do preço do efeito da oferta → `/founder-launch` (Ofertas)
- [ ] **Plano para as primeiras avaliações e provas**, sem trocar nota por desconto → `/founder-marketing` (Ofertas)
- [ ] **10 instalações reais** com pessoas, incluindo drywall → `/founder-launch` (Produto)
- [ ] Anúncio teste que **meça tráfego e custo por cliente** → `/founder-launch`, `/founder-marketing` (Monopólio)
- [ ] Uma **vantagem durável** contra cópia (marca, processo do sob medida, canal próprio) → `/founder-brand` (Monopólio)

**Perguntas em aberto:**
- tamanho do nicho sob medida;
- tráfego de um anúncio novo e custo por cliente;
- experiência do fundador em marcenaria;
- orçamento disponível;
- o que o fundador sabe que os concorrentes não sabem.

### A versão mais forte que o conselho enxerga

**É diferente do que foi apresentado.** Não é uma "marcenaria de marketplace com três produtos". É uma **marcenaria de prateleiras sob medida em madeira maciça**, começando no Mercado Livre e produzindo numa garagem, sem galpão e sem funcionário:
- uma medida por pedido, entregue em data garantida por escrito;
- foto do kit antes do envio e reposição sem devolução como prova de confiança;
- o kit pronto de 60x20 só como porta de entrada, ou nem isso, até o suporte ficar barato.

Os primeiros 30 pedidos servem para gerar avaliações com foto e medir o tempo de produção. Com isso, fica claro se o sob medida paga a mão de obra. Só depois disso se discute galpão, segundo canal ou marca própria fora do marketplace, que é a única defesa real contra cópia que o Monopólio aceitaria.

## The competition

Data da pesquisa: 2026-11-03. Fontes: só páginas públicas. **Limite:** a rede desta sessão não abre o Mercado Livre, então os números do ML vêm de trechos de resultados de busca, não das páginas abertas. Preços e notas mudam o tempo todo, então confira os anúncios antes de decidir. As premissas sobre a ideia estão em `founder/idea.md`.

### 1. Quem está no mercado (do mais direto ao menos direto)

Item de comparação: **kit 3 prateleiras 60x20 com suporte invisível**. Para móveis maciços, uma mesa ou um tampo.

| Concorrente | Tipo | Canal | Preço do item comparável | Nota (avaliações) |
|---|---|---|---|---|
| [Bignotto](https://lista.mercadolivre.com.br/prateleira-mdf) | direto | ML | R$59,94 (kit 3 60x20, MDF 15mm; de R$78,90) | 4,7 (+500 vendidos) |
| [Anúncio MLB44200402](https://www.mercadolivre.com.br/kit-3-prateleiras-suspensa-reta-mdf-suporte-invisivel-60x20-cor-preto/p/MLB44200402) | direto | ML | R$72,11 preto / R$69,90 branco | n/d |
| [Pesmah](https://lista.mercadolivre.com.br/prateleira-com-suporte-invisivel-60x20) | direto | ML | R$70,71 Pix (só aparece num trecho de busca, sem confirmação) | n/d |
| [Souza Moraes Marcenaria](https://www.mercadolivre.com.br/pagina/souzamoraesmarcenaria) | direto | ML | não confirmado (2 prateleiras 60x20) | **4,8 (401)** |
| [Loja da Isa](https://lista.mercadolivre.com.br/prateleira-nicho-mdf) | direto | ML | R$69,90 (kit 2 em S); R$191,05 (nicho triplo) | 4,7 (102 / **829**) |
| [Kit madeira real c/ suporte transparente](https://lista.mercadolivre.com.br/prateleira-com-suporte-invisivel-60x20) | direto | ML | R$259 (R$246,05 Pix) | n/d |
| [Studio Home Marcenaria](https://www.elo7.com.br/nicho-cozinha-com-prateleira-e-varao/dp/8AEB5A) | direto | Elo7 | R$279,90 (nicho cozinha) | 4,7 (19) |
| [Marcenaria Dyna](https://www.elo7.com.br/1-prateleira-nicho-em-z-tamanho-de-1-70m/dp/8BAAD9) | direto | Elo7 | n/d (prateleira Z 1,70 m) | n/d |
| [Merito Movelaria](https://lista.mercadolivre.com.br/mesa-redonda-madeira-macica) | direto (maciço) | ML | n/d (mesa redonda 90 cm) | 4,7 (85) |
| [Loja do Pinho](https://lista.mercadolivre.com.br/tampo-de-mesa-madeira-maci%C3%A7a-200x80cm) | direto (maciço) | ML | R$699,90 (tampo 200x80; faixa R$484–700) | n/d |
| [MB Móveis](https://www.mercadolivre.com.br/pagina/mbmoveis) | direto (maciço) | ML | n/d (beliches) | 4,8 (30) |
| [Fortaleza Móveis Rústicos](https://www.mercadolivre.com.br/loja/fortaleza-moveis-rusticos) | direto (maciço) | ML | n/d (madeira de demolição) | n/d |
| [MadeiraMadeira](https://escorregaopreco.com.br/ofertas/madeiramadeira/8201443) | indireto + canal | site/marketplace | R$208,20 (1 prateleira 90 cm) | Reclame Aqui 7,0, [12.349 reclamações](https://www.reclameaqui.com.br/empresa/madeiramadeira/) |
| [Shopee genéricos](https://escorregaopreco.com.br/ofertas/magazineluiza/7970244) | indireto | Shopee | R$11,49 (kit 50 cm); R$30,07 (kit 3) | n/d |
| [Pradel](https://www.casasbahia.com.br/prateleira-150cm-freijo-pradel/p/1562479059) | indireto | Casas Bahia/Extra | n/d | n/d |
| [Home centers](https://www.telhanorte.com.br/prateleira-facility-30x60cm-branca-pratk-893900/p) | substituto | loja física | n/d | — |
| [Marceneiro local / "sob medida"](https://lista.mercadolivre.com.br/prateleiras-mdf-sob-medida) | substituto | indicação, Instagram | orçamento | — |

Slogans dos concorrentes: só encontrei o da Fortaleza Móveis Rústicos ("Há mais de 15 anos no Mercado"). Nenhum outro apareceu nas fontes que consegui acessar.

### 2. Faixa de preço (kit 3 prateleiras 60x20)

- **Mais baixo:** R$59,94 (Bignotto, MDF)
- **Mediana:** R$70,71 (cinco preços: 59,94 / 69,90 / 70,71 / 72,11 / 259)
- **Mais alto:** R$259 (kit em madeira real)
- **Piso da Shopee:** R$30,07 por um kit de 3 genérico. É outra guerra, que não vale a pena entrar.
- **Peças de marcenaria artesanal (Elo7):** de R$279,90 por um nicho até R$650 ou mais por peças com ferro e madeira ([fonte](https://www.elo7.com.br/nicho-para-parede-industrial-ferro-e-madeira-com-prateleiras/dp/20E4844)).
- **Maciço (ML):** mesas de R$400 a R$4.349. Tampo 200x80 por R$699,90.

Na prática, há **um degrau grande entre R$70 e R$250**. Abaixo dele fica o MDF genérico. Acima ficam a madeira real e o trabalho artesanal.

### 3. Mapa de posicionamento

Eixos: **preço** (horizontal) × **material/personalização** (vertical: de MDF padrão a madeira real ou sob medida).

```
 madeira real / sob medida
        ^
        |                         Studio Home (Elo7)   Loja do Pinho
        |                         Kit madeira R$259     Merito / MB / Fortaleza
        |
        |           [ VAZIO: R$90–180, madeira/acabamento de
        |             marcenaria, pronto pra envio, kit completo ]
        |
        |  Souza Moraes (4,8/401)
        |  Bignotto  Pesmah  MLB44200402  Loja da Isa
        |  Shopee genéricos                MadeiraMadeira R$208
 MDF padrão +--------------------------------------------------->  preço
          R$30          R$70           R$150          R$250+
```

### 4. Reclamações dos clientes (em ordem)

A maioria vem do Reclame Aqui e trata de móveis em geral comprados online, não só de marcenarias. Os temas com menos de 3 relatos estão marcados como **fracos**.

1. **Peças ou ferragens faltando (5 relatos).** Prateleira MDF entregue [sem parafusos](https://www.reclameaqui.com.br/shopee/prateleira-incompleta-e-dificuldade-para-obter-reembolso-na-shopee_s96DYWEtoqV2O2xq/) (Shopee). Kit entregue [sem as prateleiras de madeira](https://www.reclameaqui.com.br/shopee/reclamacao_eLF9lkupYXiUpO-T/). [Peças erradas](https://www.reclameaqui.com.br/byhouse/produto-com-pecas-erradas-avarias-e-falta-do-brinde-prometido_9SZm25lmd2AW1F1Z/). [Móveis incompletos](https://www.reclameaqui.com.br/amura-baby/moveis-danificados-e-incompletos-com-descaso-no-atendimento-pos-venda-e-kit-de-berco-com-bordado-errado_4fMOqVIRXFSeeKJd/). Na Marcenaria Dyna (Elo7), um comprador escreveu: "veio faltando a bucha e parafusos para a fixação na parede" ([link](https://www.elo7.com.br/1-prateleira-nicho-em-z-tamanho-de-1-70m/dp/8BAAD9)).
2. **Chegou quebrado ou avariado no transporte (5 relatos):** [Multimóveis](https://www.reclameaqui.com.br/multimoveis/produto-entregue-quebrado-e-recusa-de-coleta-domiciliar-pelo-suporte_Gc-bsvZE0T0OGF5-/), [Shopee](https://www.reclameaqui.com.br/shopee/produto-quebrado-e-falta-de-suporte-da-shopee_UpvTO3AoMSlOBP4_/), [PS Móveis](https://www.reclameaqui.com.br/ps-moveis/estante-quebrada-suporte-zero_bJF7FzZEqGGO46hB/), [ByHouse](https://www.reclameaqui.com.br/byhouse/produto-com-pecas-erradas-avarias-e-falta-do-brinde-prometido_9SZm25lmd2AW1F1Z/), [Rede Solar](https://www.reclameaqui.com.br/rede-solar-moveis/propaganda-enganosa-entrega-atrasada-e-moveis-quebrados_JOSpVmfGMir7gA5W/). Em vários casos o dano só aparece na hora da montagem, quando o prazo de garantia já está acabando.
3. **Pós-venda fraco ou reembolso negado (4 relatos):** [Shopee recusou por prazo](https://www.reclameaqui.com.br/shopee/produto-quebrado-e-falta-de-suporte-da-shopee_UpvTO3AoMSlOBP4_/), [Multimóveis recusou a coleta](https://www.reclameaqui.com.br/multimoveis/produto-entregue-quebrado-e-recusa-de-coleta-domiciliar-pelo-suporte_Gc-bsvZE0T0OGF5-/), [Estilos Móveis](https://www.reclameaqui.com.br/estilos-moveis-projetados/atraso-na-entrega-pos-venda-pessimo_znEjSZSRBEECZryu/), [Stylo e Classe](https://www.reclameaqui.com.br/stylo-e-classe-moveis-e-decoracoes/montagem-errada-pessima-qualidade-e-pos-venda-inexistente_Br73Y9ow7N4nh2ei/).
4. **Atraso na entrega (3 relatos):** [prateleira industrial na Shopee](https://www.reclameaqui.com.br/shopee/atraso-na-entrega-e-falta-de-informacoes-sobre-prateleira-industrial-suspen_5CO-BLIz3Csj0sSt/), [Estilos](https://www.reclameaqui.com.br/estilos-moveis-projetados/atraso-na-entrega-pos-venda-pessimo_znEjSZSRBEECZryu/), [Marel](https://www.reclameaqui.com.br/marel-ind-de-moveis-s-a/marel-moveis-atraso-na-entrega-moveis-com-defeito-sem-notas-fiscais-e-falta-de-solucao_hByA_36uBOshUC2I/). No Elo7, o prazo de produção sob encomenda chega a [15 dias úteis](https://www.elo7.com.br/nicho-em-madeira-osb/dp/1E91C71).
5. **Material diferente do anunciado, como MDP ou aglomerado vendido como MDF (fraco, 2 relatos):** [Rede Solar](https://www.reclameaqui.com.br/rede-solar-moveis/propaganda-enganosa-entrega-atrasada-e-moveis-quebrados_JOSpVmfGMir7gA5W/), [Madetec](https://www.reclameaqui.com.br/madetec/moveis-de-aglomerado-vendidos-como-mdf-nas-lojas-magazine-luiza_6g_p9jAn9NjitN8Q/).

Um risco para quem vende, não para o cliente (**fraco, 2 relatos**): a MadeiraMadeira cobra comissão mesmo em venda cancelada. Um vendedor relatou: "Quando um dos clientes solicitou o cancelamento do pedido, antes mesmo de ser enviado, o valor da venda foi estornada ao cliente, porém a comissão da venda ainda continuava sendo cobrada de nós." ([link](https://www.reclameaqui.com.br/madeiramadeira/o-marketplace-madeiramadeira-cobra-comissao-mesmo-de-vendas-canceladas-um_3L_XC-vw9O29BjzH/)). A comissão citada para decoração é de [19%](https://blog.bling.com.br/madeiramadeira-como-vender/).

### 5. A lacuna

**Existe espaço entre R$90 e R$180: madeira real (ou MDF com acabamento de marcenaria), pronto para envio, com kit de fixação completo e embalagem que chega inteira.**

Por que essa lacuna parece real:
- O ML tem dois blocos de preço, R$60–75 (MDF padrão) e R$250+ (madeira real ou artesanal). Quase não há oferta no meio (seção 2).
- As duas reclamações mais frequentes, ferragem faltando e chegar quebrado, são **problemas de embalagem e conferência**, não de produto. Uma marcenaria resolve as duas com processo: checklist de peças, bucha e parafuso no kit, foto da embalagem antes do envio e caixa reforçada.
- Quem faz trabalho artesanal no Elo7 tem poucas avaliações (19, ou nenhuma) e prazo longo. Quem vende volume no ML tem muitas avaliações (401, 829) e produto genérico. **Ninguém junta as duas coisas.**
- A busca por ["sob medida"](https://lista.mercadolivre.com.br/prateleiras-mdf-sob-medida) já existe no ML. Medida personalizada com prazo curto é um diferencial que fábrica não oferece. Vocês já têm um pipeline de orçamento de marcenaria (`orcamento-marcenaria/`) que poderia gerar o preço de cada medida.

Ressalva honesta: **no MDF padrão de R$60–75 não há lacuna**. Ali vence quem tem escala e preço (Bignotto, Shopee). Não entre nessa disputa.

### 6. A ameaça

- **Quem pode copiar mais rápido:** vendedores grandes de MDF no ML, como Bignotto e Loja da Isa. Eles já têm reputação e volume, e para mudar de posição bastaria lançar uma linha com "madeira" ou "sob medida" e melhorar a embalagem. Defesa: material de verdade (madeira, ou acabamento que se vê na foto), avaliações que citam "chegou perfeito" e "veio tudo" desde a primeira venda, e uma marca que o cliente procure pelo nome.
- **No preço:** a Shopee empurra qualquer anúncio de "prateleira MDF" para R$30. A resposta é não competir pela mesma palavra-chave e anunciar pelo material e pelo resultado (ex.: "prateleira madeira maciça freijó").
- **No canal:** comissões e regras do marketplace (19% e comissão em cancelamento na MadeiraMadeira). Venda em mais de um canal e leve os clientes para um canal próprio, como Instagram ou site.

---

**Próximos passos:** o `/founder-consumer` vai transformar essas reclamações em objeções de compra, e o `/founder-pricing` vai usar a faixa de R$60 a R$260.

## The buyer panel

**2 buy · 18 pass** (10% buy) out of 20 simulated buyers. Seed 493632, so the same cards can be dealt again.

These are simulated buyers, not customers. Use this to find objections and weak spots, then confirm the big ones with real people before you spend.

### By segment

| group | buyers | buy rate |
| --- | ---: | ---: |
| Renda alta que valoriza design, renda anual em R$ | 4 | 25%  (thin) |
| Classe média que reforma ou decora, renda anual em R$ | 8 | 12% |
| Primeiro apê / aluguel, renda anual em R$ | 8 | 0% |

### By buying behaviour

| group | buyers | buy rate |
| --- | ---: | ---: |
| Precisa de medida exata | 2 | 100%  (thin) |
| Caçador de preço | 5 | 0%  (thin) |
| Já se queimou com MDF ruim | 3 | 0%  (thin) |
| Quer o visual do Pinterest | 3 | 0%  (thin) |
| Lê todas as avaliações | 4 | 0%  (thin) |
| Compra rápido | 3 | 0%  (thin) |

### By income

| group | buyers | buy rate |
| --- | ---: | ---: |
| $57,000 to $110,000 | 7 | 14%  (thin) |
| $110,000 and up | 7 | 14%  (thin) |
| under $57,000 | 6 | 0%  (thin) |

### Why they pass

| reason | buyers | in their words |
| --- | ---: | --- |
| trust | 14 | "Ordenei por menor preço e achei kits de 3 prateleiras por bem menos de R$149; pagar mais só faria sentido se eu tivesse certeza de que é pinus maciço mesmo, e uma loja nova com quase nenhuma avaliação não me dá essa certeza. Vou favoritar e esperar." (P002) · "Gostei de ser pinus maciço e não MDF, e o preço é ok, mas loja nova sem avaliação eu não arrisco de novo. Prefiro esperar ver fotos de compradores reais ou pegar de uma loja com reputação, mesmo pagando um pouco mais." (P003) |
| price | 3 | "Quando ordeno por menor preço aparece kit de 3 prateleiras flutuantes por bem menos de R$149, e na foto do celular parece tudo igual. Pagar o dobro numa loja nova sem avaliação eu não faço, vou no mais barato que tem nota boa." (P007) · "R$149 é mais que o dobro do kit de MDF de R$70 que chega amanhã pelo Full. Pinus maciço é bonito, mas pra prateleira de sala eu não vejo diferença que valha isso, ainda mais de uma loja nova que demora até 3 dias úteis." (P009) |
| quality | 1 | "Pelo menos é madeira maciça e não MDF com adesivo, e o preço não me pesa. Mas pinus com verniz costuma ficar amarelado, com cara de móvel de chácara, e não é o visual de madeira clara e fosca que eu quero no home office. Numa loja nova sem avaliações e sem fotos de cliente, prefiro pagar mais numa marca que já mostra o acabamento." (P013) |

### Why they buy

| reason | buyers | in their words |
| --- | ---: | --- |
| need | 2 | "Tenho um vão com medida certa e nunca acho prateleira pronta que encaixe; pagar R$30 a mais para vir no tamanho exato, em madeira maciça e com gabarito de furação, resolve meu problema por uns R$179. Como compro pelo Mercado Livre, se der errado tenho a garantia da plataforma." (P001) · "Tenho um vão na parede que nenhuma prateleira pronta encaixa, e a medida sob encomenda até 120 cm por só R$30 a mais resolve exatamente isso. Por R$179 em madeira maciça, com troca garantida se chegar danificada, o risco é pequeno para mim." (P004) |

### What would flip a no

- Ver várias avaliações com fotos reais mostrando a borda e o veio da madeira e a prateleira instalada com peso em cima, ou um cupom que deixasse o kit perto de R$110.
- Ver umas 30 ou mais avaliações com fotos de clientes mostrando a prateleira instalada e carregada, e reputação verde no Mercado Livre.
- Ver várias avaliações com fotos reais de clientes mostrando a prateleira instalada na parede, com o veio da madeira e o acabamento de perto.
- Ver umas 50 avaliações ou mais, com fotos das prateleiras instaladas, e as negativas mostrando que a loja resolveu rápido.
- Um cupom ou preço perto de R$110 com várias avaliações com foto de quem já instalou.
- Ver dezenas de avaliações com fotos reais de clientes mostrando a prateleira carregada de livros e plantas, e poucas reclamações nas de 1 e 2 estrelas.
- Ficar perto de R$100 com entrega Full em 1 ou 2 dias, e várias avaliações com foto mostrando que a madeira é boa mesmo.
- Ver umas 20 ou 30 avaliações com fotos de clientes mostrando a prateleira instalada, com o acabamento e o suporte invisível de verdade.
- Ver umas 30 ou mais avaliações boas com foto da prateleira instalada e carregada, e o anúncio no Full chegando em 1 ou 2 dias.
- Ver umas 20 ou 30 avaliações com fotos de clientes mostrando a madeira de perto, o suporte instalado e coisa pesada em cima.
- Fotos reais de clientes com as prateleiras instaladas, ou uma opção de acabamento fosco/tingido tipo freijó ou carvalho claro.
- Ver umas 50 ou mais avaliações reais com fotos das prateleiras instaladas e carregadas, incluindo como a loja respondeu às reclamações.

Buyers say they would buy **1.0 times** in the first month on average.

20 buyers gave all four price answers. Run founder-pricing's van_westendorp.py on the answers folder.

## Pricing

Base: 20 compradores simulados (`founder/panel/`), curva em `founder/pricing-curve.md` e concorrentes em `founder/competitors.md`. Os números do painel servem para **escolher o que testar**, não provam nada.

> **Falta a margem.** Ainda não existe `founder/numbers.json`, então não há custo por kit (madeira, verniz, suporte, parafusos, caixa, comissão e frete do marketplace). Por isso nenhum preço abaixo tem margem calculada. Rode o `/founder-cfo` com os custos reais e confira cada preço antes de publicar.

### 1. O que o painel disse (Van Westendorp)

| ponto | preço | leitura |
|---|---:|---|
| PMC | R$80 | abaixo disso, parece barato demais para ser madeira maciça |
| OPP | R$80 | ponto de menor resistência |
| IPP | R$121 | metade acha barato, metade acha caro |
| PME | R$190 | acima disso, a maioria não compra |

**Faixa aceitável: R$80 a R$190.** Medianas: "barato" R$110, "começa a ficar caro" R$180, "caro demais" R$230.

O preço atual, R$149, está dentro da faixa, mas acima do IPP. E, no painel, **o preço não foi o que barrou a compra**: 14 de 18 recusas foram por confiança (loja nova sem avaliações) e só 3 por preço. Baixar o preço sozinho não resolve. O que resolve é juntar avaliações com foto.

### 2. Contra os concorrentes (kit 3 prateleiras 60x20)

| concorrente | preço | o que inclui |
|---|---:|---|
| Bignotto (ML) | R$59,94 | MDF 15mm, suporte invisível |
| Anúncio MLB44200402 (ML) | R$69,90–72,11 | MDF, aguenta 10 kg |
| Pesmah (ML) | R$70,71 | MDF (dado não confirmado) |
| Kit em madeira com suporte transparente (ML) | R$246,05–259 | madeira real |
| Studio Home Marcenaria (Elo7) | R$279,90 | nicho artesanal (outro item) |

Entre o MDF de R$60–72 e a madeira de R$246+ quase não há oferta. Qualquer preço entre R$110 e R$180 fica nessa lacuna. Não dá para competir com o MDF pelo preço, e o painel confirmou isso: os caçadores de preço compararam com o kit de R$70 e passaram.

### 3. O preço

**Kit padrão 60x20 em pinus maciço: R$139**, ainda a confirmar com a margem do CFO.
- Fica entre o IPP (R$121) e a mediana de "começa a ficar caro" (R$180), dentro da faixa aceitável.
- É praticamente metade do kit de madeira real mais próximo (R$246) e o dobro do MDF, o que é coerente com "madeira de verdade".
- Cai de R$149 para R$139 para sair da zona em que 5 compradores já disseram "caro" (P005, P015, P016, P017, P019 deram "começa a ficar caro" entre R$129 e R$140).

### 4. A escada (bom / melhor / top)

| degrau | o quê | preço | por que subir |
|---|---|---:|---|
| Bom | Kit 3 prateleiras 60x20, pinus com verniz, pronto para envio (idealmente Full) | R$139 | — |
| Melhor | **Sob medida até 120 cm**, 7 dias úteis | R$169 | O único grupo que comprou no painel (2 de 2) foi o de quem precisa de medida exata. Ambos aceitavam R$179. |
| Top | Sob medida **+ acabamento fosco ou tingido** (tipo freijó ou carvalho claro) | R$189 | P004 e P013 (renda alta) recusaram o pinus "amarelado" e pediram exatamente esse acabamento. Para esse grupo, "caro demais" começou em R$450. |

O degrau top fica no limite da faixa (PME R$190). Ele é para o segmento de renda alta, não para o caçador de preço.

### 5. A oferta de abertura

**Preço de lançamento: R$119 no kit padrão, para os primeiros 30 pedidos ou até 31/12/2026, o que acontecer primeiro.** Depois disso, R$139.
- O objetivo não é margem, é **comprar as primeiras avaliações com foto**, que é o que 12 dos 18 "não" pediram para mudar de ideia. Junto com o produto, envie um cartão pedindo foto da prateleira instalada.
- R$119 fica perto do "barato" mediano (R$110) e do que P002, P007, P017 e P019 pediram ("cupom perto de R$110").
- Mostre "Preço de lançamento" com a data de fim. **Não use "de R$X por R$Y"** com um preço que nunca foi cobrado.
- Antes de lançar, confirme com o CFO que R$119 cobre o custo variável. Se não cobrir, é venda com prejuízo para comprar avaliação, e o CFO precisa dizer por quantos pedidos isso cabe no caixa.

### 6. O que testar com compradores reais

1. **R$119 contra R$139 no kit padrão**: dois anúncios iguais, um em cada preço, por 2 a 3 semanas. Compare conversão (visitas → vendas) e margem total, não só o volume.
2. **Sob medida a R$169 contra R$189**: o painel sugere que esse grupo é pouco sensível ao preço. Confirme com pedidos reais.

Teste também, sem mudar o preço: fotos com a prateleira carregada (livros e vasos) e um vídeo do teste de carga. Isso responde à objeção que mais apareceu.

### 7. As objeções de preço do painel (para o marketing responder)

Simulações, não depoimentos:

1. "R$149 é caro perto dos kits de MDF que vejo por R$60-80, e a loja é nova com poucas avaliações, então não sei se o pinus maciço e o suporte de 15 kg são de verdade." (P007)
2. "Pagar o dobro numa loja quase sem avaliação, sem Full, e ainda esperar uns dias. Se der problema, não sei se eles respondem rápido." (P009)
3. "Loja nova com poucas avaliações: não sei se o suporte invisível aguenta mesmo 15 kg ou se a prateleira vai entortar na parede, e R$149 já é dinheiro pra arriscar." (P016)

Nas três, o preço vem junto com a desconfiança. A resposta tem duas partes: prova (fotos, teste de carga, avaliações) e velocidade (Full).

## The offer

Método: a lente de Ofertas em `../.claude/skills/founder-board/lenses.md`, um resumo nosso do framework de *$100M Offers*. Fontes usadas: `founder/panel/results.md` (painel v1), `founder/competitors.md` e `founder/pricing.md`.

> **Atenção:** ainda não existe `founder/numbers.json` nem `founder/board.md`. Os **custos abaixo são estimativas relativas (1 a 5), não reais**, e a garantia **não foi modelada com a ferramenta do CFO**. Rode o `/founder-cfo` antes de publicar qualquer promessa.

### 1. Lista de problemas (como o comprador diz)

**Antes de comprar**
1. "Loja nova sem avaliações, não arrisco." (14 de 18 recusas no painel v1)
2. "Será que é madeira maciça ou MDF com adesivo?"
3. "O suporte invisível aguenta mesmo 15 kg?"
4. "Pagar o dobro de um kit de MDF de R$70?"
5. "Pinus com verniz fica amarelado, com cara de chácara."
6. "As fotos do anúncio todo mundo caprichou; quero ver o real."
7. "Não tenho a medida que preciso pronta."
8. "Se der problema, eles respondem?"

**Durante**
9. "Demora até 3 dias úteis e ainda tem o frete; o Full chega amanhã."
10. "Sob medida: 7 dias úteis podem virar três semanas."
11. "Vou ter que furar a parede sozinho."
12. "Tenho medo de errar a furação e entortar."
13. "E se errarem a medida do sob medida?"

**Depois**
14. "Chega quebrado ou faltando parafuso." (o tema mais comum no Reclame Aqui, 5 relatos)
15. "A troca vai virar novela no chat."
16. "Vou ter que devolver a peça quebrada e esperar."
17. "A prateleira vai ceder ou soltar depois de uns meses?"
18. "A madeira vai empenar?"
19. "Não sei se o suporte serve em drywall ou tijolo." (painel v2)

### 2. Soluções, pontuadas

Valor para o comprador e custo para entregar, de 1 a 5. O custo é uma estimativa até o CFO confirmar.

| # | Solução | Problemas | Valor | Custo | Fica? |
|---|---|---|---:|---:|---|
| A | Foto do kit DO CLIENTE, embalado, enviada pelo chat antes de despachar | 2, 5, 6, 14 | 5 | 1 | ✅ |
| B | Vídeo do teste de carga de 15 kg no anúncio | 3, 17 | 4 | 1 | ✅ |
| C | Reposição em até 2 dias úteis, sem devolver a peça danificada | 14, 15, 16 | 5 | 2–3 | ✅ (modelar) |
| D | Garantia de 12 meses contra entortar com até 15 kg | 17, 18 | 4 | 2 | ✅ (modelar) |
| E | Escolha de acabamento sem custo extra: verniz natural ou fosco incolor | 5 | 4 | 1–2 | ✅ |
| F | Gabarito de furação + QR code com vídeo de instalação de 3 minutos | 11, 12 | 4 | 1 | ✅ |
| G | Sob medida com "erro de medida é nosso, refazemos" | 7, 13 | 5 | 3 | ✅ (modelar) |
| H | Acabamento tingido (freijó ou carvalho claro) como degrau premium | 5 | 4 | 2 | ✅ (R$189) |
| I | Postagem em 1 dia útil | 9 | 3 | 2 | ✅ se a operação aguentar |
| J | Estoque no Full do Mercado Livre | 9 | 5 | 3–4 | ⏳ depois das primeiras vendas |
| K | Data total de entrega garantida no sob medida, com desconto se atrasar | 10 | 4 | 2 | ➕ pedido no v2, ainda não está na oferta |
| L | Indicar no anúncio o tipo de parede (drywall/alvenaria) e mandar a bucha certa | 19 | 3 | 1 | ➕ pedido no v2 |
| M | Preço de lançamento R$119 (30 pedidos ou até 31/12/2026) | 4 | 4 | ? | ✅ (CFO precisa confirmar que cobre o custo) |

Ficou de fora: amostra física de madeira pelo correio (custo alto) e montagem em casa (não escala por marketplace).

### 3. A pilha

- **O núcleo:** *"Parede pronta numa tarde, em madeira de verdade."* Três prateleiras flutuantes 60x20 em pinus maciço, com suporte invisível testado com 15 kg.
- **Bônus 1, "Foto do seu kit" (A):** derruba "é MDF com adesivo?" e "a foto do anúncio não é real".
- **Bônus 2, "Instala sozinho" (F + L):** gabarito, buchas, parafusos e vídeo de 3 minutos. Derruba "vou ter que furar sozinho".
- **Bônus 3, "Acabamento à escolha" (E):** natural ou fosco, mesmo preço. Derruba "pinus amarelado".
- **Garantia (C + D):** chegou quebrado ou faltando peça, a reposição sai em até 2 dias úteis, sem devolver nada. Entortou em 12 meses com até 15 kg, trocamos. No sob medida, se a medida sair diferente da pedida, refazemos.
  - *Custo ainda não modelado.* Exemplo do cálculo que o CFO deve fazer: com 5% de pedidos pedindo reposição, cada 100 kits custam 5 × (custo de uma prateleira + frete). Rode com o custo real antes de prometer.
  - O Código de Defesa do Consumidor já garante 7 dias de arrependimento na compra online e garantia legal para produto durável. A oferta precisa ir **além disso** e não pode vender o mínimo legal como bônus. Isto não é aconselhamento jurídico.
- **Urgência real:** preço de lançamento R$119 para os **primeiros 30 pedidos ou até 31/12/2026**. É verdadeiro, porque o objetivo é juntar as primeiras avaliações. Sem contagem regressiva falsa nem "só restam 3".
- **Escada:** kit pronto R$119 (lançamento) e depois R$139 · sob medida R$169 · sob medida tingido R$189.
- **Nome:** **Kit Parede Pronta**.

### 4. Equação de valor (1 a 10)

| | antes (pitch v1) | depois (v2) | o que mudou |
|---|---:|---:|---|
| Resultado dos sonhos | 6 | 7 | Acabamento à escolha e o tingido aproximam do "visual do Pinterest" |
| Probabilidade percebida | 3 | 5 | Foto do kit, vídeo de carga e reposição sem devolver. Ainda limitada por falta de avaliações reais |
| Tempo até o resultado | 5 | 6 | Postagem em 1 dia útil e vídeo de instalação. Sem Full, continua atrás do MDF |
| Esforço e sacrifício | 5 | 7 | Gabarito, vídeo e "não precisa devolver nada" |

O ponto fraco continua sendo a **probabilidade percebida**: compradores disseram que "o vídeo de teste é da própria loja". Só avaliações reais resolvem isso, e a oferta não pode inventá-las.

### 5. Reteste: mesmos 20 compradores, mesma seed (493632)

Pitch antigo em `founder/pitch-v1.md`, novo em `founder/pitch.md`, painel novo em `founder/panel-v2/`.

| | v1 (R$149) | v2 (Kit Parede Pronta, R$119) |
|---|---:|---:|
| Compram | **2 de 20 (10%)** | **5 de 20 (25%)** |
| Recusa por confiança | 14 | 11 |
| Recusa por preço | 3 | 3 |
| Recusa por acabamento | 1 | 0 |
| Recusa por prazo | 0 | 1 |

- **Passaram a comprar:**
  - P010 (visual Pinterest): pela foto do kit e pela reposição sem devolver.
  - P012 (home office): a foto do kit resolveu a dúvida "é MDF com adesivo?".
  - P013 (renda alta): comprou o tingido de R$189.
  - P017 (caçador de preço): pelo R$119.
- **Continuou comprando:** P004 (precisa de medida exata).
- **Deixou de comprar:** P001 (medida exata). Agora, com o prazo do sob medida escrito explicitamente, recusou por **prazo**: *"7 dias úteis só pra produzir, mais o frete, e se errar a medida ainda tem que refazer... vira um mês"*. Correção: prazo total garantido por escrito (solução K).
- **Objeções que caíram:** o acabamento (o pinus amarelado sumiu como motivo de recusa) e "é MDF com adesivo?" (respondida pela foto do kit).
- **Objeções que ficaram:**
  - Loja sem avaliações. A pergunta deles mudou de "é real?" para "quero ver outros compradores primeiro".
  - Falta de Full (P011, P020).
  - Preço contra o MDF de R$70 (P007, P009, P019).
- **Por segmento:**
  - O primeiro apê subiu de 0% para 38%.
  - A classe média caiu de 12% para 0%.
  - Os grupos "lê todas as avaliações" e "compra rápido" seguem em 0%: só avaliações reais e Full mudam isso.

**Ressalva importante:** a oferta e o preço mudaram juntos (R$149 → R$119). Não dá para separar quanto da melhora veio da pilha e quanto do desconto. A faixa de preço aceitável do v2 também caiu (teto de R$190 para R$160), sinal de que mostrar R$119 ancorou os compradores mais para baixo. Isso reforça usar o R$119 só como lançamento com data de fim. No teste real, rode a pilha nova a R$139 contra a pilha nova a R$119.

São compradores simulados. A taxa de 25% é teto, não previsão, e trata-se de uma amostra de 20 (todos os segmentos marcados como "thin").

### 6. Próximos passos

1. `/founder-cfo`: custo real por kit, custo da garantia com uma taxa de reclamação realista e se R$119 cobre o custo variável.
2. Incluir K (prazo total garantido no sob medida) e L (tipo de parede e bucha certa) no anúncio.
3. Planejar a entrada no Full depois das primeiras ~30 vendas.
4. `/founder-marketing`: os 30 primeiros compradores existem para gerar avaliações com foto. Peça a foto no cartão da caixa, **sem oferecer desconto em troca de avaliação positiva**.

## The numbers

> Valores em **R$**: a ferramenta imprime "$", mas tudo está em reais. Quase todos os custos são **estimativas** (veja `founder/cfo-sources.md`). Troque pelos orçamentos reais e rode de novo. Isto não é aconselhamento financeiro, contábil nem jurídico: um contador deve revisar enquadramento (MEI/Simples), folha e impostos antes de qualquer dinheiro sair.

**Veredito: do jeito que está, cada kit dá prejuízo antes mesmo do aluguel.**

- **A margem:** vendendo o kit a R$139, o custo variável é R$159,17, então cada kit **perde R$20,17**. Com 5 kits por dia, a margem fica em **-54%** e o ano 1 fecha em **-R$122.291** de operação (-R$162.591 contando o investimento). Ponto de equilíbrio: nunca.
- **O lançamento a R$119** perde **R$36,57 por kit**. Os 30 pedidos de lançamento custam cerca de R$1.097 em prejuízo. Dá para pagar isso conscientemente como custo de comprar as primeiras avaliações, mas só se o resto for corrigido.
- **A linha que mais pesa: os 6 suportes invisíveis (R$48, 30% do custo).** Logo depois vêm o frete grátis (R$25, estimado) e a madeira (R$37,40).
- **Caixa:** no modelo atual, a necessidade de caixa não para de crescer (R$162.591 no ano 1). Começar do zero, com galpão (R$3.100) e ajudante (R$4.000), é o que transforma um produto de margem fina num buraco. São R$8.300 por mês de custo fixo contra um produto que hoje não contribui nada.

### Três formas de melhorar (rodadas na ferramenta, não chutadas)

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

## Unit economics: Kit Parede Pronta - marcenaria nova vendendo em marketplaces (valores em R$)

Every number below comes from the input file. Nothing is looked up or guessed.

### One kit (3 prateleiras 60x20 pinus macico)

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

### The margin that matters

Fixed costs: $8,300 a month (Aluguel galpao 100 m2 [publico, anuncio Sorocaba] $3,100, 1 ajudante de marcenaria com encargos [estimativa] $4,000, Energia das maquinas [estimativa] $600, Contador [estimativa] $400, Internet, celular, software [estimativa] $200).

- **Break-even: never (each unit loses money) kit (3 prateleiras 60x20 pinus macico)s a day.** Below that you lose money every month.
- **Profit margin at your plan** (5 a day): **-54%** of every sale, after every cost.
- Capacity: 20 a day.

### Year 1, month by month

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

### What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | -54% | never | -$122,291 |
| Price -10% | -71% | never | -$137,929 |
| Volume -20% | -64% | never | -$117,753 |
| Unit costs +15% | -71% | never | -$149,151 |

### Red flags

- Each unit loses money before rent and salaries: the price is below the variable cost.
- Break-even needs inf kit (3 prateleiras 60x20 pinus macico)s a day but capacity is 20.
- Year 1 loses money on operations (-$122,291).
- The startup spend is not earned back within year 1.

## Operations

Modelo assumido (conversa de 2026-11-03):
- Um marceneiro com 20+ anos de experiência e orçamento de R$2.000.
- **Corte e aparelhamento terceirizados na madeireira.**
- Em casa: furação do pino com gabarito, lixa, selador e verniz à base d'água, conferência com foto e embalagem.
- Venda no Mercado Livre primeiro, conforme a condição do conselho (um produto e um canal por 90 dias, com foco no sob medida).

A cidade ainda não foi informada, então os fornecedores locais aparecem como "como achar". Os padrões de qualidade estão em `founder/quality-spec.md`.

### 1. O ciclo de cada dia

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

### 2. Fornecedores

| Insumo | Opções | Preço público | Mínimo e prazo | Pendente |
|---|---|---|---|---|
| Pinus seco aparelhado 20 cm | Madeireira local (corte no comprimento); [Beija-Flor Madeiras](https://www.beijaflormadeiras.com.br/tabua-de-20-pinus-aparelhada/); [Leroy Merlin](https://www.leroymerlin.com.br/tabua-de-20-pinus-aparelhada_1570817377) | R$44,90 e R$58,37 por 3 m (~R$15–19,50/m) | Sem mínimo no varejo | **Cotar** corte no comprimento por kit e confirmar que é seco em estufa |
| Suporte invisível 20 cm | [MFL Acessórios](https://www.mflacessorios.com.br/suporte-metalico-invisivel-para-prateleira-20cm-ferro-38); [Desicon](https://www.desicon.com.br/suporte-invisivel-20-cm-preta) | R$7,60–9,55 a unidade | Desicon: frete grátis a partir de 36 un. | **Cotar atacado** (100+ un.) ou calcular o custo de fabricar pino e chapa |
| Caixa de papelão onda dupla (BC) ~70x25x15 | Fabricante de caixa sob medida da região; lojas de caixa no ML, como [GP Caixas](https://www.mercadolivre.com.br/loja/gp-caixas-de-papelao) | Não achei essa medida. Referência: caixas de onda dupla 40x30x30 de ~R$15 a R$30 a unidade ([busca ML](https://lista.mercadolivre.com.br/caixa-de-papelao-onda-dupla)) | Fabricantes costumam ter mínimo | **Cotar** com medida, onda BC e quantidade (50 un.) |
| Selador e verniz à base d'água | Loja de tintas local ou home center | — | — | Medir o rendimento por kit |
| Parafusos, buchas, cantoneiras, plástico | Distribuidor de ferragens local | — | — | Comprar em caixa fechada |
| Higrômetro de madeira | Home center ou ML | — | — | Compra única, entra no orçamento inicial |

**Frete:** é o maior custo ainda sem cotação, estimado em R$25. Simule com a caixa e o peso reais no simulador de custos do vendedor no Mercado Livre e atualize `numbers.json`.

### 3. Pessoas

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

### 4. Rotinas (SOPs)

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

### 5. Ferramentas

- **Mercado Livre e Mercado Pago:** venda e recebimento. Comissão do Clássico em Casa de cerca de 12% ([fonte](https://ecommercenapratica.com/blog/comissao-mercado-livre/), confirmar no simulador oficial).
- **Nota fiscal:** como MEI, pelo emissor gratuito do governo. Se precisar de integração, o Bling custa a partir de ~R$55/mês no plano Cobalto, segundo um [guia de 2026](https://gosmarter.com.br/?p=6032) (confirmar na página oficial). Comece sem ele e contrate só quando o volume pedir.
- **Controle:** uma planilha simples com pedidos, tempo por kit, custos, estoque e reclamações.

### 6. Registro, impostos e seguros

Confirme cada item com o órgão oficial ou com um contador. As regras mudam e variam por cidade. Isto não é aconselhamento jurídico nem tributário.

- [ ] **MEI:** confirme no [Portal do Empreendedor](https://www.gov.br/empresas-e-negocios/pt-br/empreendedor) qual ocupação de marceneiro é permitida e se ela recolhe ICMS e/ou ISS. O DAS em 2026 fica entre R$82,05 e R$87,05/mês, com base no salário mínimo de R$1.621 ([fonte](https://soubrasilia.com/servicos/mei/)).
- [ ] ⚠️ **Teto do MEI: R$81 mil/ano**, cerca de R$6.750/mês ([fonte](https://triviumcontabil.com.br/mei-em-2026-regras-custos-e-limites/)). O plano do CFO (5 kits/dia a R$169) daria uns R$25 mil/mês, muito acima disso. **No ritmo do plano, o MEI estoura por volta do 3º ou 4º mês.** Combine com o contador a passagem para ME no Simples, e saiba que o imposto muda: o CFO estimou 6%.
- [ ] **Alvará e uso do imóvel:** marcenaria em casa gera ruído e pó. Confira com a prefeitura (zoneamento e alvará do MEI) e com o condomínio, se houver.
- [ ] **CDC:** 7 dias de arrependimento em compra online e garantia legal de produto durável. A garantia de 12 meses vem por cima disso.
- [ ] **Seguro:** opcional no começo. Avalie seguro das ferramentas e responsabilidade civil quando o volume crescer.

### 7. Riscos

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

### Perguntas em aberto

- Em que cidade você está? Define a madeireira, a caixa e o frete.
- Que máquinas você já tem: furadeira de bancada, lixadeira orbital, compressor ou pistola?
- Quanto custa o corte no comprimento na madeireira e o suporte no atacado (ou fabricado)?
- Qual é o frete real da caixa?
- Quanto tempo leva cada kit (medir nos 10 primeiros)?

**O CFO deve rodar de novo** depois das cotações, com o modelo enxuto e o imposto do MEI no lugar dos 6%. O `numbers.json` atual ainda é o cenário com galpão e ajudante.

## Not done yet

- Marketing: run /founder-marketing
- Brand: run /founder-brand
- Launch plan: run /founder-launch

_The panel is simulated buyers and the numbers are projections from your inputs. Confirm demand with real customers and costs with real quotes before you spend. Not financial, legal or tax advice._
