/* ===================== TREINO — app inspirado no Strong ===================== */
const STORAGE_KEY = 'treino_app_v1';

const MUSCLE_GROUPS = ['Peito','Costas','Pernas','Ombros','Bíceps','Tríceps','Abdômen','Cardio','Outro'];

const SEED_EXERCISES = [
  { id:'supino-reto-barra', name:'Supino Reto (Barra)', muscle:'Peito', equipment:'Barra' },
  { id:'supino-inclinado-barra', name:'Supino Inclinado (Barra)', muscle:'Peito', equipment:'Barra' },
  { id:'supino-halteres', name:'Supino Reto (Halteres)', muscle:'Peito', equipment:'Halteres' },
  { id:'crucifixo-halteres', name:'Crucifixo (Halteres)', muscle:'Peito', equipment:'Halteres' },
  { id:'crossover', name:'Crossover (Cabo)', muscle:'Peito', equipment:'Cabo' },
  { id:'flexao-braco', name:'Flexão de Braço', muscle:'Peito', equipment:'Peso Corporal' },
  { id:'puxada-frontal', name:'Puxada Frontal (Pulley)', muscle:'Costas', equipment:'Cabo' },
  { id:'remada-curvada', name:'Remada Curvada (Barra)', muscle:'Costas', equipment:'Barra' },
  { id:'remada-baixa', name:'Remada Baixa (Cabo)', muscle:'Costas', equipment:'Cabo' },
  { id:'barra-fixa', name:'Barra Fixa (Pull-up)', muscle:'Costas', equipment:'Peso Corporal' },
  { id:'levantamento-terra', name:'Levantamento Terra', muscle:'Costas', equipment:'Barra' },
  { id:'remada-unilateral', name:'Remada Unilateral (Halter)', muscle:'Costas', equipment:'Halteres' },
  { id:'agachamento-livre', name:'Agachamento Livre', muscle:'Pernas', equipment:'Barra' },
  { id:'leg-press', name:'Leg Press', muscle:'Pernas', equipment:'Máquina' },
  { id:'cadeira-extensora', name:'Cadeira Extensora', muscle:'Pernas', equipment:'Máquina' },
  { id:'mesa-flexora', name:'Mesa Flexora', muscle:'Pernas', equipment:'Máquina' },
  { id:'stiff', name:'Stiff (Barra)', muscle:'Pernas', equipment:'Barra' },
  { id:'panturrilha-pe', name:'Panturrilha em Pé', muscle:'Pernas', equipment:'Máquina' },
  { id:'afundo-halteres', name:'Afundo (Halteres)', muscle:'Pernas', equipment:'Halteres' },
  { id:'desenvolvimento-militar', name:'Desenvolvimento Militar (Barra)', muscle:'Ombros', equipment:'Barra' },
  { id:'desenvolvimento-halteres', name:'Desenvolvimento com Halteres', muscle:'Ombros', equipment:'Halteres' },
  { id:'elevacao-lateral', name:'Elevação Lateral', muscle:'Ombros', equipment:'Halteres' },
  { id:'elevacao-frontal', name:'Elevação Frontal', muscle:'Ombros', equipment:'Halteres' },
  { id:'remada-alta', name:'Remada Alta', muscle:'Ombros', equipment:'Barra' },
  { id:'rosca-direta', name:'Rosca Direta (Barra)', muscle:'Bíceps', equipment:'Barra' },
  { id:'rosca-alternada', name:'Rosca Alternada (Halteres)', muscle:'Bíceps', equipment:'Halteres' },
  { id:'rosca-martelo', name:'Rosca Martelo', muscle:'Bíceps', equipment:'Halteres' },
  { id:'rosca-scott', name:'Rosca Scott', muscle:'Bíceps', equipment:'Barra' },
  { id:'triceps-corda', name:'Tríceps Corda (Pulley)', muscle:'Tríceps', equipment:'Cabo' },
  { id:'triceps-testa', name:'Tríceps Testa', muscle:'Tríceps', equipment:'Barra' },
  { id:'triceps-frances', name:'Tríceps Francês', muscle:'Tríceps', equipment:'Halteres' },
  { id:'mergulho-paralelas', name:'Mergulho (Paralelas)', muscle:'Tríceps', equipment:'Peso Corporal' },
  { id:'abdominal-supra', name:'Abdominal Supra', muscle:'Abdômen', equipment:'Peso Corporal' },
  { id:'prancha', name:'Prancha', muscle:'Abdômen', equipment:'Peso Corporal' },
  { id:'elevacao-pernas', name:'Elevação de Pernas', muscle:'Abdômen', equipment:'Peso Corporal' },
  { id:'abdominal-polia', name:'Abdominal na Polia', muscle:'Abdômen', equipment:'Cabo' },
  { id:'esteira', name:'Esteira / Corrida', muscle:'Cardio', equipment:'Cardio' },
  { id:'bike', name:'Bicicleta Ergométrica', muscle:'Cardio', equipment:'Cardio' },
];

