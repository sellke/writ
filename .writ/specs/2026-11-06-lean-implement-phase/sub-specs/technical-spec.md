# Technical Spec: Lean Implement Phase

> Spec: [../spec.md](../spec.md)
> Business rules are numbered in `spec.md` → Specification Contract → 📋 Business Rules. This file cites them by number.

## Components

| File | Change | Story |
|---|---|---|
| `scripts/phase-state.py` `init` | `--uat` flag → top-level `uatRequested` (Business Rule 1) | 1 |
| `scripts/exit-criteria.py` `_predicate_phase_c2`, criterion text constant | Check only when `uatRequested` is true; missing key reads true (Business Rule 2) | 1 |
| `commands/implement-phase.md` frontmatter c2, Invocation, Steps 1.3, 2.3, 3.2 item 6, 4.2, Integration table, Completion | `--uat`, resume signal, report (Business Rules 1–3) | 1 |
| `.writ/docs/exit-criteria-classification.md`, `.writ/docs/phase-execution-state-format.md` | c2 condition; `uatRequested` field | 1 |
| `scripts/eval.sh` (c2 literal, line ~3560) | New c2 text | 1 |
| `README.md`, `SKILL.md` | UAT opt-in wording | 1 |
| `scripts/tests/test_exit_criteria.py`, `scripts/tests/test_phase_state.py` | c2 cases with and without `uatRequested`; `init --uat` | 1 |
| `scripts/phase-state.py` `health` | `not_requested` for omitted sources (Business Rule 4) | 2 |
| `commands/implement-phase.md` Step 4.1c, `commands/status.md` | Pass only produced sources | 2 |
| `commands/implement-phase.md` Step 1.4 | Removed (Business Rule 5) | 2 |
| `.writ/docs/agent-cli-contract.md` (`goal-emit.py` row), `scripts/tests/test_goal_emit_command_hooks.sh`, `scripts/tests/test_goal_emit.py` | Drop implement-phase as a consumer | 2 |
| `commands/_lane-brief.md` | New shipped lane brief template (Business Rule 6) | 3 |
| `commands/implement-phase.md` Step 3.2, `commands/implement-spec.md` § Phase-Orchestrated Lane Mode | Lane writes result file; orchestrator validates the file | 3 |
| `scripts/phase-state.py` `create-lane` | Records `resultPath` per spec | 3 |
| `commands/implement-phase.md` whole file | Compress to ≤ 240 lines (Business Rule 7) | 4 |
| `.writ/docs/phase-execution-state-format.md` | Receives the moved rationale | 4 |
| `scripts/tests/test_governor_enforcement.py` | Dated `KNOWN_OVER_BUDGET` entries for byte changes | 1–4 |
| Generated trees (`claude-code/`, `cursor/plugin/`, `codex/`) | `python3 scripts/gen-platform-trees.py` | 1–4 |

## c2 predicate (Story 1)

```
uat_requested = state.get("uatRequested", True)   # pre-change state files promised plans
if not uat_requested:
    return met, evidence="UAT not requested"
# existing presence / stub / ordering / evidence-half checks, unchanged
```

Criterion text, identical in all four places:

> when UAT plans were requested, each merged spec folder contains a populated uat-plan.md generated after that spec was implemented

`check-uat --spec DIR` is unchanged. It checks one spec's plan on demand, and `/create-uat-plan` still uses it.

## Resume signal (Story 1)

Step 1.3 order:

1. Phase state (`--resume`): `integrated`, `quarantined`, `skipped_blocked`, `closed_not_implemented` are terminal, so skip.
2. Story statuses: every story `Completed ✅` → skip implementation.
3. Under `uatRequested`, an integrated spec with no populated plan still gets `/create-uat-plan`.

## `health` sources (Story 2)

| Flag passed | File exists | Source value | Effect |
|---|---|---|---|
| no | — | `not_requested` | none |
| yes | no | `missing` | Warning |
| yes | yes | `pass` / `fail` (eval, verification) or `none` / `material` (drift) | as today |

`--drift` follows the same rule; today an omitted `--drift` is `missing`. Step 4.1c passes `--drift` for each merged spec's drift log that exists and `--eval` only when the phase ran `eval.sh`. It does not pass `--verification`. `--verification` stays in the CLI for `/status` and other callers.

## Lane result file (Story 3)

