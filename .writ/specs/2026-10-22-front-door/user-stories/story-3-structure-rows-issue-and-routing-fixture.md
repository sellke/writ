# Story 3: Structure Rows, Issue Resolution, and Routing Fixture

> **Status:** Completed ✅
> **Commit:** 8bd79dcccb169cc4bc850695073dd29aaf4bf368
> **Priority:** High
> **Dependencies:** Story 1, Story 2

## User Story

**As a** maintainer **I want to** pin the `/writ` rule table and its `entry_level` in the command-structure checker, close the in-your-own-words issue, and record the routing fixture against the rule table **So that** I have evidence the rule table routes real requests as the roadmap intends, and I can review at phase close whether work starts from `/writ`.

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

> **Verified by:** AC-3.3, AC-3.4 — the routing fixture run in What Was Built → Routing Fixture Run (AC-3.3, AC-3.4): 8 of 8 routes matched, so no rule-table correction was needed

> **Verified by:** AC-3.5 — the full pytest, bash test loop, and `bash scripts/eval.sh` runs in What Was Built → Test Results: 2807 passed, 0 bash failures, 0 findings

- [x] Given `scripts/eval-command-structure.py` `ROWS` has a `heading` row for `## Routing Rules` and a `frontmatter` row for `entry_level`, both against `commands/writ.md`, when `python3 scripts/eval-command-structure.py --root .` runs, then both rows report `PASS` and the helper's `self_test()` still passes. `[AC-3.1]`
- [x] Given `.writ/issues/features/2026-10-13-in-your-own-words.md`, when this story is complete, then its last H2 is `## Resolution`, which names this spec, `/writ` Step 1 Restate as the absorbed restatement (it does not end the turn because it routes), and the date 2026-10-22, and its `spec_ref` line is `.writ/specs/2026-10-22-front-door/`. `[AC-3.2]`
- [x] Given the eight requests in `technical-spec.md → ## Routing Fixture`, when Steps 1–3 of `commands/writ.md` are applied to each, stopping before the AskQuestion, then this story's What Was Built gives each request's restatement and proposed route beside its expected route. `[AC-3.3]`
- [x] Given a fixture request whose proposed route differs from its expected route, when the mismatch is resolved, then `commands/writ.md → ## Routing Rules` is corrected, `drift-log.md` records the reason under Spec said / Implementation did / Reason / Resolution, and the fixture table is unchanged. `[AC-3.4]`
- [x] Given the changes from this story, when `uv run --python 3.9 pytest`, the bash test loop, and `bash scripts/eval.sh` run outside any sandbox, then the pytest run and bash loop show no failures and `eval.sh` reports 0 findings. `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write the failing tests first. In `scripts/tests/test_front_door.py` (issue section), add a test that the in-your-own-words issue's last H2 is `## Resolution` and its `spec_ref` is `.writ/specs/2026-10-22-front-door/`. Run it and confirm it fails. Confirm the structure output has no PASS for the two new rows yet. `[AC-3.1, AC-3.2]`
- [x] 3.2 Add the `heading` row (`## Routing Rules`) and the `frontmatter` row (`entry_level`) for `commands/writ.md` to `ROWS` in `scripts/eval-command-structure.py`. Match the heading text exactly. Run `python3 scripts/eval-command-structure.py --root .` and confirm both rows PASS and `self_test()` still passes. `[AC-3.1]`
- [x] 3.3 Append `## Resolution` to `.writ/issues/features/2026-10-13-in-your-own-words.md`. Name this spec, the `/writ` command (Step 1 Restate is the absorbed restatement; it does not end the turn because it routes), and 2026-10-22. Set `spec_ref` to `.writ/specs/2026-10-22-front-door/`. Confirm the task 3.1 test passes. `[AC-3.2]`
- [x] 3.4 Apply `commands/writ.md` Steps 1–3 to each of the eight requests in `technical-spec.md → ## Routing Fixture`, stopping before the AskQuestion. Record each restatement and proposed route beside its expected route in this story's What Was Built. `[AC-3.3]`
- [x] 3.5 For each mismatch between a proposed route and its expected route, correct `commands/writ.md → ## Routing Rules`, record the reason in `drift-log.md` (create it if absent), and re-apply Steps 1–3 to the affected request. Do not edit the fixture table. If no mismatch occurs, record that in What Was Built. `[AC-3.4]`
- [x] 3.6 Run `uv run --python 3.9 pytest` and the bash test loop. Confirm no failures and no `FAIL` lines. `[AC-3.5]`
- [x] 3.7 Run `bash scripts/eval.sh` outside any sandbox. Confirm 0 findings and record the summary line in What Was Built. `[AC-3.5]`

