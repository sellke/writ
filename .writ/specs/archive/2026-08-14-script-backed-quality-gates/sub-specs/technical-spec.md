# Technical Spec — Script-Backed Quality Gates

> Parent: [`spec.md`](../spec.md)
> Consumed by: Stories 1–6

## Deliverables

| Artifact | Kind | Ships to target projects? | Story |
|---|---|---|---|
| `.writ/docs/quality-signal-classification.md` | classification doc | yes — `.writ/docs/*.md` is globbed by `append_manifest_writ_docs`, no manifest edit needed | 1 |
| `scripts/quality-config-audit.py` | read-only checker | yes — `is_shippable_script()` copies `scripts/*.py` | 2 |
| `scripts/test-integrity.py` | read-only checker | yes | 3 |
| `scripts/build-smoke.py` | executing checker | yes | 4 |
| `scripts/eval-quality-config-audit.py`, `-test-integrity.py`, `-build-smoke.py` | fixture asserters | **no** — the `eval-*` prefix is excluded | 2–4 |
| `scripts/tests/test_*.py` | unittest suites | no — `scripts/tests/` is never copied | 2–4 |

## CLI and Output Contract

All three checkers follow `scripts/ac-trace.py` exactly: `#!/usr/bin/env python3`, mode
`-rw-r--r--` (invoked as `python3 scripts/…`, never `./`), `from __future__ import
annotations`, argparse subparsers with `dest="action", required=True`, one JSON object to
stdout with `sort_keys=True`, and a module docstring naming the owning story, the read-only
property, the subcommand signature, and the exit-code contract.

```
python3 scripts/quality-config-audit.py check --project . [--baseline .writ/quality-baseline.md]
python3 scripts/test-integrity.py coverage     --project . [--report <coverage-file>] [--new-files <path>...]
python3 scripts/test-integrity.py authenticity --project . [--tests <path>...]
python3 scripts/build-smoke.py check --project . [--timeout 300]
```

**Schema strings** (each a single-line literal so `require_literal` can grep it):
`quality-config-audit-v1`, `test-integrity-v1`, `build-smoke-v1`.

**Exit codes**, matching `ac-trace.py`:

| Code | Meaning |
|---|---|
| 0 | ran correctly, no blocking findings (informational findings may be present) |
| 1 | ran correctly, at least one blocking finding |
| 2 | could not run correctly — usage error, missing project root, unreadable input |

`UNVERIFIABLE` is **not** exit 2. A check that ran and honestly could not decide exits 0 with
`verdict: "unverifiable"` and a populated `unverifiable` list. Exit 2 is reserved for the
checker itself being unable to operate.

**Envelope**, common to all three:

```json
{
  "schema": "<schema-string>",
  "verdict": "pass | fail | unverifiable",
  "project": "<path>",
  "findings": [ {"code": "...", "severity": "blocking|informational",
                 "file": "...", "line": 0, "detail": "...", "measured": "..."} ],
  "inspected": { "files": 0, "method": "...", "unparsed": [] },
  "unverifiable": [ {"code": "...", "reason": "..."} ]
}
```

`inspected` is mandatory and non-negotiable — it is the vacuous-pass guard from spec.md's
Business Rules. A report with `findings: []` and `inspected.files: 0` must be readable as
"nothing was examined", never as "everything is fine".

## Finding Vocabulary

Story 1 owns this table; Stories 2–4 transcribe it. `scripts/eval.sh` binds every code as a
`require_literal` against **both** the checker and the classification doc, exactly as
`check_ac_trace` does for its seven codes.

| Code | Checker | Severity | Fires when |
|---|---|---|---|
| `build_gate_disabled` | config-audit | blocking | typecheck or lint errors are configured not to fail the build |
| `coverage_threshold_absent` | config-audit | blocking | a coverage tool is configured with no enforced threshold |
| `coverage_scope_gap` | config-audit | informational | coverage collection excludes a source directory that contains shipped code |
| `tests_excluded_from_typecheck` | config-audit | informational | the typechecker's include/exclude omits the test tree |
| `duplicate_lockfile` | config-audit | informational | two package-manager lockfiles coexist |
| `could_not_parse` | config-audit | informational | a config file was found but not parseable; **downgrades every finding that file would have decided to `unverifiable`** |
| `coverage_below_threshold` | test-integrity | blocking | measured coverage on new files is under the declared bar |
| `coverage_regression` | test-integrity | blocking | coverage on a modified file decreased |
| `coverage_report_absent` | test-integrity | informational | no machine-readable coverage report was produced |
| `test_imports_no_source` | test-integrity | blocking | a test file resolves zero module specifiers into project source |
| `build_failed_source` | build-smoke | blocking | the build failed for a reason attributable to source |
| `build_failed_environment` | build-smoke | informational | the build failed on a missing dependency, service, or credential |
| `unsupported_stack` | all three | informational | no first-class or best-effort handler matched |

