# Spec: Progressive Disclosure — `implement-story`

> **Status:** Not Started
> **Owner:** @AdamSellke
> **Created:** 2026-08-12
> **Dependencies:** []
> **Origin:** Phase 10's `progressive disclosure` feature (`Effort: L`), governed by [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md), which sequences the work as *"one spec per file, `implement-story.md` first"* — deliberately putting the riskiest extraction first so a failure stops the phase instead of surfacing after five easier wins. This is that first spec. The prerequisite Phase 10 specs (`retire-dead-prescription`, `component-contract`, `loop-bounds`, `governor-instrumentation`, `autonomy-gate-classes`) are all `Status: Complete` in this tree; their output is already present in `commands/implement-story.md`'s frontmatter and is read, not waited on, so the dependency list is empty rather than historical.

## Contract (Locked)

**Deliverable:** `commands/implement-story.md` — the largest command file in Writ at 52,709 bytes / 989 lines — reduced to a thin contract, with its per-phase procedural detail extracted to `skills/<name>/SKILL.md` and loaded on demand through `required_skills:`. This is the **pilot**: five sibling disclosure specs follow the pattern it establishes.

**Must include:** The thin contract retains only what [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) permits — frontmatter contract (ADR-020), `## Overview`, `## Invocation` table, the phase list with gate names, `## Completion`, `## References`. Extracted skills are authored through `/new-skill` so each is born `status: candidate` and passes `lint-skill.sh` on arrival. The command declares `required_skills:` — **this is that convention's first real consumer anywhere in Writ (0 declarations exist today)**.

**Hardest constraint:** [ADR-021 caveat 2](../../decision-records/adr-021-progressive-disclosure-token-budget.md) — progressive disclosure **can raise total load**. It trades one upfront load for several conditional ones, and a run that needs every skill costs *more* than the monolith did. `implement-story` is named as the likeliest case to bite, because a full-pipeline story run fires every gate. The spec must report **floor and ceiling separately** and is not done if the ceiling regresses without justification.

## Approved Scope Change — 2026-08-12 (maintainer)

> The `## Contract (Locked)` block above is left as written and is **superseded on one point** by this dated, maintainer-approved change. It is recorded here rather than edited into the contract because a locked contract that quietly changes is not a contract.

**What changed:** the **load mechanism**, and nothing else. The eight extracted skills are loaded by an inline `Read skills/<name>/SKILL.md` placed at the step or gate that needs them. **`required_skills:` frontmatter is not used by this spec.**

**Superseded contract sentences:**

| Contract sentence (unchanged above) | Now reads as |
|---|---|
| *"loaded on demand through `required_skills:`"* | loaded on demand through an inline `Read skills/<name>/SKILL.md` at the point of need |
| *"The command declares `required_skills:` — **this is that convention's first real consumer anywhere in Writ (0 declarations exist today)**"* | The command declares nothing in frontmatter. `required_skills:` **still has zero consumers** after this spec, and that is a finding this spec must surface, not resolve (§ Technical Concerns) |

**Why.** The measurement this spec's own authoring produced was verified and accepted: `required_skills:` is an **unconditional pre-load**. [`system-instructions.md`](../../system-instructions.md) — the harness loads the skill *"before any phase work begins"*; [`adapters/claude-code.md:396`](../../adapters/claude-code.md) — the harness issues the `Read` calls *"before the consumer's first phase begins."* It is a static array, so *"only what that invocation needs"* is fixed per **command**, never per **run**. [ADR-021:12](../../decision-records/adr-021-progressive-disclosure-token-budget.md)'s *"skills loaded on demand"* is false of the mechanism [ADR-021:18](../../decision-records/adr-021-progressive-disclosure-token-budget.md) selected.

The inline form is the genuinely conditional one: the agent issues the `Read` only if execution reaches that step, so **a skipped gate is free**. It is already the shipping pattern in **six** commands with a resolvable read — `create-spec` (6,147), `implement-story` (6,101, at `:525` → `tdd-cycle`), `refactor` (6,365), `release` (9,985), `research` (5,997), `ship` (9,985), totalling 44,580 bytes the pre-`e8f2a09` instrument could not see — plus `commands/new-skill.md`, which teaches the form in a `<name>` template rather than issuing a read. And `system-instructions.md` documents it as the standing alternative: *"Without the field, agents and commands continue to inline `Read skills/<name>/SKILL.md` instructions in their prompts at the point where the skill is needed."*

Under the eager mechanism, bytes moved out of a command reappear in the **floor** plus per-skill scaffolding — extraction is byte-neutral at best and the measured ceiling regression is guaranteed rather than risked. Under the inline mechanism, the floor falls by the full extracted weight and the ceiling is paid only on the path that fires every gate.

**What did not change:** the extraction plan (8 skills, the source-line ledger, the compression ledger), the ≤24,960-byte budget, the pinned-literal constraints, the no-redesign rule, `MAX_SKILLS` handed to `governor-enforcement`, and the `create-uat-plan` correction. Only *how the skills load*.

## The Binding Budget (maintainer decision, 2026-08-12)

**A command file may not cost more to load than the shared contract it runs inside.**

The budget is the irreducible shared base — the bytes every single invocation pays before the command file is even opened:

| Component | Bytes | Reducible by this spec? |
|---|---|---|
| `system-instructions.md` | 20,153 | No |
| `commands/_preamble.md` | 4,807 | No (Business Rule 6) |
| **Shared base** | **24,960** | **No** |

`commands/implement-story.md` must land **≤ 24,960 bytes**, down from 52,709 — a 53% cut. Measured with `python3 scripts/measure-invocation.py --root . --command implement-story`, which since its 2026-08-12 correction (`e8f2a09`) models **both** load mechanisms and never conflates them:

| Field | Meaning |
|---|---|
| `eager_bytes` / `eager_skills` | skills named in `required_skills:` — paid on **every** invocation. **This spec declares none, so these are `0` / `[]`.** |
| `floor_bytes` | `base + command + eager_bytes` — the bytes every invocation pays |
| `conditional_bytes` / `conditional_skills` | skills reached by an inline `Read skills/<n>/SKILL.md` in the body — paid **only if execution reaches that step** |
| `ceiling_bytes` | `floor + conditional_bytes` — the worst-case path, where every step fires |

A skill both declared *and* inline-read emits a warning and is counted once, as eager: *"the declaration wins: it is paid on every invocation, so the inline Read buys no conditionality. Drop one."* Business Rule 8 forbids that shape outright.

Re-verified against this working tree on 2026-08-12 **after** the correction; the script's own output is the authority, not the numbers quoted here.

### The 400-line cap becomes a secondary, non-binding tripwire

Bytes per command line vary **2.63×** across the 31 commands — measured, not estimated:

| Command | Bytes | Lines | Bytes/line |
|---|---|---|---|
| `implement-phase` | 29,136 | 321 | **90.8** (widest) |
| `implement-story` | 52,709 | 989 | 53.3 |
| `migrate` | 13,656 | 396 | **34.5** (narrowest) |

