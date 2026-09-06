# Story 3: Story Selection — pipeline-baseline.py select Picks Four yuss.app Stories by Fixed Criteria

> **Status:** Complete
> **Priority:** High
> **Dependencies:** Story 1 (lands after Story 1's commit; no code dependency)

## User Story

**As a** Writ maintainer establishing a fixed, explainable task set to baseline the pipeline against
**I want to** run `python3 scripts/pipeline-baseline.py select --yuss ~/Projects/yuss --out .writ/eval/baselines/<date>-claude-fable-5-1.json` and get exactly four Completed yuss.app stories — one per surface class (API route, UI, data model, refactor) — each with a resolvable story commit, a recorded parent SHA, at least one touched test file, and tests that run without a live service, with the admitting criteria and the last ten rejections written into the JSON itself
**So that** Story 4's replay and every Stage 2 `compare` measure the same four tasks, and a reader can tell why those four stories were chosen from the JSON alone without reading the script

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given a fixture git repository shaped like yuss (`.writ/specs/archive/<folder>/user-stories/story-N-*.md` files with `> **Status:**` and `> **Commit:**` header lines, and commits that touch `app/api/**`, `components/**` or `app/**/page.tsx`, `prisma/**` or `lib/db/**`, and one no-new-files net-negative-lines refactor, each alongside a test file), when `select --yuss <fixture> --out <json>` runs, then it exits 0 and writes a JSON whose top level is exactly `schema: "pipeline-baseline-v1"`, `model` (default `claude-fable-5-1`, overridable by `--model`), `generated_at`, `yuss_head` (the fixture's `HEAD` SHA), a `criteria` block (status required, deny-list, test-file globs, per-class path patterns, refactor rule, migration-note pattern, tie-break rule, exclusion cap), a `selection` list of exactly four entries whose `surface_class` values are exactly `api_route`, `ui`, `data_model`, `refactor` once each and each entry carries `story_path` (relative to `<yuss>`), `spec_folder`, `story_id`, `story_commit`, `parent_sha`, `parent_is_merge`, `surface_class`, `eligible_classes`, `test_files`, and `criteria_values` (the observed values that admitted it: status, commit source, test-file count, deny-list hits = 0, migration note = false, new files, net lines), an `excluded` list, and an empty `runs` list. `[AC-3.1]`
- [x] Given fixture candidates that each fail exactly one admission rule — `Status:` not `Completed`; no `Commit:` line and `git log --grep "Story N" -- .writ/specs/archive/<folder>` returns nothing; a commit that touches no test file (`*.test.*`, `*.spec.*`, `__tests__/**`, `tests/**`); a touched test file whose imports match a deny-list entry (`prisma`, `stripe`, `@neondatabase`, `next-auth` server modules — read via `git show <commit>:<path>`, never a checkout); a `## Notes` section naming a database migration as a prerequisite — when `select` runs, then none of them appears in `selection`, each lands in `excluded` as `{story_path, reason, detail}` with `reason` one of `status_not_completed`, `commit_unresolved`, `no_test_files`, `live_service_import`, `migration_prerequisite`, `class_filled`, `detail` is at most 200 characters and contains a file path or a count but never a line of source or story text, `excluded` holds at most the ten most recent rejections, and a candidate whose only non-test touch is `prisma/schema.prisma` with a test that mocks the client (`jest.mock(` naming the deny-listed module) is admitted to `data_model`. `[AC-3.2]`
- [x] Given two or more admissible stories eligible for the same surface class, when `select` fills that class, then the story with the most recent commit date wins, a same-commit tie (two stories closed by one commit) breaks toward the higher story number then lexical `story_path`, the losers land in `excluded` with `reason: class_filled`, a story eligible for several classes is assigned to the class with the fewest other candidates (recorded in `eligible_classes`), and for every selected story `parent_sha` is the full 40-character `git rev-parse <commit>^1` result with `parent_is_merge: true` when the story commit has more than one parent. `[AC-3.3]`
- [x] Given a fixture in which at least one surface class has zero admissible stories, when `select` runs, then it exits non-zero, prints one line per short class in the form `select: no admissible story for class <name> (<k> candidates rejected: <reason>=<n>, …)`, does not create or overwrite the `--out` file, and the `excluded` reasons it prints account for every candidate that could have filled the class. `[AC-3.4]`
- [x] Given any invocation of `select` — success, short class, or invalid `--yuss` — when it exits, then `git status --porcelain` inside `<yuss>` is byte-identical to before the run and no path under `<yuss>` was created or modified, every subprocess the script spawned has `argv[0] == "git"` (asserted by the mocked-subprocess tests), the script imports only the Python 3.9 standard library, `uv run --python 3.9 pytest scripts/tests/test_pipeline_baseline.py` passes with the new code at ≥80% coverage, and `bash scripts/eval.sh` ends `Findings: 0`. `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write `scripts/tests/test_pipeline_baseline.py` before any script code: a fixture builder that `git init`s a temp repo, writes yuss-shaped story files (`Status`, `Commit`, `Dependencies`, `## Notes`), and commits per-class source + test file pairs (`app/api/foo/route.ts`, `components/Foo.tsx`, `prisma/schema.prisma`, a refactor with deletions only), plus a merge commit; tests for the happy-path JSON shape and key set, each of the six rejection reasons, the `jest.mock` schema-only relaxation, the ten-entry `excluded` cap and 200-character `detail` cap, most-recent and same-commit tie-breaks, multi-class assignment, merge first-parent recording, the short-class failure message and no-write guarantee, and a `subprocess.run` spy proving `argv[0] == "git"` for every call and that `<yuss>` is unchanged (`git status --porcelain` before/after). Pattern: `scripts/tests/test_archive_sweep.py`. `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`
- [x] 3.2 Create `scripts/pipeline-baseline.py` (module docstring, `argparse` subparsers in the style of `scripts/story-deps.py`) with `select --yuss PATH --out PATH [--model ID] [--deny-list a,b,…] [--excluded-cap N]` and stub `run`, `ingest`, `compare` subcommands that exit 2 with `not implemented until Story 4/5`; implement story discovery over `<yuss>/.writ/specs/archive/*/user-stories/story-*.md` and header parsing (`> **Status:**`, `> **Commit:**`, story number from the filename, `## Notes` body) into a `Candidate` dataclass; refuse a `--yuss` that is not a git repository or has no archive folder with a named error and exit 2. `[AC-3.1]`
- [x] 3.3 Implement commit resolution and change analysis through a single `git(*args)` helper that always runs `git -C <yuss>` read-only: `rev-parse --verify <commit>^{commit}` for a `Commit:` header, fallback `log --format=%H -1 --grep="Story <N>\b" -- .writ/specs/archive/<folder>`; `show --format=%H%n%P%n%ct --numstat <commit>` for changed paths with added/deleted counts; `diff-tree -r --diff-filter=A --name-only <commit>^ <commit>` for new files; `parent_sha = rev-parse <commit>^1` with `parent_is_merge = len(parents) > 1`; record `commit_source` (`header` or `log_grep`) in `criteria_values`. `[AC-3.3]`
- [x] 3.4 Implement the admission rules and surface-class derivation as pure functions over the change analysis: test-file detection by glob; deny-list scan of each touched test file's `import`/`require` lines read via `git show <commit>:<path>`; `jest.mock(` relaxation when `prisma/**` or `lib/db/**` schema files are the sole non-test touch; migration-prerequisite regex over `## Notes` only; class predicates for `api_route` (`app/api/**`), `ui` (`components/**`, `app/**/page.tsx`), `data_model` (`prisma/**`, `lib/db/**`), `refactor` (no new files and net negative lines); then assignment — order classes by ascending eligible-candidate count, fill each with the most recent eligible unassigned story (same-commit tie → higher story number → lexical path), and push every rejected or displaced candidate onto a bounded `excluded` deque with its reason code and a ≤200-character, source-free `detail`. `[AC-3.2, AC-3.3]`
- [x] 3.5 Implement the writer: assemble the `pipeline-baseline-v1` skeleton (`schema`, `model`, `generated_at`, `yuss_head`, `criteria` echoing every effective rule and the deny-list actually used, `selection`, `excluded`, `runs: []`), warn when the `--out` basename does not end in `-<model>.json` (Business Rule 4), write atomically via a sibling temp file and `os.replace`, create the `.writ/eval/baselines/` parent when missing, and on fewer than four filled classes print the per-class short line with the rejection tally and exit 1 without touching `--out`. `[AC-3.1, AC-3.2, AC-3.4]`
- [x] 3.6 Run the real selection: ensure `~/Projects/yuss` exists (clone `github.com/sellke/yuss` there if absent — a clone is outside `<yuss>` until it exists, so Business Rule 2 holds), run `select --yuss ~/Projects/yuss --out .writ/eval/baselines/2026-MM-DD-claude-fable-5-1.json`, read the four chosen stories and confirm each class assignment is defensible against the story text (`eligible_classes` and `criteria_values` explain it), apply the Notes fallback only if a class is short and record any criteria widening in the JSON `criteria` block and this story's What Was Built, confirm `git -C ~/Projects/yuss status --porcelain` is unchanged, and append the `{date} stage-1: …` line to `.writ/decision-log.md` (Business Rule 8). `[AC-3.1, AC-3.4, AC-3.5]`
- [x] 3.7 Verify: `uv run --python 3.9 pytest scripts/tests/test_pipeline_baseline.py` and the full suite pass with ≥80% coverage on the new file; `python3 -c "import ast,sys; …"` or `rg '^(import|from) ' scripts/pipeline-baseline.py` shows stdlib modules only; the committed JSON has exactly four `selection` entries with distinct `surface_class` values, 40-character `parent_sha` values, `runs: []`, no `detail` over 200 characters, and no source or story text; `bash scripts/eval.sh` ends `Findings: 0` (outside the sandbox — it does `git init` in a temp dir). `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

**yuss is not cloned at authoring time.** `ls ~/Projects/yuss` returned nothing on 2026-09-05. Tasks 3.1–3.5 need only the fixture repository the tests build; task 3.6 is the first step that needs the real clone and creates it at the sibling path if absent. The 2026-08-14 dogfooding research in `.writ/research/` puts the archive at ~113 spec folders and ~385 story files; older stories may lack a `Commit:` header, which is why the `git log --grep` fallback scoped to the story's spec folder exists. If the fallback also misses, the story is `commit_unresolved` — it is not guessed.

**The main risk is a class the heuristics admit zero stories for.** The surface-class patterns come from the spec and were written against yuss's layout as described in research, not measured against its archive. Two classes are fragile: `refactor` (a story commit with zero new files *and* net negative lines is rare when the generator also writes a `What Was Built` section into the story file itself — that edit counts toward the numstat) and `data_model` (most Prisma-touching commits also touch a route, and their tests import `@prisma/client`). Fallback, in order, each one recorded in the JSON `criteria` block so the file still explains itself: (1) exclude `.writ/**` paths from the new-files and net-lines computation for the refactor rule, since story-file edits are Writ bookkeeping, not product surface; (2) apply the schema-only relaxation to `lib/db/**` as well as `prisma/**`; (3) accept a `data_model` story whose tests import the client only through a module the same commit adds under `__mocks__/`. If a class is still short after (1)–(3), stop and report the per-class tally — do not widen further silently. Deciding whether a three-class baseline is acceptable is a scope decision for the user, recorded under Approved Scope Additions, not a script default.

**Class assignment is a small matching, not a first-match.** A commit that touches `app/api/**` and `components/**` is eligible for two classes. Filling classes in ascending order of candidate count and taking the most recent eligible story avoids the case where the only possible `refactor` story is consumed by `ui` first. Four classes and at most a few hundred candidates make this trivial; a full bipartite matcher is not warranted. `eligible_classes` is recorded so a reader sees why a story landed where it did.

**Tie-break is by commit date, then story number, then path.** The spec says "most recent story". Two stories closed by one commit share a date; the spec-lite edge case says both are eligible and the tie goes to the most recent, so the higher story number wins, with lexical path as the final deterministic tiebreak. Determinism matters more than the specific rule — the same archive must produce the same four stories on every machine.

**Business Rule 2 shapes every git call.** The script never checks anything out. File contents at a commit come from `git show <commit>:<path>`, changed paths from `--numstat` and `diff-tree`, and the parent from `rev-parse <commit>^1`. The test suite's `subprocess` spy is the enforcement: any call whose `argv[0]` is not `git`, or any `git` subcommand that writes (`checkout`, `worktree`, `stash`, `reset`), fails the test.

**Business Rule 3 and Story 5's 200-character rule share one guard.** `excluded[].detail` and every `criteria_values` field are built from paths, counts, and reason codes. The deny-list scanner reports *which* file and *which* module matched, never the import line. This is what lets Story 5's `check_pipeline_baseline` block on free text longer than 200 characters without special-casing this block.

**Integration.** Story 4 reads `selection[]` verbatim — `story_path`, `spec_folder`, `parent_sha`, `test_files` are its inputs; renaming a key here breaks Story 4. Story 5's schema check reads `schema`, `model`, `criteria`, and the four-entry `selection`. The `run`/`ingest`/`compare` stubs exist so the CLI surface Story 4 and 5 fill in is already named. `--model` defaults to `claude-fable-5-1` per Business Rule 9; the file name convention `<date>-<model-id>.json` is warned on, not enforced, because Story 5 owns validation.

## Approved Scope Additions

**2026-09-06 — `--live-test-scope file` (user-approved).** The spec's story-level live-service rule (spec.md → Detailed Requirements → Story 3: "the commit's test files import no module…") was dry-run read-only against `~/Projects/yuss` at `7c2d043` (368 candidates). It admits 5 stories — `ui` 4, `api_route` 1, `data_model` 0, `refactor` 0 — because every mature-era feature commit also touches a `tests/integration/**` file (DB-backed, excluded from `pnpm test` by yuss's `jest.config.js`), and the three Notes fallbacks are no-ops on this archive (`lib/db/` and `__mocks__/` do not exist; fallback 1 adds one refactor candidate that the per-file rule already admits). Its one `api_route` admit (`437e1ae`) is a false negative — integration-only tests that do not import a deny module directly. Approved widening: classify live-service per **test file** — a file is live if under `tests/integration/**` or `tests/e2e/**`, or has a deny-list import not covered by a `jest.mock(` of the same module in that file; live files are dropped from `test_files`; the story is admitted if ≥1 clean test file remains. The strict rule stays the script default; the widening is a flag echoed as `criteria.live_test_scope: "file"` so the baseline explains itself. Result: 11 admissible, all four classes filled. Caveat for Stage 2 readers: three of the four picks come from one spec folder (`2026-07-24-per-event-fee-revenue-model`) closed within one week; the baseline is a two-spec, one-week sample of yuss.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Live-service test → excluded at `select` with the reason in `excluded[]`, never discovered mid-run (spec.md → ## 🎯 Experience Design → Error experience), Empty input → fewer than four admissible stories fails naming the short class (spec-lite.md → ## For Testing Agents → Shadow Paths to Verify)]
- **Shadow paths:** [Happy path step (1) — `select` writes the four stories and their parent SHAs (spec.md → ## 🎯 Experience Design → Happy path), Edge cases — merge parent → first parent recorded; two stories in one commit → both eligible, tie → most recent (spec-lite.md → ## For Testing Agents → Edge Cases)]
- **Business rules:** [2 (yuss is read-only — reads only, no writes inside `<yuss>`), 3 (JSON carries IDs, SHAs, metrics, criteria — never source or story text), 4 (one model per file — `model` header, `<date>-<model-id>.json` name), 8 (decision-log line on the closing commit), 9 (Fable 5.1 default model ID)]
- **Experience:** [State catalog — `select` written (spec.md → ## 🎯 Experience Design → State catalog), Recommendation — selection criteria live in the JSON, not only the script (spec.md → ## Specification Contract → 💡 Recommendations), Technical concern — tests needing a database or Stripe keys are excluded at selection (spec.md → ## Specification Contract → ⚠️ Technical Concerns), Detailed rules — spec.md → ## Detailed Requirements → ### Story 3 — Story selection]

Reference: `.writ/docs/context-hint-format.md`.

## What Was Built

**Implementation Date:** 2026-09-06

### Files Created

- **`scripts/pipeline-baseline.py`** (706 lines, stdlib only, Python 3.9) — `select` subcommand plus `run`/`ingest`/`compare` stubs that exit 2 (`not implemented until Story 4/5`). Invocation: `select --yuss PATH --out PATH [--model claude-fable-5-1] [--deny-list a,b] [--excluded-cap 10] [--live-test-scope story|file] [--force]`. Exit codes: 0 written · 1 short class (`--out` untouched; one `select: no admissible story for class <c> (<k> candidates rejected: reason=n, …)` line per short class) · 2 usage or refusal (`--yuss` not a git repo or no archive folder, `--out` inside `<yuss>`, `--out` exists without `--force`, zero candidates).
  - `Git.run` refuses any subcommand outside `READ_ONLY_GIT = {rev-parse, log, show, diff-tree}` before a process is spawned — Business Rule 2 enforced in code, not only in tests.
  - Commit resolution: `Commit:` header first (first 7–40-hex token), then `git log -1 -E -i --grep 'stor(y|ies)[ -]?N([^0-9]|$)' -- .writ/specs/<folder> .writ/specs/archive/<folder>`. Never `\b` — Apple Git's ERE silently matches nothing on it. `([^0-9]|$)` keeps "Story 30" from resolving "Story 3".
  - Change analysis: `show -m --first-parent --no-renames --numstat` and `diff-tree -r --no-renames --diff-filter=…` so a rename counts as delete+add (the refactor rule depends on it). Status normalization: strip non-ASCII symbols, parentheticals, and whitespace, then `^complete(d)?$` case-insensitive.
  - JSON written atomically: sibling `mkstemp`, `chmod 0o666 & ~umask` (mkstemp creates 0600, which a committed baseline should not inherit), `os.replace`.
  - Top-level keys (`SCHEMA_KEYS`): `schema`, `model`, `generated_at`, `yuss_head`, `runs_per_story` (null until Story 4), `criteria`, `selection`, `excluded`, `rejection_tally`, `runs`.
  - Selection entry keys (`SELECTION_KEYS`): `story_path`, `spec_folder`, `story_id`, `story_commit`, `parent_sha`, `parent_is_merge`, `surface_class`, `eligible_classes`, `test_files`, `criteria_values{status, commit_source, commit_timestamp, test_file_count, deny_list_hits, deny_list_mocked, live_test_files_dropped, migration_note, new_files, net_lines}`.
  - Reason codes (`REASONS`): `status_not_completed`, `commit_unresolved`, `git_error`, `no_test_files`, `live_service_import`, `migration_prerequisite`, `no_surface_class`, `class_filled`.
  - Constants Story 5's validator imports: `SCHEMA`, `DEFAULT_MODEL`, `SCHEMA_KEYS`, `SELECTION_KEYS`, `SURFACE_CLASSES`, `REASONS`, `DEFAULT_DENY_LIST`, `DEFAULT_EXCLUDED_CAP`, `DETAIL_MAX_CHARS` (200), `READ_ONLY_GIT`. The filename is hyphenated, so import by path with `importlib.util.spec_from_file_location`, as the tests do.
- **`scripts/tests/test_pipeline_baseline.py`** (1157 lines, 45 tests) — `Repo` fixture builder (`git init` temp repo, yuss-shaped story files, per-class source + test commits, merge commit) and `four_class_repo`, plus an `invoke` `subprocess.run` spy. The spy asserts `argv[0] == "git"`, `-C <yuss>`, a literal read-only subcommand, and byte-identical `git status --porcelain` + `HEAD` on every invocation including refusals. `Repo`/`four_class_repo`/`invoke` are reusable by Story 4.
- **`.writ/eval/baselines/2026-09-06-claude-fable-5-1.json`** — the committed skeleton. `yuss_head` `7c2d0430…` (`7c2d043`), `criteria.live_test_scope: "file"`, `runs: []`, `runs_per_story: null`. Four picks:
  - `api_route` — `2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow` @ `79d79ae` (eligible: `api_route`, `ui`; 2 test files)
  - `ui` — `2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link` @ `8d97930` (eligible: `api_route`, `ui`; 6 test files)
  - `data_model` — `2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption` @ `c9350fc` (eligible: `api_route`, `ui`, `data_model`; 2 test files)
  - `refactor` — `2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard` @ `12eea11` (eligible: `ui`, `refactor`; 3 test files)
  - No pick is a merge commit. `excluded[]` holds 10; `rejection_tally` accounts for all 364 rejections: `commit_unresolved` 299, `status_not_completed` 30, `no_test_files` 17, `live_service_import` 11, `class_filled` 7.

### Files Modified

- **`.writ/decision-log.md`** — one `2026-09-06 stage-1:` line (Business Rule 8), written by the orchestrator: the four picks, the `--live-test-scope file` widening and why, the two-spec/one-week caveat.
- **`spec-lite.md`** — "Story 3 amendments" line (DEV-008–013).
- **`drift-log.md`** — DEV-008 through DEV-013.

### Implementation Decisions

1. **Module constants are the schema contract, not tech-spec §2** — Stories 4 and 5 import `SCHEMA_KEYS`/`SELECTION_KEYS`/`REASONS` rather than transcribe field names from prose (DEV-008).
2. **Read-only git enforced twice** — `Git.run` refuses non-allowlisted subcommands at the call site; the test spy independently checks every spawned argv. Either alone would let a future `checkout` slip through under a mock.
3. **Strict story-level live-service rule stays the default** — the user-approved per-file widening is a flag echoed as `criteria.live_test_scope`, so the committed baseline names the rule it was produced under and a strict re-run is one flag away.
4. **`--out` refused whenever it exists** — stricter than tech-spec §9, to protect Story 4's run records from an accidental re-`select` (DEV-013).
5. **No "last commit touching the story file" fallback for `commit_unresolved`** — on the real archive that heuristic resolves to Writ bookkeeping commits (status flips, archive moves), not the closing product commit. 299 stories stay unresolved rather than mis-attributed.

### Test Results

**Verification:** Automated.

- ✅ `uv run --python 3.9 pytest scripts/tests/test_pipeline_baseline.py` — 45 passed on 3.9.6; 45 passed on 3.12.13
- ✅ Coverage on `scripts/pipeline-baseline.py`: 99% — only the `if __name__ == "__main__"` guard uncovered (AC-3.5 floor: 80%)
- ✅ `bash scripts/eval.sh` (outside the sandbox) — `Findings: 0`, 23/23 scenarios
- ✅ `git -C ~/Projects/yuss status --porcelain` empty and `HEAD` = `7c2d043` before and after every real run (dry runs, the strict-scope run, and the committed `--live-test-scope file` run)
- ✅ Mutation checks each caught by a named test: grep boundary (`Story 30` vs `Story 3`), `--no-renames` on numstat/diff-tree, tie-break direction (commit date desc → story number desc → path asc), `chmod` after `mkstemp`
- ✅ `rg '^(import|from) ' scripts/pipeline-baseline.py` — stdlib only
- ✅ Committed JSON: four `selection` entries with distinct `surface_class`, 40-character `parent_sha`, `runs: []`, no `detail` over 200 characters, no source or story text

**Coverage:** 99%

### Review Outcome

**Result:** PASS

- **Iteration count:** not reported to Gate 5; format fallback 1 iteration
- **Drift:** Medium ×1 (DEV-008), Small ×5 (DEV-009–013) — `drift-log.md`, `spec-lite.md` amended
- **Security:** Clean — read-only git allowlist enforced in code; JSON carries paths, SHAs, counts, reason codes only
- **Boundary compliance:** all changes within Owned; `scripts/eval.sh`, `system-instructions.md`, `commands/_preamble.md` untouched

### Deviations from Spec

Full entries in [`drift-log.md`](../drift-log.md).

- **[DEV-008] technical-spec §2 field/class/reason names superseded** — Severity: Medium. Story-3 AC-3.1 names are implemented (`generated_at`, `yuss_head`, `parent_is_merge`, `criteria_values`, `api_route|ui|data_model|refactor`, the eight `REASONS`); `technical-spec.md` §2 left as authored; the module constants are the contract.
- **[DEV-009] Short class exits 1, not 2** — Severity: Small. Task 3.5 followed; 2 is reserved for usage and refusal.
- **[DEV-010] `runs_per_story` and `rejection_tally` added at top level** — Severity: Small. Story 4 fills the first; the second gives uncapped counts behind the capped `excluded[]`.
- **[DEV-011] Reason codes add `git_error` and `no_surface_class`** — Severity: Small. A Completed, resolved, tested story whose commit touches no class path and is not a refactor had no AC-3.2 reason.
- **[DEV-012] Test-file rule narrowed** — Severity: Small. Source extension required (`tests/integration/README.md` matched `stripe` in prose), deleted files excluded, test paths do not set class; each echoed in `criteria`.
- **[DEV-013] `--live-test-scope`, `--force`, `--out` refusal** — Severity: Small. Widening carried as a flag, default strict; `--out` refused if it exists.

### Follow-ups and observations

- **Strict `story` scope has a false-negative hole.** Its import-only heuristic admits `tests/integration/*.integration.test.ts` files that do not import a deny module directly (yuss `437e1ae`). `criteria.deny_list_scan` documents that transitive imports are not followed; the `file` scope's directory rule closes it for the committed baseline, the strict default does not.
- **Short-class tally is run-wide, not per-class.** The AC-3.4 line prints the rejection tally across all candidates, not only the candidates that could have filled that class. Adequate for a reader; a per-class breakdown would need eligibility computed for rejected candidates too.
- **`schema_only` relaxation is defeated when the closing commit also edits `.writ/**`.** The story-file edit counts as a non-test, non-schema touch. Notes fallback 1 (exclude `.writ/**` from the computation) is not implemented as a flag; on this archive it added one refactor candidate the per-file rule already admits.
- **299 `commit_unresolved` are structural, not a bug.** They are the 2025-10 / 2026-01 / 2026-02 eras with no `Commit:` header and no story-numbered commit message — no story↔commit linkage exists to resolve. See decision 5 for the rejected fallback.
- **The baseline is a two-spec, one-week sample.** Three of four picks are from `2026-07-24-per-event-fee-revenue-model`, closed within one week; the fourth is from `2026-07-23-quick-split-single-transaction`. Stage 2 readers should not generalize from it to yuss's full history.
