const STORAGE_KEY = 'treino_app_v1';

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
        exercises: parsed.exercises || def.exercises,
        routines: parsed.routines || def.routines,
        workouts: parsed.workouts || [],
        activeWorkout: parsed.activeWorkout || null,
        bodyMeasurements: parsed.bodyMeasurements || [],
      };
    }
  } catch (e) { console.error('Falha ao carregar dados', e); }
  return defaultState();
}

// Reassigned wholesale in tab-perfil.js (import backup / reset-all-data),
// which ESLint can't see from this file.
// eslint-disable-next-line prefer-const
let state = loadState();

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (e) {
    console.error('Falha ao salvar dados', e);
    toast('Não foi possível salvar — armazenamento cheio ou indisponível.');
  }
}

/* Validação mínima de um backup importado — o suficiente para recusar arquivos
   claramente malformados antes que quebrem alguma tela mais adiante, sem exigir
   um schema completo. Retorna uma mensagem de erro, ou null se estiver ok. */
function validateImportedState(data) {
  if (!data || typeof data !== 'object') return 'o arquivo não contém um objeto JSON válido.';
  if (!Array.isArray(data.exercises)) return 'campo "exercises" ausente ou inválido.';
  if (!Array.isArray(data.workouts)) return 'campo "workouts" ausente ou inválido.';
  if (data.routines !== undefined && !Array.isArray(data.routines)) return 'campo "routines" inválido.';
  if (data.bodyMeasurements !== undefined && !Array.isArray(data.bodyMeasurements)) return 'campo "bodyMeasurements" inválido.';
  if (data.settings !== undefined && (typeof data.settings !== 'object' || data.settings === null)) return 'campo "settings" inválido.';
  const badExercise = data.exercises.find(e => !e || typeof e.id !== 'string' || typeof e.name !== 'string');
  if (badExercise) return 'um ou mais exercícios estão com formato inválido (faltando id/nome).';
  const badWorkout = data.workouts.find(w => !w || typeof w.id !== 'string' || !Array.isArray(w.exercises));
  if (badWorkout) return 'um ou mais treinos estão com formato inválido.';
  return null;
}
