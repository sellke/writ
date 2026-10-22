# Rendering-Delegation Rows (Lite)

> Source: .writ/specs/2026-10-22-rendering-delegation-rows/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Each adapter's `canvas-preview` row names the renderer `/prototype` delegates to, cites first-party docs, and carries a dated verification status; Claude Code verified live in the lane, Cursor and Codex Desktop via UAT protocols, OpenClaw unverified.

**Implementation Approach:**
- Add `#### Verification record — YYYY-MM-DD` under each adapter's tool-table section: table `Check | Platform & version | Observed | Source | Status`. Status grammar `^(verified|unverified) \d{4}-\d{2}-\d{2}( \((pending UAT|no deployment)\))?$`; Source starts `https://`.
- Claude Code (lane): render one HTML draft via artifact, then preview pane; check native design surface reachability from a command run; record versions and docs URLs.
- Cursor, Codex, OpenClaw: rows from first-party docs; `unverified (pending UAT)` or `(no deployment)`. Codex row becomes CLI clause + Desktop clause, keeping `.writ/prototypes/<date>-<slug>/` and `HTML`.
- `commands/prototype.md` Step 2.5 untouched unless a run contradicts a render-table row; then drift-log it.
- Rows stay one line, first cell `` `canvas-preview` ``, degradation clause verbatim, inside the existing table (the trees spec parses by heading).

**Files in Scope:**
- `adapters/claude-code.md` (S1); `adapters/cursor.md`, `adapters/codex.md`, `adapters/openclaw.md`, `sub-specs/technical-spec.md` § UAT Protocols (S2)
- `scripts/tests/test_platform_neutral_names.py`, `commands/prototype.md` (only if contradicted), `.writ/issues/bugs/2026-10-19-prototype-visual-preview-cursor-only.md`, `drift-log.md` (S3)

**Error Handling:**
- Docs page silent on rendering → "not documented", status unverified.
- Docs URL 404 → do not cite; record "no first-party page found on <date>".
- Headless Claude Code run → record the degradation path; row unchanged.

**Integration Points:**
- `2026-10-22-generated-platform-trees` parses these tables after this spec lands: no new tables, no structural changes.
- `/create-uat-plan` derives Cursor and Codex Desktop scenarios from technical-spec.md § UAT Protocols.

---

## For Review Agents

**Acceptance Criteria:**
1. `adapters/claude-code.md` has a verification record with artifact/preview and native-surface observations, versions, URLs, and `verified` status `[AC-1.1, AC-1.2, AC-1.3]`
2. `adapters/cursor.md`, `codex.md`, `openclaw.md` have records with `unverified` status, a reason, and first-party URLs; row text matches the docs `[AC-2.1, AC-2.2]`
3. Codex row has CLI and Desktop clauses and keeps the pinned keywords `[AC-2.3]`
4. technical-spec.md § UAT Protocols gives Cursor and Codex Desktop a precondition, invocation, what to look for, and the record edit on pass/fail `[AC-2.4]`
5. `test_verification_records` passes for all four adapters; canvas tests green `[AC-1.4, AC-1.5, AC-2.5, AC-3.1, AC-3.2, AC-3.3]`
6. `prototype.md` Step 2.5 unchanged, or changed with a drift-log entry citing the contradicting observation `[AC-3.4]`
7. Origin issue has `### Verification` under `## Resolution` naming this spec and per-platform status `[AC-3.5]`

**Business Rules:**
- Rows state facts; records state evidence. Only the record says verified.
- Unverified is a status, not a defect; the row still names a floor.
- One `canvas-preview` row per adapter, clause verbatim, inside the existing table.

**Experience Design:**
- Entry: lane runs the Claude Code protocol; maintainer runs Cursor and Codex Desktop during UAT.
- Happy path: observation → record → row matches.
- Moment of truth: `/prototype` renders where the row says, or says it did not.
- Feedback: record and row agree; test proves status and source present.
- Error: missing status or URL fails `test_verification_records` naming the adapter.

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest` passes, including `test_verification_records[*]`.
2. `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` prints no FAIL.
3. `bash scripts/eval.sh` (outside the sandbox): 0 findings.

**Shadow Paths to Verify:**
- **Happy path:** four records present, grammar valid.
- **Nil input:** record row with Source "not documented" → test fails (Source must be `https://`); write the docs index page URL instead and say "not documented" in Observed.
- **Empty input:** record heading with no rows → fails.
- **Upstream error:** status text without a date → fails.

**Edge Cases:**
- `verified` without a version in Platform cell → allowed by grammar, flagged in review.
- Two record headings in one adapter → test reads the first; keep one.

**Test Strategy:**
- Static pytest over adapter text using the existing `section`/`first_table`/`cells` helpers; parametrized over the four adapters.
- No network in tests; URLs are checked for prefix only.
