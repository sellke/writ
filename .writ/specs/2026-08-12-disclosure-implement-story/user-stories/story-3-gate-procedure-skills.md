# Story 3: Gate Procedure Skills

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer extracting the gate pipeline — the block ADR-021 called the riskiest part of the riskiest file
**I want to** `boundary-map-computation`, `change-surface-classification` and `drift-triage` authored as capability prose, with every agent-spawn and user-escalation sentence deliberately left behind in the command
**So that** roughly 9,100 bytes of algorithm leaves the command while the gate *shape* stays visible in it, and the command/skill boundary is drawn where ADR-009 puts it rather than wherever the byte count happened to be convenient

## Acceptance Criteria

- [ ] Given `commands/implement-story.md` lines 436–519 specify the file-ownership map, when this story lands, then `skills/boundary-map-computation/SKILL.md` exists with `status: candidate`, carries the standard body sections, and `bash scripts/lint-skill.sh` reports it clean.
- [ ] Given lines 571–593 specify change-surface classification and lines 623–669 specify drift response, when this story lands, then `skills/change-surface-classification/SKILL.md` and `skills/drift-triage/SKILL.md` exist on the same terms and lint clean.
- [ ] Given the boundary algorithm is seven ordered steps whose order is the rule, when this story lands, then `boundary-map-computation` preserves in order: candidate-OWNED collection from the story's `## Implementation Tasks` and from `sub-specs/technical-spec.md`'s File Map with the this-story / other-story distinction; normalization with **Owned wins** on conflict; the **depth-1** import scan and its `_(imported by owned files)_` annotation; the Gate 0 `### Warnings for Coding Agent` override and its demotion annotation; the optional Check 5 merge with `_(overlap: …)_` and `_(⚠️ high-overlap: …)_`; the no-extractable-paths fallback with its exact `⚠️ boundary_map approximate` warning; and the readable-union / implicit-out-of-scope rule.
- [ ] Given the map's semantics are as load-bearing as its computation, when this story lands, then `boundary-map-computation` also preserves the markdown block schema with its three headings, the file-paths-or-globs rule, the **advisory, no hard file locking** principle, the `<10 seconds` performance target, and both Check 5 persistence locations (`assessment-report.md` with the exact `## Check 5 — File overlap` heading, or the same section embedded in `user-stories/README.md` / `spec.md` / `spec-lite.md`) plus the graceful degradation when neither exists.
- [ ] Given classification drives review attention, when this story lands, then `change-surface-classification` preserves all four classes with their criteria and examples, all six heuristic steps in order, and the **"when ambiguous, classify UP one level"** rule — which is the only rule in the block that cannot be re-derived from the table.
- [ ] Given drift severity decides whether a pipeline continues, when this story lands, then `drift-triage` preserves: the three severities with their definitions and actions; the Small-drift sequence (capture pre-edit SHA-256, auto-amend `spec-lite.md` only, one unique `DEV-NNN` entry, the canonical `recommend-spec-lite-review-v1` result bound to execution ID / story ID / `outcome: passed` / `drift_severity: small` / DEV-ID list / non-empty summary, and the blocking `scripts/recommend-state.py record-spec-lite-amendment` acknowledgment); **overall drift = highest severity present, with mixed runs pausing for Large while still auto-amending Small**; that `spec.md` is never auto-modified; the append-only `drift-log.md` rule with DEV-ID continuation; and the no-batching / contiguous-digest-chain rule with its four block conditions.
- [ ] Given Business Rule 10 keeps orchestration in the command, when this story lands, then none of the three skills contains an agent-spawn sentence, an `AskQuestion` escalation, a gate number, `Read commands/`, `Read skills/`, a bare `Task(`, or a line-initial `/command` outside a fenced block — and the Gate 3 review-loop cap sentence *"Max 3 iterations across review and visual QA gates"* is **not** moved into `drift-triage`, because `scripts/eval-loop-bounds.py:485` regexes the command body for it.
- [ ] Given this story is additive, when this story lands, then `git diff --name-only` lists only the three new `skills/*/SKILL.md` paths, `.writ/manifest.yaml`, and `SKILL.md`.

## Implementation Tasks

