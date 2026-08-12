# Story 5: The Thin Contract, the Budget, and the Drift Proof

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 2, 3, 4

## User Story

**As a** maintainer evaluating whether progressive disclosure is worth continuing across the remaining three commands
**I want to** `commands/verify-spec.md` rewritten as a thin contract, with both floor and ceiling measured before and after and the disposition ledger re-derived from the new files
**So that** the phase gets an honest answer about whether a thin contract can carry a check catalogue, rather than a smaller file and an assumption

> **Amended 2026-08-12** — maintainer ruling on the load mechanism. `required_skills:` is eager and is not used; each skill is reached by an inline `Read skills/<name>/SKILL.md` at the step that needs it. `scripts/measure-invocation.py` was fixed the same day (`e8f2a09`) and every figure below is against the fixed tool. See spec.md § *Approved Scope Change* and Business Rule 14.

## Scope

Rewrite `commands/verify-spec.md` to the ADR-021 shape, place the inline skill reads, and produce the evidence.

**Retained (4,324 source bytes plus new connective content, projected ~7,900 total):**

```
--- frontmatter ---   name, description, problem, outcome, exit_criteria (byte-identical),
                      loop (byte-identical) — NOTHING APPENDED, no required_skills:
# Verify Spec Command (verify-spec)
## Overview
## Invocation         six-row mode table + the --product boundary note (was `## Modes`)
## Command Process    Phases 1-5, each naming its gates
                      Phase 1 → Read skills/spec-metadata-diagnosis/SKILL.md
                      Phase 2 → Checks 1-8 by number, heading text, and disposition
                      Phase 3 → Read skills/verification-report-authoring/SKILL.md
                      Phase 4 → steps 4.1-4.4 + the Iteration bound paragraph (retained)
                        4.4  → Read skills/derivative-regeneration/SKILL.md
## Product Consistency Checks (`--product`)    heading BYTE-IDENTICAL (BR5)
                      Read skills/product-doc-audit/SKILL.md
                      P1-P4 by number, heading text, and disposition
                        P3   → Read skills/derivative-regeneration/SKILL.md
                        report → Read skills/verification-report-authoring/SKILL.md
## Completion
## References         skills, _preamble, system-instructions, ADR-021, and the three
                      retained relationship rows (/release, /ship, /plan-product --reconcile)
```

**Six inline reads, four skills, zero declarations.** Two skills are read twice because they serve two mutually exclusive paths; the tool dedupes names so it costs nothing in the measurement, and it is the difference between `--product` paying ~12,600 bytes and paying ~24,200. `## References` lists all four for a human reader — **a listing is not a load.**

**Removed:** `## Integration with Writ` — not permitted by ADR-021; three load-bearing rows condense into `## References`, three discoverability rows drop.

## Acceptance Criteria

