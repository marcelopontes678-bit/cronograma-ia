function makeWorkoutExercise(exerciseId, targetSets) {
  const n = targetSets || 3;
  const sets = [];
  for (let i = 0; i < n; i++) sets.push(makeEmptySet());
  return { uid: uid(), exerciseId, sets, groupId: null };
}

function makeEmptySet() { return { uid: uid(), weight: '', reps: '', rpe: '', completed: false, warmup: false }; }

function renderActiveWorkout(main) {
  const aw = state.activeWorkout;

  main.appendChild(buildActiveWorkoutTimerBar(aw));
  main.appendChild(buildActiveWorkoutProgressBar(aw));
  startActiveTimer();

  if (!aw.exercises.length) {
    main.appendChild(makeEmpty('Adicione exercícios para começar a registrar suas séries.'));
  }
  renderActiveWorkoutExerciseCards(main, aw);

  main.appendChild(buildActiveWorkoutActionsRow(aw));
}

function buildActiveWorkoutTimerBar(aw) {
  const timerBar = document.createElement('div');
  timerBar.className = 'workout-timer-bar';
  timerBar.innerHTML = `
    <div>
      <div class="workout-timer-time mono" id="activeTimer">00:00</div>
      <div class="workout-timer-label">${esc(aw.name)}</div>
    </div>
    <div class="workout-actions">
      <button class="btn btn-ghost btn-sm" id="btnDiscard">Descartar</button>
      <button class="btn btn-primary btn-sm" id="btnFinish">Finalizar</button>
    </div>
  `;
  timerBar.querySelector('#btnDiscard').onclick = () => {
    confirmDialog('Descartar este treino? Todo o progresso será perdido.', () => {
      stopActiveTimer();
      state.activeWorkout = null; saveState(); render(); toast('Treino descartado');
    });
  };
  timerBar.querySelector('#btnFinish').onclick = openFinishWorkoutModal;
  return timerBar;
}

function buildActiveWorkoutProgressBar(aw) {
  const totalSets = aw.exercises.reduce((s, we) => s + we.sets.filter(x => !x.warmup).length, 0);
  const doneSets = aw.exercises.reduce((s, we) => s + we.sets.filter(x => !x.warmup && x.completed).length, 0);
  const pct = totalSets ? Math.round((doneSets / totalSets) * 100) : 0;
  const progressBar = document.createElement('div');
  progressBar.className = 'workout-progress-bar';
  progressBar.innerHTML = `<div class="workout-progress-fill" style="width:${pct}%"></div>`;
  return progressBar;
}

function renderActiveWorkoutExerciseCards(main, aw) {
  const groupLabels = computeGroupLabels();
  const rendered = new Set();
  aw.exercises.forEach(we => {
    if (rendered.has(we.uid)) return;
    if (we.groupId) {
      const siblings = getGroupSiblings(we.groupId);
      siblings.forEach(s => rendered.add(s.uid));
      main.appendChild(renderExerciseGroup(we.groupId, siblings, groupLabels[we.groupId]));
    } else {
      rendered.add(we.uid);
      main.appendChild(renderWorkoutExerciseCard(we));
    }
  });

  if (aw.exercises.length >= 2) {
    enableDragReorder(main, ids => {
      const newList = [];
      ids.forEach(id => {
        if (id.startsWith('group:')) newList.push(...getGroupSiblings(id.slice(6)));
        else { const we = aw.exercises.find(x => x.uid === id); if (we) newList.push(we); }
      });
      aw.exercises = newList;
      saveState(); render();
    });
  }
}

function buildActiveWorkoutActionsRow(aw) {
  const actionsRow = document.createElement('div');
  actionsRow.style.display = 'flex';
  actionsRow.style.gap = '8px';
  actionsRow.style.marginTop = '4px';

  const addBtn = document.createElement('button');
  addBtn.className = 'btn btn-ghost';
  addBtn.style.flex = '1';
  addBtn.innerHTML = `+ Adicionar Exercício`;
  addBtn.onclick = () => {
    openExercisePicker(ids => {
      ids.forEach(id => aw.exercises.push(makeWorkoutExercise(id)));
      saveState(); render(); closeModal();
    }, { title: 'Adicionar Exercícios' });
  };
  actionsRow.appendChild(addBtn);

  if (aw.exercises.length >= 2) {
    const groupBtn = document.createElement('button');
    groupBtn.className = 'btn btn-ghost';
    groupBtn.style.flex = '1';
    groupBtn.innerHTML = `🔗 Agrupar`;
    groupBtn.onclick = openGroupPicker;
    actionsRow.appendChild(groupBtn);
  }
  return actionsRow;
}

function renderExerciseGroup(groupId, members, label) {
  const wrap = document.createElement('div');
  wrap.className = 'group-wrap drag-row';
  wrap.dataset.id = 'group:' + groupId;
  const head = document.createElement('div');
  head.className = 'group-wrap-head';
  head.innerHTML = `<button class="drag-handle" title="Arrastar para reordenar">≡</button><span>SUPERSET ${esc(label || '')}</span><button class="btn btn-ghost btn-sm" style="padding:5px 10px;margin-left:auto;">Desagrupar</button>`;
  head.querySelector('.btn-ghost').onclick = () => {
    members.forEach(m => { m.groupId = null; });
    saveState(); render();
  };
  wrap.appendChild(head);
  members.forEach((we, i) => {
    const card = renderWorkoutExerciseCard(we, `${label}${i + 1}`);
    card.style.marginBottom = i === members.length - 1 ? '0' : '10px';
    wrap.appendChild(card);
  });
  return wrap;
}

