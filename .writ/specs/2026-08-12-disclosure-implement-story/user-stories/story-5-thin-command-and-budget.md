# Story 5: The Thin Command and the Budget

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 2, 3, 4

## User Story

**As a** maintainer closing the window in which the same procedure exists in two places
**I want to** `commands/implement-story.md` rewritten to the thin contract ADR-021 permits, with each of the eight extracted skills loaded by one inline `Read skills/<name>/SKILL.md` at the gate or step that needs it
**So that** the file lands at or under the 24,960-byte budget with every gate, threshold and decision rule still reachable, and the floor, the full-path ceiling and the `--quick` ceiling are measured rather than projected for the first time in this phase

## Acceptance Criteria

- [ ] Given `commands/implement-story.md` is 52,709 bytes today, when this story lands, then `python3 scripts/measure-invocation.py --root . --command implement-story` reports `command_bytes ≤ 24,960` and `floor_bytes ≤ 49,920` with `eager_bytes` **0** and `eager_skills` **`[]`**, and both the before and after figures are recorded in this story's notes.
- [ ] Given ADR-021 caveat 2 warns that disclosure can raise total load, when this story lands, then the same report's `ceiling_bytes` is recorded alongside the floor, and if it exceeds **83,770** — the corrected pre-spec baseline, *not* the pre-`e8f2a09` figure of 77,669 — the story carries a written justification naming the measured overage in bytes, each Compression Ledger target attempted with its measured yield, and an explicit maintainer decision to accept — never a silent pass, never a rule deleted to close the gap, and never a `--quick` saving offered as compensation.
- [ ] Given a conditional mechanism makes cost path-dependent, when this story lands, then the story records a derived **`--quick` ceiling** — full ceiling minus the measured `wc -c` of `boundary-map-computation` (Gate 0.5) and `drift-triage` (Gate 3.5), the only two of `--quick`'s five skipped gates that carry an extracted skill — with the arithmetic shown, and it is strictly below both the full ceiling and the 83,770 a `--quick` run pays today. A `--quick` figure equal to the full ceiling means a `Read` is misplaced.
- [ ] Given `required_skills:` is an eager pre-load and was ruled out on 2026-08-12, when this story lands, then the command declares **no** `required_skills:` key, each of the eight skills is loaded by exactly one inline `Read skills/<name>/SKILL.md`, `conditional_skills` lists nine names (the eight plus the pre-existing `tdd-cycle`), `unresolved_skills` is empty, and the run emits no both-mechanisms warning.
- [ ] Given a `Read` every run reaches is an eager load in conditional syntax, when this story lands, then no inline `Read skills/…` appears in the frontmatter, `## Overview`, `## Invocation`, `## Required Artifacts`, the phase table, or anywhere above `### Step 1`, and each read sits at the gate or step named in spec.md → *The eight extracted skills* — including the two deliberate relocations (`project-context-snapshot` to Step 4 item 3, `what-was-built-authoring` to Step 4 item 4).
- [ ] Given ADR-021 permits only frontmatter, `## Overview`, `## Invocation`, the phase list with gate names, `## Completion` and `## References`, when this story lands, then the file carries exactly the sections listed in spec.md → *The thin command*, the 2,021-byte ASCII `## Agent Pipeline` diagram is replaced by a phase table with one row per gate (gate number, name, agent binding, skip modes, skill **named**), and no extracted procedure remains.
- [ ] Given `scripts/eval-loop-bounds.py` asserts the `loop:` block does not drift and `2026-08-11-component-contract` landed the contract fields, when this story lands, then `diff <(git show <base>:commands/implement-story.md | sed -n '1,24p') <(sed -n '1,24p' commands/implement-story.md)` is **empty** — no key is added, and `problem:`, `outcome:`, all three `exit_criteria`, and the `loop:` block with `review_cycle` 3, nested `testing_cycle` 2 and nested `agent_self_fix` 3 including every `calibrated_against` citation are byte-identical.
- [ ] Given `## Completion` was written by a sibling spec that is already Complete, when this story lands, then that section is byte-identical to its pre-edit text.
- [ ] Given `scripts/eval.sh` pins eleven literals to this file, when this story lands, then all eleven are present (`sub-specs/technical-spec.md` → Verification step 2 returns no output), both `forbid_literal` strings are absent from the command and from all eight skills, and `bash scripts/eval.sh` produces no new findings relative to the pre-spec baseline.
- [ ] Given `scripts/eval-loop-bounds.py:485,488` regexes the command body for two numbers, when this story lands, then the body still contains `Max 3 iterations across review` and `2 fix iterations max`, and `python3 scripts/eval-loop-bounds.py` reports **no new SKIP** for `drift-review-cycle` or `drift-testing-cycle`.
- [ ] Given every extracted skill must be reachable, when this story lands, then each of the eight is named in the phase table row for the gate or step that reads it, and no skill is read without such a citation or cited without such a read.

