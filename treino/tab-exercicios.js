/* ===================== TAB: EXERCÍCIOS ===================== */
function renderExerciciosTab(main) {
  if (ui.exerciseDetailId) { renderExerciseDetail(main, ui.exerciseDetailId); return; }

  main.appendChild(buildExerciseSearchInput());
  main.appendChild(buildMuscleFilterChips());

  const listCard = document.createElement('div');
  listCard.className = 'card';
  listCard.id = 'exListCard';
  main.appendChild(listCard);
  renderExerciseListCard(listCard);

  main.appendChild(buildNewExerciseButton());
}

function buildExerciseSearchInput() {
  const search = document.createElement('input');
  search.className = 'search-box';
  search.type = 'text';
  search.placeholder = 'Buscar exercício...';
  search.value = ui.exFilterQuery;
  search.oninput = () => {
    ui.exFilterQuery = search.value;
    renderExerciseListCard(document.getElementById('exListCard'));
  };
  return search;
}

function buildMuscleFilterChips() {
  const chips = document.createElement('div');
  chips.className = 'chip-row';
  ['Todos', ...MUSCLE_GROUPS].forEach(m => {
    const chip = document.createElement('button');
    chip.className = 'chip' + (ui.exFilterMuscle === m ? ' active' : '');
    chip.textContent = m;
    chip.onclick = () => { ui.exFilterMuscle = m; render(); };
    chips.appendChild(chip);
  });
  return chips;
}

function buildNewExerciseButton() {
  const newExBtn = document.createElement('button');
  newExBtn.className = 'btn btn-ghost btn-block';
  newExBtn.style.marginTop = '14px';
  newExBtn.textContent = '+ Criar novo exercício';
  newExBtn.onclick = () => { openModalNewExerciseStandalone(); };
  return newExBtn;
}

function renderExerciseListCard(listCard) {
  listCard.innerHTML = '';
  const filtered = state.exercises.filter(e =>
    (ui.exFilterMuscle === 'Todos' || e.muscle === ui.exFilterMuscle) &&
    e.name.toLowerCase().includes(ui.exFilterQuery.toLowerCase())
  ).sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'));
  if (!filtered.length) { listCard.appendChild(makeEmpty('Nenhum exercício encontrado.')); return; }
  filtered.forEach(e => listCard.appendChild(buildExerciseListItem(e)));
}

function buildExerciseListItem(e) {
  const item = document.createElement('div');
  item.className = 'ex-list-item';
  const pr = getExercisePR(e.id);
  item.innerHTML = `
    <div><div class="ex-list-name">${esc(e.name)}</div><div class="ex-list-muscle">${esc(e.muscle)} · ${esc(e.equipment)}</div></div>
    <div class="mono" style="font-size:11px;color:var(--muted);">${pr.maxWeight ? pr.maxWeight + unitLabel() : ''}</div>
  `;
  item.onclick = () => { ui.exerciseDetailId = e.id; ui.instructionsExpanded = false; render(); window.scrollTo(0,0); };
  return item;
}

function openModalNewExerciseStandalone() {
  openModal(`
    <div class="modal-title">Novo Exercício</div>
    <label class="field-label">Nome</label>
    <input id="neName2" type="text" placeholder="Ex: Supino Declinado">
    <label class="field-label">Grupo muscular</label>
    <select id="neMuscle2">${MUSCLE_GROUPS.map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('')}</select>
    <label class="field-label">Equipamento</label>
    <select id="neEquip2">${['Barra','Halteres','Máquina','Cabo','Peso Corporal','Cardio','Outro'].map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('')}</select>
    <div class="modal-footer">
      <button class="btn btn-ghost" style="flex:1" id="neCancel2">Cancelar</button>
      <button class="btn btn-primary" style="flex:2" id="neSave2">Criar</button>
    </div>
  `);
  document.getElementById('neCancel2').onclick = closeModal;
  document.getElementById('neSave2').onclick = () => {
    const name = document.getElementById('neName2').value.trim();
    if (!name) { toast('Informe um nome para o exercício.'); return; }
    state.exercises.push({ id: uid(), name, muscle: document.getElementById('neMuscle2').value, equipment: document.getElementById('neEquip2').value, custom: true });
    saveState(); closeModal(); render(); toast('Exercício criado');
  };
}

let exerciseAnimTimer = null;

function stopExerciseAnim() { if (exerciseAnimTimer) { clearInterval(exerciseAnimTimer); exerciseAnimTimer = null; } }

