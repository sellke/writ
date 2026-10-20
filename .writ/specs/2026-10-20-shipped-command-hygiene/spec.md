# Shipped Command Hygiene

> **Status:** Not Started
> **Created:** 2026-10-20
> **Owner:** @AdamSellke
> **Dependencies:** [2026-10-20-harness-cuts, 2026-10-20-platform-neutral-names]
> **Phase:** 13 — Subtract and Repair ([roadmap](../../product/roadmap.md), [ADR-030](../../decision-records/adr-030-contract-verifier-boundary-front-door.md))
> **Origin:** Phase 13 decomposition pre-pass (`/implement-phase 13`, 2026-10-20). Finding F7 in `.writ/research/2026-10-19-writ-vs-pstack-research.md`.

## Specification Contract

**Deliverable:** Shipped commands stop pointing at Writ's own development history, `eval.sh` stops pinning command prose that only fixes wording, and `create-spec.md` gets lighter.

**Must Include:**
1. Internal references: remove from every shipped `commands/*.md` the links to Writ's own development artifacts — archived specs (`.writ/specs/archive/...`), research documents (`.writ/research/...`), Writ's ADR files (`.writ/decision-records/adr-0NN-*.md` links, in any relative form), and `calibrated_against` text that cites Writ's own calibration state. Runtime paths stay (`.writ/state/`, `.writ/specs/<spec>/` placeholders, shipped `.writ/docs/` files). Where a removed link carried rationale an installed user needs, replace it with one plain sentence. If an eval check requires `calibrated_against` to exist, keep the field and replace its value with a plain statement of the calibration that does not cite Writ-only paths. A new eval check (name it `shipped-refs`, implemented as a check function or a small `eval-shipped-refs.py` per the repo's pattern) fails when a shipped command contains such a link; prove it with a mutation (add a link, see the check fail).
2. Pin pass: every `require_literal` / `forbid_literal` in `scripts/eval.sh` targeting a file under `commands/` is listed in `.writ/specs/2026-10-20-shipped-command-hygiene/pin-map.md` with a disposition and a one-line reason: **keep** (a safety or governance contract: Prime Directive, `--recommend` and production boundary, gate classes, loop bounds, a script invocation the command must make, verdict provenance), **convert** (replace with a structural check: frontmatter field, heading presence, script-path invocation regex), or **remove** (pins wording only; no behavior depends on it). Every such pin appears in the table. The count of literal pins on command files falls. Safety pins never move to remove.
3. `create-spec.md` reduction pass: start from the cuts the deleted lean twin made (recover it with `git show 617037b:commands/create-spec.lean.md`; the flagged-harness-cuts null result showed those cuts kept exit criteria 2/2). Adopt the cuts that remove behavior coaching, not constraints. `create-spec.md` bytes fall, and the recorded overage for `create-spec.md` in the leanness/governor tooling is repinned downward, never upward. Per ADR-023 the byte figure is a drift signal, not a design target: the reason for each cut is that it removes coaching, not that it saves bytes.

**Hardest Constraint:** the pins exist because prose drifted before. Removing one must never silently drop a safety contract; every remove/convert is justified in `pin-map.md`, and a reviewer can check each row.

**Success criteria:** `shipped-refs` passes on the tree and fails on the mutation; `pin-map.md` lists every command-file pin with disposition and reason; the command-file literal pin count is lower than before; no safety pin is removed; `create-spec.md` is smaller and its recorded overage is lower; full `eval.sh` 0 findings; pytest and bash tests pass.

**Scope out:** `agents/`, `adapters/`, `skills/`, `.writ/docs/` internal references (a later pass); behavior changes to any command; reduction passes on other commands.

**Dependency note:** `2026-10-20-harness-cuts` lands first (deletes the lean twins and the ADR-025 no-op pins) and `2026-10-20-platform-neutral-names` lands before this (renames `/design` → `/writ-design`, touching command text and pins). Line numbers and pin counts will shift; write tasks that re-inventory at implementation time and state the expected order of magnitude, not fixed counts.

