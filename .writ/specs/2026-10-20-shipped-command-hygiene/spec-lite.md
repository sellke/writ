# Shipped Command Hygiene (Lite)

> Source: .writ/specs/2026-10-20-shipped-command-hygiene/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Shipped commands stop linking Writ's own development history, eval.sh stops pinning wording-only command prose, and `create-spec.md` loses its coaching.

**Implementation Approach:**
- `scripts/eval-shipped-refs.py` + `check_shipped_refs`: four rules (numbered ADR link; dated archived-spec path, archive or old form; dated research path; `calibrated_against` naming `.writ/state/` or `.writ/specs/archive/` outside a glob). Self-test scenarios, PASS/FAIL TSV, `--root`.
- Remove each link with its label; one plain sentence only where listed. Rewrite five `calibrated_against` values with a shipped path token or `no recorded run`.
- Pin map: recipe in technical-spec.md; one row per instance; categories decide what may be removed.
- Convert rows move to `scripts/eval-command-structure.py` (`heading`, `frontmatter`, `invocation`) run by `check_command_structure`.
- `create-spec.md`: adopt lean-twin cuts that remove coaching; decline anything behavioral, pinned, or test-asserted.
- Python 3.9 standard library. `eval-*` helpers are dev-only.

**Files in Scope:**
- `scripts/eval.sh` — two new checks, pin removals (S1, S2)
- `scripts/eval-shipped-refs.py`, `scripts/tests/test_eval_shipped_refs.py` — new (S1)
- 12 `commands/*.md` — reference removals, `calibrated_against` rewrites (S1)
- `pin-map.md`, `scripts/eval-command-structure.py`, `scripts/tests/test_eval_command_structure.py` — new (S2)
- `scripts/tests/test_product_check_direction.py`, `test_review_panel.py` — mutation cases (S2)
- `commands/create-spec.md`, `cut-log.md`, `scripts/tests/test_governor_enforcement.py` (S3)

**Error Handling:**
- Helper missing → run error, eval exit 2. Broken regex → self-test FAIL.
- Pin removed that a test mutates → change the test in the same commit.
- Lean twins still present → stop; the dependency has not landed.

**Integration Points:**
- `eval-loop-bounds.py` reads `calibrated_against` (assertion 4, refactor literal).
- `test_governor_enforcement.py` asserts `total_overage` exactly.

See spec.md → ## 📋 Business Rules and sub-specs/technical-spec.md.

---

## For Review Agents

**Acceptance Criteria:**
1. `shipped-refs` flags each kind with file:line and passes runtime paths and its self-tests `[AC-1.1, AC-1.2]`
2. The eval-level mutation fails, then passes; a missing helper exits 2 `[AC-1.3]`
3. The tree passes `shipped-refs`; no bare label left; `loop-bounds` passes on the rewrites `[AC-1.4, AC-1.5]`
4. `pin-map.md` has one row per instance; no safety row is `remove`; every keep literal remains `[AC-2.1, AC-2.2]`
5. Each convert row fails on its mutation; the pin count falls by convert + remove `[AC-2.3, AC-2.4]`
6. Tests that mutated removed pins changed with them; suites green `[AC-2.5]`
7. Every lean-twin change is logged adopted or declined, with no byte reasons `[AC-3.1]`
8. Kept pins, structural rows, Jev and spec-analyze tests pass; frontmatter, step numbers, AskQuestion blocks, invocations intact `[AC-3.2, AC-3.3]`
9. Bytes fall; overage repinned exactly, below start and below 29,304; every hunk maps to a log row `[AC-3.4, AC-3.5]`

**Business Rules:**
- Shipped = `commands/*.md` except `*.lean.md`, including `_preamble.md`.
- Runtime paths, placeholders, and globs stay.
- Safety categories never take `remove`; when unsure, keep.
- Cuts remove coaching only; no behavior change; step numbers stay.

**Experience Design:**
- Entry: maintainer runs `bash scripts/eval.sh`.
- Happy path: both new checks pass; pin count lower.
- Moment of truth: a pasted ADR link fails eval with file:line.
- Feedback: one finding per offending line.
- Error: remediation says remove the link, add one sentence if needed.

---

## For Testing Agents

**Success Criteria:**
1. `shipped-refs` passes on the tree and fails on the mutation.
2. Command-file literal pin count lower than the pin map's before count.
3. `create-spec.md` smaller; recorded overage lower; full eval 0 findings; pytest (3.9) and bash tests pass.

**Shadow Paths to Verify:**
- **Happy path:** clean tree → PASS with scenario counts.
- **Nil input:** helper missing → run error, exit 2.
- **Empty input:** `commands/` empty in a temp root → PASS, self-tests still run.
- **Upstream error:** a rule regex matches nothing → self-test FAIL.

**Edge Cases:**
- Old path to an archived spec (`revert.md:178` form) → FAIL.
- Example ID with no archive folder → no finding.
- `.writ/state/phase-execution-*.json` glob on a `calibrated_against` line → no finding.
- Heading text left only as prose → `command-structure` FAIL.

**Test Strategy:**
- Python tests run helpers with `--root <tmp>`; eval-level tests copy `eval.sh` into a temp `scripts/`.
- No test mutates the real repository.
