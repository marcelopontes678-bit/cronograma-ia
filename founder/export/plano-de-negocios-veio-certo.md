# Veio Certo: tábua de corte end grain · Plano de negócios

**Veredito: Profitable (lucrativo, nas estimativas)**

- ✓ Each tabua end grain 40x30x4 earns R$83.36 before fixed costs (33% contribution).
- ✓ Year 1 operating profit: R$35,619.
- ✓ Break-even is 1 tabua end grain 40x30x4s a day against a capacity of 3.
- ✓ 10 of 20 simulated buyers buy (50%, the bar is 25%).

| número-chave | |
| --- | ---: |
| Price | R$249.00 a tabua end grain 40x30x4 |
| Profit margin at plan | 31% per tabua end grain 40x30x4 |
| Break-even | 1 tabua end grain 40x30x4s a day |
| Year 1 operating profit | R$35,619 |
| Startup spend | R$2,000 |
| Cash needed before it pays for itself | R$2,000 |
| Startup money earned back | month 3 |
| Buyer panel | 10 buy · 10 pass |

## A ideia

- **O que é:** um marceneiro com 20+ anos de oficina fabrica em casa tábuas de corte end grain (madeira de topo) em xadrez de madeiras nobres brasileiras e vende pelo Mercado Livre.
- **Para quem:** brasileiros de 28 a 55 anos que fazem churrasco ou cozinham em casa e se importam com as facas, e quem procura um presente marcante (Natal e Dia dos Pais).
- **O que vende e a que preço:** tábua 40x30x4 cm, numerada e assinada, a **R$249 de lançamento** (30 primeiros pedidos ou até 31/12/2026) e **R$349 depois**. Planejada, ainda não testada: tábua de presente menor, 30x20, a R$149–179.
- **Onde e como:** Mercado Livre, envio pelo vendedor e postagem em até 5 dias úteis.
- **Orçamento e restrições:** R$2.000. O fundador é marceneiro experiente. Produção em casa, como MEI.
- **Madeiras:** Marfim (clara) e Muiracatiara (escura) são **sugestão a confirmar** pelo marceneiro.
- **Histórico:** o pack começou com prateleiras de pinus. A análise mostrou prejuízo por peça (`arquivo-prateleiras/`) e o produto mudou para a tábua em 03/11/2026.

## Resumo

**Veredito: Profitable** (calculado pelo `compile.py`), **com base em estimativas e compradores simulados.** Ainda não houve nenhuma venda real. A madeira, o frete e o tempo por tábua precisam ser cotados e medidos antes de qualquer gasto.

**O negócio:** um marceneiro com 20+ anos de oficina faz em casa tábuas de corte end grain (madeira de topo), em xadrez de duas madeiras nobres brasileiras, numeradas e assinadas, e vende no Mercado Livre. O público é quem faz churrasco ou cozinha a sério e quem procura um presente marcante. O produto substituiu as prateleiras, que davam prejuízo ou margem quase nula por peça (`arquivo-prateleiras/`).

**Os três números (R$249 de lançamento, até 2 tábuas/dia):**

- **Lucro por tábua: R$83,36 (33%).** Margem no plano: 31%.
- **Equilíbrio: ~0,15 tábua/dia** (uns 5 por mês). A capacidade estimada é de 3/dia.
- **Ano 1: +R$35.619 de operação.** Os R$2.000 voltam no 3º mês. A R$349, o lucro por tábua vai a R$171 e o ano 1 a +R$78.123.

**Painel e conselho:**

- O painel da tábua subiu de **10% para 50% de compra** quando a oferta passou a nomear as madeiras, enviar a foto da tábua do cliente, numerar e assinar, e garantir o prazo de presente, junto com o preço de lançamento.
- A renda alta comprou toda. Quem caça preço e quem compra presente com orçamento apertado não comprou.
- O conselho avaliou a ideia anterior (prateleiras). As condições dele continuam valendo e estão atendidas: um produto, um canal, sem galpão e sem funcionário. O prejuízo por peça foi resolvido.

**Maior risco:** os números de custo e tempo. Se a madeira passar de R$60 por tábua ou o tempo passar de 5 h, a margem cai muito. No pior caso testado (R$249, madeira a R$90, frete a R$35), ainda sobram R$43 por tábua, mas sem pagar o seu trabalho de forma justa. **O que fazer:** cotar antes de comprar, cronometrar o 1º lote e subir para R$349.

**Outros riscos:**

- Loja nova, sem avaliações.
- Teto do MEI estourando por volta do 8º mês.
- Regras da Anvisa e do Inmetro para utensílio em contato com alimento.
- Um concorrente já usa marfim e muiracatiara.

**Para começar:** R$2.000, que cabem no orçamento, para o 1º lote de ~15 tábuas e os insumos. O teste real é vender 10 tábuas entre 30/11 e 13/12, com lucro por tábua ≥ R$60 e ≤ 5 h por peça (`launch.md`).

**Esta semana:**

1. Escolher o par de madeiras e **cotar na madeireira**.
2. **Simular o frete** da caixa no Mercado Livre.
3. Confirmar as regras da **Anvisa e do Inmetro** para tábua de madeira.

_O painel são compradores simulados e os números são projeções a partir de estimativas. Clientes e orçamentos reais confirmam ou derrubam tudo isso. Isto não é aconselhamento financeiro, jurídico nem tributário: um contador deve revisar o enquadramento e os impostos._

## O conselho

> **Nota (03/11/2026):** o conselho avaliou a ideia anterior, as prateleiras. O produto mudou para a tábua end grain. Os riscos levantados continuam válidos: loja nova sem avaliações, um produto e um canal por 90 dias, e evitar galpão e funcionário. O risco de prejuízo por peça foi resolvido pela tábua (ver `cfo.md`). Para uma avaliação nova, rode o `/founder-board` de novo.

