# ac-trace counts AC tokens inside test fixtures as citations

> **Type:** Bug
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-09-26
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`scripts/ac-trace.py` counts `AC-N.M` tokens in fixture stories and test-data strings as real test citations. As a result it reports false `dangling_reference` findings, and it can hide a real `untested_criterion` in any later spec whose IDs happen to match a fixture's.

## Current State

- `CITATION_SCAN_SKIP` exempts only `scripts/tests/test_ac_trace.py`.
- On `2026-09-25-jev-judgment-pilot`, `ac-trace.py check --repo .` reports 3 blocking `dangling_reference` findings, and none of them is a real citation:
  - `scripts/tests/test_jev_judge.py:2002`: `AC-1.6`, a parser test string.
  - `scripts/tests/fixtures/spec-analyze/synthetic-clean-api-rate-limit/...:15`: `AC-4.5`, a fixture story's own criterion.
  - `scripts/tests/fixtures/spec-analyze/synthetic-clean-email-verification/...:15`: `AC-5.6`, same.
- `scripts/tests/fixtures/spec-analyze/` now holds 24 fixture stories full of `[AC-N.M]` tags. A future spec that defines, say, `AC-4.5` would have that criterion counted as "tested" by a fixture file.

## Expected Outcome

- Nothing under `scripts/tests/fixtures/` is ever counted as a citation.
- Test files whose AC tokens are parser test data (`test_jev_judge.py`, `test_jev_judge_spec_findings.py`, `test_jev_calibrate.py`) are skipped explicitly, or those tokens are marked so the scanner ignores them.
- A regression test covers the prefix skip.

## Relevant Files

- `scripts/ac-trace.py` - `CITATION_SCAN_SKIP`, the citation walk
- `.writ/docs/acceptance-criteria-ids.md` - Scan Bounds section to update
- `scripts/tests/test_ac_trace.py` - add the fixture-prefix case
