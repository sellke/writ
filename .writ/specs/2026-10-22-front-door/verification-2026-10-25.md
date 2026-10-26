# Verification Report: Front Door

> **Date:** 2026-10-25
> **Spec:** 2026-10-22-front-door
> **Mode:** default
> **Result:** ⚠️ Passed with warnings

## Summary

| Check | Status | Details |
|-------|--------|---------|
| Story file integrity | ✅ | 3 stories, all well-formed |
| Status consistency | ✅ | README in sync: 3 stories, 21 tasks, 15 criteria |
| Completion integrity | ✅ | 3a to 3f clean: every completed story has all criteria, tasks, and Definition of Done checked; `scripts/ac-trace.py check` reports no findings. 3g: 8 advisory notes |
| Dependency validation | ✅ | Story dependencies satisfied, no cycle; `scripts/spec-deps.py validate` reports the cross-spec graph `ok`. |
| Deliverables checklist | ✅ | No checkbox list; all 10 files the contract names exist; status Complete |
| Contract alignment | ⚠️ | 3 heuristic findings (WARN-1 to WARN-3) |
| Spec-lite integrity | 🔧 | Diverged from the 2026-10-24 amendments; regenerated (FIX-1) |
| Spec owner field | ✅ | @AdamSellke |

## Stories

| # | Title | Status | Tasks | Criteria | DoD |
|---|---|---|---|---|---|
| 1 | The `/writ` Command File | ✅ | 7/7 | 5/5 | 5/5 |
| 2 | Registration and Catalogs | ✅ | 7/7 | 5/5 | 5/5 |
| 3 | Structure Rows, Issue Resolution, and Routing Fixture | ✅ | 7/7 | 5/5 | 5/5 |

## Issues Found & Resolved

- [FIX-1] `spec-lite.md` regenerated from `spec.md`. spec.md was amended on 2026-10-24 (DEV-007, DEV-009), after spec-lite was written on 2026-10-22. spec-lite still allowed every route as an option, had no four-option cap, and said routing proceeds unless the goal is missing, which contradicts the DEV-009 case.

## Outstanding Warnings

- [WARN-1] Check 6, Must Include 4: the DEV-009 case (a request names something the project lacks) is in `commands/writ.md` Step 1, but no test in `scripts/tests/test_front_door.py` pins it.
- [WARN-2] Check 6, Scope out: DEV-008 changed `commands/prototype.md` Step 3. The spec excluded changes to the routed commands' own workflows. The drift log records and justifies the change; confirm the exception or amend Scope out.
- [WARN-3] Check 6, records: DEV-009 and `.writ/eval/phase-14-acceptance/report.md` say Business Rule 4 was amended for D9. The amendment is in Must Include 4 and the State Catalog; Business Rule 4 is the confirmation rule.
- [WARN-4] Check 7 side effect: the regenerated spec-lite no longer carries DEV-006's tie-break refinement (an escalation signal counts only when the request states it or the restatement can name it), because spec.md Business Rule 2 never received it. The rule still lives in `commands/writ.md` Step 2 and the drift log. Fold it into Business Rule 2 with `/edit-spec`, then run `/verify-spec --fix`.

## Notes

- Check 3g (advisory): `scripts/spec-analyze.py check` prints `pass` with no `reason:` lines. Jev (`scripts/jev-judge.py spec-findings`) escalated most stories; the orchestrator judged them. These meaning-level notes do not fail the check or the report:
  - contradiction, `story-1-writ-command-file.md` (AC-1.4): AC-1.4 still requires "every other route as an option" while its DEV-007 amendment and Business Rule 4 cap the question at "at most four options, two alternatives", so with five routes the criterion cannot hold as written.
  - ambiguity, `story-1-writ-command-file.md` (AC-1.3): AC-1.3 sends a tie to /create-spec "when any /prototype escalation signal fires" without saying whether an unstated signal counts, and DEV-006 recorded fixture request 7 ("everywhere") routing to either /create-spec or /prototype --no-diverge depending on that reading.
  - ambiguity, `story-1-writ-command-file.md` (AC-1.2): AC-1.2 adds the Proof: line only "when the request names evidence" yet requires that "a missing part is named", so for a request with no proof one implementer omits the Proof: line and another prints it marked missing, as the spec's Journey example does.
  - gap, `story-1-writ-command-file.md` (AC-1.2): No criterion covers the amended Must Include 4 and State Catalog case where the request "names a file, function, or system that a search of the project does not find" (DEV-009), which must ask one question before routing, while AC-1.2 lets routing proceed whenever a goal is present.
  - gap, `story-1-writ-command-file.md` (story level): The Notes and the Upstream error shadow path require /writ to name a missing routed command file and /update-writ ("Do not improvise the workflow"), but no criterion covers that error case.
  - gap, `story-1-writ-command-file.md` (story level): No criterion covers the State Catalog case where roadmap.md is absent ("route not offered", and the restatement points to /plan-product), although Story 1 owns Required Artifacts and its stated degradation.
  - gap, `story-1-writ-command-file.md` (story level): No criterion covers the Nil input state "/writ with no request and no context", which gets one question ("what do you want to do?") and no restatement, since AC-1.2 only covers a request that lacks a goal.
  - gap, `story-1-writ-command-file.md` (AC-1.4): AC-1.4 puts "Not what I meant" last but no criterion covers what happens after a pick, although Story 1 owns the State Catalog rows "One free-text follow-up, then restate and route again" and, for another route, "the restatement is unchanged".
- `jev-judge.py status` printed `reason: model_unpinned`.
- Diagnostic only. Use `/release` when you are ready to publish; it runs build checks, conditional tests, and changelog work.
