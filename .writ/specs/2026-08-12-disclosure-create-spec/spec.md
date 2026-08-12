# Spec: Progressive Disclosure — `/create-spec`

> **Status:** Closed — Not Implemented (measured evidence, 2026-08-12)
> **Owner:** @AdamSellke
> **Created:** 2026-08-12
> **Dependencies:** [2026-08-12-disclosure-implement-story]
> **Origin:** Phase 10 progressive disclosure, governed by [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md), which applies the thin-contract pattern to the top 6 command files "in descending size order, **one spec per file**." `commands/create-spec.md` is file two: 46,423 bytes / 871 lines, measured 2026-08-12 against this working tree. The binding budget is a maintainer decision recorded 2026-08-12; the instrument is `scripts/measure-invocation.py`, new in this phase. The extraction pattern, the naming convention, and the declaration rule are **inherited** from the pilot spec `2026-08-12-disclosure-implement-story` and are not re-decided here.

> **Not implemented — closed 2026-08-12 on measured evidence.** The pilot
> (`2026-08-12-disclosure-implement-story`) shipped and measured progressive
> disclosure's real cost: **~1,017 bytes of irreducible overhead per extracted
> skill** (27,872 B removed from the command, 36,005 B added as 8 skills). Its
> worst path regressed **+9.7%** against a projected +4.1% — the projection
> underestimated overhead by 2.3x, and every spec in this set was projected the
> same way. Per this spec set's own Business Rule 1, a pilot regression is *"a
> signal about the approach rather than a per-file exemption."*
>
> The saving tracks how genuinely branchy a command is, not how large its file
> is. Selecting by file size was the error. This spec's own measured common-path
> payoff did not justify ~5 more skills of overhead on a command that is either a
> sequential pipeline or already near break-even.
>
> The contract, extraction plan, pinned-literal inventory and measurement method
> here are **kept intact and unexecuted** — they are the design record if the
> economics change (a materially smaller skill preamble, or a harness that loads
> lazily by default). Nothing here was wrong; the premise underneath it was.

## Contract (Locked)

**Deliverable:** `commands/create-spec.md` — 46,423 bytes / 871 lines, the second-largest command in Writ — reduced to a thin contract with its per-phase procedural detail extracted to `skills/<name>/SKILL.md`, loaded on demand via `required_skills:`.

**Must include:** The thin contract retains only what [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) permits — frontmatter contract (ADR-020), `## Overview`, `## Invocation` table, the phase list with gate names, `## Completion`, `## References`. Skills are authored through `/new-skill` (born `status: candidate`, lint-clean). **The extraction pattern and skill-naming convention are established by the dependency spec `2026-08-12-disclosure-implement-story` — follow it, do not invent a second one.**

**Hardest constraint:** `/create-spec` is Writ's contract-first entry point and carries `--recommend`, one of only two commands permitted autonomous authoring ([ADR-013](../../decision-records/adr-013-recommended-autonomous-delivery.md)). Relocating its procedure must not weaken the contract-lock discipline (ADR-001) or the `--recommend` evidence boundary. A skill that loads *after* a contract decision was already made is a behavioral change, not a relocation.

## Approved Scope Change — Load Mechanism (maintainer decision, 2026-08-12)

**Recorded here, not in `## Contract (Locked)`, which is unaltered.**

This spec and its sibling `2026-08-12-disclosure-verify-spec` independently found that `required_skills:` is an **unconditional pre-load**. The finding is **verified and accepted**: `system-instructions.md` § *Harness contract* has the harness load every declared skill *"before any phase work begins"*, and `adapters/claude-code.md:396` says the same — *"the harness issues `Read skills/<name>/SKILL.md` calls before the consumer's first phase begins."* [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) §12's description of extracted skills as *"loaded on demand"* is false of the mechanism §18 chose.

**Ruling: `required_skills:` is not used by this spec.** Every extracted skill is reached by an inline `Read skills/<name>/SKILL.md` **at the step that needs it**. That form is genuinely conditional — the agent issues the call only if execution reaches that step — and it is already the shipping pattern in seven command files, `commands/create-spec.md:765` (`error-rescue-mapping`) among them.

**Why the mechanism changes and the plan does not.** Under the eager mechanism every extracted byte reappears in the floor, plus roughly 650 bytes of per-skill scaffolding that did not exist in the monolith. Extraction is therefore byte-neutral at best and mildly negative in practice — which is why this spec's projected ceiling missed by ~3,227 bytes and the sibling's needed a 27% prose compression to break even. The **deliverable, the extraction map, the five skill names, the nineteen-pin inventory, the 113-row rule inventory, the Compression Ledger, and the 24,960-byte budget are all unchanged.** Only the load mechanism and the ceiling accounting change. The locked contract's phrase *"loaded on demand"* becomes true for the first time under the inline form.

**What this changes downstream, carried through the rest of this document:**

1. No `required_skills:` block is added to `commands/create-spec.md`. Reachability is one inline `Read` per skill (Business Rule 7).
2. **Placement is the whole point**, so the inherited declare-all rule is reversed (Business Rule 3): each inline `Read` sits at the *narrowest* step that needs it, and hoisting one to the command preamble is forbidden.
3. Ceiling accounting becomes **path-dependent** (Business Rule 1): floor, worst-path ceiling, and at least one realistic partial path that skips skills.
4. `scripts/measure-invocation.py` was fixed on 2026-08-12 (`e8f2a09`) — it had treated `required_skills:` as conditional. It now reports `floor = base + command + eagerly-declared skills` and `ceiling = floor + inline-read skills`. **Every figure in this spec has been re-measured against the fixed tool.**
5. Business Rule 12's finding — that `error-rescue-mapping` must not be promoted to a declaration — is **strengthened, not weakened**. See Business Rule 12.

## Inherited Convention (from `2026-08-12-disclosure-implement-story`)

