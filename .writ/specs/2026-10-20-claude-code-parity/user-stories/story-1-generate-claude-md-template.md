# Story 1: Generate the CLAUDE.md Template from the Manifest

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer adding or renaming commands in the Writ source repo
**I want to** generate `claude-code/CLAUDE.md` from `.writ/manifest.yaml` and have `eval.sh` fail when the committed template falls behind
**So that** a Claude Code install always lists every command and imports the system instructions, and CI catches a forgotten regenerate

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given the committed manifest and `claude-code/agents/`, when `python3 scripts/gen-claude-md.py` runs, then `claude-code/CLAUDE.md` holds one table row per manifest command in manifest order (32 today, including `/implement-phase`, `/knowledge`, and `/revert`) with file `.claude/commands/<name>.md` and the manifest purpose; one agents entry per `claude-code/agents/*.md` file (7 today, including `writ-evaluator.md`); the pipeline line; and the line `@.claude/system-instructions.md` alone on its line outside any backtick span or fence; the file uses LF endings and ends with exactly one newline; stdout line 1 is `pass`; and a second run leaves the bytes unchanged `[AC-1.1]`
- [x] Given the committed template, when `--check` runs, then it prints `pass` and exits 0; given a temp copy whose `/revert` row is deleted, then it prints `fail`, exactly one `reason: missing revert`, a `gen-claude-md:` summary as the last line, and exits 1; given any other byte difference with the row set intact, then it prints `reason: stale claude-code/CLAUDE.md` and exits 1 `[AC-1.2]`
- [x] Given a missing `.writ/manifest.yaml`, an unknown flag, a manifest command without `purpose`, a purpose containing `@` outside backticks, or a pipeline command absent from the manifest, when the generator runs, then it prints `unverifiable` and exits 0, prints usage on stderr with empty stdout and exits 2, or prints `fail` with a `reason:` line naming the entry and exits 1, respectively; and write mode leaves the committed template untouched in every failing case `[AC-1.3]`
- [x] Given `is_shippable_script` in `scripts/install.sh`, `scripts/update.sh`, and `scripts/unlink.sh`, when it is called with `gen-claude-md.py`, then it returns non-zero in all three and the three function bodies are byte-identical; a temp `install.sh --platform claude --no-commit` copies no `scripts/gen-claude-md.py` and records no manifest entry for it; and the note under the Classification table in `.writ/docs/agent-cli-contract.md` and `commands/update-writ.md` Step 3 both name it as dev-only `[AC-1.4]`
- [x] Given a temp root holding `eval.sh`, the generator, the manifest, and `claude-code/`, when `bash scripts/eval.sh --check=claude-md` runs on a fresh copy, then the section is PASS; when the `/revert` row is deleted from the template, or a command is added to the manifest, then the run exits 1 with exactly one finding that names the command and the remedy `python3 scripts/gen-claude-md.py`; and `claude-md` is in the `CHECKS` list, so the full run and CI include it `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write failing tests in `scripts/tests/test_gen_claude_md.py`: import the hyphenated module by path (the `test_gen_codex_agent_tomls.py` recipe), render from temp-root fixtures, run the CLI with `subprocess` from a temp copy of the script, and cover output content, determinism, the trailing newline, the import line's placement, `--check` pass/missing/stale, and every error row `[AC-1.1, AC-1.2, AC-1.3]`
- [x] 1.2 Write failing shell tests: `scripts/tests/test_eval_claude_md.sh`, following `scripts/tests/test_eval_codex_tomls.sh` (temp roots, `--check=claude-md --report=`, finding count, remedy text), and `scripts/tests/test_gen_claude_md_not_shipped.sh`, which loads `is_shippable_script` from all three lifecycle scripts the way `test_install_update_dev_scripts.sh` does and installs into a temp project from a committed temp source copy `[AC-1.4, AC-1.5]`
- [x] 1.3 Implement `scripts/gen-claude-md.py` per `sub-specs/technical-spec.md` → Generator: argparse CLI, the line-based manifest reader, frontmatter reader, renderer, `--check` comparison with `missing`/`extra`/`stale` reasons, check-shape output, atomic write; stdlib only, Python 3.9 `[AC-1.1, AC-1.2, AC-1.3]`
- [x] 1.4 Run the generator, review the diff of `claude-code/CLAUDE.md` (7 new rows, `writ-evaluator.md`, current purposes, import line), and confirm `bash scripts/eval.sh --check=ralph-retirement` still passes on it `[AC-1.1]`
- [x] 1.5 Add `gen-claude-md.py` to the dev-only case arm of `is_shippable_script` in `scripts/install.sh`, `scripts/update.sh`, and `scripts/unlink.sh` (identical edit in all three); name it in the Classification note of `.writ/docs/agent-cli-contract.md`, in `DEV_ONLY` of `scripts/tests/test_agent_cli_contract_doc.py`, and in the dev-only list of `commands/update-writ.md` Step 3 `[AC-1.4]`
- [x] 1.6 Add `check_claude_md` to `scripts/eval.sh`, modeled on `check_codex_tomls` (helper missing, bad exit, `unverifiable`, one finding per `reason:` line, summary as a note), and add `claude-md` to `CHECKS` after `codex-tomls` `[AC-1.5]`
- [x] 1.7 Verify: `uv run --python 3.9 pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/eval.sh` outside the sandbox with 0 findings; all must pass `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **Never run `install.sh` or `update.sh` against the Writ repo.** `.claude/` and `.cursor/` are symlinks into the product source (CLAUDE.md). AC-1.4's install runs in a temp directory against a committed temp copy of the tree.
- **Dependency on `2026-10-20-harness-cuts`.** That spec edits `is_shippable_script` and the lean-sibling logic first. Add the name to whatever dev-only arm exists after it lands; do not assume line numbers or the current arm's exact text.
- **`gen-skill.sh` ships; this generator does not.** The pattern borrowed is "generator plus `--check`". The generator reads `.writ/manifest.yaml`, which installed projects do not have.
- **Agents list source.** `claude-code/agents/*.md` frontmatter, not the manifest's `agents:` list (spec.md → Decisions D1). The test must assert all 7 Claude agent files appear.
- **One reason per removed row.** A row-set difference suppresses the `stale` reason, so the eval mutation test sees exactly one finding.
- **Leanness.** A new script adds to the `scripts` surface. `check_leanness` reports growth as a note, not a finding. Keep the generator small (target under 200 lines).
- **Do not edit `.github/workflows/eval.yml`.** CI already runs `bash scripts/eval.sh`; another Phase 13 spec owns the workflow file.
- **Unrelated working-tree edits.** Other Phase 13 specs touch the same lifecycle scripts. Run `git diff` before and after, and change only the targeted lines.
- **Read first.** technical-spec.md → Import Line, Generator (Story 1), Eval Check (Story 1); spec.md → Grounding Notes → Decisions D1, D2, D4. The shadow-path rows' Generator column applies here.
- **Test patterns.** `scripts/tests/test_gen_codex_agent_tomls.py` (import by path), `scripts/tests/test_eval_codex_tomls.sh` (eval mutation in temp roots), `scripts/tests/test_install_update_dev_scripts.sh` (filter bodies, temp install).

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Generator reads manifest, Generator validates manifest, Generator renders a purpose, Generator checks pipeline, Generator reads agents, Generator writes, `--check`]
- **Shadow paths:** [Happy, Nil input, Empty input, Upstream error]
- **Business rules:** [Import line, Generator is dev-only, Generator output shape, Deterministic template, Command rows, No accidental imports, CI coverage, Test isolation]
- **Experience:** [State Catalog]

