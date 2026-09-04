function renderWorkoutExerciseCard(we, subLabel) {
  const ex = getExercise(we.exerciseId);
  const card = document.createElement('div');
  card.className = 'card ex-card' + (subLabel ? '' : ' drag-row');
  if (!subLabel) card.dataset.id = we.uid;

  card.appendChild(buildExerciseCardHead(we, ex, subLabel));
  card.appendChild(buildExerciseSetTable(we, ex));
  return card;
}

// Fragmentos condicionais do cabeçalho, cada um isolado em sua própria função
// pra manter a complexidade de buildExerciseCardHead baixa -- ela só monta o
// template, cada ramo (mostrar ou não) mora aqui.
function dragHandleHtml(subLabel) {
  return subLabel ? '' : '<button class="drag-handle" title="Arrastar para reordenar">≡</button>';
}
function subLabelHtml(subLabel) {
  return subLabel ? `<span class="ex-sublabel">${esc(subLabel)}</span>` : '';
}
function bestBadgeHtml(exPr) {
  return exPr.maxWeight ? ` · <span class="ex-best-badge">🏆 ${exPr.maxWeight}${unitLabel()}</span>` : '';
}
function exerciseNoteHtml(we) {
  return we.notes ? `<div class="ex-card-note">📝 ${esc(we.notes)}</div>` : '';
}
function headSuggestionHtml(headSuggestion) {
  return headSuggestion ? `<div class="ex-card-suggestion">💡 ${esc(headSuggestion.reason)}</div>` : '';
}
function plateButtonHtml(ex) {
  return ex && ex.equipment === 'Barra' ? '<button class="icon-btn ex-plate-btn" title="Calculadora de anilhas">🏋</button>' : '';
}
function checkBadgeHtml(allDone) {
  const doneClass = allDone ? 'on' : '';
  const doneTitle = allDone ? 'Exercício concluído' : '';
  return `
    <div class="ex-check-badge ${doneClass}" title="${doneTitle}">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M4 12l5 5L20 6"/></svg>
    </div>
  `;
}

function buildExerciseCardHead(we, ex, subLabel) {
  const workingSets = we.sets.filter(s => !s.warmup);
  const allDone = workingSets.length > 0 && workingSets.every(s => s.completed);
  const exPr = getExercisePR(we.exerciseId);
  // Sugestão da 1ª série representa a tendência geral do exercício — é a que
  // aparece como dica no cabeçalho do card (cada série individual ainda tem
  // sua própria sugestão nos placeholders/preenchimento automático abaixo).
  const headSuggestion = !allDone ? getProgressionSuggestion(we.exerciseId, 0) : null;

  const head = document.createElement('div');
  head.className = 'ex-card-head';
  head.innerHTML = `
    ${dragHandleHtml(subLabel)}
    <div class="ex-card-head-info">
      <div class="ex-card-title">${esc(ex ? ex.name : 'Exercício')}${subLabelHtml(subLabel)}</div>
      <div class="ex-card-sub">${esc(ex ? ex.muscle : '')}${bestBadgeHtml(exPr)}</div>
      ${exerciseNoteHtml(we)}
      ${headSuggestionHtml(headSuggestion)}
    </div>
    <div class="ex-card-head-actions">
      ${plateButtonHtml(ex)}
      ${checkBadgeHtml(allDone)}
      <button class="ex-card-menu-btn" title="Mais opções">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><circle cx="12" cy="5" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="12" cy="19" r="1.4"/></svg>
      </button>
    </div>
  `;
  head.querySelector('.ex-card-menu-btn').onclick = () => openExerciseActionMenu(we, ex);
  const plateBtn = head.querySelector('.ex-plate-btn');
  if (plateBtn) plateBtn.onclick = () => openPlateCalculator(we);
  return head;
}

function buildExerciseSetTable(we, ex) {
  const table = document.createElement('div');
  table.className = 'set-table';
  table.innerHTML = `
    <div class="set-row-header">
      <span>SET</span><span>REPS</span><span>${unitLabel().toUpperCase()}</span><span>RPE</span><span>✓</span>
    </div>
  `;
  let workingIdx = 0;
  we.sets.forEach((s) => {
    const numLabel = s.warmup ? 'W' : String(++workingIdx);
    const prevIdx = s.warmup ? -1 : workingIdx - 1;
    const prev = !s.warmup ? getProgressionSuggestion(we.exerciseId, prevIdx) : null;
    table.appendChild(buildSetRow(we, ex, s, { numLabel, prev }));
    if (restTimer.active && !restTimer.finished && restTimer.contextWeUid === we.uid && restTimer.contextSetUid === s.uid) {
      table.appendChild(buildInlineRestDivider());
    }
  });
  table.appendChild(buildAddSetButton(we));
  return table;
}

