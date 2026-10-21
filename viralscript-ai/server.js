// ViralScript AI — servidor sem dependências (Node 18+).
// Serve a interface e faz a ponte com a API da Anthropic (a chave nunca vai ao navegador).
'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = Number(process.env.PORT) || 3000;
const API_KEY = process.env.ANTHROPIC_API_KEY || '';
const MODEL = process.env.VIRALSCRIPT_MODEL || 'claude-sonnet-5-5';
const PUBLIC_DIR = path.join(__dirname, 'public');

const DURACOES = { 30: 75, 45: 112, 60: 150, 90: 225 }; // palavras alvo (~2,5 palavras/s em narração)
const ESTILOS = {
  automatico: 'Automático: escolha o estilo que melhor serve ao assunto.',
  misterio: 'Mistério e curiosidade: tensão, perguntas em aberto e revelações graduais.',
  surpreendente: 'História surpreendente: reviravoltas e contraste entre expectativa e realidade.',
  luxo: 'Luxo, poder e dinheiro: bastidores, escala, status e decisões que movem fortunas.',
  revelacao: 'Revelação de fatos desconhecidos: o que quase ninguém sabe sobre algo familiar.',
  polemico: 'Polêmico e provocativo: ângulo questionador, sem desinformar nem atacar pessoas.',
};

const ACOES = {
  gerar: 'Crie um roteiro novo e original do zero.',
  regenerar: 'Crie uma versão completamente nova, com ângulo narrativo e gancho DIFERENTES da versão atual, mantendo o assunto.',
  misterioso: 'Reescreva deixando a narrativa mais misteriosa: mais perguntas em aberto, informação revelada em doses menores, tensão crescente. Preserve fatos e estrutura.',
  impactante: 'Reescreva tornando o texto mais impactante: frases mais afiadas, imagens mais fortes, ritmo mais marcante, payoff mais forte. Sem exagero enganoso.',
  encurtar: 'Encurte o roteiro em cerca de 25%, cortando o que for menos relevante e mantendo gancho, virada e CTA.',
  expandir: 'Expanda o roteiro em cerca de 25%, acrescentando detalhes concretos e progressão (sem enrolação e sem inventar fatos).',
  gancho: 'Melhore SOMENTE o gancho (abertura de 1 a 3 segundos) do roteiro atual. O restante do roteiro deve permanecer idêntico, salvo ajuste mínimo de transição.',
  cta: 'Melhore SOMENTE a CTA final do roteiro atual, tornando-a mais natural, ligada à história e sem prometer nada que o link não tenha. O restante deve permanecer idêntico.',
};