## What Was Built

**Implementation Date:** 2026-10-21

### Files Created

- **`scripts/gen-claude-md.py`** — dev-only generator (stdlib, Python 3.9). Write mode, `--check`, `--help`. Reads the manifest `commands:` list with a line reader and `claude-code/agents/*.md` frontmatter; prints the check shape (`pass`/`fail`/`unverifiable`, `reason:` lines, `gen-claude-md:` summary last); exits 0, 1, or 2; writes through a temp file and `os.replace`, keeping the file mode; writes nothing on any `fail`.
- **`scripts/tests/test_gen_claude_md.py`** — 31 tests for AC-1.1 to AC-1.3: content, order, agents read from the files, import-line placement, LF and final newline, determinism, `--check` pass/missing/extra/stale/absent, and every error row.
- **`scripts/tests/test_eval_claude_md.sh`** — AC-1.5 mutation test in temp roots: fresh copy PASS; deleted `/revert` row or a new manifest command gives exactly one finding naming the command and the remedy; stale template, missing manifest, and missing helper each give a finding; `claude-md` registered once, after `codex-tomls`.
- **`scripts/tests/test_gen_claude_md_not_shipped.sh`** — AC-1.4: all three `is_shippable_script` bodies reject the generator and are identical; a temp `install.sh --platform claude --no-commit` from a committed temp source copy neither copies nor records it; the CLI contract note and `/update-writ` Step 3 name it.

