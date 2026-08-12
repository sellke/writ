# Spec: Progressive Disclosure — `/ship`

> **Status:** Closed — Not Implemented (measured evidence, 2026-08-12)
> **Owner:** @AdamSellke
> **Created:** 2026-08-12
> **Dependencies:** [2026-08-12-disclosure-implement-story]
> **Origin:** `/plan-product` Phase 10 discovery (2026-08-11), governed by [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md). `/ship` is one of the six command files ADR-021 targets in descending size order, and it is the one where the binding budget leaves the least room: `commands/ship.md` is 28,371 bytes against a 24,960-byte budget, a 12% gap. It is also the only one of the six that crosses the **production boundary** ([ADR-022](../../decision-records/adr-022-autonomy-gate-classes.md)) and the only one that performs a durable provenance write (`refs/notes/writ`, spec `2026-07-18-git-notes-audit-channel`). Both properties constrain what may be relocated.

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

**Deliverable:** `commands/ship.md` — 28,371 bytes / 627 lines — reduced to a thin contract with its per-phase procedural detail extracted to `skills/<name>/SKILL.md`, loaded on demand via `required_skills:`.

**Must include:** The thin contract retains only what [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) permits — frontmatter contract (ADR-020), `## Overview`, `## Invocation` table, the phase list with gate names, `## Completion`, `## References`. Skills authored through `/new-skill` (born `status: candidate`, lint-clean). **Follow the extraction pattern and skill-naming convention established by the dependency spec `2026-08-12-disclosure-implement-story`.**

**Hardest constraint:** `/ship` crosses the **production boundary** — it opens a PR. [ADR-022](../../decision-records/adr-022-autonomy-gate-classes.md) classifies merge/PR/release/tag as a **human gate**. Relocating procedure into on-demand skills must not move a gate-crossing decision into a skill that loads without the gate having fired. `/ship` also **attaches the git-notes audit digest to the landed commit** (spec `2026-08-18-git-notes-audit-channel`); that is a durable provenance write and must not become conditional on a skill loading.

> **Contract erratum (recorded, contract text unchanged).** The locked text cites spec `2026-08-18-git-notes-audit-channel`. The spec's actual slug is **`2026-07-18-git-notes-audit-channel`** (`.writ/specs/archive/2026-07-18-git-notes-audit-channel/`, verified 2026-08-12). The contract block is reproduced verbatim above and is not edited; every other reference in this package uses the real slug. Nothing about the constraint changes — only the date component of the citation was wrong.

### Approved scope change — the loading mechanism (maintainer decision, 2026-08-12)

**The contract block above is reproduced unedited.** It says the extracted procedure is "loaded on demand via `required_skills:`". That clause is superseded by maintainer ruling on 2026-08-12: the mechanism is an **inline `Read skills/<name>/SKILL.md` issued at the step that needs it**, and `required_skills:` is **not used by this spec**. Everything else in the contract stands — the deliverable, ADR-021's permitted sections, `/new-skill` authoring, the dependency spec's naming convention, the production boundary, and the durable provenance write. **The extraction plan is unchanged**; only the mechanism that reaches the extracted skills changes.

**Why, and this spec's own § *The measurement hides a load that already happens* is the sharpest evidence for it.** `required_skills:` is an *eager* pre-load: `system-instructions.md` says the harness loads the named skills "before any phase work begins", and `adapters/claude-code.md:396` says the harness issues the `Read` calls "before the consumer's first phase begins". A declared skill is paid on **every** invocation. Declaring this spec's five skills — the four new ones plus `conventional-commits` — would have moved ~20,900 bytes into the **floor**: a post-spec floor of ~57,200 against a pre-spec 53,331, a **rise of ~3,900 bytes on every run**, including the ones that stop at a merge conflict. Meanwhile `ship.md:224` has been doing the correct thing all along — an inline `Read skills/conventional-commits/SKILL.md` at Step 4, the step that needs it. This spec's Story-1 finding that the tool was blind to those 9,985 bytes is what exposed both defects: the instrument's, and the mechanism's.

**The instrument has been fixed** (`e8f2a09`). `scripts/measure-invocation.py` treated `required_skills:` as conditional and ignored inline reads entirely. It now reports `floor = base + command + eagerly-declared skills` and `ceiling = floor + inline-read skills`, and re-measured on this tree `/ship` is **floor 53,331 / conditional 9,985 / ceiling 63,316** — exactly the adjusted baseline this spec computed by hand. The number is no longer an argument the story has to make; it is what the tool prints.

**What this changes downstream.** Business Rule 1's escalation ladder **collapses** — the ceiling now passes outright, with no justification owed (see § *Projected budget*). Business Rule 3's "declare all, not a subset" clause is **reversed** into a placement requirement. Business Rule 5's composition mechanism becomes two inline reads at Step 4 rather than two declarations. Business Rules 4 and 6 get **stronger**, because a conditional load can genuinely fail. Business Rule 12 tightens: the frontmatter is now byte-for-byte unchanged rather than "unchanged plus one key". The clause ledger, the seven `eval-git-notes-audit.py` pins, the retained-content minimums, and the skill roster are untouched.

## Binding Budget (maintainer decision, 2026-08-12, revised for the corrected instrument)

**A command file may not cost more to load than the shared contract it runs inside.** The budget is the irreducible shared base every invocation pays:

| Component | Bytes | Verified |
|---|---|---|
| `system-instructions.md` | 20,153 | `measure-invocation.py --root . --command ship` |
| `commands/_preamble.md` | 4,807 | same |
| **Shared base = the budget** | **24,960** | same |

