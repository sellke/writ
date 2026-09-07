# Story 4: Replay Runner — Isolated Checkout, Headless /implement-story, Metrics Per Run

> **Status:** Completed ✅ (2026-09-06)
> **Commit:** eefffa1c4b21ab0777b8031a7d8c8d3492a4b7a2
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** Writ maintainer who needs eight reproducible pipeline runs without hand-driving eight agent sessions
**I want to** run `scripts/pipeline-baseline.py run --model <id> --runs N` and have it build an isolated checkout per (story, run), execute `/implement-story` headless inside it, and append one metrics record per run
**So that** every later Phase 11 instruction cut is measured against a number the same command can regenerate, not against a maintainer's recollection of eight sessions

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given `ANTHROPIC_API_KEY` is absent from `os.environ` or no `claude` binary is on `PATH`, when `pipeline-baseline.py run` is invoked, then it exits non-zero naming the missing env var or the `claude` install path, and no `$TMPDIR/writ-baseline-*` directory, no baseline-file write, and no `git` or `claude` subprocess occurs `[AC-4.1]`
- [x] Given a selected story with parent SHA `<sha>`, when the runner builds the checkout for run `n`, then it creates `$TMPDIR/writ-baseline-<story>-<n>/` via a fresh `git init` + `git fetch --depth 1 <yuss> <sha>` + checkout (or `git archive <sha>` into a new `git init`) — never `git worktree` — asserts `git rev-list --all | wc -l` equals the truncated depth before any `claude` invocation, records the assertion (`isolation: {reachable_commits, expected, asserted: true}`) in the run record, and performs no write inside `<yuss>` `[AC-4.2]`
- [x] Given a built checkout, when the runner stages the run, then the story file plus the spec folder's `spec.md`, `spec-lite.md`, and sub-specs are copied into the checkout's `.writ/specs/<folder>/`, current `scripts/` is copied in only when the checkout predates a needed script (recording `writ_scripts: current`, otherwise `writ_scripts: checkout`), `claude -p "/implement-story <story-id>" --model <id> --output-format stream-json` is invoked with `cwd` set to the checkout under a wall-clock cap with stdout captured to `<tmpdir>/transcript.jsonl`, and a cap breach records `status: timeout` and continues to the next run `[AC-4.3]`
- [x] Given a finished (or timed-out) headless run, when the runner post-processes it, then it runs the parent's `package.json` test command against the produced tree, runs `exit-criteria.py check`, `test-integrity.py coverage`, and `build-smoke.py check` against the checkout, parses the transcript for summed `input_tokens` / `output_tokens` / `cache_read_input_tokens`, counts of AskQuestion and `STATUS: BLOCKED` occurrences, review-loop iterations, and the `ARCH_CHECK:` / `REVIEW_RESULT:` / `TEST_RESULT:` / `DOCS_UPDATED:` verdict strings, and appends one run record where each gate carries `reported` beside `rederived` (`rederived: null` for Gates 0, 1, 3, 5), with no field exceeding 200 characters and no transcript text, source text, or key material anywhere in the JSON `[AC-4.4]`
- [x] Given a multi-run invocation, when each run completes, then its record is flushed to the baseline file before the next run starts, a re-invocation skips every (story, n) pair already present, the temp dir is deleted unless `--keep` is passed, one stdout line per run prints story id, exit-criteria verdict, tests passed/total, tokens in/out/cache, wall-clock, and interrupts, and `ingest --checkout <dir> --transcript <file>` produces a record with the identical schema from an existing checkout and transcript `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write `scripts/tests/test_pipeline_baseline_run.py` with `subprocess.run` mocked: preflight refusal with zero side effects (both missing-key and missing-binary branches), checkout-builder command sequence and `rev-list` assertion (including a mismatched count that aborts), input staging and `writ_scripts` detection, `claude` argv and timeout → `status: timeout`, stream-json transcript fixture parsing (usage sums, AskQuestion / `STATUS: BLOCKED` counts, review iterations, four verdict strings), record assembly with `reported` / `rederived` pairs and the 200-char / no-secret guard, flush-then-resume skipping completed pairs, `--keep` vs. delete, and `ingest` producing the same record shape `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [~] 4.2 (deferred — see Approved Scope Additions, decision 3; smoke-run command under *Smoke-run checklist (pending)* in What Was Built) Smoke run before further implementation: build one isolated checkout by hand-invoking the Task 4.3 builder (or the equivalent shell sequence) for the first selected story, run `claude -p "/implement-story <story-id>" --model claude-fable-5-1 --output-format stream-json` with `cwd` in the checkout and a 30-minute cap, and confirm the transcript shows the slash command resolving from the checkout's `.claude/commands/` and Gate 0 output appearing; if `-p` does not resolve the slash command, record the deviation in What Was Built and make `ingest` (Task 4.6) the primary path for Story 5, with `run` invoking a manual-session prompt instead `[AC-4.3]`
- [x] 4.3 Implement `preflight()` (env var + `shutil.which("claude")`, run before any filesystem or subprocess side effect) and `build_checkout(yuss, sha, tmpdir)` in `scripts/pipeline-baseline.py`: `git init`, `git fetch --depth 1 <yuss> <sha>`, `git checkout FETCH_HEAD`, then `git rev-list --all --count` asserted against the expected depth, returning the `isolation` block; every `git` call uses `<yuss>` only as a fetch source `[AC-4.1, AC-4.2]`
- [x] 4.4 Implement `stage_inputs()` (copy story file, `spec.md`, `spec-lite.md`, `sub-specs/` into `.writ/specs/<folder>/`; detect missing `scripts/exit-criteria.py` / `test-integrity.py` / `build-smoke.py` in the checkout and copy current `scripts/`, setting `writ_scripts`) and `invoke_headless()` (`subprocess.run` with `cwd=checkout`, `timeout=--cap`, stdout to `transcript.jsonl`, `TimeoutExpired` → `status: timeout`) `[AC-4.3]`
- [x] 4.5 Implement `postprocess()`: read the parent `package.json` test script and run it in the checkout; shell out to `exit-criteria.py check`, `test-integrity.py coverage --project <checkout>`, `build-smoke.py check --project <checkout>` and parse their JSON; implement `parse_transcript(path)` over stream-json lines (sum `usage` fields, count AskQuestion and `STATUS: BLOCKED`, count review iterations, extract the last value of each verdict string); assemble the run record with `gates.<name>.{reported, rederived}` (`rederived: null` where no script exists) and a `scrub()` that rejects any string field over 200 characters or matching `sk-ant-` `[AC-4.4]`
- [x] 4.6 Implement the `run` loop (iterate `selection.stories × range(runs)`, skip pairs already in `runs[]`, `json.dump` after every record, `shutil.rmtree` unless `--keep`, one progress line per run) and the `ingest --checkout <dir> --transcript <file>` subcommand that calls the same `postprocess()` and appends to the same file; register both in the argparse tree beside `select` `[AC-4.5]`
- [x] 4.7 Verify: run `uv run pytest scripts/tests/test_pipeline_baseline_run.py` green with ≥80% coverage on the new code and 100% on the isolation-assertion and scrub paths; walk each acceptance criterion against the smoke-run record; run `bash scripts/eval.sh` outside the sandbox to `Findings: 0`; append the `{date} stage-1:` line to `.writ/decision-log.md` `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

**Isolation rationale.** A `git worktree` of `~/Projects/yuss` shares the object store and refs, so `git log --all`, reflogs, and `git branch -a` all expose the commit that completed the story — the model could read its own answer. A fresh `git init` plus `git fetch --depth 1 <yuss> <sha>` leaves exactly one reachable commit; the `rev-list --all --count` assertion is the machine-checkable proof and is stored in the record (Business Rule 1). Using `<yuss>` only as a fetch source keeps Business Rule 2 (yuss read-only) — the runner never runs a mutating `git` command with `cwd` inside yuss. If the parent SHA is a merge commit, Story 3 has already recorded the first parent; the runner uses the SHA as given.

**Headless invocation risk and fallback.** Whether `claude -p` resolves a project slash command from the checkout's `.claude/commands/` is the spec's named unverified concern. That is why Task 4.2 runs before Tasks 4.3–4.6 are complete: one real story, one run, `--keep` semantics, 30-minute cap. Outcomes: (a) slash command resolves — `run` proceeds as specified; (b) it does not — `ingest` becomes the primary Story 5 path (maintainer drives the session, then `ingest --checkout --transcript` computes the same record), and What Was Built records the deviation, the failing transcript shape, and the prompt variant tried. The record schema is identical either way so Story 5's `check_pipeline_baseline` and `compare` are unaffected.

**Cost.** Each headless run is a full five-gate pipeline at Fable 5.1 default-high effort; the smoke run alone is one such run. Keep the smoke run to one story and one run, and prefer the story Story 3 ranked as smallest by changed lines. Token fields in the record are what Story 5 sums for the dollar estimate — parse `cache_read_input_tokens` separately so cache hits are not mistaken for paid input.

**Transcript parsing.** stream-json emits one JSON object per line; `usage` blocks appear on assistant/result messages and must be summed, not read once. Verdict strings (`ARCH_CHECK:`, `REVIEW_RESULT:`, `TEST_RESULT:`, `DOCS_UPDATED:`) may appear more than once across review iterations — take the last occurrence as the reported verdict and count `REVIEW_RESULT: FAIL` occurrences as review iterations. AskQuestion in headless mode surfaces as a tool-use block; count it as an interrupt alongside `STATUS: BLOCKED`.

**Re-derivation CLIs.** `exit-criteria.py check --command implement-spec --spec <dir> --repo <checkout>` (exit 0 met / 1 unmet / 2 impossible); `test-integrity.py coverage --project <checkout>` reads a coverage report the test run must have produced — if the parent's test command does not emit one, store `rederived: "unverifiable"` rather than fabricating; `build-smoke.py check --project <checkout> --timeout 300` classifies environment failure separately from source failure, so a missing database yields `unverifiable`, not FAIL.

**Integration.** Extends the `scripts/pipeline-baseline.py` file and `pipeline-baseline-v1` skeleton Story 3 creates; reads Story 3's `selection.stories[]` (path, spec folder, parent SHA, test files) and fills `runs[]`. Story 5 consumes `runs[]` unchanged. Secrets come only from `os.environ` (Business Rule 3); the scrub in Task 4.5 is the enforcement point.

## Approved Scope Additions

**2026-09-06 — three decisions taken at Gate 0 (user-approved).** Gate 0 verified against the real parents and the installed CLI (`claude` 2.1.260):

1. **Which Writ runs in the checkout: the current repo's, overlaid.** All four `parent_sha`s carry a copied Writ install at `e1a3fd1` (2026-04-27; 905-line `implement-story.md`, no `scripts/*.py`, no skills). The spec's purpose is to baseline the *repaired current* corpus, so the runner overlays this repo's install via `bash scripts/install.sh --platform claude --no-commit --force` with `cwd=<checkout>` (`--no-commit` keeps the isolation assertion `rev-list --all --count == 1` true before the run starts) and records `writ: {source: "overlay", commit, checkout_manifest_version, manifest_diff_count}` in place of the story's `writ_scripts` field. Alternative rejected: running the historical `e1a3fd1` install as-is — Stage 2's `compare` would then measure April-Writ against cut-current-Writ, not the cut.
2. **Permission mode: bypass, inside the isolated checkout.** In `-p` mode anything that would prompt is denied; `--permission-mode acceptEdits` (technical-spec §4) does not cover Bash, so `pnpm test`, `git commit`, and `python3 scripts/*.py` would all be denied and the record would measure denial handling. Approved: `--dangerously-skip-permissions --permission-prompts none --setting-sources project --strict-mcp-config --no-session-persistence` (user-level hooks, MCP servers, and plugins do not run inside the measured session; no session file lands in `~/.claude/projects/`). Compensating controls: the checkout has no remotes, `.git/FETCH_HEAD` (the only reference to yuss's path) is removed after checkout, and `git -C <yuss> rev-parse HEAD` is recorded before and after every run (`yuss_head_unchanged`). Alternative rejected: an explicit `--allowedTools` allow-list — brittle, and every denial becomes measurement noise.
3. **Task 4.2 smoke run deferred.** `ANTHROPIC_API_KEY` is unset in the implementing environment. The runner is built and tested against mocked `claude`/`pnpm`/`git` fixtures; the one live smoke run is left as a documented one-line command for a maintainer, with a 30-minute cap and `--max-budget-usd`. Task 4.2 is marked pending until it runs. What 4.2 must confirm: slash command resolves with the path argument; the permission flags let Bash run; `result` event field names for `usage`/`total_cost_usd`/`subtype`; gate verdicts arrive as `Task` tool_results; `pnpm install --frozen-lockfile` wall time; `--model claude-fable-5-1` is accepted (record `model_resolved`); `apiKeySource`.

Also corrected at Gate 0 without a scope decision (recorded as drift): inputs are staged from the **parent** commit, never yuss HEAD — the HEAD/archive copy of the story carries `Status: Completed`, `> **Commit:**`, and `## What Was Built`, i.e. the answer; `scripts/exit-criteria.py` has no `implement-story` mode, so completion is re-derived from `implement-story.md`'s own success predicates; `claude` 2.1.260 has no `--max-turns` — stop caps are `--cap` seconds plus `--budget-usd` (→ `--max-budget-usd`).

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [No `ANTHROPIC_API_KEY` → `run` refuses to start; `claude` binary missing → stop before any checkout, name install path; headless run timeout → `status: timeout`, continue] — spec.md → ## 🎯 Experience Design → Error experience; spec-lite.md → ## For Testing Agents → Shadow Paths → Nil input, Upstream error
- **Shadow paths:** [Happy path step (2) `run --model claude-fable-5-1 --runs 2` builds eight isolated checkouts and appends eight records; State catalog `run` in progress (partial records flushed per run) / `run` complete] — spec.md → ## 🎯 Experience Design → Happy path, State catalog
- **Business rules:** [1 Isolation (assert `rev-list --all` count, record it), 2 yuss read-only (temp dirs only, fetch source only), 3 Secrets stay in the environment (no transcript text or keys in JSON), 5 Verdict beside re-derivation (`rederived: null` where no script), 9 Fable 5.1 only (`--model` accepts any ID; only Fable file committed)] — spec.md → ## 📋 Business Rules
- **Experience:** [Feedback model (one stdout line per story per run: story id, exit-criteria verdict, tests passed/total, tokens in/out/cache, wall-clock, interrupts); JSON is the durable record] — spec.md → ## 🎯 Experience Design → Feedback model
- **Contract:** spec.md → ## Specification Contract → Hardest Constraint (isolation, never a worktree); → ⚠️ Technical Concerns (headless invocation unverified, smoke-run-first, ingest fallback; eight runs dominate cost)
- **Detailed requirements:** spec.md → ## Detailed Requirements → ### Story 4 — Replay runner; → ### Story 3 — Story selection (`selection` block fields this story reads); → ## Implementation Approach (Python 3.9 stdlib, shells out to `git` and `claude`, never imports yuss code)
- **Edge cases:** [Parent SHA is a merge commit → first parent recorded by Story 3; checkout predates a needed script → copy current `scripts/`, record `writ_scripts: current`] — spec-lite.md → ## For Testing Agents → Edge Cases
- **Pipeline strings to parse:** `commands/implement-story.md` → Gates 0–5 verdict lines (`ARCH_CHECK:`, `REVIEW_RESULT:`, `TEST_RESULT:`, `DOCS_UPDATED:`), `STATUS: BLOCKED` handling, review loop `max_iterations: 3`
- **Re-derivation scripts:** `scripts/exit-criteria.py check`, `scripts/test-integrity.py coverage`, `scripts/build-smoke.py check` — read each module docstring for exit codes and `unverifiable` semantics

## What Was Built

**Implementation Date:** 2026-09-06

### Files Created

- **`scripts/tests/test_pipeline_baseline_run.py`** (1744 lines, 74 tests) — `FakeProc` / `Dispatcher` fixtures that mock `subprocess.run` and `subprocess.Popen` for `git`, `claude`, `pnpm`, `bash install.sh`, and `python3 <gate script>` by argv prefix; test classes `ContractTest`, `PreflightTest`, `ParseTranscriptTest`, `ScrubTest`, `BuildCheckoutTest`, `RunTest`, `IngestTest`, `CliTest`. No test spawns `claude` or writes inside `<yuss>`; the Story 3 `Repo` fixture is reused for the yuss side.

### Files Modified

- **`scripts/pipeline-baseline.py`** (706 → 1770 lines; stdlib only, Python 3.9) — `run` and `ingest` implemented from the `# run / ingest — record contract` block (line 689) onward; `compare` stays a stub. Module docstring rewritten to describe all three subcommands and the exit codes.
- **`scripts/tests/test_pipeline_baseline.py`** — `test_stubs_exit_2` narrowed to `compare` (the `run`/`ingest` stubs no longer exist).
- **`drift-log.md`** — DEV-018 through DEV-025.
- **`spec-lite.md`** — "Story 4 amendments" line (DEV-018–025).
- **`user-stories/story-4-replay-runner.md`** — Approved Scope Additions (three Gate 0 decisions + the parent-staging correction); this record.
- **`.writ/decision-log.md`** — the task 4.7 `2026-09-06 stage-1:` line is written by the orchestrator at commit (Business Rule 8), as for Story 3. Not written by Gate 5.

### CLI contract

```
run     --baseline PATH --yuss PATH [--model ID] [--runs N=2] [--story ID|stem]
        [--cap S=5400] [--budget-usd N=75] [--keep] [--force] [--tmp-root DIR=$TMPDIR]
        [--writ-root DIR=<this repo>]
ingest  --baseline PATH --yuss PATH --checkout DIR --transcript FILE
        [--story-id ID --run N] [--force] [--tmp-root DIR] [--writ-root DIR]
```

- **Exit codes:** `0` written · `2` usage or refusal — `run` preflight (`ANTHROPIC_API_KEY` unset, `claude` or `pnpm` not on `PATH`; checked before any filesystem or subprocess side effect), `--baseline` missing / not `pipeline-baseline-v1` / empty selection, `--yuss` not a git repo, `--model` ≠ the file's `model` (Business Rule 4), `--runs < 1`, `runs_per_story` already set to a different value without `--force`, `--story` matching nothing, `ingest` with no `run-meta.json` sidecar and no `--story-id`/`--run`, `ingest` of an already-recorded pair without `--force` · `3` a record failed `scrub()` (nothing written) or yuss `HEAD` moved during a run (the record *is* flushed first, then the process stops).
- **`run` loop:** `selection × range(1, runs+1)`; pairs already in `runs[]` print `skip (already recorded)`; each record is scrubbed, appended, and `write_json`-flushed before the next run starts. `runs_per_story` is set on the first `run` and changed only with `--force`. Run dir `<tmp-root>/writ-baseline-<story stem>-<n>/` holds `checkout/`, `transcript.jsonl`, `stderr.log`, `install.log`, `pnpm-install.log`, `run-meta.json`; removed after a complete record unless `--keep`; on any exception it is kept and its path printed to stderr.
- **`ingest`:** same `postprocess()` as `run`, so the record shape is identical. Reads `run-meta.json` beside or inside `--checkout` when present; without it, `--story-id` and `--run` are required and the record carries `reason: "ingested without sidecar"`, `isolation.asserted: false`. `--transcript` may be a `-p` stream-json file or a `~/.claude/projects/*.jsonl` session file (see `cost_usd` below). `--force` replaces the recorded pair.
- **Progress line** (one per run, stdout): `run: <story_id> run <n>: <status>[ (<reason>)] exit=<met|unmet> tests=<passed>/<total> tokens=<in>/<out>/<cache_read> wall=<s>s interrupts=<n>`.
- **`claude` argv** (recorded verbatim in `invocation.argv`): `claude -p "/implement-story <story rel path>" --output-format stream-json --verbose --model <id> --max-budget-usd <n> --dangerously-skip-permissions --permission-prompts none --setting-sources project --strict-mcp-config --no-session-persistence`, `cwd=<checkout>`, `CLAUDECODE`/`CLAUDE_CODE_ENTRYPOINT` stripped from the child env, `Popen(start_new_session=True)`; on the cap or Ctrl-C the process group gets SIGTERM, 15 s, SIGKILL.

### Record contract (what Story 5 imports)

Import by path (`importlib.util.spec_from_file_location`) as the tests do. Every constant below is asserted against the assembled record (`assert tuple(rec) == RUN_KEYS` etc.), so the constants *are* the schema.

- **`RUN_KEYS`** (key order of one `runs[]` entry): `story_id`, `run`, `status`, `reason`, `started_at`, `isolation`, `writ`, `inputs`, `deps`, `invocation`, `wall_clock_s`, `num_turns`, `tokens`, `tokens_main_thread`, `cost_usd`, `interrupts`, `review_iterations`, `tests`, `gates`, `rederivation`, `exit_criteria`, `yuss_head_unchanged`.
- **`RUN_STATUSES`**: `complete`, `budget`, `error`, `timeout`. `status` comes from `RESULT_SUBTYPE_STATUS[result.subtype]` (unknown subtype → `error`), overridden to `timeout` when the cap fired; a run that never reached the model is `error`.
- **`reason`** (string or null) — vocabulary, all from code:
  - pre-model failures (`RunError`): `fetch_failed`, `isolation_failed`, `inputs_missing`, `answer_leak`, `overlay_failed`, `git_<verb>_failed` (any non-zero `git -C <checkout> <verb>` other than the fetch, e.g. `git_checkout_failed`, `git_rev-list_failed`);
  - transcript-derived: `no_result_event` (a `-p` stream that never emitted a `result` event); otherwise the `result.subtype` string when `status != complete` — the pinned keys are `error_max_budget_usd`, `error_max_budget` → `budget`, `error_during_execution`, `error_max_turns` → `error`; an empty subtype reads `unknown_subtype`;
  - `ingest` without a sidecar: `ingested without sidecar` (kept only when the transcript itself has no stop reason);
  - `timeout` records carry `reason: null` unless a pre-model reason was set.
- **`isolation`** (`ISOLATION_KEYS`): `reachable_commits` (int|null), `expected` (1), `asserted` (bool — `rev-list --all --count == 1` *and* `git remote -v` empty), `answer_scrub_asserted` (bool).
- **`writ`** (`WRIT_KEYS`) or null: `source` (`"overlay"`), `commit` (HEAD of `--writ-root`), `dirty` (bool — `git status --porcelain` of `--writ-root` non-empty; `install.sh` copies the working tree, so `commit` alone under-describes a dirty repo), `checkout_manifest_version` (the parent's `.claude/.writ-manifest` version or null), `manifest_diff_count` (manifest entries whose digest changed).
- **`inputs`**: one of `INPUT_SOURCES` — `parent` (spec folder present in the checkout tree at `parent_sha`) or `parent_show` (at least one file materialized via `git -C <yuss> show <parent_sha>:<path>`) — or null.
- **`deps`**: `{seconds, exit}` from `pnpm install --frozen-lockfile --prefer-offline`; `exit` is the return code or `"timeout"` (900 s).
- **`invocation`** (`INVOCATION_KEYS`): `argv`, `model`, `model_resolved`, `claude_version`, `permission_mode` (`"bypass"`), `api_key_source`. The last three come from the `system/init` event via `INIT_FIELDS`; null when absent.
- **`tokens`** and **`tokens_main_thread`** (`TOKEN_KEYS`): `input`, `output`, `cache_read`, `cache_creation`. `tokens` is the `result` event's `usage` (includes subagent spend); `tokens_main_thread` is the sum over main-thread `assistant` messages (events with `parent_tool_use_id` are skipped). Expect `tokens_main_thread < tokens` on a real run.
- **`cost_usd`**: `result.total_cost_usd`. **`null` means "not from a `result` event"** — a session-`.jsonl` ingest, a `no_result_event` stream, or a pre-model failure. Story 5 must not read `null` as zero cost, and in session mode `tokens == tokens_main_thread` (no subagent spend is visible).
- **`interrupts`** (`INTERRUPT_KEYS`): `ask_user_question` (main-thread `tool_use` blocks named in `INTERRUPT_TOOLS` = `AskUserQuestion`, `ExitPlanMode`), `status_blocked` (regex `\bSTATUS: BLOCKED\b` over assistant text and tool results, excluding `Read` results of `*.md` files so command templates are not counted).
- **`review_iterations`**: count of `REVIEW_RESULT: FAIL` in the *same source* the final `gate3_review` verdict came from, so an orchestrator echoing the reviewer does not double it.
- **`tests`**: `suite: {passed, total, reason}` (whole jest suite, `--ci --json --forceExit --coverage`, report and coverage written outside the tree) and `original: {passed, total, reason, files}` (the story commit's `test_files` restored via `git show <story_commit>:<path>` *after* the agent exits, run with `--runTestsByPath`). `TEST_BLOCK_KEYS` = `passed`, `total`, `reason`. `reason` is null on a clean run, else `timeout after 1200s`, `no jest report`, `unreadable jest report`, or `suite failed to run (<n> failed suites)` — the last is a compile failure and reads as a failed run, not an empty one.
- **`gates`** — `GATE_NAMES` = `gate0_arch`, `gate2_build`, `gate3_review`, `gate4_tests`, `gate5_docs`; each is `{verdict, source, rederived}` (`GATE_KEYS`); `gate4_tests` also carries `integrity`.
  - `verdict`: last `ARCH_CHECK:` / `REVIEW_RESULT:` / `TEST_RESULT:` / `DOCS_UPDATED:` value (`PROCEED|CAUTION|ABORT|PASS|FAIL|PAUSE|YES|NO|BLOCKED`) or null. `gate2_build.verdict` is always null — no verdict line exists for Gate 2.
  - `source` ∈ `tool_result` (the gate agent's own output, read from the `Task`/`Agent` `tool_result` block), `assistant_text` (fallback: the orchestrator's text), null. **Story 5's `compare` must read `source`**: an `assistant_text` verdict is the orchestrator's restatement, not the agent's.
  - `rederived`: `gate2_build` ← `rederivation.build_smoke.verdict`; `gate4_tests` ← `pass|fail|null` from the suite run (`pass` when `passed == total > 0`, `fail` when any test failed or the suite failed to load, null when nothing ran); `gate0_arch`, `gate3_review`, `gate5_docs` stay null (Business Rule 5: no script exists). `gate4_tests.integrity` ← `rederivation.test_integrity.verdict`.
- **`rederivation`** (`REDERIVATION_KEYS`): `build_smoke`, `test_integrity`; each block is `{argv, verdict, reason}` (`REDERIVATION_BLOCK_KEYS`). `argv` shows `<writ_root>`, `<checkout>`, `<artifacts>` placeholders in place of machine paths. `verdict` ∈ `GATE_SCRIPT_VERDICTS` = `pass`, `fail`, `unverifiable`; a non-zero exit with no parseable verdict, a 600 s timeout, or a missing interpreter is `unverifiable` with a short `reason` (never an exception). Commands: `build-smoke.py check --project <checkout> --timeout 300`, `test-integrity.py coverage --project <checkout> --report <artifacts>/coverage/coverage-final.json`.
- **`exit_criteria`**: `{reported, rederived, rederived_by}`. `reported` is a heuristic over the final assistant text (`DEGRADED` → `"DEGRADED"`, `complete(d)` → `"COMPLETE"`, else null); `rederived` is authoritative — `met` when the staged story reads Completed, carries a commit SHA in `> **Commit:**`, has `## What Was Built`, and `git cat-file -e <sha>^{commit}` succeeds in the checkout, else `unmet`; `rederived_by` = `"implement-story success predicates"`.
- **`yuss_head_unchanged`**: `git -C <yuss> rev-parse HEAD` before vs after the run (Business Rule 2). `false` flushes the record and exits 3.

### Implementation Decisions

1. **Inputs come from the parent commit, never yuss HEAD** (DEV-018) — the HEAD/archive story carries its own answer. `assert_answer_scrubbed` aborts with `answer_leak` if the staged story has `## What Was Built`, a `> **Commit:**` line, or a Complete(d) status.
2. **Current-Writ overlay replaces `writ_scripts`** (DEV-021, user decision 1) — `install.sh --platform claude --no-commit --force` with `cwd=<checkout>`; `--no-commit` keeps `rev-list --all --count == 1` true before the run.
3. **Bypass permission mode with compensating controls** (DEV-019, user decision 2) — no remotes, `FETCH_HEAD` removed, yuss HEAD asserted, `--setting-sources project --strict-mcp-config` so user-level hooks/MCP/plugins stay out of the measured session.
4. **Tokens from the `result` event, main-thread usage kept beside it** (DEV-024) — subagent spend is invisible on per-message `usage`; `tokens_main_thread` exists so the two can be compared.
5. **`postprocess()` is the single record path** — `run` and `ingest` both call it, which is what makes AC-4.5's "identical schema" a structural fact rather than a test assertion.
6. **Transcript is the paid artifact** — any exception after `claude` has run keeps the run dir and prints its path; `ingest` rebuilds the record from it.
7. **Sidecar before the long step** (DEV-024) — `run-meta.json` is written before `claude` starts and again after, so a killed run is ingestable.

### Smoke-run checklist (pending)

Task 4.2 is deferred (user decision 3). A maintainer with `ANTHROPIC_API_KEY`, `claude`, and `pnpm` on `PATH` runs, from this repo's root:

```bash
ANTHROPIC_API_KEY=… python3 scripts/pipeline-baseline.py run \
  --baseline .writ/eval/baselines/2026-09-06-claude-fable-5-1.json \
  --yuss ~/Projects/yuss \
  --story story-4-messaging-migration-quick-split-guard \
  --runs 1 --cap 1800 --budget-usd 25 --keep
```

This pins `runs_per_story: 1` in the baseline; the Story 5 full capture then needs `--runs 2 --force` (the smoke record is kept as run 1 of that story). Keep `--keep` so the transcript survives for inspection.

Confirm against the kept `transcript.jsonl` and record, in order — each is a pinned constant in `scripts/pipeline-baseline.py` that only a live run can validate:

1. The slash command resolves with the path argument (`/implement-story .writ/specs/<folder>/user-stories/<story>.md`) and Gate 0 output appears; the permission flags let Bash (`pnpm test`, `git commit`, `python3 scripts/*.py`) run without denials.
2. `RESULT_SUBTYPE_STATUS` keys — the `result` event's `subtype` on success is `success`; on budget stop it is one of `error_max_budget_usd` / `error_max_budget`.
3. `RESULT_USAGE_FIELDS` — `result.usage` carries `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`; `RESULT_COST_FIELD` = `total_cost_usd`, `RESULT_DURATION_FIELD` = `duration_ms`, `RESULT_TURNS_FIELD` = `num_turns`.
4. `INIT_FIELDS` — the `system`/`init` event carries `model`, `apiKeySource`, `claude_code_version`; `--model claude-fable-5-1` is accepted and `invocation.model_resolved` is populated.
5. `SUBAGENT_TOOLS` (`Task`, `Agent`) and `INTERRUPT_TOOLS` (`AskUserQuestion`, `ExitPlanMode`) are the tool names actually emitted.
6. Subagent events carry `parent_tool_use_id`; main-thread events do not — otherwise `tokens_main_thread` and the verdict source are wrong.
7. The `Task` `tool_result` carries the subagent's verdict line (`ARCH_CHECK:`, `REVIEW_RESULT:`, …), so `gates.<g>.source` reads `tool_result`, not `assistant_text`.
8. `tokens_main_thread < tokens` in every field where subagents ran.
9. `pnpm exec jest --coverage --coverageDirectory=<outside the tree>` writes `coverage-final.json` under yuss's `jest.config.js` (the `json` reporter is on) — otherwise `test_integrity` reads `unverifiable`.
10. `test-integrity.py coverage --report <that file>` returns `pass` or `fail`, not `unverifiable`.
11. `build-smoke.py check --project <checkout> --timeout 300` finishes inside the 600 s wrapper and, on a machine without Postgres, reads `unverifiable` with `environment_*` reasons — not `fail`.
12. `deps.seconds` — `pnpm install --frozen-lockfile --prefer-offline` wall time is well inside `DEPS_TIMEOUT_S` (900 s).

Where a live value differs from a pinned constant, change the constant and its test fixture in one commit and record the deviation here.

### Known limitations

- **No `<json>.lock`.** Two concurrent `run`s against one baseline interleave their `write_json` calls; run them serially (DEV-025).
- **Run-dir name uses the story file stem only** (`writ-baseline-<stem>-<n>`). Distinct for the four committed picks (`story-2-event-creation-payment-flow`, `story-3-settlement-view-share-link`, `story-3-fee-sharing-pro-exemption`, `story-4-messaging-migration-quick-split-guard`); two selected stories sharing a stem across spec folders would collide.
- **Business Rule 2 runtime check covers yuss `HEAD` only** (`yuss_head_unchanged`), not the working tree. The mocked-subprocess tests are the guard for writes under `<yuss>`.
- **`_show_tree` is text-only.** Files materialized via `git show <sha>:<path>` are decoded as UTF-8 with replacement; a binary under `sub-specs/` (a mockup image) would be corrupted in the checkout. All four parents carry the spec folder in-tree, so the fallback did not fire on the committed baseline.
- **A parent without `sub-specs/` is `inputs_missing`.** `stage_inputs` requires `spec.md`, `spec-lite.md`, the story, and a `sub-specs/` directory; a spec folder authored without sub-specs cannot be replayed without a code change.
- **Gate 2 has no reported verdict.** `gate2_build.verdict` is always null; only `rederived` is populated.

### Test Results

**Verification:** Automated (mocked `git`/`claude`/`pnpm`/`bash`/`python3` subprocesses; no live model call — see the smoke-run checklist).

- ✅ `uv run --python 3.9 pytest scripts/tests/test_pipeline_baseline_run.py scripts/tests/test_pipeline_baseline.py` — 119 passed on 3.9 (74 new + 45 Story 3), re-run at Gate 5
- ✅ Gate 4: 99.0 % line coverage on `scripts/pipeline-baseline.py` lines ≥ 685 (the run/ingest code) — task 4.7's 80 % floor met; the per-path 100 % figure for isolation and `scrub()` was not reported separately to Gate 5
- ✅ Gate 4 mutation pass: 11 mutants killed by named tests (6 requested by the testing brief + 5 found)
- ✅ Gate 4 found and fixed 2 bugs: a jest compile failure (`success: false`, `numTotalTests: 0`) read as an empty run instead of `gate4_tests.rederived: fail`; a sidecar-less `ingest` lost its `ingested without sidecar` reason when the transcript status was `complete`
- ✅ Preflight refusal has zero side effects: no `$TMPDIR/writ-baseline-*`, no baseline write, no `git`/`claude`/`pnpm` spawn (AC-4.1)
- ✅ Every spawned argv in the run tests is `git -C <checkout>`, `git -C <yuss> {rev-parse,show}`, `claude`, `pnpm`, `bash <writ_root>/scripts/install.sh`, or `python3 <writ_root>/scripts/{build-smoke,test-integrity}.py`; `<yuss>` is only ever a fetch source or `show` target
- ✅ Committed baseline `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json` and `~/Projects/yuss` unchanged by the story (Gate 2)
- ✅ Stdlib-only import set on Python 3.9 (`StdlibOnlyTest`, AST-based)

**Coverage:** 99.0 % (new code)

### Gate Record

| Gate | Result | Notes |
|---|---|---|
| 0 Architecture | CAUTION | 4 High findings → 3 user decisions (overlay current Writ; bypass permission mode; smoke run deferred) + the exit-criteria correction (`exit-criteria.py` has no `implement-story` mode → completion re-derived from `implement-story.md` predicates) |
| 1 Coding | Complete | `run`/`ingest` + 74 tests, TDD against mocked subprocesses |
| 2 Mechanical | Pass | 119 tests on 3.9; floor-interpreter AST import check; baselines and `~/Projects/yuss` unchanged |
| 3 Review | PASS | 4 should-fixes applied — S1 interrupt safety (`_kill_group` on `KeyboardInterrupt`, SIGKILL always sent), S2 Business Rule 5 gate scripts restored (`build-smoke.py`, `test-integrity.py`), S3 `writ.dirty`, S4 `--force` persistence of `runs_per_story` when nothing else is flushed; nits N1, N2, N3, N5 applied |
| 4 Testing | PASS | 99.0 % line coverage on lines ≥ 685; 11 mutants killed; 2 bugs found and fixed (above) |
| 5 Documentation | YES | This record; `README.md` status; `technical-spec.md` §3 amendment callout |

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 review pass + 1 fix pass (S1–S4, N1/N2/N3/N5)
- **Drift:** Medium ×4 (DEV-018–021), Small ×4 (DEV-022–025) — `drift-log.md`, `spec-lite.md` amended; `technical-spec.md` §3 carries a dated pointer
- **Security:** Clean — secrets only from `os.environ`, never in argv or JSON; `scrub()` rejects `sk-ant-`, strings > 200 chars, and newlines before any write; `.git/FETCH_HEAD` (the only reference to yuss's path) removed from the checkout; bypass permission mode confined to a remote-less checkout with yuss `HEAD` asserted
- **Boundary compliance:** all changes within `scripts/pipeline-baseline.py`, `scripts/tests/`, and this spec folder; `scripts/eval.sh`, the committed baseline, and `~/Projects/yuss` untouched

### Deviations from Spec

Full entries in [`drift-log.md`](../drift-log.md).

- **[DEV-018] Inputs from the parent, never HEAD** — Severity: Medium. `assert_answer_scrubbed` aborts with `answer_leak`; `inputs ∈ {parent, parent_show}`.
- **[DEV-019] Permission mode is bypass** — Severity: Medium. User-approved (decision 2); compensating controls recorded in `invocation` and `isolation`.
- **[DEV-020] Completion re-derived from `implement-story.md` predicates; Gates 2/4 via `build-smoke.py` / `test-integrity.py`** — Severity: Medium. `exit-criteria.py` has no `implement-story` mode.
- **[DEV-021] Current-Writ overlay; `writ{…}` replaces `writ_scripts`** — Severity: Medium. User-approved (decision 1).
- **[DEV-022] `tests.suite` + `tests.original`; `pnpm install` as `deps` before the clock** — Severity: Small.
- **[DEV-023] `Popen` + `killpg`; `--cap` + `--budget-usd` → `--max-budget-usd`; no `--max-turns`** — Severity: Small.
- **[DEV-024] `gates.<g>.source`, `tokens_main_thread`, `exit_criteria.reported` heuristic, sidecar, session-`.jsonl` ingest, exit 3** — Severity: Small.
- **[DEV-025] No `git archive` fallback, no lock, smoke run deferred** — Severity: Small. User-approved (deferral).

### Next Story

**Story 5:** Baseline capture and gate — runs the smoke checklist first, then `run --runs 2 --force` for the full eight records, and implements `check_pipeline_baseline` + `compare` against `RUN_KEYS`/`GATE_NAMES`/`RUN_STATUSES` from this file — reading `gates.<g>.source` and treating `cost_usd: null` as "no `result` event", not zero.
