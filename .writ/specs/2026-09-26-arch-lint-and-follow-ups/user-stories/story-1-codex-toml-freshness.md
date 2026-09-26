# Story 1: Codex TOML Freshness

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer shipping agent definitions to Codex users
**I want to** have `scripts/gen-codex-agent-tomls.py` map every agent, refuse to write a partial set, and report drift through a `--check` mode wired into `eval.sh`
**So that** `codex/agents/*.toml` can no longer drift silently from `agents/*.md` (6 of 8 TOMLs differ today and no check catches it)

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given `agents/evaluator-agent.md` exists, when `PURPOSES` and `SANDBOX` are read, then `evaluator-agent` maps to its `.writ/manifest.yaml` purpose verbatim and to `read-only`; and given any `agents/*.md` stem, then its `PURPOSES` value equals the manifest `agents[].purpose` for that stem `[AC-1.1]`
- [x] Given an `agents/` directory containing a stem missing from `PURPOSES` or `SANDBOX`, when the generator runs in write mode, then it exits non-zero naming every unmapped stem and writes no file (every stem is validated before the first write) `[AC-1.2]`
- [x] Given `--check` and generated output identical to `codex/agents/*.toml`, when it runs, then it writes nothing, prints `pass` and the summary `gen-codex-agent-tomls: pass (0 stale, 0 missing, 0 orphan, 0 unmapped)` last, and exits 0; and given an unknown argument, then it exits 2 `[AC-1.3]`
- [x] Given `--check` with a hand-edited TOML, an `.md` without a `.toml`, a `.toml` without an `.md`, or a stem missing from `PURPOSES`/`SANDBOX`, when it runs, then it prints `fail`, one `reason: stale|missing|orphan|unmapped <stem>` line per problem in stem order, the counted summary last, and exits 1 without crashing or writing `[AC-1.4]`
- [x] Given `bash scripts/eval.sh`, when `check_codex_tomls` runs against a temp copy with a hand-edited TOML, then it records one finding per `reason:` line with remediation `python3 scripts/gen-codex-agent-tomls.py` (and a finding when the helper is missing); and given the real repo after regenerating all 8 TOMLs via the CLI, then the check passes and `test_codex_bodies_match_agent_sources` stays green `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write failing tests in `scripts/tests/test_gen_codex_agent_tomls.py`: every `agents/*.md` stem has `PURPOSES` and `SANDBOX` entries, each `PURPOSES` value equals its `.writ/manifest.yaml` purpose, and `evaluator-agent` is `read-only` `[AC-1.1]`
- [x] 1.2 Write failing tests using temp agent/output dirs: write mode with an unmapped stem exits non-zero naming all unmapped stems and leaves the output dir untouched; `--check` pass, each of `stale`/`missing`/`orphan`/`unmapped` in stem order with the counted summary, no writes in check mode, and exit 2 on a bad argument `[AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.3 Write failing `scripts/tests/test_eval_codex_tomls.sh` that copies the needed files to a temp dir, hand-edits one TOML, and asserts `check_codex_tomls` emits a finding naming the stem with the remediation command; plus a missing-helper case `[AC-1.5]`
- [x] 1.4 Extend `scripts/gen-codex-agent-tomls.py` per technical-spec §1: add `evaluator-agent` to `PURPOSES`/`SANDBOX`; refactor `main()` into `expected_tomls()` that validates every stem before any write; add `--check` with helper-family output and exit codes 0/1/2; make agent/output dirs overridable for tests; update the module docstring `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.5 Add `check_codex_tomls` to `scripts/eval.sh`, registered like `check_drift_format`: runs `--check`, one `add_finding` per `reason:` line, `add_finding` when the helper is missing `[AC-1.5]`
- [x] 1.6 Regenerate all 8 `codex/agents/*.toml` with `python3 scripts/gen-codex-agent-tomls.py` (never by hand) and review the diff `[AC-1.1, AC-1.5]`
- [x] 1.7 Verify: `uv run --python 3.9 pytest scripts/tests/test_gen_codex_agent_tomls.py scripts/tests/test_drift_severity_wiring.py`, `bash scripts/tests/test_eval_codex_tomls.sh`, `python3 scripts/gen-codex-agent-tomls.py --check` prints `pass`, and `bash scripts/eval.sh --check=codex-tomls` has no findings `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

Today `main()` writes files alphabetically and crashes at `evaluator-agent` via `emit_toml`'s `SystemExit`, leaving earlier TOMLs rewritten and later ones stale; validating first removes that half-written state. In `--check`, an unmapped stem is a `reason:` line, not a crash, so `eval.sh` can name it. Business Rule 6 makes the generator the only TOML writer: regenerate, never hand-edit. The `eval.sh` bash test must never mutate the real `codex/agents/`. Keep the helper stdlib-only and Python 3.9-compatible (`from __future__ import annotations` is already present for the `dict[...]` hints).

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** spec.md → ## 📋 Business Rules (6 The generator is the only TOML writer)
- **Requirements:** spec.md → ## Detailed Requirements → Codex TOML freshness (Story 1)
- **Technical:** sub-specs/technical-spec.md → ## 1 (reason table, summary format, `eval.sh` wiring) and ## 5 (verification)
- **Edge cases:** spec-lite.md → ## For Testing Agents → Edge Cases (hand-edited TOML → `stale`; extra TOML → `orphan`)

## What Was Built

**Implementation Date:** 2026-09-26

### Files Modified

1. **`scripts/gen-codex-agent-tomls.py`** — `evaluator-agent` in `PURPOSES`/`SANDBOX` (`read-only`); `main()` split into `expected_tomls()` (validates every stem before any write), `write()` and `check()`; `--check` prints `pass|fail`, one `reason: stale|missing|orphan|unmapped <stem>` per problem in stem order, then the counted summary; exit 0/1/2 with `allow_abbrev=False`; `--agents-dir`/`--out-dir` for tests. [AC-1.1, AC-1.2, AC-1.3, AC-1.4]
2. **`scripts/tests/test_gen_codex_agent_tomls.py`** — 10 tests driving the real CLI on temp dirs; manifest read without PyYAML. [AC-1.1, AC-1.2, AC-1.3, AC-1.4]
3. **`scripts/eval.sh`** — `codex-tomls` in `CHECKS` after `drift-format`; `check_codex_tomls` adds one finding per `reason:` line (remediation names the generator), plus findings for a missing helper, an unexpected exit, or a fail without reasons; the summary is a note. [AC-1.5]
4. **`scripts/tests/test_eval_codex_tomls.sh`** (new) — 6 temp-copy cases: fresh pass, stale, two problems, unmapped plus orphan, missing helper, registration. [AC-1.5]
5. **`codex/agents/*.toml`** — regenerated via the CLI; 6 of 8 changed in body text only. [AC-1.5]

### Verification

- 25 story tests pass on Python 3.9; bash test 6/6; `--check` reports `0 stale, 0 missing, 0 orphan, 0 unmapped`; `eval.sh --check=codex-tomls` passes.
- Gate 3: `review-agent` (routed by boundary crossings) PASS, 3 Minor findings; the eval-coverage and task-text findings were fixed, the empty `--agents-dir` write-mode no-op is test-only and left as is.
- Drift: DEV-001..DEV-004, all Small.