The pilot spec runs first and owns the pattern. Its naming convention and its no-regression bar bind this spec unchanged. Its **declaration rule does not**, for the reason recorded above:

| Inherited | Source | Effect here |
|---|---|---|
| ~~**Declare every extracted skill.**~~ **Superseded 2026-08-12.** The pilot's rule was correct under eager loading, where a curated `required_skills:` subset understated `ceiling_bytes` while the harness loaded it anyway. Under conditional loading it is backwards. | pilot BR8 | **Reversed.** No skill is declared. Each is inline-read at the narrowest step that needs it, and precise placement — not completeness of a list — is what the metric now measures. See Business Rule 3. |
| **`required_skills:` pre-load is unconditional.** `system-instructions.md` defines a static array loaded before the first phase begins; there is no per-invocation selection mechanism. | pilot § *The finding that shapes the work* | **Verified and accepted — and it is the reason the field is not used.** The conditional mechanism `system-instructions.md:250` names as the standing alternative is used instead. |
| **The ceiling may not regress**, and a regression requires a written justification naming the measured overage, the compression attempted with its yield, and an explicit maintainer decision. | pilot BR1 | Business Rule 1 below, with this file's re-measured numbers and a path-dependent report. |
| **Skill naming: six rules** — kebab-case noun phrase, 2–3 words, ≤30 chars; shape `<object>-<operation>` or `<operation>-<object>`; never named after the extraction site; `description:` is a bare-imperative verb phrase; a shared skill carries no consumer's vocabulary; collision protocol on the head noun with first-writer-owns. Documented in `.writ/docs/skills.md` → *Extraction Patterns* by the pilot's Story 1. | pilot BR3 | Business Rule 9 below; the names in § *The extraction map* are derived from it and re-checked at authoring time. |
| **The ADR-021 amendment** — byte budget supersedes the 400-line cap as the binding instrument; `required_skills:` pre-load is unconditional. | pilot § *The ADR-021 amendment* | Authored by the pilot. This spec is a **reader** of it and does not amend ADR-021 again. The 2026-08-12 mechanism ruling means the amendment's second clause is now a statement about a field this spec declines to use, not about a field it relies on. |

## Binding Budget (maintainer decision, 2026-08-12)

**A command file may not cost more to load than the shared contract it runs inside.**

The shared base every invocation pays — `system-instructions.md` (20,153 B) + `commands/_preamble.md` (4,807 B) — is **24,960 bytes**, measured 2026-08-12 by `python3 scripts/measure-invocation.py --root . --command create-spec`. That figure is the budget. The 400-line cap is a secondary, non-binding tripwire, superseded as the binding instrument by the pilot's ADR-021 amendment.

Two numbers bind, both re-measured 2026-08-12 against the **fixed** `measure-invocation.py` (`e8f2a09`):

- **Floor:** `command_bytes ≤ 24,960` (equivalently `floor_bytes ≤ 49,920`), down from 46,423 — a 46% cut. No skill is eagerly declared, so `floor_bytes = base + command` exactly.
- **Worst-path ceiling:** `ceiling_bytes ≤ 77,530`, i.e. `command_bytes + Σ(inline-read skill bytes) ≤ 52,570`. **The extracted system may not cost more on its worst path than the monolith costs on its worst path.**

Corrected measured baseline — the old table reported a ceiling of 71,383 because the pre-fix tool counted only `required_skills:`. `error-rescue-mapping` is an inline read and now sits where it belongs, above the floor:

| Figure | Value | Note |
|---|---|---|
| `command_bytes` | 46,423 | |
| `command_lines` | 871 | |
| `base_bytes` (irreducible) | 24,960 | |
| `eager_bytes` | 0 | no `required_skills:` declared, then or after |
| `floor_bytes` | **71,383** | base + command |
| `conditional_bytes` | **6,147** | `skills/error-rescue-mapping/SKILL.md`, inline-read at line 765 |
| `ceiling_bytes` | **77,530** | floor + the one inline skill |
| `base_share_of_floor` | 35.0% | |

The figure this spec previously called *"true worst case"* is the tool's `ceiling_bytes`. The third reported number is retired: there is one ceiling, and it already contains the inline read. **The create-spec agent computed 77,530 by hand before the tool was fixed; the fixed tool now returns exactly that.**

### Path-dependent accounting (replaces the single ceiling report)

Because every skill is now reached conditionally, the load a run pays depends on the path it takes. Business Rule 1 requires three figures, not one:

1. **Floor** — every run pays it, whatever happens next.
2. **Worst-path ceiling** — the tool's `ceiling_bytes`, which sums *every* inline-read skill in the file. It is an **envelope**, not an observed path: the tool cannot know that two reads are mutually exclusive. Story 6 must name the maximal *reachable* path and state whether it equals the envelope.
3. **At least one realistic partial path** that skips skills, with its arithmetic.

## Why This Exists

`commands/create-spec.md` is 46,423 bytes. Every `/create-spec` invocation — including one that answers "this is too small for a spec, use `/prototype`" — pays all of it, plus 24,960 bytes of shared base, before the first question is asked. 35% of that load is irreducible.

The measured composition (byte counts by `sed -n 'A,Bp' commands/create-spec.md | wc -c`, 2026-08-12):

| Block | Lines | Bytes | Share |
|---|---|---|---|
| Step 1.3 discovery conversation | 307–390 | 5,571 | 12.0% |
| `## Example Usage` worked transcript | 787–865 | 3,491 | 7.5% |
| `spec-lite.md` template + line budget | 598–718 | 3,750 | 8.1% |
| `--from-prototype` mode | 100–171 | 3,983 | 8.6% |
| `--from-issue` mode | 172–256 | 3,826 | 8.2% |
| `## Recommended Mode (--recommend)` | 31–99 | 4,130 | 8.9% |
| Step 2.4 `spec.md` requirements | 562–583 | 2,554 | 5.5% |
| Step 1.5 visual references | 484–520 | 1,938 | 4.2% |
| Step 1.4 contract proposal format | 405–453 | 1,891 | 4.1% |
| Steps 1.3b / 1.4b / 2.4b / 2.5–2.9 / other | — | 15,289 | 32.9% |

