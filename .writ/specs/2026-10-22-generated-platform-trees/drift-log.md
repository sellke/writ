# Drift Log

> Spec: .writ/specs/2026-10-22-generated-platform-trees/
> Created: 2026-10-22
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Adapter Table Parser and Parity Repairs — Drift Report

> Run: 2026-10-22
> Overall Drift: Small

### Deviations

#### [DEV-001] `is_shippable_script` entry pulled forward from Story 4
- **Severity:** Small
- **Spec said:** technical-spec.md → Eval Wiring assigns the `is_shippable_script` dev-only entry for `gen-platform-trees.py` to Story 4 (`install.sh` and `update.sh`); Contract Rule 1 requires the entry.
- **Implementation did:** Added the entry in Story 1, in `scripts/install.sh`, `scripts/update.sh`, and `scripts/unlink.sh` (three byte-identical bodies).
- **Reason:** The moment `scripts/gen-platform-trees.py` exists, `test_agent_cli_contract.py::test_table_complete` and `test_agent_cli_contract_doc.py::test_every_shipped_script_has_exactly_one_row` treat it as shipped and fail; `test_install_update_dev_scripts.sh` requires the three bodies to match. Story assignment moved; scope and intent unchanged.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → Implementation Approach, the check-shape line now says the denylist entry landed in Story 1 across the three scripts.

#### [DEV-002] URL-shaped tokens excluded from vendor identifiers
- **Severity:** Small
- **Spec said:** Rule 4 / technical-spec.md → Vocabulary Rule: `vendor_only` = backticked identifiers in mapping cells minus neutral minus ALLOWLIST.
- **Implementation did:** `identifiers()` in `scripts/gen-platform-trees.py` skips a backticked token that contains `://`. On the real tree the only effect is that `http` (from `` `http://localhost:3000` `` in the cursor `canvas-preview` cell) is not in `vendor_only`.
- **Reason:** `http` is not a tool name; without the exclusion Story 4's coverage check would flag any backticked `http…` token in shipped text as a vendor hit with no neutral name to rewrite it to.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → Implementation Approach, the vocabulary line gains "a token containing `://` is a URL, not an identifier".

#### [DEV-003] Cursor `Plan Mode` row split across columns 2 and 3
- **Severity:** Small
- **Spec said:** technical-spec.md → Plan Mode Rows gives the cursor row a Mapping cell and a Notes cell ("Used by create-spec, plan-product, new-command. If the platform has no toggle, say so and proceed read-only."), while the cursor table is `Tool | Used By | Purpose` and the grammar makes column 3 both mapping and notes.
- **Implementation did:** `adapters/cursor.md` row: column 2 `create-spec, plan-product, new-command`; column 3 `Ask the user to switch to Plan Mode; continue when they have. If the platform has no toggle, say so and proceed read-only.` (story task 1.5's layout).
- **Reason:** The cursor table has no separate notes column; the degradation sentence stays in the cell Story 2's "When unavailable" extraction reads.
- **Resolution:** Auto-amended (Small).
- **Spec amendment:** spec-lite.md → Implementation Approach, the Story 1 line names the cursor layout.