function openGroupPicker() {
  const aw = state.activeWorkout;
  const selected = new Set();
  const draw = () => {
    openModal(`
      <div class="modal-title">Agrupar Exercícios</div>
      <p style="font-size:13px;color:var(--muted);margin-bottom:12px;line-height:1.5;">Selecione 2 ou mais exercícios deste treino para formar um superset (alternados sem descanso entre eles).</p>
      <div class="card" id="gpList"></div>
      <div class="modal-footer">
        <button class="btn btn-ghost" style="flex:1" id="gpCancel">Cancelar</button>
        <button class="btn btn-primary" style="flex:2" id="gpConfirm">Agrupar (${selected.size})</button>
      </div>
    `);
    const list = document.getElementById('gpList');
    aw.exercises.forEach(we => {
      const ex = getExercise(we.exerciseId);
      const on = selected.has(we.uid);
      const item = document.createElement('div');
      item.className = 'ex-list-item';
      item.innerHTML = `
        <div><div class="ex-list-name">${esc(ex ? ex.name : '?')}</div><div class="ex-list-muscle">${esc(ex ? ex.muscle : '')}${we.groupId ? ' · já agrupado' : ''}</div></div>
        <div class="ex-list-check ${on ? 'on' : ''}">${on ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M4 12l5 5L20 6"/></svg>' : ''}</div>
      `;
      item.onclick = () => { if (selected.has(we.uid)) selected.delete(we.uid); else selected.add(we.uid); draw(); };
      list.appendChild(item);
    });
    document.getElementById('gpCancel').onclick = closeModal;
    document.getElementById('gpConfirm').onclick = () => {
      if (selected.size < 2) { toast('Selecione ao menos 2 exercícios.'); return; }
      const groupId = uid();
      const firstIdx = aw.exercises.findIndex(we => selected.has(we.uid));
      const chosen = aw.exercises.filter(we => selected.has(we.uid));
      chosen.forEach(we => { we.groupId = groupId; });
      const remaining = aw.exercises.filter(we => !selected.has(we.uid));
      const insertPos = aw.exercises.slice(0, firstIdx).filter(we => !selected.has(we.uid)).length;
      remaining.splice(insertPos, 0, ...chosen);
      aw.exercises = remaining;
      saveState(); closeModal(); render(); toast('Exercícios agrupados');
    };
  };
  draw();
}

let activeTimerInterval = null;

function startActiveTimer() {
  stopActiveTimer();
  const tick = () => {
    const el = document.getElementById('activeTimer');
    if (!el || !state.activeWorkout) { stopActiveTimer(); return; }
    const sec = Math.floor((Date.now() - state.activeWorkout.startedAt) / 1000);
    el.textContent = formatDuration(sec);
  };
  tick();
  activeTimerInterval = setInterval(tick, 1000);
}

function stopActiveTimer() { if (activeTimerInterval) { clearInterval(activeTimerInterval); activeTimerInterval = null; } }

function openFinishWorkoutModal() {
  const aw = state.activeWorkout;
  const durationSec = Math.floor((Date.now() - aw.startedAt) / 1000);
  const vol = workoutVolume(aw);
  const sets = workoutSetCount(aw);
  openModal(`
    <div class="modal-title">Finalizar Treino</div>
    <label class="field-label">Nome do treino</label>
    <input id="fName" type="text" value="${esc(aw.name)}">
    <label class="field-label">Notas (opcional)</label>
    <textarea id="fNotes" rows="3" placeholder="Como foi o treino?">${esc(aw.notes || '')}</textarea>
    <div class="stats-row" style="margin-top:16px;">
      <div class="stat-box"><div class="stat-num">${formatDuration(durationSec)}</div><div class="stat-label">Duração</div></div>
      <div class="stat-box"><div class="stat-num">${sets}</div><div class="stat-label">Séries</div></div>
      <div class="stat-box"><div class="stat-num">${Math.round(vol).toLocaleString('pt-BR')}</div><div class="stat-label">Volume ${unitLabel()}</div></div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost" style="flex:1" id="fCancel">Voltar</button>
      <button class="btn btn-primary" style="flex:2" id="fSave">Salvar Treino</button>
    </div>
  `);
  document.getElementById('fCancel').onclick = closeModal;
  document.getElementById('fSave').onclick = () => {
    aw.name = document.getElementById('fName').value.trim() || 'Treino';
    aw.notes = document.getElementById('fNotes').value.trim();
    aw.date = todayISO();
    aw.durationSec = durationSec;
    aw.exercises = aw.exercises.filter(we => we.sets.some(s => s.completed));
    aw.exercises.forEach(we => { we.sets = we.sets.filter(s => s.completed); });
    if (!aw.exercises.length) { toast('Registre ao menos uma série antes de finalizar.'); return; }
    state.workouts.unshift(aw);
    stopActiveTimer();
    stopRestTimer();
    state.activeWorkout = null;
    saveState();
    closeModal();
    ui.tab = 'historico';
    ui.historyDetailId = aw.id;
    render();
    window.scrollTo(0, 0);
    toast('Treino salvo');
  };
}