## Conselho: Kit Parede Pronta

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

## Concorrência

Pesquisa de 2026-11-03. Os dados vêm de **trechos de busca**, porque o Mercado Livre bloqueia acesso automatizado daqui. Os preços são de anúncio. Confira antes de decidir.

### Quem já vende

| Concorrente / anúncio | Canal | Preço | Madeira | Fonte |
|---|---|---:|---|---|
| End grain carvalho europeu | ML | — | carvalho | [ML](https://produto.mercadolivre.com.br/MLB-3813436327-tabua-de-corte-end-grain-madeira-carvalho-europeu-exclusiva-_JM) |
| End grain teca (frete grátis) | ML | R$329 | teca | [ML end grain](https://lista.mercadolivre.com.br/tabuas-de-corte-end-grain) |
| End grain peroba | ML | R$354,25 | peroba | [ML end grain](https://lista.mercadolivre.com.br/tabuas-de-corte-end-grain) |
| Faixa geral end grain | ML | R$329–440 | teca, peroba, eucalipto, carvalho | [ML](https://lista.mercadolivre.com.br/tabua-end-grain) |
| Ponciano Tábuas Artesanais (teca premium 50x30) | loja própria | R$480 (R$456 Pix) | teca | [Ponciano](https://poncianotabuasartesanais.com/products/tabua-end-grain-retangular-teca-premium) |
| Original Woodcraft | loja própria | R$600 (R$570 Pix) | imbuia, marfim, muiracatiara | [Original Woodcraft](https://www.originalwoodcraft.com.br/157-tabua-de-corte-end-grain) |
| Rickgreen Woodworks | loja própria | — | — | [Rickgreen](https://rickgreen.com.br/tabuas-de-corte) |
| Cutelaria Cimo (teca) | loja própria | — | teca | [Cimo](https://www.cutelariacimo.com.br/products/tabua-end-grain-teca) |
| Tábua artesanal de angelim (substituto) | ML | R$78,90 | angelim | [ML](https://lista.mercadolivre.com.br/tabua-de-corte-madeira) |
| Tábuas comuns e personalizadas (substituto) | ML | R$38–240 | pinus, teca | [ML](https://lista.mercadolivre.com.br/tabua-de-frios-personalizada) |

**Faixa de preço da end grain:** de R$329 (ML) a R$600 (loja artesanal). Os substitutos ficam entre R$38 e R$100.

> ⚠️ **Atenção:** a Original Woodcraft já usa **marfim e muiracatiara**, as mesmas madeiras sugeridas para a nossa oferta. Para não parecer cópia, considere outro par de madeiras ou um desenho próprio.

### A lacuna

- O painel simulado mostrou que o comprador desconfia de **madeira tingida** e de **cola que solta**, e que acha o **xadrez genérico**.
- Ninguém nas fontes encontradas promete, ao mesmo tempo:
  - **foto da tábua do próprio cliente antes do envio**;
  - **peça numerada e assinada** por um marceneiro;
  - **prazo de presente garantido**.
- **R$249** fica abaixo de toda end grain encontrada, mas o plano é subir para R$349.

### A ameaça

- Quem já vende end grain no ML (teca, peroba) pode copiar a foto antes do envio e a numeração em uma semana.
- A defesa é a assinatura de um marceneiro real, com 20 anos de oficina mostrados no Instagram, e a mesma pessoa no chat.
- Reclamações públicas de clientes desses concorrentes **não foram pesquisadas**. Faça isso antes de lançar.

---

## Arquivo: concorrentes das prateleiras (análise anterior)


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

## Painel de compradores (simulado)

**10 buy · 10 pass** (50% buy) out of 20 simulated buyers. Seed 825715, so the same cards can be dealt again.

These are simulated buyers, not customers. Use this to find objections and weak spots, then confirm the big ones with real people before you spend.

### By segment

| group | buyers | buy rate |
| --- | ---: | ---: |
| Renda alta, gosta de cozinha e design, renda anual em R$ | 7 | 100%  (thin) |
| Classe media que cozinha em casa, renda anual em R$ | 9 | 33% |
| Renda mais apertada, compra para presentear, renda anual em R$ | 4 | 0%  (thin) |

### By buying behaviour

| group | buyers | buy rate |
| --- | ---: | ---: |
| Quer peca de design | 2 | 100%  (thin) |
| Cozinheiro entusiasta | 4 | 75%  (thin) |
| Churrasqueiro de fim de semana | 5 | 60%  (thin) |
| Procurando presente | 4 | 50%  (thin) |
| Le todas as avaliacoes | 2 | 0%  (thin) |
| Cacador de preco | 3 | 0%  (thin) |

### By income

| group | buyers | buy rate |
| --- | ---: | ---: |
| R$186,000 and up | 7 | 100%  (thin) |
| R$73,000 to R$186,000 | 7 | 43%  (thin) |
| under R$73,000 | 6 | 0%  (thin) |

### Why they pass

| reason | buyers | in their words |
| --- | ---: | --- |
| price | 8 | "Minha tabua ta riscada e preciso trocar, mas R$249 numa tabua de loja nova, sem quase nenhuma avaliacao, e muito pra arriscar quando acho tabua de madeira por R$80. Vou deixar no favorito e ver se aparecem avaliacoes de gente que usou no churrasco." (P002) · "Achei bonita, a embalagem e a garantia de entrega antes do Natal ajudam, mas R$249 numa tabua ainda pesa demais pro meu orcamento de presente. Com esse dinheiro eu resolvo dois presentes, e tem tabua boa de madeira por R$80 a R$120." (P004) |
| trust | 2 | "Achei a tabua bonita e a proposta parece seria, mas eu so compro de anuncio com muitas avaliacoes, e loja nova com quase nenhuma eu nao arrisco R$249. Vou salvar o anuncio e voltar quando tiver gente contando como a tabua ficou depois de uns meses." (P005) · "Loja nova com quase nenhuma avaliacao, e eu so compro anuncio que tem muita avaliacao pra eu ler as de 1 e 2 estrelas primeiro. R$249 pra presentear e muito dinheiro pra apostar numa loja que eu nao conheco, ainda mais com o orcamento apertado." (P016) |

### Why they buy

| reason | buyers | in their words |
| --- | ---: | --- |
| quality | 6 | "Numerada, assinada e com a foto do topo da minha tabua antes de mandar: isso e presente que ninguem mais vai ter, e fica lindo no Instagram. Chegando ate 23/12 e com caixa de presente, por R$249 eu resolvo o Natal." (P001) · "Tábua end grain de 40x30x4 em Muiracatiara por R$249 com frete grátis é preço bom pra mim, e a foto da minha tábua antes de despachar mais a garantia de 12 meses tiram boa parte do risco. Se pagar R$249 e vier bem colada, vai virar a tábua do churrasco de sábado." (P003) |
| need | 3 | "Minha tabua ja esta riscada e com cheiro, e end grain de Muiracatiara a R$249 e mais barato que as importadas que eu vinha olhando. A foto do topo da minha tabua antes do envio e a compra pelo Mercado Livre me deixam arriscar mesmo com loja nova." (P006) · "Preciso de um presente nas proximas semanas e uma tabua end grain de Muiracatiara, numerada e assinada, e exatamente o tipo de coisa que um churrasqueiro guarda como trofeu. A R$249 com frete gratis e garantia de entrega antes do Natal, e mais barato que as end grain boas que vejo por ai, e o Mercado Livre me devolve o dinheiro se vier errado." (P012) |
| timing | 1 | "Preciso resolver o presente do meu marido para o Natal e isso parece especial de verdade: numerada, assinada, com caixa de presente e prazo claro se eu pedir até 10/12. Por R$249 com frete grátis fica dentro do que eu gastaria num presente bom, então eu peço cedo, lá pelo fim de novembro, para ter folga." (P018) |

### What would flip a no

- Ver umas 20 avaliacoes boas com foto de quem usa no churrasco, ou o preco cair para uns R$199.
- Se ficasse em torno de R$150 com frete gratis e a loja ja tivesse um bom numero de avaliacoes de quem comprou.
- Ver umas 30 ou mais avaliacoes reais com foto, inclusive as negativas, de pessoas que usam a tabua ha alguns meses.
- Ter umas 50 avaliacoes boas com foto de gente que ja usa ha meses, e o preco cair perto de R$150.
- Ver avaliacoes de outros compradores com fotos de tabuas reais que chegaram no prazo, ou o preco perto de R$180 com a embalagem de presente incluida.
- Ver umas 20 ou 30 avaliacoes boas com foto de gente que usa ha meses, ou o preco cair pra perto de R$180 parcelado sem juros.
- Preco perto de R$150 com varias avaliacoes boas de quem ja comprou, e alguma explicacao simples de por que madeira de topo nao e menos higienica que plastico.
- Ver umas 50 avaliacoes reais no Mercado Livre, inclusive as ruins, mostrando que a tabua aguenta e que a loja resolve problema, e o preco ficar perto de R$180.
- Ver várias avaliações de gente que comprou mostrando a tábua depois de meses de uso, e um cupom que deixasse ela perto de R$170 a R$180.
- Uma versão menor ou um cupom que deixasse ela por uns R$170, com algumas avaliações reais de compradores mostrando a tábua que chegou.

Buyers say they would buy **1.0 times** in the first month on average.

20 buyers gave all four price answers. Run founder-pricing's van_westendorp.py on the answers folder.

## Preço

Fontes: painéis `panel-tabua/` (v1, R$349) e `panel/` (= `panel-tabua-v2`, oferta nova a R$249), concorrentes em `competitors.md` e números em `cfo.md`. As respostas dos compradores simulados servem para **escolher o que testar**, não provam demanda.

### 1. O que os compradores disseram (Van Westendorp)

| | Painel v1 (viu R$349) | Painel v2 (viu R$249) |
|---|---:|---:|
| Barato demais (PMC) | R$121 | R$121 |
| Menor resistência (OPP) | R$150 | R$121 |
| Indiferença (IPP) | R$250 | R$200 |
| Caro demais (PME) | R$399 | R$321 |
| Mediana "começa a ficar caro" | R$330 | R$300 |

- **Ver R$249 ancorou os compradores para baixo.** O teto caiu de R$399 para R$321.
- **A renda alta é outro público:** deu "começa a ficar caro" entre R$380 e R$450 e "caro demais" entre R$550 e R$900.

### 2. Contra os concorrentes

Fonte: `competitors.md`.

- **End grain no Mercado Livre:** R$329–440 (teca R$329, peroba R$354,25).
- **Loja artesanal:** R$456–600 (teca 50x30 a R$480; imbuia, marfim ou muiracatiara a R$600).
- **Tábua comum de madeira:** R$78,90–100. É a referência de quem caça preço, e esse grupo não é o público.

R$249 fica **abaixo** de toda end grain encontrada, e R$349 fica no meio do Mercado Livre.

### 3. O preço e a margem

Valores da ferramenta do CFO (`cfo.md`):

| preço | lucro por tábua | margem | ano 1 |
|---|---:|---:|---:|
| R$249 (lançamento) | R$83,36 | 33% | +R$35.619 |
| R$349 (preço cheio) | R$171,36 | 49% | +R$78.123 |

**Recomendação:** lançar a **R$249** para os 30 primeiros pedidos ou até 31/12/2026, para comprar as primeiras avaliações. Depois, ir para **R$349**. O lucro dobra e o público que mais comprou (renda alta, 7 de 7 no painel v2) aceita esse preço.

### 4. A escada

| degrau | produto | preço | por quê |
|---|---|---:|---|
| Entrada | Tábua de presente 30x20x3 | R$149–179 | Para quem compra presente com orçamento apertado, que no painel parou em R$150–200. **Não testada.** |
| Principal | End grain 40x30x4 xadrez, numerada | R$249 → R$349 | A peça testada no painel |
| Topo | End grain 50x35x5 para churrasco, com canaleta | a definir | Para o churrasqueiro de renda alta. **Não testada.** |

### 5. Oferta de abertura

- **R$249 para os 30 primeiros pedidos ou até 31/12/2026**, o que acontecer primeiro. Depois, R$349.
- No anúncio, use "preço de lançamento" com a data de fim. **Não use "de R$349 por R$249" antes de ter vendido a R$349.**

### 6. O que testar com compradores reais

1. A mesma oferta nova a **R$249 e a R$349**, em dois anúncios ou em períodos alternados. Compare conversão e lucro total.
2. A tábua de presente 30x20 a **R$159**, a partir de dezembro, para quem compra presente.

### 7. Objeções de preço do painel

Simulações, não depoimentos:

1. "R$249 numa tabua e duas vezes e meia o que eu pago numa boa no Mercado Livre. [...] pra mim tabua e tabua, nao vejo motivo pra pagar tanto mais." (P009)
2. "R$249 numa tabua ainda pesa no meu orcamento de presente. [...] ou pego uma tabua boa de R$80 a R$120 e completo com outra coisa." (P011)
3. "R$249 é mais que o dobro do que eu pago numa tábua boa de R$80 a R$100. Pra cortar carne e legume em casa, a minha atual dá conta." (P017)

Esse público não é o alvo. A resposta para ele é a tábua de presente menor, não baixar o preço da principal.

## A oferta

**Pitch antigo:** `pitch-tabua-v1.md` (R$349). **Pitch novo:** `pitch-tabua.md`. Mesmos 20 compradores simulados (seed 825715). Painéis em `panel-tabua/` e `panel-tabua-v2/`.

### O que mudou na oferta

| Objeção do v1 | O que entrou no v2 |
|---|---|
| "Não diz quais madeiras" (6 pediram) | **Marfim (clara) e Muiracatiara (escura)**, compradas com nota fiscal de madeireira. As espécies foram escolhidas por mim, a partir de anúncios reais de end grain: **o marceneiro precisa confirmar ou trocar** |
| "Pode ser madeira tingida" / "fotos genéricas" | **Foto do topo da SUA tábua** enviada pelo chat antes de despachar |
| "Xadrez já vejo em todo lugar" | **Numerada e assinada** pelo marceneiro, gravado na lateral |
| "A cola solta?" | Cola à prova d'água citada no anúncio |
| "Presente, chega a tempo?" | **Embalagem de presente grátis**. Pedidos até 10/12 postados até 14/12; se não chegar até 23/12, devolvemos R$50 |
| "R$349 é muito" | **Lançamento a R$249** para os 30 primeiros pedidos ou até 31/12/2026; depois, R$349 |

### Resultado

| | v1 (R$349) | v2 (oferta nova, R$249) |
|---|---:|---:|
| **Compram** | **2 de 20 (10%)** | **10 de 20 (50%)** |
| Recusa por confiança | 10 | 2 |
| Recusa por preço | 7 | 8 |
| Recusa por design | 1 | 0 |

**Por segmento (v2), todos com amostra pequena:**

- Renda alta: 100% (7 de 7)
- Classe média: 33%
- Renda apertada que compra para presente: 0%

**Por comportamento (v2):**

- Quer peça de design: 100%
- Cozinheiro entusiasta: 75%
- Churrasqueiro: 60%
- Procurando presente: 50%
- Lê todas as avaliações: 0%
- Caçador de preço: 0%

**Objeções que caíram:** "é madeira tingida?" (resolvida pela foto da própria tábua), "peça genérica" (resolvida pela numeração e assinatura) e "chega antes do Natal?". **A confiança caiu de 10 para 2 recusas.**

**Objeções que ficaram:**

- **Preço para quem compra presente com orçamento apertado.** Esse grupo para em R$150–200 e compara com tábuas de R$80.
- **Higiene da madeira** (P008, P015, P020). A oferta não responde.
- **A expressão "contato indireto" na cola confundiu** dois compradores (P007, P008), que cortam alimento direto na tábua.
- Os grupos "lê todas as avaliações" e "caçador de preço" seguem em 0%. Só avaliações reais mudam isso.

**Faixa de preço (Van Westendorp):**

- v1: R$121–399
- v2: R$121–321, com "barato" mediano em R$180 e "começa a ficar caro" em R$300

Mostrar R$249 **ancorou os compradores para baixo**. Os de renda alta deram "começa a ficar caro" entre R$380 e R$450.

### ⚠️ Ressalvas

- **O preço caiu junto com a oferta** (R$349 → R$249). Não dá para separar o efeito das melhorias do efeito do desconto. No teste real, rode a oferta nova a R$249 contra a oferta nova a R$349.
- São compradores simulados (que tendem a ser agradáveis) e a amostra é de 20. Trate os 50% como **teto**.
- Não use as frases dos compradores simulados como depoimento.

### Próximos ajustes sugeridos

1. **Escada de tamanhos para quem compra presente:** uma tábua de presente menor (ex.: 30x20x3) a **R$149–179**, para o grupo que parou em R$150–200, e a 40x30 como peça principal.
2. **Responder à higiene com fato verificável:** cuidados de limpeza e secagem, sem promessa de saúde que não dê para comprovar.
3. **Cola:** troque "contato indireto" pelo nome e pela especificação reais da cola usada, depois de conferir a ficha técnica do fabricante.
4. **CFO da tábua:** custo da madeira (marfim e muiracatiara por m³ ou por tábua), tempo por peça, caixa e frete reais.

## Os números

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

## Unit economics: Veio Certo - tabua de corte end grain 40x30x4 (marfim + muiracatiara), producao em casa, venda no Mercado Livre (valores em R$)

Every number below comes from the input file. Nothing is looked up or guessed.

### One tabua end grain 40x30x4

| line | per tabua end grain 40x30x4 |
| --- | ---: |
| Price | R$249.00 |
| Madeira nobre: ~0,01 m3 com perda (2x o volume final) a ~R$6.000/m3 [estimativa, cotar] | -R$60.00 |
| Cola Titebond III ~50 g (R$110,94 por 1,05 kg) [publico] | -R$5.30 |
| Lixas (topo consome muita lixa) [estimativa] | -R$8.00 |
| Oleo mineral + cera alimentar no acabamento [estimativa] | -R$4.00 |
| Frasco de oleo 100 ml para o cliente (R$8,56 farmacia) [publico] | -R$8.56 |
| 4 pes antiderrapantes [estimativa] | -R$4.00 |
| Embalagem de presente (caixa kraft + cartao) [estimativa] | -R$10.00 |
| Caixa de envio e protecao [estimativa] | -R$6.00 |
| Comissao ML Classico Casa ~12% [publico, blogs] | -R$29.88 |
| Frete gratis pago pelo vendedor, ~4,5 kg [estimativa] | -R$25.00 |
| Reserva garantia (3% x R$80) + atraso de Natal (5% x R$50 no ano) [estimativa] | -R$4.90 |
| **Contribution** (what each tabua end grain 40x30x4 leaves to pay the fixed costs) | **R$83.36** (33%) |

### The margin that matters

Fixed costs: R$387 a month (DAS MEI 2026 [publico] R$87, Energia extra das maquinas [estimativa] R$100, Internet e celular [estimativa] R$200).

- **Break-even: 1 tabua end grain 40x30x4s a day.** Below that you lose money every month.
- **Profit margin at your plan** (2 a day): **31%** of every sale, after every cost.
- Capacity: 3 a day.

### Year 1, month by month

| month | tabua end grain 40x30x4s a day | revenue | profit | cumulative (after R$2,000 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | R$2,241 | R$363 | -R$1,637 |
| 2 | 0 | R$3,735 | R$863 | -R$773 |
| 3 | 1 | R$5,976 | R$1,614 | R$840 |
| 4 | 1 | R$7,470 | R$2,114 | R$2,954 |
| 5 | 1 | R$8,964 | R$2,614 | R$5,568 |
| 6 | 2 | R$11,205 | R$3,364 | R$8,932 |
| 7 | 2 | R$11,205 | R$3,364 | R$12,296 |
| 8 | 2 | R$11,205 | R$3,364 | R$15,661 |
| 9 | 2 | R$13,446 | R$4,114 | R$19,775 |
| 10 | 2 | R$14,940 | R$4,615 | R$24,390 |
| 11 | 2 | R$14,940 | R$4,615 | R$29,004 |
| 12 | 2 | R$14,940 | R$4,615 | R$33,619 |

- **Year 1 operating profit: R$35,619** on R$120,267 of revenue.
- After the R$2,000 startup spend: R$33,619.
- Startup money earned back: month 3.
- Cash you need before it pays for itself: **R$2,000**.

### What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 31% | 1 | R$35,619 |
| Price -10% | 23% | 1 | R$23,592 |
| Volume -20% | 30% | 1 | R$27,566 |
| Unit costs +15% | 21% | 1 | R$23,618 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.

## Marketing

Base: o painel da tábua `panel/` (oferta nova, 10 de 20 compram), `panel-tabua/` (v1), `competitors.md`, `pricing.md` e `cfo.md`. O plano anterior das prateleiras está em `arquivo-prateleiras/marketing.md`.

### 1. Evidência

**Quem comprou no v2** (amostras pequenas):

- Renda alta: 7 de 7
- Quer peça de design: 2 de 2
- Cozinheiro entusiasta: 3 de 4
- Churrasqueiro: 3 de 5
- Procurando presente: 2 de 4

**Quem não comprou:**

- Lê todas as avaliações: 0 de 2
- Caçador de preço: 0 de 3
- Renda apertada que compra presente: 0 de 4

**Objeções que restam:** preço contra tábuas de R$80, higiene da madeira, a expressão "contato indireto" da cola e "loja nova".

### 2. Posicionamento (recomendado)

> *Para quem leva churrasco e cozinha a sério e quer uma peça que ninguém tem, a Veio Certo é a tábua end grain numerada e assinada por um marceneiro de 20 anos, que você vê antes de sair da oficina. Diferente das tábuas de série, de fábrica ou importadas.*

O porquê: a numeração, a assinatura e a foto da tábua do próprio cliente foram o que tirou "desconfiança" de 10 para 2 recusas no painel.

### 3. Canais

| Canal | Por quê | Custo | Sinal de que funcionou |
|---|---|---|---|
| **Mercado Livre** (orgânico) | Onde se busca "tábua end grain" e "tábua de churrasco" | Comissão de ~12% | ≥ 30 visitas/dia, conversão ≥ 1% |
| **Seu Instagram e TikTok** | A colagem em xadrez e o topo sendo lixado são conteúdo muito visual. Mostra o marceneiro real | R$0 + tempo | Mensagens e cliques no link |
| **WhatsApp (rede e clientes antigos)** | Primeiras vendas e avaliações | R$0 | Pedidos "por indicação" |
| Mercado Livre Ads | Acelera visitas no Natal | Por clique | Custo por venda < limite abaixo. **Só depois das 3 primeiras avaliações** |
| Outros marketplaces e influenciador pago | — | — | **Não agora** (um canal por 90 dias) |

### 4. Dez ganchos

| # | Formato | Gancho | Responde a |
|---|---|---|---|
| 1 | Vídeo 3 s | "Essa tábua começou como 40 ripas. Olha a segunda colagem." | "É madeira de verdade?" |
| 2 | Vídeo 3 s | "Por que a faca dura mais na tábua de topo? Olha a fibra de perto." | Por que end grain |
| 3 | Vídeo 3 s | "Antes de despachar, você recebe a foto da SUA tábua." | Desconfiança da loja nova |
| 4 | Título do anúncio | "Tábua de Corte End Grain Marfim e Muiracatiara 40x30 Numerada — Feita por Marceneiro" | Busca e madeiras |
| 5 | Vídeo 3 s | "Tábua nº 001. Cada uma sai numerada e com a minha assinatura." | "Xadrez genérico" |
| 6 | Post | "Presente de Natal: pedidos até 10/12 são postados até 14/12. Se não chegar até 23/12, devolvo R$50." | Prazo de presente |
| 7 | Stories | "Como cuidar: lavar à mão, secar em pé, óleo uma vez por mês. Pronto." | Trabalho de manutenção |
| 8 | Vídeo 3 s | "Tábua de R$80 e tábua de R$249: a diferença está aqui." (mostrar a colagem e o topo) | Preço |
| 9 | Post | "Qual cola eu uso e por quê." (nome e ficha técnica reais) | Cola e alimento |
| 10 | WhatsApp | "Abri minha loja: tábua end grain feita por mim, numerada. Os 30 primeiros pedidos saem a R$249 até 31/12." | Primeiras vendas |

**Oferta de lançamento:** R$249 para os 30 primeiros pedidos ou até 31/12/2026; depois, R$349. Sempre com a data de fim e sem "de/por" falso.

### 5. Verba e números

**Máximo que vale pagar por cliente:** lucro por tábua × compras do cliente no 1º mês = **R$83,36 × 1,0 ≈ R$83** a R$249 (ou R$171 a R$349). A média de 1,0 compra vem do painel.

- **Anúncio pago no lançamento: R$0.** Os R$2.000 vão para o lote. Depois de 3 avaliações, teste **R$100–150 de Mercado Livre Ads** no Natal, com teto de custo por venda **< R$60**.
- **Três números por semana:** visitas por dia (< 30), conversão (< 1%) e avaliações com foto (< 3 até 31/12).

### 6. Calendário (16/11 a 16/12/2026)

| Data | Canal | O quê |
|---|---|---|
| 16/11 | IG/TT | "20 anos de marcenaria. Agora, tábuas end grain feitas por mim." |
| 17/11 | IG/TT | Gancho 1, parte 1: as ripas e a 1ª colagem |
| 18/11 | IG/TT | Gancho 1, parte 2: a 2ª colagem em xadrez |
| 19/11 | IG/TT | Gancho 2: por que o topo preserva o fio da faca |
| 20/11 | WA | Convite para o lançamento fechado |
| 21/11 | ML/WA | **Lançamento fechado** (5 tábuas) |
| 22/11 | IG/TT | Gancho 5: gravação da tábua nº 001 |
| 23/11 | IG | Gancho 7: como cuidar |
| 24/11 | IG/TT | Planificando o topo, antes e depois da lixa |
| 25/11 | IG | Gancho 9: a cola que eu uso |
| 26/11 | IG/TT | Gancho 3: a foto antes de despachar |
| 27/11 | IG/TT | Black Friday: **sem desconto**. "Uma tábua para 20 anos." |
| 28/11 | IG | Embalagem de presente |
| 29/11 | IG/TT | "Amanhã abre. Os 30 primeiros a R$249." |
| **30/11** | **todos** | **Lançamento público** (gancho 10 no WA) |
| 01/12 | IG/TT | Gancho 8: R$80 contra R$249 |
| 02/12 | IG/TT | Gancho 6: prazo de Natal |
| 03/12 | IG/TT | Tábua em uso no churrasco (a sua) |
| 04/12 | IG | Números verdadeiros da semana |
| 05/12 | IG/TT | Escolhendo a madeira na madeireira |
| 07/12 | — | **Revisão do dia 7** |
| 08/12 | IG/TT | "Faltam 2 dias para o prazo de Natal" (só se for verdade) |
| 09/12 | IG/TT | Tábuas numeradas lado a lado (só as reais) |
| 10/12 | IG/WA | **Último dia** para a garantia de Natal |
| 11–13/12 | IG | Bastidores e respostas a perguntas do ML |
| 14/12 | — | **Revisão: linha de sucesso** |
| 15–16/12 | IG/TT | Foto de cliente (**só com autorização por escrito**) |

### Regras

- Nada de avaliação, depoimento ou número de seguidores falso.
- As frases do painel são **pesquisa simulada**: nunca use em anúncio.
- Afirmações de higiene ou de segurança alimentar, só com base verificável (ficha técnica, norma).
- O CDC e o CONAR valem para anúncio. Isto não é aconselhamento jurídico.

## Marca

**Posicionamento usado aqui:** ainda não existe `founder/marketing.md`. Por isso o posicionamento abaixo foi tirado do conselho, da oferta e dos painéis. Confirme ou ajuste no `/founder-marketing`.

> **Tábua end grain numerada e assinada por um marceneiro com 20 anos de oficina, que você vê antes de sair da oficina.** (Atualizado em 03/11/2026: o produto mudou de prateleiras para tábuas. O nome, a voz e o visual abaixo continuam valendo. Adapte os pontos de contato: a caixa vira embalagem de presente, e o primeiro post vira o vídeo da colagem em xadrez.)

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

1. **Veio Certo. Madeira de verdade, na medida da sua parede.** (para a tábua: *Veio Certo. Cada tábua tem número, nome e veio próprio.*)
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

## Operação

Um marceneiro, em casa, como MEI, vendendo no Mercado Livre. A operação das prateleiras está em `arquivo-prateleiras/ops.md`. As regras de MEI, alvará e CDC continuam valendo e estão lá.

### 1. O ciclo de produção (em lote de 5 a 10 tábuas)

👁 = etapa que o cliente vê.

| Dia | Etapa |
|---|---|
| 1 | Conferir a madeira (umidade de 8–12% no higrômetro, sem racha nem medula). Cortar as ripas e fazer a **1ª colagem** (face). Grampos até o dia seguinte |
| 2 | Aplainar o bloco, cortar fatias no **topo** e fazer a **2ª colagem** em xadrez |
| 3 | Planificar o topo (lixadeira de cinta ou gabarito de tupia: o topo lasca na desengrossadeira), lixar 80 → 120 → 180 → 220, chanfrar e arredondar as arestas |
| 4 | Gravar número e assinatura na lateral. Aplicar óleo mineral até saturar, depois cera. Instalar os pés |
| 5 | 👁 **Foto do topo de cada tábua enviada ao cliente.** Embalagem de presente, cartão e frasco de óleo. 👁 Postagem |

Todos os dias:

- 👁 Responder perguntas em até 2 h úteis.
- 👁 Confirmar o pedido e a data de postagem.

**Capacidade:** o CFO usou 3 tábuas/dia e 3,5 h por tábua, mas isso é estimativa. Em lote, a secagem da cola define o ritmo, não as horas de bancada. **Cronometre o primeiro lote.**

### 2. Fornecedores

| Insumo | Onde | Preço | Pendente |
|---|---|---|---|
| Madeira nobre (par claro + escuro) | Madeireira local de nativas, com nota fiscal e DOF | Não encontrado | **Cotar** por m³ ou por prancha, seca em estufa |
| Cola Titebond III | Lojas de ferramentas e Magalu | R$110,94 por 1,05 kg ([Magalu](https://www.magazineluiza.com.br/busca/cola+titebond)) | — |
| Óleo mineral USP | Farmácia ou distribuidor | 100 ml a R$8,56 ([Cliquefarma](https://www.cliquefarma.com.br/preco/oleo-mineral-1l)) | Comprar 1 L para o acabamento |
| Cera (abelha ou carnaúba) | Loja de artesanato | — | Cotar |
| Pés de borracha, lixas, caixa kraft, cartões | Distribuidores e lojas de embalagem | — | Cotar |
| Ferro de marcar ou carimbo de fogo (número e assinatura) | Gravação sob encomenda | — | Cotar (custo único) |

### 3. Máquinas

Lista das que o processo pede. **Confirme quais você já tem:**

- serra circular de bancada ou esquadrejadeira, com guia para fatiar o topo;
- desempenadeira e desengrossadeira, só para as ripas, **não para o topo**;
- lixadeira de cinta ou tupia com gabarito para planificar o topo;
- lixadeira orbital;
- grampos;
- tupia para chanfro.

### 4. Rotinas (resumo)

- **Pedido:** confirmar no chat, informar a data de postagem e, perto do Natal, lembrar o prazo de 10/12.
- **Antes de enviar:** checklist com tábua sem marcas de lixa, juntas fechadas, número gravado, óleo, cartão e frasco. Foto do topo para o cliente.
- **Reclamação** (descolou ou rachou): pedir foto, responder em até 4 h e enviar outra (garantia de 12 meses). Registrar a causa (madeira, cola ou uso).
- **Semana:** conferir o estoque de madeira e embalagem e anotar o tempo por tábua e as vendas.

### 5. Regras específicas da tábua

Confirme com o órgão ou com um profissional. Isto não é aconselhamento jurídico nem regulatório.

- [ ] **Utensílio em contato com alimento:** verifique as exigências da **Anvisa** e do **Inmetro** para tábua de madeira (materiais, acabamento, rotulagem).
- [ ] **Origem da madeira nativa:** compre com nota fiscal e documento de origem florestal (DOF) da madeireira.
- [ ] **Cola:** a ficha técnica da Titebond III fala em contato **indireto** com alimentos. Explique isso com clareza no anúncio, sem prometer mais do que a ficha diz.
- [ ] **Teto do MEI (R$81 mil/ano):** o plano passa do limite por volta do 8º mês. Combine a migração para ME com o contador.

### 6. Riscos

| Risco | Chance | Impacto | Plano |
|---|---|---|---|
| Madeira nobre mais cara que R$60/tábua | Média | Alto | Cotar antes, aproveitar sobras, ter um par alternativo de madeiras |
| Tábua racha ou descola depois de vendida | Média | Alto | Madeira seca e conferida, colagem em 2 etapas, teste de lavagem nas primeiras peças |
| Tempo por tábua acima de 5 h | Média | Alto | Produzir em lote; se não resolver, subir o preço para R$349 mais cedo |
| Atraso no Natal | Média | Médio | Corte de pedidos em 10/12, estoque de 5 tábuas prontas no início de dezembro |
| Poucas avaliações | Alta | Alto | Lançamento para 30 pedidos, cartão pedindo foto, rede própria |
| Ficar parecido com concorrente que usa as mesmas madeiras | Média | Médio | Escolher um par próprio de madeiras ou um desenho exclusivo |
| Exigência sanitária não atendida | Baixa a média | Alto | Confirmar com Anvisa e Inmetro antes de anunciar |

## Lançamento

Hoje é 03/11/2026. **Lançamento fechado: sáb 21/11. Público: seg 30/11.** O prazo de Natal fecha em 10/12, com postagem até 14/12. Responsável: você.

### 1. O teste antes de gastar

Anúncio real no Mercado Livre com **um lote de 10 tábuas** (as 5 primeiras vão para o lançamento fechado) e pré-venda para a sua rede no Instagram e no WhatsApp.

**Linha de sucesso (30/11 a 13/12):**

- [ ] **10 tábuas vendidas** a R$249
- [ ] Conversão no anúncio ≥ 1%
- [ ] **3 avaliações com foto** até 31/12
- [ ] Lucro real por tábua ≥ R$60, com custo e frete reais
- [ ] Tempo real ≤ 5 h por tábua
- [ ] Nenhuma tábua descolada ou rachada

**Como comparar com o painel:** o painel simulado deu 50% de intenção, mas mede quem viu a oferta inteira. A conversão de marketplace é muito menor. **Menos de 5 vendas em 14 dias** → volte ao `/founder-offer` com os dados reais.

**Os R$2.000** (estimativa, a confirmar com as cotações):

| Item | Valor |
|---|---:|
| Madeira para ~15 tábuas (R$60 cada) | ~R$900 |
| Cola | ~R$111 |
| Lixas | ~R$120 |
| Óleo, cera e 15 frascos | ~R$180 |
| Pés | ~R$60 |
| Embalagens de presente e de envio | ~R$240 |
| Ferro de marcar | ~R$150 |
| Higrômetro | ~R$150 |
| **Reserva** | **~R$89** |
| **Total** | **R$2.000** |

### 2. Contagem regressiva (🔴 = caminho crítico)

**Semana 1 (03 a 08/11): números**

- [ ] 🔴 Escolher o par de madeiras e cotar na madeireira (05/11)
- [ ] 🔴 Simular o frete da caixa no Mercado Livre (06/11)
- [ ] 🔴 Confirmar as regras da Anvisa e do Inmetro para tábua (07/11)
- [ ] Refazer o `/founder-cfo` com os números reais (08/11)

**Semana 2 (09 a 15/11): legal e primeiro lote**

- [ ] 🔴 Abrir o MEI (10/11)
- [ ] 🔴 Comprar madeira e insumos (10/11)
- [ ] 🔴 Produzir o lote 1 de 10 tábuas, **cronometrando**, de 10 a 15/11
- [ ] 🔴 Teste de durabilidade: 2 tábuas lavadas e secas todos os dias por 7 dias, olhando as juntas
- [ ] Encomendar o ferro de marcar (11/11)

**Semana 3 (16 a 22/11): anúncio**

- [ ] 🔴 Fotos: topo, lateral com a assinatura, em uso no churrasco, embalagem de presente (17/11)
- [ ] 🔴 Anúncio com as madeiras nomeadas, a cola especificada, os cuidados, a garantia, o prazo de Natal e "loja nova" (19/11)
- [ ] **Sáb 21/11: lançamento fechado** para 5 conhecidos que vão usar a tábua de verdade. Peça avaliação honesta, com foto se quiserem, e **sem trocar por desconto**

**Semana 4 (23 a 29/11)**

- [ ] Produzir o lote 2 para o estoque de Natal (5 tábuas prontas)
- [ ] Black Friday (27/11): sem desconto extra. Mostrar o processo
- [ ] **Seg 30/11: lançamento público**

### 3. Dia do lançamento (30/11)

| Hora | O quê |
|---|---|
| 07h30 | Anúncio ativo a R$249 com "preço de lançamento até 31/12 ou 30 pedidos" |
| 08h00 | Post e Stories com o vídeo da 2ª colagem e da gravação da assinatura, e o link. WhatsApp para a lista |
| 08–12h | Responder toda pergunta em até 30 min |
| 13–16h | Produção (lote em andamento) |
| 16h | Foto do topo para cada comprador. Embalar e postar |
| 18h | Stories com números verdadeiros |
| 21h | Anotar visitas, vendas, perguntas e tempo |

**Se algo der errado:**

- **Pedidos acima da capacidade:** aumente o prazo de postagem antes de aceitar mais pedidos.
- **Tábua com defeito no controle final:** não envie. Avise o cliente e produza outra.

### 4. Primeiros 30 dias (30/11 a 29/12)

| Número | Limite que força mudança |
|---|---|
| Visitas/dia | < 30 → título, foto principal, palavras-chave ("tábua end grain", "tábua de churrasco") |
| Conversão | < 1% → fotos e respostas às dúvidas repetidas no anúncio |
| Lucro real por tábua | < R$60 → subir para R$349 antes de 31/12 |
| Tempo por tábua | > 5 h → mudar o processo ou o preço |
| Avaliações com foto | < 3 até 31/12 → reforçar o cartão e a mensagem pós-entrega |
| Faturamento do mês | > R$5 mil → falar com o contador sobre o teto do MEI |

**Revisões:**

- **07/12:** visitas e conversão.
- **10/12 (corte de Natal):** quantos pedidos de presente chegaram?
- **14/12:** linha de sucesso.
- **29/12:** quanto sobrou de verdade, horas reais e a decisão de janeiro (R$349, tábua de presente 30x20 para o Dia dos Pais, ou segundo canal).

_The panel is simulated buyers and the numbers are projections from your inputs. Confirm demand with real customers and costs with real quotes before you spend. Not financial, legal or tax advice._
