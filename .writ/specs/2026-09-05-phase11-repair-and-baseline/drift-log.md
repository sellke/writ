# Drift Log — Phase 11 Stage 1: Repair and Baseline

> Parent: [`spec.md`](spec.md)

Deviations recorded during implementation. Per-story detail lives in each
story's `## What Was Built` → *Deviations from Spec*; this file carries the
spec-level entries. Append-only; `spec.md` is never auto-modified.

| ID | Story | Severity | Title |
|---|---|---|---|
| DEV-001 | 1 | Medium | `check_knowledge_integrity` also blocks on an empty `## TL;DR` |
| DEV-002 | 1 | Small | `--force` removed with a `/revert` pointer rather than bare removal |
| DEV-003 | 1 | Small | Integration-failure next action is fix-in-place / revert / abort, not `implement-phase` quarantine vocabulary |
| DEV-004 | 1 | Small | Typecheck detection list is new (`ship.md` detects no typechecker); test-runner detection borrowed as specified |
| DEV-005 | 1 | Small | Bare `*.md` tokens in `check_referenced_paths` resolve by basename anywhere in `git ls-files -co` |
| DEV-006 | 1 | Small | Allowlist self-checks (malformed row, stale row) are additional blocking findings |
| DEV-007 | 1 | Small | Lesson TL;DR reconstructed from the H1 title; payload `statement` was empty in all ten |
| DEV-008 | 3 | Medium | technical-spec §2 field/class/reason names superseded by story-3 AC-3.1 names; `SCHEMA_KEYS`/`SELECTION_KEYS`/`REASONS` are the contract |
| DEV-009 | 3 | Small | Short surface class exits 1 (task 3.5), not 2 (tech-spec §7); 2 is reserved for usage/refusal |
| DEV-010 | 3 | Small | Top-level keys add `runs_per_story` (null until run) and `rejection_tally` (uncapped counts behind the capped `excluded[]`) |
| DEV-011 | 3 | Small | Reason codes add `no_surface_class` and `git_error` (tech-spec §8) to AC-3.2's six |
| DEV-012 | 3 | Small | Test-file rule narrowed: source extension required, deleted files excluded, test files ignored for class paths — each echoed in `criteria` |
| DEV-013 | 3 | Small | New flags `--live-test-scope` (default `story`, echoed) and `--force`; `--out` refused whenever it exists |
| DEV-014 | 2 | Small | Cache key separator is NUL per story task 2.3; technical-spec §5 said `"\n"` — intra-spec conflict, story text followed |
| DEV-015 | 2 | Small | Tokenizer tests live in `test_measure_invocation.py` per story task 2.1, not §10's `test_measure_invocation_tokenizer.py` — intra-spec conflict, story text followed |
| DEV-016 | 2 | Small | `token_failures` counts distinct failed texts by content hash — a skill shared by N commands is 1 failure |
| DEV-017 | 2 | Small | `--tokenizer estimate` bypasses an installed `tiktoken` (chars/N regardless); `auto` without a key keeps tiktoken-if-installed |
| DEV-018 | 4 | Medium | Inputs staged from the parent commit, never yuss HEAD; `assert_answer_scrubbed` aborts with `answer_leak` |
| DEV-019 | 4 | Medium | Permission mode is bypass (`--dangerously-skip-permissions --permission-prompts none …`), not `acceptEdits`; compensating controls recorded — user-approved |
| DEV-020 | 4 | Medium | Completion re-derived from `implement-story.md` success predicates, not `exit-criteria.py` (no `implement-story` mode); `build-smoke.py` / `test-integrity.py` called for Gates 2/4 |
| DEV-021 | 4 | Medium | Current-repo Writ overlaid via `install.sh --platform claude --no-commit --force`; `writ{source, commit, dirty, checkout_manifest_version, manifest_diff_count}` replaces `writ_scripts` — user-approved |
| DEV-022 | 4 | Small | Tests split into `tests.suite` and `tests.original` (story-commit test files restored post-exit); `pnpm install` before `claude` as `deps`; `pnpm` in preflight |
| DEV-023 | 4 | Small | `Popen(start_new_session=True)` + `killpg` escalation replaces `subprocess.run(timeout=)`; `--budget-usd` → `--max-budget-usd` beside `--cap`; no `--max-turns` in `claude` 2.1.260 |
| DEV-024 | 4 | Small | `gates.<g>.source`, `tokens_main_thread`, `exit_criteria.reported` heuristic, `run-meta.json` sidecar, session-`.jsonl` ingest (`cost_usd: null`), exit 3 for scrub/HEAD-moved |
| DEV-025 | 4 | Small | No `git archive` fallback (fetch refusal → `fetch_failed`); no `<json>.lock`; smoke run (task 4.2) deferred — user-approved |

---

