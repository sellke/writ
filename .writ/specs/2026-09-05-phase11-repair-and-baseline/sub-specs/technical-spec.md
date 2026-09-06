# Technical Specification — Phase 11 Stage 1: Repair and Baseline

> Parent: [`../spec.md`](../spec.md) · Stories: [`../user-stories/README.md`](../user-stories/README.md)

## 1. Components

| Component | Story | Location | Responsibility |
|---|---|---|---|
| Dead-end fixes | 1 | `commands/*.md`, `adapters/*.md`, `.writ/manifest.yaml`, `.writ/knowledge/lessons/*.md` | Close the 19 items in assessment §2.4 |
| Knowledge writeback fix | 1 | `scripts/phase-state.py` (`knowledge_writeback`, ~line 794) | Stop iterating a string as a list when writing `related_artifacts` and evidence bullets |
| `check_referenced_paths` | 1 | `scripts/eval.sh` | Every backticked `*.md` path in `commands/*.md` exists, is created by a named command, or is allowlisted with a reason |
| `check_skill_manifest_parity` | 1 | `scripts/eval.sh` | `comm -3 <(ls skills) <(manifest skill names)` is empty |
| `check_knowledge_integrity` | 1 | `scripts/eval.sh` | No `.writ/knowledge/**/*.md` bullet has single-character content |
| `.writ/decision-log.md` | 1 | repo root `.writ/` | One line per story: `{date} stage-1: {what changed and why}` |
| `--tokenizer anthropic` | 2 | `scripts/measure-invocation.py` | Real token counts via `count_tokens`; content-hash cache in `.writ/state/token-cache.json` |
| `pipeline-baseline.py select` | 3 | `scripts/pipeline-baseline.py` | Fixed-criteria selection of four yuss stories; JSON skeleton |
| `pipeline-baseline.py run` / `ingest` | 4 | same | Isolated checkout, headless `/implement-story`, metrics parse, run records |
| `pipeline-baseline.py validate` / `compare` | 5 | same | Schema validation for the eval check; per-story deltas |
| `check_pipeline_baseline` | 5 | `scripts/eval.sh` | Note when absent; block on schema violation |
| Baseline file | 5 | `.writ/eval/baselines/<date>-claude-fable-5-1.json` | The committed record |

## 2. Baseline JSON schema (`pipeline-baseline-v1`)

```json
{
  "schema": "pipeline-baseline-v1",
  "created": "YYYY-MM-DD",
  "model": "claude-fable-5-1",
  "writ_version": "0.35.0",
  "writ_commit": "<sha>",
  "yuss_commit_at_selection": "<sha>",
  "runs_per_story": 2,
  "criteria": {
    "status": "Completed",
    "requires_story_commit": true,
    "requires_test_file": true,
    "live_service_denylist": ["prisma", "stripe", "@neondatabase", "next-auth"],
    "surface_classes": {
      "api": ["app/api/**"],
      "ui": ["components/**", "app/**/page.tsx"],
      "data": ["prisma/**", "lib/db/**"],
      "refactor": "no new files and net negative lines"
    },
    "tie_break": "most recent story"
  },
  "selection": [
    {
      "story_id": "<spec-folder>/story-N-<slug>",
      "story_path": ".writ/specs/archive/<spec-folder>/user-stories/story-N-<slug>.md",
      "spec_folder": "<spec-folder>",
      "story_commit": "<sha>",
      "parent_sha": "<sha>",
      "parent_is_first_parent_of_merge": false,
      "surface_class": "api|ui|data|refactor",
      "test_files": ["path", "..."],
      "test_command": "npx jest <paths>",
      "admitted_by": {"status": "Completed", "commit_found_via": "Commit: header|git log --grep", "test_files": 2, "denylist_hits": 0}
    }
  ],
  "excluded": [{"story_path": "...", "reason": "denylist:prisma|no_test_file|no_commit|class_full:ui"}],
  "runs": [
    {
      "story_id": "...",
      "run": 1,
      "status": "complete|timeout|error",
      "isolation": {"reachable_commits": 1, "asserted": true},
      "writ_scripts": "checkout|current",
      "wall_clock_s": 0,
      "tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
      "interrupts": {"ask_question": 0, "status_blocked": 0},
      "review_iterations": 0,
      "tests": {"passed": 0, "total": 0, "command": "..."},
      "ac_trace_findings": 0,
      "gates": {
        "gate0_arch":   {"reported": "PROCEED|CAUTION|ABORT|null", "rederived": null},
        "gate2_build":  {"reported": "pass|fail|null", "rederived": "pass|fail|null"},
        "gate3_review": {"reported": "PASS|FAIL|PAUSE|null", "rederived": null},
        "gate4_tests":  {"reported": "pass|fail|null", "rederived": "pass|fail|null", "coverage_reported": 0, "coverage_rederived": 0},
        "gate5_docs":   {"reported": "YES|NO|BLOCKED|null", "rederived": null},
        "exit_criteria": {"reported": "complete|incomplete|null", "rederived": "met|unmet|impossible"}
      }
    }
  ]
}
```

