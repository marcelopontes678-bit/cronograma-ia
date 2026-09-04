/* Ponto único de log do app treino/ -- todo console.* direto no resto do
   código passa por aqui, pra manter a porta aberta pra um dia mandar
   erros pra um serviço de monitoramento sem caçar console.error espalhado
   pelo código. Hoje só encaminha pro console mesmo. */
function logError(...args) {
  console.error(...args);
}
