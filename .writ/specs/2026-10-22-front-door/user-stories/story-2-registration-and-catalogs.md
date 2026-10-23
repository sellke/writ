# Story 2: Registration and Catalogs

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** new user reading the README or a platform catalog, and the maintainer who keeps the generated catalogs honest **I want to** find `/writ` first on every surface, with the generated files produced by their generators **So that** every catalog agrees on the front door, and a missed or stale surface fails a test.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [x] Given `.writ/manifest.yaml`, when `categories:` and `commands:` are read, then `categories:` starts with `- id: entry` and `label: "Start here"`, and `commands:` holds a `writ` entry with `file: commands/writ.md`, `category: entry`, and `tags: [entry, routing]`, placed after `verify-spec` and before `writ-design` `[AC-2.1]`
- [x] Given `scripts/gen-claude-md.py` with its TEMPLATE edit, `SKILL.md`, and `claude-code/CLAUDE.md`, when both generators run and both `--check` commands run, then each `--check` prints `pass` as its first line, `SKILL.md` renders the `entry` table first with a `/writ` row, and `claude-code/CLAUDE.md` has a "Start with" line that names `/writ "<what you want>"` above its Commands table `[AC-2.2]`
- [x] Given `codex/AGENTS.md.template` and the Commands section of `README.md`, when each is read, then the Codex template has a `### Start here` table with a `/writ` row above `Planning & Specification`, and README § Commands has a `### Start here` table with a `/writ` row `[AC-2.3]`
- [x] Given `README.md` § Quick Start, when read from its top, then `/writ` and its two-line example appear before the first table, the prompting-guide pointer sentence ends with "then type `/writ` followed by what you want.", and the five-command table sits under the heading "What `/writ` routes to" `[AC-2.4]`
- [x] Given `adapters/cursor.md` § Directory Structure, `commands/status.md`'s command list, `.writ/docs/model-tiers.md`'s `high` row, and `adapters/claude-code.md` § Tool Mapping → Quick Reference, when each is read, then the tree line `writ.md  # /writ` sits between `verify-spec.md` and `writ-design.md` with its count comment at 33, the status list starts with `/writ`, the `high` row lists `writ` in sorted order with its count at (16), and the Claude Code `todo_write` row's second cell is `TodoWrite` with Notes "Native todo list; phases mirror here" `[AC-2.5]`

## Implementation Tasks