function renderExerciseDetail(main, exerciseId) {
  const ex = getExercise(exerciseId);
  if (!ex) { ui.exerciseDetailId = null; renderExerciciosTab(main); return; }

  main.appendChild(buildExerciseDetailBackButton());
  if (ex.hasImages) main.appendChild(buildExerciseDemoCard(ex));
  main.appendChild(buildExerciseTitleCard(ex));
  if (ex.instructions && ex.instructions.length) main.appendChild(buildExerciseInstructionsCard(ex));
  main.appendChild(buildExerciseInfoCard(ex));
  main.appendChild(buildExerciseRestPrefCard(ex));
  main.appendChild(buildExercisePRCard(exerciseId));
  main.appendChild(buildExerciseChartCard(exerciseId));
  main.appendChild(buildExerciseHistoryCard(exerciseId));
  if (ex.custom) main.appendChild(buildExerciseDeleteButton(ex, exerciseId));
}

function buildExerciseDetailBackButton() {
  const back = document.createElement('button');
  back.className = 'btn btn-ghost btn-sm';
  back.style.marginBottom = '14px';
  back.textContent = '← Voltar';
  back.onclick = () => { stopExerciseAnim(); ui.exerciseDetailId = null; render(); };
  return back;
}

// Demonstração do exercício: uma imagem parada, com um botão que alterna entre
// dois quadros (0.jpg/1.jpg) num intervalo, simulando uma animação sem vídeo.
function buildExerciseDemoCard(ex) {
  const imgCard = document.createElement('div');
  imgCard.className = 'card';
  imgCard.innerHTML = `
    <div class="ex-demo-wrap">
      <img class="ex-demo-img" id="exDemoImg" src="exercises/${esc(ex.id)}/0.jpg" alt="${esc(ex.name)}">
      <button class="ex-demo-play" id="exDemoPlay" title="Reproduzir demonstração">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
      </button>
    </div>
  `;
  const imgEl = imgCard.querySelector('#exDemoImg');
  const playBtn = imgCard.querySelector('#exDemoPlay');
  stopExerciseAnim();
  const PLAY_ICON = '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';
  const PAUSE_ICON = '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>';
  playBtn.onclick = () => {
    if (exerciseAnimTimer) {
      stopExerciseAnim();
      imgEl.src = `exercises/${ex.id}/0.jpg`;
      playBtn.classList.remove('playing');
      playBtn.innerHTML = PLAY_ICON;
      return;
    }
    playBtn.classList.add('playing');
    playBtn.innerHTML = PAUSE_ICON;
    let frame = 0;
    exerciseAnimTimer = setInterval(() => {
      frame = 1 - frame;
      imgEl.src = `exercises/${ex.id}/${frame}.jpg`;
    }, 650);
  };
  return imgCard;
}

function buildExerciseTitleCard(ex) {
  const titleCard = document.createElement('div');
  titleCard.className = 'card card-pad';
  titleCard.innerHTML = `<div class="history-name" style="font-size:19px;">${esc(ex.name)}</div>`;
  return titleCard;
}

function buildExerciseInstructionsCard(ex) {
  const insCard = document.createElement('div');
  insCard.className = 'card card-pad';
  const shown = ui.instructionsExpanded ? ex.instructions : ex.instructions.slice(0, 1);
  insCard.innerHTML = `
    <div class="ex-card-title" style="margin-bottom:10px;">Instruções</div>
    <ol class="ex-instructions-list">${shown.map(s => `<li>${esc(s)}</li>`).join('')}</ol>
    ${ex.instructions.length > 1 ? `<button class="btn btn-ghost btn-sm" id="insToggle" style="margin-top:8px;">${ui.instructionsExpanded ? '▲ Menos' : '▼ Mais'}</button>` : ''}
  `;
  const insToggle = insCard.querySelector('#insToggle');
  if (insToggle) insToggle.onclick = () => { ui.instructionsExpanded = !ui.instructionsExpanded; render(); };
  return insCard;
}

function buildExerciseInfoCard(ex) {
  const infoCard = document.createElement('div');
  infoCard.className = 'card card-pad';
  infoCard.innerHTML = `
    <div class="ex-info-row"><span class="ex-card-title">Parte do corpo</span><span class="mono" style="color:var(--muted);">${esc(ex.muscle)}</span></div>
    <div class="ex-info-row"><span class="ex-card-title">Categoria</span><span class="mono" style="color:var(--muted);">${esc(ex.equipment)}</span></div>
  `;
  return infoCard;
}

