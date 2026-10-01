# Behavioral Verification

> **Status:** Not Started
> **Created:** 2026-10-01
> **Owner:** @unknown
> **Dependencies:** []
> **Phase:** 12 — Behavioral Verification (Features 1 and 2, merged at contract lock)
> **Amends:** [adr-028-behavioral-verification-and-cross-family-panels](../../decision-records/adr-028-behavioral-verification-and-cross-family-panels.md) Decisions 1 and 2
> **Origin:** `/create-spec` discovery, 2026-10-01. ADR-028 named a generated `verify-<app>` skill produced by `/initialize`. Discovery replaced it with a recipe document authored by `/create-uat-plan`, because `/initialize` runs before any feature exists and gathers perspective for `/plan-product`. It also merged Features 1 and 2, because the recipe's only consumers are the UAT binding and Gate 4.5, and Writ's live-consumer rule says a recipe nothing reads is dead weight.

## Specification Contract

**Deliverable:** Writ can prove a story's feature works by running the project's own checks against the running app, with saved evidence. A per-project recipe at `.writ/docs/app-verification.md` says how; `/create-uat-plan` drafts it; Gate 4.5 runs it; `exit-criteria.py` checks that the cited evidence exists.

**Must Include:** A pass/fail verdict decided by a machine (exit code or test assertion), never an agent's opinion.

**Hardest Constraint:** Writ ships no runtime. The recipe names the project's own commands; Writ only starts them, records the result, and stops what it started.

**🎯 Experience Design:**
- **Entry point:** `/create-uat-plan` on a spec. When the recipe is missing, it drafts one from the project's harness, scripts, and test folders and asks the developer to confirm it.
- **Happy path:** confirm the recipe → UAT scenarios cite feature IDs → during `/implement-story`, Gate 4.5 runs the checks for features the story touched → evidence lands in `{spec}/evidence/` → the story completes.
- **Moment of truth:** a UAT scenario reads "passed — evidence: `evidence/uat/event-create/result.json`" instead of "human, please check."
- **Feedback model:** one line per feature: `pass`, `fail`, or `human-only: <reason>`.
- **Error experience:** a missing recipe, an undrivable feature, or a refused safety check each print one line and fall back to today's behavior. None silently passes.

**📋 Business Rules:**
1. Recipe sections: Launch, Safety, Login, Feature Map, Evidence, Cleanup. A feature entry has either a `check` command or `human-only: <reason>`.
2. Automate as much as possible, as long as a machine decides. When a feature has no check, the coding agent may write one into the project's own test folder, reviewed like any other test. An agent never grades a result.
3. Safety refuses by default. The recipe names the environment variable(s) and the targets allowed for verification runs; anything else, and nothing runs. Writ never edits the project's environment files, migrations, or data.
4. Cleanup stops only processes Writ started and always keeps the evidence.
5. Gate 4.5 becomes behavioral verification, decided by the script (`verification: script`), so the `prose-only` count in `implement-story.md` drops from 2 to 1. The mockup comparison stays as an optional comment under `--full-pipeline` and cannot fail the story.
6. A UAT scenario citing an evidence file that does not exist reports `unmet` in `exit-criteria.py`, proven by mutation.
7. Gate 4.5 runs a script, not an agent, so the two-subagent default pipeline is unchanged.

**Success Criteria:** A fixture app's UAT scenarios pass end to end with machine-captured evidence and no human step. The Gate 4.5 `prose-only` count drops to 1 and `eval.sh` enforces a cap of 1. The missing-evidence mutation reports `unmet`. `uv run pytest` (Python 3.9+), the bash tests, and `bash scripts/eval.sh` are green.

**Scope Boundaries:**
- **Included:** recipe format and validator; `/create-uat-plan` drafting and scenario binding; the run script (safety, launch, check, evidence, cleanup); Gate 4.5 rewrite in `implement-story.md` and its `.lean` twin; `exit-criteria.py` evidence check; a fixture app; ADR-028, roadmap, and mission amendments.
- **Excluded:** yuss.app or any external project; agent-judged browser checks; the cross-family review panel (its own spec); a Writ-owned browser or test runner; raising the autonomy ceiling; any change to `/initialize`.

