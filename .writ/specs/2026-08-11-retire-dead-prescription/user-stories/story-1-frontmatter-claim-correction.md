# Story 1: Correct the False Frontmatter Claim

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** Writ maintainer building the component contract on `system-instructions.md`
**I want to** the root contract to state what commands actually carry — `---` YAML frontmatter in 32/32 files — instead of asserting they carry none
**So that** ADR-020's chosen carrier is documented truthfully and `/new-command` stops teaching a workaround for a constraint that no longer exists

## Acceptance Criteria

- [ ] Given `system-instructions.md` § Model Tiers → Carrier per file type, when the Commands bullet is read, then it states that command files carry `model_tier` in `---` YAML frontmatter (advisory only) and contains no claim that commands lack a frontmatter or config-block mechanism.
- [ ] Given the literals `verified 0/31 files` and `no frontmatter mechanism` (and the variant `carry no frontmatter mechanism`), when this story's own files are grepped (`system-instructions.md`, `cursor/writ.mdc`, `commands/new-command.md`), then zero hits are returned. `.writ/docs/model-tiers.md` and `scripts/lint-skill.sh` carry the same claim and were transferred to **Story 6** on 2026-08-11 — this story neither clears nor edits them. See the Risks note on `commands/new-command.md`'s contested ownership.
- [ ] Given the same literals grepped across `.writ/decision-records/`, `.writ/specs/archive/`, `.writ/research/`, and `CHANGELOG.md`, when compared to the pre-story hit counts, then every count is unchanged — history is not rewritten.
- [ ] Given `commands/new-command.md`, when a command author follows Step 2.1 and the Step 2.2 checklist, then they are instructed to declare advisory `model_tier` in the generated command's frontmatter, not as a prose note. (`.writ/docs/model-tiers.md`'s matching carrier table row is Story 6's deliverable, not this story's.)
- [ ] Given `system-instructions.md` and `cursor/writ.mdc` after the edit, when the § Model Tiers section of each is compared line for line, then the two are identical.
- [ ] Given the full validation suite after the edit, when `bash scripts/eval.sh` runs, then it reports `Findings: 0` with no new `eval-exempt:` marker introduced by this story.

## Implementation Tasks

- [ ] 1.1 Re-measure before editing: `ls commands/*.md | wc -l` and a per-file `head -1` frontmatter check. Record the exact numbers used in the replacement prose (expected 32 files, 32 with `---`, of which 31 are commands and 1 is `_preamble.md`). Business Rule 1 forbids swapping one unverified figure for another.
- [ ] 1.2 Rewrite the Commands bullet in `system-instructions.md` § Model Tiers → "Carrier per file type" (currently line 277) and delete the fenced prose-note example beneath it. Leave the Skills and Agents bullets untouched — both are accurate as measured.
- [ ] 1.3 Mirror the identical change into `cursor/writ.mdc`, then diff the § Model Tiers section of both files to confirm they match. `prime-directive-sync` does not cover this section — the diff is the only check.
- [ ] 1.4 Update `commands/new-command.md`: Step 2.1's Model tier note (lines 145–151) and the Step 2.2 checklist bullet (line 171). Both currently prescribe the prose note; both become frontmatter guidance. Keep the ADR-016 and `.writ/docs/model-tiers.md` references intact.
- [ ] 1.5 Verify: run the active-surface and historical-surface greps from the acceptance criteria (use `grep -F` — the prose-note literal contains regex metacharacters), run `bash scripts/eval.sh` to `Findings: 0`, and run `bash scripts/gen-skill.sh --check` to exit 0.