- [x] 2.1 Write the failing tests first. Add `test_manifest`, `test_catalogs`, `test_readme`, and `test_surfaces` to `scripts/tests/test_front_door.py`, which Story 1 created with its command-section tests. Assert what technical-spec.md → ## Tests lists for each. Follow the registration style in `scripts/tests/test_platform_neutral_names.py`: Python 3.9 stdlib, `subprocess` for the two `--check` calls. Run them and confirm each fails on the missing registration, not on an import or syntax error `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [x] 2.2 Register `/writ` in `.writ/manifest.yaml`. Add `- id: entry` with `label: "Start here"` as the first `categories:` entry. Add the `writ` command entry with the `purpose` and `tags` from technical-spec.md → ## Registration Edits, placed after `verify-spec`. Run `test_manifest` and confirm it passes `[AC-2.1]`
- [x] 2.3 Regenerate the generated catalogs. Run `bash scripts/gen-skill.sh` to regenerate `SKILL.md`. Add the "Start with" line to the TEMPLATE in `scripts/gen-claude-md.py`, above the Commands table, then run `python3 scripts/gen-claude-md.py`. Confirm both `--check` commands print `pass`. Do not hand-edit `SKILL.md` or `claude-code/CLAUDE.md` `[AC-2.2]`
- [x] 2.4 Hand-edit the Codex template and the README Commands section. In `codex/AGENTS.md.template`, add a `### Start here` table with the `/writ` row above `Planning & Specification`. In README § Commands, add a `### Start here` table with the `/writ` row. Locate both by heading text `[AC-2.3]`
- [x] 2.5 Rewrite README § Quick Start. Put `/writ` and a two-line example first. Complete the prompting-guide pointer sentence with its `/writ` clause, so it ends "then type `/writ` followed by what you want." Place the five-command table under the heading "What `/writ` routes to". Run `test_readme` and confirm it passes `[AC-2.4]`
- [x] 2.6 Update the remaining surfaces. In `adapters/cursor.md` § Directory Structure, add `writ.md  # /writ` after `verify-spec.md` and change the count comment from 32 to 33. In `commands/status.md`, add `` `/writ` `` first in the command list. In `.writ/docs/model-tiers.md`, add `writ` to the `high` row in sorted order and change its count from 15 to 16. In `adapters/claude-code.md` § Tool Mapping → Quick Reference, set the `todo_write` row's second cell to `` `TodoWrite` `` and its Notes to "Native todo list; phases mirror here". Run `test_surfaces` and confirm it passes `[AC-2.5]`
- [x] 2.7 Verify. Run `uv run --python 3.9 pytest`, then `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, then `bash scripts/eval.sh` outside any sandbox. Confirm all four registration tests pass, both `--check` commands print `pass`, and eval reports 0 findings. Run `git diff --stat` and confirm no edits under `.claude/` or `.cursor/` `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Generated files.** `SKILL.md` comes from `bash scripts/gen-skill.sh`. `claude-code/CLAUDE.md` comes from `python3 scripts/gen-claude-md.py`. Change the generator or the manifest, then regenerate. A hand edit fails the `--check`. See technical-spec.md → ## Registration Edits.
- **Edit by heading.** Locate every edit by section heading or list text, never by line number. technical-spec.md → ## Registration Edits cites `commands/status.md` line 249 only for orientation. The list text is the anchor.
- **Manifest order.** `commands:` stays sorted by name, so `writ` sits between `verify-spec` and `writ-design`. `scripts/gen-skill.sh` renders categories in manifest order, so `entry` renders first with no script change. `scripts/gen-claude-md.py` has no category handling, so its TEMPLATE gains the "Start with" line instead. See spec.md → ## Business Rules (Expanded), Rules 8 and 9.
- **Count comments.** The cursor tree comment goes 32 to 33. The model-tiers `high` count goes 15 to 16. Check the current count before each edit. If it differs from these numbers, stop and report the mismatch.
- **Stale README sentence.** Task 2.5 replaces "Writ ships 32 commands, but you only need five." The spec gives no replacement wording. Drop the count rather than add a new hard-coded one.
- **Risks.**
  - A missed surface leaves one catalog without the front door. `test_catalogs` and `test_surfaces` catch it.
  - `check_manifest` in `scripts/eval.sh` fails for any `commands/*.md` with no manifest entry. Once Story 1's `commands/writ.md` exists, eval fails until task 2.2 lands. Land 2.2 before any eval run.
  - Task 2.5 completes the pointer sentence from `2026-10-22-prompting-guide`. If that sentence is absent, stop at 2.5 and report it. The prompting-guide spec owns that line.
  - The Claude Code `todo_write` row still maps to a file write (`Write(".writ/state/tracking.json")`). Until task 2.6 lands, `/writ` mirroring on Claude Code would write a file instead of using the native list.
- **Integration.** Story 1 wrote `commands/writ.md` and the command-section tests in `scripts/tests/test_front_door.py`. Story 2 adds the registration tests to that file. Story 3 adds the `scripts/eval-command-structure.py` rows, the issue Resolution, and the routing fixture.
- **Shadow path mapping.** In this story, "Upstream error" means a stale generated file. `test_catalogs` fails on it, and the fix is a regeneration. The missing routed-command case in technical-spec.md → ## Shadow Paths belongs to Story 1.
- **Source edits only.** Edit `commands/` and `adapters/` sources. `.claude/` and `.cursor/` are symlinks to them. Never edit those copies or run `install.sh` on this repo.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Upstream error)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (rules 8 Registration order, 9 Generated files are regenerated, 10 README, 11 Entry level, 12 Runtime)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (Platform maps `todo_write` to a file)

---

## What Was Built

**Implementation Date:** 2026-10-22

### Files Created

[None created]

### Files Modified

- **`.writ/manifest.yaml`** (`categories:`, `commands:`)
  - `- id: entry` / `label: "Start here"` is the first category. The `writ` entry (`file: commands/writ.md`, `category: entry`, the technical-spec purpose, `tags: [entry, routing]`) sits between `verify-spec` and `writ-design`; `commands:` stays sorted (33 entries).