**Suggested stories:** (1) strip internal references from shipped commands and add `shipped-refs`; (2) pin map and conversions; (3) `create-spec.md` reduction pass.

## Grounding Notes

Found while grounding the contract on `8528726`. They change no scope.

- The command-file pin count is 221 instances at 206 call sites on `8528726`, not about 114. Expect about 207 after `2026-10-20-harness-cuts` removes 8 lean-file pins and 6 ADR-025 pins.
- The flagged-harness-cuts null result ran `/implement-story` on one story, two runs per arm. `/create-spec` was never invoked, so its 2/2 exit criteria say nothing about `create-spec.lean.md`. Story 3 judges each cut by class (coaching or constraint), and the lean twin is a candidate list, not evidence.
- `revert.md:178` names an archived spec by its old path. The contract grep misses it; the `archived-spec` rule catches it by checking `.writ/specs/archive/<name>/`.
- 23 lines in 10 commands name a Writ ADR as a bare label with no link (`(ADR-013)` in `_preamble.md`, `(ADR-014)` in `new-skill.md`, `Design principle (ADR-001)` in three commands). They are outside the contract's "links" and stay for the later pass. `2026-10-20-harness-cuts` removes some of them with the ADR-025 lines.
- Pytest and bash tests also pin command text (for example `test_jev_setup_hooks.sh`, `test_product_check_direction.py`), and several `eval-*.py` helpers assert command text directly. They are not eval.sh pins and are not in the pin map.

## 🎯 Experience Design

### Who uses it

- **A developer in an installed project** reads a Writ command. Every path it names exists in their project or is a placeholder for one.
- **The maintainer** rewords a command. Wording-only edits no longer require an eval.sh edit; safety contracts still fail eval when they drift.
- **A reviewer** checks `pin-map.md` row by row and `cut-log.md` hunk by hunk.

### Journey

1. Entry: the maintainer runs `bash scripts/eval.sh` or `--check=shipped-refs`.
2. Happy path: `shipped-refs` passes; `command-structure` passes; the pin count in `pin-map.md`'s header is lower than its baseline.
3. Moment of truth: someone pastes `[ADR-017](../.writ/decision-records/adr-017-git-notes-audit-channel.md)` into `ship.md`. Eval fails and names `commands/ship.md:<line>` and the kind.
4. Feedback: one finding per offending line with file, line, kind, and the token.
5. Error: the remediation says to remove the link and, if the user needs the reason, write one plain sentence.

### State Catalog

| State | What the maintainer sees |
|---|---|
| Tree clean | `shipped-refs`: PASS, scenarios N/N |
| ADR link added to a command | FAIL `shipped-refs:commands/<file>:<line>` `adr: decision-records/adr-NNN-…` |
| Dated archive or research path added | FAIL with kind `archived-spec` or `research` |
| Old path to an archived spec | FAIL `archived-spec` (the folder exists under `.writ/specs/archive/`) |
| `calibrated_against` names `.writ/state/<file>` or `.writ/specs/archive/` | FAIL `calibration-state` |
| Runtime path (`.writ/state/`, `.writ/specs/<spec>/`, `.writ/research/[DATE]-…`, `adr-*.md` glob) | No finding |
| Helper missing | Run error, eval exit 2 |
| A rule regex broken | Its self-test scenario fails |
| Heading demoted to prose after conversion | `command-structure` FAIL naming the row |
| Safety pin marked `remove` in the map | Story 2 verification lists the row; the story is not done |
| `create-spec.md` overage repinned upward | Guard test fails |

### Interaction Patterns

- Findings name the file and line first, then the kind, then the token.
- `pin-map.md` and `cut-log.md` are tables a reviewer reads beside `git diff`.

## 📋 Business Rules

