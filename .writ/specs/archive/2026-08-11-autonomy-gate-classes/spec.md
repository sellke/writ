# Spec: Autonomy Gate Classes

> **Status:** Complete
> **Owner:** @AdamSellke
> **Created:** 2026-08-11
> **Dependencies:** []
> **Origin:** `/plan-product` Phase 10 discovery (2026-08-11). The maintainer was asked directly which decision classes must retain a human, selected three (product & spec direction, production boundary, design & UX judgment), and deliberately did not select destructive/irreversible operations. A concern was raised that this is a safety regression; the choice was reaffirmed. Both the decision and the objection are recorded in [ADR-022](../../decision-records/adr-022-autonomy-gate-classes.md). This spec is the Phase 10 roadmap feature "Autonomy boundary" (`Effort: XS`) — the recording of that ADR into the file every command loads.

## Contract (Locked)

**Deliverable:** ADR-022's five-row gate-class table plus the reversibility precondition, recorded in `commands/_preamble.md`, and the `check_length` `_preamble` cap raised 80 → 95.

**Must include:** The destructive class ships as **autonomous-with-precondition**, per the maintainer's reaffirmed decision — ADR-022 records the dissent and the git-reversibility reasoning that makes it defensible. The precondition's two conditions (provably git-revertable; restore path recorded *before* the mutation) are stated as an enforceable rule, not advice.

**Hardest constraint:** `commands/_preamble.md` is **79 lines against a hard 80-line cap** that produces a *blocking* eval finding. The table must land within 95 total while keeping the cap binding. This spec owns **only** the `_preamble` length constant in `scripts/eval.sh` (`check_length`, ~line 411); the *command* limit twelve lines below it belongs to the later `governor-enforcement` spec — that split is what preserves single-writer-per-file across the phase.

## Why This Exists

ADR-013 established *how* Writ decides whether to act alone: evidence-based select-or-pause, with a human-owned production boundary. It never enumerated *which classes of decision* are categorically off-limits versus merely conditioned on evidence. Phase 10's posture — "maximally autonomous except where taste and agency require humans" — cannot be stated, let alone checked, without that enumeration. Today the three retained gates are implied across 31 command files and stated nowhere.

ADR-022 supplies the enumeration. This spec is the recording step, and it is deliberately small: `commands/_preamble.md` is loaded by every command, so every line added is paid on every invocation. The whole deliverable is one table, one precondition paragraph, and a two-line constant change in `scripts/eval.sh`.

The interesting part is the constant. `commands/_preamble.md` is 79 lines against a hard 80-line limit enforced at `scripts/eval.sh:411` — and unlike the leanness growth signals, this one is a **finding**, not a warning: it fails the run. The content does not fit, so the cap has to move. **Raising a cap to fit content is exactly how caps stop binding.** Phase 10's own roadmap documents where that ends: the command-file limit sits at 2000 lines against a worst offender of 961, so it can never fire, and four unjustified-growth warnings have been live and ignored. This spec must not add a fifth dead governor.

The defense is procedural, not rhetorical. The new number is derived from a **stated line budget** (79 existing + 14 for the new section + 2 reserve = 95) rather than measured off whatever the finished content happens to weigh; a regression test proves a 96-line `_preamble.md` still produces a blocking finding; and adding a length exemption to the file is forbidden, because an exemption removes the cap instead of resizing it.

The other half of the reason this spec is scoped so tightly: `scripts/eval.sh` `check_length` also holds the command-file limit (line 422) that Phase 10's "Make the governor bite" feature will take 2000 → 400. Two specs editing adjacent lines of the same function is a merge conflict waiting to happen and, worse, an ownership question nobody can answer at review time. This spec owns the `_preamble` constant and nothing else in that function.

## 📋 Business Rules

