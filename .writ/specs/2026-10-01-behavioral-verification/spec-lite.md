# Behavioral Verification (Lite)

> Source: .writ/specs/2026-10-01-behavioral-verification/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Prove a story's feature works by running the project's own checks against the running app, with saved evidence; recipe at `.writ/docs/app-verification.md`.

**Implementation Approach:**
- `scripts/app-verify.py` (stdlib, Py ≥3.9): `validate`, `touched`, `run`; exit 0 pass / 1 fail / 2 unverifiable; one `app-verify:` line, JSON under `--json`.
- Recipe = six `##` sections, `- **Key:** value` settings, feature table `ID | Feature | Paths | Check`. `Allowed`/`Never` take comma-separated globs; `Ready when` is a URL or `port N`; `Ready timeout` is `30s`/`30`, default 120 s (DEV-001).
- Gate 4.5 picks features by matching `Paths` globs against the story's changed files (UAT plans come later).
- Line forms (DEV-002/003): `app-verify: N/N pass — evidence/<label>/`, `app-verify: K/N fail — <id> (exit C) — evidence/<label>/<id>/`, `app-verify: fail (not_ready Ns|launch_exited C) — evidence/<label>/_launch/`, `app-verify: refused (<reason>)`, `app-verify: unverifiable (<reason>)`, `app-verify: no mapped features touched by this story`; human-only features append `; human-only — <id> (<reason>)`.
- Prove on a stdlib fixture app under `scripts/tests/fixtures/app-verify/`, 127.0.0.1 only. No yuss, no browser.

**Files in Scope:**
- `.writ/docs/app-verification-format.md`, `scripts/app-verify.py`, `scripts/tests/test_app_verify.py`, fixture dir — new
- `commands/create-uat-plan.md` — draft recipe, bind scenarios, run machine checks
- `commands/implement-story.md` + `.lean.md` — Gate 4.5 rewrite, `gates:` entry
- `agents/coding-agent.md` — write a check for new user-facing behavior
- `scripts/verdict-provenance.py` — `DEFAULT_MAX_PROSE_ONLY = 1`, `HEADING_TO_ID["4.5"]`
- `scripts/exit-criteria.py` — c2 evidence half, `check-uat`; `scripts/eval.sh` — `app-verify` check
- ADR-028, `roadmap.md`, `mission.md`, `mission-lite.md` — amendments (preserve uncommitted edits)

**Error Handling:** see `sub-specs/technical-spec.md` → Error & Rescue Map. No recipe / invalid / refused → exit 2, one line, today's path. Launch or check failure → exit 1. Cleanup always runs and keeps evidence.

**Line Budget Constraints:** `implement-story.md` is over budget — net-tight edit, re-pin ratchet with disclosure. `create-uat-plan.md` must stay under 24,960 bytes.

---

## For Review Agents

**Acceptance Criteria:**
1. Recipe grammar documented; `validate` exits 0/1/2 with the named finding codes; Writ never ships `.writ/docs/app-verification.md` `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
2. ADR-028, roadmap, and mission amended without losing pending edits `[AC-1.5]`
3. `/create-uat-plan` drafts the recipe once (save / edit / skip), validates it, binds `**Feature:**`/`**Verification:**`, and marks machine scenarios from script results only `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
4. `touched` maps changed files to features; `run` enforces safety, launch, evidence, and cleanup on the fixture `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
5. Gate 4.5 is script-decided with no spawn; mockup QA is notes only; `prose_only_count: 1 (cap 1)` `[AC-4.1, AC-4.2, AC-4.3, AC-4.5]`
6. Coding agent writes checks for uncovered user-facing behavior and never grades them `[AC-4.4]`
7. Missing or non-`pass` cited evidence makes `implement-phase.c2` unmet; mutation proven; `eval.sh --check=app-verify` green `[AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5]`

**Business Rules:**
- A machine decides: verdict = exit code; screenshots and traces are evidence only.
- Safety refuses by default; recipe holds variable names and patterns, never secret values.
- Cleanup stops only what Writ started.
- Gate 4.5: pass → continue; fail → Gate 1 (shared 3-iteration cap); unverifiable → one line, not DEGRADED. Runs under `--review-only` (fail ends the run); skipped under `--quick`.
- Default pipeline stays at two subagents.

**Experience Design:**
- Entry: `/create-uat-plan` drafts the recipe when it is missing
- Happy path: confirm → bind → Gate 4.5 runs touched checks → evidence → complete
- Moment of truth: scenario shows "passed — evidence: `evidence/uat/<id>/result.json`"
- Feedback: one `app-verify:` line per run
- Error: one line and today's behavior; never a silent pass

---

## For Testing Agents

**Success Criteria:**
1. Fixture UAT scenarios pass with machine evidence and no human step
2. `verdict-provenance.py` reports one prose-only gate; a second is a blocking finding
3. Deleting a cited `result.json` flips c2 / `check-uat` to unmet
4. `uv run pytest` (incl. `--python 3.9`), bash tests, and `bash scripts/eval.sh` green

**Shadow Paths to Verify:**
- **Happy path:** fixture launches → checks pass → `result.json` verdict `pass`
- **Nil input:** no recipe → exit 2 `unverifiable (no_recipe)`
- **Empty input:** no touched features → `no mapped features` line, gate continues
- **Upstream error:** never-ready app → `fail (not_ready)`, cleanup runs, no PID survives

**Edge Cases:**
- Instance already running → `refused (instance_already_running)`
- Check timeout → its process group killed, verdict `fail (timeout)`
- Pre-Phase-12 UAT plan → met, noted `legacy plan`

**Coverage Requirements:** new code ≥80%; every Error & Rescue Map row owned by the run script has a test.

**Test Strategy:** pytest for `app-verify.py` and `exit-criteria.py`; bash hook tests for command prose; one `eval.sh` check (runs outside the sandbox).
