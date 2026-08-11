# Story 1: Contract Schema and Authoring Template

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer authoring a new Writ command
**I want to** the component contract to be documented once and mandated by `commands/new-command.md` itself, with the two documents that claimed the mandate already existed corrected in place
**So that** every command written from this point forward is born compliant, the 30-file migration has a fixed schema to author against instead of 30 chances to invent a variant, and the governing record says what was actually measured rather than what was assumed

## Acceptance Criteria

- [ ] Given `.writ/docs/component-contract.md` does not exist today, when this story lands, then it documents the schema for both carriers (command frontmatter and agent fenced block), the fixed key order, the swap test, the restatement test, the observable requirement, and the line budget with its derivation — at the density and length of the sibling `.writ/docs/model-tiers.md`, not as a second copy of the spec.
- [ ] Given `commands/new-command.md`'s generated-command structure table currently has six rows and no Completion row, when this story lands, then the table includes a **Completion** row placed between "Integration with Writ" and "References".
- [ ] Given the generated file's quality bars say nothing about frontmatter today, when this story lands, then they state the three required fields, the fixed key order (`name`, `description`, …existing keys…, `problem`, `outcome`, `exit_criteria`), and the 7-line ceiling.
- [ ] Given `new-command.md`'s Model tier note is owned by the dependency spec `2026-08-11-retire-dead-prescription` (locked contract clause (a); its Story 1 Task 1.4), when this story lands, then `git diff` shows this story made **zero** changes to the Model tier note (Step 2.1) or the Step 2.2 model-tier checklist bullet — and, because the dependency lands first, the note it reads already prescribes frontmatter rather than a prose note.
- [ ] Given the authoring coaching must be usable rather than exhaustive, when this story lands, then `new-command.md` carries the swap test, the restatement test, and one contrasting example pair, and defers the full rules to `.writ/docs/component-contract.md` by reference rather than restating them.
- [ ] Given `commands/new-command.md` is the exemplar the other 30 commands are authored against, when this story lands, then it carries its own `problem:` / `outcome:` / `exit_criteria:` derived from what it actually does, each entry passing the swap and restatement tests, within the 7-line ceiling — and its existing `## Completion` section is unchanged unless it contradicts the new `exit_criteria`.
- [ ] Given `.writ/decision-records/adr-020-component-contract.md` asserts a `## Completion` mandate that does not exist, when this story lands, then the ADR carries a dated `## Amendments` section placed immediately before `## References` and following ADR-009's convention (`### 2026-08-11 — <title>` with **Correction:** / **Rationale:** / **Measured:** / **Originating work:**), recording that `Completion` occurs exactly once in `commands/new-command.md` (line 202, its own heading), that the structure table at lines 136–143 has six rows and no Completion row, that this was measured on 2026-08-11 during spec authoring and independently re-verified by @AdamSellke, and that the decision is unaffected — **and** its Date line reads `> **Date:** 2026-08-11 (amended 2026-08-11 — see Amendments)`.
- [ ] Given the false premise also sits inline in three places in ADR-020, when this story lands, then all three are replaced in place with the exact after-text in spec.md → *ADR-020 and roadmap premise corrections*: the Decision sentence about `## Completion` (no longer "already mandates"), the `### The finding that reframed the decision` heading and its "contract is not missing; it is **unenforced**" paragraph, and the Consequences bullet that says "closing a template violation" — while `diff` confirms Decision items 1–3 and the `| Commands with a `## Completion` section | **13 of 32** |` measurement row are byte-for-byte unchanged.
- [ ] Given `.writ/product/roadmap.md` Phase 10 asserts the same violation twice, when this story lands, then line 316's trailing clause reads "an emergent convention: `new-command.md` does not mandate it and nothing checks it" (the verified `**13 of 32**` untouched), line 330 reads "carry a `## Completion` section, and `new-command.md` mandates it for generated commands (18 sections written; the mandate is created, not enforced)", and the 2026-08-11 Revision Log row records the correction with a link to ADR-020's Amendments anchor.
- [ ] Given `2026-08-11-retire-dead-prescription` cites `.writ/product/roadmap.md:341` and `:343` by line number, when this story lands, then `git diff --numstat -- .writ/product/roadmap.md` reports equal added and deleted counts and `wc -l .writ/product/roadmap.md` still returns 424 — every roadmap edit is a one-line-for-one-line replacement, and the Revision Log correction is appended to the existing 2026-08-11 row rather than added as a new one.
- [ ] Given the false framing must not survive in this spec's own history, when this story lands, then no commit message, changelog entry, or file this story writes contains the strings "template violation", "19 files", or "unenforced" as a description of the `## Completion` state.
- [ ] Given no eval check belongs to this spec, when this story lands, then `git diff --name-only` shows zero files under `scripts/`, and the only files outside `commands/` and `.writ/docs/` are `.writ/decision-records/adr-020-component-contract.md` and `.writ/product/roadmap.md`.

