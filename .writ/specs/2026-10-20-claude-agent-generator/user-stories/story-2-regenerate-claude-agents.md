# Story 2: Regenerate Claude Agents

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Claude Code user of Writ
**I want to** receive `writ-*.md` agents whose bodies match the canonical `agents/*.md` templates, including a `writ-visual-qa` agent
**So that** `/implement-story` on a Claude install gets the full prompt contract (prompt template, iteration caps, verdict keys, `STATUS: BLOCKED` contract, boundary rules) instead of the 45-79-line hand-written bodies

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given the Story 1 generator and the committed `agents/*.md` templates, when `python3 scripts/gen-claude-agents.py` runs, then the seven existing `claude-code/agents/writ-*.md` files are rewritten, `claude-code/agents/writ-visual-qa.md` is created with `model: inherit` and `permissionMode: plan`, and `python3 scripts/gen-claude-agents.py --check` exits 0 with `gen-claude-agents: pass (0 stale, 0 missing, 0 orphan, 0 unmapped)` `[AC-2.1]`
- [ ] Given the frontmatter of the seven `writ-*.md` files as committed before regeneration, when the files are regenerated, then each file's frontmatter block (keys, values, key order) is byte-identical to its prior version and only the content after the closing `---` changes `[AC-2.2]`
- [ ] Given the regenerated `claude-code/agents/writ-coder.md`, when it is searched, then it contains the literal `MAX_SELF_FIX_ITERATIONS = 3` and the File Ownership Boundaries rules that reference `boundary_map` `[AC-2.3]`
- [ ] Given the `scripts/tests/test_jev_shadow_hooks.sh` pin on "then its trailing `[AC-N.M]` tag" in `writ-evaluator.md`, when the pin is retargeted to the canonical wording "ending with the criterion's `[AC-N.M]` tag", then `bash scripts/tests/test_jev_shadow_hooks.sh` passes and `scripts/tests/test_review_panel.py` `TaggedOutputContractTests` passes against the regenerated `writ-reviewer.md` and `writ-evaluator.md` `[AC-2.4]`
- [ ] Given the committed `agents/` and `claude-code/agents/` trees, when the repo-level test runs `gen-claude-agents.py --check` against those real paths and `bash scripts/install.sh --dry-run --platform claude` runs in an empty temp project, then the test passes and the dry run lists 8 agents `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write the repo-level tests first: a pytest that runs `gen-claude-agents.py --check` with `--agents-dir agents --out-dir claude-code/agents` and asserts exit 0, plus pins for `MAX_SELF_FIX_ITERATIONS = 3` and `boundary_map` in `writ-coder.md`; confirm they fail on the pre-regeneration tree `[AC-2.3, AC-2.5]`
- [ ] 2.2 Save the frontmatter block of each of the seven current `writ-*.md` files to the scratchpad, then run `python3 scripts/gen-claude-agents.py` `[AC-2.1, AC-2.2]`
- [ ] 2.3 Diff each regenerated frontmatter block against the saved copy; if any key, value, or order differs, fix the `OVERLAY` entry in the generator and regenerate until the diff is empty `[AC-2.2]`
- [ ] 2.4 Retarget the `test_jev_shadow_hooks.sh` grep at line 94 to "ending with the criterion's `[AC-N.M]` tag"; run that script and `uv run pytest scripts/tests/test_review_panel.py -k TaggedOutputContractTests` until both pass `[AC-2.4]`
- [ ] 2.5 Inspect `writ-visual-qa.md` for `model: inherit`, `permissionMode: plan`, `disallowedTools: Write, Edit`, and the generated-header comment; run `--check` on the tree and confirm the pass summary `[AC-2.1]`
- [ ] 2.6 Run `bash scripts/install.sh --dry-run --platform claude` from an empty temp directory and confirm the agent count is 8 `[AC-2.5]`
- [ ] 2.7 Run the full suites: `uv run pytest`, `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t"; done`, and `bash scripts/eval.sh`; commit the regenerated files, the new test, and the pin retarget together `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Frontmatter is the regression risk.** Story 1 seeds `OVERLAY` from today's files. Any transcription error shows up here as a frontmatter diff, so fix it in the overlay, never in the generated file.
- **Header comment placement.** The generated-header HTML comment sits after the closing `---`. It counts as body change and does not affect the AC-2.2 frontmatter comparison.
- **Pin semantics.** `TaggedOutputContractTests` already reads both canonical and Claude files. After regeneration, the Claude bodies equal canonical, so the regex `` `- \[ \]`[^\n]*`\[AC-N\.M\]` tag `` should match without edits. If it fails, the canonical file is the problem, not the mirror.
- **Install dry run.** `install.sh` installs into the current directory and counts agents with `AGENTS_SRC="claude-code/agents"` (`scripts/install.sh:78`, `:769`). Run it from a throwaway directory, not this repo. This repo's `.claude/` is symlinks; do not run `install.sh` here.
- **Installed-user effect.** `scripts/update.sh` three-way merge marks each `writ-*.md` as upstream-changed once. Customized files follow the overlay-merge path. Expected, not a regression.
- **Out of scope.** Do not rewrite Cursor `Task(...)` wrappers or filter sections in bodies. `check-agent-parity.sh`, `eval.sh`, and the visual-qa exclusion removal belong to Story 3.
- **Python 3.9 floor.** The repo-level test must pass on `uv run --python 3.9 pytest`.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`--check` / Generated file edited by hand → `reason: stale <stem>`; `--check` / Generated file deleted → `reason: missing <stem>`; `--check` / Extra `writ-*.md` → `reason: orphan writ-<x>`; Write mode / Stem has no overlay → `reason: unmapped <stem>`, write nothing] — from technical-spec.md → Error & Rescue Map
- **Shadow paths:** [Happy: canonical edit → regenerate → check passes] — from technical-spec.md → Shadow Paths
- **Business rules:** [1. Single writer; 2. Body is verbatim; 3. Overlay owns Claude metadata; 4. Stem → filename map is explicit; 7. 3.9 floor] — from spec.md → ## Business Rules
- **Experience:** [Happy path: the generator rewrites the eight `writ-*.md` files; State catalog: Aligned; Installed-user effect] — from spec.md → Experience Design
