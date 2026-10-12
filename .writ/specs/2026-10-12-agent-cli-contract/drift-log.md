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

---

## Story 3: Agent CLI Contract Test — Drift Report

> Run: 2026-10-12
> Overall Drift: Medium

### Deviations

#### [DEV-001] Check-tool exit-code rule amended
- **Severity:** Medium
- **Spec said:** Business Rule 4: exit 0 pass, 1 fail, 2 unverifiable.
- **Implementation did:** Exit 0 when the check ran (`pass` or `unverifiable`), 1 on `fail`, 2 on usage or could-not-start. Data tools may exit non-zero with their normal verdict document; `blocker` is required only when the tool cannot do its job.
- **Reason:** The first test run flagged 8 check scripts whose `--help` documents exit 0 for `unverifiable`; `.writ/docs/quality-signal-classification.md` says "`unverifiable` never exits 2", and gate callers treat exit 2 as a helper failure. The maintainer chose to match the scripts. Only `app-verify.py` exits 2 on `unverifiable`; Story 5 fixes it.
- **Resolution:** Accepted (Medium — maintainer decision).
- **Spec amendment:** spec.md Business Rules 3–4 and State Catalog, spec-lite.md, ADR-029 amendment, `.writ/docs/agent-cli-contract.md` Data and Check shape, Stories 4 and 5.

#### [DEV-002] Separate `exit_code` rule key
- **Severity:** Small
- **Spec said:** The test checks shape; no exit-code test is named.
- **Implementation did:** `test_exit_code_smoke` checks the exit code of each check smoke whose line 1 is a verdict, with a fixture for both outcomes.
- **Reason:** Enforces Business Rule 4 as amended. No current entry needs it; `app-verify.py`'s exit 2 surfaces once Story 5 fixes its line 1.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-003] Stricter shell `--help` rule
- **Severity:** Medium
- **Spec said:** technical-spec.md: shell `--help` exits 0 or prints usage.
- **Implementation did:** Requires a `usage:` line naming the script.
- **Reason:** The looser rule passes `check-agent-parity.sh`, which runs the check on `--help` and exits 0. New Story 5 debt (`check-agent-parity.sh` help and bad flag, `lint-skill.sh` help).
- **Resolution:** Accepted. Story 5 tasks 5.2 and 5.3 now cover usage handling.
- **Spec amendment:** Story 5 tasks 5.2, 5.3; spec.md Story 5 requirements.

#### [DEV-004] Shell scripts in the shape smoke
- **Severity:** Small
- **Spec said:** Shell scripts get table, help, and bad-flag checks only.
- **Implementation did:** The three shell scripts are also smoked for shape.
- **Reason:** "Only" applies to the static scans; AC-3.5 covers every check script, and Story 5 needs the enforcement.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-005] One smoke invocation per script
- **Severity:** Medium
- **Spec said:** `KNOWN_VIOLATIONS` lists the remaining debt.
- **Implementation did:** Each script is smoked in one mode. Non-conforming modes not smoked (goal-emit pass path, review-panel trial-*, boundary-map crossings, app-verify touched, gen-skill write mode) are not in `KNOWN_VIOLATIONS`; the contract doc's `### Notes` remain the full debt list.
- **Reason:** One case per `(script, rule)` key keeps xfail mapping simple.
- **Resolution:** Accepted. Stories 4 and 5 add a smoke case for each mode they fix before fixing it.
- **Spec amendment:** Story 4 task 4.4, Story 5 task 5.5.

---

## Story 4: Bring Data Tools and Python Check Tools into Conformance — Drift Report

> Run: 2026-10-12
> Overall Drift: Small

### Deviations

#### [DEV-001] review-panel trial-record and trial-label also fixed
- **Severity:** Small
- **Spec said:** Task 4.4 named `trial-init` and `trial-prepare`.
- **Implementation did:** All four trial subcommands that write a file print `pass` on line 1.
- **Reason:** The contract applies the check shape to every mode. No caller parses these words.
- **Resolution:** Auto-amended
- **Spec amendment:** None (covered by the contract's every-mode rule).

#### [DEV-002] A saved compute blocker reads as an unreadable map
- **Severity:** Small
- **Spec said:** `compute` prints a blocker on a story error; silent on how `crossings` reads it.
- **Implementation did:** `boundary-map.py` `load_map` treats a dict holding `blocker` as unreadable, so `crossings` routes `unverifiable` / `map_unreadable` to review-agent, as an empty file did before.
- **Reason:** Gate 0.5 saves `compute` output; without this, a saved blocker would read as an empty map and flag every file.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-003] Atomic writes keep normal permissions
- **Severity:** Small
- **Spec said:** Temp file in the same directory, then `os.replace`.
- **Implementation did:** `goal-emit.py` sets the mode a plain write would give (`mkstemp` creates 0600); `roadmap-sync.py` keeps the target's existing mode.
- **Reason:** Without it, emitted files would become 0600.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-004] review-panel tally and trial-report verdict words moved to Story 5
- **Severity:** Small
- **Spec said:** Every check-tool mode prints `pass`/`fail`/`unverifiable` on line 1.
- **Implementation did:** Not changed in Story 4: `tally` prints `block` and `trial-report` prints `keep`/`remove`. The contract test does not smoke either mode. Found by Gate 3.
- **Reason:** `tally` feeds Gate 3's panel paragraph in `implement-story.md`, which Story 5 already edits under the same byte pin.
- **Resolution:** Accepted. Story 5 task 5.5 now fixes both modes and adds smokes; task 5.4 also clarifies Gate 2.5's `--surface <class>` wording.
- **Spec amendment:** Story 5 tasks 5.4 and 5.5.