`commands/ship.md` must land **≤ 24,960 bytes**, down from 28,371. The 400-line cap ADR-021 proposes is a **secondary, non-binding tripwire** — `scripts/eval.sh check_length` still enforces 2000 for commands (verified 2026-08-12, `eval.sh:423`), and raising it is `2026-08-11-governor-instrumentation`'s work, not this spec's.

**12% is the smallest gap of the six files, which is exactly why the byte cap alone is an insufficient success test.** Deleting the ASCII pipeline diagram (1,445 bytes) and the duplicated `--dry-run` block (1,138 bytes) would clear the budget without extracting anything, and would satisfy every number in this section while falsifying the contract. § Detailed Requirements therefore also fixes a **design target of ≤ 13,000 bytes**, derived from what ADR-021's permitted section list plus the two mandatory retentions can actually hold. The budget is the pass/fail line; the design target is the shape.

## Why This Exists

Measured against this working tree on 2026-08-12, not inherited from the roadmap:

| Measure | Value | How verified |
|---|---|---|
| `commands/ship.md` | 28,371 bytes / 627 lines | `wc -c -l commands/ship.md` |
| Invocation floor (base + command) | 53,331 bytes | `measure-invocation.py --command ship` |
| Invocation ceiling (floor + inline-read skills) | **63,316 bytes** | same — `conditional_bytes: 9,985` |
| `required_skills:` declared by `ship.md` | **none** | `eager_skills: []`, `eager_bytes: 0` |
| Inline-read skills | `conventional-commits` (`ship.md:224`) | `conditional_skills` in the same report |
| Base share of floor | 46.8% | same |

### The measurement hid a load that already happened — and that finding decided the mechanism

`ship.md` line 224 instructs `Read skills/conventional-commits/SKILL.md` — 9,985 bytes — in prose, inside Step 4. The pre-`e8f2a09` `scripts/measure-invocation.py` resolved `required_skills:` frontmatter only, so that load was invisible to it and `conditional_bytes` reported `0`. **Any `/ship` run that reaches commit-message authoring already pays 63,316 bytes, not 53,331.** The spec computed that by hand; the fixed tool now prints it.

Two things followed from the finding, and the second is the more important:

1. **The baseline was understated by 9,985 bytes.** Every ceiling comparison in this package is against **63,316**. Against the old 53,331, a correct extraction looked like a 7% regression.
2. **`ship.md:224` was already the right mechanism.** An inline `Read` at the step that needs it is genuinely conditional — a run that pauses on a merge conflict at Step 2 never issues it and never pays. `required_skills:` cannot express that: it is a static array loaded before phase 1. Declaring the five skills would have raised the *floor* from 53,331 to ~57,200. **The one thing `/ship` was doing that the tool could not see was the one thing worth copying.** The maintainer ruling of 2026-08-12 makes it the mechanism for all four new skills; `ship.md:224` itself is left exactly as it is.

The consequence for reporting is the opposite of what this spec originally braced for. There is no phantom ceiling rise to explain, because `conventional-commits` is counted on both sides by construction — it was an inline read before and it stays an inline read after.

### The file argues against its own extraction

`ship.md:226` carries a **Non-extraction note** from Phase 7:

> `/ship`'s high-traffic capability was already extracted as `conventional-commits`; the commit-splitting and PR-assembly logic above is command-specific orchestration, not a reusable capability. No further skill extraction from `/ship` was warranted.

ADR-021 reverses that conclusion for all six top files. The Prime Directive requires new evidence rather than pressure for a reversal, and there is some: the Phase 7 note judged *reusability*, while ADR-021's criterion is *per-invocation load*, which nothing measured until `scripts/measure-invocation.py` existed. A capability used by exactly one consumer still stops being paid for on every invocation once it is conditional. The note is superseded in place by Story 4, with that reasoning recorded — not deleted, because deleting it would leave the next reader to re-derive the same question.

### Two things cannot move, and one script must not be touched

- **The production boundary.** `_preamble.md`'s Autonomy Gate Classes table (added by `2026-08-11-autonomy-gate-classes`) marks merge/PR/release/tag/publish a **human gate**, and its Narrow Recommended-Delivery Exception states that no `--recommend` command "merges, opens PRs, or releases." `/ship` is therefore always human-invoked; the invocation *is* the gate. What must not happen is a gate-crossing **decision** — draft-vs-ready, push, `gh pr create` — landing in a file the harness may or may not have loaded.
- **The provenance write.** `scripts/eval-git-notes-audit.py` `scenario_ship()` asserts **seven literal-string conditions against `commands/ship.md` itself** (verified 2026-08-12). Extracting Step 6 wholesale fails `bash scripts/eval.sh`. The check is not incidental — it is the mechanical expression of the hardest constraint, and it is the cheapest verification this spec has.
- **`scripts/resolve-spec-reference.py`** is the shared Spec Reference heuristic that `/ship` and `/release` both call (spec `2026-08-04-post-merge-archival-hook`, Story 1). Its module docstring records why it exists: `ship.md` described the matching only as prose, so `release.md` "could not reuse it without either duplicating the prose or drifting into a second, independent heuristic." Re-describing the heuristic inside a skill would recreate exactly that defect.

## 📋 Business Rules

