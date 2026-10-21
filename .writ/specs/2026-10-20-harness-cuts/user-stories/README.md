# User Stories: Harness Cuts

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [Delete the Lean Siblings and Their Install Logic](story-1-delete-lean-siblings.md) | Completed ✅ | High | None | 7 | 7/7 |
| 2 | [Remove the Lean Code Paths from the Scripts](story-2-remove-lean-code-paths.md) | Not Started | High | Story 1 | 7 | 0/7 |
| 3 | [Remove the ADR-025 No-Op Lines and Correct the /ship Description](story-3-noop-lines-and-ship-description.md) | Not Started | Medium | Story 2 | 7 | 0/7 |
| 4 | [Make Recommended-Delivery Staging Dev-Only](story-4-staging-dev-only.md) | Not Started | High | Story 2 | 7 | 0/7 |

**Total:** 4 stories, 28 tasks, 19 acceptance criteria.

## Dependencies

- **Story 1** has no story dependency. The spec as a whole depends on `2026-10-20-ci-and-update-integrity`, whose every-category carry-forward AC-1.4 and AC-4.3 rely on.
- **Story 2** needs Story 1. The lean files must be gone before the code that exempts them, or `eval-leanness.py`, `eval.sh` `check_manifest`, and the governor test count them as commands.
- **Story 3** needs Story 2. It extends `scripts/tests/test_harness_cuts.py`, which Story 2 widens. Its no-op grep over `commands/` also needs Story 1.
- **Story 4** needs Story 2. Both edit the dev-only arm of the three ship filters, `.writ/docs/agent-cli-contract.md`, `commands/update-writ.md`, and `test_agent_cli_contract_doc.py`. It extends `test_install_update_harness_cuts.sh` from Story 1.
- **Stories 3 and 4** can run in parallel. They share only `scripts/eval.sh`, in different functions (`check_model_escalation` and `check_recommended_spec_implementation`).