const SEED_ROUTINES = [
  { id:'rt-push', name:'Treino A — Superior (Push)', exercises:[
    { exerciseId:'supino-reto-barra', targetSets:4 },
    { exerciseId:'desenvolvimento-halteres', targetSets:3 },
    { exerciseId:'elevacao-lateral', targetSets:3 },
    { exerciseId:'triceps-corda', targetSets:3 },
  ]},
  { id:'rt-pull', name:'Treino B — Superior (Pull)', exercises:[
    { exerciseId:'puxada-frontal', targetSets:4 },
    { exerciseId:'remada-curvada', targetSets:3 },
    { exerciseId:'rosca-direta', targetSets:3 },
    { exerciseId:'rosca-martelo', targetSets:3 },
  ]},
  { id:'rt-legs', name:'Treino C — Inferior (Pernas)', exercises:[
    { exerciseId:'agachamento-livre', targetSets:4 },
    { exerciseId:'leg-press', targetSets:3 },
    { exerciseId:'mesa-flexora', targetSets:3 },
    { exerciseId:'panturrilha-pe', targetSets:4 },
  ]},
];

/* ---------- estado / persistência ---------- */
const PLATES_KG = [25, 20, 15, 10, 5, 2.5, 1.25];
const PLATES_LB = [45, 35, 25, 10, 5, 2.5];

function defaultState() {
  return {
    settings: { unit: 'kg', restDefault: 90, barWeight: 20, theme: 'dark' },
    exercises: SEED_EXERCISES.map(e => ({ ...e, custom: false })),
    routines: SEED_ROUTINES.map(r => ({ ...r, exercises: r.exercises.map(x => ({ ...x })) })),
    workouts: [],
    activeWorkout: null,
    bodyMeasurements: [],
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      const def = defaultState();
      return {
        settings: { ...def.settings, ...(parsed.settings || {}) },
        exercises: parsed.exercises && parsed.exercises.length ? parsed.exercises : def.exercises,
        routines: parsed.routines || def.routines,
        workouts: parsed.workouts || [],
        activeWorkout: parsed.activeWorkout || null,
        bodyMeasurements: parsed.bodyMeasurements || [],
      };
    }
  } catch (e) { console.error('Falha ao carregar dados', e); }
  return defaultState();
}

let state = loadState();

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