## Error & Rescue Map

Every fallible operation, what rescues it, whether a test covers it, and what the developer
sees. Written per `skills/error-rescue-mapping/SKILL.md`.

| Operation | Failure | RESCUED? | TEST? | USER SEES |
|---|---|---|---|---|
| Locate project root | path missing or not a directory | yes — `UsageError` | yes | exit 2, JSON `{"error": "..."}` naming the path |
| Read `package.json` | absent | yes — `unsupported_stack`, informational | yes | "no Node manifest found; stack unsupported" |
| Read `package.json` | present, invalid JSON | yes — `could_not_parse` | yes | "package.json found but unparseable"; dependent findings become `unverifiable` |
| Read `next.config.js` | executable JS, unparseable by stdlib | **by design** — regex heuristic, then `could_not_parse` if the heuristic cannot bound its answer | yes | "next.config.js inspected by pattern match" in `inspected.method`, or `unverifiable` |
| Read `tsconfig.json` | JSONC — comments, trailing commas | yes — comment/trailing-comma stripping pass, then `could_not_parse` | yes | as above |
| Read a lockfile | unreadable | yes — informational, does not block | yes | file named in `inspected.unparsed` |
| Read baseline | absent | yes — treated as empty; every finding is new | yes | "no baseline; all findings reported" |
| Read baseline | malformed | **no rescue** — exit 2 | yes | exit 2 naming the line; a silently-ignored baseline would either hide findings or flood them |
| Parse coverage report | absent | yes — `coverage_report_absent`, informational | yes | "no coverage report at `<path>`" |
| Parse coverage report | unknown format | yes — `unverifiable` | yes | "coverage report format unrecognized" |
| Extract module specifiers | multi-line import | **must not fail** — this is the defect the check exists to avoid | yes — pinned fixture | file is not flagged |
| Extract module specifiers | dynamic `await import()` | **must not fail** — same | yes — pinned fixture | file is not flagged |
| Extract module specifiers | file is not valid TS/JS | yes — `could_not_parse`, file excluded from the verdict | yes | file named in `inspected.unparsed` |
| Run build | non-zero exit, source-attributable | yes — `build_failed_source`, blocking | yes | compiler output excerpt, exit 1 |
| Run build | non-zero exit, environment-attributable | yes — `build_failed_environment`, informational | yes | "build could not run here: `<reason>`" |
| Run build | exceeds timeout | yes — `unverifiable`, never `fail` | yes | "build exceeded `<n>`s; treated as unverifiable" |
| Run build | build tool absent | yes — `unsupported_stack` | yes | "no recognized build command" |

## Shadow Paths

| Path | Expected behavior |
|---|---|
| **Happy** | verdict `pass`, `findings: []`, `inspected.files > 0` |
| **Nil input** | `--project` pointing at a nonexistent path → exit 2, never 0 |
| **Empty input** | a project with zero config files and zero tests → verdict `unverifiable`, `inspected.files: 0`. Never `pass` — this is the vacuous-pass guard's whole purpose |
| **Upstream error** | coverage tool crashed and wrote a truncated report → `unverifiable`, not `pass`, not `fail` |

## Interaction Edge Cases

| Case | Expected |
|---|---|
| Monorepo — several `package.json` files | inspect the package containing the story's changed files; record which in `inspected` |
| Both `bun.lock` and `pnpm-lock.yaml` present | `duplicate_lockfile`; use `packageManager` to decide which toolchain to invoke |
| `coverageThreshold` present but set to `0` | `coverage_threshold_absent` — a zero bar is an absent bar, and this is the obvious way to launder the check |
| A test file legitimately tests only types | flagged `test_imports_no_source`; waiver is the intended resolution, recorded in the baseline |
| Two runs, byte-identical input | byte-identical stdout — asserted, as in `ac-trace.py` |
| Build succeeds but emits warnings | `pass`; warnings are not this check's job |

