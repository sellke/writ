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

---

## Story 3: Upgrade-Path Test, Reference Gate, and Issue Resolutions — Drift Report

> Run: 2026-10-21
> Overall Drift: Medium

### Deviations

#### [DEV-004] Gate record list exempts all of `.writ/specs/` instead of named folders
- **Severity:** Medium
- **Spec said:** The contract's Hardest Constraint lists `.writ/specs/archive/` as the spec record path. Business Rule 12 and technical-spec.md → Record list add this spec's folder and the parity spec's folder, and allow another in-flight `.writ/specs/<folder>/` one at a time with a reason and a drift-log entry. The story Note says "Record list stays narrow."
- **Implementation did:** `RECORD_PREFIXES` replaces `.writ/specs/archive/` and the two named folders with `.writ/specs/`. Today this also exempts the in-flight `2026-10-20-ci-and-update-integrity` and `2026-10-20-shipped-command-hygiene` folders, which name `/design`, and every later spec folder. Story 1's `test_cursor_ide_browser_confined` shares the list.
- **Reason:** The phase orchestrator directed it, citing the Phase 13 precedent from harness-cuts (DEV-009): a repo-wide guard grep excludes `.writ/specs/` as a whole, because spec folders, including UAT plans and drift logs other Phase 13 specs write into them, are planning and history records. Spec folders never ship: `install.sh` and `update.sh` copy only `.writ/docs/*.md` from `.writ/`. The evaluator's probes show every shipped path is still guarded. The three dated snapshots stay in the list. Medium because it replaces a path the contract names and drops the per-folder review step.
- **Resolution:** Flagged for review
- **Spec amendment:** spec-lite.md → For Review Agents → Business Rules: the record-list line now names all of `.writ/specs/`. spec.md and technical-spec.md are not changed.

#### [DEV-005] Gate fixture's fourth reported line moved out of `.writ/specs/`
- **Severity:** Small
- **Spec said:** technical-spec.md → Reference Gate → Tests: the fixture reports `.writ/specs/2026-01-01-other/spec.md` (`/design`) as its fourth line.
- **Implementation did:** That line is now in the ignored set. `.writ/docs/other.md` is reported instead, which shows only the three named snapshots are exempt in `.writ/docs/`. The fixture also plants the snapshot path that has a space, to exercise `--null`.
- **Reason:** Follows from DEV-004. The fixture still reports exactly four lines and proves each ignore rule.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed in spec-lite (it gives no fixture detail); recorded here.

#### [DEV-006] `.writ/context.md` added to the gate's record list
- **Severity:** Small
- **Spec said:** The record list holds the contract paths, the named spec folders, and three dated snapshots; only in-flight spec folders may be added.
- **Implementation did:** `RECORD_PREFIXES` includes `.writ/context.md`, with the reason "Regenerated after each story; quotes story and drift titles from the spec folders."
- **Reason:** The first real-repo gate run hit `.writ/context.md`, which quoted Story 2's title. The file is tracked but never shipped, it is rewritten after every story from spec-folder records, and it is not one of the shipped paths the technical spec forbids adding. A hit there cannot become a dead pointer for users.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md record-list line names `.writ/context.md`.
