# User Stories: Progressive Disclosure — `/verify-spec`

> **Status:** Not Started — 0/5 stories, 0/54 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Baseline Measurement and the Disposition Ledger](./story-1-baseline-and-disposition-ledger.md) | Not Started | 11 | 0/11 | None |
| 2 | [The Eight-Check Diagnostic as a Skill](./story-2-spec-metadata-diagnosis-skill.md) | Not Started | 11 | 0/11 | Story 1 |
| 3 | [The `--product` Check Set and the Shared Regeneration Discipline](./story-3-product-checks-and-regeneration-skills.md) | Not Started | 9 | 0/9 | Story 1 |
| 4 | [One Report Shape, Three Instantiations](./story-4-verification-report-authoring-skill.md) | Not Started | 9 | 0/9 | Story 1 |
| 5 | [The Thin Contract, the Budget, and the Drift Proof](./story-5-thin-contract-and-budget-proof.md) | Not Started | 14 | 0/14 | Stories 2, 3, 4 |

## Dependency Graph

```
Story 1 (baseline measurement + disposition ledger + pinned-literal
         inventory + namespace collision check)
   ├── Story 2 (spec-metadata-diagnosis — checks 1-8 + repairs 4.1-4.3)  ─┐
   ├── Story 3 (product-doc-audit + derivative-regeneration)        ├── parallel
   └── Story 4 (verification-report-authoring)                              ─┘
          └── Story 5 (thin commands/verify-spec.md + required_skills:
                        + before/after floor AND ceiling + ledger diff)
```

**Story 1 is a hard prerequisite.** Stories 2–4 author against its disposition ledger, and Story 5's entire pass condition is a diff against it. Starting an extraction before the ledger exists means the only record of what the command did is the file being rewritten. Story 1 also builds the pinned-literal inventory — three of those four strings live inside Check 4d, so discovering them in Story 5 means re-authoring both a skill and the command.

**Stories 2–4 are mutually independent** — each creates only its own `skills/<name>/` directory. The one shared write is `.writ/manifest.yaml`, appended once per skill by `/new-skill`; Story 1 records the pre-existing `skills:` block and Story 5 runs `gen-skill.sh --check` as the reconciliation, so a lost entry surfaces rather than disappearing.

**Story 5 is sequenced last** because an inline `Read skills/<name>/SKILL.md` cannot point at a skill that does not exist yet — an unresolved name makes `measure-invocation.py` report the ceiling as a lower bound, which would invalidate the one number this spec exists to produce. (Amended 2026-08-12: this held for `required_skills:` and holds identically for inline reads. Note the detector differs — `eval-leanness.py check_required_skills` reads frontmatter only and is blind to a mistyped inline read; `unresolved_skills` is the only backstop.)

**Suggested execution order:** Story 1 alone. Then Stories 2, 3, 4 in parallel. Then Story 5.

## Task Count

54 tasks across 5 stories. Story 5 carries 14 — the largest count for the smallest amount of authoring — because the measurement, the ledger rebuild, the heading-survival grep, the citation re-read, and the six tool runs are all *its* evidence, not the skill stories'.

## Quick Links

- [spec.md](../spec.md) — locked contract, the two budgets, business rules, the ceiling finding
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — byte ledger, disposition ledger, the loop guard's exact grammar, cross-file reference surface, verification commands
- [ADR-021](../../../decision-records/adr-021-progressive-disclosure-token-budget.md) — the governing decision
- [ADR-020](../../../decision-records/adr-020-component-contract.md) — the frontmatter contract being preserved
- [ADR-009](../../../decision-records/adr-009-command-agent-skill-boundary.md) — why skills are capabilities, not workflows

## Findings at Spec Time (2026-08-12)

Four things were measured during authoring that change how this spec should be read.

**1. The framing this spec was commissioned under was wrong on one number.** The 22.3% cut is correct; *"the smallest of the six"* is not. Measured against this working tree: `implement-story` 52.6%, `create-spec` 46.2%, **`verify-spec` 22.3%**, `implement-phase` 14.3%, `release` 12.7%, `ship` 12.0%. `verify-spec` needs the **third-largest** cut. The reason it is still the best achievability test survives, restated honestly: it is the first of the six whose file is almost entirely irreducible substance — a check catalogue rather than a narrative pipeline.

**2. The floor budget is not the hard part; the ceiling is — and the load mechanism changed on 2026-08-12.** Only 4,324 of the file's 32,110 bytes are content ADR-021 permits the thin contract to keep, so the command lands near 7,900 — 68% under the 24,960 cap.

This spec found that `required_skills:` has no conditional form (`system-instructions.md`: the harness loads every declared skill *"before any phase work begins"*; `adapters/claude-code.md:396` agrees), so a `--product` run would pay for the spec-check skill and a default run for the product skill. **That finding is verified and accepted, and the maintainer's response was to change the mechanism rather than the budget:** `required_skills:` is not used. Each skill is reached by an inline `Read skills/<name>/SKILL.md` at the step that needs it — the standing alternative `system-instructions.md:250` documents, genuinely conditional, and already shipping in seven commands. `measure-invocation.py` was fixed the same day (`e8f2a09`) to model both mechanisms; re-measured, this command's pre-spec ceiling equals its floor at **57,070**, since it has no inline read today.

