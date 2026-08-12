# Spec: Progressive Disclosure — `/release`

> **Status:** Not Started
> **Owner:** @AdamSellke
> **Created:** 2026-08-12
> **Dependencies:** [2026-08-12-disclosure-implement-story]
> **Origin:** Phase 10 progressive disclosure, governed by [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md), which applies thin-contract extraction to the top 6 command files "one spec per file, `implement-story.md` first." This is the `release.md` spec. It is also the one file in the six where the extracted procedure crosses the **production boundary** [ADR-022](../../decision-records/adr-022-autonomy-gate-classes.md) classifies as a permanent human gate, and the one file whose prose is directly pinned by `scripts/eval.sh`.

## Contract (Locked)

**Deliverable:** `commands/release.md` — 28,589 bytes / 640 lines — reduced to a thin contract with its per-phase procedural detail extracted to `skills/<name>/SKILL.md`, loaded on demand via `required_skills:`.

**Must include:** The thin contract retains only what [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) permits — frontmatter contract (ADR-020), `## Overview`, `## Invocation` table, the phase list with gate names, `## Completion`, `## References`. Skills authored through `/new-skill` (born `status: candidate`, lint-clean). **Follow the extraction pattern and skill-naming convention established by the dependency spec `2026-08-12-disclosure-implement-story`.**

**Hardest constraint:** `/release` crosses the **production boundary** — changelog, version bump, git tag, GitHub release. [ADR-022](../../decision-records/adr-022-autonomy-gate-classes.md) classifies that as a **human gate**, and the Prime Directive forbids autonomous release. Relocating procedure into on-demand skills must not move a production-boundary decision into a skill that loads without the gate having fired. The release gate stays in the command contract, never in a conditionally-loaded skill.

### Approved scope change — the loading mechanism (maintainer decision, 2026-08-12)

**The contract block above is reproduced unedited.** It says the extracted procedure is "loaded on demand via `required_skills:`". That clause is superseded by maintainer ruling on 2026-08-12: the mechanism is an **inline `Read skills/<name>/SKILL.md` issued at the step that needs it**, and `required_skills:` is **not used by this spec**. Everything else in the contract stands unchanged — the deliverable, ADR-021's permitted sections, `/new-skill` authoring, the pilot spec's naming convention, and the production boundary. **The extraction map is unchanged**; only the mechanism that reaches the extracted skills changes.

**Why.** `required_skills:` is an *eager* pre-load, verified twice against this tree: `system-instructions.md` says the harness loads the named skills "before any phase work begins", and `adapters/claude-code.md:396` says the harness issues the `Read` calls "before the consumer's first phase begins". A declared skill is paid on **every** invocation. Declaring this spec's five skills would have moved ~17,029 bytes out of `commands/release.md` and straight into the **floor** — a post-spec floor of ~58,120 against a pre-spec 53,549, a **rise of ~4,571 bytes on every run**, including the ones that abort at the gate. The mechanism the contract named cannot deliver progressive disclosure at all. The inline form can: the agent issues the call only if execution reaches that step. Six commands already use it (`create-spec.md`, `implement-story.md`, `refactor.md`, `research.md`, `ship.md`, and `release.md:88` itself), with the established phrasing *"the skill owns how; this command owns when and which"*.

**The instrument was wrong too, and has been fixed** (`e8f2a09`). `scripts/measure-invocation.py` treated `required_skills:` as conditional and ignored inline reads entirely. It now reports `floor = base + command + eagerly-declared skills` and `ceiling = floor + inline-read skills`. Re-measured on the same tree, `/release` is **floor 53,549 / conditional 9,985 / ceiling 63,534** — the 9,985 is `skills/conventional-commits/SKILL.md`, read inline at `commands/release.md:88` since long before this spec and invisible to the old tool. **Every ceiling figure in this package is measured against 63,534, not against the understated 53,549.**

**What this changes downstream, in one list.** Business Rule 1 (the bar moves to 63,534 and reporting becomes path-dependent), Business Rule 3 (the "declare all, no curated subset" rule is **reversed** — precise placement replaces exhaustive declaration), Business Rule 4 (strengthened, not weakened: a Read that never fires is now a real failure mode), the *Why `npm-package-publication` is declared anyway* section (its exemption is **reinstated**), the projected arithmetic, and the reachability half of every success criterion. Nothing in the extraction map, the eval pin inventory, the retained ranges, or the drift-ledger method moves.

### Binding budget (maintainer decision, 2026-08-12, revised for the corrected instrument)

**A command file may not cost more to load than the shared contract it runs inside.** The budget is the irreducible shared base — `system-instructions.md` (20,153 B) + `commands/_preamble.md` (4,807 B) = **24,960 bytes**. `commands/release.md` must land **≤ 24,960 bytes**, down from 28,589 — a 13% cut, the second-smallest gap of the six target files, so the failure mode here is a contract that is thin in name only.

Measured with `python3 scripts/measure-invocation.py --root . --command release`. **Both** `floor_bytes` and `ceiling_bytes` are reported before and after, plus the realistic partial paths below. The 400-line cap is a **secondary, non-binding tripwire**; `check_length` still enforces 2000 today, and the ADR-021 amendment that makes bytes the binding instrument belongs to the dependency spec.

Two numbers bind, matching the standard the pilot spec `2026-08-12-disclosure-implement-story` set for all six:

