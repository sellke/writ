# Story 1: Delta-Bound Justification

> **Status:** Complete
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer who is about to route ~142 new findings through `eval-leanness.py`
**I want to** `justification` to silence exactly the increment it describes — per metric, up to a recorded value — instead of muting a whole surface forever
**So that** the ratchet cannot be switched off with one sentence, and the four checks this spec adds cannot be silenced by the same defect that silenced the ratchet

## Acceptance Criteria

- [x] Given a baseline surface at `lines: 100` with no justification and a current measurement of `120`, when the check runs, then it emits exactly one growth warning whose `subject` is `<surface>.lines` — naming the metric, not just the surface.
- [x] Given that same surface with `justifications.lines = {"value": 120, "date": …, "text": "<why>"}`, when the current measurement is `120`, then **no** warning is emitted — the justification covers the increment it names.
- [x] Given that same justification (`value: 120`), when the current measurement is `121`, then a warning **is** emitted, and its `what` names the ceiling that was passed (`justified to 120, now 121`) — one sentence buys one increment, not unlimited silence.
- [x] Given a surface whose `justifications` names **only** `lines`, when both `lines` and `chars` have grown, then exactly one warning is emitted — for `chars`. A justification for one metric must never silence the other. This is the direct regression test for the current placement of the justification read outside the per-metric loop (`scripts/eval-leanness.py:527`).
- [x] Given any surface, when the current measurement is less than or equal to its baseline, then no warning is emitted regardless of whether a justification exists, is malformed, or names a lower ceiling — "down is free" is evaluated first and this story does not weaken it.
- [x] Given a legacy schema-2 entry carrying the unbounded string form (`"justification": "<why>"`) and a current measurement above the baseline by any margin, when the check runs, then a warning **is** emitted, and its `fix` names the bound replacement (`justifications.<metric>`) — the unbounded mute does not survive the migration in old data either.
- [x] Given the six committed schema-2 entries, which all carry `"justification": ""`, when the check runs, then behavior is byte-identical to today for them — an empty legacy string never silenced anything and still does not.
- [x] Given a malformed justification — `value` non-numeric, `value` at or below the baseline, `text` blank or absent, or `justifications` not a dict — when the current measurement exceeds the baseline, then a warning is emitted and no exception is raised. A justification that cannot be evaluated never silences.
- [x] Given `check_baseline()`'s growth-warning `fix` string after this story, when a maintainer follows it literally, then the instruction is self-consistent: it never tells them to write a value that the next prescribed command erases, and it states what `--update-baseline` does differently (moves every surface's floor, records no reason).
- [x] Given the committed `.writ/leanness-baseline.json` (schema 2) after this story's code lands but before Story 2 rewrites it, when the check runs, then `structural` is `[]` — the reader accepts schema 2 and schema 3, so no intermediate state turns `eval.sh` red.
- [x] Given `python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json` after this story, when its `warnings` are read, then exactly the same `(surface, metric)` pairs warn as before it — no more, no fewer. This story changes what a justification *means*; it clears nothing. Clearing is Story 2.

> **Measured correction, 2026-08-11 (implementation).** The spec was authored when four growth warnings were live. Three Phase 10 specs landed before this one (`e23fbdc` retire-dead-prescription, `b8b96d5` component-contract, `dfc0807` loop-bounds), and they grew a third gated surface. The live count on this story's base is **six**, not four: `commands.lines`, `commands.chars`, **`agents.lines`, `agents.chars`**, `scripts.lines`, `scripts.chars`. Verified before and after this story's code landed — the same six pairs warn, with new `subject` values and new text. Everywhere the spec and these stories say "the four", read "the six", and treat `agents` as a fourth justified grower alongside `commands` and `scripts`.

## Implementation Tasks

- [x] 1.1 Write the tests first in `scripts/tests/test_eval_leanness_contract.py` (importlib-by-path load of `eval-leanness.py`, the established recipe in `test_archive_sweep.py`): the full matrix in `sub-specs/technical-spec.md` → "Test matrix for the bound justification" — 16 rows covering equal/down/up, justified-exactly, justified-then-exceeded, per-metric independence, legacy empty string, legacy non-empty string, four malformed shapes, both schema versions, and the reseed output shape
- [x] 1.2 Add `justified_ceiling(base_entry, metric_key)` — returns the `(ceiling, text, date)` for one `(surface, metric)` pair from `justifications.<metric>`, or a `None` ceiling when the entry is absent, malformed, or is the legacy unbounded string
- [x] 1.3 Rewrite `check_baseline()`'s per-surface loop: move the justification read **inside** the `for metric_key in ("lines", "chars")` loop, evaluate `current_value <= base_value` first and unconditionally (down is free), then apply the bound
- [x] 1.4 Change the growth warning's `subject` from `<surface>` to `<surface>.<metric>` so the two metrics of one surface are separately addressable — the same Business Rule 2 granularity the four new checks are held to
- [x] 1.5 Write the three `what` variants (no justification recorded / justified ceiling exceeded / legacy unbounded string present), replace the `fix` string that currently prescribes the write-then-erase sequence (`scripts/eval-leanness.py:540`), and correct `check_baseline()`'s own docstring, whose three-line summary still advertises *"current > baseline, justification present -> silent (up costs a sentence)"* (`scripts/eval-leanness.py:490-492`)
- [x] 1.6 Accept `schema` 2 **or** 3 in the structural gate at `scripts/eval-leanness.py:510`, and change the `--update-baseline` reseed to write `"schema": 3` with `"justifications": {}` per surface, dropping the legacy `"justification"` key and rewriting the payload's `note` string (`scripts/eval-leanness.py:613-614`), which repeats the same "requires a justification string, or it warns" claim. Extend the existing reseed comment (`scripts/eval-leanness.py:590-595`) — the reset stays, and under a bound justification it is more clearly right: a ceiling at or below the new floor is dead data
- [x] 1.7 Verify against the real repo: the same four `(surface, metric)` pairs warn, `structural` is `[]`, `bash scripts/eval.sh --check=leanness` exits 0, and the committed schema-2 baseline produces no structural finding
- [x] 1.8 Verify all tests pass — the new pytest file, `bash scripts/tests/test_eval_leanness.sh`, the full `scripts/tests/*.py` suite, and `bash scripts/eval.sh`

