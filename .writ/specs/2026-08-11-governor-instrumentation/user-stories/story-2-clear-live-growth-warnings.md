# Story 2: Clear the Four Live Growth Warnings

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer about to add ~142 findings to `eval-leanness.py`'s `warnings` channel
**I want to** clear the four unjustified-growth warnings that are live today, and record why they were accepted in the field the checker actually reads
**So that** the new findings arrive into a quiet channel instead of inheriting the invisibility of warnings everyone already scrolls past

## Acceptance Criteria

- [ ] Given the current repo, when `python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json` is run, then `warnings` contains **no** growth entry for `commands.lines`, `commands.chars`, `scripts.lines`, or `scripts.chars`, and `structural` is `[]`.
- [ ] Given `.writ/leanness-baseline.json` after this story, when its `surfaces` map is read, then every surface's `lines` and `chars` are **unchanged** from the 2026-08-04 reseed (`commands` 10974/514594, `scripts` 27210/1155797, and the other four untouched) — the floor is not moved, so the ratchet keeps measuring cumulative drift from the last true reseed rather than resetting its own memory.
- [ ] Given `.writ/leanness-baseline.json` after this story, when `surfaces.commands.justifications` and `surfaces.scripts.justifications` are read, then each carries a `lines` and a `chars` entry whose `value` equals the measurement taken **after Story 1 landed**, whose `date` is the day this story runs, and whose `text` names the cause: `a5c5a66` — *"feat(install): fan out runtime scripts and Writ docs on install/update"*, PR #34, released in v0.28.0.
- [ ] Given the recorded ceilings, when any of the four measurements grows by even one unit past its `value`, then the warning returns and names the ceiling it passed — verified by decrementing one recorded `value` by 1, observing the warning, and restoring it. The channel is quiet because the growth is accounted for, not because it is muted.
- [ ] Given `.writ/leanness-baseline.json` after this story, when the file is searched for the legacy key, then **no** surface carries `"justification"` — all six legacy empty strings are removed, and `schema` is `3`.
- [ ] Given `.writ/leanness-baseline.json` after this story, when its top-level keys are read, then there is **no** `absorbed` array — the audit record lives in `justifications`, which the checker reads and enforces, rather than in an inert key that the next `--update-baseline` would silently delete.
- [ ] Given no command, agent, adapter, skill, or script under the product surface is edited by this story, when the leanness metrics are recomputed after it, then `per_surface` is byte-identical to the pre-story measurement.

## Implementation Tasks

- [ ] 2.1 Reproduce and record the current output: capture the four warnings verbatim and confirm the delta arithmetic against `git log <baseline-commit>..HEAD -- commands scripts` (expect exactly one commit, `a5c5a66`; `commands/update-writ.md` +31/−9 = +22 lines; `install.sh`+`update.sh`+`unlink.sh` +306/−184 = +122 lines)
- [ ] 2.2 Take the ceiling measurements **after** Story 1 has landed — Story 1 grows `scripts`, so `scripts.lines` and `scripts.chars` will exceed the +122/+2596 quoted in `spec.md`. Record what the run reports, never the numbers quoted in this spec; the quoted figures are the pre-Story-1 evidence for the *cause*, not the ceiling
- [ ] 2.3 Hand-edit `.writ/leanness-baseline.json`: set `schema` to `3`, delete all six legacy `"justification": ""` keys, and add a `justifications` map to `commands` and `scripts` with a `lines` and a `chars` entry each (`value`, `date`, `text`). Leave every `lines`/`chars` baseline number untouched
- [ ] 2.4 Verify the run is quiet: no growth warning for the four `(surface, metric)` pairs, `structural: []`, `bash scripts/eval.sh --check=leanness` exits 0
- [ ] 2.5 Verify the ratchet is still armed at the new ceilings: decrement one recorded `value` by 1, confirm the warning returns naming the exceeded ceiling, restore the value, confirm it is quiet again
- [ ] 2.6 Verify `per_surface` is byte-identical to the pre-story measurement — this story writes no product-surface file
- [ ] 2.7 Verify all tests pass — `bash scripts/tests/test_eval_leanness.sh`, the full `scripts/tests/*.py` pytest suite, and `bash scripts/eval.sh`

