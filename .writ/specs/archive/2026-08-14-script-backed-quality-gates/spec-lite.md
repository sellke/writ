# Script-Backed Quality Gates (Lite)

> Source: .writ/specs/2026-08-14-script-backed-quality-gates/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Four prompt-level quality guarantees — coverage ≥80%, tests that test the
code, a project that still builds, a project whose own gates are on — become read-only
scripts whose verdicts override the self-report.

**Implementation Approach:**
- Three checkers modeled exactly on `scripts/ac-trace.py`: argparse subparsers, one JSON
  object to stdout with `sort_keys=True`, exit 0/1/2, `#!/usr/bin/env python3`, mode 644
- No new gate number. Extend Gate 2 (`implement-story.md:183–191`) and Gate 4 (`:235–249`)
- `unittest`, not pytest; hyphenated modules imported by path via `importlib.util`
- Stdlib only — no dependencies, no build step

**Files in Scope:**
- `.writ/docs/quality-signal-classification.md` — finding vocabulary (Story 1)
- `scripts/quality-config-audit.py`, `scripts/test-integrity.py`, `scripts/build-smoke.py`
- `scripts/eval-*.py` + `scripts/tests/test_*.py` for each
- `commands/implement-story.md`, `agents/testing-agent.md` (Story 5)
- `commands/initialize.md`, `commands/status.md` (Story 6)

**Error Handling:**
- Unparseable config → `could_not_parse`, dependent findings become `unverifiable`; never
  read a non-match as "gate enabled"
- Absent baseline → empty. Malformed baseline → exit 2, never ignored
- Build fails on missing DB/env/dep → `build_failed_environment`, informational, exit 0

**Integration Points:** Gate 2 ← `build-smoke`; Gate 4 ← `test-integrity` (overrides
`Coverage threshold met`); `/initialize` + `/status` ← `quality-config-audit`

---

## For Review Agents

**Acceptance Criteria:**
1. Against a real yuss checkout: `build_gate_disabled` ×2, `coverage_threshold_absent`,
   `duplicate_lockfile`, `coverage_scope_gap`
2. `authenticity` flags exactly 4 of 147 test files; `coverage` re-derives 57.2%
3. `unverifiable` is distinct from both pass and fail, and never exits 2
4. `bash scripts/eval.sh` passes; the five pinned routing rows at `eval.sh:2232–2236` unchanged

**Business Rules:**
- Verdict trichotomy `pass`/`fail`/`unverifiable`, mapping onto `/status`'s existing
  `Healthy`/`Warning`/`Attention`
- Unparseable is not absent — `next.config.js`/`jest.config.js` are executable JS,
  `tsconfig.json` is JSONC, stdlib parses none of them
- "0 findings" and "0 things inspected" must not read the same — `inspected` is mandatory
- Baseline then ratchet; coverage thresholds written at the measured floor, never 80%
- No permanent-warning instruments — blocking or explicitly waived
- `DEGRADED` is consumed, not redefined; `implement-story.c3` stays `Scope: excluded`
- Node/TS first-class, Python best-effort, everything else `unsupported_stack`
- `/status` may run no build or test command — config audit only

**Experience Design:**
- Entry: invisible — no new command, flag, or question
- Happy path: one extra line each in Gate 2 and Gate 4
- Moment of truth: `Coverage threshold met: YES` contradicted by the measured number, and
  the story does not close
- Error: `unverifiable` reads as "could not run here, and here is why"

---

## For Testing Agents

**Success Criteria:**
1. Every finding code bound by `require_literal` to both the checker and Story 1's doc
2. ≥80% coverage on new code, 100% on error paths
3. Byte-identical stdout across repeat runs, tested at both direct-call and CLI-subprocess
   level

**Shadow Paths to Verify:**
- **Happy:** verdict `pass`, `findings: []`, `inspected.files > 0`
- **Nil input:** nonexistent `--project` → exit 2, never 0
- **Empty input:** zero configs or zero tests → `unverifiable`, never `pass`
- **Upstream error:** truncated coverage report → `unverifiable`, not `pass`, not `fail`

**Edge Cases:**
- Multi-line `import {\n…\n} from '@/…'` → NOT flagged (naive regex over-reports 82%)
- Dynamic `await import('@/…')` → NOT flagged
- `coverageThreshold: 0` → `coverage_threshold_absent` (a zero bar is an absent bar)
- Monorepo with several `package.json` → inspect the package owning the changed files
- Build exceeds timeout → `unverifiable`, never `fail`

**Coverage Requirements:**
- New code: ≥80% · Critical paths: 100% · Error paths: 100%

**Test Strategy:** `unittest` suites per checker with tempdir fixtures; `eval-*.py` fixture
asserters emitting PASS/FAIL TSV. Note CI runs `scripts/eval.sh` only — never
`scripts/tests/` — so eval scenarios plus `require_literal` bindings are the real protection.