- `create-lane` computes `resultPath = <repo>/.writ/state/lane-result-<phase>-<spec>.json` and stores it under `specs.{id}.resultPath`. The path is absolute and in the main checkout, not the worktree.
- `commands/_lane-brief.md` holds the brief with placeholders: `{spec_path}`, `{phase_state}`, `{lane_branch}`, `{worktree}`, `{mode}`, `{result_path}`, `{answer_sources}`.
- The lane writes `phase-spec-result-v1` JSON to `{result_path}` as its last action, then replies with the path.
- The orchestrator runs `validate-result --input {result_path}`. The supervisor gets the file path in place of the verbatim report.
- A missing or unparseable file → resume the lane agent once to write it → still missing → `classify` as `transient`.

`commands/_lane-brief.md` is underscore-prefixed like `_preamble.md`. Confirm `install.sh` and `gen-platform-trees.py` ship it. If either skips underscore files other than `_preamble.md`, add it to their lists in this story.

## Pinned literals (Story 4)

`eval.sh` requires these strings in `commands/implement-phase.md`. Story 4 keeps each one:

`Valid explicit \`Dependencies\` graph` · `inference remains advisory` · `stop before the confirmation gate` · `fresh subagent` · `writ/phase/{phase-id}/{spec-id}` · `phase-spec-result-v1` · `only a verified` · `User Challenge` · `ordinary failures use their normal` · `writ/quarantine/{spec-id}` · `one transient retry` · `skipped_blocked` · `does not guess or mutate git` · `evidence-bound` · `no qualifying candidate` · `production health` · `closed_not_implemented` · `Closed by decision` · `close-spec` · the c1 and c2 criterion text

Rebuild this list with `grep -n 'require_literal "$implement_phase"' scripts/eval.sh` before cutting. Also check `scripts/eval-*.py` and `scripts/tests/` for `implement-phase.md` pins (`grep -rln implement-phase scripts/tests scripts/eval*.py`).

## Compression targets (Story 4)

| Section | Now | Target |
|---|---|---|
| Step 1.2b | 5 method steps + proposal + approval | proposal shape + Doubt Rule line + create-spec seeding + close-spec line |
| Step 3.1 phase-branch note | paragraph | one line: name it `phase/{N}-{slug}`, never under `writ/phase/` |
| Step 3.2 iteration bound | paragraph | `record-halt` line; no quarantine on exhaustion |
| Step 3.3 + mid-run closure | prose | table: event → subcommand → effect |
| Initiative, Question Policy, inherited-answer rule, Step 4.3 | four statements | one Question Policy section |
| Step 4.2 checker branches | three bullets with rationale | three one-line bullets |
| Rationale removed | — | `phase-execution-state-format.md` → "Why" subsections |

## Error & Rescue Map

| Where | Failure | Handling |
|---|---|---|
| c2 change (Story 1) | Old state file lacks `uatRequested` | Read as `true`; verdict on finished runs unchanged |
| c2 change (Story 1) | One of the four text copies missed | `eval.sh` c2 literal check fails; fix before commit |
| Resume (Story 1) | Spec has `uat-plan.md` but incomplete stories | Not skipped; inventory reads stories |
| `health` (Story 2) | A caller relied on omitted `--drift` meaning `missing` | `/status` passes its drift log explicitly; test covers both |
| Goal emit removal (Story 2) | A test or eval still asserts implement-phase emit | Update the assertion to `/create-goal` only |
| Lane result (Story 3) | Lane never writes the file | Resume once; then `transient` |
| Lane result (Story 3) | Template not shipped by `install.sh` / plugin tree | Add to the ship lists; `test_eval_shipped_refs.py` catches the dangling reference |
| Compression (Story 4) | A pinned literal is cut | `eval.sh` fails; restore the literal |
| Compression (Story 4) | Behavior silently dropped | Phase tests and eval checks pass unchanged; any edit to a test assertion in this story is a review flag |

## Shadow Paths

- **Happy path:** no `--uat`; specs merge; c2 `met` (`UAT not requested`).
- **Nil input:** state file without `uatRequested` → treated as requested.
- **Empty input:** phase with no merged specs → c2 `met` (`no merged specs`), as today.
- **Upstream error:** `/create-uat-plan` fails under `--uat` → c2 `unmet` naming the spec; report status `PARTIALLY COMPLETE` or `IMPLEMENTED — pending human validation` per the checker.

## Interaction Edge Cases

- `--uat --quick`: both pass through; `--quick` goes to `/implement-spec`, and `--uat` stays at the phase level.
- `--all --uat`: `uatRequested` is set per phase state file.
- `--resume --uat` on a run started without it: `--uat` sets `uatRequested: true` from then on and generates plans for integrated specs that lack one. Record the change in state.