Lines are therefore a poor proxy for load. A 400-line cap **misses `implement-phase` entirely** — 321 lines, under the cap, yet the 4th-heaviest command file in the product at 29,136 bytes. It fires instead on `create-uat-plan` (417 lines, 16,239 bytes), a file barely half its weight. `migrate` marks the other end of the spread at 34.5 bytes per line — 396 lines and only 13,656 bytes, so it sits just under a cap that a file twice its size escapes.

**This spec owns the ADR-021 amendment recording that change**, and a second entry recording the mechanism correction. Amend, do not rewrite: ADR-021's Decision — thin contracts, extracted skills loaded on demand, an absolute budget — stands. What changes is the *instrument* (lines → bytes) and the *mechanism that makes "on demand" true* (`required_skills:` → inline `Read`). The amendment follows ADR-009's convention as ADR-020's `## Amendments` section does. Implementing the instrument in `scripts/eval.sh` belongs to the later `governor-enforcement` spec (Business Rule 7).

## Why This Exists

Writ's [`mission.md`](../../product/mission.md) positions it as *"the **thin**, portable methodology layer on top of increasingly capable AI harnesses."* The command surface measured 555,965 bytes across 31 command files on 2026-08-12. The top 6 files carry 217,338 of them — **39% of all command bytes in six files**. `implement-story.md` alone is 52,709, nearly a tenth of the surface, and every byte of it loads before a single line of a story's code is read.

The measured state (re-verified 2026-08-12 against this working tree via `scripts/measure-invocation.py`, not inherited from the roadmap):

| Measure | Value | How verified |
|---|---|---|
| `commands/implement-story.md` | 52,709 bytes / 989 lines / 53.3 B per line | `measure-invocation.py --command implement-story` |
| Shared base every invocation pays | 24,960 bytes | same, `base.components` |
| `implement-story` floor | **77,669 bytes** | same, `floor_bytes` — base + command; `eager_bytes` is 0 |
| `implement-story` conditional | **6,101 bytes** | same, `conditional_bytes` — the `tdd-cycle` inline read at `implement-story.md:525` |
| `implement-story` ceiling | **83,770 bytes** | same, `ceiling_bytes` — floor + `tdd-cycle` |
| Base share of floor | 32.1% | same, `base_share_of_floor` |
| `required_skills:` declarations across all commands and agents | **0** | `eval-leanness.py` → `metrics.required_skills_declarations`. **Still 0 after this spec** — see § Technical Concerns |
| Commands already using the inline mechanism | **7** | `grep -n 'Read skills/' commands/*.md` — `implement-story`, `create-spec`, `new-skill`, `refactor`, `release`, `research`, `ship` |
| Skills in `skills/` | 6 (`code-explanation`, `conventional-commits`, `error-rescue-mapping`, `gbrain-interop`, `safe-refactor-loop`, `tdd-cycle`) | `ls skills/` |

### The finding that shaped the work: `required_skills:` pre-load is unconditional

ADR-021 point 3 says the command *"declares `required_skills: [...]` so the harness pre-loads **only what that invocation needs**."* That is not what the convention specifies. [`system-instructions.md`](../../system-instructions.md) → *Harness contract* defines it as a **static frontmatter array** that the harness loads *"before any phase work begins"*; [`adapters/claude-code.md:396`](../../adapters/claude-code.md) says the same for this platform. There is no per-invocation selection mechanism, and nothing in any adapter provides one.

**The maintainer verified and accepted this on 2026-08-12, and ruled the mechanism out of this spec** (§ Approved Scope Change). `scripts/measure-invocation.py` was corrected the same day (`e8f2a09`) — it had wrongly counted declared skills as conditional, which understated the floor and *"would have let progressive disclosure self-certify against a number nobody pays."* It now puts declared skills in the **floor** and inline-read skills **above** it.

The consequence for this spec is the reason Business Rule 8 was rewritten: under the eager mechanism a `--quick` run that skips five gates still pays for every declared skill, so floor and ceiling collapse and extraction is byte-neutral at best. Under the inline mechanism they separate honestly — **the floor is what every run pays, the ceiling is what the all-gates path pays, and the gap between them is the only thing progressive disclosure actually buys.**

Precision of placement therefore becomes the whole exercise. A skill inline-read at the top of the command is paid on every run and has bought nothing; the same skill read inside Gate 0.5 is free on every `--quick` run. Business Rule 8 governs placement for exactly this reason.

### Why the ceiling is where this spec can fail

The arithmetic is uncomfortable and is stated up front rather than discovered in Story 5. Relocating ~30,000 bytes of procedure into 8 skill files costs roughly 650 bytes per file in frontmatter, `## Purpose`, `## When to Use`, and `## How to Apply` scaffolding — about 5,200 bytes of pure overhead that did not exist in the monolith. Add a thin command of ~21,000 bytes and the projected all-gates ceiling lands **above** 83,770.

ADR-021 predicted exactly this, named `implement-story` as the likeliest case, and offered a mitigation: *"If real measurement shows `implement-story` loading everything anyway, that file is the correct place to grant a tracked exemption rather than force a worse outcome to satisfy a metric."*

That mitigation is available but it is not the default. The default is **compression as a tactic within extraction** — ADR-021's own words, and the roadmap's Phase 10 Out of Scope entry says the phase *"relocates and **contracts** procedure."* Contracting is in scope; redesigning is not. The identified compression targets are enumerated in `sub-specs/technical-spec.md` → *Compression Ledger* and total roughly 3,000 bytes of duplicated examples and restated field lists. Business Rule 1 sets the bar; the exemption requires a written maintainer decision, not an implementer's shrug.

## 📋 Business Rules

1. **Report three numbers: the floor, the full-path ceiling, and the `--quick` ceiling. The ceiling may not regress.** Once loading is conditional, per-invocation cost is **path-dependent** and a single "ceiling" no longer describes a run. Two of the three bind:

   - **Floor (binds):** `command_bytes ≤ 24,960` (equivalently `floor_bytes ≤ 49,920`, since `eager_bytes` must be 0). The budget above. Paid by every invocation, on every path.
   - **Full-path ceiling (binds):** `ceiling_bytes ≤ 83,770` — the corrected pre-spec baseline, measured on this tree after `e8f2a09`. **The extracted system may not weigh more than the monolith it replaced, on the path where every gate fires.** The old bar of 77,669 was computed by an instrument that did not see the `tdd-cycle` inline read at `implement-story.md:525`; it understated the baseline by 6,101 bytes and must not be quoted.
   - **`--quick` ceiling (reported, does not bind):** floor + only those skills whose steps `--quick` reaches. `--quick` skips Gates 0, 0.5, 3, 3.5 and 5, and must therefore skip those gates' skills entirely. Today a `--quick` run pays the full 83,770 because the monolith carries everything. **This contrast is the spec's proof the mechanism works** — it is the number the eager mechanism could not have moved, and it is reported for `--quick` specifically because `--quick` is the case that motivated the correction.

   `measure-invocation.py` reports the *all-inline-reads* ceiling; it does not model paths. The `--quick` figure is therefore derived by hand — full ceiling minus the measured `wc -c` of each skill whose gate `--quick` skips — and the derivation is shown, not just its result.

   All three are recorded before and after in the final story's evidence. A full-path ceiling above 83,770 does **not** silently pass. It requires a written justification naming the measured overage in bytes, the compression already attempted with its measured yield, and an explicit maintainer decision to accept it — recorded in the story file and in the ADR-021 amendment. "It is only 4% worse" is not a justification; a justification states what was tried and why the remainder is irreducible without redesign. **A `--quick` saving does not buy off a full-path regression** — they are different runs, and both are real.

