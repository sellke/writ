# User Stories: Progressive Disclosure — `/release`

> **Status:** Not Started — 0/5 stories, 0/48 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Changelog Generation and README Freshness Skills](./story-1-changelog-and-readme-skills.md) | Not Started | 8 | 0/8 | None |
| 2 | [Version Resolution and Bump Mechanics Skill](./story-2-version-bump-skill.md) | Not Started | 8 | 0/8 | None |
| 3 | [Publication and Runtime-Helper Skills](./story-3-publication-skills.md) | Not Started | 9 | 0/9 | None |
| 4 | [The Thin `/release` Contract](./story-4-thin-release-contract.md) | Not Started | 12 | 0/12 | Stories 1, 2, 3 |
| 5 | [Budget Measurement and No-Drift Certification](./story-5-budget-and-drift-verification.md) | Not Started | 11 | 0/11 | Story 4 |

## Dependency Graph

```
Story 1 (changelog-generation, readme-freshness-audit)   ─┐
Story 2 (semver-version-bump)                             ├── parallel: each creates
Story 3 (git-tag-publication, npm-package-publication)   ─┘   only its own skills/ dirs
        └── Story 4 (rewrite commands/release.md — the only writer of that file)
                └── Story 5 (measure, certify, or halt)
```

**Stories 1–3 create skills and never write `commands/release.md`.** They read it at a recorded base SHA. Their file sets are disjoint by construction — five new `skills/<name>/` directories, no overlap — so they parallelize across worktrees.

**Their one shared surface is `.writ/manifest.yaml`.** Each appends its own alphabetically placed block under `skills:`. None of them runs `scripts/gen-skill.sh` in write mode: three parallel branches each regenerating the root `SKILL.md` produce three conflicting full-file rewrites. Story 4 regenerates it once, from the merged manifest.

**Story 4 is the only story that touches `commands/release.md`,** so no two stories can race on the file every constraint in this spec is measured against.

**Story 5 is separated from Story 4 deliberately.** The story that writes the file is not the story that certifies it, and Business Rule 1's ceiling bar needs somewhere it can force a maintainer conversation without unwinding Story 4's work.

**Suggested execution order:** Stories 1, 2, 3 in parallel. Then Story 4. Then Story 5.

## Task Count

48 tasks across 5 stories. Story 4 carries 12 and Story 5 carries 11 (each gained one placement-verification task under the 2026-08-12 mechanism ruling) — the back half is heavier than the front because the skills are transcription under a lint, while the command rewrite is transcription under fifteen eval pins, a byte budget, five gate-placement rules, and a byte-identity requirement on the archival hook. Stories 1–3 each carry one Compression Ledger task, because the ceiling projection misses and the yields have to be measured where the prose is written, not asserted later.

## Quick Links

- [spec.md](../spec.md) — locked contract, binding budget, business rules, the eval-pin finding
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — baseline measurement, the fifteen-row extraction map, the eval pin inventory with line numbers, projected and ceiling arithmetic, skill roster, lint hazards, testing strategy
- [ADR-021](../../../decision-records/adr-021-progressive-disclosure-token-budget.md) — thin contracts, on-demand skills, the budget
- [ADR-022](../../../decision-records/adr-022-autonomy-gate-classes.md) — the production boundary as a permanent human gate

## Contradictions Found at Spec Time (2026-08-12)

Four at authoring time, all verified against the working tree rather than inferred, and all resolved into the contract rather than left for implementation to discover. Finding 3 was **re-resolved on 2026-08-12** by maintainer ruling after the measuring instrument was corrected; its entry below is the current text, not the original.

**1. `commands/release.md` is prose-pinned by `scripts/eval.sh`, which this spec may not edit.** Fifteen literal strings are asserted against the command file itself by `check_post_merge_archival()`, `check_git_notes_audit()`, `check_artifact_integrity()`, and `check_preamble()`; one string (`is_complete_family`) is forbidden. `require_literal` reads the command file and does not follow `required_skills:`, so a pinned string moved into a skill is an `eval.sh` finding. **Resolution:** 8,260 bytes — the release gate (3,836), the archival hook (3,188), and the audit-rollup core (1,236) — are structurally un-extractable. That is 52% of the projected post-spec file, and it happens to be exactly the content the production-boundary rule protects. Recorded as Business Rule 6 with a full inventory in the technical spec.

**2. `/release` is the sequential-pipeline case ADR-021 warned about, and on a full release disclosure buys almost nothing.** Against the *corrected* baselines (floor 53,549 / ceiling 63,534), the projections are: abort before Step 1.2 −22.4%, gate-blocked −8.8%, `--no-tag` −5.2%, **full release −0.2%**, tool worst path +4.1%. Only the last misses the bar, and by less than `npm-package-publication`'s own size — a skill no `/release` run reaches. **Resolution:** Business Rule 1 now requires a **path-dependent** report — floor, worst-path ceiling, and each realistic partial path — and requires the ~0% full-release result to be stated in those words rather than buried under the floor number. An overage still carries the three-part written justification (measured overage, compression with measured yield, explicit maintainer acceptance); naming a cheaper path explains an overage, it does not retire one. Two structural levers remain named (consolidate `readme-freshness-audit`; or drop the `npm-package-publication` extraction, trading ~2,754 B of worst-path ceiling for ~2,454 B of floor).

