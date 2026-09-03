# Story 2: Agents, Manifest, and Scaffolders — Rename Tiers, Retire "fast", Replace the Advisory Carrier

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer implementing ADR-024 (agent, command, and platform author)
**I want to** migrate the three carrier families — the seven `agents/*.md` configuration blocks, the `.writ/manifest.yaml` agent entries, and the two scaffolders — onto the Story 1 vocabulary (`anchor`/`floor`), remove every hardcoded `model: "fast"`, and make `/new-command` emit `entry_level` instead of the inert advisory `model_tier`
**So that** every agent's tier is a value the adapters (Story 3) can resolve against the user's origin, no file asserts a Cursor model value ahead of Story 3's verification, and newly scaffolded commands and skills are born on the new contract rather than needing a second migration.

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given the seven `agents/*.md` files, when the tier rename lands, then `rg "model_tier:" agents/` returns exactly 7 hits whose values are `anchor` for `coding-agent`, `review-agent`, `testing-agent`, `visual-qa-agent`, `documentation-agent` and `floor` for `architecture-check-agent`, `user-story-generator` — matching `spec.md` → *Tier derivation applied* row for row — and `visual-qa-agent.md`'s value still sits inside its `yaml`-fenced `## Agent Specification` block rather than a new `---` header `[AC-2.1]`
- [ ] Given `architecture-check-agent.md` and `user-story-generator.md`, when the hardcoded model is retired, then `rg '"fast"' agents/` returns 0, neither Agent Configuration block contains a `model:` line, and each of the six `Task({...})` templates (one in `architecture-check-agent.md`, five in `user-story-generator.md`) carries exactly one comment stating the model is adapter-resolved from `model_tier: floor` rather than hardcoded `[AC-2.2]`
- [ ] Given the `.writ/manifest.yaml` agent entries, when they are migrated, then every entry carries `model_tier: anchor|floor` equal to the value in its `agents/*.md` file, no agent entry carries a `model:` key, the skills template comment no longer offers `model_tier`, and `bash scripts/gen-skill.sh --check` exits 0 against a regenerated `SKILL.md` whose Available Agents table reflects the tier (the generator no longer requires or renders a `model` field) `[AC-2.3]`
- [ ] Given `commands/new-command.md` and `commands/new-skill.md`, when the scaffolders are updated, then `rg "model_tier" commands/ skills/` returns 0, the generated-command frontmatter template in `new-command.md` emits `entry_level: <high|standard|any>` after `outcome:` accompanied by the Business Rule 8 two-question derivation note (Q1 spawns/locks/judges → `high`; Q2 durable artifacts → `standard`; else `any`), and `new-skill.md`'s template, example, and exit-criteria text emit no tier field at all `[AC-2.4]`
- [ ] Given the completed migration, when `bash scripts/lint-skill.sh` and `bash scripts/eval.sh` run, then lint exits 0 with zero deprecated-alias warnings originating from `agents/` or `.writ/manifest.yaml`, and eval reports `Findings: 0` `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write the migration check first, red before green: add `scripts/tests/test_model_tier_migration.sh` (alongside the existing `test_*.sh` files in `scripts/tests/`) that asserts (a) `rg "model_tier:" agents/` yields exactly 7 hits and each agent's value equals the *Tier derivation applied* table (5 `anchor`, 2 `floor`, by name); (b) `rg '"fast"' agents/` and `rg "model_tier" commands/ skills/` both yield 0; (c) every manifest agent entry's `model_tier` matches its agent file and no manifest agent entry has a `model:` key; (d) `rg "entry_level:" commands/new-command.md` ≥ 1. Run it and confirm it fails on the current tree `[AC-2.1, AC-2.2, AC-2.3, AC-2.4]`
- [ ] 2.2 Rename the tier in all seven Agent Configuration blocks: `orchestration` → `anchor` in `coding-agent.md`, `review-agent.md`, `testing-agent.md`, `documentation-agent.md` (plain fence, line ~12) and `visual-qa-agent.md` (`## Agent Specification`, `yaml` fence, line ~26 — edit in place, do not add frontmatter); `capability` → `floor` in `architecture-check-agent.md` and `user-story-generator.md` (line ~12). Verify each against the derivation table, not against the old value `[AC-2.1]`
- [ ] 2.3 Retire `"fast"`: delete `model: "fast"` from the Agent Configuration blocks of `architecture-check-agent.md` (line ~11) and `user-story-generator.md` (line ~11); in the six `Task({...})` templates (`architecture-check-agent.md` ~48; `user-story-generator.md` ~56, ~206, ~213, ~220, ~227) remove the `model: "fast",` argument and its `# mirrors model_tier: capability` comment, replacing with one comment per template — e.g. `# model: resolved by the platform adapter from model_tier: floor (ADR-024) — never hardcoded here`. Re-run `rg '"fast"\|capability' agents/` and expect 0 `[AC-2.2]`
- [ ] 2.4 Migrate the manifest and its generator together: in `.writ/manifest.yaml` agent entries (lines ~186–222) rename `model_tier` values to match Task 2.2 and delete every `model: fast|default|inherit` line; update the skills template comment (line ~228) to drop `model_tier` (skills carry neither field per technical-spec §1). Then adapt `scripts/gen-skill.sh`, which currently requires `model` (yq path line ~151, fallback parser line ~368, required-field check line ~484) and renders it in the Available Agents `Model` column (line ~639): read `model_tier` instead, require it non-empty, and rename the column to `Tier`. Regenerate with `bash scripts/gen-skill.sh` and confirm `--check` exits 0 `[AC-2.3]`
- [ ] 2.5 Rewrite `commands/new-command.md`'s scaffold guidance (lines ~152–162 "Model tier note" and the exit-criteria bullet at ~200): the frontmatter template becomes `name:` / `description:` / `problem:` / `outcome:` / `entry_level: <high|standard|any>` / `exit_criteria:`; the note states the two-question derivation from spec.md Business Rule 8 and that the value is *what the command expects the user to have entered at*, not what it runs at; drop the ADR-016 link in favor of ADR-024 and `.writ/docs/model-tiers.md` (Story 1's rewrite). Do not touch `new-command.md`'s own frontmatter — Story 5 owns `entry_level` declarations on existing commands `[AC-2.4]`
- [ ] 2.6 Strip the advisory carrier from `commands/new-skill.md`: remove the `model_tier: orchestration` line from the frontmatter template (~117) and the worked example (~173), and remove the `model_tier: orchestration — advisory only…` clause from exit criterion 1 (~266). Confirm `rg "model_tier" commands/ skills/` → 0 `[AC-2.4]`
- [ ] 2.7 Verify end to end: `bash scripts/tests/test_model_tier_migration.sh` green; `bash scripts/lint-skill.sh` exits 0 with no `orchestration`/`capability` alias warnings from `agents/` or the manifest; `bash scripts/gen-skill.sh --check` exits 0; `bash scripts/eval.sh` (full permissions if sandboxed) reports `Findings: 0`. Record the four command outputs in the story's implementation summary `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