function buildExerciseRestPrefCard(ex) {
  const prefCard = document.createElement('div');
  prefCard.className = 'card card-pad';
  const restOptions = [null, 30, 60, 90, 120, 180];
  prefCard.innerHTML = `
    <div class="ex-card-title" style="margin-bottom:4px;">Preferências</div>
    <div class="toggle-row" style="border-bottom:none;">
      <span>Temporizador de Descanso</span>
    </div>
    <div class="seg" id="exRestSeg" style="flex-wrap:wrap;">
      ${restOptions.map(v => `<button data-v="${v ?? ''}" class="${(ex.restOverride || null) === v ? 'on' : ''}">${v ? formatDuration(v) : 'Padrão'}</button>`).join('')}
    </div>
  `;
  prefCard.querySelectorAll('#exRestSeg button').forEach(b => b.onclick = () => {
    ex.restOverride = b.dataset.v ? Number(b.dataset.v) : null;
    saveState(); render();
  });
  return prefCard;
}

function buildExercisePRCard(exerciseId) {
  const head = document.createElement('div');
  head.className = 'card card-pad';
  const pr = getExercisePR(exerciseId);
  head.innerHTML = `
    <div class="pr-grid" style="margin-bottom:0;">
      <div class="stat-box"><div class="stat-num">${pr.maxWeight ? pr.maxWeight + unitLabel() : '—'}</div><div class="stat-label">Recorde de Carga</div></div>
      <div class="stat-box"><div class="stat-num">${pr.best1rm ? Math.round(pr.best1rm) + unitLabel() : '—'}</div><div class="stat-label">1RM Estimado</div></div>
    </div>
  `;
  return head;
}

function buildExerciseChartCard(exerciseId) {
  const workouts = getExerciseWorkouts(exerciseId).slice().reverse();
  const points = [];
  workouts.forEach(w => {
    const we = w.exercises.find(e => e.exerciseId === exerciseId);
    const maxSet = (we.sets || []).filter(s => s.completed && !s.warmup && s.weight).sort((a,b) => Number(b.weight) - Number(a.weight))[0];
    if (maxSet) points.push({ date: w.date, value: Number(maxSet.weight) });
  });

  const chartCard = document.createElement('div');
  chartCard.className = 'card';
  chartCard.style.marginTop = '12px';
  chartCard.innerHTML = `<div class="ex-card-head"><div class="ex-card-title">Progressão de Carga</div></div><div class="chart-wrap" id="chartWrap"></div>`;
  const chartWrap = chartCard.querySelector('#chartWrap');
  if (points.length < 2) {
    chartWrap.appendChild(makeEmpty('Registre esse exercício em pelo menos 2 treinos para ver o gráfico de progresso.'));
  } else {
    chartWrap.innerHTML = renderLineChartSVG(points, unitLabel());
  }
  return chartCard;
}

function buildExerciseHistoryCard(exerciseId) {
  const histCard = document.createElement('div');
  histCard.className = 'card';
  histCard.style.marginTop = '12px';
  const rowsHtml = getExerciseWorkouts(exerciseId).map(w => {
    const we = w.exercises.find(e => e.exerciseId === exerciseId);
    const setsTxt = we.sets.filter(s => s.completed).map(s => `${s.warmup ? 'W:' : ''}${s.weight}${unitLabel()}×${s.reps}`).join(', ');
    return `<div class="set-history-row"><span class="set-history-date">${esc(formatDateShort(w.date))}</span><span>${esc(setsTxt)}</span></div>`;
  }).join('');
  histCard.innerHTML = `<div class="ex-card-head"><div class="ex-card-title">Histórico</div></div>${rowsHtml || '<div class="set-history-row"><span>Nenhum registro ainda</span></div>'}`;
  return histCard;
}

function buildExerciseDeleteButton(ex, exerciseId) {
  const delBtn = document.createElement('button');
  delBtn.className = 'btn btn-danger btn-block';
  delBtn.style.marginTop = '14px';
  delBtn.textContent = 'Excluir Exercício';
  delBtn.onclick = () => {
    confirmDialog(`Excluir o exercício "${ex.name}"? O histórico registrado com ele será mantido.`, () => {
      state.exercises = state.exercises.filter(e => e.id !== exerciseId);
      saveState(); ui.exerciseDetailId = null; render(); toast('Exercício excluído');
    });
  };
  return delBtn;
}
