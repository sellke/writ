# Fixture Loop Yes Card

## OBJECTIVE

Convert a Goal Card into paste-ready goal files.

## DONE WHEN

- Emitter writes GOAL.md and VERIFY.md
- Printed invoke matches the adapter template

## STOP-CAPS

- loop.max_iterations: 8
- on_exhaustion: halt_reported

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