1. **The extracted system may not weigh more than the monolith, and the report is path-dependent.** Report `floor_bytes`, `ceiling_bytes`, **and the realistic partial paths** before and after from `python3 scripts/measure-invocation.py --root . --command ship`. The floor **must** fall. The ceiling bar is **≤ 63,316 bytes** — the *corrected* pre-spec ceiling from the fixed instrument (`e8f2a09`), which counts `ship.md:224`'s inline read of `conventional-commits`. "Only 7% worse" is not a justification, and the ceiling is never closed by deleting rules.

   **The escalation ladder this rule used to carry is withdrawn as obsolete.** It read: exceeding 63,316 fails outright; landing between 53,331 and 63,316 requires a three-part justification showing the excess is `conventional-commits` becoming visible. That ladder existed because the instrument was blind and `required_skills:` would have made the load appear from nowhere. Neither condition holds now — 63,316 is the measured baseline, not an adjustment argued for in prose, and `conventional-commits` is an inline read on both sides. There is one bar, 63,316, and the projection clears it by ~5,800 bytes (§ *Projected budget*). **If the measurement clears it, no justification is owed and none should be written.** If it does not, the standard three-part form applies: measured overage, compression attempted with **measured** yield, explicit maintainer acceptance.

   **Two figures are still reported alongside, both because they are informative and neither because a rule is in doubt:**
   - `ceiling_bytes` **excluding** `conventional-commits` — pre-spec 53,331 vs post-spec, so the symmetry of that 9,985-byte load is visible rather than asserted.
   - **The path table** (§ *Projected budget*): a run that pauses on a merge conflict, a `--no-split` run, a run with `writ.auditNotes=false`, and a full run to PR-open plus audit note. On a sequential pipeline the worst path is the common one, so a single ceiling number hides which runs actually got cheaper. Unlike the sibling `/release` spec, **every `/ship` path improves**; say so with the numbers, not as a claim.

2. **Relocate and contract; do not redesign — verified by clause ledger, not by reading.** Every normative clause in today's `ship.md` — each imperative, table row, decision branch, output block, and warning — is enumerated in `sub-specs/clause-ledger.md` (Story 1) with a pre-extraction byte offset. After Story 4, every ledger row carries exactly one disposition: **`retained`** (still in `ship.md`), **`skill:<name>#<section>`**, or **`deduped:<reason>`**. A row with no disposition is a dropped clause and is a spec failure. `deduped` is permitted only where the same clause appears twice in today's file (the `--dry-run` previews of Steps 4–5 are duplicated verbatim in `## Dry Run Mode`); it is never a licence to decide a clause is unnecessary. The ledger is closed out in Story 5 and its final state is the evidence.

   Backing the ledger, these literals must still be present after the change (Story 5 runs the greps):

   | Literal | Must remain in |
   |---|---|
   | `refs/notes/writ`, `refs/notes/commits`, `git notes --ref=writ add -f -F`, `writ.auditNotes`, `landed`, `squash`, `minimal digest` | `commands/ship.md` (Business Rule 6) |
   | `scripts/resolve-spec-reference.py resolve --branch … --commits … --specs-dir .writ/specs` | `commands/ship.md` **or** `skills/pr-body-composition/SKILL.md` |
   | `--test`, `--no-split`, `--draft`, `--rebase`, `--dry-run` | `commands/ship.md` `## Invocation` (all five rows plus bare `/ship`) |
   | `Summary`, `Changes`, `Spec Reference`, `Test Results`, `Spec Health`, `Drift Report`, `Review Notes` | the PR-body section list — the first four in `commands/ship.md` (they are named in its `exit_criteria`), all seven in `skills/pr-body-composition/SKILL.md` |

3. **Every extracted skill is reached by exactly one inline `Read` at the narrowest step that needs it — placement is the mechanism, and hoisting is forbidden.** This rule **reverses** the "declare all, not a subset" clause it replaces. That clause was correct under eager loading, where a static array under-filled understates the number being judged and the only honest thing to do is fill it completely. It is backwards under conditional loading, where *where the call sits* is the entire saving.

   Each new skill is (a) reached by an inline `Read skills/<name>/SKILL.md` placed at the phase or step that consumes it — never in the frontmatter, never in `## Overview`, never hoisted into a preamble or a "load these first" block — (b) named at the phase that consumes it in the phase list, and (c) resolvable, with `measure-invocation.py --command ship` reporting it under `conditional_skills` and `unresolved_skills: []`. The phase-list table must carry **no** `Read skills/` string: a table read top-to-bottom as a map is exactly the hoist this rule forbids. A skill created and never read is dead surface; a skill read but not named at a phase is unfindable by a reader of the contract.

   **`required_skills:` is not used.** `system-instructions.md` describes a static array loaded before the first phase, and `adapters/claude-code.md:396` confirms it — declaring the five skills would have raised the floor from 53,331 to ~57,200. `measure-invocation.py` must report `eager_bytes: 0` and `eager_skills: []`, and it emits an explicit warning if a skill is both declared and inline-read; that warning is a story failure. Because there is no declaration, `eval-leanness.py`'s `check_required_skills` has nothing to resolve for `commands/ship.md` and correctly reports nothing — its silence is not evidence of anything and must not be cited as a pass.

   The two costs this rule used to accept are now **saved instead**: `/ship --no-split` does not reach the commit-plan composition and never issues `commit-organization`'s `Read`; a run with `writ.auditNotes=false` skips Phase 6 and never issues `audit-digest-composition`'s. Those are the paths Business Rule 1's table measures.