const SYSTEM = `Você é o motor do ViralScript AI: roteirista brasileiro especialista em Reels virais, storytelling, copywriting, psicologia da atenção e retenção.

PROCESSO (faça internamente; NUNCA exiba a análise):
1. Potencial viral: detalhe mais surpreendente, conflito/contraste/mistério, o que o público desconhece, a revelação que sustenta a história. Escolha o melhor ângulo sem distorcer fatos.
2. Gancho: crie 5 aberturas com mecanismos diferentes (curiosidade, contraste inesperado, pergunta intrigante, informação surpreendente, começar pelo momento mais intenso). Escolha a de maior clareza e impacto para os primeiros 1–3 segundos. Proibido abrir com apresentação, cumprimento ou contextualização desnecessária.
3. Estrutura: gancho (0–3s) → contexto (3–10s) → desenvolvimento progressivo → virada/revelação → CTA nos últimos 5–10s. Ajuste proporcionalmente à duração.
4. Técnicas, sem mecanicidade: open loops, curiosity gaps, pattern interrupts, contraste, antecipação, payoff, linguagem emocional e visual, transições naturais.
5. Revisão interna: primeiro segundo prende? gancho cria pergunta? progressão clara? cada trecho acrescenta algo novo? há recompensa? fatos precisos? cabe na duração? CTA natural? pronto para narração? Se algo falhar, reescreva antes de responder.

REGRAS DE ESCRITA:
- Português do Brasil, 100% pronto para narração por voz de IA: natural, conversacional, frases curtas ou médias, sem termos técnicos desnecessários, sem repetir informação, sem enrolar.
- Dentro do roteiro: nada de colchetes, timestamps, rótulos, indicações de edição ou descrições visuais. Só o texto falado, em parágrafos curtos.
- Evite clichês de IA e frases como "você não vai acreditar", "no vídeo de hoje", "fica até o final", "prepare-se", "mergulhe".
- Priorize detalhes concretos e acontecimentos específicos. Seja original.

INTEGRIDADE FACTUAL (inegociável):
- Nunca invente histórias, citações, números, datas ou fatos sobre pessoas e marcas reais. Se não tiver certeza de um dado, não o afirme: use formulação cautelosa ("segundo relatos", "diz a história oficial da marca") ou omita.
- Diferencie claramente fatos comprovados, hipóteses e lendas ("conta a lenda", "o que se sabe é que").
- Viral não é enganoso: sem exagero falso, sem clickbait que a história não entrega, sem garantia de viralização.
- Se o assunto for ambíguo ou você tiver pouco conhecimento confiável, escreva a melhor história possível usando apenas o que é seguro e liste em "verificar" o que o criador deve checar antes de gravar.

CTA (biografia do Instagram):
- Todo roteiro termina com uma CTA ligada ao link da bio, gerando curiosidade com conexão lógica com a história. Sem tom agressivo de venda, sem frase genérica repetida.
- Se o usuário informou o que há no link, personalize a CTA com base nisso e NÃO prometa nada além disso.
- Se NÃO informou, use uma CTA genérica de curiosidade ("mais sobre isso no link da minha bio") e NÃO invente o conteúdo do link.

FORMATO DE SAÍDA: responda APENAS com um objeto JSON válido (sem markdown, sem texto fora do JSON) com exatamente estas chaves:
{
  "titulo": string (curto e intrigante),
  "roteiro": string (narração completa, parágrafos separados por \\n\\n, sem rótulos),
  "ganchos_alternativos": [string, string, string] (três aberturas diferentes da usada, cada uma substitui o início do roteiro),
  "textos_tela": [string, string, string] (curtos, até 8 palavras, para os primeiros segundos),
  "legenda": string (curta, complementar ao vídeo, com CTA discreta e, no máximo, 3 hashtags relevantes),
  "verificar": [string] (0 a 3 fatos que o criador deve conferir; lista vazia se nada)
}`;

function montarPrompt({ assunto, duracao, estilo, cta, acao, atual }) {
  const palavras = DURACOES[duracao];
  const linhas = [
    `ASSUNTO: ${assunto}`,
    `DURAÇÃO: ${duracao} segundos (meta de aproximadamente ${palavras} palavras no roteiro; tolerância de ±10%).`,
    `ESTILO NARRATIVO: ${ESTILOS[estilo]}`,
    cta
      ? `LINK DA BIO (o que existe de fato): ${cta}`
      : 'LINK DA BIO: não informado. Use CTA genérica de curiosidade e não invente o conteúdo do link.',
    '',
    `TAREFA: ${ACOES[acao]}`,
  ];
  if (atual) {
    linhas.push(
      '',
      'ROTEIRO ATUAL (preserve o assunto e reescreva apenas o necessário para a tarefa):',
      atual.roteiro,
      '',
      `TÍTULO ATUAL: ${atual.titulo || ''}`
    );
    if (acao === 'gancho' || acao === 'cta') {
      linhas.push('', 'Mantenha o restante do roteiro igual. Atualize também ganchos_alternativos, textos_tela e legenda apenas se a mudança exigir.');
    } else {
      linhas.push('', 'Devolva o objeto JSON completo e coerente com o novo roteiro.');
    }
  }
  return linhas.join('\n');
}

function extrairJson(texto) {
  const limpo = texto.trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '');
  const ini = limpo.indexOf('{');
  const fim = limpo.lastIndexOf('}');
  if (ini === -1 || fim === -1) throw new Error('Resposta sem JSON.');
  return JSON.parse(limpo.slice(ini, fim + 1));
}

function validar(o) {
  const str = (v) => typeof v === 'string' && v.trim().length > 0;
  const arr3 = (v) => Array.isArray(v) && v.length >= 3 && v.slice(0, 3).every(str);
  if (!str(o.titulo) || !str(o.roteiro) || !arr3(o.ganchos_alternativos) || !arr3(o.textos_tela) || !str(o.legenda)) {
    throw new Error('JSON incompleto.');
  }
  return {
    titulo: o.titulo.trim(),
    roteiro: o.roteiro.trim(),
    ganchos_alternativos: o.ganchos_alternativos.slice(0, 3).map((s) => s.trim()),
    textos_tela: o.textos_tela.slice(0, 3).map((s) => s.trim()),
    legenda: o.legenda.trim(),
    verificar: Array.isArray(o.verificar) ? o.verificar.filter(str).slice(0, 3) : [],
  };
}