- [ ] 3.1 Read `commands/implement-story.md` lines 427–519, 571–593 and 617–669 in full, plus `.writ/docs/drift-report-format.md`, `agents/coding-agent.md` and `agents/review-agent.md`'s `boundary_map` handling — the map's consumers define what the map must contain
- [ ] 3.2 Check all three names and their head nouns against `.writ/manifest.yaml` per the collision protocol, then scaffold with `/new-skill`
- [ ] 3.3 Author `boundary-map-computation` — schema, flag semantics, the seven ordered steps, the performance target, and both Check 5 persistence locations with their degradation
- [ ] 3.4 Author `change-surface-classification` — four classes, six heuristic steps, and the classify-up-when-ambiguous rule
- [ ] 3.5 Author `drift-triage` — three severities and their actions, the Small-drift recommended-mode sequence, the four principles, and the `drift-log.md` append-only and DEV-ID rules
- [ ] 3.6 Apply Compression Ledger entries C4 (`boundary_map` Flags list duplicating the schema block's inline annotations) and C5 (the drift-log entry example, already authoritative in `.writ/docs/drift-report-format.md`), recording measured yield per entry
- [ ] 3.7 Verify the boundary: `grep -nE 'Read commands/|Read skills/|[^A-Za-z_]Task\(|^/[a-z]' skills/boundary-map-computation/SKILL.md skills/change-surface-classification/SKILL.md skills/drift-triage/SKILL.md` returns only fenced-block or 4-space-indented hits; then run `bash scripts/lint-skill.sh` on all three
- [ ] 3.8 Run `bash scripts/gen-skill.sh` and `--check`; record measured byte sizes against the technical spec's projections and flag any overshoot now, not at Story 5

## Notes

**Technical considerations:**

- This is where ADR-009's boundary does real work. Gate 0.5 is *"an inline orchestration step (data transformation, not a judgment call)"* — the transformation is the skill; the fact that it runs before Gate 1 and is skipped in `--quick` is the command's. Gate 3.5 is the same shape: severity classification is the skill, pausing the pipeline is not.
- `change-surface-classification` at ~1,646 source bytes is the smallest extraction in this spec and the marginal case for whether it should be a skill at all. It earns its file on two grounds: `assess-spec` and `review-agent` both already reason about change surface, and the classification is a self-contained input→output transform. Record the measured file size — if scaffolding overhead approaches the extracted content, that is real evidence for the remaining five specs about **fewer, larger skills**.
- `drift-triage`'s recommended-mode paragraphs reference `scripts/recommend-state.py` and a canonical result schema. Naming a script by path is not a lint violation (the patterns are `Read commands/` and `Read skills/`), and the reference must survive — the acknowledgment is described as **blocking**, which is a rule.
- The `boundary_map` schema block is a fenced markdown example. Fenced content is lint-exempt, so it transfers as written.

**Risks / challenges:**

- **The Gate 3 iteration-cap sentence looks like drift procedure and is not.** It sits three lines from the drift section and reads as part of it. Moving it degrades `eval-loop-bounds.py`'s `drift-review-cycle` cross-read to a reported `SKIP` — not a failure, which is exactly why it could ship unnoticed. The same trap exists for `2 fix iterations max` at Gate 4 (Story 5's surface).
- **Losing step order.** Both the boundary algorithm and the classification heuristic are ordered, and both read as unordered lists of considerations. "Owned wins unless step 3 or 4 demotes it" and "classify UP one level" are the two rules most likely to be dropped as obvious.
- **Smoothing the mixed-drift rule.** *"Overall drift = highest severity present. Mixed runs pause for Large while still auto-amending Small"* is two rules in one sentence, and the second is counter-intuitive enough that an author may harmonize it into "pause and do nothing else."
- **Writing an escalation into a skill because the byte count is there.** The two `STATUS: BLOCKED` `AskQuestion` blocks are ~2,000 bytes and would be the easiest extraction in the file. They are orchestration; they stay. Business Rule 10 exists for this specific temptation.

**Integration points:**

- Story 5 replaces the source blocks with gate contract stubs — agent binding, skip modes, result vocabulary, iteration caps — and places one inline `Read skills/<name>/SKILL.md` inside each gate: `boundary-map-computation` in Gate 0.5, `change-surface-classification` in Gate 2.5, `drift-triage` in Gate 3.5 § A.
- **Two of these three are the spec's entire `--quick` saving.** Gates 0.5 and 3.5 are skipped by `--quick`, so `boundary-map-computation` (~5,950) and `drift-triage` (~2,420) are genuinely not loaded on those runs — a projected −8,370 bytes that the `required_skills:` mechanism could not have delivered at all. Gate 2.5 is **not** in `--quick`'s skip list, so `change-surface-classification` is paid on every run despite feeding a gate that `--quick` skips; do not assume otherwise when sizing it.
- Story 6 walks inventory rows for lines 427–519, 571–593 and 617–669 against these three files. The seven boundary steps, six heuristic steps and three severities are all rows.
- `agents/coding-agent.md` and `agents/review-agent.md` consume `boundary_map` and are **not** edited by this spec. The skill must describe the map exactly as they already expect it.
- `assess-spec`'s Check 5 output is the optional input to boundary step 5. That command is not edited here; the persistence contract is read, not changed.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/*/SKILL.md` clean
- [ ] `bash scripts/gen-skill.sh --check` passes
- [ ] `bash scripts/eval.sh` shows no new findings
- [ ] Reviewed against Business Rules 2, 3, 4, 5, 10
- [ ] Confirmed `Max 3 iterations across review` still appears in `commands/implement-story.md`
- [ ] Measured byte sizes recorded, with an explicit note on `change-surface-classification`'s scaffolding-to-content ratio
- [ ] `git diff --name-only` shows no path under `commands/` or `scripts/`

## Context for Agents

- **Business rules:** [BR2 relocate-and-contract, BR3 naming convention, BR4 reachability, BR5 pinned literals and regexes stay in the command, BR10 orchestration stays in the command] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The eight extracted skills — rows 4, 5, 6; What deliberately does not become a skill] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [`lint-skill.sh` forbids the vocabulary the gate blocks are written in; per-skill scaffolding is a real, new, permanent cost] — from spec.md → ## Technical Concerns
- **Technical spec:** [Section Ledger rows for L436–519, L571–593, L623–669; Skill Specifications rows 4–6; Pinned Regexes; Boundary rules that constrain authoring; Compression Ledger C4 and C5] — from sub-specs/technical-spec.md
- **Interaction edge cases:** [`--review-only` passes `boundary_map` as the literal `(none)`; Gate 0.5 is not on the `/prototype` path; mixed drift severities] — from sub-specs/technical-spec.md → Interaction Edge Cases
