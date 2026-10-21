# Product Consistency Report

> **Date:** 2026-10-21
> **Mode:** `--product` (default)
> **Trigger:** post-implementation check after `/implement-phase 13` (phase branch `phase/13-subtract-and-repair`, unreleased)
> **Maintainer constraint for this run:** Writ's `/writ-design` and Claude Code's native `/design` are separate commands and should stay separate. Flag product-doc wording that conflates them or plans to merge them.
> **Result:** ⚠️ Passed with warnings. Mission and roadmap agree with each other (P1 ✅) but both lag what was built (P4). Four lines conflate or couple the two design commands.

## Summary

| Check | Status | Details |
|-------|--------|---------|
| P1. Phase-status parity | ✅ | `mission.md` and `roadmap.md` both label Phases 13–16 committed. They agree. Both lag reality for Phase 13; see P4. |
| P2. ADR reference resolution | ✅ | Every ADR referenced in mission, roadmap, and mission-lite resolves under `.writ/decision-records/`, including ADR-030. |
| P3. Derivative freshness | 🔧 | `.writ/context.md` regenerated. Its mission paragraph predated ADR-030, and its knowledge count was stale (21, now 23). `mission-lite.md` matches `mission.md`; no change. |
| P4. Shipped-claim sanity | ⚠️ | Every shipped claim has evidence. Two items run the other way: built work with no matching status or home (below). |
| Requested: design-command separation | ⚠️ | Shipped commands and adapters keep the two separate: no delegation between them. Four product-doc lines use the old name or describe coupling. |

## Regenerated

- `.writ/context.md`: full rewrite per `/status` Step 8.
  - The Product Mission paragraph now carries the ADR-030 posture: contract, verifier, boundary, one front door.
  - Active Spec reads "none in progress", with Phase 13 implemented pending human validation.
  - Knowledge count is 23, docs 29, open issues 22 of 33.
  - Recent Drift is taken from the last spec.

## Outstanding (needs human judgment)

### Phase status

- **[P4, inverse] Phase 13 is implemented, but both authoritative files say "📋 Committed".**
  - `roadmap.md`'s Phase 13 heading and its success criteria are unmarked.
  - `mission.md`'s "Phases 13–16 (📋 committed)" block still lists Phase 13 as committed.
  - The phase state records `IMPLEMENTED_PENDING_HUMAN_VALIDATION`, with all nine machine criteria passing (`.writ/state/phase-execution-20261020T205551Z.json`).
  - Run `/plan-product --reconcile` to mark Phase 13 implemented and pending UAT, tick its criteria against the recorded evidence, and update the Current status line.
- **[P4, inverse] `2026-10-20-claude-agent-generator` has no roadmap home.** The spec is Complete. Another session committed it on the phase branch, and it generates `claude-code/agents/*.md` from `agents/*.md`. The condensed history has no row for it. Reconcile records it as inter-phase work riding in the Phase 13 branch.

### Design-command separation (maintainer constraint)

1. **`mission.md` line ~202 (parking-lot summary):** "`/design` Mode A modernization". This names Writ's command by its retired name, which is now the native command's name. Should read `/writ-design`.
2. **`roadmap.md` line ~786 (parking lot):** "**`/design` Mode A modernization** … revisit it with AI image mockups or native design tools". It has the same old-name problem. "Native design tools" can also be read as folding `/writ-design`'s rendering into Claude Code's native `/design`, which the constraint rules out. Suggested wording: modernize `/writ-design`'s own Mode A, kept separate from the native command.
3. **`roadmap.md` line ~617 (Phase 13 feature, now built):** "rename Writ's `/design`, or detect and delegate". "Detect and delegate" is the coupling option, and it was rejected on 2026-10-20. Suggested wording: "renamed to `/writ-design` (decided 2026-10-20)".
4. **`roadmap.md` line ~674 (Phase 14, rendering-delegation rows):** "First-party verification of Claude Code's native `/design`". This concerns `/prototype` using native artboards to render its drafts, not `/writ-design`, so it does not merge the two design commands. It does couple Writ to the native command. Confirm that this coupling is wanted, or reword it as "the platform's renderer" without naming `/design`.

These are authoritative files, so `--product` reports and does not edit. `/plan-product --reconcile` applies the wording.

## Notes

- `mission.md` and `roadmap.md` were not modified.
- Code check for the constraint: `commands/writ-design.md`, `commands/prototype.md`, and `adapters/*.md` contain no wording that delegates between `/writ-design` and the native `/design`.
- Verification surfaces drift after implementation; `/plan-product --reconcile` realigns the baseline when it does.
