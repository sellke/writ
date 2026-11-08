# Recommendation Log: Lean Implement Phase

## Source issue

- **Decision:** promote `2026-11-06-implement-phase-over-prescribed.md`, not the path given at invocation.
- **Evidence:** the invocation named `2026-11-06-story-pipeline-over-prescribed.md`, which already has `spec_ref` → `2026-11-06-lean-story-pipeline`. The added note ("UAT plans should only be generated upon request") matches the implement-phase issue.
- **Alternatives:** add UAT-on-request to lean-story-pipeline through `/edit-spec`.
- **Risk / reversibility:** reversible; spec files only.
- **Result:** asked (conflicting evidence). The user chose the implement-phase issue.

## How UAT is requested

- **Decision:** a `--uat` flag on `/implement-phase`, stored as `uatRequested`; c2 keeps its ID and checks plans only when requested.
- **Evidence:** retro F10/F24 (201 human-only scenarios, about 1.04M output tokens); the user's instruction that plans be generated only on request.
- **Alternatives:** manual `/create-uat-plan` only, retiring c2.
- **Risk / reversibility:** reversible. Old state files read as requested, so finished runs keep their verdicts.
- **Result:** asked. The user chose "--uat flag (Recommended)".

## Scope

- **Decision:** include health sources, Goal emit removal, lane result file (F22) and prose compression; exclude parallel spec execution.
- **Evidence:** the source issue's Expected Outcome; parallel lanes have no measurement yet.
- **Alternatives:** UAT only; drop the lane result file.
- **Risk / reversibility:** reversible; each story is its own commit.
- **Result:** asked at contract lock. The user chose "Lock it (Recommended)".

## Story order

- **Decision:** stories run one after another (1 → 2 → 3 → 4).
- **Evidence:** all four edit `commands/implement-phase.md`; Story 4 compresses text the first three change.
- **Alternatives:** run 1–3 in one parallel batch.
- **Risk / reversibility:** none beyond wall-clock time.
- **Result:** acted on (plan).

## Story authoring

- **Decision:** the orchestrator wrote the four story files directly instead of spawning `user-story-generator` subagents.
- **Evidence:** four stories, all context already loaded; `ac-trace.py` validation (Step 2.6a) still runs.
- **Alternatives:** parallel generator subagents per Step 2.6.
- **Risk / reversibility:** reversible; validation catches format defects.
- **Result:** acted on.
