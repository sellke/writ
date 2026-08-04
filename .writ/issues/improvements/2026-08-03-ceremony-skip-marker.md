# Structured Ceremony-Skip Marker

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Small
> **Created:** 2026-08-03
> **Status:** Open — deliberately excluded from [`2026-08-03-deterministic-story-substrate`](../../specs/2026-08-03-deterministic-story-substrate/spec.md) as bookkeeping rather than quality work. Filed rather than dropped because the false-positive symptom is real.
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

Give `--quick` and `/prototype` a structured, queryable marker so `/verify-spec` and `/status` can distinguish a deliberate ceremony skip from work that was never finished.

## Current State

Ceremony reduction is flag- and prose-based, leaving no record a command can query.

- `commands/implement-story.md` `--quick` (lines 949–952) skips gates. Its only trace is an optional inline note in the What Was Built record: `> Note: Review skipped (\`--quick\` mode)` (lines 909–915). There is no header field.
- `commands/prototype.md` writes nothing to `.writ/specs/` at all — its summary is console-only (lines 174–178).
- Some specs carry a hand-written convention, e.g. `.writ/specs/2026-03-13-pipeline-quality-improvements/spec.md` line 6: `> Implementation Mode: \`--quick\``. Nothing validates or reads it.

The consequence is a false positive in a gate. `commands/verify-spec.md` Check 3 (lines 171–198) reports unchecked acceptance criteria and Definition of Done items on a `Completed` story as "false completion" / "incomplete DoD". For a story deliberately run with `--quick`, that finding is noise. `/status` has the same blind spot: "incomplete" (lines 81–85, 354) covers both cases identically.

A gate that reports known-acceptable states as failures trains the maintainer to skim its output, which costs more than the bookkeeping gap itself.

## Expected Outcome

- A story or spec records *why* ceremony was reduced in a structured field — e.g. `> **Ceremony:** reduced (--quick)` or a `skip_reason:` value — in the same blockquote header that already carries `Status`, `Priority`, and `Dependencies`.
- `/verify-spec` reads the marker and reports a deliberate skip as an informational note rather than an integrity finding.
- `/status` distinguishes "deliberately reduced" from "incomplete" when summarizing a spec.
- `/implement-story --quick` writes the marker automatically; a maintainer never has to remember to add it.
- Contradictory metadata is rejected rather than silently accepted — a story claiming a reduced-ceremony skip while also recording a full review result is an inconsistency worth surfacing.

## Relevant Files

- `commands/implement-story.md` — `--quick` handling; writes the marker
- `commands/verify-spec.md` — Check 3, so a deliberate skip stops reading as false completion
- `commands/status.md` — the incomplete-versus-skipped distinction
- `commands/prototype.md` — decide whether prototype runs leave any spec-side trace at all
- `agents/user-story-generator.md` — story header template, if the field lives there

## Notes

**Origin.** Recommendation P3 of [`2026-08-03-writ-vs-openspec-analysis`](../../research/2026-08-03-writ-vs-openspec-analysis.md). OpenSpec's `skip_specs: true` is the reference: schema-validated, accepted only for genuinely zero-delta changes, rejected if a delta spec is also present, and rendered by `openspec status` as "specs: explicitly skipped" rather than merely absent. The validated-contradiction behavior is the part worth copying — a marker nothing checks is just another prose convention.

**Why it was excluded from the substrate spec.** That spec's thesis is moving high-consequence, high-volume steps from agent judgment to program. This is observability bookkeeping — real, but a different kind of work, and small enough that bundling it would have diluted a focused spec.

**Scope caution.** Resist growing this into a general spec-metadata schema. The valuable version is one field, written automatically, read by two commands. If it starts to look like a schema engine, that is a signal to stop and reconsider.