Business Rule 1's arithmetic is **unchanged**: `command_bytes + Σ(skill bytes) ≤ 32,110` — **the sum of the parts may not exceed the whole** — and it still forces roughly 27% genuine compression. What changed is what that number means and what else must be reported. `ceiling_bytes` is now an **envelope**: the tool sums every inline read and cannot know that `--product` and the default path are mutually exclusive. **No invocation reaches all four skills.** `spec-metadata-diagnosis` (≤ 11,600) is never read under `--product`; `product-doc-audit` (≤ 4,400) is never read on a default run. The maximal *reachable* path — the default full run, ~52,660 — sits ~4,400 bytes below the envelope, and that gap is this command's real per-invocation saving. Under the eager mechanism it did not exist: every run paid all four. Business Rule 1 now requires floor, worst-path ceiling, **and** the per-path figures; Business Rule 14 is new and says why placement is what produces them.

**3. `scripts/eval.sh` pins five literal strings inside `commands/verify-spec.md`, and four of them live in text this extraction was going to move.** `check_spec_dependencies` (`:1781-1783`) requires `Cross-spec dependency validation`, `self-reference`, and `story dependency validation is unchanged` — all three inside **Check 4d**, the densest extraction target in the file. `check_spec_lifecycle_docs` (`:1901`) requires `spec-lifecycle.md`, which appears only in Phase 1's `--all` prose. The same function forbids `specs/**` (`:1902`). `require_literal` tests the **command file**, never the command plus its skills, so a clean relocation produces four blocking eval findings — and `scripts/eval.sh` is out of scope to change. This was found by reading the harness, not by running it; nothing in the spec's framing predicted it. Business Rule 5 pins all six strings with their minimum retained carrier.

**4. Three files cite this command's check numbers and one deep-links a section anchor, and none of them is in scope.** `release.md:106` (checks 1–6, *"same logic as the standalone command"*), `ship.md:335` (checks 1–3, *"definitions identical"*), `README.md:134` (checks 1–8), and `plan-product.md:39` (`verify-spec.md#product-consistency-checks---product`). `scripts/eval.sh check_broken_refs` resolves the path and never the fragment, so deleting the `## Product Consistency Checks (\`--product\`)` heading would break that link **silently and permanently**. Business Rules 4 and 5 exist because the repair is an edit this spec may not make. Note the failure asymmetry: the four pinned strings fail **loudly**, the heading fails **silently**.

**5. `commands/migrate.md:323` already says "checks 1–7".** Check 8 landed and that line was never updated — a pre-existing defect discovered while verifying the citation surface, deliberately **not fixed** (Business Rule 9). It is recorded here because it is the concrete evidence for why Business Rule 4 is a hard rule rather than a preference: cross-file citations of this command's internals go stale silently and stay stale across releases.

## Two Conflicts Recorded, Neither Resolved Here

**ADR-021's retained-section list and `commands/new-command.md`'s generated-command structure table disagree.** ADR-021 permits frontmatter, `## Overview`, `## Invocation`, the phase list, `## Completion`, `## References`. The authoring template also mandates `## Integration with Writ`. A command authored to ADR-021 will not match the template new commands are generated from. **This spec follows ADR-021** — it is the decision being implemented — removes the section, and condenses its three load-bearing rows into `## References`. Reconciling the template is not this spec's authority and belongs with whichever Phase 10 spec next edits `new-command.md`. Flagged so the remaining disclosure specs do not re-litigate it three more times.

**`scripts/eval-loop-bounds.py`'s `verify-spec-no-recheck-step` guard develops a blind spot the moment this spec lands, and the 2026-08-12 mechanism ruling does not close it.** It scans `commands/verify-spec.md`'s structural lines for `re-?(check|verify|run)` and never reads `skills/`. After extraction, most of the procedure lives where the guard cannot see it, so a re-check step relocated into a skill would change the loop's shape *and pass*. Business Rule 7 extends the prohibition to skills by contract; nothing enforces it. Extending the guard is a `scripts/` change and out of scope (Business Rule 9).

The ruling is neutral here, and precisely so: the guard does not read `skills/` **at all**, so it is indifferent to whether a skill arrives via `required_skills:` or via an inline `Read`. **This is an accepted reduction in enforcement coverage, unchanged by the ruling, and the governor-enforcement work should still be told.** The hand-run grep over command + skills (`sub-specs/technical-spec.md` § *Verification Commands* step 4) is the only substitute this spec has.

## Anti-Goal (applies to every story)

The failure mode is not an incomplete extraction. It is a **smaller file that no longer says what each check auto-fixes versus reports** — a `/verify-spec` that still runs eight checks but has quietly lost that 4a–4c are report-only, that 4d blocks except on duplicates, that Check 8 never backfills without approval, or that P1 and P2 surface authoritative divergence for a human rather than rewriting it. That outcome passes every byte measurement in this spec and destroys the command.

The related failure is subtler and more likely: **resolving an ambiguity while relocating it.** Check 1 has no stated disposition. An extractor who supplies one has improved the file and broken the contract, and every downstream reader will treat the invention as the original. Business Rule 3's ledger, with its literal `unstated in source` cells, is the only defense — and it is a diff someone has to actually run.
