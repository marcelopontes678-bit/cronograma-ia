/* ===================== SELETOR DE EXERCÍCIOS (modal) ===================== */
let picker = { selected: new Set(), query: '', muscle: 'Todos', onConfirm: null, confirmLabel: 'Adicionar' };

function openExercisePicker(onConfirm, opts) {
  picker = { selected: new Set(), query: '', muscle: 'Todos', onConfirm, confirmLabel: (opts && opts.confirmLabel) || 'Adicionar' };
  renderExercisePicker(opts && opts.title || 'Selecionar Exercícios');
}

function renderExercisePicker(title) {
  const muscles = ['Todos', ...MUSCLE_GROUPS];
  openModal(`
    <div class="modal-title">${esc(title)}</div>
    <input class="search-box" id="pickerSearch" type="text" placeholder="Buscar exercício..." value="${esc(picker.query)}">
    <div class="chip-row" id="pickerChips">
      ${muscles.map(m => `<button class="chip ${m === picker.muscle ? 'active' : ''}" data-m="${esc(m)}">${esc(m)}</button>`).join('')}
    </div>
    <div class="card" id="pickerList" style="max-height:42vh;overflow-y:auto;"></div>
    <button class="btn btn-ghost btn-block" id="pickerNewEx" style="margin-top:12px;">+ Criar novo exercício</button>
    <div class="modal-footer">
      <button class="btn btn-ghost" style="flex:1" id="pickerCancel">Cancelar</button>
      <button class="btn btn-primary" style="flex:2" id="pickerConfirm">${picker.confirmLabel} (${picker.selected.size})</button>
    </div>
  `);
  // A busca só atualiza a lista de resultados (updatePickerResults), nunca reconstrói
  // o modal inteiro — recriar o <input> a cada tecla jogava o cursor de volta pro início.
  document.getElementById('pickerSearch').oninput = (ev) => { picker.query = ev.target.value; updatePickerResults(title); };
  document.getElementById('pickerCancel').onclick = closeModal;
  document.getElementById('pickerConfirm').onclick = () => {
    if (!picker.selected.size) { toast('Selecione ao menos um exercício.'); return; }
    picker.onConfirm(Array.from(picker.selected));
  };
  document.getElementById('pickerNewEx').onclick = () => openNewExerciseForm(title);
  updatePickerResults(title);
}

function updatePickerResults(title) {
  const filtered = state.exercises.filter(e =>
    (picker.muscle === 'Todos' || e.muscle === picker.muscle) &&
    e.name.toLowerCase().includes(picker.query.toLowerCase())
  );
  const list = document.getElementById('pickerList');
  list.innerHTML = '';
  if (!filtered.length) {
    list.appendChild(makeEmpty('Nenhum exercício encontrado.'));
  } else {
    filtered.forEach(e => {
      const item = document.createElement('div');
      item.className = 'ex-list-item';
      const on = picker.selected.has(e.id);
      item.innerHTML = `
        <div><div class="ex-list-name">${esc(e.name)}</div><div class="ex-list-muscle">${esc(e.muscle)} · ${esc(e.equipment)}</div></div>
        <div class="ex-list-check ${on ? 'on' : ''}">${on ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M4 12l5 5L20 6"/></svg>' : ''}</div>
      `;
      item.onclick = () => {
        if (picker.selected.has(e.id)) picker.selected.delete(e.id); else picker.selected.add(e.id);
        updatePickerResults(title);
      };
      list.appendChild(item);
    });
  }
  document.querySelectorAll('#pickerChips .chip').forEach(chip => {
    chip.classList.toggle('active', chip.dataset.m === picker.muscle);
    chip.onclick = () => { picker.muscle = chip.dataset.m; updatePickerResults(title); };
  });
  const confirmBtn = document.getElementById('pickerConfirm');
  if (confirmBtn) confirmBtn.textContent = `${picker.confirmLabel} (${picker.selected.size})`;
}

function openNewExerciseForm(returnTitle) {
  openModal(`
    <div class="modal-title">Novo Exercício</div>
    <label class="field-label">Nome</label>
    <input id="neName" type="text" placeholder="Ex: Supino Declinado">
    <label class="field-label">Grupo muscular</label>
    <select id="neMuscle">${MUSCLE_GROUPS.map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('')}</select>
    <label class="field-label">Equipamento</label>
    <select id="neEquip">${['Barra','Halteres','Máquina','Cabo','Peso Corporal','Cardio','Outro'].map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('')}</select>
    <div class="modal-footer">
      <button class="btn btn-ghost" style="flex:1" id="neCancel">Cancelar</button>
      <button class="btn btn-primary" style="flex:2" id="neSave">Criar</button>
    </div>
  `);
  document.getElementById('neCancel').onclick = () => renderExercisePicker(returnTitle);
  document.getElementById('neSave').onclick = () => {
    const name = document.getElementById('neName').value.trim();
    if (!name) { toast('Informe um nome para o exercício.'); return; }
    const ex = { id: uid(), name, muscle: document.getElementById('neMuscle').value, equipment: document.getElementById('neEquip').value, custom: true };
    state.exercises.push(ex);
    saveState();
    picker.selected.add(ex.id);
    renderExercisePicker(returnTitle);
  };
}