2. **Relocate and contract; never redesign.** The roadmap's Phase 10 Out of Scope reads: *"Rewriting commands' substance. This phase relocates and contracts procedure; it does not redesign workflows."* Every gate, threshold, and decision rule in `implement-story.md` survives the move faithful in meaning. A behavioral change is a defect, not an improvement.

   **The verification method is a no-drift inventory, built before any edit.** Story 1 enumerates, from `git show <base>:commands/implement-story.md`, every: gate name and number; agent binding; skip-mode rule; numeric threshold; result vocabulary; graceful-degradation row; literal log/warning string; and output-variable name. Story 6 matches that inventory 1:1 against `commands/implement-story.md` plus the eight `SKILL.md` files. **A rule present before and absent after is a defect regardless of how much better the new wording reads.** Wording may change; the rule may not.

   *Contraction that is permitted:* deleting a worked example that illustrates a format specified elsewhere in the same text; collapsing two byte-identical blocks into one parameterized block; replacing a restated field list with a pointer to the one authority. *Contraction that is not permitted:* dropping a degradation row, a threshold, a fallback value, or an "always/never" clause because it seemed obvious.

3. **Skill naming convention — established here, inherited by five sibling specs.** `skills/` is a shared namespace across six specs that run in sequence. This spec runs first and therefore owns the convention:

   1. **Kebab-case noun phrase, 2–3 words, ≤ 30 characters**, unique across `commands:`, `agents:`, and `skills:` in `.writ/manifest.yaml`. Matches all six incumbents.
   2. **Shape is `<object>-<operation>` or `<operation>-<object>`** — `boundary-map-computation`, `what-was-built-authoring`. The name says what capability is wielded.
   3. **Never named after its extraction site.** No command name, no gate number, no step number. `implement-story-context`, `gate-0-5-boundary`, `step-2-loading` are rejected. A skill named after where it came from cannot be read by a second consumer without reading as a foreign import, and it re-encodes the workflow shape `lint-skill.sh` exists to reject.
   4. **`description:` is a bare-imperative verb phrase** — "Compute…", "Assemble…", "Classify…", "Triage…", "Record…". This is the only shape `lint-skill.sh`'s `DESC_PATTERNS` rejection grammar leaves standing, and it is the difference between a tool and a role.
   5. **A shared skill carries no consumer's vocabulary.** If two or more commands read it, its `## When to Use` bullets state trigger conditions, not gate numbers, and its body never names the command that extracted it. This matters more under the inline mechanism, not less: `## When to Use` is now the only thing telling a second consumer *where* to put its own `Read`.
   6. **Collision protocol.** Before running `/new-skill`, grep `.writ/manifest.yaml`'s `skills:` block for the intended name **and its head noun**. If a sibling spec already claimed the noun, the later spec **inline-reads the existing skill** at its own point of need rather than authoring a near-duplicate, and adds an `evidence:` entry with `type: promotion` to that skill per ADR-014. First writer owns the name.

   The convention is written into `.writ/docs/skills.md` → *Extraction Patterns* by Story 1, because that file already ships to installed projects and already documents the extraction transform.

4. **Every extracted skill must be reachable, and reachable exactly once.** A skill this spec creates must (a) be loaded by exactly one inline `Read skills/<name>/SKILL.md` in `commands/implement-story.md`, and (b) be named in the phase table row for the step or gate that issues that read. `measure-invocation.py` must report it under `conditional_skills` with `eager_skills` empty and `unresolved_skills` empty. **An unreferenced skill is dead weight that made the surface worse** — it adds a file, a manifest entry, and a count against `MAX_SKILLS` while removing nothing from any invocation. A skill read from **two** places is worse still: it is paid on the union of both paths while reading as if it were paid on one, and it makes the `--quick` derivation in Business Rule 1 wrong.

5. **Eleven strings are pinned inside `commands/implement-story.md` by tooling this spec may not edit.** They must survive **in the command file**, not in a skill. `scripts/eval.sh` calls `require_literal` against `commands/implement-story.md` for nine of them (lines 2134, 2137–2141, 2721–2722, 2727, 2787–2788); `scripts/eval-loop-bounds.py:480–489` regexes the command **body** (frontmatter stripped) for two numbers. The full inventory with exact strings, source line numbers and the minimum retained carrier is in `sub-specs/technical-spec.md` → *Pinned Literals*. Two `forbid_literal` strings must stay absent from the command **and must not reappear anywhere**, including in a skill — they name retired prose that `scripts/story-context.py` replaced.

6. **`commands/_preamble.md` is not the escape valve.** It is **93 lines against a hard 95-line cap** (`scripts/eval.sh:411–414`) — 2 lines of headroom. ADR-021 point 4 offers it as the home for detail duplicated across ≥3 commands; that valve is effectively closed. Shared procedure becomes a **shared skill** instead. The cap is **not** raised: `2026-08-11-autonomy-gate-classes` owns that constant, derived it from a stated budget (79 + 14 + 2 = 95), and its Business Rule 1 states *"a cap chosen after the fact to accommodate whatever was written is not a cap."* Raising it again would be exactly the failure that spec banned, and its own Technical Concerns anticipate this spec by name: *"this cap raise is not a precedent for raising it again."*

7. **No edits under `scripts/`, with one bounded exception.** Zero changes to `scripts/eval.sh` and `scripts/eval-leanness.py` — the `check_length` 400-line change, the absolute `per_surface.commands.chars` cap, the `CONTRACT_CHECK_SEVERITY` flip, and `MAX_SKILLS` all belong to the later `governor-enforcement` spec. This spec's job is to bring the file into compliance; that spec's job is to enforce it. **The single exception:** if the assembler-failure degradation table relocates, `scripts/eval-story-context.py` lines 32, 436 and 442 cite it by location in comments and docstrings; those three pointers may be updated **as comments only**, with no logic change and no behavioral effect. `.writ/leanness-baseline.json` is a data file, not a script, and Business Rule 9 governs it.

