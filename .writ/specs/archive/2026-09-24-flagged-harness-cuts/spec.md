> **Status:** Complete
> **Created:** 2026-09-24
> **Owner:** @unknown
> **Dependencies:** []

# Flagged harness cuts

## Specification Contract

**Deliverable:** Three harness cuts ship default-off, and become the default only when a same-model 8-run baseline on the current default frontier keeps every exit-criteria row at 2/2 and driver `cost_usd` drops against that model’s own flag-off control.

**Must Include:** A flag-off path that is byte-identical to today’s commands, preamble, and truncation. The keep-or-revert story records a null (flags stay off) as a completed gate, not a failed spec.

**Hardest Constraint:** The last base prune held quality at 8/8 and moved cost about 5%, inside a 59% run-to-run cache-read spread. Cache reads are already ~98% of input-side tokens, so a smaller prefix mostly saves the cheap billing type. The gate can pass on quality and still refuse the default flip.

**🎯 Experience Design:**
- **Entry point:** An implementer sets `WRIT_HARNESS_LEAN=1` for a baseline run. Unset, nothing in the loaded prefix changes.
- **Happy path:** Lean variants live in sibling files, not inside the default command. Flag off, `measure-invocation.py` floor is unchanged. Flag on, the run loads the lean preamble and lean command body, and over-budget context is spilled to a file instead of truncated. The last story runs the 8-story × 2 baseline and either flips the default or leaves it off.
- **Moment of truth:** `pipeline-baseline.py compare` of flag-on against a flag-off control on the same model, priced with `harness-cost.py`. Keep only if every exit-criteria row is 2/2 and same-model `cost_usd` is lower. The 2026-09-07 Fable file is the method precedent, not the model and not the price to beat.
- **Feedback model:** The compare table plus a decision-log line that says keep or null, with the numbers.
- **Error experience:** A short exit-criteria row reverts any default flip and records the table. A cost drop inside noise, or a cost rise, is a null: flags stay off, the spec still completes.

**📋 Business Rules:**
- No instruction that tells the model to use fewer tokens.
- Cuts may remove behavior the current default frontier already does, and preamble sentences that restate Plan Mode or `--recommend` from `system-instructions.md`. They may not remove exit criteria, gates, the production boundary, User Challenge, or stakes triage. “Current default frontier” means the model this work actually runs on now: Claude Opus 5.5 for much of it, and GPT-6 Astra on the OpenAI side. Both outrank the Fable 5.1 run that produced the 2026-09-07 baseline. That file is not the capability bar.
- `commands/_preamble.md` stays within the existing 95-line blocking cap. The lean file should get shorter, not longer.
- Overflow spill covers `scripts/story-context.py` and the 1,000-line “What Was Built” truncate. Flag off keeps today’s truncate-and-warn behavior, tests included.
- Lean siblings are excluded from the default invocation floor. Embedding both texts in the live command fails the spec.
- Dependencies: `[]`. Cost is compared to a same-model flag-off control, not to another spec and not to the Fable 5.1 dollar total.

**Success Criteria:** Flag-off bytes match the pre-change floor. Flag-on runs load the lean text and, when over budget, return a path, size, and short tail with the full text on disk. The baseline story ends in either a default flip or a recorded null. It does not end in a default flip when any exit-criteria row is under 2/2.

**Scope Boundaries:**
- Included: lean siblings for `create-spec`, `verify-spec`, `implement-phase`, and `implement-story`; preamble dedup; spill-to-file; the 8-run keep-or-revert story.
- Excluded: model routing, reasoning-effort defaults, changing which agent does which work, and further edits to `system-instructions.md`. Telemetry is already shipped (`scripts/harness-cost.py`).

**⚠️ Technical Concerns:**
- Four command rewrites in one story can blow the 5–7 task cap. The contract splits them as one story whose tasks are one file each, plus a floor-measurement check, not four specs.
- Spill files belong under `.writ/state/` so they stay gitignored. A spill the agent never reads is a quality risk the baseline is there to catch.

**💡 Recommendations:**
- Story order: flag substrate and byte-identical default, then preamble, then spill, then the four lean commands, then the baseline. The baseline is last because it is the only story that may change the default.
- Treat a null result as the expected outcome unless `cost_usd` actually moves. The 09-07 prune is the precedent.

## Experience design

The person running this is a Writ maintainer judging a harness cut, not an end user of an installed project.

### Journey

1. They implement Stories 1–4 with the flag off in ordinary runs.
2. They set `WRIT_HARNESS_LEAN=1` and confirm `measure-invocation.py` reports the lean floor, and that an over-budget `story-context.py` assemble writes a spill file.
3. They run the four stories × 2, flag on and flag off, on the current default frontier (Opus 5.5, or GPT-6 Astra when that is the family under test). Stage 2’s Fable 5.1 file supplies the task shape and the noise precedent, not the opponent.
4. They read the compare table and `harness-cost.py baseline` output.
5. They either make the lean siblings the files commands load by default, or they append a null line to the decision log and leave the defaults alone.

### State catalog

