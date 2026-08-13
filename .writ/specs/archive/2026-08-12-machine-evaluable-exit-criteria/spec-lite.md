# Machine-Evaluable Exit Criteria (Lite)

> Source: .writ/specs/2026-08-12-machine-evaluable-exit-criteria/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `scripts/exit-criteria.py check --command <name> --state <path>` —
a stop-time gate returning `met | unmet | impossible` with per-criterion evidence.

**Implementation Approach:**
- Classify criteria first (Story 1), implement only what is classified (Story 3)
- Predicates read `.writ/state/*.json`, spec folders, and git — never write
- Reuse `scripts/phase-state.py` `cmd_progress` (returns a dict) rather than
  re-reading phase state; reuse `scripts/spec-status.py` and `scripts/story-deps.py`
- Eval integration copies the `check_story_deps` shape in `scripts/eval.sh:2109`

**Files in Scope:**
- `scripts/exit-criteria.py` — new, the checker
- `scripts/eval-exit-criteria.py` — new, PASS/FAIL TSV fixture scenarios
- `scripts/tests/test_exit_criteria.py` — new, predicate unit tests
- `scripts/eval.sh` — append `check_exit_criteria()` + `CHECKS` entry, modify nothing
- `commands/implement-phase.md`, `commands/implement-spec.md` — write run record, call checker
- `.writ/docs/exit-criteria-classification.md` — new; `.writ/docs/phase-execution-state-format.md` — document fields
- `adapters/claude-code.md` — `/goal` wiring under § Quality Gates with Hooks

**Error Handling:**
- State file missing/unparseable → `impossible`, never `unknown` or `unmet`
- Pre-spec state file lacking the new fields → `unknown`, never `unmet`
- Predicate raises → `impossible` with the exception named

**Integration Points:** `scripts/eval.sh` (append-only), `phase-state.py` reducers.
**Out of scope:** `commands/implement-story.md`, `scripts/eval-leanness.py`, rewriting any criterion.

---

## For Review Agents

**Acceptance Criteria:**
1. Three-verdict contract correct for both commands, with per-criterion evidence
2. Rollup precedence holds: impossible > unmet > unknown/met
3. Unreadable inputs yield `impossible`; missing new fields yield `unknown`
4. Each predicate cites the criterion text it evaluates, asserted by `eval.sh`
5. Archived phase-execution files verdict-match their recorded outcomes

**Business Rules:**
- Reaching a retained pause **satisfies** the gate — a goal condition must be
  satisfiable by pausing, not only by finishing (`_preamble.md` § Autonomy Gate Classes)
- Run-record fields are additive; no `schemaVersion` bump; unknown fields preserved
- The checker never writes
- Classification (Story 1) precedes implementation (Story 3) — no unclassified predicate
- `impossible` triggers: `halt_reported` fired · unresolved `challenge_required` ·
  criterion recorded unachievable · `reconcile` state/git mismatch

**Experience Design:**
- Entry: a command reaching its completion step, or `/goal` on Claude Code
- Happy path: verdict `met`, exit 0, run stops legitimately
- Moment of truth: an `unmet` verdict naming which criterion and why
- Feedback: JSON on stdout + the verdict in the completion report
- Error: `impossible` halts the loop and names the pause — it never spins

**Design Principle 4 note:** "never re-implement what the harness does natively"
was considered and answered in spec.md § On Design Principle 4. Do not re-litigate.

---

## For Testing Agents

**Success Criteria:**
1. `bash scripts/eval.sh --check=exit-criteria` exits 0; full suite stays green
2. One fixture per `impossible` trigger (4 triggers)
3. Every unobservable criterion returns `unknown` + its recorded reason — none `met`
4. Coverage ≥80% on `scripts/exit-criteria.py`

**Shadow Paths to Verify:**
- **Happy path:** all criteria met → `met`, exit 0
- **Nil input:** `--state` points at a nonexistent file → `impossible`, exit 2
- **Empty input:** state file with `specs: {}` → not vacuously `met`
- **Upstream error:** `phase-state.py` raises → `impossible` naming the exception

**Edge Cases:**
- Pre-spec state file (no `exitCriteria[]`) → `unknown`, not `unmet`
- Mixed verdicts including one `impossible` → overall `impossible`, not `unmet`
- All criteria `unknown` → `met` only if all were **declared** unobservable
- Phase 10's archived `PARTIALLY COMPLETE` state → `impossible`

**Coverage Requirements:** new code ≥80%; rollup precedence 100%; error paths 100%.

**Test Strategy:** `pytest scripts/tests/test_exit_criteria.py` for predicates and
rollup; `eval-exit-criteria.py` fixture scenarios for suite integration; a
read-only replay against archived `.writ/state/phase-execution-*.json`.
