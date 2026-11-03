# Kit Parede Pronta (nome de trabalho) · Business plan

**Verdict: Not yet**

- ✓ Each prateleira 100x20x3 cm earns $0.62 before fixed costs (1% contribution).
- ✗ Year 1 operating LOSS: $4,039.
- ✗ Break-even is 21 prateleira 100x20x3 cms a day against a capacity of 10.
- ✗ 2 of 20 simulated buyers buy (10%, the bar is 25%).

| key number | |
| --- | ---: |
| Price | $119.00 a prateleira 100x20x3 cm |
| Profit margin at plan | -2% per prateleira 100x20x3 cm |
| Break-even | 21 prateleira 100x20x3 cms a day |
| Year 1 operating profit | $-4,039 |
| Startup spend | $2,000 |
| Cash needed before it pays for itself | $6,039 |
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

> **Correção (2026-11-03, `mais-vendidos.md`):** buscas posteriores acharam pinus maciço com suporte invisível a R$53,90 (120x20 cm) no Mercado Livre e kits de pinus de R$36 a R$49 na Shopee. A afirmação de que há "pouca oferta entre R$90 e R$180 em madeira real" **não se sustenta**. A lacuna real é mais estreita: sob medida, prateleira grossa ou premium e acabamento.

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

## Unit economics: Veio Certo - prateleira grossa de pinus 30 mm sob medida, producao em casa, venda no Mercado Livre (valores em R$)

Every number below comes from the input file. Nothing is looked up or guessed.

### One prateleira 100x20x3 cm

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

### The margin that matters

Fixed costs: $387 a month (DAS MEI 2026 (R$82,05-87,05) [publico] $87, Energia extra das maquinas em casa [estimativa] $100, Internet e celular [estimativa] $200).

- **Break-even: 21 prateleira 100x20x3 cms a day.** Below that you lose money every month.
- **Profit margin at your plan** (4 a day): **-2%** of every sale, after every cost.
- Capacity: 10 a day.

### Year 1, month by month

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

### What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | -2% | 21 | -$4,039 |
| Price -10% | -14% | never | -$15,642 |
| Volume -20% | -3% | 21 | -$4,160 |
| Unit costs +15% | -17% | never | -$21,353 |

### Red flags

- Break-even needs 21 prateleira 100x20x3 cms a day but capacity is 10.
- Year 1 loses money on operations (-$4,039).
- The startup spend is not earned back within year 1.

## Marketing

Baseado em `panel/results.md` (v1), `panel-v2/results.md`, `competitors.md`, `offer.md`, `pricing.md`, `numbers.json`, `brand.md` e `launch.md`.
Lançamento fechado: **21/11/2026**. Lançamento público: **30/11/2026**.

### 1. O que as evidências dizem

**Quem compra, nos painéis simulados (amostras pequenas):**
- Medida exata: 100% no v1 e 50% no v2.
- Visual de Pinterest: 67% no v2.
- Renda alta: 50% no v2.
- Primeiro apê: 38% no v2.

**Quem não compra:**
- Quem lê todas as avaliações: 0% nas duas rodadas.
- Quem quer receber rápido: 0% nas duas rodadas.

**Objeções a responder:**
1. Loja nova sem avaliações (14 e 11 recusas)
2. "Aguenta 15 kg mesmo?"
3. "É madeira ou MDF com adesivo?"
4. "Pinus amarelado"
5. Preço contra o MDF de R$70
6. Demora (sem Full, sob medida em 7 dias)
7. "Serve no drywall?"

**O que os concorrentes fazem:** os vendedores de MDF vendem preço e volume, e o artesanal do Elo7 tem poucas avaliações. Ninguém vende **marceneiro, sob medida e chegar certo** ao mesmo tempo.

### 2. Posicionamento

1. **(Recomendado)** *Para quem tem uma parede ou um vão que nenhuma prateleira pronta encaixa e não quer arriscar MDF que chega quebrado, a Veio Certo é a marcenaria de prateleiras sob medida em madeira maciça, feita e testada por um marceneiro de 20 anos, que chega inteira e completa. Diferente dos kits de MDF de fábrica.*
   - **Por quê:** o único grupo que comprou nas duas rodadas foi o de quem precisa de medida exata. O ofício responde ao "loja nova não confio".
