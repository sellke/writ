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

---

## Story 4: Gate 4.5 Becomes Behavioral Verification — Drift Report

> Run: 2026-10-01
> Overall Drift: Small

### Deviations

#### [DEV-006] Consistency edits outside the Story 4 file list
- **Severity:** Small
- **Spec said:** technical-spec Files in Scope lists the two implement-story bodies, `verdict-provenance.py`, `eval.sh`, `agents/coding-agent.md`, and the tests for Story 4.
- **Implementation did:** Also edited `agents/visual-qa-agent.md` (integration section and FAIL action now notes-only), regenerated `codex/agents/*.toml`, relabeled the quoted prose in `scripts/eval-loop-bounds.py`, and fixed stale visual-QA-recodes wording in `adapters/codex.md` and `commands/design.md`.
- **Reason:** Each file restated the old contract (visual QA FAIL recodes and counts toward the cap) that AC-4.2 removes; boundary-map reported the crossings and Gate 3 judged them justified.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; recorded here.

#### [DEV-007] Check-authoring rule lives in the coding agent, not the command body; byte offset
- **Severity:** Small
- **Spec said:** technical-spec Files in Scope names a "coding-agent check-authoring line" in the implement-story row; AC-4.4 places the rule in `agents/coding-agent.md`.
- **Implementation did:** The single rule is rule 6 in `agents/coding-agent.md` (loaded at Gate 1), with no restatement in the command body. To stay net-tight, one Gate 4 analogy clause ("as `scripts/exit-criteria.py` lets a run report COMPLETE and be published `unmet`") was trimmed; `commands/implement-story.md` is 7 bytes smaller than before. The gate passes `--features` comma-joined, which `run` requires.
- **Reason:** AC-4.4 is the binding contract; a second copy in the over-budget command would only spend bytes.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; recorded here.

---

## Story 2: /create-uat-plan Drafts the Recipe and Binds Scenarios — Drift Report

> Run: 2026-10-01
> Overall Drift: Small

### Deviations

#### [DEV-008] Human-only features are matched from the recipe, not through `touched`
- **Severity:** Small
- **Spec said:** AC-2.3 binds scenarios to the IDs `touched` prints and binds a `human-only: <reason>` feature as human with that reason; AC-3.1 has `touched` never print human-only rows.
- **Implementation did:** Step 4.3 also reads the recipe's `human-only` Feature Map rows whose `Paths` match the story's files, and binds among all matched IDs. Story 3's `touched` interface is unchanged.
- **Reason:** Without it the AC-2.3 human-only rule could never fire (Gate 3 iteration 1 found this as Medium drift; fixed in iteration 2). The match only chooses a binding; verdicts still come from the script.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; recorded here.

#### [DEV-009] Draft validated via a scratch file; other unverifiable reasons; sentence placement
- **Severity:** Small
- **Spec said:** Validate the saved or existing recipe; exit 2 with `refused` → `human — refused`; the never-writes-test-code sentence sits next to the Terminal constraint.
- **Implementation did:** A draft is written to `.writ/state/app-verification-draft.md` and validated there, so a failing draft is never saved to `.writ/docs/`. Exit 2 for any other unverifiable reason writes `human — <reason>`. The sentence sits in the Terminal constraint, which now also says checks run only through `scripts/app-verify.py`; `--check` asks nothing as well as saving and running nothing.
- **Reason:** `validate` needs a file path, and AC-2.2 forbids saving a failing draft; the other changes cover cases the spec left open, failing to the human fallback.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; recorded here.

---

## Story 5: exit-criteria.py Evidence Check, Mutation Test, and Eval Check — Drift Report

> Run: 2026-10-01
> Overall Drift: Small

### Deviations

#### [DEV-010] One reason prefix per unmet outcome; impossible output omits scenarios
- **Severity:** Small
- **Spec said:** AC-5.1 gives `evidence missing: <spec-id> / Scenario 3 (<path>)` as the example reason; AC-5.3 lists `scenarios` in the `check-uat` output.
- **Implementation did:** Reasons use `evidence missing`, `evidence not pass`, `evidence unreadable`, `evidence outside spec folder`, and `evidence path absent`, all as `<prefix>: <spec-id> / Scenario N (<path>[: detail])`. The `check-uat` impossible output carries `schema`, `verdict`, `spec`, and `reason`; `scenarios` appears on met and unmet only, since no plan was read.
- **Reason:** Each outcome stays distinguishable while keeping the AC's shape.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; recorded here.

#### [DEV-011] Parser tolerates bulleted, indented, or capitalized Verification lines
- **Severity:** Small
- **Spec said:** UAT scenario lines are exactly `**Verification:** machine — evidence: <path>` or `**Verification:** human — <reason>`.
- **Implementation did:** The evidence half also reads `- **Verification:** …`, indented lines, and `Machine`, and takes the spec id from the resolved folder name.
- **Reason:** Without it a hand-edited variant silently read as `legacy plan` and c2 was met (Gate 3 iteration 1 finding); tolerance fails closed.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; recorded here.

#### [DEV-012] Referenced-paths allowlist rows for the recipe files (Story 2 follow-up)
- **Severity:** Small
- **Spec said:** AC-5.5 requires the full `eval.sh` to report Findings 0.
- **Implementation did:** Added `referenced_paths_allowlist` rows in `scripts/eval.sh` for `.writ/docs/app-verification.md` and `.writ/state/app-verification-draft.md`, both created by `/create-uat-plan`. Story 2's commit had left the full eval at Findings 2 (its verification ran targeted checks only).
- **Reason:** The paths are runtime artifacts of a named command, exactly what the allowlist records.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; recorded here.
