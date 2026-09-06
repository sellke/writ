# Story 2: Validated Token Measurement — measure-invocation.py Counts With the Anthropic API

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1 (lands after Story 1's commit so measurements are taken on the repaired corpus; no code dependency)

## User Story

**As a** Writ maintainer who needs real token counts, not a chars/4 estimate, before comparing pipeline runs
**I want to** run `scripts/measure-invocation.py` and have it count every measured text with the Anthropic Messages `count_tokens` endpoint when `ANTHROPIC_API_KEY` is in my environment, and say so in its output
**So that** the Goal Card's DONE WHEN 2 (`token_method_validated: true`) holds on a real measurement, and Stage 2 cuts are judged against token figures that were counted rather than assumed

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given `ANTHROPIC_API_KEY` is set in `os.environ` and `urllib.request.urlopen` is mocked to return `{"input_tokens": N}`, when `measure(root)` runs with the default tokenizer, then every request is a `POST` to `https://api.anthropic.com/v1/messages/count_tokens` carrying `x-api-key`, `anthropic-version`, and `content-type: application/json` headers and a body of `{"model": "claude-fable-5-1", "messages": [{"role": "user", "content": <text>}]}`, and the report carries `token_method: "anthropic-count-tokens"`, `token_method_validated: true`, `token_model: "claude-fable-5-1"` (or the `--model` override), with each `*_tokens_estimated` figure equal to the sum of the mocked counts for the texts that compose it `[AC-2.1]`
- [ ] Given `ANTHROPIC_API_KEY` is absent from the environment, when `measure(root)` runs with the default tokenizer, then the JSON output is byte-identical to the pre-story output for the same tree except that `token_note` names `ANTHROPIC_API_KEY`, `token_method` stays `estimate:chars/4.0`, `token_method_validated` stays `false`, no HTTP call is attempted, and the process exits 0 `[AC-2.2]`
- [ ] Given a key is set and `.writ/state/token-cache.json` already holds an entry for a text's content hash under the requested model, when `measure(root)` runs, then no HTTP call is issued for that text, every newly counted text is written back keyed by its content hash, and the cache file contains only hashes and integer counts — never the API key, the model text, or any source text `[AC-2.3]`
- [ ] Given a key is set and the mocked HTTP call raises `urllib.error.URLError` (or times out) for some of the measured texts, when `measure(root)` runs, then the failed texts fall back to the `chars_per_token` estimate, the succeeded texts keep their API counts, the report sets `token_method_validated: false` and `token_failures` equal to the number of failed texts, `token_note` says which items degraded, and the process still exits 0 `[AC-2.4]`
- [ ] Given the full test suite, when `uv run --python 3.9 pytest scripts/tests/test_measure_invocation.py scripts/tests/test_governor_enforcement.py` runs with no network and no key, then every test passes, the script imports nothing outside the Python 3.9 stdlib, and every key of the `invocation-load-v1` schema present before this story (`schema`, `root`, `token_method`, `token_method_validated`, `chars_per_token`, `token_note`, `ceiling_note`, `base`, `commands`, `corpus`, `warnings`, and each per-command and `corpus` field) is still present with its existing type `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write tests in `scripts/tests/test_measure_invocation.py`: a new `AnthropicCounting` class that patches `urllib.request.urlopen` on the loaded module via `unittest.mock.patch` (matching the `importlib.util.spec_from_file_location` load recipe already in the file) and asserts the request URL, headers, body, and report fields with a key; a `NoKeyIsTodaysOutput` test that runs `measure()` twice with the key removed from `os.environ` (once through the new code path, once with `tokenizer="estimate"`) and asserts the two JSON dumps differ only in `token_note`, which must contain `ANTHROPIC_API_KEY`; a cache test that seeds `<root>/.writ/state/token-cache.json` and asserts zero calls for the seeded hash plus writeback for the rest and no key or source text in the file; a degradation test where the mock raises `URLError` for a subset and asserts `token_failures`, `token_method_validated: false`, and the per-item fallback; and a schema-key test that pins the pre-story `invocation-load-v1` key set `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.2 Add `_count_tokens_anthropic(text, model, api_key, timeout)` to `scripts/measure-invocation.py`: builds a `urllib.request.Request` `POST` to `https://api.anthropic.com/v1/messages/count_tokens` with the three headers and the `{model, messages}` body, parses `input_tokens` from the JSON response, and raises a single narrow `TokenCountError` on `URLError`, `HTTPError`, `socket.timeout`, or a malformed response so the caller has exactly one failure type to degrade on; the key is read once from `os.environ.get("ANTHROPIC_API_KEY")` and never logged, never placed in the report, never written to disk `[AC-2.1, AC-2.4]`
- [ ] 2.3 Add a `TokenCache` helper that loads `<root>/.writ/state/token-cache.json` (tolerating a missing, empty, or malformed file by starting empty), keys entries by `sha256(model + "\0" + text)` so a model change never returns a stale count, stores only `hash -> int`, creates `.writ/state/` on first write, and writes once at the end of `measure()` rather than per lookup `[AC-2.3]`
- [ ] 2.4 Refactor `measure(root, chars_per_token, command, tokenizer, model, cache_path)`: replace the byte-only `to_tokens(text_bytes)` closure with per-text counting so `floor_tokens_estimated`, `ceiling_tokens_estimated`, and `irreducible_base_tokens_estimated` are sums of real counts over the actual component texts (each base file, the command file, each eager and conditional skill — the base files are counted once and reused across commands); on the anthropic path set `token_method`, `token_method_validated`, `token_model`, `token_failures`, and `token_note` per AC-2.1 and AC-2.4; leave the estimate branch's code and emitted key set untouched so AC-2.2 holds `[AC-2.1, AC-2.4, AC-2.5]`
- [ ] 2.5 Wire the CLI in `main()`: `--tokenizer {auto,anthropic,estimate}` (default `auto` = `anthropic` when the key is present, otherwise today's behavior), `--model` (default `claude-fable-5-1`), `--cache` (default `<root>/.writ/state/token-cache.json`); update `TOKEN_NOTE` so the estimate note names `ANTHROPIC_API_KEY` as the way to get a real count; extend the module docstring's Usage block and `render_table()` so the table header shows the model when the anthropic path ran `[AC-2.1, AC-2.2]`
- [ ] 2.6 Verify acceptance criteria against the real tree: with the key unset, diff `python3 scripts/measure-invocation.py --root .` against `git show HEAD:scripts/measure-invocation.py | python3 - --root .` and confirm the only differing line is `token_note`; with a key available, confirm `token_method_validated: true` and that `.writ/state/token-cache.json` is gitignored and contains only hashes and integers; append the `{date} stage-1: ...` line to `.writ/decision-log.md` (Business Rule 8) `[AC-2.1, AC-2.2, AC-2.3]`
- [ ] 2.7 Verify all tests pass: `uv run --python 3.9 pytest scripts/tests/` and `uv run pytest scripts/tests/`, the bash tests loop, and `bash scripts/eval.sh` at `Findings: 0` run outside the sandbox `[AC-2.5]`

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

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** `spec.md` → `## 🎯 Experience Design` → Error experience (No `ANTHROPIC_API_KEY`: existing estimate, `token_method_validated: false`, one-line note naming the env var); `spec-lite.md` → `## For Testing Agents` → Shadow Paths → Upstream error (API timeout → estimate for failed items, `validated: false`, failure count)
- **Shadow paths:** `spec-lite.md` → `## For Testing Agents` → Shadow Paths → Nil input (no key → named refusal, zero side effects); `spec.md` → `## Specification Contract` → Success Criteria → DONE WHEN 2 (`measure-invocation.py` reports `token_method_validated: true`)
- **Business rules:** `spec.md` → `## 📋 Business Rules` → 3 (Secrets stay in the environment — key from `os.environ` only, never in output or on disk), 8 (Decision log line in the closing commit), 7 (ADR-013 boundary — no merge, PR, or release)
- **Experience:** `spec.md` → `## 🎯 Experience Design` → Error experience (no-key note names the env var); `spec.md` → `## Detailed Requirements` → `### Story 2 — Validated token measurement`; `spec.md` → `## Implementation Approach` (stdlib `urllib`, `anthropic-version` header, Python 3.9, tests under `scripts/tests/`, `eval.sh` at `Findings: 0`)