## Notes

**Technical considerations**

- `scripts/eval-command-structure.py`: `KINDS = ("heading", "frontmatter", "invocation")`. `ROWS` is a tuple of (command file, kind, value) rows. Read the module docstring and an existing row before adding one.
- `has_heading` ignores fenced code. The `## Routing Rules` heading must sit outside a code fence in `commands/writ.md`.
- `self_test()` runs one case per kind. The helper prints TSV (`PASS|FAIL\t<name>\t<reason>`) that `check_command_structure` in `scripts/eval.sh` consumes.
- The fixture is applied by the implementing agent reading `commands/writ.md` and reasoning. No script runs it. The recorded table is the evidence.
- Issue pinning: `test_issue_closure_wiring.py` and `test_platform_neutral_names.py::test_issue_resolution` pin other resolutions. This issue has no pin yet, so the test goes in `scripts/tests/test_front_door.py`. Model the resolution on `.writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md`.
- Drift log labels: "Spec said / Implementation did / Reason / Resolution", as in `.writ/specs/2026-10-20-ci-and-update-integrity/drift-log.md`.
- Python 3.9 standard library only.

**Risks**

- A mismatch tempts a fixture edit. The fix goes in the rule table. The fixture table stays as written.
- The structure row value must match the heading text exactly. A mismatch fails `check_command_structure`.

**Integration**

- Stories 1 and 2 must be complete. Story 1 creates `scripts/tests/test_front_door.py` with the command section. Story 2 adds the registration section. This story adds the issue section.
- This story closes the spec. The recorded fixture run and a 0-finding `eval.sh` are the phase-close evidence.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (1 Rule table is the classifier; 2 Tie-break; 3 Restatement shape)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Request names a roadmap phase or feature; Request is a why or how question; Request is a fork; Request lacks a done check or proof)

---

## What Was Built

**Implementation Date:** 2026-10-22

### Files Created

[None created]

### Files Modified

- **`scripts/eval-command-structure.py`** (`ROWS`, first tuple, after the `Artifact Integrity` row)
  - Two rows for `commands/writ.md`: `heading` `Routing Rules` (was: `check_command_structure`) and `frontmatter` `entry_level` (was: `check_entry_level`). `python3 scripts/eval-command-structure.py --root .` → 35 PASS (3 kind self-tests + 32 rows), 0 FAIL, exit 0. `SELF_TESTS` and `self_test()` untouched.
- **`.writ/issues/features/2026-10-13-in-your-own-words.md`** (header `spec_ref`; new last H2 `## Resolution`)
  - `> **spec_ref:** .writ/specs/2026-10-22-front-door/`. The Resolution names 2026-10-22, the lane, this spec, Story 1's commit, `/writ` Step 1 Restate as the absorbed restatement, that it does not end the turn because Steps 2–5 route (ADR-030), the ADR-009 primitive choice (a command, not a skill), the pinning test, and what is not done (no restate-only invocation; pick "Not what I meant" or stop at the confirmation).
- **`scripts/tests/test_front_door.py`** (docstring "Issue and structure section (Story 3)"; `test_issue_resolution`, `test_structure_rows`)
  - `test_issue_resolution` (AC-3.2): last H2 is `## Resolution`, `spec_ref` names the spec folder, the section names the spec, `/writ`, `Restate`, and the date. `test_structure_rows` (AC-3.1): runs the checker through `subprocess.run([sys.executable, …], cwd=REPO_ROOT)`, asserts exit 0, the three `command-structure-kind-*` PASS lines, and the two `commands/writ.md` PASS lines named exactly as `main()` builds them. 490 lines in total; 11 tests.