8. **Every inline `Read` sits at the narrowest step that needs its skill.** Placement *is* the mechanism. A `Read skills/<name>/SKILL.md` is paid by exactly the runs that reach the line it is written on, so where it sits decides what it costs.

   *Superseded:* this rule previously read *"declare all, don't curate."* That was correct under eager loading — a curated `required_skills:` array understates `ceiling_bytes` while every invocation still pays for the whole array, which games the metric. Under conditional loading it is **backwards**: there is nothing to curate, and precision is the entire point.

   1. **Narrowest scope wins.** The `Read` goes inside the gate or step whose procedure the skill carries — `boundary-map-computation` inside Gate 0.5, `drift-triage` inside Gate 3.5 — never one level up "for readability".
   2. **A `Read` hoisted into the command's preamble is forbidden.** No inline `Read skills/…` may appear in the frontmatter, `## Overview`, `## Invocation`, `## Required Artifacts`, the phase table, or any prose that precedes `### Step 1`. Every run reaches those, so a `Read` there is an eager load wearing a conditional syntax — it costs the same as `required_skills:` and hides the fact in the body instead of the frontmatter. The phase table **names** each skill against its gate; it does not read it.
   3. **`required_skills:` is not used by this command.** `eager_skills` must be `[]` and `eager_bytes` must be `0` in the final measurement.
   4. **Never both mechanisms for one skill.** `measure-invocation.py` warns and charges it as eager (*"the inline Read buys no conditionality. Drop one."*). A run that produces that warning has failed this rule.
   5. **One `Read` per skill** (Business Rule 4). If two gates genuinely need the same skill, the second cites the first (*"the skill loaded at Gate 0.5 also governs …"*) rather than re-reading it.

   The gate-to-skill mapping stays visible in the phase table, so the *shape* is legible without opening a skill — ADR-021's own mitigation for the indirection cost.

9. **Growth in the `skills` surface is justified through the bound-justification mechanism, not absorbed silently.** The `skills` surface baseline is 932 lines / 41,620 chars (`.writ/leanness-baseline.json`, recorded 2026-08-04, no justifications). Eight new skills roughly double it and will raise an unjustified-growth warning. The disposition is a **bound justification** — the `(surface, metric)`-scoped `{date, value, text}` record that `2026-08-11-governor-instrumentation` Story 1 built for exactly this case — naming this spec, the byte count moved, and the corresponding `commands` reduction. `--update-baseline` is not used: it moves every surface's floor and records no reason.

10. **Skill bodies must pass `scripts/lint-skill.sh` as capability prose, and orchestration stays in the command.** The lint rejects `Read commands/`, `Read skills/`, a bare `Task(`, and a line-initial `/command` outside fenced blocks.

    **This constrains Business Rule 8 directly.** `scripts/lint-skill.sh:52` rejects `Read skills/` **inside a skill** — *"Skills do not call other skills. Combine them into the consumer (agent/command) that uses both."* Every one of the eight inline reads therefore lives in `commands/implement-story.md` and **nowhere else**; no extracted skill may load another. The eight skills of this spec are a flat set with no chaining, which is checked by Stories 2–4's own lint runs and again by `grep -RF 'Read skills/' skills/` returning nothing. Much of what `implement-story.md` contains is orchestration by nature — *which* agent is spawned, *when*, and *how the user is asked*. That material does not become a skill; it stays in the command, which is the correct home for it under [ADR-009](../../decision-records/adr-009-command-agent-skill-boundary.md). A skill describes *how to do the thing well*, given inputs; the command decides who does it and when.

## Detailed Requirements

### The eight extracted skills

Authored through `/new-skill`, born `status: candidate`, clean on `lint-skill.sh`. Byte figures are the measured size of the source block in today's `commands/implement-story.md`; the *authored* skill is that content minus the retained stub, minus compression, plus roughly 650 bytes of scaffolding.

The **Inline `Read` sits at** column is the Business Rule 8 placement and is as much a part of the extraction as the content: it decides which runs pay for the skill. `--quick` skips Gates 0, 0.5, 3, 3.5 and 5, so a skill placed inside one of those gates is free on every `--quick` run.

| # | Skill | Source block(s) in `implement-story.md` | Source bytes | Inline `Read` sits at | Paid on `--quick`? | Consumers beyond `implement-story` |
|---|---|---|---|---|---|---|
| 1 | `story-context-assembly` | *Parsing Context Hints* (L95–141), *Loading Knowledge Context* (L142–195), *Extracting Agent-Specific Spec-Lite Sections* (L196–220, minus the routing table) | ~6,720 | Step 2, at the context-assembly sub-step | yes | `knowledge_context` is consumed by 3 agents today |
| 2 | `dependency-context-loading` | *Loading "What Was Built" from Dependencies* (L221–340) | ~4,772 | Step 2, inside the *"if the story has dependencies"* branch | only when the story has dependencies | — |
| 3 | `what-was-built-authoring` | *B. "What Was Built" Data Extraction* (L670–733), *"What Was Built" Record Assembly* (L842–956) | ~6,198 | Step 4 item 4 (record assembly) — **not** Gate 3.5, because `--quick` skips 3.5 yet still writes the minimal record | yes | `create-uat-plan`, `ship`, `revert` read WWB records |
| 4 | `boundary-map-computation` | Gate 0.5 schema (L436–459), computation algorithm (L460–496), Check 5 persistence (L497–519) | ~5,708 | **Gate 0.5** | **no — skipped** | `coding-agent`, `review-agent` consume the map |
| 5 | `change-surface-classification` | Gate 2.5 (L571–593) | ~1,646 | Gate 2.5 | yes — Gate 2.5 is not in `--quick`'s skip list | `assess-spec`, `review-agent` |
| 6 | `drift-triage` | *A. Drift Response* (L623–669) | ~1,769 | **Gate 3.5 § A** | **no — skipped** | `implement-phase`, `ship`, `status`, `retro` read `drift-log.md` |
| 7 | `project-context-snapshot` | *`.writ/context.md` — Format & Regeneration* (L341–396) | ~1,848 | Step 4 item 3 (regenerate `.writ/context.md`) — **not** Step 2, where the schema currently sits | yes | **`implement-spec`, `status`** — the file itself says all three regenerate it |
| 8 | `story-commit-provenance` | *Recording the Story Commit SHA* (L829–841) | ~1,375 | Step 4 item 7 | yes | `revert` + `scripts/revert-resolve.py` are named consumers |

Two placements are deliberate relocations away from the source block's position, and both are Business Rule 8 rule 1 in action:

- **`project-context-snapshot`** is *specified* in Step 2 today but *used* in Step 4 (*"Regenerate `.writ/context.md` — full rewrite using the schema defined in Step 2"*). The read belongs where the regeneration happens.
- **`what-was-built-authoring`** has source in Gate 3.5 § B and in Step 4. Reading it at Gate 3.5 would make it free on `--quick` runs that nonetheless still write the `--quick` minimal record — a rule the skill owns. One read, at Step 4, per Business Rule 4.