## Notes

**Technical considerations:**

- **The defect is two lines, and they are both verifiable by reading.** `scripts/eval-leanness.py:527` reads `justification` **once per surface, outside** the `for metric_key` loop; line 533 is `if current_value <= base_value or justification: continue`. Together: any non-empty string skips **both** `lines` and `chars` for that surface, at any magnitude, on every future run. The advertised price of growth — "up costs a sentence" (`scripts/eval-leanness.py:491`, and the baseline's own `note`) — is real for exactly one run and free forever after.
- **The reset is not the bug; do not "fix" it.** The reseed comment (`scripts/eval-leanness.py:590-595`) argues that a justification describes a specific past delta which ceases to exist once the baseline absorbs it. That reasoning is sound and this story keeps it. What was wrong was the *remediation text* (line 540) telling a maintainer to write a justification and then run the command that erases it — and, underneath that, a justification that had no delta to be specific about.
- **Binding to a value is what makes the sentence honest.** A justification says "this growth, to here, for this reason." Recording `value` turns that sentence into an assertion the checker can hold you to: growth to `value` is covered, growth past it is not. That is the whole mechanism. Everything else — the per-metric map, the malformed-shape handling — exists to keep that one property from leaking.
- **Per-metric, not per-surface.** `lines` and `chars` are independent measurements of independent kinds of growth; a file that adds 200 short lines and one that adds one 8KB line are different events. Justifying one must not silence the other, and the current code's single per-surface read is why it does.
- **Legacy entries fail loud, not silent.** All six committed entries carry `"justification": ""` (verified in `.writ/leanness-baseline.json`), which never silenced anything, so their behavior is unchanged. A *non-empty* legacy string is the only case where behavior changes, and it changes in the safe direction: it stops silencing and starts warning with a migration hint. Treating an unbounded string as still-valid would carry the exact defect this story removes into the migration.
- **Schema 3, with a reader that accepts 2.** The per-surface entry shape genuinely changed, so the writer bumps to `"schema": 3`. The reader must accept both **before or in the same commit as** any write of 3 — `check_baseline()` currently makes `schema != 2` a *structural* finding (`scripts/eval-leanness.py:510`), so a writer-first change would fail `eval.sh` on the very run that introduced it.

**Risks / challenges:**

- **This story grows the `scripts` surface while a `scripts` growth warning is live.** That is expected and must not be papered over: adding this reader grows `scripts.lines`, the delta gets larger, and the warning text changes — but the *count* of live growth warnings stays at four. Assert the count and the four `(surface, metric)` pairs, not the delta numbers.
- **Recording a ceiling is now easier than pruning, and that is a hazard with a name.** Bound justifications make each raise cheap individually. What stops the ratchet from being walked upward one justified step at a time is that every step is a dated, reviewable diff naming a number and a reason — growth costs a diff each time rather than a sentence once. If this spec's own history shows a surface raised repeatedly with thin `text`, that is a finding for the Tier B audit, not a reason to re-add an unbounded mute.
- **A ceiling at or below the baseline is meaningless but must not crash.** After Story 2 or any `--update-baseline`, stale ceilings can sit below the floor. Handle it as "no valid justification" and warn; do not special-case it into silence.

**Integration points:**

- **Gates Story 2.** Story 2 clears the four live warnings *using this mechanism* — it records bound justifications rather than reseeding the floor. Running Story 2 first would force the old absorb-only disposition and then require redoing it.
- **Gates Stories 3–6 transitively.** Those four checks land in `warnings`. Until a justification is bounded, any one of them could be silenced wholesale by a single unbounded string on the surface they measure.
- Touches `scripts/eval-leanness.py` only. `.writ/leanness-baseline.json` is **not** edited by this story — the reader accepts the committed schema-2 file as-is, and Story 2 owns the rewrite.
- No command, agent, adapter, or skill file is read differently or written at all (Business Rule 4).

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 9 (a justification is bound to a specific recorded value, per metric, or it silences nothing — this story *is* Rule 9); Rule 2 (every finding names the exact thing it asserts — the `subject` becomes `<surface>.<metric>`); Rule 4 (checks read the surface, never modify it)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Delta-bound justification — the schema-3 entry shape, the per-metric evaluation order, legacy handling, and the corrected remediation text] — from spec.md → ## Detailed Requirements → ### Delta-bound justification (the silencer fix)
- **Error map rows:** [Malformed justification → warns, never silences, never raises; legacy unbounded string → warns with a migration hint; schema 2 read by a schema-3 writer → accepted, never structural] — from sub-specs/technical-spec.md → ## The silencer fix (Story 1), ## Error & Rescue Map
- **Contract:** [Hardest constraint: "Four unjustified-growth warnings are **live right now** … This spec must clear the existing four — justify in baseline or prune — or its own output is noise from birth." The approved scope addition of 2026-08-11 makes "justify in baseline" mean a bounded justification.] — from spec.md → ## Contract (Locked), ## Approved Scope Addition — 2026-08-11