- **`commands/writ.md`** (Step 2 → Tie-break bullet)
  - One sentence added after the fixture run: "A signal counts here only when the request states it or the restatement can name it; an unstated file count is not a signal, because `/prototype` counts files when it runs and escalates itself." The `## Routing Rules` table is unchanged; 135 lines (DEV-006).
- **`.writ/specs/2026-10-22-front-door/drift-log.md`** — Story 3 section (DEV-006).

### Routing Fixture Run (AC-3.3, AC-3.4)

`commands/writ.md` Steps 1–3 applied to each request in technical-spec.md → Routing Fixture, stopping before the AskQuestion, by the coding agent and again by the orchestrator; the evaluator re-applied requests 2, 6, and 7. `.writ/product/roadmap.md` is present with `## Phase 15: Code-Level Rigor`. No request names evidence, so every `Proof:` line reads `(not stated — see prompting-guide.md § What a request carries)`; "(implied)" marks a done check derived from the request rather than stated.

| # | Request | Restatement (condensed) | Proposed route (row, reason) | Expected | Match |
|---|---|---|---|---|---|
| 1 | "users can't paste into the search box on Safari" | Goal: pasting into the search box works on Safari. Problem: on Safari the box drops pasted text. Done check: a paste on Safari fills the box and the search runs (implied). Proof: (not stated) | `/prototype --no-diverge` (row 2: a bug with one obvious shape; no escalation signal named) | `/prototype --no-diverge` | Yes |
| 2 | "a settings page where people can manage API keys" | Goal: users create, view, and revoke API keys from a settings page. Problem: no place to manage keys today. Done check: (not stated). Proof: (not stated) | `/create-spec` (row 3: a capability users will rely on; key storage is a schema change and key handling is security-sensitive, so the tie-break also lands here) | `/create-spec` | Yes |
| 3 | "something to make onboarding feel less empty" | Goal: a new user's first screens feel populated. Problem: onboarding shows empty states with nothing to do. Done check: (not stated). Proof: (not stated) | `/prototype` (row 1: names a goal, not a change; "something" leaves the direction unsettled) | `/prototype` | Yes |
| 4 | "do Phase 15" | Goal: Phase 15 (Code-Level Rigor) implemented to its exit criteria. Problem: the phase is committed, its specs unbuilt. Done check: the phase's Success Criteria hold (carried by the roadmap). Proof: (not stated) | `/implement-phase 15` (row 4: names a roadmap phase; roadmap present, `## Phase 15` matched) | `/implement-phase 15` | Yes |
| 5 | "why does the importer skip rows with empty emails?" | Goal: an evidenced explanation of the skip. Problem: unknown whether the skip is intended or a defect. Done check: the reason is stated with the code path that produces it (implied). Proof: (not stated) | `/research` (row 5: a why question; the confirmation notes `/why` takes this route when it ships) | `/research` | Yes |
| 6 | "should we use Postgres full-text search or Meilisearch for this?" | Goal: one search backend chosen on evidence. Problem: two candidates and no measured basis (relevance, latency, operating cost). Done check: (not stated). Proof: (not stated) | `/prototype`, fork named: index the project's data both ways and compare relevance, latency, and setup cost (row 6; a throwaway run answers it faster than asking the person who is asking) | `/prototype` (empirical fork) | Yes |
| 7 | "rename `getUser` to `fetchUser` everywhere" | Goal: every `getUser` reference reads `fetchUser`; nothing else changes. Problem: the name does not say what the function does. Done check: no `getUser` reference remains and the suite passes (implied). Proof: (not stated) | `/prototype --no-diverge` (row 2: a mechanical rename, one obvious shape; "everywhere" is scope, not a file count, and `/writ` reads no code before routing; `/prototype` counts files when it runs and offers `/create-spec --from-prototype` itself) | `/prototype --no-diverge` | Yes |
| 8 | "add multi-tenant billing with per-seat pricing" | Goal: each tenant is billed per seat. Problem: no tenant-scoped billing exists. Done check: (not stated). Proof: (not stated) | `/create-spec` (row 3: a capability users rely on; schema change, new payment dependency, core architecture all fire) | `/create-spec` | Yes |

