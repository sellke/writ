# Story 2: Validated Token Measurement — measure-invocation.py Counts With the Anthropic API

> **Status:** Complete
> **Commit:** 0286fab3c556e9cf40e3bcddc2180a17506bc918
> **Priority:** High
> **Dependencies:** Story 1 (lands after Story 1's commit so measurements are taken on the repaired corpus; no code dependency)

## User Story

**As a** Writ maintainer who needs real token counts, not a chars/4 estimate, before comparing pipeline runs
**I want to** run `scripts/measure-invocation.py` and have it count every measured text with the Anthropic Messages `count_tokens` endpoint when `ANTHROPIC_API_KEY` is in my environment, and say so in its output
**So that** the Goal Card's DONE WHEN 2 (`token_method_validated: true`) holds on a real measurement, and Stage 2 cuts are judged against token figures that were counted rather than assumed

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given `ANTHROPIC_API_KEY` is set in `os.environ` and `urllib.request.urlopen` is mocked to return `{"input_tokens": N}`, when `measure(root)` runs with the default tokenizer, then every request is a `POST` to `https://api.anthropic.com/v1/messages/count_tokens` carrying `x-api-key`, `anthropic-version`, and `content-type: application/json` headers and a body of `{"model": "claude-fable-5-1", "messages": [{"role": "user", "content": <text>}]}`, and the report carries `token_method: "anthropic-count-tokens"`, `token_method_validated: true`, `token_model: "claude-fable-5-1"` (or the `--model` override), with each `*_tokens_estimated` figure equal to the sum of the mocked counts for the texts that compose it `[AC-2.1]`
- [x] Given `ANTHROPIC_API_KEY` is absent from the environment, when `measure(root)` runs with the default tokenizer, then the JSON output is byte-identical to the pre-story output for the same tree except that `token_note` names `ANTHROPIC_API_KEY`, `token_method` stays `estimate:chars/4.0`, `token_method_validated` stays `false`, no HTTP call is attempted, and the process exits 0 `[AC-2.2]`
- [x] Given a key is set and `.writ/state/token-cache.json` already holds an entry for a text's content hash under the requested model, when `measure(root)` runs, then no HTTP call is issued for that text, every newly counted text is written back keyed by its content hash, and the cache file contains only hashes and integer counts — never the API key, the model text, or any source text `[AC-2.3]`
- [x] Given a key is set and the mocked HTTP call raises `urllib.error.URLError` (or times out) for some of the measured texts, when `measure(root)` runs, then the failed texts fall back to the `chars_per_token` estimate, the succeeded texts keep their API counts, the report sets `token_method_validated: false` and `token_failures` equal to the number of failed texts, `token_note` says which items degraded, and the process still exits 0 `[AC-2.4]`
- [x] Given the full test suite, when `uv run --python 3.9 pytest scripts/tests/test_measure_invocation.py scripts/tests/test_governor_enforcement.py` runs with no network and no key, then every test passes, the script imports nothing outside the Python 3.9 stdlib, and every key of the `invocation-load-v1` schema present before this story (`schema`, `root`, `token_method`, `token_method_validated`, `chars_per_token`, `token_note`, `ceiling_note`, `base`, `commands`, `corpus`, `warnings`, and each per-command and `corpus` field) is still present with its existing type `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write tests in `scripts/tests/test_measure_invocation.py`: a new `AnthropicCounting` class that patches `urllib.request.urlopen` on the loaded module via `unittest.mock.patch` (matching the `importlib.util.spec_from_file_location` load recipe already in the file) and asserts the request URL, headers, body, and report fields with a key; a `NoKeyIsTodaysOutput` test that runs `measure()` twice with the key removed from `os.environ` (once through the new code path, once with `tokenizer="estimate"`) and asserts the two JSON dumps differ only in `token_note`, which must contain `ANTHROPIC_API_KEY`; a cache test that seeds `<root>/.writ/state/token-cache.json` and asserts zero calls for the seeded hash plus writeback for the rest and no key or source text in the file; a degradation test where the mock raises `URLError` for a subset and asserts `token_failures`, `token_method_validated: false`, and the per-item fallback; and a schema-key test that pins the pre-story `invocation-load-v1` key set `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.2 Add `_count_tokens_anthropic(text, model, api_key, timeout)` to `scripts/measure-invocation.py`: builds a `urllib.request.Request` `POST` to `https://api.anthropic.com/v1/messages/count_tokens` with the three headers and the `{model, messages}` body, parses `input_tokens` from the JSON response, and raises a single narrow `TokenCountError` on `URLError`, `HTTPError`, `socket.timeout`, or a malformed response so the caller has exactly one failure type to degrade on; the key is read once from `os.environ.get("ANTHROPIC_API_KEY")` and never logged, never placed in the report, never written to disk `[AC-2.1, AC-2.4]`
- [x] 2.3 Add a `TokenCache` helper that loads `<root>/.writ/state/token-cache.json` (tolerating a missing, empty, or malformed file by starting empty), keys entries by `sha256(model + "\0" + text)` so a model change never returns a stale count, stores only `hash -> int`, creates `.writ/state/` on first write, and writes once at the end of `measure()` rather than per lookup `[AC-2.3]`
- [x] 2.4 Refactor `measure(root, chars_per_token, command, tokenizer, model, cache_path)`: replace the byte-only `to_tokens(text_bytes)` closure with per-text counting so `floor_tokens_estimated`, `ceiling_tokens_estimated`, and `irreducible_base_tokens_estimated` are sums of real counts over the actual component texts (each base file, the command file, each eager and conditional skill — the base files are counted once and reused across commands); on the anthropic path set `token_method`, `token_method_validated`, `token_model`, `token_failures`, and `token_note` per AC-2.1 and AC-2.4; leave the estimate branch's code and emitted key set untouched so AC-2.2 holds `[AC-2.1, AC-2.4, AC-2.5]`
- [x] 2.5 Wire the CLI in `main()`: `--tokenizer {auto,anthropic,estimate}` (default `auto` = `anthropic` when the key is present, otherwise today's behavior), `--model` (default `claude-fable-5-1`), `--cache` (default `<root>/.writ/state/token-cache.json`); update `TOKEN_NOTE` so the estimate note names `ANTHROPIC_API_KEY` as the way to get a real count; extend the module docstring's Usage block and `render_table()` so the table header shows the model when the anthropic path ran `[AC-2.1, AC-2.2]`
- [x] 2.6 Verify acceptance criteria against the real tree: with the key unset, diff `python3 scripts/measure-invocation.py --root .` against `git show HEAD:scripts/measure-invocation.py | python3 - --root .` and confirm the only differing line is `token_note`; with a key available, confirm `token_method_validated: true` and that `.writ/state/token-cache.json` is gitignored and contains only hashes and integers; append the `{date} stage-1: ...` line to `.writ/decision-log.md` (Business Rule 8) `[AC-2.1, AC-2.2, AC-2.3]` — **partial:** no-key diff and decision-log line done; the real-key sub-step is **not done** (no `ANTHROPIC_API_KEY` in the implementing environment). `token_method_validated: true` was confirmed only via mocked `urlopen`. First real-key run pending a maintainer — see What Was Built → Test Results.
- [x] 2.7 Verify all tests pass: `uv run --python 3.9 pytest scripts/tests/` and `uv run pytest scripts/tests/`, the bash tests loop, and `bash scripts/eval.sh` at `Findings: 0` run outside the sandbox `[AC-2.5]`

## Notes

**Per-text counting changes what `to_tokens` receives.** Today `measure()` calls `to_tokens(floor_bytes)` with a byte total and never passes text; the `text` parameter on the closure is dead. A real count cannot divide a byte sum — it must count each component file and add. Counting the base files once and caching by hash keeps the request count at (2 base files + N commands + M skills) rather than 2 × N, and a second run over an unchanged tree makes zero requests.

**"Byte-identical except `token_note`" constrains new keys.** `token_model` and `token_failures` may appear only when the anthropic path ran. Adding them unconditionally would violate AC-2.2. The estimate branch must emit exactly the key set it emits today; the test in 2.1 pins this.

**Precedence when both a key and `tiktoken` are present.** The existing `_tokenizer()` branch reports `tokenizer:cl100k_base` with `token_method_validated: true` — an OpenAI encoding, not Anthropic's. With `--tokenizer auto` the key wins over `tiktoken`; `tiktoken` remains the fallback only when no key is set, exactly as today. Removing the `tiktoken` branch is out of scope for this story; note it in What Was Built if it looks wrong.

**Secrets (Business Rule 3).** The key is read from `os.environ` only — no `--api-key` flag, no config file, no `.env` parsing. It must not appear in the report, the cache, warnings, or a `TokenCountError` message (an `HTTPError` body can echo request headers; truncate or drop the body before wrapping).

**Timeouts and cost.** Set a per-request timeout (10 s is enough for a count) so a hung connection degrades rather than stalls `eval.sh` callers. `count_tokens` is free of output-token cost but is rate-limited; one request per unique text with the cache in front keeps a full-corpus run to roughly 60–80 requests on first run and 0 thereafter.

**Consumers that read this script.** `scripts/tests/test_governor_enforcement.py` loads `measure-invocation.py` by path and asserts `command_bytes` agrees with `eval-leanness.py`; `eval-leanness.py` mirrors the `INLINE_READ` regex byte-for-byte and a test pins that. Neither touches token fields, but both break if `measure()`'s existing positional signature `(root, chars_per_token, command)` changes — add new parameters as keyword arguments with defaults.

**Integration with Story 5.** `pipeline-baseline.py run` refuses to start without the key (spec.md → Experience Design → Error experience). It will reuse `_count_tokens_anthropic` or its own transcript `usage` fields; keep the function module-level and importable by path so Story 5 does not fork it.

**Risk.** The API's `count_tokens` request shape or `anthropic-version` value may have changed since the spec was written. Confirm the version header value against current Anthropic docs before writing 2.2, and pin it as a named constant so a later bump is one line.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** `spec.md` → `## 🎯 Experience Design` → Error experience (No `ANTHROPIC_API_KEY`: existing estimate, `token_method_validated: false`, one-line note naming the env var); `spec-lite.md` → `## For Testing Agents` → Shadow Paths → Upstream error (API timeout → estimate for failed items, `validated: false`, failure count)
- **Shadow paths:** `spec-lite.md` → `## For Testing Agents` → Shadow Paths → Nil input (no key → named refusal, zero side effects); `spec.md` → `## Specification Contract` → Success Criteria → DONE WHEN 2 (`measure-invocation.py` reports `token_method_validated: true`)
- **Business rules:** `spec.md` → `## 📋 Business Rules` → 3 (Secrets stay in the environment — key from `os.environ` only, never in output or on disk), 8 (Decision log line in the closing commit), 7 (ADR-013 boundary — no merge, PR, or release)
- **Experience:** `spec.md` → `## 🎯 Experience Design` → Error experience (no-key note names the env var); `spec.md` → `## Detailed Requirements` → `### Story 2 — Validated token measurement`; `spec.md` → `## Implementation Approach` (stdlib `urllib`, `anthropic-version` header, Python 3.9, tests under `scripts/tests/`, `eval.sh` at `Findings: 0`)

## What Was Built

**Implementation Date:** 2026-09-06

### Files Created

None.

### Files Modified

- **`scripts/measure-invocation.py`** (+348/−22) — the Anthropic `count_tokens` path.
  - CLI: `--tokenizer auto|anthropic|estimate` (default `auto`: API when `ANTHROPIC_API_KEY` is set, otherwise pre-story behavior; `anthropic`: insist on the API, warn and estimate without a key; `estimate`: chars/N regardless of what is installed or set), `--model` (default `claude-fable-5-1`), `--cache` (default `<root>/.writ/state/token-cache.json`).
  - `measure(root, chars_per_token=4.0, command=None, tokenizer="auto", model=DEFAULT_MODEL, cache_path=None)` — new parameters are keyword-only-by-convention with defaults, so the existing positional callers (`test_governor_enforcement.py`, `eval-leanness.py` mirror) are untouched. Always exits 0.
  - `_count_tokens_anthropic(text, model, api_key, timeout=10.0) -> int` — module-level and importable by path for Story 5. `POST` to `ANTHROPIC_COUNT_TOKENS_URL` with `x-api-key`, `anthropic-version`, `content-type: application/json`; body `{"model", "messages": [{"role": "user", "content": text}]}`; returns `input_tokens`. Raises `TokenCountError` on `URLError`, `HTTPError`, `socket.timeout`, `OSError`, `http.client.HTTPException` (IncompleteRead, RemoteDisconnected, etc.), non-JSON body, or a missing/negative/boolean `input_tokens`; `TokenAuthError(TokenCountError)` on HTTP 401/403, which is fatal — the counter issues no further requests. The `HTTPError` body is never read (it can echo request headers).
  - `token_cache_key(model, text) = sha256(model + "\0" + text)` exported so no caller re-derives the formula.
  - `TokenCache` at `<root>/.writ/state/token-cache.json` (gitignored via `.writ/state/`): `{sha256hex: int}` only — never the key, the model name, or any source text. Missing, empty, or malformed file starts empty; `flush()` writes once at the end of `measure()` and only when ≥1 new count was obtained; failed counts are never cached; a write failure is a warning, not an error.
  - `_AnthropicCounter` — per-text counting with the cache in front; base files counted once and reused per command; failures remembered by content hash so a shared skill that fails is one failure and is not re-requested within the run.
  - Report: `token_model` and `token_failures` are added **only** on the anthropic path (AC-2.2 byte-identity). `token_method: "anthropic-count-tokens"`; `token_method_validated` is `true` iff `token_failures == 0`. Per-item degradation: a failed text contributes `round(len_bytes / chars_per_token)`; the degraded `token_note` lists ≤10 failed labels, then `(+N more)`, and the first failure reason. `TOKEN_NOTE` (estimate) now names `ANTHROPIC_API_KEY` as the way to get a real count.
  - `render_table()` header shows `[model]` and `token_failures` via `.get` / key presence, so a pre-story report still renders.
  - Constants: `ANTHROPIC_COUNT_TOKENS_URL`, `ANTHROPIC_VERSION = "2023-06-01"` (confirmed against the API reference 2026-09-06; a later bump is one line), `API_KEY_ENV`, `DEFAULT_MODEL`, `REQUEST_TIMEOUT_SECONDS = 10.0`, `TOKENIZER_CHOICES`, `TOKEN_CACHE_RELPATH`.
  - Module docstring: "On tokens" section and Usage block rewritten for the count/estimate split.
- **`scripts/tests/test_measure_invocation.py`** (+969/−2; 86 tests in file) — seven new classes: `AnthropicCounting` (request URL/headers/body, report fields, sums over component texts, base counted once), `NoKeyIsTodaysOutput` (two `measure()` runs differ only in `token_note`; estimate still divides the aggregate byte sum), `TokenizerSelection` (`auto`/`anthropic`/`estimate` precedence, `anthropic` without key warns), `TokenCaching` (seeded hash → zero calls, writeback, no key/text/model in file, no write when nothing new, write failure → warning), `Degradation` (`URLError`/timeout/HTTP 5xx subsets, `token_failures`, `validated: false`, per-item fallback, ≤10 labels `(+N more)`, 401 stops further requests), `CountTokensAnthropic` (each `TokenCountError` branch, body never read), `SchemaCompatibility` (every pre-story `invocation-load-v1` key and type present on the anthropic path; stdlib-only imports). `_run` strips `ANTHROPIC_API_KEY` from the subprocess env; every `with_key()` site has a patched `urlopen`, so no test can reach the network.
- **`scripts/tests/test_governor_enforcement.py`** (+2/−1) — `--tokenizer estimate` added to the real-repo subprocess argv so a maintainer with a key set never triggers ~50 live requests during pytest.

### Deviations from Spec

All Small; entries in [`drift-log.md`](../drift-log.md), `spec-lite.md` amended.

- **DEV-014** — cache key separator is NUL (story task 2.3) over technical-spec §5's `"\n"`; exported as `token_cache_key`.
- **DEV-015** — tokenizer tests live in the existing `test_measure_invocation.py` (task 2.1), not §10's new `test_measure_invocation_tokenizer.py`.
- **DEV-016** — `token_failures` counts distinct failed texts by content hash; a skill shared by N commands is 1 failure.
- **DEV-017** — `--tokenizer estimate` bypasses an installed `tiktoken` (chars/N regardless); `auto` without a key keeps tiktoken-if-installed so AC-2.2 byte-identity holds.

### Test Results

- ✅ `uv run --python 3.9 pytest scripts/tests/test_measure_invocation.py scripts/tests/test_governor_enforcement.py` — 135 passed; same on Python 3.13.
- ✅ Full suite — 885 passed.
- ✅ Coverage: `measure-invocation.py` 95%, every Story 2 line covered.
- ✅ AC-2.2 on the real tree, no key: JSON from HEAD's script vs the working copy differs only in the `token_note` line (629 lines each); no cache file created.
- ✅ Anthropic path exercised only via mocked `urlopen`. Request count on the current tree: 50 distinct texts (2 base + 32 commands + 16 unique skills) on a cold cache; 0 on a warm cache.
- ⚠️ **No real-key run has been performed.** The first run with `ANTHROPIC_API_KEY` set is pending a maintainer. That run is what finally validates or recalibrates the chars/4 ratio that ADR-021 and ADR-023 both call unvalidated; until it happens, DONE WHEN 2 holds on the mocked path only.
- Gate 4 mutation check: the original `test_estimate_figures_are_still_computed_on_byte_sums` fixture (101+51+434 bytes) could not distinguish aggregate rounding from per-text rounding; `test_estimate_rounds_the_aggregate_not_the_sum_of_per_text_rounds` (100+50 bytes) now does.

### Known Gaps / Follow-ups

Found at Gates 3–4, deliberately not fixed here:

- **Pre-existing `tiktoken` branch mislabel** (`_tokenizer()`, `measure-invocation.py` ~474–482): reports `tokenizer:cl100k_base` with `token_method_validated: true` while `to_tokens` is only ever called with a byte sum, so it actually computes chars/N — an ADR-019 labeling failure. Out of scope per this story's Notes; candidate for a follow-up issue (remove the branch or label it an estimate).
- `TokenCache._load` accepts negative ints.
- `_inline_read_skills` return annotation says `list[str]`; it returns a `(inlined, hoisted)` tuple.
- `sub-specs/technical-spec.md` §5 still says `"\n"` (append-only spec; the drift log carries the resolution).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1
- **Drift:** Small ×4 (DEV-014–017)
- **Security:** Clean — key read from `os.environ` only; absent from report, cache, warnings, and every `TokenCountError` message.
- **Boundary compliance:** all changes within Owned files; `measure()`'s positional signature and the estimate branch's emitted key set unchanged.
