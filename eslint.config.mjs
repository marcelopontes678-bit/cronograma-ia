// Fast lint tier for this repo. Plain JavaScript, no TypeScript and no
// bundler: worker/index.js is an ES module (Cloudflare Workers), the
// treino/ and root files are plain browser scripts, and
// orcamento-marcenaria/engine is CommonJS. sourceType is set per group
// below instead of assumed globally.
import js from "@eslint/js";
import { defineConfig, globalIgnores } from "eslint/config";

import quality from "./eslint-rules/index.cjs";

export default defineConfig([
  {
    languageOptions: {
      // js.configs.recommended turns on no-undef, which knows nothing about
      // the runtime this project targets -- without this, every console,
      // fetch or browser global reference is reported as an undefined
      // variable. Declare what the code actually uses.
      globals: {
        console: "readonly",
        fetch: "readonly",
        Response: "readonly",
        Request: "readonly",
        URL: "readonly",
        URLSearchParams: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        localStorage: "readonly",
        document: "readonly",
        window: "readonly",
        navigator: "readonly",
        alert: "readonly",
        confirm: "readonly",
        prompt: "readonly",
      },
    },
  },
  js.configs.recommended,

  {
    // worker/index.js is the only real ES module in the repo (Cloudflare
    // Workers module syntax).
    files: ["worker/**/*.js"],
    languageOptions: {
      sourceType: "module",
      globals: {
        Response: "readonly",
        URL: "readonly",
      },
    },
  },
  {
    // sw.js (root, and its copy served from treino/) is the service worker
    // registered by treino/app.js: no import/export, registered directly,
    // so it parses as a script.
    files: ["sw.js", "treino/sw.js"],
    languageOptions: {
      sourceType: "script",
      globals: {
        caches: "readonly",
        self: "readonly",
      },
    },
  },
  {
    // treino/*.js are plain browser scripts, no import/export, loaded via a
    // sequence of <script> tags (see treino/index.html) rather than a
    // bundler. Each one only declares top-level functions/variables that
    // become globals shared with every other script tag on the page --
    // ESLint lints one file at a time and has no notion of that shared
    // scope, so every name declared in one of these files but used in
    // another has to be listed here too, or no-undef misreads a normal
    // cross-file call as an undefined reference.
    files: ["treino/**/*.js"],
    languageOptions: {
      sourceType: "script",
      globals: {
        setInterval: "readonly",
        clearInterval: "readonly",
        Blob: "readonly",
        FileReader: "readonly",

        // Cross-file globals declared across treino/*.js, app.js included
        // (render/setTab live there and are called from every tab module).
        render: "readonly",
        setTab: "readonly",
        ui: "readonly",
        logError: "readonly",
        MUSCLE_GROUPS: "readonly",
        SEED_EXERCISES: "readonly",
        SEED_ROUTINES: "readonly",
        MEASURE_FIELDS: "readonly",
        STORAGE_KEY: "readonly",
        PLATES_KG: "readonly",
        PLATES_LB: "readonly",
        defaultState: "readonly",
        loadState: "readonly",
        saveState: "readonly",
        validateImportedState: "readonly",
        uid: "readonly",
        esc: "readonly",
        getExercise: "readonly",
        unitLabel: "readonly",
        formatDuration: "readonly",
        formatDateShort: "readonly",
        formatDateFull: "readonly",
        formatDateTimeFull: "readonly",
        todayISO: "readonly",
        epley1RM: "readonly",
        workoutVolume: "readonly",
        workoutSetCount: "readonly",
        getWorkoutExerciseSummaries: "readonly",
        countWorkoutPRs: "readonly",
        getExerciseWorkouts: "readonly",
        getLastPerformance: "readonly",
        getBestPerformance: "readonly",
        getProgressionSuggestion: "readonly",
        getExercisePR: "readonly",
        isSetPR: "readonly",
        calculatePlates: "readonly",
        getWeeklyMuscleVolume: "readonly",
        getGroupSiblings: "readonly",
        isLastInGroup: "readonly",
        computeGroupLabels: "readonly",
        buildWorkoutSummaryCard: "readonly",
        renderHistoricoTab: "readonly",
        renderHistoryDetail: "readonly",
        enableDragReorder: "readonly",
        enableSwipeToDelete: "readonly",
        toast: "readonly",
        openModal: "readonly",
        closeModal: "readonly",
        makeEmpty: "readonly",
        confirmDialog: "readonly",
        renderTreinoTab: "readonly",
        renderRoutineCard: "readonly",
        startEmptyWorkout: "readonly",
        startRoutineWorkout: "readonly",
        makeWorkoutExercise: "readonly",
        makeEmptySet: "readonly",
        renderActiveWorkout: "readonly",
        renderExerciseGroup: "readonly",
        openGroupPicker: "readonly",
        startActiveTimer: "readonly",
        stopActiveTimer: "readonly",
        openFinishWorkoutModal: "readonly",
        renderWorkoutExerciseCard: "readonly",
        openPlateCalculator: "readonly",
        openExerciseActionMenu: "readonly",
        openExerciseNoteEditor: "readonly",
        addWarmupSet: "readonly",
        openExerciseRestOverrideEditor: "readonly",
        openReplaceExercise: "readonly",
        unlockAudio: "readonly",
        startRestTimer: "readonly",
        stopRestTimer: "readonly",
        adjustRestTimer: "readonly",
        tickRestTimer: "readonly",
        playRestDoneAlert: "readonly",
        renderRestBar: "readonly",
        buildInlineRestDivider: "readonly",
        openRestTimerEditor: "readonly",
        openExercisePicker: "readonly",
        renderExercisePicker: "readonly",
        updatePickerResults: "readonly",
        openNewExerciseForm: "readonly",
        renderExerciciosTab: "readonly",
        openModalNewExerciseStandalone: "readonly",
        stopExerciseAnim: "readonly",
        renderExerciseDetail: "readonly",
        renderLineChartSVG: "readonly",
        bodyDiagramSVG: "readonly",
        openRoutineEditor: "readonly",
        renderRoutineEditor: "readonly",
        openStepperEditor: "readonly",
        openRepRangeEditor: "readonly",
        renderPerfilTab: "readonly",
        renderMeasurementsView: "readonly",
        applyTheme: "readonly",

        state: "writable",
        activeTimerInterval: "writable",
        restTimer: "writable",
        sharedAudioCtx: "writable",
        picker: "writable",
        exerciseAnimTimer: "writable",
        routineDraft: "writable",
      },
    },
    rules: {
      // Every name listed above as a global is ALSO declared locally in
      // whichever treino/*.js file actually defines it -- that's what makes
      // it reachable from sibling <script> tags in the first place. Flat
      // config has no per-file globals, so the same list applies uniformly,
      // and no-redeclare would flag every one of those defining files as
      // redeclaring its own global. vars:"local" keeps no-unused-vars
      // checking real local-scope dead code while not flagging a top-level
      // function whose only callers live in another file.
      "no-redeclare": "off",
      "no-unused-vars": ["error", { vars: "local", argsIgnorePattern: "^_" }],
    },
  },
  {
    // orcamento-marcenaria/engine is a Node CommonJS script (require/module).
    files: ["orcamento-marcenaria/engine/**/*.js"],
    languageOptions: {
      sourceType: "commonjs",
      globals: {
        require: "readonly",
        module: "readonly",
        process: "readonly",
        __dirname: "readonly",
      },
    },
  },

  {
    files: ["**/*.{js,cjs,mjs}"],
    plugins: { quality },
    rules: {
      "no-empty": ["error", { allowEmptyCatch: true }],
      "no-var": "error",
      "prefer-const": "error",
      // The size and complexity budget is all "warn" on purpose. These
      // numbers are a conversation starter about factoring, not a gate --
      // promote one to "error" once the count for it reaches zero.
      complexity: ["warn", 12],
      "max-depth": ["warn", 4],
      "max-statements": ["warn", 20],
      "max-params": ["warn", 4],
      "max-lines-per-function": [
        "warn",
        { max: 150, skipBlankLines: true, skipComments: true },
      ],
      "max-nested-callbacks": ["warn", 3],
      "quality/max-lines": ["error", { max: 350 }],
      // Baseline reached zero: treino/logger.js (logError) and
      // worker/logger.js (logError) are now the project's logging
      // helpers, and every call site in treino/ and worker/ goes through
      // one of them. orcamento-marcenaria/engine is a CLI script where
      // console IS the right interface -- see its own override below,
      // which is a deliberate tracked exception, not a silent gap.
      "quality/no-direct-console": [
        "error",
        { logger: "logError (treino/logger.js or worker/logger.js)" },
      ],
    },
    // quality/no-direct-data-access is intentionally not configured: this
    // repo has no shared database/ORM client for a presentation layer to
    // reach around. The backend/ Python API owns persistence; the
    // JS/TS side here is a static client app plus a thin Cloudflare Worker
    // proxy, with no data module of its own.
  },
  {
    // The logging adapters themselves -- this block MUST come after the
    // block that turns quality/no-direct-console on above: for a file
    // matched by both, flat config applies the later block's rules last,
    // so an "off" placed earlier would be silently overridden by the
    // "error" that follows it.
    files: ["treino/logger.js", "worker/logger.js"],
    rules: {
      "quality/no-direct-console": "off",
    },
  },
  {
    // orcamento-marcenaria/engine/gerar_orcamento_docx.js is a standalone
    // CLI script (`node gerar_orcamento_docx.js dados.json saida.docx`):
    // console IS its correct, intended output surface, not a logging
    // shortcut to clean up. Tracked exception (lint burn-down, 2026-09),
    // not a silent gap -- see docs/prompts/02-eslint-warning-burndown.md.
    files: ["orcamento-marcenaria/engine/gerar_orcamento_docx.js"],
    rules: {
      "quality/no-direct-console": "off",
    },
  },
  {
    files: ["eslint-rules/**/*.cjs"],
    languageOptions: {
      sourceType: "commonjs",
      globals: { module: "readonly", require: "readonly", __dirname: "readonly" },
    },
  },
  {
    // Temporary self-check script (deleted after step 5); real Node ESM.
    files: ["verify.mjs"],
    languageOptions: {
      sourceType: "module",
      globals: { process: "readonly" },
    },
  },
  globalIgnores([
    ".claude/**",
    ".github/agents/**",
    ".github/hooks/**",
    ".github/skills/**",
    ".agents/**",
    "node_modules/**",
    "**/node_modules/**",
    "android/**",
    "backend/**",
    "dist/**",
    "build/**",
    "coverage/**",
    "orcamento-marcenaria/output/**",
    "package-lock.json",
  ]),
]);