8 of 8 match; `## Routing Rules` needed no correction and the fixture table is unchanged. Request 7 exposed one ambiguity rather than a mismatch: Step 2's tie-break did not say whether an unstated file count "fires" the `/create-spec` cue. The Tie-break bullet gained one sentence pinning the reading that produced the expected route (DEV-006).

### Implementation Decisions

1. **Rows pinned by structure, not literal** — the `heading` row matches `## Routing Rules` by prefix outside code fences and the `frontmatter` row matches a top-level `entry_level:` key, so a heading that turns into prose or a key that moves into the body fails the check.
2. **The structure test runs the checker** — `test_structure_rows` asserts the checker's own PASS lines rather than re-implementing the matchers, and its `subprocess` call gives the test file a project-script reference for the authenticity checker.
3. **Resolution written against the issue's own expectation** — the issue asked for a restatement that ends the turn; the Resolution says plainly that ADR-030's front door replaces that expectation and names the primitive choice under ADR-009, so a reader of the issue does not look for a restate-only command.
4. **Tie-break clarified in Step 2, not the table** — the table rows are the contract's exact wording; the sentence belongs to the tie-break procedure Business Rule 2 defines and adds no classification machinery (DEV-006).

### Test Results

**Verification:** Automated, test-first (`uv run --python 3.9 pytest scripts/tests/test_front_door.py` red: `2 failed, 9 passed` — last H2 was `## Notes`; the two PASS lines absent; green: `11 passed`), plus the recorded fixture run above.
**Coverage:** Not measured by the script (no coverage report; markdown, one tuple of rows, and test changes only).

- ✅ Targeted: `uv run --python 3.9 pytest scripts/tests/test_front_door.py` → 11 passed.
- ✅ `python3 scripts/eval-command-structure.py --root .` → 35 PASS, 0 FAIL, exit 0.
- ✅ Full pytest (3.9): 2807 passed, 2 skipped.
- ✅ Bash tests: 45 run, 0 failed.
- ✅ `bash scripts/eval.sh`: Findings 0, Run errors 0 (`.writ/state/eval-20261023-031124.md`), the spec's phase-close evidence. Non-blocking leanness WARNINGs (surface lines/chars past justified ceilings) pre-date this spec on the phase branch.
- ✅ Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 0 crossings, route evaluator-agent. Gate 3 review-override: pass; ac-trace: 0 findings. Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: pass. Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-006)
- **Security:** None (markdown edits; one subprocess with a fixed argv list, `cwd=REPO_ROOT`, no `shell=True`)
- **Boundary Compliance:** only owned paths changed (`scripts/tests/test_front_door.py`, `scripts/eval-command-structure.py`, the issue file, `commands/writ.md`); no deviation, no violation.
- gate3-route: evaluator-agent. review-panel: unverifiable (platform_cannot_spawn_other_vendors). jev-shadow: unverifiable (no_api_key). arch-lint: none — see .writ/docs/architecture-lint.md.
- Evaluator residuals, not drift: `test_structure_rows` asserts exit 0 for the whole `ROWS` set, so an unrelated row failing fails this test too (redundant with `check_command_structure`); the rows' `was` values name the consuming check rather than a converted literal pin, as the `Required Artifacts` rows already do. Two taste items were applied before commit: the Resolution's last paragraph no longer calls "Not what I meant" an exit, and `test_issue_resolution` now pins "does not end the turn".
- The evaluator re-applied Steps 1–3 to all eight fixture requests and reached the expected route 8 of 8, with and without the DEV-006 sentence.
- Coding agent and evaluator ran as nested `general-purpose` spawns with the prompt templates from `agents/coding-agent.md` and `agents/evaluator-agent.md`.

### Deviations from Spec

- **[DEV-006] Step 2 tie-break says when an escalation signal counts** — Severity: Small
  - Spec said: Business Rule 2 names the signals that decide the tie-break; neither the rule nor the table says whether an unstated file count counts.
  - Reality: one sentence in the Tie-break bullet: a signal counts only when the request states it or the restatement can name it; `/prototype` counts files when it runs and escalates itself.
  - Resolution: Auto-amended; spec-lite.md Implementation Approach line for the rule table gains the same clause.
