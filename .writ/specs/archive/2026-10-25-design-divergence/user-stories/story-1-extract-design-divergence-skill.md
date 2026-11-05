# Story 1: Extract the design-divergence Skill and Register It

> **Status:** Completed ✅ (2026-10-26)
> **Commit:** 42754d7b076313a6777d8487fc03a585e993a0b4
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer
**I want to** move the divergence rules from `/prototype` Step 2.5 into one skill file, add the usage-first rule and the axis catalogs for UI, API shape, and data model, and register the skill everywhere skills are registered
**So that** `/prototype` and `/implement-story` Gate 0 (Stories 2 and 3) can load one shared procedure for getting alternatives that differ, and the skill is discoverable and lint-clean before either caller depends on it

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given `skills/design-divergence/SKILL.md`, when `bash scripts/lint-skill.sh skills/design-divergence/SKILL.md` runs, then line 1 is `pass`, and the frontmatter carries `name: design-divergence`, a description starting with the verb "Generate", `disable-model-invocation: true`, and `status: candidate` `[AC-1.1]`
- [x] Given the skill body, when it is read, then `## How to Apply` states the eight rules from technical-spec.md → Skill (usage first, axes first, independent contexts, commit before drafting, ordinary personas, two or three drafts, the anti-pattern with its reason, same model family), and one axis-catalog table covers UI, API shape, and data model; `## Examples` holds one API example and one data-model example; no body line starts with `/`, and the body contains no `Read commands/`, `Read skills/`, or `Task(` text `[AC-1.2]`
- [x] Given registration, when `bash scripts/gen-skill.sh --check` runs, then it prints `pass`; `.writ/manifest.yaml` has one alphabetically placed `design-divergence` entry with `status: candidate` and `tags: [design, divergence, exploration]`; the root `SKILL.md` catalog lists the skill; and README.md's `## Skills` table has one row for it `[AC-1.3]`
- [x] Given the generated trees were regenerated with `python3 scripts/gen-platform-trees.py`, when `python3 scripts/gen-platform-trees.py --check` runs, then it prints `pass`, and the skill appears in the generated plugin trees with no generated file edited by hand `[AC-1.4]`
- [x] Given the change, when `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` run, then all pass with 0 findings, including the skill-manifest-parity and skill-lifecycle checks `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write failing tests in new `scripts/tests/test_design_divergence_wiring.py` for the skill file: frontmatter fields, lint pass, required sections, the three media, the anti-pattern rule, and no forbidden body patterns `[AC-1.1, AC-1.2]`
- [x] 1.2 Write `skills/design-divergence/SKILL.md`, starting from `commands/prototype.md` Step 2.5 "Getting drafts that actually differ" and the prototype research Recommendation 2 (`.writ/research/2026-10-19-prototype-visual-drafts-research.md`); read `skills/plain-prose/SKILL.md` first `[AC-1.1, AC-1.2]`
- [x] 1.3 Add the `design-divergence` entry to `.writ/manifest.yaml` and run `bash scripts/gen-skill.sh` to regenerate the root `SKILL.md` catalog `[AC-1.3]`
- [x] 1.4 Add the `design-divergence` row to README.md's `## Skills` table `[AC-1.3]`
- [x] 1.5 Regenerate the platform trees with `python3 scripts/gen-platform-trees.py` and confirm `python3 scripts/gen-platform-trees.py --check` prints `pass` `[AC-1.4]`
- [x] 1.6 Verify acceptance criteria AC-1.1 through AC-1.4 by running the lint, gen-skill check, and tree check, and by reading the skill body against the eight rules and the axis table `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.7 Verify all tests pass: `uv run pytest`, `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` run outside the sandbox `[AC-1.5]`

## Notes

- **Ownership boundary.** The skill owns how to get alternatives that differ: axes, independence, commitment, personas, count, the anti-pattern, and model family. Callers own when to run it, what a draft is in their medium, how drafts are rendered or shown, and where the decision is recorded (spec Business Rule 9). Keep caller-specific steps out of the skill body. Do not describe the Step 2.5 render table or the Gate 0 report line in the skill.
- **Command, agent, skill boundary.** Apply the boundary in `commands/new-skill.md` before writing the file. The skill is a procedure a command or agent reads. It is not a command, and it does not spawn agents or name a Task call. The `Task(` and `Read commands/` checks in AC-1.2 enforce this.
- **Cross-vendor drafting is out of scope.** Drafts come from the session's model family (ADR-024). Do not add routing to other vendors, even as an example.
- **Medium coverage.** Three axis tables only: UI, API shape, data model. Two or three rows each, as in technical-spec.md → Skill. Do not add a fourth medium.
- **Examples.** The API example shows two axis commitments and the usage line each one changes. The data-model example follows the same shape. Keep each example short. Story 1 does not run the trial, so the examples are illustrative, not measured.
- **Integration points.** Story 2 replaces `commands/prototype.md` Step 2.5 rules with a `Read skills/design-divergence/SKILL.md` line. Story 3 adds the Gate 0 `Read` line. Neither caller changes in this story, so the skill's existence and lint status are the only contract Stories 2 and 3 depend on.
- **Status stays candidate.** The skill keeps `status: candidate` until the blind trial (Story 6) gives a verdict. Do not promote it here.
- **Generated files.** Regenerate with the scripts. Do not hand-edit `plugins/writ/**`, `cursor/plugin/**`, `codex/AGENTS.md.template`, or the root `SKILL.md`. Task 1.5's `--check` must pass on the committed result.
- **Test runtime.** `bash scripts/eval.sh` runs `git init` in a temp directory. Run it outside any sandbox (task 1.7).
- **Python floor.** The suite must stay green on Python 3.9. Use stdlib only in `test_design_divergence_wiring.py`.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 9 (skill boundary: the skill owns how to get alternatives that differ; callers own when, what a draft is, rendering, and the record)] — from spec.md → ## Business Rules (Expanded), item 9
- **Error map rows:** []
- **Shadow paths:** []
- **Experience:** []

Pointers for this story's content:

- spec.md → Specification Contract → Must Include, item 1 (skill, status, registration, media, axis catalogs)
- technical-spec.md → Skill: `skills/design-divergence/SKILL.md` (frontmatter, body sections, the eight rules, axis table, examples, registration)
- technical-spec.md → Files in Scope → rows for Story 1
- spec.md → Detailed Requirements → Story 1: Extract the skill and register it

---

## What Was Built

**Implementation Date:** 2026-10-26

### Files Created

1. **`skills/design-divergence/SKILL.md`** (126 lines)
   - `status: candidate` skill: eight rules under `## How to Apply` (usage first, axes first, independent contexts, commit before drafting, ordinary personas, two or three drafts, the anti-pattern with its reason, same model family), an axis catalog with one table each for UI, API shape, and data model, and one API and one data-model example.
2. **`scripts/tests/test_design_divergence_wiring.py`** (382 lines)
   - 26 stdlib wiring tests: frontmatter, lint `pass`, section order, the eight rules in order, per-medium tables, examples, forbidden body patterns, manifest entry, catalog row, README row, generated copies.
3. **`plugins/writ/skills/design-divergence/SKILL.md`**, **`cursor/plugin/skills/design-divergence/SKILL.md`** — generated by `scripts/gen-platform-trees.py`.

### Files Modified

- **`.writ/manifest.yaml`** (`skills:`)
  - `design-divergence` entry between `dependency-context-loading` and `drift-triage`, `status: candidate`, `tags: [design, divergence, exploration]`.
- **`README.md`** (`## Skills` table)
  - One row for the skill.
- **`SKILL.md`** (root catalog) — regenerated by `scripts/gen-skill.sh`.
- **`codex/AGENTS.md.template`** — one skill row, regenerated by `scripts/gen-platform-trees.py`.

### Implementation Decisions

1. **No caller-specific text in the skill** — no render table, Gate 0, report line, or `exploration.md`; the wiring test enforces it (Business Rule 9).
2. **Primary action placement kept** — the UI table holds three rows; one line under it keeps the inline Step 2.5 axis that Story 2 deletes (Gate 3 recommendation).

### Test Results

**Verification:** `uv run pytest scripts/tests/test_design_divergence_wiring.py -q` → 26 passed; `bash scripts/lint-skill.sh skills/design-divergence/SKILL.md` → pass; `bash scripts/gen-skill.sh --check` → pass; `python3 scripts/gen-platform-trees.py --check` → pass; full `uv run pytest` → 3097 passed, 2 skipped; `bash scripts/eval.sh` → 0 findings.
- ✅ test-integrity authenticity: pass; coverage: unverifiable (no coverage report; markdown deliverable)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small
- **Security:** Clean
- **Boundary Compliance:** every change is owned or a registration/generated file AC-1.3 and AC-1.4 require
- **gate3-route:** review-agent (outside_boundary README.md; outside_boundary SKILL.md; outside_boundary codex/AGENTS.md.template; outside_boundary cursor/plugin/skills/design-divergence/SKILL.md; outside_boundary plugins/writ/skills/design-divergence/SKILL.md)
- **review-panel:** skipped — platform cannot spawn other vendors

### Deviations from Spec

- **[DEV-001] One axis-catalog table per medium, not one shared table** — Severity: Small
  - Spec said: AC-1.2 "one axis-catalog table"; technical spec "one table per medium"
  - Reality: three per-medium tables under `### Axis catalog`
  - Resolution: Auto-amended (Small); no spec-lite change needed