4. **No gate-crossing decision may live in a conditionally-loaded file — and this rule is now stronger, not weaker.** A clause is gate-crossing if a wrong answer produces an unintended push, PR, merge, tag, release, or publish — the production-boundary class in `_preamble.md`'s Autonomy Gate Classes table.

   Under the withdrawn `required_skills:` mechanism one could argue the harness always pre-loaded the skill, so a relocated gate would still be present in context. **The inline mechanism removes that argument entirely.** A `Read` is an instruction the agent may not reach, may skip, or may have fail — the load is genuinely conditional, which is why the mechanism was adopted and precisely why nothing that decides may sit behind one. The rule's own load test is unchanged and now has teeth: *if this skill silently failed to load, could `/ship` still open a PR, and would it open the wrong one?* Four clauses in `ship.md` qualify and stay in the command file:

   - the **draft-vs-ready determination table** (five conditions) and the `--draft` override;
   - `git push -u origin [branch-name]` and `gh pr create …`, including the `gh auth login` rescue;
   - the **commit-plan `AskQuestion` approval gate** before git history is restructured;
   - the **merge-conflict pause** and its explicit "do not auto-resolve" rule, plus the `--test` failure branch (fix / ship-anyway-as-draft / abort), because option 2 sets draft status.

   A skill may describe how to *compose* the material such a decision consumes. It may not contain the decision. The test to apply during authoring: *if this skill silently failed to load, could `/ship` still open a PR, and would it open the wrong one?* If yes, the clause is in the wrong file.

5. **Reuse `conventional-commits`; never extract a near-duplicate; leave `ship.md:224` exactly as it is.** `skills/conventional-commits/SKILL.md` is `status: proven` with three evidence entries, one of which cites `commands/ship.md`. The extracted `commit-organization` skill owns *which* changes group into *which* commit; `conventional-commits` owns *how to phrase* each message. `commit-organization` must not restate the type vocabulary, the scope rules, the summary craft rules, the body guidance, or the footer table. **It also must not `Read` it:** `scripts/lint-skill.sh:52` rejects a `Read skills/` line in skill prose as skill-chaining (code blocks are exempt from the body scan, and that exemption is not a workaround).

   **The composition happens in `commands/ship.md`, by two inline reads at Step 4** — `commit-organization` and the existing `conventional-commits` read at line 224 — not by two `required_skills:` entries. `ship.md:224` is **not converted into a declaration and not re-extracted**: it is already the correct mechanism, it is 9,985 bytes counted symmetrically on both sides of every measurement, and declaring it would move those bytes into the floor for no benefit. Story 4 preserves it in place at Step 4 and places `commit-organization`'s read beside it.

6. **The git-notes provenance write stays unconditional in the command — and "unconditional" now means something sharper.** Under an eager pre-load, "the skill will be there" was a defensible assumption. Under an inline `Read`, the digest-composition skill is loaded only if Phase 6 is reached and the call succeeds, so the attach path must be complete without it. `commands/ship.md` retains, in its own body: the `writ.auditNotes` opt-out gate; landed-SHA resolution for all three land strategies (squash / merge commit / rebase-and-merge); the exact `git notes --ref=writ add -f -F` invocation with its explicit `--ref=writ`; the prohibition on writing `refs/notes/commits`; the strictly-non-blocking rule and its `⚠️ audit note not attached — {error}` log line; the **minimal-digest fallback** for when no `## What Was Built` records are found; and the confirmation line. Only the *composition* of the full digest from WWB records moves to `skills/audit-digest-composition/SKILL.md`. The consequence is deliberate and must hold: **if that skill never loads, `/ship` still attaches the fallback digest.** Verification is mechanical — `bash scripts/eval.sh` must report all seven `git-notes-audit` `scenario_ship` checks passing.

7. **`scripts/resolve-spec-reference.py` is referenced, never reimplemented and never edited.** No skill or command in this spec describes the branch-name / commit-message matching heuristic, its dedup rule, or its `matched` / `none` / `ambiguous` outcomes as procedure to follow. They state the call, and state the three outcomes' handling: `matched` populates from that spec's folder, `none` and `ambiguous` both write "Standalone change (no spec)". `git diff --name-only` must list no path under `scripts/`.

8. **`commands/_preamble.md` is not touched and its cap is not raised.** It is 93 lines against a 95-line limit (`eval.sh:412`, verified 2026-08-12). Shared procedure becomes a **shared skill**, never a preamble addition. The cap belongs to `2026-08-11-autonomy-gate-classes`.

9. **This spec owns exactly one command file.** `commands/ship.md`, plus the skills it creates and their `.writ/manifest.yaml` entries and the regenerated root `SKILL.md`. No other file under `commands/` is edited — `commands/release.md` in particular belongs to a sibling spec, even though it shares `resolve-spec-reference.py` and the `refs/notes/writ` channel. No file under `scripts/`, `agents/`, `adapters/`, or `.writ/decision-records/` is edited.

10. **Skills are born through `/new-skill`, follow the phase naming convention, and stay lint-clean.** Each new skill: `status: candidate` with `status_evidence` recording the extraction date and consumer; `disable-model-invocation: true`; `## Purpose` and `## When to Use` present; a `description:` that survives `bash scripts/lint-skill.sh`; an alphabetically placed entry in `.writ/manifest.yaml`; and `bash scripts/gen-skill.sh --check` reporting no delta. A description that reads as a workflow ("Run the full…", "Execute the entire…") is rejected by the lint at authoring time — reach for a capability phrasing rather than arguing with the lint.

    **Naming is not this spec's to invent.** The dependency spec lands the convention in `.writ/docs/skills.md` → *Extraction Patterns*, and that document is the authority: kebab-case noun phrase, 2–3 words, ≤30 characters, shaped `<object>-<operation>`, **never named after a command, gate, or step**; `description:` a bare-imperative verb phrase; a reusable skill carries no consumer vocabulary. Before scaffolding, grep `.writ/manifest.yaml` for the name **and its head noun** — a near-match means declaring the existing skill, not forking it. This spec's roster (`repo-convention-detection`, `commit-organization`, `pr-body-composition`, `audit-digest-composition`) was checked against the convention and against the five sibling specs' rosters on 2026-08-12 with no collision; re-check at authoring time, because the namespace is shared and the siblings are moving.