`tdd-cycle` is a ninth conditional skill this command already inline-reads at Gate 1 (`implement-story.md:525`, 6,101 bytes). It is **not** extracted by this spec, is not re-placed, and its line survives the rewrite unchanged — but it counts in every ceiling figure and is the reason the corrected baseline is 83,770 rather than 77,669.

**Skill 7 is the first shared skill and the reason Business Rule 3 rule 5 exists.** `commands/implement-story.md:343` states that `.writ/context.md` is *"always fully regenerated … by `implement-story`, `implement-spec`, and `status`."* Three commands, one schema, currently specified in one of them. ADR-021 point 4 routes ≥3-command duplication to `_preamble.md` — closed at 93/95 lines — so it becomes a shared skill. `implement-spec` and `status` are **not** edited by this spec (Out of Scope); they inline-read it at their own point of need when their own disclosure specs run, and rule 6's collision protocol is what stops them re-authoring it.

**What deliberately does not become a skill.** The two `STATUS: BLOCKED` escalation blocks (Gate 1 L533–551, Gate 4 L754–771) are near-identical `AskQuestion` templates differing only in agent name and gate number. They are **orchestration** — asking the user for a repair decision — and under ADR-009 they belong to the command, not to a tool. They are collapsed in place into one parameterized escalation block, which is contraction under Business Rule 2, not extraction.

### The thin command

Retained sections, in order:

| Section | Disposition | Notes |
|---|---|---|
| Frontmatter | **Byte-identical — nothing added** | No `required_skills:` key. See below |
| `# Implement Story Command` | keep | |
| `## Overview` | keep | ADR-021 permits. **No inline `Read`** (Business Rule 8 rule 2) |
| `## Required Artifacts` | keep | `eval.sh:2727` pins `## Required Artifacts` in this file |
| `## Invocation` | keep | ADR-021 permits |
| **Phase table** | **replaces** the 2,021-byte ASCII `## Agent Pipeline` diagram | One row per gate: gate number, name, agent binding, skip modes, and the skill *named* — the table never issues the `Read` (Business Rule 8 rule 2). This is ADR-021's "phase list with gate names" and its mitigation for the indirection cost — *"the shape stays visible even when the detail does not."* |
| `## Command Process` → Steps 1–4 | keep the numbered step lists; sub-procedures leave | The 10-item Step 2 list and the 8-item Step 4 list are the phase list |
| Per-agent routing table | keep | `eval.sh:2137–2141` pins all five rows in this file |
| Gate 0 / 0.5 / 1 / 2 / 2.5 / 3 / 3.5 / 4 / 4.5 / 5 | contract stubs | Agent binding, skip modes, result vocabulary, iteration caps. Procedure leaves. |
| `## Error Handling` | keep | |
| `## Quick Mode (--quick)` | keep | |
| `## Completion` | keep, byte-identical | Landed by `2026-08-11-component-contract` |
| `## References` | keep, plus the eight skill links | Links, not `Read` directives — a `## References` entry never loads anything |

**Frontmatter preservation is absolute, and now total.** `commands/implement-story.md` lines 1–24 carry `problem:`, `outcome:`, three `exit_criteria` entries, and a `loop:` block with three declarations — `review_cycle` 3, `testing_cycle` 2 (nested), `agent_self_fix` 3 (nested) — each with a `calibrated_against` citation running to several sentences of evidence. `scripts/eval-loop-bounds.py` asserts these do not drift and cross-reads two of the three against prose in the command body. **All of it survives byte-identical, and nothing is added** — the mechanism change removes the one key this spec was going to append, so the frontmatter diff against `<base>` is now expected to be **empty**. Nothing is reflowed, reworded, or "tidied." That is a stricter and cheaper check than the original one.

### The ADR-021 amendment

A dated `## Amendments` section in `.writ/decision-records/adr-021-progressive-disclosure-token-budget.md`, inserted immediately before `## References`, following the ADR-009 convention that ADR-020's `## Amendments` section uses (`### <date> — <title>` → **Correction:** / **Rationale:** / **Measured:** / **Originating work:**). Two entries, one dated section.