## Implementation Tasks

- [ ] 1.1 Read `commands/new-command.md` end to end, plus `.writ/docs/model-tiers.md` and `.writ/docs/skills.md` for the reference-doc density bar; re-verify the finding before editing anything that depends on it — `grep -n 'Completion' commands/new-command.md` must return exactly one line (202), and `sed -n '136,143p' commands/new-command.md` must show six table rows with no Completion row. If either check disagrees, stop and escalate: the amendments in tasks 1.8–1.9 assert a measurement, and asserting a stale one repeats the exact defect they correct
- [ ] 1.2 Write `.writ/docs/component-contract.md` — schema for both carriers, key order, the two authoring tests with one contrasting example pair, the observable-requirement grammar, the line budget with its 31×7 + 7×7 + 18×14 = 518 derivation, the honest statement that `exit_criteria` is only nominally machine-checkable and why the field still earns its lines, and a pointer to ADR-020
- [ ] 1.3 Add the **Completion** row to `new-command.md`'s generated-command structure table, between "Integration with Writ" and "References"
- [ ] 1.4 Add the frontmatter contract to the generated file's quality bars — three fields, fixed key order, 7-line ceiling
- [ ] 1.5 Add compact `exit_criteria` coaching (swap test, restatement test, one contrasting pair) that references `.writ/docs/component-contract.md` instead of restating it
- [ ] 1.6 Verify with `git diff commands/new-command.md` that this story changed **nothing** in the Model tier note or the Step 2.2 model-tier bullet — both belong to the dependency spec `2026-08-11-retire-dead-prescription`. If those lines still prescribe a prose note when this story runs, the dependency did not land as ordered: stop and escalate rather than fixing it here
- [ ] 1.7 Author `new-command.md`'s own three fields; apply the swap test against at least three other command files and the restatement test against its own `description:`; confirm the frontmatter grew by ≤7 lines and `grep -c '^---$'` still returns 2
- [ ] 1.8 Amend `.writ/decision-records/adr-020-component-contract.md` — apply the four in-place replacements (Date line, the Decision `## Completion` sentence, the `### The finding that reframed the decision` heading plus its false paragraph, the Consequences "template violation" bullet) and add the `## Amendments` section before `## References`, all using the exact before/after text in spec.md → *ADR-020 and roadmap premise corrections*. Verify with `git diff` that Decision items 1–3 and the `13 of 32` measurement row show no changed bytes
- [ ] 1.9 Correct `.writ/product/roadmap.md` — replace line 316's trailing clause and line 330 one-for-one, and append the correction note to the existing 2026-08-11 Revision Log row (line 17). Verify `git diff --numstat -- .writ/product/roadmap.md` shows equal added/deleted counts, `wc -l` returns 424, and `grep -n 'template violation\|19 file\|already mandating' .writ/product/roadmap.md` returns nothing
- [ ] 1.10 Run `bash scripts/eval.sh` and confirm no new findings versus the pre-story baseline; run `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` and confirm `status: ok`; confirm `git diff --name-only` lists no path under `scripts/`

## Notes

**Technical considerations:**

- `.writ/docs/*.md` ships to installed projects via `install.sh`'s doc fan-out (`append_manifest_writ_docs`, `overlay_scan_flat_dir "$WRIT_SRC/.writ/docs"`). This doc is read by Writ *users* authoring their own commands, not only by this repo's maintainer — write it for that audience.
- The Model tier note is **not touched by this story at all** (ownership ruling, 2026-08-11). An earlier draft reasoned that the prose-note format was load-bearing for `lint-skill.sh` and `.writ/docs/model-tiers.md` and so should stay locked. That reasoning is now void: the dependency spec `2026-08-11-retire-dead-prescription` retires the carrier under its locked contract clause (a), and its Story 6 removes the `lint-skill.sh` branch and the `model-tiers.md` rows that were the stated dependency. Editing those lines here would re-lock what the dependency just retired.
- `new-command.md` is where the anti-boilerplate rules either take hold or do not. Coaching that reads as "fill in these three fields" reproduces the exact failure mode the contract exists to prevent. The coaching must lead with the tests, not the schema — the schema is in the doc.
- Do not add `status:` / `evidence:` (ADR-014 vocabulary) here. ADR-020 mentions extending them to commands and agents, but that belongs to the governor spec, not this one.
- **The two premise amendments were added to this story on 2026-08-11 by maintainer approval**, after the contract was locked. The `## Contract (Locked)` block in `spec.md` is deliberately unchanged; the addition is recorded in `spec.md` → § Approved Scope Additions. The work size is unchanged — 18 `## Completion` sections either way. Only the framing moves: this story *creates* the mandate.
- **Amend, do not delete.** ADR-020's Decision is correct and stands. An amendment that removed the "finding" subsection outright would erase the reasoning trail and make the ADR read as if the premise had never been claimed — which is the same class of harm as leaving it false. Replace the false sentences, keep the true tooling-inventory sentence verbatim, and let the `## Amendments` entry carry the history.
- **The roadmap edits must be line-count neutral.** `2026-08-11-retire-dead-prescription` cites `.writ/product/roadmap.md:341` and `:343`. Adding a Revision Log row would shift both by one and silently break a sibling spec's evidence. Append to the existing 2026-08-11 row instead.
- **The `13 of 32` figures in both files are verified and correct.** They count the raw `commands/*.md` file list. This spec's own table says `13 of 31` because it counts commands only, excluding `_preamble.md`. Both are true; `2026-08-11-governor-instrumentation` `user-stories/story-3-completion-presence-check.md:37` explicitly instructs that neither be "corrected." Only the *clauses about a mandate* are false.