1. **The cap number comes from a stated budget, not from the content's measured length.** The new limit is derived before authoring: 79 lines currently in `_preamble.md`, plus a **14-line budget** for the gate-class section, plus **2 lines of reserve**, equals 95. If the authored section does not fit in 14 lines, prose is cut — from the new section or from elsewhere in `_preamble.md` — and the cap is **not** raised a second time. A cap chosen after the fact to accommodate whatever was written is not a cap.
2. **The cap must still bind, and that must be proven.** A regression test asserts that a `commands/_preamble.md` of 96 lines produces a blocking finding and a non-zero exit from `bash scripts/eval.sh --check=length`, and that 95 lines passes. Without this test the change is indistinguishable from deleting the check.
3. **This spec owns exactly one constant in `check_length`.** The `_preamble` test and its finding message (`scripts/eval.sh:411-412`) are in scope. The command-file limit (`-gt 2000`, line 422) and the `spec-lite.md` limit (`-gt 100`, line 403) are **out of scope and must not be touched** — the command limit belongs to the Phase 10 `governor-enforcement` work. A diff of `scripts/eval.sh` from this spec that touches any line outside 411-412 fails review.
4. **No exemption, ever.** `commands/_preamble.md` must not gain an `eval-exempt:` marker for `length`. `file_has_exemption` short-circuits the check entirely; using it here would convert a resized cap into no cap, silently, and no test would notice.
5. **The precondition is stated as a rule, not as advice.** Both conditions must hold for a destructive-class operation to run unattended: (a) the effect is **provably git-revertable** — confined to tracked files with a resolvable revert target; (b) the **restore path is recorded before the mutation**, not after. If either fails, the operation **pauses** with a bounded `AskQuestion`. The wording in `_preamble.md` is normative ("only when both hold", "pauses") — never "should", "consider", or "prefer".
6. **This extends ADR-013; it does not replace it.** The "Destructive / irreversible" and "Everything else" rows both resolve into ADR-013's evidence-based select-or-pause boundary. Nothing added to `_preamble.md` may weaken ADR-013's standing constraints — no autonomous merge, PR, release, or tag; durable audit rationale for automatic choices; resumable persisted state; required checks never bypassed. The preamble already carries those in its `User Challenge` section; the new section sits alongside them and cites the same ADR.
7. **The dissent stays recorded.** The destructive-class decision was made over a recorded objection that removing the human gate is a genuine safety regression, and it was reaffirmed rather than re-argued. No artifact produced by this spec may present that decision as uncontested or as merely obvious. `_preamble.md` states the rule; the ADR carries the objection, the git-reversibility reasoning, and the **2026-11-11 review trigger** under which a single manual recovery beyond `git revert` reverses the decision.
8. **The table is faithful to ADR-022.** Five rows, the same five class names, the same behavior for each. Wording may be compressed to fit the line budget; meaning may not change, and no sixth class may be invented at authoring time.
9. **No command files change in this spec.** `commands/revert.md`, `commands/refactor.md`, `commands/uninstall-writ.md`, and `commands/reinstall-writ.md` are **read-only inputs**. Story 3 is a verification pass; anything it finds is recorded as a written finding and, if it warrants action, filed via `/create-issue` — it is not fixed here. This keeps the spec at its `Effort: XS` size and avoids colliding with other Phase 10 specs.

## Detailed Requirements

### The `_preamble.md` line budget

| Component | Lines |
|---|---|
| `commands/_preamble.md` as it stands today | 79 |
| Budget for the new `## Autonomy Gate Classes` section | 14 |
| Reserve (absorbs a future one-line correction without a second cap change) | 2 |
| **New `check_length` limit** | **95** |

The 14-line section budget covers: a blank separator, the heading, one line stating the ADR-013 relationship, the table's header plus separator plus five rows, a blank, and the precondition. Compressing the precondition onto one long line is acceptable — `_preamble.md`'s `Artifact Integrity` section already uses long unwrapped lines, so this is existing house style, not a new one.

### The gate-class section in `commands/_preamble.md`

A new `## Autonomy Gate Classes` section carrying ADR-022's five rows verbatim in meaning:

| Class | Behavior |
|---|---|
| Product & spec direction | Human gate — contract lock stays an explicit human action |
| Production boundary (merge / PR / release / tag) | Human gate — already a Prime Directive hard constraint |
| Design & UX judgment | Human gate — taste is not evidence-decidable |
| Destructive / irreversible | Autonomous, subject to the reversibility precondition |
| Everything else | Autonomous within ADR-013's evidence boundary, with audit rationale |

Placement is a judgment call for the implementer, with one constraint: it must sit adjacent to the `User Challenge (Scope-Degradation Escalation)` section, which is where ADR-013's select-or-pause boundary is already stated. The two are one idea split across a mechanism and a classification; separating them across the file makes the classification look freestanding.

### The reversibility precondition

Stated immediately below the table, in normative language, naming both conditions and the consequence of either failing:

> A destructive-class operation runs unattended **only when both hold**: (1) its effect is provably git-revertable — confined to tracked files with a resolvable revert target; (2) the restore path is recorded **before** the mutation, not after. If either fails, **pause** with a bounded `AskQuestion`, exactly as ADR-013 requires for material irreversible risk.

The two conditions must be individually checkable by a command author reading them. "Provably git-revertable" fails on untracked files, uncommitted working-tree changes, operations reaching outside the repository, and any operation without a resolvable revert target. "Recorded before" means the restore path is written down while the pre-mutation state still exists — a path recorded after the mutation is not a restore path, it is a description of a loss.

### The `check_length` constant change

`scripts/eval.sh` lines 411-412 only:

```bash
    if [ "$count" -gt 95 ]; then
      add_finding "commands/_preamble.md" "$count lines (limit 95)." "Move command-specific detail out of the shared preamble."
```

Both the test and the message string change together — a message that still says "limit 80" while the test reads 95 is a lie the next reader has to debug. Nothing else in `check_length` moves.

### The regression test

`scripts/eval.sh` derives `PROJECT_ROOT` from its own location (`scripts/eval.sh:13`), so the check can be exercised against a fixture tree by copying the script into a temporary `scripts/` directory alongside a synthetic `commands/_preamble.md`. Verified working during spec authoring: a 96-line fixture preamble exits 1 with `` `commands/_preamble.md`: 96 lines (limit 80). ``; an 80-line fixture exits 0. Post-change the same harness must show 95 → exit 0 and 96 → exit 1 with a `limit 95` finding.