11. **Skills-surface growth is justified, never re-baselined.** These four skills grow the `skills` surface against `.writ/leanness-baseline.json` (baseline 932 lines / 41,620 chars, no justification recorded before Phase 10). Record a bound justification in the `skills` surface's `justifications` block naming this spec and the extraction, in the form the `commands` and `agents` surfaces already use. **Never run `--update-baseline`** — that erases the ratchet ADR-019 built rather than justifying the growth.

12. **The foundation contract is preserved byte-for-byte, and now the whole frontmatter block is.** `ship.md`'s `problem:`, `outcome:`, `exit_criteria:` (from `2026-08-11-component-contract`) and its `## Completion` section survive unchanged — and because `required_skills:` is not used (Business Rule 3), **no key is added at all**, so the frontmatter diffs empty against its pre-spec text. `exit_criteria` names "Summary, Changes, Spec Reference and Test Results sections" — so the contract must remain self-sufficient about *which* sections the PR body carries even though the skill owns how to fill them (Business Rule 2's literal table enforces this). If authoring reveals a genuine contradiction between an `exit_criteria` entry and the thinned body, record it in the story notes; do not silently reword the frontmatter.

## Detailed Requirements

### What `commands/ship.md` retains

ADR-021 permits: frontmatter contract, `## Overview`, `## Invocation` table, the phase list with gate names, `## Completion`, `## References`. Three sections are retained **beyond** that list, each for a stated reason:

| Retained section | Why it is not extractable |
|---|---|
| `## Required Artifacts` | `_preamble.md`'s **Artifact Integrity** rule operates on the command's *declared* Required Artifacts. Moving the declaration into a conditionally-loaded file breaks the preamble contract for any run that does not load it — and under the inline mechanism "does not load it" is the ordinary case, not a hypothetical. |
| The production-boundary block (push, `gh pr create`, draft-vs-ready, `gh auth` rescue) | Business Rule 4. |
| The audit-note attach contract (Step 6 minus digest composition) | Business Rule 6, and `eval-git-notes-audit.py` asserts it against this file. |

`## Integration with Writ` is **compressed, not dropped**: `commands/new-command.md`'s generated-command structure table mandates it (added by `2026-08-11-component-contract` Story 1), while ADR-021's permitted list omits it. That tension is recorded in § Technical Concerns; this spec resolves it locally by folding `## When to Use /ship vs Other Commands` (546 bytes) and `## Integration with Writ` (431 bytes) into one routing table of at most 600 bytes. Both tables answer the same question and share three rows today.

`## Error Handling` (2,076 bytes) compresses to a rescue table of at most 900 bytes covering the same five states — on the default branch, no remote, no changes, PR tool unavailable, uncommitted changes, and the combined default-branch-plus-uncommitted case. The recommendation ("option 1, commit now") and the reasoning behind it survive; the illustrative output blocks do not.

`## Pipeline`'s ASCII diagram (1,445 bytes) is replaced by the phase list. The diagram encodes phase order, the two conditional paths (`--test`), and three failure exits — all of which the phase table states in less space.

### The phase list with gate names

The shape ADR-021 asks for. Every phase names its gate class and, where one applies, its skill. This is the contract's index and the reader's map:

| # | Phase | Gate | Detail |
|---|---|---|---|
| 1 | Detect conventions | none (autonomous — `_preamble.md` "everything else") | `repo-convention-detection` |
| 2 | Merge / rebase default branch | **pause on conflict** — never auto-resolve | retained inline |
| 3 | Run tests (`--test` only) | **branch on failure** — fix / draft / abort | retained inline |
| 4 | Commit intelligence | **`AskQuestion` approval before history is restructured** | `commit-organization` + `conventional-commits` |
| 5 | PR creation | **production boundary — human gate** (`_preamble.md` gate-class table) | `pr-body-composition` |
| 6 | Audit note (post-land) | none — non-blocking provenance write | `audit-digest-composition` (composition only) |

The table **names** skills; it carries no `Read skills/` string. Each phase's inline `Read` sits at that phase's own retained anchor beneath the table (Business Rule 3): `repo-convention-detection` at Phase 1, `commit-organization` beside the existing `conventional-commits` read at Step 4, `pr-body-composition` at the body-assembly step of Phase 5 — *before* the draft-vs-ready and `gh pr create` block, which is retained and gate-crossing — and `audit-digest-composition` at Step 6.2, *after* the `writ.auditNotes` opt-out check and the landed-SHA resolution, so a run that opts out never issues it. Placement is what makes the load conditional; the phrasing convention is the established one already at `ship.md:224` — state the read, then the seam.

If the dependency spec `2026-08-12-disclosure-implement-story` landed a different table shape for the same purpose, **its shape wins** (Business Rule in the contract: follow the established pattern). Story 1 reconciles this before Story 4 authors anything. **One exception:** if the dependency landed `required_skills:` declarations, this spec does **not** follow that — the 2026-08-12 maintainer ruling overrides the follow-the-dependency clause on the loading mechanism specifically, and Story 1 records the divergence rather than resolving it in the dependency's favour.

### Skill roster

Four new skills. Names are capability nouns matching the existing corpus (`code-explanation`, `error-rescue-mapping`, `safe-refactor-loop`, `tdd-cycle`) rather than command-prefixed, so a sibling spec can declare them too.

