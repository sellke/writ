# Drift Log — Leanness Guardian

> Tracks deviations between spec contract and implementation reality.

## Story 1: Leanness Tripwire

#### [DEV-001] Registry parity is directional, not bidirectional across all three registries
- **Severity:** Medium (contract-level; user-approved before implementation)
- **Spec said:** `spec.md` AC2 and `sub-specs/technical-spec.md` required every
  non-infra `commands/*.md` to appear in **both** the README command table **and**
  the `/status` allowlist ("orphan = absent from README table *or* status allowlist").
- **Reality found:** The `/status` "Maintainer Note: Command Allowlist" is an
  intentionally **curated suggestion subset** (27 entries), not a complete command
  registry. Three shipping commands — `knowledge`, `new-skill`, `create-uat-plan` —
  are deliberately excluded because `/status` does not proactively suggest them.
  Enforcing "both" would (a) FAIL the clean repo, breaking Success Criterion #1, or
  (b) force adding those commands to the allowlist, breaking Success Criterion #6 /
  the "allowlist unchanged" hard business rule. The two readings are mutually
  exclusive; "both" is impossible.
- **Resolution:** Adopt the **directional** parity already defined in `spec-lite.md`
  "Shadow Paths to Verify":
  - **README table** is the authoritative full registry → **bidirectional** parity
    with `commands/*.md` (orphan = file missing from README; phantom = README names
    a missing file). Holds today: 30 ↔ 30.
  - **`/status` allowlist** is a curated subset → **one-directional** check only
    (phantom = allowlist names a command with no file). Never flag a command for
    being absent from the allowlist.
  - Both AC fixtures still FAIL: orphan (`ghost.md` absent from README) and phantom
    (allowlist names a missing command).
- **User decision:** Confirmed via AskQuestion before any code was written
  (2026-07-11). Selected "Directional parity per spec-lite."
- **Spec-lite updated:** No change needed — spec-lite already frames it directionally.
- **Spec + technical-spec updated:** Yes — AC2 wording and the technical-spec
  "Registry parity" section reworded to the directional contract; this entry is the
  authoritative record.

#### [DEV-002] `commands` metric counts all command files (incl. `_preamble`)
- **Severity:** Small
- **Spec said:** Baseline `commands: 31`; parity excludes `_preamble.md`.
- **Implementation did:** The aggregate **weight/count metric** counts all
  `commands/*.md` (31 files, 10659 lines, 484616 chars — matches the seeded
  baseline exactly). The **parity check** operates only on the non-infra set (30).
- **Resolution:** Auto-amended — the count metric measures total surface weight
  (infra included, matching the stated baseline); parity excludes infra by design.
  Consistent with the spec's own baseline numbers.
- **Spec-lite updated:** No.
