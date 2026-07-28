# Site — Móveis Planejados (landing de conversão)

Página única, autocontida (`index.html`). Sem build, sem dependências.
Abrir no navegador ou publicar em qualquer hospedagem estática.

## O que trocar antes de publicar (5 minutos)

| Onde | O quê |
|---|---|
| `<script>` → `CFG.whatsapp` | Número com DDI, só dígitos (`5511940028922`) |
| `<script>` → `CFG.acabamento` | R$ por metro linear (mín/máx) de cada acabamento |
| `<script>` → `CFG.ambiente` | Multiplicador de complexidade e dias por ambiente |
| `<script>` → `CFG.extras` | Multiplicador e dias de cada item adicional |
| HTML | Nome da marca, telefone, e-mail, endereço, CNPJ, cidades atendidas |
| HTML | Números de prova social (1.420 projetos / 97% no prazo / garantia) |
| HTML | Depoimentos — usar apenas com autorização por escrito |

**Importante:** os preços, prazos, percentuais e depoimentos que estão no arquivo
são valores de exemplo plausíveis. Só publique depois de substituir pelos números
reais da operação — sobretudo a multa por atraso e a garantia, que aparecem
descritas como cláusula de contrato.

## Estrutura das seções

1. Hero com desenho técnico animado + prova numérica
2. Diagnóstico (3 erros que quebram um projeto)
3. Comparador arrastável: projeto executivo → peça instalada
4. Simulador de investimento (faixa + prazo + parcela + link WhatsApp preenchido)
5. Ambientes executados (6 casos com restrição real)
6. Processo em 6 etapas com prazo por etapa
7. Depoimentos com projeto identificado
8. Garantia / inversão de risco
9. FAQ (6 objeções de venda)
10. CTA final com escassez operacional real + rodapé

## Acessibilidade e compatibilidade

- Tema claro/escuro: segue o sistema e tem botão de alternância
- `prefers-reduced-motion` respeitado (contadores e traçados)
- Comparador operável por teclado (setas) e por arraste
- Sem fontes ou scripts de terceiros além do Google Fonts