**Technical considerations**

- **The one non-uniform carrier.** Six agents use `## Agent Configuration` with a plain fence; `visual-qa-agent.md` uses `## Agent Specification` with a `yaml` fence. The value changes identically; the block does not. Do not normalize the heading or fence in this story — that is a separate, unrequested change.
- **Manifest → `gen-skill.sh` → `SKILL.md` → `eval.sh` is one chain.** `scripts/gen-skill.sh` reads `.agents[].model` via yq, mirrors it in a bash fallback parser, treats it as a required field (exit 1 when empty), and renders it as the `Model` column of `SKILL.md`'s Available Agents table. `scripts/eval.sh` (line ~496) runs `gen-skill.sh --dry-run` and files a Finding when it fails. Dropping `model:` from the manifest as Business Rule 6 requires therefore **breaks the generator and the eval gate** unless `gen-skill.sh` is changed in the same task. `spec.md`'s Story 2 surface list omits `scripts/gen-skill.sh` and `SKILL.md`; this story adds them as a necessary consequence of Rule 6, not as scope creep — the alternative (keeping a stale `model:` mirror to appease the generator) is exactly what Rule 6 forbids.
- **Six template copies, not one.** `user-story-generator.md` repeats its `Task({...})` template five times (~56, ~206, ~213, ~220, ~227) plus one in `architecture-check-agent.md` (~48). Task 2.1's `rg '"fast"'` check is the only defense against missing one; run it after Task 2.3, not only at the end.
- **What replaces `model: "fast"` in the templates.** Nothing executable. The templates gain one comment pointing at adapter resolution. Story 3 decides the concrete Cursor value from observation (Business Rule 10) and writes it into `adapters/cursor.md`, never back into the agent files.
- **`new-command.md`'s frontmatter shape.** Existing commands use `---` / `name:` / `description:` / `problem:` / `outcome:` / `exit_criteria:` / `---`; technical-spec §1 places `entry_level` after `outcome:`. The current scaffold note (~152–162) shows only `name`/`description`/`model_tier` — bring it into line with the real shape while replacing the field.