Rules the validator enforces (Story 5): every string field ≤ 200 characters; no value matching `sk-ant-` or containing a newline (transcript/source text cannot fit); `len(selection) == 4`; each `surface_class` appears exactly once; `len(runs) == runs_per_story * 4` for a `complete` file (a partial file is valid during `run` but the eval check requires complete).

## 3. Isolation procedure (Business Rule 1)

```bash
dir="$TMPDIR/writ-baseline-${story}-${n}"; mkdir -p "$dir" && cd "$dir"
git init -q
git fetch -q --depth 1 "$YUSS" "$PARENT_SHA"
git checkout -q FETCH_HEAD
test "$(git rev-list --all | wc -l)" -eq 1   # recorded as isolation.reachable_commits
```

`git fetch --depth 1 <sha>` requires the source repo to allow fetching unadvertised objects (`uploadpack.allowReachableSHA1InWant`); a local path source does. If the fetch is refused, fall back to `git -C "$YUSS" archive "$PARENT_SHA" | tar -x -C "$dir" && git init && git add -A && git commit -qm baseline` — one synthetic commit, still one reachable. Either way, the model cannot see the story's real commit or anything after it.

Inputs copied into the checkout after isolation: `.writ/specs/<folder>/{spec.md,spec-lite.md,sub-specs/,user-stories/<story>.md}` from `$YUSS` at HEAD (these are the artifacts a real run had), plus current `scripts/` from this repo when the checkout's `.claude/`-installed Writ predates a script `/implement-story` calls (recorded as `writ_scripts: current`).

## 4. Headless invocation (Story 4)

```bash
timeout "$CAP" claude -p "/implement-story ${STORY_ID}" \
  --model "$MODEL" --output-format stream-json --permission-mode acceptEdits \
  > "$dir/transcript.jsonl" 2> "$dir/stderr.log"
```

