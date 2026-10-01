# Drift Log

> Spec: .writ/specs/2026-10-01-behavioral-verification/
> Created: 2026-10-01
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Recipe Format, Validator, and Product Amendments — Drift Report

> Run: 2026-10-01
> Overall Drift: Small

### Deviations

#### [DEV-001] Recipe grammar fills in unstated value forms
- **Severity:** Small
- **Spec said:** The Recipe Grammar shows a single `Allowed`/`Never` value and an `http://` Ready URL, and lists `bad_timeout` without valid values or a default.
- **Implementation did:** `Allowed`/`Never` accept comma-separated globs; `Ready when` accepts an http(s) URL or `port N` (Run Contract step 5); `Ready timeout` accepts `30s` or `30` and defaults to 120 s (the State Catalog's "not ready after 120s"); `Safety: none` accepts an em dash, en dash, or hyphen; a `Variable` with no `Allowed` is `missing_safety`.
- **Reason:** Each fills a gap the spec left open without changing the interface Stories 2–5 consume; refuse-by-default is preserved.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Recipe =" line records the value forms; the format doc is the grammar of record.