**Stories:**
1. Recipe format, validator, and product amendments
2. `/create-uat-plan` drafts the recipe and binds scenarios to feature IDs
3. Run script and fixture app (safety, launch, check, evidence, cleanup)
4. Gate 4.5 becomes behavioral verification; mockup comparison becomes advisory
5. `exit-criteria.py` evidence check, mutation test, and eval check

**⚠️ Technical Concerns:**
- A Writ script that starts project commands sits close to "Writ ships no runtime." It stays on the right side because it runs only commands the recipe names, keeps no state between runs, and runs no daemon — the same posture as `eval.sh` and `build-smoke.py`. Story 1's ADR amendment states this explicitly.
- `/create-uat-plan` runs after stories finish, so Gate 4.5 cannot learn a story's features from UAT scenarios. Each feature-map row lists the source paths it covers; Gate 4.5 runs every feature whose paths intersect the story's changed files. This is mechanical and needs no new authoring step.
- `commands/implement-story.md` is over its byte budget. Story 4's edit must be net-tight and re-pin the ratchet with disclosure, as earlier specs did.

**💡 Recommendations:**
- Prove the mechanics on a stdlib-only fixture app under `scripts/tests/fixtures/app-verify/`, with no browser, no Playwright, and no network. Real-project trials (yuss.app or any other) happen outside this spec, at the developer's discretion.
- Writ must never ship a file named `.writ/docs/app-verification.md`; install's three-way overlay would otherwise collide with the project-authored recipe. A test guards it.

**Cross-Spec Overlap:** none — no active spec is in progress.

---

## 🎯 Experience Design

### User Journey

1. **First UAT plan in a project.** The developer runs `/create-uat-plan <spec>`. No recipe exists, so the command scans for a test harness (Playwright, Cypress, pytest, `package.json` test scripts), a dev or start command, a readiness URL or port, and environment files that name a database. It drafts `.writ/docs/app-verification.md` with every feature it can map to an existing check, and marks the rest `human-only: no check yet`. It shows the draft and asks once: save, edit, or skip. Skip keeps today's all-human UAT plan.
2. **Binding.** Each scenario gets `**Feature:**` and `**Verification:**` lines. Machine scenarios run their checks through the run script; the result and evidence path are written into the scenario.
3. **Per story.** In `/implement-story`, Gate 4.5 asks the run script which features the story's changed files touch, runs those checks, and saves evidence under `{spec}/evidence/story-N/`. A failing check sends the story back to Gate 1, counting toward the shared review-loop cap.
4. **New features.** When the recipe exists and a story adds user-facing behavior with no check, the coding agent writes a check in the project's harness and adds a feature-map row. The developer reviews both in the diff.

### State Catalog

| State | What the developer sees |
|---|---|
| No recipe | `app-verify: no recipe — run /create-uat-plan to draft one` (Gate 4.5 skips, as today) |
| Recipe invalid | `app-verify: recipe invalid — <first finding>` (Gate 4.5 skips; `/create-uat-plan` offers to fix) |
| Safety refused | `app-verify: refused — DATABASE_URL does not match an allowed target` (nothing runs) |
| No features touched | `app-verify: no mapped features touched by this story` |
| Checks pass | `app-verify: 2/2 pass — evidence/story-3/` |
| Check fails | `app-verify: 1/2 fail — event-create (exit 1) — evidence/story-3/event-create/` → Gate 1 |
| Launch fails | `app-verify: fail — app not ready after 120s — evidence/story-3/_launch/` → Gate 1 |
| Human-only feature | `app-verify: human-only — google-oauth (third-party login)` |

### Interaction Patterns

- One confirmation, at recipe creation. Gate 4.5 never asks a question.
- Every line starts with `app-verify:` so it greps cleanly in story reports.

---

## 📋 Business Rules (Expanded)

