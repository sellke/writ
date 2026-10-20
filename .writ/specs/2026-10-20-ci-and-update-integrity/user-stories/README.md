# User Stories: CI and Update Integrity

> Spec: [`../spec.md`](../spec.md)

| # | Story | Status | Priority | Dependencies | Tasks | Progress |
|---|---|---|---|---|---|---|
| 1 | [CI Runs Every Suite](story-1-ci-runs-every-suite.md) | Not Started | High | None | 6 | 0/6 |
| 2 | [Keep the Codex Config Baseline on Update](story-2-keep-codex-config-baseline.md) | Not Started | Medium | None | 6 | 0/6 |
| 3 | [Record Baselines Only for Shipped Paths; Customized Files Keep Their Baseline](story-3-baselines-for-shipped-paths-only.md) | Not Started | High | Story 2 | 6 | 0/6 |
| 4 | [Keep Modified Stale Files in Every Category](story-4-keep-modified-stale-files.md) | Not Started | High | Story 3 | 7 | 0/7 |
| 5 | [Repair Legacy Manifests and Remove Stale Files From Their Real Path](story-5-legacy-manifests-and-stale-removal.md) | Not Started | High | Story 4 | 6 | 0/6 |

**Total:** 5 stories, 31 tasks, 23 acceptance criteria.

## Dependencies

- **Story 1** is independent. It edits only `.github/workflows/eval.yml` and adds `scripts/tests/test_ci_workflow.py`. Its bash step's glob picks up every test the other stories add.
- **Stories 2 → 3 → 4 → 5** are serial, because each edits the same `scripts/update.sh` functions:
  - Story 2 reads the Codex baseline before `write_copy_manifest` truncates the manifest.
  - Story 3 generalizes that into a per-run baseline file, rewrites `write_copy_manifest` in `update.sh` and `install.sh` to record only shipped paths, and writes the `# baselines: shipped` header.
  - Story 4 widens the stale warning in `detect_stale_files` and corrects `commands/update-writ.md`.
  - Story 5 reads header-less (legacy) manifests through the per-run baseline file and fixes the stale-removal block.
- Stories 1 and 2 can run in parallel.

*Amended 2026-10-20 (maintainer-approved contract amendment): Stories 3 and 5 added. The first draft's Story 2 (stale files) is now Story 4, and its Story 3 (Codex baseline) is now Story 2, so that the stories land in edit order.*