| Skill | Source | Owns | Does **not** own |
|---|---|---|---|
| `repo-convention-detection` | Step 1 (2,821 B) | `.writ/config.md` precedence; the four detection chains (default branch, test runner, merge strategy, PR tool); the persist-once offer; the opinionated merge-over-rebase and `gh` defaults with their reasoning | anything that acts on the detected values |
| `commit-organization` | Step 4 (4,182 B) minus the approval gate | the layer/grouping/prefix table; the four "when NOT to split" rules; the buildable-intermediate-state rule and its `--test` variant; the staging order (infra → models → logic → tests → version); the `Ref:` footer's source; the commit-plan presentation format | commit *message* grammar (Business Rule 5); the approval `AskQuestion` (Business Rule 4) |
| `pr-body-composition` | Step 5 (5,818 B) minus the production-boundary block | the seven-section body template and its population table; the "no data → explicit placeholder, except Spec Health which is omitted" rule; the inline spec-health checks 1–3 with auto-fix; the five auto-labels and the never-fail label fallback | draft-vs-ready, push, `gh pr create` (Business Rule 4); the Spec Reference heuristic itself (Business Rule 7) |
| `audit-digest-composition` | Step 6.2–6.3 (~1,200 B of 3,610 B) | resolving the spec + squashed source range for the digest header; aggregating the spec-level digest from per-story `## What Was Built` records (worst verdict, highest drift severity, DEV-ID union, aggregate coverage, file counts, review iterations); the audit-only content prohibition | the opt-out gate, landed-SHA resolution, the attach command, the non-blocking rule, the minimal-digest fallback (Business Rule 6) |

Each skill carries its own `--dry-run` preview text for the phase it owns, which is how `## Dry Run Mode`'s 1,138 bytes of duplicated previews are eliminated without losing a clause (Business Rule 2, `deduped`).

### Projected budget

Projections, not measurements — Story 5 re-measures and the measured numbers govern. Baselines are the **corrected** ones from `measure-invocation.py` after `e8f2a09`.

| Measure | Before (measured 2026-08-12) | Projected after | Test |
|---|---|---|---|
| `commands/ship.md` bytes | 28,371 | ~11,650 | **≤ 24,960** (binding); ≤ 13,000 (design target) |
| `commands/ship.md` lines | 627 | ~265 | ≤ 400 (non-binding tripwire) |
| `eager_bytes` | 0 | **0** | must stay 0 — no `required_skills:` |
| `floor_bytes` | 53,331 | ~36,610 | must fall — projected **−31.4%** |
| `conditional_bytes` | 9,985 | ~20,900 | — |
| `ceiling_bytes` (worst path) | **63,316** | ~57,510 | **≤ 63,316** — projected **−9.2%**, clears with ~5,800 B to spare |
| `ceiling_bytes` excluding `conventional-commits` | 53,331 | ~47,525 | reported for symmetry; also below 53,331 |

The `+~11,650` command projection replaces the pre-ruling `~11,300`: the difference is four per-phase `Read` anchors instead of a five-entry `required_skills:` block. It costs ~350 bytes in the command and saves ~20,900 in the floor.

**Every path improves, and the report says so with numbers.** Each row is `floor + Σ(skills that path reads)`, with per-skill projections `repo-convention-detection` ~2,400, `commit-organization` ~3,300, `pr-body-composition` ~4,000, `audit-digest-composition` ~1,200, `conventional-commits` 9,985.

| Invocation path | Skills the run reads | Projected | vs. pre-spec | Δ |
|---|---|---|---|---|
| Merge conflict pause at Step 2 (never reaches Step 4) | convention | **39,010** | 53,331 | **−26.9%** |
| `--test` failure abort at Step 3 | convention | **39,010** | 53,331 | **−26.9%** |
| `--no-split`, reaches Step 4 | + `conventional-commits` | **48,995** | 63,316 | **−22.6%** |
| Full run to PR-open, `writ.auditNotes=false` | + commit-org, pr-body | **56,295** | 63,316 | **−11.1%** |
| Full run incl. audit note (worst path) | + audit-digest | **57,510** | 63,316 | **−9.2%** |

Note the pre-spec column is not constant: a run that pauses at Step 2 never reached `ship.md:224` and paid 53,331; a run reaching Step 4 paid 63,316. Comparing every post-spec path against one before-number would flatter the early rows and penalise the late ones.

This is the result the sibling `/release` spec does **not** get, and the difference is instructive rather than lucky: `/ship`'s early phases can terminate (conflict pause, test failure, `--no-split`, audit opt-out), while `/release`'s pipeline reaches every phase on a normal run. Disclosure pays where a command has real early exits.

The extracted skills must total **no more than the bytes removed from `ship.md`** — roughly 17,000 against a ~11,000-byte skill budget. That gap is the prose compression ADR-021 calls "a tactic within extraction": the ASCII diagram, the duplicated dry-run previews, and the illustrative output blocks do not survive relocation.

## Out of Scope

