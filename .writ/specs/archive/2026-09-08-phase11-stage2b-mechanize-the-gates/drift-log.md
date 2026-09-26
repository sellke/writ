# Drift Log

> Spec: .writ/specs/2026-09-08-phase11-stage2b-mechanize-the-gates/
> Created: 2026-09-08
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1–4: Batch 1 shared-file landing — Drift Report

> Run: 2026-09-08
> Overall Drift: Medium

### Deviations

#### [DEV-001] Parallel batch landed shared files in one checkout
- **Severity:** Medium
- **Spec said:** Batch 1 (Stories 1–4) may run in parallel; each owns a disjoint script and a different `gates:` entry, editing `implement-story.md` and `eval.sh` additively.
- **Implementation did:** Exclusive scripts and tests were authored concurrently. Shared wiring (`commands/implement-story.md`, `scripts/eval.sh`, real-command provenance tests, leanness overage pin) was applied sequentially in one checkout so four writers would not collide. One implementation commit covers the batch.
- **Reason:** The graph allows parallel; the files do not. The spec README already named this as sequential-safer.
- **Resolution:** Accepted — contract (scripts, frontmatter `script:` paths, FAIL-only / ABORT residual / advisory maps) is intact.
- **Spec amendment:** none
