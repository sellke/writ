# User Stories: Autonomy Gate Classes

> **Status:** In Progress — 2/3 stories, 15/23 tasks.

| Story | Title | Status | Tasks | Progress | Dependencies |
|---|---|---|---|---|---|
| 1 | [Raise the `_preamble` Cap and Prove It Still Binds](./story-1-raise-preamble-cap-with-binding-test.md) | Complete | 7 | 7/7 | None |
| 2 | [Record the Gate-Class Table and Reversibility Precondition](./story-2-gate-class-table-and-precondition.md) | Complete | 8 | 8/8 | Story 1 |
| 3 | [Verify the Precondition Is Applicable to Destructive-Class Commands](./story-3-destructive-command-applicability.md) | Not Started | 8 | 0/8 | Story 2 |

## Dependency Graph

```
Story 1 (cap + binding test)
   └── Story 2 (gate-class table + precondition in _preamble.md)
          └── Story 3 (read-only applicability check, 4 destructive commands)
```

Strictly serial, and the ordering is not incidental. **Story 1 first** because the cap is what makes Story 2's content legal — authoring first would put the branch through a state where the Tier 1 CI gate fails, and it would also destroy the evidence that the budget was set before the content was written. **Story 3 last** because it assesses the wording that actually shipped, not the draft in the technical spec.

**Suggested execution order:** 1 → 2 → 3, no parallelism available or wanted. The whole spec is `Effort: XS`; Story 3 is the only part that can meaningfully run long, and it produces prose, not code.

## File Ownership (single writer per file)

| File | Owner | Note |
|---|---|---|
| `scripts/eval.sh` lines 411-412 | Story 1 | **Only** these two lines. Line 422 (`-gt 2000`) belongs to Phase 10's `governor-enforcement` spec; line 403 (`-gt 100`) belongs to nobody here. |
| New shell test under `scripts/tests/` | Story 1 | Cap regression + adjacent-limit regressions + exemption tripwire |
| `commands/_preamble.md` | Story 2 | One section, ≤14 lines added, final file ≤95 lines |
| `commands/revert.md`, `refactor.md`, `uninstall-writ.md`, `reinstall-writ.md` | **Nobody** | Read-only inputs to Story 3 |

## Quick Links

- [spec.md](../spec.md) — locked contract, the nine business rules, detailed requirements
- [spec-lite.md](../spec-lite.md) — condensed agent-context version
- [sub-specs/technical-spec.md](../sub-specs/technical-spec.md) — verified current state of `check_length`, the line budget derivation, the fixture harness, the line-verified candidate section, the Story 3 applicability template
- [ADR-022](../../../decision-records/adr-022-autonomy-gate-classes.md) — governing decision: the five-row table, the two-condition precondition, the recorded dissent, the 2026-11-11 review trigger
- [ADR-013](../../../decision-records/adr-013-recommended-autonomous-delivery.md) — the evidence-based select-or-pause boundary this extends rather than replaces

## The Risk Worth Restating

This spec raises a limit that currently produces a **blocking** eval finding, in order to fit content underneath it. That is, mechanically, the same move that produced Phase 10's own worst governor: a 2000-line command limit against a 961-line worst offender, which can never fire. Three artifacts exist to keep this one different — a budget derived before authoring (79 + 14 + 2 = 95), a regression test proving a 96-line preamble still fails, and a ban on the `eval-exempt: length` escape hatch. If a reviewer can find where 95 came from without reading the finished `_preamble.md`, the defense held.

## The Decision Being Recorded Was Contested

ADR-022's destructive-class ruling — autonomous, subject to a reversibility precondition, rather than a human gate — was made over a recorded objection that it is a genuine safety regression, and reaffirmed by the maintainer. These stories implement it as decided. They do not present it as uncontested: the objection, the git-reversibility reasoning that makes it defensible, and the 2026-11-11 review trigger all live in the ADR, and Story 3's assessment is deliberately biased toward finding the cases where the precondition cannot actually be evaluated.