- [ ] Given the budget is 24,960 bytes, when `python3 scripts/measure-invocation.py --root . --command verify-spec` is run, then `command_bytes` ≤ 24,960 (down from 32,110), `eager_bytes` == 0, `eager_skills` == [], `conditional_skills` holds all four names, `unresolved_skills` is empty, and the tool emits **no "loads both ways" warning**.
- [ ] Given Business Rule 1, when the measurement is reported, then **all three figures** are given before and after: `floor_bytes` (fallen from 57,070), `ceiling_bytes` (≤ 57,070 **or** a written justification citing ADR-021 caveat 2 and naming what would have had to be cut), **and the per-path figures** — at minimum the `--product` full run and the default full run, computed by summing the skills each path's reads would issue. The evidence names the **maximal reachable path** (projected: the default full run, ~52,660), states its gap to the tool's envelope, and states explicitly that **no invocation reaches all four skills** because `--product` and the default path are mutually exclusive.
- [ ] Given Business Rule 14 forbids hoisting, when this story lands, then `grep -n 'required_skills:' commands/verify-spec.md` returns nothing; `grep -n 'Read skills/' commands/verify-spec.md` returns exactly **six** hits across **four** distinct names, each inside the phase or check row named in § Scope; **no hit sits above `## Command Process`**; and every line number is recorded in the evidence. Specifically verified: `spec-metadata-diagnosis` is unreachable on a `--product` run and `product-doc-audit` is unreachable on a default run. No tool checks this — the recorded line numbers are the check.
- [ ] Given Business Rule 3, when the disposition ledger is rebuilt by reading only `commands/verify-spec.md` and its declared skills, then it matches Story 1's ledger **cell for cell** — same twelve checks, same sub-checks, same run order, same dispositions, and the same literal `unstated in source` cells.
- [ ] Given Business Rule 4, when every `#### Check …` heading from `git show <base>:commands/verify-spec.md` is grepped against the command plus its skills, then each appears verbatim in exactly one place; and checks 1–8 and P1–P4 keep their numbers so `release.md:106`, `ship.md:335`, and `README.md:134` still resolve.
- [ ] Given Business Rule 5, when `commands/verify-spec.md` is read, then all four `require_literal` strings are present — `Cross-spec dependency validation`, `self-reference`, `story dependency validation is unchanged`, `spec-lifecycle.md` — the `forbid_literal` string `specs/**` is absent from the command **and** from every skill, and `## Product Consistency Checks (\`--product\`)` is byte-identical so `plan-product.md:39`'s fragment link still resolves.
- [ ] Given Business Rule 13, when `bash scripts/eval.sh` is run, then any `skills`-surface growth warning is answered by a bound justification recording this spec, the bytes moved into `skills`, and the corresponding `commands` reduction — and `--update-baseline` was not used.
- [ ] Given Business Rule 8, when `git diff commands/verify-spec.md` is inspected, then there is no `-` line inside the frontmatter's `problem:`, `outcome:`, `exit_criteria:`, or `loop:` block; and the `calibrated_against` citation's three assertions (Phase 2 = checks 1–8, Phase 4 = auto-fixes 4.1–4.4, Phase 5 = report file; no re-check step; the only "again" is `/release`'s separate entry point) are re-read against the new file and confirmed still true.
- [ ] Given Business Rule 7, when `python3 scripts/eval-loop-bounds.py` is run, then `verify-spec-no-recheck-step` reports PASS, and the same grep over `skills/*/SKILL.md` also returns nothing.
- [ ] Given Business Rule 10, when the phase list is read, then every skill is reached by a literal `Read skills/<name>/SKILL.md` **inside** the row whose detail it carries; no skill is unreachable; and the two skills serving both paths (`derivative-regeneration`, `verification-report-authoring`) carry **one read per path** rather than one read hoisted to their common ancestor.
- [ ] Given Business Rule 9, when `git diff --name-only` is read for this spec's whole branch, then it lists only `commands/verify-spec.md`, the new `skills/*/SKILL.md` files, `.writ/manifest.yaml`, `SKILL.md`, and this spec's own files — no other command, no `scripts/`, no `commands/_preamble.md`.
- [ ] Given the invocation surface must not change, when the `## Invocation` table is read, then all six invocations survive with their behavior text: default, `--check`, `--fix`, `--spec [path]`, `--all`, `--product` — and `adapters/claude-code.md:447`'s `/verify-spec --check` still describes a real mode.
- [ ] Given `bash scripts/eval.sh` and `bash scripts/gen-skill.sh --check`, when both are run, then there are no new findings relative to Story 1's baseline and no manifest/SKILL.md delta.

## Implementation Tasks

- [ ] 5.1 Read Story 1's ledger and baseline; read all four skills as landed (names, byte counts, and what each actually carries after compression)
- [ ] 5.2 Rewrite `commands/verify-spec.md`: copy the frontmatter unchanged — **append nothing, add no `required_skills:`** — and author the retained sections
- [ ] 5.3 Rename `## Modes` → `## Invocation`, preserving all six rows and the `--product` boundary note
- [ ] 5.4 Author `## Command Process` as the phase list — Phases 1–5 by their existing numbers, checks 1–8 by number/name/disposition under Phase 2, steps 4.1–4.4 under Phase 4, and the Iteration bound paragraph retained in place
- [ ] 5.5 Author the `## Product Consistency Checks (\`--product\`)` section: heading byte-identical, P1–P4 by number/name/disposition, skill cited
- [ ] 5.5a Place the six inline `Read skills/<name>/SKILL.md` calls inside their phase and check rows per § Scope; record all six line numbers and confirm none sits above `## Command Process`; confirm the two mode exclusions hold by reading the file, not by asserting them
- [ ] 5.6 Condense the three load-bearing `## Integration with Writ` rows into `## References`; add the four skill links as a **human-readable index, not a load**; remove the section
- [ ] 5.7 Re-read `calibrated_against` against the new phase list and confirm each of its three assertions is still true
- [ ] 5.8 Rebuild the disposition ledger from command + skills only; diff against Story 1's; record the result
- [ ] 5.9 Grep every pre-extraction check heading against command + skills; record any `LOST:` line as a blocking failure
- [ ] 5.10 Measure: `measure-invocation.py` before/after — `command_bytes`, `eager_bytes`, `eager_skills`, `floor_bytes`, `conditional_bytes`, `conditional_skills`, `ceiling_bytes`, `unresolved_skills` — plus per-skill byte counts and the Σ arithmetic; confirm no "loads both ways" warning
- [ ] 5.10a Compute the per-path report BR1 requires: for each path (floor, `--product --check` graceful skip, `--product` full, `--check`, default full), sum the skills that path's reads would issue and state the total against the pre-spec 57,070. Name the maximal reachable path and its gap to `ceiling_bytes`
- [ ] 5.11a Grep the four `require_literal` strings against `commands/verify-spec.md` and `specs/**` against the command plus all skills; record pass/fail per string before running the full eval
- [ ] 5.11b Write the `skills`-surface bound justification against `.writ/leanness-baseline.json` using Story 1's recorded figures; do not run `--update-baseline`
- [ ] 5.11 Run `eval-loop-bounds.py`, `lint-skill.sh skills/*/SKILL.md`, `gen-skill.sh --check`, `eval.sh`, `spec-deps.py validate`, and the re-check grep over command + skills
- [ ] 5.12 Verify `git diff --name-only` against Business Rule 9's allowed list, and confirm the `#product-consistency-checks---product` anchor by rendering or by exact-string match

## Notes

**Technical considerations:**

- **Four `require_literal` strings must survive in the command file, and three of them sit inside Check 4d** — the block Story 2 extracts wholesale. The Phase 2 gate row for Check 4 is their carrier: it names 4d as `Cross-spec dependency validation`, lists `self-reference` among its blocking findings, and states that `story dependency validation is unchanged`. Phase 1's `--all` row carries the `spec-lifecycle.md` link. These are not decorative; `scripts/eval.sh` fails without them and this spec may not edit it.
- The `calibrated_against` string is preserved byte-identical **and** must remain true. Those are two different obligations and only the first is mechanically checkable. Task 5.7 is the second one, and it is why the phase list keeps Phase 1–5 numbering and 4.1–4.4 sub-numbering instead of adopting cleaner names.
- The Iteration bound paragraph stays in the command deliberately. It is prose about the `loop:` declaration, it names `autofix_pass` / the bound / `halt_reported` / the resume command, and it contains the phrase "re-running Phase 2" — which is safe in the command (the guard reads only structural lines, and this is prose) and would be an unguarded liability in a skill.
- Dispositions stay in the command even though the procedures leave. A reader of the thin file must be able to predict *what gets written* without loading anything; that is the difference between a contract and a table of contents.
- **Placement is the one thing no tool checks, and it is where this story's value is.** `measure-invocation.py` sums the reads wherever they sit; `lint-skill.sh` never opens a command; `eval.sh` and `eval-loop-bounds.py` have no opinion. Six reads hoisted to the top of the file report an identical `ceiling_bytes`, pass every check in this spec, and make every run pay every skill — the eager mechanism the 2026-08-12 ruling rejected, rebuilt by hand. Task 5.5a's recorded line numbers are the entire enforcement.
- **`ceiling_bytes` is an envelope, not a path.** No invocation reaches all four skills. Task 5.10a exists because the number that answers "did disclosure work" is the per-path figure, and no tool produces it.
- **A mistyped inline read is caught by `unresolved_skills` and by nothing else.** `eval-leanness.py check_required_skills` reads `required_skills:` frontmatter only; with no declarations it reports `required_skills_declarations: 0` with no finding, which is correct by design and silent about inline reads.
- `## Modes` → `## Invocation` is safe: no file links to `verify-spec.md#modes`. Re-verify before renaming rather than trusting this note.

**Risks / challenges:**

- **The worst-path ceiling is the likely failure.** `command_bytes` will land far under 24,960; `ceiling_bytes` may not land under 57,070 if the four skills together exceed ~24,200. If they do, the correct response is the written justification (BR1), **not** trimming a check — fidelity outranks both budgets (BR2 precedence). Trading allocations between skills is legitimate; trading away a disposition is not. Note the mechanism ruling does **not** relax this bar: Σ ≤ 24,200 stays, because it is what a tool can check and a bar redrawn at the reachable path would be a bar chosen after the fact.
- **Hoisting the reads "so the reader sees the skills up front."** Both mode exclusions vanish, `--product` starts paying 11,600 bytes for the eight-check diagnostic, and every number in the evidence stays the same. This is the highest-value, lowest-visibility mistake available in this story.
- **Adding `required_skills:` back "for discoverability."** It moves all four skills into `floor_bytes`, blows the 24,960 floor bar, and inverts the spec's result. Out of Scope, by maintainer ruling.
- Removing `## Integration with Writ` is the one place where a fact other commands rely on could disappear. The `/release` row is load-bearing for the preserved `calibrated_against`; the `/ship` row is the only statement of the checks-1–3 subset from this side.
- This story rewrites a file three other commands describe as authoritative for their own behavior. It cannot edit them. Everything it can do is keep numbering and names stable.

**Integration points:**

- Consumes all four skills from Stories 2–4 and Story 1's ledger and baseline.
- `2026-08-11-governor-instrumentation` will assert `required_skills:` resolution and command length. **After the 2026-08-12 ruling this story produces no declaration for it to assert against** — `check_required_skills` has nothing to resolve here, by design, and that fact should be handed to governor-enforcement along with the observation that no check today validates an inline read's *target* or its *placement*. Command length it still asserts against.
- The `verify-spec-no-recheck-step` guard's blind spot (it cannot see skills) is recorded in the spec's Technical Concerns, is **unchanged by the mechanism ruling** — the guard does not read `skills/` at all, so how a skill loads is irrelevant to it — and should be carried forward to whichever spec next edits `scripts/eval-loop-bounds.py`.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Before/after `floor_bytes`, `ceiling_bytes`, **and** the per-path figures recorded in the evidence, with a written justification if the ceiling rose; the maximal reachable path named with its gap to the envelope
- [ ] `eager_bytes == 0`; `grep -n 'required_skills:'` returns nothing; `grep -n 'Read skills/'` returns six hits across four names, each line number recorded and matched against § Scope, none above `## Command Process`
- [ ] Both mode exclusions verified by reading the file: `spec-metadata-diagnosis` unreachable under `--product`, `product-doc-audit` unreachable on a default run
- [ ] The rebuilt disposition ledger and its diff against Story 1's are recorded in the evidence
- [ ] No check heading reported as `LOST:`
- [ ] All four `require_literal` strings present in the command; `specs/**` absent everywhere
- [ ] `eval.sh`, `eval-loop-bounds.py`, `lint-skill.sh`, `gen-skill.sh --check`, and `spec-deps.py validate` all clean relative to baseline
- [ ] The `skills`-surface bound justification is written, naming this spec and the byte movement
- [ ] `git diff --name-only` matches Business Rule 9's allowed list exactly

## Context for Agents

- **Load mechanism (READ FIRST):** inline reads at the point of need, no `required_skills:`, narrowest placement, path-dependent ceiling — from spec.md → **Approved Scope Change — Load Mechanism (2026-08-12)** and → *The thin contract's shape* / *Skills — names and allocations*
- **Business rules:** [BR1 ceiling + per-path report, BR2 floor and precedence, BR3 ledger, BR4 frozen numbering, BR5 pinned literals and the anchor, BR6 hybrid boundary, BR7 no re-check step and its unenforced skill gap, BR8 preserved `loop:`, BR9 ownership, BR10 reachability by inline read, BR13 bound justification, **BR14 placement is the mechanism**] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The thin contract's shape; `## Integration with Writ`; The byte ledger] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [The ceiling is paid every run; ADR-021 vs `new-command.md` template conflict; three files cite check numbers; the guard's new blind spot] — from spec.md → ## Technical Concerns
- **Contract:** [Deliverable and the binding budget; hardest constraint on checks, order, and dispositions] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Measurement Instrument; The Preserved `loop:` Block and the guard's exact grammar; Cross-File Reference Surface; Verification Commands] — from sub-specs/technical-spec.md
