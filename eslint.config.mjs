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
    // treino/app.js and sw.js are plain browser scripts and the Cloudflare
    // Worker's static-asset service worker: no import/export, loaded via a
    // <script> tag or registered directly, so they parse as scripts, not
    // modules.
    files: ["treino/**/*.js", "sw.js"],
    languageOptions: {
      sourceType: "script",
      globals: {
        caches: "readonly",
        self: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        Blob: "readonly",
        FileReader: "readonly",
      },
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
      // Only one file over budget today (treino/app.js, ~2099 lines) -- a
      // handful of offenders, so the gate stays "error" and that file is
      // listed explicitly instead of the rule being softened for everyone.
      "quality/max-lines": [
        "error",
        { max: 350, ignore: ["treino/app.js"] },
      ],
      // Baseline as of this install: 5 direct console calls (2 in
      // orcamento-marcenaria/engine/gerar_orcamento_docx.js, 2 in
      // treino/app.js, 1 in worker/index.js). No project-wide log adapter
      // exists yet, so "warn" until one is introduced and the count above
      // reaches zero -- then promote back to "error".
      "quality/no-direct-console": [
        "warn",
        { logger: "a project logging helper (none exists yet)" },
      ],
    },
    // quality/no-direct-data-access is intentionally not configured: this
    // repo has no shared database/ORM client for a presentation layer to
    // reach around. The backend/ Python API owns persistence; the
    // JS/TS side here is a static client app plus a thin Cloudflare Worker
    // proxy, with no data module of its own.
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