**Entry 1 — the instrument changes from lines to bytes.** Records that ADR-021 Decision point 5 (`check_length`'s command limit 2000 → 400 lines) is superseded as the *binding* instrument by an absolute byte budget of 24,960 — the measured shared base — with the 400-line cap retained as a secondary, non-binding tripwire. The rationale is the 2.63× bytes-per-line spread and the fact that a 400-line cap misses `implement-phase` (321 lines, 29,136 bytes, 4th-largest file) while firing on `create-uat-plan` (417 lines, 16,239 bytes). **The Decision is not reopened** — thin contracts, extracted skills loaded on demand, and an absolute budget all stand, as does the 2026-11-11 review trigger. Only the unit changes. The Date line gains `(amended 2026-08-12 — see Amendments)`.

**Entry 2 — the mechanism correction.** This entry corrects a **premise**, not only an instrument, and it is the more consequential of the two. It records four things:

1. **The internal contradiction.** ADR-021:12 promises *"skills loaded **on demand**"*; ADR-021:18 selects `required_skills:` as the mechanism that delivers it and claims the harness *"pre-loads only what that invocation needs."* Those cannot both be true. `required_skills:` is a **static frontmatter array** that `system-instructions.md` → *Harness contract* loads *"before any phase work begins"* and `adapters/claude-code.md:396` loads *"before the consumer's first phase begins."* Selection is per **command**, never per **run**. Decision point 3's mechanism does not implement Decision line 12's promise.
2. **The correction.** The six disclosure specs use an inline `Read skills/<name>/SKILL.md` at the point of need — genuinely conditional, already shipping in six commands totalling 44,580 measured bytes (`implement-story.md:525` → `tdd-cycle` among them), and documented in `system-instructions.md` as the standing alternative to the field. `required_skills:` is not used. ADR-021's *outcome* — thin contracts, extracted skills, load only what a run needs — is preserved; only the mechanism named in point 3 is replaced.
3. **Why the ADR picked the wrong one, stated plainly.** ADR-021:54–58 chose `required_skills:` partly because *"the convention has 0 real adoptions and its own review trigger fired 8 days before this ADR"* and *"deprecating it would mean designing the same thing again under a new name within the same phase."* A convention needing a consumer is a reason to look at it; it is not evidence that it does the job. The mechanism was adopted on its stated contract without the contract being measured against the requirement. **Recording this is the point of the entry** — the failure mode is reusable, and the review trigger should see it.
4. **The measured consequence.** Under the eager mechanism, extraction is byte-neutral at best: bytes leaving the command reappear in the floor, plus ~650 bytes of scaffolding per skill. ADR-021 Consequences already warned *"progressive disclosure can increase total tokens"* — under `required_skills:` that is not a risk, it is arithmetic. The pilot's measured floor, full-path ceiling and `--quick` ceiling are `<recorded at Story 6>`.

**What entry 2 does not do.** It does not deprecate `required_skills:` — that convention's status is owned by `system-instructions.md` and by whoever picks up the correction below, not by this spec. It does not reopen the Decision's five points, the alternatives analysis, the top-6 ordering, or the 2026-11-11 review trigger. It attaches evidence to that trigger, which already asks whether measured per-invocation load dropped for 4 of 6 targeted commands. If the full-path ceiling regressed and a tracked exemption was granted, that grant is recorded here too.

ADR-021's Consequences already contain the honest negative (*"Progressive disclosure can increase total tokens"*) and the honest caveat about the 400-line figure (*"not from a measured quality threshold. Expect to tune it after 2-3 real extractions"*). The amendment is the tuning those sentences invited, arriving after extraction 1 of 6 rather than 3.

### Skill-naming documentation

Business Rule 3's six rules land in `.writ/docs/skills.md` under the existing `## Extraction Patterns` section, which already documents the extraction transform and already names the four skills extracted by `2026-07-10-skill-extraction`. Written at that file's existing density — the naming convention is roughly a table and a paragraph, not a second specification. `.writ/docs/*.md` ships to installed projects through `install.sh`'s doc fan-out, so the audience includes Writ users authoring their own skills.

## Out of Scope

- **The other five disclosure specs.** `create-spec`, `verify-spec`, `implement-phase`, `release`, and `ship` are untouched. This spec establishes the pattern; it does not apply it.
- **`commands/implement-spec.md` and `commands/status.md`.** They will inline-read `project-context-snapshot` at their own point of need when their own specs run. Editing them here would put a third writer in files two other specs own and would break the collision protocol this spec is writing.
- **`system-instructions.md` and `adapters/*.md` — the `required_skills:` first-consumer claim.** Both assert a fact this spec makes false, and **neither is in this spec's file set.** Correcting them is a required follow-up recorded in § Technical Concerns with no owner assigned, deliberately: silently editing the root behavioral contract from inside an extraction spec is how a convention gets retired without a decision.
- **`scripts/eval.sh` and `scripts/eval-leanness.py`, in any direction.** Business Rule 7. The `check_length` command limit, the absolute `per_surface.commands.chars` cap, the `CONTRACT_CHECK_SEVERITY` flip, and `MAX_SKILLS` belong to `governor-enforcement`.
- **Raising `MAX_SKILLS`.** It is 12 (`scripts/eval-leanness.py:71`); 6 + 8 = 14 exceeds it. `check_ceilings` emits a **warning**, never a finding, so nothing breaks. The overage is measured and reported (Success Criterion 8) and handed to `governor-enforcement`, which owns the constant. ADR-021 already requires that the cap "be raised deliberately with justification rather than silently" — this spec supplies the justification, not the edit.
- **`commands/_preamble.md`.** Business Rule 6. Not edited, cap not raised.
- **Re-deciding ADR-021.** Two amendment entries: one changes an instrument, one corrects a mechanism against the Decision's own stated outcome. The Decision's five points are not rewritten, its alternatives analysis is not reopened, and its 2026-11-11 review trigger is not moved.
- **Deprecating `required_skills:`.** This spec establishes that the convention does not do what ADR-021 needed and declines to use it. That is not the same as retiring it: it remains a correct mechanism for a skill a consumer genuinely needs on **every** invocation, which is a real case. Its status is `system-instructions.md`'s to change.
- **`.writ/product/roadmap.md`.** Phase 10's Success Criteria still reads *"No command file exceeds **400 lines** without a tracked exemption."* The ADR-021 amendment supersedes that as the binding instrument, leaving the roadmap line stale. Correcting it is flagged in § Technical Concerns and assigned to `governor-enforcement`, which changes the instrument in code and should change the criterion in the same breath. This spec does not edit a roadmap line another spec must edit anyway.
- **Skill promotion.** All eight are born `status: candidate` per ADR-014. `proven` requires ≥3 evidence entries accrued from real use; `promoted` additionally requires a `type: promotion` entry. A second consumer adopting one of these skills is exactly what `type: promotion` records — but promotion is earned from use afterward, and asserting it on the day of extraction would be the "unearned state" `lint-skill.sh` L3/L4 exists to reject.
- **Rewriting command substance, consolidating gates, or removing a gate that looks redundant.** Business Rule 2. Findings are recorded in story notes; they are not acted on here.
- **`claude-code/agents/*.md`, `codex/agents/*.toml`, `cursor/`, and the adapters.** No agent definition changes. The adapters already document **both** mechanisms in their Skills → Invocation subsections — `adapters/claude-code.md:387–393` specifies the inline `Read skills/<name>/SKILL.md` form this spec uses, so no adapter work is needed to support it. The stale first-consumer sentence at `:396` is the follow-up recorded above.
- **`.writ/manifest.yaml`'s stale `version:` and entry count.** Owned by `2026-08-11-retire-dead-prescription`. This spec appends eight `skills:` entries through `/new-skill` and regenerates `SKILL.md` via `gen-skill.sh`; it does not fix unrelated manifest defects.

## Implementation Approach

1. **Story 1 — the pattern, the convention, the amendment, and the drift baseline.** Nothing else can start until the naming convention exists (three parallel stories are about to author eight skill names into a namespace five more specs share) and until the no-drift inventory is captured from the pre-edit file. Capturing the inventory after any edit would mean verifying the new file against itself.
2. **Stories 2, 3, 4 — author the eight skills**, grouped by capability family: context assembly (2), gate procedure (3), records (4). Mutually independent — disjoint file sets, each touching only its own `skills/<name>/` directories plus `.writ/manifest.yaml` and `SKILL.md`. They are **additive**: the command still carries the prose while they run, so nothing is broken mid-flight and each can be reverted independently.
3. **Story 5 — the thin command.** Single writer on `commands/implement-story.md`. Rewrites it to the thin contract, places one inline `Read skills/<name>/SKILL.md` per skill at its point of need, deletes the relocated prose, and measures the floor, the full-path ceiling and the `--quick` ceiling. This is the only story that touches the command file.
4. **Story 6 — verification.** No-drift inventory matched 1:1, placement audit, unresolved-name degradation probe, `eval.sh` clean against baseline, leanness disposition recorded, before/after floor and both ceilings reported for the spec.

The `.writ/manifest.yaml` `skills:` block and the generated root `SKILL.md` are written by all three of Stories 2–4. `/new-skill` appends alphabetically and `gen-skill.sh` regenerates deterministically, so the conflict is textual, not semantic — if the three run in parallel worktrees, the last to land re-runs `bash scripts/gen-skill.sh` and confirms `--check` passes.

## Success Criteria

1. `python3 scripts/measure-invocation.py --root . --command implement-story` reports `command_bytes ≤ 24,960` (from 52,709) and `floor_bytes ≤ 49,920` (from 77,669), with `eager_bytes` **0** and `eager_skills` **`[]`**.
2. The same report shows `ceiling_bytes ≤ 83,770` — the corrected pre-spec baseline — **or** the final story carries a written justification naming the measured overage, the compression attempted with its measured yield, and an explicit maintainer acceptance, and that acceptance is recorded in the ADR-021 amendment. **And** the derived `--quick` ceiling is reported with its derivation and is below both the full-path ceiling (by at least the measured size of `boundary-map-computation` + `drift-triage`) and the 83,770 a `--quick` run pays today. A `--quick` ceiling equal to the full-path ceiling means placement failed and the mechanism bought nothing.
3. `conditional_skills` lists the eight extracted skills **plus** `tdd-cycle` (nine names); `unresolved_skills` is empty; and the run emits **no** both-mechanisms warning for any skill.
4. Eight `skills/<name>/SKILL.md` files exist, each `status: candidate`, each named per Business Rule 3, and `bash scripts/lint-skill.sh skills/*/SKILL.md` reports every file clean.
5. Each of the eight is loaded by **exactly one** inline `Read skills/<name>/SKILL.md` in `commands/implement-story.md`, that read sits inside the gate or step named in § *The eight extracted skills*, none sits above `### Step 1`, and every skill named in the phase table has such a read (Business Rules 4 and 8).
6. **The no-drift inventory matches 1:1.** Every gate name, agent binding, skip-mode rule, numeric threshold, result vocabulary, degradation row, literal log string, and output-variable name captured in Story 1 is present in `commands/implement-story.md` or in exactly one of the eight `SKILL.md` files. Zero unaccounted removals.
7. All eleven pinned literals are present in `commands/implement-story.md`, both `forbid_literal` strings are absent from the command **and** from all eight skills, and `bash scripts/eval.sh` produces no new findings relative to its pre-spec baseline.
8. `python3 scripts/eval-loop-bounds.py` reports **no new SKIP results** for `drift-review-cycle` or `drift-testing-cycle` — both prose caps still cross-read from the command body — and the `loop:` block is byte-identical to `git show <base>:commands/implement-story.md`.
9. **Graceful degradation is probed on the mechanism actually used.** An inline `Read skills/deliberately-missing-skill/SKILL.md` added at a real step produces a **warning** and exit 0 from `scripts/measure-invocation.py` (the unresolved name lands in `unresolved_skills` and the figures are labelled a lower bound), never a hard failure; the probe is reverted; the observed behavior — including whatever the harness itself did with an unreadable path — is recorded. **`scripts/eval-leanness.py`'s `check_required_skills` cannot be exercised by this spec** — it reads frontmatter only, and this command declares nothing — so its untested state is reported as the finding in § Technical Concerns rather than claimed as a pass. If either rule breaks in practice, that is a finding to surface, not to paper over.
10. `bash scripts/gen-skill.sh --check` passes, `.writ/manifest.yaml` carries 14 `skills:` entries, and the `skills` surface growth carries a bound justification in `.writ/leanness-baseline.json` naming this spec.
11. `.writ/docs/skills.md` documents the six naming rules and the collision protocol; `.writ/decision-records/adr-021-progressive-disclosure-token-budget.md` carries a dated `## Amendments` section with both entries, its Decision points 1–5 otherwise unchanged and its 2026-11-11 review trigger unmoved.
12. `git diff --name-only` lists **no** path under `scripts/` except, at most, comment-only lines in `scripts/eval-story-context.py` (Business Rule 7).

## Technical Concerns (surfaced at contract time)

- **The full-path ceiling is still projected to regress, and that is the spec's real risk.** The mechanism change does not close the gap — it moves both sides of the comparison by the same 6,101 bytes (`tdd-cycle`, invisible to the old instrument). Projection: floor ~45,930 + `tdd-cycle` 6,101 + eight skills ~35,200 = **~87,231** against an 83,770 allowance — **+3,461 bytes, +4.1%** — against a floor improvement of about **−41%**. Roughly 3,600 bytes of compression targets are identified in `sub-specs/technical-spec.md` → *Compression Ledger*, all of them duplicated examples or restated field lists that Business Rule 2 explicitly permits removing. If they land, the ceiling holds. If they do not, Business Rule 1's justification path opens and ADR-021's tracked-exemption mitigation is the fallback. **These are projections from block measurements, not results.** The implementer measures.

- **What the mechanism change actually buys is the `--quick` path, and it is smaller than "five gates" suggests.** Projected `--quick` ceiling: ~87,231 − `boundary-map-computation` (~5,950) − `drift-triage` (~2,420) = **~78,861**, against the 83,770 a `--quick` run pays today — a real **−4,909 bytes / −5.9%** that the eager mechanism could not have delivered at all. But `--quick` skips five gates and only **two** of them carry an extracted skill: Gate 0 (arch-check), Gate 3 (review) and Gate 5 (docs) are agent spawns whose procedure lives in `agents/*.md`, which this instrument does not measure and this spec does not touch. Do not report "five gates skipped" as though five skills were saved. The larger conditional win is `dependency-context-loading` (~5,400), skipped on every story with no dependencies regardless of mode — a `--quick` run of a dependency-free story projects to ~73,461, **−12.3%**.

- **Per-skill scaffolding is a real, new, permanent cost.** Eight files × frontmatter + `## Purpose` + `## When to Use` + `## How to Apply` ≈ 5,200 bytes that did not exist in the monolith. ADR-021 names it (*"plus per-skill frontmatter overhead"*) without quantifying it. This is the first spec that can, and the number should inform how aggressively the remaining five split their extractions — **fewer, larger skills carry less overhead than many small ones**, and `change-surface-classification` at ~1,646 source bytes is the marginal case in this spec.

- **`lint-skill.sh` forbids the vocabulary the gate blocks are written in.** The body patterns reject `Read commands/`, `Read skills/`, bare `Task(`, and line-initial `/command`. Gate 1's prose currently reads *"Spawns the coding agent to run the red → green → refactor loop via `Read skills/tdd-cycle/SKILL.md`"* — a line that would fail the lint the moment it moved into a skill. This is ADR-009 working as designed, and it is a load-bearing constraint on the extraction, not an obstacle to route around: it forces the split between *how to do the thing* (skill) and *who does it, when, and what happens on failure* (command). Fenced code blocks and 4-space-indented lines are exempt, so an `AskQuestion({…})` example inside a fence is fine.

  **The mechanism change makes that Gate 1 line the exemplar rather than a curiosity.** `lint-skill.sh:52` rejecting `Read skills/` inside a skill is what confines every one of this spec's eight inline reads to the command file: skills do not chain, so the command is the only place a `Read` can live, and the command is therefore the single place where load order and load cost are decided. That is the same property Business Rule 8 depends on — placement is auditable because it is all in one file — and it is why an eight-skill flat set is the right shape and a skill-loads-skill tree would not be.

- **`scripts/eval.sh` pins nine literals inside this specific file, and `eval-loop-bounds.py` regexes two numbers out of its body.** They constrain the extraction in ways ADR-021 never considered. Most are cheap to retain — `## Artifact Map` and `**Integrity:**` survive as a one-sentence assertion about the regenerated snapshot that points at `project-context-snapshot`, and `> **Commit:**` already lives in `exit_criteria`. The two `eval-loop-bounds.py` regexes matter more: `Max (\d+) iterations across review` and `(\d+) fix iterations max` must remain in the **body**, because a missing source value degrades a real drift check to a reported `SKIP` — not a failure, which is precisely why it could pass unnoticed. Retaining them is also correct on the merits: an iteration cap is contract, not procedure.

- **`scripts/eval-story-context.py` cites the assembler-degrade table by location in three comments.** If the table relocates to `story-context-assembly`, those pointers go stale. Business Rule 7 permits comment-only correction; it is deliberately the only `scripts/` write allowed, and it must not become a wedge for touching the file's logic.

- **`MAX_SKILLS` is 12 and this spec takes the count to 14, with five sibling specs still to come.** Warn-only, so nothing breaks. But the trajectory matters: if the remaining five average even six skills each, the surface reaches ~44 skills against a cap of 12. ADR-021 flagged the risk (*"the cap exists to prevent exactly the sprawl this work risks"*). The measured number from this pilot is the first real input to setting a new one, and `governor-enforcement` should not pick it by extrapolating from six files it has not extracted.

- **`.writ/product/roadmap.md` Phase 10's Success Criteria will be stale on landing.** It asserts the 400-line cap as a criterion; the ADR-021 amendment demotes lines to a non-binding tripwire. The ADR is the governing record and the divergence is recorded in the amendment, but a reader of the roadmap alone would get the wrong instrument. Assigned to `governor-enforcement` (§ Out of Scope) rather than fixed here, because that spec has to edit the criterion when it changes the code.

- **Four obligations are handed to `2026-08-12-governor-enforcement`.** The byte cap's implementation, the `MAX_SKILLS` raise, the `CONTRACT_CHECK_SEVERITY` flip, and the stale roadmap criterion all leave this spec unenforced. That spec was authored the same day, declares this one as a dependency, and its Story 3 halts if the ADR-021 amendment is absent — so the handoff has a receiver. It is still a handoff: until it lands, this file is compliant with a budget nothing checks, which is the "ratchet at a bloated baseline" failure ADR-021 diagnosed, one level up.

- **A sibling spec measured one of this spec's examples differently, and it is right.** `2026-08-12-governor-enforcement` records that a 400-line tripwire fires on a byte-compliant surface — `security-audit` (527 lines / 18,230 bytes), `refresh-command` (506 / 20,493), `status` (478 / 22,874), `plan-product` (443 / 24,753), `create-uat-plan` (417 / 16,239) all sit over 400 lines while under the byte budget. Five standing notes is a standing channel, which is the invisibility ADR-021 reason 2 documents. This spec's amendment sets the instrument; that spec's Business Rule 6 governs what happens if the retained tripwire fires on a compliant tree. The **Measured:** line in amendment entry 1 must use `create-uat-plan` as the fires-when-it-should-not example, not `migrate` (396 lines — under the cap, and cited here only as the low end of the bytes-per-line spread).

- **Stories 2–4 leave the tree in a state where the same procedure exists twice.** Between them and Story 5, eight skills and `commands/implement-story.md` both carry the same rules. This is deliberate — additive stories revert cleanly and the command is never half-rewritten — but the window must not be left open. If Story 5 stalls, the honest state is to revert Stories 2–4 rather than ship a surface with duplicated procedure, which would make `commands` *and* `skills` both grow.

- **The pilot's failure is supposed to stop the phase.** ADR-021 chose `implement-story` first *"since a failure there should stop the phase rather than surface after five easier wins."* If the ceiling cannot be held here, that finding is about the approach, not about this file, and the correct escalation is to ADR-021's review trigger — not to a per-file exemption applied five more times.

- **`required_skills:` loses its first consumer, and the claim that it has one is written into files this spec does not own.** This is the correction the mechanism change creates, and it has **no owner**:

  | File | The now-false claim | Owner |
  |---|---|---|
  | `system-instructions.md` → *`required_skills:` frontmatter convention* | *"**Status: adopted.** … The first consumer is Phase 10 progressive disclosure ([ADR-021](…)), which needs a declarative, harness-resolved, **per-invocation** load mechanism — the exact contract this convention already specifies … Progressive disclosure's extraction work lands the first real declarations"* | **none.** Product source; not in this spec's file set; `2026-08-11-retire-dead-prescription` Story 3 wrote the adoption and is `Complete` |
  | `adapters/claude-code.md:396` | *"Phase 10 progressive disclosure (ADR-021) is its first consumer, and no consumer declares the field yet"* | **none.** § Out of Scope excludes adapters |

  Both sentences will be false the moment Story 5 lands, and the second half of each (*"no consumer declares the field yet"*) will be **permanently** true instead of temporarily. The adoption decision itself is not necessarily wrong — the convention is still the right mechanism for a skill needed on *every* invocation — but its stated justification (*"per-invocation"*, *"the exact contract"*) is the very claim this spec disproves, and an adoption whose only cited consumer never materializes needs re-examination by whoever owns it.

  **This spec does not fix it**, and the reason is not timidity: `system-instructions.md` is the root behavioral contract, editing it from inside an extraction spec would retire a convention without a decision, and doing so here would also break the "no product-source edits outside the file set" promise the locked contract makes to a reviewer. **Assigning an owner is a maintainer action this spec cannot take.** `2026-08-12-governor-enforcement` is the nearest candidate — it already carries two orphaned obligations from this spec and records the disposition pattern (*"Both need an owner … Either the maintainer widens this spec's file set to cover them, or a later spec picks them up"*) — but it owns `scripts/`, not `system-instructions.md`, so naming it here would be assigning work outside its own locked file set. Recorded, unassigned, and surfaced at Story 6.

- **A second guard goes vacuous, and `governor-enforcement` is about to render it.** `scripts/eval-leanness.py`'s `check_required_skills` returns `metrics.required_skills_declarations`, which exists — per `2026-08-11-governor-instrumentation` Business Rule 8 — so that *"a check with nothing to assert reports nothing, and says so in the metrics."* It reports **0** today and will still report **0** after all six disclosure specs land. `2026-08-12-governor-enforcement` Story 1 exists to surface that metric in the eval report for the first time; what it will surface is a permanent zero. That is the guard working exactly as designed — it is telling the truth about a check with nothing to check — and it should be read as evidence for the correction above, not as a defect in either script. It does mean the convention's graceful-degradation contract (*"unknown names warn, never hard-fail"*) stays **unexercised** in the product: Success Criterion 9's probe can only test the inline mechanism.
