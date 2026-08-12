# User Stories: Component Contract

> **Status:** Complete — 7/7 stories, 51/51 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Contract Schema and Authoring Template](./story-1-contract-schema-and-authoring-template.md) | Complete | 10 | 10/10 | None |
| 2 | [Planning and Specification Command Contracts](./story-2-planning-command-contracts.md) | Complete | 7 | 7/7 | Story 1 |
| 3 | [Implementation and Recovery Command Contracts](./story-3-implementation-command-contracts.md) | Complete | 7 | 7/7 | Story 1 |
| 4 | [Quality and Release Command Contracts](./story-4-quality-release-command-contracts.md) | Complete | 7 | 7/7 | Story 1 |
| 5 | [Meta and Installation Command Contracts](./story-5-meta-install-command-contracts.md) | Complete | 7 | 7/7 | Story 1 |
| 6 | [The Eighteen Missing Completion Sections](./story-6-missing-completion-sections.md) | Complete | 7 | 7/7 | Stories 2, 3, 4, 5 |
| 7 | [Agent Config Contracts Across Both Carriers](./story-7-agent-config-contracts.md) | Complete | 6 | 6/6 | Story 1 |

## Dependency Graph

```
Story 1 (Contract Schema + new-command.md + .writ/docs/component-contract.md
         + ADR-020 amendment + roadmap Phase 10 correction)
   ├── Story 2 (Planning & specification — 10 commands)  ─┐
   ├── Story 3 (Implementation & recovery — 6 commands)   ├── parallel, disjoint file sets
   ├── Story 4 (Quality & release — 7 commands)           │
   ├── Story 5 (Meta & installation — 7 commands)        ─┘
   │      └── Story 6 (18 missing ## Completion sections) — after all four
   └── Story 7 (7 agent config blocks) — parallel with 2-6, disjoint from all
```

**Story 1 is a hard prerequisite for everything.** Every other story authors fields against a schema that does not exist until Story 1 fixes it, and `commands/new-command.md` is the worked exemplar the other 30 commands are written against. Starting Story 2 before Story 1 lands means re-authoring 10 files when the schema settles.

**Stories 2–5 are mutually independent** — their file sets are disjoint by construction (10 + 6 + 7 + 7 = 30 commands; `new-command.md` is the 31st and belongs to Story 1). They parallelize cleanly across worktrees.

**Story 6 is sequenced after Stories 2–5, not because it consumes their output but because it re-enters 17 of the same 18 files.** Running it in parallel guarantees merge conflicts in `commands/` at exactly the moment every file in the directory is dirty. Sequencing also lets each `## Completion` section be checked against the `exit_criteria` already present in its own file (Business Rule 7), which is only possible once the frontmatter has landed.

**Story 7 touches only `agents/` and is disjoint from every command story.** It runs in parallel with Stories 2–6.

**Suggested execution order:** Story 1 alone. Then Stories 2, 3, 4, 5, 7 in parallel. Then Story 6. Story 6 also carries the aggregate line-budget measurement, since it is the last story to touch `commands/`.

## Task Count

51 tasks across 7 stories. Story 1 carries 10 — the two extra are the ADR-020 and roadmap premise corrections added by maintainer approval on 2026-08-11 (spec.md → § Approved Scope Additions). The batch stories (2–5) carry 7 tasks each regardless of batch size because the work is the same shape at every size: read, derive, author, verify against both authoring tests, check the budget, record findings.

## Quick Links

- [spec.md](../spec.md) — locked contract, business rules, the ADR-premise finding
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — carrier analysis, worked `exit_criteria` examples, line-budget arithmetic, exact `new-command.md` edit set, structural verification commands
- [ADR-020](../../../decision-records/adr-020-component-contract.md) — governing decision

## Contradiction Found at Spec Time — Resolved into Story 1 (2026-08-11)

ADR-020 and `.writ/product/roadmap.md` both state that `commands/new-command.md` **already mandates** `## Completion` and that 19 command files therefore violate Writ's own template. Verified against the working tree: the string `Completion` occurs **exactly once** in `commands/new-command.md` — line 202, the heading of `new-command`'s own `## Completion` section (its success criteria for itself). The generated-command structure table at lines 136–143 lists six rows — Overview, Invocation, Command Process, Core rules or conventions, Integration with Writ, References — and has no Completion row. Independently re-verified by @AdamSellke on 2026-08-11.

**The mandate does not exist. The contract is missing, not unenforced.** `## Completion` is an emergent convention present in 13 files that nothing ever required and nothing ever checked. The work is the same size — 18 sections either way — but Story 1 *creates* the mandate rather than merely enforcing it, and "template violation" / "19 files" / "unenforced" must not appear in commit messages, changelog entries, or downstream specs.

**Disposition (maintainer approval, 2026-08-11):** both documents are amended by Story 1, with exact before/after text specified in `spec.md` → *Detailed Requirements → ADR-020 and roadmap premise corrections*.

- `.writ/decision-records/adr-020-component-contract.md` — a dated `## Amendments` entry (ADR-009 convention) plus four in-place replacements. **Amend, do not delete.** ADR-020's Decision — three carriers, one contract, frontmatter over prose — stands, and its `13 of 32` measurement row is correct and untouched.
- `.writ/product/roadmap.md` — two Phase 10 lines corrected one-for-one, plus an append to the existing 2026-08-11 Revision Log row. Line count stays at 424 because `2026-08-11-retire-dead-prescription` cites `roadmap.md:341` and `:343` by line number.

**File ownership verified:** no sibling Phase 10 spec writes to either file. `2026-08-11-retire-dead-prescription` explicitly excludes ADR-020 from its edits and only reads the roadmap.

**Still carrying the false premise, deliberately not fixed here:** `2026-08-11-governor-instrumentation` `spec.md:19` and `:49`, and `2026-08-11-loop-bounds` `spec.md:26`. Editing another spec's locked contract is outside this spec's authority; the ADR-020 amendment is the record they are read against, and neither spec's deliverable depends on the premise.

## Anti-Goal (applies to every story)

The failure mode for this spec is not incomplete work. It is **complete work that is informationally empty** — 31 commands carrying three fields each, all technically present, all boilerplate. That state passes every automated check `2026-08-11-governor-instrumentation` will build on top of it. The swap test (Business Rule 1) and the restatement test (Business Rule 2) are the only defenses, and they are review actions a human or reviewing agent must actually run, not lint rules.
