# `test-integrity.py authenticity` Flags Every Bash Test as `test_imports_no_source`

> **Type:** Improvement
> **Priority:** Medium
> **Effort:** Small
> **Created:** 2026-09-03
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`python3 scripts/test-integrity.py authenticity --tests scripts/tests/<any>.sh` returns
`verdict: fail` with the blocking code `test_imports_no_source` for **every** bash test in
this repository — new or pre-existing — because its "whole-file module-specifier
extraction" has no notion of a shell script invoking a project script by path
(`bash "$REPO/scripts/lint-skill.sh"`). The finding's own claim ("cannot fail when the code
it claims to test changes") is empirically false for these files: mutation checks against
`scripts/tests/test_lint_model_tier.sh` (three behavioral mutations of `lint-skill.sh`)
were caught 3/3.

## Current State

- `scripts/test-integrity.py` `authenticity` treats `.sh` files as in-scope (`inspected.files: 1`,
  `out_of_scope: 0`) and then reports zero module specifiers — a `fail`, not an
  `unverifiable`.
- `.writ/docs/quality-signal-classification.md`'s stack support matrix does not list shell as a
  supported stack; by the doc's own rule an unsupported surface should classify as
  `unverifiable` with reason `unsupported_stack`, as the sibling `coverage` subcommand already
  does for the same file.
