# Writ Phase 11: Contract-and-Verifier Layer

> **Type:** Goal
> **Priority:** High
> **Effort:** Large
> **Created:** 2026-09-05
> **loop:** yes
> **spec_ref:** .writ/specs/2026-09-05-phase11-repair-and-baseline/spec.md _(Stage 1, complete)_ · .writ/specs/2026-09-07-phase11-stage2-prune-the-base/spec.md _(Stage 2a, complete)_ · .writ/specs/2026-09-08-phase11-stage2b-mechanize-the-gates/spec.md _(Stage 2b)_ · .writ/specs/2026-09-08-phase11-stage3-spec-analysis/spec.md _(Stage 3; Stage 4 gets its own spec)_

## OBJECTIVE

Rebalance Writ for Fable 5.1-class models: remove behavior instruction the models no longer need, and put a script behind every quality guarantee that is currently prose. Produced for Writ's maintainer; consumed by every installed project on the next release.

## OUTPUT

Edits to `commands/`, `agents/`, `skills/`, `scripts/`, `system-instructions.md`, `adapters/`, plus new `.writ/eval/baselines/`, `.writ/decision-records/pruned-instructions-ledger.md`, and `scripts/spec-analyze.py`. Edited in place, one spec per iteration, each on its own branch.

## DONE WHEN

- Every `.md` path referenced in `commands/*.md` resolves on disk or to a creating command; `comm` of `skills/` vs `.writ/manifest.yaml` is empty; zero `.writ/knowledge/` entries contain single-character bullets.
- `.writ/eval/baselines/` holds at least one JSON for Fable 5.1 over the 4-story yuss.app set, and `scripts/measure-invocation.py` reports `token_method_validated: true`.
- `system-instructions.md` + `commands/_preamble.md` total at most 10,000 bytes, and every removed line appears in `.writ/decision-records/pruned-instructions-ledger.md` with a dated reason.
- `commands/implement-story.md` marks at most 2 gates `verification: prose-only`; every other gate names a script under `scripts/`.
- `scripts/spec-analyze.py` exists, is invoked from `create-spec` Step 2.6, and has an `eval.sh` check.
- `implement-story`'s default path spawns at most 2 subagents, and a `loop: yes` Goal Card converts to a Claude Code `/goal` invocation with zero manual edits.

## QUALITY

- Baseline exit-criteria pass rate on the yuss.app set after each cut is at or above the Stage 1 figure.
- `bash scripts/eval.sh` exits 0 at the end of every iteration.
- No file under `adapters/` gains more than one model-specific instruction line per model.

## CONTEXT

- `.writ/research/2026-09-05-goldilocks-harness-research.md` - external evidence and the constraint-vs-behavior-request test
- `.writ/product/2026-09-05-goldilocks-assessment.md` - measured findings, the six steps, exit criteria
- `.writ/research/2026-08-14-writ-dogfooding-quality-assessment-research.md` - prior yuss.app data; the prompt-vs-mechanical finding
- `.writ/decision-records/adr-023-stakes-proportional-diligence.md` - why the governor counts decisions, not bytes
- `.writ/product/roadmap.md` - Phase 10 closure and the parking lot this phase draws from

## CONSTRAINTS

- ADR-013 boundary holds: the loop never merges, opens PRs, or releases; installed projects receive changes only through a human `/release`.
- The pruning ledger is append-only; a line re-added after removal counts toward the stall counter.
- No byte target beyond DONE WHEN line 3; the governor is decisions-per-run and verdict provenance.
- Baseline runs use Fable 5.1 only until GPT-6 Astra is runnable from this workspace; the card is amended, not assumed, when it is.
- Each cycle appends one line to the decision log: `{date} {stage}: {what changed and why}`

## STAGES

1. Repair and baseline - dead ends closed; tokenizer validated; Fable 5.1 baseline JSON committed
2. Prune and mechanize - base under 10 KB with ledger; review, architecture, docs, and visual gates script-backed or marked `prose-only`
3. Spec analysis - `spec-analyze.py` advisory at lock and verify; precision recorded on the baseline set
4. Demote and emit - single-agent default with fresh-context evaluator, five-agent pipeline as escalation; Goal Card to `/goal` round-trip

## STOP-CAPS

- loop.max_iterations: 8
- on_exhaustion: halt_reported
- stalled 3 turns: stop and report

## VERDICT

Loop it. Checkable finish line: present — the mission's adjectives ("Goldilocks", "true leap") were replaced by six count, path, and format assertions; nothing in DONE WHEN needs a human to judge. Bounded sandbox: present — every pass edits a git repo on a branch and a wrong pass is a revert; the one irreversible step (reaching installed projects) sits behind `/release`, outside the loop. Convergent: present but weakest — dead ends, ledger length, prose-only gate count, and subagent count are monotone, but the pruning stage can oscillate against a single-model baseline, and a pass that cuts a line and re-adds it leaves nothing measurably smaller. The append-only ledger plus the stall counter turns that oscillation into a stop instead of a spin; it does not make the stage inherently convergent.
