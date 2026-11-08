# Recommendation Log: Lean Story Tasks

## Discovery skipped

- **Decision:** write the contract from the issue without a discovery conversation.
- **Evidence:** the issue's Expected Outcome names all four changes and the trial; the codebase settled the rest (verify-spec 1d requires DoD; `ac-trace.py` already parses task lines; byte-budget ledger).
- **Alternatives:** Plan Mode discovery on trial scope.
- **Risk / reversibility:** low; spec files only, git-revertable.
- **Result:** contract printed in the session.

## Contract lock

- **Decision:** lock the contract as printed.
- **Evidence:** issue Expected Outcome; verify-spec Check 1d; `KNOWN_OVER_BUDGET` entries for `create-spec.md` (14169) and `verify-spec.md` (10818); no blocking cross-spec overlap.
- **Alternatives:** edit the contract; drop the `/implement-story` trial for a cheaper comparison.
- **Risk / reversibility:** reversible. `jev-judge.py doubt` returned `fail (fallback_direction, doubt_uncalibrated, p=0.62)`, so it asked.
- **Result:** user chose "Lock and create (Recommended)". Decision `5d913b27057c` labeled `as_recommended`.

## 50-word cap

- **Decision:** cap tasks at 50 words.
- **Evidence:** p90 task length was 33–50 words in specs from March to August 2026, and 69–97 in October and November (spec.md → Evidence).
- **Alternatives:** 40 words (would flag 24% of all historical tasks); no cap (advice only, which the issue says the generator ignores).
- **Risk / reversibility:** a constant in one script and one sentence in two files.
- **Result:** Business Rule 2.

## Check lives in `ac-trace.py`, informational, `Not Started` only

- **Decision:** add `oversized_task` to `ac-trace.py` as informational, scoped to `Not Started` stories; Step 2.6a makes it a failure.
- **Evidence:** `ac-trace.py` already parses `## Implementation Tasks` lines and Step 2.6a already runs it once per spec. `/verify-spec` also runs it, so a blocking finding would fail completed legacy specs.
- **Alternatives:** a new script (more surface); orchestrator counts by hand (not mechanical); blocking severity (breaks legacy specs).
- **Risk / reversibility:** additive finding code; schema unchanged.
- **Result:** Story 1.

## Drift claim not carried into the spec

- **Decision:** the spec does not claim lean tasks reduce drift.
- **Evidence:** r = −0.23 between median task words and `[DEV-` entries per story across 24 archived specs.
- **Alternatives:** keep the issue's "invites drift" framing.
- **Risk / reversibility:** none; framing only. The trial (Story 5) tests the claim.
- **Result:** spec.md → Evidence.

## Stories in sequence

- **Decision:** five stories, each depending on the one before (Story 5 on 2–4).
- **Evidence:** Stories 2, 3, and 4 all edit `agents/user-story-generator.md` and `commands/create-spec.md`.
- **Alternatives:** run 3 and 4 in parallel (file conflicts).
- **Result:** `user-stories/README.md`.

## Stories generated under this spec's own task rules

- **Decision:** generator prompts for this spec told the floor-tier generator to follow Business Rules 1–4 and keep the Definition of Done.
- **Evidence:** the locked contract; `/verify-spec` 1d still requires DoD until Story 3 ships.
- **Alternatives:** generate under the current template only.
- **Risk / reversibility:** story files only.
- **Result:** stories double as a small preview of the lean format.