- `/implement-story` Gate 4 treats `test_imports_no_source` as blocking → BLOCKED escalation.
  On a bash-only story (Writ's own Stories 1, 2, 5 of `2026-09-03-model-delegation`) this
  fires by construction.

## Expected Outcome

- `authenticity` classifies test files whose language has no module-specifier concept
  (`.sh`, and any other unsupported suffix) as `out_of_scope` or `unverifiable`
  (`unsupported_stack`), never `fail`.
- Optionally: a shell-aware heuristic — a test that references a project path under
  `scripts/` via `bash`, `source`, or `$VAR` invocation counts as importing project source.
- A unit case in `scripts/tests/test_test_integrity.py` pinning the new classification.

## Relevant Files

- `scripts/test-integrity.py` — `authenticity` loop (~lines 620–676), `imports_project_source`
- `.writ/docs/quality-signal-classification.md` — stack support matrix and the unsupported-stack rule
- `commands/implement-story.md` Gate 4 — the consumer that turns this verdict into a block

## Origin

Surfaced during `/implement-spec 2026-09-03-model-delegation` Story 1 Gate 4. The story was
carried to Completed on the mutation evidence above with this issue filed as the durable
record — the orchestrator's judgment, recorded here rather than made quietly.

**Second occurrence — Story 3 of the same spec, Python this time.**
`scripts/tests/test_gen_codex_agent_tomls.py` loads `scripts/gen-codex-agent-tomls.py` via
`importlib.util.spec_from_file_location` because the module name contains a hyphen — the
same recipe `scripts/tests/test_ac_trace.py` already uses. The whole-file specifier extractor
finds no `import`/`from` statement naming project source and returns
`test_imports_no_source` / `blocking`. The review agent ran the same test file against
`git show HEAD:scripts/gen-codex-agent-tomls.py` and got 6 failures, so the file demonstrably
fails when its subject changes. Add to Expected Outcome: treat a `spec_from_file_location(...,
<path under project>)` call (or any `Path(__file__)...` that resolves inside the project) as
a project-source import. Every hyphenated script under `scripts/` can only be tested this way.

**Third occurrence — Story 1 of `2026-09-09-phase11-stage4-goal-emit`.**
`scripts/tests/test_goal_emit.py` drives `scripts/goal-emit.py` via subprocess CLI plus
`importlib.util.spec_from_file_location` (hyphenated filename). Coverage re-derivation
passed at 99.4%. Authenticity still returned `test_imports_no_source` / `blocking`.
Carried to Completed on that coverage evidence; this is the same importlib-by-path
gap already named above.

**2026-09-26 (arch-lint-and-follow-ups):** the same verdict hits Python tests that only read markdown. `test_issue_closure_wiring.py` pins command prose and resolves no executed source, so it reads as `test_imports_no_source` although markdown is Writ's product source. Bash tests `test_eval_codex_tomls.sh` and `test_eval_drift_format.sh` were flagged the same way.

## Second case: Python repro of a data file (2026-11-06)

- `scripts/tests/test_gate_evidence_drift_citation_repro.py` (lean-story-pipeline Story 1) reads `commands/implement-story.md` and imports no project module. `authenticity` reported `test_imports_no_source` (blocking).
- The claim is false: the test failed at `713af07` and passes after the fix in `31d8c29`.
- ADR-032 requires evidence repros committed unchanged, so the two gates conflict for any repro that tests a data or markdown file. The maintainer recorded it as a false positive (`.writ/specs/2026-11-06-lean-story-pipeline/drift-log.md` DEV-005).
- `SPECIFIER_PATTERNS` match only quoted specifiers (`from '…'`, `import('…')`, `require('…')`), so Python `import x` / `from x import y` lines are never seen either.


## Runner excludes shell tests (2026-11-06)

- `scripts/story-gate.py` (lean-story-pipeline Story 3) now passes `authenticity` only test files with a suffix it can read: `.py` and the Node / TypeScript suffixes. Shell tests (`.sh`, `.bash`, `.zsh`) and other suffixes stay out of its input.
- Why: the runner passes every changed test file, and the check fails every shell test by construction. Shell is not in the stack matrix of `.writ/docs/quality-signal-classification.md`. Story 3's own post-review failed on `scripts/tests/test_jev_shadow_hooks.sh`.
- The check's reason line counts the exclusions (`skipped N shell test(s): unsupported_stack`). When every changed test is excluded, the check records `skip` with that reason.
- This works around the issue in the runner. The checker itself still flags a shell test passed to it directly, and the Python cases above (importlib by path, markdown-reading tests) are still open.

## Runner excludes ADR-032 evidence repros (2026-11-07)

- `scripts/story-gate.py` (lean-story-pipeline, during Story 4) now leaves every repro path the evidence manifest (`<state-dir>/evidence-<story-stem>.json`, `evidence-manifest-v1`) records out of the `--tests` list it passes to `review-override.py check` and to `test-integrity.py authenticity`. The manifest counts only when `review-override.py`'s `_load_manifest` would accept it: every entry a dict with a `sha256` string, a repo-relative `path`, and a `content` string when present. Otherwise (missing, unreadable, or one bad entry) the list is unchanged, since `evidence --prior` then reads `bad_manifest` and guards no repro. `scripts/tests/test_story_gate.py` pins the two readers to the same result.
- Why: ADR-032 requires the coder to commit a Gate 3 repro unchanged, and a repro often reads a command or data file instead of importing source. `authenticity` then reports `test_imports_no_source` (blocking), through `check` as Gate 3 row 2 (`restart: gate1`) and through Gate 4 directly: a loop the coder cannot fix. Story 4's post-review hit row 2 on `scripts/tests/test_ship_suite_claim_repro.py`; Story 3 hit the Gate 4 form on `test_story_gate_respawn_repro.py`; Story 1 on `test_gate_evidence_drift_citation_repro.py`.
- Both checks carry the reason `skipped N evidence repro(s): adr032_repro`. When only repros are left, `authenticity` records `skip` with that reason; `check` still runs without `--tests`, because its ac-trace part applies regardless.
- The repro's own integrity is covered elsewhere: `review-override.py evidence --prior` checks each recorded repro is present, unchanged (SHA-256), and passing.
- Residual: anyone who can write `.writ/state/` can forge a well-formed manifest with a correct hash for an ordinary test and so exempt it from authenticity; `--prior` would accept it. The runner does not compare the manifest's repros with the findings Gate 3 confirmed.
- The shell and unsupported-stack exclusion now applies to `check --tests` as well (it feeds only check's authenticity step), so a changed `.sh` test no longer fails Gate 3 row 2 there.
- Like the shell exclusion, this works around the checker in the runner; `test-integrity.py` itself still flags such a file passed to it directly.

## Checker resolves Python doc-pin tests (2026-11-07)

- `scripts/test-integrity.py authenticity` (lean-story-pipeline Story 5) now credits a Python test that reads a project file it names by path: a string like `"commands/implement-story.md"` or a chain like `ROOT / "adapters" / "claude-code.md"`, resolving to an existing file outside test directories and `.writ/state/`, in a file that calls `read_text`, `read_bytes` or `open(`.
- `from pkg import mod` now resolves `pkg/mod.py` when `pkg/` has no `__init__.py`. Plain `import x` of a project module was already resolved; the 2026-11-06 note above was wrong on that point.
- A test that imports a test helper counts when the helper itself imports, runs or reads project source (cycle-safe). This clears `test_story_gate_respawn_repro.py`, which drives `story-gate.py` through `test_story_gate.Repo`.
- Measured on `scripts/tests/*.py` (100 files): 20 flagged before, 2 after. The 18 cleared are doc-pin tests and repros, including `test_claude_code_adapter_claims.py`, `test_gate_evidence_drift_citation_repro.py`, `test_ship_suite_claim_repro.py` and `test_issue_closure_wiring.py`. The 2 still flagged (`test_edit_spec_ac_stability_fixtures.py`, `test_recommend_state_ac_tag_compat.py`) copy their subject inline and touch no project file: true positives.
- Resolved here: the Python cases in this issue (importlib by path, earlier; markdown-reading tests, now).
- Still open: shell. The checker still flags a `.sh` / `.bash` test passed to it directly; only `story-gate.py` filters shell tests out. The runner's ADR-032 repro exclusion is now redundant for Python repros that read or run source, but still needed for any repro that does neither.