## DEV-001 — `check_knowledge_integrity` also blocks on an empty `## TL;DR`

**Severity:** Medium · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review

**Spec said:** the check fails when any `.writ/knowledge/**/*.md` has a bullet whose content is a single character. **Implementation did:** additionally emits a blocking finding for a `## TL;DR` section with no text (fixture asserts it). **Why it matters:** scope expansion of a blocking gate — a future ledger entry without a statement now fails `eval.sh`. Consistent with the spec's own observation that all ten shredded entries had an empty TL;DR and with `knowledge_writeback` now rejecting empty statements. **Resolution:** ⚠️ flagged; pipeline PASS. `spec.md` unchanged; a maintainer who disagrees removes the `tldr` branch and its fixture.

## DEV-002 — `--force` removed with a `/revert` pointer

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. Spec allowed removal; implementation removed the clause and points at `/revert` (exists) as the re-run path. `spec-lite.md` amended.

## DEV-003 — Integration-failure next action vocabulary

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. Spec said "quarantine per `implement-phase`'s vocabulary"; quarantine is a spec-level lane concept, so at story level `implement-spec.md` offers Fix in place (`/implement-story {id} --review-only`), Revert (`/revert`), Abort. `spec-lite.md` amended.

## DEV-004 — Typecheck detection by manifest file

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. `ship.md` detects test runners but no typechecker; test-runner detection follows `ship.md:92–96`, typecheck detection is by manifest file (`tsconfig.json` / mypy / `cargo check` / `go vet`). `spec-lite.md` amended.

## DEV-005 — Bare-name resolution by basename

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. Path-form tokens resolve against repo root, `commands/`, and the spec archive; bare tokens resolve if any file with that basename exists in `git ls-files -co`. Matches the assessment's `objective.md` criterion but lets the dogfooding `.writ/` workspace stand in for "created by a named command" for ~10 runtime-created names (reviewer Minor 1). `spec-lite.md` amended to record the rule.

## DEV-006 — Allowlist self-checks

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. Rows missing a command/reason and rows no longer referenced (when the creating command exists) are blocking findings. Fixtures for both added at Gate 4. `spec-lite.md` amended.

## DEV-007 — TL;DR from title

**Severity:** Small · **Story:** 1 · **Found:** 2026-09-06, Gate 3 review. The payload `statement` was empty in all ten source records (which is why the files had empty TL;DRs); the H1 is the lesson as source commits `a9b3ed8` / `2dba942` list it. Not invented content, not a distinct recovered field. `spec-lite.md` amended.

## DEV-008 — technical-spec §2 names superseded by story-3 AC-3.1

**Severity:** Medium · **Story:** 3 · **Found:** 2026-09-06, Gate 0 + Gate 3

**Spec said:** `sub-specs/technical-spec.md` §2 sketches the baseline with `created`, `yuss_commit_at_selection`, `parent_is_first_parent_of_merge`, `admitted_by`, `commit_found_via`, `test_command`, `writ_version`/`writ_commit`, classes `api|ui|data`, and reasons `denylist:prisma|no_test_file|no_commit|class_full:ui`. **Implementation did:** followed story-3 AC-3.1, the later and more specific artifact — `generated_at`, `yuss_head`, `parent_is_merge`, `criteria_values`, `commit_source`, classes `api_route|ui|data_model|refactor`, reasons `status_not_completed|commit_unresolved|no_test_files|live_service_import|migration_prerequisite|class_filled` (+ `git_error`, `no_surface_class`, DEV-011). `test_command` is not emitted; Story 4 derives it from `test_files`. **Why it matters:** Story 4 reads `selection[]` verbatim and Story 5's validator checks the schema — both must read Story 3's *What Was Built* and import `SCHEMA_KEYS`/`SELECTION_KEYS`/`REASONS` from `scripts/pipeline-baseline.py`, not transcribe §2. **Resolution:** ⚠️ flagged; pipeline PASS. `technical-spec.md` §2 is left as authored (append-only rule); the module constants are the contract.

## DEV-009 — Short class exits 1

**Severity:** Small · **Story:** 3 · **Found:** 2026-09-06, Gate 0. Task 3.5 says exit 1; tech-spec §7 says 2. Implemented 1; 2 is reserved for usage errors and refusals (`--yuss` invalid, `--out` inside yuss or existing without `--force`, zero candidates). `spec-lite.md` amended.

## DEV-010 — `runs_per_story` and `rejection_tally` at top level

**Severity:** Small · **Story:** 3 · **Found:** 2026-09-06, Gate 0. AC-3.1's "exactly" list omits both. `runs_per_story: null` exists so Story 4 fills it and Story 5's `runs = runs_per_story × 4` check finds the key; `rejection_tally` gives counts for all ~364 rejections while `excluded[]` stays capped at 10. `spec-lite.md` amended.

