# Phase 11 Stage 1: Repair and Baseline (Lite)

> Source: .writ/specs/2026-09-05-phase11-repair-and-baseline/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Repaired Writ corpus (19 dead ends closed, 3 blocking eval checks) plus one committed Claude Fable 5.1 pipeline baseline over four replayed yuss.app stories.

**Implementation Approach:**
- Python 3.9 stdlib only; tests in `scripts/tests/`; every story ends `bash scripts/eval.sh` → `Findings: 0` (outside sandbox)
- Replay isolation: fresh clone truncated at parent SHA (`fetch --depth 1 <sha>`), never a worktree; assert `rev-list --all` count before the model runs
- Token counting: Anthropic `count_tokens` via `urllib`, keyed by `ANTHROPIC_API_KEY`, content-hash cache in `.writ/state/`
- Runner: `claude -p "/implement-story <id>" --model claude-fable-5-1 --output-format stream-json`; parse usage + gate strings from transcript
- Story 1 lands before any measurement

**Files in Scope:**
- `commands/{create-spec,implement-spec,implement-story,verify-spec,release,status,ship}.md` — dead-end fixes only
- `adapters/{cursor,claude-code,codex,openclaw}.md` — staleness fixes only
- `.writ/manifest.yaml`, `.writ/knowledge/lessons/*.md`, `.writ/decision-log.md` (new)
- `scripts/measure-invocation.py` — `--tokenizer anthropic`
- `scripts/pipeline-baseline.py` (new) — `select` / `run` / `ingest` / `compare`
- `scripts/eval.sh` — `check_referenced_paths` (path tokens resolve against root/`commands/`/archive; bare names by basename in `git ls-files -co`; allowlist rows `path|command|reason`, self-checked for missing fields and stale rows — DEV-005/006), `check_skill_manifest_parity`, `check_knowledge_integrity`, `check_pipeline_baseline`
- Story 1 amendments (Gate 3, 2026-09-06): `--force` removed with a `/revert` pointer (DEV-002); integration failure → fix-in-place / revert / abort (DEV-003); typecheck detection by manifest file, test runners per `ship.md` (DEV-004); lesson TL;DR = source-commit title when payload `statement` was empty (DEV-007)
- `.writ/eval/baselines/<date>-claude-fable-5-1.json` (new)
- Story 2 amendments (Gates 0–3, 2026-09-06): cache key `sha256(model + "\0" + text)` via exported `token_cache_key` (DEV-014); tokenizer tests in `test_measure_invocation.py` (DEV-015); `token_failures` counts distinct texts by hash (DEV-016); `--tokenizer estimate` is chars/N regardless of tiktoken, `auto` without a key is pre-story behavior (DEV-017); `token_model`/`token_failures` keys appear only on the anthropic path; helpers `_count_tokens_anthropic`, `TokenCache`, `_AnthropicCounter` are importable by path for Stories 4–5
- Story 4 amendments (Gates 0–3, 2026-09-06): inputs staged from `parent_sha`, never yuss HEAD, with an answer-leak assertion (DEV-018); permission bypass flags with compensating controls — user-approved (DEV-019); completion re-derived from `implement-story.md` predicates, `build-smoke.py`/`test-integrity.py` called for Gates 2/4, `exit-criteria.py` not used (DEV-020); current-Writ overlay via `install.sh --no-commit`, `writ{source, commit, dirty, …}` replaces `writ_scripts` — user-approved (DEV-021); `tests.suite` + `tests.original`, `deps` before `claude` (DEV-022); `Popen` + `killpg`, `--cap` + `--budget-usd` (DEV-023); `gates.<g>.source`, `tokens_main_thread`, sidecar, session-jsonl ingest, exit 3 (DEV-024); no archive fallback/lock, smoke run deferred — user-approved (DEV-025). `RUN_KEYS`/`GATE_NAMES` are the record contract Story 5 imports
- Story 3 amendments (Gates 0–3, 2026-09-06): field/class/reason names per story-3 AC-3.1, exported as `SCHEMA_KEYS`/`SELECTION_KEYS`/`REASONS` — Stories 4–5 import these, not tech-spec §2 (DEV-008); short class exits 1, usage/refusal exits 2 (DEV-009); top level adds `runs_per_story` (null until run) and `rejection_tally` (DEV-010); reasons add `git_error`, `no_surface_class` (DEV-011); test files need a source extension, deleted files excluded, test paths don't set class (DEV-012); `--live-test-scope {story,file}` (user-approved `file` for the committed baseline — story → Approved Scope Additions) and `--force`; `--out` refused if it exists (DEV-013)

