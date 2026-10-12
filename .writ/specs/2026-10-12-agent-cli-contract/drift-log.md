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

---

## Story 2: Stop Shipping Dev-Only Scripts — Drift Report

> Run: 2026-10-12
> Overall Drift: Medium

### Deviations

#### [DEV-001] update.sh stale handling extended beyond the filter arm
- **Severity:** Medium
- **Spec said:** technical-spec.md "Ship Filter (Story 2)": the existing stale-file logic already removes dev-only copies; the change is the six-name arm only.
- **Implementation did:** `scripts/update.sh` `detect_stale_files` resolves `scripts/` manifest paths at the project root, treats a manifest-listed script the filter rejects as stale, and warns when a kept stale script is locally modified. `write_copy_manifest` carries that script's old baseline forward (`STALE_KEPT_ENTRIES`) so later updates warn again. Side effect: an unmodified installed script deleted upstream is now removed; before, it was skipped.
- **Reason:** The spec's premise was false; AC-2.3 and AC-2.4 could not pass without it. The maintainer approved the patch at the BLOCKED escalation. After Gate 3, the orchestrator limited the warning to `scripts/`, where "kept" holds across runs.
- **Resolution:** Accepted (Medium — warn and continue). Two pre-existing bugs found on the way were filed: `.writ/issues/bugs/2026-10-12-update-deletes-modified-stale-files.md`, `.writ/issues/bugs/2026-10-12-codex-config-baseline-dropped-on-update.md`.
- **Spec amendment:** technical-spec.md "Ship Filter (Story 2)" carries a dated amendment; its Error & Rescue Map row now describes the new behavior.

#### [DEV-002] unlink.sh carries the six-name arm
- **Severity:** Small
- **Spec said:** Change `install.sh` and `update.sh`.
- **Implementation did:** Added the same arm to `scripts/unlink.sh`, which has a byte-identical `is_shippable_script`; the test compares all three bodies.
- **Reason:** Leaving it out would let the three copies diverge.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-003] update-writ.md "Detect stale files" reworded
- **Severity:** Small
- **Spec said:** Reword the Step 3 exclusion list.
- **Implementation did:** Also says that scripts the filter rejects count as stale.
- **Reason:** Matches DEV-001's behavior.
- **Resolution:** Auto-amended
- **Spec amendment:** None.
