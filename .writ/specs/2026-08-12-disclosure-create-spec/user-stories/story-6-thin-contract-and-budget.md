# Story 6: The Thin Command, the Budget, and the No-Drift Proof

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 1, 2, 3, 4, 5

## User Story

**As a** maintainer who has to believe the phase worked
**I want to** `commands/create-spec.md` rewritten to ADR-021's permitted shape with each skill inline-read at the step that needs it, and the floor, the worst-path ceiling, the partial paths, and the absence of behavioral drift each proven by a command someone else can re-run
**So that** "progressive disclosure reduced per-invocation load" is a measurement rather than an impression, and the ADR-021 caveat-2 failure mode is ruled out rather than assumed away

> **Amended 2026-08-12** — maintainer ruling on the load mechanism. `required_skills:` is eager and is not used; skills are reached by inline `Read skills/<name>/SKILL.md` at the point of need. `scripts/measure-invocation.py` was fixed the same day (`e8f2a09`) and every figure below is against the fixed tool. See spec.md § *Approved Scope Change*.

## Acceptance Criteria

- [ ] Given ADR-021 point 1 names the sections a thin contract retains, when this story lands, then `commands/create-spec.md` contains the frontmatter contract **byte-identical with nothing appended — no `required_skills:` block**, `## Overview`, `## Required Artifacts`, `## Invocation` **as a table listing all four invocation forms** (bare, `--from-prototype`, `--from-issue`, `--recommend [idea]`), `## Recommended Mode` unchanged, a phase list with gate names and the inline skill reads, `## Completion`, and `## References` — and nothing else. The two deviations from ADR-021's list (`## Required Artifacts`, `## Recommended Mode`) are stated in the evidence with the eval that forces each.
- [ ] Given the phase list must keep the shape visible when the detail is not, when this story lands, then it names every step from 1.0 through 2.9 with its gate where it has one — the invocation validation gate, the cross-spec overlap gate, the **contract lock gate** (human `AskQuestion` or `--recommend` auto-lock, the only door into Phase 2), the visual reference gate, and the terminal package review — and each step that needs a skill carries the literal `Read skills/<name>/SKILL.md` call **inside the step**, as executable text rather than a citation beside it.
- [ ] Given Business Rule 3 forbids hoisting, when this story lands, then `grep -n 'Read skills/' commands/create-spec.md` returns exactly **six** hits, each at the step named in spec.md § *Load placement* — `spec-source-prepopulation` after the `--from-*` mode branch, `requirements-discovery` at 1.3, **`contract-lock` at 1.3b (strictly before the 1.4b gate and the `--recommend` auto-lock)**, `spec-package-authoring` at 1.5 or 2.2, `user-story-decomposition` at 2.5, `error-rescue-mapping` unchanged at Step 2.8 — with **no hit above the first phase heading**, and the line numbers recorded in the evidence. No tool checks this; the recorded line numbers are the check.
- [ ] Given the floor bar is 24,960 bytes, when this story lands, then `python3 scripts/measure-invocation.py --root . --command create-spec` reports `command_bytes ≤ 24,960` (from 46,423), `floor_bytes ≤ 49,920` (from 71,383), **`eager_bytes == 0` and `eager_skills == []`**, and `command_lines ≤ 400` (from 871).
- [ ] Given the worst-path ceiling bar is `command_bytes + conditional_bytes ≤ 52,570`, when this story lands, then `ceiling_bytes ≤ 77,530` with `conditional_skills` listing exactly the five extracted names plus `error-rescue-mapping`, `unresolved_skills` empty, and **no "loads both ways" warning** — **or** the evidence carries a written justification naming the measured overage in bytes, each Compression Ledger entry's measured yield, and an explicit maintainer decision to accept the remainder. The corrected pre-spec ceiling is **77,530**, not 71,383.
- [ ] Given Business Rule 1 now requires path-dependent accounting, when this story lands, then the evidence reports **the floor, the worst-path ceiling, and at least one realistic partial path** as arithmetic — minimally the `--recommend` invocation-rejection path (zero reads, floor only, ~−43% against today's 71,383) and the bare collaborative docs-only run (four of six reads) — **and states whether the maximal reachable path equals the tool's `ceiling_bytes` envelope**, since the tool sums every inline read and cannot know which are mutually exclusive. The evidence also states plainly that a *successful* `--recommend` run reads the same four skills a collaborative run reads, so the mode's saving is at the rejection boundary and not in the happy path.
- [ ] Given Business Rule 2 forbids redesign, when this story lands, then all **113 rows** of `sub-specs/technical-spec.md` § *Rule Inventory* reconcile in both directions — every row names a destination that exists, and no skill or command section carries a rule absent from the table — and the frozen regions diff clean against the spec's base commit: `## Recommended Mode`, `## Completion`, and the frontmatter's `problem:` / `outcome:` / `exit_criteria:` values byte-for-byte.
- [ ] Given the surface must stay green and the growth must be owned, when this story lands, then `bash scripts/eval.sh` reports no new findings against the pre-spec baseline (nineteen literal assertions, eight matrix rows, three ordering assertions, `## Required Artifacts`), `bash scripts/lint-skill.sh skills/*/SKILL.md` exits 0 for every file **with no `Read skills/` finding — the inline reads live in the command only (`lint-skill.sh:52` forbids them inside a skill)**, `bash scripts/gen-skill.sh --check` reports no delta, `python3 scripts/eval-leanness.py --root .` reports `required_skills_declarations: 0` for this command **with no finding** (`check_required_skills` reads frontmatter only and is silent on zero, so it will *not* catch a mistyped inline read — `unresolved_skills` is what catches that), the `skills/` count is reported against `MAX_SKILLS = 12` without raising it, and the `skills`-surface growth is recorded as a **bound justification** in `.writ/leanness-baseline.json` naming this spec — not an `--update-baseline` sweep.

## Implementation Tasks

- [ ] 6.1 Delete the five relocated blocks from `commands/create-spec.md`. **Leave the frontmatter byte-identical — append nothing, and add no `required_skills:` block** (maintainer ruling 2026-08-12)
- [ ] 6.2 Rebuild `## Invocation` as a table with all four forms — adding the `--from-issue` row that rule-inventory row 6 records as missing today — and write the phase list with gate names from rule-inventory rows 42, 44 (gate half), 45, 59, 61, 68, 75, 76, 80–85, 87–88, 90 (gate half), 105, 108–111
- [ ] 6.2a Place the five inline `Read skills/<name>/SKILL.md` calls **inside** their steps per spec.md § *Load placement*, verify `error-rescue-mapping`'s incumbent read at Step 2.8 is untouched, then record all six line numbers. Confirm none sits above the first phase heading and that `contract-lock`'s read precedes the Step 1.4b gate
- [ ] 6.3 Extend `## References` to `commands/_preamble.md`, `system-instructions.md`, the five skills, and `error-rescue-mapping`, as a human-readable index. **A `## References` entry is a listing, not a load** — the reads in the phase list are what execute
- [ ] 6.4 Measure: `measure-invocation.py` in both `--format json` and `--format table`; record `command_bytes`, `command_lines`, `eager_bytes`, `eager_skills`, `floor_bytes`, `conditional_bytes`, `conditional_skills`, `ceiling_bytes`, `unresolved_skills`; confirm no "loads both ways" warning; compute `command_bytes + conditional_bytes` against 52,570 and `ceiling_bytes` against 77,530
- [ ] 6.4a Compute the partial-path report BR1 requires: for each path in spec.md § *Projected paths*, sum the byte counts of the skills that path's reads would issue and state the total against the pre-spec 71,383 / 77,530. Name the maximal reachable path and state whether it equals the tool's envelope
- [ ] 6.5 Reconcile all 113 rule-inventory rows: for each, name the file and heading where it now lives; then reverse the check — read the command and all five skills and confirm every rule maps back to a row. Collect the five stories' Compression Ledger yields and total them against the overage
- [ ] 6.6 Run the frozen-region `diff`s against the base commit, re-anchoring the `## Recommended Mode` range on whatever heading now follows it and stating which anchor was used; confirm the three frontmatter contract values and `## Completion` byte-identical
- [ ] 6.7 Run the full verification set from `sub-specs/technical-spec.md` § Verification — including both `forbid_literal` greps against the command and all five skills — record the leanness bound justification, and write the evidence record: before/after table, the ceiling arithmetic, the net product-surface delta, the two ADR-021 deviations, the `skills/` count against `MAX_SKILLS`, and every inconsistency preserved unfixed

## Notes

**Technical considerations:**

- **Report the floor, the worst-path ceiling, and the partial paths.** With no `required_skills:` declared, `floor_bytes` is base + command and is what *every* run pays — it is no longer a hypothetical about a future harness. `conditional_bytes` is the sum of the six inline reads, `error-rescue-mapping` included: the fixed tool counts inline reads, so the separate "true worst case" figure this story used to carry is retired into `ceiling_bytes`.
- **`ceiling_bytes` is an envelope, not a path.** The tool sums every inline read in the file and cannot know that `spec-source-prepopulation` and a standard run are mutually exclusive. Task 6.4a exists because the number that answers "did disclosure work" is the *partial path*, and no tool produces it.
- **The worst-path ceiling is the bar that can fail.** Projection before compression is ~80,760 against 77,530 — roughly 3,227 over. **The overage is numerically unchanged by the mechanism ruling**, because the same bytes moved across the floor/ceiling line on both sides of the comparison. The Compression Ledger identifies ~3,300 bytes of permitted contraction spread across all five extraction stories. This story totals the measured yields. If they fall short, the answer is the written justification, not a shaved skill: ADR-021's tracked-exemption path exists and is taken deliberately, with numbers.
- **Placement is the one thing no tool checks.** `measure-invocation.py` sums the reads wherever they sit; `lint-skill.sh` never opens a command; `eval.sh` has no opinion. Six reads hoisted to the top of the file report an identical `ceiling_bytes`, pass every check in this spec, and make every run pay every skill — the eager mechanism rebuilt by hand. Task 6.2a's recorded line numbers are the entire enforcement.
- Expect the **total product surface to grow** by roughly 3,250 bytes of skill scaffolding even as per-invocation load falls by tens of KB. `eval-leanness.py` measures surfaces, so it reads this as growth in `skills/` and shrinkage in `commands/`. The disposition is a bound justification (Business Rule 13) — the `(surface, metric)`-scoped record built by `2026-08-11-governor-instrumentation`, naming this spec, the bytes moved, and the corresponding `commands` reduction. `--update-baseline` moves every surface's floor and records no reason; it is not used.
- The `## Invocation` table gains a `--from-issue` row. Not a new capability: the mode is documented at line 175 of the base file and named in the `--recommend` matrix. Recorded as documentation completion, not a feature.
- **The graceful-degradation concern is retired.** It applied to `required_skills:`, which this spec does not use. An inline `Read skills/<name>/SKILL.md` is an ordinary file read that every adapter already implements (`adapters/claude-code.md` maps it to the native `Read` tool) and that seven shipping commands already use. There is no harness-support question left to degrade from. What remains is the ordinary failure of a mistyped path — caught by `unresolved_skills`, **not** by `eval-leanness.py`, which reads frontmatter only.

**Risks / challenges:**

- **Hitting 24,960 by deleting instead of relocating.** The byte check cannot tell the difference and neither can any eval pin. The 113-row reconciliation is the only defense and it must be done row by row, both directions, not sampled.
- **Trimming `## Recommended Mode` "since we are in the file anyway."** It is 4,130 bytes of the remaining budget and the most tempting cut. Business Rule 5 forbids it; `eval.sh`'s matrix parser catches the structural half; nothing catches the semantic half except this story's diff.
- **Hoisting the inline reads "so the reader sees the skills up front."** Identical `ceiling_bytes`, identical `floor_bytes`, all checks green — and the eager mechanism the ruling rejected, rebuilt by hand. `## References` is where a reader sees the list; the phase-list steps are where the loads happen.
- **Adding `required_skills:` back "for discoverability."** It moves every skill into `floor_bytes`, blows the 24,960 floor bar, and inverts the spec's result. Out of Scope, by maintainer ruling.
- **Letting `contract-lock`'s read drift below Step 1.4b while tidying the phase list.** `--recommend` would auto-lock a contract using a procedure it has not loaded — an *unreviewed* wrong lock, not a visibly wrong prompt. Nothing automated catches it.
- **Deleting an inline read to make `ceiling_bytes` clear the bar.** The number improves and the procedure becomes unreachable — Business Rule 7's dead-weight failure. The honest move is the written justification.
- Re-anchoring the frozen-region `diff`: the `## Command Process` heading that currently follows `## Recommended Mode` may not survive the restructure. State the anchor actually used rather than reporting an empty diff produced by an empty range.

**Integration points:**

- This story's evidence is what ADR-021's 2026-11-11 review trigger reads for `create-spec`. It needs the ceiling and the true worst case, not just the file size.
- Four remaining disclosure specs inherit this story's evidence format.
- `skills/` reaches 19 against `MAX_SKILLS = 12` with the pilot's eight landed. Report the count; hand it to `governor-enforcement`; do not raise the cap.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `command_bytes ≤ 24,960`, `floor_bytes ≤ 49,920`, `eager_bytes == 0`, `command_lines ≤ 400`, recorded from `measure-invocation.py`
- [ ] `command_bytes + conditional_bytes ≤ 52,570` (`ceiling_bytes ≤ 77,530`), or the written justification with measured overage, per-entry compression yields, and maintainer decision
- [ ] Floor, worst-path ceiling, and ≥1 partial path all reported as arithmetic; the maximal reachable path named and compared to the tool's envelope
- [ ] `eager_skills` empty; `conditional_skills` lists the five new names plus `error-rescue-mapping`; `unresolved_skills` empty; no "loads both ways" warning
- [ ] `grep -n 'Read skills/' commands/create-spec.md` returns exactly six hits; each line number recorded and matched against spec.md § *Load placement*; none above the first phase heading; `contract-lock`'s read precedes the Step 1.4b gate
- [ ] `grep -n 'required_skills:' commands/create-spec.md` returns nothing
- [ ] All 113 rule-inventory rows reconciled in both directions
- [ ] `## Recommended Mode`, `## Completion`, and the three frontmatter contract values diff clean against the base commit
- [ ] `bash scripts/eval.sh` shows no new findings vs. the pre-spec baseline; both `forbid_literal` strings absent from the command and all five skills
- [ ] `bash scripts/lint-skill.sh skills/*/SKILL.md` exits 0; `bash scripts/gen-skill.sh --check` reports no delta
- [ ] `skills/` count reported against `MAX_SKILLS = 12`; cap not raised
- [ ] `skills`-surface growth recorded as a bound justification in `.writ/leanness-baseline.json`
- [ ] Net product-surface delta and the two ADR-021 deviations recorded
- [ ] `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok`

## Context for Agents

- **Load mechanism (READ FIRST):** inline reads at the point of need, no `required_skills:`, narrowest placement, path-dependent ceiling — from spec.md → **Approved Scope Change — Load Mechanism (2026-08-12)** and → Detailed Requirements → **Load placement** / **Projected paths**
- **Inherited convention:** naming rules and the ceiling bar (the declare-everything clause is **reversed**) — from spec.md → Inherited Convention
- **Business rules:** BR1 (floor + ceiling + true worst case), BR2 (rule inventory), BR3, BR4, BR5, BR6, BR7, BR10, BR11, BR12, BR13 — from spec.md → 📋 Business Rules
- **Retained-section table and the two recorded deviations** — from spec.md → Detailed Requirements → What stays in `commands/create-spec.md`
- **Phase list and gate names** — from spec.md → Detailed Requirements → The phase list with gate names
- **Measurement protocol, the two bars, the true-worst-case formula** — from sub-specs/technical-spec.md → Measurement Protocol
- **Compression Ledger** — from sub-specs/technical-spec.md → Compression Ledger
- **Rule inventory: all 113 rows** — from sub-specs/technical-spec.md → Rule Inventory
- **Verification command set** — from sub-specs/technical-spec.md → Verification