## Implementation Tasks

- [ ] 5.1 Confirm the window is closing, not extending: verify Stories 2–4 all landed and the eight `SKILL.md` files exist and lint clean. If any is missing, **stop** — a partial rewrite that references a skill that does not exist declares an unresolvable name and leaves the tree in the one state the README names as a revert trigger
- [ ] 5.2 Record the before measurement from `python3 scripts/measure-invocation.py --root . --command implement-story --format table`, and capture `git show <base>:commands/implement-story.md` for the frontmatter and `## Completion` diffs
- [ ] 5.3 Build the phase table that replaces the ASCII diagram — one row per gate (0, 0.5, 1, 2, 2.5, 3, 3.5, 4, 4.5, 5) with gate name, agent binding or *inline*, skip modes, and the skill **named**. The table names; it never issues a `Read` (Business Rule 8 rule 2, and the table sits above Step 1 where every run reaches it). This is ADR-021's mitigation for the indirection cost: *"the shape stays visible even when the detail does not"*
- [ ] 5.4 Rewrite the body — keep `## Overview`, `## Required Artifacts`, `## Invocation`, the Steps 1–4 numbered lists, the per-agent routing table, gate contract stubs (agent binding, skip modes, result vocabulary, iteration caps), `## Error Handling`, `## Quick Mode`, `## Completion`, `## References` + eight skill links. Delete the relocated procedure. Retain the minimum carriers named in the Pinned Literals table for literals 1, 7, 8 and 11
- [ ] 5.5 Place the eight inline reads, one per skill, at the sites in spec.md → *The eight extracted skills*. Copy the form already at L525 for `tdd-cycle`: orchestration sentence, the `Read skills/<name>/SKILL.md`, one clause naming the split (*"this gate owns when …; the skill owns how …"*). Put `dependency-context-loading` **inside** the has-dependencies branch, `project-context-snapshot` and `what-was-built-authoring` at Step 4 rather than at their source positions, and leave L525's own `tdd-cycle` line untouched
- [ ] 5.6 Collapse the two `STATUS: BLOCKED` `AskQuestion` blocks (Gate 1 and Gate 4) into one parameterized escalation block referenced from both gates — Compression Ledger C6. This is contraction under Business Rule 2: same three options, same `FAILURE` / `PARTIAL_STATE` fields, same skip-with-warning `⚠️ DEGRADED` semantics, one template
- [ ] 5.7 Confirm the frontmatter is untouched: `diff` lines 1–24 against `<base>` (expect **empty**) and `grep -c '^required_skills:'` (expect 0). Diff `## Completion` against `<base>` as well
- [ ] 5.8 Audit placement before measuring: `grep -n 'Read skills/' commands/implement-story.md` — nine lines, no skill twice, none above `### Step 1`; and `grep -RF 'Read skills/' skills/` — no output (`lint-skill.sh:52`)
- [ ] 5.9 Measure: run `measure-invocation.py` and record `command_bytes`, `command_lines`, `eager_bytes`, `floor_bytes`, `conditional_bytes`, `ceiling_bytes`, `conditional_skills`, `unresolved_skills`, and any warnings. Then derive the `--quick` ceiling (Verification 1b) and show the arithmetic. If `ceiling_bytes` exceeds 83,770, re-check every Compression Ledger target for unrealized yield **before** writing a justification — the justification must state what was tried
- [ ] 5.10 Run the full verification block from `sub-specs/technical-spec.md` → Verification steps 1–7, 9 and 10; confirm `git diff --name-only` lists no path under `scripts/` beyond the permitted comment-only exception

