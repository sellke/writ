# Drift Log

> Spec: .writ/specs/2026-09-25-jev-judgment-pilot/
> Created: 2026-09-25
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: ADR-027 and Opt-in Resolution — Drift Report

> Run: 2026-09-25
> Overall Drift: Small

### Deviations

#### [DEV-001] Key set with no config line reports `no_config_line`, not `provider_disabled`
- **Severity:** Small
- **Spec said:** Task 1.1, the story Notes, and the technical-spec §5 "Resolve opt-in" row say a key with no config line gives `provider_disabled`. AC-1.3 and technical-spec §1 map a missing line to `no_config_line`.
- **Implementation did:** `no_config_line`. The provider stays disabled and no request is built.
- **Reason:** The acceptance criterion controls, and Story 6's setup prompt fires on `no_config_line`. The intent (a key alone never enables) holds.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Nil input" shadow path and the technical-spec §5 "Resolve opt-in" row now name `no_config_line` for a missing line and `provider_disabled` for `none` or an unknown value. The spec.md Success Criteria wording is unchanged (spec.md is never auto-modified).

#### [DEV-002] `vercel-gateway` status outputs add `reason: model_unpinned`
- **Severity:** Small
- **Spec said:** AC-1.3: `pass` and `reason: enabled`.
- **Implementation did:** The primary reason comes first, then `reason: model_unpinned` on every `vercel-gateway` output.
- **Reason:** Business Rule 5 and technical-spec §1 require `model_unpinned` on every gateway output.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; this matches Business Rule 5.

#### [DEV-003] Summary adds `key_env=<var>` and `export=<var>`
- **Severity:** Small
- **Spec said:** Summary `backend=<name> model=<backend model>`; `no_api_key` names the env var to export.
- **Implementation did:** Adds `key_env=` on pass and `export=` on `no_api_key`.
- **Reason:** Operator clarity. Only variable names are printed, never values; tests confirm this.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-004] `--repo` pointing at a non-directory exits 2
- **Severity:** Small
- **Spec said:** Exit 2 for usage errors; this case is not specified.
- **Implementation did:** stderr message, exit 2.
- **Reason:** A bad path argument is a usage error under Business Rule 2.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-005] No test pins the decision-log line
- **Severity:** Small
- **Spec said:** AC-1.5: the closing commit appends a `jev-pilot:` line.
- **Implementation did:** The line is appended and included in the closing commit; no test checks it.
- **Reason:** The AC requires the line, not a test. It is a workspace artifact.
- **Resolution:** Auto-amended
- **Spec amendment:** None.
