# Story 4: Safety fact at Gate 3

> **Status:** Completed ✅ (2026-10-29)
> **Commit:** 149dc40597653ace9c5129b385f4176db417e28c
> **Priority:** High
> **Dependencies:** Story 1, Story 2, Story 3

## User Story

**As a** review-agent on the risk route, the `/implement-story` orchestrator, or the maintainer reading story reports
**I want to** get one named safety fact for each Gate 3 review, with its evidence rung re-derived by a script
**So that** a reader sees why the change is safe and how well that was checked, and an unevidenced claim fails Gate 3

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given fixture review outputs that cite evidence for each of the five rungs (`claimed`, `read`, `traced`, `tested`, `reproduced`), when `review-override.py safety-fact` runs on each, then it prints the measured rung that the technical-spec ladder table assigns to that evidence, and a cited path that does not exist or resolves outside `--repo` is rejected so the rung does not count `[AC-4.1]`
- [x] Given a review output whose `Rung` is `traced`, when the blast-radius file is readable with verdict `pass`, then `traced` is accepted only when at least one cited caller is in the union of its `consumers`, and `- traced: none` is accepted only when that union is empty and the file's verdict is `pass` `[AC-4.2]`
- [x] Given review outputs that trigger each fail reason, when the verifier runs, then `safety_fact_missing`, `safety_fact_below_floor <measured>`, and `safety_fact_contradicts_verdict` each fire on their own condition, every applicable reason prints in table order, an overclaim alone prints the `rung:` line without a fail, and an unreadable review output prints `unverifiable` with `review_output_unreadable` and exits 0 `[AC-4.3]`
- [x] Given the review-agent route with the `safety-fact` switch on, when Gate 3 runs, then it runs the verifier and routes each reason as spec.md → Business Rules → Verifier outcomes states, and the one re-review counts as the same Gate 3 attempt with no `review_cycle` increment `[AC-4.4]`
- [x] Given the `safety-fact` switch off, or the evaluator route, when Gate 3 runs, then no `### Safety Fact` section is requested, no verifier runs, and the story report prints `safety-fact: off` or `safety-fact: not on route`, and a pytest fails if any ladder rung definition appears in `agents/*.md`, `commands/*.md`, or `claude-code/agents/*.md` `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write verifier tests first in `scripts/tests/test_review_override.py` (rung fixtures, path escape, `traced` consumers rule, fail reasons, unreadable output) and the ladder-placement test in `scripts/tests/test_review_route_rigor.py` `[AC-4.1, AC-4.2, AC-4.3, AC-4.5]`
- [x] 4.2 Implement the `safety-fact` subcommand in `scripts/review-override.py`: parse the section, re-derive the measured rung, print `pass` or `fail` with reasons, `rung:` and `fact:` lines, and summary last `[AC-4.1, AC-4.2, AC-4.3]`
- [x] 4.3 Write `skills/blast-radius/SKILL.md` (ladder, Safety Fact section format, push-up rules, reading `blast_radius`, `Holds: no`) and its `.writ/manifest.yaml` entry; add its README `## Skills` row, update the live-skill count, and regenerate the root `SKILL.md` with `bash scripts/gen-skill.sh` `[AC-4.5]`
- [x] 4.4 Edit `agents/review-agent.md`: add input rows `recorded_test_results`, `safety_fact`, `blast_radius`, one conditional `Read skills/blast-radius/SKILL.md` line, and a one-line output slot; add no ladder text `[AC-4.4, AC-4.5]`
- [x] 4.5 Edit only the `#### Gate 3` section of `commands/implement-story.md`: pass inputs on the risk route, save review output and recorded test run under `.writ/state/`, run the verifier, route reasons, print the `safety-fact:` lines; measure growth with `wc -c` against the 1,800-byte cap shared with Gate 2.5 `[AC-4.4, AC-4.5]`
- [x] 4.6 Regenerate trees with `python3 scripts/gen-platform-trees.py` and confirm the generated `claude-code/agents/` files match their sources `[AC-4.5]`
- [x] 4.7 Verify acceptance criteria: run `uv run --python 3.9 pytest`, the bash test loop, `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh`; check each AC against its test output `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

- `reproduced` is out of reach on a first Gate 3 pass. Gate 4.5 runs after Gate 3. The verifier can accept `reproduced` only on a recode iteration where a passing `app-verify-result-v1` file already exists for the story.
- Panel reviewers receive the same inputs as the primary reviewer. The verifier reads only the primary reviewer's output.
- A false safety fact is reported with category `architecture` (or `security` when it is one). This keeps `review-panel.py` keying unchanged.
- Do not touch Gate 0, Step 4, `agents/coding-agent.md`, or `skills/tdd-cycle/`.
- Byte budget: Gate 2.5 and Gate 3 together grow by at most 1,800 bytes net. `commands/implement-story.md` is already over the per-invocation budget. Keep the how in the skill and the when in the gate.
- The blast radius is a text-reference heuristic, not a call graph. Story 3 owns it. This story reads its JSON only.
- Integration: Story 1 provides the `switch` subcommand that Gate 3 calls. Story 2 and this story both edit `agents/review-agent.md` and `.writ/manifest.yaml`. Apply Story 2's changes first.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [`safety-fact` reads review output, `safety-fact` resolves a cited path, `safety-fact` reads blast radius, `safety-fact` reads tests output] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Safety-fact verify, Gate 3 routing] — from technical-spec.md → Shadow Paths
- **Business rules:** [When the safety fact applies (required only on `gate3_route` = `review-agent` with switch on), Verifier outcomes (one re-review, then BLOCKED or recode), unverifiable never DEGRADED] — from spec.md → Business Rules (Expanded)
- **Experience:** [State Catalog rows for risk route, `safety-fact` off, and unverifiable (story report lines)] — from spec.md → Experience Design → State Catalog
- **Ladder and section format:** technical-spec.md → Evidence Ladder, Safety Fact Section, Verifier (parsing and output table)
- **Gate 3 wording:** technical-spec.md → Gate 3 Change (draft); byte budget in the same section

## What Was Built

**Implementation Date:** 2026-10-29

### Files Created

- **`skills/blast-radius/SKILL.md`** — `status: candidate`, one consumer (`agents/review-agent.md`). The five-rung Evidence Ladder (`claimed`, `read`, `traced`, `tested`, `reproduced`: meaning and evidence line), the `### Safety Fact` section format (heading exactly `### Safety Fact`), the rules (one fact, a fact about the code, push up the ladder, `Holds: no` → cite the breaking caller and FAIL with `architecture` or `security`), reading the `blast_radius` JSON, when `reproduced` can be cited, and how to use the appended `rung:`/`reason:` lines on a re-review. Example citations are repo-neutral (`src/parser.py:142`).
- Generated skill copies: `plugins/writ/skills/blast-radius/SKILL.md`, `cursor/plugin/skills/blast-radius/SKILL.md`.

