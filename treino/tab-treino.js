/* ===================== TAB: TREINO ===================== */
function renderTreinoTab(main) {
  if (state.activeWorkout) { renderActiveWorkout(main); return; }

  main.appendChild(buildTreinoStatsRow());

  const weeklyVolumeCard = buildWeeklyVolumeCard();
  if (weeklyVolumeCard) main.appendChild(weeklyVolumeCard);

  main.appendChild(buildStartEmptyWorkoutButton());
  main.appendChild(buildRoutinesSectionTitle());

  if (!state.routines.length) {
    main.appendChild(makeEmpty('Nenhuma rotina criada ainda.'));
  } else {
    state.routines.forEach(r => main.appendChild(renderRoutineCard(r)));
  }
}

function buildTreinoStatsRow() {
  const totalWorkouts = state.workouts.length;
  const weekAgo = new Date(Date.now() - 7 * 24 * 3600 * 1000);
  const thisWeek = state.workouts.filter(w => new Date(w.date) >= weekAgo).length;
  const totalVolume = state.workouts.reduce((s, w) => s + workoutVolume(w), 0);

  const stats = document.createElement('div');
  stats.className = 'stats-row';
  stats.innerHTML = `
    <div class="stat-box"><div class="stat-num">${totalWorkouts}</div><div class="stat-label">Treinos</div></div>
    <div class="stat-box"><div class="stat-num">${thisWeek}</div><div class="stat-label">Esta semana</div></div>
    <div class="stat-box"><div class="stat-num">${Math.round(totalVolume).toLocaleString('pt-BR')}</div><div class="stat-label">Volume ${unitLabel()}</div></div>
  `;
  return stats;
}

// null quando não há treinos na última semana -- o chamador decide se anexa.
function buildWeeklyVolumeCard() {
  const weeklyVolume = getWeeklyMuscleVolume();
  if (!weeklyVolume.length) return null;
  const maxVol = weeklyVolume[0].volume;
  const volCard = document.createElement('div');
  volCard.className = 'card card-pad';
  volCard.style.marginTop = '12px';
  volCard.innerHTML = `<div class="ex-card-title" style="margin-bottom:10px;">Volume por Grupo Muscular (7 dias)</div>` +
    weeklyVolume.map(v => `
      <div class="muscle-vol-row">
        <span class="muscle-vol-label">${esc(v.muscle)}</span>
        <div class="muscle-vol-bar-wrap"><div class="muscle-vol-bar" style="width:${Math.max(4, (v.volume / maxVol) * 100)}%"></div></div>
        <span class="muscle-vol-value mono">${Math.round(v.volume).toLocaleString('pt-BR')}</span>
      </div>
    `).join('');
  return volCard;
}

function buildStartEmptyWorkoutButton() {
  const startBtn = document.createElement('button');
  startBtn.className = 'btn btn-primary btn-block';
  startBtn.style.marginTop = '14px';
  startBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5v14"/></svg> Começar Treino Vazio`;
  startBtn.onclick = startEmptyWorkout;
  return startBtn;
}

function buildRoutinesSectionTitle() {
  const sectionTitle = document.createElement('div');
  sectionTitle.className = 'section-title';
  sectionTitle.style.display = 'flex';
  sectionTitle.style.justifyContent = 'space-between';
  sectionTitle.style.alignItems = 'center';
  sectionTitle.innerHTML = `<span>Rotinas</span>`;
  const newRoutineBtn = document.createElement('button');
  newRoutineBtn.className = 'btn btn-ghost btn-sm';
  newRoutineBtn.textContent = '+ Nova rotina';
  newRoutineBtn.onclick = () => openRoutineEditor(null);
  sectionTitle.appendChild(newRoutineBtn);
  return sectionTitle;
}

function renderRoutineCard(r) {
  const card = document.createElement('div');
  card.className = 'card routine-card';
  const exLine = r.exercises.map(x => {
    const ex = getExercise(x.exerciseId);
    if (!ex) return '';
    const reps = x.repsMin && x.repsMax ? ` (${x.repsMin}-${x.repsMax})` : '';
    return `${ex.name} · ${x.targetSets}x${reps}`;
  }).filter(Boolean).join('  •  ');
  card.innerHTML = `
    <div class="routine-head">
      <div class="routine-name">${esc(r.name)}</div>
    </div>
    <div class="routine-ex-list">${esc(exLine) || 'Sem exercícios'}</div>
    <div class="routine-actions">
      <button class="btn btn-primary btn-sm" style="flex:1" data-act="start">Iniciar</button>
      <button class="icon-btn" data-act="edit" title="Editar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg></button>
      <button class="icon-btn" data-act="del" title="Excluir"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V6"/></svg></button>
    </div>
  `;
  card.querySelector('[data-act="start"]').onclick = () => startRoutineWorkout(r.id);
  card.querySelector('[data-act="edit"]').onclick = () => openRoutineEditor(r.id);
  card.querySelector('[data-act="del"]').onclick = () => {
    confirmDialog(`Excluir a rotina "${r.name}"?`, () => {
      state.routines = state.routines.filter(x => x.id !== r.id);
      saveState(); render(); toast('Rotina excluída');
    });
  };
  return card;
}

/* ---------- treino ativo ---------- */
function startEmptyWorkout() {
  state.activeWorkout = { id: uid(), name: 'Treino', date: todayISO(), startedAt: Date.now(), notes: '', exercises: [] };
  saveState(); render();
  openExercisePicker(ids => {
    ids.forEach(id => state.activeWorkout.exercises.push(makeWorkoutExercise(id)));
    saveState(); render(); closeModal();
  }, { title: 'Adicionar Exercícios' });
}

function startRoutineWorkout(routineId) {
  const r = state.routines.find(x => x.id === routineId);
  if (!r) return;
  state.activeWorkout = {
    id: uid(), name: r.name, date: todayISO(), startedAt: Date.now(), notes: '',
    exercises: r.exercises.map(x => makeWorkoutExercise(x.exerciseId, x.targetSets)),
  };
  saveState(); render(); setTab('treino');
}
