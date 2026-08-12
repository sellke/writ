# Story 4: Record and Snapshot Skills

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer extracting the three blocks that produce durable artifacts other commands read
**I want to** `what-was-built-authoring`, `project-context-snapshot` and `story-commit-provenance` authored as capability prose, with `project-context-snapshot` written from the start as a **shared** skill
**So that** roughly 9,400 bytes leaves the command, and the first skill that three commands will read is authored once with no consumer's vocabulary in it — rather than extracted for `implement-story` and re-forked twice when `implement-spec` and `status` reach the same block

## Acceptance Criteria

- [ ] Given `commands/implement-story.md` lines 670–733 and 842–956 specify extracting and formatting the What Was Built record, when this story lands, then `skills/what-was-built-authoring/SKILL.md` exists with `status: candidate`, carries the standard body sections, and `bash scripts/lint-skill.sh` reports it clean.
- [ ] Given lines 341–396 specify the `.writ/context.md` schema and lines 829–841 the commit-SHA record, when this story lands, then `skills/project-context-snapshot/SKILL.md` and `skills/story-commit-provenance/SKILL.md` exist on the same terms and lint clean.
- [ ] Given `commands/implement-story.md:343` states `.writ/context.md` is *"always fully regenerated … by `implement-story`, `implement-spec`, and `status`"* and ADR-021 point 4's `_preamble.md` route is closed at 93/95 lines, when this story lands, then `project-context-snapshot` is authored as a shared skill: no gate number, no step number, no command name, and `## When to Use` stated as trigger conditions ("after a story's status changes", "when reporting current project state") rather than as pipeline positions.
- [ ] Given the snapshot schema is consumed by `/status` and by every subsequent context load, when this story lands, then `project-context-snapshot` preserves the full markdown schema with all six sections, all four missing-source fallbacks (`mission-lite.md`, no active spec, absent-or-empty `drift-log.md`, absent `.writ/issues/`), the three Artifact Map rules including that **the Integrity line always renders**, its two states (`✅ all required present` / `⚠️ missing required: <list>`), and the **rewritten wholesale, never appended or patched, no separate index or pointer file** rule.
- [ ] Given `scripts/eval.sh:2721–2722` pins `## Artifact Map` and `**Integrity:**` to `commands/implement-story.md`, when this story lands, then both strings are still present in the command — Story 5 retains them as a one-sentence assertion, and this story must not treat the relocation as removing them from the file.
- [ ] Given the What Was Built record is read by `create-uat-plan`, `ship` and `revert`, when this story lands, then `what-was-built-authoring` preserves: all five extraction sources with their mandatory / best-effort marking; the `git diff --name-status` fallback for files; every named fallback value (`**Verification:** N/A`, `"None"`, `"Not assessed"`, omit-the-section); the DEV-ID preservation rule; the full formatting template with the omit-Implementation-Decisions-entirely-when-empty and `[None created]` / `[None modified]` rules; the append procedure with its `\n---\n\n` separator; the `--quick`-mode minimal record with its `> Note: Review skipped` banner; and **"The pipeline must NEVER block story completion due to incomplete WWB data. Partial records are better than no records."**
- [ ] Given `scripts/revert-resolve.py` treats the commit SHA as its highest-confidence resolution layer, when this story lands, then `story-commit-provenance` preserves: capture via `git rev-parse HEAD`; the `> **Commit:** <full-sha>` header placement beside `> **Status:**`; the **idempotent update-in-place, never duplicate** rule; the fold-into-the-following-bookkeeping-commit rule with its explicit **do not `--amend`** prohibition and the reason (amending rewrites the SHA just recorded); and the backward-compatibility rule that the field is optional and a missing SHA never fails a story.
- [ ] Given Business Rules 3 and 10, when this story lands, then none of the three skills contains a gate number, an agent-spawn sentence, `Read commands/`, `Read skills/`, a bare `Task(`, or a line-initial `/command` outside a fenced block, and all three `description:` values are bare-imperative verb phrases.
- [ ] Given this story is additive, when this story lands, then `git diff --name-only` lists only the three new `skills/*/SKILL.md` paths, `.writ/manifest.yaml`, and `SKILL.md`.

## Implementation Tasks