### The finding that reframes the work

**`scripts/eval.sh` asserts nineteen literal strings against `commands/create-spec.md`, and one of its checks parses that file's markdown table structure.** Verified 2026-08-12 by `grep -n '_literal "\$create_spec"' scripts/eval.sh` — 17 `require_literal`, 2 `forbid_literal` — plus the inline Python scenario at `scripts/eval.sh:737–800`, which reads the file, extracts the table under `### Authoritative \`--recommend\` Invocation Matrix` row by row, and asserts three *ordering* relations between headings inside it.

| Pin | Asserted by | Consequence |
|---|---|---|
| `Parse \`--recommend\` exactly once at command entry.` | `eval.sh:1644` | stays in the command |
| `Normal branch (authoritative): when \`--recommend\` is absent, follow every` | `eval.sh:1645`, plus an ordering assert that it precedes the matrix heading | stays, in order |
| `### Authoritative \`--recommend\` Invocation Matrix` + its 8 table rows, each `Supported…`/`Reject…` | `eval.sh:1646–1651` and the row-parsing scenario | table structure stays intact, immediately after the heading |
| `Validate the complete invocation before` | `eval.sh:1652`, plus an ordering assert that it precedes `### Autonomous Authoring Boundary` | stays, in order |
| `### Autonomous Authoring Boundary` | required to exist by that ordering assert — a missing heading makes `find` return `-1` and the comparison fail | heading stays |
| `recommendation-log.md`, `never triggers \`/implement-spec\`` | `eval.sh:1653–1654` | stay |
| `> **Dependencies:**`, `exact spec-folder IDs` | `eval.sh:1778–1779` | Step 2.4's dependency-header rules stay |
| `spec-status.py`, `Canonical complete-family spelling` | `eval.sh:1824–1825` | the complete-family detection sentence and the canonical-spelling note stay |
| `supersession-writeback.py`, `Amends` | `eval.sh:1972–1973` | Step 2.4b's helper invocation stays |
| `## Required Artifacts` | `scripts/eval-artifact-integrity.py:27` + `eval.sh:2725` — one of 7 high-traffic commands | the section stays |
| absence of `skip specs with \`Status: Complete\`` and `grep -v archive` | `eval.sh:1822`, `eval.sh:1867` (`forbid_literal`) | satisfied by absence; extraction must not reintroduce either string in the command **or** in any skill |

This spec **may not edit `scripts/eval.sh`** — `governor-enforcement` owns it. The pins are therefore fixed law, and two consequences follow. Both are **recorded deviations from ADR-021 point 1's retained-section list**:

1. **`## Required Artifacts` is retained.** `eval-artifact-integrity.py` names `create-spec` explicitly. The pilot spec retains it for the same reason (`eval.sh:2727`), so this is the established disposition, not a local exception.
2. **`## Recommended Mode (--recommend)` is retained whole** — all 69 lines / 4,130 bytes. Of those, only ~1,414 bytes are not directly pinned; relocating that much behind ~650 bytes of skill scaffolding plus an indirection would trade a real ADR-013 boundary for a section-list win. The locked contract's hardest constraint points the same way.

This contradicts the extraction sketch this spec was scoped against, which named *"the `--recommend` evidence flow"* as a skill. The sketch predates the pin measurement. **The measurement wins**, and the reason is recorded rather than the omission being silent.

### Why the ceiling is where this spec can fail

Same arithmetic that bit the pilot, stated up front. Relocating ~30,400 bytes of procedure into five skill files costs roughly 650 bytes each in frontmatter, `## Purpose`, `## When to Use`, and `## How to Apply` scaffolding — about 3,250 bytes of pure overhead that did not exist in the monolith. A thin command of ~16,000 bytes plus ~33,650 bytes of skills plus the incumbent 6,147-byte inline read lands the **worst path at ~80,757 against a 77,530 ceiling: roughly 3,227 bytes over.**

The overage is **numerically identical** to the pre-ruling projection, because switching the mechanism moves the same bytes across the floor/ceiling line on both sides of the comparison. The Compression Ledger's ~3,300-byte target still closes it, and the ledger is unchanged.

What the ruling *does* change is that the overage is now the worst case rather than the only case. Under the eager mechanism every run paid the full 33,650 bytes of skills whether it used them or not; under the inline mechanism a run pays for what it reaches. The partial paths in § *Detailed Requirements → Projected paths* are where the phase's claimed win actually lives.

The default response is **compression as a tactic within extraction** — ADR-021's own words, and the roadmap's *"relocates and **contracts** procedure."* The identified targets are enumerated in `sub-specs/technical-spec.md` → *Compression Ledger* and total roughly 3,300 bytes of duplicated worked examples, a near-identical pair of source-mode blocks, and restated budget arithmetic. Business Rule 1 sets the bar; the tracked-exemption path ADR-021 offers requires a written maintainer decision, not an implementer's shrug.

## 📋 Business Rules

