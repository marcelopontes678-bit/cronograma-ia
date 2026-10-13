# Operação: Gestori Orçamento

Como o negócio roda no dia a dia, com um fundador só, 20 marcenarias fundadoras no começo e meta de 50 clientes (`numbers.json`). Isto não é assessoria jurídica, contábil ou tributária; cada item legal tem a fonte para você confirmar.

## 1. O ciclo de cada dia
(👁 = o cliente vê)

1. **Manhã, 15 min:** conferir se o sistema está no ar e se alguma leitura de projeto falhou durante a noite (logs do Supabase e do Render).
2. 👁 **Novos testes:** dar boas-vindas pelo WhatsApp a quem se cadastrou e pedir os 2 ou 3 projetos já fechados.
3. 👁 **Leituras da IA:** quando um projeto chega, a IA monta o orçamento. Revisar os primeiros de cada cliente **antes** que ele compare (são eles que decidem a compra).
4. 👁 **Implantações:** chamada de vídeo de 45 a 60 minutos para cadastrar a tabela de preço (só os 20 fundadores).
5. 👁 **Suporte:** responder o WhatsApp em até 4 horas úteis.
6. **Conteúdo:** gravar ou publicar o post do dia (`marketing.md`).
7. **Fim do dia, 10 min:** anotar erros da IA (qual projeto, qual peça, qual diferença) numa planilha. Essa lista guia as correções da semana.

## 2. Fornecedores

