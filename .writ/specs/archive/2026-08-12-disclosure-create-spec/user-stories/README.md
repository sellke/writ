# User Stories: Progressive Disclosure — `/create-spec`

> **Status:** Not Started — 0/6 stories, 0/42 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Namespace Reconciliation and the `requirements-discovery` Skill](./story-1-requirements-discovery-skill.md) | Not Started | 7 | 0/7 | None |
| 2 | [Author the `contract-lock` Skill](./story-2-contract-lock-skill.md) | Not Started | 7 | 0/7 | Story 1 |
| 3 | [Author the `spec-package-authoring` Skill](./story-3-spec-package-authoring-skill.md) | Not Started | 7 | 0/7 | Story 1 |
| 4 | [Author the `user-story-decomposition` Skill](./story-4-user-story-decomposition-skill.md) | Not Started | 7 | 0/7 | Story 1 |
| 5 | [Author the `spec-source-prepopulation` Skill](./story-5-source-mode-prepopulation-skill.md) | Not Started | 7 | 0/7 | Story 1 |
| 6 | [The Thin Command, the Budget, and the No-Drift Proof](./story-6-thin-contract-and-budget.md) | Not Started | 7 | 0/7 | Stories 1–5 |

## Dependency Graph

```
Story 1 (namespace reconciliation for all five names + requirements-discovery)
   ├── Story 2 (contract-lock — ADR-001 spine)          ─┐
   ├── Story 3 (spec-package-authoring — most pins)      ├── parallel, disjoint skill dirs
   ├── Story 4 (user-story-decomposition — orch. split)  │
   └── Story 5 (spec-source-prepopulation — most compression) ─┘
          └── Story 6 (thin command, budget, no-drift proof) — after all five
```

**Story 1 is a hard prerequisite for everything.** `skills/` is a shared namespace across six Phase 10 specs plus six incumbent skills. Story 1 reads the pilot's convention from `.writ/docs/skills.md` → *Extraction Patterns* and runs the collision protocol — name **and head noun** — for all five names at once. Four sibling stories racing their own protocols against each other and against the pilot's eight names is the failure that produces near-duplicate skills.

**Stories 2–5 are additive and mutually independent.** Each authors one skill under its own `skills/<name>/` directory and touches nothing in `commands/`. The command keeps its prose while they run, so the tree is green and runnable throughout and each story reverts independently. They parallelize cleanly.

**Story 6 is the only writer on `commands/create-spec.md`.** It deletes the relocated prose, places one inline `Read skills/<name>/SKILL.md` per skill at the step that needs it (no `required_skills:` — maintainer ruling 2026-08-12), rebuilds the thin contract, and produces the proof. Nothing is ever duplicated between the command and a skill in a *landed* state: the duplication window is exactly the interval between Stories 2–5 and Story 6, which is why Story 6 is a hard successor rather than five incremental rewires.

**Shared-file note.** All five extraction stories append to `.writ/manifest.yaml`'s `skills:` block and regenerate the root `SKILL.md`. `/new-skill` appends alphabetically and `gen-skill.sh` regenerates deterministically, so a parallel conflict is textual, not semantic — the last to land re-runs `bash scripts/gen-skill.sh` and confirms `--check` passes. `2026-08-11-retire-dead-prescription` also edits that file (`version:` and the `commands:` list) and the pilot appends eight `skills:` entries; the keys are disjoint, but sequence them anyway.

## Task Count

42 tasks across 6 stories. Seven per extraction story (reconcile → measure → `/new-skill` → author → compress → verify → check off) and seven in Story 6 (delete + declare → invocation table and phase list → references → measure → reconcile 113 rows → frozen-region diffs → full verification and evidence).

## Quick Links

- [spec.md](../spec.md) — locked contract, inherited convention, the two bars, the eval-pin finding, 13 business rules
- [spec-lite.md](../spec-lite.md) — condensed agent context
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — measurement protocol, Compression Ledger, the 113-row rule inventory, naming and collision protocol, verification commands, error & rescue map
- [ADR-021](../../../decision-records/adr-021-progressive-disclosure-token-budget.md) — the governing decision, including caveat 2
- [ADR-013](../../../decision-records/adr-013-recommended-autonomous-delivery.md) — the `--recommend` evidence boundary
- [ADR-009](../../../decision-records/adr-009-command-agent-skill-boundary.md) — command / agent / skill boundary, enforced by `lint-skill.sh`
- [`2026-08-12-disclosure-implement-story`](../../2026-08-12-disclosure-implement-story/spec.md) — the pilot whose convention this spec inherits

## Contradictions Found at Spec Time (2026-08-12)

**1. The `--recommend` block cannot be extracted, and should not be.**

The work was scoped with a sketch naming *"the `--recommend` evidence flow"* as a skill. `scripts/eval.sh` asserts **nineteen literal strings** against `commands/create-spec.md` (17 `require_literal`, 2 `forbid_literal`, at `eval.sh:1644–1973`), and `check_recommended_spec_implementation` (`eval.sh:737–800`) runs an inline Python scenario that reads the file, **parses the markdown table** under `### Authoritative \`--recommend\` Invocation Matrix` row by row, asserts each of eight rows begins with `Supported` or `Reject`, and asserts three ordering relations between headings — including one that fails outright if `### Autonomous Authoring Boundary` is absent. Verified 2026-08-12 by `grep -n '_literal "\$create_spec"' scripts/eval.sh` and by reading the scenario.

