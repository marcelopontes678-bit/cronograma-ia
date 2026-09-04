/* ===================== GIBOR — Worker (Camada 2) =====================
   Hoje a única responsabilidade deste Worker é expor um proxy seguro para
   chamadas de IA: o app (100% client-side, sem backend próprio) nunca deve
   guardar uma chave de API no navegador. Este endpoint guarda a chave como
   segredo do lado do servidor e é o único lugar que fala com a Anthropic.

   Tudo que não é /api/* continua sendo servido como arquivo estático de
   ./treino, exatamente como antes desta mudança (ver GIBOR_AUDIT.md,
   Camada 2 do plano de evolução).

   Nenhuma funcionalidade de IA foi ligada a este endpoint ainda — isso é
   trabalho da Camada 3. Este é só o "cano".

   Débito conhecido: não há rate limiting por usuário/IP aqui (exigiria KV,
   Durable Objects ou as regras de Rate Limiting do painel Cloudflare — todas
   fora do escopo mínimo da Camada 2). Enquanto não existir, monitore o uso
   pelo painel da Anthropic para não ser pego de surpresa por um custo alto.

   Nota: se ANTHROPIC_API_KEY for adicionada/alterada pelo painel da
   Cloudflare depois do deploy mais recente, é preciso um novo deploy pra
   ela valer — o binding é fixado na versão publicada, não é lido "ao vivo".
*/

import { logError } from './logger.js';

const ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages';
const ANTHROPIC_VERSION = '2023-06-01';
const MODEL = 'claude-sonnet-5';
const MAX_TOKENS_CAP = 1024;
const MAX_TEXT_CHARS = 8000;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/api/health') {
      return json({ ok: true });
    }

    if (url.pathname === '/api/ai/generate') {
      return handleGenerate(request, env);
    }

    return env.ASSETS.fetch(request);
  },
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

async function handleGenerate(request, env) {
  if (request.method !== 'POST') {
    return json({ error: 'Método não permitido, use POST.' }, 405);
  }

  const originError = checkOrigin(request);
  if (originError) return originError;

  const parsed = await parseGenerateBody(request);
  if (parsed.error) return parsed.error;

  // Checa a chave só depois de validar a entrada do cliente — assim um pedido
  // malformado sempre recebe o erro certo, com ou sem a chave configurada.
  if (!env.ANTHROPIC_API_KEY) {
    return json({ error: 'Chave de IA não configurada no servidor.' }, 500);
  }

  const anthropicResult = await callAnthropic(env, parsed);
  if (anthropicResult.error) return anthropicResult.error;

  return json(await buildGenerateResult(anthropicResult.response));
}

// Restringe o proxy ao próprio app — não é uma API pública aberta a qualquer
// origem. Checagem simples (não é proteção completa contra CSRF nem
// substitui rate limiting — ver nota no topo do arquivo). Um Origin
// malformado (ex.: "null", mandado em navegações sandboxed) é tratado
// como não permitido em vez de derrubar a requisição com uma exceção.
function checkOrigin(request) {
  const origin = request.headers.get('Origin');
  if (!origin) return null;
  try {
    if (new URL(origin).host !== new URL(request.url).host) {
      return json({ error: 'Origem não permitida.' }, 403);
    }
  } catch {
    return json({ error: 'Origem não permitida.' }, 403);
  }
  return null;
}

function parseMaxTokens(body) {
  if (body.maxTokens === undefined) return { maxTokens: MAX_TOKENS_CAP };
  const n = Number(body.maxTokens);
  if (!Number.isFinite(n) || n <= 0) {
    return { error: json({ error: '"maxTokens" precisa ser um número maior que zero.' }, 400) };
  }
  return { maxTokens: Math.min(n, MAX_TOKENS_CAP) };
}

async function parseGenerateBody(request) {
  let body;
  try {
    body = await request.json();
  } catch {
    return { error: json({ error: 'Corpo da requisição precisa ser um JSON válido.' }, 400) };
  }
  if (!body || typeof body !== 'object') {
    return { error: json({ error: 'Corpo da requisição precisa ser um objeto JSON.' }, 400) };
  }

  const prompt = typeof body.prompt === 'string' ? body.prompt.trim() : '';
  if (!prompt) {
    return { error: json({ error: 'Campo "prompt" é obrigatório.' }, 400) };
  }
  if (prompt.length > MAX_TEXT_CHARS) {
    return { error: json({ error: `"prompt" excede o limite de ${MAX_TEXT_CHARS} caracteres.` }, 400) };
  }

  const system = typeof body.system === 'string' ? body.system : undefined;
  if (system && system.length > MAX_TEXT_CHARS) {
    return { error: json({ error: `"system" excede o limite de ${MAX_TEXT_CHARS} caracteres.` }, 400) };
  }

  const maxTokensResult = parseMaxTokens(body);
  if (maxTokensResult.error) return maxTokensResult;

  return { prompt, system, maxTokens: maxTokensResult.maxTokens };
}

async function callAnthropic(env, { prompt, system, maxTokens }) {
  let anthropicRes;
  try {
    anthropicRes = await fetch(ANTHROPIC_API_URL, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': env.ANTHROPIC_API_KEY,
        'anthropic-version': ANTHROPIC_VERSION,
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: maxTokens,
        ...(system ? { system } : {}),
        messages: [{ role: 'user', content: prompt }],
      }),
    });
  } catch {
    return { error: json({ error: 'Falha ao contatar o serviço de IA.' }, 502) };
  }

  if (!anthropicRes.ok) {
    const detail = await anthropicRes.text().catch(() => '');
    logError('Anthropic API error', anthropicRes.status, detail);
    return { error: json({ error: 'O serviço de IA retornou um erro.' }, 502) };
  }

  return { response: anthropicRes };
}

async function buildGenerateResult(anthropicRes) {
  const data = await anthropicRes.json();
  const text = (data.content || []).map(b => b.text || '').join('').trim();
  // Sinaliza pro cliente quando a resposta foi cortada por atingir max_tokens,
  // em vez de deixar um texto truncado passar como se fosse uma resposta completa.
  return { text, truncated: data.stop_reason === 'max_tokens' };
}