- [ ] 4.1 Read `commands/implement-story.md` lines 341–396, 670–733 and 829–956 in full, plus `.writ/docs/what-was-built-format.md` and `scripts/revert-resolve.py`'s four resolution layers — the SHA field's contract is defined by its consumer
- [ ] 4.2 Read how `commands/implement-spec.md` and `commands/status.md` refer to `.writ/context.md` today. `project-context-snapshot` must be authorable by them unchanged; anything in it that only makes sense from inside `implement-story` is a defect in this story
- [ ] 4.3 Check all three names and their head nouns against `.writ/manifest.yaml` per the collision protocol, then scaffold with `/new-skill`
- [ ] 4.4 Author `project-context-snapshot` — full schema, four fallbacks, three Artifact Map rules, the always-renders Integrity line, and the wholesale-rewrite rule. Consumer-neutral throughout
- [ ] 4.5 Author `what-was-built-authoring` — five extraction sources with mandatory/best-effort marking and fallbacks, the formatting template, the append procedure, the `--quick` minimal record, and the never-block rule
- [ ] 4.6 Author `story-commit-provenance` — capture, placement, idempotency, the bookkeeping-commit fold with the `--amend` prohibition and its reason, and backward compatibility
- [ ] 4.7 Apply Compression Ledger entries C1 (the 41-line worked "Example Coding Agent Context (with WWB)" block at L299–339, which illustrates a format specified at L274–286), C2 (the `what_was_built_data` JavaScript object literal at L712–728, which restates the formatting template's field list) and the remainder of C3, recording measured yield per entry. **If a target yields less than projected, record the shortfall — do not recover it by cutting a rule**
- [ ] 4.8 Run `bash scripts/lint-skill.sh` on all three; confirm `## Artifact Map` and `**Integrity:**` are still present in `commands/implement-story.md`; run `bash scripts/gen-skill.sh` and `--check`; record measured byte sizes against projections

## Notes

**Technical considerations:**

- `project-context-snapshot` is the first shared skill in Writ and the reason Business Rule 3 rule 5 exists. Getting it consumer-neutral now is what lets `implement-spec` and `status` **read** it at their own point of need later instead of forking it — the collision protocol's whole purpose. Written wrong, it becomes three near-identical skills and the namespace argument is lost in the first spec that made it.
- `what-was-built-authoring` and `dependency-context-loading` (Story 2) are the write and read halves of the same artifact. Neither may restate the other; `.writ/docs/what-was-built-format.md` is the shared authority they both point at.
- C1 is the single largest compression target in the spec at ~1,200 bytes. It is a worked example of an aggregation format specified twenty lines above it — the definition of a duplicate under Business Rule 2. It is also the target most likely to be defended as "helpful context", which is exactly what makes it worth naming here.
- The `--amend` prohibition in `story-commit-provenance` carries its reason inline (*"amending would rewrite the very SHA just recorded"*). Reasons that prevent a plausible-looking mistake are rules, not commentary.
- `> **Commit:**` already appears in the command's `exit_criteria` (frontmatter line 7), so pinned literal 10 is safe by construction. Verify it rather than assuming it.

**Risks / challenges:**

- **Authoring `project-context-snapshot` from `implement-story`'s perspective.** The source block sits inside Step 2 and refers to Step 4. Both references must go, and the skill has to read as though it had never lived in a command.
- **"Never block story completion" reads like reassurance and is a rule.** It governs every incomplete-data path in the block. Dropping it as a closing flourish changes behavior on exactly the runs where behavior matters most.
- **The mandatory / best-effort distinction across the five extraction sources.** Files Created/Modified is mandatory with a `git diff` fallback; Implementation Decisions is best-effort and omitted when missing; Review Result is mandatory and defaults to `"Unknown"`. Three different failure semantics that flatten easily into one.
- **The `--quick` minimal record is a second, smaller template**, not a degraded version of the first. It has its own banner and its own section list.
- **C1 and C2 are deletions, and deletions in a spec whose second business rule is "do not lose rules" attract scrutiny.** Record for each what remains that carries the same information and where it lives. A deletion with a citation is contraction; a deletion without one is drift.

**Integration points:**

- Story 5 replaces the source blocks with the Step 4 numbered list, a one-sentence `## Artifact Map` / `**Integrity:**` assertion, and a `> **Commit:**` provenance line, then places all three inline reads **at Step 4** — `project-context-snapshot` at item 3, `what-was-built-authoring` at item 4, `story-commit-provenance` at item 7. Two of those are deliberate moves away from the source block's position: the snapshot schema is *specified* in Step 2 but *used* in Step 4, and half of `what-was-built-authoring`'s source sits in Gate 3.5 — which `--quick` skips even though a `--quick` run still writes the minimal record. Reading it at 3.5 would leave that run writing a record whose rules never loaded.
- **All three are on the always-paid path.** Step 4 runs in every mode, so compression yield in these three skills is realized on every invocation. That is the argument for pursuing C1 and C2 here rather than treating them as optional.
- Story 6 walks inventory rows for lines 341–396, 670–733 and 829–956 against these three files, and separately confirms pinned literals 7, 8 and 10 survived in the command.
- `commands/implement-spec.md` and `commands/status.md` are **not** edited by this spec (Out of Scope). They inline-read `project-context-snapshot` at their own point of need when their own disclosure specs run — and `## When to Use` is what tells them where that is, so the shared-skill rule is doing load-placement work, not just style work.
- `scripts/revert-resolve.py` and `commands/revert.md` are unchanged consumers of both the SHA field and the WWB record's `> **Reverted:**` banner.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/*/SKILL.md` clean
- [ ] `bash scripts/gen-skill.sh --check` passes
- [ ] `bash scripts/eval.sh` shows no new findings
- [ ] Reviewed against Business Rules 2, 3, 4, 5, 10
- [ ] `project-context-snapshot` read once more with `implement-spec` and `status` in mind: nothing in it assumes `implement-story`
- [ ] C1, C2 and C3 yields recorded with a citation for what still carries each deleted item's information
- [ ] `git diff --name-only` shows no path under `commands/` or `scripts/`

## Context for Agents

- **Business rules:** [BR2 relocate-and-contract with its permitted-contraction list, BR3 naming convention including rule 5 on shared skills, BR4 reachability, BR5 pinned literals, BR10 capability prose] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The eight extracted skills — rows 3, 7, 8; "Skill 7 is the first shared skill and the reason Business Rule 3 rule 5 exists"] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [Per-skill scaffolding is a real, new, permanent cost; the ceiling is projected to regress] — from spec.md → ## Technical Concerns
- **Technical spec:** [Section Ledger rows for L341–396, L670–733, L829–956; Skill Specifications rows 3, 7, 8; Compression Ledger C1, C2, C3; Pinned Literals 7, 8, 10] — from sub-specs/technical-spec.md
- **Interaction edge cases:** [Reverted WWB records and their `ℹ️` line; `--quick` mode's minimal record] — from sub-specs/technical-spec.md → Interaction Edge Cases
