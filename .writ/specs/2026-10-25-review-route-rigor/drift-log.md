# Drift Log

> Spec: .writ/specs/2026-10-25-review-route-rigor/
> Created: 2026-10-29
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Upgrade switches — Drift Report

> Run: 2026-10-29
> Overall Drift: Medium

### Deviations

#### [DEV-001] `switch` prints a state word on line 1, an exception to the agent CLI check shape
- **Severity:** Medium
- **Spec said:** technical-spec § Resolver calls the output "check shape" with line 1 `on` or `off`; AC-1.1–1.3 pin line 1 to `on`/`off`.
- **Implementation did:** Line 1 is `on` or `off`, as the ACs require. `.writ/docs/agent-cli-contract.md` gained a Notes bullet recording `review-override.py switch` as a documented exception to the Check shape (line 1 is `pass`/`fail`/`unverifiable` everywhere else; `review-panel.py status` and `jev-judge.py status` print `pass` and carry state in `reason:` lines).
- **Reason:** The ACs and the Check-shape rule cannot both hold. The locked spec answers the question, and Stories 2–4 branch on line 1, so the shape is frozen here. `test_agent_cli_contract.py` has no smoke row for `switch`.
- **Resolution:** Flagged for review
- **Spec amendment:** N/A — flagged for post-implementation review. If the contract should stay uniform, a later spec can move the state to a `reason:` line and print `pass` on line 1.

#### [DEV-002] `on` is matched in any case
- **Severity:** Small
- **Spec said:** "value `on` or empty → `config_on`"; only `off` is described as "any case".
- **Implementation did:** `ON` and `On` resolve to `config_on`, not `malformed_value ON`.
- **Reason:** Line 1 and the exit code are the same either way; only the reason text differs. Matches the rule that only `off` turns a switch off.
- **Resolution:** Auto-amended
- **Spec amendment:** technical-spec § Resolver row "value `on` or empty" reads as "value `on` (any case) or empty". None needed in spec-lite.md; it says only `off` turns a switch off.

#### [DEV-003] A script edit regenerates the plugin tree
- **Severity:** Small
- **Spec said:** task 1.4: "confirm no generated tree changes are needed for a script-only edit"; technical-spec regenerates trees after stories that edit `agents/`, `commands/`, or `skills/`.
- **Implementation did:** Ran `python3 scripts/gen-platform-trees.py`, which rewrote `plugins/writ/scripts/review-override.py`; `--check` fails without it.
- **Reason:** `scripts/` is mirrored into `plugins/writ/scripts/`, so the task's premise was wrong. The change matches Must Include 7.
- **Resolution:** Auto-amended
- **Spec amendment:** Task 1.4 reads "run `python3 scripts/gen-platform-trees.py`; `scripts/` is mirrored into `plugins/writ/scripts/`". None needed in spec-lite.md; it already says to regenerate trees.