function buildSetRow(we, ex, s, { numLabel, prev }) {
  const pr = s.completed && !s.warmup && isSetPR(we.exerciseId, s.weight, s.reps, state.activeWorkout.id);
  const row = document.createElement('div');
  row.className = 'set-row' + (s.completed ? ' completed' : '') + (s.warmup ? ' warmup' : '');
  row.innerHTML = `
    <button class="set-num-btn" title="Marcar como aquecimento">${numLabel}${pr ? '<span class="pr-dot">🏆</span>' : ''}</button>
    <input class="set-input" type="number" inputmode="numeric" placeholder="${prev ? prev.reps : '0'}" value="${s.reps}">
    <input class="set-input" type="number" inputmode="decimal" placeholder="${prev ? prev.weight : '0'}" value="${s.weight}">
    <input class="set-input set-input-rpe" type="number" step="0.5" min="1" max="10" inputmode="decimal" placeholder="${prev && prev.rpe ? prev.rpe : '–'}" value="${s.rpe || ''}">
    <button class="set-check ${s.completed ? 'on' : ''}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M4 12l5 5L20 6"/></svg></button>
  `;
  const [numBtn, repsInput, weightInput, rpeInput, checkBtn] = row.children;
  numBtn.onclick = () => { s.warmup = !s.warmup; saveState(); render(); };
  weightInput.oninput = () => { s.weight = weightInput.value; saveState(); };
  repsInput.oninput = () => { s.reps = repsInput.value; saveState(); };
  rpeInput.oninput = () => { s.rpe = rpeInput.value; saveState(); };
  checkBtn.onclick = () => completeWorkoutSet(we, ex, s, prev);
  enableSwipeToDelete(row, () => { we.sets = we.sets.filter(x => x.uid !== s.uid); saveState(); render(); });
  return row;
}

function completeWorkoutSet(we, ex, s, prev) {
  s.completed = !s.completed;
  if (s.completed) {
    if (!s.weight && prev) s.weight = prev.weight;
    if (!s.reps && prev) s.reps = prev.reps;
    if (!s.warmup && isLastInGroup(we)) {
      saveState();
      startRestTimer(ex && ex.restOverride ? ex.restOverride : state.settings.restDefault, { weUid: we.uid, setUid: s.uid });
      return; // startRestTimer já re-renderiza
    }
  }
  saveState(); render();
}

function buildAddSetButton(we) {
  const addSetBtn = document.createElement('button');
  addSetBtn.className = 'btn btn-ghost btn-sm add-set-btn';
  addSetBtn.textContent = '+ Adicionar Série';
  addSetBtn.onclick = () => { we.sets.push(makeEmptySet()); saveState(); render(); };
  return addSetBtn;
}

function openPlateCalculator(we) {
  const ex = getExercise(we.exerciseId);
  const lastWeight = [...we.sets].reverse().find(s => s.weight)?.weight || state.settings.barWeight;
  openModal(`
    <div class="modal-title">Calculadora de Anilhas</div>
    <div class="ex-card-sub" style="margin-bottom:14px;">${esc(ex ? ex.name : '')}</div>
    <label class="field-label">Peso total (${unitLabel()})</label>
    <input id="pcTarget" type="number" inputmode="decimal" value="${lastWeight}">
    <label class="field-label">Peso da barra (${unitLabel()})</label>
    <input id="pcBar" type="number" inputmode="decimal" value="${state.settings.barWeight}">
    <div id="pcResult"></div>
    <div class="modal-footer">
      <button class="btn btn-primary btn-block" id="pcClose">Fechar</button>
    </div>
  `);
  const targetEl = document.getElementById('pcTarget');
  const barEl = document.getElementById('pcBar');
  const resultEl = document.getElementById('pcResult');
  const update = () => {
    const r = calculatePlates(targetEl.value, barEl.value);
    const plateChips = r.perSide.length
      ? r.perSide.map(p => `<span class="plate-chip">${p}</span>`).join('')
      : '<span class="mono" style="color:var(--muted);font-size:12px;">Sem anilhas — só a barra</span>';
    resultEl.innerHTML = `
      <div class="field-label" style="margin:16px 0 8px;">Anilhas por lado</div>
      <div class="plate-chips">${plateChips}</div>
      ${r.leftover > 0.01 ? `<div class="mono" style="color:var(--yellow);font-size:11px;margin-top:8px;">Sobram ${r.leftover.toFixed(2)}${unitLabel()} por lado (sem anilha exata disponível)</div>` : ''}
    `;
  };
  targetEl.oninput = update;
  barEl.oninput = update;
  document.getElementById('pcClose').onclick = closeModal;
  update();
}

