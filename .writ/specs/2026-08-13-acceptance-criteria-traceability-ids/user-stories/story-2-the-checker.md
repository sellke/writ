# Story 2: The Checker

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1
> **Commit:** d9d04a1e1352671f19e3b2787ca7bb19c0d66782

## User Story

**As a** developer or agent about to trust a `Completed ✅` story
**I want** a read-only script that decides, deterministically, whether every criterion is
covered and every citation resolves
**So that** the verdict does not depend on who read the markdown, and a blocking check has an
executable reference behind it like every other blocking check in this repo

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given a fixture triggering each of the seven finding codes, when `ac-trace.py check` runs, then it reports that code with the severity recorded in `.writ/docs/acceptance-criteria-ids.md` and exits 1 for any blocking finding, 0 when the only findings are informational. `[AC-2.1]`
- [x] Given an ID-shaped token that is not an end-anchored `` `[AC-n.m]` `` group — a high-water-mark line, or an example ID quoted in criterion prose — when the check runs, then that token is neither a definition nor a citation, so a marker never satisfies its own ID and quoted prose never manufactures one. `[AC-2.2]`
- [x] Given two runs over byte-identical input, when their stdout is compared, then it is byte-identical and finding order is deterministic rather than filesystem-order dependent. `[AC-2.3]`
- [x] Given a `--spec` path with no `user-stories/` directory, or a story file that cannot be read, when the check runs, then it exits 2 naming the offending path — never 0, and never 1. `[AC-2.4]`
- [x] Given this spec's own four story files, when the check runs against this spec folder, then it exits 0, or it exits 1 with only the findings documented as accepted exceptions in `drift-log.md` → DEV-4 as of 2026-08-13 (`untested_criterion` on Stories 1/2's own criteria; fixture-collision `dangling_reference` findings) — any finding outside that documented set is a real failure. `[AC-2.5]`