| State | What the maintainer sees |
|---|---|
| Flag unset | Same command bytes and the same truncate-and-warn warnings as before this spec |
| Flag set, under budget | Lean preamble and lean command text; context payload unchanged |
| Flag set, over budget | Tool result names the spill path, byte size, and a short tail; the full text is in the file |
| Baseline keep | Decision-log line says keep, and the default load path is the lean text |
| Baseline null | Decision-log line says null with the numbers; default load path is unchanged |
| Baseline quality miss | Any exit-criteria row under 2/2; default flip is reverted if it was applied; the table is in the story’s What Was Built |

## Business rules

1. **No token-saving instruction.** No lean file contains a line asking the model to conserve tokens, be brief, or avoid waste.
2. **Deletion class.** A lean command or preamble may drop behavior the current default frontier already does, and sentences that restate `system-instructions.md` on Plan Mode or `--recommend`. Exit criteria, named gates, the production boundary (no autonomous merge, PR, or release), User Challenge, and stakes triage stay. The bar is relative prowess: Opus 5.5 and GPT-6 Astra are the defaults this spec is written for. Fable 5.1 is the older measured run, below both. A cut is not justified by what a weaker model needed, and a keep on the default frontier does not license the lean default for a weaker model.
3. **Preamble cap.** `commands/_preamble.md` remains at or under 95 lines, the blocking `check_length` limit. The lean sibling is shorter than the default preamble.
4. **Spill, don’t truncate, only when the flag is on.** Over-budget story context and a “What Was Built” record over 1,000 lines are written under `.writ/state/` and the result carries path, size, and a short tail. Flag off, `enforce_budget` and the 1,000-line truncate stay, including their current tests.
5. **Siblings are not in the default floor.** `measure-invocation.py` with the flag unset does not count lean files. Putting both texts in the live command is a failure.
6. **Null completes the spec.** Story 5 is done when it records keep or null. A null is not a reason to mark the spec failed. A default flip with any exit-criteria row under 2/2 is a failure of Story 5 until the flip is reverted and the table is recorded.
7. **Same-model compare.** Story 5 runs the same four stories × 2, flag on and flag off, on one current default frontier (Opus 5.5, or GPT-6 Astra when that family is the one under test). `cost_usd` on that pair is the price of record. The $10 / $50 / $0.25 formula is reported beside it and does not decide. `.writ/eval/baselines/2026-09-07-claude-fable-5-1.json` documents how Stage 2 ran and how wide cache-read noise was. Its dollar total is not a cross-model target.
8. **Out of scope.** No model routing, no reasoning-effort change, no change to which agent does which work, no further edit to `system-instructions.md`.

## Implementation approach

`WRIT_HARNESS_LEAN=1` is an environment variable read by the loader and by `scripts/story-context.py`. It is unset in production and in the default test suite.

Lean text lives beside the default, not inside it:

| Default (flag off) | Lean (flag on) |
|---|---|
| `commands/_preamble.md` | `commands/_preamble.lean.md` |
| `commands/create-spec.md` | `commands/create-spec.lean.md` |
| `commands/verify-spec.md` | `commands/verify-spec.lean.md` |
| `commands/implement-phase.md` | `commands/implement-phase.lean.md` |
| `commands/implement-story.md` | `commands/implement-story.lean.md` |

Story 1 teaches `measure-invocation.py` to select the lean sibling only when the variable is set, and adds a regression that the unset floor’s byte count does not include those siblings. Stories 2–4 author the siblings. Story 3 adds `--spill` behavior gated on the same variable: the full over-budget text goes to `.writ/state/`, and the returned payload keeps a short tail plus path and size. The dependency-context skill’s 1,000-line rule gets the same spill branch in its lean text; the default skill text stays the truncate rule.

Story 5 does not run inside spec authoring. It is an implementation story: the same four stories × 2, once with the flag on and once off, on the current default frontier (Opus 5.5, or GPT-6 Astra for an OpenAI run). Keep flips the default load to the lean siblings for models of that prowess or higher, and records the table. Null leaves the default and records the table. A quality miss reverts a flip. The Fable 5.1 baseline is not re-run as the judge.

## Story plan

1. `story-1-flag-substrate` — `WRIT_HARNESS_LEAN` unset is byte-identical. Lean paths exist and are invisible to the default floor. Dependencies: none.
2. `story-2-lean-preamble` — Drop the Plan Mode and `--recommend` restatement. Keep the product rules. Dependencies: Story 1.
3. `story-3-spill-to-file` — Spill-to-file behind the flag for story context and “What Was Built”. Dependencies: Story 1.
4. `story-4-lean-commands` — Lean bodies for the four large commands. Dependencies: Story 1.
5. `story-5-keep-or-revert` — Eight-run keep-or-revert. Flip the default, or record a null and leave it off. Dependencies: Stories 2, 3, and 4.

## Amendment 2026-09-25 — Story 5 sample

User-approved during `/implement-spec` (drift-log DEV-010). Story 5 runs one story × 2 per arm instead of four stories × 2. Reason: the lean `/implement-story` prefix is ~1,170 tokens (4,687 bytes) smaller; re-read on each of ~91 turns that is ~107k of ~13.6M cache-read tokens per run, under 1%, against a 59% run-to-run cache-read spread. No sample in this plan can separate a prefix-driven cost drop from noise. The reduced run tests whether lean-loaded `/implement-story` still completes a real story, and may end only in null or quality miss. A keep still requires the full four stories × 2. On null, `install.sh` / `update.sh` do not ship `*.lean.md` siblings.