/* ---------- menu de ações por exercício (⋮) ---------- */
function openExerciseActionMenu(we, ex) {
  const items = [
    { icon: '📝', label: 'Adicionar observação', act: () => openExerciseNoteEditor(we) },
    { icon: '➕', label: 'Adicionar série de aquecimento', act: () => addWarmupSet(we) },
    { icon: '⏱', label: 'Atualizar temporizador de descanso', act: () => openExerciseRestOverrideEditor(ex) },
    { divider: true },
    { icon: '⇄', label: 'Substituir exercício', act: () => openReplaceExercise(we) },
    { icon: '🔗', label: 'Criar supersérie', act: () => { closeModal(); openGroupPicker(); } },
    { divider: true },
    { icon: '✕', label: 'Remover exercício', danger: true, act: () => {
      closeModal();
      confirmDialog(`Remover "${ex ? ex.name : 'exercício'}" deste treino?`, () => {
        state.activeWorkout.exercises = state.activeWorkout.exercises.filter(x => x.uid !== we.uid);
        saveState(); render();
      });
    } },
  ];
  openModal(`
    <div class="action-menu-list">
      ${items.map((it, i) => it.divider
        ? '<div class="action-menu-divider"></div>'
        : `<button class="action-menu-item ${it.danger ? 'danger' : ''}" data-i="${i}"><span class="action-menu-icon">${it.icon}</span>${esc(it.label)}</button>`
      ).join('')}
    </div>
  `);
  document.querySelectorAll('.action-menu-item').forEach(btn => {
    btn.onclick = () => items[Number(btn.dataset.i)].act();
  });
}

function openExerciseNoteEditor(we) {
  openModal(`
    <div class="modal-title">Observação</div>
    <textarea id="weNoteInput" rows="3" placeholder="Ex: usar pegada fechada, cadeira no ajuste 4...">${esc(we.notes || '')}</textarea>
    <div class="modal-footer">
      <button class="btn btn-ghost" style="flex:1" id="weNoteCancel">Cancelar</button>
      <button class="btn btn-primary" style="flex:2" id="weNoteSave">Salvar</button>
    </div>
  `);
  document.getElementById('weNoteCancel').onclick = closeModal;
  document.getElementById('weNoteSave').onclick = () => {
    we.notes = document.getElementById('weNoteInput').value.trim();
    saveState(); closeModal(); render();
  };
}

function addWarmupSet(we) {
  const s = makeEmptySet();
  s.warmup = true;
  we.sets.unshift(s);
  saveState(); closeModal(); render();
}

function openExerciseRestOverrideEditor(ex) {
  if (!ex) { closeModal(); return; }
  const restOptions = [null, 30, 60, 90, 120, 180];
  openModal(`
    <div class="modal-title">Temporizador de Descanso</div>
    <div class="ex-card-sub" style="margin-bottom:14px;">${esc(ex.name)}</div>
    <div class="seg" id="weRestSeg" style="flex-wrap:wrap;">
      ${restOptions.map(v => `<button data-v="${v ?? ''}" class="${(ex.restOverride || null) === v ? 'on' : ''}">${v ? formatDuration(v) : 'Padrão'}</button>`).join('')}
    </div>
    <div class="modal-footer">
      <button class="btn btn-primary btn-block" id="weRestClose">Fechar</button>
    </div>
  `);
  document.querySelectorAll('#weRestSeg button').forEach(b => b.onclick = () => {
    ex.restOverride = b.dataset.v ? Number(b.dataset.v) : null;
    saveState(); closeModal(); render();
  });
  document.getElementById('weRestClose').onclick = closeModal;
}

function openReplaceExercise(we) {
  openExercisePicker(ids => {
    const newId = ids[0];
    if (!newId || newId === we.exerciseId) { closeModal(); return; }
    we.exerciseId = newId;
    we.notes = '';
    we.sets = we.sets.map(s => ({ uid: uid(), weight: '', reps: '', rpe: '', completed: false, warmup: s.warmup }));
    saveState(); closeModal(); render(); toast('Exercício substituído');
  }, { title: 'Substituir Por', confirmLabel: 'Substituir' });
}