Metrics come from the `stream-json` events: `usage` fields on assistant messages sum to `tokens.*`; count of tool-use events named `AskQuestion` (or Claude Code's equivalent prompt) → `interrupts.ask_question`; regex `STATUS: BLOCKED` → `interrupts.status_blocked`; last occurrence of `ARCH_CHECK:`, `REVIEW_RESULT:`, `TEST_RESULT:`, `DOCS_UPDATED:` → `gates.*.reported`; count of `REVIEW_RESULT: FAIL` → `review_iterations`. `--permission-mode` and the exact event shape are verified in task 4.2's smoke run and recorded; if `-p` will not accept a slash command, the fallback is a human session in the same checkout plus `ingest --checkout <dir> --transcript <file>`, which computes an identical record.

Wall-clock cap default 90 minutes per run; a timeout produces a record with `status: timeout` and whatever re-derivation the tree supports, and the runner continues.

## 5. Token counting (Story 2)

`POST https://api.anthropic.com/v1/messages/count_tokens`, headers `x-api-key: $ANTHROPIC_API_KEY`, `anthropic-version: 2023-06-01`, `content-type: application/json`; body `{"model": "<id>", "messages": [{"role": "user", "content": "<text>"}]}`; response `input_tokens`. Cache key: `sha256(model + "\n" + text)`; cache file `.writ/state/token-cache.json` (gitignored). Output additions to `invocation-load-v1`: `token_method: "anthropic-count-tokens"`, `token_method_validated: true`, `token_model: "<id>"`, `token_failures: 0`. Every pre-existing key is preserved and `measure()`'s signature stays compatible: the consumers are `scripts/tests/test_governor_enforcement.py` (loads the module by path, compares `command_bytes` with `eval-leanness.py`) and `eval-leanness.py`'s byte-identical `INLINE_READ` regex mirror — not `eval.sh`, which never reads this script. Today `measure()` calls `to_tokens(floor_bytes)` with a byte sum and never sees text, so counting becomes per-text (each base file, command, skill), with base files counted once and cached by hash. One request per distinct text, sequential, 10 s timeout each; on any failure the item falls back to the estimate and `token_failures` increments, `token_method_validated` becomes `false`.

## 6. eval.sh checks

| Check | Blocking | Fixture test |
|---|---|---|
| `referenced-paths` | yes | `scripts/tests/test_referenced_paths.sh`: a command citing `nonexistent.md` → finding; citing `.writ/docs/tech-stack.md` with `initialize.md` naming it → pass; allowlist entry with reason → pass |
| `skill-manifest-parity` | yes | temp `skills/` dir with an extra folder → finding; matched → pass |
| `knowledge-integrity` | yes | fixture entry with `- s` bullets → finding; intact entry → pass |
| `pipeline-baseline` | note when absent, block on invalid | valid fixture → pass; `len(selection)==3` → finding; 300-char string → finding; `sk-ant-` substring → finding |

## 7. Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| `count_tokens` request | No `ANTHROPIC_API_KEY` | Estimate path unchanged; `token_note` names the env var; `validated: false` | Unit test with env cleared |
| `count_tokens` request | HTTP 4xx/5xx or timeout | Estimate for that item; `token_failures += 1`; `validated: false`; run continues | Mocked 529 and socket timeout |
| `count_tokens` request | 401 (bad key) | Stop after first 401 with one line naming the header; no further requests | Mocked 401 |
| `select` scan | `<yuss>` path missing or not a git repo | Refuse before writing; name the path | Unit test with temp dir |
| `select` scan | Story has no resolvable commit | Excluded with `reason: no_commit`; appears in `excluded[]` | Fixture story without `Commit:` and no grep hit |
| `select` scan | Fewer than four admissible stories | Exit 2 naming the short class; JSON not written | Fixture archive with three admissible |
| Isolation | `fetch --depth 1 <sha>` refused | `git archive` fallback; `isolation.method: archive` | Mocked git returning non-zero on fetch |
| Isolation | Reachable commit count ≠ 1 | Abort this run before invoking the model; record `status: error`, `isolation.asserted: false` | Unit test with two-commit fixture |
| Headless run | `claude` binary absent | Refuse at `run` start; no checkout created; name install docs | Unit test with PATH cleared |
| Headless run | `-p` rejects slash command | Task 4.2 smoke run detects; fall back to `ingest`; deviation recorded in What Was Built | Live smoke run |
| Headless run | Wall-clock cap hit | `status: timeout`; partial re-derivation; continue to next run | Mocked subprocess with `timeout` exit |
| Run record | Crash after run k of 8 | Records flushed per run; rerun skips `(story, n)` pairs already present | Unit test resuming from a 3-record file |
| Original tests | Test command needs a live service after all | `tests.total: 0`, `tests.error: "<first line of stderr, ≤200 chars>"`; story flagged in `excluded_post_hoc` | Mocked jest failure with ECONNREFUSED |
| `validate` | Field > 200 chars or key-like string | Finding names the JSON path | Fixture |
| `compare` | Different `selection` blocks | Refuse; print the differing story IDs | Fixture pair |
| Knowledge writeback | Iterating a string as a list | Type-check at the writeback boundary; wrap scalars in a list; regression test with a single-string `related_artifacts` | Unit test on `phase-state.py knowledge_writeback` |

No `[UNPLANNED]` rows remain.

## 8. Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| `measure-invocation.py --tokenizer anthropic` | JSON with real counts, `validated: true` | No key → estimate, `validated: false`, note names env var | Empty text → `0` tokens, no request | API down → estimate for failed items, `token_failures` count |
| `select` | Four stories, one per class, JSON written | No `--yuss` → usage error, nothing written | Archive with zero stories → exit 2 "no candidates" | `git log` fails → story excluded `reason: git_error` |
| `run` | Eight records, temp dirs removed | No key or no `claude` → refuse before any checkout | Empty `selection` → refuse "run select first" | Fetch refused → archive fallback; model timeout → `status: timeout` |
| `compare` | Per-story delta table | One path → usage error | Baseline with zero runs → "nothing to compare" | Mismatched selection → refuse with IDs |
| `eval.sh --check=pipeline-baseline` | Pass | No file → note | Empty JSON → finding "schema missing" | — |

## 9. Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Two `run` invocations concurrently on the same JSON | Lock file `<json>.lock`; second invocation refuses |
| Story commit is a merge | Use first parent; `parent_is_first_parent_of_merge: true` |
| Two selected stories share one commit | Both eligible; tie → most recent; recorded |
| `select` re-run after yuss advances | New file, not an overwrite, unless `--force`; `yuss_commit_at_selection` differs |
| `compare` across `runs_per_story` 2 vs 3 | Allowed; per-story medians |
| Checkout's `.claude/` predates a script | Copy current `scripts/`; `writ_scripts: current` |

## 10. Test plan

- pytest: `scripts/tests/test_pipeline_baseline.py` (select criteria, isolation assertion, record parsing from a fixture `stream-json` transcript, resume, validate, compare), `scripts/tests/test_measure_invocation_tokenizer.py` (key/no-key, cache hit, 401, 529, timeout). Subprocess and `urllib` mocked throughout. Python 3.9 and 3.12 both green.
- bash: one fixture test per new eval check (§6).
- Live: one smoke run (task 4.2) and the eight baseline runs (Story 5), each recorded in What Was Built with tokens and dollars.
- Coverage: new code ≥ 80%; isolation-assertion and secret-exclusion paths 100%.

## 11. Story dependencies

```
Story 1 (repair) ─ commit first
Story 2 (tokens) ──────────────┐
Story 3 (select) ── Story 4 (run) ── Story 5 (capture + gate)
```

Stories 2 and 3 have no code dependency on Story 1 but land after its commit so the corpus measured is the repaired one.
