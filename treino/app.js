/* ===================== TREINO — app inspirado no Strong ===================== */
/* Orquestrador: carrega por último (ver treino/index.html) e depende de todos os
   outros módulos de treino/ já terem sido avaliados -- eles só declaram funções e
   variáveis de script global, então a ordem entre eles não importa, mas este
   arquivo chama render() e applyTheme() de imediato, então ele tem que vir depois. */

/* ===================== NAVEGAÇÃO / RENDER ===================== */
let ui = {
  tab: 'treino',
  exFilterQuery: '',
  exFilterMuscle: 'Todos',
  exerciseDetailId: null,
  historyDetailId: null,
  showMeasurements: false,
  instructionsExpanded: false,
};

function setTab(tab) {
  ui.tab = tab;
  ui.exerciseDetailId = null;
  ui.historyDetailId = null;
  ui.showMeasurements = false;
  render();
  window.scrollTo(0, 0);
}

function render() {
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === ui.tab));
  const headerSub = document.getElementById('headerSub');
  const subs = { treino: 'Diário de treino', historico: 'Histórico de treinos', exercicios: 'Biblioteca de exercícios', perfil: 'Perfil & Ajustes' };
  headerSub.textContent = subs[ui.tab] || '';

  const main = document.getElementById('main');
  main.innerHTML = '';
  if (ui.tab === 'treino') renderTreinoTab(main);
  else if (ui.tab === 'historico') renderHistoricoTab(main);
  else if (ui.tab === 'exercicios') renderExerciciosTab(main);
  else if (ui.tab === 'perfil') renderPerfilTab(main);

  renderRestBar();
}

/* ===================== INIT ===================== */
applyTheme();
if (state.activeWorkout) { /* mantém sessão ativa entre reloads */ }
render();

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('./sw.js').catch(() => {});
}