- **Floor:** `command_bytes ≤ 24,960` (equivalently `floor_bytes ≤ 49,920`). Because this spec declares no `required_skills:`, `eager_bytes` is 0 and `floor_bytes = 24,960 + command_bytes` exactly.
- **Ceiling:** `ceiling_bytes ≤ 63,534` — **the extracted system may not weigh more than the monolith it replaced.** 63,534 is the *corrected* pre-spec ceiling from the fixed instrument, not the 53,549 the broken one reported.

A third obligation, not a threshold: the report is **path-dependent**. Floor, worst-path ceiling, and the named partial paths in § *What disclosure can and cannot buy here* all appear, because on a sequential pipeline the worst path is the common one and a single ceiling number hides that.

## Why This Exists

`/release` is the fourth-largest command file and the most structurally constrained one in the phase. Everything below was measured against this working tree on 2026-08-12, not inherited.

| Measure | Value | How verified |
|---|---|---|
| `commands/release.md` | 28,589 bytes / 640 lines | `wc -c -l commands/release.md` |
| Shared base every invocation pays | 24,960 bytes | `measure-invocation.py --format table` |
| `/release` floor (base + command) | **53,549 bytes** | same — `eager_bytes` is 0; `release.md` declares no `required_skills:` |
| `/release` ceiling | **63,534 bytes** | same — `conditional_bytes` is 9,985: `release.md:88` inline-reads `skills/conventional-commits/SKILL.md` |
| Base share of floor | 46.6% | same |
| `commands/_preamble.md` | 93 lines against a 95-line cap | `scripts/eval.sh` `check_length` |
| Existing skills | 6 (`MAX_SKILLS = 12` in `eval-leanness.py`) | `ls skills/`, `grep MAX_SKILLS scripts/eval-leanness.py` |

### The constraint nobody measured: `release.md` is prose-pinned by the eval harness

This is the finding that shapes the whole spec, and it is the reason `/release` cannot be extracted the way a topic-first reading would suggest.

`scripts/eval.sh` asserts **fifteen literal strings** inside `commands/release.md` and **forbids one**. Two separate checks do it:

- `check_post_merge_archival()` (`scripts/eval.sh:2012–2051`) — eight assertions pinning Step 1.3c's archival hook and the conditional-test-suite table, plus `forbid_literal … is_complete_family`.
- `check_git_notes_audit()` (`scripts/eval.sh:2626`) plus `scripts/eval-git-notes-audit.py` `scenario_release()` — five assertions pinning Step 4.4's audit rollup.
- `check_artifact_integrity()` (`scripts/eval.sh:2727`) — `## Required Artifacts` must exist in `release.md`.
- `check_preamble()` (`scripts/eval.sh:525`) — the References section must link `commands/_preamble.md`.

`require_literal` matches against **the command file itself**, not against anything it loads. A pinned string relocated into a skill is a `scripts/eval.sh` finding, and this spec is forbidden from editing `scripts/eval.sh` to follow it. The pins are therefore a **hard boundary on the extraction surface**, discovered at spec time rather than at implementation time. The complete inventory with line numbers is in `sub-specs/technical-spec.md` → *Eval Pin Inventory*.

The pins are not an obstacle to route around. They encode exactly the two things the locked contract already protects — the archival hook's placement and the audit channel's non-blocking guarantees — so honoring them and honoring the contract are the same act.

### What disclosure can and cannot buy here

`/release` is a sequential pipeline. A full, non-`--dry-run`, non-`--no-tag` run needs changelog generation *and* version-file writes *and* tag/publish detail. That is the case [ADR-021 caveat 2](../../decision-records/adr-021-progressive-disclosure-token-budget.md) names as the one that could invalidate the approach — *"a command that ends up needing every extracted skill costs more than the monolith did."* Under the inline mechanism the saving is real but **path-dependent**, and on this command the worst path is the common one. Both halves of that sentence are stated up front rather than discovered in review.

**Floor.** Projected ~16,591 B command / ~41,551 B floor: a **−22.4% floor reduction** (53,549 → 41,551) and a 42% file reduction. Every invocation pays this and nothing more until it reaches a step that reads a skill. Under the withdrawn `required_skills:` mechanism this number would have gone the *other way* — to ~58,120, a 4,571-byte rise — which is the whole reason the mechanism changed.

**Paths.** Projections against the corrected pre-spec figures (floor 53,549 / ceiling 63,534), assuming the Compression Ledger's estimated −2,400 B on skill prose (C1–C5, C7; C6 not taken). Story 5 replaces every figure with a measurement.

| Invocation path | Skills the run reads | Projected load | vs. pre-spec | Δ |
|---|---|---|---|---|
| Aborts in Phase 1 before Step 1.2 — dirty tree, no releasable changes | none | **41,551** | 53,549 | **−22.4%** |
| Release gate blocks at Step 1.3 | `semver-version-bump`, `changelog-generation`, `conventional-commits` | **57,941** | 63,534 | **−8.8%** |
| `--no-tag` / `bump_only` (skips Phases 4–5) | + `readme-freshness-audit` | **60,199** | 63,534 | **−5.2%** |
| Full release, README present | + `git-tag-publication` | **63,411** | 63,534 | **−0.2%** |
| Tool-reported worst path | + `npm-package-publication` | **66,165** | 63,534 | **+4.2%** |

Three honest readings of that table, none of them omitted from Story 5's report:

1. **The gate-blocked and aborted paths are where disclosure pays.** Those are not exotic: an abort before Step 1.2 costs 22.4% less than today, and a blocked gate 8.8% less. This is the class of run the floor was always about.
2. **On a full release the saving is ~123 bytes — effectively nil.** Say so plainly. A sequential pipeline that reaches every phase reads every skill, and the scaffolding overhead of five `SKILL.md` files very nearly eats the compression. Reporting `−0.2%` as a win would be the same defect the old instrument committed.
3. **The only figure above the bar is the tool's worst path, and it exceeds it by ~2,631 B for one reason: `npm-package-publication` (~2,754 B), a manual, out-of-band procedure no `/release` run executes.** Remove that one skill from the path — which every real release path does — and the worst *release* path lands under the bar. Business Rule 1 still requires the overage to be reported with that arithmetic attached; it does not require pretending the tool's regex-derived worst case is a run anyone performs.

## 📋 Business Rules

1. **Report floor, worst-path ceiling, and the realistic partial paths; the ceiling may not regress.** Every figure comes from `python3 scripts/measure-invocation.py --root . --command release`, recorded before and after in Story 5's evidence:
   - **Floor:** `command_bytes ≤ 24,960` (equivalently `floor_bytes ≤ 49,920`). `eager_bytes` must be **0** — this spec declares no `required_skills:`.
   - **Ceiling:** `ceiling_bytes ≤ 63,534`. **The extracted system may not weigh more than the monolith it replaced.** The bar is the *corrected* pre-spec ceiling; using the old 53,549 would compare an after-figure that counts `conventional-commits` against a before-figure that did not, manufacturing a 9,985-byte regression no change caused.
   - **Paths:** the table in § *What disclosure can and cannot buy here*, re-measured, with the per-path skill list. A single ceiling number on a sequential pipeline hides which runs actually got cheaper.

   A ceiling above 63,534 does **not** silently pass. It requires a written justification naming (a) the measured overage in bytes, (b) the compression already attempted with its **measured** yield — the Compression Ledger in `sub-specs/technical-spec.md` is the starting list, not the finishing one — and (c) an explicit maintainer decision to accept it, recorded in the story file. *"Only 4% worse"* is not a justification; a justification states what was tried and why the remainder is irreducible without redesign. **A path table is not a substitute for the justification** — naming a cheaper path does not retire an overage on the worst one; it explains its shape.

   Symmetrically, **a small saving must be reported as small.** The projected full-release path saves ~123 bytes. If the measurement confirms that, Story 5 says so in those words. Reporting only the floor, or only the best path, is a failed story: [ADR-021 caveat 2](../../decision-records/adr-021-progressive-disclosure-token-budget.md) exists because one number cannot tell you whether disclosure worked. This is the same standard the pilot spec `2026-08-12-disclosure-implement-story` set for all six disclosure specs, adopted with the mechanism correction applied so six specs are judged on one bar.

