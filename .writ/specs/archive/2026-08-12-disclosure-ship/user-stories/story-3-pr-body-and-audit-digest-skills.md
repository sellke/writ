# Story 3: PR Body and Audit Digest Skills

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer thinning the two phases that touch the production boundary and the provenance channel
**I want** PR-body composition and audit-digest aggregation extracted into skills while every gate-crossing decision and every attach clause stays behind
**So that** the largest remaining block of procedure (5,818 bytes of Step 5) stops loading unconditionally, and `/ship` can still open the right PR and still attach an audit note if neither skill ever loads

## Acceptance Criteria

- [ ] Given `/new-skill` is the authoring path, when this story lands, then `skills/pr-body-composition/SKILL.md` and `skills/audit-digest-composition/SKILL.md` exist with `disable-model-invocation: true`, `status: candidate`, a `status_evidence` line naming the extraction date and `commands/ship.md` as the single consumer, and `## Purpose` + `## When to Use` sections — and `bash scripts/lint-skill.sh skills/*/SKILL.md` exits 0.
- [ ] Given `.writ/manifest.yaml` is the registry, when this story lands, then it carries two new alphabetically placed `skills:` entries (`audit-digest-composition`, `pr-body-composition`) with `name`, `file`, `description`, `status: candidate`, and tags, and `bash scripts/gen-skill.sh --check` reports no delta.
- [ ] Given Step 5's PR body has seven sections, when this story lands, then `pr-body-composition` carries all seven — Summary, Changes, Spec Reference, Test Results, Spec Health, Drift Report, Review Notes — with the template, the seven-row population table, the "no data → explicit placeholder" rule, and the single exception that `## Spec Health` is **omitted entirely** when clean.
- [ ] Given the inline spec-health pass is part of body composition, when this story lands, then `pr-body-composition` carries `/verify-spec` checks 1–3 by definition (story file integrity, status consistency, completion integrity) with the auto-fix-silently rule and the unfixable-issues-become-bullets rule — inlined, because a skill may not invoke a slash command.
- [ ] Given auto-labeling never blocks a PR, when this story lands, then `pr-body-composition` carries the five-row label table, the additive (non-exclusive) rule, the `gh label list` existence check, the skip-silently fallback with its log line, and the explicit statement that a missing label never fails the flow.
- [ ] Given Business Rule 7 forbids reimplementation, when this story lands, then `pr-body-composition`'s Spec Reference row states the `scripts/resolve-spec-reference.py resolve --branch … --commits … --specs-dir .writ/specs` call and the handling of `matched` / `none` / `ambiguous`, and describes **no** matching heuristic, no dedup rule, and no tie-break — and `git diff --name-only -- scripts/` is empty.
- [ ] Given Business Rule 4 and Business Rule 6, when this story lands, then neither skill contains the draft-vs-ready determination, `git push`, `gh pr create`, the `gh auth login` rescue, the `writ.auditNotes` opt-out gate, landed-SHA resolution, `git notes --ref=writ add -f -F`, the `refs/notes/commits` prohibition, the non-blocking rule, or the minimal-digest fallback — and `python3 scripts/eval-git-notes-audit.py` still reports all seven `scenario_ship` checks passing against the **unmodified** `commands/ship.md`.
- [ ] Given the loading mechanism is placement (spec.md → *Approved scope change*, BR3), when this story lands, then neither skill is declared in `required_skills:` — that key is not used — neither contains a `Read skills/` line in prose or inside a code fence (`scripts/lint-skill.sh:52`), and the story evidence records each skill's `Read` anchor for Story 4: `pr-body-composition` at the Phase 5 body-assembly step **before** the retained draft-vs-ready / `gh pr create` block, and `audit-digest-composition` at Step 6.2 **after** the `writ.auditNotes` opt-out check and landed-SHA resolution — placed above that gate, an opted-out run would pay for a skill it never uses.
- [ ] Given `audit-digest-composition` owns composition only, when this story lands, then it carries the source-range capture for the digest header, the six aggregation rules over per-story `## What Was Built` records (worst verdict, highest drift severity, DEV-ID union, aggregate coverage, files created/modified counts, total review iterations), a pointer to `.writ/docs/git-notes-audit-format.md` for the schema, and the audit-only content prohibition — never chain-of-thought, prompts, transcripts, or verbatim "Implementation Decisions" narrative.

## Implementation Tasks

