# User Stories: Retire Dead Prescription

> **Status:** Not Started — 0/6 stories, 0/38 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Correct the False Frontmatter Claim](./story-1-frontmatter-claim-correction.md) | Not Started | 5 | 0/5 | None |
| 2 | [Deprecate the Ordinal-Offset Reservation](./story-2-ordinal-offset-deprecation.md) | Not Started | 7 | 0/7 | Story 1 |
| 3 | [Resolve `required_skills:` by Adoption](./story-3-required-skills-adoption.md) | Not Started | 6 | 0/6 | Story 2 |
| 4 | [Reconcile `.writ/manifest.yaml`](./story-4-manifest-reconciliation.md) | Not Started | 6 | 0/6 | None |
| 5 | [Formally Deprecate `decisions.md`](./story-5-decisions-md-deprecation.md) | Not Started | 7 | 0/7 | None |
| 6 | [Retire the Prose-Note Carrier in the Explainer and the Lint](./story-6-model-tiers-doc-and-lint-branch.md) | Not Started | 7 | 0/7 | Story 2 |

## Dependency Graph

```
Story 1 (Frontmatter claim)
   └── Story 2 (Ordinal deprecation)
          ├── Story 3 (required_skills adoption)
          └── Story 6 (model-tiers.md + lint-skill.sh carrier)   ← parallel with Story 3

Story 4 (Manifest reconciliation)   ─┐
Story 5 (decisions.md deprecation)  ─┴── independent of the chain and of each other
```

**Stories 1, 2, and 3 are serialized by file overlap, not by logic.** All three edit `system-instructions.md` and its full mirror `cursor/writ.mdc` — Stories 1 and 2 both inside `## Model Tiers`, Story 3 inside `## Skills`. Nothing in Story 2's content depends on Story 1's outcome; the ordering exists because concurrent edits to the same two files would conflict, and because each story owes a manual mirror diff that a parallel branch would invalidate.

**Story 6 depends on Story 2 for the same reason.** It edits `.writ/docs/model-tiers.md` and `scripts/lint-skill.sh`, both of which Story 2 also edits — including `.writ/docs/model-tiers.md:97` and `lint-skill.sh`'s `usage()` block and `lint_model_tier()` comment block, where Story 2 owns the ordinal half and Story 6 owns the prose-note half. Story 6 touches neither `system-instructions.md` nor `cursor/writ.mdc`, so it is parallel-safe with Story 3 once Story 2 has landed.

**Stories 4 and 5 touch disjoint files** (`.writ/manifest.yaml`; `.writ/product/decisions.md`) and can run at any time, in parallel with the chain or with each other. Story 2's single manifest edit is a one-line schema *comment* at `.writ/manifest.yaml:227`; Story 4's is `metadata.version` at line 4. They do not collide, but if both are in flight, land Story 4 first and let Story 2 re-locate by literal.

**Suggested execution order:** Stories 4 and 5 first — they are the cheapest, fully independent, and prove the per-story `Findings: 0` discipline before the chain starts. Then 1 → 2 → (3 ‖ 6).

## Approved scope addition — 2026-08-11

Story 6 was added after the package was written, by maintainer decision. The same *"commands have no frontmatter mechanism / verified 0/31 files"* claim that clause (a) of the locked contract corrects in `system-instructions.md` also lives in two further live prescribing artifacts — `.writ/docs/model-tiers.md:45` (the user-facing carrier table) and `scripts/lint-skill.sh:279-280` (a regex branch that exists only to parse the prose note). The locked Contract block is unchanged; the addition is recorded in `spec.md` → Detailed Requirements → "(f) Approved scope addition, 2026-08-11".

Story 1's original Tasks 1.5 and 1.6 covered exactly those two files and were **transferred to Story 6** so a single story owns them (Story 1 drops from 7 tasks to 5). Task 1.6 had left the lint branch's removal optional; Story 6 decides it.

## Open conflict — `commands/new-command.md` is double-claimed

Story 1's Task 1.4 converts `commands/new-command.md`'s Model tier note (lines 145–151, 171) from a prose note to frontmatter guidance. The sibling Phase 10 spec `2026-08-11-component-contract` claims the same edit in its own Story 1 (Task 1.6), and its `spec.md:122` states the prose-note *format* "stays locked" and that relocating `model_tier` into frontmatter "is not this spec's decision." That spec declares this one as its dependency (`spec-deps.py` order: `retire-dead-prescription` → `component-contract`), so it lands **second** and would restate the carrier this spec retires.

This is a single-writer-per-file violation with contradictory intent, not a merge-order problem, and it needs a maintainer ruling before either Story 1 starts. Story 6 does not touch `commands/new-command.md` and its Task 6.3 measures that file's actual behavior before describing it, so the conflict cannot silently propagate into `.writ/docs/model-tiers.md`.

## Historical records that are never edited

`.writ/decision-records/adr-016-model-tier-delegation.md:76` and `CHANGELOG.md:143` both carry the "no frontmatter mechanism / verified 0/31 command files" wording. Both correctly describe what was true on 2026-07-10 when the model-tier work shipped. Business Rules 3 and 8 forbid rewriting either. No story in this spec claims them.

## Quick Links

- [spec.md](../spec.md) — locked contract, business rules, detailed requirements, out of scope
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — measured line-by-line edit surface, mirror constraint, error/shadow/edge-case tables

## The constraint that has no gate

`cursor/writ.mdc` mirrors `system-instructions.md` in full (300 lines verbatim, plus a 10-line Writ-repo-only appendix and a 3-line Cursor header). The `prime-directive-sync` eval check diffs **only** the `## Prime Directive` section. Every line Stories 1, 2, and 3 touch lives outside that section, so a story can edit one file, skip the other, and still see `Findings: 0`.

This is the spec's likeliest silent failure. Each of the three stories carries an explicit mirror-diff task for exactly this reason.

## Contract-vs-repo discrepancies carried into the stories

Two literals in the locked contract do not match the repository as measured. Both are documented in `spec.md` → Contract reading notes; neither changes any deliverable.

- **`.writt/product/decisions.md`** (contract clause d) is a typo for `.writ/product/decisions.md`. Story 5 targets the real path.
- **"45 `file:` entries"** (contract clause c) is a raw grep count. 44 are data entries — 31 commands + 7 agents + 6 skills; the 45th occurrence is inside a YAML schema comment at `.writ/manifest.yaml:225`. `.writ/product/roadmap.md:343` states 44. Story 4 reconciles the 44.

## Baseline

`bash scripts/eval.sh` → `Findings: 0`, measured 2026-08-11 before any story started (report: `.writ/state/eval-20260811-200730.md`). `bash scripts/gen-skill.sh --check` → exit 0. Every story must return to both.
