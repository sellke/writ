# Story 1: The Contract — Anchor/Floor Vocabulary, Origin, Ceiling, and Lint Aliases

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer implementing ADR-024 (agent, command, and platform author)
**I want to** rewrite `## Model Tiers` in `system-instructions.md` (mirrored byte-identically in `cursor/writ.mdc`) and `.writ/docs/model-tiers.md` to state the `anchor`/`floor` vocabulary, the two-question tier derivation, origin capture, anchor-as-ceiling, the floor resolution order, the escalate-once rule, graceful degradation, and the `entry_level` field with its one-line entry notice — and teach `scripts/lint-skill.sh` the new grammar with a warned alias window for the old names
**So that** Stories 2, 3, and 5 migrate agents, adapters, and commands against vocabulary that already lives in the root contract, a new reader can derive every agent's tier from two questions without a theory section, and nothing already installed breaks when `orchestration`/`capability` are still on disk

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [ ] Given `system-instructions.md` § Model Tiers after the rewrite, when a reader who has not seen the assignment applies the two questions (Q1 decides for others → `anchor`; Q2 bounded and checked → `floor`) to the seven agents, then the section states the questions in ADR-024 Decision 2's form, the origin fields (`anchor.model`, `anchor.effort`, `anchor.platform` — read, never asked; stamped only on audit records and `escalated`/`degraded` lines), the ceiling rule, the floor resolution order (a) family tier below anchor → (b) effort below `anchor.effort` or `low` when unknown → (c) anchor with the "collapses to anchor, say so once, no `degraded`" rule, the escalate-once rule with its iteration accounting, and graceful degradation (unknown → warn, run at `anchor`), and `rg "advisory" system-instructions.md` within § Model Tiers returns no carrier prose for commands or skills. `[AC-1.1]`
- [ ] Given the rewritten § Model Tiers, when the section states the `entry_level` field, then it names the carrier (commands only, existing `---` frontmatter), the two derivation questions (Q1 spawns/locks/unverified judgment → `high`; Q2 durable artifacts → `standard`; else `any`), and the normative entry-check text of technical-spec §5 verbatim — one line, at most once per session, never a question, skipped when origin is `unknown`, with the plain self-assessment guidance for `high`/`standard`/`any`. `[AC-1.2]`
- [ ] Given `system-instructions.md` and `cursor/writ.mdc` after the rewrite, when `diff` is run over the two files with the mirror's `## Self-Dogfooding` appendix excluded, then the output is empty, and `bash scripts/eval.sh` reports the `prime-directive-sync` check clean and `Findings: 0`. `[AC-1.3]`
- [ ] Given a fixture file carrying `model_tier: anchor` or `model_tier: floor`, when `bash scripts/lint-skill.sh <fixture>` runs, then it exits 0 with no `model_tier` finding; given `model_tier: orchestration` or `model_tier: capability`, then it exits 0 and prints exactly one `⚠️` line naming the replacement (`anchor` / `floor`) and the release in which the alias is rejected; given `model_tier: fast` or `model_tier: n-1`, then it prints a `❌` finding naming `anchor` or `floor` and exits 1. `[AC-1.4]`
- [ ] Given a fixture file carrying `entry_level: high`, `standard`, or `any`, when `bash scripts/lint-skill.sh <fixture>` runs, then it exits 0 with no `entry_level` finding; given `entry_level: max`, then it prints a `❌` finding naming `high`, `standard`, `any` and exits 1. `[AC-1.5]`

## Implementation Tasks

- [ ] 1.1 Add `scripts/tests/test_lint_model_tier.sh` following the `fail`/`assert_*`/`mktemp -d` convention of `scripts/tests/test_merge_agents_md.sh`: write minimal SKILL.md-shaped fixtures under a temp dir and assert exit code plus output for each technical-spec §9 lint case — `anchor`, `floor` (exit 0, no finding); `orchestration`, `capability` (exit 0, one `⚠️` line naming the replacement and the rejection release); `fast`, `n-1` (exit 1, `❌`); `entry_level: high|standard|any` (exit 0); `entry_level: max` (exit 1, `❌`). Run it first and confirm it fails against the current `^(orchestration|capability)$` regex. `[AC-1.4, AC-1.5]`
- [ ] 1.2 Replace `lint_model_tier()` in `scripts/lint-skill.sh` (lines ~253–284) with the ADR-024 block from technical-spec §1: `case` on `anchor|floor` (pass), `orchestration`/`capability` (echo the `⚠️` alias warning, no violation increment), `*` (❌, increment `MODEL_TIER_VIOLATIONS`); add the `elif` branch for `^entry_level:` validating `^(high|standard|any)$`. Rewrite the header comment to drop the "advisory (skill and command frontmatter)" framing, name the release in which the two alias branches flip to `*`, and keep the whole-file scan and first-non-identifier capture stop unchanged. Re-run the test from 1.1 until it passes. `[AC-1.4, AC-1.5]`
- [ ] 1.3 Rewrite `## Model Tiers` in `system-instructions.md` (line ~266) against ADR-024 Decisions 1–7 and Amendments A1–A3: replace the ADR-016 link and the "agent-as-carrier, relative-not-absolute, staged 2-band resolver" framing; state the two tiers, the Q1/Q2 derivation table, origin capture (§2 fields, read-never-asked, stamp sites), anchor-as-ceiling, the §3 resolution order with the collapse rule, the escalate-once rule with the `loop.max_iterations` pair-counts-once sentence, `model:` as concrete override, and the degradation table (unset → inherit; alias → warn, resolve as its new name; unknown → warn, run at `anchor`). Delete every sentence describing commands or skills as `model_tier` carriers, including the "Enforcement boundary" advisory paragraph and the Skills/Commands bullets under "Carrier per file type". Do not add a line to `commands/_preamble.md`. `[AC-1.1]`
- [ ] 1.4 In the same § Model Tiers, add the `entry_level` subsection: carrier (commands only, existing `---` frontmatter, after `outcome:`), values `high | standard | any`, the two derivation questions from Business Rule 8, and the normative entry-check blockquote from technical-spec §5 copied verbatim (including the exact one-line notice text and the `high`/`standard`/`any` self-assessment guidance). State that commands do not repeat this text. `[AC-1.2]`
- [ ] 1.5 Mirror the rewritten section into `cursor/writ.mdc` (line ~260) byte-for-byte, leaving the trailing `## Self-Dogfooding` appendix untouched; then rewrite `.writ/docs/model-tiers.md` to match the new contract — replace "The Two Named Tiers", "Native Relative Resolution Per Platform", and "Allowed Values" with the anchor/floor vocabulary, the two-question tables (tier and `entry_level`), the origin fields, the resolution order, the escalation rule, and the alias window; point references at ADR-024 and mark ADR-016 as superseded history only. `[AC-1.1, AC-1.2, AC-1.3]`
- [ ] 1.6 Verify: `diff <(sed '/^## Self-Dogfooding/,$d' cursor/writ.mdc) system-instructions.md` is empty; `bash scripts/tests/test_lint_model_tier.sh` passes; `bash scripts/lint-skill.sh skills/*/SKILL.md` is clean; `bash scripts/eval.sh` (run outside the sandbox — it does `git init` in a temp dir) ends `Findings: 0` with `prime-directive-sync` clean; `rg "orchestration|capability" system-instructions.md cursor/writ.mdc .writ/docs/model-tiers.md` returns only the alias-window sentences. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