2. **Relocate and contract; do not redesign — proven by a drift ledger, not by assertion.** Every step of the changelog/version/tag flow, the release gate, and `--skip-gate` behavior survives **byte-faithful in meaning**. The verification method is concrete and required, not optional:

   `sub-specs/technical-spec.md` carries an **Extraction Map** — fifteen source line ranges in the pre-spec `commands/release.md`, each with a byte count and exactly one destination. Each story that extracts a range appends a row to the drift ledger in its evidence: `source range → destination heading → bytes out → bytes in → semantic delta`. `semantic delta` is either `none (verbatim)` or `contracted: <what was compressed and why the meaning is unchanged>`. **Any other value is a redesign and is out of scope.** The ledger is checked with `git show <base-sha>:commands/release.md | sed -n '<range>p'` against the skill body — this is a mechanical comparison a reviewer can run, not a judgment call. Prose compression is permitted as a *tactic within* relocation (ADR-021's own framing); adding a step, removing a step, reordering the flow, or changing a default is not.

3. **Every extracted skill is reached by exactly one inline `Read` at the narrowest step that needs it — placement is the mechanism, and hoisting is forbidden.** This rule **reverses** the "declare all, don't curate" rule this spec inherited from the pilot's Business Rule 8. That rule was right under eager loading, where the only honest thing to do with a static array was to fill it completely. It is backwards under conditional loading, where *where the call sits* is the entire saving.

   Each skill this spec creates is reached by (a) an inline `Read skills/<name>/SKILL.md` instruction placed at the retained anchor for the phase or step that consumes it — never in the frontmatter, never in `## Overview`, never hoisted into a preamble or a "load these first" block — **and** (b) a naming in the `## Command Process` phase list's Detail column, so a reader of the thin contract can see *when* the detail is needed without loading it. The phase-list table itself must contain **no** `Read skills/` string: a table read top-to-bottom as a map is exactly the hoist this rule forbids, and it would invite an agent to issue all five calls before Phase 1. `measure-invocation.py` must report **zero** `unresolved_skills`, and every name in `conditional_skills` must appear in the phase list.

   **`required_skills:` is not used.** No skill this spec creates is declared in frontmatter. A declaration would move that skill's bytes into the floor, which is the opposite of the deliverable. `measure-invocation.py` must report `eager_bytes: 0` and `eager_skills: []`; it emits an explicit warning if a skill is both declared and inline-read, and that warning is a story failure.

   **`npm-package-publication` is the deliberate exemption, and it is correct.** Its inline `Read` lives on the single `## References` line that marks the `@sellke/writ` runtime-helper procedure as manual and out-of-band — the narrowest anchor there is, because that procedure is not a phase of `/release` at all. No `/release` run reaches it, so no `/release` run pays its ~2,754 bytes. Under the eager mechanism an earlier draft withdrew this exemption on the grounds that curating a static array games the ceiling; under conditional loading there is no array to curate and the saving is real, so the exemption is **reinstated as correct**. It is not hidden: the skill is still reachable, `measure-invocation.py` still counts it in the tool's worst-path ceiling, and Story 5 reports that number alongside the release-path number that excludes it.

   **`conventional-commits` stays exactly as it is.** `commands/release.md:88` reaches it by an inline read from the command; that line is preserved as an inline read, relocated with its step, and `conventional-commits` is **not** converted into a declaration and is **not** re-extracted. The corrected instrument now counts it on both sides of the comparison, which makes the exclusion automatic and symmetric. Story 5 additionally reports the `conventional-commits`-excluded pair (53,549 → post-spec) so no reader has to take the symmetry on trust.

4. **No gate-crossing decision may live in a conditionally-loaded skill — and this rule is now stronger, not weaker.** [ADR-022](../../decision-records/adr-022-autonomy-gate-classes.md) classifies the production boundary — merge, PR open, release, tag, publish — as a permanent human gate, and the Prime Directive forbids autonomous release. A skill loads *because a phase reached it*; that is the wrong place for the decision about whether the phase should have been reached.

   Under the withdrawn `required_skills:` mechanism one could at least argue that the harness always pre-loaded the skill, so a relocated gate would still be present. **The inline mechanism removes that argument.** A `Read` is an instruction the agent may not reach, may skip, or may have fail — the load is genuinely conditional, which is exactly why the mechanism was adopted, and exactly why nothing that decides may sit behind one. The authoring test: *if this `Read` never fires, does `/release` still refuse to release when it should?* If the answer depends on the skill, the clause is in the wrong file. The following stay in `commands/release.md` and may not be relocated under any byte pressure:
   - The **release gate** in full — Step 1.3a spec-metadata validation, 1.3b build verification, 1.3c conditional test suite and its three-row decision table, and the blocking semantics of each.
   - **`--skip-gate`** — its meaning, everything it bypasses, and the fact that bypassing is a user's explicit choice, not a default.
   - Both **`AskQuestion` gates** — Step 1.5's version-bump proposal and Step 2.3's "Proceed with this release?" confirmation, including the `abort` and `bump_only` options.
   - The **dirty-working-tree** and **no-releasable-changes** prompts in `## Error Handling`. Both decide whether a release proceeds at all.
   - The **audit rollup's non-blocking guarantee** and its `writ.auditNotes` opt-out. A release must never fail because an audit note did not attach, and that promise cannot be conditional on a skill having loaded.

   A skill may describe *how to execute* a step the gate already authorized. It may never contain the authorization.

5. **The post-merge archival hook does not move.** Step 1.3c's hook — `LAST_MERGED_SHA` vs `HEAD_SHA`, the resolver call, the `archive-one` call, the status branch, and the immediate `chore(archive): auto-archive <spec> via PR #<n>` commit — stays in `commands/release.md`, verbatim, inside the same `LAST_MERGED_SHA == HEAD_SHA` branch it lives in today (spec `2026-08-04-post-merge-archival-hook`). The reasoning is the hook's own design, and the mechanism change sharpens it: the hook is **silent and best-effort**, and an inline `Read` that never fires would disable it with no output and no failure. Under an eager pre-load that was a theoretical risk; under a conditional read it is the ordinary case for any run that takes a different branch. A silent feature cannot survive a load that may not happen. Its `--skip-gate` inheritance is structural (it nests inside the block `--skip-gate` skips), and relocation would break that inheritance and require a second, drifting check. `scripts/eval.sh --check=post-merge-archival` must pass unchanged, and `scripts/eval-post-merge-dogfood.py` must keep matching the hook's literal commit pattern.

6. **The eval pin inventory is a hard constraint on the extraction surface.** Fifteen literal strings must remain present in `commands/release.md` and one (`is_complete_family`) must remain absent. The inventory with line numbers is in `sub-specs/technical-spec.md`. `bash scripts/eval.sh --check=post-merge-archival --check=git-notes-audit --check=artifact-integrity --check=preamble` is the check. Editing `scripts/eval.sh`, `scripts/eval-leanness.py`, or `scripts/archive-sweep.py` to relax a pin is out of scope (Business Rule 10) — the pins move the boundary, the boundary does not move the pins.

7. **`commands/_preamble.md` is not a destination.** It sits at 93 of 95 lines. Nothing this spec extracts goes there, and its cap is not raised — `2026-08-11-autonomy-gate-classes` owns that file and that number. Procedure shared with another command becomes a **shared skill** (ADR-021 clause 4), which is what `skills/` is for.

8. **`skills/` is a shared namespace, and the naming convention is inherited, not invented here.** The pilot spec `2026-08-12-disclosure-implement-story` owns the convention (its Business Rule 3, written into `.writ/docs/skills.md` → *Extraction Patterns* by its Story 1) and this spec follows it verbatim: kebab-case noun phrase, 2–3 words, ≤ 30 characters, unique across `commands:` / `agents:` / `skills:` in `.writ/manifest.yaml`; shape `<object>-<operation>` or `<operation>-<object>`; **never named after its extraction site** — no command name, no phase number, no step number; `description:` a bare-imperative verb phrase; a shared skill carries no consumer's vocabulary.

   **Collision protocol (the pilot's rule 6, adopted):** before running `/new-skill`, grep `.writ/manifest.yaml`'s `skills:` block for the intended name **and its head noun**. If a sibling spec already claimed the noun, reach the existing skill with an inline `Read` at the step that needs it rather than authoring a near-duplicate, and add an `evidence:` entry with `type: promotion` to it per ADR-014. **First writer owns the name.** Six skills exist today and five sibling extraction specs are writing into the same directory, so a name free at spec-authoring time may not be free at implementation time — re-read, do not assume.

9. **Skills are capabilities, not workflows, and are born `candidate`. Inline reads live in commands only.** Authored through `/new-skill`, so each carries `disable-model-invocation: true` and `status: candidate`, and passes `bash scripts/lint-skill.sh skills/<name>/SKILL.md` on arrival (ADR-009, ADR-014). The lint's body grammar (`scripts/lint-skill.sh:52`) rejects `Read skills/` inside a skill as skill chaining, alongside `Read commands/`, `Task(`, and a line beginning with a slash command — extracted prose that references `/verify-spec` or `/ship` must be rewritten so those references do not open a line.

   The mechanism change makes this a boundary, not a nuisance: **the inline `Read` is the command's instrument and only the command's.** Every one of this spec's five reads sits in `commands/release.md`; not one appears in a `skills/*/SKILL.md`, and a skill that needs a sibling capability states the boundary in prose and stops (ADR-021 clause 4: never copied, never chained). The check is `grep -n 'Read skills/' skills/*/SKILL.md` → no prose hits, and it is not satisfied by hiding the line inside a code fence, which the lint exempts for legitimate examples. Descriptions are verb-phrases; `Run the full …` and `Execute the entire …` are rejected by the lint, which is the correct outcome for anything shaped like a release workflow.

10. **This spec owns exactly two surfaces.** `commands/release.md`, and the skills it creates (each skill's `skills/<name>/SKILL.md`, its `.writ/manifest.yaml` entry, and the resulting root `SKILL.md` regeneration, which `/new-skill` Step 3.2–3.3 requires). No other command file, no `scripts/eval.sh`, no `scripts/eval-leanness.py`, no `scripts/archive-sweep.py`, no adapter, no ADR. If the work reveals a defect in a file it does not own, the finding is recorded in the story's notes and left there.

## Detailed Requirements

### The retained thin contract

`commands/release.md` after this spec contains, in order:

| Section | Source | Notes |
|---|---|---|
| Frontmatter contract | preserved, **unchanged** | `problem:` / `outcome:` / `exit_criteria:` survive **byte-for-byte** (constraint 6 of the phase; they were authored by `2026-08-11-component-contract` Story 4). **No key is added** — `required_skills:` is not used (Business Rule 3), so the frontmatter is byte-identical to its pre-spec text. |
| `## Overview` | preserved | Including the **Self-sufficient** line naming the inline release gate — it is the contract's statement that the gate exists. |
| `## Required Artifacts` | preserved | Pinned by `check_artifact_integrity()`. |
| `## Invocation` | the existing `## Modes` table | Renamed to `## Invocation` per ADR-021 clause 1; all seven rows preserved verbatim, including `--skip-gate`. |
| `## Command Process` — phase list with gate names | **new** | Five phases, each one line, each naming its gate (where it has one) and the skill that carries its detail. This is the reader's map, and it carries **no** `Read skills/` string (Business Rule 3). |
| Per-phase `Read` anchors | **new** | One short retained anchor per phase carrying that phase's inline `Read skills/<name>/SKILL.md` at the point of need. ~5 lines total; this is what replaces the `required_skills:` array. |
| The release gate (Step 1.3a/b/c) | preserved in full | Business Rules 4, 5, 6. |
| Step 1.5 and Step 2.3 `AskQuestion` blocks | preserved | Business Rule 4. |
| Audit-rollup retained core | partially preserved | Non-blocking guarantee, `writ.auditNotes` opt-out, `TAG_TARGET_SHA` attach block, never-`refs/notes/commits` rule. Composition detail extracts. |
| `## Error Handling` | preserved | Business Rule 4 — two of its three prompts decide whether a release happens. |
| `## Completion` | preserved **byte-for-byte** | Constraint 6 of the phase. Its terminal constraint — *"Do not publish to a package registry or announce the release"* — is a production-boundary statement and stays in the contract. |
| `## References` | preserved + extended | Adds one line per declared skill; absorbs the four `## Integration with Writ` relationships as compact reference lines. Must keep the `commands/_preamble.md` link (`check_preamble()`). |

Everything else extracts. `## Integration with Writ`, `## Monorepo Support`, `## Dry Run Mode`, and `## Runtime Helper Publish (manual)` are not among ADR-021 clause 1's permitted sections and do not survive as top-level sections.

### The extraction map

Fifteen source ranges: fourteen relocate into five skills, one is contracted in place. Byte counts measured 2026-08-12 against the pre-spec file; the full table with line ranges is in `sub-specs/technical-spec.md`. Names follow the pilot spec's convention (Business Rule 8) and are checked against the manifest before scaffolding.

| Skill | Absorbs | Bytes out | `Read` anchor | Loads when |
|---|---|---|---|---|
| `changelog-generation` | Step 1.2 Analyze Changes; Steps 2.1–2.2 changelog format, source priority, quality rules, `CHANGELOG.md` create/prepend | 2,354 | Phase 1 → Step 1.2 anchor | Every path that reaches Step 1.2, including `--dry-run` and gate-blocked runs |
| `semver-version-bump` | Step 1.1 version-source detection + release-context gather; Step 1.5 bump-determination table; Steps 3.1–3.2 version-file writes and release commit; Monorepo scope selection | 3,201 | Phase 1 → Step 1.1 anchor | Every path past Step 1.1; the write half is re-read at Phase 3 with no second charge |
| `git-tag-publication` | Steps 4.1–4.3 tag/push/`gh release`; Step 4.4 rollup composition; Phase 5 summary; the dry-run "commands that would run" detail | 3,912 | Phase 4 anchor | **Never on `--no-tag` or bump-only** — the largest real conditional win |
| `readme-freshness-audit` | Step 1.4 README freshness check | 1,858 | Phase 1 → Step 1.4 anchor | Only when a `README.md` exists |
| `npm-package-publication` | The `@sellke/writ` decoupling note in 1.3c; `## Runtime Helper Publish (manual)` | 2,454 | `## References`, marked manual/out-of-band | **Never during a `/release` run** — manual, out-of-band, Writ-source-repo only |

Total relocated: **13,779 bytes**, plus ~650 bytes of scaffolding per skill. A further 689 bytes (`## Integration with Writ`) is contracted into `## References` rather than relocated.

The right-hand column is now a description of what the harness actually does, not of a hypothetical lazy one. Each `Read` fires only if execution reaches its anchor, so the column and the path table in § *Why This Exists* are the same claim stated twice. Two consequences worth stating outright: `--dry-run` still previews the tag/publish commands, so it reads `git-tag-publication` and saves almost nothing (§ Interaction Edge Cases); and `semver-version-bump` is read on nearly every path, so its 3,201 bytes are close to floor-like in practice even though they are formally conditional.

### Why `npm-package-publication` costs no `/release` run anything

It is the one skill no `/release` run reaches. `commands/release.md` states today that the `@sellke/writ` runtime helper is **decoupled from `/release`** — no `npm publish`, no `package.json#version` bump, no preflight.

An earlier draft of this spec exempted it from `required_skills:` on exactly that reasoning, then **withdrew the exemption** under the pilot spec's Business Rule 8: declare every extracted skill, never a curated subset, because a static array under-filled reports a ceiling below the true worst case.

**The exemption is reinstated, and the withdrawal is recorded as an artifact of the wrong mechanism.** Business Rule 8's reasoning was sound for a static, eagerly-loaded array — the only defensible way to fill one is completely, since every entry is paid on every run regardless. It does not transfer to an inline `Read`, where there is no array to curate and no way to under-fill one. The saving is not a reporting choice; it is a call that does not happen. A release that publishes no package genuinely never pays those ~2,754 bytes, and saying otherwise would be the fiction, not the exemption.

Nothing is hidden by this. The skill is still reachable (its `Read` sits on the `## References` line that marks the procedure manual and out-of-band), `measure-invocation.py` still finds that line by regex and still counts the skill in the tool's worst-path ceiling, and Story 5 reports that number beside the release-path number that excludes it. The remaining honest statement is the reverse of the old one: **relocating this section improves the floor and improves every real path's ceiling, and worsens only a worst-path figure no run performs.** If Story 5 needs the tool's worst-path number under 63,534 and nothing else will do it, dropping this extraction and leaving the section in the command is still a named lever — ~2,754 B of worst-path ceiling for ~2,454 B of floor — and it is still a maintainer decision, not an implementer's.

### Skill authoring mechanics

Each skill is scaffolded with `/new-skill <name>`, which writes `skills/<name>/SKILL.md` with the `## Purpose` / `## When to Use` / `## How to Apply` / `## Examples` shape, appends an alphabetically placed entry to `.writ/manifest.yaml`, and regenerates the root `SKILL.md` catalog via `scripts/gen-skill.sh`.

`.writ/manifest.yaml` and root `SKILL.md` are **shared with five sibling specs**. To keep parallel worktrees from colliding: each skill story writes its own contiguous alphabetical block into `.writ/manifest.yaml`, and the root `SKILL.md` is regenerated **once**, in Story 4, from the merged manifest — not three times in three parallel branches. `bash scripts/gen-skill.sh --check` must report no delta at the end.

**The `skills` surface will grow and that growth is justified, not absorbed.** `.writ/leanness-baseline.json` records the `skills` surface at 932 lines / 41,620 chars with no justifications. Five new skills raise it materially and will trip an unjustified-growth warning. The disposition is the **bound justification** mechanism `2026-08-11-governor-instrumentation` built and the pilot spec adopted: a `(surface, metric)`-scoped `{date, value, text}` record naming this spec, the bytes moved out of `commands`, and the corresponding `commands` reduction. `--update-baseline` is **not** used — it moves every surface's floor and records no reason. `.writ/leanness-baseline.json` is a data file shared with the sibling specs; Story 5 appends this spec's entries and touches nothing else in it.

## Out of Scope

- **Any change to `scripts/eval.sh`, `scripts/eval-leanness.py`, or `scripts/archive-sweep.py`** — Business Rules 6 and 10. Including relaxing a `require_literal` that this extraction finds inconvenient.
- **Lowering `check_length`'s 2000-line command limit to 400, and any absolute `per_surface.commands.chars` cap.** ADR-021 clause 5; owned by `2026-08-12-governor-enforcement`, which depends on this spec. The 400 figure is a tripwire this spec measures itself against, not a limit it installs.
- **Raising `MAX_SKILLS` from 12.** Six skills exist and six specs are adding; the cap will be crossed. It is warn-only in `eval-leanness.py` and ADR-021 says raising it must be "deliberate … rather than silently." Recording the crossing is this spec's job; raising the cap is not.
- **Any other command file.** `/ship` shares `resolve-spec-reference.py` with the archival hook and `refs/notes/writ` with the audit channel, and is a sibling spec's surface.
- **`commands/_preamble.md`** — Business Rule 7.
- **Redesigning the release flow.** Business Rule 2. Consolidating the two `AskQuestion` gates, changing a default, dropping monorepo support, or "simplifying" the audit rollup are all redesigns, however defensible they might be on their own.
- **Amending ADR-021 or ADR-022.** The pilot spec `2026-08-12-disclosure-implement-story` owns the ADR-021 `## Amendments` section — including the bytes-over-lines instrument change and the recorded measurement that `required_skills:` pre-load is eager rather than per-invocation. ADR-021 clause 3 still reads *"the command declares `required_skills: [...]` so the harness pre-loads only what that invocation needs"*, which the 2026-08-12 ruling contradicts; **amending that clause is the pilot spec's job, not this one's.** This spec follows the ruling, records its measured floor/ceiling/path figures as evidence for the amendment, and does not write to the ADR.
- **Changing `scripts/measure-invocation.py`.** It was fixed in `e8f2a09` and its output is this spec's instrument. If a further defect surfaces, it is recorded in the story notes and escalated (Business Rule 10) — not patched to make a number land.
- **Establishing the skill-naming convention or writing `.writ/docs/skills.md` → *Extraction Patterns*.** The pilot spec owns both. This spec follows (Business Rule 8).
- **Promoting the new skills past `candidate`.** ADR-014: promotion accrues from real use. ADR-021 says this phase does not close the lifecycle loop.
- **Migrating the extracted prose into `scripts/`.** ADR-021 considered and rejected it for this phase.

## Implementation Approach

1. **Stories 1–3 create skills only.** They read `commands/release.md`, they do not write it. Their file sets are disjoint by construction (each creates its own `skills/<name>/` directories), so they parallelize. Their only shared surface is `.writ/manifest.yaml`, handled by the alphabetical-block discipline above.
2. **Story 4 rewrites `commands/release.md`.** It is the only story that touches the command file, so no two stories ever race on it. It deletes the extracted ranges, writes the phase list and the per-phase `Read` anchors, leaves the frontmatter untouched, keeps the gate and the hook, and regenerates the root `SKILL.md` once.
3. **Story 5 measures and proves.** Budget (floor and ceiling, before and after), the full eval suite, the drift ledger, and the pin inventory. Separated from Story 4 deliberately: the story that writes the file is not the story that certifies it, and the ceiling number needs somewhere it can force a halt without unwinding Story 4's work.

Ordering: 1 ∥ 2 ∥ 3 → 4 → 5.

## Success Criteria

1. `python3 scripts/measure-invocation.py --root . --command release` reports `command_bytes` **≤ 24,960** (from 28,589), `unresolved_skills: []`, `eager_bytes: 0`, and `eager_skills: []` — no `required_skills:` declaration exists, and the tool emits no "loads both ways" warning.
2. The same run reports `floor_bytes` **< 53,549** (from 53,549), and floor, worst-path ceiling, and the § *What disclosure can and cannot buy here* path table are all recorded before and after in Story 5's evidence — none reported alone.
3. `ceiling_bytes` ≤ **63,534** (the corrected pre-spec ceiling), or above it with the three-part written justification Business Rule 1 requires — measured overage, compression attempted with measured yield, explicit maintainer acceptance. The report also carries the `conventional-commits`-excluded pair (53,549 → post-spec) so the symmetry of that 9,985-byte load is visible rather than assumed.
3a. Each named partial path is measured, not projected: an abort before Step 1.2, a gate-blocked run, a `--no-tag` run, and a full release. If the full-release saving is within noise of zero, the report says so in those words rather than leading with the floor.
4. `bash scripts/eval.sh` produces **no new findings** relative to its pre-spec baseline. Specifically, `--check=post-merge-archival`, `--check=git-notes-audit`, `--check=artifact-integrity`, and `--check=preamble` all pass, and all fifteen pinned literals are present in `commands/release.md` while `is_complete_family` is absent.
5. `bash scripts/eval.sh --check=length` passes, and `commands/release.md` is under the 400-line ADR-021 tripwire (secondary, non-binding — a miss is reported, not a failure).
6. The release gate, `--skip-gate` semantics, both `AskQuestion` gates, the dirty-tree and no-changes prompts, and the audit rollup's non-blocking + opt-out guarantees are all present in `commands/release.md` and absent from every skill (Business Rule 4). Verified by grepping each skill body for the gate vocabulary.
7. Step 1.3c's archival hook is byte-identical to its pre-spec text and still nested inside the `LAST_MERGED_SHA == HEAD_SHA` branch (Business Rule 5). `git show <base-sha>:commands/release.md | sed -n '154,163p'` diffs clean against the post-spec file's corresponding block.
8. `commands/release.md`'s whole frontmatter block is byte-for-byte unchanged — `problem:` / `outcome:` / `exit_criteria:` and no added key — and its `## Completion` section is byte-for-byte unchanged.
9. Every skill created passes `bash scripts/lint-skill.sh skills/<name>/SKILL.md`, carries `status: candidate` and `disable-model-invocation: true`, has a `.writ/manifest.yaml` entry, satisfies the pilot spec's naming convention, and is reached by exactly one inline `Read skills/<name>/SKILL.md` at its anchor **and** named in the phase list — with no `Read skills/` string inside the phase-list table and none inside any `skills/*/SKILL.md` prose (`scripts/lint-skill.sh:52`).
10. `bash scripts/gen-skill.sh --check` reports no delta.
11. The drift ledger in Story 5's evidence accounts for **all fifteen** extraction-map ranges, each with `semantic delta` of `none (verbatim)` or `contracted: <reason>`, and no other value.
12. `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` reports `status: ok` with this spec ordered after `2026-08-12-disclosure-implement-story` and before `2026-08-12-governor-enforcement`, which depends on it.
13. `.writ/leanness-baseline.json` carries a bound justification for the `skills` surface naming this spec, the bytes moved, and the corresponding `commands` reduction — and `--update-baseline` was not run.

## Technical Concerns (surfaced at contract time)

- **ADR-021 clause 3 is wrong on its face and this spec no longer follows it.** It says the command declares `required_skills: [...]` "so the harness pre-loads only what that invocation needs." It is a static array in a static file — it cannot vary between `/release --dry-run` and `/release major`, and both `system-instructions.md` and `adapters/claude-code.md:396` say the load happens before phase 1 regardless. The 2026-08-12 maintainer ruling replaces it with the inline read (see § *Approved scope change*). The residual concern is **document divergence**: until the pilot spec lands the ADR-021 amendment, the governing decision record and six specs disagree in writing, and a reader who finds clause 3 first will build the wrong thing. This spec cannot fix that (Out of Scope) and flags it as the phase's highest-priority documentation debt.
- **`/release` is the sequential-pipeline case ADR-021 warned about, and the mechanism change does not rescue the full-release path.** Every phase reaches its skill, so the full path reads all of them: projected ~63,411 against a 63,534 bar — a saving of ~123 bytes, or 0.2%. Disclosure works here for aborted and gate-blocked runs (−22.4% and −8.8%) and for `--no-tag` (−5.2%); it does essentially nothing for the run most maintainers perform. That is not a reason to stop — the floor reduction is real and permanent, and ADR-021's own framing is per-invocation load, not best-case load — but it is the number most likely to be quietly omitted from a summary. Two named levers if the tool's worst-path figure needs to clear the bar: consolidate `readme-freshness-audit` into `changelog-generation` (−650 B scaffolding; both are Phase-1 read-side capabilities), or drop the `npm-package-publication` extraction and leave that section in the command (−~2,754 B worst-path ceiling, +~2,454 B floor). The second trades a figure no run pays against one every run pays — a maintainer decision, not an implementer's.
- **A conditional load can fail, and this spec's own edge cases are where it will show.** The mechanism that produces the saving is a `Read` the agent may not issue. Business Rules 4 and 5 keep everything load-bearing out from behind one, but the residual risk is a *partially* loaded phase: a run that reads `semver-version-bump` at Step 1.1 and then, after a long gate interaction, no longer has it in context at Phase 3. Nothing in this spec detects that, and no lint can. It is recorded here because the honest description of the mechanism is "conditional and best-effort", and Story 4's anchors should therefore sit at the step that *uses* the procedure rather than at the earliest step that mentions it.
- **The pins make part of this file un-extractable, and that is load-bearing rather than unfortunate.** 8,260 bytes — the gate (3,836), the archival hook (3,188), and the rollup core (1,236) — cannot leave `commands/release.md` without breaking `scripts/eval.sh`. That is 52% of the projected post-spec file. It is the same content the production-boundary rule protects. If a future spec relaxes a pin, it must re-derive the production-boundary argument first; the pin is currently doing double duty as both a regression check and an architectural constraint, and only one of those is written down in `eval.sh`.
- **The skill-naming convention arrived mid-authoring, and one name changed because of it.** The dependency spec `2026-08-12-disclosure-implement-story` was authored in parallel with this one and now exists; its Business Rule 3 rule 3 forbids naming a skill after its extraction site, including the command name. The draft name `release-publication` failed that test and is now `git-tag-publication`. The remaining four were checked against all six rules and against the pilot's eight skill names for head-noun collisions (`story-context-assembly`, `dependency-context-loading`, `what-was-built-authoring`, `boundary-map-computation`, `change-surface-classification`, `drift-triage`, `project-context-snapshot`, `story-commit-provenance`) — none collide. The collision protocol still applies at implementation time: four sibling specs write into the same namespace after this one is authored and before it is built.
- **Six specs share `skills/`, `.writ/manifest.yaml`, and the generated root `SKILL.md`.** The manifest is a hand-edited YAML file that `/new-skill` appends to alphabetically, and `gen-skill.sh` regenerates `SKILL.md` from it wholesale. Three parallel branches each running `gen-skill.sh` produce three conflicting full-file rewrites of `SKILL.md`. The single-regeneration rule in Detailed Requirements is the mitigation; it needs to hold across sibling specs too, which is beyond this spec's authority to enforce.
- **`MAX_SKILLS = 12` is already crossed before this spec runs.** Six exist today; the pilot spec alone adds eight, reaching 14. This spec adds five more, reaching 19 before three sibling specs have run. It is a warn-only tripwire in `eval-leanness.py`, so nothing blocks — which is exactly how ADR-021 says it must *not* be crossed ("deliberately with justification rather than silently"). Raising the constant belongs to `2026-08-12-governor-enforcement`. This spec records the count in Story 5's evidence and does not touch `eval-leanness.py`.
- **The archival hook has never actually fired in production.** `scripts/eval-post-merge-dogfood.py` reports 0 of 2 motivating specs hook-archived and is deliberately unregistered in `eval.sh`'s `CHECKS=()` until it does. So the hook's behavior is asserted by fixture and by prose pin, never by a live run. That raises the cost of getting its relocation wrong — a silent, best-effort, never-yet-fired feature has no observable failure signal — and is the reason Business Rule 5 is byte-identity rather than behavioral equivalence.
