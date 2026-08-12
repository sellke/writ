# Spec: Progressive Disclosure — `/verify-spec`

> **Status:** Not Started
> **Owner:** @AdamSellke
> **Created:** 2026-08-12
> **Dependencies:** [2026-08-12-disclosure-implement-story]
> **Origin:** `/plan-product` Phase 10 discovery (2026-08-11) measured the command surface at 516,589 chars / 10,996 lines across 32 files, with the top 6 files carrying 40% of all command bytes. [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) rules that those six shrink to thin contracts with per-phase procedure extracted to `skills/<name>/SKILL.md`, one spec per file, in descending size order. `commands/verify-spec.md` is the **third** file — 32,110 bytes / 732 lines, re-measured against this working tree on 2026-08-12.

## Contract (Locked)

**Deliverable:** `commands/verify-spec.md` — 32,110 bytes / 732 lines — reduced to a thin contract with its per-check procedural detail extracted to `skills/<name>/SKILL.md`, loaded on demand via `required_skills:`.

**Must include:** The thin contract retains only what [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) permits — frontmatter contract (ADR-020), `## Overview`, `## Invocation` table, the phase list with gate names, `## Completion`, `## References`. Skills authored through `/new-skill` (born `status: candidate`, lint-clean). **Follow the extraction pattern and skill-naming convention established by the dependency spec `2026-08-12-disclosure-implement-story`.**

**Hardest constraint:** `/verify-spec` is an 8-check diagnostic with auto-fix and a `--product` mode with its own P1-P4 check set. Its checks are its substance. Extracting them to skills must not change which checks run, in what order, or what each auto-fixes versus reports — the hybrid disposition (auto-fix derivatives, report-only on authoritative divergence) is a locked boundary, not an implementation detail.

## Approved Scope Change — Load Mechanism (maintainer decision, 2026-08-12)

**Recorded here, not in `## Contract (Locked)`, which is unaltered.**

This spec and its sibling `2026-08-12-disclosure-create-spec` independently found that `required_skills:` is an **unconditional pre-load**. The finding is **verified and accepted**: `system-instructions.md` § *Harness contract* has the harness load every declared skill *"before any phase work begins"*, and `adapters/claude-code.md:396` says the same. [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) §12's description of extracted skills as *"loaded on demand"* is false of the mechanism §18 chose. § *Why the byte budget is not the hard part* and § *Technical Concerns* stated this correctly and were right to.

**Ruling: `required_skills:` is not used by this spec.** Each of the four skills is reached by an inline `Read skills/<name>/SKILL.md` **at the step that needs it**. That form is genuinely conditional — the agent issues the call only if execution reaches that step — and it is already the shipping pattern in seven command files.

**Why the mechanism changes and the plan does not.** Under the eager mechanism every extracted byte reappears in the floor plus ~1,400 bytes of per-skill overhead: extraction is byte-neutral at best, which is why this spec's ceiling arithmetic demanded a 27% compression of the extracted prose merely to break even. **The byte ledger, the four skill names and their allocations, the disposition ledger, the frozen numbering, the six pinned literals, the preserved `loop:` block, and the 24,960-byte floor budget are all unchanged.** Only the load mechanism and the ceiling accounting change. The locked contract's phrase *"loaded on demand"* becomes true for the first time under the inline form.

**What this changes downstream, carried through the rest of this document:**

1. No `required_skills:` block is added to `commands/verify-spec.md`. Reachability is one inline `Read` per skill per path (Business Rule 10).
2. **Placement is the whole point** (new Business Rule 14): each inline `Read` sits at the *narrowest* step that needs it, and hoisting one to the command preamble is forbidden.
3. Ceiling accounting becomes **path-dependent** (Business Rule 1): floor, worst-path ceiling, and at least one realistic partial path. For this command the natural contrast is `--product` versus the 8-check default — and it is a strong one, because **the two paths are mutually exclusive and share only two of the four skills.**
4. `scripts/measure-invocation.py` was fixed on 2026-08-12 (`e8f2a09`) — it had treated `required_skills:` as conditional. It now reports `floor = base + command + eagerly-declared skills` and `ceiling = floor + inline-read skills`. **Re-measured pre-spec baseline: `verify-spec` has no inline read today, so its ceiling equals its floor at 57,070** — the same number this spec already recorded, for a newly correct reason.
5. **Business Rule 7's gap is unchanged by this ruling and stays flagged.** See Business Rule 7.

## Why This Exists

`/verify-spec` is not a large command because it is verbose. It is large because it *is* twelve checks: eight spec checks with a four-step auto-fix phase, plus a self-contained `--product` set of four more with its own dispositions, its own report, and its own output file. There is very little padding to cut. That makes this the extraction where the pattern either holds or is revealed as prose-shuffling.

### The measured state (re-verified 2026-08-12 against this working tree)

| Measure | Value | How verified |
|---|---|---|
| `commands/verify-spec.md` | **32,110 bytes / 732 lines** | `wc -c -l commands/verify-spec.md` |
| Rank in `commands/` by bytes | **3rd** of 32 | `for f in commands/*.md; do echo "$(wc -c < $f) $f"; done \| sort -rn` |
| Irreducible shared base | **24,960 bytes** (`system-instructions.md` 20,153 + `commands/_preamble.md` 4,807) | `python3 scripts/measure-invocation.py --root . --command verify-spec` |
| Floor (base + command) | **57,070 bytes** | same |
| Ceiling (floor + declared skills) | **57,070 bytes** — identical, because the command declares no `required_skills:` | same |
| Base share of floor | **43.7%** | same |
| Declared `required_skills:` across the whole product surface | **0** | `eval-leanness.py check_required_skills` docstring: *"this check has nothing to resolve today"* |

### The binding budget