2. *Para quem quer o visual de madeira de revista sem pagar móvel planejado, a Veio Certo é a prateleira de madeira de verdade com acabamento à escolha, a partir de R$119. Diferente do MDF com adesivo.*
   - **Por quê:** o grupo do visual de Pinterest teve 67% de compra no v2. Mas são só 3 compradores, então a evidência é fraca.
3. *Para quem já recebeu móvel quebrado ou sem parafuso, a Veio Certo é a prateleira que você vê embalada antes de sair, com reposição em 2 dias sem devolver nada.*
   - **Por quê:** é a reclamação nº 1 do setor. Mas só 1 de 3 compradores desse grupo comprou no v2.

**Recomendo a versão 1.** Ela segue a condição do conselho (sob medida e um canal) e a evidência mais repetida. As versões 2 e 3 viram ganchos de conteúdo.

### 3. Canais

| Canal | Por que serve | Custo | Como saber se funcionou | Começa? |
|---|---|---|---|---|
| **Anúncio no Mercado Livre** (busca orgânica) | É onde o comprador já procura "prateleira sob medida" e "prateleira madeira maciça" | Só a comissão (~12%) | Visitas/dia ≥ 30 e conversão ≥ 1% (painel do vendedor) | ✅ sim |
| **Seu Instagram e TikTok** (você já cria conteúdo) | O marceneiro e o processo são o conteúdo. Vídeo de oficina e de teste de carga gera confiança, e é isso que falta à loja nova | R$0 + seu tempo | Cliques no link do anúncio e mensagens "quero uma na medida X" | ✅ sim |
| **WhatsApp: sua lista, clientes antigos e grupos do bairro** | Gente que já confia em você compra primeiro e gera as primeiras avaliações | R$0 | Pedidos com origem "indicação" | ✅ sim |
| Mercado Livre Ads (anúncio pago) | Acelera visitas | Por clique | Custo por venda < limite da seção 5 | ⏸ só depois que a margem real for positiva |
| Shopee, Elo7, MadeiraMadeira | Mais alcance | Comissões (MadeiraMadeira ~19%) | — | ❌ não: o conselho pediu 1 canal por 90 dias |
| Influenciadores pagos | Alcance | Variável | — | ❌ não: sem verba e sem margem ainda |

### 4. Dez ganchos

Cada um responde a uma objeção ou usa um motivo de compra:

| # | Formato | Gancho | Responde a |
|---|---|---|---|
| 1 | Vídeo (3 s) | "Coloquei 30 kg nessa prateleira e deixei 3 dias. Olha o que aconteceu." | "Aguenta 15 kg?" |
| 2 | Vídeo (3 s) | "Isso aqui é MDF com adesivo. Isso aqui é madeira. Repara no topo." | "É madeira de verdade?" |
| 3 | Vídeo (3 s) | "Seu vão tem 87 cm e nenhuma prateleira pronta cabe? Eu faço na medida." | Medida exata |
| 4 | Título do anúncio | "Prateleira Sob Medida Madeira Maciça — Feita por Marceneiro, Até 120 cm" | Busca e medida exata |
| 5 | Vídeo (3 s) | "Antes de despachar, eu te mando a foto do SEU kit embalado." | "Loja nova, não confio" |
| 6 | Post ou carrossel | "Pinus fica amarelado? Depende do verniz. Natural, fosco ou freijó: veja os três na parede." | "Pinus amarelado" |
| 7 | Vídeo (3 s) | "20 anos de marcenaria e a reclamação que mais escuto é: 'faltou parafuso'. Por isso vai um a mais de cada." | Peça faltando |
| 8 | Stories | "Drywall? Me fala sua parede antes de comprar. Te digo a carga certa e mando a bucha certa." | Drywall |
| 9 | Vídeo (3 s) | "Por que minha prateleira custa R$119 e a de MDF R$70? Te mostro em 20 segundos." | Preço contra o MDF |
| 10 | Mensagem de WhatsApp | "Abri a minha loja: prateleira sob medida em madeira maciça, feita por mim. Os 30 primeiros pedidos saem a preço de lançamento até 31/12." | Primeiras vendas |

