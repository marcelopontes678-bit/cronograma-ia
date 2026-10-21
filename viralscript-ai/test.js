// Testes do que roda sem chamar a API: montagem de prompt, parsing e validação.
const assert = require('assert');
const { montarPrompt, extrairJson, validar } = require('./server');

const base = { assunto: 'Hermès', duracao: 60, estilo: 'luxo', cta: '', acao: 'gerar', atual: null };
assert(montarPrompt(base).includes('não informado'), 'sem CTA deve instruir a não inventar o link');
assert(montarPrompt({ ...base, cta: 'e-book X' }).includes('e-book X'));
assert(montarPrompt({ ...base, acao: 'encurtar', atual: { roteiro: 'texto atual', titulo: 't' } }).includes('texto atual'));

const ok = { titulo: 'a', roteiro: 'b', ganchos_alternativos: ['1', '2', '3'], textos_tela: ['1', '2', '3'], legenda: 'l' };
assert.deepStrictEqual(validar(extrairJson('```json\n' + JSON.stringify(ok) + '\n```')).verificar, []);
assert.throws(() => validar({ ...ok, ganchos_alternativos: ['1'] }));
assert.throws(() => extrairJson('sem json'));
console.log('ok');