async function chamarModelo(prompt) {
  const resp = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': API_KEY,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 3000,
      system: SYSTEM,
      messages: [{ role: 'user', content: prompt }],
    }),
    signal: AbortSignal.timeout(90_000),
  });
  const corpo = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const e = new Error(corpo?.error?.message || `Erro ${resp.status} na API.`);
    e.status = resp.status;
    throw e;
  }
  return (corpo.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('');
}

async function gerar(entrada) {
  const prompt = montarPrompt(entrada);
  let ultimo;
  for (let tentativa = 0; tentativa < 2; tentativa++) {
    const texto = await chamarModelo(prompt);
    try {
      return validar(extrairJson(texto));
    } catch (e) {
      ultimo = e; // resposta fora do formato: tenta mais uma vez
    }
  }
  throw new Error(`O modelo devolveu uma resposta fora do formato esperado (${ultimo.message}). Tente novamente.`);
}

// Limite simples por IP para proteger a chave (10 requisições/minuto).
const janela = new Map();
function limitado(ip) {
  const agora = Date.now();
  const lista = (janela.get(ip) || []).filter((t) => agora - t < 60_000);
  lista.push(agora);
  janela.set(ip, lista);
  return lista.length > 10;
}

function json(res, status, obj) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(JSON.stringify(obj));
}

function lerCorpo(req) {
  return new Promise((resolve, reject) => {
    let dados = '';
    req.on('data', (c) => {
      dados += c;
      if (dados.length > 50_000) { reject(new Error('Corpo muito grande.')); req.destroy(); }
    });
    req.on('end', () => resolve(dados));
    req.on('error', reject);
  });
}

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml' };

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');

  if (req.method === 'GET' && url.pathname === '/api/status') {
    return json(res, 200, { configurado: Boolean(API_KEY), modelo: MODEL });
  }

  if (req.method === 'POST' && url.pathname === '/api/generate') {
    if (!API_KEY) {
      return json(res, 503, { erro: 'Servidor sem ANTHROPIC_API_KEY configurada. Nenhum roteiro foi gerado.' });
    }
    if (limitado(req.socket.remoteAddress)) {
      return json(res, 429, { erro: 'Muitas requisições. Aguarde um minuto.' });
    }
    let b;
    try { b = JSON.parse(await lerCorpo(req)); } catch { return json(res, 400, { erro: 'Requisição inválida.' }); }

    const assunto = String(b.assunto || '').trim().slice(0, 300);
    const duracao = DURACOES[b.duracao] ? Number(b.duracao) : 60;
    const estilo = ESTILOS[b.estilo] ? b.estilo : 'automatico';
    const cta = String(b.cta || '').trim().slice(0, 300);
    const acao = ACOES[b.acao] ? b.acao : 'gerar';
    const roteiroAtual = String(b.atual?.roteiro || '').trim().slice(0, 6000);
    if (!assunto) return json(res, 400, { erro: 'Informe o assunto do vídeo.' });
    if (acao !== 'gerar' && acao !== 'regenerar' && !roteiroAtual) {
      return json(res, 400, { erro: 'Gere um roteiro antes de refiná-lo.' });
    }
    const atual = roteiroAtual ? { roteiro: roteiroAtual, titulo: String(b.atual?.titulo || '').slice(0, 200) } : null;

    try {
      const resultado = await gerar({ assunto, duracao, estilo, cta, acao, atual });
      return json(res, 200, resultado);
    } catch (e) {
      console.error('Falha na geração:', e.message);
      const status = e.status === 401 ? 502 : e.status === 429 ? 429 : 502;
      const msg = e.status === 401 ? 'Chave da API inválida.' : e.message;
      return json(res, status, { erro: msg });
    }
  }

  if (req.method === 'GET') {
    const rel = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
    const arq = path.resolve(PUBLIC_DIR, rel);
    if (arq.startsWith(PUBLIC_DIR + path.sep) && fs.existsSync(arq) && fs.statSync(arq).isFile()) {
      res.writeHead(200, { 'content-type': MIME[path.extname(arq)] || 'application/octet-stream' });
      return fs.createReadStream(arq).pipe(res);
    }
  }
  res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
  res.end('Não encontrado');
});

if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`ViralScript AI em http://localhost:${PORT} (modelo: ${MODEL})`);
    if (!API_KEY) console.warn('AVISO: ANTHROPIC_API_KEY não definida — a geração ficará indisponível.');
  });
}

module.exports = { montarPrompt, extrairJson, validar, server };