1. **Recipe shape.** Markdown with six `##` sections. Settings are `- **Key:** value` lines, the format `.writ/config.md` already uses. The feature map is a table with columns `ID | Feature | Paths | Check`. `Check` holds a backticked command or `human-only: <reason>`. IDs are kebab-case and unique.
2. **Machine verdicts only.** The verdict is the check's exit code: 0 passes, anything else (including timeout) fails. Screenshots and traces are evidence, never the verdict.
3. **Safety.**
   - `## Safety` either lists one or more `- **Variable:**` entries, each with `- **Allowed:**` patterns, or states `- **Safety:** none — <reason>` for stateless apps.
   - The run script resolves each variable from the process environment, then from the `- **Env file:**` the recipe names (read-only, `KEY=VALUE` lines only), and refuses when the value is unset, matches no allowed pattern, or matches a `- **Never:**` pattern.
   - The recipe stores variable names and patterns, never secret values. The validator rejects values that look like credentials (a URL with `user:password@`, or a long token).
   - If the readiness URL already answers before launch, the script refuses unless `- **Reuse running instance:** yes`, because a running server's environment cannot be checked.
4. **Cleanup.** The script stops the process group it started (terminate, then kill after 10 s) and runs an optional `- **After:**` command. It never stops a process it did not start. Evidence is kept even when cleanup fails.
5. **Gate 4.5 verdicts.** `pass` → continue. `fail` (check failed, launch failed, or not ready) → Gate 1 recode, counting toward the shared 3-iteration cap. `unverifiable` (no recipe, invalid recipe, safety refused, no touched features) → one line, continue as today, and the story is not marked DEGRADED on that basis alone. Launch failure is a fail because the recipe was confirmed launchable when it was saved, so a non-starting app is the story's regression.
6. **Mockup comparison.** Under `--full-pipeline` with visual references, `visual-qa-agent` still runs after the script; its mismatches are written to the story report as notes and never fail the gate.
7. **Evidence.** Each feature run writes `result.json` (feature ID, command, exit code, start and end timestamps, duration, recipe SHA-256, verdict) plus `stdout.log` and `stderr.log`, each truncated to 256 KB, under `{spec}/evidence/<run>/<feature-id>/`. Here `<run>` is `story-N` for Gate 4.5 or `uat` for `/create-uat-plan`. Artifacts named in `## Evidence` are copied up to 5 MB per feature; larger ones are recorded by path only.
8. **Evidence check.** For every UAT scenario with `**Verification:** machine`, `exit-criteria.py` resolves the cited evidence path relative to the spec folder; a missing file, or a `result.json` whose verdict is not `pass`, is `unmet`.

---

## Detailed Requirements

- **Run script:** `scripts/app-verify.py`, Python ≥3.9 stdlib only, with subcommands `validate --recipe PATH`, `touched --recipe PATH --changed FILE…` (prints matching feature IDs), and `run --recipe PATH --spec DIR --run-label LABEL [--features id,…]`. Exit codes: 0 pass, 1 fail, 2 unverifiable. One `app-verify:` summary line on stdout plus a JSON object under `--json`.
- **Format doc:** `.writ/docs/app-verification-format.md` (ships to projects) defines the recipe grammar, with one worked example and the fixture recipe as a second.
- **Fixture:** `scripts/tests/fixtures/app-verify/`: `app.py` (stdlib `http.server`, port from `PORT`, stateless), `check_home.py` (GET `/` and assert the body), `check_fail.py` (always exits 1), and recipe variants for pass, fail, safety-refused, and not-ready.
- **Gate entry:** `gates:` frontmatter `gate4_5_visual` → `gate4_5_behavior` with `script: scripts/app-verify.py`; `verdict-provenance.py` `DEFAULT_MAX_PROSE_ONLY` drops to 1.
- **UAT scenario lines:** `**Feature:** <id>` and either `**Verification:** machine — evidence: evidence/uat/<id>/result.json` or `**Verification:** human — <reason>`.

## Implementation Approach

Build bottom-up: grammar and validator (Story 1) → run mechanics on the fixture (Story 3) → two consumers (Stories 2 and 4) → the stop-time evidence check (Story 5). Stories 2 and 4 depend on Story 3 and are independent of each other. Follow existing script conventions (`build-smoke.py`, `exit-criteria.py`): argparse subcommands, JSON output, exit codes 0/1/2, sibling pytest file, an `eval.sh` check function, and `require_literal` pins where command prose cites script behavior. See `sub-specs/technical-spec.md`.