> **Transferred out on 2026-08-11 (approved scope addition).** The former Tasks 1.5 (`.writ/docs/model-tiers.md` lines 45/95/97) and 1.6 (the disposition of `scripts/lint-skill.sh`'s prose-note regex branch) now belong to **Story 6**, which depends on Story 2. Task 1.6 permitted the lint branch to be either removed or retained; Story 6 makes that a decided deliverable rather than an implementer's option, so Story 2 no longer needs a recorded choice from this story to know what it will find.

## Notes

**Technical considerations:**

- The false claim is load-bearing in three directions, which is why this story is larger than a one-line edit: ADR-020 cites it as the justification for choosing frontmatter, `commands/new-command.md` teaches the workaround forward into every future command, and `scripts/lint-skill.sh` carries a bespoke regex that exists only to parse the workaround's output. Fixing only `system-instructions.md` leaves the prescription alive in the authoring path.
- `grep -rn "Model tier (advisory only)" commands/ agents/ skills/` returns exactly 2 hits, both in `commands/new-command.md` (the template at line 148 and the checklist at line 171). No shipped command carries the note, so retiring the prescribed carrier orphans no existing file and requires no migration pass.
- `commands/_preamble.md` is the 32nd file and is excluded from `check_manifest`'s command-parity scan by the `_*.md` prefix rule (`scripts/eval.sh:490`). State the count precisely — "32/32 files in `commands/`, comprising 31 commands and `_preamble.md`" — rather than implying 32 commands.
- New prose in `commands/*.md`, `agents/*.md`, `system-instructions.md`, and `cursor/writ.mdc` is scanned by `check_anti_sycophancy()` against `.writ/eval/anti-sycophancy-phrases.txt`. Write the correction plainly.
- This story does **not** add `model_tier:` to any command's frontmatter. It documents the carrier; populating it is not in this spec (spec.md → Out of Scope).

**Risks / challenges:**

- **The mirror has no gate.** `cursor/writ.mdc` is a full 300-line mirror plus a dogfooding appendix, but `check_prime_directive_sync()` diffs only the `## Prime Directive` section. Editing `system-instructions.md` alone leaves the suite green and the mirror wrong. Task 1.3 exists solely to catch this.
- Risk of over-broad substitution. A repo-wide `sed` for `0/31` would rewrite `.writ/decision-records/adr-020-component-contract.md:55` and `:112`, which cite the false claim deliberately as the thing being corrected. Scope every replacement to the named files.
- **`commands/new-command.md` was double-claimed — RESOLVED 2026-08-11, this story wins.** This story's Task 1.4 converts the Model tier note to frontmatter guidance. The sibling spec `2026-08-11-component-contract` had also claimed it, asserting the prose-note format "stays locked." **Ruling: the Model tier note, the Step 2.2 checklist bullet, and the entire prose-note carrier belong to this spec**, on the locked contracts rather than on preference — this spec's clause (a) reads *"The prose-note workaround for advisory `model_tier` is replaced by frontmatter,"* while the sibling's contract says only that `new-command.md` "updates so newly authored commands are born compliant" and never mentions `model_tier`. The sibling's stated rationale (that `lint-skill.sh` and `.writ/docs/model-tiers.md` depend on the prose format) does not survive this spec's own **Story 6**, which deletes both dependencies. The sibling has been amended: its Business Rule 4, Out of Scope, § Why This Exists, technical spec §4, and Story 1's AC and Task 1.6 now require `git diff` to show **zero** changes to these lines, and to escalate rather than repair if they still prescribe a prose note when it runs. Single-writer-per-file is restored; no merge-order workaround is involved.

**Integration points:**

- Story 2 edits the same `system-instructions.md` § Model Tiers section — it depends on this story landing first. It no longer depends on a recorded decision from this story about `scripts/lint-skill.sh`; that function's prose-note branch moved to Story 6, which runs after Story 2.
- Story 6 carries the same correction into `.writ/docs/model-tiers.md` and `scripts/lint-skill.sh`. Its Task 6.3 verifies `commands/new-command.md`'s actual behavior before describing it, so whatever this story (or the sibling spec) leaves in that file is measured, not assumed.
- ADR-020 (`.writ/decision-records/adr-020-component-contract.md:55`, `:112`) names this correction as a prerequisite for its frontmatter choice. The ADR itself is not edited (Business Rule 3).

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/eval.sh` reports `Findings: 0`
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (measured, not asserted), Rule 2 (`cursor/writ.mdc` is a full mirror with no gate over this section), Rule 3 (active surface only — history preserved), Rule 4 (`Findings: 0` per story, no self-serving exemptions), Rule 5 (no new contract fields)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [(a) The false frontmatter claim, and the carrier it justified — including the downstream-file table] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [The mirror constraint; the orphaned lint branch; anti-sycophancy interaction] — from sub-specs/technical-spec.md → "The mirror constraint" and "(a) The false frontmatter claim — Story 1"
- **Contract:** [Must include (a): the "verified 0/31 files" claim is false, 32/32 carry frontmatter, prose-note workaround replaced by frontmatter; Hardest constraint: every edit leaves the suite at `Findings: 0`] — from spec.md → ## Contract (Locked)
