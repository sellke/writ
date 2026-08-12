# Story 3: Gate Procedure Skills

> **Status:** Completed ✅ (2026-08-12)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer extracting the gate pipeline — the block ADR-021 called the riskiest part of the riskiest file
**I want to** `boundary-map-computation`, `change-surface-classification` and `drift-triage` authored as capability prose, with every agent-spawn and user-escalation sentence deliberately left behind in the command
**So that** roughly 9,100 bytes of algorithm leaves the command while the gate *shape* stays visible in it, and the command/skill boundary is drawn where ADR-009 puts it rather than wherever the byte count happened to be convenient

## Acceptance Criteria

- [x] Given `commands/implement-story.md` lines 436–519 specify the file-ownership map, when this story lands, then `skills/boundary-map-computation/SKILL.md` exists with `status: candidate`, carries the standard body sections, and `bash scripts/lint-skill.sh` reports it clean.
- [x] Given lines 571–593 specify change-surface classification and lines 623–669 specify drift response, when this story lands, then `skills/change-surface-classification/SKILL.md` and `skills/drift-triage/SKILL.md` exist on the same terms and lint clean.
- [x] Given the boundary algorithm is seven ordered steps whose order is the rule, when this story lands, then `boundary-map-computation` preserves in order: candidate-OWNED collection from the story's `## Implementation Tasks` and from `sub-specs/technical-spec.md`'s File Map with the this-story / other-story distinction; normalization with **Owned wins** on conflict; the **depth-1** import scan and its `_(imported by owned files)_` annotation; the Gate 0 `### Warnings for Coding Agent` override and its demotion annotation; the optional Check 5 merge with `_(overlap: …)_` and `_(⚠️ high-overlap: …)_`; the no-extractable-paths fallback with its exact `⚠️ boundary_map approximate` warning; and the readable-union / implicit-out-of-scope rule.
- [x] Given the map's semantics are as load-bearing as its computation, when this story lands, then `boundary-map-computation` also preserves the markdown block schema with its three headings, the file-paths-or-globs rule, the **advisory, no hard file locking** principle, the `<10 seconds` performance target, and both Check 5 persistence locations (`assessment-report.md` with the exact `## Check 5 — File overlap` heading, or the same section embedded in `user-stories/README.md` / `spec.md` / `spec-lite.md`) plus the graceful degradation when neither exists.
- [x] Given classification drives review attention, when this story lands, then `change-surface-classification` preserves all four classes with their criteria and examples, all six heuristic steps in order, and the **"when ambiguous, classify UP one level"** rule — which is the only rule in the block that cannot be re-derived from the table.
- [x] Given drift severity decides whether a pipeline continues, when this story lands, then `drift-triage` preserves: the three severities with their definitions and actions; the Small-drift sequence (capture pre-edit SHA-256, auto-amend `spec-lite.md` only, one unique `DEV-NNN` entry, the canonical `recommend-spec-lite-review-v1` result bound to execution ID / story ID / `outcome: passed` / `drift_severity: small` / DEV-ID list / non-empty summary, and the blocking `scripts/recommend-state.py record-spec-lite-amendment` acknowledgment); **overall drift = highest severity present, with mixed runs pausing for Large while still auto-amending Small**; that `spec.md` is never auto-modified; the append-only `drift-log.md` rule with DEV-ID continuation; and the no-batching / contiguous-digest-chain rule with its four block conditions.
- [x] Given Business Rule 10 keeps orchestration in the command, when this story lands, then none of the three skills contains an agent-spawn sentence, an `AskQuestion` escalation, a gate number, `Read commands/`, `Read skills/`, a bare `Task(`, or a line-initial `/command` outside a fenced block — and the Gate 3 review-loop cap sentence *"Max 3 iterations across review and visual QA gates"* is **not** moved into `drift-triage`, because `scripts/eval-loop-bounds.py:485` regexes the command body for it.
- [x] Given this story is additive, when this story lands, then `git diff --name-only` lists only the three new `skills/*/SKILL.md` paths, `.writ/manifest.yaml`, and `SKILL.md`.

## Implementation Tasks

