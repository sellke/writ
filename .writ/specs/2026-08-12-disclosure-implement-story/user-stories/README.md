# User Stories: Progressive Disclosure — `implement-story`

> **Status:** In Progress — 4/6 stories, 31/48 tasks.
>
> **Amended 2026-08-12 (maintainer):** skills load via an inline `Read skills/<name>/SKILL.md` at the point of need; `required_skills:` is not used. See [spec.md → Approved Scope Change](../spec.md). Stories 1, 5 and 6 gained tasks; the extraction plan is unchanged.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Extraction Pattern, Naming Convention, and the ADR-021 Amendment](./story-1-extraction-pattern-and-adr-amendment.md) | Completed ✅ | 8 | 8/8 | None |
| 2 | [Context Assembly Skills](./story-2-context-assembly-skills.md) | Completed ✅ | 7 | 7/7 | Story 1 |
| 3 | [Gate Procedure Skills](./story-3-gate-procedure-skills.md) | Completed ✅ | 8 | 8/8 | Story 1 |
| 4 | [Record and Snapshot Skills](./story-4-record-and-snapshot-skills.md) | Completed ✅ | 8 | 8/8 | Story 1 |
| 5 | [The Thin Command and the Budget](./story-5-thin-command-and-budget.md) | Not Started | 10 | 0/10 | Stories 2, 3, 4 |
| 6 | [No-Drift Verification and the Load Report](./story-6-no-drift-verification-and-load-report.md) | Not Started | 7 | 0/7 | Story 5 |

## Dependency Graph

```
Story 1 (naming convention + ADR-021 amendment + no-drift inventory captured
         from the PRE-EDIT file)
   ├── Story 2 (story-context-assembly, dependency-context-loading)      ─┐
   ├── Story 3 (boundary-map-computation, change-surface-classification,  ├── parallel,
   │            drift-triage)                                            │   disjoint
   └── Story 4 (what-was-built-authoring, project-context-snapshot,      ─┘   file sets
                story-commit-provenance)
                     │
                     ▼
              Story 5 (the thin command — sole writer of
                       commands/implement-story.md)
                     │
                     ▼
              Story 6 (no-drift walk, degradation probe, load report)
```

**Story 1 is a hard prerequisite for two independent reasons.** First, `skills/` is a namespace shared by six sibling specs, and three parallel stories are about to author eight names into it — the convention has to exist before they do, or the pilot ships the sprawl it was meant to prevent. Second, the no-drift inventory must be captured from `git show <base>:commands/implement-story.md` **before any edit**. Capture it after Story 5 and it verifies the new file against itself.

**Stories 2, 3 and 4 are mutually independent and purely additive.** Their file sets are disjoint by construction — each writes only its own `skills/<name>/` directories. They do not touch `commands/implement-story.md`, so the command keeps working throughout and each story reverts cleanly on its own. The one shared surface is `.writ/manifest.yaml` plus the generated root `SKILL.md`; `/new-skill` appends alphabetically and `scripts/gen-skill.sh` is deterministic, so the conflict is textual — the last story to land re-runs the generator and confirms `--check`.

**Story 5 is the sole writer of `commands/implement-story.md`.** One story, one rewrite, one diff to review. Splitting the command edit across stories would produce a file that is half thin and half monolithic at every intermediate commit, and would make the budget unmeasurable until the last one landed. It is also the only story that decides **where** each skill is loaded — the eight inline `Read` calls exist nowhere until it runs, and their placement, not the extraction, is what makes the load conditional.

**Story 6 is separated from Story 5 deliberately.** The author of a rewrite is the worst person to certify that nothing was lost, and the no-drift walk is the spec's only real defense against a file that hits its byte budget by dropping behavior. Story 6 also carries the load report and the leanness disposition, because both need the final measured numbers.

**Suggested execution order:** Story 1 alone. Then Stories 2, 3, 4 in parallel. Then Story 5. Then Story 6.

## Task Count

48 tasks across 6 stories. Stories 2–4 carry 7–8 each because the work is the same shape at every size — read the source block, author the skill through `/new-skill`, lint it, check it against the boundary rules, and record what compression was applied and what it yielded. Story 1 carries 8 because it produces three separate artifacts (the convention, the amendment, the inventory) that share no code path. Stories 5 and 6 carry 10 and 7 after the 2026-08-12 mechanism amendment added read placement, a placement audit, the derived `--quick` figure, and the ownerless `required_skills:` correction.

## The Window Between Story 4 and Story 5

Between the last skill story and the command rewrite, **the same procedure exists in two places**: eight `SKILL.md` files and the still-monolithic `commands/implement-story.md`. This is deliberate — additive stories revert cleanly and the command is never half-rewritten — but it is a state the tree must not be left in. If Story 5 stalls, the honest disposition is to revert Stories 2–4 rather than ship a surface where `commands` and `skills` have both grown. Story 5's first task is to confirm the window is being closed, not extended.

## The Risk That Decides This Spec

The projected full-path ceiling is **~87,231 bytes against an allowance of 83,770** — a ~4.1% regression, against a floor improvement of ~41%. (Both figures are 6,101 bytes higher than earlier drafts said: the pre-`e8f2a09` instrument could not see the `tdd-cycle` inline read at `implement-story.md:525`. **The baseline is 83,770, never 77,669.**) ADR-021 predicted the regression, named `implement-story` as the likeliest case, and left one mitigation: *"that file is the correct place to grant a tracked exemption rather than force a worse outcome to satisfy a metric."*

That mitigation exists and is not the default. The default is compression as a tactic within extraction — five identified targets in `sub-specs/technical-spec.md` → *Compression Ledger*, totalling ~3,600 bytes, every one of them a duplicated example or a restated field list rather than a rule. Story 5 measures. Story 6 reports every number. **If the ceiling still regresses, the escalation is to ADR-021's review trigger, not to a per-file exemption applied five more times** — the pilot was sequenced first precisely so that a failure here stops the phase.

**The `--quick` path is the offsetting evidence, and it is a different number, not a discount.** With loading genuinely conditional, a `--quick` run skips Gates 0.5 and 3.5 and therefore never loads `boundary-map-computation` or `drift-triage`: projected **~78,861 against the 83,770 such a run pays today, −5.9%**. Under the `required_skills:` mechanism this spec no longer uses, that saving would have been exactly zero. Report both; subtract neither from the other. And state honestly that `--quick` skips five gates but only **two** of them carry an extracted skill — Gates 0, 3 and 5 are agent spawns whose procedure lives in `agents/*.md`.

## Quick Links

- [spec.md](../spec.md) — locked contract, the binding budget, ten business rules
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — section ledger, compression ledger, pinned literals and regexes, skill specifications, verification commands
- [ADR-021](../../../decision-records/adr-021-progressive-disclosure-token-budget.md) — governing decision, amended by Story 1
- [ADR-009](../../../decision-records/adr-009-command-agent-skill-boundary.md) — the command/agent/skill boundary the extraction must respect
- [ADR-014](../../../decision-records/adr-014-skill-lifecycle.md) — why every extracted skill is born `candidate`

## Anti-Goal (applies to every story)

**A file that reaches 24,960 bytes by losing rules.** The budget is trivially satisfiable by deleting behavior, and no script in this repository would notice: `eval.sh` checks eleven literals, `eval-loop-bounds.py` checks two numbers, and nothing at all checks whether the 1000-line WWB truncation priority, the `+3/+2/+1/+1` knowledge scoring weights, or the "classify UP one level when ambiguous" rule still exist. The no-drift inventory is the only defense, and it is a walk a human or reviewing agent must actually perform — not a lint.
