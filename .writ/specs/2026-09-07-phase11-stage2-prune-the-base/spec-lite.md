# Phase 11 Stage 2a: Prune the Base (Lite)

> Source: .writ/specs/2026-09-07-phase11-stage2-prune-the-base/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `system-instructions.md` + `commands/_preamble.md` at ≤ 10,000 bytes (from 28,157), every removed line in an append-only ledger, every `implement-story` gate carrying a verification marker, and the cut kept only because an eight-run Fable 5.1 re-run held 8/8.

**Implementation Approach:**
- Python 3.9 stdlib; tests in `scripts/tests/`; each story ends with `bash scripts/eval.sh` → `Findings: 0` (outside sandbox)
- Line diffs come from `git diff -U0 cf84742 -- <file>`; kept lines stay byte-identical
- Ledger row: `| date | file | reason-class | reason | verbatim text |`; rows land in the removal commit
- Moves (Story 2) before cuts (Story 3); bytes recorded between
- Keep-or-revert (Story 5) is mechanical: every `compare` exit-criteria row `2/2` or revert Stories 2–3

**Files in Scope:**
- `system-instructions.md`, `commands/_preamble.md` — the cut
- `cursor/writ.mdc` — Prime Directive mirror, edited in lockstep
- `.writ/docs/{model-tiers,skills-convention,startup-update-awareness,recommendation-semantics}.md` — new or merged
- `adapters/*.md` — one Fable 5.1 batching line each
- `.writ/decision-records/adr-026-constraint-test-pruning.md`, `.writ/decision-records/pruned-instructions-ledger.md` — new
- `scripts/prune-ledger.py`, `scripts/verdict-provenance.py` — new
- `scripts/eval.sh` — `pruned-base`, `verdict-provenance` checks
- `commands/implement-story.md` — frontmatter `gates:` block; Gate 4.5 percentages dropped
- `.writ/eval/baselines/<date>-claude-fable-5-1.json` — re-run file, Stage 1 `selection` copied verbatim

**Error Handling:**
- Removal without ledger row → `pruned-base` finding naming file and text
- Ledger text reappearing in base → finding (stall signal)
- Gate heading without marker / marker without heading / missing script path → `verdict-provenance` finding
- Re-run below 8/8 → retry failed pair once, then revert Stories 2–3

**Integration Points:** `check_prime_directive_sync`, `check_referenced_paths` (new doc links), `pipeline-baseline.py run|compare`, `install.sh` ships `.writ/docs/*.md`.

---

## For Review Agents

**Acceptance Criteria:**
1. Every line removed from either base file since `cf84742` has a ledger row with identical text; `prune-ledger.py check` exits 0 `[AC-1.3, AC-2.2, AC-3.2]`
2. Base total ≤ 10,000 bytes after Story 3; the cap is blocking from then on `[AC-3.5]`
3. Prime Directive in `cursor/writ.mdc` byte-identical to `system-instructions.md` `[AC-2.3, AC-3.5]`
4. Each `adapters/*.md` gains at most one model-specific line `[AC-3.4]`
5. `implement-story.md` frontmatter names every gate with `script:` or `verification: prose-only`; `verdict-provenance` exits 0 `[AC-4.1]`
6. `compare` of Stage 1 vs re-run prints exit criteria `2/2` on all four rows, or the revert is recorded `[AC-5.3, AC-5.4]`

**Business Rules:**
- Constraint test: environment fact or human boundary stays; behavior request leaves (ADR-026)
- Ledger append-only; removed includes moved; rows in the removal commit
- Kept lines byte-identical; moves before cuts; selection reused verbatim
- ADR-013: no merge, PR, or release; decision-log line per story

**Experience Design:**
- Entry: `/implement-spec`; installed projects see it after `/release`
- Happy path: ADR + empty ledger → five moves → cuts to cap → gate markers → eight runs
- Moment of truth: `compare` table, exit criteria unchanged at a third of the bytes
- Feedback: one line per finding; one summary line with bytes, ledger count, re-adds
- Error: blocked at the offending file and text; revert path names the commit range

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest` green; new bash fixture tests green
2. `bash scripts/eval.sh` Findings: 0 at every story close
3. Base bytes ≤ 10,000 (Story 3 onward); eight-run re-run 8/8 (Story 5)

**Shadow Paths to Verify:**
- **Happy path:** removal + ledger row in one commit → check green
- **Nil input:** no ledger file yet → check reports bytes, zero rows, no finding
- **Empty input:** empty `gates:` block → one finding per gate heading
- **Upstream error:** `git diff` fails (bad base commit) → exit 2 with the git error, no findings fabricated

**Edge Cases:**
- Line removed then re-added → re-add finding names the ledger date
- Ledger row with pipe in text → escaped, round-trips
- Kept line reflowed → reads as removal without row → finding (intended)
- `compare` with differing `selection` → refusal, so Story 5 copies Stage 1's block verbatim
- `runs_per_story` differs between files → per-story medians

**Coverage Requirements:** new scripts ≥ 80% lines; every finding class has a fixture.

**Test Strategy:** pytest fixtures with a temp git repo pinned at a fake base commit; bash fixture tests for both eval checks following `test_eval_pipeline_baseline.sh`.
