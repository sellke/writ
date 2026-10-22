# Story 4: `--check`, Coverage, Tokens, and Eval Wiring

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** Writ maintainer who edits adapters, commands, or agents
**I want to** run one `--check` that names each stale, missing, or orphan generated file and each unmapped or vendor name, with the command that fixes it
**So that** CI tells me which file to regenerate and what to run, and the plugin spec can add a non-identity target that rewrites script invocations without copying prose

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given a committed tree, when `python3 scripts/gen-platform-trees.py --check` runs, then line 1 is `pass` and the summary reads `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`; and after a hand edit to `cursor/writ.mdc`, a deleted `claude-code/CLAUDE.md`, or an extra file under `claude-code/agents/`, line 1 is `fail` with `reason: stale cursor/writ.mdc`, `reason: missing claude-code/CLAUDE.md`, or `reason: orphan claude-code/agents/<name>.md`, and no file is written `[AC-4.1]`
- [ ] Given an adapter with no row for a neutral name, or a command with `` `TodoWrite` `` as a whole backticked token, when `coverage` runs, then it prints `reason: unmapped <name> in adapters/<x>.md` or `reason: vendor TodoWrite in commands/<file>.md:<line>` with the real line number; `--check` reports the same reasons; and `` `Read` `` in a command produces no reason `[AC-4.2]`
- [ ] Given `--target fixture --out-dir <dir>`, when the driver runs, then `<dir>/fixture/commands/*.md` and `<dir>/fixture/skills/<name>/SKILL.md` exist, every `python3 scripts/<name>` or `bash scripts/<name>` match reads `${PLUGIN_ROOT}/scripts/<name>` with the same interpreter, prose `scripts/` mentions are unchanged, every other byte matches the source, and `--target cursor`, `--target claude-code`, or `--target codex` writes no `commands/` or `skills/` output `[AC-4.3]`
- [ ] Given a temp copy of the tree with `cursor/writ.mdc` hand-edited, or with `` `TodoWrite` `` added to a command, when `check_platform_trees` runs in `scripts/eval.sh`, then each `reason:` line becomes a finding with the remedy `Run python3 scripts/gen-platform-trees.py, then commit the regenerated files.`, and a helper exit of 2 or higher, or a missing verdict line, counts as a run error `[AC-4.4]`
- [ ] Given `gen-platform-trees.py` in the dev-only case of `is_shippable_script` in `scripts/install.sh` and `scripts/update.sh`, when `is_shippable_script gen-platform-trees.py` runs in each, then both report not shippable, and the two function bodies are byte-identical `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Write the failing tests first. In `scripts/tests/test_gen_platform_trees.py` (Python 3.9 stdlib): `test_check_stale` covers stale, missing, and orphan cases; `test_vendor_hit` puts `` `TodoWrite` `` in a fixture command under `scripts/tests/fixtures/platform-trees/` and expects `reason: vendor TodoWrite in commands/<f>.md:<line>`, and expects no reason for `` `Read` ``; `test_fixture_target` expects the rewrite, untouched prose, and no identity-target `commands/` output; `test_dev_only` expects the driver to be non-shippable. Add `scripts/tests/test_eval_platform_trees.sh` in the style of `scripts/tests/test_eval_claude_md.sh`. Run both. Each must fail because the feature is missing, not on a syntax error `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [ ] 4.2 Add the `coverage` subcommand to `scripts/gen-platform-trees.py`, using Story 1's `parse_adapter` and `vocabulary`. Report `unmapped` for each neutral name missing from an adapter. Report `vendor` for each vendor-only name that appears as a whole backticked token in `commands/*.md`, `agents/*.md`, or `skills/*/SKILL.md`, with its line number. Define `ALLOWLIST = {"Read", "Write", "Bash"}` with one comment per entry. Output follows the check shape. Exit 0 or 1 `[AC-4.2]`
- [ ] 4.3 Add `--check` to the driver. Render `cursor/writ.mdc`, `claude-code/CLAUDE.md`, and `codex/AGENTS.md.template` in memory with the Story 2 and Story 3 render functions and compare the bytes with disk. Report `stale` (bytes differ), `missing` (no file), and `orphan` (a file under `claude-code/agents/` or `codex/agents/` that no generator produces). Run `gen-claude-agents.py --check` and `gen-codex-agent-tomls.py --check`; re-emit their reasons as `reason: <kind> <path>` for the driver's own paths and `reason: <gen>: <kind> <stem>` for folded sub-generator reasons (technical-spec.md § Driver CLI). A sub-generator exit of 2 or higher yields `fail` with `reason: <gen> --check exited <rc>`. Run `coverage` inside `--check`. Write nothing. Exit codes per `spec.md → ## Business Rules (Expanded)`, Rule 1 `[AC-4.1, AC-4.2]`
- [ ] 4.4 Add the `TARGETS` table with `cursor`, `claude-code`, and `codex` (`script_root: "scripts"`) and `fixture` (`script_root: "${PLUGIN_ROOT}/scripts"`, tests only). Use `TOKEN = re.compile(r"\b(python3|bash) scripts/([a-z0-9_-]+\.(?:py|sh))")`. Add `--target <name> --out-dir <dir>`. Identity targets write no `commands/` or `skills/`. Non-identity targets write `<out-dir>/<target>/commands/*.md` and `<out-dir>/<target>/skills/<name>/SKILL.md`, replacing each TOKEN match with the same interpreter and `<script_root>/<name>`. Use a callable replacement so `${PLUGIN_ROOT}` stays literal. Read and write bytes so every other byte survives `[AC-4.3]`
- [ ] 4.5 Add `check_platform_trees` to `scripts/eval.sh` after the `gen-claude-agents.py` and `gen-codex-agent-tomls.py` checks. Run `--check` only; it already runs coverage, and a second `coverage` run reports each vendor and unmapped hit twice. Count a helper exit of 2 or higher, or a missing verdict line, in `RUN_ERRORS`. Turn each `reason:` line into `add_finding "<path or name>" "<reason>" "Run python3 scripts/gen-platform-trees.py, then commit the regenerated files."`. Do not start this task until the `create-issue.md` decision in Notes is made. Then run `scripts/tests/test_eval_platform_trees.sh` and confirm both mutations produce findings `[AC-4.4]`
- [ ] 4.6 Add `gen-platform-trees.py` to the dev-only case of `is_shippable_script` in `scripts/install.sh` and `scripts/update.sh`. Keep the two functions byte-identical; compare the extracted function bodies with `cmp`. Follow `scripts/tests/test_install_update_dev_scripts.sh`. Confirm `test_dev_only` passes `[AC-4.5]`
- [ ] 4.7 Run the verification. `uv run --python 3.9 pytest`: all four new Python tests pass. `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`: no `FAIL` lines, including `test_eval_claude_md.sh` and `test_install_update_dev_scripts.sh`. `python3 scripts/gen-platform-trees.py --check` prints `pass` on the committed tree. `bash scripts/eval.sh`, run outside any sandbox, reports 0 findings. Record the eval findings count in `## What Was Built` `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

## Notes

- **Vendor hits on the current tree (resolved 2026-10-22).** `commands/create-issue.md` uses `` `Grep` `` and `` `Glob` `` as tool names. The spec now permits exactly this: task 4.2 rewrites each hit to its neutral name (`codebase_search`, `file_search`), one line each, and records them in What Was Built. Run `coverage` on the real tree first; any further hit gets the same treatment. The allowlist stays verbs-only.
- **Vendor list is incomplete.** A grep for a short list of vendor names found only the two hits above. Run `coverage` on the real tree in 4.2 to get the full list before 4.5.
- **Edge case to decide in 4.2.** `` `Grep("pattern")` `` is not a whole-token match under the rule as written, so it passes unflagged. Decide whether call-syntax tokens count, record the decision in the 4.2 commit, and add a test if they do.
- **Technical considerations** (`technical-spec.md → ## Driver CLI`, `## Tokens`, `## Eval Wiring`):
  - Stale means the bytes on disk differ from the in-memory render. Do not compare parsed content or ignore whitespace.
  - Orphan means a file under `claude-code/agents/` or `codex/agents/` that no generator produces.
  - Vendor scan matches whole backticked tokens only. A bare `TodoWrite` in prose is not a hit.
  - Fixture target: `test_fixture_target` compares bytes. Do not normalize line endings or trailing newlines.
  - Check shape: match the output contract in the `scripts/gen-claude-agents.py` docstring. Verdict on line 1, `reason:` lines next, summary last. Exit 0 for pass or unverifiable, 1 for fail, 2 for usage.
  - Parser reasons from Story 1 (`malformed`, `empty`, `section`) pass through unchanged. A missing heading is `unverifiable`, exit 0, nothing written.
