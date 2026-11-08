# Recommendation Log: Lean Story Pipeline

## Removal bar

- **Decision:** a gate with no recorded catch moves to `--full-pipeline`. Nothing is deleted.
- **Evidence:** ADR-023 rule 6 ("a gate that cannot name one is the candidate for removal"). The removal trial spent a full spec and removed nothing. Six default-path gates have no measurement.
- **Alternatives:** measure each gate first, which is slow and repeats the removal-trial cost; delete outright, which is hard to undo.
- **Risk / reversibility:** reversible. A demoted gate's section and script stay in the product.
- **Result:** asked in discovery. The user chose "Name it or demote (Recommended)".

## Gate runner

- **Decision:** a new `story-gate.py` runs the default-path checks in two calls.
- **Evidence:** retro F6 (lanes skipped steps); 21 script subcommands in the default path.
- **Alternatives:** trim the prose only, leaving the orchestrator to sequence each script.
- **Risk / reversibility:** ADR-029 rule 4 tension (see spec Technical Concerns). The fallback is to trim the prose.
- **Result:** asked in discovery. The user chose "One gate-run script (Recommended)".

## File-creation rule excluded

- **Decision:** leave the rule that agents may create only files the tasks name.
- **Evidence:** `2026-11-06-lean-story-tasks` Business Rule 6 kept it, and that spec's trial ran clean with it.
- **Alternatives:** relax it to "list and justify new files" (the origin issue's proposal).
- **Risk / reversibility:** none. This is the status quo.
- **Result:** Business Rule 8. Stated in the contract the user approved.

## Retro F7, F8, F26 excluded

- **Decision:** out of scope.
- **Evidence:** each adds rules to Gate 3 or to the coding agent. This spec removes rules.
- **Alternatives:** fold them in.
- **Risk / reversibility:** low. They stay deferred in the retro.
- **Result:** Scope Boundaries → Excluded.

## Contract lock

- **Decision:** lock the contract as printed.
- **Evidence:** both discovery choices went with the recommendation, and the user approved the contract at Plan Mode exit. No blocking cross-spec overlap was found.
- **Alternatives:** edit the contract; explore risks first.
- **Risk / reversibility:** reversible. It touches spec files only.
- **Result:** locked on the user's plan approval. No separate `jev-judge.py doubt` question was asked, because the user's explicit approval answers it.

## Story decomposition

- **Decision:** six stories:
  1. evidence
  2. demote
  3. runner
  4. test ownership
  5. supervisor and implement-spec
  6. trial
- **Evidence:** demotion needs the evidence first, and the runner needs the final default set. Stories 4 and 5 share no files.
- **Alternatives:** fold the runner and the demotion into one story. That would exceed 7 tasks and touch more than 40 pinning tests at once.
- **Risk / reversibility:** reversible.
- **Result:** story plan in `user-stories/README.md`.