## Determinism

All three checkers sort findings by `(file, line, code)` before emitting, and
`json.dumps(..., sort_keys=True)`. Both a direct-call and a CLI-subprocess repeat-run test
are required, mirroring `test_ac_trace.py`'s `test_two_runs_byte_identical` and
`test_cli_two_runs_stdout_byte_identical`.

## Eval Registration

Per `scripts/eval.sh`'s four-step recipe: add the name to `CHECKS`, define
`check_<name_with_underscores>()`, write `scripts/eval-<name>.py` emitting `PASS\t<name>` /
`FAIL\t<name>\t<reason>` TSV, write `scripts/tests/test_<name>.py`.

Two constraints that are easy to miss:

1. **CI runs `scripts/eval.sh` and `scripts/gen-skill.sh --check` only** — never
   `scripts/tests/`. A checker's CI protection comes entirely from its `eval-*.py` scenarios
   plus `require_literal` / `forbid_literal` bindings. Unit tests that exist only under
   `scripts/tests/` are developer-run and protect nothing in CI.
2. **Any spec-relative path referenced from `eval.sh` must go through `resolve_spec_path`** —
   completed specs move to `.writ/specs/archive/<name>/`, so a hardcoded active path breaks
   on archival.

Read-only discipline is asserted the way `check_ac_trace` asserts it — `forbid_literal` on
`os.remove`, `.write_text(`, and mutating git subcommands, against
`quality-config-audit.py` and `test-integrity.py`. `build-smoke.py` executes a build and so
is exempt from the subprocess ban, but must still never write a file itself.

## Gate Wiring

**Gate 2** (`commands/implement-story.md:183–191`) — extend the existing block, do not add a
gate. The Pipeline-table cell at line 60 (`| Gate 2 | Lint, Typecheck & Format | inline —
auto | — | — |`) gains the smoke step in its Name; `--quick`'s `**Keeps:** … Gate 2 (lint)`
at line 333 gains the same rewording. `agents/coding-agent.md:130,132,221` and its parity
carrier `claude-code/agents/writ-coder.md:60` describe Gate 2's remit and must stay accurate
— run `scripts/check-agent-parity.sh`.

**Gate 4** (`commands/implement-story.md:235–249`) — the checker runs *after* the testing
agent returns and re-derives the verdict from the coverage tool's own output. Where they
disagree, the checker wins and the story does not close, exactly as
`commands/implement-spec.md:261–265` says of `exit-criteria.py`. `agents/testing-agent.md`
gains a sentence recording that its `Coverage threshold met: [YES/NO]` field at `:133` is now
verified rather than trusted; the field itself stays, because Gate 4's BLOCKED handling and
`skills/subagent-result-completeness/SKILL.md:44` both key off the existing `TEST_RESULT:`
shape.

**What must not change:** the five literal-pinned routing-table rows at
`scripts/eval.sh:2232–2236`; `scripts/eval-leanness.py:257 GATE_AGENT_FILES` (no new agent is
spawned, so it stays as-is); the gate-numbering scheme; `agents/visual-qa-agent.md:5,149`;
`loop.nested` in `implement-story.md`'s frontmatter — neither addition introduces an
iteration cap, so `scripts/eval-loop-bounds.py:487–498` stays satisfied. If a cap is later
added, a `loop.nested` unit **and** a matching prose sentence must land together or that eval
emits `drift-*`.

**Opportunistic fix, unrelated but adjacent:** `skills/tdd-cycle/SKILL.md:10` reads *"Gate 2
spawns the coding agent"*. Gate 1 spawns the coding agent. Correct it in Story 5.

## Byte Budget

`commands/implement-story.md` is 354 lines / 25,695 bytes — already 735 bytes over
`COMMAND_BYTE_BUDGET` (24,960), which ADR-023 demoted to permanently non-blocking. The
400-line tripwire in `scripts/eval.sh:449` is a note, not a finding, and leaves 46 lines of
headroom. The real cost is `.writ/leanness-baseline.json`: growth past a recorded per-surface
value needs a dated schema-3 justification entry. Story 5 budgets that edit.
