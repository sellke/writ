# Story 3: Generated Codex Template

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Codex user with Writ installed in my project
**I want to** have the Writ block in `AGENTS.md` list every command, agent, and skill, and map every capability to Codex, without pointing at any file my project does not have
**So that** I can find and run any Writ capability from the one file Codex loads every session

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.4

- [ ] Given `.writ/manifest.yaml` (`categories:`, `commands:`, `agents:`) and every `skills/*/SKILL.md`, when the driver renders `codex/AGENTS.md.template`, then each `commands:` entry appears once in its category table with its manifest purpose and path `.codex/commands/<name>.md`, the `### Start here` table holding the `/writ` row is the first table under `## Available Commands`, each manifest agent appears under `## Available Agents` with path `.codex/agents/<name>.toml`, and each skill appears under `## Available Skills` with its frontmatter `description` and path `.agents/skills/<name>/SKILL.md` `[AC-3.1]`
- [ ] Given the rendered template, when it is read, then line 1 is the merge-marker comment byte-identical to the hand-maintained file's line 1, a generator comment names `scripts/gen-platform-trees.py`, the file contains no `adapters/` substring, `## Writ on Codex` points at the Capability Map below, and the sections appear in this order: Writ on Codex, Available Commands, Available Agents, Available Skills, Built-in Codex slash commands vs Writ, Capability Map, Catalog source `[AC-3.2]`
- [ ] Given the hand-maintained `codex/AGENTS.md.template` and the generator's output, when the two are diffed before the first write, then every dropped or changed sentence is recorded with its reason in a `## What Was Built` section of this story, and no sentence that is still true is missing from the generated file `[AC-3.3]`
- [ ] Given the regenerated template, when its byte size is measured and the merge and install suites run, then the file is under 16384 bytes, `scripts/tests/test_merge_agents_md.sh` passes, and every `scripts/tests/test_install_update_*.sh` passes `[AC-3.4]`

## Implementation Tasks

- [ ] 3.1 Write the failing `test_codex_template` in `scripts/tests/test_gen_platform_trees.py` (Python 3.9 stdlib): every `commands:` name, every manifest agent, and every `skills/*/SKILL.md` name appears in the rendered output; the `/writ` row sits under `### Start here`; no `adapters/` substring; size under 16384 bytes; the built-ins heading is present; line 1 equals the hand-maintained file's line 1. Run it and confirm it fails against today's hand-maintained template `[AC-3.1, AC-3.2, AC-3.4]`
- [ ] 3.2 Add `render_codex_template` to `scripts/gen-platform-trees.py`. It returns the file text and writes nothing. Inputs: the manifest (categories in manifest order with `entry` first, purposes verbatim), the `skills/` directory (names and frontmatter descriptions), the built-ins section as a literal string, and the Codex capability map from Story 2's map function. Place the generator comment on line 2, directly after the merge-marker line. Follow the manifest reading in `scripts/gen-claude-md.py` and the category-table rendering in `scripts/gen-skill.sh` `[AC-3.1, AC-3.2]`
- [ ] 3.3 Render to a temp file outside the repo and diff it against `codex/AGENTS.md.template`. In a new `## What Was Built` section of this story, record every dropped or changed sentence with its reason. Mark each as intended (stale command and skill lists, the `adapters/` clause, the purpose cuts) or a bug. Fix every bug and re-render. Do not write the repo file until this record exists `[AC-3.3]`
- [ ] 3.4 Add the codex target to the driver's write mode, so `python3 scripts/gen-platform-trees.py` writes `codex/AGENTS.md.template` and prints `wrote codex/AGENTS.md.template`. Write nothing when any reason exists. Run it once; that output is the baseline `[AC-3.2, AC-3.3]`
- [ ] 3.5 Rerun the 3.1 test until it passes. Confirm the generated file is under 16384 bytes (`wc -c`) and contains no `adapters/` (`grep -c 'adapters/'` returns 0) `[AC-3.1, AC-3.2, AC-3.4]`
- [ ] 3.6 Run `bash scripts/tests/test_merge_agents_md.sh` and each `bash scripts/tests/test_install_update_*.sh`. All must pass with the generated template. These tests use temp directories; do not run `install.sh` or `update.sh` against this repo `[AC-3.4]`
- [ ] 3.7 Run the full verification: `uv run --python 3.9 pytest`; `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` with no `FAIL` lines; `bash scripts/eval.sh` outside any sandbox. Record the eval findings count. The eval stale check for this file belongs to Story 4 `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`

## Notes

- **Front-door dependency.** The current `.writ/manifest.yaml` has no `entry` category and no `writ` command. The hand-maintained template has no `### Start here` table. All three arrive with `2026-10-22-front-door`, which is not yet committed. Do not start 3.1 to 3.5 until it lands, or the `/writ` assertion has nothing to render. This header lists only Story 2; add `2026-10-22-front-door` to Dependencies if the spec owner agrees.
- **Merge-marker line.** Line 1 is the contract that `install.sh` `merge_agents_md` and `update.sh` use to find `writ:start` and `writ:end`. Keep it byte-identical. Its "edit there, not by hand" wording still points maintainers at the template. With generation they should regenerate instead, and the generator comment on line 2 says so. Do not edit line 1.
- **Only `adapters/` mention.** The hand file mentions `adapters/` once, in the `## Writ on Codex` paragraph ("map tools via `adapters/codex.md`"). Replace that clause with "the Capability Map below". The Catalog source note has no `adapters/` reference.
- **Purpose text.** The hand file ends 19 table cells with `…`. The manifest holds the full purposes. Use the manifest text verbatim. Truncate only if the 16384-byte cap forces it; the technical spec estimates under 12 KiB. Each hand-file cut goes in the 3.3 record as an intended change.
- **Expected additions.** The hand file omits `create-goal`, `implement-phase`, `revert`, and `writ`. It lists 7 agents where the manifest lists 8. It lists 1 skill where `skills/` holds 16. The generated file adds these. They are not losses.
- **Skill source.** Skill names and descriptions come from `skills/*/SKILL.md`, not from the manifest's `skills:` list, which carries `status:` fields. The spec requires every `SKILL.md`.
- **Built-ins literal.** Copy the hand file's `## Built-in Codex slash commands vs Writ` section into the generator as a literal string, including its link. Change a sentence only when the 3.3 record gives a reason.
- **Size.** The cap is 16384 bytes (test). Codex's AGENTS.md budget is 32 KiB, so the cap is tighter than the platform limit on purpose.
- **Risks.** Dropping the built-ins section or a still-true sentence during the takeover (3.3 is the guard). Exceeding 16 KiB (the size test catches it). Moving the map above the built-ins section, which breaks the order in AC-3.2.
- **Integration.** Story 2 supplies the driver write path and the Codex map function. Story 4's `--check` will treat this file as generated, so the committed baseline from 3.4 must match a fresh render. `test_merge_agents_md.sh` pins the merge between the markers. The five `test_install_update_*.sh` files exercise install and update.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** []
- **Shadow paths:** `technical-spec.md → ## Shadow Paths` (Happy path, Nil input, Empty input)
- **Business rules:** `spec.md → ## Business Rules (Expanded)` (Rule 5 Capability Map section; Rule 8 Codex template composition and 16 KiB cap; Rule 12 generated-file comment; Rule 15 Python 3.9 stdlib only)
- **Experience:** `spec.md → ## Experience Design → ### State Catalog` (`Clean tree`, `Installed Codex project`)