**3. `required_skills:` is an eager pre-load, so the mechanism changed — maintainer ruling, 2026-08-12.** ADR-021 clause 3 says the command declares `required_skills: [...]` "so the harness pre-loads only what that invocation needs." That is false against this harness: `system-instructions.md` says the named skills load "before any phase work begins" and `adapters/claude-code.md:396` says the same. Declaring this spec's five skills would have moved ~17,029 bytes into the **floor**, raising it from 53,549 to ~58,120 — the exact opposite of the deliverable. **Resolution:** `required_skills:` is **not used**. Each skill is reached by an inline `Read skills/<name>/SKILL.md` at the step that needs it, which is genuinely conditional and is already the pattern in six commands. Recorded in `spec.md` → *Approved scope change*; the locked contract block is unedited and the extraction map is unchanged. Two consequences invert earlier decisions: the pilot's "declare all, no curated subset" rule is **reversed** in favour of precise placement (Business Rule 3), and `npm-package-publication`'s exemption is **reinstated as correct** — under conditional loading a release that publishes no package genuinely never pays those bytes. `skills/conventional-commits/SKILL.md` stays exactly as it is: an inline read from the command at `release.md:88`, not a declaration, not re-extracted, and now counted symmetrically on both sides by the corrected instrument.

**3a. The instrument was wrong and has been fixed (`e8f2a09`).** `scripts/measure-invocation.py` treated `required_skills:` as conditional and ignored inline reads entirely, so it reported `/release` at ceiling 53,549 with `conditional_bytes: 0` — blind to the 9,985 bytes `release.md:88` has always loaded. It now reports `floor = base + command + eager skills` and `ceiling = floor + inline-read skills`, giving **floor 53,549 / cond 9,985 / ceiling 63,534**. Every figure in this package that reads 53,549 as a *ceiling* is superseded; 53,549 remains correct as the floor. **Resolution:** all bars re-set against 63,534, and Story 5 measures against the fixed tool.

**4. The naming convention arrived mid-authoring and cost one rename.** The dependency spec `2026-08-12-disclosure-implement-story` was authored in parallel with this one and now exists. Its Business Rule 3 rule 3 forbids naming a skill after its extraction site — including the command name — which the draft name `release-publication` violated. **Resolution:** renamed to `git-tag-publication`. The other four were re-checked against all six of the pilot's naming rules and against its eight skill names for head-noun collisions; none collide. The collision protocol (first writer owns the name; a later spec declares the existing skill rather than forking it) still applies at implementation time, because three sibling specs write into the same namespace between this spec's authoring and its build.

Three further findings are recorded but not acted on, because this spec does not own them. `MAX_SKILLS = 12` is crossed **before this spec runs** — 6 exist, the pilot alone adds 8 to reach 14, and this spec reaches 19 with three sibling specs still to come; raising the constant belongs to `2026-08-12-governor-enforcement`. `commands/release.md:346–349`'s `sed -i` lines are GNU-flavored and break on BSD `sed`, a pre-existing defect Story 2 carries across unchanged rather than smuggling a behavior fix inside a relocation. And the archival hook has **never fired in production** — `scripts/eval-post-merge-dogfood.py` reports 0 of 2 motivating specs and is deliberately unregistered in `eval.sh`'s `CHECKS=()` until it does, which is why Business Rule 5 demands byte identity rather than behavioral equivalence.

## Anti-Goal (applies to every story)

The failure mode is not an incomplete extraction. It is **a thin contract that is thin in name only** — bytes moved into skills that every invocation loads anyway, a path table nobody measured, and a drift ledger of fifteen rows all reading "verbatim" that nobody actually diffed. `/release` has the second-smallest gap of the six target files (13%), which makes it the easiest one to declare finished on a file-size number alone. It is also the one whose full-release path saves ~0.2%, which makes the file-size number the most misleading thing in the report.

The mechanism ruling gives this anti-goal a precise new shape: **a hoisted `Read` is `required_skills:` written in prose.** Five `Read` lines collected in the frontmatter, in `## Overview`, or in the phase-list table produce a file that is smaller, a floor that is unchanged, and a report that looks identical to a correct one. Business Rule 3's placement requirement and Testing Strategy check 6 are the only things that catch it.

The four defenses are Business Rule 1 (floor, worst path, and every partial path, every time), Business Rule 2 (a ledger checked with `git show`, not asserted), Business Rule 3 (placement, checked mechanically), and Business Rule 4 (no gate-crossing decision behind a conditional load — now a real risk, not a theoretical one). Three of the four are review actions someone has to actually run.
