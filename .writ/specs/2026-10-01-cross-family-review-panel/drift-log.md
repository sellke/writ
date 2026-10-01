# Drift Log

> Spec: .writ/specs/2026-10-01-cross-family-review-panel/
> Created: 2026-10-01
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Panel Config, Vendor Table, Status, and Amendments — Drift Report

> Run: 2026-10-01
> Overall Drift: Small

### Deviations

#### [DEV-001] Config key read case-insensitively
- **Severity:** Small
- **Spec said:** Read the `- **Review Panel:**` line "the way `scripts/jev-judge.py` reads `- **Judgment Provider:**`" (that regex is case-sensitive on the key); only the value `none` is specified as case-insensitive.
- **Implementation did:** The key matches case-insensitively (`- **review panel:**` also counts); the first matching line still wins.
- **Reason:** `.writ/docs/config-format.md` → Rules states "Keys are case-insensitive on read", the file format's own contract. A human still writes the line either way, so consent is unchanged.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Error Handling" records the key-case rule.

#### [DEV-002] Unreadable config is a usage error
- **Severity:** Small
- **Spec said:** Missing line → `unverifiable no_config_line`; unreadable repo → exit 2.
- **Implementation did:** A missing `.writ/config.md` is `no_config_line`; an existing `config.md` that cannot be read or decoded, or a repo directory without read permission, exits 2.
- **Reason:** Reporting an unreadable consent file as "no line" would hide the error; exit 2 is the spec's usage path and still leaves Gate 3 unchanged (the Gate 3 paragraph acts only on `pass`).
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Error Handling" records the unreadable-config exit.