This spec may not edit `scripts/eval.sh` — `governor-enforcement` owns it. So `## Recommended Mode` (lines 31–99, 4,130 B) stays whole. Only ~1,414 of its bytes are not directly pinned, and relocating that behind ~650 bytes of skill scaffolding plus an indirection would trade a real ADR-013 boundary for a section-list win. The locked contract's hardest constraint points the same way. **`## Required Artifacts` is retained for the same class of reason** (`scripts/eval-artifact-integrity.py:27`). Both are recorded deviations from ADR-021 point 1 and are re-stated in Story 6's evidence.

**2. The load mechanism changed on 2026-08-12. `required_skills:` is not used.**

Two drafts of this spec argued about `required_skills:` — one proposed a curated subset, the other (inheriting pilot BR8) declared all five. **A maintainer ruling on 2026-08-12 settled it by rejecting the field entirely**, and both drafts are superseded.

The finding both this spec and its sibling `disclosure-verify-spec` reached independently — that `required_skills:` is an **unconditional pre-load** — is verified and accepted. `system-instructions.md` § *Harness contract* loads every declared skill *"before any phase work begins"*; `adapters/claude-code.md:396` says the same. ADR-021 §12's "loaded on demand" is false of it.

**Ruling: inline `Read skills/<name>/SKILL.md` at the point of need.** That form is genuinely conditional — the agent issues the call only if execution reaches the step — and it is already the shipping pattern in seven commands, this one at line 765 among them. Under the eager mechanism the extracted bytes reappear in the floor plus ~650 bytes of scaffolding per skill, so extraction is byte-neutral at best; that is why this spec's ceiling missed by ~3,227 bytes and the sibling's needed 27% compression just to break even.

**What did not change:** the extraction map, the five names, the nineteen pins, the 113-row inventory, the Compression Ledger, the 24,960-byte budget. What did: no declaration; each read placed at the **narrowest** step (the inherited declare-all rule is **reversed** — right under eager loading, backwards under conditional, where placement *is* the mechanism); the ceiling reported path-dependently; and `scripts/measure-invocation.py` re-run after its own fix (`e8f2a09`). Corrected pre-spec baseline: **floor 71,383, ceiling 77,530** — the ceiling now includes the 6,147-byte inline `error-rescue-mapping` read, which is precisely the number this spec had computed by hand.

The hardest constraint is still met mechanically, by **ordering** rather than eagerness: `contract-lock` is read at Step 1.3b, strictly before the Step 1.4b gate and the `--recommend` auto-lock, so no path reaches the lock without it. That guarantee is stronger in principle and more fragile in practice — it holds exactly as long as that read stays above that gate.

**3. `error-rescue-mapping` is already extracted, stays inline, and is not promoted — and the ruling strengthens this.**

`commands/create-spec.md:765` already reads it, and that skill's `status_evidence` records `create-spec` as its one consumer. It is not re-extracted (Business Rule 12) and not declared. Under the fixed tool that is a measurement rather than an argument: a declaration moves 6,147 bytes from `conditional_bytes` into `floor_bytes`, and a documentation-only run — where the data-flow heuristic says *skip* — pays them for nothing. **Left inline, a docs-only run genuinely never pays them: its ceiling equals its floor.** It is no longer an exception to the spec's pattern; it is the worked example of it, shipping in this file since Phase 7.

**4. Preserved inconsistencies, deliberately unfixed.** Step 2.5 and `## Completion` say "5-7 implementation tasks"; the frontmatter `exit_criteria` says "no more than 7". Business Rule 2 forbids fixing a threshold during a relocation — recorded in Story 4's notes, not resolved. Separately, `--from-issue` is documented at line 175 but absent from `## Invocation`; Story 6 adds the row as documentation completion, since the mode is already named in the `--recommend` matrix.

## Anti-Goals (apply to every story)

**A file that hits 24,960 bytes by deleting rules instead of relocating them.** That state passes the byte budget, the line tripwire, all nineteen eval pins, the matrix scenario, and `lint-skill.sh` — every automated check this phase has. The 113-row rule inventory in `sub-specs/technical-spec.md` is the only defense, and it must be reconciled row by row in both directions, not sampled.

**A worst-path ceiling cleared by deleting an inline read instead of compressing.** The number improves, the procedure becomes unreachable, and a skill nobody loads is dead weight that made the surface worse (Business Rule 7). If the ceiling does not clear after the Compression Ledger's measured yields, the honest outcome is ADR-021's tracked exemption with numbers attached — not a missing read and not a skill trimmed below the rules it must carry.

**A thin command whose six inline reads all sit near the top of the file.** Every automated check passes: `floor_bytes`, `ceiling_bytes`, the eval pins, the lint, the rule inventory. And every run pays every skill, because the reads are hoisted above the branches that decide whether they are needed — the eager mechanism the 2026-08-12 ruling rejected, rebuilt by hand. **No tool checks placement.** Story 6 verifies it by reading `grep -n 'Read skills/'` line numbers against spec.md § *Load placement*, and that check is the only enforcement the spec has.
