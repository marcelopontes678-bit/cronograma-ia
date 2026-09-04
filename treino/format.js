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

function formatDateTimeFull(iso) {
  const d = new Date(iso);
  const time = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  return `${formatDateFull(iso)} às ${time}`;
}

function todayISO() { return new Date().toISOString(); }

function epley1RM(weight, reps) {
  if (!weight || !reps) return 0;
  return weight * (1 + reps / 30);
}