**Oferta de lançamento** (de `pricing.md`): kit a R$119 para os primeiros 30 pedidos ou até 31/12/2026, depois R$139. Sob medida a R$169 e tingido a R$189. Sempre com a data de fim. **Nunca "de R$X por R$Y"** com um preço que nunca foi cobrado.

### 5. Verba e números

**Verba de anúncio pago: R$0 no lançamento.** O motivo:
- Com os custos de hoje, cada kit perde R$20,17 (`numbers.json`). O limite para pagar por cliente é **contribuição por kit × compras por comprador** = -R$20,17 × 1,0 = **menos que zero**.
- No cenário enxuto de `terceirizacao.md` (R$169, suporte a R$4, frete R$15, terceirizado a R$20), a conta é **R$18,43 × 1,0 = no máximo ~R$18 por cliente**. A média de 1,0 compra no 1º mês vem dos painéis.
- Os R$2.000 já estão no primeiro lote (`launch.md`). Se a margem real ficar positiva depois das cotações, teste **R$100 de Mercado Livre Ads** tirados da reserva, só no sob medida, com limite de custo por venda abaixo da contribuição real.

**Os três números da semana** (fechamento de sexta):

| Número | Limite que pede mudança |
|---|---|
| Visitas por dia no anúncio | < 30 → mudar título, palavras-chave e foto principal |
| Conversão (visitas → vendas) | < 1% → fotos, ganchos 1, 2 e 5 no anúncio, responder as perguntas repetidas na descrição |
| Avaliações com foto | < 3 até 31/12 → reforçar o cartão e a mensagem pós-entrega (sem trocar por desconto) |

### 6. Calendário de 30 dias (16/11 a 16/12/2026)

IG = Instagram, TT = TikTok, WA = WhatsApp, ML = Mercado Livre.

| Data | Canal | O que sai |
|---|---|---|
| seg 16/11 | IG/TT | "Vou abrir minha loja online. 20 anos de marcenaria, agora prateleira sob medida." Rosto e oficina |
| ter 17/11 | IG/TT | Bastidores: escolhendo e conferindo tábuas (higrômetro, sem miolo) |
| qua 18/11 | IG/TT | Gancho 2: madeira × MDF com adesivo (topo e veio) |
| qui 19/11 | IG/TT | Gancho 1, parte 1: começa o teste de 30 kg ("volto em 72 h") |
| sex 20/11 | WA | Convite pessoal para 5 conhecidos comprarem no lançamento fechado (link do anúncio) |
| sáb 21/11 | ML/WA | **Lançamento fechado**: 5 pedidos reais. Stories da produção |
| dom 22/11 | IG/TT | Gancho 1, parte 2: resultado do teste de 72 h |
| seg 23/11 | IG/TT | Gancho 5: a foto do kit antes de despachar (mostrar a do lançamento fechado) |
| ter 24/11 | IG/TT | Gancho 7: "vai um parafuso a mais de cada" |
| qua 25/11 | IG/TT | Gancho 6: os 3 acabamentos lado a lado |
| qui 26/11 | IG/TT | Gancho 3: "seu vão tem 87 cm?" + como medir em 3 pontos |
| sex 27/11 | IG/TT | Black Friday: **sem desconto extra.** "Não entro em guerra de preço, entro em prateleira que dura." Processo da oficina |
| sáb 28/11 | IG/TT | Caixa e teste de queda de 1 m |
| dom 29/11 | IG/TT | "Amanhã abre. Os 30 primeiros a preço de lançamento até 31/12." |
| **seg 30/11** | **ML/IG/TT/WA** | **Lançamento público**: gancho 10 no WhatsApp, post e stories com o link (roteiro em `launch.md`) |
| ter 01/12 | IG/TT | Gancho 9: R$119 × R$70 em 20 segundos |
| qua 02/12 | IG/TT | Bastidores: furação do pino no gabarito |
| qui 03/12 | IG/TT | Gancho 8: drywall, me fala sua parede |
| sex 04/12 | IG | Números verdadeiros da semana ("X kits saíram") |
| sáb 05/12 | IG/TT | Instalação em 3 minutos (o vídeo do QR code) |
| dom 06/12 | IG | Pergunta nos stories: "qual vão da sua casa está vazio?" |
| seg 07/12 | — | **Revisão do dia 7** (visitas e conversão). Ajustar o anúncio |
| ter 08/12 | IG/TT | Responder em vídeo a pergunta mais repetida no ML |
| qua 09/12 | IG/TT | Gancho 3 de novo, com um pedido sob medida real (com permissão do cliente) |
| qui 10/12 | IG/TT | Bastidores: aplicação do tingido freijó |
| sex 11/12 | IG | Números da semana. Quantos dos 30 de lançamento restam (só o número real) |
| sáb 12/12 | IG/TT | Presente de Natal: "prateleira na medida, para chegar antes do dia 24", com o prazo real de produção e entrega |
| dom 13/12 | IG | Fotos de clientes, **só as enviadas com autorização** |
| seg 14/12 | — | **Revisão do dia 14: linha de sucesso** (10 pedidos, 1% de conversão, margem positiva) |
| ter 15/12 | IG/TT | Gancho 2 ou 1, o que tiver performado melhor, repostado |
| qua 16/12 | IG/TT | "Último prazo para chegar antes do Natal", só se for verdade |

