# User Stories — Script-Backed Quality Gates

> Parent: [`../spec.md`](../spec.md)

## Summary

| # | Story | Status | Priority | Tasks | AC | Dependencies |
|---|---|---|---|---|---|---|
| 1 | [Classification doc](story-1-classification-doc.md) | Not Started | High | 0/7 | 5 | — |
| 2 | [Quality-config audit](story-2-quality-config-audit.md) | Not Started | High | 0/7 | 5 | Story 1 |
| 3 | [Test integrity](story-3-test-integrity.md) | Not Started | High | 0/7 | 5 | Story 1 |
| 4 | [Build smoke](story-4-build-smoke.md) | Not Started | Medium | 0/7 | 5 | Story 1 |
| 5 | [Gate wiring](story-5-gate-wiring.md) | Not Started | High | 0/7 | 5 | Stories 3, 4 |
| 6 | [Initialize & status](story-6-initialize-and-status.md) | Not Started | Medium | 0/7 | 5 | Stories 2, 3 |

**Progress:** 0/6 stories complete · 0/42 tasks · 30 acceptance criteria

## Dependency Graph

```
        Story 1 (classification doc)
       /        |        \
  Story 2   Story 3   Story 4          ← parallel batch A
      |        |   \      |
      |        |    \     |
      |        |     Story 5           ← needs 3 + 4
       \      /
        Story 6                        ← needs 2 + 3
```

**Batch A — Stories 2, 3, 4** touch disjoint files (`quality-config-audit.py`,
`test-integrity.py`, `build-smoke.py` plus their own tests and eval asserters) and can run
concurrently. All three edit `scripts/eval.sh`'s `CHECKS` array and add a `check_*` function;
that is the one shared file in the batch and the likeliest merge conflict — sequence the
`eval.sh` edits or expect a trivial resolution.

**Batch B — Stories 5 and 6** also touch disjoint files (`implement-story.md` +
`testing-agent.md` versus `initialize.md` + `status.md`) and can run concurrently once their
dependencies land. Story 6 does not depend on Story 4, so it can start as soon as 2 and 3 are
done, in parallel with Story 5 waiting on Story 4.

## Sequencing Notes

Story 1 first, always. Stories 2–4 implement against its finding vocabulary and severities,
and `scripts/eval.sh` binds every code to *both* the checker and the doc — so a code invented
in a checker before it exists in the doc fails eval by design.

Story 4 carries an explicit disposition criterion (`AC-4.5`) permitting it to close
`Closed — Not Implemented` if the environment-versus-code classifier cannot be made reliable.
If that happens, Story 5's Gate 2 half drops with it and its Gate 4 half proceeds unchanged —
the two halves of Story 5 share no logic.

Before running `/implement-spec`, run `/assess-spec`. Six stories, three new scripts and six
modified product files is at the upper end of a single spec; the parent spec records the clean
decomposition seam if it recommends splitting.
