# ViralScript AI

Gerador de roteiros virais para Instagram Reels, em português do Brasil. Você digita o assunto; o modelo de linguagem faz o resto (gancho, storytelling, CTA para a bio, textos de tela e legenda).

## Rodar

```bash
export ANTHROPIC_API_KEY=sk-ant-...
npm start        # http://localhost:3000
npm test         # testes de prompt/parsing (não chamam a API)
```

Variáveis: `ANTHROPIC_API_KEY` (obrigatória), `VIRALSCRIPT_MODEL` (padrão `claude-sonnet-5-5`), `PORT`.

## Como funciona

- `server.js` — servidor Node sem dependências; guarda a chave, monta o prompt, chama a API da Anthropic e valida o JSON retornado. Limite de 10 requisições/min por IP.
- `public/index.html` — interface. Os botões de refinamento reenviam o roteiro atual (inclusive suas edições manuais) com uma instrução específica.
- Sem chave configurada, a interface avisa e **não** gera nada — não há roteiros fixos nem simulados.

## Limitações

- O pedido original citava o modelo do "Google Flow". Não encontrei uma API de modelo de linguagem do Google Flow para conectar; a integração usa a API da Anthropic. Trocar de provedor exige alterar apenas `chamarModelo()` em `server.js`.
- O modelo não pesquisa na web: fatos sobre pessoas e marcas reais saem do conhecimento dele e podem estar errados. A ferramenta lista em "Confira antes de gravar" o que deve ser verificado.
- Nada aqui garante viralização.