- [x] 3.1 Read `commands/implement-story.md` lines 427–519, 571–593 and 617–669 in full, plus `.writ/docs/drift-report-format.md`, `agents/coding-agent.md` and `agents/review-agent.md`'s `boundary_map` handling — the map's consumers define what the map must contain
- [x] 3.2 Check all three names and their head nouns against `.writ/manifest.yaml` per the collision protocol, then scaffold with `/new-skill`
- [x] 3.3 Author `boundary-map-computation` — schema, flag semantics, the seven ordered steps, the performance target, and both Check 5 persistence locations with their degradation
- [x] 3.4 Author `change-surface-classification` — four classes, six heuristic steps, and the classify-up-when-ambiguous rule
- [x] 3.5 Author `drift-triage` — three severities and their actions, the Small-drift recommended-mode sequence, the four principles, and the `drift-log.md` append-only and DEV-ID rules
- [x] 3.6 Apply Compression Ledger entries C4 (`boundary_map` Flags list duplicating the schema block's inline annotations) and C5 (the drift-log entry example, already authoritative in `.writ/docs/drift-report-format.md`), recording measured yield per entry
- [x] 3.7 Verify the boundary: `grep -nE 'Read commands/|Read skills/|[^A-Za-z_]Task\(|^/[a-z]' skills/boundary-map-computation/SKILL.md skills/change-surface-classification/SKILL.md skills/drift-triage/SKILL.md` returns only fenced-block or 4-space-indented hits; then run `bash scripts/lint-skill.sh` on all three
- [x] 3.8 Run `bash scripts/gen-skill.sh` and `--check`; record measured byte sizes against the technical spec's projections and flag any overshoot now, not at Story 5

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `bash scripts/lint-skill.sh skills/*/SKILL.md` clean
- [x] `bash scripts/gen-skill.sh --check` passes
- [x] `bash scripts/eval.sh` shows no new findings
- [x] Reviewed against Business Rules 2, 3, 4, 5, 10
- [x] Confirmed `Max 3 iterations across review` still appears in `commands/implement-story.md`
- [x] Measured byte sizes recorded, with an explicit note on `change-surface-classification`'s scaffolding-to-content ratio
- [x] `git diff --name-only` shows no path under `commands/` or `scripts/`

## Context for Agents

- **Business rules:** [BR2 relocate-and-contract, BR3 naming convention, BR4 reachability, BR5 pinned literals and regexes stay in the command, BR10 orchestration stays in the command] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The eight extracted skills — rows 4, 5, 6; What deliberately does not become a skill] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [`lint-skill.sh` forbids the vocabulary the gate blocks are written in; per-skill scaffolding is a real, new, permanent cost] — from spec.md → ## Technical Concerns
- **Technical spec:** [Section Ledger rows for L436–519, L571–593, L623–669; Skill Specifications rows 4–6; Pinned Regexes; Boundary rules that constrain authoring; Compression Ledger C4 and C5] — from sub-specs/technical-spec.md
- **Interaction edge cases:** [`--review-only` passes `boundary_map` as the literal `(none)`; Gate 0.5 is not on the `/prototype` path; mixed drift severities] — from sub-specs/technical-spec.md → Interaction Edge Cases

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

1. **`skills/boundary-map-computation/SKILL.md`** (6,537 bytes)
   - The markdown block schema with its three headings and the file-paths-or-globs rule; the three flag annotations carrying their own semantics; all seven ordered algorithm steps (candidate-OWNED collection with the this-story / other-story distinction, normalization with **Owned wins**, the depth-1 import scan, the architecture-review demotion with its annotation, the optional overlap merge, the no-extractable-paths fallback with its exact `⚠️ boundary_map approximate` warning, and the readable-union / implicit-out-of-scope rule); the **advisory, no hard file locking** principle; the `< 10 seconds` target; and both Check 5 persistence locations with their graceful degradation.
2. **`skills/change-surface-classification/SKILL.md`** (2,875 bytes)
   - Four classes with criteria and examples, six ordered heuristic steps, and the **classify UP one level when ambiguous** rule stated as the rule that cannot be re-derived from the table.
