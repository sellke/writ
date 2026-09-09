# Drift Log

> Spec: .writ/specs/2026-09-09-phase11-stage4b-pipeline-demote/
> Created: 2026-09-09
> ⚠️ Append-only — do not modify existing entries.

---

## Story 2: Default Path and Flags — Two-Spawn implement-story — Drift Report

> Run: 2026-09-09
> Overall Drift: Small

### Deviations

#### [DEV-001] Gate 0.5 leftover “full pipeline” wording
- **Severity:** Small
- **Spec said:** Gate 0.5 is an inline default-path script (`boundary-map.py`); skip only `--quick` / `--review-only` / `/prototype`.
- **Implementation did:** Pipeline table still runs Gate 0.5 on default; a prototype note still says Gate 0.5 “exists only on the full pipeline.”
- **Reason:** Leftover prototype-vs-implement-story wording; `--full-pipeline` now means the six-agent hatch, not “skip inline gates.” Behavior is correct.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach states Gate 0.5 is inline on default implement-story, not `--full-pipeline`-only.

#### [DEV-002] Control flow omits the `--review-only` FAIL exception
- **Severity:** Small
- **Spec said:** `--review-only` FAIL ends the run; no recode; no silent `--full-pipeline`.
- **Implementation did:** Invocation + Gate 3 state that exception; Control flow still says Gate 3 FAIL → Gate 1 without repeating `--review-only`.
- **Reason:** Specific sites win; Control flow is the general recode rule.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Error Handling lists `--review-only` FAIL ends the run.

Prior spec-lite SHA-256: `c86f0cb5853de6bb795d873f2e65608be27f60966d5d32043dd46ec98c8f546b`

---

## Story 3: Eval, Adapters, and Spawn-Cap Proof — Drift Report

> Run: 2026-09-09
> Overall Drift: Small

### Deviations

#### [DEV-003] Adapter knowledge-loading still names older default recipients
- **Severity:** Small
- **Spec said:** Rewrite only sentences that treat no-flag `/implement-story` as the full SDLC / five-agent / six-gate default; that path is `--full-pipeline`.
- **Implementation did:** Relitigating headings and lead sentences now name `--full-pipeline`. Knowledge-loading paragraphs still mention architecture-check / review as `/implement-story` recipients.
- **Reason:** Those sentences load context routing, not the no-flag spawn claim. AC-3.3 limited edits to relitigating sentences.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Implementation Approach and Files in Scope state that leftover knowledge-loading recipients stay unless they relitigate the no-flag default.

Prior spec-lite SHA-256: `00122e19553be18c545c56bd53ea49c58ada728036de426d2e400ad04e604223`
