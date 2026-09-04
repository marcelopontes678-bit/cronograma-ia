function buildWorkoutSummaryCard(w) {
  const summaries = getWorkoutExerciseSummaries(w);
  const prCount = countWorkoutPRs(w);
  const card = document.createElement('div');
  card.className = 'card card-pad workout-summary-card';
  card.innerHTML = `
    <div class="history-name" style="font-size:19px;">${esc(w.name)}</div>
    <div class="history-date" style="margin-bottom:${w.notes ? '6px' : '14px'};">${esc(formatDateTimeFull(w.date))}</div>
    ${w.notes ? `<p style="font-size:13px;color:var(--muted);line-height:1.6;margin-bottom:14px;">${esc(w.notes)}</p>` : ''}
    <div class="summary-cols-head">
      <span>Séries</span><span>Melhor série</span>
    </div>
    <div class="summary-rows">
      ${summaries.map(s => `
        <div class="summary-row">
          <span class="summary-row-left">${s.count} × ${esc(s.name)}</span>
          <span class="summary-row-right mono">${s.best ? `${esc(s.best.weight)}${unitLabel()} × ${esc(s.best.reps)}` : '—'}</span>
        </div>
      `).join('')}
    </div>
    <div class="summary-footer">
      <span class="summary-footer-item">⏱ ${formatDuration(w.durationSec || 0)}</span>
      <span class="summary-footer-item">🏋 ${Math.round(workoutVolume(w)).toLocaleString('pt-BR')}${unitLabel()}</span>
      <span class="summary-footer-item">🏆 ${prCount} PR${prCount === 1 ? '' : 's'}</span>
    </div>
  `;
  return card;
}

/* ===================== TAB: HISTÓRICO ===================== */
function renderHistoricoTab(main) {
  if (ui.historyDetailId) { renderHistoryDetail(main, ui.historyDetailId); return; }

  if (!state.workouts.length) {
    main.appendChild(makeEmpty('Nenhum treino registrado ainda.\nSeus treinos concluídos aparecerão aqui.'));
    return;
  }
  const sorted = [...state.workouts].sort((a, b) => new Date(b.date) - new Date(a.date));
  sorted.forEach(w => {
    const card = document.createElement('div');
    card.className = 'card history-card';
    const exLine = w.exercises.map(we => { const ex = getExercise(we.exerciseId); return ex ? ex.name : ''; }).filter(Boolean).join(', ');
    card.innerHTML = `
      <div class="history-head">
        <div>
          <div class="history-name">${esc(w.name)}</div>
          <div class="history-date">${esc(formatDateShort(w.date))}</div>
        </div>
      </div>
      <div class="history-meta">
        <span class="history-meta-item">⏱ ${formatDuration(w.durationSec || 0)}</span>
        <span class="history-meta-item">🏋 ${workoutSetCount(w)} séries</span>
        <span class="history-meta-item">📊 ${Math.round(workoutVolume(w)).toLocaleString('pt-BR')} ${unitLabel()}</span>
      </div>
      <div class="history-ex-line">${esc(exLine)}</div>
    `;
    card.onclick = () => { ui.historyDetailId = w.id; render(); window.scrollTo(0,0); };
    main.appendChild(card);
  });
}

function renderHistoryDetail(main, workoutId) {
  const w = state.workouts.find(x => x.id === workoutId);
  if (!w) { ui.historyDetailId = null; renderHistoricoTab(main); return; }

  main.appendChild(buildHistoryBackButton());
  main.appendChild(buildWorkoutSummaryCard(w));
  main.appendChild(buildHistoryDetailsTitle());
  w.exercises.forEach(we => main.appendChild(buildHistoryExerciseCard(we)));
  main.appendChild(buildHistoryDetailActions(w, workoutId));
}

function buildHistoryBackButton() {
  const back = document.createElement('button');
  back.className = 'btn btn-ghost btn-sm';
  back.style.marginBottom = '14px';
  back.innerHTML = '← Voltar';
  back.onclick = () => { ui.historyDetailId = null; render(); };
  return back;
}

function buildHistoryDetailsTitle() {
  const detailsTitle = document.createElement('div');
  detailsTitle.className = 'section-title';
  detailsTitle.textContent = 'Detalhes de todas as séries';
  return detailsTitle;
}

function buildHistoryExerciseCard(we) {
  const ex = getExercise(we.exerciseId);
  const card = document.createElement('div');
  card.className = 'card';
  card.style.marginTop = '12px';
  const rows = we.sets.map((s, i) => `<div class="set-history-row"><span>${s.warmup ? 'W' : (i+1)}</span><span>${esc(s.weight)}${unitLabel()} × ${esc(s.reps)}${s.rpe ? ` · RPE ${esc(s.rpe)}` : ''}</span></div>`).join('');
  card.innerHTML = `
    <div class="ex-card-head"><div class="ex-card-title">${esc(ex ? ex.name : 'Exercício')}</div></div>
    ${rows}
  `;
  return card;
}

function buildHistoryDetailActions(w, workoutId) {
  const actions = document.createElement('div');
  actions.className = 'modal-footer';
  actions.style.marginTop = '18px';
  actions.innerHTML = `
    <button class="btn btn-ghost" style="flex:1" id="dRepeat">Repetir Treino</button>
    <button class="btn btn-danger" style="flex:1" id="dDelete">Excluir</button>
  `;
  actions.querySelector('#dRepeat').onclick = () => {
    if (state.activeWorkout) { toast('Finalize ou descarte o treino em andamento primeiro.'); return; }
    state.activeWorkout = {
      id: uid(), name: w.name, date: todayISO(), startedAt: Date.now(), notes: '',
      exercises: w.exercises.map(we => ({ uid: uid(), exerciseId: we.exerciseId, sets: we.sets.map(() => makeEmptySet()) })),
    };
    saveState(); ui.historyDetailId = null; setTab('treino');
  };
  actions.querySelector('#dDelete').onclick = () => {
    confirmDialog('Excluir este treino do histórico?', () => {
      state.workouts = state.workouts.filter(x => x.id !== workoutId);
      saveState(); ui.historyDetailId = null; render(); toast('Treino excluído');
    });
  };
  return actions;
}