3. **`skills/drift-triage/SKILL.md`** (3,162 bytes)
   - Three severities with definitions and actions; the Small-drift sequence (pre-edit SHA-256, `spec-lite.md`-only auto-amend, one unique `DEV-NNN`, the canonical `recommend-spec-lite-review-v1` result with all six bindings, and the blocking `scripts/recommend-state.py record-spec-lite-amendment` acknowledgment); **overall drift = highest severity present, mixed runs pause for Large while still auto-amending Small**; `spec.md` never auto-modified; append-only `drift-log.md` with DEV-ID continuation; and the no-batching / contiguous-digest-chain rule with its four blocking conditions.

### Files Modified

- **`.writ/manifest.yaml`** — three `skills:` entries appended alphabetically, all `status: candidate`.
- **`SKILL.md`** — regenerated; `--check` clean.

### Implementation Decisions

1. **Gate numbers and agent-spawn language stayed behind.** Step 4 of the boundary algorithm reads "the upstream architecture review's `### Warnings for Coding Agent` section" rather than naming a gate; the rule is byte-faithful, the pipeline position is not the skill's to know.
2. **The two `STATUS: BLOCKED` `AskQuestion` blocks were not extracted** despite being the easiest ~2,000 bytes in the file. They are orchestration — asking a human for a repair decision — and belong to the command under ADR-009. Business Rule 10 exists for exactly this temptation.
3. **`Max 3 iterations across review and visual QA gates` was left in the command body.** It sits three lines from the drift section and reads as drift procedure; moving it would degrade `eval-loop-bounds.py:485`'s `drift-review-cycle` cross-read to a reported SKIP rather than a failure — which is precisely why it could have shipped unnoticed. Verified present twice in the command after this story.
4. **`change-surface-classification`'s scaffolding-to-content ratio, recorded for the remaining five specs.** Source block 1,896 bytes → authored 2,875 bytes. Frontmatter + `# Title` + `## Purpose` + `## When to Use` + `## How to Apply` scaffolding is roughly 900–1,000 bytes irrespective of content, so this file is **~34% scaffolding**. It is the marginal case in this spec and the clearest evidence available that **fewer, larger skills carry less overhead than many small ones**.

### Test Results

**Verification:** structural.

- ✅ `bash scripts/lint-skill.sh` on all three — clean, exit 0.
- ✅ `grep -nE 'Read commands/|Read skills/|[^A-Za-z_]Task\(|^/[a-z]'` across all three — no output at all, fenced or otherwise.
- ✅ `grep -c 'Max 3 iterations across review' commands/implement-story.md` — 2 (frontmatter citation and the Gate 3 body sentence), unchanged.
- ✅ `bash scripts/gen-skill.sh --check` — no delta.
- ✅ `git diff --name-only` shows no path under `commands/` or `scripts/`.

### Measured sizes vs. projection (task 3.8)

| Skill | Projected | First draft | After compression | Delta vs. projection |
|---|---|---|---|---|
| `boundary-map-computation` | ~5,950 | 7,033 | **6,537** | +587 |
| `change-surface-classification` | ~2,300 | 3,152 | **2,875** | +575 |
| `drift-triage` | ~2,420 | 3,287 | **3,162** | +742 |
| Subtotal | ~10,670 | 13,472 | **12,574** | **+1,904** |

The compression pass removed only commentary — a "not applicable" bullet with no source rule behind it, two sentences of my own justification for depth-1 and for the `< 10 seconds` target, and four verbose transitions. **No rule was removed to hit a number.** The residual +1,904 is real and is carried into Story 5's ceiling arithmetic rather than hidden.

### Compression Ledger entries applied (task 3.6)

| Entry | Applied | Projected | Measured yield |
|---|---|---|---|
| C4 — `boundary_map` Flags list duplicating the schema block's inline annotations | Yes. The schema fence retains the `(overlap: …)` / `(⚠️ high-overlap: …)` annotations inline, and the separate **Flags (annotations)** list beneath it is replaced by one paragraph that states each flag's semantics once | ~300 | **~330** |
| C5 — drift-log entry format example | Yes. `.writ/docs/drift-report-format.md` is cited as the authority in the Purpose block and the ten-line worked `#### [DEV-003]` example is not reproduced | ~350 | **~350** |

Both targets met or beat their projection. Neither deletion removed a rule: the flag semantics survive in the annotation paragraph, and the entry format survives in the document that owns it.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Additive only — three new skill directories plus the manifest and generated catalog.

### Deviations from Spec

None
