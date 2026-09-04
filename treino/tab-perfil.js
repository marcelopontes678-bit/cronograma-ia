/* ===================== TAB: PERFIL ===================== */
function renderPerfilTab(main) {
  if (ui.showMeasurements) { renderMeasurementsView(main); return; }

  const card = document.createElement('div');
  card.className = 'card card-pad';
  card.innerHTML = `
    <div class="toggle-row">
      <span>Tema</span>
      <div class="seg" id="themeSeg">
        <button data-t="dark" class="${state.settings.theme === 'dark' ? 'on' : ''}">Escuro</button>
        <button data-t="light" class="${state.settings.theme === 'light' ? 'on' : ''}">Claro</button>
        <button data-t="system" class="${state.settings.theme === 'system' ? 'on' : ''}">Sistema</button>
      </div>
    </div>
    <div class="toggle-row">
      <span>Unidade de peso</span>
      <div class="seg" id="unitSeg">
        <button data-u="kg" class="${state.settings.unit === 'kg' ? 'on' : ''}">KG</button>
        <button data-u="lb" class="${state.settings.unit === 'lb' ? 'on' : ''}">LB</button>
      </div>
    </div>
    <div class="toggle-row">
      <span>Timer de descanso padrão</span>
      <div class="seg" id="restSeg">
        ${[60,90,120,180].map(s => `<button data-s="${s}" class="${state.settings.restDefault===s?'on':''}">${s}s</button>`).join('')}
      </div>
    </div>
    <div class="toggle-row">
      <span>Peso da barra padrão (${unitLabel()})</span>
      <input id="barWeightInput" type="number" inputmode="decimal" style="max-width:80px;text-align:center;" value="${state.settings.barWeight}">
    </div>
    <p style="font-size:11px;color:var(--muted);margin-top:10px;line-height:1.6;">Alterar a unidade não converte os pesos já registrados — serve apenas para novos registros.</p>
  `;
  main.appendChild(card);
  card.querySelectorAll('#themeSeg button').forEach(b => b.onclick = () => { state.settings.theme = b.dataset.t; saveState(); applyTheme(); render(); });
  card.querySelectorAll('#unitSeg button').forEach(b => b.onclick = () => { state.settings.unit = b.dataset.u; saveState(); render(); });
  card.querySelectorAll('#restSeg button').forEach(b => b.onclick = () => { state.settings.restDefault = Number(b.dataset.s); saveState(); render(); });
  document.getElementById('barWeightInput').oninput = (e) => { state.settings.barWeight = Number(e.target.value) || 0; saveState(); };

  const measureBtn = document.createElement('button');
  measureBtn.className = 'btn btn-ghost btn-block';
  measureBtn.style.marginTop = '12px';
  measureBtn.textContent = '📏 Medidas Corporais';
  measureBtn.onclick = () => { ui.showMeasurements = true; render(); window.scrollTo(0, 0); };
  main.appendChild(measureBtn);

  const dataTitle = document.createElement('div');
  dataTitle.className = 'section-title';
  dataTitle.textContent = 'Dados';
  main.appendChild(dataTitle);

  const dataCard = document.createElement('div');
  dataCard.className = 'card card-pad';
  dataCard.style.display = 'flex';
  dataCard.style.flexDirection = 'column';
  dataCard.style.gap = '10px';
  dataCard.innerHTML = `
    <button class="btn btn-ghost btn-block" id="btnExport">Exportar dados (JSON)</button>
    <button class="btn btn-ghost btn-block" id="btnImport">Importar dados (JSON)</button>
    <input type="file" id="fileImport" accept="application/json" style="display:none;">
    <button class="btn btn-danger btn-block" id="btnReset">Apagar todos os dados</button>
  `;
  main.appendChild(dataCard);

  document.getElementById('btnExport').onclick = () => {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `treino-backup-${new Date().toISOString().slice(0,10)}.json`;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    toast('Backup exportado');
  };
  document.getElementById('btnImport').onclick = () => document.getElementById('fileImport').click();
  document.getElementById('fileImport').onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result);
        const validationError = validateImportedState(data);
        if (validationError) throw new Error(validationError);
        confirmDialog('Importar estes dados vai substituir tudo que existe atualmente. Continuar?', () => {
          state = data;
          state.activeWorkout = state.activeWorkout || null;
          saveState(); render(); toast('Dados importados');
        });
      } catch (err) { toast('Arquivo inválido: ' + err.message); }
    };
    reader.readAsText(file);
    e.target.value = '';
  };
  document.getElementById('btnReset').onclick = () => {
    confirmDialog('Isso vai apagar TODOS os treinos, rotinas e exercícios personalizados permanentemente. Tem certeza?', () => {
      state = defaultState();
      saveState(); render(); toast('Dados apagados');
    });
  };

  const about = document.createElement('div');
  about.style.marginTop = '22px';
  about.style.textAlign = 'center';
  about.style.color = 'var(--muted)';
  about.style.fontSize = '11px';
  about.style.lineHeight = '1.7';
  about.innerHTML = `Gibor — diário de treino inspirado no Strong.<br>Todos os dados ficam salvos apenas neste dispositivo.`;
  main.appendChild(about);
}