/* ---------- utilitários ---------- */
function uid() { return 'id_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }
function esc(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
}
function getExercise(id) { return state.exercises.find(e => e.id === id); }
function unitLabel() { return state.settings.unit === 'lb' ? 'lb' : 'kg'; }

function formatDuration(sec) {
  sec = Math.max(0, Math.floor(sec));
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
  if (h > 0) return `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  return `${m}:${String(s).padStart(2,'0')}`;
}
function formatDateShort(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('pt-BR', { day:'2-digit', month:'short' }).replace('.', '');
}
function formatDateFull(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('pt-BR', { weekday:'long', day:'2-digit', month:'long', year:'numeric' });
}
function todayISO() { return new Date().toISOString(); }

function epley1RM(weight, reps) {
  if (!weight || !reps) return 0;
  return weight * (1 + reps / 30);
}

function workoutVolume(w) {
  let total = 0;
  (w.exercises || []).forEach(we => (we.sets || []).forEach(s => {
    if (s.completed && !s.warmup && s.weight && s.reps) total += Number(s.weight) * Number(s.reps);
  }));
  return total;
}
function workoutSetCount(w) {
  let total = 0;
  (w.exercises || []).forEach(we => (we.sets || []).forEach(s => { if (s.completed) total++; }));
  return total;
}

/* histórico de um exercício: lista de treinos concluídos que o contêm, mais recentes primeiro */
function getExerciseWorkouts(exerciseId) {
  return state.workouts
    .filter(w => (w.exercises || []).some(we => we.exerciseId === exerciseId))
    .sort((a, b) => new Date(b.date) - new Date(a.date));
}

function getLastPerformance(exerciseId, setIndex) {
  const past = getExerciseWorkouts(exerciseId);
  for (const w of past) {
    const we = w.exercises.find(e => e.exerciseId === exerciseId);
    if (!we || !we.sets || !we.sets.length) continue;
    const workingSets = we.sets.filter(s => !s.warmup);
    const s = workingSets[setIndex] || workingSets[workingSets.length - 1];
    if (s && s.weight != null && s.weight !== '') return s;
  }
  return null;
}

function getExercisePR(exerciseId) {
  let maxWeight = 0, maxWeightReps = 0, best1rm = 0;
  state.workouts.forEach(w => {
    (w.exercises || []).forEach(we => {
      if (we.exerciseId !== exerciseId) return;
      (we.sets || []).forEach(s => {
        if (!s.completed || s.warmup || !s.weight || !s.reps) return;
        const wt = Number(s.weight), rp = Number(s.reps);
        if (wt > maxWeight) { maxWeight = wt; maxWeightReps = rp; }
        const rm = epley1RM(wt, rp);
        if (rm > best1rm) best1rm = rm;
      });
    });
  });
  return { maxWeight, maxWeightReps, best1rm };
}

function isSetPR(exerciseId, weight, reps, excludeWorkoutId) {
  if (!weight || !reps) return false;
  let maxWeight = 0;
  state.workouts.forEach(w => {
    if (w.id === excludeWorkoutId) return;
    (w.exercises || []).forEach(we => {
      if (we.exerciseId !== exerciseId) return;
      (we.sets || []).forEach(s => {
        if (s.completed && !s.warmup && s.weight) maxWeight = Math.max(maxWeight, Number(s.weight));
      });
    });
  });
  return Number(weight) > maxWeight && maxWeight > 0 || (maxWeight === 0 && Number(weight) > 0);
}

/* ---------- calculadora de anilhas ---------- */
function calculatePlates(target, bar) {
  const plates = state.settings.unit === 'lb' ? PLATES_LB : PLATES_KG;
  target = Number(target) || 0;
  bar = Number(bar) || 0;
  if (target <= bar) return { perSide: [], leftover: 0, exact: target === bar };
  let remaining = (target - bar) / 2;
  const perSide = [];
  const EPS = 1e-6;
  plates.forEach(p => {
    while (remaining + EPS >= p) { perSide.push(p); remaining -= p; }
  });
  return { perSide, leftover: Math.max(0, remaining), exact: remaining <= EPS };
}

/* ---------- volume semanal por grupo muscular ---------- */
function getWeeklyMuscleVolume() {
  const weekAgo = Date.now() - 7 * 24 * 3600 * 1000;
  const totals = {};
  state.workouts.forEach(w => {
    if (new Date(w.date).getTime() < weekAgo) return;
    (w.exercises || []).forEach(we => {
      const ex = getExercise(we.exerciseId);
      if (!ex) return;
      (we.sets || []).forEach(s => {
        if (!s.completed || s.warmup || !s.weight || !s.reps) return;
        totals[ex.muscle] = (totals[ex.muscle] || 0) + Number(s.weight) * Number(s.reps);
      });
    });
  });
  return Object.entries(totals).map(([muscle, volume]) => ({ muscle, volume })).sort((a, b) => b.volume - a.volume);
}

/* ---------- supersets (exercícios agrupados) ---------- */
function getGroupSiblings(groupId) {
  if (!state.activeWorkout) return [];
  return state.activeWorkout.exercises.filter(x => x.groupId === groupId);
}
function isLastInGroup(we) {
  if (!we.groupId) return true;
  const siblings = getGroupSiblings(we.groupId);
  return siblings.length > 0 && siblings[siblings.length - 1].uid === we.uid;
}
function computeGroupLabels() {
  const labels = {};
  let i = 0;
  const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  (state.activeWorkout ? state.activeWorkout.exercises : []).forEach(we => {
    if (we.groupId && !(we.groupId in labels)) labels[we.groupId] = LETTERS[i++ % LETTERS.length];
  });
  return labels;
}

/* ---------- arrastar para reordenar (pointer events, funciona em touch e mouse) ---------- */
function enableDragReorder(containerEl, onReorderIds) {
  containerEl.querySelectorAll(':scope > .drag-row').forEach(row => {
    const handle = row.querySelector('.drag-handle');
    if (!handle) return;
    handle.style.touchAction = 'none';
    handle.onpointerdown = (e) => {
      e.preventDefault();
      const dragging = row;
      dragging.classList.add('dragging');
      // Capture on the container (which never moves) rather than the dragged row itself —
      // reparenting the captured element via insertBefore silently drops pointer capture in Chromium.
      containerEl.setPointerCapture(e.pointerId);

      const onMove = (ev) => {
        const rows = [...containerEl.querySelectorAll(':scope > .drag-row')].filter(r => r !== dragging);
        const y = ev.clientY;
        let inserted = false;
        for (const r of rows) {
          const rect = r.getBoundingClientRect();
          if (y < rect.top + rect.height / 2) { containerEl.insertBefore(dragging, r); inserted = true; break; }
        }
        if (!inserted && rows.length) containerEl.insertBefore(dragging, rows[rows.length - 1].nextSibling);
      };
      const onUp = () => {
        dragging.classList.remove('dragging');
        containerEl.releasePointerCapture(e.pointerId);
        containerEl.onpointermove = null;
        containerEl.onpointerup = null;
        const ids = [...containerEl.querySelectorAll(':scope > .drag-row')].map(r => r.dataset.id);
        onReorderIds(ids);
      };
      containerEl.onpointermove = onMove;
      containerEl.onpointerup = onUp;
    };
  });
}

/* ---------- arrastar (swipe) para excluir ---------- */
function enableSwipeToDelete(row, onDelete, excludeSelector) {
  let startX = 0, startY = 0, active = false, committed = false, pointerId = null;
  row.style.touchAction = 'pan-y';
  row.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    if (excludeSelector && e.target.closest(excludeSelector)) return;
    startX = e.clientX; startY = e.clientY; active = true; committed = false; pointerId = e.pointerId;
    row.style.transition = 'none';
    // Não captura o ponteiro ainda: um toque simples deve deixar o clique do
    // botão/input filho disparar normalmente. Só captura ao confirmar o swipe.
  });
  row.addEventListener('pointermove', (e) => {
    if (!active) return;
    const dx = e.clientX - startX, dy = e.clientY - startY;
    if (!committed) {
      if (Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(dy)) { committed = true; row.setPointerCapture(pointerId); }
      else if (Math.abs(dy) > 8) { active = false; return; }
    }
    if (committed) {
      const clamped = Math.min(0, Math.max(dx, -96));
      row.style.transform = `translateX(${clamped}px)`;
      row.classList.toggle('swipe-armed', clamped < -48);
    }
  });
  const finish = (e) => {
    if (!active) return;
    active = false;
    row.style.transition = 'transform .18s ease';
    const dx = e.clientX - startX;
    if (committed && dx < -48) {
      row.style.transform = 'translateX(-100%)';
      row.style.opacity = '0';
      setTimeout(onDelete, 160);
      return;
    }
    row.style.transform = 'translateX(0)';
    row.classList.remove('swipe-armed');
    if (committed) {
      const suppressClick = (ev) => { ev.stopPropagation(); ev.preventDefault(); };
      row.addEventListener('click', suppressClick, { capture: true, once: true });
    }
    committed = false;
  };
  row.addEventListener('pointerup', finish);
  row.addEventListener('pointercancel', () => {
    active = false; committed = false;
    row.style.transition = 'transform .18s ease';
    row.style.transform = 'translateX(0)';
    row.classList.remove('swipe-armed');
  });
}

/* ---------- toast ---------- */
function toast(msg) {
  const root = document.getElementById('toastRoot');
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  root.innerHTML = '';
  root.appendChild(el);
  setTimeout(() => { if (el.parentNode) el.remove(); }, 2400);
}

/* ---------- modal genérico ---------- */
function openModal(html) {
  document.getElementById('modalRoot').innerHTML =
    `<div class="modal-backdrop" onclick="if(event.target===this) closeModal()"><div class="modal-sheet">${html}</div></div>`;
}
function closeModal() { document.getElementById('modalRoot').innerHTML = ''; }

/* ===================== NAVEGAÇÃO / RENDER ===================== */
let ui = {
  tab: 'treino',
  exFilterQuery: '',
  exFilterMuscle: 'Todos',
  exerciseDetailId: null,
  historyDetailId: null,
  showMeasurements: false,
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

/* ===================== TAB: TREINO ===================== */
function renderTreinoTab(main) {
  if (state.activeWorkout) { renderActiveWorkout(main); return; }

  const totalWorkouts = state.workouts.length;
  const now = new Date();
  const weekAgo = new Date(now.getTime() - 7 * 24 * 3600 * 1000);
  const thisWeek = state.workouts.filter(w => new Date(w.date) >= weekAgo).length;
  const totalVolume = state.workouts.reduce((s, w) => s + workoutVolume(w), 0);

  const stats = document.createElement('div');
  stats.className = 'stats-row';
  stats.innerHTML = `
    <div class="stat-box"><div class="stat-num">${totalWorkouts}</div><div class="stat-label">Treinos</div></div>
    <div class="stat-box"><div class="stat-num">${thisWeek}</div><div class="stat-label">Esta semana</div></div>
    <div class="stat-box"><div class="stat-num">${Math.round(totalVolume).toLocaleString('pt-BR')}</div><div class="stat-label">Volume ${unitLabel()}</div></div>
  `;
  main.appendChild(stats);

  const weeklyVolume = getWeeklyMuscleVolume();
  if (weeklyVolume.length) {
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
    main.appendChild(volCard);
  }

  const startBtn = document.createElement('button');
  startBtn.className = 'btn btn-primary btn-block';
  startBtn.style.marginTop = '14px';
  startBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5v14"/></svg> Começar Treino Vazio`;
  startBtn.onclick = startEmptyWorkout;
  main.appendChild(startBtn);

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
  main.appendChild(sectionTitle);

  if (!state.routines.length) {
    main.appendChild(makeEmpty('Nenhuma rotina criada ainda.'));
  } else {
    state.routines.forEach(r => main.appendChild(renderRoutineCard(r)));
  }
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

function makeEmpty(text) {
  const div = document.createElement('div');
  div.className = 'empty';
  div.innerHTML = `<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="9"/><path d="M9 12h6"/></svg><span>${esc(text)}</span>`;
  return div;
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

function makeWorkoutExercise(exerciseId, targetSets) {
  const n = targetSets || 3;
  const sets = [];
  for (let i = 0; i < n; i++) sets.push(makeEmptySet());
  return { uid: uid(), exerciseId, sets, groupId: null };
}
function makeEmptySet() { return { uid: uid(), weight: '', reps: '', rpe: '', completed: false, warmup: false }; }

function renderActiveWorkout(main) {
  const aw = state.activeWorkout;

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
  main.appendChild(timerBar);
  timerBar.querySelector('#btnDiscard').onclick = () => {
    confirmDialog('Descartar este treino? Todo o progresso será perdido.', () => {
      stopActiveTimer();
      state.activeWorkout = null; saveState(); render(); toast('Treino descartado');
    });
  };
  timerBar.querySelector('#btnFinish').onclick = openFinishWorkoutModal;

  const totalSets = aw.exercises.reduce((s, we) => s + we.sets.filter(x => !x.warmup).length, 0);
  const doneSets = aw.exercises.reduce((s, we) => s + we.sets.filter(x => !x.warmup && x.completed).length, 0);
  const pct = totalSets ? Math.round((doneSets / totalSets) * 100) : 0;
  const progressBar = document.createElement('div');
  progressBar.className = 'workout-progress-bar';
  progressBar.innerHTML = `<div class="workout-progress-fill" style="width:${pct}%"></div>`;
  main.appendChild(progressBar);

  startActiveTimer();

  if (!aw.exercises.length) {
    main.appendChild(makeEmpty('Adicione exercícios para começar a registrar suas séries.'));
  }

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
  main.appendChild(actionsRow);
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

function renderWorkoutExerciseCard(we, subLabel) {
  const ex = getExercise(we.exerciseId);
  const card = document.createElement('div');
  card.className = 'card ex-card' + (subLabel ? '' : ' drag-row');
  if (!subLabel) card.dataset.id = we.uid;

  const workingSets = we.sets.filter(s => !s.warmup);
  const allDone = workingSets.length > 0 && workingSets.every(s => s.completed);

  const head = document.createElement('div');
  head.className = 'ex-card-head';
  head.innerHTML = `
    ${subLabel ? '' : '<button class="drag-handle" title="Arrastar para reordenar">≡</button>'}
    <div class="ex-card-head-info">
      <div class="ex-card-title">${esc(ex ? ex.name : 'Exercício')}${subLabel ? `<span class="ex-sublabel">${esc(subLabel)}</span>` : ''}</div>
      <div class="ex-card-sub">${esc(ex ? ex.muscle : '')}</div>
    </div>
    <div class="ex-card-head-actions">
      ${ex && ex.equipment === 'Barra' ? '<button class="icon-btn ex-plate-btn" title="Calculadora de anilhas">🏋</button>' : ''}
      <div class="ex-check-badge ${allDone ? 'on' : ''}" title="${allDone ? 'Exercício concluído' : ''}">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M4 12l5 5L20 6"/></svg>
      </div>
      <button class="ex-card-menu-btn" title="Remover exercício">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V6"/></svg>
      </button>
    </div>
  `;
  head.querySelector('.ex-card-menu-btn').onclick = () => {
    confirmDialog(`Remover "${ex ? ex.name : 'exercício'}" deste treino?`, () => {
      state.activeWorkout.exercises = state.activeWorkout.exercises.filter(x => x.uid !== we.uid);
      saveState(); render();
    });
  };
  const plateBtn = head.querySelector('.ex-plate-btn');
  if (plateBtn) plateBtn.onclick = () => openPlateCalculator(we);
  card.appendChild(head);

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
    const prev = !s.warmup ? getLastPerformance(we.exerciseId, prevIdx) : null;
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
    checkBtn.onclick = () => {
      s.completed = !s.completed;
      if (s.completed) {
        if (!s.weight && prev) s.weight = prev.weight;
        if (!s.reps && prev) s.reps = prev.reps;
        if (!s.warmup && isLastInGroup(we)) startRestTimer(state.settings.restDefault);
      }
      saveState(); render();
    };
    enableSwipeToDelete(row, () => { we.sets = we.sets.filter(x => x.uid !== s.uid); saveState(); render(); });
    table.appendChild(row);
  });

  const addSetBtn = document.createElement('button');
  addSetBtn.className = 'btn btn-ghost btn-sm add-set-btn';
  addSetBtn.textContent = '+ Adicionar Série';
  addSetBtn.onclick = () => { we.sets.push(makeEmptySet()); saveState(); render(); };
  table.appendChild(addSetBtn);

  card.appendChild(table);
  return card;
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
    setTab('historico');
    toast('Treino salvo!');
  };
}

/* ---------- confirmação ---------- */
function confirmDialog(message, onConfirm) {
  openModal(`
    <div class="modal-title">Confirmar</div>
    <p style="font-size:14px;color:var(--muted);line-height:1.6;">${esc(message)}</p>
    <div class="modal-footer">
      <button class="btn btn-ghost" style="flex:1" id="cCancel">Cancelar</button>
      <button class="btn btn-danger" style="flex:1" id="cOk">Confirmar</button>
    </div>
  `);
  document.getElementById('cCancel').onclick = closeModal;
  document.getElementById('cOk').onclick = () => { closeModal(); onConfirm(); };
}

/* ---------- rest timer ---------- */
let restTimer = { active: false, endsAt: 0, duration: 0, interval: null, finished: false };

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
  } catch (e) { /* áudio indisponível */ }
}
document.addEventListener('pointerdown', unlockAudio, { once: true });

