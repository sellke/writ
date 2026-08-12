# Story 4: The Thin `/ship` Contract

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 2, 3

## User Story

**As a** reader or harness opening `commands/ship.md`
**I want** a contract that states what `/ship` guarantees, which phases it runs, which gate each phase carries, and which skill supplies each phase's procedure
**So that** the shape of the workflow stays visible at 11,000 bytes instead of 28,371, while every production-boundary decision and the whole audit-note attach path remain in the file that always loads

## Acceptance Criteria

- [ ] Given the budget is the shared base, when this story lands, then `python3 scripts/measure-invocation.py --root . --command ship` reports `command_bytes` **≤ 24,960**, `floor_bytes` strictly below 53,331, `eager_bytes: 0` with `eager_skills: []`, `unresolved_skills: []`, and no "loads both ways" warning — with the design target of ≤ 13,000 bytes / ≤ 400 lines met or its miss explained in the story notes.
- [ ] Given ADR-021 defines the thin contract, when this story lands, then `commands/ship.md` contains its frontmatter contract, `## Overview`, `## Required Artifacts`, `## Invocation` (all six rows), a phase list naming all six phases with their gate names and skills, the retained production-boundary and audit-note blocks, a compressed rescue table, a single routing table, `## Completion`, and `## References` — and no `### Step N` procedural body beyond the retained blocks.
- [ ] Given Business Rule 3 makes placement the mechanism, when this story lands, then `commands/ship.md` carries exactly five inline `Read skills/<name>/SKILL.md` instructions, each at the step that consumes it — `repo-convention-detection` at Phase 1's detection step; `commit-organization` at Step 4; `conventional-commits` at **`ship.md:224`, preserved in place, not converted and not relocated**; `pr-body-composition` at the Phase 5 body-assembly step *before* the retained draft-vs-ready / `gh pr create` block; `audit-digest-composition` at Step 6.2 *after* the `writ.auditNotes` opt-out check and landed-SHA resolution — `measure-invocation.py` lists all five under `conditional_skills` with `unresolved_skills: []`, and each of the five is named at the phase that consumes it in the phase list.
- [ ] Given hoisting forfeits the saving, when this story lands, then `grep -n 'Read skills/'` finds no match in the frontmatter, in `## Overview`, or in the phase-list table, no "skills this command uses" block exists anywhere in the file, and `grep -c required_skills commands/ship.md` returns 0. `eval-leanness.py check_required_skills` is **not** cited as evidence here — with zero declarations it has nothing to resolve and its silence means nothing.
- [ ] Given Business Rule 6, when this story lands, then `bash scripts/eval.sh` reports all seven `git-notes-audit` `scenario_ship` checks passing against the thinned file, and `commands/ship.md` still contains `writ.auditNotes`, the three land-strategy rows, `git notes --ref=writ add -f -F` with explicit `--ref=writ`, the `refs/notes/commits` prohibition, the non-blocking rule with its `⚠️ audit note not attached` log line, the minimal-digest fallback, and the confirmation line.
- [ ] Given Business Rule 4, when this story lands, then `commands/ship.md` still contains the five-row draft-vs-ready table with the `--draft` override and the both-directions override clause, `git push -u origin`, `gh pr create`, the `gh auth login` rescue, the orphaned-commits warning, the commit-plan `AskQuestion` with its rationale, the merge-conflict pause with "Do not auto-resolve merge conflicts", and the three `--test` failure options.
- [ ] Given Business Rule 2, when this story lands, then every row of `sub-specs/clause-ledger.md` carries a disposition of `retained`, `skill:<name>#<section>`, or `deduped:<row #>`; every `gate`-class row is `retained`; every `provenance`-class row is `retained` except the digest-composition rows; and no row is empty.
- [ ] Given the Phase 7 non-extraction note contradicts this work, when this story lands, then `commands/ship.md`'s note is **superseded in place** — it records that the Phase 7 judgment was made on reusability, that ADR-021's criterion is per-invocation load, that the load was unmeasurable before `scripts/measure-invocation.py` (and understated by 9,985 bytes until `e8f2a09`), and that four further skills are now reached by inline reads at their steps **using the same mechanism line 224 already used** — and it is not deleted.
- [ ] Given Business Rules 9 and 12, when this story lands, then `git diff --name-only` lists exactly one path under `commands/` and nothing under `scripts/`, `agents/`, or `adapters/`, and `ship.md`'s **entire frontmatter block** diffs empty against its pre-spec text (no added key, no `required_skills:`) along with its `## Completion` text.

## Implementation Tasks

- [ ] 4.1 Re-read `sub-specs/clause-ledger.md` and the four new SKILL.md files; confirm every clause the ledger sends to a skill is actually present in that skill before removing it from the command. Removing first and checking later is how clauses get lost
- [ ] 4.2 Author the phase list with gate names — six phases, each with gate class and skill — replacing `## Pipeline`'s ASCII diagram and `## Command Process`, in the shape Story 1 recorded from the dependency spec. The table names skills and carries no `Read skills/` string
- [ ] 4.3 Leave the frontmatter untouched — no `required_skills:`, no added key of any kind — then write the four new `Read` anchors at their steps (technical-spec → *The `Read` anchors*), using the phrasing convention `ship.md:224` already uses: state the read, then the seam. Preserve line 224 itself in place
- [ ] 4.4 Remove the extracted bodies of Steps 1, 4, 5, and 6.2–6.3, retaining verbatim the gate-crossing clauses (Business Rule 4) and the audit-note attach contract (Business Rule 6). Compress Steps 2 and 3 to their gates plus the commands they run
- [ ] 4.5 Compress `## Error Handling` to a rescue table of ≤900 bytes covering all six states, keeping the "option 1, commit now" recommendation and its reasoning; merge `## When to Use /ship vs Other Commands` and `## Integration with Writ` into one routing table of ≤600 bytes; replace `## Dry Run Mode` with one line pointing at the per-phase previews now carried by the skills
- [ ] 4.6 Supersede the Phase 7 non-extraction note in place with the reversal and its evidence
- [ ] 4.7 Fill every Disposition cell in the ledger, then run `python3 scripts/measure-invocation.py --root . --command ship`, `bash scripts/eval.sh`, and `wc -c -l commands/ship.md`; record all figures in the story notes

