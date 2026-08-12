# Story 1: Extract the Decomposition Pre-Pass to a Skill

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer running `/implement-phase` on a phase whose features are already specced
**I want to** stop paying 3,919 bytes for the decomposition pre-pass on every invocation that will never enter it
**So that** the largest single block of conditional procedure in the command lives in a capability file, and the naming and compression pattern for the two harder extractions is proven on the clean case first

## Acceptance Criteria

- [ ] Given `skills/` is a namespace shared with five sibling disclosure specs and `2026-08-12-disclosure-implement-story` fixes the convention, when this story starts, then the proposed name is checked against that spec's landed skills, against the six incumbents (`code-explanation`, `conventional-commits`, `error-rescue-mapping`, `gbrain-interop`, `safe-refactor-loop`, `tdd-cycle`), and against every `name:` under `commands:`, `agents:`, and `skills:` in `.writ/manifest.yaml` — and the final name is recorded in the story notes with the convention it follows
- [ ] Given skills are authored through `/new-skill` (Business Rule 9), when the skill is created, then `bash scripts/lint-skill.sh` exited 0 on the description **before** any file was written, and the resulting `SKILL.md` carries `disable-model-invocation: true`, `status: candidate`, and a `status_evidence:` line naming the extraction date, source section, and consumer count
- [ ] Given the source prose is a transcript of `/implement-phase`'s Step 1.2b (it names `/create-spec`, `--recommend`, and Step 2.3 by reference), when the skill is written, then it reads as a portable capability — *how to decompose a set of features into independently shippable specs* — with no line invoking a command, a slash command, another skill, or a subagent, and `bash scripts/lint-skill.sh skills/<name>/SKILL.md` exits 0
- [ ] Given Business Rule 3 forbids redesign, when the skill is written, then it carries all five analysis steps (analyze against the codebase, propose specs, draw the dependency graph, assign single-writer file ownership, name the seams), the proposal presentation format, and the rationale that boundaries are drawn at implementation time against the current codebase rather than stale plan-time assumptions — compressed in wording, unchanged in meaning
- [ ] Given none of the 20 eval anchors occurs in pre-spec lines 93–128 (verified in `sub-specs/technical-spec.md`), when this story lands, then re-running the anchor grep against `commands/implement-phase.md` still reports zero missing — trivially, because this story does not edit that file
- [ ] Given Business Rule 6 forbids any intermediate state of the command file, when this story lands, then `git diff --name-only` shows **zero** changes to `commands/implement-phase.md`
- [ ] Given Business Rule 1's hard skill-bytes cap was **retired** by the 2026-08-12 mechanism ruling, when this story lands, then the skill is authored to its source (≈3,600 B projected, not the pre-ruling ~2,614 B share) and its measured byte size is **recorded** in the story notes as an input to Story 5's path table — recorded, not scored against an allowance
- [ ] Given Business Rule 4 requires reachability, when this story lands, then the skill is registered in `.writ/manifest.yaml` under `skills:` in alphabetical position and `bash scripts/gen-skill.sh --check` reports no delta
- [ ] Given Business Rule 8 restricts this spec's edit surface, when this story lands, then `git diff --name-only` lists only `skills/<name>/SKILL.md`, `.writ/manifest.yaml`, and `SKILL.md` — no path under `scripts/` or `commands/`

## Implementation Tasks

- [ ] 1.1 Read `commands/implement-phase.md` lines 73–128 in full, plus `skills/safe-refactor-loop/SKILL.md` and `skills/error-rescue-mapping/SKILL.md` as the density and shape exemplars. Re-measure the source range: `sed -n '93,128p' commands/implement-phase.md | wc -c` must return ≈3,919
- [ ] 1.2 Reconcile the skill name (Business Rule 10). If `2026-08-12-disclosure-implement-story` has not landed, record that fact and the convention inferred from ADR-021 and the six incumbents; do not invent a divergent style
- [ ] 1.3 Run `/new-skill <name>` — capture the verb-phrase description, pass the pre-write lint, write `skills/<name>/SKILL.md`, append the manifest entry, run `gen-skill.sh --check`
- [ ] 1.4 Author `## Purpose` / `## When to Use` / `## How to Apply` from the source range, rewriting orchestration references out: `/create-spec` becomes "the project's spec-authoring command", Step 2.3 becomes "the caller's execution gate", `--recommend` becomes "an autonomous-authoring mode the caller may declare"
- [ ] 1.5 Carry the `--all` / autonomous-mode boundary as a capability-level rule ("creating specs requires human agreement unless the caller has explicit authorization to author autonomously"), so the command retains only the mode-specific wiring
- [ ] 1.6 Verify: `bash scripts/lint-skill.sh skills/<name>/SKILL.md` exits 0; `wc -c skills/<name>/SKILL.md` recorded against the budget; `bash scripts/gen-skill.sh --check` reports no delta
- [ ] 1.7 Confirm ownership: `git diff --name-only` shows no `scripts/` path and no `commands/` path

