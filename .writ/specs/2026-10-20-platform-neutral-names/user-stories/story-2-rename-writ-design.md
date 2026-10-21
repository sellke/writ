# Story 2: Rename `/design` to `/writ-design` Across Every Reference

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ user on Claude Code, Cursor, or Codex
**I want to** reach Writ's wireframe and mockup command as `/writ-design`, with every Writ file pointing at that name
**So that** `/design` on Claude Code no longer collides with the platform's native command, and no Writ file sends me to a command that no longer exists

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given the rename commit, when `git show -M --stat` and `git show -M` run on it, then they report `commands/{design.md => writ-design.md}`; every changed line in that file is a self-naming line (frontmatter `name: writ-design`, the H1, the five invocation-table rows, and the two in-body `/writ-design` references); and `commands/design.md` does not exist `[AC-2.1]`
- [x] Given `.writ/manifest.yaml`, when it is read, then it has a `writ-design` entry with `file: commands/writ-design.md` and the old category, purpose, and tags; no command is named `design`; no `aliases` list contains `design`; the commands list is sorted; and `bash scripts/gen-skill.sh --check` prints `pass` with `SKILL.md` showing a `` `/writ-design` `` row `[AC-2.2]`
- [x] Given every rename-class line in technical-spec.md → ## Reference Inventory, plus any the re-run grep adds, when the story is done, then each names `/writ-design`, `writ-design`, or `writ-design.md`: `README.md`, `adapters/cursor.md`, `codex/AGENTS.md.template`, `commands/create-spec.md` Step 1.5, `commands/create-spec.lean.md` if present, `commands/create-adr.md`, `commands/research.md`, `commands/status.md`, `commands/prototype.md` (two lines), `.writ/docs/model-tiers.md`, and the five `scripts/eval.sh` allowlist rows `[AC-2.3]`
- [x] Given `scripts/gen-claude-md.py` from `2026-10-20-claude-code-parity`, when it regenerates `claude-code/CLAUDE.md`, then the file lists `` `/writ-design` `` and no `` `/design` ``, `python3 scripts/gen-claude-md.py --check` prints `pass`, its eval check passes, and the file was not hand-edited `[AC-2.4]`
- [x] Given the keep-class lines in the inventory (`design-system.md` paths, "roadmap/design", "artboard/design", record paths, the three dated snapshots), when the story is done, then none of them has changed; and `uv run --python 3.9 pytest`, the bash tests, and `bash scripts/eval.sh` (0 findings) pass `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Re-run `git grep -n -e '/design' -e 'design\.md'` and compare it with technical-spec.md → ## Reference Inventory. Classify any new or moved line. Then add failing registration tests to `scripts/tests/test_platform_neutral_names.py` (`test_writ_design_file`, `test_manifest_entry`, `test_skill_catalog`, `test_eval_allowlist_rows`), citing AC IDs in docstrings, and confirm they fail `[AC-2.1, AC-2.2, AC-2.3, AC-2.5]`
- [x] 2.2 Run `git mv commands/design.md commands/writ-design.md`, then edit only the self-naming lines listed in technical-spec.md → ## Rename → File edits `[AC-2.1]`
- [x] 2.3 Rename the manifest entry, move it after `verify-spec`, run `bash scripts/gen-skill.sh`, and confirm `bash scripts/gen-skill.sh --check` prints `pass` `[AC-2.2]`
- [x] 2.4 Update the rename-class references in `README.md`, `adapters/cursor.md` (directory tree, sorted), `codex/AGENTS.md.template` (row moved after `/verify-spec`), `commands/create-spec.md`, `commands/create-spec.lean.md` if it still exists, `commands/create-adr.md`, `commands/research.md`, `commands/status.md`, `commands/prototype.md`, `.writ/docs/model-tiers.md`, and the five allowlist rows in `scripts/eval.sh` `[AC-2.3]`
- [x] 2.5 Confirm `scripts/gen-claude-md.py` exists. If it does not, stop and report blocked; do not hand-edit. Otherwise run `python3 scripts/gen-claude-md.py`, then `--check` (before regenerating it reports `missing /writ-design` and `extra /design`; after, `pass`), and confirm the `/writ-design` row `[AC-2.4]`
- [x] 2.6 Verify the sweep: re-run the inventory grep and check that only keep-class lines remain; check `git diff --stat` shows no edits to keep-class files; commit with a `BREAKING CHANGE: /design is renamed to /writ-design` footer, then run `git show -M --stat` and `git show -M` on the commit `[AC-2.1, AC-2.3, AC-2.5]`
- [x] 2.7 Verify the regression surface: `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` outside the sandbox, with 0 findings `[AC-2.2, AC-2.4, AC-2.5]`

## Notes

- **Name only.** Do not touch the modes, flags, exit criteria, or outputs of the command. `/design` Mode A modernization is out of scope (roadmap parking lot).
- **No alias.** A `design` alias would bring the collision back. If anything asks for one, the answer is no.
- **The grep misses bare names.** `.writ/manifest.yaml` `name: design`, the command's own frontmatter and H1, and the `.writ/docs/model-tiers.md` entry-level list do not contain `/design` or `design.md`. The inventory lists them under "Rename-class references the grep misses".
- **Eval allowlist rows fail silently if missed.** `check_referenced_paths` judges a row's staleness only when `commands/<creating-command>.md` exists. A row still naming `/design` is skipped with no finding. `test_eval_allowlist_rows` and Story 3's gate are the only things that catch it.
- **Generated files.** `SKILL.md` comes from `gen-skill.sh`. `claude-code/CLAUDE.md` comes from `scripts/gen-claude-md.py` (dev-only, added by the parity spec). `codex/AGENTS.md.template` is hand-maintained today; if the parity spec has put it under a generator, regenerate it instead. No `codex/agents/*.toml` names the command, so do not run `gen-codex-agent-tomls.py` for this story.
- **Cross-spec edits.** The Phase 13 `create-spec` reduction pass and the cuts spec may have rewritten `create-spec.md` Step 1.5, `prototype.md`, or deleted the `*.lean.md` siblings. Find each line by its text, not by line number.
- **Symlinks.** `.claude/commands` and `.cursor/commands` link to `commands/`. `git mv` in `commands/` is enough. Never replace a symlink with a copy.
- **Never run `install.sh` or `update.sh` against the Writ repo.** Story 3 tests installs in temp directories.
- **Release.** `/release` Step 1.2 finds breaking changes by the `BREAKING CHANGE` commit footer, and its table proposes a major bump for one. The maintainer picks the version.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Rename sweep, Eval allowlist rows left as `/design`, Regenerate `claude-code/CLAUDE.md`, `SKILL.md`] — technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** []
- **Business rules:** [Rule 5 (name-only rename), Rule 6 (`git mv`, symlinks stay), Rule 7 (reference classes), Rule 8 (regenerate generated files), Rule 9 (no alias), Rule 10 (manifest order)] — spec.md → ## Business Rules (Expanded)
- **Experience:** [State Catalog rows "User types `/design` on Claude Code after upgrade" and "on Cursor or Codex after upgrade"] — spec.md → ## Experience Design → ### State Catalog
- **Technical:** technical-spec.md → ## Rename (Story 2), ## Reference Inventory (2026-10-20)

---

## What Was Built

**Implementation Date:** 2026-10-21

### Files Created

[None created]

### Files Modified

- **`commands/design.md` → `commands/writ-design.md`** (`git mv`, 95% similarity)
  - 9 self-naming lines: frontmatter `name: writ-design`, H1 `# Design Command (writ-design)`, the five invocation rows, "(added by `/writ-design` or `/create-spec`)", and "Generates specs that `/writ-design` adds visuals to". No mode, flag, exit criterion, or output changed.
- **`.writ/manifest.yaml`** — entry renamed to `writ-design` / `commands/writ-design.md` and moved after `verify-spec`; category, purpose, and tags unchanged; no alias.
- **`SKILL.md`** — regenerated with `bash scripts/gen-skill.sh`; the row is last in Planning & Specification.
- **`claude-code/CLAUDE.md`** — regenerated with `python3 scripts/gen-claude-md.py`. Before regenerating, `--check` printed `reason: missing writ-design`, `reason: extra design`, `gen-claude-md: fail (1 missing, 1 extra)`; after, `gen-claude-md: pass (32 commands, 8 agents)`.
- **`codex/AGENTS.md.template`** — hand edit: `/writ-design` · `.codex/commands/writ-design.md`, moved after `/verify-spec`.
- **`README.md`**, **`commands/create-adr.md`**, **`commands/research.md`** — table rows renamed in place.
- **`commands/create-spec.md`** (§ Step 1.5) — "Follow wireframe conventions from `/writ-design` command."
- **`commands/prototype.md`** (§ When to Use, § Completion) — both lines name `/writ-design`.
- **`commands/status.md`** — the Suggested Actions slash allowlist and the Maintainer Note bare allowlist both name `writ-design` (DEV-003).
- **`adapters/cursor.md`** (§ Directory Structure) — `└── writ-design.md         # /writ-design` is the last entry; `verify-spec.md` is `├──`; 32 entries.
- **`.writ/docs/model-tiers.md`** — `high` row lists `writ-design` last; count stays 15.
- **`scripts/eval.sh`** — five `referenced_paths_allowlist` rows name `/writ-design` in column 2 and the reason text.
- **`scripts/tests/test_governor_enforcement.py`** — `KNOWN_OVER_BUDGET["commands/create-spec.md"]` 28733 → 28738 with a dated comment (DEV-002).
- **`scripts/tests/test_platform_neutral_names.py`** — registration section: 22 new cases (28 in the file).

### Implementation Decisions

1. **Tests find renamed lines by anchor text, not whole-line pins.** A sibling Phase 13 spec reduces `commands/create-spec.md`; each anchor must match one line that names `/writ-design`, and a whole-file check rejects the old name, slash or bare.
2. **Counts come from the manifest.** The cursor-tree test compares the tree to the sorted manifest command files; the model-tiers test checks the row's `(N)` against its own list.
3. **`test_eval_allowlist_rows` requires every allowlist row's creating command to exist**, which closes the silent skip in `check_referenced_paths` for good.
4. **The test file spells the old name from parts** (`OLD_SLASH = "/" + OLD_NAME`), so Story 3's gate gets no hit from it. The registration section's header names this spec's slug so `ac-trace` attributes its AC tokens here, not to the parity slug in `RECORD_PREFIXES`.
5. **Unsorted lists were renamed in place** (README, both status allowlists); sorted ones moved the entry to the end (manifest, generated catalogs, codex template, cursor tree, model-tiers).

### Test Results

**Verification:** test-first, then full suites.

- Red: 18 of 24 registration cases failed before any edit, each for the expected reason.
- Mutations: the coder's 9 probes, then the review agent's 24 (iteration 1) and 26 (iteration 2) probes on scratch copies. Every regression probe failed its targeted test. The surviving iteration-1 probes (a changed flag or exit criterion in `writ-design.md`; a new `/design` in an unswept file) are covered by the AC-2.1 commit diff and by Story 3's gate.
- Orchestrator run: `test_platform_neutral_names.py`, `test_governor_enforcement.py`, `test_harness_cuts.py` → 119 passed; `gen-skill.sh --check`, `gen-claude-md.py --check`, `gen-claude-agents.py --check` → pass; `ac-trace.py check` → 0 findings.
- Full suites (orchestrator, after iteration 2): pytest 3.9 → 2710 passed, 2 skipped (2688 + 22); bash loop → 44 run, 0 failed; `bash scripts/eval.sh` → Findings: 0, Run errors: 0.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iteration(s)
- **Drift:** Small (DEV-002, DEV-003)
- **Security:** Clean
- **Boundary Compliance:** one disclosed crossing, `scripts/tests/test_governor_enforcement.py` (DEV-002), judged justified. The script-computed map left out the manifest, `SKILL.md`, `claude-code/CLAUDE.md`, and the command file, which the story's tasks name.
- gate3-route: review-agent (outside_boundary .writ/manifest.yaml; outside_boundary SKILL.md; outside_boundary claude-code/CLAUDE.md; outside_boundary commands/design.md; outside_boundary commands/writ-design.md; outside_boundary scripts/tests/test_governor_enforcement.py). review-panel: skipped — platform cannot spawn other vendors. arch-lint: none — see .writ/docs/architecture-lint.md.
- Gate 0 arch-check: pass (rederived proceed). Gate 2: `py_compile` and `bash -n scripts/eval.sh` clean; no linter configured. Gate 3 iteration 1: PASS with four Minor test-brittleness issues, sent back; iteration 2: PASS, no issues. review-override: pass. Gate 3.5 drift-format: pass. Gate 4 authenticity: pass. Gate 4.5: app-verify unverifiable (no recipe). Gate 5: docs-check unverifiable (no public exports).

### Deviations from Spec

- **[DEV-002] Governor ledger re-pinned for the create-spec Step 1.5 rename** — Severity: Small
  - Spec said: no change to `scripts/tests/test_governor_enforcement.py`.
  - Reality: create-spec ledger 28733 → 28738, because the required Step 1.5 text adds 5 bytes and the ledger must equal the exact overage.
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md S2 Files in Scope names the ledger.
- **[DEV-003] Inventory missed the bare `design` in the `/status` Maintainer Note allowlist** — Severity: Small
  - Spec said: one `commands/status.md` line.
  - Reality: both status.md allowlists renamed; `eval-leanness.py` phantom-checks the bare list.
  - Resolution: Auto-amended
  - Spec amendment: spec-lite.md S2 Files in Scope says both `status.md` command lists.
