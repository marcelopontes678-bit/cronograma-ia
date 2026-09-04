/* ---------- rest timer ---------- */
const restTimer = { active: false, endsAt: 0, duration: 0, interval: null, finished: false, contextWeUid: null, contextSetUid: null };

/* Contexto de áudio compartilhado: navegadores móveis só liberam áudio depois de
   um gesto do usuário, então destravamos no primeiro toque em qualquer lugar do
   app, em vez de tentar criar um novo AudioContext de dentro do timer (que
   rodaria "mudo" em boa parte dos navegadores). */
let sharedAudioCtx = null;

function unlockAudio() {
  if (sharedAudioCtx) return;
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    sharedAudioCtx = new AC();
  } catch { /* áudio indisponível */ }
}

document.addEventListener('pointerdown', unlockAudio, { once: true });

function startRestTimer(seconds, context) {
  restTimer.active = true;
  restTimer.finished = false;
  restTimer.duration = seconds;
  restTimer.endsAt = Date.now() + seconds * 1000;
  restTimer.contextWeUid = context ? context.weUid : null;
  restTimer.contextSetUid = context ? context.setUid : null;
  if (restTimer.interval) clearInterval(restTimer.interval);
  restTimer.interval = setInterval(tickRestTimer, 250);
  render();
}

function stopRestTimer() {
  restTimer.active = false;
  restTimer.finished = false;
  restTimer.contextWeUid = null;
  restTimer.contextSetUid = null;
  if (restTimer.interval) { clearInterval(restTimer.interval); restTimer.interval = null; }
  render();
}

function adjustRestTimer(deltaSec) {
  restTimer.endsAt += deltaSec * 1000;
  renderRestBar();
}

function tickRestTimer() {
  const remaining = Math.round((restTimer.endsAt - Date.now()) / 1000);
  if (remaining <= 0) {
    if (!restTimer.finished) {
      restTimer.finished = true;
      if (restTimer.interval) { clearInterval(restTimer.interval); restTimer.interval = null; }
      playRestDoneAlert();
      render(); // troca estrutural: some o divisor embutido, aparece o aviso flutuante
      setTimeout(() => { if (restTimer.finished) stopRestTimer(); }, 2500);
    }
    return;
  }
  renderRestBar();
}

function playRestDoneAlert() {
  try {
    if (!sharedAudioCtx) unlockAudio();
    const ctx = sharedAudioCtx;
    if (ctx) {
      if (ctx.state === 'suspended') ctx.resume();
      [880, 880, 1046, 1046].forEach((freq, i) => {
        const t = ctx.currentTime + i * 0.22;
        const o = ctx.createOscillator(); const g = ctx.createGain();
        o.type = 'sine'; o.frequency.value = freq;
        o.connect(g); g.connect(ctx.destination);
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.25, t + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.2);
        o.start(t); o.stop(t + 0.22);
      });
    }
  } catch { /* som indisponível */ }
  if (navigator.vibrate) navigator.vibrate([250, 100, 250, 100, 400]);
}

