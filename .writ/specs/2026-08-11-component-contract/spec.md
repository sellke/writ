# Spec: Component Contract

> **Status:** Not Started
> **Owner:** @AdamSellke
> **Created:** 2026-08-11
> **Dependencies:** [2026-08-11-retire-dead-prescription]
> **Origin:** `/plan-product` Phase 10 discovery (2026-08-11). A maintainer raised the concern that Writ is "too prescriptive in some ways (wasting tokens) and not deterministic enough in other ways," flagging it as explicitly unverified. Per the Prime Directive it was measured before planning. The determinism half measured worse than the token half: 2 of 32 commands declare a goal, 13 of 32 carry `## Completion`, and 0 of 5 loop-bearing commands declare an iteration bound. Governed by [ADR-020](../../decision-records/adr-020-component-contract.md).

## Contract (Locked)

**Deliverable:** `problem:` / `outcome:` / `exit_criteria:` in all 31 commands' existing frontmatter and all 7 agents' existing config block, plus a `## Completion` section in all 31 commands.

**Must include:** No new mechanism — commands extend the `---` YAML already present in 32/32 files; agents extend the fenced block that already carries `model_tier`. `agents/visual-qa-agent.md` uses `## Agent Specification` with a `yaml` fence where the other 6 use `## Agent Configuration` with a plain fence; both carriers must be handled. `commands/new-command.md` updates so newly authored commands are born compliant.

**Hardest constraint:** `exit_criteria` must be **machine-checkable assertions**, not restated descriptions. 31 commands × 3 fields authored as boilerplate would add ~400 lines of prose to a phase whose entire purpose is reducing prose — that failure mode is the phase falsifying itself. Each command's fields are derived from what it actually does; the 18 missing `## Completion` sections are written, not templated.

## Approved Scope Additions

Additions agreed after the contract was locked. The `## Contract (Locked)` block above is unchanged; this section carries the delta.

### 2026-08-11 — ADR-020 and roadmap premise corrections (Story 1)

**Approved by:** @AdamSellke, 2026-08-11. **Lands in:** Story 1.

Story 1 already owed a record of the false `## Completion`-mandate premise. That record is now specified as two concrete file amendments rather than left to the implementer's choice of carrier:

- `.writ/decision-records/adr-020-component-contract.md` — a dated `## Amendments` entry plus three in-place premise corrections. **Amend, do not delete.** ADR-020's Decision — three carriers, one contract, frontmatter over prose — is unaffected and stands.
- `.writ/product/roadmap.md` — two Phase 10 lines that assert a template violation, corrected in place. Verified numbers (`13 of 32`, `2 of 32`, `0 of 5`, `516,589`) are not touched.

**Work size is unchanged.** Eighteen `## Completion` sections are still written. The change is framing: Story 1 **creates** the mandate in `commands/new-command.md`, it does not enforce one that already existed. Exact before/after text is in § Detailed Requirements → *ADR-020 and roadmap premise corrections*.

**No sibling conflict.** No other Phase 10 spec claims either file as an edit surface — `2026-08-11-retire-dead-prescription` explicitly excludes ADR-020 from its edits (its Story 1 notes: *"The ADR itself is not edited (Business Rule 3)"*) and reads `.writ/product/roadmap.md` without writing to it.

## Why This Exists

Writ has ~30 `eval-*.py` scripts, a `scripts/eval.sh` harness, `lint-skill.sh`, `check-agent-parity.sh`, and `phase-state.py`. All of them check specs, stories, phases, skills, and byte counts. **Nothing checks the commands and agents themselves.** The guardian measures its own file sizes and never asks whether a command knows what it is for.

The measured state (re-verified 2026-08-11 against this working tree, not inherited from the roadmap):

