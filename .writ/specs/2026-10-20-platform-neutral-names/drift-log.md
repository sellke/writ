# Drift Log

> Spec: .writ/specs/2026-10-20-platform-neutral-names/
> Created: 2026-10-21
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Canvas-Preview Capability in `/prototype` and the Four Adapters — Drift Report

> Run: 2026-10-21
> Overall Drift: Small

### Deviations

#### [DEV-001] OpenClaw row says "HTML file" where the technical spec's row text says "file"
- **Severity:** Small
- **Spec said:** technical-spec.md → Adapter rows gives the OpenClaw second cell as `` `Write({ path: ".writ/prototypes/<date>-<slug>/<draft>.html" })`, one self-contained file per draft ``.
- **Implementation did:** `adapters/openclaw.md` reads "…, one self-contained HTML file per draft". Every other cell matches the technical spec word for word.
- **Reason:** The technical spec's own test table requires the case-sensitive keyword `HTML` in the OpenClaw row, and its row text has only lowercase `.html`, so the spec's text fails the spec's test (evaluator probe P14). The implemented text matches the contract ("a self-contained HTML file"), AC-1.4, and Business Rule 3.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed. spec-lite.md already says "one self-contained HTML file per draft". technical-spec.md is not auto-modified; this entry records the corrected row text.