**The mirror constraint.** `cursor/writ.mdc` is `system-instructions.md` plus an appended `## Self-Dogfooding` section. Outside that appendix the two must be byte-identical; `eval.sh`'s `prime-directive-sync` check enforces the Prime Directive slice, and the spec's Success Criteria require the full § Model Tiers slice to match. Edit `system-instructions.md` first, then copy the section — never author the mirror independently.

**The preamble cap.** `commands/_preamble.md` is at its 95-line hard cap. The contract text lands in `system-instructions.md` § Model Tiers (already the convention's home, paid once per invocation), not the preamble. Commands do not repeat the entry-check text; Story 5 adds only the `entry_level:` declaration.

**The alias window.** `orchestration`→`anchor` and `capability`→`floor` are warned (exit 0) until the next minor release after this spec ships, then rejected. The header comment in `lint-skill.sh` must name that release so the flip is a two-line change (move both alias branches into `*`). Until Story 2 lands, all seven `agents/*.md` still carry the old values — the lint must warn, not fail, or the repo's own gate breaks between stories. `lint_model_tier()` scans the whole raw file regardless of fences; the new `entry_level` branch anchors on `^entry_level:` so prose mentions in this spec or the docs do not trip it.

**What this story does not touch.** No agent file, `.writ/manifest.yaml`, adapter, `commands/*.md` frontmatter, `claude-code/agents/`, or `codex/agents/` changes here — those are Stories 2, 3, 5. ADR-016 is not edited beyond its existing supersession header (Business Rule 11). No `.writ/state/` file is introduced for origin (Business Rule 3).

**Risks.** (1) Under-specifying the collapse rule — a floor that resolves to anchor because the origin is already at the family floor is *correct*, and the text must say no `degraded` line is emitted, or Story 3's tables and Story 4's escalation sites will encode it as a failure. (2) The `entry_level` text is the only place the notice wording lives; Story 5's `require_literal` pins and the user-facing line depend on it being copied verbatim from technical-spec §5. (3) `rg "model_tier" commands/ skills/` → 0 is a Story 2 success criterion, but the *prose* that licensed those carriers is removed here — leave any sentence in place and Story 2's removal looks like a regression against the contract.

**Integration.** Stories 2 (agents/manifest/scaffolders), 3 (adapters + Cursor verification), and 5 (`entry_level` declarations + entry check) all cite this vocabulary and depend on this story alone; Story 4 depends on 2 and 3. Land this first. Story 5 extends the `entry_level` lint with the non-blocking eval presence note — the lint grammar itself ships here.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Lint (alias value), Lint (unknown value), Resolve floor (origin at family floor), Read origin]
- **Shadow paths:** [Nil origin]
- **Business rules:** [1 — only agents carry `model_tier`; `anchor`/`floor` with warned aliases, 2 — tier derived by Q1/Q2, 3 — origin is read never asked; stamped on audit and `escalated`/`degraded` lines, 4 — anchor is the ceiling, 5 — floor resolves at or below origin (a)(b)(c) with collapse rule, 8 — commands carry `entry_level` by two questions, 9 — entry check is one line once per session never a question]
- **Experience:** [Entry point (agent author sees `anchor`/`floor` with the two questions one link away; command author sees `entry_level`), Feedback model (lint warns on `orchestration`/`capability` by their new names; the one-line entry notice text), Error experience (nothing hard-fails; every path degrades to `anchor` = `inherit`), State catalog (Origin already at family floor, Alias value in a file, Unknown tier value)]

Reference: `.writ/docs/context-hint-format.md`.
