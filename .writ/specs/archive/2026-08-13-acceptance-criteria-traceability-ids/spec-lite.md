# Per-Criterion Traceability IDs (Lite)

> Source: .writ/specs/2026-08-13-acceptance-criteria-traceability-ids/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Stable IDs on every acceptance criterion, cited by tasks and tests, with a
bidirectional orphan check in `/verify-spec`.

**Implementation Approach:**
- ID form `AC-<story>.<n>`, rendered as a **trailing** backticked tag: `` ... then X. `[AC-3.1]` ``
- Suffix placement is load-bearing — `recommend-state.py:378` and `:2981` anchor on
  `^- \[x\] Given `. A prefix breaks UAT derivation. Do not move the tag.
- Stability by high-water mark: `> **AC IDs assigned through:** AC-3.6` under the
  `## Acceptance Criteria` heading. New criterion takes mark+1; siblings never renumber;
  retired numbers never reused.
- Tag is **end-anchored**: `` r"`\[((?:AC-\d+\.\d+)(?:,\s*AC-\d+\.\d+)*)\]`\s*$" ``. Only a
  match counts. An ID token elsewhere on the line is prose — Story 4's criteria quote
  `AC-2.1`–`AC-2.5` as fixture examples and an unanchored scan mis-reads them.
- The marker line contains an ID-shaped token — exclude it from both the definition set and
  the citation set, or every marker satisfies its own ID.
- Blocking checks get an executable reference: `scripts/ac-trace.py check --spec <dir>`,
  read-only, one JSON object to stdout, exit 0/1/2. Pattern: `spec-deps.py`, `story-deps.py`.
- Check lands as `/verify-spec` **3e/3f**, not a Check 9 — the command's `exit_criteria`
  promise an eight-row check table.

**Files in Scope:**
- `.writ/docs/acceptance-criteria-ids.md` — new; the grammar the checker implements against
- `commands/create-spec.md`, `agents/user-story-generator.md` — the emitter
- `scripts/ac-trace.py` (+ `tests/test_ac_trace.py`, `eval-ac-trace.py`, `eval.sh`) — checker
- `commands/verify-spec.md` — Check 3e/3f wiring
- `commands/edit-spec.md` — never-renumber rule + marker advance
- **Do not touch:** `recommend-state.py`, `eval-recommend-stage.py`,
  `eval-recommend-state-adversarial.py`

**Error Handling:**
- Malformed marker, or spec folder without `user-stories/` → exit 2, path named
- Findings present → exit 1 (distinct from exit 2)
- Story with zero IDs → `legacy_story`, informational, exit unaffected

---

## For Review Agents

**Acceptance Criteria:**
1. A criterion inserted by `/edit-spec` leaves every sibling ID byte-identical
2. A `Completed ✅` story with an untested criterion is a blocking finding, not a warning
3. A task or test citing an undefined ID is named with that ID
4. `recommend-state.py` and its two eval fixture sets are unmodified at spec close

**Business Rules — finding vocabulary:**
- `untasked_criterion` — no task cites it → **blocking at any status** (task tags are
  authored at spec time, so this is a defect the moment it's written)
- `untested_criterion` — tasked, no test citation, story `Completed ✅` → **blocking**
- `dangling_reference`, `duplicate_id`, `marker_violation`, `partial_adoption` → **blocking**
- `legacy_story` (zero IDs) → informational; mirrors Check 4d treating a missing
  `Dependencies` header as `[]`
- Test citations count only from test-shaped paths (`tests/`, `test/`, `spec/`,
  `__tests__/`, `test_*`, `*_test.*`, `*.test.*`, `*.spec.*`); other occurrences outside
  `.writ/` are source citations and do **not** satisfy coverage
- Archived specs never scanned; no retroactive backfill
- Nothing auto-fixable — 3e/3f are report-only in default mode; Phase 4 never touches them

**Evidence base:** Mäder & Egyed 2015, Empir. Softw. Eng. 20(2):413–441 — 71 subjects, 461
tasks, 24% faster / 50% more correct **with recorded caveat**: human maintenance on
requirement-to-code links, not agent implementation of story criteria. Mechanism transfers;
effect size is not a Writ promise. See spec.md → ## Evidence Base.

---

## For Testing Agents

**Success Criteria:**
1. One test per finding code (7 codes), each asserting severity as well as detection
2. Marker exclusion proven: a story whose only ID occurrence is the marker reports
   `untasked_criterion`, never clean
3. Byte-identical repeat runs; deterministic finding order
4. This spec's own 4 stories pass `ac-trace.py` as the dogfood fixture

**Shadow Paths to Verify:**
- **Happy path:** all IDs tasked, `Completed ✅` stories tested → exit 0
- **Nil input:** `--spec` pointing at a folder with no `user-stories/` → exit 2, path named
- **Empty input:** story with zero criteria lines → no findings, not an error
- **Upstream error:** unreadable story file → exit 2, never a silent clean pass

**Edge Cases:**
- Criterion tagged `[AC-3.1, AC-3.2]` (two IDs, one line) → both defined, `duplicate_id`
  only if an ID repeats across lines
- ID cited in a git-ignored or binary file → not a citation
- Same ID in two different specs → scoped per spec; no cross-spec collision

**Coverage Requirements:**
- New code: ≥80% · Critical paths: 100% · Error paths: 100%

**Test Strategy:**
- `scripts/tests/test_ac_trace.py` unit tests; `scripts/eval-ac-trace.py` fixture scenarios
  building disposable spec folders in tempdirs, per `eval-story-deps.py`
