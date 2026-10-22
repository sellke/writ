# Drift Log

> Spec: .writ/specs/2026-10-22-rendering-delegation-rows/
> Created: 2026-10-22
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Claude Code Live Verification and Record — Drift Report

> Run: 2026-10-22
> Overall Drift: Small

### Deviations

#### [DEV-001] Headless row's Platform cell omitted the session kind
- **Severity:** Small
- **Spec said:** AC-1.3: the Platform cell carries the `claude --version` output and desktop or terminal session.
- **Implementation did:** Row 4 (headless `claude -p`) was written as "Claude Code 2.1.308, docs read 2026-10-22" because the headless context was not run and the evidence source was recorded instead.
- **Reason:** The row describes a path the run did not take, so the cell named the docs date in place of the session.
- **Resolution:** Fixed in Story 1 before completion (Small): the cell now reads "Claude Code 2.1.308 (`claude --version`), desktop app session; `-p` not run, docs read 2026-10-22".
- **Spec amendment:** None.

#### [DEV-002] Two Observed cells stated one step past what the run saw
- **Severity:** Small
- **Spec said:** AC-1.3 and the Hardest Constraint: every Observed cell states only what the run saw.
- **Implementation did:** Row 3 said "a command creates a design canvas by publishing to that URL" (the quickstart instruction restated as a mechanism; nothing was published). Row 2 said the tool "refuses screenshots and page reads on a local-file tab" (only a screenshot was attempted).
- **Reason:** Paraphrases of tool output rather than the observation.
- **Resolution:** Fixed in Story 1 before completion (Small): row 2 now says a screenshot of the local-file tab was refused; row 3 now says the quickstart listed the type with a `type_url` and said to publish to it, and that nothing was published and no canvas was created.
- **Spec amendment:** None.
