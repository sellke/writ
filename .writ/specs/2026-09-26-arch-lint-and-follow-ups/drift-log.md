# Drift Log

> Spec: .writ/specs/2026-09-26-arch-lint-and-follow-ups/
> Created: 2026-09-26
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Codex TOML Freshness — Drift Report

> Run: 2026-09-26
> Overall Drift: Small

### Deviations

#### [DEV-001] eval.sh check registered as `codex-tomls`
- **Severity:** Small
- **Spec said:** Task 1.7 verifies with `bash scripts/eval.sh --check=codex_tomls`.
- **Implementation did:** Registers the check as `codex-tomls` in `CHECKS`; the function is `check_codex_tomls` as specified.
- **Reason:** Every `CHECKS` name is hyphenated and `eval.sh` rejects unregistered names, so the underscore spelling could never run.
- **Resolution:** Auto-amended
- **Spec amendment:** story-1 task 1.7 now reads `--check=codex-tomls`.

#### [DEV-002] An unmapped stem without a TOML reports only `unmapped`
- **Severity:** Small
- **Spec said:** One `reason:` line per problem from `stale|missing|orphan|unmapped`.
- **Implementation did:** An unmapped stem yields a single `unmapped` line, never an extra `missing` line.
- **Reason:** No expected TOML exists until the stem is mapped, so `missing` would repeat the same fix; one root-cause line per stem.
- **Resolution:** Auto-amended
- **Spec amendment:** Reason kinds are exclusive per stem, `unmapped` first; recorded here, pinned by `test_gen_codex_agent_tomls.py`.

#### [DEV-003] Write mode leaves orphan TOMLs in place
- **Severity:** Small
- **Spec said:** Nothing about orphans in write mode.
- **Implementation did:** Write mode never deletes; `--check` and `eval.sh` flag orphans with remediation "Delete the orphan TOML or restore agents/<stem>.md".
- **Reason:** Deletion is a destructive side effect the spec never approved.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; recorded here.

#### [DEV-004] Spec slugs added to four older test files
- **Severity:** Small
- **Spec said:** Nothing; the files belong to archived specs.
- **Implementation did:** Named the owning spec near the AC tags in `test_goal_emit_command_hooks.sh` (stage4-goal-emit), `test_measure_invocation.py` (phase11-repair-and-baseline), `test_update_claude_md.sh` (claude-md-install-merge) and `test_spec_analyze_command_hooks.sh` (stage3-spec-analysis). Comment-only.
- **Reason:** Unattributed `AC-2.x` tags were credited to this spec, so `AC-2.5` dangled and would block `eval.sh`; the attribution convention in `.writ/docs/acceptance-criteria-ids.md` is to name the spec next to AC tags.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; ac-trace for this spec and the four owning specs reports no new findings.
