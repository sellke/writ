# Writ Phase 11: Contract-and-Verifier Layer

## OBJECTIVE

Rebalance Writ for Fable 5.1-class models: remove behavior instruction the models no longer need, and put a script behind every quality guarantee that is currently prose. Produced for Writ's maintainer; consumed by every installed project on the next release.

## DONE WHEN

- Every `.md` path referenced in `commands/*.md` resolves on disk or to a creating command; `comm` of `skills/` vs `.writ/manifest.yaml` is empty; zero `.writ/knowledge/` entries contain single-character bullets.
- `.writ/eval/baselines/` holds at least one JSON for Fable 5.1 over the 4-story yuss.app set, and `scripts/measure-invocation.py` reports `token_method_validated: true`.
- `system-instructions.md` + `commands/_preamble.md` total at most 10,000 bytes, and every removed line appears in `.writ/decision-records/pruned-instructions-ledger.md` with a dated reason.
- `commands/implement-story.md` marks at most 2 gates `verification: prose-only`; every other gate names a script under `scripts/`.
- `scripts/spec-analyze.py` exists, is invoked from `create-spec` Step 2.6, and has an `eval.sh` check.
- `implement-story`'s default path spawns at most 2 subagents, and a `loop: yes` Goal Card converts to a Claude Code `/goal` invocation with zero manual edits.

## STOP-CAPS

- loop.max_iterations: 8
- on_exhaustion: halt_reported
- stalled 3 turns: stop and report

No `--recommend` command merges, opens PRs, or releases. Production remains a human decision.

```
/goal Treat this stop as acceptable when ANY of the following is true — do not
collapse these into "the checker passed":
(a) `python3 scripts/exit-criteria.py check --command implement-phase --state .writ/state/phase-execution-{timestamp}.json` exits 0 (verdict: met);
(b) the run is currently paused awaiting a retained AskQuestion — for example the
    Step 2.3 execute/edit/abort confirmation — regardless of whether the checker
    has been invoked yet; this state is met on its own;
(c) the checker exits 2 (verdict: impossible) — a tripped loop bound, an
    unresolved challenge_required, or a phase-state/git mismatch.
If none of these hold, the condition is not-met: continue the run rather than
stopping, and never treat a pause as something to route around.
```