- [ ] 3.1 Read Story 1's Dependency Pattern section, `.writ/docs/skills.md` → *Extraction Patterns*, and the ledger rows for Steps 5 and 6; grep `.writ/manifest.yaml` for each intended name and its head noun; confirm Story 2 has landed its manifest entries before appending (alphabetical insertion into the same block)
- [ ] 3.2 Run `/new-skill pr-body-composition`; write the body from the ledger's Step 5 `procedure` and `output` rows only, skipping every `gate` row
- [ ] 3.3 Inline `/verify-spec` checks 1–3 by definition rather than by reference — a skill may not invoke a slash command, and today's command text already says the definitions are identical to the standalone command
- [ ] 3.4 Run `/new-skill audit-digest-composition`; write the body from the ledger's Step 6.2–6.3 rows, excluding every row annotated with an `eval-git-notes-audit.py` scenario name
- [ ] 3.5 Verify the seam by simulation: read `commands/ship.md` Step 6 as it stands and confirm that with `audit-digest-composition` absent, the retained text alone still specifies a complete attach — opt-out check, landed SHA, minimal digest, `git notes --ref=writ add -f -F`, confirmation. Under the inline mechanism this is no longer a thought experiment: the skill loads only if Step 6.2's `Read` is reached and succeeds, so "absent" is a state real runs occupy. Record the walkthrough in the story notes
- [ ] 3.6 Run `python3 scripts/eval-git-notes-audit.py` and confirm 7/7 `scenario_ship` PASS (this story does not edit `commands/ship.md`, so any failure means something else moved)
- [ ] 3.7 Run `bash scripts/lint-skill.sh skills/*/SKILL.md`, `bash scripts/gen-skill.sh --check`, `git diff --name-only -- scripts/` (expect empty), and record both skills' byte sizes for Story 5

## Notes

**Technical considerations:**

- This story does **not** edit `commands/ship.md`. Steps 5 and 6 are read as the source; Story 4 does the removal. Running `eval-git-notes-audit.py` here is a control, not a check of this story's own output — it should pass trivially, and a failure means something outside this spec moved.
- The composition/attach seam in Step 6 is the subtlest boundary in this spec. The rule: `audit-digest-composition` answers *what goes in the digest*; `commands/ship.md` answers *whether, where, and how it is written*. 6.0, 6.1, 6.4, and 6.5 stay; 6.2 and 6.3's aggregation stays only in the sense that 6.3's **fallback** stays in the command.
- `.writ/docs/git-notes-audit-format.md` carries the schema. The skill points at it and does not restate it — the same discipline Business Rule 7 applies to `resolve-spec-reference.py`.
- `pr-body-composition` is the largest new skill (~4,000 bytes projected). It is also the one most likely to be reused: a sibling spec thinning `/release` may want the body/label machinery. Name sections so they can be cited from outside.
- The "no data → explicit placeholder, don't omit the section" rule and its single Spec Health exception are easy to state backwards. Today's text: every section gets clear placeholder text when it has no data, **except** `## Spec Health`, which is omitted entirely when clean.

**Risks / challenges:**

- **Draft-vs-ready migrating into the skill.** It sits inside Step 5, immediately after labeling, and reads like part of PR assembly. It is the production-boundary decision — Business Rule 4's load test applies: if the skill silently failed to load, could `/ship` mark a failing-test PR ready for review? Yes. It stays in the command.
- **Over-extracting Step 6 to make the byte target easier.** 3,610 bytes is tempting and only ~1,200 of it may move. `eval-git-notes-audit.py` catches the literal-string half; nothing catches a paraphrase that keeps the literal and loses the meaning.
- **Restating the Spec Reference heuristic "for clarity."** The script's docstring records that `ship.md` describing the matching only as prose is exactly why `release.md` could not reuse it. Re-prosing it in a skill recreates the defect.
- **Manifest conflict with Story 2.** Same block, same regenerated catalog.

**Integration points:**

- Story 4 places both skills' inline `Read`s (Phase 5 body-assembly; Step 6.2 after the opt-out gate), names `pr-body-composition` at phase 5 and `audit-digest-composition` at phase 6 in the phase list, and removes the extracted text from `commands/ship.md`. Neither is declared in `required_skills:`.
- Story 5 re-runs `eval-git-notes-audit.py` against the **thinned** command, which is the real test.
- `scripts/resolve-spec-reference.py` and `.writ/docs/git-notes-audit-format.md` are read-only references throughout.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/*/SKILL.md` exits 0
- [ ] `bash scripts/gen-skill.sh --check` reports no delta
- [ ] Two alphabetically placed `.writ/manifest.yaml` entries, both `status: candidate`
- [ ] `python3 scripts/eval-git-notes-audit.py` reports 7/7 `scenario_ship` PASS
- [ ] `git diff --name-only` lists nothing under `scripts/` and nothing under `commands/`
- [ ] Reviewed against Business Rules 4, 6, 7, and 10
- [ ] Both skills' byte sizes recorded for Story 5

## Context for Agents

- **Business rules:** [BR4 production boundary; BR6 provenance write stays unconditional; BR7 reference `resolve-spec-reference.py`, never reimplement; BR10 skill authoring] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Skill roster — `pr-body-composition`, `audit-digest-composition`] — from spec.md → ## Detailed Requirements
- **Technical spec:** [The audit-note block — minimum retained content; Spec Reference — the call, not the heuristic; Skill Authoring Rules] — from sub-specs/technical-spec.md
- **Technical concerns:** [Splitting Step 6 between a command and a skill is the subtlest part of this spec] — from spec.md → ## Technical Concerns
- **Read-only references:** [`scripts/resolve-spec-reference.py`, `.writ/docs/git-notes-audit-format.md`, ADR-017]