| Measure | Value | How verified |
|---|---|---|
| `.md` files in `commands/` | 32 (31 commands + `_preamble.md`) | `ls commands/*.md \| wc -l` |
| Files carrying `---` frontmatter with `name` + `description` | 32 of 32 | frontmatter terminator at line 4 in 31 files, line 5 in `_preamble.md` |
| Files carrying `problem:` | **0 of 32** | `grep -l '^problem:' commands/*.md` |
| Commands carrying `## Completion` | **13 of 31** | `grep -l '^## Completion' commands/*.md` — 13 files, none of them `_preamble.md`. ADR-020 and the roadmap state the same measurement as **13 of 32** against the raw file list. Both are correct; neither is to be "corrected." |
| Files in `agents/` | 7 | 6 × `## Agent Configuration` (line 7), 1 × `## Agent Specification` (line 18) |

### The finding that reframes the work

ADR-020 states that `commands/new-command.md` "already mandates" `## Completion` and that nineteen commands therefore violate Writ's own template. **That is not what the file says.** The string `Completion` occurs **exactly once** in `commands/new-command.md` — at line 202, the heading of `new-command`'s *own* `## Completion` section, its success criteria for itself. The generated-command structure table in Step 2.1 (lines 136–143) lists six rows: Overview, Invocation, Command Process, Core rules or conventions, Integration with Writ, References. There is no Completion row. Measured 2026-08-11 during spec authoring; independently re-verified by @AdamSellke the same day.

So the mandate does not exist. **The contract is missing, not unenforced.** `## Completion` is an **emergent convention observed in 13 files** — one that nothing ever asked for and nothing ever checked. The work is the same size either way: 18 sections still get written. What changes is Story 1's nature. It is load-bearing rather than clerical, because the authoring template must *acquire* the mandate before the migration has anything to migrate toward, and because it now also corrects the two documents that carry the false premise forward.

**The false framing is not to be repeated.** "Unenforced," "template violation," and "19 files violate Writ's own template" are banned from this spec's commits, its changelog entries, and any downstream reference to it. `2026-08-11-governor-instrumentation` (`spec.md` lines 19 and 49) and `2026-08-11-loop-bounds` (`spec.md` line 26) currently repeat the premise; correcting those is not this spec's scope, but it is flagged in § Technical Concerns so the amendment note is discoverable from ADR-020 when they are read.

`commands/new-command.md` also carries a second copy of the stale claim ADR-020 flags only in `system-instructions.md`. Its Model tier note reads *"Commands have no frontmatter mechanism, so weight intent ships as a prose note"* — false against 32/32 files carrying frontmatter.

> **Ownership ruling, 2026-08-11.** An earlier draft of this spec claimed that correction. It belongs to **`2026-08-11-retire-dead-prescription`** — this spec's dependency, which lands first — whose locked contract clause (a) reads *"The prose-note workaround for advisory `model_tier` is replaced by frontmatter."* Both copies of the claim (`system-instructions.md:277` and `new-command.md:145`) and the entire prose-note carrier travel with that spec. This spec is a **reader** of the outcome, not a writer: by the time it runs, `new-command.md` already prescribes frontmatter, and this spec adds the Completion row and the contract fields on top of that. Two specs editing the same lines with opposite intent was a decomposition defect, caught during spec authoring and resolved from the locked contracts rather than by preference.

### Why this is not another token tax

The contract is deliberately small, and it is only defensible because [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) removes an order of magnitude more than this adds. Landing it alone would make Writ heavier while calling it streamlined — the explicit failure mode identified at plan time. Business Rule 4 turns "deliberately small" into a number a reviewer can hold the work to, because "roughly four lines" is not a budget, it is an intention.

## 📋 Business Rules

1. **Every field is derived from the component, never templated across components.** The authoring test is the **swap test**: paste any `problem:`, `outcome:`, or `exit_criteria` entry into a different command's frontmatter. If it remains plausible there, it is boilerplate and must be rewritten. A criterion that would fit `/review` and `/retro` equally well describes neither.

2. **`exit_criteria` may never restate `description:`.** The **restatement test**: if deleting the criterion and re-deriving it from `description:` alone would produce roughly the same sentence, the criterion carries no information. Banned constructions include "the command completes successfully," "the report is generated," "the user is informed," "the output is correct," and any criterion whose verb is the command's own name. `description:` says what the command is for; `exit_criteria` says what is observably true afterward that was not true before.

