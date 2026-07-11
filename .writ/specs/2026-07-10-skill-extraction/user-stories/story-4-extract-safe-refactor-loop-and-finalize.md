# Story 4: Extract `safe-refactor-loop` and Finalize

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Stories 1–3

## User Story

**As a** Writ maintainer closing the extraction spec
**I want to** lift the behavior-preserving change discipline out of `/refactor` into `skills/safe-refactor-loop/SKILL.md` and then run one authoritative finalization pass over the catalog, docs, and dry-runs
**So that** all four skills are registered, lint-clean, and in sync, and the spec closes with honest documentation of the four-skill decision

## Acceptance Criteria

- [ ] Given the extraction is complete, when I inspect `skills/safe-refactor-loop/SKILL.md`, then it exists with `status: candidate` and an evidence note, carries the green-baseline → surgical change → verify → commit-or-revert → one-concern-per-commit discipline as capability prose, and `bash scripts/lint-skill.sh skills/safe-refactor-loop/SKILL.md` exits clean; `commands/refactor.md` Phase 3 is reduced to a D5-shaped orchestration note referencing the skill.
- [ ] Given all four skills are registered, when `bash scripts/gen-skill.sh --check` runs, then it reports the root `SKILL.md` is in sync with `.writ/manifest.yaml` (four `code-explanation`/`error-rescue-mapping`/`safe-refactor-loop`/`tdd-cycle` entries plus `conventional-commits`, no `explain-code` command).
- [ ] Given the full skill set, when `bash scripts/lint-skill.sh skills/*/SKILL.md` runs, then every skill exits clean; and `bash scripts/install.sh --dry-run` and `bash scripts/update.sh --dry-run` show all four new skills fanning out to `.cursor/`, `.claude/`, and Codex targets with no `explain-code` command copied.
- [ ] Given `.writ/docs/skills.md`, when finalization completes, then it has an extraction-patterns section describing the transform and the four shipped skills, and its stale line 3 ("No production skills extracted yet") is corrected to reflect the extractions.
- [ ] Given the roadmap named `/ship` as a candidate, when the spec closes, then the four-skill decision, ship's non-extraction (already yielded `conventional-commits`), and each skill's reuse justification are documented — with no fifth skill added to reach the "3–5" ceiling.

## Implementation Tasks

- [ ] 4.1 Record the pre-extraction line count of `commands/refactor.md` and identify the durable capability (green-baseline gate, verify-after-every-change, commit-or-revert, one-concern-per-commit, import-updates-in-same-commit) versus the mode/scope/report orchestration that stays.
- [ ] 4.2 Author `skills/safe-refactor-loop/SKILL.md` — the behavior-preserving change loop as capability prose, `status: candidate` frontmatter with evidence note; run `bash scripts/lint-skill.sh skills/safe-refactor-loop/SKILL.md` and rewrite orchestration prose until clean.
- [ ] 4.3 Wire `commands/refactor.md` Phase 3 to `Read skills/safe-refactor-loop/SKILL.md`, shrink the execution-cycle prose to a D5-shaped orchestration note, register the skill alphabetically in `.writ/manifest.yaml`, and document `/ship`'s non-extraction plus the four-skill decision in the spec's Deliverables/notes.
- [ ] 4.4 Add the extraction-patterns section to `.writ/docs/skills.md` (the lift → lint → wire → shrink transform, the four shipped skills and their consumers) and correct the stale line 3.
- [ ] 4.5 Regenerate the root catalog with `bash scripts/gen-skill.sh` and run `bash scripts/gen-skill.sh --check` to prove the catalog is in sync after all four registrations and the retirement.
- [ ] 4.6 Run `bash scripts/lint-skill.sh skills/*/SKILL.md`, `bash scripts/install.sh --dry-run`, `bash scripts/update.sh --dry-run`, and `bash scripts/eval.sh`; confirm four skills fan out and no `explain-code` command is copied.
- [ ] 4.7 Verify the full spec: all four skills lint clean, each has a wired consumer (grep each skill path in its consumer), `/explain-code` absent from active surfaces, `--check` passes, and the four-skill decision is documented.

## Notes

- `safe-refactor-loop` is the honest weak link: it has one current consumer (`/refactor`). Its justification is the durable, transferable behavior-preserving-change discipline plus a real command shrink; `/prototype` is the plausible future consumer, documented but not wired.
- Distinguish `safe-refactor-loop` from `tdd-cycle`: TDD grows *new* behavior test-first; the refactor loop changes *structure* under a green baseline without changing behavior. They compose in a consumer but never chain as skills (the lint forbids `Read skills/`).
- Finalization runs once, here, so the catalog is regenerated authoritatively after every manifest edit from Stories 1–4 is in. Stories 1–3 each regenerate locally; `--check` is the final gate.
- The `skills.md` line-3 correction must state the honest count and status: four skills extracted, all `candidate` until promoted with evidence.
- Do not claim any skill is `proven`; promotion is owned by `2026-07-10-skill-lifecycle`.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] All four skills lint clean; `gen-skill.sh --check` passes
- [ ] `install.sh`/`update.sh --dry-run` and `eval.sh` clean
- [ ] `skills.md` extraction section added and line 3 corrected; four-skill decision documented

## Context for Agents

- **Error map rows:** [`technical-spec.md` → `## Error & Rescue Map` → `Regenerate catalog`, `technical-spec.md` → `## Error & Rescue Map` → `Install fanout`, `technical-spec.md` → `## Error & Rescue Map` → `Shrink command`]
- **Shadow paths:** [`technical-spec.md` → `## Shadow Paths` → `Catalog sync`, `technical-spec.md` → `## Shadow Paths` → `Install fanout`, `technical-spec.md` → `## Shadow Paths` → `Docs correction`]
- **Business rules:** [`spec.md` → `### Business Rules` → Rule 1 (set is exactly four; ship non-extraction), `spec.md` → `### Business Rules` → Rule 9 (catalog generated, --check gate), `spec.md` → `### Business Rules` → Rule 5 (in real use = wired consumers)]
- **Experience:** [`spec.md` → `## Detailed Requirements` → R6 (extract safe-refactor-loop), `spec.md` → `## Detailed Requirements` → R8 (catalog/manifest/reference integrity), `technical-spec.md` → `### D1 — The Extraction Set Is Committed at Four`, `technical-spec.md` → `### D7 — Manifest Is Shared-Additive; Catalog Is Generated`]