function renderRestBar() {
  const root = document.getElementById('restBarRoot');

  if (!restTimer.active) { root.innerHTML = ''; return; }

  if (restTimer.finished) {
    if (root.querySelector('.rest-bar-done')) return;
    root.innerHTML = `
      <div class="rest-bar rest-bar-done" id="restDoneBar">
        <div class="rest-bar-left">
          <span class="rest-bar-time mono">🔔</span>
          <span class="mono" style="font-size:11px;letter-spacing:1px;text-transform:uppercase;">Descanso concluído</span>
        </div>
        <div class="rest-bar-actions"><button id="restDismiss">OK</button></div>
      </div>
    `;
    document.getElementById('restDismiss').onclick = stopRestTimer;
    return;
  }

  const remaining = Math.max(0, Math.round((restTimer.endsAt - Date.now()) / 1000));
  const hasInlinePosition = restTimer.contextWeUid && document.getElementById('restInlineTime');

  if (hasInlinePosition) {
    // O cronômetro tem uma posição embutida entre as séries — não duplica na barra flutuante.
    root.innerHTML = '';
    document.getElementById('restInlineTime').textContent = formatDuration(remaining);
    return;
  }

  const existing = root.querySelector('#restEdit');
  if (existing) {
    // apenas atualiza o texto — evita recriar o DOM (e replay da animação de entrada) a cada tick
    existing.textContent = formatDuration(remaining);
    return;
  }
  root.innerHTML = `
    <div class="rest-bar">
      <div class="rest-bar-left">
        <button class="rest-bar-time mono" id="restEdit" title="Editar tempo">${formatDuration(remaining)}</button>
        <span class="mono" style="font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;">Descanso</span>
      </div>
      <div class="rest-bar-actions">
        <button id="restMinus">-15s</button>
        <button id="restPlus">+15s</button>
        <button id="restSkip">Pular</button>
      </div>
    </div>
  `;
  document.getElementById('restEdit').onclick = () => openRestTimerEditor(Math.max(0, Math.round((restTimer.endsAt - Date.now()) / 1000)));
  document.getElementById('restMinus').onclick = () => adjustRestTimer(-15);
  document.getElementById('restPlus').onclick = () => adjustRestTimer(15);
  document.getElementById('restSkip').onclick = stopRestTimer;
}

/* Divisor de descanso embutido entre as séries — a posição preferida do cronômetro,
   em vez da barra flutuante (que fica só como reserva quando não há uma série de
   referência visível, por exemplo se o timer foi iniciado pelo botão do cabeçalho). */
function buildInlineRestDivider() {
  const remaining = Math.max(0, Math.round((restTimer.endsAt - Date.now()) / 1000));
  const div = document.createElement('div');
  div.className = 'set-rest-divider';
  div.innerHTML = `<span class="set-rest-divider-time mono" id="restInlineTime">${formatDuration(remaining)}</span>`;
  div.onclick = () => openRestTimerEditor(Math.max(0, Math.round((restTimer.endsAt - Date.now()) / 1000)));
  return div;
}

function openRestTimerEditor(currentSeconds) {
  const min = Math.floor(currentSeconds / 60);
  const sec = currentSeconds % 60;
  openModal(`
    <div class="modal-title">Editar Descanso</div>
    <label class="field-label">Tempo (min:seg)</label>
    <div style="display:flex;gap:10px;align-items:center;">
      <input id="rtMin" type="number" inputmode="numeric" min="0" value="${min}" style="text-align:center;">
      <span class="mono" style="font-size:16px;">:</span>
      <input id="rtSec" type="number" inputmode="numeric" min="0" max="59" value="${sec}" style="text-align:center;">
    </div>
    <label class="field-label">Ou escolha um preset</label>
    <div class="chip-row">
      ${[30, 60, 90, 120, 180, 240].map(s => `<button class="chip" data-s="${s}">${formatDuration(s)}</button>`).join('')}
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost" style="flex:1" id="rtCancel">Cancelar</button>
      <button class="btn btn-primary" style="flex:2" id="rtSave">Definir</button>
    </div>
  `);
  // Mantém a posição embutida entre as séries, se já havia uma, ao redefinir o tempo.
  const keepContext = restTimer.contextWeUid ? { weUid: restTimer.contextWeUid, setUid: restTimer.contextSetUid } : undefined;
  document.querySelectorAll('.chip-row [data-s]').forEach(chip => {
    chip.onclick = () => { startRestTimer(Number(chip.dataset.s), keepContext); closeModal(); };
  });
  document.getElementById('rtCancel').onclick = closeModal;
  document.getElementById('rtSave').onclick = () => {
    const m = Math.max(0, Number(document.getElementById('rtMin').value) || 0);
    const s = Math.max(0, Number(document.getElementById('rtSec').value) || 0);
    const total = m * 60 + s;
    if (total <= 0) { toast('Informe um tempo maior que zero.'); return; }
    startRestTimer(total, keepContext);
    closeModal();
  };
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('btnQuickTimer').onclick = () => startRestTimer(state.settings.restDefault);
});
