# Story 1: Baseline Measurement and the Disposition Ledger

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer who has to prove an extraction changed nothing
**I want to** a transcribed ledger of every check, its sub-checks, its run-order position, and its disposition, taken from the pre-extraction file and pinned to a commit
**So that** "no behavioral drift" is a diff two people can run rather than a claim the implementer makes about their own work

## Scope

No file is extracted in this story. It produces the four artifacts every later story is judged against:

1. The **baseline measurement** — `floor_bytes` and `ceiling_bytes` before any change, plus the pinned pre-extraction copy of `commands/verify-spec.md`.
2. The **disposition ledger** — twelve rows (checks 1–8, P1–P4), transcribed from the source, including the `unstated in source` cells.
3. The **pinned-literal inventory** — the six strings Business Rule 5 requires to survive in the command file (or, for `specs/**`, to stay absent), each re-verified against `scripts/eval.sh` and located in the current file.
4. The **namespace check** — the four skill names re-collision-checked against `skills/` and `.writ/manifest.yaml` as the tree actually stands, under `2026-08-12-disclosure-implement-story`'s Business Rule 3 convention and Business Rule 6 collision protocol.

The ledger and the measurement land in this story's Notes and in `sub-specs/technical-spec.md`'s ledger table (which is a *prediction* to be verified, not a source to be copied).

## Acceptance Criteria

- [ ] Given `commands/verify-spec.md` is 32,110 bytes / 732 lines, when `python3 scripts/measure-invocation.py --root . --command verify-spec` is run **against the tool as fixed on 2026-08-12 (`e8f2a09`)**, then the recorded baseline names `command_bytes`, `eager_bytes`, `floor_bytes`, `conditional_bytes`, and `ceiling_bytes` explicitly, and states that `ceiling_bytes == floor_bytes == 57,070` today because the command declares no skill **and issues no inline `Read skills/…` call**. The baseline also records that the fixed tool models `floor = base + command + eagerly-declared` and `ceiling = floor + inline-read`, which is why this spec's skills are inline-read rather than declared (spec.md § *Approved Scope Change*).
- [ ] Given the pre-extraction file must survive the rewrite, when the baseline is captured, then `git rev-parse HEAD` is recorded as `<base>` and `git show <base>:commands/verify-spec.md` is confirmed to reproduce the 32,110-byte file.
- [ ] Given the disposition ledger is the no-redesign instrument, when it is transcribed, then it carries one row per check (1–8, P1–P4) with: the heading string **verbatim**, the complete sub-check list, the check's position in run order, and the disposition **as the source states it** — with the literal string `unstated in source` wherever no disposition blockquote exists.
- [ ] Given `sub-specs/technical-spec.md` contains a predicted ledger, when the transcription is compared against it, then every discrepancy is resolved **in favor of the source file** and recorded in this story's Notes.
- [ ] Given Business Rule 5, when `scripts/eval.sh` lines 1781–1783 and 1901–1902 are read, then the pinned-literal inventory records all six strings, their enforcing call (`require_literal` / `forbid_literal`), their current locus in `commands/verify-spec.md`, and the minimum retained carrier for each — and confirms `specs/**` is currently absent.
- [ ] Given the skill namespace is shared, when `skills/` and `.writ/manifest.yaml` are re-read, then the current skill list is recorded, the four names are collision-checked by **name and head noun** under the dependency spec's protocol, and any sibling skill this spec should declare instead of authoring is named.
- [ ] Given Business Rule 13, when `.writ/leanness-baseline.json` is read, then the `skills` surface baseline (932 lines / 41,620 chars, recorded 2026-08-04) is recorded together with the projected post-spec value, so Story 5 writes a bound justification rather than discovering the warning.
- [ ] Given Business Rule 4 freezes numbering, when the cross-file citation surface is re-verified by grep, then `release.md`, `ship.md`, `README.md`, and `plan-product.md`'s anchor are confirmed still present at the loci `sub-specs/technical-spec.md` records, and any drift since 2026-08-12 is noted.
- [ ] Given Business Rule 1, when the byte allocations are recorded, then `command_bytes_projected + Σ(skill allocations) ≤ 32,110` is shown as arithmetic, not asserted — **and the per-path arithmetic is shown alongside it**: the `--product` path (`product-doc-audit` + `derivative-regeneration` + `verification-report-authoring`) and the default path (`spec-metadata-diagnosis` + `derivative-regeneration` + `verification-report-authoring`), each against the pre-spec 57,070, with the note that the two paths are mutually exclusive so **no invocation reaches all four skills** and `ceiling_bytes` is an envelope.

## Implementation Tasks