**Risks**

- A missed template copy re-introduces `"fast"` into a spawn and Cursor's `Task` rejects it (spec Recommendations: the current tool already refuses `"fast"`). Mitigated by the rg-based test written first.
- Renaming manifest values without renaming agent-file values (or vice versa) leaves the two sources disagreeing; Task 2.1(c) asserts parity by name.
- Story 1's lint accepts the old values as aliases, so a partial rename passes lint with warnings only. AC-2.5 therefore requires *zero* alias warnings from `agents/` and the manifest — lint exit code alone is not sufficient evidence.

**Integration**

- **Story 1 (vocabulary):** this story cites `anchor`/`floor`, the two-question rule, and `.writ/docs/model-tiers.md` as Story 1 rewrote them. Land Story 1 first; otherwise `lint-skill.sh` rejects `anchor`/`floor` as unknown values.
- **Story 3 (adapters):** resolves the tier this story declares. Story 3's Cursor verification protocol (technical-spec §4, V1) spawns with `"fast"` deliberately to record the rejection — that is a test input in Story 3, not a file value, and does not conflict with `rg '"fast"' agents/` → 0.
- **Story 5 (entry_level on existing commands):** declares the field on all 31 commands and adds the lint grammar. This story only changes what `/new-command` *emits* into future commands; it does not declare `entry_level` on `new-command.md` or `new-skill.md` themselves, and it does not add the lint branch (technical-spec §1 regex is Story 1/5).
- **ADR-016 (Business Rule 11):** the `new-command.md` note currently links ADR-016; repoint to ADR-024 without editing ADR-016.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Lint (alias value), Lint (unknown value)]
- **Business rules:** [Only agents carry `model_tier`; values `anchor`/`floor` with `orchestration`/`capability` as warned aliases (Rule 1), Tier is derived by Q1/Q2 and no agent changes tier (Rule 2), `model:` remains the concrete override; manifest drops its stale `model:` mirror and keeps `model_tier` only (Rule 6), Commands carry `entry_level` derived by two questions (Rule 8), `"fast"` is retired everywhere; Cursor's floor value comes only from Story 3's observation (Rule 10), ADR-016 is history — not edited (Rule 11)]
- **Experience:** [Entry point (agent author sees `model_tier: anchor|floor`; command author sees `entry_level` in existing frontmatter), Feedback model (lint warns on `orchestration`/`capability` by their new names), State catalog (Alias value in a file — lint warns with the new name, resolves as today)]

Reference: `.writ/docs/context-hint-format.md`.
