# Story 1: Contract Doc and ADR-029 Amendment

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer and the agents that run Writ commands in installed projects
**I want to** one written agent CLI contract with a classification row for every shipped script, and a dated amendment to ADR-029 that records the rules that changed
**So that** the contract test in Story 3 has a fixed table to check against, and agents know which output shape each script prints

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given the repo after this story, when a reader opens `.writ/docs/agent-cli-contract.md`, then it has headed sections for Scope, Data shape, Check shape, Usage errors, Never spawn or wait unbounded, Network, State, Runtime, Adding a script, and Classification `[AC-1.1]`
- [ ] Given the Classification table, when a reader parses its rows, then every `*.py` and `*.sh` that `is_shippable_script` in `scripts/install.sh` accepts appears exactly once, except the six dev-only scripts, which appear only in a note below the table. Each row has Shape `data` or `check`, and Allowances empty or drawn from `network: opt-in` and `bounded-wait` `[AC-1.2]`
- [ ] Given the Classification table, when a reader checks the allowances, then `jev-judge.py` and `app-verify.py` each carry `network: opt-in, bounded-wait`, and no other row carries `network: opt-in` `[AC-1.3]`
- [ ] Given ADR-029 section "The agent CLI contract", when a reader opens it, then a dated block `*Amended 2026-10-12 by [2026-10-12-agent-cli-contract]*` follows rule 7 and records the two shapes, `error` accepted beside `blocker`, the usage-error rule matching pstack `orch`, the bounded-wait clarification, and the dev-only exclusion; and the text of rules 1 through 7 is byte-identical to the pre-change file `[AC-1.4]`
- [ ] Given `scripts/tests/test_agent_cli_contract_doc.py`, when `uv run --python 3.9 pytest scripts/tests/test_agent_cli_contract_doc.py` runs, then it fails before the doc and amendment exist, and passes after this story. Each test names its AC ID in its docstring `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Write failing doc-content tests in `scripts/tests/test_agent_cli_contract_doc.py` for the required sections, the table rules, the allowances, and the ADR amendment. Run them and confirm they fail `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`
- [ ] 1.2 Write the nine prose sections of `.writ/docs/agent-cli-contract.md` from the spec's business rules. State each rule in the doc's own words; do not copy spec text `[AC-1.1]`
- [ ] 1.3 Write the `## Classification` table with the rows and rulings in Notes, using columns `Script | Shape | Allowances | Callers`. Add the six-script note below the table `[AC-1.2, AC-1.3]`
- [ ] 1.4 Add the dated amendment to `.writ/decision-records/adr-029-agent-cli-contract.md` after rule 7 of "The agent CLI contract", using targeted edits only. Do not rewrite rules 1 through 7 `[AC-1.4]`
- [ ] 1.5 Check whether `/new-skill` already discusses adding scripts. If it does, add a one-line pointer to the contract doc. If it does not, make no command edit `[AC-1.1]`
- [ ] 1.6 Verify the criteria: run the doc-content tests on Python 3.9, run `uv run pytest`, run the bash tests, run `bash scripts/eval.sh` outside the sandbox, and run `bash scripts/install.sh --dry-run` into a temp project to confirm the doc is listed `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

**Scope boundary.** This story writes the doc, the ADR amendment, the test file, and at most one line in `/new-skill`. It does not change `is_shippable_script` (Story 2), write the contract test (Story 3), or edit any script (Story 4).

**Ordering.** Story 3 reads this table as its source of truth. Story 3's `SHIPPED` set must filter to `*.py` and `*.sh`. `is_shippable_script` also accepts `jev-thresholds.json`, a data file with no `--help`, so a set built from the raw function output would fail `test_table_complete`. The doc's Scope section states this rule.

**Classification rulings.** Preliminary shapes come from `sub-specs/technical-spec.md` → "Current State (audit, 2026-10-12)". Confirmed at authoring time:

- **Data (15), kept as preliminary:** ac-trace, archive-sweep, build-smoke, exit-criteria, phase-state, quality-config-audit, recommend-state, resolve-spec-reference, roadmap-sync, spec-deps, spec-status, story-context, story-deps, supersession-writeback, test-integrity. Each prints JSON through `json.dumps` in its output path. Per-script `--help` and bad-flag behavior is not yet run; Story 3 runs it.
- **Check (9), kept as preliminary:** arch-check, docs-check, drift-format, goal-emit, review-override, review-panel, spec-analyze, verdict-provenance, jev-judge. Each prints the verdict word first and a summary last. Confirm `verdict-provenance` line 1 during the table pass; its print order was not fully read.
- **Ruled (10):**

| Script | Ruling | Reason | Gap for Story 4 |
|---|---|---|---|
| `app-verify.py` | check; `network: opt-in`, `bounded-wait` | Verdict sits in the summary line `app-verify: <verdict> …`. `--json` prints the summary before the JSON object. | Requires the rule 4 wording change below |
| `arch-lint.py` | check | `detect` prints the verdict first. `main` returns 0 even when unverifiable. | Exit 2 on `unverifiable` |
| `boundary-map.py` | data | `compute` prints JSON. `crossings` prints text lines. | `crossings` emits JSON; update `commands/implement-story.md` |
| `change-surface.py` | data | `classify` prints one class word. | Emit `{"class": …}`; update `commands/implement-story.md` |
| `gen-codex-agent-tomls.py` | check | `--check` prints the verdict first, `reason:` lines, summary, exit 0 or 1. Write mode prints `wrote` lines. | Write mode prints a verdict first; update `adapters/codex.md` and `commands/refresh-command.md` if output text changes |
| `revert-resolve.py` | data | Default output is text. `--json` opts in. | JSON default, `--pretty` for text; update `commands/revert.md` (spec Story 4) |
| `knowledge-consolidate.py` | data | Default output is markdown. `--json` opts in. | JSON default, `--pretty` for the report; update `commands/knowledge.md` (spec Story 4) |
| `gen-skill.sh` | check | `--check` exits 0 or 1. Default mode writes `SKILL.md`. | Smoke test runs `--check` only |
| `lint-skill.sh` | check | Exit 0 pass, 2 usage (per header). Line 1 verdict not verified. | Confirm in Story 3 smoke |
| `check-agent-parity.sh` | check | Prints warning lines and always exits 0. No verdict line. | Verdict first; exit 1 on drift; update `/refresh-command` warning-only text |

- **Allowances.** `network: opt-in`: `jev-judge.py` (ADR-027 double opt-in), `app-verify.py` (local readiness probe). `bounded-wait`: `jev-judge.py` (retry loop, bounded by `MAX_ATTEMPTS`), `app-verify.py` (readiness poll, bounded by the recipe's ready timeout; confirm the `while True` near line 637).
- **`test-integrity.py` is not a bounded wait.** Its `while True` near line 320 walks parent folders. Rule 7 does not cover it. Leave it unmarked and let Story 4 rewrite it as a bounded `for` loop. Do not add `bounded-wait` to hide it.
- **Network scan list.** The doc's Network section names the modules the scan flags: `urllib.request`, `urllib.error`, `http.client`, `socket`, `requests`. `urllib.parse` is exempt, because `recommend-state.py` imports it for URL splitting and makes no request.
- **Dev-only scripts.** Omit `pipeline-baseline.py`, `measure-invocation.py`, `harness-cost.py`, `lean-decision.py`, `prune-ledger.py`, and `spawn-cap.py` from the table. The note under the table names them and says Story 2 removes them from the shipped set.
- **Callers column.** Every shipped script had at least one caller at authoring time, found with `grep -rl <name>` over `commands/`, `agents/`, `skills/`, `adapters/`, and `.writ/docs/`. Rerun the grep for each row. Keep the column non-empty.
- **ADR rule 4 deviation.** Spec Business Rule 4 says line 1 is exactly `pass`, `fail`, or `unverifiable`. Accepting `app-verify`'s `app-verify: <verdict>` line requires the maintainer to approve a wording change to rule 4 in the doc. The alternative is changing `app-verify.py` output in Story 4. Raise this with the maintainer before writing the Check shape section.
- **Working tree.** The dispatch says the tree has unrelated uncommitted edits (`commands/retro.md`, ADR-025, `SKILL.md`). The session snapshot shows only the untracked spec folder. Run `git status` before starting. Do not touch files outside the list above.
- **Shipping.** `.writ/docs/` ships to every installed project. Write the doc for an agent reader in another project. Do not refer to dev-only scripts as available.
- **Test file name.** Use `test_agent_cli_contract_doc.py` here. Story 3 owns `test_agent_cli_contract.py`. Do not reuse that name.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** spec.md → "Specification Contract" → Business Rules 2 (table format), 3 (data shape), 4 (check shape), 5 (usage errors), 7 (bounded waits), 8 (network opt-in)
- **Detailed requirements:** spec.md → "Detailed Requirements" → "Story 1: Contract doc and ADR amendment"
- **Expanded rules:** spec.md → "Business Rules (Expanded)" → Business Rules 2 and 10, for the table format and the strict-debt rule that Story 3 enforces
- **Experience:** spec.md → "Experience Design" → "State Catalog" → "Bad arguments" row, for the usage-error behavior the doc must state
- **Contract section list:** sub-specs/technical-spec.md → "Contract Doc (Story 1)" → Sections 1 through 10, and the Table columns paragraph
- **Amendment content:** sub-specs/technical-spec.md → "ADR-029 Amendment (Story 1)"
- **Audit and preliminary shapes:** sub-specs/technical-spec.md → "Current State (audit, 2026-10-12)"
- **ADR text to amend:** `.writ/decision-records/adr-029-agent-cli-contract.md` → "The agent CLI contract", rules 1 through 7. Implementation Notes step 4 names the contract doc
- **Out of scope for this story:** sub-specs/technical-spec.md → "Ship Filter (Story 2)", "Contract Test (Story 3)", "Conformance Fixes (Story 4)"