## Notes

**Technical considerations:**

- This is the only story that writes `commands/implement-story.md`. One rewrite, one diff, one measurement — splitting it would leave the file half thin and half monolithic at every intermediate commit and make the budget unmeasurable until the last one landed.
- The phase table is doing two jobs at once and both matter: it satisfies ADR-021's "phase list with gate names" *and* it is where Business Rule 4's reachability citation lives. A skill read in the body but absent from the table is a defect even though every script passes — and a skill named in the table with no read anywhere is a dead file.
- **Placement is the deliverable, not a detail of it.** The eight skills already exist when this story starts; what this story adds is *where each one is loaded*, and that decision is the entire measurable benefit. A correct rewrite with all eight reads at the top of Step 1 would pass every byte check in this story and deliver nothing — the floor would be right, the full ceiling would be right, and the `--quick` ceiling would equal the full ceiling. That last number is the one that catches it.
- **`--quick` skips five gates and only two of them carry a skill.** Gate 0 (arch-check), Gate 3 (review) and Gate 5 (docs) are agent spawns; their procedure lives in `agents/*.md`, which this instrument does not measure. Write the load report accordingly — "five gates skipped" is not "five skills saved", and a reader of the phase's go/no-go evidence will check.
- The budget is a **byte** budget. `command_lines` should land near 390 but is explicitly non-binding under the amended ADR-021, and optimizing lines instead of bytes reintroduces the instrument the amendment just retired.
- Four pinned literals need deliberate minimum carriers rather than surviving by accident: the `scripts/story-context.py assemble` invocation fence, a one-sentence `## Artifact Map` / `**Integrity:**` assertion about the regenerated snapshot, and a one-line reverted-record statement. Write them as contract assertions pointing at the owning skill — not as stub headings that exist to satisfy a grep.
- `git show <base>:commands/implement-story.md` is the frontmatter source of truth. Retyping the `loop:` block from memory is how a `calibrated_against` citation loses a sentence and `eval-loop-bounds.py` starts reporting drift against agent definitions that never changed.

**Risks / challenges:**

- **Meeting the byte budget by losing rules.** The budget is trivially satisfiable by deleting behavior and nothing automated would notice — `eval.sh` checks eleven literals, `eval-loop-bounds.py` checks two numbers, and nothing at all checks the 1000-line truncation priority or the `+3/+2/+1/+1` scoring weights. Story 6's inventory walk is the only defense, and this story must be written so that walk can succeed.
- **The full-path ceiling.** Projected at ~87,231 against an allowance of 83,770. The mechanism change did not shrink that gap — it lifted both numbers by the same 6,101 bytes of `tdd-cycle`. If the Compression Ledger under-delivers, the honest outcome is a recorded overage with a maintainer decision, not a quiet pass and not a rule deleted to make the arithmetic work. ADR-021's tracked-exemption mitigation exists for exactly this and is the fallback, not the first move.
- **Reflowing frontmatter while editing around it.** Editors reformat YAML; the `calibrated_against` strings are long and invite wrapping. Byte-identical means byte-identical — and now means an *empty* diff, since nothing is appended.
- **Rewriting gate prose "while we're in here".** Gate stubs are contract only. A gate that reads better but skips a result value has changed behavior under Business Rule 2.
- **Hoisting a `Read` "so the reader sees the dependencies up front".** It is the single most natural editorial instinct in this rewrite and it silently converts a conditional load into an unconditional one. The phase table exists to give the reader that overview without paying for it.
- **Adding `required_skills:` because it looks like the tidy declarative option.** It was ruled out on 2026-08-12 and `measure-invocation.py` will charge it to the floor and warn if the skill is also read inline. `eager_bytes` must be 0.