### Applicability of the precondition to the destructive-class commands

A read-only pass over the four commands ADR-022 names as destructive-class (`/revert`, `/refactor`, `/uninstall-writ`, `/reinstall-writ`), answering one question each: **can an agent reading `_preamble.md` actually evaluate both conditions before invoking this command?** The answer is recorded in the story file as evidence, whether it is yes or no. `/revert` already has a dirty-tree HALT guard (`commands/revert.md:56-62`) that is condition (1) in all but name; `/uninstall-writ` deletes platform files that in a target project may be untracked or gitignored, which is the case the precondition is supposed to catch. Neither observation causes an edit in this spec.

## Implementation Approach

1. **Story 1 — cap and its proof.** Raise the constant, add the regression test in the same story so the resize and the evidence that it still binds land together. Nothing else in `check_length` is touched.
2. **Story 2 — the content.** Author the section into `_preamble.md` within the 14-line budget. Depends on Story 1: authoring first would put the repo through a state where `bash scripts/eval.sh` fails on `main`-bound work.
3. **Story 3 — applicability.** Read the four destructive-class commands, record whether both conditions are evaluable for each. Depends on Story 2 (there is nothing to check applicability *of* until the wording exists). Read-only.

## Success Criteria

1. `bash scripts/eval.sh --check=length` exits 0 with `commands/_preamble.md` at 95 lines or fewer.
2. A fixture `commands/_preamble.md` of 96 lines produces a blocking finding reading `96 lines (limit 95).` and a non-zero exit; a 95-line fixture exits 0.
3. `git diff scripts/eval.sh` for this spec touches only the two `_preamble` lines — the `-gt 2000` and `-gt 100` limits are byte-identical.
4. `commands/_preamble.md` contains all five class names with ADR-022's behavior for each, and both precondition conditions in normative form, and carries no `eval-exempt:` marker.
5. `bash scripts/eval.sh` (full run) produces no new findings relative to the pre-spec baseline.
6. Story 3's applicability record exists for all four destructive-class commands, with a yes/no answer per condition per command.

## Technical Concerns (surfaced at contract time)

- **The cap change is the risk, not the table.** Fifteen lines of headroom is generous relative to what is being added. The mitigations are Business Rules 1, 2, and 4 — a budget derived before authoring, a test proving the new number fires, and a ban on the exemption escape hatch. If a future spec needs more preamble room, it should have to make the same argument again, from a new budget.
- **This content is paid on every invocation.** `_preamble.md` is loaded by all 31 commands. Sixteen lines is a real, if small, recurring token cost, which is why the section is a compressed table plus one paragraph rather than a restatement of ADR-022's reasoning. The reasoning lives in the ADR; the preamble carries only the rule.
- **The precondition is prose, not enforcement.** ADR-022 states this plainly as a negative consequence: "provably git-revertable" has no implementation, so until one exists the precondition binds only agents that read and follow it — the same gap ADR-020 acknowledges for `exit_criteria`. This spec does not close that gap and should not pretend to. Story 3 measures how large the gap is; it does not fill it.
- **The decision this records was contested.** A human gate catches a class of error the reversibility check cannot: a correct, fully reversible operation applied to the wrong target. Git can undo the change but not the confusion. The maintainer reaffirmed the decision and it ships as decided — with ADR-022's 2026-11-11 review trigger as the agreed reversal mechanism, requiring a single incident rather than a renewed argument.
- **Phase 10 may relocate preamble content later.** The progressive-disclosure feature moves procedural detail out of commands into skills. If `_preamble.md` is ever restructured under that work, this cap raise is not a precedent for raising it again — the budget in Business Rule 1 is the artifact that survives, not the number 95.

## Out of Scope

- **The command-file length limit (`-gt 2000` → 400).** Owned by Phase 10's `governor-enforcement` work, eleven lines below the constant this spec changes. Deliberately not touched — the split is what keeps one writer per file across the phase. The sibling spec `2026-08-11-governor-instrumentation` independently defers the same limit to `governor-enforcement` in its own Out of Scope section, so the ownership chain is unambiguous: three Phase 10 specs touch `check_length`, and only one of them owns each constant.
- **The `spec-lite.md` limit (`-gt 100`).** Same function, not this spec's business.
- **Any implementation of a "provably git-revertable" check.** A script or eval check that mechanically verifies reversibility is a separate, larger piece of work. ADR-022 records its absence as a known consequence.
- **Edits to `/revert`, `/refactor`, `/uninstall-writ`, or `/reinstall-writ`.** Story 3 reads them and records findings. Any change to their behavior is a follow-up issue, not part of this spec.
- **Changes to `system-instructions.md`, the Prime Directive, or ADR-013.** The gate-class table extends the existing boundary and must be consistent with it; it does not amend it.
- **Moving `_preamble.md` content into a skill, or any progressive-disclosure restructuring.** Separate Phase 10 feature.
- **Re-litigating the destructive-class decision.** It was raised, reaffirmed, and recorded with a dated review trigger. New evidence reopens it; this spec does not.