| Insumo | Opções | Preço público | Observações |
|---|---|---|---|
| **IA de leitura** | Anthropic API (atual: `claude-opus-5`) | US$ 5 / US$ 25 por milhão de tokens ([agregador](https://anotherwrapper.com/llm-pricing/claude-opus-5)) | Pré-pago no cartão. **Ação:** registrar o consumo de cada chamada para medir o custo real (ver `cfo.md`) e testar um modelo mais barato nas páginas simples |
| **Banco e backend** | Supabase Pro | US$ 25/mês + uso ([makerkit](https://makerkit.dev/blog/md/saas/supabase-pricing)) | Ativar backup diário |
| **Servidor** | Render Starter | US$ 7/mês ([costbench](https://costbench.com/software/developer-tools/render/)) | Plano grátis "dorme" e deixa o primeiro acesso lento: usar o pago no lançamento |
| **Cobrança recorrente** | Asaas, Mercado Pago ou um intermediador com **Pix Automático** | Asaas: taxa fixa por cartão, valor não encontrado ([blog Asaas](https://blog.asaas.com/taxas-asaas/)) | **Pedir a tabela atual a dois deles.** O Pix Automático pode sair mais barato que o cartão para assinatura ([Baguete](https://www.baguete.com.br/noticias/cakto-pay-lidera-adocao-do-pix-automatico-e-marca-o-fim-da-dependencia-de-cartoes-no-mercado-saas-brasileiro)). A Stripe tem relatos conflitantes sobre o Brasil: confirmar antes |
| **Contador** | Contabilidade online ou local | Não pesquisado; estimado em R$ 300/mês | Pedir orçamento a dois, explicando CNAE de software e Fator R (seção 6) |
| **WhatsApp Business** | App gratuito | Grátis | Um número só para o Gestori |

**Custos atualizados:** o imposto no `numbers.json` passou de 6% para **15,5%** (Simples Nacional, Anexo V, ver seção 6). O CFO foi rodado de novo: a sobra por cliente caiu para **R$ 81,36**, o equilíbrio subiu para **7 clientes** e o lucro do ano 1 ficou em **R$ 11.227** (`cfo.md`).

## 3. Pessoas
Só você, por enquanto. Sem salário na conta (`cfo.md`).

| Bloco semanal | Mês 1 (lançamento, 20 fundadores) | Com 50 clientes |
|---|---|---|
| Implantações (1 h cada) | 5 h (5 por semana) | 1 h |
| Suporte e revisão da IA | 5 h | 6 h |
| Corrigir erros da IA e melhorar o produto | 6 h | 6 h |
| Conteúdo e grupos | 5 h | 4 h |
| Administrativo (cobrança, contador) | 1 h | 2 h |
| **Total** | **~22 h por semana** | **~19 h por semana** |

Isso é **em cima** do trabalho na Marcenaria Pontes, do canal e dos estudos de programação. **Ponto de atenção:** com mais de 50 clientes, o suporte precisa de ajuda (um atendente meio período ou automação). Os custos de contratar (INSS, FGTS, encargos) mudam por regime: perguntar ao contador.

## 4. Rotinas (uma página cada)

**R1. Novo teste grátis**
1. Cadastro recebido → mensagem de boas-vindas no WhatsApp em até 4 h.
2. Pedir 2 ou 3 projetos **já fechados**, com o valor que ele cobrou.
3. Rodar a leitura, revisar e marcar onde a IA errou.
4. Mandar a comparação peça por peça: "IA × o que você cobrou".
5. Dia 25 do teste: perguntar se quer continuar e explicar a cobrança.
6. Registrar: a IA acertou dentro de 5%? Virou cliente? (`marketing.md`, seção 6)

**R2. Implantação de fundador**
1. Agendar chamada de 1 h. Pedir a tabela de preço (planilha, foto, o que tiver).
2. Cadastrar junto com ele: chapas, fita, ferragens, markups e margem mínima por ambiente.
3. Rodar um projeto real na chamada e mostrar o alerta de margem.
4. Confirmar por escrito o preço travado por 12 meses.

**R3. A IA errou num orçamento**
1. Agradecer e pedir o projeto e o valor certo.
2. Corrigir o orçamento do cliente na hora.
3. Anotar na lista de erros (projeto, peça, diferença).
4. Toda sexta: corrigir o erro mais frequente da semana.
5. Avisar o cliente quando corrigir. É a resposta-modelo do `brand.md`.

**R4. Cancelamento e reembolso**
1. Cancelar sem perguntas e sem multa.
2. Primeiro mês pago: reembolso total, conforme a garantia.
3. Enviar a exportação dos dados em planilha (**depois que a exportação existir**).
4. Perguntar em uma frase: "O que faltou?". Anotar.

**R5. Revisão semanal (sexta, 30 min)**
1. Os três números do `marketing.md`: testes iniciados, acerto da IA, conversão.
2. Custo de IA da semana (quando houver o registro de uso).
3. Maior erro da IA da semana → tarefa da próxima semana.
4. Vagas de fundador restantes (número real, usado nos posts).

## 5. Ferramentas (o mínimo)
| Para quê | Ferramenta | Custo |
|---|---|---|
| O produto | Gestori (Supabase + Render + Cloudflare) | Em `numbers.json` |
| Cobrança | Asaas ou Mercado Pago (assinatura + Pix Automático) | Taxa por cobrança, a confirmar |
| Atendimento | WhatsApp Business | Grátis |
| Agenda das implantações | Google Agenda com link de agendamento | Grátis |
| Controle de testes e erros da IA | Uma planilha | Grátis |
| Nota fiscal de serviço | Emissor da prefeitura (NFS-e) ou o do contador | Depende da cidade |

## 6. Empresa, impostos, dados e seguros (confirmar cada item)

- [ ] **Abrir empresa como ME, não MEI.** As atividades de software (CNAE 6203-1/00, para o mesmo sistema vendido a todos) **não são permitidas ao MEI** ([Agilize](https://agilize.com.br/artigos/?p=4217), [contabilidade.com](https://contabilidade.com/blog/programador-pode-ser-mei-descubra-como-abrir-empresa/)).
- [ ] **Simples Nacional e Fator R.** O CNAE 6203-1/00 começa no **Anexo V (15,5%)**. Se a folha, **incluindo o seu pró-labore**, chegar a cerca de **28% da receita**, cai para o **Anexo III (6%)**. As fontes são blogs de contabilidade com a tabela de 2025: **confirmar com o contador** quanto de pró-labore compensa, considerando o INSS sobre ele.
- [ ] **Inscrição municipal e nota fiscal de serviço (NFS-e)** na prefeitura da sua cidade.
- [ ] **LGPD.** Você guarda dados dos clientes das marcenarias (nomes, projetos, preços). Pequenas empresas têm regras simplificadas pela **Resolução CD/ANPD nº 2/2022**: registro simplificado, prazos em dobro, política de segurança simplificada ([Fenacon](https://fenacon.org.br/noticias/aprovado-regulamento-de-aplicacao-da-lgpd-para-agentes-de-tratamento-de-pequeno-porte/), [Lefosse](https://lefosse.com/noticias/anpd-publica-regulamento-que-flexibiliza-a-aplicacao-da-lgpd-a-microempresas-empresas-de-pequeno-porte-startups-e-associacoes-sem-fins-lucrativos)). Ainda assim, você precisa de **termos de uso, política de privacidade e cláusula de tratamento de dados** no contrato (você é o "operador" dos dados que a marcenaria coloca no sistema). Peça a um advogado.
- [ ] **Contrato de assinatura** com preço, garantia de reembolso, cancelamento sem multa, limite de uso da IA (`cfo.md`) e quem é dono dos dados.
- [ ] **Marca no INPI**, depois de resolver a questão do nome "Gestori" (`brand.md`).
- [ ] **Seguro:** não é obrigatório. Seguro de responsabilidade civil profissional ou cibernético pode valer depois de ter clientes. Cotar quando passar de 20 clientes.

As regras mudam e dependem da sua cidade. Confirme cada item com a autoridade, o contador ou o advogado.

## 7. Registro de riscos

| # | Risco | Chance | Estrago | Plano |
|---|---|---|---|---|
| 1 | **IA erra peças em projetos de outras marcenarias** | Alta | Alto (o cliente perde dinheiro e confiança) | Revisar os primeiros orçamentos de cada cliente; parar a divulgação se o acerto ficar abaixo de 70% (`marketing.md`) |
| 2 | **Custo de IA explode** com cliente pesado | Média | Alto (prejuízo por cliente) | Limite de 15 orçamentos ou 75 páginas por mês no plano; registrar o consumo |
| 3 | **Conflito com a marca "Gestori"** (empresa de 1999) | Média | Alto (troca de nome com clientes) | Busca no INPI e decisão **antes** do lançamento (`brand.md`) |
| 4 | **Você sem tempo** (fábrica, canal, estudos) | Alta | Médio | Limitar a 20 fundadores; agenda fixa de implantações; atrasar o lançamento em vez de atender mal |
| 5 | Sistema fora do ar ou lento | Média | Médio | Plano pago do Render; backup diário do Supabase; aviso no WhatsApp quando cair |
| 6 | Vazamento de dados (tabela de preço é segredo do cliente) | Baixa | Alto | Revisar as regras de acesso por empresa (multiempresa) antes do lançamento; contrato com cláusula de dados |
| 7 | Mudança de preço ou de modelo da Anthropic | Média | Médio | Código preparado para trocar de modelo; acompanhar o custo semanal |
| 8 | Cliente não paga (cartão recusado) | Média | Baixo | Cobrança automática com novas tentativas e Pix Automático; bloquear após 10 dias |
| 9 | Concorrente (Calcme ou Promob) lança alerta de margem | Média | Médio | Velocidade: caso real publicado e relação próxima com os fundadores |
| 10 | Mês fraco de vendas | Alta | Baixo (custos fixos de R$ 495) | Caixa de R$ 2.500 (`cfo.md`); manter o conteúdo constante |

Próximo: `/founder-launch`.
