# Story 2: Record the Gate-Class Table and Reversibility Precondition

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ command or agent deciding whether to act without asking
**I want** the five gate classes and the reversibility precondition stated once, in the file every command already loads
**So that** "maximally autonomous except where taste and agency require humans" is a rule I can apply, rather than a posture implied across 31 command files

## Acceptance Criteria

- [ ] Given `commands/_preamble.md` after this story, when it is read, then it contains an `## Autonomy Gate Classes` section with all five of ADR-022's classes — product & spec direction, production boundary, design & UX judgment, destructive/irreversible, everything else — each carrying that ADR's behavior.
- [ ] Given the destructive/irreversible row, when it is read, then it says the class is autonomous **subject to the reversibility precondition** — not a human gate, and not unconditionally autonomous.
- [ ] Given the reversibility precondition text, when it is read, then both conditions are numbered and separately checkable — (1) provably git-revertable, confined to tracked files with a resolvable revert target; (2) restore path recorded **before** the mutation — and the consequence of either failing is stated as behavior ("pauses with a bounded `AskQuestion`"), not as a suggestion.
- [ ] Given the section's wording, when it is checked for hedges, then it contains no "should", "consider", "where practical", or equivalent softening applied to the precondition or to the three human gates.
- [ ] Given the section, when its relationship to ADR-013 is read, then it states that it extends ADR-013's evidence-based select-or-pause boundary rather than replacing it.
- [ ] Given `wc -l commands/_preamble.md` after this story, then the count is **≤ 95**, and the section added is **≤ 14 lines** including its leading blank separator.
- [ ] Given `bash scripts/eval.sh --check=length`, when it runs against the real repository, then it exits 0; and given a full `bash scripts/eval.sh` run, then it produces no new findings relative to the pre-spec baseline.
- [ ] Given the section, when it is compared against ADR-022, then it carries none of the ADR's reasoning, recorded dissent, or review trigger — the preamble states the rule; the ADR keeps the argument.

## Implementation Tasks

- [ ] 2.1 Read [ADR-022](../../../decision-records/adr-022-autonomy-gate-classes.md) in full — the Decision table, the reversibility precondition, and the "why the three retained gates are retained" reasoning. The table must be faithful in meaning; compression is a wording exercise, not an editorial one.
- [ ] 2.2 Confirm Story 1 has landed: `grep -n 'gt 95' scripts/eval.sh` returns the `_preamble` branch. Authoring before the cap moves puts the branch through a failing CI gate.
- [ ] 2.3 Draft the section against the 14-line budget, using `sub-specs/technical-spec.md` → "Candidate content" as a line-verified starting point. Count lines before pasting, not after.
- [ ] 2.4 Insert it after the `User Challenge (Scope-Degradation Escalation)` section and before `## File Organization` — adjacent to where ADR-013's select-or-pause boundary is already stated.
- [ ] 2.5 Verify the length budget: `wc -l commands/_preamble.md` ≤ 95 and the diff adds ≤ 14 lines. If over, cut prose — compress the precondition to a single line, tighten the table's behavior cells — and do **not** revisit the cap (Business Rule 1).
- [ ] 2.6 Wording pass against the normative requirements: "only when both hold", "pauses", numbered conditions, emphasis on "before". Remove any hedge that crept in during compression.
- [ ] 2.7 Run `bash scripts/eval.sh --check=length` (exit 0) and the full `bash scripts/eval.sh`, comparing findings against the pre-spec baseline — no new findings, including `check_preamble` and `check_autonomy_governance`, both of which read this file.
- [ ] 2.8 Confirm no `eval-exempt:` marker was added to `commands/_preamble.md` at any point.

## Notes

**Technical considerations:**

- Every line here is paid on every command invocation across all 31 commands. That is the entire reason for the 14-line budget and for keeping ADR-022's reasoning out of the file. If the section reads as slightly terse, it is correctly sized.
- Placement is load-bearing for comprehension, not just tidiness. The `User Challenge` section already states ADR-013's boundary; the gate classes are the classification that boundary applies to. Separated by three unrelated sections, the table reads as freestanding policy.
- One long unwrapped line for the precondition is acceptable — `Artifact Integrity` (lines 58-62) already does this. Wrapping to three lines spends the entire 2-line reserve, which is legal but leaves nothing for a later correction.
- `scripts/eval.sh` has other checks that read `_preamble.md` (`check_preamble` for reference integrity, `check_autonomy_governance` for policy-surface consistency). Run the full suite, not just `--check=length`.
- Cite ADR-013 by name in the section — it is already named elsewhere in the file, so this adds no new vocabulary.

**Risks / challenges:**

- **Compression that changes meaning.** Squeezing "Autonomous, subject to a reversibility precondition" into "Autonomous*" with a footnote marker saves a line and loses the rule. The five behaviors must survive compression intact; cut adjectives, not conditions.
- **Hedging under review pressure.** The destructive-class decision is contested (see Business Rule 7), and the natural instinct when writing a contested rule is to soften it — "should generally pause". That produces the worst of both: no human gate *and* no enforceable precondition. Write it as decided, and let ADR-022 carry the objection.
- **Budget overrun.** Fourteen lines is tight if the table's behavior cells are written conversationally. The technical spec's candidate content fits; deviating from it is fine, exceeding the budget is not.
- **Scope drift into command files.** It is tempting, while writing the precondition, to also add it to `/revert` or `/refactor`. Business Rule 9 forbids it — that is Story 3's read-only observation and, if warranted, a separate issue.

**Integration points:**

- Depends on Story 1's cap. Blocks Story 3, which has nothing to check applicability of until this wording exists.
- Consumed by every command via the existing `_preamble.md` reference convention — no wiring, no adapter change, no new mechanism.
- `check_autonomy_governance` in `scripts/eval.sh` asserts policy-surface consistency across `system-instructions.md`, `cursor/writ.mdc`, and `_preamble.md`. Nothing here should trip it, since ADR-013's constraints are unchanged — but verify rather than assume.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (14-line section budget; cut prose rather than raise the cap), Rule 5 (precondition stated as an enforceable rule, not advice), Rule 6 (extends ADR-013, never weakens it), Rule 7 (the dissent stays recorded — in the ADR, not softened in the preamble), Rule 8 (table faithful to ADR-022), Rule 9 (no command files change)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The gate-class section in `commands/_preamble.md`; The reversibility precondition] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [This content is paid on every invocation; the precondition is prose, not enforcement] — from spec.md → ## Technical Concerns
- **Contract:** [Must include: destructive class ships as autonomous-with-precondition per the maintainer's reaffirmed decision; both conditions stated as an enforceable rule, not advice] — from spec.md → ## Contract (Locked)
- **Technical detail:** [Placement, line-verified candidate content, normative wording requirements, what must not appear] — from sub-specs/technical-spec.md → ## Story 2
- **Governing ADR:** [`.writ/decision-records/adr-022-autonomy-gate-classes.md`] — the five-row table, the two-condition precondition, the recorded dissent, the 2026-11-11 review trigger
