# Drift Log

> Spec: .writ/specs/2026-10-12-agent-cli-contract/
> Created: 2026-10-12
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Contract Doc and ADR-029 Amendment — Drift Report

> Run: 2026-10-12
> Overall Drift: Medium

### Deviations

#### [DEV-001] Check shape covers every mode, including write modes
- **Severity:** Medium
- **Spec said:** Business Rule 4: stdout line 1 is the verdict. The spec is silent on modes that write files.
- **Implementation did:** `.writ/docs/agent-cli-contract.md` says every subcommand and mode of a check tool prints the check shape, including write modes. `review-panel.py` `trial-init`/`trial-prepare`, `gen-codex-agent-tomls.py` write mode, and `gen-skill.sh` write mode become conformance work.
- **Reason:** Follows the maintainer's 2026-10-12 decision to keep the check rule strict. An agent should not need to know which mode it ran to parse the output.
- **Resolution:** Accepted (Medium — warn and continue). The conformance work splits into Story 4 (data tools and Python check tools) and a new Story 5 (shell scripts and app-verify line 1), per the same maintainer decision.
- **Spec amendment:** Story 5 added; Story 4 narrowed (recorded in spec.md and user-stories/README.md before Story 3 runs).

#### [DEV-002] Classification rulings beyond the spec's minimum list
- **Severity:** Medium
- **Spec said:** Story 4 fixes at minimum `revert-resolve.py` and `knowledge-consolidate.py`, plus anything else the contract test flags.
- **Implementation did:** The audit flagged about 15 scripts: app-verify, arch-lint, boundary-map, change-surface, check-agent-parity, gen-codex-agent-tomls, gen-skill, goal-emit, knowledge-consolidate, lint-skill, review-panel, revert-resolve, test-integrity, verdict-provenance. The doc's `### Notes` record what each prints today.
- **Reason:** A strict rule applied to the real scripts.
- **Resolution:** Accepted. The spec adds Story 5. The doc's State section also notes that `roadmap-sync.py` and `goal-emit.py` write in place, which belongs to Story 4.
- **Spec amendment:** Story 4 scope lists the flagged data and Python check scripts plus the two in-place writers.

#### [DEV-003] Dev-only note states Story 2 behavior
- **Severity:** Small
- **Spec said:** Story 2 makes update remove unmodified dev-only copies.
- **Implementation did:** The doc's "Not in the table" note states that `/update-writ` removes them.
- **Reason:** True once Story 2 lands. Both stories ship on the same branch.
- **Resolution:** Auto-amended (no change needed)
- **Spec amendment:** None.