3. **Every criterion names something a script could check.** Each entry must name at least one of: a **file or directory path** (`.writ/specs/<slug>/spec.md`), a **field value** (`Status: Complete`), a **count or comparison** (`user-stories/README.md row count equals story file count`), a **process outcome** (`git tag v<VERSION> exists`), or a **command-observable state** (`git status reports a clean tree`). Criteria are written as present-tense assertions about post-run state, not as instructions or aspirations. Placeholders in angle brackets are permitted and expected — the assertion must be *shaped* like something checkable, since nothing in this spec executes it. That limit is real and is stated in ADR-020's Consequences; the field's value is forcing the author to name a falsifiable condition.

4. **Line budget — stated as numbers, enforced by review.**
   - **7 added frontmatter lines per command, hard ceiling.** That is 1 `problem:` + 1 `outcome:` + 1 `exit_criteria:` key + a maximum of 4 criteria entries. Two criteria (5 lines) is the floor; three is the expected shape.
   - **7 added config-block lines per agent, hard ceiling.** Same arithmetic, same carrier rules.
   - **14 added lines per new `## Completion` section, hard ceiling** — heading, blank lines, and trailing separator included. Derived from the 13 incumbent sections, which run 12–18 lines with a median of 15–16; a new section may not exceed the incumbent median.
   - **Aggregate ceiling: 518 added lines** across `commands/` and `agents/` (31×7 + 7×7 + 18×14). The implementing agent reports the **measured actual** (`git diff --stat` against the spec's base commit) in the final story's evidence. Coming in under the ceiling is the pass condition; coming in *at* the ceiling on every file is evidence the swap test was not applied.

5. **`problem:` and `outcome:` are one line each.** One sentence, no line continuation, no YAML block scalars, no lists. A component that cannot state either in one line has a scoping defect the contract should surface, not accommodate. Soft target: under 200 characters.

6. **No new mechanism, and no carrier normalization.** Commands extend the existing `---` YAML. Agents extend the existing fenced block. `agents/visual-qa-agent.md`'s `## Agent Specification` + ` ```yaml ` fence and the other six agents' `## Agent Configuration` + plain fence are **both** written to as they are. Converting one style to the other is a separate decision and is out of scope for this spec.

7. **`## Completion` and `exit_criteria` must not contradict each other.** Frontmatter carries the machine-checkable assertions; the section carries the human-readable elaboration — terminal constraints, suggested next step, outcome interpretation. Every `exit_criteria` entry must be traceable to something the `## Completion` section also asserts. Where a command already has a `## Completion` section, its `exit_criteria` are derived *from* that section rather than invented alongside it.

8. **`commands/_preamble.md` is out of scope.** It is the 32nd file but not a command — it carries `disable-model-invocation: true`, is never invoked, and has no completion state. It is counted in "32/32 carry frontmatter" and excluded from "all 31 commands."

9. **This spec adds no eval checks.** It produces the compliant surface; `2026-08-11-governor-instrumentation` asserts it. No edit to `scripts/eval.sh`, `scripts/eval-leanness.py`, or any `scripts/eval-*.py` belongs in this spec, not even a warning-level one.

10. **Substance is not rewritten.** This spec adds declarative fields and one section per command. It does not restructure Command Process sections, reword Overviews, extract prose to skills, or change any command's behavior. If authoring a `problem:` reveals that a command has no distinct reason to exist, that finding is recorded in the story's notes — it is not acted on here.

## Detailed Requirements

### The contract schema

Commands, in the existing frontmatter, after `description:`:

```yaml
---
name: implement-story
description: "..."           # already present
problem: "..."               # NEW — one line: what goes wrong without this command
outcome: "..."               # NEW — one line: the artifact/state that exists after
exit_criteria:               # NEW — 2-4 machine-checkable assertions
  - "story status is Complete in .writ/specs/<spec>/user-stories/"
  - "all review gates returned PASS"
---
```

Field order is fixed: `name`, `description`, then `problem`, `outcome`, `exit_criteria`. Existing keys (`disable-model-invocation` and any others already present) keep their current position relative to `name`/`description`; the three new keys append after them. Values are double-quoted strings; `exit_criteria` is a block sequence of quoted strings.

Agents, in the existing fenced block that already carries `model_tier`, appended after the last existing key:

```
subagent_type: "generalPurpose"
model: default (inherits from parent)
model_tier: orchestration
readonly: false
problem: "..."
outcome: "..."
exit_criteria:
  - "..."
  - "..."
```

Six agents use a plain (unlabeled) fence under `## Agent Configuration` at line 7. `agents/visual-qa-agent.md` uses a ` ```yaml ` fence under `## Agent Specification` at line 18 and carries a different key set (`name`, `description`, `tools`, `disallowedTools`, `model`, `model_tier`, `readonly`, `maxTurns`). Both are appended to in place. Note that the six plain-fence blocks are not strictly valid YAML today (`model: default (inherits from parent)`), which is fine — the block is a documented convention, not a parsed document, and this spec does not change that.

### `## Completion` section shape

The section states the command's terminal condition in prose, and where applicable the terminal constraint that stops the agent from volunteering the next step. The 13 incumbent sections establish the shape; `commands/review.md` and `commands/new-command.md` are the reference exemplars. A new section contains, within the 14-line budget:

- A one-sentence success condition naming the artifact or state produced.
- Where the command has a meaningful failure or zero-result mode, one sentence stating that it is a valid outcome rather than an error.
- Where the command produces an artifact someone might expect it to then act on, a **Terminal constraint** line stating what the command does *not* do next.

Not every section needs all three. A 6-line `## Completion` that is accurate beats a 14-line one that pads to the ceiling.

### `commands/new-command.md` updates

Four edits, all inside Phase 2 / Step 2.1:

1. **Add a `## Completion` row to the generated-command structure table.** This is the mandate that ADR-020 assumed already existed. The row states that every generated command declares its terminal condition and, where applicable, its terminal constraint.
2. **Add the frontmatter contract to the generated file's requirements** — the three fields, with the field order above.
3. **Add authoring guidance for `exit_criteria`** — the swap test (Business Rule 1) and the restatement test (Business Rule 2), stated compactly enough to be usable coaching rather than a second specification.
4. **Do not touch the Model tier note.** ~~Correct the Model tier note's stale premise.~~ **Superseded 2026-08-11 (ownership ruling).** `commands/new-command.md`'s Model tier note (Step 2.1, lines 145–151) and its Step 2.2 checklist bullet (line 171) belong to **`2026-08-11-retire-dead-prescription`**, whose *locked contract clause (a)* states: *"The prose-note workaround for advisory `model_tier` is replaced by frontmatter."* That spec is this spec's dependency and lands first; it retires the carrier outright, and its Story 6 removes the `scripts/lint-skill.sh` branch and the `.writ/docs/model-tiers.md` rows that were this spec's stated reason for keeping the format locked. Restating the prose-note convention here would re-lock what the dependency just retired.

`commands/new-command.md` also receives its own three frontmatter fields and keeps its existing `## Completion` section, making it the self-demonstrating exemplar the other 30 commands are authored against.

### ADR-020 and roadmap premise corrections

Approved scope addition, 2026-08-11 (see § Approved Scope Additions). Both files land in Story 1. Every edit below is a **replacement in place**; nothing is deleted and no verified number changes.

All before/after text below is given in fenced blocks and is **authoritative** — the implementer pastes it, not a paraphrase of it. Relative link paths inside the blocks are written relative to the *target* file, not to this spec.

#### `.writ/decision-records/adr-020-component-contract.md`

Four in-place corrections plus one new section. ADR-020's Decision items 1–3 (commands / agents / skills) are untouched.

**1. Date line (line 3).**

```
Before:  > **Date:** 2026-08-11
After:   > **Date:** 2026-08-11 (amended 2026-08-11 — see Amendments)
```

**2. Decision section, the sentence following the three carriers (line 31).**

Before:

```markdown
The `## Completion` section that [`commands/new-command.md`](../../commands/new-command.md) **already mandates** becomes actually enforced rather than aspirational.
```

After:

```markdown
The `## Completion` section becomes a mandate in [`commands/new-command.md`](../../commands/new-command.md) and a check in `eval.sh`. It was neither when this ADR was written — see [Amendments](#amendments), 2026-08-11.
```

**3. `### The finding that reframed the decision` (lines 47–51) — heading plus the two false claims.**

Before:

```markdown
### The finding that reframed the decision

`new-command.md` — Writ's own authoring template — **already mandates `## Completion`** in its generated command structure. Nineteen of thirty-two commands violate it.

This changes what the problem *is*. The contract is not missing; it is **unenforced**. Writ has extensive deterministic tooling (~30 `eval-*.py` scripts, a 155KB `eval.sh` harness, `lint-skill.sh`, `check-agent-parity.sh`, `phase-state.py`) covering specs, stories, phases, and skills — but **nothing that checks the commands and agents themselves**. The guardian measures its own byte count and never asks whether a command knows what it is for.
```

After:

```markdown
### The finding: nothing checks the components themselves

Writ has extensive deterministic tooling (~30 `eval-*.py` scripts, a 155KB `eval.sh` harness, `lint-skill.sh`, `check-agent-parity.sh`, `phase-state.py`) covering specs, stories, phases, and skills — but **nothing that checks the commands and agents themselves**. The guardian measures its own byte count and never asks whether a command knows what it is for.

`## Completion` is the sharpest case. Thirteen of thirty-two files carry it; nothing ever required it and nothing ever checked it. **The contract is missing, not merely unenforced.** This subsection originally claimed the opposite, on a premise that was never measured — see [Amendments](#amendments), 2026-08-11.
```

The tooling-inventory and "guardian measures its own byte count" sentences survive **verbatim**. Only the false first paragraph and the false "not missing; it is unenforced" clause are replaced.

**4. Consequences → Positive, third bullet (line 87).**

Before:

```markdown
- `## Completion` compliance goes from 13/32 to 31/31, closing a template violation that has been accumulating unnoticed.
```

After:

```markdown
- `## Completion` coverage goes from 13/32 files to 31/31 commands, and `commands/new-command.md` acquires the mandate that keeps future commands compliant by construction.
```

**5. New `## Amendments` section**, inserted immediately before `## References` (currently line 104), following the convention in [ADR-009](../../decision-records/adr-009-command-agent-skill-boundary.md) — `## Amendments` → `### <date> — <title>` → **Correction:** / **Rationale:** / **Originating work:**. This entry adds a **Measured:** line, because the defect being corrected is precisely that the original claim was asserted without measurement.

```markdown
## Amendments

### 2026-08-11 — The `## Completion` mandate did not exist

**Correction:** This ADR originally asserted that `commands/new-command.md` "already mandates `## Completion`" and that "nineteen of thirty-two commands violate it," concluding that "the contract is not missing; it is **unenforced**." The premise is false. The string `Completion` occurs **exactly once** in `commands/new-command.md` — line 202, the heading of that command's own `## Completion` section — and the generated-command structure table (lines 136–143) has six rows: Overview, Invocation, Command Process, Core rules or conventions, Integration with Writ, References. There is no Completion row. No mandate exists, so nothing violates it. `## Completion` is an emergent convention carried by 13 of 32 files.

**Rationale:** The Decision is unaffected and is not reopened — three carriers, one contract, frontmatter over prose all stand, as does the 2026-11-11 review trigger. The migration is the same size: eighteen commands still need a `## Completion` section written. What changes is that the migration **creates** the mandate in `commands/new-command.md` rather than enforcing one that was already there. The phrases "unenforced," "template violation," and "19 files violate Writ's own template" are retired from downstream use.

**Measured:** 2026-08-11, during authoring of the `2026-08-11-component-contract` spec; independently re-verified by @AdamSellke the same day.

**Originating work:** Story 1 of [`2026-08-11-component-contract`](../specs/2026-08-11-component-contract/spec.md). `.writ/product/roadmap.md` Phase 10 carried the same premise and is corrected by the same story.
```

**Unchanged and verified unchanged:** the Context measurement table, including ``| Commands with a `## Completion` section | **13 of 32** |`` — that number is correct.

#### `.writ/product/roadmap.md`

Three edits, each **one line for one line**, so the file's line count stays at 424. This is a hard constraint, not tidiness: `2026-08-11-retire-dead-prescription` cites `.writ/product/roadmap.md:341` and `:343` by line number, and a shift would silently invalidate both.

**1. Phase 10 → "Problem (measured, not assumed)" table (line 316).** The count `13 of 32` is verified and stays; only the trailing clause is false.

Before:

```markdown
| Commands with `## Completion` | **13 of 32** — despite `new-command.md` already mandating it (19 violate Writ's own template) |
```

After:

```markdown
| Commands with `## Completion` | **13 of 32** — an emergent convention: `new-command.md` does not mandate it and nothing checks it |
```

**2. Phase 10 → Success Criteria (line 330).**

Before:

```markdown
- **All 31 commands** carry a `## Completion` section (closes the 19-file template violation)
```

After:

```markdown
- **All 31 commands** carry a `## Completion` section, and `new-command.md` mandates it for generated commands (18 sections written; the mandate is created, not enforced)
```

**3. Revision Log, the existing 2026-08-11 row (line 17)** — appended to, **not** added as a new row, to hold the line count fixed. Append this sentence to the end of that row's Change cell, before the closing `|`:

```markdown
Phase 10's `## Completion` "template violation" framing corrected the same day — no such mandate exists in `new-command.md`; see [ADR-020 Amendments](../decision-records/adr-020-component-contract.md#amendments).
```

No other roadmap line is touched. `516,589`, `2 of 32`, `0 of 5`, `44`, and the 400-line / 2000-line governor figures are verified and stay as written.

### Schema documentation

The schema, both carriers, the two authoring tests, and the line budget are documented once in `.writ/docs/component-contract.md`, alongside the existing `.writ/docs/model-tiers.md`, `.writ/docs/skills.md`, and `.writ/docs/spec-format.md`. `.writ/docs/*.md` ships to installed projects via `install.sh`'s fan-out (`append_manifest_writ_docs`, `overlay_scan_flat_dir`), so this is the correct home for a convention that Writ users authoring their own commands need to read. `commands/new-command.md` references it rather than restating it.

### Command batching

The 31 commands are authored in four batches grouped by pipeline role, so that a single agent holds one coherent mental model per batch and the swap test has real neighbours to be tested against:

| Batch | Commands | Count |
|---|---|---|
| Planning & specification | `plan-product`, `create-spec`, `edit-spec`, `assess-spec`, `create-adr`, `create-uat-plan`, `research`, `design`, `knowledge`, `create-issue` | 10 |
| Implementation & recovery | `implement-phase`, `implement-spec`, `implement-story`, `prototype`, `refactor`, `revert` | 6 |
| Quality & release | `review`, `verify-spec`, `security-audit`, `retro`, `ship`, `release`, `status` | 7 |
| Meta & installation | `new-skill`, `refresh-command`, `initialize`, `migrate`, `reinstall-writ`, `uninstall-writ`, `update-writ` | 7 |
| (Story 1) | `new-command` | 1 |

### The 18 commands missing `## Completion`

`assess-spec`, `implement-spec`, `implement-story`, `initialize`, `migrate`, `prototype`, `refactor`, `refresh-command`, `reinstall-writ`, `release`, `retro`, `revert`, `security-audit`, `ship`, `status`, `uninstall-writ`, `update-writ`, `verify-spec`.

Each section is placed immediately before the file's final `## References` section, matching the placement in all 13 incumbent files.

## Out of Scope

- **Any eval, lint, or CI check.** Business Rule 9. `2026-08-11-governor-instrumentation` owns enforcement and depends on this spec.
- **Loop bounds (`loop.max_iterations`, `on_exhaustion`).** A separate Phase 10 feature with its own spec, even though it lands in the same frontmatter block.
- **Progressive disclosure / skill extraction.** ADR-021's work. This spec adds fields to command files; it does not shrink them.
- **The `system-instructions.md` "verified 0/31 files" correction.** Owned by `2026-08-11-retire-dead-prescription`. This spec corrects only the duplicate copy inside `commands/new-command.md`, because it is editing that file's authoring guidance regardless.
- **`claude-code/agents/*.md` and `codex/agents/*.toml` mirrors.** ADR-020 names `agents/` only. `check-agent-parity.sh` checks file existence, not field parity, so the mirrors do not break. Extending the contract to them is a later decision.
- **Skills.** ADR-020 §3: skills already carry `## Purpose` and `## When to Use`; asserting those is `lint-skill.sh`'s job, not a new field.
- **`commands/_preamble.md`.** Business Rule 8.
- **Carrier normalization.** Business Rule 6 — `visual-qa-agent.md` keeps `## Agent Specification`.
- **The `model_tier` carrier in `commands/new-command.md`, in any direction.** Owned end-to-end by `2026-08-11-retire-dead-prescription` (locked contract clause (a); its Story 1 Task 1.4 and Story 6). This spec edits `new-command.md` **only** for the Completion row, the contract-field requirements, the `exit_criteria` authoring guidance, and that file's own three frontmatter fields. Ownership ruling recorded 2026-08-11 — see Business Rule 4.
- **Rewriting command substance, consolidating redundant commands, or acting on scoping defects the audit surfaces.** Business Rule 10 — findings are recorded, not acted on.
- **Correcting the repeated premise inside sibling Phase 10 specs.** `2026-08-11-governor-instrumentation` (`spec.md:19`, `:49`) and `2026-08-11-loop-bounds` (`spec.md:26`) restate the false mandate claim. Editing another spec's locked contract is not this spec's authority; the ADR-020 amendment is the record they are read against. Flagged in § Technical Concerns.
- **Re-deciding ADR-020.** The amendment corrects a premise. The Decision — three carriers, one contract, frontmatter over prose — is not reopened, and its 2026-11-11 review trigger is not moved.

## Implementation Approach

1. **Story 1 — schema, docs, authoring template, and the two premise amendments.** Nothing else can start until the schema is fixed and `new-command.md` mandates it, because every subsequent story authors against that shape. Establishes `new-command.md` as the worked exemplar. The ADR-020 and roadmap corrections land here too: they are the record that the mandate is being *created*, and leaving them to the end would mean six stories' worth of commits written under the false framing.
2. **Stories 2–5 — the 30 remaining commands' frontmatter**, in the four role batches above. Mutually independent (disjoint file sets), parallelizable.
3. **Story 6 — the 18 `## Completion` sections.** Depends on Stories 2–5. Not because it needs their output, but because 17 of its 18 files are also edited by them; serializing avoids merge conflicts across parallel worktrees, and it lets each section be checked against the `exit_criteria` already in the file (Business Rule 7).
4. **Story 7 — the 7 agent config blocks.** Depends only on Story 1. Disjoint from every command story, so it runs in parallel with Stories 2–6.

## Success Criteria

1. All 31 commands carry `problem:`, `outcome:`, and `exit_criteria:` in their existing `---` frontmatter, with `exit_criteria` holding 2–4 entries. `commands/_preamble.md` is unchanged.
2. All 7 agents carry the same three fields in their existing fenced block, with `visual-qa-agent.md`'s `## Agent Specification` / ` ```yaml ` carrier and the other six's `## Agent Configuration` / plain-fence carrier both intact and unconverted.
3. All 31 commands carry a `## Completion` section, placed immediately before `## References` (13 pre-existing, 18 new).
4. `commands/new-command.md`'s generated-command structure table includes a `## Completion` row and the three-field frontmatter contract, and its Model tier note no longer claims commands have no frontmatter mechanism.
5. `.writ/docs/component-contract.md` documents the schema, both agent carriers, the swap and restatement tests, and the line budget.
6. **No `exit_criteria` entry survives the swap test** — spot-check any 10 entries drawn from different commands against a different command's frontmatter; each must be false or nonsensical there.
7. **Measured added lines are at or under 518** across `commands/` and `agents/`, reported from `git diff --stat` in the final story's evidence, with no single command exceeding 7 frontmatter lines or 14 `## Completion` lines.
8. `bash scripts/eval.sh` produces no new findings relative to its pre-spec baseline, and `bash scripts/check-agent-parity.sh` still reports parity OK.
9. **The premise corrections have landed and cost nothing else.** `.writ/decision-records/adr-020-component-contract.md` carries a dated `## Amendments` entry recording what was measured, when, and by whom, while its Decision items 1–3 and its `13 of 32` measurement row are byte-for-byte unchanged. `.writ/product/roadmap.md` asserts no template violation anywhere in Phase 10; `git diff --numstat -- .writ/product/roadmap.md` reports equal added and deleted line counts and `wc -l` still returns 424, proving the `roadmap.md:341` / `:343` references in `2026-08-11-retire-dead-prescription` still resolve.

## Technical Concerns (surfaced at contract time)

- **The ADR's premise is wrong, the spec must not inherit it, and two sibling specs already have.** ADR-020 and the roadmap both describe "19 files violating Writ's own template." No template mandate exists (see Why This Exists). The work is the same size; the framing is not, and Story 1 is where the difference lands — it now amends both documents in place (§ Detailed Requirements → *ADR-020 and roadmap premise corrections*), as an amendment note rather than a re-decision, because the decision ADR-020 makes is unaffected by its premise being off. **Two sibling Phase 10 specs repeated the premise and were corrected by the phase orchestrator on 2026-08-11, not by this spec:** `2026-08-11-governor-instrumentation` (§ Why This Exists and the sequencing rationale; also its `story-4` user-story line) and `2026-08-11-loop-bounds` (its ADR-020 cross-reference and its `story-5` user-story line). Editing another spec's contract is out of this spec's authority, so `/implement-phase` made those edits directly — each is a prose correction outside the locked `## Contract` blocks, and neither spec's *deliverable* changed: governor-instrumentation still builds a presence check for 18 missing sections, and loop-bounds still adds `loop:` to five commands. Note that loop-bounds' "unenforced, not missing" framing is **correct for loop bounds** on its own evidence (`implement-story.md:595`, `implement-phase.md:201`); only its borrowed ADR-020 `## Completion` citation was wrong. The ADR-020 amendment note this spec writes remains the durable record. Note also that `2026-08-11-governor-instrumentation` `user-stories/story-3-completion-presence-check.md:37` correctly reconciles `13 of 32` against `13 of 31` and instructs that neither number be "corrected" — that guidance stands and this spec follows it.
- **`exit_criteria` is only nominally machine-checkable.** A lint can verify the field exists and is non-empty; it cannot verify the assertion is true. ADR-020 records this as a known limit. Business Rule 3 is the mitigation: forcing the author to name a falsifiable condition is the value, even when nothing executes it. ADR-020's 2026-11-11 review trigger exists precisely because this could turn out to be insufficient.
- **This migration conflicts with any concurrent command edit.** It touches every file in `commands/` and `agents/`. Sequencing Story 6 after Stories 2–5 handles the intra-spec case; concurrent work from other Phase 10 specs (notably progressive disclosure, which rewrites whole command files) must not run against the same files at the same time.
- **The six plain-fence agent blocks are not valid YAML.** `model: default (inherits from parent)` parses as a string, but the block has never been fed to a parser. Appending an `exit_criteria:` block sequence does not make it worse and does not make it better. If a future check wants to parse these blocks, converting them is that spec's problem.
- **Authoring 31 commands' worth of derived fields is the expensive part of this spec, and the part most likely to degrade under time pressure.** The failure mode is not that the work is skipped — it is that it is completed with fields that are technically present and informationally empty, which passes every check the next spec will build. Business Rules 1–3 exist to be cited in review, and Success Criterion 6 exists to be actually run.
