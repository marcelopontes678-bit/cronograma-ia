// Componentes interativos reutilizáveis das lições.
//
// 1) Pergunta de múltipla escolha:
//    <div class="quiz-q" data-resposta="2">
//      <p class="pergunta">...</p>
//      <div class="opcoes"><button class="opcao">A</button>...</div>
//      <p class="explica">Por que a certa é a certa.</p>
//    </div>
//    data-resposta é o índice (começando em 0) do botão correto.
//
// 2) Classificação (cada item tem uma categoria certa):
//    <div class="classifica" data-categoria="Backend">
//      <p class="item">backend/app/main.py</p>
//      <div class="botoes"><button class="opcao">Frontend</button>...</div>
//      <p class="explica">...</p>
//    </div>
//
// Um elemento com a classe "placar" mostra o total de acertos da página.

(function () {
  let acertos = 0;
  let total = 0;

  function atualizarPlacar() {
    document.querySelectorAll(".placar").forEach((el) => {
      const respondidas = document.querySelectorAll(".respondida").length;
      el.textContent = `Acertos: ${acertos} de ${respondidas} respondidas (${total} no total)`;
    });
  }

  function responder(bloco, botoes, botaoClicado, correto) {
    botoes.forEach((b) => (b.disabled = true));
    if (correto) {
      botaoClicado.classList.add("certo");
      acertos += 1;
    } else {
      botaoClicado.classList.add("errado");
      // Mostra também qual era a certa, para fechar o ciclo de feedback.
      botoes.forEach((b) => {
        if (b.dataset.certo === "sim") b.classList.add("certo");
      });
    }
    bloco.classList.add("respondida");
    atualizarPlacar();
  }

  document.querySelectorAll(".quiz-q").forEach((bloco) => {
    total += 1;
    const certa = Number(bloco.dataset.resposta);
    const botoes = Array.from(bloco.querySelectorAll("button.opcao"));
    botoes.forEach((botao, i) => {
      if (i === certa) botao.dataset.certo = "sim";
      botao.addEventListener("click", () => responder(bloco, botoes, botao, i === certa));
    });
  });

  document.querySelectorAll(".classifica").forEach((bloco) => {
    total += 1;
    const certa = bloco.dataset.categoria;
    const botoes = Array.from(bloco.querySelectorAll("button.opcao"));
    botoes.forEach((botao) => {
      const ehCerta = botao.textContent.trim() === certa;
      if (ehCerta) botao.dataset.certo = "sim";
      botao.addEventListener("click", () => responder(bloco, botoes, botao, ehCerta));
    });
  });

  // Checklists de tarefas reais: lembra o que foi marcado neste navegador.
  document.querySelectorAll(".checklist input[type=checkbox]").forEach((caixa) => {
    const chave = `${location.pathname}#${caixa.id}`;
    try {
      caixa.checked = localStorage.getItem(chave) === "1";
    } catch (e) { /* armazenamento indisponível: segue sem lembrar */ }
    caixa.addEventListener("change", () => {
      try {
        localStorage.setItem(chave, caixa.checked ? "1" : "0");
      } catch (e) { /* idem */ }
    });
  });

  atualizarPlacar();
})();
