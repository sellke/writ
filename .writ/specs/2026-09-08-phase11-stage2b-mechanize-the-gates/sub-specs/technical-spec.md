# Technical Spec — Phase 11 Stage 2b: Mechanize the Gates

> Source: [`../spec.md`](../spec.md) · Stories: [`../user-stories/`](../user-stories/)

Shared contract for every new script. Python 3.9 stdlib. Exit 0 = ran, no blocking verdict; exit 1 = `fail` (or a well-formed map/class that the caller treats as data — see §4); exit 2 = usage. Verdict vocabulary is `pipeline-baseline.py` `GATE_SCRIPT_VERDICTS`: `pass` / `fail` / `unverifiable`. One verdict line, then optional `reason: <code>` lines, then a summary line last.

`eval.sh` registers one check per script; findings via `add_finding`, the summary via `add_note`. `--prose-only-blocking` is **not** passed until Story 5.

## 1. `scripts/review-override.py` (Story 1)

```
review-override.py check --spec PATH --repo . [--story PATH] [--new-files FILE …] [--tests FILE …]
```

Calls `ac-trace.py check` and, when `--new-files` / `--tests` are present, `test-integrity.py coverage` / `authenticity`. Does not reimplement either parser.

| Verdict | When |
|---|---|
| `fail` | ac-trace blocking finding on the story, or test-integrity `coverage_below_threshold` / `coverage_regression` / `test_imports_no_source` |
| `unverifiable` | either helper `unverifiable`, or `--spec` / `--story` missing |
| `pass` | otherwise |

**FAIL-only override.** A script `fail` blocks (existing Gate 3 recode path). A script `pass` or `unverifiable` leaves the review-agent FAIL/PAUSE standing. Record the asymmetry in Story 1 What Was Built.

Frontmatter: set `gate3_review: script: scripts/review-override.py` in this story so provenance stays truthful.

## 2. `scripts/arch-check.py` (Story 2)

```
arch-check.py check --story PATH --repo . [--planned FILE … | --changed FILE …] [--boundary PATH]
```

`--planned` is Gate 0’s real moment (pre-implementation). `--changed` is replay / post-hoc. Neither → `unverifiable` (`reason: no_file_mode`). Both → exit 2.

| Verdict | When |
|---|---|
| `proceed` (printed as `pass` with `rederived: proceed`) | `story-deps.py validate` exits 0 and the file set is non-empty and ⊆ owned∪readable (or no `--boundary`) |
| `caution` (printed as `pass` with `rederived: caution`) | empty set, or a path in out-of-scope, or story-deps warning-class |
| `fail` | story-deps graph invalid (blocker) |
| `unverifiable` | no mode; or caller asks to classify ABORT (`reason: abort_is_llm_residual`) |

Never prints `abort`. Gate 0 ABORT path, including the ADR-024 floor→anchor re-run, is untouched.

On `caution`, inject `reason` into the coding-agent warnings. On `fail`, BLOCKED. On `proceed`, continue.

## 3. `scripts/docs-check.py` (Story 3)

```
docs-check.py check --repo . [--changed FILE …]
```

Public exports in `--changed` (or `git diff --name-only` against `HEAD^` when omitted and git can answer) vs documented symbols in README / CHANGELOG / detected docs framework / adjacent docstrings.

| Verdict | When |
|---|---|
| `pass` | every new or newly-public export is named in a readable doc |
| `fail` | a changed export has no matching documented symbol |
| `unverifiable` | no docs framework **and** no public exports in the set (Writ itself); or the set cannot be resolved |

Fixtures are a tiny app tree. This repo is the `unverifiable` case. Gate 5 `fail` → BLOCKED with agent `documentation-agent`.

## 4. `scripts/boundary-map.py` and `scripts/change-surface.py` (Story 4)

```
boundary-map.py compute --story PATH --repo . [--overlap PATH]
change-surface.py classify --changed FILE …
```

`boundary-map.py` prints JSON `{owned, readable, out_of_scope}` and writes nothing. Overlap absent → owned = paths named in the story, readable = [], out_of_scope = []. Exit 0 well-formed; 1 malformed story; 2 usage.

`change-surface.py` prints one of `style-only` / `single-component` / `cross-component` / `full-stack` from `skills/change-surface-classification/SKILL.md`, as path heuristics. Exit 0 with the class; 2 if no files.

Maps stay advisory. Gate 0.5 / 2.5 pass stdout to Gates 1 and 3 as today.

## 5. `scripts/drift-format.py` (Story 5)

```
drift-format.py check --story PATH [--drift-log PATH] [--review-output PATH]
```

| Verdict | When |
|---|---|
| `pass` | every `DEV-NNN` entry matches `.writ/docs/drift-report-format.md` required fields, and a Large-drift heading implies a PAUSE token in story or `--review-output` |
| `fail` | malformed entry, or Large-drift without PAUSE |
| `unverifiable` | no drift log and no Large-drift heading |

Does not decide accept / reject / modify-spec.

## 6. Frontmatter flip, provenance, visual-qa, runner (Story 5)

Final `gates:` block:

| id | source |
|---|---|
| `gate0_arch` | `scripts/arch-check.py` |
| `gate0_5_boundary` | `scripts/boundary-map.py` |
| `gate1_coding` | `prose-only` |
| `gate2_build` | `scripts/build-smoke.py` |
| `gate2_5_surface` | `scripts/change-surface.py` |
| `gate3_review` | `scripts/review-override.py` |
| `gate3_5_drift` | `scripts/drift-format.py` |
| `gate4_tests` | `scripts/test-integrity.py` |
| `gate4_5_visual` | `prose-only` |
| `gate5_docs` | `scripts/docs-check.py` |

`eval.sh` `check_verdict_provenance()` passes `--prose-only-blocking`. Drop 85/70 from `agents/visual-qa-agent.md`; keep PASS / SOFT PASS / FAIL.

`pipeline-baseline.py`: add `background_tasks_outstanding` (int, default 0) on new run records; extend `GATE_NAMES` and `REDERIVATION_KEYS` for future runs. Do not rewrite `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json` or `2026-09-07-claude-fable-5-1.json`. Ingest parses Claude Code stderr for `Background tasks still running after 600s`.

## 7. Replay (Story 5)

`scripts/tests/test_gate_replay.py` (or a `replay` subcommand) loads both committed baseline JSONs (16 records), invokes each new script in `--changed` / post-hoc mode from paths the record already carries, and prints agent-verdict vs re-derived. Disagreement is a note. `unverifiable` on historical `test_integrity: nothing_inspected` is the expected majority.

## 8. Tests

Every new script: pytest fixtures for `pass`, `fail`, and `unverifiable` (or the §4 exit-code equivalents). Bash eval-wiring tests following `scripts/tests/test_eval_verdict_provenance.sh`. Python 3.9 floor. No new gate numbers. `install.sh` already copies `scripts/*.py`.
