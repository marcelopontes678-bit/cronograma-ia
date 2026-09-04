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

/* Resumo por exercício de um treino: nº de séries concluídas e a melhor série (maior
   peso, com mais reps como desempate) — usado no resumo ao finalizar e no histórico. */
function getWorkoutExerciseSummaries(w) {
  return (w.exercises || []).map(we => {
    const ex = getExercise(we.exerciseId);
    const completed = (we.sets || []).filter(s => s.completed);
    let best = null;
    completed.forEach(s => {
      if (!s.weight) return;
      const better = !best
        || Number(s.weight) > Number(best.weight)
        || (Number(s.weight) === Number(best.weight) && Number(s.reps || 0) > Number(best.reps || 0));
      if (better) best = s;
    });
    return { exerciseId: we.exerciseId, name: ex ? ex.name : 'Exercício', count: completed.length, best };
  }).filter(s => s.count > 0);
}

function countWorkoutPRs(w) {
  let count = 0;
  (w.exercises || []).forEach(we => (we.sets || []).forEach(s => {
    if (s.completed && !s.warmup && s.weight && s.reps && isSetPR(we.exerciseId, s.weight, s.reps, w.id)) count++;
  }));
  return count;
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

/* Maior carga já registrada nessa posição de série (não apenas a última vez) — é essa
   referência que aparece como sugestão ao logar, pra sempre mirar em evoluir o próprio
   recorde em vez de só repetir o treino anterior. */
function getBestPerformance(exerciseId, setIndex) {
  const past = getExerciseWorkouts(exerciseId);
  let best = null;
  past.forEach(w => {
    const we = w.exercises.find(e => e.exerciseId === exerciseId);
    if (!we || !we.sets || !we.sets.length) return;
    const workingSets = we.sets.filter(s => !s.warmup);
    const s = workingSets[setIndex] || workingSets[workingSets.length - 1];
    if (!s || s.weight == null || s.weight === '') return;
    const better = !best
      || Number(s.weight) > Number(best.weight)
      || (Number(s.weight) === Number(best.weight) && Number(s.reps || 0) > Number(best.reps || 0));
    if (better) best = s;
  });
  return best;
}

/* Sugestão de progressão de carga pra próxima vez que este exercício for
   feito nesta posição de série. Progressão linear: prioriza subir o peso
   (não pedir mais repetições), baseada no desempenho MAIS RECENTE (não no
   recorde) pra refletir onde você está agora. RPE muito alto na última vez
   segura a progressão em vez de empurrar mais carga.
   É uma heurística determinística, não uma chamada de IA — decisão numérica
   como essa é mais confiável como regra fixa do que como resposta de modelo. */
function getProgressionSuggestion(exerciseId, setIndex) {
  const last = getLastPerformance(exerciseId, setIndex);
  if (!last) return null;
  const weight = Number(last.weight), reps = Number(last.reps);
  if (!weight || !reps) return null;

  const rpe = last.rpe !== '' && last.rpe != null ? Number(last.rpe) : null;
  const increment = state.settings.unit === 'lb' ? 5 : 2.5;

  if (rpe != null && rpe >= 9.5) {
    return { weight, reps, reason: `RPE ${rpe} na última vez — mantenha a carga e foque na execução.` };
  }
  return { weight: weight + increment, reps, reason: `Aumente para ${weight + increment}${unitLabel()} mantendo ${reps} reps (última vez: ${weight}${unitLabel()}).` };
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