1. **Report floor, worst-path ceiling, and at least one realistic partial path. The worst-path ceiling may not regress.** All from `scripts/measure-invocation.py` as fixed on 2026-08-12:
   - **Floor:** `command_bytes ≤ 24,960`, i.e. `floor_bytes ≤ 49,920`. `eager_bytes` must be `0` — no `required_skills:` is declared.
   - **Worst-path ceiling:** `ceiling_bytes ≤ 77,530`, i.e. `command_bytes + Σ(inline-read skill bytes) ≤ 52,570`. `conditional_bytes` now includes `error-rescue-mapping`'s 6,147, because the tool counts inline reads; the separate "true worst case" figure this spec used to require is retired into it.
   - **Partial paths:** at least one realistic path that now skips skills, reported as arithmetic. The `--recommend` invocation-rejection path and the bare collaborative docs-only run are the two named in § *Projected paths*; Story 6 reports measured values for both.

   The reported `ceiling_bytes` is an **envelope**, not a path — the tool sums every inline read in the file and cannot know which are mutually exclusive. Story 6 states whether the maximal *reachable* path equals it, and if not, by how much. A ceiling above 77,530 does not silently pass: it requires a written justification naming the measured overage in bytes, the compression already attempted with its measured yield, and an explicit maintainer decision recorded in the story file. "It is only 4% worse" is not a justification.

