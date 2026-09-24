# Flagged Harness Cuts (Lite)

> Source: .writ/specs/2026-09-24-flagged-harness-cuts/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Three cuts ship default-off and become the default only after a same-model 8-run keep-or-revert on the current default frontier.

**Implementation Approach:**
- `WRIT_HARNESS_LEAN=1` selects `*.lean.md` siblings and spill. Unset loads today’s files.
- Only the five in-scope siblings (`_preamble`, `create-spec`, `verify-spec`, `implement-phase`, `implement-story`) warn when missing under the flag; other commands load their default silently. Loader warnings name the file actually loaded.
- Do not embed both texts in the live command. `measure-invocation.py` must ignore lean siblings when the flag is unset.
- Spill writes the full over-budget text under `.writ/state/` and returns path, size, and a short tail.
- No line that tells the model to use fewer tokens.

**Files in Scope:**
- `scripts/measure-invocation.py` — flag selects the lean floor
- `scripts/story-context.py` — spill only when the flag is on
- `commands/_preamble.md` and `commands/_preamble.lean.md`
- `commands/{create-spec,verify-spec,implement-phase,implement-story}.md` plus `.lean.md` siblings
- `skills/dependency-context-loading/SKILL.md` — lean spill branch only; default truncate stays

**Error Handling:**
- Flag unset and over budget → today’s truncate-and-warn
- Flag set and spill path not writable → warning names the failure; do not silently truncate without saying so
- Baseline quality miss → revert any default flip

**Integration Points:**
- Judge on the current default frontier: Claude Opus 5.5, or GPT-6 Astra when that family is under test. Both outrank the Fable 5.1 run in `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json`.
- Compare flag-on `cost_usd` to a same-model flag-off control. Do not beat the Fable dollar total.
- `scripts/harness-cost.py` prices the pair. `cost_usd` decides, not the $10/$50/$0.25 formula.

**Line Budget Constraints:** `commands/_preamble.md` stays ≤95 lines. The lean preamble is shorter.

---

## For Review Agents

**Acceptance Criteria:**
1. Flag unset: invocation floor bytes match the pre-change measurement, and truncate-and-warn tests still pass. `[AC-1.1, AC-3.2, AC-4.1]`
2. Flag set: lean preamble and the four lean commands are what the loader reports, and an over-budget assemble returns path, size, and tail. `[AC-1.2, AC-2.1, AC-3.1, AC-4.2]`
3. Story 5 ends in keep or null. A null leaves the default load path unchanged. Any exit-criteria row under 2/2 forbids a lasting default flip. `[AC-5.1, AC-5.2, AC-5.3]`

**Business Rules:**
- Cuts may drop restated Plan Mode / `--recommend` text and behavior the current default frontier already does. A keep does not license the lean default for a weaker model.
- Cuts may not drop exit criteria, gates, the production boundary, User Challenge, or stakes triage.
- Lean siblings are excluded from the default floor.

**Experience Design:**
- Entry: `WRIT_HARNESS_LEAN=1` on a baseline run
- Happy path: lean load, spill instead of truncate, then compare
- Moment of truth: compare table plus a keep or null decision-log line
- Feedback: `harness-cost.py` and `pipeline-baseline.py compare`
- Error: quality miss reverts the flip; cost noise is a null, and the spec still completes

---

## For Testing Agents

**Success Criteria:**
1. Unset-flag floor byte count equals the count from before lean files existed.
2. A fixture over the story-context budget spills only when the flag is on.
3. A fake compare with one exit-criteria row under 2/2 does not leave the lean files as the default.

**Shadow Paths to Verify:**
- **Happy path:** flag on, under budget, lean text loads, no spill file
- **Nil input:** variable unset, lean siblings ignored
- **Empty input:** over-budget category is empty — no spill, no false truncation warning
- **Upstream error:** spill directory not writable — warning, payload still names what was kept

**Edge Cases:**
- Preamble lean file over 95 lines → fail the story; do not raise `check_length`
- Both texts pasted into `commands/implement-story.md` → floor test fails

**Coverage Requirements:**
- New code: ≥80%
- Flag-off path: 100% of existing truncate tests still pass
- Keep/revert decision: 100% of the three outcomes (keep, null, quality miss)

**Test Strategy:**
- Unit tests on the loader and `story-context.py` before any baseline spend
- Story 5 is the only story that runs the eight-run baseline