**Quando não há novidade:** bastidores da oficina, a escolha da tábua, erros e acertos de 20 anos, antes e depois de uma parede **da sua casa**, explicação de madeira, verniz ou parede, e respostas às perguntas do Mercado Livre.

### Regras

- **Nada de avaliação, depoimento, antes e depois ou número de seguidores falso.** Foto de cliente só com autorização por escrito.
- As frases dos painéis são **pesquisa simulada**: nunca use em anúncio como fala de cliente.
- Parceria paga deve ser sinalizada (#publi). As promessas de carga, garantia e prazo precisam ser cumpridas: o CDC e o CONAR valem para anúncio. Isto não é aconselhamento jurídico.

## Brand

**Posicionamento usado aqui:** ainda não existe `founder/marketing.md`. Por isso o posicionamento abaixo foi tirado do conselho, da oferta e dos painéis. Confirme ou ajuste no `/founder-marketing`.

> **Prateleira sob medida em madeira de verdade, feita por um marceneiro com 20 anos de oficina, que chega inteira e completa.**

Por que esse posicionamento:
- Os compradores que fecharam compra queriam **medida exata** e **madeira de verdade** (ver `panel/results.md` e `panel-v2/results.md`).
- O motivo nº 1 de recusa foi **"loja nova, não confio"**. O seu ofício de 20 anos é a resposta mais forte para isso, e a única vantagem difícil de copiar que o conselho encontrou.

### 1. Dez candidatos a nome

| # | Nome | Estilo | O que diz | Em voz alta / no ícone | Risco |
|---|---|---|---|---|---|
| 1 | **Veio Certo** | evocativo | Duplo sentido: o *veio* da madeira e "o pedido *veio certo*", que responde direto à reclamação nº 1 do setor | Curto e fácil de falar; "VC" funciona no ícone | Nenhuma marcenaria com esse nome apareceu na busca. Falta checar no INPI |
| 2 | **[Seu nome] Marcenaria** | nome do fundador | Pessoa real, ofício real e confiança | Depende do nome | Fraco como marca registrável se o sobrenome for comum. Não escala se um dia tiver equipe |
| 3 | **Oficina 20** | evocativo | 20 anos de oficina | "Oficina vinte" soa forte e o número funciona no ícone | O número "envelhece" (vira 21, 22…), e "oficina" é termo genérico |
| 4 | **Pino & Veio** | descritivo e evocativo | O suporte invisível (pino) e a madeira (veio) | Simpático; "P&V" no ícone | Ninguém com esse nome apareceu na busca. O "&" complica domínio e @ |
| 5 | **Medida Exata** | descritivo | Sob medida | Claro, mas sem graça | Muito genérico. O INPI tende a recusar ou a proteção fica fraca |
| 6 | **Kit Parede Pronta** | descritivo (produto) | O resultado: parede pronta | Longo para um ícone | É nome de **produto**, não de marca. Use como nome da oferta |
| 7 | **Madeira de Verdade** | descritivo | Contra o MDF com adesivo | Forte em voz alta | Expressão comum, provavelmente não registrável sozinha |
| 8 | **Tábua Corrida** | evocativo | Madeira e ritmo de casa | Bom de falar | Termo técnico de piso, confunde |
| 9 | **Lenho** | evocativo ou inventado | Madeira, em palavra curta e elegante | Ótimo no ícone | Palavra de dicionário, é provável que já exista em algum lugar. Checar |
| 10 | **[Sua cidade] Marcenaria** | lugar | Origem e proximidade | Depende da cidade | Pouco distintivo. Não escala para venda nacional |

### 2. Os três finalistas e as verificações que você precisa fazer

**Finalistas: 1. Veio Certo · 2. Pino & Veio · 3. [Seu nome] Marcenaria**

Recomendo **Veio Certo**: é curto, tem duplo sentido e promete exatamente o que os compradores temem não receber.

Eu só consigo fazer buscas públicas. Daqui não tive acesso ao registro de domínios nem às redes sociais. **Só um advogado ou agente de marcas confirma a disponibilidade, e nada fica registrado até você mesmo registrar.** Isto não é aconselhamento jurídico.

| Verificação | Como fazer | Veio Certo | Pino & Veio | [Seu nome] Marcenaria |
|---|---|---|---|---|
| **Marca no INPI** | [Busca de marcas do INPI](https://busca.inpi.gov.br/pePI/) por nome, nas **classes 20** (móveis e prateleiras) e **35** (comércio varejista de móveis) — [lista de classes](https://www.gov.br/inpi/pt-br/assuntos/arquivos-dirma-1/NCL11Listadeclassesenotasexplicativas.pdf) | ⬜ a fazer | ⬜ a fazer | ⬜ a fazer |
| **Domínio .com.br** | [registro.br](https://registro.br) (eu não consegui acessar daqui) | ⬜ veiocerto.com.br | ⬜ pinoeveio.com.br | ⬜ |
| **Instagram / TikTok / YouTube** | Procurar @veiocerto, @veiocerto.marcenaria ou @veiocertomarcenaria | ⬜ | ⬜ | ⬜ |
| **Nome da loja no Mercado Livre** | Tentar criar o apelido da loja | ⬜ | ⬜ | ⬜ |
| **Confusão com concorrentes** | Comparado com `competitors.md` | ✅ Nenhum parecido. O nome mais próximo encontrado foi "Ponto Certo Móveis" (SP), parecido só no "Certo" | ✅ Nenhum parecido | ✅ |

Plano B se o .com.br estiver ocupado: veiocertomarcenaria.com.br ou veiocerto.art.br.

### 3. Voz e promessa

**A promessa, numa linha:** *Chega na medida, inteira e completa. Se não chegar, o problema é nosso.*

**Três opções de slogan:**
1. **Veio Certo. Madeira de verdade, na medida da sua parede.**
2. Feito por marceneiro, não por fábrica.
3. Do jeito que você pediu, do jeito que chegou.

**A voz em três adjetivos:**

| Adjetivo | Faça | Não faça |
|---|---|---|
| **De ofício** | Fale como quem sabe: "pinus seco em estufa, sem miolo, selado nas 6 faces" | Termos vagos como "alta qualidade", "premium" ou "o melhor" |
| **Direta** | Prazo, carga e garantia em números: "15 kg em alvenaria", "postado em 1 dia útil" | Letra miúda, "consulte condições" ou promessas sem número |
| **Calorosa** | Primeira pessoa e bastidores: "eu furo cada pino no gabarito" | Tom de robô corporativo ou excesso de emoji |

**Antes e depois** (uma frase de `founder/pitch.md`):
- *Antes:* "Kit Parede Pronta: 3 prateleiras flutuantes 60x20 cm em madeira maciça de pinus, feitas por uma marcenaria e vendidas no Mercado Livre e na Shopee."
- *Depois:* "Três prateleiras de pinus maciço, 60x20, feitas por mim na minha oficina. Marceneiro há 20 anos. Furo cada pino no gabarito e te mando foto do seu kit antes de despachar."

### 4. O visual (briefing)

**Cores** (contrastes calculados pela fórmula WCAG):

| Cor | Hex | Papel | Contraste |
|---|---|---|---|
| Grafite | `#2B2A28` | Texto, logo, etiqueta | 12,5:1 sobre Areia ✅ AAA |
| Areia | `#F5EFE6` | Fundo de foto, cartão, embalagem | — |
| Freijó | `#8A5A2B` | Destaque, selo, botões | 5,1:1 sobre Areia ✅ AA · branco sobre Freijó 5,9:1 ✅ AA |
| Musgo (opcional) | `#3F5B45` | Detalhe secundário, stories | branco sobre Musgo 7,5:1 ✅ AAA |

Os concorrentes de MDF usam muito preto e branco nas fotos. A paleta quente de madeira e areia separa você deles, sem copiar ninguém.

**Tipografia** (as duas são gratuitas, licença OFL, no [Google Fonts](https://fonts.google.com)):
- **Títulos:** [Fraunces](https://fonts.google.com/specimen/Fraunces), serifada, com cara de ofício.
- **Texto:** [Inter](https://fonts.google.com/specimen/Inter), legível em celular e em etiqueta.

**Briefing do logo:**
- **O que precisa dizer:** madeira de verdade, precisão e mão de marceneiro.
- **Ideias de partida:** o veio da madeira formando um "V" ou um ✓ (o "certo"), ou um pino entrando na madeira.
- **Onde precisa funcionar:** carimbo de 1 cor na caixa de papelão, gravado a quente ou a laser na madeira, ícone de 32 px da loja no Mercado Livre e no Instagram, e etiqueta preto e branco.
- **O que evitar:** serrote, martelo ou árvore genérica (todo mundo usa), degradês (não carimbam) e letras finas (somem no ícone pequeno).
- Se quiser, gero **conceitos** com uma ferramenta de imagem. Seriam ideias de partida, não um logo final.

**Os cinco primeiros pontos de contato:**
1. **Capa da loja no Mercado Livre e perfil do Instagram:** foto sua na oficina, nome, slogan e "Marceneiro há 20 anos".
2. **Caixa:** carimbo Veio Certo em grafite e, dentro, um cartão em areia: *"Conferido por [seu nome]. Se faltar algo, me chama: resolvo em até 2 dias úteis."*, com QR do vídeo de instalação e um pedido de foto da prateleira instalada (sem troca por desconto).
3. **Confirmação do pedido (chat):** *"Recebi seu pedido! Vou fazer seu kit e te mando a foto dele embalado antes de despachar. Postagem até [data]."*
4. **Primeiro post:** vídeo do teste de carga com 30 kg por 72 h na sua oficina, com a legenda *"Antes de vender, eu testo."*
5. **Resposta à primeira reclamação:** *"Poxa, sinto muito. Me manda uma foto que eu já separo a peça. Sai em até 2 dias úteis e você não precisa devolver nada."*

Próximos passos: `/founder-marketing` (posicionamento final e calendário de posts) e checar o nome no INPI e no registro.br.

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

## Launch plan

Hoje é terça, 03/11/2026. Ainda não há data-alvo informada. Proponho a mais cedo que dá para cumprir com os prazos de `founder/ops.md`:

- **Lançamento fechado:** sábado, **21/11/2026**.
- **Lançamento público:** segunda, **30/11/2026**, logo depois da Black Friday (27/11), com o preço de lançamento valendo até 31/12/2026, como está na oferta.

Responsável por tudo: **você**. Ainda não há mais ninguém no time.

### 1. O teste antes de gastar

**O teste:** em vez de fazer estoque, publicar o anúncio real no Mercado Livre e produzir **por pedido**. O sob medida já funciona assim. Do kit pronto, só um lote pequeno de 5 unidades. Em paralelo, faça uma **pré-venda para a sua rede** (Instagram, WhatsApp, quem já é cliente da marcenaria). É o seu ponto forte como criador de conteúdo.

**Linha de sucesso, definida antes de começar** (14 dias de anúncio público, 30/11 a 13/12):
- [ ] **10 pedidos pagos**, com pelo menos 5 do sob medida (R$169 ou mais)
- [ ] **Conversão no anúncio ≥ 1%** (visitas → vendas, no painel do Mercado Livre)
- [ ] **3 avaliações com foto** até 31/12
- [ ] **Margem real por kit positiva**, medida com custo e frete reais
- [ ] **Zero reclamações** por peça faltando ou medida errada

**Como comparar com o painel:** o painel simulado chegou a 25% de intenção de compra, mas mede quem viu a oferta inteira e decidiu, não quem passou pelo anúncio. A conversão real de marketplace costuma ser muito menor que isso. Se em 14 dias vierem **menos de 5 pedidos**, confie nos compradores reais e volte ao `/founder-offer` ou ao `/founder-pricing`. Se a **margem real for negativa**, pare o kit pronto e mantenha só o sob medida.

**Orçamento do teste (de R$2.000).** Valores estimados, exceto madeira e suporte, que vêm dos preços públicos do `cfo-sources.md`:

| item | valor |
|---|---:|
| Madeira para ~10 kits (R$37,40 por kit) | R$374 |
| 60 suportes (R$8 a unidade) | R$480 |
| 15 caixas onda dupla (~R$20 cada) | R$300 |
| Selador e verniz à base d'água | R$150 |
| Ferragens, cantoneiras e plástico | R$80 |
| Higrômetro de madeira | R$150 |
| **Reserva** para reposições, frete de troca e imprevistos | **R$466** |
| **Total** | **R$2.000** |

### 2. A contagem regressiva

🔴 = caminho crítico: se atrasar, o lançamento atrasa.

**Semana 1 — 03/11 a 08/11: números reais**
- [ ] 🔴 Cotar o corte e o aparelhamento na madeireira (2 madeireiras), até 05/11
- [ ] 🔴 Cotar o suporte no atacado **ou** fazer 6 pinos e chapas e anotar custo e tempo, até 06/11
- [ ] 🔴 Cotar a caixa onda dupla na medida certa, com prazo de entrega, até 06/11
- [ ] 🔴 Simular o frete real no Mercado Livre com o peso e a caixa, até 07/11
- [ ] Rodar o `/founder-cfo` de novo com os números reais e o modelo enxuto, até 08/11. **Se a margem por kit continuar negativa, lance só o sob medida.**

**Semana 2 — 09/11 a 15/11: legal e protótipo**
- [ ] 🔴 Abrir o MEI no Portal do Empreendedor, confirmando a ocupação, até 10/11
- [ ] Conta PJ ou Mercado Pago no CNPJ, até 11/11
- [ ] Confirmar com a prefeitura ou o condomínio o trabalho em casa, até 12/11
- [ ] 🔴 Comprar o primeiro lote de madeira, suportes, verniz e ferragens, até 11/11 (as caixas dependem do prazo do fabricante)
- [ ] 🔴 Fazer 3 kits de protótipo seguindo o `quality-spec.md`, até 14/11
- [ ] 🔴 **Teste de carga de 30 kg por 72 h** em 1 prateleira, de 12/11 a 15/11, filmado
- [ ] 🔴 **Teste de queda** de 1 m numa caixa pronta, até 15/11
- [ ] Rodar `/founder-brand` (nome final, se não for "Kit Parede Pronta") e `/founder-marketing` (calendário), até 15/11

**Semana 3 — 16/11 a 22/11: anúncio e lançamento fechado**
- [ ] 🔴 Fotos do anúncio: prateleira instalada e carregada, veio de perto, as duas opções de acabamento e o tingido, até 17/11
- [ ] 🔴 Vídeo curto do teste de carga e vídeo de instalação de 3 minutos (QR code no cartão), até 18/11
- [ ] 🔴 Criar o anúncio no Mercado Livre, até 19/11. Incluir: carga por tipo de parede, data total no sob medida, garantia e "loja nova". **Sem "de R$X por R$Y" falso.**
- [ ] Imprimir o cartão da caixa (pedido de foto, QR do vídeo) e o checklist de conferência, até 19/11
- [ ] **Sábado 21/11 — lançamento fechado:** vender pelo anúncio real para 5 pessoas conhecidas, a preço cheio ou de lançamento. Elas compram, instalam e contam o que deu errado, com honestidade. **Não peça avaliação positiva:** peça avaliação sincera, com foto, se quiserem.

**Semana 4 — 23/11 a 29/11: ajustes**
- [ ] Corrigir o que os 5 primeiros apontaram (embalagem, instrução, ferragem), até 25/11
- [ ] Preparar o estoque mínimo: 5 kits prontos e material para 10 sob medida, até 27/11
- [ ] Posts de pré-lançamento no seu Instagram (bastidores da marcenaria, teste de carga), de 24/11 a 29/11
- [ ] Black Friday (27/11): não entre na guerra de desconto. Use os dias para mostrar o processo.

**Segunda 30/11 — lançamento público**

### 3. Dia do lançamento (segunda, 30/11/2026)

| hora | o quê |
|---|---|
| 07h30 | Conferir que o anúncio está ativo, com preço R$119 e as variações sob medida (R$169 e R$189) |
| 08h00 | Post de lançamento no Instagram e Stories (vídeo do teste de carga e link do anúncio). Mensagem no WhatsApp para a lista de contatos e clientes antigos |
| 08h00–12h00 | Responder **toda** pergunta do anúncio em até 30 minutos. Pergunta de pré-venda vira venda |
| 10h00 | Stories: bastidores da furação e do acabamento |
| 12h00 | Confirmar a medida dos pedidos sob medida por escrito no chat |
| 13h00–16h00 | Produzir os pedidos do dia (furação, lixa e selador) |
| 16h00 | Embalar o que estiver pronto, tirar a foto de conferência e enviar ao cliente |
| 17h00 | Postar. Segunda janela de respostas |
| 18h00 | Stories: "primeiro dia, X pedidos". Só números verdadeiros |
| 21h00 | Anotar no controle: visitas, pedidos, perguntas mais repetidas, tempo por kit |

**Se algo der errado** (do registro de riscos em `ops.md`):
- **Anúncio pausado ou recusado pelo Mercado Livre:** revisar o motivo, corrigir e reativar. Enquanto isso, vender pela rede com link de pagamento do Mercado Pago.
- **Muitos pedidos sob medida ao mesmo tempo:** aumentar o prazo no anúncio antes de prometer. Melhor 10 dias cumpridos que 7 estourados.
- **Primeira reclamação:** seguir a rotina D, com resposta em até 4 horas e reposição em até 2 dias úteis.
- **Faltou material:** pausar a variação do kit pronto e manter o sob medida.

### 4. Os primeiros 30 dias (30/11 a 29/12)

**Números da semana** (fechamento de sexta):

| número | de onde vem | limite que força mudança |
|---|---|---|
| Pedidos por dia | Mercado Livre | Menos de 0,5/dia na 2ª semana → rever foto, título e preço |
| Conversão (visitas → vendas) | Painel do vendedor no ML | Menos de 1% → rever fotos e as perguntas que ficaram sem resposta |
| Visitas por dia | Painel do vendedor no ML | Menos de 30/dia → título e palavras-chave (`/founder-marketing`) |
| Margem real por kit | Seu controle com custos reais | Negativa → parar o kit pronto e vender só sob medida |
| Tempo por kit | Cronômetro | Sob medida acima de 2× o tempo do kit pronto → subir o preço do sob medida |
| Reclamações | Chat e avaliações | 2 com a mesma causa → mudar o processo na hora |
| Avaliações com foto | Mercado Livre | Menos de 3 até 31/12 → reforçar o cartão e a mensagem pós-entrega |
| Faturamento do mês | Controle | Acima de R$5.000/mês → falar com o contador sobre o teto do MEI |

O plano do CFO (5 kits/dia) ainda é o cenário com galpão. **O ponto de equilíbrio do modelo enxuto só sai depois das cotações da semana 1.**

**Revisões:**
- **Dia 7 (07/12):** as pessoas veem o anúncio? (visitas) Quem vê, compra? (conversão) Que pergunta todo mundo faz e o anúncio não responde?
- **Dia 14 (14/12): a linha de sucesso.** Bateu 10 pedidos, 1% de conversão e margem positiva? Se **não**: voltar ao `/founder-offer` ou ao `/founder-pricing` com os dados reais, não com o painel. Se **sim**: manter e planejar o estoque de dezembro.
- **Dia 30 (29/12):** quanto sobrou de verdade? Quanto tempo leva cada peça? O sob medida paga a sua hora? Depois de 31/12, o preço do kit sobe para R$139 como prometido? Qual é o próximo passo: segundo canal (Shopee ou Elo7), mais um produto, ou continuar focado mais 60 dias, como pediu o conselho?

_The panel is simulated buyers and the numbers are projections from your inputs. Confirm demand with real customers and costs with real quotes before you spend. Not financial, legal or tax advice._