1. **Shipped commands.** Every `commands/*.md` except `*.lean.md`, including `_preamble.md`.
2. **Internal reference kinds.** A numbered ADR file link (`decision-records/adr-NNN-…`, any relative prefix); a dated archived-spec path, in archive form or in the old form when the folder now lives under `.writ/specs/archive/`; a dated research document path; and, on a `calibrated_against:` line, any `.writ/state/` or `.writ/specs/archive/` token that is not a glob. Patterns are in `sub-specs/technical-spec.md` → Rules.
3. **Runtime paths stay.** Directories, placeholders, and globs over the user's own files (`.writ/state/…-*.json`, `.writ/specs/<name>/`, `.writ/specs/archive/<name>/`, `.writ/research/[DATE]-…`, `.writ/decision-records/adr-*.md`) and shipped `.writ/docs/` files.
4. **Removal.** Remove the link with its label; never leave a bare `ADR-NNN` where the link was. Add one plain sentence only where an installed user needs the reason. No other text in the file changes.
5. **`calibrated_against` stays.** `eval-loop-bounds.py` requires the key and a value carrying a shipped path token or `no recorded run`, and requires `refactor.md`'s value to contain `no recorded run`. Rewritten values state the calibration plainly and cite only shipped paths or globs.
6. **Pin scope.** Every `require_literal`, `forbid_literal`, and `forbid_literal_ci` call in `scripts/eval.sh` whose target resolves to a file under `commands/`. A loop over several files is one row per file.
7. **Categories.** `prime-directive`, `recommend-boundary`, `gate-class`, `loop-bound`, `script-invocation`, `verdict-provenance`, and `parsed-format` never take `remove`. `structure`, `wording`, and `retired-text` may. A row that fits two categories takes the stricter.
8. **Convert means still enforced.** A converted pin becomes a `heading`, `frontmatter`, or `invocation` row in `scripts/eval-command-structure.py`, and a test shows the row fails on the drift the pin guarded.
9. **Tests move with pins.** A test that mutates a removed or converted pin changes in the same commit. No test that guards a keep row is deleted.
10. **Cuts remove coaching only.** No command behavior changes. Text a keep row, a structural row, or a test requires stays. Step numbers stay.
11. **Repin downward.** `KNOWN_OVER_BUDGET["commands/create-spec.md"]` equals the new measured overage, below its value at Story 3 start and below 29,304. Its comment names coaching removal as the reason, not bytes (ADR-023).
12. **Runtime.** New helpers are Python 3.9 standard library and dev-only (`eval*` is never shipped).

## Detailed Requirements

### Story 1: Strip internal references and add `shipped-refs`
- `scripts/eval-shipped-refs.py` with the four rules, `--root`, self-test scenarios, PASS/FAIL TSV.
- `check_shipped_refs` in `scripts/eval.sh`, registered in `CHECKS`.
- Re-inventory, then remove the references (19 lines in 12 files on the snapshot) and rewrite five `calibrated_against` values.
- Tests: `scripts/tests/test_eval_shipped_refs.py`, including the eval-level mutation.

### Story 2: Pin map and conversions
- Re-inventory with the recipe; confirm no `commands/*.lean.md` remains.
- `pin-map.md`: one row per instance, category, disposition, reason; before and after counts.
- `scripts/eval-command-structure.py` and `check_command_structure` for convert rows; remove-row pins deleted; affected tests updated.

### Story 3: `create-spec.md` reduction pass
- Candidate cuts from the lean twin, decided per row (technical spec table).
- `cut-log.md` maps every diff hunk to a coaching reason.
- Guard test, then the repin in `scripts/tests/test_governor_enforcement.py`.

## Implementation Approach

- **Order:** Story 1, then Story 2, then Story 3. Stories 1 and 2 both edit `scripts/eval.sh`. Story 2 classifies pins on the text Story 1 leaves. Story 3 cuts only text that no keep row, structural row, or test requires.
- **Follow the repo's eval pattern.** A dev-only `eval-*.py` emitter with PASS/FAIL TSV and a thin `check_*` function, like `eval-cursorindexingignore.py` and `check_leanness`.
- **Re-inventory every time.** The counts in this spec are from `8528726`. Each story re-runs its inventory on the tree it starts from, after its tests are written.
- **One concern per commit.** Reference removals, each pin group, and each cut group are separately revertable.
- **Verification:** `uv run --python 3.9 pytest`, `for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`, and `bash scripts/eval.sh` (outside the sandbox).