## Notes

**Technical considerations:**

- Write the file, do not edit it incrementally. A 28,371-byte file trimmed by successive deletions retains the old file's structure; the contract is a different document with a different shape.
- `## Required Artifacts` is retained verbatim because `_preamble.md`'s Artifact Integrity rule operates on the command's *declared* artifacts. That is the one section ADR-021's list omits which cannot move.
- **Where each `Read` sits is the deliverable, not a formatting choice.** A `Read` at Step 6.2 is not issued by a run with `writ.auditNotes=false`; the same `Read` collected into a block at the top of the file is issued by every run, the floor absorbs it, and the spec has produced a smaller file and no disclosure. Anchor each read at the step that *uses* the procedure, not the earliest step that mentions it.
- The `--no-split` and `writ.auditNotes=false` paths **now genuinely skip** the skills they will not use — ~3,300 B and ~1,200 B respectively. That is the whole point of the mechanism change, and it is what Story 5's path table measures. Under the withdrawn `required_skills:` mechanism both paths would have paid regardless.
- The superseded note is not an apology. It records what changed in the evidence, which is what lets a future reader evaluate the reversal instead of re-litigating it.

**Risks / challenges:**

- **Clearing the budget without extracting.** The file needs to shed only 3,411 bytes to pass. The ledger's disposition column is the check: a column of all-`retained` means nothing moved.
- **Trimming a provenance clause to hit the design target.** `bash scripts/eval.sh` catches the seven literals. It does not catch a paraphrase that keeps a literal and loses its meaning — for example, keeping the word `landed` while dropping the three land-strategy rows.
- **Dropping the orphaned-commits warning as "output, not behavior."** It is the file's own stated defense against a real failure mode (commits pushed after merge, requiring cherry-pick recovery). Ledger class `output`, disposition `retained`.
- **Rewording `exit_criteria` to match the thinner body.** Business Rule 12 forbids it, and the frontmatter is now byte-for-byte untouched, so any frontmatter diff at all is a defect. If a genuine contradiction appears, record it; the frontmatter contract belongs to `2026-08-11-component-contract`.
- **Anchoring `audit-digest-composition` above the `writ.auditNotes` gate.** It reads naturally as "Step 6 needs this skill", and it silently costs an opted-out run ~1,200 bytes it should never pay. Step 6.2, after the gate and after landed-SHA resolution.
- **Stories 2 and 3 supply the skills; a typo'd path in a `Read` is caught by `unresolved_skills`, not by `eval-leanness.py`.** There are no declarations for `check_required_skills` to resolve, so that check will pass silently either way.
- **The phase list becoming a table of contents.** It has to carry the gate names, or the file stops being a contract and becomes an index.

**Integration points:**

- Stories 2 and 3 supply the skills this story reads; a typo in a `Read skills/<name>/SKILL.md` path shows up as `unresolved_skills` plus a lower-bound warning from `measure-invocation.py`. It does **not** show up in `eval-leanness.py` — there are no declarations for `check_required_skills` to resolve.
- Story 5 re-measures, writes the ceiling justification, and audits the ledger this story fills.
- `scripts/eval-git-notes-audit.py` is the mechanical guard on the hardest constraint and should be run after every edit to the audit block, not only at the end.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `command_bytes` ≤ 24,960, `floor_bytes` < 53,331, `eager_bytes` 0
- [ ] Five skills inline-read at their steps and resolved, none unresolved, none declared, none hoisted; `ship.md:224` preserved in place
- [ ] `bash scripts/eval.sh` shows no new findings and 7/7 `git-notes-audit` ship checks pass
- [ ] Every ledger row carries a disposition; every `gate` row is `retained`
- [ ] Phase 7 non-extraction note superseded in place, not deleted
- [ ] `problem:` / `outcome:` / `exit_criteria:` / `## Completion` unchanged
- [ ] Exactly one file under `commands/` in `git diff --name-only`; nothing under `scripts/`

## Context for Agents

- **Business rules:** [BR2 clause ledger; BR3 reachability; BR4 production boundary; BR6 provenance write; BR9 one command file; BR12 foundation contract preserved] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [What `commands/ship.md` retains; The phase list with gate names] — from spec.md → ## Detailed Requirements
- **Technical spec:** [Retained Contract — Required Shape; The audit-note block — minimum retained content; The production-boundary block — minimum retained content] — from sub-specs/technical-spec.md
- **Finding to act on:** [`commands/ship.md:226` carries a Phase 7 non-extraction note that ADR-021 reverses — supersede in place] — from spec.md → ## Why This Exists
