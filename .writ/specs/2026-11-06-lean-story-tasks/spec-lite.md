# Lean Story Tasks (Lite)

> Source: .writ/specs/2026-11-06-lean-story-tasks/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Generated story tasks name files, external contracts, and test order and stay ≤50 words; rules are stated once; new stories have no generic Definition of Done; a trial measures the effect.

**Implementation Approach:**
- `ac-trace.py` gains informational `oversized_task` for `Not Started` stories; Step 2.6a treats it as a failure
- Prose changes in the generator and two commands, each pinned by a test, platform trees regenerated
- The shipped generator states rule content, not this spec's rule numbers; `create-spec.md` edits are offset to stay net-zero in bytes
- Trial in two worktrees from the pre-implementation commit of one small archived spec

**Files in Scope:**
- `scripts/ac-trace.py`, `scripts/tests/test_ac_trace.py`, `.writ/docs/acceptance-criteria-ids.md` — the finding
- `agents/user-story-generator.md` — task rules, no DoD, rule citations
- `commands/create-spec.md` — Steps 2.4, 2.6, 2.6a, 2.8
- `commands/verify-spec.md` — Checks 1d, 3b
- `scripts/tests/test_governor_enforcement.py` — byte ledger
- `claude-code/agents/writ-story-gen.md`, `cursor/plugin/**` — generated

**Error Handling:**
- No tasks section or no status → no `oversized_task`
- Anchor retry still over 50 words → listed in Step 2.9, package still written
- Trial arm stops → recorded, not retried alone

**Integration Points:**
- `/create-spec`, `/edit-spec`, `/implement-phase` via the generator; `/verify-spec` 1d/3b, 3e/3f

**Line Budget Constraints:** `create-spec.md` and `verify-spec.md` are over budget; target net-zero bytes, disclose any growth in `KNOWN_OVER_BUDGET`.

---

## For Review Agents

**Acceptance Criteria:**
1. `ac-trace.py check` reports `oversized_task` for a >50-word task in a `Not Started` story, nothing for other statuses, and its exit code is unchanged `[AC-1.1, AC-1.3, AC-1.4]`
2. Generator task rules state what tasks prescribe and omit; template has no Definition of Done `[AC-2.1, AC-2.2, AC-3.1]`
3. Step 2.6a regenerates a story with `oversized_task` once at `anchor` `[AC-2.3]`
4. `/verify-spec` passes a new story with no DoD and still warns on an unchecked DoD in a completed legacy story `[AC-3.3, AC-3.4]`
5. `create-spec.md` Steps 2.4 and 2.8 and the generator's hints cite rule numbers `[AC-4.1, AC-4.2]`
6. Trial report compares both arms and ends in one verdict line `[AC-5.3, AC-5.5]`

**Business Rules:**
- Spec Business Rules 1–6 (`spec.md` → Specification Contract)

**Experience Design:**
- Entry: `/create-spec`, `/edit-spec`, `/implement-phase`
- Happy path: lock → generate → Step 2.6a passes
- Moment of truth: Story 1 in about half the words, ACs and Notes unchanged
- Feedback: Step 2.9 lists `story=N task N.M words=W` after a failed retry
- Error: legacy DoD still checked; missing DoD not flagged

---

## For Testing Agents

**Success Criteria:**
1. `uv run --isolated --python 3.9 --with pytest pytest` and the 3.14 run pass, each run alone
2. `bash scripts/eval.sh` passes; `python3 scripts/gen-platform-trees.py --check` clean
3. `trial-report.md` exists with a verdict line

**Shadow Paths to Verify:**
- **Happy path:** all tasks ≤50 words → no finding
- **Nil input:** no tasks section → no finding
- **Empty input:** checkbox and tag only → 0 words, no finding
- **Upstream error:** completed legacy story with long tasks → no finding

**Edge Cases:**
- Exactly 50 words → no finding; 51 → finding
- Task without `N.M` number → detail names the line
- Inline code with spaces counts each word

**Coverage Requirements:**
- New code: ≥80%
- Critical paths: 100%
- Error paths: 100%

**Test Strategy:**
- Temp-folder fixtures in `test_ac_trace.py`; literal pins for prose changes; regenerated trees checked by `--check`