**Error Handling:**
- No API key → estimate + `token_method_validated: false`; `run` refuses to start
- `claude` missing → stop before any checkout, name install path
- Live-service test → excluded at `select`, reason in `excluded[]`
- Crash mid-`run` → records flushed per run; resume skips completed (story, n) pairs

**Integration Points:** `exit-criteria.py`, `test-integrity.py`, `build-smoke.py` re-derive verdicts stored beside agent-reported ones; `~/Projects/yuss` is read-only.

---

## For Review Agents

**Acceptance Criteria:**
1. Every backticked `*.md` path in `commands/*.md` exists, is created by a named command, or is allowlisted with a reason; `comm -3` skills vs manifest is empty; no knowledge entry has a single-character bullet — all three enforced by blocking `eval.sh` checks `[AC-1.1, AC-1.2, AC-1.3]`
2. `measure-invocation.py` with a key reports `token_method: anthropic-count-tokens`, `token_method_validated: true`, model ID; without a key its output is byte-identical to today except `token_note` `[AC-2.1, AC-2.2]`
3. `select` writes exactly four stories, one per surface class, each with parent SHA and admitting criteria values, plus an `excluded[]` list `[AC-3.1, AC-3.2]`
4. Each run record stores reported and re-derived verdicts for Gates 2, 4, completion; `rederived: null` where no script exists `[AC-4.4]`
5. Baseline JSON: `schema: pipeline-baseline-v1`, 8 run records, no free-text field > 200 chars, no source or transcript text, no keys `[AC-5.1, AC-5.3]`
6. `check_pipeline_baseline` notes when absent, blocks on schema violation; `compare` refuses mismatched selections `[AC-5.2, AC-5.3, AC-5.5]`

**Business Rules:** 1 isolation asserted and recorded · 2 yuss read-only, temp dirs only · 3 secrets from env only · 4 one model per file · 5 verdict beside re-derivation · 6 dead ends blocked not noted · 7 ADR-013: no merge/PR/release · 8 decision-log line per story · 9 Fable 5.1 only

**Experience Design:**
- Entry: `.writ/eval/baselines/` + `pipeline-baseline.py compare`
- Happy path: `select` → `run --runs 2` → `eval.sh --check=pipeline-baseline` → commit
- Moment of truth: first `compare` after a Stage 2 cut decides keep/revert on numbers
- Feedback: one stdout line per story per run; JSON is the record
- Error: see spec.md → ## 🎯 Experience Design → Error experience

---

## For Testing Agents

**Success Criteria:**
1. Goal Card DONE WHEN 1 and 2 hold verbatim (spec.md → Success Criteria)
2. New scripts ≥80% coverage; `count_tokens` and `claude` calls mocked; both key/no-key branches tested
3. `eval.sh` new checks: red against pre-story fixtures, green after

**Shadow Paths to Verify:**
- **Happy path:** 4 stories × 2 runs → 8 records → check passes → commit
- **Nil input:** no key / no `claude` / no yuss path → named refusal, zero side effects
- **Empty input:** yuss archive yields <4 admissible stories → `select` fails naming the short class
- **Upstream error:** API timeout → estimate for failed items, `validated: false`, failure count; headless run timeout → record `status: timeout`, continue

**Edge Cases:**
- Story whose parent SHA is a merge commit → use first parent, record it
- Two stories in one commit → both eligible, tie → most recent
- Checkout predates a needed script → copy current `scripts/`, record `writ_scripts: current`
- `compare` across different `runs_per_story` → allowed, per-story medians

**Coverage Requirements:** new code ≥80%; isolation assertion and secret-exclusion paths 100%

**Test Strategy:** pytest with mocked subprocess/HTTP for `pipeline-baseline.py` and `measure-invocation.py`; bash fixture tests for the four `eval.sh` checks; one real smoke run recorded in Story 4's What Was Built.