> **Amended 2026-08-13 via `/edit-spec`** — see the spec folder's `CHANGELOG.md`. Originally
> read "then it exits 0" with no exception; DEV-4 (below) disclosed that this could never be
> honestly satisfied without backfilling tests onto already-`Completed ✅` stories or
> weakening the checker, so the criterion was reworded to name its own disclosed exception
> rather than promise an absolute clean exit. (Kept off the criterion line above so the
> trailing `[AC-2.5]` tag stays end-anchored per this spec's own grammar — an earlier version
> of a similar note broke that anchoring and produced two spurious findings of its own, caught
> by Story 3's architecture review.)

## Implementation Tasks

- [x] 2.1 Write `scripts/tests/test_ac_trace.py` first — one test per finding code, plus the two non-tag hazards (marker line, prose-quoted ID), determinism, and the three exit codes `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [x] 2.2 Implement the end-anchored `TAG` parser: definitions and marker from `## Acceptance Criteria`, citations from `## Implementation Tasks`, with the marker consumed and every non-anchored ID token treated as prose. Use Story 4's own criteria as the regression fixture — they must yield exactly four `AC-4.*` definitions `[AC-2.1, AC-2.2]`
- [x] 2.3 Implement the citation scan outside `.writ/` — classify test-shaped paths as test citations and everything else as informational source citations `[AC-2.1]`
- [x] 2.4 Implement the finding pass and JSON output with sorted, deterministic finding order; wire exit codes 0/1/2 `[AC-2.1, AC-2.3, AC-2.4]`
- [x] 2.5 Write `scripts/eval-ac-trace.py` fixture scenarios (disposable spec folders in tempdirs, PASS/FAIL TSV) following `scripts/eval-story-deps.py`, and register `check_ac_trace` in `scripts/eval.sh` `[AC-2.1, AC-2.3]`
- [x] 2.6 Run the checker against this spec folder as the dogfood fixture and resolve anything it finds — ran it, findings are genuine (see DEV-4), correctly not silenced by backfilling tests or weakening the checker `[AC-2.5]`
- [x] 2.7 Verify all tests pass and coverage on new code is ≥80% with error paths at 100% `[AC-2.1, AC-2.4]`

## Notes

**Technical considerations:** Read-only, in the strict sense `scripts/exit-criteria.py`
documents about itself — never writes a file, and any git invocation stays within the
read-only subcommand families. The output contract is one JSON object on stdout with a schema
string, matching `spec-deps.py` and `exit-criteria.py`.

The citation scan is the only part that reaches outside the spec folder. Bound it: skip
`.git/`, skip anything git-ignored, skip binaries, and do not follow symlinks out of the repo.
A repo-wide scan that silently reads a vendored `node_modules` is both slow and wrong.

**Risks:** The tempting shortcut is to satisfy coverage from *any* occurrence of an ID outside
`.writ/`. That would let a citation in a changelog or a commit-message fixture count as a test
and would launder exactly the gap this spec exists to close. Test-shaped paths satisfy
coverage; everything else is informational and must be reported as such.

Second risk: reporting `untested_criterion` on a story that is not `Completed ✅`. Tests do not
exist before the work does, and a checker that cries every time a spec is authored gets muted,
taking the real findings with it.

**Integration:** Story 1's grammar doc is the specification. A disagreement between the doc and
this script is a defect in whichever is wrong — resolve it in the doc first, then the code, so
the recorded contract stays authoritative.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met — AC-2.5 amended 2026-08-13 via `/edit-spec` to resolve DEV-4
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** Read spec folder, Parse story file, Scan repo for citations, Emit
  verdict — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** Happy path, Nil input (no `user-stories/`), Empty input (zero criteria),
  Upstream error (unreadable story) — from sub-specs/technical-spec.md → ## Shadow Paths
- **Business rules:** All seven finding codes with severities, and the "test-shaped path"
  classification — from spec.md → ## 📋 Business Rules
- **Precedent to mirror:** `scripts/story-deps.py` (CLI shape, JSON output, named finding
  codes), `scripts/eval-story-deps.py` (fixture-scenario harness), `scripts/exit-criteria.py`
  (read-only discipline, schema string, exit-code trichotomy)

---

## What Was Built

**Implementation Date:** 2026-08-13

### Files Created

1. **`scripts/ac-trace.py`** (629 lines)
   - The read-only checker: end-anchored `TAG` parser (copied verbatim from
     `.writ/docs/acceptance-criteria-ids.md`), marker validation with exclusion from both
     definition and citation sets, a bounded repo-wide citation scan (nested-worktree boundary
     via `.git`-file-vs-directory detection, batched `git check-ignore --stdin`, binary/symlink
     guards, non-git-worktree degraded fallback with `ignore_filter: false`), the seven-finding
     pass, and CLI (`check --spec PATH [--repo .]`) with schema `ac-trace-check-v1` and exit
     0/1/2. All git usage stays within `rev-parse`/`check-ignore`; no file is ever written.
2. **`scripts/tests/test_ac_trace.py`** (915 lines, 50 tests)
   - One test per finding code with severity asserted alongside detection; both non-tag
     hazards (marker self-satisfaction, prose-quoted IDs); a real-repo regression fixture
     confirming Story 4's own file yields exactly four `AC-4.*` definitions with no phantom
     `AC-2.*` definitions from its quoted example prose; determinism at both direct-call and
     CLI-subprocess level; all three exit codes including chmod-000 and invalid-UTF-8
     fixtures; and citation-scan boundary tests (nested worktree, git-ignore, binary, symlink
     escape/loop, non-git fallback, bare-token adjacency `AC-3.1x`/`xAC-3.1`).
3. **`scripts/eval-ac-trace.py`** (435 lines, 20 scenarios)
   - Disposable-spec-folder PASS/FAIL TSV harness following `eval-story-deps.py`'s shape.

### Files Modified

- **`scripts/eval.sh`** — registered `ac-trace` in the `CHECKS` array and added
  `check_ac_trace()` (scenario loop plus `require_literal`/`forbid_literal` static assertions
  binding the seven finding-code strings to both the checker and the grammar doc, and
  read-only-discipline guards against `os.remove`, `.write_text(`, and mutating `git` calls).

### Implementation Decisions

1. **Bare-token boundary regex is an original design choice** — neither the grammar doc nor
   technical-spec.md gives a literal regex for the bare `AC-n.m` citation case (only the
   backticked `TAG` has one). Chosen: `` (?<![\w-])AC-(\d+)\.(\d+)(?![\w-]) ``, pinned by tests
   against both adjacency directions.
2. **`untasked_criterion`/`dangling_reference` computed spec-wide, not per-story** — matches
   spec.md's literal wording ("no implementation task **in the spec** cites it").
3. **A cross-story-tagged definition is excluded from that ID's definition set entirely**
   (reported as `marker_violation`, never silently re-homed to the story it appears in) — per
   spec.md's explicit "reported, never silently re-homed" cross-story guard.

### Test Results

**Verification:** `python3 -m pytest scripts/tests/ -q`
**Coverage:** 96% on `scripts/ac-trace.py` (all seven finding codes and all error paths at
100%; remaining gaps are defensive belt-and-suspenders branches — git-binary-missing,
already-covered symlink `OSError` paths)
- ✅ 521/521 passing (468 pre-Story-2 baseline + 50 new + 3 from Story 4)
- ✅ `bash scripts/eval.sh --check=ac-trace` → 20/20 scenarios, 0 findings
- ✅ Dogfood run (task 2.6) against this spec folder: exit 1, 12 findings — see Deviations
  (DEV-4) for why this is correct, disclosed behavior rather than a defect

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** Small, plus one disclosed spec-contract gap (DEV-4, resolved 2026-08-13 via
  `/edit-spec` — not implementation drift)
- **Security:** Clean — read-only discipline independently verified (no write calls, git usage
  confined to `rev-parse`/`check-ignore`, no shell injection surface)
- **Boundary Compliance:** Only the four declared Owned files touched; `commands/verify-spec.md`
  and `commands/edit-spec.md` confirmed untouched by this story; `scripts/recommend-state.py`
  and its two eval fixture sets confirmed untouched, matching the spec's explicit exclusion list

### Deviations from Spec

- **[DEV-4] AC-2.5's literal "exits 0" is not satisfied by a live dogfood run** — Severity:
  Disclosed; **resolved 2026-08-13 via `/edit-spec`** (see spec folder's `CHANGELOG.md`) —
  AC-2.5 reworded to name its own disclosed exception rather than promise an absolute clean
  exit; not a Story 2 implementation defect
  - Spec said: "Given this spec's own four story files, when the check runs against this spec
    folder, then it exits 0."
  - Reality: running `ac-trace.py check` against this spec's own folder exits **1**. As of
    Story 3's architecture review, this is 14 findings, in two classes: (1) `untested_criterion`
    on Story 1's `AC-1.1`–`AC-1.4` **and** Story 2's own `AC-2.2`/`AC-2.3` — six total, and
    systemic rather than unique to Story 1: none of this spec's own test suites (Stories 1, 2,
    4) were written to cite their AC IDs by name/docstring, since that convention didn't exist
    until this very story built the checker that wants it; (2) eight `dangling_reference`
    findings whose IDs are literal fixture-content strings inside `scripts/tests/test_ac_trace.py`
    and `scripts/tests/test_edit_spec_ac_stability_fixtures.py` that happen to collide with
    this spec's own live ID space. See `drift-log.md` DEV-4 for the fuller, updated accounting.
  - Why not resolved: the grammar doc's "no retroactive backfill" rule (`.writ/docs/acceptance-criteria-ids.md`
    → Legacy and Archive Posture) explicitly forbids writing sham tests now to launder a
    completed story's real gap — doing so "would manufacture the appearance of a trace link
    that never existed." Weakening the checker to stop reporting this would defeat the spec's
    own stated purpose (spec.md → Must Include: the bidirectional, dangling-reference-catching
    check). Reviewer's independent assessment: this is a defect in AC-2.5's premise (written
    assuming a clean dogfood state that this spec's own pre-Story-2 test-authoring convention
    made structurally impossible), not in Story 2's implementation.
  - Resolution: **left open for the spec owner.** Options on the table: (a) amend AC-2.5's
    wording via `/edit-spec` to scope it appropriately (e.g., "no *new* blocking findings
    beyond a documented, accepted exception for Stories 1/2/4's pre-existing test suites"), or
    (b) record the `untested_criterion` findings on Stories 1 and 2 as that documented,
    accepted exception directly. AC-2.5's checkbox above is deliberately left unchecked rather
    than marked met by reinterpretation — checking it without the literal condition holding
    would be exactly the kind of quiet box-ticking this whole spec exists to make impossible to
    get away with.
  - Minor, non-blocking follow-up noted by review: the 8 fixture-collision `dangling_reference`
    findings could be reduced (not eliminated — the `untested_criterion` findings remain
    regardless) by choosing fixture IDs outside any real story's ID range in a future cleanup
    pass.
  - **Authoring note:** an earlier version of the AC-2.5 checkbox line above appended this
    disclosure directly after the `` `[AC-2.5]` `` tag, un-anchoring it per this spec's own
    grammar and producing two further spurious findings. Caught by Story 3's architecture
    review before landing; fixed by moving the annotation below the criterion line.
