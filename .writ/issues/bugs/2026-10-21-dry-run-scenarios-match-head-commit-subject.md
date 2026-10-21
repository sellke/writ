# Install Dry-Run Scenarios Fail When HEAD's Commit Subject Names a Dev-Only Script

> **Type:** Bug
> **Priority:** Low
> **Effort:** XS
> **Created:** 2026-10-21
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

`eval.sh`'s `recommended-spec-implementation` scenarios `install-{cursor,claude,codex}-dry-run-names-neither` assert that the whole dry-run output never mentions `recommend-state.py`. The installer prints the source's HEAD commit subject as its `📌 Version:` line, so a commit whose subject names the script fails all three scenarios. The scripts themselves are fine.

## Current State

- Reproduced on `phase/13-subtract-and-repair` at `2eb6611`, whose subject is "fix(docs): leanness audit names recommend-state.py without its scripts/ path": `Findings: 3`, `Scenarios: 144/147`.
- The assertion matches anywhere in stdout, including the version banner, which comes from `git log -1` of the source tree.

## Expected Outcome

- The scenarios check what the install would copy or record (the file list and manifest lines), not the banner. A commit message cannot fail them.

## Relevant Files

- `scripts/eval.sh`: `check_recommended_spec_implementation` dry-run scenarios
- `scripts/install.sh`: the `📌 Version:` banner line