function startRestTimer(seconds) {
  restTimer.active = true;
  restTimer.finished = false;
  restTimer.duration = seconds;
  restTimer.endsAt = Date.now() + seconds * 1000;
  if (restTimer.interval) clearInterval(restTimer.interval);
  restTimer.interval = setInterval(tickRestTimer, 250);
  renderRestBar();
}
function stopRestTimer() {
  restTimer.active = false;
  restTimer.finished = false;
  if (restTimer.interval) { clearInterval(restTimer.interval); restTimer.interval = null; }
  renderRestBar();
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
      renderRestBar();
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
  } catch (e) { /* som indisponível */ }
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
          <span class="mono" style="font-size:11px;letter-spacing:1px;text-transform:uppercase;">Descanso concluído!</span>
        </div>
        <div class="rest-bar-actions"><button id="restDismiss">OK</button></div>
      </div>
    `;
    document.getElementById('restDismiss').onclick = stopRestTimer;
    return;
  }

  const remaining = Math.max(0, Math.round((restTimer.endsAt - Date.now()) / 1000));
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
  document.querySelectorAll('.chip-row [data-s]').forEach(chip => {
    chip.onclick = () => { startRestTimer(Number(chip.dataset.s)); closeModal(); };
  });
  document.getElementById('rtCancel').onclick = closeModal;
  document.getElementById('rtSave').onclick = () => {
    const m = Math.max(0, Number(document.getElementById('rtMin').value) || 0);
    const s = Math.max(0, Number(document.getElementById('rtSec').value) || 0);
    const total = m * 60 + s;
    if (total <= 0) { toast('Informe um tempo maior que zero.'); return; }
    startRestTimer(total);
    closeModal();
  };
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('btnQuickTimer').onclick = () => startRestTimer(state.settings.restDefault);
});

/* ===================== SELETOR DE EXERCÍCIOS (modal) ===================== */
let picker = { selected: new Set(), query: '', muscle: 'Todos', onConfirm: null };

function openExercisePicker(onConfirm, opts) {
  picker = { selected: new Set(), query: '', muscle: 'Todos', onConfirm };
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
      <button class="btn btn-primary" style="flex:2" id="pickerConfirm">Adicionar (${picker.selected.size})</button>
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
  if (confirmBtn) confirmBtn.textContent = `Adicionar (${picker.selected.size})`;
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

  const back = document.createElement('button');
  back.className = 'btn btn-ghost btn-sm';
  back.style.marginBottom = '14px';
  back.innerHTML = '← Voltar';
  back.onclick = () => { ui.historyDetailId = null; render(); };
  main.appendChild(back);

  const head = document.createElement('div');
  head.className = 'card card-pad';
  head.innerHTML = `
    <div class="history-name" style="font-size:19px;">${esc(w.name)}</div>
    <div class="history-date" style="margin-bottom:12px;">${esc(formatDateFull(w.date))}</div>
    <div class="stats-row">
      <div class="stat-box"><div class="stat-num">${formatDuration(w.durationSec || 0)}</div><div class="stat-label">Duração</div></div>
      <div class="stat-box"><div class="stat-num">${workoutSetCount(w)}</div><div class="stat-label">Séries</div></div>
      <div class="stat-box"><div class="stat-num">${Math.round(workoutVolume(w)).toLocaleString('pt-BR')}</div><div class="stat-label">Volume ${unitLabel()}</div></div>
    </div>
    ${w.notes ? `<p style="margin-top:14px;font-size:13px;color:var(--muted);line-height:1.6;">${esc(w.notes)}</p>` : ''}
  `;
  main.appendChild(head);

  w.exercises.forEach(we => {
    const ex = getExercise(we.exerciseId);
    const card = document.createElement('div');
    card.className = 'card';
    card.style.marginTop = '12px';
    const rows = we.sets.map((s, i) => `<div class="set-history-row"><span>${s.warmup ? 'W' : (i+1)}</span><span>${esc(s.weight)}${unitLabel()} × ${esc(s.reps)}${s.rpe ? ` · RPE ${esc(s.rpe)}` : ''}</span></div>`).join('');
    card.innerHTML = `
      <div class="ex-card-head"><div class="ex-card-title">${esc(ex ? ex.name : 'Exercício')}</div></div>
      ${rows}
    `;
    main.appendChild(card);
  });

  const actions = document.createElement('div');
  actions.className = 'modal-footer';
  actions.style.marginTop = '18px';
  actions.innerHTML = `
    <button class="btn btn-ghost" style="flex:1" id="dRepeat">Repetir Treino</button>
    <button class="btn btn-danger" style="flex:1" id="dDelete">Excluir</button>
  `;
  main.appendChild(actions);
  document.getElementById('dRepeat').onclick = () => {
    if (state.activeWorkout) { toast('Finalize ou descarte o treino em andamento primeiro.'); return; }
    state.activeWorkout = {
      id: uid(), name: w.name, date: todayISO(), startedAt: Date.now(), notes: '',
      exercises: w.exercises.map(we => ({ uid: uid(), exerciseId: we.exerciseId, sets: we.sets.map(() => makeEmptySet()) })),
    };
    saveState(); ui.historyDetailId = null; setTab('treino');
  };
  document.getElementById('dDelete').onclick = () => {
    confirmDialog('Excluir este treino do histórico?', () => {
      state.workouts = state.workouts.filter(x => x.id !== workoutId);
      saveState(); ui.historyDetailId = null; render(); toast('Treino excluído');
    });
  };
}

/* ===================== TAB: EXERCÍCIOS ===================== */
function renderExerciciosTab(main) {
  if (ui.exerciseDetailId) { renderExerciseDetail(main, ui.exerciseDetailId); return; }

  const search = document.createElement('input');
  search.className = 'search-box';
  search.type = 'text';
  search.placeholder = 'Buscar exercício...';
  search.value = ui.exFilterQuery;
  search.oninput = () => { ui.exFilterQuery = search.value; renderList(); };
  main.appendChild(search);

  const chips = document.createElement('div');
  chips.className = 'chip-row';
  ['Todos', ...MUSCLE_GROUPS].forEach(m => {
    const chip = document.createElement('button');
    chip.className = 'chip' + (ui.exFilterMuscle === m ? ' active' : '');
    chip.textContent = m;
    chip.onclick = () => { ui.exFilterMuscle = m; render(); };
    chips.appendChild(chip);
  });
  main.appendChild(chips);

  const listCard = document.createElement('div');
  listCard.className = 'card';
  main.appendChild(listCard);

  const newExBtn = document.createElement('button');
  newExBtn.className = 'btn btn-ghost btn-block';
  newExBtn.style.marginTop = '14px';
  newExBtn.textContent = '+ Criar novo exercício';
  newExBtn.onclick = () => {
    openModalNewExerciseStandalone();
  };
  main.appendChild(newExBtn);

  function renderList() {
    listCard.innerHTML = '';
    const filtered = state.exercises.filter(e =>
      (ui.exFilterMuscle === 'Todos' || e.muscle === ui.exFilterMuscle) &&
      e.name.toLowerCase().includes(ui.exFilterQuery.toLowerCase())
    ).sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'));
    if (!filtered.length) { listCard.appendChild(makeEmpty('Nenhum exercício encontrado.')); return; }
    filtered.forEach(e => {
      const item = document.createElement('div');
      item.className = 'ex-list-item';
      const pr = getExercisePR(e.id);
      item.innerHTML = `
        <div><div class="ex-list-name">${esc(e.name)}</div><div class="ex-list-muscle">${esc(e.muscle)} · ${esc(e.equipment)}</div></div>
        <div class="mono" style="font-size:11px;color:var(--muted);">${pr.maxWeight ? pr.maxWeight + unitLabel() : ''}</div>
      `;
      item.onclick = () => { ui.exerciseDetailId = e.id; render(); window.scrollTo(0,0); };
      listCard.appendChild(item);
    });
  }
  renderList();
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

function renderExerciseDetail(main, exerciseId) {
  const ex = getExercise(exerciseId);
  if (!ex) { ui.exerciseDetailId = null; renderExerciciosTab(main); return; }

  const back = document.createElement('button');
  back.className = 'btn btn-ghost btn-sm';
  back.style.marginBottom = '14px';
  back.textContent = '← Voltar';
  back.onclick = () => { ui.exerciseDetailId = null; render(); };
  main.appendChild(back);

  const head = document.createElement('div');
  head.className = 'card card-pad';
  const pr = getExercisePR(exerciseId);
  head.innerHTML = `
    <div class="history-name" style="font-size:18px;">${esc(ex.name)}</div>
    <div class="ex-card-sub" style="margin-bottom:14px;">${esc(ex.muscle)} · ${esc(ex.equipment)}</div>
    <div class="pr-grid">
      <div class="stat-box"><div class="stat-num">${pr.maxWeight ? pr.maxWeight + unitLabel() : '—'}</div><div class="stat-label">Recorde de Carga</div></div>
      <div class="stat-box"><div class="stat-num">${pr.best1rm ? Math.round(pr.best1rm) + unitLabel() : '—'}</div><div class="stat-label">1RM Estimado</div></div>
    </div>
  `;
  main.appendChild(head);

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
  main.appendChild(chartCard);
  const chartWrap = chartCard.querySelector('#chartWrap');
  if (points.length < 2) {
    chartWrap.appendChild(makeEmpty('Registre esse exercício em pelo menos 2 treinos para ver o gráfico de progresso.'));
  } else {
    chartWrap.innerHTML = renderLineChartSVG(points, unitLabel());
  }

  const histCard = document.createElement('div');
  histCard.className = 'card';
  histCard.style.marginTop = '12px';
  const rowsHtml = getExerciseWorkouts(exerciseId).map(w => {
    const we = w.exercises.find(e => e.exerciseId === exerciseId);
    const setsTxt = we.sets.filter(s => s.completed).map(s => `${s.warmup ? 'W:' : ''}${s.weight}${unitLabel()}×${s.reps}`).join(', ');
    return `<div class="set-history-row"><span class="set-history-date">${esc(formatDateShort(w.date))}</span><span>${esc(setsTxt)}</span></div>`;
  }).join('');
  histCard.innerHTML = `<div class="ex-card-head"><div class="ex-card-title">Histórico</div></div>${rowsHtml || '<div class="set-history-row"><span>Nenhum registro ainda</span></div>'}`;
  main.appendChild(histCard);

  if (ex.custom) {
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
    main.appendChild(delBtn);
  }
}

function renderLineChartSVG(points, unit) {
  const W = 300, H = 140, padL = 34, padR = 12, padT = 14, padB = 22;
  const values = points.map(p => p.value);
  let min = Math.min(...values), max = Math.max(...values);
  if (min === max) { min -= 5; max += 5; }
  const range = max - min;
  const stepX = (W - padL - padR) / (points.length - 1);
  const coords = points.map((p, i) => {
    const x = padL + i * stepX;
    const y = padT + (H - padT - padB) * (1 - (p.value - min) / range);
    return { x, y, v: p.value, d: p.date };
  });
  const linePath = coords.map((c, i) => (i === 0 ? 'M' : 'L') + c.x.toFixed(1) + ',' + c.y.toFixed(1)).join(' ');
  const areaPath = linePath + ` L${coords[coords.length-1].x.toFixed(1)},${(H-padB).toFixed(1)} L${coords[0].x.toFixed(1)},${(H-padB).toFixed(1)} Z`;
  const dots = coords.map(c => `<circle cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="3.2" fill="#2dd4bf" stroke="#0d0d0f" stroke-width="1.5"/>`).join('');
  const firstLabel = formatDateShort(coords[0].d), lastLabel = formatDateShort(coords[coords.length-1].d);
  return `
    <svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;overflow:visible;">
      <line x1="${padL}" y1="${padT}" x2="${padL}" y2="${H-padB}" stroke="#2a2a2e" stroke-width="1"/>
      <line x1="${padL}" y1="${H-padB}" x2="${W-padR}" y2="${H-padB}" stroke="#2a2a2e" stroke-width="1"/>
      <text x="2" y="${padT+4}" font-size="8" fill="#8a8a90" font-family="IBM Plex Mono">${Math.round(max)}${unit}</text>
      <text x="2" y="${H-padB}" font-size="8" fill="#8a8a90" font-family="IBM Plex Mono">${Math.round(min)}${unit}</text>
      <path d="${areaPath}" fill="#2dd4bf22" stroke="none"/>
      <path d="${linePath}" fill="none" stroke="#2dd4bf" stroke-width="2"/>
      ${dots}
      <text x="${padL}" y="${H-4}" font-size="8" fill="#8a8a90" font-family="IBM Plex Mono">${esc(firstLabel)}</text>
      <text x="${W-padR}" y="${H-4}" font-size="8" fill="#8a8a90" font-family="IBM Plex Mono" text-anchor="end">${esc(lastLabel)}</text>
    </svg>
  `;
}

/* ---------- diagrama corporal simplificado (frente/costas) ---------- */
function bodyDiagramSVG(activeMuscles) {
  const on = (m) => activeMuscles.has(m) ? 'var(--accent)' : 'var(--surface2)';
  const skin = 'var(--border)';
  return `
    <svg viewBox="0 0 220 250" style="width:100%;max-width:240px;margin:0 auto;display:block;">
      <g>
        <circle cx="55" cy="20" r="15" fill="var(--surface2)" stroke="${skin}"/>
        <rect x="33" y="37" width="44" height="16" rx="6" fill="${on('Ombros')}" stroke="${skin}"/>
        <rect x="37" y="53" width="36" height="48" rx="10" fill="${on('Peito')}" stroke="${skin}"/>
        <rect x="37" y="101" width="36" height="30" rx="8" fill="${on('Abdômen')}" stroke="${skin}"/>
        <rect x="18" y="55" width="15" height="52" rx="7" fill="${on('Bíceps')}" stroke="${skin}"/>
        <rect x="77" y="55" width="15" height="52" rx="7" fill="${on('Bíceps')}" stroke="${skin}"/>
        <rect x="37" y="133" width="17" height="74" rx="8" fill="${on('Pernas')}" stroke="${skin}"/>
        <rect x="56" y="133" width="17" height="74" rx="8" fill="${on('Pernas')}" stroke="${skin}"/>
        <text x="55" y="238" text-anchor="middle" font-size="9" fill="var(--muted)" font-family="IBM Plex Mono" letter-spacing="1">FRENTE</text>
      </g>
      <g transform="translate(110,0)">
        <circle cx="55" cy="20" r="15" fill="var(--surface2)" stroke="${skin}"/>
        <rect x="33" y="37" width="44" height="16" rx="6" fill="${on('Ombros')}" stroke="${skin}"/>
        <rect x="37" y="53" width="36" height="48" rx="10" fill="${on('Costas')}" stroke="${skin}"/>
        <rect x="37" y="101" width="36" height="30" rx="8" fill="var(--surface2)" stroke="${skin}"/>
        <rect x="18" y="55" width="15" height="52" rx="7" fill="${on('Tríceps')}" stroke="${skin}"/>
        <rect x="77" y="55" width="15" height="52" rx="7" fill="${on('Tríceps')}" stroke="${skin}"/>
        <rect x="37" y="133" width="17" height="74" rx="8" fill="${on('Pernas')}" stroke="${skin}"/>
        <rect x="56" y="133" width="17" height="74" rx="8" fill="${on('Pernas')}" stroke="${skin}"/>
        <text x="55" y="238" text-anchor="middle" font-size="9" fill="var(--muted)" font-family="IBM Plex Mono" letter-spacing="1">COSTAS</text>
      </g>
    </svg>
  `;
}

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
      row.querySelector('[data-act="sets"]').onclick = () => openStepperEditor('Número de Séries', x.targetSets, 1, 10, v => { x.targetSets = v; renderRoutineEditor(); });
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

function openStepperEditor(title, value, min, max, onSave) {
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
        if (!data.exercises || !data.workouts) throw new Error('Formato inválido');
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
  about.innerHTML = `Treino — diário de treino inspirado no Strong.<br>Todos os dados ficam salvos apenas neste dispositivo.`;
  main.appendChild(about);
}

/* ===================== MEDIDAS CORPORAIS ===================== */
const MEASURE_FIELDS = [
  { key: 'chest', label: 'Peito' }, { key: 'waist', label: 'Cintura' },
  { key: 'hips', label: 'Quadril' }, { key: 'arm', label: 'Braço' },
  { key: 'thigh', label: 'Coxa' }, { key: 'calf', label: 'Panturrilha' },
];

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

/* ===================== INIT ===================== */
applyTheme();
if (state.activeWorkout) { /* mantém sessão ativa entre reloads */ }
render();

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('./sw.js').catch(() => {});
}
