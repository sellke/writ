# Story 5: Supersession Banner Convention

> **Status:** Completed ✅
> **Priority:** Low
> **Dependencies:** None
> **Commit:** 090d038

## User Story

**As a** Writ maintainer or AI agent reading an old spec
**I want to** see a documented `Amends:`/`Extends:` forward pointer on the superseding spec and a matching `Superseded by:` reverse pointer on the superseded spec's header metadata block
**So that** I can immediately tell whether something has replaced a spec without cross-referencing every newer spec's `Amends:`/`Extends:` field by hand — satisfying Business Rule 9 and Success Criterion 5

## Acceptance Criteria

- [x] Given the locked contract or generated `spec.md` declares `> **Amends:**` or `> **Extends:**` pointing at an existing spec (relative path under `.writ/specs/<folder>/spec.md`, as in `2026-07-26-leanness-instrumentation`), when `commands/create-spec.md` Phase 2 completes and the new spec's `spec.md` is written, then the **referenced (older) spec's header** gains a new line `> **Superseded by:** [<new-spec-name>](../<new-spec-folder>/spec.md)` inserted alongside existing metadata (`Status`, `Owner`, `Created`, etc.) — and the older spec's own `Status:` line is **never replaced or rewritten** (a superseded spec keeps recording its own terminal state independently).
- [x] Given a supersession relationship is declared **after the fact** via `/edit-spec` (e.g. adding `Amends:` to an existing spec that was created separately), when the modification contract is locked and Phase 2 updates the edited spec, then `commands/edit-spec.md` documents and executes the same surgical write-back: read the referenced older spec, insert `> **Superseded by:**` if absent (or update if already present), preserve all other header lines unchanged — following the same single-line surgical pattern as `create-spec.md`'s `--from-issue` `spec_ref` writeback (read → replace/insert one line → write back).
- [x] Given the `Amends:`/`Extends:` convention is currently ad hoc (e.g. line 8 of `.writ/specs/2026-07-26-leanness-instrumentation/spec.md` points at `2026-07-11-leanness-guardian` but the guardian spec has no reverse pointer), when durable documentation ships, then the forward-pointer semantics (`Amends:` = replaces/supersedes prior spec work; `Extends:` = builds on prior spec without full replacement — consistent with ADR `Extends:` usage) and the reverse-pointer requirement (`Superseded by:`) are recorded in a durable location (prefer `.writ/docs/spec-lifecycle.md` from Story 3 if it exists; otherwise a focused subsection in that doc or an equivalent product doc — implementer's call).
- [x] Given a round-trip validation on the real leanness pair (`2026-07-26-leanness-instrumentation` → `2026-07-11-leanness-guardian`), when the retroactive fix is applied as proof the mechanism works (one pair only — not a full corpus backfill; Story 6 may dogfood more broadly), then `.writ/specs/2026-07-11-leanness-guardian/spec.md` header contains `> **Superseded by:** [2026-07-26-leanness-instrumentation](../2026-07-26-leanness-instrumentation/spec.md)` and the instrumentation spec's existing `> **Amends:**` line remains unchanged — establishing the bidirectional link called for in Success Criterion 5.
- [x] Given a malformed or missing `Amends:`/`Extends:` reference (broken relative path, spec folder not found, or header block absent on the referenced file), when Phase 2 write-back runs, then the command **fails gracefully**: logs a clear warning naming the bad reference, skips the write-back (does not corrupt the referenced spec's header or body), and still completes the new spec package creation — the new spec is not blocked by a bad supersession pointer.

## Implementation Tasks

- [x] 5.1 Write failing round-trip tests (prefer `scripts/tests/test_supersession_writeback.py` or an `eval.sh` scenario fixture): create disposable superseding + superseded spec headers, simulate `Amends:` declaration, assert the referenced spec gains `Superseded by:` at the correct relative path and that the referenced spec's `Status:` line is untouched; include a malformed-reference case that asserts no header corruption.
- [x] 5.2 Document the `Amends:`/`Extends:`/`Superseded by:` convention durably — add a **Supersession banners** section to `.writ/docs/spec-lifecycle.md` (or create the subsection there if Story 3 hasn't landed yet) describing: forward-pointer field names and semantics aligned with ADR `Extends:`/`Amends:` patterns; reverse-pointer format and placement rule (new line in header metadata block, never replacing `Status:`); when each field applies; cross-link from `commands/create-spec.md` Phase 2 Step 2.4 header template notes.
- [x] 5.3 Update `commands/create-spec.md` Phase 2: after Step 2.4 writes the new `spec.md`, scan the new spec's header metadata for `> **Amends:**` or `> **Extends:**` lines that reference another spec under `.writ/specs/`; for each resolvable reference, perform surgical write-back to the referenced spec's header — mirror the `--from-issue` Step 3 pattern (read file → insert/update single `Superseded by:` line → write back, everything else preserved). Wire into ordinary Phase 2, `--from-issue`, and `--from-prototype` paths where Phase 2 runs.
- [x] 5.4 Update `commands/edit-spec.md` Phase 2 Step 2.2: when the modification contract adds or changes an `Amends:`/`Extends:` relationship on the edited spec, document and execute the same write-back to each referenced older spec — including guidance for the human/agent executor (read referenced spec, insert line after existing metadata, do not alter `Status:`).
- [x] 5.5 Apply the retroactive fix to the one real validation pair: add `> **Superseded by:** [2026-07-26-leanness-instrumentation](../2026-07-26-leanness-instrumentation/spec.md)` to `.writ/specs/2026-07-11-leanness-guardian/spec.md` header (manual commit in this story — the pair predates the automated write-back). Scope explicitly to this single pair; do not backfill other historical `Amends:`/`Extends:` relationships (Story 6 dogfood may spot-check more, but mass backfill is out of scope).
- [x] 5.6 Add an `eval.sh` static assertion that `commands/create-spec.md` and `commands/edit-spec.md` both mention `Superseded by:` write-back prose and that create-spec's Phase 2 section references the surgical write-back pattern — preventing silent regression if someone removes the instruction.
- [x] 5.7 Run pytest/eval fixtures, manually verify the leanness pair bidirectional link, and confirm create-spec/edit-spec prose matches the technical-spec contract at `sub-specs/technical-spec.md` → `## Supersession Banners (Story 5)` before marking complete.

## Notes

**Fully independent of Stories 1–4.** This story touches only header-convention documentation and command prose in `create-spec.md` / `edit-spec.md`. It does not modify status detection, the archive sweep, `verify-spec`, or `.cursorindexingignore`. It can ship in parallel once reviewed.

**Coordinate with Story 3 on doc location.** The preferred home for supersession convention docs is `.writ/docs/spec-lifecycle.md` (Story 3). If Story 3 hasn't merged yet, add the section there anyway (Story 3 can integrate) or ship a minimal standalone note and fold it in when Story 3 lands — avoid leaving the convention implicit in command prose alone.

**Coordinate with Story 6 on scope.** Task 5.5 applies the fix to **one** real pair (`leanness-instrumentation` → `leanness-guardian`) as proof the mechanism works. Story 6's dogfood run validates archive sweep and broader lifecycle behavior — it should not duplicate a full supersession backfill. Success Criterion 5 is satisfied by this single pair.

**Write-back pattern precedent:** `commands/create-spec.md` `--from-issue` Step 3 (`spec_ref` writeback): read source file → replace one targeted line → write back preserving everything else. Supersession write-back must follow the same discipline — never rewrite the referenced spec's body or replace its `Status:` line.

**ADR alignment:** ADRs already document `Extends:` (e.g. ADR-014, ADR-015, ADR-019). Spec-level `Amends:`/`Extends:` should use the same relative-link markdown format and semantic split: `Amends:` indicates the new spec supersedes/replaces prior spec work; `Extends:` indicates building on prior work (partial supersession may still warrant `Superseded by:` when the new spec is the canonical successor — document the rule clearly).

**Risks:**

- **Multiple `Amends:`/`Extends:` targets** — a spec may reference both another spec and an ADR (see leanness-instrumentation line 8). Write-back applies only to resolvable `.writ/specs/<folder>/spec.md` paths; ADR references are forward-only, no reverse write-back.
- **Duplicate write-back** — if `Superseded by:` already exists, update the link rather than appending a second line (or skip if identical).
- **Relative path resolution** — parse the markdown link target from the header line; resolve relative to the superseding spec's folder; fail gracefully if the target file doesn't exist.
- **Header block detection** — insert the new line within the leading `>` metadata block (before the first `##` heading), not in the contract body.

**Out of scope:** Archive sweep, status detection, rewriting historical cross-references project-wide, ADR reverse pointers, mass backfill of all existing `Amends:`/`Extends:` pairs beyond the one validation pair.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Malformed Amends/Extends reference] — `spec.md` → `## Technical Concerns` (conservative default on missing headers; approximate path matching heuristic — adapt write-back failure to fail gracefully without corrupting referenced spec headers, inferring from Business Rule 9 supersession contract)
- **Shadow paths:** []
- **Business rules:** [Supersession gets a real reverse pointer (Amends:/Extends: documented; Superseded by: written back onto superseded spec header)]
- **Experience:** []

Reference: `.writ/docs/context-hint-format.md` — read `spec.md` directly for full contract text at `## 📋 Business Rules` (item 9), `## Detailed Requirements` → `### Supersession banner convention`, and Success Criterion 5; read `sub-specs/technical-spec.md` → `## Supersession Banners (Story 5)` for exact write-back format and placement rule.

---

## What Was Built

**Implementation Date:** 2026-08-04

### Files Created

1. **`scripts/supersession-writeback.py`** — the executable reference implementation (mirroring the Story 1/2 pattern of a testable helper that command prose invokes rather than hand-rolling markdown edits): `scan --new-spec-file PATH` reports every `Amends:`/`Extends:` markdown-link target, classified as a resolvable `spec` target, a forward-only `other` target (e.g. an ADR), or missing; `apply --new-spec-file PATH` performs the real write-back — inserting or updating (never duplicating) a `> **Superseded by:**` line on each resolvable target's header, always preserving the target's own `Status:` line and all other content.
2. **`scripts/tests/test_supersession_writeback.py`** (8 tests) — round-trip coverage: single-target write-back, idempotent re-run (no duplicate line, no unnecessary rewrite), multi-target lines (spec + ADR, only the spec gets written), replacing a stale pre-existing `Superseded by:` pointer, a broken/missing reference (graceful skip, no corruption), the `Extends:` field, the no-supersession-line no-op case, and the missing-file contract error.
3. **`scripts/eval-supersession-writeback.py`** (8 scenarios) — the same round trip through the actual `scan`/`apply` CLI subcommands (not just the Python functions directly), proving the exact invocation `commands/create-spec.md` Step 2.4b and `commands/edit-spec.md` use.

### Files Modified

- **`commands/create-spec.md`** — added a "Supersession banners" note to Step 2.4's frontmatter bullet (documenting the `Amends:`/`Extends:` field shape) and a new **Step 2.4b: Supersession Write-back** that invokes `scripts/supersession-writeback.py apply` after the new spec's `spec.md` is written, applying uniformly across the standard, `--from-issue`, and `--from-prototype` paths (all converge on the same Phase 2).
- **`commands/edit-spec.md`** Step 2.2 — added the equivalent supersession write-back paragraph invoking the same helper when a modification contract adds/changes an `Amends:`/`Extends:` relationship.
- **`.writ/specs/2026-07-11-leanness-guardian/spec.md`** — the one real retroactive validation pair (task 5.5): added `> **Superseded by:** [2026-07-26-leanness-instrumentation](../2026-07-26-leanness-instrumentation/spec.md)` to the header, verified idempotent by re-running `supersession-writeback.py apply` against the real `leanness-instrumentation` spec (reports `unchanged`, zero diff).
- **`scripts/eval.sh`** — registered the `supersession-writeback` check (CHECKS array + `check_supersession_writeback()`), with scenario wiring, static assertions that both commands invoke the helper and that `create-spec.md` documents `Amends:`, and a direct assertion that the real leanness-guardian spec carries the exact retroactive reverse pointer (regression guard for task 5.5's evidence).
- **`.writ/docs/spec-lifecycle.md`** — the "Supersession Banners" section referenced by both commands was authored during Story 3 (per that story's own note anticipating this convention); no additional edit was needed here beyond confirming it matches this story's shipped behavior exactly (field semantics, placement rule, and the leanness pair as the validation example were already correct).

### Implementation Decisions

1. **Built a real executable helper, not prose-only instructions.** The story's Notes point to the `spec_ref` writeback (pure command prose, no script) as precedent, but Task 5.1 explicitly asks for round-trip *tests* — untestable without something to test. Followed the Story 1/2 precedent instead (`spec-status.py`, `archive-sweep.py`): a small, testable Python helper that command prose invokes via `python3 scripts/supersession-writeback.py apply --new-spec-file ...`, reducing the risk of an agent hand-rolling the surgical header edit incorrectly.
2. **Multi-target lines split by resolution, not by field.** `2026-07-26-leanness-instrumentation`'s real `Amends:` line references both a spec and an ADR in one line. The helper parses every markdown link on the line and classifies each independently — only `.writ/specs/<folder>/spec.md` targets get write-back; everything else (ADRs, or any other link) is reported under `skipped_other` and never touched.
3. **Idempotent by construction, not by a separate "already applied" check.** Re-running `apply` against the same pair is a no-op — `_upsert_superseded_by` compares the candidate line against what's already there and returns `changed=False` when they match, verified directly against the real leanness pair (see Test Results).
4. **Fixed a real symlink-resolution bug surfaced by the eval CLI scenario during implementation.** The first version of `apply()` computed the relative link using the unresolved `new_spec_file` path against a `.resolve()`d target path; on macOS, where `/tmp` is a symlink into `/private/var/...`, this produced a nonsensical, overlong relative path. Fixed by resolving `new_spec_file` the same way as the target before computing `os.path.relpath` — caught by `scripts/eval-supersession-writeback.py`'s CLI-level round trip (the pytest suite alone didn't catch it because `tmp_path` fixtures already return resolved paths), which is itself evidence for keeping both a direct-function test suite and a CLI-level scenario.

### Test Results

**Verification:**
- `/usr/local/bin/python3 -m pytest scripts/tests/test_supersession_writeback.py -v` → ✅ 8/8 passed
- `python3 scripts/eval-supersession-writeback.py` → ✅ 8/8 scenarios passed
- `bash scripts/eval.sh --check=supersession-writeback` → ✅ PASS, 0 findings (scenario + static assertion + real leanness-guardian regression guard)
- `bash scripts/eval.sh` (full suite, all 24 checks) → ✅ PASS, 0 findings, 0 run errors — including `broken-refs`, which caught and required a fix for two illustrative markdown-link examples in `create-spec.md` that resolved to nonexistent paths relative to the command file's own location (rewritten as prose descriptions instead of literal `[text](path)` syntax)
- Manual verification against the real pair: `python3 scripts/supersession-writeback.py scan --new-spec-file .writ/specs/2026-07-26-leanness-instrumentation/spec.md` correctly reports 1 resolvable spec target (leanness-guardian) and 1 `other` target (ADR-015); `apply` against the same file reports the guardian spec as `unchanged` (the manual task-5.5 edit already matches byte-for-byte what the helper would write) — confirming the retroactive fix and the automated mechanism agree exactly

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration (one self-caught fix: the symlink-resolution bug above, found and fixed before this write-up, not discovered in a separate review pass)
- **Drift:** None
- **Security:** N/A — reads/writes only within `.writ/specs/`, no network or external input; broken references degrade to a reported no-op rather than a crash or partial write

### Deviations from Spec

**Added a script where the story's own precedent suggested prose-only.** Documented above under Implementation Decisions #1 — this is an enhancement, not a scope reduction: it satisfies every acceptance criterion the story specifies (including the ones that presuppose something testable) while also making the write-back safer than a purely manual per-agent edit.
