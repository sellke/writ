# Phase 11 Stage 4a: Goal Emit

> **Status:** Not Started
> **Created:** 2026-09-09
> **Owner:** @unknown
> **Dependencies:** [2026-09-05-phase11-repair-and-baseline]
> **Origin:** Promoted from Goal Card [`2026-09-05-writ-contract-and-verifier-layer.md`](../../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) — Stage 4 **emit only** (assessment §5 Step 6). Demote (default ≤2 subagents, fresh-context evaluator) is out of this spec and gets its own later package. Evidence: [`2026-09-05-goldilocks-assessment.md`](../../product/2026-09-05-goldilocks-assessment.md) §5 Step 6; [`adapters/claude-code.md`](../../../adapters/claude-code.md) § The /goal Stop Hook; [`commands/create-goal.md`](../../../commands/create-goal.md) Core Rule 4 (card is not a runner).
> **Loop:** unit `story` · `max_iterations: 8` · `on_exhaustion: halt_reported` · stalled 3 turns: stop and report (carried from the Goal Card's STOP-CAPS)

## Specification Contract

**Deliverable:** A `loop: yes` Goal Card converts to `GOAL.md` + `VERIFY.md` plus a printed Claude Code `/goal` invoke line that is a byte-for-byte copy of the adapter template, with the ADR-013 production boundary quoted verbatim in the emitted files.

**Must Include:** Python 3.9 stdlib emitter; `/create-goal` emit after save (still never registers a hook); `/implement-phase` emit when the phase origin is a Goal Card; Claude Code adapter documents the invoke as copy-paste from the emit; `eval.sh` check; committed fixture round-trip (card → gold files). No live Claude Code session.

**Hardest Constraint:** “Zero manual edits” cannot mean a live `/goal` registration in CI. Prove the round-trip by gold-file equality plus a printed invoke line identical to `adapters/claude-code.md`. A FAIL that means “could not tell” must be `unverifiable`. `loop: no` is skip/unverifiable, not fail.

**Stories:**

1. **CLI + schema** — `scripts/goal-emit.py emit --card PATH [--out DIR]`: read a Goal Card, write `GOAL.md` / `VERIFY.md`, print the invoke line; `check` schema-validates an emit dir; `pass` / `fail` / `unverifiable`.
2. **Hooks** — `/create-goal` after save; `/implement-phase` when origin is a Goal Card; notes only on analysis-class misses; helper missing / exit 2 is a finding.
3. **Adapter + eval + round-trip** — adapter invoke is the emit’s printed line; `eval.sh` `goal-emit` check; gold fixtures; decision-log `{date} stage-4a:`.

**Success Criteria** (Goal Card DONE WHEN line 6, emit half only):

- `scripts/goal-emit.py` exists and is Python 3.9 stdlib.
- `/create-goal` emits after a `loop: yes` save; `/implement-phase` emits when the phase origin is a Goal Card. Neither command registers a `/goal` hook.
- The printed invoke line equals the Claude Code adapter `/goal` template (three-way disjunction already in `adapters/claude-code.md`). ADR-013 sentence present verbatim in both emitted files.
- `bash scripts/eval.sh` has a `goal-emit` check and exits 0 at the end of every story.
- Round-trip recorded in Story 3 What Was Built: fixture card → emit matches gold (`GOAL.md`, `VERIFY.md`, invoke line). Nothing in this spec demotes the five-agent pipeline.

**Scope Boundaries:**

- **Included:** emitter CLI; Goal Card → `GOAL.md` / `VERIFY.md`; create-goal + implement-phase hooks; Claude Code adapter invoke-as-copy; eval check; labeled fixtures + gold equality.
- **Excluded:** five-agent demotion; fresh-context evaluator; `--full-pipeline`; `implement-story` spawn changes; Stage 3 blocking promotion; eight-run; yuss checkout; live Claude Code `/goal` registration; rewriting the three-way disjunction; Codex goal-mode files (no adapter surface today); merge / PR / release.

---

## 🎯 Experience Design

**Entry point.** A maintainer finishes `/create-goal` on a `loop: yes` card, or starts `/implement-phase` whose origin is that card.

**Happy path.** (1) Card is saved. (2) Emitter writes `.writ/goals/<card-stem>/GOAL.md` and `VERIFY.md`. (3) Command prints the `/goal` line. (4) On Claude Code the human pastes that line unchanged. (5) Story 3 records gold equality.

**Moment of truth.** The printed invoke line diffs empty against the adapter template. Both emitted files contain the ADR-013 sentence: `No --recommend command merges, opens PRs, or releases. Production remains a human decision.`

**Feedback model.** One verdict line (`pass` / `fail` / `unverifiable`), optional `reason:` lines, summary last — same family as Stage 2b/3 scripts. Commands relay via `add_note` except helper missing / exit 2 → `add_finding`.

**Error experience.** Missing or unreadable card → `unverifiable`. `loop: no` → `unverifiable` `loop_no` (create-goal still succeeds; no files). Malformed card (missing OBJECTIVE / DONE WHEN / STOP-CAPS) → `fail` `malformed_card`. Missing ADR sentence in a check of already-written files → `fail` `missing_boundary`. No AskQuestion on emit notes.

**State catalog.** Script exists / hooks wired / adapter invoke is copy / eval registered / gold recorded / five-agent default unchanged.

### State catalog (detail)

| State | What the user sees |
|---|---|
| Empty / first card | `/create-goal` save on `loop: yes` creates `.writ/goals/<stem>/` |
| Loading | Emitter runs in-process; no spinner contract |
| Populated | `GOAL.md`, `VERIFY.md`, printed invoke |
| Error | Verdict + `reason:`; card file itself is never deleted |
| Edge | `loop: no` → no emit dir; re-emit overwrites the same stem dir |

---

## 📋 Business Rules

1. **Emit is not register.** `/create-goal` Core Rule 4 stays: the command never registers a `/goal` hook and never iterates. This spec only writes files and prints a line.
2. **`loop: no` does not emit.** Skip with `unverifiable` `loop_no`. Do not write an empty dir.
3. **ADR-013 verbatim.** Both `GOAL.md` and `VERIFY.md` contain the exact sentence `No --recommend command merges, opens PRs, or releases. Production remains a human decision.` (backticks around `--recommend` allowed to match markdown; the words and punctuation otherwise match ADR-013 Decision point 4).
4. **Invoke is copy-paste.** The printed `/goal` line is the three-way disjunction already documented in `adapters/claude-code.md`. This spec does not rewrite clause (a)/(b)/(c). Cursor / Codex / OpenClaw adapters are not required to grow a `/goal` section.
5. **Single-slot reminder stays in the adapter**, not in the emitter. Emitter does not register hooks.
6. **Overwrite is idempotent.** Re-running emit on the same card replaces `GOAL.md` / `VERIFY.md` in the same `--out` dir. It does not append.
7. **Default `--out`** is `.writ/goals/<card-stem>/` where `<card-stem>` is the Goal Card filename without `.md`.
8. **Advisory for helper health only.** A `loop: no` or missing card is a note on the command; a missing `scripts/goal-emit.py` or exit 2 is a finding.
9. **ADR-013 / no yuss / no eight-run / no live `/goal`.** Same honesty as Stages 2b and 3.
10. **Decision log.** Each closing story appends `{date} stage-4a: {what changed}`.

---

## Detailed Requirements

### Story 1 — CLI + schema

`scripts/goal-emit.py` with `emit` and `check`. Python 3.9 stdlib. No LLM API. Required card sections: `## OBJECTIVE`, `## DONE WHEN`, `## STOP-CAPS`, `> **loop:**`. `GOAL.md` carries title, OBJECTIVE, DONE WHEN, STOP-CAPS, ADR-013 sentence, invoke block. `VERIFY.md` carries QUALITY (if present), how to check DONE WHEN, ADR-013 sentence. `check` reads `--out` and validates those files without rewriting the card.

### Story 2 — Command hooks

After `/create-goal` Phase 3 save of a `loop: yes` card, run emit and print the invoke line. `/implement-phase` runs the same emit when the phase’s origin Goal Card path is known (spec `Origin:` / issue `spec_ref` back to a card). Do not call `/goal`. Do not change `/implement-story` spawn.

### Story 3 — Adapter + eval + round-trip

`adapters/claude-code.md` states that the human pastes the emitter’s printed line and that the line must match the existing template. `eval.sh` `goal-emit`: missing helper / exit 2 → finding; emit `pass` / `fail` / `unverifiable` → notes. Fixtures under `scripts/tests/fixtures/goal-emit/` (at least `loop-yes` gold match and `loop-no` unverifiable). Story 3 WWB records gold equality. Decision-log `stage-4a:` line names emit + hooks + gold.

---

## Implementation Approach

Same helper family as `spec-analyze.py`: argparse, verdict line, `reason:`, summary last, exit 0/1/2. Additive `eval.sh` check. Command bodies name the CLI; no new agent file. Installed projects receive `scripts/*.py` via existing `install.sh`.

## ⚠️ Technical Concerns

- Live `/goal` cannot be proven in this repo’s eval. Gold files are the proof; the decision-log must say so.
- Stage 2b and Stage 3 headers still read `Not Started` while their stories are done — do not “fix” those headers in this spec.
- `implement-phase` may not always have a Goal Card origin; missing origin is `unverifiable`, not fail.

## 💡 Recommendations

- Keep the adapter template as the single source of the invoke text; the script copies it from a pinned literal or from the adapter file, documented in the technical spec.
- Demote remains a separate spec. Do not sneak spawn-count changes into the emitter.

## ⚠️ Cross-Spec Overlap

- `2026-09-08-phase11-stage3-spec-analysis` (Not Started header; stories landed) excluded Stage 4 emit — complementary, not a file fight except shared `eval.sh` (additive `CHECKS` only).
- `2026-09-08-phase11-stage2b-mechanize-the-gates` (Not Started header; stories landed) excluded Goal Card → `/goal` emit and five-agent demotion — complementary. Do not change `implement-story.md` spawn.
- Archived `2026-08-12-machine-evaluable-exit-criteria` already wired `/goal` as a delivery vehicle over `exit-criteria.py`. This spec emits files; it does not replace that checker or rewrite the three-way disjunction.