- **`commands/release.md`**, even where it shares `resolve-spec-reference.py` and the `refs/notes/writ` channel with `/ship`. A sibling Phase 10 spec owns it. If this spec's skills are useful to it, that spec declares them.
- **Any other command file.** Business Rule 9.
- **`scripts/`, in any direction.** No new eval check, no edit to `resolve-spec-reference.py`, no change to `check_length`'s 2000-line command limit, no raise of `MAX_SKILLS`. `2026-08-11-governor-instrumentation` owns enforcement.
- **`commands/_preamble.md`.** Business Rule 8.
- **Adding a gate `/ship` does not have today.** ADR-022 classifies PR-open as a human gate and `/ship` satisfies it by being human-invoked (`_preamble.md`: no `--recommend` command opens PRs). Adding an explicit pre-`gh pr create` confirmation would be a redesign, and Business Rule 2 forbids it. The production-boundary rule here is about *where clauses live*, not about adding ceremony.
- **Changing `/ship`'s behavior in any way a user could observe** — the default no-test path, the momentum-over-ceremony silence on clean merges, the label-failure tolerance, the post-merge orphaned-commit warning. All survive.
- **Promoting any skill past `candidate`.** ADR-014 state is earned from evidence; this spec creates one consumer each. `conventional-commits` gains no new declaration — `ship.md:224`'s inline read is preserved unchanged — so nothing about its lifecycle state moves here either.
- **Editing `scripts/measure-invocation.py`.** Fixed in `e8f2a09`; its output is this spec's instrument. A further defect is recorded and escalated (Business Rule 9), never patched to make a number land.
- **Amending ADR-021 clause 3**, which still reads "the harness pre-loads only what that invocation needs". The 2026-08-12 ruling contradicts it; the dependency spec owns the ADR's `## Amendments` section. This spec follows the ruling and contributes its measured figures as evidence.
- **Reconciling the phase-wide skill cap.** § Technical Concerns records that this spec takes the corpus from 6 to 10 against `MAX_SKILLS = 12`.
- **Editing ADR-021, ADR-022, or the roadmap.** The Phase 7 non-extraction note inside `ship.md` is superseded in place (Story 4); no decision record is amended.

## Implementation Approach