- **`SKILL.md`** — regenerated by `bash scripts/gen-skill.sh`; the `### Start here` table with the `/writ` row renders first under `## Available Commands`. `--check` prints `pass`.
- **`scripts/gen-claude-md.py`** (TEMPLATE) — one line above the Commands table: `Start with `/writ "<what you want>"`: it restates the request and routes it to the right command.`
- **`claude-code/CLAUDE.md`** — regenerated by `python3 scripts/gen-claude-md.py` (33 commands, 8 agents); the "Start with" line and the `/writ` row. `--check` prints `pass`.
- **`codex/AGENTS.md.template`** (§ Available Commands) — `### Start here` table with `| `/writ` | `.codex/commands/writ.md` | … |` above `### Planning & Specification`; the purpose cell follows the file's truncation convention (74 characters plus `…`, as every truncated neighbour).
- **`README.md`** (§ Commands, § Quick Start) — § Commands gains a `### Start here` table with the `/writ` row above Planning. § Quick Start opens with "Type `/writ` followed by what you want:" and a two-line fenced example, then the prompting-guide pointer completed to end "then type `/writ` followed by what you want.", then `### What `/writ` routes to` over the unchanged five-row table; the "Writ ships 32 commands" sentence is dropped. The Cursor, Claude Code, and Codex install follow-up lines name `/writ "my feature"` (DEV-004).
- **`adapters/cursor.md`** (§ Directory Structure) — `│   │   ├── writ.md                # /writ` between `verify-spec.md` and `writ-design.md`, `#` column aligned; the count comment reads `(33)`.
- **`commands/status.md`** (Step 8 command allowlist; § Maintainer Note: Command Allowlist) — `/writ` first in the slash allowlist and `writ` first in the bare list (DEV-003).
- **`.writ/docs/model-tiers.md`** (§ Deriving a Command's `entry_level`, `high` row) — `writ` between `security-audit` and `writ-design`; count `(15)` → `(16)`.
- **`adapters/claude-code.md`** (§ Tool Mapping → Quick Reference) — `| `todo_write` | `TodoWrite` | Native todo list; phases mirror here |`; the `#### Verification record — 2026-10-22` tables are untouched (one changed line in the diff).
- **`scripts/tests/test_front_door.py`** (docstring "Registration section (Story 2)"; `test_manifest`, `test_catalogs`, `test_readme`, `test_surfaces`; helpers `read`, `first_equal`, `first_prefixed`, `first_containing`, `cells`, `manifest_block`, `manifest_entries`) — 432 lines; the two generator `--check` calls run through `subprocess.run` argv lists with `cwd=REPO_ROOT` and assert exit 0 with `pass` as the first stdout line.
- **`scripts/tests/test_gen_claude_md.py`** (`EXPECTED_FIXTURE`) — gains the "Start with" line and blank line in the template's position (DEV-005).
- **`scripts/tests/test_platform_neutral_names.py`** (`test_status_allowlists`, `test_cursor_tree`) — the allowlist anchors match the `create-spec` token instead of the line start; the expected tree order sorts by command name, since `writ-design.md` precedes `writ.md` by file name but follows it by name (DEV-005).
- **`.writ/specs/2026-10-22-front-door/spec-lite.md`** — Registration line and Files in Scope (S2) line amended for DEV-003, DEV-004, DEV-005.
- **`.writ/specs/2026-10-22-front-door/drift-log.md`** — Story 2 section (DEV-003 to DEV-005).

### Implementation Decisions

1. **Generated files regenerated, never hand-edited** — `SKILL.md` and `claude-code/CLAUDE.md` byte-match their generators (`--check` pass for both); the template edit lives in `scripts/gen-claude-md.py`, and its fixture test moves with it.
2. **`gen-skill.sh --check` first line** — the `Parser: pure-bash fallback` line is stderr; stdout's first line is `pass`, which is what `test_catalogs` pins for both checks, matching `test_platform_neutral_names.py`'s existing convention.
3. **Both `status.md` allowlists updated** — the Maintainer Note's own rule says to add a new command there, and `test_status_allowlists` checks the two lists together (DEV-003).
4. **Install follow-up lines name `/writ`** — they sit inside § Quick Start, which the contract rewrites around the front door; `/create-spec "my feature"` there would contradict the section's first line (DEV-004).
5. **Anchor fixes rather than exemptions** — the two pre-existing tests broke only because their anchors assumed `/create-spec` opened the lists and file-name order matched manifest order; re-anchoring keeps their intent and avoids an eval-exempt marker (DEV-005).
6. **Map-generator omissions treated as owned** — `README.md`, `adapters/claude-code.md`, and `.writ/docs/model-tiers.md` are named by tasks 2.4–2.6 and the contract; Gate 2.5 reported them as crossings and routed `review-agent`, which judged them justified.

### Test Results

**Verification:** Automated, test-first (`uv run --python 3.9 pytest scripts/tests/test_front_door.py` red: `4 failed, 5 passed`, each an assertion on the missing registration; green: `9 passed`).
**Coverage:** Not measured by the script (no coverage report; markdown, YAML, generator template, and test changes only).

- ✅ Targeted: `uv run --python 3.9 pytest scripts/tests/test_front_door.py scripts/tests/test_platform_neutral_names.py scripts/tests/test_gen_claude_md.py scripts/tests/test_prompting_guide.py` → 95 passed.
- ✅ Full pytest (3.9): 2805 passed, 2 skipped. Story 1's eight README-orphan failures are cleared.
- ✅ `bash scripts/gen-skill.sh --check` → `pass`; `python3 scripts/gen-claude-md.py --check` → `pass (33 commands, 8 agents)`.
- ✅ Bash tests: 45 run, 0 failed (`scripts/tests/test_eval_leanness.sh` green again).
- ✅ `bash scripts/eval.sh`: Findings 0, Run errors 0 (`.writ/state/eval-20261023-023410.md`); `check_manifest` and the leanness orphan from Story 1 are cleared. Non-blocking leanness WARNINGs (commands/agents/skills/adapters lines and chars past their justified ceilings) pre-date this spec on the phase branch.
- ✅ `git diff --stat`: no paths under `.claude/` or `.cursor/`.
- ✅ Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 4 crossings (`README.md`, `adapters/claude-code.md`, `.writ/docs/model-tiers.md`, `scripts/tests/test_gen_claude_md.py`), route review-agent. Gate 3 review-override: pass; ac-trace: 0 findings. Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: pass (the `subprocess` calls to `scripts/gen-skill.sh` and `scripts/gen-claude-md.py` give the file a project-script reference, clearing Story 1's `test_imports_no_source`). Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports). `python3 scripts/eval-leanness.py --root .` → `structural: []`.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-003, DEV-004, DEV-005)
- **Security:** Clean (markdown/YAML edits; test subprocesses use argv lists, `cwd=REPO_ROOT`, no `shell=True`)
- **Boundary Compliance:** all changes within Owned or justified Readable deviations; three crossings are map-generator omissions of files the story names, the fourth (`scripts/tests/test_gen_claude_md.py`) is a fixture that pins the template byte-for-byte.
- gate3-route: review-agent (outside_boundary README.md; outside_boundary adapters/claude-code.md; outside_boundary .writ/docs/model-tiers.md; outside_boundary scripts/tests/test_gen_claude_md.py). review-panel: unverifiable (platform_cannot_spawn_other_vendors). jev-shadow: unverifiable (no_api_key). arch-lint: none — see .writ/docs/architecture-lint.md.
- Reviewer recommendations, not drift: `test_readme` could pin that the five-row table sits under `### What `/writ` routes to`; `cells()` duplicates `first_table`'s split; `.writ/docs/model-tiers.md` still says "Applied to the 31 commands" (pre-existing staleness, outside this story).
- Coding agent and review agent ran as nested `general-purpose` spawns with the prompt templates from `agents/coding-agent.md` and `agents/review-agent.md`.

### Deviations from Spec

- **[DEV-003] `commands/status.md` Maintainer Note bare list also gains `writ`** — Severity: Small
  - Spec said: the slash allowlist adds `/writ` first.
  - Reality: both allowlists add it first.
  - Resolution: Auto-amended; spec-lite.md Registration line names both lists.
- **[DEV-004] README install follow-up lines and closing sentence point at `/writ`** — Severity: Small
  - Spec said: Business Rule 10 specifies the opening of § Quick Start only.
  - Reality: the three per-platform "Then in …" lines inside § Quick Start name `/writ "my feature"`.
  - Resolution: Auto-amended; spec-lite.md Registration line names the follow-up lines.
- **[DEV-005] Maintenance edits to two pre-existing test files outside the S2 file list** — Severity: Small
  - Spec said: `scripts/tests/test_front_door.py` is the only test file in scope.
  - Reality: `test_gen_claude_md.py`'s fixture and `test_platform_neutral_names.py`'s two anchors moved with the contracted edits.
  - Resolution: Auto-amended; spec-lite.md Files in Scope (S2) names them.
