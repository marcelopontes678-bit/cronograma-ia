/* ===================== EDITOR DE ROTINA ===================== */
let routineDraft = null;

function openRoutineEditor(routineId) {
  const existing = routineId ? state.routines.find(r => r.id === routineId) : null;
  routineDraft = existing
    ? { id: existing.id, name: existing.name, exercises: existing.exercises.map(x => ({ ...x })) }
    : { id: uid(), name: '', exercises: [] };
  renderRoutineEditor();
}

function renderRoutineEditor() {
  const musclesInRoutine = new Set(routineDraft.exercises.map(x => { const ex = getExercise(x.exerciseId); return ex ? ex.muscle : null; }).filter(Boolean));
  openModal(`
    <div class="modal-title">${routineDraft.name ? 'Editar Rotina' : 'Nova Rotina'}</div>
    ${musclesInRoutine.size ? `<div class="body-diagram-wrap">${bodyDiagramSVG(musclesInRoutine)}</div>` : ''}
    <label class="field-label">Nome da rotina</label>
    <input id="rName" type="text" placeholder="Ex: Treino A — Push" value="${esc(routineDraft.name)}">
    <label class="field-label">Exercícios</label>
    <div id="rExList"></div>
    <button class="btn btn-ghost btn-block" id="rAddEx" style="margin-top:10px;">+ Adicionar Exercício</button>
    <div class="modal-footer">
      <button class="btn btn-ghost" style="flex:1" id="rCancel">Cancelar</button>
      <button class="btn btn-primary" style="flex:2" id="rSave">Salvar Rotina</button>
    </div>
  `);
  const list = document.getElementById('rExList');
  if (!routineDraft.exercises.length) {
    list.appendChild(makeEmpty('Nenhum exercício adicionado.'));
  } else {
    routineDraft.exercises.forEach((x) => {
      const ex = getExercise(x.exerciseId);
      const row = document.createElement('div');
      row.className = 'card routine-editor-row drag-row';
      row.dataset.id = x.exerciseId;
      const repsLabel = x.repsMin && x.repsMax ? `${x.repsMin}-${x.repsMax} Wdh` : (x.repsMin ? `${x.repsMin} Wdh` : '— Wdh');
      row.innerHTML = `
        <button class="drag-handle" title="Arrastar para reordenar">≡</button>
        <div class="routine-editor-row-info">
          <div class="ex-list-name">${esc(ex ? ex.name : '?')}</div>
          <div class="ex-list-muscle">${esc(ex ? ex.muscle : '')}</div>
          <div class="routine-chip-row">
            <span class="routine-chip" data-act="sets">${x.targetSets} Séries</span>
            <span class="routine-chip" data-act="reps">${esc(repsLabel)}</span>
          </div>
        </div>
        <button class="icon-btn" data-act="del" style="width:28px;height:28px;color:var(--red);flex-shrink:0;">✕</button>
      `;
      row.querySelector('[data-act="sets"]').onclick = () => openStepperEditor('Número de Séries', x.targetSets, { min: 1, max: 10 }, v => { x.targetSets = v; renderRoutineEditor(); });
      row.querySelector('[data-act="reps"]').onclick = () => openRepRangeEditor(x, () => renderRoutineEditor());
      const removeRow = () => { routineDraft.exercises = routineDraft.exercises.filter(e => e !== x); renderRoutineEditor(); };
      row.querySelector('[data-act="del"]').onclick = removeRow;
      enableSwipeToDelete(row, removeRow, '.drag-handle');
      list.appendChild(row);
    });
    if (routineDraft.exercises.length >= 2) {
      enableDragReorder(list, ids => {
        routineDraft.exercises = ids.map(id => routineDraft.exercises.find(x => x.exerciseId === id)).filter(Boolean);
        renderRoutineEditor();
      });
    }
  }
  document.getElementById('rName').oninput = (e) => { routineDraft.name = e.target.value; };
  document.getElementById('rAddEx').onclick = () => {
    openExercisePicker(ids => {
      ids.forEach(id => { if (!routineDraft.exercises.some(x => x.exerciseId === id)) routineDraft.exercises.push({ exerciseId: id, targetSets: 3, repsMin: '', repsMax: '' }); });
      renderRoutineEditor();
    }, { title: 'Adicionar Exercícios' });
  };
  document.getElementById('rCancel').onclick = closeModal;
  document.getElementById('rSave').onclick = () => {
    const name = document.getElementById('rName').value.trim();
    if (!name) { toast('Dê um nome para a rotina.'); return; }
    if (!routineDraft.exercises.length) { toast('Adicione ao menos um exercício.'); return; }
    routineDraft.name = name;
    const idx = state.routines.findIndex(r => r.id === routineDraft.id);
    if (idx >= 0) state.routines[idx] = routineDraft; else state.routines.push(routineDraft);
    saveState(); closeModal(); render(); toast('Rotina salva');
  };
}

function openStepperEditor(title, value, range, onSave) {
  const { min, max } = range;
  let v = value;
  const draw = () => {
    openModal(`
      <div class="modal-title">${esc(title)}</div>
      <div class="stepper-big">
        <button class="icon-btn" id="stMinus" style="width:44px;height:44px;">−</button>
        <span class="mono stepper-big-value">${v}</span>
        <button class="icon-btn" id="stPlus" style="width:44px;height:44px;">+</button>
      </div>
      <div class="modal-footer">
        <button class="btn btn-primary btn-block" id="stSave">Confirmar</button>
      </div>
    `);
    document.getElementById('stMinus').onclick = () => { v = Math.max(min, v - 1); draw(); };
    document.getElementById('stPlus').onclick = () => { v = Math.min(max, v + 1); draw(); };
    document.getElementById('stSave').onclick = () => { onSave(v); };
  };
  draw();
}

function openRepRangeEditor(x, onSave) {
  openModal(`
    <div class="modal-title">Faixa de Repetições</div>
    <div style="display:flex;gap:10px;">
      <div class="field-group" style="flex:1;">
        <label class="field-label">Mínimo</label>
        <input id="repMin" type="number" inputmode="numeric" value="${x.repsMin || ''}" placeholder="Ex: 8">
      </div>
      <div class="field-group" style="flex:1;">
        <label class="field-label">Máximo</label>
        <input id="repMax" type="number" inputmode="numeric" value="${x.repsMax || ''}" placeholder="Ex: 12">
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost" style="flex:1" id="rrClear">Limpar</button>
      <button class="btn btn-primary" style="flex:2" id="rrSave">Confirmar</button>
    </div>
  `);
  document.getElementById('rrClear').onclick = () => { x.repsMin = ''; x.repsMax = ''; closeModal(); onSave(); };
  document.getElementById('rrSave').onclick = () => {
    x.repsMin = document.getElementById('repMin').value;
    x.repsMax = document.getElementById('repMax').value;
    closeModal(); onSave();
  };
}