1. **Story 1 — the ledger and the census.** Enumerate every normative clause with its byte offset; classify each as retained / extractable / gate-crossing / provenance; read the dependency spec's landed skills and record its section shape, frontmatter conventions, and naming pattern. No product file changes. Nothing else can start, because Business Rule 2's verification method does not exist until this lands and Stories 2–4 all author against the dependency's pattern.
2. **Stories 2 and 3 — the four skills, in parallel.** Disjoint file sets (`repo-convention-detection` + `commit-organization`; `pr-body-composition` + `audit-digest-composition`). Both touch `.writ/manifest.yaml` and the regenerated root `SKILL.md`, which is the one merge surface between them — Story 3 rebases on Story 2 rather than running in a separate worktree if that conflict is inconvenient.
3. **Story 4 — the thin command.** Depends on both. An inline `Read skills/<name>/SKILL.md` naming a file that does not exist lands in `unresolved_skills` and makes every budget figure a lower bound (Business Rule 3's resolution check would fail), and the retained-versus-relocated boundary is only verifiable once the skills' contents are fixed.
4. **Story 5 — measure and prove.** Depends on Story 4. Re-measures floor and ceiling, writes the ceiling justification, closes the clause ledger, and runs the eval suite. This is deliberately a separate story: folding it into Story 4 makes the author of the cut the sole judge of whether the cut was faithful.

## Success Criteria

1. `python3 scripts/measure-invocation.py --root . --command ship` reports `command_bytes` **≤ 24,960**, `floor_bytes` strictly below 53,331, `eager_bytes: 0`, `eager_skills: []`, and no "loads both ways" warning.
2. `ceiling_bytes` is **≤ 63,316** (the corrected monolith test), or above it with the three-part justification in Business Rule 1 carrying explicit maintainer acceptance. The projection says ~57,510, so the expected outcome is a clean pass with no justification written. The recomputed ceiling excluding `conventional-commits` is reported alongside for symmetry (pre 53,331 vs post ~47,525).
2a. The path table is measured, not projected: merge-conflict pause, `--test` abort, `--no-split`, `writ.auditNotes=false`, and a full run — each compared against the correct pre-spec figure for that path (53,331 for paths that never reached `ship.md:224`, 63,316 for paths that did).
3. `conditional_skills` for `ship` contains `repo-convention-detection`, `commit-organization`, `pr-body-composition`, `audit-digest-composition`, and `conventional-commits`; `unresolved_skills` is empty; each is reached by exactly one inline `Read` at its phase anchor, each is named in the phase list, and no `Read skills/` string appears in the frontmatter, `## Overview`, or the phase-list table.
4. `sub-specs/clause-ledger.md` has a disposition on every row, no row marked dropped, and every `deduped` row names the duplicate it merges with.
5. Every literal in Business Rule 2's table is present at its required location — reported as grep output in the story evidence, not asserted.
6. `bash scripts/eval.sh` shows no new findings against its pre-spec baseline, and all seven `git-notes-audit` `scenario_ship` checks pass.
7. `bash scripts/lint-skill.sh skills/*/SKILL.md` exits 0; `bash scripts/gen-skill.sh --check` reports no delta; `.writ/manifest.yaml` carries four new alphabetically placed `skills:` entries, each `status: candidate`; all four names conform to `.writ/docs/skills.md` → *Extraction Patterns*; and `.writ/leanness-baseline.json` carries a bound `skills`-surface justification written by hand, with `--update-baseline` never run.
8. `git diff --name-only` lists nothing under `scripts/`, `agents/`, or `adapters/`, and exactly one file under `commands/`.
9. `commands/ship.md`'s whole frontmatter block diffs empty against its pre-spec text — `problem:`, `outcome:`, `exit_criteria:` unchanged and **no key added**, in particular no `required_skills:` anywhere in the file — and `## Completion` is unchanged.
9a. `grep -n 'Read skills/' skills/*/SKILL.md` returns nothing (`scripts/lint-skill.sh:52`): every one of `/ship`'s five inline reads lives in `commands/ship.md`, and `ship.md:224` is preserved in place rather than converted or relocated.
10. **Behavioral neutrality, stated as a reading test:** a reviewer given only the thinned `commands/ship.md` plus the five declared skills can answer every question today's file answers about what `/ship` does. Any question that requires reading git history to answer is a dropped clause.

## Technical Concerns (surfaced at contract time)

- **The dependency spec is authored but not implemented.** `2026-08-12-disclosure-implement-story` exists as of 2026-08-12 and `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok` with this spec ordered after it. What does **not** exist yet are its eight skills, its `.writ/docs/skills.md` → *Extraction Patterns* section, and its ADR-021 amendments — and those are what the contract binds this spec to follow. Story 1 Task 1.1 gates on the **landed files**, not on the spec folder's existence. A green `spec-deps.py` is not evidence the pattern is available.
- **This spec's Story-1 finding propagated to the whole phase, and the other five specs have not all absorbed it.** Commands carry inline `Read skills/…` lines that the pre-`e8f2a09` `measure-invocation.py` could not see — `ship.md:224` (`conventional-commits`, 9,985 B) is the largest, and `implement-story.md:525` (`tdd-cycle`, 6,101 B) is the dependency spec's own. The tool is fixed and now counts both, so the dependency's ceiling bound of 77,669 is understated by 6,101 and its projected ~81,130 "overage" is substantially an artifact of the broken instrument. This spec edits nothing in the dependency; it records the observation for whoever reconciles the six specs and states its own corrected baseline explicitly. **Until that reconciliation happens, sibling specs will be judged against bars derived from a tool that no longer behaves the way they assume.**
- **ADR-021 clause 3 and the six specs now disagree in writing.** The ADR still says `required_skills:` "pre-loads only what that invocation needs"; the 2026-08-12 ruling says it pre-loads everything, always. Neither this spec nor the dependency's implementation can be read correctly by someone who finds clause 3 first. Amending it belongs to the dependency spec (Out of Scope here); flagging it as the phase's highest-priority documentation debt belongs here.
- **A conditional load can fail, and `/ship` is where that matters most.** The mechanism that produces the saving is a `Read` the agent may not issue. Business Rules 4 and 6 keep every gate-crossing decision and the whole attach path out from behind one, but the residual risk is a *partially* loaded phase — a run that reads `pr-body-composition` at the start of Phase 5, then, after a long body-assembly interaction, no longer has it when labels are derived. Nothing detects that and no lint can. It is the reason each anchor must sit at the step that *uses* the procedure rather than the earliest step that mentions it.
- **`eval-git-notes-audit.py` pins seven literal strings to `commands/ship.md`.** `scenario_ship()` asserts `refs/notes/writ`, `git notes --ref=writ add -f -F`, a non-blocking phrase, `writ.auditNotes`, `landed` plus one of `surviving`/`squash`, one of `minimal digest`/`Fallback`, and `refs/notes/commits` with a negation. This is a benefit, not an obstacle: it is the only mechanical guard in this spec against the hardest constraint being violated. It also means an over-eager thinning pass fails `eval.sh` rather than shipping quietly.
- **The measured ceiling no longer rises, and the risk has inverted.** The original concern was a reviewer reading `53,331 → ~57,200` as evidence that ADR-021 caveat 2 had bitten. The corrected instrument reports the true comparison — `63,316 → ~57,510`, a 9.2% *fall* — so that failure mode is closed. The new one is complacency: this is the spec in the phase where the numbers come out well on every path, which makes it the one where the clause ledger, the seven provenance pins, and Business Rule 4's per-clause load test are most likely to be treated as formalities. The byte result says nothing about whether a gate moved.
- **`MAX_SKILLS = 12` is already exceeded by the phase, not by this spec.** `scripts/eval-leanness.py:71`, corpus of 6 today. Counted from the five sibling specs' authored rosters on 2026-08-12: `implement-story` +8, `create-spec` +4, `implement-phase` +3, `release` +4, this spec +4 — **at least 29 skills**, before `verify-spec` names its own. ADR-021 predicted the overrun and required the cap be raised "deliberately with justification rather than silently." No spec in the phase can raise it: this one is barred by Business Rule 9, and the dependency's BR7 bars edits to `eval-leanness.py` outright. That leaves the raise unowned. It needs to be assigned — plausibly to `2026-08-12-governor-enforcement` — before the second disclosure spec lands, not after `eval.sh` starts reporting it.
- **The `skills` surface will ratchet, and `--update-baseline` is the wrong fix.** `.writ/leanness-baseline.json` records `skills` at 932 lines / 41,620 chars with no justification. Six specs extracting into that surface will trip ADR-019's growth warning repeatedly; four such warnings for other surfaces were live and ignored for months, which is the exact failure ADR-021 §2 cites. Business Rule 11 requires a bound justification and forbids re-baselining.
- **ADR-021's permitted-section list is under-specified against two other governing documents.** It omits `## Required Artifacts`, which `_preamble.md`'s Artifact Integrity rule depends on, and `## Integration with Writ`, which `commands/new-command.md`'s generated-command structure table mandates. This spec resolves both locally (retain the first, compress the second) and records the tension rather than treating either document as wrong. If the dependency spec resolved it differently, the dependency wins and this spec's § Detailed Requirements is amended, not silently diverged from.
- **Splitting Step 6 between a command and a skill is the subtlest part of this spec.** The seam is *compose* versus *attach*. Put a byte too much in the skill and a run where the skill fails to load attaches a wrong-shaped note; put a byte too little and the command re-inflates. The fallback path is what makes the seam safe, and it is the clause most likely to be trimmed by someone optimizing for the byte target. Business Rule 6 names it explicitly for that reason.
- **`/ship` and `/release` share two mechanisms and are being thinned by two different specs concurrently.** `resolve-spec-reference.py` and the `refs/notes/writ` channel. Business Rules 7 and 9 keep this spec out of the sibling's way, but if both specs run in the same window, `.writ/manifest.yaml` and the regenerated root `SKILL.md` are a real conflict surface. Sequence them, or expect a manifest merge.