### Files Modified

- **`claude-code/CLAUDE.md`** — regenerated: import line `@.claude/system-instructions.md`, 32 command rows in manifest order with manifest purposes (`/ship` now "Take a green branch through commit intelligence and PR creation."), 8 agents including `writ-evaluator.md`, the pipeline, and the `/implement-phase` sentence.
- **`scripts/eval.sh`** — `check_claude_md`, modeled on `check_codex_tomls`; `claude-md` in `CHECKS` after `claude-agents` (DEV-001).
- **`scripts/install.sh`, `scripts/update.sh`, `scripts/unlink.sh`** — `gen-claude-md.py` joins the dev-only arm of `is_shippable_script`; the three bodies stay byte-identical.
- **`.writ/docs/agent-cli-contract.md`** — one sentence names `gen-claude-md.py` as dev-only (DEV-002).
- **`commands/update-writ.md`** (Step 3) — names the dev-only Claude Code template generator.
- **`scripts/tests/test_agent_cli_contract_doc.py`** — `gen-claude-md.py` in `DEV_ONLY`.

### Implementation Decisions

1. **Agents come from the files, not a count.** Tests derive the expected agent set from `claude-code/agents/*.md`, so the eighth agent (`writ-visual-qa`, added by `2026-10-20-claude-agent-generator`) needed no test change.
2. **Row-set differences suppress `stale`.** A removed row yields exactly one reason, so the eval mutation test sees one finding.
3. **Write mode keeps the file mode** (0644 for a new file) because `mkstemp` would otherwise leave 0600.

### Test Results

**Verification:** test-first, then full suites.

- Red: 31 pytest failures before the generator existed; `test_eval_claude_md.sh` failed at "fresh: expected exit 0, got 2"; `test_gen_claude_md_not_shipped.sh` failed at "install.sh: is_shippable_script accepts gen-claude-md.py".
- Mutations (coder, scratch copies): `check_claude_md` returning early, or reason findings turned into notes, each fail `test_eval_claude_md.sh`. Evaluator probes on copies confirmed the `missing`/`stale`/`absent` paths and write-mode no-write on every failure.
- Orchestrator run: `test_gen_claude_md.py`, `test_agent_cli_contract_doc.py`, `test_agent_cli_contract.py` → 344 passed; `test_eval_claude_md.sh`, `test_gen_claude_md_not_shipped.sh`, `test_install_update_dev_scripts.sh`, `test_eval_claude_agents.sh` → exit 0; `gen-claude-md.py --check` → `gen-claude-md: pass (32 commands, 8 agents)`; `eval.sh --check=claude-md` → Findings 0.
- Full suites (coder and evaluator): pytest 3.9 → 2637 passed, 1 failed, 2 skipped (the failure is pre-existing: `test_harness_cuts.py` guard grep hits `.writ/specs/2026-10-20-ci-and-update-integrity/uat-plan.md`; fixed on the phase branch); bash loop → 41 run, 0 failed; `bash scripts/eval.sh` → Findings 0.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-001, DEV-002, DEV-003, DEV-004)
- **Security:** Clean
- **Boundary Compliance:** all edits in owned files; Gate 2.5 found 0 crossings
- gate3-route: evaluator-agent. review-panel: skipped — platform cannot spawn other vendors. arch-lint: none — see .writ/docs/architecture-lint.md.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; `bash -n` and `py_compile` clean; build-smoke unverifiable (unsupported stack). Gate 3 review-override: unverifiable (no coverage report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no report). Gate 4 authenticity: `test_imports_no_source` on the two bash tests, the known false positive for shell tests (`.writ/issues/improvements/2026-10-12-test-integrity-shell-tests.md`); carried on the red-phase and mutation evidence above, not DEGRADED. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).
- Evaluator residual (Minor, not drift): the manifest line reader drops an entry that does not start with `  - name:`; `check_manifest` (via `gen-skill.sh --dry-run`) still rejects such a manifest in CI.

### Deviations from Spec

- **[DEV-001] `claude-md` sits after `claude-agents` in `CHECKS`** — Severity: Small. Resolution: Auto-amended (spec-lite S1 line).
- **[DEV-002] Classification note keeps "Six dev-only scripts" and adds a sentence** — Severity: Small. Resolution: Auto-amended (spec-lite S1 line).
- **[DEV-003] Generator is 236 lines** — Severity: Small. Resolution: recorded in drift-log.md.
- **[DEV-004] Choices where the spec is silent, and eight agents** — Severity: Small. Resolution: Auto-amended (spec-lite S1 line).
