# Story 2: Convention Detection and Commit Organization Skills

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** `/ship` invocation that never reaches commit splitting
**I want** the convention-detection chains and the commit-grouping heuristic to live in skills the harness loads only when they are needed
**So that** 7,003 bytes of Steps 1 and 4 stop being paid on every run, and the grouping capability becomes available to any other command that needs it — without the commit-plan approval gate or the message grammar moving anywhere

## Acceptance Criteria

- [ ] Given `/new-skill` is the authoring path, when this story lands, then `skills/repo-convention-detection/SKILL.md` and `skills/commit-organization/SKILL.md` exist, each with `disable-model-invocation: true`, `status: candidate`, a `status_evidence` line naming the extraction date and `commands/ship.md` as the single consumer, and `## Purpose` + `## When to Use` sections — and `bash scripts/lint-skill.sh skills/*/SKILL.md` exits 0.
- [ ] Given `.writ/manifest.yaml` is the registry, when this story lands, then it carries two new alphabetically placed `skills:` entries (`commit-organization`, `repo-convention-detection`) each with `name`, `file`, `description`, `status: candidate`, and tags, and `bash scripts/gen-skill.sh --check` reports no delta against the regenerated root `SKILL.md`.
- [ ] Given Step 1 is 2,821 bytes covering four detection chains, when this story lands, then `repo-convention-detection` carries all of them byte-faithful in meaning — the `.writ/config.md` precedence order and its three-step shape, the default-branch chain (`git remote show origin` → local `main`/`master`/`develop` → ask), the test-runner chain (`package.json` → `Makefile` → `pytest.ini`/`setup.cfg`/`pyproject.toml` → `mix.exs` → `Cargo.toml` → ask), the merge-strategy chain, the PR-tool chain, the persist-once offer that writes only on **y**, and both opinionated defaults with the reasoning that justifies them.
- [ ] Given Step 4 is 4,182 bytes, when this story lands, then `commit-organization` carries the five-row layer/grouping/prefix table, the four "when NOT to split" rules, the buildable-intermediate-state rule including its `--test`-dependent variant, the five-stage staging order, the per-commit buildability check with its merge-adjacent fallback, the `Ref:` footer's source, and the commit-plan presentation format including the reasoning line that accompanies a recommended split.
- [ ] Given Business Rule 5 forbids a near-duplicate, when this story lands, then `commit-organization` contains no type vocabulary table, no scope rules, no summary craft rules, no body guidance, and no footer table — and **no `Read skills/` line anywhere in either skill**, in prose or inside a code fence (`scripts/lint-skill.sh:52` scans prose only; the fence exemption is for examples, not a channel). The composition is two inline reads at Step 4 *in `commands/ship.md`*, so `commit-organization` states the boundary in prose ("message phrasing is the command's other read at this step") and stops.
- [ ] Given the loading mechanism is placement (spec.md → *Approved scope change*, BR3), when this story lands, then neither skill is declared in `required_skills:` — that key is not used — and the story evidence records each skill's `Read` anchor for Story 4 to place: `repo-convention-detection` at Phase 1, `commit-organization` at Step 4 beside the existing `ship.md:224` read.
- [ ] Given Business Rule 4 keeps gate-crossing clauses in the command, when this story lands, then `commit-organization` contains no `AskQuestion` block, no approval step, and no statement about proceeding without approval — the gate stays in `commands/ship.md`, and the skill's text is written so that a reader arriving from the command finds the plan-composition rules and nothing that decides.
- [ ] Given `## Dry Run Mode` duplicates the Step 4 preview, when this story lands, then `commit-organization` carries the `--dry-run` preview format for the commit plan, so the duplicate can be dispositioned `deduped` in Story 4 rather than dropped.

## Implementation Tasks

- [ ] 2.1 Read Story 1's `sub-specs/clause-ledger.md` Dependency Pattern section, `.writ/docs/skills.md` → *Extraction Patterns*, and the dependency's landed skills; match their section order, heading style, and `status_evidence` wording. Grep `.writ/manifest.yaml` for each intended name **and its head noun** before scaffolding
- [ ] 2.2 Run `/new-skill repo-convention-detection`, using a verb-phrase description that passes the lint on the first pass (see technical-spec.md → Description shapes that pass); write the body from the ledger's Step 1 rows
- [ ] 2.3 Run `/new-skill commit-organization`; write the body from the ledger's Step 4 rows, excluding the approval `AskQuestion` and every clause the ledger classes as `gate`
- [ ] 2.4 Add the commit-plan and convention-detection `--dry-run` preview formats to their respective skills
- [ ] 2.5 Verify Business Rule 5 mechanically: `diff <(grep -o '`[a-z]*`' skills/commit-organization/SKILL.md | sort -u) <(...)` is not sufficient — read both files and confirm no row of `conventional-commits`' type vocabulary, scope rules, summary rules, body rules, or footer table appears in `commit-organization`. Record the check as a reviewer note, not as a grep result alone
- [ ] 2.6 Run `bash scripts/lint-skill.sh skills/*/SKILL.md` (expect 0), `grep -n 'Read skills/\|Read commands/\|Task(' skills/repo-convention-detection/SKILL.md skills/commit-organization/SKILL.md` (expect no prose hits), and `bash scripts/gen-skill.sh --check` (expect no delta)
- [ ] 2.7 Record each skill's byte size and confirm the pair totals no more than the 7,003 bytes being removed from Steps 1 and 4 — the extraction must compress, not merely relocate