**Integration points:**

- Consumes all eight skills from Stories 2–4. Every inline read must resolve to a real `skills/<name>/SKILL.md` or `measure-invocation.py` warns and labels its figures a lower bound (never fails — that is deliberate, and it is why an unresolved path could otherwise ship silently). Note that `eval-leanness.py`'s `check_required_skills` reads frontmatter only and will **not** catch a bad inline path.
- Story 6 verifies this story's output against the Story 1 inventory and supplies the measured figures for ADR-021's amendment entry 2 placeholders.
- `agents/coding-agent.md`, `agents/review-agent.md`, `agents/testing-agent.md` and `agents/visual-qa-agent.md` are unchanged and continue to receive the same parameters. The thin command must still route `boundary_map`, `spec_lite_for_*`, `knowledge_context`, `change_surface`, `fetched_context` and `dependency_wwb_context` by name.
- The five sibling disclosure specs read this file as the worked exemplar. Its phase table is the shape they will copy.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `command_bytes`, `eager_bytes`, `floor_bytes`, `conditional_bytes` and `ceiling_bytes` recorded before and after, plus the derived `--quick` ceiling with its arithmetic
- [ ] `eager_bytes == 0`; nine inline reads, no duplicates, none above `### Step 1`; `grep -RF 'Read skills/' skills/` empty
- [ ] `bash scripts/eval.sh` shows no new findings
- [ ] `python3 scripts/eval-loop-bounds.py` shows no new SKIP results
- [ ] `bash scripts/lint-skill.sh skills/*/SKILL.md` still clean
- [ ] Frontmatter and `## Completion` diffs against `<base>` reviewed and confirmed byte-identical apart from `required_skills:`
- [ ] Reviewed against Business Rules 1, 2, 4, 5, 7, 8, 9
- [ ] `git diff --name-only` shows no path under `scripts/` beyond the permitted comment-only exception

## Context for Agents

- **Business rules:** [BR1 report floor, full-path ceiling and `--quick` ceiling, the full-path ceiling may not regress past 83,770; BR2 relocate and contract; BR4 reachable exactly once; BR5 eleven pinned literals and two pinned regexes; BR7 no `scripts/` edits; BR8 placement — narrowest step, nothing above Step 1, no `required_skills:`; BR10 `lint-skill.sh:52` keeps every read in the command] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The eight extracted skills — the *Inline `Read` sits at* column and the two deliberate relocations; The thin command — retained-sections table; Frontmatter preservation is absolute; What deliberately does not become a skill] — from spec.md → ## Detailed Requirements
- **Contract:** ["The thin contract retains only what ADR-021 permits"] — from spec.md → ## Contract (Locked), **as superseded on the mechanism by** spec.md → ## Approved Scope Change (2026-08-12): inline `Read` at the point of need, `required_skills:` not used
- **Technical concerns:** [The full-path ceiling is projected to regress; what the mechanism change actually buys is the `--quick` path and it is smaller than "five gates" suggests; `scripts/eval.sh` pins nine literals inside this specific file and `eval-loop-bounds.py` regexes two numbers out of its body] — from spec.md → ## Technical Concerns
- **Technical spec:** [Section Ledger — full disposition column; Per-skill projections; Path-dependent ceilings; Pinned Literals; Pinned Regexes; Compression Ledger C6; Verification steps 1, 1b, 2–7, 9, 10; Error & Rescue Map] — from sub-specs/technical-spec.md