**Risks / challenges:**

- Scope creep into rewriting `new-command.md`. Four edits plus its own frontmatter. Its Phase 1 discovery flow, its AskQuestion block, its Core Rules, and its category table are untouched.
- Over-writing `.writ/docs/component-contract.md`. A reference doc that runs longer than this spec is itself a token tax, in a phase whose purpose is reducing prose. Match `model-tiers.md`.
- The temptation to also fix `system-instructions.md`'s copy of the same false claim. That is `2026-08-11-retire-dead-prescription`'s work; touching it here creates a merge conflict with the dependency spec.
- **Scope creep from the ADR amendment into a re-decision.** The premise is wrong; the decision is not. Reopening the carrier choice, the field set, or the 2026-11-11 review trigger under cover of "while we're in here" turns a correction into an unreviewed architecture change.
- **The same temptation for the two sibling specs that repeat the premise** — `2026-08-11-governor-instrumentation` `spec.md:19` and `:49`, `2026-08-11-loop-bounds` `spec.md:26`. Editing another spec's locked contract is not this story's authority. The ADR-020 amendment is the record; flag it, do not fix it (spec.md → Out of Scope).

**Integration points:**

- Stories 2–5 and Story 7 all author against the schema this story fixes. A late schema change costs 37 files of rework.
- Story 6 depends on the `## Completion` shape guidance this story writes into `.writ/docs/component-contract.md` and `new-command.md`.
- `2026-08-11-governor-instrumentation` builds its `structural` checks against this schema — key names and nesting settled here become that spec's grammar. It also inherits the false premise in its own prose (`spec.md:19`, `:49`); the ADR-020 amendment this story writes is what a reader of that spec should land on.
- `.writ/decision-records/adr-020-component-contract.md` and `.writ/product/roadmap.md` are newly claimed by this spec as of 2026-08-11. Verified against all four sibling Phase 10 specs: none writes to either file. `2026-08-11-retire-dead-prescription` explicitly disclaims editing ADR-020 (`user-stories/story-1-frontmatter-claim-correction.md:50`) and reads the roadmap without writing to it.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/eval.sh` shows no new findings
- [ ] `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok`
- [ ] Reviewed against Business Rules 1–6, 9, 10
- [ ] `.writ/docs/component-contract.md` reviewed for density against `.writ/docs/model-tiers.md`
- [ ] ADR-020 diff reviewed: `## Amendments` present, Decision items 1–3 and the `13 of 32` row unchanged
- [ ] `.writ/product/roadmap.md` diff reviewed: line count 424, added lines equal deleted lines, no "template violation" / "19 file" / "already mandating" strings remain

## Context for Agents

- **Business rules:** [BR1 swap test, BR2 restatement test, BR3 observable requirement, BR4 line budget, BR5 one-line fields, BR6 no carrier normalization, BR9 no eval checks, BR10 no substance rewrite] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [`commands/new-command.md` updates (four edits); ADR-020 and roadmap premise corrections (exact before/after text); Schema documentation] — from spec.md → ## Detailed Requirements
- **Approved scope addition:** [2026-08-11 — ADR-020 and roadmap premise corrections, approved by @AdamSellke; contract block deliberately unchanged] — from spec.md → ## Approved Scope Additions
- **Technical concerns:** [The ADR's premise is wrong, the spec must not inherit it, and two sibling specs already have] — from spec.md → ## Technical Concerns
- **Contract:** [Must include: "`commands/new-command.md` updates so newly authored commands are born compliant"] — from spec.md → ## Contract (Locked)
- **Technical spec:** [`commands/new-command.md` — Exact Edit Set; `.writ/decision-records/adr-020-component-contract.md` and `.writ/product/roadmap.md` — Exact Edit Surface; `.writ/docs/component-contract.md`] — from sub-specs/technical-spec.md