- [ ] 1.1 Record `<base>` = `git rev-parse HEAD`; save `git show <base>:commands/verify-spec.md` and confirm 32,110 bytes / 732 lines
- [ ] 1.2 Run `python3 scripts/measure-invocation.py --root . --command verify-spec`; record the full JSON including `eager_bytes` / `eager_skills` / `conditional_skills`, confirm the tool is at or after `e8f2a09` (its docstring must say `required_skills:` is EAGER), and note that `token_method_validated` is `false` so no token figure may be quoted as measured
- [ ] 1.3 Transcribe the twelve-row disposition ledger from the pinned copy — heading verbatim, sub-checks, run-order position, disposition-as-stated, source line range
- [ ] 1.4 Transcribe the run order separately: Phase 1 → Phase 2 (1→8, collect all before reporting) → Phase 3 → Phase 4 (4.1→4.4, default only) → Phase 5; and the separate `--product` path P1→P4 → P3 regeneration → product report
- [ ] 1.5 Diff the transcription against `sub-specs/technical-spec.md`'s predicted ledger; record every discrepancy and resolve in favor of the source
- [ ] 1.6 Re-read `skills/` and `.writ/manifest.yaml`; record the current skill list and the `skills:` block as it stands before any story appends to it
- [ ] 1.7 Run the collision protocol on all four names — name **and** head noun — against the manifest and every sibling disclosure spec; record any name to declare rather than author, with the ADR-014 `type: promotion` evidence entry it would need
- [ ] 1.8 Build the pinned-literal inventory from `scripts/eval.sh:1781-1783` and `:1901-1902`; locate each string in the current command and name its minimum retained carrier
- [ ] 1.9 Re-verify the cross-file citation surface (`release.md`, `ship.md`, `migrate.md`, `plan-product.md`, `README.md`, `implement-spec.md`, `adapters/claude-code.md`) and note any drift
- [ ] 1.10 Record `.writ/leanness-baseline.json`'s `skills` surface figures and the projected post-spec value for Story 5's bound justification
- [ ] 1.11 Record the byte allocation table with the arithmetic shown, and capture `bash scripts/eval.sh` output as the pre-spec baseline for Success Criterion 10

## Notes

**Technical considerations:**

- The ledger's value is entirely in its `unstated in source` cells. Check 1 has no disposition blockquote; Checks 2, 3, and 5 have none either, and are auto-fixed only by inference from Phase 4's steps. A transcriber who "completes" those cells has already redesigned the command, and every later story will inherit the error as though it were the contract.
- Pin `<base>` before anything else. Once Story 5 rewrites the file, the only way to prove nothing drifted is a copy taken beforehand — and the ledger's line-range column becomes unresolvable without it.
- `measure-invocation.py` always exits 0. Read the JSON; a green run says nothing.
- The predicted ledger in `sub-specs/technical-spec.md` was transcribed during spec authoring on 2026-08-12. It is expected to be correct and must still be verified — if the two disagree, the file wins and the technical spec is wrong.

**Risks / challenges:**

- The dependency's convention landed and was applied at spec-authoring time; the collision check was clean against the six incumbents and the eleven names claimed by the five sibling disclosure specs. **Re-run it anyway** — the siblings were authored in parallel and a name may have been claimed since. If a head noun now collides, the protocol is explicit: declare the existing skill, add an ADR-014 `type: promotion` evidence entry, and drop this spec's allocation for it.
- The dependency may have created something equivalent to `derivative-regeneration` (`/implement-story` also amends `spec-lite.md` on Small drift). Reuse is the correct outcome and it changes this spec's allocations — record it here so Stories 3 and 5 inherit the change.
- The pinned-literal inventory is the finding most likely to be skipped and most expensive to skip. Three of the four `require_literal` strings live inside Check 4d, which is otherwise the densest extraction target in the file. Discovering them in Story 5 means re-authoring both a skill and the command's Phase 2 row.

**Integration points:**

- Stories 2, 3, and 4 author against the ledger.
- Story 5 rebuilds the ledger from command + skills and diffs it against this one; that diff is Success Criterion 3.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `<base>` commit and the pinned pre-extraction file are recorded and reproducible
- [ ] The ledger carries at least one literal `unstated in source` cell (Check 1) — its absence means the transcription resolved an ambiguity
- [ ] The pinned-literal inventory lists all six strings with their enforcing call and minimum retained carrier
- [ ] Skill names are collision-checked against the tree as it stands, by name and by head noun
- [ ] No file under `commands/` or `skills/` was modified by this story

## Context for Agents

- **Business rules:** [BR1 ceiling arithmetic, BR3 disposition ledger and the ambiguity clause, BR4 frozen numbering, BR5 pinned literals, BR11 naming convention and collision protocol, BR13 skills-surface bound justification] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The byte ledger; Skills — provisional names and allocations] — from spec.md → ## Detailed Requirements
- **Load mechanism (amended 2026-08-12):** no `required_skills:`; each skill inline-read at the narrowest step; `ceiling_bytes` is an envelope and per-path figures are required — from spec.md → **Approved Scope Change — Load Mechanism** and Business Rules 1, 10, 14
- **Technical concerns:** [The ceiling was paid every run and why it no longer is; placement is now load-bearing and unchecked; the skill namespace is shared and the dependency lands first] — from spec.md → ## Technical Concerns
- **Contract:** [Hardest constraint: extraction must not change which checks run, in what order, or what each auto-fixes versus reports] — from spec.md → ## Contract (Locked)
- **Technical spec:** [Measurement Instrument; The Disposition Ledger; Cross-File Reference Surface] — from sub-specs/technical-spec.md