## Notes

**Technical considerations:**

- `/new-skill` lints the description against a temp file **before** writing anything, appends the manifest entry, and leaves the root `SKILL.md` to `bash scripts/gen-skill.sh`. Running the generator is part of this story, not Story 5's cleanup.
- Do not author `evidence:` entries. `status_evidence` is a one-line prose field (see `skills/code-explanation/SKILL.md`); `evidence:` is the structured ladder `scripts/lint-skill.sh` proves state from, and three fabricated entries would forge `proven`.
- `scripts/lint-skill.sh` scans body prose only — fenced code blocks are exempt. That exemption is for legitimate examples, not a channel for smuggling a `Read skills/` line past the check.
- The opinionated defaults in Step 1 ("I recommend merge because it preserves commit history for bisection", "I recommend `gh` because it is the most widely available") are clauses with reasons. Both travel into the skill intact — Design Principle 6 is why they exist, and dropping the reasoning turns judgment back into a menu.
- Step 1's persist-once offer writes to `.writ/config.md` only on an explicit **y**. That is a file mutation described inside a skill; it is not gate-crossing under Business Rule 4 (nothing about a push, PR, merge, tag, or release depends on it), and it already carries its own confirmation.

**Risks / challenges:**

- **`commit-organization` drifting into commit-message advice.** The two capabilities are adjacent and the temptation is to explain the whole flow in one file. The seam is *which changes go in which commit* versus *how the message reads*.
- **Losing the `--test` conditional in the buildability rule.** Today's text says: with `--test`, avoid splits that leave tests failing midway; without it, prioritize buildability. Collapsing that into one rule is a behavior change.
- **The four "when NOT to split" rules read like advice and get compressed into two.** Each is a distinct trigger — single file, under 50 lines, tight coupling, `--no-split`. All four are ledger rows.
- **Manifest conflict with Story 3.** Both stories append to `.writ/manifest.yaml` and regenerate root `SKILL.md`. Sequence rather than merge two regenerated catalogs.

**Integration points:**

- Story 4 places both skills' inline `Read`s — `repo-convention-detection` at the Phase 1 detection step, `commit-organization` at Step 4 — and names them at phases 1 and 4 in the phase list. Neither is declared in `required_skills:`.
- `conventional-commits` is read inline alongside `commit-organization` at Step 4 by the command, at the line `ship.md:224` already occupies. **That composition is the mechanism**, it is why `commit-organization` never needs to reference the other skill, and it is why `ship.md:224` is preserved in place rather than converted into a declaration.
- `commit-organization` is the skill a `--no-split` run never reads: the run reaches Step 4, needs message phrasing, and does not need grouping. Write the skill so that boundary is legible — a reader who loaded only `conventional-commits` should not be missing anything a `--no-split` run needs.
- Story 5 measures both skills' bytes into the ceiling arithmetic.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/*/SKILL.md` exits 0
- [ ] `bash scripts/gen-skill.sh --check` reports no delta
- [ ] Two alphabetically placed `.writ/manifest.yaml` entries, both `status: candidate`
- [ ] No `Read skills/`, `Read commands/`, `Task(`, or slash-command line in either skill's prose
- [ ] Reviewed against Business Rules 4, 5, and 10
- [ ] Both skills' byte sizes recorded for Story 5

## Context for Agents

- **Business rules:** [BR4 no gate-crossing decision in a conditionally-loaded file; BR5 reuse `conventional-commits`; BR10 skills born through `/new-skill`, lint-clean] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Skill roster — `repo-convention-detection`, `commit-organization`] — from spec.md → ## Detailed Requirements
- **Technical spec:** [Skill Authoring Rules; Description shapes that pass; Error & Rescue Map] — from sub-specs/technical-spec.md
- **Prior art:** [`skills/conventional-commits/SKILL.md` (the boundary partner), `skills/code-explanation/SKILL.md` (the `status_evidence` form)]