### Files Modified

- **`scripts/review-override.py`** (`safety-fact` subcommand) — `safety-fact --review-output FILE [--repo .] [--blast-radius FILE] [--tests-output FILE]`. Parses the section (heading `^#{2,6}\s*Safety Fact\s*$`, fields case-insensitive, bold optional, backticks stripped), re-derives the measured rung (highest accepted, non-cumulative; every line of a rung must be accepted), enforces the `traced` floor and the consumers-union rule, and prints line 1, `rung: claimed=… measured=…`, `fact:`, `reason:` lines in table order, summary last. Repo-relative paths only; `..`/absolute/symlink escapes rejected. Unreadable review → `unverifiable` exit 0; no `--review-output` → exit 2. Huge line numbers and deeply nested JSON are rejected, not a traceback. `check` and `switch` unchanged.
- **`agents/review-agent.md`** — input rows `recorded_test_results`, `safety_fact`, `blast_radius`; a `{recorded_test_results}` prompt block (DEV-018); the conditional line "When `{safety_fact}` is `on`, `Read skills/blast-radius/SKILL.md` and write its `### Safety Fact` section, starting from `{blast_radius}`."; the output slot after Security Assessment. No ladder text.
- **`commands/implement-story.md`** (`#### Gate 3` only) — review-agent inputs gain `recorded_test_results`, `blast_radius`, `safety_fact` (`on` unless `blast_radius` is `(none)`); the **Safety fact** paragraph saves `gate3-review-<story-stem>.md` and `gate3-tests-<story-stem>.txt`, runs the verifier, routes first-match (contradicts → FAIL; missing/below floor → one re-review in the same Gate 3 attempt, then BLOCKED or FAIL with "add a test that exercises the fact"; pass/unverifiable/crash → continue, never DEGRADED), and prints `safety-fact: <measured> (claimed <claimed>) — <fact>`, `safety-fact: off`, or `safety-fact: not on route`. File 39,076 → 40,229 bytes (+1,153; Gate 2.5 + Gate 3 total +1,795 of the 1,800 cap).
- **`scripts/tests/test_review_override.py`** — 53 verifier tests (Story 4 section). **`scripts/tests/test_review_route_rigor.py`** — 28 wiring and isolation tests (Story 4 section).
- **`scripts/tests/test_governor_enforcement.py`** — `KNOWN_OVER_BUDGET["commands/implement-story.md"]` 14116 → 15269, dated.
- **`.writ/manifest.yaml`** — `blast-radius` entry. **`README.md`** — Skills row; live count 18 → 19. **`SKILL.md`** — regenerated.
- Regenerated: `claude-code/agents/writ-reviewer.md`, `codex/agents/review-agent.toml`, `codex/AGENTS.md.template`, and the `cursor/plugin/` and `plugins/writ/` agent, command, and script copies.

