# Fontes dos números do CFO

Valores em R$. Dólar a **R$ 5,15** (cotação de 16/09/2026 em [Meelion](https://www.meelion.com/indicadores-financeiros/dolar-hoje/); confirmar no Banco Central).

| Número | Valor | De onde veio |
|---|---:|---|
| Preço | R$ 147/mês | `pricing.md` |
| Orçamentos por marcenaria | 10/mês | **Fundador**: a Marcenaria Pontes faz de 6 a 15 por mês (usei o meio) |
| Páginas por projeto | 5 | **Fundador**: "até 5 páginas" (usei o máximo) |
| Modelo de IA | `claude-opus-5`, 1 página por chamada | Código do Gestori: `supabase/functions/orcamento-ia-extrair/index.ts` (linhas 285 e 444) |
| Preço da IA | US$ 5 por milhão de tokens de entrada, US$ 25 por milhão de saída | Agregadores ([anotherwrapper](https://anotherwrapper.com/llm-pricing/claude-opus-5), [eesel](https://eesel.ai/blog/claude-opus-5-pricing)); confirmar na página oficial da Anthropic |
| Tokens por página | ~6.500 de entrada, ~4.000 de saída | **ESTIMATIVA**: prompt do sistema tem ~7.300 caracteres (~2.100 tokens) + preferências + a página do PDF; a saída é o JSON dos módulos. **Medir de verdade**: registrar `usage` de cada chamada |
| Custo de IA por página | ~US$ 0,13 (R$ 0,67) | 6.500 × US$ 5/M + 4.000 × US$ 25/M |
| Custo de IA por marcenaria | R$ 33,50/mês | 10 orçamentos × 5 páginas × R$ 0,67 |
| Simples Nacional | ~6% | **ESTIMATIVA**; o anexo e a alíquota dependem do enquadramento. Confirmar com o contador |
| Taxa de cobrança | ~5% | **ESTIMATIVA**; não encontrei a tabela atual do Asaas ([docs](https://docs.asaas.com/docs/assinaturas-recorrência)) |
| Supabase Pro | US$ 25/mês | [makerkit](https://makerkit.dev/blog/md/saas/supabase-pricing), [toolradar](https://toolradar.com/blog/supabase-pricing-2026); confirmar em supabase.com/pricing. Uso extra é cobrado à parte |
| Render Starter | US$ 7/mês | [costbench](https://costbench.com/software/developer-tools/render/); confirmar em render.com/pricing |
| Domínio e ferramentas | R$ 30/mês | **ESTIMATIVA** |
| Contador | R$ 300/mês | **ESTIMATIVA** |
| Abertura da empresa | R$ 500 | **ESTIMATIVA** |
| Testes grátis | 50 × R$ 10 | 3 projetos × 5 páginas × R$ 0,67 ≈ R$ 10 por teste |
| Anúncios de teste | R$ 1.000 | **ESTIMATIVA** |
| Rampa de clientes | de 2 a 34 em 12 meses; plano de 50 | **ESTIMATIVA**: 20 fundadores até o mês 6 (oferta), depois +3 por mês. O painel deu no máximo 30% de compra entre quem viu a oferta; o número real depende de quantas marcenarias você alcança |

**Não incluído:** salário (pró-labore) do fundador e o tempo dele em implantação e suporte.
