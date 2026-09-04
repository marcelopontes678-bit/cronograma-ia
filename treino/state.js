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
  } catch (e) { logError('Falha ao carregar dados', e); }
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
    logError('Falha ao salvar dados', e);
    toast('Não foi possível salvar — armazenamento cheio ou indisponível.');
  }
}

/* Cada checagem roda na ordem, e a primeira que devolver uma mensagem vence --
   mesma semântica da cadeia de "if early-return" que isso substitui. Checagens
   depois da primeira podem assumir "data" é um objeto porque, se não fosse, o
   loop já teria parado ali. */
const IMPORT_VALIDATIONS = [
  (data) => (!data || typeof data !== 'object') && 'o arquivo não contém um objeto JSON válido.',
  (data) => !Array.isArray(data.exercises) && 'campo "exercises" ausente ou inválido.',
  (data) => !Array.isArray(data.workouts) && 'campo "workouts" ausente ou inválido.',
  (data) => data.routines !== undefined && !Array.isArray(data.routines) && 'campo "routines" inválido.',
  (data) => data.bodyMeasurements !== undefined && !Array.isArray(data.bodyMeasurements) && 'campo "bodyMeasurements" inválido.',
  (data) => data.settings !== undefined && (typeof data.settings !== 'object' || data.settings === null) && 'campo "settings" inválido.',
  (data) => data.exercises.find(e => !e || typeof e.id !== 'string' || typeof e.name !== 'string')
    && 'um ou mais exercícios estão com formato inválido (faltando id/nome).',
  (data) => data.workouts.find(w => !w || typeof w.id !== 'string' || !Array.isArray(w.exercises))
    && 'um ou mais treinos estão com formato inválido.',
];

/* Validação mínima de um backup importado — o suficiente para recusar arquivos
   claramente malformados antes que quebrem alguma tela mais adiante, sem exigir
   um schema completo. Retorna uma mensagem de erro, ou null se estiver ok. */
function validateImportedState(data) {
  for (const check of IMPORT_VALIDATIONS) {
    const error = check(data);
    if (error) return error;
  }
  return null;
}