**A command file may not cost more to load than the shared contract it runs inside.** The budget is the irreducible shared base: **24,960 bytes**. `verify-spec.md` must land **≤ 24,960**, down from 32,110 — a **22.3%** cut. The 400-line cap from ADR-021 is a secondary, non-binding tripwire; bytes are the instrument, because a 400-line file of dense tables costs more than a 500-line file of short lines.

**A correction to the framing this spec was commissioned under.** The 22% figure is right; the claim that it is *the smallest cut of the six* is not. Measured 2026-08-12:

| Command | Bytes | Cut to reach 24,960 |
|---|---|---|
| `implement-story` | 52,709 | 52.6% |
| `create-spec` | 46,423 | 46.2% |
| **`verify-spec`** | **32,110** | **22.3%** |
| `implement-phase` | 29,136 | 14.3% |
| `release` | 28,589 | 12.7% |
| `ship` | 28,371 | 12.0% |

`verify-spec` is the **third-largest** required cut, not the smallest — `ship`, `release`, and `implement-phase` all need less. The reason this spec is still the best test of *achievability* survives the correction, but it is a different reason and must be stated as the real one: **this is the first of the six whose file is almost entirely irreducible substance.** `implement-story` and `create-spec` are sequential pipelines with narrative connective tissue; `verify-spec` is a check catalogue. If a thin contract can carry a check catalogue without losing a disposition, it can carry anything. If it cannot, the phase learns that here rather than after five easier wins.

### Why the byte budget is not the hard part

The floor budget is comfortably reachable. Section-level measurement of the current file (`spec.md` § Detailed Requirements → *The byte ledger*) shows only **4,324 bytes** of it are content ADR-021 permits the thin contract to retain. Even after writing a new phase list from scratch, the command lands near **7,900 bytes** — 68% under the 24,960 cap.