- **Reason-line shape (settled 2026-10-22).** `reason: <kind> <path>` for the driver's own paths; `reason: <gen>: <kind> <stem>` for folded sub-generator reasons, per `technical-spec.md → ## Driver CLI`. The eval remedy reads the same for both.
- **Risks.**
  - A `--check` that passes on a stale tree because it compares the wrong thing. Guard: the stale case in 4.1 must fail before 4.3 is written and pass after.
  - False vendor hits on English verbs. Only `Read`, `Write`, and `Bash` are allowlisted. Each new entry needs a reason in the commit.
  - Breaking the existing generator checks' bash tests. Run the full bash loop after 4.5, not only the new test.
  - Python 3.9 floor: no 3.10+ syntax (`X | Y` annotations, `match`) and no 3.10+ stdlib.
  - Eval passes only when the committed generated files match a fresh render. That depends on the baseline write from Story 2 and Story 3.
- **Integration.**
  - Story 1: `parse_adapter` and `vocabulary`. Do not reparse the tables.
  - Story 2: the render functions for `cursor/writ.mdc` and `claude-code/CLAUDE.md`.
  - Story 3: `render_codex_template`.
  - Story 5 adds `scripts/tests/test_install_platform_trees.sh`. This story touches the install scripts only for the dev-only denylist.
  - The plugin spec adds real targets. Adding a target should take one `TARGETS` entry and no driver change.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Empty input, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 Driver CLI; Rule 3 Vocabulary and parity; Rule 4 Vendor-only names; Rule 11 Tokens; Rule 13 Eval)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (`Clean tree`, `Hand edit to a generated file`, `Capability used in a command with no row in one adapter`, `Vendor identifier in a shipped command`, `Adapter section heading missing`)
