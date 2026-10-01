# Drift Log

> Spec: .writ/specs/2026-10-01-behavioral-verification/
> Created: 2026-10-01
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Recipe Format, Validator, and Product Amendments — Drift Report

> Run: 2026-10-01
> Overall Drift: Small

### Deviations

#### [DEV-001] Recipe grammar fills in unstated value forms
- **Severity:** Small
- **Spec said:** The Recipe Grammar shows a single `Allowed`/`Never` value and an `http://` Ready URL, and lists `bad_timeout` without valid values or a default.
- **Implementation did:** `Allowed`/`Never` accept comma-separated globs; `Ready when` accepts an http(s) URL or `port N` (Run Contract step 5); `Ready timeout` accepts `30s` or `30` and defaults to 120 s (the State Catalog's "not ready after 120s"); `Safety: none` accepts an em dash, en dash, or hyphen; a `Variable` with no `Allowed` is `missing_safety`.
- **Reason:** Each fills a gap the spec left open without changing the interface Stories 2–5 consume; refuse-by-default is preserved.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Recipe =" line records the value forms; the format doc is the grammar of record.

---

## Story 3: Run Script and Fixture App — Drift Report

> Run: 2026-10-01
> Overall Drift: Small

### Deviations

#### [DEV-002] Summary lines use the parenthetical form
- **Severity:** Small
- **Spec said:** The State Catalog shows `refused — DATABASE_URL does not match…` and `fail — app not ready after 120s — …`; AC-3.1/3.2/3.4 and the technical spec say `refused (<var> …)`, `fail (not_ready <N>s)`, `unverifiable (recipe_invalid: <finding>)`.
- **Implementation did:** Prints `app-verify: refused (<reason>)`, `app-verify: fail (not_ready Ns) — evidence/<label>/_launch/`, `app-verify: fail (launch_exited N) — …`, `app-verify: unverifiable (<reason>)`. Pass, check-fail, no-touched, and human-only lines match the Catalog verbatim.
- **Reason:** The story's ACs and the technical spec are the more specific and later source; the State Catalog's prose forms conflict with them.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Implementation Approach" records the exact line forms consumers quote.

#### [DEV-003] One summary line per run, not one per feature
- **Severity:** Small
- **Spec said:** Feedback model "one line per feature"; AC-3.5 "exactly one `app-verify:` summary line".
- **Implementation did:** One line per run; per-feature verdicts in `--json` and each `result.json`; human-only features in scope are appended as `; human-only — <id> (<reason>)`, and a run selecting only human-only features prints `app-verify: human-only — <id> (<reason>)` with exit 2.
- **Reason:** AC-3.5 is binding; the appended clauses keep every feature visible, so no undrivable feature disappears from a full run (the evaluator's Medium finding, fixed in place).
- **Resolution:** Auto-amended
- **Spec amendment:** Recorded here and in spec-lite.md.

#### [DEV-004] Env file accepts `export` and quoted values; new unverifiable reasons
- **Severity:** Small
- **Spec said:** Env file is `KEY=VALUE` lines only; unverifiable reasons listed as no recipe, invalid recipe, refused, unsupported platform.
- **Implementation did:** Also accepts `export KEY=…` and strips matching quotes (dotenv convention; anything else still refuses). Adds `no_spec_dir`, `unknown_feature: <ids>`, and `no_runnable_features` (all exit 2). Artifact paths that are absolute or contain `..` are recorded `outside_project` and never copied.
- **Reason:** Each closes an input the spec did not cover, failing closed.
- **Resolution:** Auto-amended
- **Spec amendment:** Recorded here.

#### [DEV-005] `After` runs only when the run launched the app; SIGTERM still cleans up
- **Severity:** Small
- **Spec said:** Business Rule 4: stop the started group, run optional `After`.
- **Implementation did:** On the reuse path nothing was started, so neither cleanup nor `After` runs. The CLI turns SIGTERM into a normal exit (code 143) so `finally` cleanup still runs.
- **Reason:** Matches AC-3.5 ("any run that launched the app") and the never-leave-a-process-behind rule.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; recorded here.