The number that binds is the **ceiling**. [ADR-021's caveat 2](../../decision-records/adr-021-progressive-disclosure-token-budget.md) states the failure mode plainly: *"Progressive disclosure can increase total tokens. A command that ends up needing every extracted skill costs more than the monolith."* This spec found that for `/verify-spec` that was not a risk but the **default case**, because `required_skills:` as specified in [`system-instructions.md`](../../../system-instructions.md) has no conditional or mode-scoped form:

> *"When a consumer with `required_skills: [foo]` is invoked, the harness loads `skills/foo/SKILL.md` … and makes it accessible to the agent before any phase work begins."*

**That finding was correct, and on 2026-08-12 the maintainer accepted it and changed the mechanism rather than the budget** (§ *Approved Scope Change*). `required_skills:` is not used. Each skill is inline-read at the step that needs it, and the analysis below is restated against that mechanism.

**The ceiling is still the binding number, but it is now a *worst path* rather than *every run*.** Two consequences, and the second is the more important:

1. **The tool's `ceiling_bytes` is an envelope, not a path.** `measure-invocation.py` sums every inline read in the file; it cannot know which are mutually exclusive. Holding `ceiling_bytes ≤ 57,070` is still exactly `command_bytes + Σ(skill bytes) ≤ 32,110` — **the sum of the parts may not exceed the whole** — and it remains Business Rule 1's mechanical bar, unchanged, including the ~27% compression it demands.
2. **No invocation of this command reaches all four skills.** The `--product` path and the default 8-check path are mutually exclusive by construction, which is *why* the skill split follows the `--product` boundary. So the envelope overstates every real run, and the per-path figures — which Business Rule 1 now also requires — are far below it:

| Path | Skills read | Projected bytes | vs. today's 57,070 |
|---|---|---:|---|
| **Floor** — any run, before any branch | none | ~32,860 | −24,210 |
| `--product --check`, no `.writ/product/` (graceful skip) | product-doc-audit | ~37,260 | −19,810 |
| `--product` full run | product-doc-audit, derivative-regeneration, report-authoring | ~45,460 | −11,610 |
| `--check` (read-only, no regeneration) | spec-metadata-diagnosis, report-authoring | ~50,060 | −7,010 |
| **Default full run — the maximal *reachable* path** | spec-metadata-diagnosis, derivative-regeneration, report-authoring | **~52,660** | **−4,410** |
| *(tool envelope — all four, unreachable)* | all four | ~57,060 | −10 |

Projections against the allocation table below; Story 5 replaces every cell with a measurement. **The maximal reachable path is ~4,400 bytes below the envelope**, because `product-doc-audit` (≤ 4,400) is never read on the default path and `spec-metadata-diagnosis` (≤ 11,600) is never read under `--product`. That headroom is the phase's actual win on this command, and under the superseded eager design it did not exist: every run paid all four.

**This does not relax the compression requirement.** Σ ≤ 24,200 stays as Business Rule 1's bar, because it is the one figure a tool can check and because a bar set to the reachable path would be a bar chosen after the fact. What changes is that the compression now buys real per-run savings instead of buying a break-even.

### What makes this extraction dangerous

Three things, all verified in the working tree, none of them about bytes:

1. **Other commands cite `verify-spec`'s checks by number, and this spec may not edit those files.** `commands/release.md:106` runs *"`/verify-spec` **checks 1–6** inline against each applicable spec (same logic as the standalone command)"*. `commands/ship.md:335` runs *"**`/verify-spec` checks 1–3 only** … (definitions identical to the standalone command)"*. `README.md:134` describes checks 1–8. If extraction renumbers or renames a check, three files start pointing at nothing, and none of them is in scope.

2. **`commands/plan-product.md:39` deep-links a section anchor inside `verify-spec.md`** — `[/verify-spec --product](verify-spec.md#product-consistency-checks---product)`. `scripts/eval.sh check_broken_refs` resolves the *path* and never the *fragment* (`resolve_ref_target`, `scripts/eval.sh:362-392`), so deleting the `## Product Consistency Checks (`--product`)` heading breaks that link **silently**. Nothing in the repo would report it.

3. **`scripts/eval-loop-bounds.py` guards this exact file against gaining a re-check step, and it reads only the command.** The `verify-spec-no-recheck-step` finding (`scripts/eval-loop-bounds.py:524-536`) scans `commands/verify-spec.md`'s structural lines — headings and numbered steps — for `re-?(check|verify|run)`. It does not read `skills/`. A re-check step relocated into a skill would change the loop's shape and pass the guard.

4. **`scripts/eval.sh` pins five literal strings inside `commands/verify-spec.md`, and four of them live in text this extraction was going to move.** `check_spec_dependencies` (`scripts/eval.sh:1781-1783`) requires `Cross-spec dependency validation`, `self-reference`, and `story dependency validation is unchanged` — all three inside Check 4d. `check_spec_lifecycle_docs` (`scripts/eval.sh:1901`) requires `spec-lifecycle.md`, which appears only in Phase 1's `--all` prose. The same function forbids `specs/**` (`:1902`). `require_literal` tests the **command file**, not the command plus its skills; moving those strings into a skill produces four blocking eval findings, and `scripts/eval.sh` is out of scope to change. Business Rule 5 pins them.

## 📋 Business Rules

1. **The worst-path ceiling may not regress, and the report is path-dependent.** After extraction, `command_bytes + Σ(bytes of every inline-read skill) ≤ **32,110**` — today's single-file total. Measured with `python3 scripts/measure-invocation.py --root . --command verify-spec` as fixed on 2026-08-12, whose `ceiling_bytes` must be ≤ the pre-spec `ceiling_bytes` of **57,070**. A rise is not automatically a failure, but it is a **written** finding: the final story's evidence must state the measured rise, cite [ADR-021 caveat 2](../../decision-records/adr-021-progressive-disclosure-token-budget.md), and name what would have to be cut to avoid it. An unexplained rise fails review.

   **Three figures are reported, not one.** Reporting only `floor_bytes` fails review; so does reporting only `ceiling_bytes`.
   - **Floor** — `command_bytes ≤ 24,960`, and `eager_bytes` must be **0**: no `required_skills:` is declared.
   - **Worst-path ceiling** — `ceiling_bytes ≤ 57,070`. This is the tool's **envelope**: it sums every inline read and cannot know which are mutually exclusive.
   - **Per-path figures** — at minimum the `--product` path and the default 8-check path, which share only `derivative-regeneration` and `verification-report-authoring`. The evidence must name the **maximal reachable path** (projected: the default full run, ~52,660) and state how far it sits below the envelope. That gap is where this command's per-invocation saving actually lives, and no tool produces it.

2. **Floor budget: `command_bytes` ≤ 24,960.** Down from 32,110. The 400-line cap is a secondary tripwire, reported but not binding. **Precedence when these conflict: fidelity (Rule 3) > floor budget > ceiling non-regression.** Fidelity is absolute; the floor budget is a hard number this spec commits to; the ceiling is the number that may be missed *with a written justification* and may never be missed silently. With no skill declared, `floor_bytes = base + command`, so the floor is now genuinely what every run pays rather than a number nobody pays.

3. **No redesign — and the verification method is the disposition ledger, not an assurance.** Story 1 transcribes, from the pre-extraction file, a ledger of every check: its number, its heading text verbatim, its sub-checks, its position in run order, and its disposition (auto-fix / report-only / blocking / warning-only). Story 5 rebuilds the same ledger by reading **only** the thin command plus its declared skills, and the two must match **cell for cell**. Any mismatch is a redesign, whether or not it looks like an improvement.
   - **Ambiguity is transcribed, never resolved.** Where the source states no disposition for a check (Check 1 has no disposition blockquote), the ledger records `unstated in source` and the extraction preserves it as unstated. Resolving an ambiguity *is* redesigning; a reader who wants Check 1's disposition settled should open an issue, not a diff.
   - The before-ledger is built with `git show <base>:commands/verify-spec.md`, so it survives the rewrite and can be diffed against afterwards.

4. **Check numbering and heading text are frozen.** Checks 1–8, sub-checks 1a–1d / 2a–2c / 3a–3d / 4a–4d / 5a–5b / 7 / 8, auto-fix steps 4.1–4.4, and product checks P1–P4 keep their numbers and their heading strings verbatim wherever they land. `commands/release.md:106`, `commands/ship.md:335`, and `README.md:134` cite them by number and are **out of scope** (Business Rule 9). A renumbering this spec cannot follow through is a break it cannot repair.

5. **Strings other tooling depends on survive *in the command file*, not in a skill.** Six of them, none negotiable, all verified 2026-08-12:

   | String | Enforced by | Currently at | Minimum retained carrier |
   |---|---|---|---|
   | `Cross-spec dependency validation` | `require_literal`, `scripts/eval.sh:1781` | `verify-spec.md:234` | Check 4d's name in the Phase 2 gate list |
   | `self-reference` | `require_literal`, `scripts/eval.sh:1782` | `verify-spec.md:246` | Check 4d's blocking-finding list in the Phase 2 gate list |
   | `story dependency validation is unchanged` | `require_literal`, `scripts/eval.sh:1783` | `verify-spec.md:237` | The 4a–4c / 4d two-graph boundary note |
   | `spec-lifecycle.md` | `require_literal`, `scripts/eval.sh:1901` | `verify-spec.md:46` | The `--all` row's link to the archive-exclusion doc |
   | `specs/**` | **`forbid_literal`**, `scripts/eval.sh:1902` | absent | Must stay absent — from the command **and** from every skill |
   | `## Product Consistency Checks (\`--product\`)` | nothing — and that is the problem | `verify-spec.md:544` | The heading itself, byte-identical |

   `require_literal` tests `commands/verify-spec.md`, never the command plus its skills. Moving Check 4d's three strings or the `spec-lifecycle.md` link into a skill produces four **blocking** eval findings, and `scripts/eval.sh` is out of scope (Business Rule 9). The last row is the inverse hazard: `commands/plan-product.md:39` links `verify-spec.md#product-consistency-checks---product`, `check_broken_refs` resolves the path and never the fragment, so deleting that heading breaks the link **silently and permanently**. Four strings are checked and would fail loudly; one heading is unchecked and would fail invisibly. Both are pinned here.

6. **The hybrid disposition boundary is locked.** Derivatives are regenerated; authoritative files are read and never written. `spec.md` is never a target of Check 7 / step 4.4. `mission.md` and `roadmap.md` are never targets of `--product`. P1 (phase-status parity) and P2 (ADR reference resolution) surface *authoritative* divergence and stay report-only; P3 (derivative freshness) regenerates `mission-lite.md` and `.writ/context.md`; P4 stays report-only heuristic. 4a–4c stay report-only; 4d stays blocking except duplicate entries, which auto-fix by order-preserving deduplication; 6 stays report-only heuristic; 8 stays warning-only and never backfills without explicit approval. No skill may soften, sharpen, or generalize any of these.

7. **No re-check step — in the command *or* in any extracted skill.** `scripts/eval-loop-bounds.py`'s `verify-spec-no-recheck-step` reads only `commands/verify-spec.md`'s structural lines and would not see a re-check relocated into `skills/`. Introducing one there would change the loop's shape while passing the guard, which is worse than tripping it. No heading and no numbered step in the command or in any skill this spec creates may match `re-?(check|verify|run)`.

   **This rule extends the guard into skills by contract, and nothing enforces it. The 2026-08-12 mechanism ruling does not change that, and the gap stays flagged.** Extending the guard to read a command's skills is a `scripts/` change and out of scope (Business Rule 9). It is worth being precise about why the ruling is neutral here: the guard's blind spot is that it does not read `skills/` **at all**, so it is indifferent to *how* a skill is loaded. Switching from `required_skills:` to an inline read neither widens nor narrows it. The accepted reduction in enforcement coverage stands exactly as § *Technical Concerns* records it, and the governor-enforcement work should still be told. The only defense in this spec is the grep in `sub-specs/technical-spec.md` § *Verification Commands* step 4, run by hand over command **and** skills.

8. **The `loop:` block is preserved byte-identical, and its citation must stay true.** `loop.unit: autofix_pass`, `max_iterations: 1`, `on_exhaustion: halt_reported`, and the full `calibrated_against` string carry over unedited, together with `problem:` / `outcome:` / `exit_criteria:` from `2026-08-11-component-contract`. The citation asserts that the command *"runs Phase 2 (checks 1-8) then Phase 4 (auto-fixes 4.1-4.4) then Phase 5 (report file)"* — so the thin contract keeps **Phase 1–5 numbering and the 4.1–4.4 sub-numbering** in its phase list. A phase list that renames or renumbers those makes a preserved string false, which is worse than editing it.

9. **This spec owns `commands/verify-spec.md` and the skills it creates. Nothing else.** No edits to any other command, to `scripts/eval.sh`, to `scripts/eval-leanness.py`, or to `scripts/eval-loop-bounds.py`. `commands/_preamble.md` is **not** a carrier for shared procedure: it is 93 of 95 lines and its cap is owned by `2026-08-11-autonomy-gate-classes`, which forbids raising it a second time. Detail shared across consumers becomes a **shared skill**, per ADR-021 item 4. Registering new skills necessarily touches `.writ/manifest.yaml` and the generated root `SKILL.md` — that is `/new-skill`'s own behavior and is in scope as **append-only**; no other spec's entries may be reordered or edited.

10. **Every skill is reachable by an inline read at its step.** No `required_skills:` block is written. Each skill created here is reached by a literal `Read skills/<name>/SKILL.md` written **inside** the phase-list row whose detail it carries — executable text in the step, not a citation beside it. `measure-invocation.py` must report it under `conditional_skills`, with `eager_skills` empty, `unresolved_skills` empty, and **no "loads both ways" warning** (the tool emits that when a name is both declared and inline-read). A skill with no read is dead weight that made the surface worse; a skill both declared and read is a measurement that lies.

    **A skill needed on two disjoint paths gets one read per path.** `derivative-regeneration` is reached from step 4.4 on the default path and from Check P3 on the `--product` path, and `verification-report-authoring` from Phase 3/5 and from the product report. Each gets **two** reads, one at each point of need — **not** one read hoisted to their common ancestor. The tool deduplicates names, so this costs nothing in the measurement and is the difference between `--product` paying 12,600 bytes and paying 24,200.

14. **Placement is the mechanism: narrowest step, no hoisting.** Each inline `Read` sits at the last point after which the skill is genuinely needed — inside the phase or check row, never in the command preamble, never in `## Overview`, never in a "skills this command uses" block near the top. **A read hoisted above the branch that decides whether it is needed re-creates the eager mechanism by hand**, reports an identical `ceiling_bytes`, and passes every automated check in this spec. Specifically: `spec-metadata-diagnosis` is read under Phase 1/2 and must **not** be reachable on a `--product` run; `product-doc-audit` is read under the `## Product Consistency Checks (\`--product\`)` section and must **not** be reachable on a default run. Those two exclusions are the entire per-path saving, and nothing but placement produces them. Story 5 records the line numbers; that record is the only enforcement.

11. **The skill namespace is shared, and the naming convention is inherited, not invented.** `2026-08-12-disclosure-implement-story` Business Rule 3 owns it: kebab-case noun phrase, 2–3 words, ≤ 30 characters, unique across `commands:` / `agents:` / `skills:` in `.writ/manifest.yaml`; shape `<object>-<operation>` or `<operation>-<object>`; **never named after its extraction site** (no command name, no phase or check number); `description:` a bare-imperative verb phrase; a shared skill carries no consumer's vocabulary. Its **collision protocol** binds this spec: grep the `skills:` block for the intended name *and its head noun* before scaffolding; if a sibling already claimed the noun, **declare the existing skill** rather than authoring a near-duplicate, and add an ADR-014 `evidence:` entry of `type: promotion` to it. First writer owns the name. Never rename, edit, or absorb a sibling's skill.

12. **Skills are authored through `/new-skill` and are born lint-clean.** `status: candidate`, `disable-model-invocation: true`, verb-phrase `description:`, `## Purpose` + `## When to Use` present, `bash scripts/lint-skill.sh` exits 0, `bash scripts/gen-skill.sh --check` reports no delta. A skill body may not contain `Read commands/` or `Read skills/`, may not start a line with a slash command, and may not spawn subagents — `scripts/lint-skill.sh`'s body grammar rejects all four, and the extracted text contains slash-command references that must be re-shaped (not deleted) to satisfy it.

    **`lint-skill.sh:52` forbids `Read skills/` inside a skill body — no skill chaining — so every inline read introduced by the 2026-08-12 ruling lives in `commands/verify-spec.md` and nowhere else.** Checked against this spec's plan at amendment time: all placements are in the command. The one cross-skill dependency the plan contains — Story 2's Check 7 finding triggering Story 3's `derivative-regeneration` — is a *control-flow* relationship the command sequences, and the command's own step 4.4 read is what loads the skill. No skill loads another.

13. **Growth in the `skills` surface is justified, not absorbed.** The recorded baseline is **932 lines / 41,620 chars** (`.writ/leanness-baseline.json`, recorded 2026-08-04). Four skills carrying ~24,200 bytes grow that surface by roughly 58% and will raise an unjustified-growth warning in `eval-leanness.py`. The disposition is a **bound justification** — the `(surface, metric)`-scoped `{date, value, text}` record that `2026-08-11-governor-instrumentation` Story 1 built for exactly this case — naming this spec, the bytes moved into `skills`, and the corresponding `commands` reduction. **`--update-baseline` is not used:** it moves every surface's floor at once and records no reason, which is how the four live growth warnings ADR-021 complains about came to be ignored. `.writ/leanness-baseline.json` is a data file, not a script, so this is inside Business Rule 9's boundary.

## Detailed Requirements

### The byte ledger (measured 2026-08-12, `commands/verify-spec.md`)

Section boundaries are line ranges in the pre-extraction file; bytes include line terminators.

| Lines | Section | Bytes | Disposition |
|---|---|---:|---|
| 1–15 | frontmatter incl. `loop:` block | 1,729 | **Retain verbatim, append nothing** — no `required_skills:` (2026-08-12 ruling) |
| 16–24 | title + `## Overview` | 502 | Retain |
| 25–37 | `## Modes` table + `--product` boundary note | 1,386 | Retain, renamed `## Invocation` |
| 38–110 | Phase 1 — discovery, loading, JSON data model | 2,408 | Extract |
| 112–122 | Phase 2 header + mode behavior | 433 | Extract (mode rows stay in `## Invocation`) |
| 124–155 | Check 1 — story file integrity | 784 | Extract |
| 157–180 | Check 2 — status consistency | 609 | Extract |
| 182–211 | Check 3 — completion integrity | 903 | Extract |
| 213–260 | Check 4 — dependency validation (4a–4d) | 2,053 | Extract |
| 262–280 | Check 5 — deliverables checklist | 532 | Extract |
| 282–299 | Check 6 — contract vs implementation | 567 | Extract |
| 301–352 | Check 7 — spec-lite integrity | 2,897 | Split: checks → diagnosis skill, `--fix` behavior → regeneration skill, report shape → report skill |
| 354–389 | Check 8 — spec owner field | 1,321 | Extract |
| 391–444 | Phase 3 — console verification report | 2,479 | Extract |
| 446–485 | Phase 4 — auto-fix 4.1–4.4 + iteration bound | 2,235 | Split: 4.1–4.3 → diagnosis skill, 4.4 → regeneration skill, iteration-bound paragraph → **retain in command** |
| 487–541 | Phase 5 — verification report file | 1,720 | Extract |
| 544–702 | `--product` — P1–P4, inputs, mechanics, report | 7,744 | Split across product / regeneration / report skills; heading retained |
| 704–718 | `## Integration with Writ` | 1,081 | Not permitted by ADR-021 — three load-bearing rows condense into `## References` |
| 719–727 | `## Completion` | 541 | Retain |
| 728–733 | `## References` | 166 | Retain, extended |

**Retained source: 4,324 bytes.** Everything else — 27,786 bytes — is either extracted or condensed.

### The thin contract's shape

```
--- frontmatter ---            name, description, problem, outcome, exit_criteria,
                               loop (verbatim) — NO required_skills:
# Verify Spec Command (verify-spec)
## Overview
## Invocation                  the six-row mode table + the --product boundary note
## Command Process             Phases 1-5, each one line, naming its gates
  Phase 1                      Read skills/spec-metadata-diagnosis/SKILL.md
  Phase 2 gate names           Checks 1-8 by number and heading text, with disposition
  Phase 3                      Read skills/verification-report-authoring/SKILL.md
  Phase 4 gate names           4.1-4.4 by number, with the iteration-bound paragraph
    step 4.4                   Read skills/derivative-regeneration/SKILL.md
## Product Consistency Checks (`--product`)     heading byte-identical (BR5)
                               Read skills/product-doc-audit/SKILL.md
                               P1-P4 by number and heading text, with disposition
    Check P3 mechanics         Read skills/derivative-regeneration/SKILL.md
    product report             Read skills/verification-report-authoring/SKILL.md
## Completion
## References                  skills, preamble, system-instructions, ADR-021,
                               and the three retained relationship rows
```

**Six inline reads, four skills, zero declarations.** Two skills are read twice because they are needed on two mutually exclusive paths; `measure-invocation.py` deduplicates names, so the duplication costs nothing in the measurement and is what keeps `--product` from paying for `spec-metadata-diagnosis`. `## References` lists all four for a human reader — **a listing is not a load.**

**`## Modes` becomes `## Invocation`.** ADR-021 names the retained section `## Invocation`; `commands/new-command.md`'s generated-command structure table names it the same. No other file links to `#modes` (verified: `grep -rn 'verify-spec.md#' commands/ agents/ adapters/ *.md` returns only the `#product-consistency-checks---product` link in `plan-product.md`).

**Disposition stays in the command, procedure goes to the skill.** The phase list carries, per check, only what a reader needs to predict the command's behavior without loading anything: the number, the heading text, and whether it auto-fixes, reports, blocks, or warns. *How* each check is performed is the skill's content. This split is what keeps the hybrid boundary (Business Rule 6) legible in the thin file, where it is a contract, rather than only in a skill, where it would be a procedure.

### Skills — names and allocations

Four skills. Names are authored against `2026-08-12-disclosure-implement-story`'s Business Rule 3 convention (Business Rule 11) and were **collision-checked at spec-authoring time, 2026-08-12**, against the six incumbents and against every name claimed by the five sibling disclosure specs: `story-context-assembly`, `boundary-map-computation`, `change-surface-classification`, `drift-triage`, `drift-review-cycle`, `drift-testing-cycle`, `what-was-built-authoring`, `changelog-generation`, `readme-freshness-audit`, `audit-digest-composition`, `git-notes-audit`. **No name and no head noun collides.** Story 1 re-runs the check against the tree as it actually stands, because sibling specs may still land names after this one was written.

| Name | Carries | Source bytes | Allocation |
|---|---|---:|---:|
| `spec-metadata-diagnosis` | Phase 1 loading + data model; Checks 1–8 with their sub-checks and dispositions; repairs 4.1–4.3 | ~12,900 | **≤ 11,600** |
| `derivative-regeneration` | The whole-file regeneration discipline shared by step 4.4 (`spec-lite.md` ← `spec.md`) and Check P3 (`mission-lite.md`, `.writ/context.md` ← `mission.md`): source-is-never-target, full replacement never a patch, dated regeneration marker, single pass | ~3,500 | **≤ 2,600** |
| `product-doc-audit` | Checks P1–P4 with dispositions, the inputs table, the graceful-skip rule, the `--reconcile` boundary | ~4,600 | **≤ 4,400** |
| `verification-report-authoring` | The eight-row console table, the findings-detail sections, the Phase 5 report file template, the P1–P4 product report and its file, and all four completion messages | ~6,800 | **≤ 5,600** |
| | | **~27,800** | **Σ ≤ 24,200** |

Each is `<object>-<operation>`, 2–3 words, ≤ 30 characters, and named for the capability rather than for `/verify-spec` — `verify-spec-checks` would have been rejected by clause 3 of the convention and by ADR-009 besides.

| Name | Inline read placed at | Reachable on |
|---|---|---|
| `spec-metadata-diagnosis` | Phase 1, at spec discovery | default / `--check` / `--fix` / `--spec` / `--all` — **never `--product`** |
| `derivative-regeneration` | step 4.4, **and** Check P3's mechanics | default (after a Check 7 finding) or `--fix`; default `--product` (after P3) — **never under `--check` or `--product --check`** |
| `product-doc-audit` | the `## Product Consistency Checks (\`--product\`)` section | **`--product` only** |
| `verification-report-authoring` | Phase 3, **and** the product report | every path that reports |

The first and third rows are the whole per-path saving: 11,600 bytes a `--product` run never pays, and 4,400 bytes a default run never pays. Both depend entirely on where the read sits (Business Rule 14).

**Individual allocations may be traded; the total may not.** `command_bytes + Σ ≤ 32,110` (Business Rule 1) is the only figure that binds. With the command projected at ~7,900, skills get ~24,200 to carry ~27,800 bytes of source **plus** roughly 1,400 bytes each of skill frontmatter, `## Purpose`, and `## When to Use` — about 5,600 bytes of new overhead. That is a **~27% compression of the extracted prose**, and it is achievable only because the source repeats itself:

- The regeneration procedure is written **twice** — step 4.4 and the `--product` auto-fix mechanics — and the second copy says so out loud (*"Reuse default `/verify-spec`'s derivative-regeneration pattern"*). One skill, one copy. This is ADR-021 item 4 applied literally.
- The report structure is written **three times** — the console table, the Phase 5 file, and the product report that *"mirrors Phase 5's file."* One skill, one shape, two instantiations.
- Phase 1's 2,408-byte JSON data model is illustrative scaffolding around a six-line read list.

If the compression cannot be achieved without dropping a check, a disposition, or a run-order fact, **fidelity wins and the ceiling rise is written up** (Business Rule 2's precedence).

### `## Integration with Writ`

ADR-021's retained list does not include it, and `commands/new-command.md`'s generated-command structure table does — a genuine conflict between the two, recorded in § Technical Concerns. **Ruling for this spec: ADR-021 governs, because it is the decision this spec implements.** The section is removed; three of its six rows are load-bearing facts that other files depend on and are condensed into `## References`:

- `/release` re-runs checks 1–8 through its own entry point — the fact the preserved `calibrated_against` string depends on.
- `/ship` embeds checks 1–3 only when opening a PR.
- `/plan-product --reconcile` is `--product`'s revision counterpart (before/after discipline) — already stated in the retained `--product` boundary note.

The other three rows (`/implement-spec`, `/security-audit`, `/status`) are discoverability prose that each of those commands already states from its own side.

## Out of Scope

- **Any other command file.** `release.md`, `ship.md`, `migrate.md`, `plan-product.md`, `implement-spec.md`, `assess-spec.md`, `create-uat-plan.md`, `refresh-command.md`, `refactor.md`, `retro.md`, `status.md` all reference `/verify-spec` and are all out of scope (Business Rule 9). This includes the stale *"checks 1–7"* in `commands/migrate.md:323` — see § Technical Concerns.
- **`scripts/eval.sh`, `scripts/eval-leanness.py`, `scripts/eval-loop-bounds.py`, `scripts/lint-skill.sh`.** Extraction is measured *by* these scripts, never *with* changes to them — which is precisely why Business Rule 5's four `require_literal` strings must be worked around rather than relaxed, and why the `verify-spec-no-recheck-step` guard's new blind spot is accepted rather than closed. `.writ/leanness-baseline.json` is a data file and takes a bound justification (Business Rule 13), not a `--update-baseline` sweep. The `check_length` command limit (2000 → 400) belongs to Phase 10's governor-enforcement work; `MAX_SKILLS` belongs to whichever spec first exceeds 12 (this one does not — 6 existing + 4 new = 10, and it is warn-only besides).
- **`commands/_preamble.md`.** 93 of 95 lines; the cap is owned by `2026-08-11-autonomy-gate-classes` and may not be raised. Shared procedure becomes a shared skill.
- **Redesigning any check.** No check gains, loses, or changes a sub-check. No disposition moves. No ambiguity is resolved (Business Rule 3). Findings about a check's design are recorded in the story's notes and acted on by nobody here.
- **Adding a re-check pass, a second auto-fix pass, or any change to `loop:`.** Business Rules 7 and 8.
- **`--include-archived`.** The current file defers it explicitly; it stays deferred.
- **Promoting any skill past `candidate`.** ADR-014 promotion accrues from real use; ADR-021 records that this phase does not close the lifecycle loop.
- **Editing, renaming, or absorbing a sibling spec's skill.** Reuse is encouraged; mutation is forbidden.
- **A conditional or mode-scoped form of `required_skills:`.** The eager schema in `system-instructions.md` is left **unchanged**. That every declared skill loads on every invocation is a finding this spec records and the maintainer accepted on 2026-08-12 (§ *Approved Scope Change*); the response was to use the *other* mechanism `system-instructions.md:250` already documents — inline `Read skills/<name>/SKILL.md` at the point of need — not to change the field.
- **Declaring `required_skills:` at all.** Not an oversight and not deferred work: a maintainer ruling. An implementer who adds the block "for discoverability" moves all four skills into `floor_bytes`, blows the floor budget, erases both per-path exclusions, and inverts the spec's result — while `ceiling_bytes` is unchanged and every check still passes.
- **Correcting ADR-021 §12's "loaded on demand" claim.** It is false of the `required_skills:` mechanism §18 chose. Recorded by the 2026-08-12 ruling and handed to whichever spec next amends the ADR; this spec routes around it by not using the field.

## Implementation Approach

1. **Story 1 — baseline and the disposition ledger.** Re-measure floor and ceiling, transcribe the twelve-check ledger from the pre-extraction file, confirm the skill-naming convention against the landed dependency spec, and record the byte allocations. Nothing else can start: Stories 2–4 author against the ledger, and Story 5 verifies against it.
2. **Stories 2, 3, 4 — the four skills, in parallel.** Disjoint file sets by construction (each story creates only its own `skills/<name>/` directories). Each story ends with `lint-skill.sh` clean and its own byte allocation measured.
3. **Story 5 — the thin contract, the measurement, and the drift proof.** Rewrites `commands/verify-spec.md`, declares `required_skills:`, then rebuilds the ledger from command + skills and diffs it against Story 1's. Carries the before/after floor **and** ceiling report and the ceiling-rise justification if one is needed.

`.writ/manifest.yaml` is appended by each skill story via `/new-skill`. Three stories appending to one file in parallel is the only shared-write risk in this spec; Story 1 records the current `skills:` block so a mis-merge is detectable, and Story 5 runs `gen-skill.sh --check` as the reconciliation.

## Success Criteria

1. `commands/verify-spec.md` is **≤ 24,960 bytes**, measured by `python3 scripts/measure-invocation.py --root . --command verify-spec` (`command_bytes`), down from 32,110.
2. **Floor, worst-path ceiling, and per-path figures** are all reported before and after. `floor_bytes` falls from 57,070 and `eager_bytes` is `0`. `ceiling_bytes` is ≤ 57,070, **or** the final story's evidence carries a written justification citing ADR-021 caveat 2 and naming what would have had to be cut. The evidence additionally reports the `--product` path and the default 8-check path separately, names the **maximal reachable path**, and states how far below the tool's envelope it sits.
3. The **disposition ledger rebuilt from the thin command plus its declared skills matches Story 1's ledger cell for cell** — same twelve checks, same sub-checks, same run order, same disposition, same `unstated in source` cells.
4. Every check heading string from the pre-extraction file (`#### Check 1: Story File Integrity` … `#### Check P4: Shipped-Claim Sanity`) appears verbatim in exactly one of the command or its skills, verified by grep against `git show <base>:commands/verify-spec.md`.
5. All four `require_literal` strings — `Cross-spec dependency validation`, `self-reference`, `story dependency validation is unchanged`, `spec-lifecycle.md` — are present in `commands/verify-spec.md`; the `forbid_literal` string `specs/**` is absent from the command **and** from every skill; and `## Product Consistency Checks (\`--product\`)` is byte-identical so `plan-product.md`'s `verify-spec.md#product-consistency-checks---product` link resolves when rendered.
6. `python3 scripts/eval-loop-bounds.py` reports `PASS verify-spec-no-recheck-step`, and **no heading or numbered step in any skill created here** matches `re-?(check|verify|run)` either.
7. The frontmatter `loop:` block and the `problem:` / `outcome:` / `exit_criteria:` fields are byte-identical to their pre-spec state (`git diff` shows no hunk inside them), and the `calibrated_against` citation's assertions about Phases 2, 4, and 5 remain true of the new phase list.
8. `bash scripts/lint-skill.sh skills/*/SKILL.md` exits 0; every new skill carries `status: candidate` and `disable-model-invocation: true`; `bash scripts/gen-skill.sh --check` reports no delta.
9. **`commands/verify-spec.md` declares no `required_skills:`** (`grep` returns nothing). Every inline `Read skills/<name>/SKILL.md` resolves to a real file: `measure-invocation.py` reports `eager_skills: []`, `conditional_skills` holding all four names, `unresolved_skills` empty, and no "loads both ways" warning. `eval-leanness.py`'s `check_required_skills` reports `required_skills_declarations: 0` for this command with **no finding** — it reads frontmatter only, so it is silent on zero declarations **and will not catch a mistyped inline read**; `unresolved_skills` is what catches that. Every read sits inside the phase-list row whose detail it carries, and its line number is recorded (Business Rule 14).
10. `bash scripts/eval.sh` produces no new findings relative to its pre-spec baseline, including `check_broken_refs` and `check_length`.
11. `git diff --name-only` lists only `commands/verify-spec.md`, `skills/<new>/SKILL.md` files, `.writ/manifest.yaml`, `SKILL.md`, `.writ/leanness-baseline.json` (bound justification only), and this spec's own files.
12. Any `skills`-surface growth warning from `eval-leanness.py` is answered by a **bound justification** naming this spec, the bytes moved into `skills`, and the corresponding `commands` reduction. `--update-baseline` was not run.

## Technical Concerns (surfaced at contract time)

- **The ceiling, not the floor, is this spec's real budget — and until 2026-08-12 it was paid on every run.** `required_skills:` has no conditional form: `system-instructions.md` specifies that the harness loads every declared skill *"before any phase work begins."* Under that mechanism a `--product` invocation paid for `spec-metadata-diagnosis` and a default invocation paid for `product-doc-audit`, and the per-invocation saving was real only to the extent the extracted prose was genuinely compressed. **The maintainer accepted the finding and changed the mechanism** (§ *Approved Scope Change*): skills are inline-read at the point of need, the two mode-specific skills are no longer reachable from the other mode, and the maximal *reachable* path lands ~4,400 bytes below the tool's envelope. Business Rule 1 keeps the envelope bar as arithmetic **and** now requires the per-path figures, because the envelope is the number a tool can check and the per-path figures are the number that answers whether disclosure worked.
- **Placement is now the load-bearing detail, and no tool checks it.** Under the eager mechanism the load discipline was a YAML list that was either complete or not. Under inline reads it is six `Read` calls whose *positions* determine what every run pays. `measure-invocation.py` sums them wherever they sit; `lint-skill.sh` never opens a command; `eval.sh` and `eval-loop-bounds.py` have no opinion. Six reads hoisted to the top of the file report an identical `ceiling_bytes` and pass everything — while restoring the eager behavior exactly. Business Rule 14 states the rule; Story 5's recorded line numbers are the only enforcement.
- **ADR-021's retained-section list and `commands/new-command.md`'s generated-command structure table disagree.** ADR-021 permits frontmatter, `## Overview`, `## Invocation`, the phase list, `## Completion`, `## References`. `new-command.md`'s table also mandates `## Integration with Writ` (and, after `2026-08-11-component-contract` Story 1, `## Completion`). A command authored to ADR-021 will not match the template a new command is generated from. This spec follows ADR-021 and records the conflict; **reconciling the authoring template is not this spec's authority** and belongs with whichever Phase 10 spec next edits `new-command.md`. Flagged so the sixth disclosure spec does not re-litigate it six times.
- **Three files cite `verify-spec`'s check numbers and one cites a section anchor; none is in scope.** `release.md:106` (checks 1–6), `ship.md:335` (checks 1–3), `README.md:134` (checks 1–8), `plan-product.md:39` (the `--product` anchor). Business Rules 4 and 5 exist because the repair for breaking any of them is an edit this spec is not permitted to make.
- **`commands/migrate.md:323` already says `checks 1–7`.** Check 8 landed and that line was never updated — a pre-existing defect, discovered while verifying Business Rule 4, and **not fixed here** (Business Rule 9). Recorded so the next spec touching `migrate.md` has the finding rather than rediscovering it. It is also evidence for why Business Rule 4 is a hard rule: cross-file citations of this command's internals go stale silently and stay stale for releases.
- **The `verify-spec-no-recheck-step` guard develops a blind spot the moment this spec lands, and the 2026-08-12 mechanism ruling does not change it.** It reads `commands/verify-spec.md` only. After extraction, most of the procedure lives where the guard cannot see it. Business Rule 7 extends the prohibition to skills by contract, but nothing enforces it — extending the guard to scan a command's skills is a `scripts/` change and out of scope (Business Rule 9). The ruling is neutral here for a precise reason: the guard does not read `skills/` **at all**, so it is indifferent to whether a skill arrives via `required_skills:` or via an inline `Read`. **This remains a real, accepted reduction in enforcement coverage, it is unchanged, and the governor-enforcement spec should still be told about it.** The hand-run grep over command + skills (`sub-specs/technical-spec.md` § *Verification Commands* step 4) is the only substitute.
- **`lint-skill.sh`'s body grammar will reject naive extraction.** It rejects `Read commands/`, `Read skills/`, `Task(`, and any line beginning with a slash command. The source text contains lines such as `**If \`/verify-spec --spec [path]\`:**` (safe — the line begins with `**`) alongside prose that will need re-shaping. Re-shaping to satisfy the lint is permitted; deleting the content to satisfy it is a Business Rule 3 violation.
- **Three stories append to `.writ/manifest.yaml` in parallel.** `/new-skill` appends one `skills:` entry per skill. Alphabetical placement plus `gen-skill.sh --check` in Story 5 is the reconciliation; a lost entry surfaces as a `check_required_skills` finding rather than silently.
- **The skill namespace is shared across six sibling specs and the dependency lands first.** Story 1's first action is re-reading `skills/` and `.writ/manifest.yaml`, not scaffolding. If the dependency spec has already created something equivalent to `derivative-regeneration` — plausible, since `implement-story` also amends `spec-lite.md` — reuse it and drop the allocation. `MAX_SKILLS` is 12 and warn-only; 6 + 4 = 10 clears it, but the sixth disclosure spec probably will not, and that is that spec's decision to make deliberately.