## Notes

**Technical considerations:**

- **Justify, do not absorb, do not prune.** The entire delta traces to `a5c5a66` — reviewed, shipped, released feature work. Pruning it to satisfy a counter would revert released functionality and is named out of scope. Absorbing it via `--update-baseline` would also silence it correctly *now*, but it moves all six floors, records no reason anywhere the checker reads, and throws away the cumulative-drift measurement from the last true reseed. A bound justification silences exactly the accepted increment, keeps the floor, and puts the reason in the file.
- **This story does not run `--update-baseline`.** The reseed is the right tool for a deliberate whole-file re-arming, not for accepting two surfaces' growth with a reason. It would also wipe the `justifications` this story is writing.
- **The `absorbed` array is dropped, deliberately.** It was designed to hold date + surfaces + delta + cause + disposition for accepted growth. A bound justification holds the same content (`date`, `value`, `text`), attached to the exact `(surface, metric)` it explains, in a field `check_baseline()` reads and enforces. Shipping both would be two records of one fact, one of which nothing reads. The `absorbed` design also had a self-erasure flaw of its own — `--update-baseline` rewrites the file wholesale and would drop it — which is a small echo of the very defect Story 1 fixes. What is lost is the append-only *history* across absorptions: a `justifications` entry is overwritten by the next raise. `git log .writ/leanness-baseline.json` is that history, and it is a better one — it carries the diff and the commit that caused it.
- **Order matters, and it is now simpler than it was.** Story 1 edits `scripts/eval-leanness.py`, which grows the `scripts` surface. Measure the ceilings after that edit is committed. There is no longer a write-then-erase sequence to sequence around, because nothing in this story runs the reseed.
- **The other four surfaces get no `justifications` key.** `agents`, `skills`, `adapters`, and `system_instructions` have not drifted; an absent or empty `justifications` map is the correct state, and the check treats it as "no justification recorded."

**Risks / challenges:**

- Recording a ceiling from the numbers in `spec.md` rather than from a live run is the most likely way this story fails. The spec's `+22 / +1995 / +122 / +2596` figures are pre-Story-1 evidence of *cause*; the ceilings are whatever the run reports at the moment the entry is written.
- Every story after this one that edits `scripts/eval-leanness.py` will grow `scripts` past this story's recorded ceiling and re-warn. That is the mechanism working, not a regression. The disposition is a fresh, dated `justifications` entry naming the story that caused the growth — recorded as part of that story, not batched at the end of the spec.

**Integration points:**

- Depends on Story 1: bound justifications do not exist until Story 1 ships the reader, and clearing the four with the pre-fix mechanism would mean either an unbounded mute (forbidden) or a reseed that Story 1 then makes unnecessary.
- Stories 3–6 are gated on this story's first acceptance criterion. Each of them re-asserts that its own findings are the only new entries in `warnings` — an assertion that is only meaningful because this story emptied the channel first.
- No product-surface file changes, so no interaction with `eval.sh check_length`, `check_manifest`, or the parity checks.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (no new warning emitted while any of the four existing growth warnings is live — this story *is* Rule 1); Rule 9 (a justification is bound to a recorded value, per metric — this story is its first real use); Rule 4 (checks read the surface, never modify it — this story modifies baseline data only, never a measured product file)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Baseline resolution (the four live warnings) — the justify-don't-absorb decision, the `justifications` entry shape, and why `absorbed` was dropped] — from spec.md → ## Detailed Requirements → ### Baseline resolution (the four live warnings)
- **Error map rows:** [Malformed or stale justification → warns, never silences; a ceiling at or below the floor is dead data] — from sub-specs/technical-spec.md → ## Error & Rescue Map, ## The silencer fix (Story 1)
- **Contract:** [Hardest constraint: "Four unjustified-growth warnings are **live right now** … New warnings added on top of ignored warnings inherit their invisibility. This spec must clear the existing four — justify in baseline or prune — or its own output is noise from birth."] — from spec.md → ## Contract (Locked)