### Implementation Decisions

1. **Gate 0 divergence chose sketch A** — Gate 3 prose owns routing and the verifier prints only the contract lines; sketch B added `--spawn`, `next:`, and `evidence:` names and changed the verifier usage.
2. **Contradiction routes first** — a reviewer that found the fact does not hold goes straight to recode (DEV-019).
3. **Dogfooded on this story** — Gate 2.5 wrote `.writ/state/blast-radius-story-4-gate-3-safety-fact.json`; the Gate 3 reviewer wrote a Safety Fact; the verifier measured it: `pass`, `rung: claimed=traced measured=traced`.
4. **Post-review fixes** — after Gate 3 PASS, the coder applied review recommendations 1–3 test-first: crash-proof citation parsing, a pin on the Gate 3 condition, neutral skill example paths.

### Test Results

**Verification:** `uv run --python 3.9 pytest scripts/tests/test_review_override.py scripts/tests/test_review_route_rigor.py -q` → 140 passed (also on 3.12); recorded Gate 3 run of 5 files → 347 passed; full 3.9 suite → 3436 passed, 3 skipped, 1 working-tree-only failure (`test_review_agent_not_in_story_edit_set`); `bash scripts/eval.sh` → 0 findings; `gen-platform-trees.py --check`, `gen-skill.sh --check`, `lint-skill.sh` → pass.
- ✅ test-integrity authenticity: pass
- coverage: unverifiable (no_coverage_report) — markdown skill; script covered by subprocess tests

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Medium
- **Security:** Low (path containment via resolve; read-only; no subprocess)
- **Boundary Compliance:** eight owned files; README, root SKILL.md, governor pin, and generated trees justified
- **gate3-route:** review-agent (outside_boundary README.md; outside_boundary SKILL.md; outside_boundary scripts/tests/test_governor_enforcement.py; outside_boundary for 10 generated copies)
- **reviewer-filters:** on
- **safety-fact:** traced (claimed traced) — Gate 3 asks for and verifies a Safety Fact only on a `review-agent` spawn whose `safety_fact` is on, and the default `evaluator-agent` spawn receives no `safety_fact` or `blast_radius` input
- **gate0-divergence:** chose A (prose routing × contract lines only) — B added `--spawn`, `next:`, and `evidence:` names
- **review-panel:** skipped — platform cannot spawn other vendors
- **review-override check:** pass (no blocking helper finding)
- **jev shadow:** unverifiable (state_too_large) — advisory only

### Deviations from Spec

- **[DEV-012] Story report line leaves out the State Catalog outcome suffixes** — Severity: Medium — Resolution: Flagged for review
- **[DEV-013] `Holds: no` with no verdict line is a contradiction** — Severity: Small — Resolution: Auto-amended
- **[DEV-014] No section prints `missing section` and `below_floor none`** — Severity: Small — Resolution: Auto-amended
- **[DEV-015] Every evidence line of a rung must be accepted, for every rung** — Severity: Small — Resolution: Auto-amended
- **[DEV-016] Absolute cited paths are rejected even inside `--repo`** — Severity: Small — Resolution: Auto-amended
- **[DEV-017] `tested` accepts pytest node IDs** — Severity: Small — Resolution: Auto-amended
- **[DEV-018] `review-agent` gains a `## Recorded Test Results` prompt block** — Severity: Small — Resolution: Auto-amended
- **[DEV-019] Routing precedence when reasons co-occur** — Severity: Small — Resolution: Auto-amended
