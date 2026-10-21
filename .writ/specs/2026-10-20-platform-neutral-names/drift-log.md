# Drift Log

> Spec: .writ/specs/2026-10-20-platform-neutral-names/
> Created: 2026-10-21
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Canvas-Preview Capability in `/prototype` and the Four Adapters — Drift Report

> Run: 2026-10-21
> Overall Drift: Small

### Deviations

#### [DEV-001] OpenClaw row says "HTML file" where the technical spec's row text says "file"
- **Severity:** Small
- **Spec said:** technical-spec.md → Adapter rows gives the OpenClaw second cell as `` `Write({ path: ".writ/prototypes/<date>-<slug>/<draft>.html" })`, one self-contained file per draft ``.
- **Implementation did:** `adapters/openclaw.md` reads "…, one self-contained HTML file per draft". Every other cell matches the technical spec word for word.
- **Reason:** The technical spec's own test table requires the case-sensitive keyword `HTML` in the OpenClaw row, and its row text has only lowercase `.html`, so the spec's text fails the spec's test (evaluator probe P14). The implemented text matches the contract ("a self-contained HTML file"), AC-1.4, and Business Rule 3.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed. spec-lite.md already says "one self-contained HTML file per draft". technical-spec.md is not auto-modified; this entry records the corrected row text.

---

## Story 2: Rename `/design` to `/writ-design` Across Every Reference — Drift Report

> Run: 2026-10-21
> Overall Drift: Small

### Deviations

#### [DEV-002] Governor ledger re-pinned for the create-spec Step 1.5 rename
- **Severity:** Small
- **Spec said:** technical-spec.md → Files in Scope and spec-lite.md list no change to `scripts/tests/test_governor_enforcement.py`. The Rename table requires the Step 1.5 text "wireframe conventions from `/writ-design` command".
- **Implementation did:** `KNOWN_OVER_BUDGET["commands/create-spec.md"]` went from 28733 to 28738, with a dated comment naming this spec and story.
- **Reason:** `test_governor_enforcement.py` and `test_harness_cuts.py` (`OverageLedgerFellTest`) require the ledger to equal the file's exact overage. The required text adds 5 bytes, and three tests failed without the re-pin. Rewording the bullet or trimming other create-spec text would each be a larger deviation. 28738 stays under the hygiene spec's 29304 bound.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S2 Files in Scope names the ledger.

#### [DEV-003] Inventory missed the bare `design` in the `/status` Maintainer Note allowlist
- **Severity:** Small
- **Spec said:** technical-spec.md → Reference Inventory lists one `commands/status.md` line (the slash-command allowlist). "Rename-class references the grep misses" names no status.md line.
- **Implementation did:** Also renamed `` `design` `` to `` `writ-design` `` in `commands/status.md` § Maintainer Note: Command Allowlist.
- **Reason:** It names the Writ command, so Must Include 2 and Business Rule 7 cover it. `eval-leanness.py` checks that list for phantom commands; the review agent confirmed the old name there yields a structural finding, which would fail AC-2.5's 0-findings bar.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S2 Files in Scope says both `status.md` command lists.