## DEV-011 — Two additional reason codes

**Severity:** Small · **Story:** 3 · **Found:** 2026-09-06, Gate 1. `git_error` (tech-spec §8 row the story omitted) and `no_surface_class` (a Completed, resolved, tested story whose commit touches no class path and is not a refactor — AC-3.2 has no reason for it). Both in `REASONS`; `criteria.reason_codes` echoes the vocabulary. `spec-lite.md` amended.

## DEV-012 — Test-file rule narrowed

**Severity:** Small · **Story:** 3 · **Found:** 2026-09-06, Gate 1. Test files must carry a source extension (`tests/integration/README.md` matched `stripe` in prose otherwise); files the commit deleted are excluded (no content at `<commit>`); test files do not count toward class paths (`app/api/x/__tests__/` alone is not an API-route change). Each echoed as a `criteria` key. Side effect noted by review: `tests/setup.ts`-style helpers count as test files and reach Story 4's `test_files`.

## DEV-013 — `--live-test-scope`, `--force`, and `--out` refusal

**Severity:** Small · **Story:** 3 · **Found:** 2026-09-06, Gate 0. `--live-test-scope {story,file}` carries the user-approved widening (story file → Approved Scope Additions) as a flag echoed in `criteria`, default strict. `--out` is refused whenever it exists unless `--force` — stricter than tech-spec §9 — to protect Story 4's run records. `spec-lite.md` amended.

## DEV-014 — Cache key separator

**Severity:** Small · **Story:** 2 · **Found:** 2026-09-06, Gate 0. Story task 2.3 says `sha256(model + "\0" + text)`; tech-spec §5 says `"\n"`. NUL implemented (the story is the later, more specific artifact); exported as `token_cache_key(model, text)` so no caller re-derives the formula. `spec-lite.md` amended.

## DEV-015 — Tokenizer test location

**Severity:** Small · **Story:** 2 · **Found:** 2026-09-06, Gate 0. Tech-spec §10 names a new `test_measure_invocation_tokenizer.py`; story task 2.1 extends the existing `test_measure_invocation.py`. Story followed; six new test classes live in the existing file. `spec-lite.md` amended.

## DEV-016 — `token_failures` is per distinct text

**Severity:** Small · **Story:** 2 · **Found:** 2026-09-06, Gate 3 review. AC-2.4's "number of failed texts" is read literally: failures are counted once per content hash, so a skill referenced by N commands that fails to count is one failure with one label, and a failed text is not re-requested within the run. `spec-lite.md` amended.

## DEV-017 — `--tokenizer estimate` semantics

**Severity:** Small · **Story:** 2 · **Found:** 2026-09-06, Gate 3 review. Task 2.5 left `estimate` undefined relative to an installed `tiktoken`. Implemented: `estimate` is chars/N regardless of site-packages (this is what makes `--tokenizer estimate` a safe test flag); `auto` without a key preserves the pre-story tiktoken-if-installed path so AC-2.2 byte-identity holds. The tiktoken branch's `validated: true` mislabel is untouched, per story Notes — follow-up candidate. `spec-lite.md` amended.

## DEV-018 — Inputs from the parent, never HEAD

**Severity:** Medium · **Story:** 4 · **Found:** 2026-09-06, Gate 0

**Spec said:** technical-spec §3 stages the story and spec files "from `$YUSS` at HEAD". **Implementation did:** verifies the inputs in the checkout tree at `parent_sha` (all four parents carry the spec folder active with the story `Not Started`), falls back to `git -C <yuss> show <parent_sha>:<path>` only if a file is missing, and asserts before invoking `claude` that the staged story has no `## What Was Built`, no `> **Commit:**`, and Status ≠ Complete(d) — a violation aborts the run with `reason: answer_leak`. `inputs ∈ {parent, parent_show}`, `isolation.answer_scrub_asserted` added. Story-commit test files are restored only after the agent exits. **Why it matters:** the HEAD/archive copy of every selected story carries `Status: Completed`, the closing commit SHA, and a `What Was Built` file list — the answer key. **Resolution:** ⚠️ flagged; pipeline PASS. Story → Approved Scope Additions records the correction.

## DEV-019 — Permission mode is bypass

**Severity:** Medium · **Story:** 4 · **Found:** 2026-09-06, Gate 0 · **User decision** 2026-09-06

**Spec said:** technical-spec §4 `--permission-mode acceptEdits`. **Implementation did:** `--dangerously-skip-permissions --permission-prompts none --setting-sources project --strict-mcp-config --no-session-persistence`; `invocation.permission_mode: "bypass"`; exact argv recorded; `CLAUDECODE`/`CLAUDE_CODE_ENTRYPOINT` stripped from the child env. Compensating controls: the checkout has no remotes, `.git/FETCH_HEAD` is removed, yuss `HEAD` is asserted unchanged (exit 3 on change), no `.claude/settings.json` or hooks exist at the parents or in the overlay. **Why it matters:** in `-p` mode anything that would prompt is denied and `acceptEdits` does not cover Bash — `pnpm test`, `git commit`, and `python3 scripts/*.py` would all be denied and the record would measure denial handling. **Resolution:** user-approved (story → Approved Scope Additions, decision 2).