## Notes

**Technical considerations:**

- This is deliberately the first story because it is the **only extraction with zero eval anchors in its source range**. It proves the naming, the lint-clean capability rewrite, and the byte discipline before the same techniques are applied to prose the eval suite pins.
- The source range includes a fenced ``## Decomposition Proposal`` template. It is inside a code fence, so it is not a real heading — an editor that splits the file on `^##` will mis-slice it. Slice on the source line ranges, not on a heading regex.
- The five-step analysis is the substance. The presentation template is format. If the byte budget forces a cut, compress the template's example rows before touching any of the five steps — Business Rule 3 protects rules, not illustrations.

**Risks / challenges:**

- **Drifting into redesign while rewriting for lint compliance.** Removing `/create-spec` by name is required by `lint-skill.sh`; changing *when* specs are created is not. The single-writer-per-file ownership rule is the clause most likely to get softened into advice during a rewrite — it is the rule that keeps concurrent lanes from colliding on merge, and it stays normative.
- **Over-compressing to a number that no longer exists.** The pre-ruling budget forced this skill toward ~2,600 bytes; the 2026-08-12 ruling retired that cap because the compression pressure pushed straight against Business Rule 3 — the cheapest way to hit an aggressive byte target on normative prose is to soften a rule into advice. Author to the source at ≈3,600 B. Still well under the 6,000–10,000 B house range, but not at a size that trades a rule for bytes.
- **Name collision with a sibling spec that has not landed.** Business Rule 10 is a check, not a guarantee. Record the convention followed so a later rename is a mechanical fix rather than a judgment call.

**Integration points:**

- Story 4 loads this skill with a single inline `Read skills/<name>/SKILL.md` placed **inside** the decomposition pre-pass, after the branch that establishes unspecced features exist and the user approved decomposing them — not in Step 1.2's classification, which runs on every phase. That placement is what makes the skill's bytes genuinely unpaid on a phase whose features all resolve to existing spec folders, which spec.md names the clearest win in the phase.
- Story 5 measures this skill's bytes as part of `conditional_bytes`.
- `.writ/manifest.yaml` is appended by Stories 1, 2, and 3 in sequence — see `user-stories/README.md` for why these are not parallelized.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/<name>/SKILL.md` exits 0
- [ ] `bash scripts/gen-skill.sh --check` reports no delta
- [ ] Skill byte size recorded in the notes against the ≈7,841-byte three-skill budget
- [ ] `git diff --name-only` shows zero changes to `commands/implement-phase.md` and no path under `scripts/`

## Context for Agents

- **Business rules:** [BR1 path-dependent ceiling (hard skill-bytes cap retired), BR3 relocate-not-redesign, BR4 precise placement, BR8 ownership, BR9 `/new-skill` and lint, BR10 name reconciliation] — from spec.md → 📋 Business Rules
- **Mechanism ruling:** [inline `Read` replaces `required_skills:`; the hard skill-bytes cap is retired; this skill is the one that fires rarely] — from spec.md → ## Approved Scope Changes
- **Detailed requirements:** [What extracts, and where → `skills/phase-decomposition/SKILL.md`] — from spec.md → ## Detailed Requirements
- **Technical spec:** [Section Byte Ledger (lines 93–128); Skill Authoring; The 20 Blocking Anchors — none in this range] — from sub-specs/technical-spec.md
- **Contract:** ["Skills authored through `/new-skill` (born `status: candidate`, lint-clean)"] — from spec.md → ## Contract (Locked)
