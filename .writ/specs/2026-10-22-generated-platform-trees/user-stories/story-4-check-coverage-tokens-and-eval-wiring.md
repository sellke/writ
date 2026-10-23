# Story 4: `--check`, Coverage, Tokens, and Eval Wiring

> **Status:** Completed ✅ (2026-10-23)
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** Writ maintainer who edits adapters, commands, or agents
**I want to** run one `--check` that names each stale, missing, or orphan generated file and each unmapped or vendor name, with the command that fixes it
**So that** CI tells me which file to regenerate and what to run, and the plugin spec can add a non-identity target that rewrites script invocations without copying prose

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [x] Given a committed tree, when `python3 scripts/gen-platform-trees.py --check` runs, then line 1 is `pass` and the summary reads `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`; and after a hand edit to `cursor/writ.mdc`, a deleted `claude-code/CLAUDE.md`, or an extra file under `claude-code/agents/`, line 1 is `fail` with `reason: stale cursor/writ.mdc`, `reason: missing claude-code/CLAUDE.md`, or `reason: orphan claude-code/agents/<name>.md`, and no file is written `[AC-4.1]`
- [x] Given an adapter with no row for a neutral name, or a command with `` `TodoWrite` `` as a whole backticked token, when `coverage` runs, then it prints `reason: unmapped <name> in adapters/<x>.md` or `reason: vendor TodoWrite in commands/<file>.md:<line>` with the real line number; `--check` reports the same reasons; and `` `Read` `` in a command produces no reason `[AC-4.2]`
- [x] Given `--target fixture --out-dir <dir>`, when the driver runs, then `<dir>/fixture/commands/*.md` and `<dir>/fixture/skills/<name>/SKILL.md` exist, every `python3 scripts/<name>` or `bash scripts/<name>` match reads `${PLUGIN_ROOT}/scripts/<name>` with the same interpreter, prose `scripts/` mentions are unchanged, every other byte matches the source, and `--target cursor`, `--target claude-code`, or `--target codex` writes no `commands/` or `skills/` output `[AC-4.3]`
- [x] Given a temp copy of the tree with `cursor/writ.mdc` hand-edited, or with `` `TodoWrite` `` added to a command, when `check_platform_trees` runs in `scripts/eval.sh`, then each `reason:` line becomes a finding with the remedy `Run python3 scripts/gen-platform-trees.py, then commit the regenerated files.`, and a helper exit of 2 or higher, or a missing verdict line, counts as a run error `[AC-4.4]`
- [x] Given `gen-platform-trees.py` in the dev-only case of `is_shippable_script` in `scripts/install.sh` and `scripts/update.sh`, when `is_shippable_script gen-platform-trees.py` runs in each, then both report not shippable, and the two function bodies are byte-identical `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write the failing tests first. In `scripts/tests/test_gen_platform_trees.py` (Python 3.9 stdlib): `test_check_stale` covers stale, missing, and orphan cases; `test_vendor_hit` puts `` `TodoWrite` `` in a fixture command under `scripts/tests/fixtures/platform-trees/` and expects `reason: vendor TodoWrite in commands/<f>.md:<line>`, and expects no reason for `` `Read` ``; `test_fixture_target` expects the rewrite, untouched prose, and no identity-target `commands/` output; `test_dev_only` expects the driver to be non-shippable. Add `scripts/tests/test_eval_platform_trees.sh` in the style of `scripts/tests/test_eval_claude_md.sh`. Run both. Each must fail because the feature is missing, not on a syntax error `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`
- [x] 4.2 Add the `coverage` subcommand to `scripts/gen-platform-trees.py`, using Story 1's `parse_adapter` and `vocabulary`. Report `unmapped` for each neutral name missing from an adapter. Report `vendor` for each vendor-only name that appears as a whole backticked token in `commands/*.md`, `agents/*.md`, or `skills/*/SKILL.md`, with its line number. Define `ALLOWLIST = {"Read", "Write", "Bash"}` with one comment per entry. Output follows the check shape. Exit 0 or 1 `[AC-4.2]`
- [x] 4.3 Add `--check` to the driver. Render `cursor/writ.mdc`, `claude-code/CLAUDE.md`, and `codex/AGENTS.md.template` in memory with the Story 2 and Story 3 render functions and compare the bytes with disk. Report `stale` (bytes differ), `missing` (no file), and `orphan` (a file under `claude-code/agents/` or `codex/agents/` that no generator produces). Run `gen-claude-agents.py --check` and `gen-codex-agent-tomls.py --check`; re-emit their reasons as `reason: <kind> <path>` for the driver's own paths and `reason: <gen>: <kind> <stem>` for folded sub-generator reasons (technical-spec.md § Driver CLI). A sub-generator exit of 2 or higher yields `fail` with `reason: <gen> --check exited <rc>`. Run `coverage` inside `--check`. Write nothing. Exit codes per `spec.md → ## Business Rules (Expanded)`, Rule 1 `[AC-4.1, AC-4.2]`
- [x] 4.4 Add the `TARGETS` table with `cursor`, `claude-code`, and `codex` (`script_root: "scripts"`) and `fixture` (`script_root: "${PLUGIN_ROOT}/scripts"`, tests only). Use `TOKEN = re.compile(r"\b(python3|bash) scripts/([a-z0-9_-]+\.(?:py|sh))")`. Add `--target <name> --out-dir <dir>`. Identity targets write no `commands/` or `skills/`. Non-identity targets write `<out-dir>/<target>/commands/*.md` and `<out-dir>/<target>/skills/<name>/SKILL.md`, replacing each TOKEN match with the same interpreter and `<script_root>/<name>`. Use a callable replacement so `${PLUGIN_ROOT}` stays literal. Read and write bytes so every other byte survives `[AC-4.3]`
- [x] 4.5 Add `check_platform_trees` to `scripts/eval.sh` after the `gen-claude-agents.py` and `gen-codex-agent-tomls.py` checks. Run `--check` only; it already runs coverage, and a second `coverage` run reports each vendor and unmapped hit twice. Count a helper exit of 2 or higher, or a missing verdict line, in `RUN_ERRORS`. Turn each `reason:` line into `add_finding "<path or name>" "<reason>" "Run python3 scripts/gen-platform-trees.py, then commit the regenerated files."`. Do not start this task until the `create-issue.md` decision in Notes is made. Then run `scripts/tests/test_eval_platform_trees.sh` and confirm both mutations produce findings `[AC-4.4]`
- [x] 4.6 Add `gen-platform-trees.py` to the dev-only case of `is_shippable_script` in `scripts/install.sh` and `scripts/update.sh`. Keep the two functions byte-identical; compare the extracted function bodies with `cmp`. Follow `scripts/tests/test_install_update_dev_scripts.sh`. Confirm `test_dev_only` passes `[AC-4.5]`
- [x] 4.7 Run the verification. `uv run --python 3.9 pytest`: all four new Python tests pass. `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`: no `FAIL` lines, including `test_eval_claude_md.sh` and `test_install_update_dev_scripts.sh`. `python3 scripts/gen-platform-trees.py --check` prints `pass` on the committed tree. `bash scripts/eval.sh`, run outside any sandbox, reports 0 findings. Record the eval findings count in `## What Was Built` `[AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Empty input, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 1 Driver CLI; Rule 3 Vocabulary and parity; Rule 4 Vendor-only names; Rule 11 Tokens; Rule 13 Eval)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (`Clean tree`, `Hand edit to a generated file`, `Capability used in a command with no row in one adapter`, `Vendor identifier in a shipped command`, `Adapter section heading missing`)

---

## What Was Built

**Implementation Date:** 2026-10-23

### Files Created

1. **`scripts/tests/test_eval_platform_trees.sh`** (125 lines)
   - Bash test for `check_platform_trees` in the style of `test_eval_claude_md.sh`: each case copies `eval.sh`, every `scripts/*.py`, `adapters/`, `agents/`, `commands/`, `skills/`, the three platform directories, `system-instructions.md`, and `.writ/manifest.yaml` into a temp root and runs `eval.sh --check=platform-trees` there, never the repo. Six assertions: fresh copy → PASS, exit 0, summary line as a note; hand-edited `cursor/writ.mdc` → exactly one finding located at `` `cursor/writ.mdc` `` carrying `stale cursor/writ.mdc` and the remedy; `` `TodoWrite` `` appended to `commands/status.md` → exactly one finding at `` `commands/status.md:<line>` `` with the line computed from the file; a driver that exits 2 → eval exit 2, one run error, the finding names the driver; a missing driver → the same; `platform-trees` registered exactly once in `CHECKS` after `claude-md` and `check_platform_trees` defined.
2. **`scripts/tests/fixtures/platform-trees/vendor/commands/vendor-fixture.md`** (10 lines)
   - The command `test_vendor_hit` copies into a temp tree's `commands/`: `` `TodoWrite` `` (line 7, hit), `` `Read` `` (line 8, allowlisted), `` `message.usage` `` (line 9, a dotted field), `` `Grep("pattern")` `` (line 10, a call-syntax hit).

### Files Modified

- **`scripts/gen-platform-trees.py`** (docstring; new sections "Vendor scan", "Targets and tokens"; "Sub-generators and write mode")
  - Vendor scan: `SCANNED` (commands/*.md, agents/*.md, skills/*/SKILL.md, in report order), `tool_reference(token)` (the token's leading identifier, normalized like a first-column cell, when the rest is empty or call syntax starting with `(` or `{`; `None` for a dotted field, URL, path, `key: value`, flag, assignment, or empty token), `vendor_hits(root, vendor_only)` (`vendor <name> in <path>:<line>`, 1-based, once per name, file, and line). `ALLOWLIST` (`Read`, `Write`, `Bash`, one comment each) is Story 1's; unchanged.
  - Targets and tokens: `IDENTITY_SCRIPT_ROOT`, `TARGETS` (`cursor`, `claude-code`, `codex` with `script_root: "scripts"` plus each platform's `generated` paths and `subgenerators`; `fixture` with `${PLUGIN_ROOT}/scripts`, tests only), `TOKEN` (the technical-spec regex as bytes), `EMITTED`, `is_identity`, `rewrite_tokens` (callable replacement, so `${PLUGIN_ROOT}` stays literal), `emit_tree` (bytes in, bytes out through `write_file`, which now accepts bytes; one `wrote <target>/<path>` per file; a missing `commands/` or `skills/` is `unverifiable`).
  - `--check` and `coverage`: `TRANSLATED` (gen-claude-md `stale`/`absent claude-code/CLAUDE.md` → `stale`/`missing claude-code/CLAUDE.md`; gen-claude-agents `orphan <stem>` → `orphan claude-code/agents/<stem>.md`; gen-codex-agent-tomls `orphan <stem>` → `orphan codex/agents/<stem>.toml`), `fold_reason`, `fold_check(..., translate)` (`--check` keeps every sub-generator reason; write mode still drops `REPAIRED_KINDS`), `kind_of`, `COUNTED_KINDS`, `finish_check` (the five-count summary), `adapter_reasons`, `vendor_reasons`, `render_all`, `stale_reasons` (byte comparison of the in-memory render with disk), `stray_agent_reasons` (a `claude-code/agents/*.md` outside gen-claude-agents' `writ-*.md` glob is `orphan claude-code/agents/<name>`; no generator produces it and `install.sh` ships every file there), `check_mode` (adapters → unmapped → renders and stale/missing → stray agents → the three sub-generator `--check`s, folded → vendor scan; writes nothing), `coverage_mode` (adapters → unmapped → vendor scan; nothing else).
  - Write mode now runs the vendor scan and, when gen-claude-agents is among its sub-generators, the stray-agent scan as pre-checks, so a hit blocks every write. `write_mode(root, generated, subgenerators)` takes the narrowed sets an identity target passes; `target_mode` (identity: write mode for that platform's files only; non-identity: `emit_tree` into `--out-dir`); `main` rejects `coverage`/`--check`/`--target` combinations, `--out-dir` alone, an identity target with `--out-dir`, and a non-identity target without one (usage, exit 2); `--target` has `choices=TARGETS`.
- **`scripts/tests/test_gen_platform_trees.py`** (docstring; the `test_cli_stub` cases removed; new Story 4 section, 41 cases, 100 in the file)
  - `test_check_clean` (AC-4.1: `pass` and the five-zero summary from `--check` and `coverage` on a temp copy and on the committed tree, nothing written); `test_check_stale` ×7 over `STALE_CASES` (stale `cursor/writ.mdc`; missing `claude-code/CLAUDE.md`; orphan `claude-code/agents/writ-extra.md` plus the stale `CLAUDE.md` it implies; orphan stray `claude-code/agents/helper.md` plus the same; orphan `codex/agents/extra.toml`; stale `codex/AGENTS.md.template`; a hand-edited agent file folded as `gen-claude-agents: stale testing-agent` — each `fail`, exit 1, exact reason lines, the counts, no byte changed); `test_check_counts` (every mutation at once, counts add up); `test_tool_reference` ×13 (AC-4.2 whole-token rule, call syntax included); `test_vendor_hit` (the fixture's two hits with line numbers derived from the file, none for `` `Read` `` or `` `message.usage` ``, the same from `--check`, then an `agents/` and a `skills/` hit); `test_coverage_unmapped` (the Story 1 parity fixture → `unmapped file_search in adapters/codex.md`; `--check` adds the stale Codex template it implies); `test_fixture_target` (AC-4.3: a token fixture with both interpreters, a prose `scripts/` mention, a bare path, an uppercase name, CRLF, a tab, and a non-UTF-8 byte; every emitted file equals an independent rewrite; the in-place tree untouched; the output set exact); `test_identity_target` ×3 (each writes only its platform's in-place files, no `commands/` or `skills/`); `test_target_usage_errors` ×7; `test_dev_only` (AC-4.5: the three `is_shippable_script` bodies byte-identical, the driver denied, `spec-status.py` allowed); `test_write_blocked_by_stray_agent` ×2 and `test_write_blocked_by_vendor` (write mode and `--target claude-code` fail on a stray or a vendor hit, nothing written; `--target cursor` still writes).
- **`scripts/eval.sh`** (`CHECKS`; new `check_platform_trees` after `check_claude_md`)
  - `platform-trees` registered after `claude-md`. The check runs `--check` only (DEV-008); a missing helper, an exit of 2 or more, or no verdict line is a run error with a finding; each `reason:` line becomes `add_finding "<location>" "gen-platform-trees --check: <reason>" "Run python3 scripts/gen-platform-trees.py, then commit the regenerated files."`, located at the reason's last `/`-bearing token (a path or `path:line`), else at `scripts/<gen>.py` for a folded reason, else at the driver; the summary line becomes a note; a non-pass verdict with no reason line is its own finding.
- **`commands/create-issue.md`** (Step 3, Step 4) — the two vendor hits the first `coverage` run found, one line each: line 54 `` `Grep` `` → `` `codebase_search` ``; line 70 `` `Glob` `` → `` `file_search` ``.
- **`commands/writ-design.md`** (Screenshot capture, step 2) — the third hit, line 137: `` `browser_navigate` `` has no neutral name, so the sentence now reads "navigate to each screen with the platform's browser tool and take screenshots" (DEV-009).
- **`.writ/specs/2026-10-22-generated-platform-trees/spec-lite.md`** — the check-shape line (DEV-008) and the vocabulary line (DEV-009).
- **`.writ/specs/2026-10-22-generated-platform-trees/drift-log.md`** — Story 4 section (DEV-008, DEV-009).
- Not modified: `scripts/install.sh`, `scripts/update.sh`, `scripts/unlink.sh` — task 4.6's denylist entry landed in Story 1 (DEV-001); the three bodies are byte-identical (`cmp`) and deny `gen-platform-trees.py` (`test_dev_only`, `test_install_update_dev_scripts.sh`).

### Vendor Rewrites (contract item 3)

`python3 scripts/gen-platform-trees.py coverage` on the committed tree (HEAD 186f6b2 text) printed three reasons: `vendor Grep in commands/create-issue.md:54`, `vendor Glob in commands/create-issue.md:70`, `vendor browser_navigate in commands/writ-design.md:137`. Each was rewritten on its own line as listed above; `coverage` and `--check` now print `pass`. No other prose changed.

### Implementation Decisions

1. **Call-syntax tokens are hits** — the story's open edge case; Business Rule 4 already states that `` `Grep("pattern")` `` is a hit for `Grep` (same normalization as a first-column cell). `tool_reference` accepts `(` or `{` after the identifier and rejects everything else, so `` `message.usage` ``, `` `scripts/x.py` ``, `` `http://x` ``, `` `key: value` ``, `` `--check` ``, and `` `exec=1` `` reference no tool. Pinned by `test_tool_reference` and the fixture.
2. **`check_platform_trees` runs `--check` once** — `check_mode` already carries the coverage reasons; a second `coverage` run would report each hit twice (task 4.5; DEV-008 against Rule 13).
3. **Sub-generator reasons about files this driver owns the check of are translated, the rest folded** — AC-4.1 requires `reason: missing claude-code/CLAUDE.md` and `reason: orphan claude-code/agents/<name>.md`, so `TRANSLATED` maps those four kinds to the driver's own `reason: <kind> <path>` form; every other sub-generator reason keeps the technical-spec's `reason: <gen>: <kind> <stem>` form. The summary counts a folded reason by the token after `<gen>: `.
4. **Stray agent files are the driver's own orphans** — `gen-claude-agents.py --check` only globs `writ-*.md`, so a `claude-code/agents/helper.md` was reported as `stale claude-code/CLAUDE.md`, absorbed by the next write, and then shipped by `install.sh` (which copies `agents/*.md`). Task 4.3 defines orphan as a file under `claude-code/agents/` that no generator produces, so `stray_agent_reasons` reports it and write mode refuses it. Applied after the Gate 3 review (its Minor recommendation) and re-verified by the orchestrator's runs below.
5. **The vendor scan blocks write mode too** — the contract's "fails on a vendor tool name in shipped text" and the standing "nothing is written when any reason exists" rule; `test_write_blocked_by_vendor`.
6. **Identity targets narrow write mode instead of taking a second code path** — `TARGETS` carries each platform's `generated` paths and `subgenerators`; `--target cursor` writes only `cursor/writ.mdc`. Adding a non-identity target is one `TARGETS` entry (story Integration note).
7. **Known, spec-consistent blind spots** — `` `Grep -r x` `` and `` `Grep pattern` `` are not hits because the first-column normalization admits spaces and hyphens (Rule 4); `` `message` `` alone would be a hit because the mapping cell's `` `message.usage` `` reduces to `message`. Neither occurs in the tree.

### Test Results

**Verification:** Automated, test-first. Red (attempt 1 of this lane, before the driver work): `uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py` → 26 failed, 70 passed on the stub driver (`--check`, `coverage`, and `--target` printed `unverifiable` / `not-implemented`). Green on the final tree: 100 passed (5.68s).
**Coverage:** Not measured by the script (`test-integrity.py coverage`: unverifiable, no_coverage_report).

- ✅ Targeted: `uv run --python 3.9 pytest scripts/tests/test_gen_platform_trees.py -q` → 100 passed (orchestrator's own run, after the stray-agent fix).
- ✅ `bash scripts/tests/test_eval_platform_trees.sh` → 6 assertions passed. Mutation evidence in a scratch copy (the known `test_imports_no_source` false positive for bash tests needs it): the remedy text changed → the test fails; the run-error increment removed from `check_platform_trees` → fails; the stale byte comparison disabled in the driver → fails. Three mutants, three kills.
- ✅ Real tree: `python3 scripts/gen-platform-trees.py --check` → `pass` / `gen-platform-trees: pass (0 stale, 0 missing, 0 orphan, 0 unmapped, 0 vendor)`, exit 0; `coverage` → the same. A stray `claude-code/agents/helper.md` in a temp copy → `fail`, `reason: orphan claude-code/agents/helper.md`, `reason: stale claude-code/CLAUDE.md`; before the fix the same copy printed only the stale line and a write made `--check` pass.
- ✅ Full pytest (3.9): 2913 passed, 2 skipped (150s).
- ✅ Bash tests: 46 run, 0 failed (includes `test_eval_platform_trees.sh`, `test_eval_claude_md.sh`, `test_install_update_dev_scripts.sh`; temp projects only).
- ✅ `bash scripts/eval.sh` (outside the sandbox): Findings 0, Run errors 0 (`.writ/state/eval-20261023-072840.md`); `## platform-trees` PASS with the summary note.
- ✅ Gate 0 arch-check: pass (rederived caution: `outside_boundary` — the Gate 0.5 map held only task 4.1's test file; every other changed file is named in tasks 4.2–4.6 or the contract's vendor-rewrite allowance). Gate 2: `bash -n` and `py_compile` clean; no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 1 crossing (outside_boundary), route review-agent. Gate 3 review-override: unverifiable (no_coverage_report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: `test_imports_no_source` on `test_eval_platform_trees.sh`, the known checker false positive for bash tests (open issue `.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`); carried on the three killed mutants above, not DEGRADED. Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-008, DEV-009)
- **Security:** Low (dev-only script denied by `is_shippable_script`; subprocesses with list args; temp-file plus `os.replace` writes; every expansion of driver output quoted in `eval.sh`; no network)
- **Boundary Compliance:** the Gate 0.5 map owned only `scripts/tests/test_gen_platform_trees.py`; the six other changed files are named by the story's tasks or Notes or by contract item 3; no unjustified edit; the install scripts named in task 4.6 were correctly left untouched (DEV-001).
- gate3-route: review-agent (outside_boundary). review-panel: unverifiable (platform_cannot_spawn_other_vendors). jev-shadow: unverifiable (no_api_key). arch-lint: none — see .writ/docs/architecture-lint.md.
- The review agent re-ran `--check`, `coverage`, the 96 targeted tests then on disk, and the bash test; probed stale, missing, and orphan on a scratch copy; extracted and `cmp`-compared the three `is_shippable_script` bodies. Its one Minor finding (the `writ-*.md`-only orphan glob) is decision 4 above and was fixed post-review. Its other recommendations are recorded, not applied: pin the `--check` shadow paths directly (sub-generator exit ≥ 2, missing adapter heading); add `gen-platform-trees.py` to the dev-only paragraph in `.writ/docs/agent-cli-contract.md` (a DEV-001 leftover; no test derives from it).
- This lane's first attempt was cut off at Gate 1 by a spend limit; attempt 2 resumed from the on-disk diff, verified it against the story and the technical spec, and ran Gates 1–5 as recorded here. The coding work is attempt 1's coding agent's; the stray-agent fix is attempt 2's.

### Deviations from Spec

- **[DEV-008] `check_platform_trees` runs `--check` only, not `--check` then `coverage`** — Severity: Small
  - Spec said: Rule 13 and technical-spec → Eval Wiring: "runs `--check`, then `coverage`".
  - Reality: one `--check` run; `check_mode` already carries the coverage reasons, and a second run would report each hit twice (task 4.5).
  - Resolution: Auto-amended; spec-lite check-shape line says so.
- **[DEV-009] `browser_navigate` hit rewritten to neutral prose, not a neutral name** — Severity: Small
  - Spec said: every hit the first `coverage` run finds "is rewritten to its neutral name".
  - Reality: `commands/writ-design.md:137` had no neutral name to take; the sentence was reworded on the same line with no backticked token.
  - Resolution: Auto-amended; spec-lite vocabulary line records the rule.