## DEV-020 — Completion re-derivation and Gate 2/4 scripts

**Severity:** Medium · **Story:** 4 · **Found:** 2026-09-06, Gate 0 (exit-criteria) and Gate 3 (build-smoke / test-integrity)

**Spec said:** AC-4.4 / Business Rule 5 re-derive gate verdicts with `exit-criteria.py check`, `build-smoke.py check`, `test-integrity.py coverage`. **Implementation did:** `exit-criteria.py` has no `implement-story` mode and requires an `execution-*.json` only `/implement-spec` writes, so completion is re-derived from `implement-story.md`'s own success predicates (Status Complete(d), commit SHA in header, `## What Was Built`, `cat-file -e <sha>`) — `exit_criteria: {reported, rederived, rederived_by}`. Gate 3 found `build-smoke.py` / `test-integrity.py` had been dropped without approval; the fix pass restores both calls (`gate2_build.rederived`, `gate4_tests.integrity`, `unverifiable` on non-zero exit). **Resolution:** ⚠️ flagged; pipeline PASS after the fix pass.

## DEV-021 — Current-Writ overlay

**Severity:** Medium · **Story:** 4 · **Found:** 2026-09-06, Gate 0 · **User decision** 2026-09-06

**Spec said:** AC-4.3 copies current `scripts/` when the checkout predates one; `writ_scripts: current|checkout`. **Implementation did:** full overlay of this repo's install via `bash scripts/install.sh --platform claude --no-commit --force` with `cwd=<checkout>`; `writ: {source: "overlay", commit, dirty, checkout_manifest_version, manifest_diff_count}` replaces `writ_scripts`; `--writ-root` flag. **Why it matters:** all four parents run Writ `e1a3fd1` (2026-04-27, no scripts, no skills); the spec baselines the *repaired current* corpus. `dirty` (added at Gate 3) records whether the overlaid tree matched `commit`. **Resolution:** user-approved (decision 1).

## DEV-022 — Tests split; deps before the clock

**Severity:** Small · **Story:** 4 · **Found:** 2026-09-06, Gate 0. `tests.suite` (whole jest suite, `--ci --json --outputFile` outside the tree) and `tests.original` (story-commit test files restored via `git show <story_commit>:<path>` after the agent exits, `--runTestsByPath`); compile failure reads as failed, not error. `pnpm install --frozen-lockfile --prefer-offline` runs before `claude` → `deps{seconds, exit}`; `pnpm` added to preflight. `spec-lite.md` amended.

## DEV-023 — Process control and stop caps

**Severity:** Small · **Story:** 4 · **Found:** 2026-09-06, Gate 0. `Popen(start_new_session=True)` with stdout streamed to `transcript.jsonl` (never `capture_output` on a 90-minute stream); `killpg` SIGTERM → 15 s → SIGKILL, also on `KeyboardInterrupt` (Gate 3 S1); `--cap` 5400 s plus `--budget-usd` 75 → `--max-budget-usd` (`claude` 2.1.260 has no `--max-turns`); `status ∈ {complete, budget, error, timeout}` from `result.subtype`. `spec-lite.md` amended.

## DEV-024 — Record shape extras and ingest modes

**Severity:** Small · **Story:** 4 · **Found:** 2026-09-06, Gates 1–3. `gates.<g>.source ∈ {tool_result, assistant_text, null}`; `review_iterations` counted per source; `exit_criteria.reported` is a regex heuristic on the final text (`rederived` is authoritative); `tokens_main_thread` beside `tokens` (subagent spend is only in the `result` event); `run-meta.json` sidecar; `ingest` accepts a session `.jsonl` (`cost_usd: null`, `tokens == tokens_main_thread`); `runs_per_story` set on first run, `--force` to change; exit 3 for scrub failure / yuss HEAD moved. Story 5 must read `source` and treat `cost_usd: null` as "not from a `result` event". `spec-lite.md` amended.

## DEV-025 — No archive fallback, no lock, smoke deferred

**Severity:** Small · **Story:** 4 · **Found:** 2026-09-06, Gate 3 · **User decision** (deferral). Fetch refusal → `fetch_failed` error record (no `git archive` fallback); no `<json>.lock` (two concurrent `run`s would interleave); task 4.2 smoke run deferred because `ANTHROPIC_API_KEY` is unset in the implementing environment — `RESULT_*`/`INIT_*` field-name constants are pinned pending it. `spec-lite.md` amended.