2. **Relocate and contract; never redesign.** Roadmap Phase 10 Out of Scope: *"This phase relocates and contracts procedure; it does not redesign workflows."* Every discovery step, question-policy rule, gate, heuristic, and threshold survives faithful in meaning.

   **The verification method is the rule inventory**, built from the pre-edit file: `sub-specs/technical-spec.md` § *Rule Inventory* enumerates all 113 rules with source line ranges and destinations. Each story checks off its own rows by quoting the destination; Story 6 reconciles all 113 in both directions. **A rule present before and absent after is a defect regardless of how much better the new wording reads.** Wording may change; the rule may not.

   *Permitted contraction* (pilot BR2's list, applied here): deleting a worked example that illustrates a format specified elsewhere in the same text; collapsing two near-identical blocks into one parameterized block; replacing a restated field list with a pointer to the one authority. *Not permitted:* dropping a threshold, a fallback value, a degradation path, or an "always/never" clause because it seemed obvious.

3. **Each skill is inline-read at the narrowest step that needs it. Hoisting is forbidden.** No `required_skills:` block is added. Every extracted skill is reached by exactly one `Read skills/<name>/SKILL.md` written into the phase-list step whose procedure it carries — and *inside* that step, not in the command preamble, not in `## Overview`, not in a "skills used by this command" block near the top. **A read hoisted above the branch that decides whether it is needed re-creates the eager mechanism by hand** and is a defect under this rule even though every automated check passes.

   *Narrowest* means: the last point at which the procedure is still not needed is the point after which the read is placed. Two disjoint paths that both need one skill get **one read per path**, at each path's own point of need — not one read hoisted to their common ancestor. `## References` still lists every skill; a list is not a load.

   This rule **reverses** the inherited pilot BR8, and the reversal is the direct consequence of the mechanism ruling. Under eager loading, curating the set understated the metric while the harness loaded everything anyway, so declaring all was the honest move. Under conditional loading, what a run pays *is* what the placement says it pays: precision is the entire mechanism, and a completeness rule would destroy it.

   **The locked contract's hardest constraint is still satisfied mechanically, by ordering rather than by eagerness.** `contract-lock` is read at Step 1.4, before the Step 1.4b decision and before the `--recommend` auto-lock; no path reaches the lock without having read it. That guarantee is now a property of *where the read sits*, which is why Business Rule 4 and Story 6's placement evidence carry weight they did not carry before.

4. **Contract-lock discipline is preserved verbatim, not paraphrased.** The five-option `AskQuestion` at Step 1.4b (`yes` / `edit` / `risks` / `blueprint` / `questions`) and its five response handlers survive with the same option ids, the same labels, and the same handling. ADR-001's rule — *"Use AskQuestion when you know the option space. Use Plan Mode when you need to discover it"* — survives as a rule wherever it lands. Phase 2 remains reachable only through an explicit human `yes` or the `--recommend` auto-lock, and through no third path.

5. **The `--recommend` boundary does not move and does not thin.** `## Recommended Mode` stays in `commands/create-spec.md` in full: the entry parse, the normal-branch statement, the terminal-scope paragraph, the eight-row invocation matrix, the `### Autonomous Authoring Boundary` heading, its auto-adopt and pause lists, and the `recommendation-log.md` writeback. No auto-adopt entry, pause condition, or rejection row is relocated, reworded, reordered, added, or removed. The scenario at `eval.sh:737–800` is the mechanical check; ADR-013 is the reason.

6. **Nineteen strings are pinned inside `commands/create-spec.md` by tooling this spec may not edit.** They survive **in the command file**, never in a skill. The full inventory with line numbers and minimum retained carrier is in § *The finding that reframes the work* and in `sub-specs/technical-spec.md` → *Rule Inventory*, where every pinned row is marked `C`. The two `forbid_literal` strings must stay absent from the command **and must not appear in any skill**.

7. **Every extracted skill must be reachable, exactly once, at its step.** A skill this spec creates appears as exactly one `Read skills/<name>/SKILL.md` inside the phase-list step that needs it — no declaration, no second copy of the read at another step on the same path. `measure-invocation.py` reports it under `conditional_skills` (and therefore `resolved_skills`), with `unresolved_skills` empty, `eager_skills` empty, and **no "loads both ways" warning** — the tool emits that warning when a name is both declared and inline-read, and it would mean the eager mechanism had crept back in. An unreferenced skill is dead weight that made the surface worse; a doubly-reachable one is a measurement that lies.

8. **`commands/_preamble.md` is not the escape valve.** 93 lines against a hard 95-line cap (`scripts/eval.sh:411–414`) — 2 lines of headroom. ADR-021 point 4 offers it as the home for detail shared by ≥3 commands; that valve is closed. Shared procedure becomes a shared skill. The cap is **not** raised: `2026-08-11-autonomy-gate-classes` owns that constant and its own Business Rule 1 states *"a cap chosen after the fact to accommodate whatever was written is not a cap."*

9. **Skill names follow the inherited convention and the collision protocol.** Kebab-case noun phrase, 2–3 words, ≤30 characters, unique across `commands:`, `agents:`, and `skills:` in `.writ/manifest.yaml`; shape `<object>-<operation>` or `<operation>-<object>`; never named after the extraction site (no `create-spec-*`, no step numbers); `description:` a bare-imperative verb phrase. Before running `/new-skill`, grep the manifest's `skills:` block for the intended name **and its head noun**; if a sibling spec already claimed it, declare the existing skill rather than authoring a near-duplicate, and record an ADR-014 `type: promotion` evidence entry. **First writer owns the name.** The pilot's eight names and the sibling specs' claims are checked at authoring time, not assumed from this document.

10. **No edits under `scripts/`, and one command file only.** `commands/create-spec.md` is the only command edited. Zero changes to `scripts/eval.sh` and `scripts/eval-leanness.py` — the `check_length` change, the absolute `per_surface.commands.chars` cap, the severity flip, and `MAX_SKILLS` belong to `governor-enforcement`. `.writ/manifest.yaml` and the root `SKILL.md` are touched additively through `/new-skill` Step 3.2 and `bash scripts/gen-skill.sh`.

11. **The Phase 10 foundation is preserved byte-identical.** `create-spec.md`'s existing `problem:` / `outcome:` / `exit_criteria:` frontmatter (`2026-08-11-component-contract`) and its `## Completion` section survive unchanged. `required_skills:` is appended; nothing is reflowed, reworded, or tidied. `## Completion`'s five numbered conditions, its `--from-prototype`/`--from-issue` clause, its suggested next step, and its terminal constraint are untouched.

12. **`error-rescue-mapping` is already extracted — do not re-extract it, and do not promote it to a declaration. The 2026-08-12 ruling strengthens this, and makes it the spec's worked example.** `commands/create-spec.md:765` already reads it inline, and that skill's `status_evidence` records `create-spec` as its one consumer. The command owns *when* error mapping applies (the data-flow heuristic at line 763); the pointer and the heuristic both stay, exactly where they are.

    Promoting it to `required_skills:` was always wrong, and the reason is now sharper rather than softer. Under the old accounting the argument was that a declaration would make every run pay 6,147 bytes it might never read. Under the fixed tool that is not an argument but a measurement: a declaration moves those 6,147 bytes from `conditional_bytes` into `floor_bytes`, and a documentation-only run — where the data-flow heuristic says *skip* — pays them for nothing. **Left inline, a docs-only run genuinely never pays them: its ceiling equals its floor.** That is the entire behavior this spec is now buying for its own five skills, already shipping in this file, at this line, since Phase 7. It is not a leftover to tidy up; it is the pattern.

13. **Growth in the `skills` surface is justified, not absorbed.** Five new skills raise the `skills` surface against its recorded `.writ/leanness-baseline.json` floor and will produce an unjustified-growth warning under ADR-019's ratchet. The disposition is a **bound justification** — the `(surface, metric)`-scoped `{date, value, text}` record built by `2026-08-11-governor-instrumentation` Story 1 and used by the pilot for the same reason — naming this spec, the bytes moved, and the corresponding `commands` reduction. `--update-baseline` is not used: it moves every surface's floor and records no reason.

## Detailed Requirements

### The extraction map

Five new skills. Source line ranges are against `commands/create-spec.md` at 871 lines. Names are derived from the inherited convention (Business Rule 9) and re-checked against the manifest at authoring time.

| # | Skill | Source blocks | Extracted bytes | Consumers beyond `create-spec` |
|---|---|---|---|---|
| 1 | `requirements-discovery` | Step 1.3 discovery conversation (307–390); `## Example Usage` worked transcript (787–865) | 9,062 | `plan-product`, `edit-spec` run the same open-ended interview shape |
| 2 | `contract-lock` | Step 1.3b overlap procedure (391–404, less the pinned detection sentence); Step 1.4 contract format (405–453); Step 1.4b decision + handlers (454–483) | 4,243 | `edit-spec` locks a modification contract against the same format |
| 3 | `spec-package-authoring` | Step 1.5 visual references (484–520); Step 2.2 date + owner (529–545); Step 2.3 tree (547–561); Step 2.4 non-pinned bullets (578–583); Step 2.4b non-pinned prose (594–596); `spec-lite.md` template + budget (598–718) | 6,905 | `edit-spec`, `verify-spec` read the same package shape |
| 4 | `user-story-decomposition` | Step 2.5 story plan (719–736); Step 2.6 story-file content and context hints (737–752, less the subagent dispatch); Step 2.7 README (753–756); Step 2.8 sub-spec selection (757–763) | 2,474 | `assess-spec`, `edit-spec` |
| 5 | `spec-source-prepopulation` | `--from-prototype` mode (100–171); `--from-issue` mode (172–256) | 7,809 | — |

Two names deserve their reasoning on the record, because the collision protocol is new and this is its first test:

- **`user-story-decomposition`, not `story-decomposition`.** A sibling disclosure spec claims `phase-decomposition`. The capabilities are genuinely different — one breaks a locked contract into stories, the other breaks a roadmap phase into specs — but the head noun is close enough that the qualified form removes any question. 24 characters, three words, inside the convention.
- **`spec-package-authoring`, not `spec-package-layout`.** "Layout" is a noun, not an operation; the convention's shape rule wants `<object>-<operation>`, and `what-was-built-authoring` in the pilot is the precedent.

### Load placement (replaces the `required_skills:` declaration)

**No `required_skills:` block is written.** Each skill is reached by one inline read, placed per Business Rule 3 at the narrowest step that needs it:

| Skill | Inline read placed at | Reached only when |
|---|---|---|
| `spec-source-prepopulation` | Step 0 of `--from-prototype` / `--from-issue`, after the mode branch is taken | the invocation carries `--from-prototype` or `--from-issue` |
| `requirements-discovery` | Step 1.3, at the start of the discovery conversation | discovery runs (skipped by an invocation rejected at the `--recommend` matrix gate) |
| `contract-lock` | Step 1.3b, **before** the overlap check and therefore before the Step 1.4b decision and the `--recommend` auto-lock | any run that reaches a contract proposal |
| `spec-package-authoring` | Step 1.5 on a UI feature; Step 2.2 otherwise — one read per path, per Business Rule 3 | Phase 2 begins |
| `user-story-decomposition` | Step 2.5, at the start of story planning | Phase 2 reaches decomposition |
| `error-rescue-mapping` *(incumbent, not extracted here)* | Step 2.8, line 765, **unchanged** | the data-flow heuristic says the feature needs error mapping |

Two placements carry the load-bearing guarantees and must be verified, not assumed:

- **`contract-lock` at Step 1.3b, not 1.4b.** The read must precede the auto-lock, or `--recommend` can lock a contract using a procedure it has not loaded. This is the ordering half of the locked contract's hardest constraint (Business Rule 3).
- **`spec-source-prepopulation` after the mode branch, not before it.** Placed before, it is read by every standard run and the largest single skill in the spec becomes a floor cost — the exact failure the ruling exists to avoid.

### Projected paths

Projections against the pre-spec baseline (floor 71,383 / ceiling 77,530). Story 6 replaces every cell with a measurement.

| Path | Skills read | Projected bytes | vs. today |
|---|---|---:|---|
| **Floor** — any run, before any branch | none | ~40,960 | — |
| **`--recommend` rejected at the invocation matrix** — an unsupported form, rejected before mutation | none | **~40,960** | −30,423 (−43%) against 71,383 |
| **Bare collaborative run, docs-only feature, no UI** | discovery, contract-lock, package-authoring, story-decomposition | ~64,200 | −7,200 against 71,383 |
| **`--from-issue`, data-flow feature (worst path)** | all five + `error-rescue-mapping` | ~77,460 after compression (~80,760 before) | ~77,530 bar |

**The `--recommend` versus collaborative contrast is at the rejection boundary, not in the happy path** — and this is worth stating plainly because the framing invites the opposite reading. A *successful* `--recommend` run still runs contract-first discovery (rule 9 of `## Recommended Mode`), still proposes a contract, still decomposes stories: it reads the same four skills a collaborative run reads. What `--recommend` uniquely adds is a validation gate that rejects eight enumerated forms **before any mutation and before any discovery** — and every skill read in this command sits downstream of that gate. So the mode's saving is total on the rejection path and nil on the success path. Story 6 reports both; reporting only the first would overstate the win.

### What stays in `commands/create-spec.md`

| Section | Why |
|---|---|
| Frontmatter contract, **byte-identical with nothing appended** — no `required_skills:` block | ADR-020 + Business Rule 11 + the 2026-08-12 mechanism ruling |
| `## Overview` | ADR-021 permits |
| `## Required Artifacts` | `eval-artifact-integrity.py` — recorded deviation, same disposition as the pilot |
| `## Invocation` as a table, all four forms | ADR-021 permits |
| `## Recommended Mode (--recommend)`, whole | Business Rule 5 — recorded deviation |
| Phase list with gate names and the inline `Read skills/<name>/SKILL.md` call inside each step that needs one | ADR-021 point 1 + Business Rule 3 |
| The pinned sentences: `spec-status.py` complete-family detection; Step 2.4's `> **Dependencies:**` rules, exact-folder-ID rule, canonical complete-family spelling, and `Amends:`/`Extends:` banner rules; Step 2.4b's `supersession-writeback.py` invocation and its never-blocks rule; the Step 2.8 data-flow heuristic and its `error-rescue-mapping` pointer | Business Rule 6 |
| Step 2.6's parallel-subagent dispatch (`generalPurpose`, model `fast`, up to 4, batch beyond) and Step 2.8's parallelism note | Orchestration — `lint-skill.sh` rejects `Task(` in a skill body; ADR-009 assigns it to the command |
| `## Completion`, byte-identical | ADR-021 point 1 + Business Rule 11 |
| `## References` — `_preamble.md`, `system-instructions.md`, and every skill this command loads | ADR-021 point 1 + `eval.sh check_preamble` |

### The phase list with gate names

ADR-021 point 1 keeps the *shape* visible when the detail is not. The phase list replaces each extracted `#### Step N` body with one row: step number, name, its gate if it has one, and — where the step needs a skill — the literal `Read skills/<name>/SKILL.md` call that loads it. The read is executable text inside the step, not a citation beside it; that is the difference between a load and a note. The gates, named explicitly because a reader must not have to open a skill to find them:

- **Invocation validation gate** (`## Recommended Mode`) — rejects before any mutation.
- **Cross-spec overlap gate** (Step 1.3b) — advisory; a *blocking* conflict pauses even under `--recommend`.
- **Contract lock gate** (Step 1.4b) — human `AskQuestion`, or `--recommend` auto-lock. The only door into Phase 2.
- **Visual reference gate** (Step 1.5) — bounded `AskQuestion`; auto-resolved under `--recommend`.
- **Package review** (Step 2.9) — terminal; the command stops.

### Skill authoring constraints

`bash scripts/lint-skill.sh skills/<name>/SKILL.md` must pass. Three rejection patterns bite here:

- **`Read skills/`** — `scripts/lint-skill.sh:52` rejects it in a skill body: no skill chaining. **The inline reads this spec introduces therefore live in `commands/create-spec.md` and nowhere else.** Where two skills need the same fact, the command carries the pointer; a skill may never load another skill to get it. Verified against both extraction plans at amendment time (2026-08-12): every inline read in this spec is placed in the command, and the two cross-skill pointers the plan does contain (Story 5 → Story 2's contract format, Compression Ledger entry 5) are prose references resolved by the command, not reads.
- **`Read commands/`** — no skill may point back into `commands/`.
- **`Task(`** — Step 2.6's subagent dispatch stays in the command.

Every skill carries `## Purpose` and `## When to Use` (lint-asserted) plus `## How to Apply` and `## Examples` per the `/new-skill` scaffold, with frontmatter `name`, `description` (bare-imperative verb phrase), `disable-model-invocation: true`, `status: candidate`, and a `status_evidence` line naming the extraction date and consumer.

## Out of Scope

- **`scripts/eval.sh` and `scripts/eval-leanness.py`, in any direction.** Business Rule 10. The nineteen pins are worked around, never relaxed, and no request to relax them is filed.
- **Raising `MAX_SKILLS`.** It is 12 (`scripts/eval-leanness.py:71`). The pilot already takes the count to 14; this spec takes it to 19. `check_ceilings` emits a **warning**, never a finding, so nothing breaks. The overage is measured, reported, and handed to `governor-enforcement`, which owns the constant.
- **`commands/_preamble.md`.** Business Rule 8. Not edited; cap not raised.
- **Amending ADR-021.** The pilot writes the amendment (byte instrument, unconditional pre-load). This spec reads it and adds nothing — **including the correction that ADR-021 §12's "loaded on demand" is false of the `required_skills:` mechanism §18 chose.** That inaccuracy is recorded by the 2026-08-12 mechanism ruling above and handed to whichever spec next amends the ADR; this spec routes around it by not using the field.
- **Declaring `required_skills:` at all.** Not an oversight and not deferred work — a maintainer ruling (2026-08-12). An implementer who adds the block "for discoverability" has converted every inline read back into a floor cost and inverted the spec's result while every check still passes.
- **Adding a conditional or mode-scoped form of `required_skills:`.** The eager schema in `system-instructions.md` is left exactly as it is. This spec uses the *other* mechanism that file already documents at line 250 — inline reads at the point of need — rather than changing the field.
- **Any other command file.** Four sibling disclosure specs cover the rest of the top 6.
- **Redesigning the discovery conversation, the contract format, story sizing, or the spec-lite budget.** Business Rule 2. The 95%-confidence threshold, the 3–5 acceptance criteria, the 5–7 tasks, the 100-line spec-lite limit, the 35/35/30 section budgets, and the 4-subagent batch size all survive at their current values even where they disagree with each other (§ Technical Concerns).
- **Promoting any skill past `candidate`.** ADR-014 earns `proven` from ≥3 evidence entries accrued from real use.
- **Editing `commands/edit-spec.md`, `commands/assess-spec.md`, `commands/plan-product.md`** — named as future consumers of three of these skills. They declare them when their own work runs; the collision protocol exists to stop a second author re-writing the same capability.
- **`.writ/manifest.yaml`'s stale `version:` and entry count.** Owned by `2026-08-11-retire-dead-prescription`. This spec appends five `skills:` entries and regenerates `SKILL.md`.

## Implementation Approach

Six stories. Stories 1–5 are **additive and mutually independent**: each authors one skill under its own `skills/<name>/` directory and touches nothing in `commands/`. The command keeps its prose while they run, so the tree is green and runnable throughout and each story reverts independently. Story 6 is the single writer on `commands/create-spec.md`.

1. **Story 1 — `requirements-discovery`.** Largest extraction (9,062 B) and furthest from any pin. Reads the pilot's convention from `.writ/docs/skills.md` → *Extraction Patterns* and runs the collision protocol for all five names before any `/new-skill` call, so four sibling stories are not each re-deciding a shared namespace.
2. **Story 2 — `contract-lock`.** The ADR-001 spine; highest behavioral risk in the spec.
3. **Story 3 — `spec-package-authoring`.** Highest pin density — Steps 2.4 and 2.4b split mid-list between pinned sentences and movable prose.
4. **Story 4 — `user-story-decomposition`.** Smallest extraction; carries the capability/orchestration split the lint enforces.
5. **Story 5 — `spec-source-prepopulation`.** Two source modes, one skill; the largest compression target.
6. **Story 6 — the thin command, the budget, and the no-drift proof.** Rewrites `commands/create-spec.md`, declares all five, deletes the relocated prose, applies the Compression Ledger, measures floor and ceiling, reconciles all 113 inventory rows, and records the leanness bound justification.

Stories 1–5 all append to `.writ/manifest.yaml`'s `skills:` block and regenerate the root `SKILL.md`. `/new-skill` appends alphabetically and `gen-skill.sh` regenerates deterministically, so a parallel run's conflict is textual, not semantic: the last to land re-runs `bash scripts/gen-skill.sh` and confirms `--check` passes.

## Success Criteria

1. `python3 scripts/measure-invocation.py --root . --command create-spec` reports `command_bytes ≤ 24,960` (from 46,423), `floor_bytes ≤ 49,920` (from 71,383), `eager_bytes == 0`, and `command_lines ≤ 400` (from 871).
2. **`ceiling_bytes ≤ 77,530`** — `command_bytes + conditional_bytes ≤ 52,570`, against the corrected pre-spec ceiling of 77,530. Reported with the floor and with at least one measured partial path (§ *Projected paths*), plus a statement of whether the maximal reachable path equals the tool's envelope. Any overage carries the written justification Business Rule 1 specifies.
3. Five skills exist under `skills/`, each `status: candidate`, each named per the inherited convention with its collision check recorded, `bash scripts/lint-skill.sh skills/*/SKILL.md` clean for every file, each with a `.writ/manifest.yaml` entry, and `bash scripts/gen-skill.sh --check` reporting no delta.
4. **`commands/create-spec.md` declares no `required_skills:`.** `measure-invocation.py` reports `eager_skills: []`, `conditional_skills` holding exactly the five extracted names plus `error-rescue-mapping`, `unresolved_skills` empty, and no "loads both ways" warning; `python3 scripts/eval-leanness.py --root .` reports `required_skills_declarations: 0` for this command **with no finding** (`check_required_skills` only reports names that fail to resolve, so zero declarations is silent by design). Each of the six inline reads appears exactly once, inside the phase-list step named in § *Load placement*, and `grep -c 'Read skills/' commands/create-spec.md` returns 6.
5. `bash scripts/eval.sh` produces **no new findings** against its pre-spec baseline. All nineteen literal assertions pass, `check_recommended_spec_implementation` passes its eight row assertions and three ordering assertions, and `check_artifact_integrity` still finds `## Required Artifacts`. Neither `forbid_literal` string appears in the command or in any of the five skills.
6. **All 113 rule-inventory rows reconcile in both directions** — every row names a destination that exists, and no skill or command section carries a rule absent from the table.
7. **No behavioral drift.** `## Recommended Mode`, `## Completion`, and the frontmatter's `problem:`/`outcome:`/`exit_criteria:` values are byte-identical to the spec's base commit, proven by `diff` against `git show <base>:commands/create-spec.md`. The five-option contract decision survives with identical option ids and labels, and Phase 2 is reachable only through it or the `--recommend` auto-lock.
8. `skills/` count and the `skills` surface growth are both reported: the count against `MAX_SKILLS = 12` (expected 19 with the pilot's eight landed), and the growth as a bound justification in `.writ/leanness-baseline.json` naming this spec — not an `--update-baseline` sweep.
9. `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok` with `2026-08-12-disclosure-implement-story` resolving.

## Technical Concerns (surfaced at contract time)

- **The worst-path ceiling is the failure mode, and the margin is roughly 3,200 bytes.** Projected skills (~33,650) plus the incumbent inline `error-rescue-mapping` (6,147) plus a projected thin command (~16,000) exceed the corrected 52,570-byte allowance. The Compression Ledger in `sub-specs/technical-spec.md` identifies ~3,300 bytes of permitted contraction — a worked transcript that restates a format specified 400 lines earlier, a near-identical pair of source-mode blocks, and budget arithmetic stated three times. If the ledger's measured yield falls short, the honest outcome is the written justification Business Rule 1 requires, not a skill trimmed below the rules it must carry. Note that the overage is unchanged by the 2026-08-12 mechanism ruling: the same bytes moved across the floor/ceiling line on both sides of the comparison.
- **Placement, not declaration, is now the thing a reviewer must check by hand.** Under the eager mechanism the load discipline was a five-line YAML list that either was or was not complete. Under the inline mechanism it is six `Read` calls whose *positions* determine what every run pays, and no tool checks a position. `measure-invocation.py` sums the reads wherever they sit; `lint-skill.sh` never opens the command; `eval.sh` has no opinion. A read hoisted to the command preamble reproduces the eager mechanism exactly, reports an identical `ceiling_bytes`, and passes every check in this spec. Business Rule 3 states the rule and Story 6's placement evidence is the only enforcement.
- **The eval pins were not known when this work was scoped, and they contradict the scoping sketch.** The `--recommend` evidence flow was proposed as an extraction target; it is eval-parsed, ADR-013-load-bearing, and 4,130 bytes. It stays. If a reviewer disagrees, the move is to reopen the contract, not to extract it anyway.
- **Total product surface grows while per-invocation load falls.** Roughly 3,250 bytes of skill scaffolding are added that did not exist in the monolith. `eval-leanness.py` measures surfaces, not invocations, so it reads this as growth in `skills/` and shrinkage in `commands/`. That is the trade ADR-021 chose and the reason `measure-invocation.py` exists. Business Rule 13 is the disposition.
- **`--recommend` is the mode most exposed to load-order defects, and after the 2026-08-12 ruling the thing that closes it is placement, not eagerness.** Auto-lock at Step 1.4b happens without a human gate, so a late-loading `contract-lock` would produce an *unreviewed* wrong lock rather than a visibly wrong prompt. The eager mechanism removed that failure class by loading everything up front — at the price the ruling rejects. The inline mechanism removes it by placing the `contract-lock` read at Step 1.3b, strictly before the Step 1.4 proposal and the Step 1.4b decision, so no path reaches the lock without the skill. **This is a stronger guarantee than it sounds and a more fragile one than the old design: it holds exactly as long as that read stays above that gate.** Story 2 and Story 6 both carry it as explicit evidence, and it is the one placement where "narrowest step" and "before the gate" must be reconciled deliberately rather than mechanically.
- **Existing internal inconsistencies are preserved, not fixed.** Step 2.5 says *"5-7 implementation tasks max"*; the frontmatter `exit_criteria` says *"no more than 7 implementation tasks"*; `## Completion` says *"5-7 implementation tasks."* Separately, `--from-issue` is documented at line 175 but absent from `## Invocation` (25–29). Business Rule 2 forbids resolving the first here — a relocation that "tidies" a threshold is a redesign. The second is a missing documentation row for a mode already named in the `--recommend` matrix; Story 6 adds it and says so.
- **Three of the five skills are named with consumers beyond `create-spec`** — `edit-spec`, `assess-spec`, `plan-product`. Those commands are not edited here (Out of Scope), so those consumers are prospective. The `status_evidence` line must say so rather than claiming multi-consumer use that does not exist yet; ADR-014's `proven` bar is ≥3 recorded evidence entries, not three plausible readers.
- **`skills/` reaches 19 against `MAX_SKILLS = 12`.** Warning only, by design. The count is reported and handed to `governor-enforcement`. Raising the cap here would be the "cap chosen after the fact" failure `2026-08-11-autonomy-gate-classes` banned for `_preamble.md`.