function renderMeasurementsView(main) {
  const back = document.createElement('button');
  back.className = 'btn btn-ghost btn-sm';
  back.style.marginBottom = '14px';
  back.textContent = '← Voltar';
  back.onclick = () => { ui.showMeasurements = false; render(); };
  main.appendChild(back);

  const formCard = document.createElement('div');
  formCard.className = 'card card-pad';
  const today = new Date().toISOString().split('T')[0];
  formCard.innerHTML = `
    <div class="ex-card-title" style="margin-bottom:12px;">Novo Registro</div>
    <label class="field-label">Data</label>
    <input id="mDate" type="date" value="${today}">
    <div class="measure-form-grid" style="margin-top:10px;">
      <div>
        <label class="field-label">Peso Corporal (${unitLabel()})</label>
        <input id="mWeight" type="number" inputmode="decimal" placeholder="0">
      </div>
      <div>
        <label class="field-label">% Gordura</label>
        <input id="mBodyFat" type="number" inputmode="decimal" placeholder="0">
      </div>
    </div>
    <label class="field-label" style="margin-top:14px;">Medidas (cm) — opcional</label>
    <div class="measure-form-grid">
      ${MEASURE_FIELDS.map(f => `<input id="m_${f.key}" type="number" inputmode="decimal" placeholder="${f.label}">`).join('')}
    </div>
    <button class="btn btn-primary btn-block" id="mSave" style="margin-top:14px;">Salvar Registro</button>
  `;
  main.appendChild(formCard);
  document.getElementById('mSave').onclick = () => {
    const weight = document.getElementById('mWeight').value;
    const bodyFat = document.getElementById('mBodyFat').value;
    const entry = { id: uid(), date: document.getElementById('mDate').value || today, weight, bodyFat };
    MEASURE_FIELDS.forEach(f => { entry[f.key] = document.getElementById(`m_${f.key}`).value; });
    if (!weight && !bodyFat && !MEASURE_FIELDS.some(f => entry[f.key])) { toast('Preencha ao menos um valor.'); return; }
    state.bodyMeasurements.push(entry);
    saveState(); render(); window.scrollTo(0, 0); toast('Registro salvo');
  };

  const weightPoints = state.bodyMeasurements
    .filter(m => m.weight)
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .map(m => ({ date: m.date, value: Number(m.weight) }));
  if (weightPoints.length >= 2) {
    const chartCard = document.createElement('div');
    chartCard.className = 'card';
    chartCard.style.marginTop = '12px';
    chartCard.innerHTML = `<div class="ex-card-head"><div class="ex-card-title">Progressão do Peso Corporal</div></div><div class="chart-wrap">${renderLineChartSVG(weightPoints, unitLabel())}</div>`;
    main.appendChild(chartCard);
  }

  const listCard = document.createElement('div');
  listCard.className = 'card';
  listCard.style.marginTop = '12px';
  const sorted = [...state.bodyMeasurements].sort((a, b) => new Date(b.date) - new Date(a.date));
  if (!sorted.length) {
    listCard.appendChild(makeEmpty('Nenhum registro ainda.'));
  } else {
    sorted.forEach(m => {
      const detailParts = [];
      if (m.bodyFat) detailParts.push(`${m.bodyFat}% gordura`);
      MEASURE_FIELDS.forEach(f => { if (m[f.key]) detailParts.push(`${f.label}: ${m[f.key]}cm`); });
      const row = document.createElement('div');
      row.className = 'measure-entry';
      row.innerHTML = `
        <div>
          <div class="measure-entry-date">${esc(formatDateShort(m.date))}</div>
          <div class="measure-entry-detail">${m.weight ? `${m.weight}${unitLabel()}` : ''}${detailParts.length ? (m.weight ? ' · ' : '') + esc(detailParts.join(' · ')) : ''}</div>
        </div>
        <button class="icon-btn" style="width:28px;height:28px;color:var(--red);flex-shrink:0;">✕</button>
      `;
      row.querySelector('button').onclick = () => {
        confirmDialog('Excluir este registro?', () => {
          state.bodyMeasurements = state.bodyMeasurements.filter(x => x.id !== m.id);
          saveState(); render();
        });
      };
      listCard.appendChild(row);
    });
  }
  main.appendChild(listCard);
}

/* ===================== TEMA ===================== */
function applyTheme() {
  const t = state.settings.theme;
  if (t === 'system') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', t);
}
