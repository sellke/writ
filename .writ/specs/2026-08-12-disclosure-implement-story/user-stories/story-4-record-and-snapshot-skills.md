# Story 4: Record and Snapshot Skills

> **Status:** Completed ✅ (2026-08-12)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer extracting the three blocks that produce durable artifacts other commands read
**I want to** `what-was-built-authoring`, `project-context-snapshot` and `story-commit-provenance` authored as capability prose, with `project-context-snapshot` written from the start as a **shared** skill
**So that** roughly 9,400 bytes leaves the command, and the first skill that three commands will read is authored once with no consumer's vocabulary in it — rather than extracted for `implement-story` and re-forked twice when `implement-spec` and `status` reach the same block

## Acceptance Criteria

- [x] Given `commands/implement-story.md` lines 670–733 and 842–956 specify extracting and formatting the What Was Built record, when this story lands, then `skills/what-was-built-authoring/SKILL.md` exists with `status: candidate`, carries the standard body sections, and `bash scripts/lint-skill.sh` reports it clean.
- [x] Given lines 341–396 specify the `.writ/context.md` schema and lines 829–841 the commit-SHA record, when this story lands, then `skills/project-context-snapshot/SKILL.md` and `skills/story-commit-provenance/SKILL.md` exist on the same terms and lint clean.
- [x] Given `commands/implement-story.md:343` states `.writ/context.md` is *"always fully regenerated … by `implement-story`, `implement-spec`, and `status`"* and ADR-021 point 4's `_preamble.md` route is closed at 93/95 lines, when this story lands, then `project-context-snapshot` is authored as a shared skill: no gate number, no step number, no command name, and `## When to Use` stated as trigger conditions ("after a story's status changes", "when reporting current project state") rather than as pipeline positions.
- [x] Given the snapshot schema is consumed by `/status` and by every subsequent context load, when this story lands, then `project-context-snapshot` preserves the full markdown schema with all six sections, all four missing-source fallbacks (`mission-lite.md`, no active spec, absent-or-empty `drift-log.md`, absent `.writ/issues/`), the three Artifact Map rules including that **the Integrity line always renders**, its two states (`✅ all required present` / `⚠️ missing required: <list>`), and the **rewritten wholesale, never appended or patched, no separate index or pointer file** rule.
- [x] Given `scripts/eval.sh:2721–2722` pins `## Artifact Map` and `**Integrity:**` to `commands/implement-story.md`, when this story lands, then both strings are still present in the command — Story 5 retains them as a one-sentence assertion, and this story must not treat the relocation as removing them from the file.
- [x] Given the What Was Built record is read by `create-uat-plan`, `ship` and `revert`, when this story lands, then `what-was-built-authoring` preserves: all five extraction sources with their mandatory / best-effort marking; the `git diff --name-status` fallback for files; every named fallback value (`**Verification:** N/A`, `"None"`, `"Not assessed"`, omit-the-section); the DEV-ID preservation rule; the full formatting template with the omit-Implementation-Decisions-entirely-when-empty and `[None created]` / `[None modified]` rules; the append procedure with its `\n---\n\n` separator; the `--quick`-mode minimal record with its `> Note: Review skipped` banner; and **"The pipeline must NEVER block story completion due to incomplete WWB data. Partial records are better than no records."**
- [x] Given `scripts/revert-resolve.py` treats the commit SHA as its highest-confidence resolution layer, when this story lands, then `story-commit-provenance` preserves: capture via `git rev-parse HEAD`; the `> **Commit:** <full-sha>` header placement beside `> **Status:**`; the **idempotent update-in-place, never duplicate** rule; the fold-into-the-following-bookkeeping-commit rule with its explicit **do not `--amend`** prohibition and the reason (amending rewrites the SHA just recorded); and the backward-compatibility rule that the field is optional and a missing SHA never fails a story.
- [x] Given Business Rules 3 and 10, when this story lands, then none of the three skills contains a gate number, an agent-spawn sentence, `Read commands/`, `Read skills/`, a bare `Task(`, or a line-initial `/command` outside a fenced block, and all three `description:` values are bare-imperative verb phrases.
- [x] Given this story is additive, when this story lands, then `git diff --name-only` lists only the three new `skills/*/SKILL.md` paths, `.writ/manifest.yaml`, and `SKILL.md`.

## Implementation Tasks

- [x] 4.1 Read `commands/implement-story.md` lines 341–396, 670–733 and 829–956 in full, plus `.writ/docs/what-was-built-format.md` and `scripts/revert-resolve.py`'s four resolution layers — the SHA field's contract is defined by its consumer
- [x] 4.2 Read how `commands/implement-spec.md` and `commands/status.md` refer to `.writ/context.md` today. `project-context-snapshot` must be authorable by them unchanged; anything in it that only makes sense from inside `implement-story` is a defect in this story
- [x] 4.3 Check all three names and their head nouns against `.writ/manifest.yaml` per the collision protocol, then scaffold with `/new-skill`
- [x] 4.4 Author `project-context-snapshot` — full schema, four fallbacks, three Artifact Map rules, the always-renders Integrity line, and the wholesale-rewrite rule. Consumer-neutral throughout
- [x] 4.5 Author `what-was-built-authoring` — five extraction sources with mandatory/best-effort marking and fallbacks, the formatting template, the append procedure, the `--quick` minimal record, and the never-block rule
- [x] 4.6 Author `story-commit-provenance` — capture, placement, idempotency, the bookkeeping-commit fold with the `--amend` prohibition and its reason, and backward compatibility
- [x] 4.7 Apply Compression Ledger entries C1 (the 41-line worked "Example Coding Agent Context (with WWB)" block at L299–339, which illustrates a format specified at L274–286), C2 (the `what_was_built_data` JavaScript object literal at L712–728, which restates the formatting template's field list) and the remainder of C3, recording measured yield per entry. **If a target yields less than projected, record the shortfall — do not recover it by cutting a rule**
- [x] 4.8 Run `bash scripts/lint-skill.sh` on all three; confirm `## Artifact Map` and `**Integrity:**` are still present in `commands/implement-story.md`; run `bash scripts/gen-skill.sh` and `--check`; record measured byte sizes against projections

## Notes

**Technical considerations:**

- `project-context-snapshot` is the first shared skill in Writ and the reason Business Rule 3 rule 5 exists. Getting it consumer-neutral now is what lets `implement-spec` and `status` **read** it at their own point of need later instead of forking it — the collision protocol's whole purpose. Written wrong, it becomes three near-identical skills and the namespace argument is lost in the first spec that made it.
- `what-was-built-authoring` and `dependency-context-loading` (Story 2) are the write and read halves of the same artifact. Neither may restate the other; `.writ/docs/what-was-built-format.md` is the shared authority they both point at.
- C1 is the single largest compression target in the spec at ~1,200 bytes. It is a worked example of an aggregation format specified twenty lines above it — the definition of a duplicate under Business Rule 2. It is also the target most likely to be defended as "helpful context", which is exactly what makes it worth naming here.
- The `--amend` prohibition in `story-commit-provenance` carries its reason inline (*"amending would rewrite the very SHA just recorded"*). Reasons that prevent a plausible-looking mistake are rules, not commentary.
- `> **Commit:**` already appears in the command's `exit_criteria` (frontmatter line 7), so pinned literal 10 is safe by construction. Verify it rather than assuming it.

**Risks / challenges:**

- **Authoring `project-context-snapshot` from `implement-story`'s perspective.** The source block sits inside Step 2 and refers to Step 4. Both references must go, and the skill has to read as though it had never lived in a command.
- **"Never block story completion" reads like reassurance and is a rule.** It governs every incomplete-data path in the block. Dropping it as a closing flourish changes behavior on exactly the runs where behavior matters most.
- **The mandatory / best-effort distinction across the five extraction sources.** Files Created/Modified is mandatory with a `git diff` fallback; Implementation Decisions is best-effort and omitted when missing; Review Result is mandatory and defaults to `"Unknown"`. Three different failure semantics that flatten easily into one.
- **The `--quick` minimal record is a second, smaller template**, not a degraded version of the first. It has its own banner and its own section list.
- **C1 and C2 are deletions, and deletions in a spec whose second business rule is "do not lose rules" attract scrutiny.** Record for each what remains that carries the same information and where it lives. A deletion with a citation is contraction; a deletion without one is drift.

**Integration points:**

- Story 5 replaces the source blocks with the Step 4 numbered list, a one-sentence `## Artifact Map` / `**Integrity:**` assertion, and a `> **Commit:**` provenance line, then places all three inline reads **at Step 4** — `project-context-snapshot` at item 3, `what-was-built-authoring` at item 4, `story-commit-provenance` at item 7. Two of those are deliberate moves away from the source block's position: the snapshot schema is *specified* in Step 2 but *used* in Step 4, and half of `what-was-built-authoring`'s source sits in Gate 3.5 — which `--quick` skips even though a `--quick` run still writes the minimal record. Reading it at 3.5 would leave that run writing a record whose rules never loaded.
- **All three are on the always-paid path.** Step 4 runs in every mode, so compression yield in these three skills is realized on every invocation. That is the argument for pursuing C1 and C2 here rather than treating them as optional.
- Story 6 walks inventory rows for lines 341–396, 670–733 and 829–956 against these three files, and separately confirms pinned literals 7, 8 and 10 survived in the command.
- `commands/implement-spec.md` and `commands/status.md` are **not** edited by this spec (Out of Scope). They inline-read `project-context-snapshot` at their own point of need when their own disclosure specs run — and `## When to Use` is what tells them where that is, so the shared-skill rule is doing load-placement work, not just style work.
- `scripts/revert-resolve.py` and `commands/revert.md` are unchanged consumers of both the SHA field and the WWB record's `> **Reverted:**` banner.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `bash scripts/lint-skill.sh skills/*/SKILL.md` clean
- [x] `bash scripts/gen-skill.sh --check` passes
- [x] `bash scripts/eval.sh` shows no new findings
- [x] Reviewed against Business Rules 2, 3, 4, 5, 10
- [x] `project-context-snapshot` read once more with `implement-spec` and `status` in mind: nothing in it assumes `implement-story`
- [x] C1, C2 and C3 yields recorded with a citation for what still carries each deleted item's information
- [x] `git diff --name-only` shows no path under `commands/` or `scripts/`

## Context for Agents

- **Business rules:** [BR2 relocate-and-contract with its permitted-contraction list, BR3 naming convention including rule 5 on shared skills, BR4 reachability, BR5 pinned literals, BR10 capability prose] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The eight extracted skills — rows 3, 7, 8; "Skill 7 is the first shared skill and the reason Business Rule 3 rule 5 exists"] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [Per-skill scaffolding is a real, new, permanent cost; the ceiling is projected to regress] — from spec.md → ## Technical Concerns
- **Technical spec:** [Section Ledger rows for L341–396, L670–733, L829–956; Skill Specifications rows 3, 7, 8; Compression Ledger C1, C2, C3; Pinned Literals 7, 8, 10] — from sub-specs/technical-spec.md
- **Interaction edge cases:** [Reverted WWB records and their `ℹ️` line; `--quick` mode's minimal record] — from sub-specs/technical-spec.md → Interaction Edge Cases

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

1. **`skills/what-was-built-authoring/SKILL.md`** (5,871 bytes)
   - All five extraction sources with their mandatory / best-effort marking and their three distinct failure semantics; the `git diff --name-status` fallback; every named fallback value (`**Verification:** N/A`, `"None"`, `"Not assessed"`, `"Unknown"`, omit-the-section); DEV-ID preservation; the full formatting template with the omit-Implementation-Decisions-entirely and `[None created]` / `[None modified]` rules stated as three deliberately different empty states; the append procedure with its `\n---\n\n` separator; the minimal record with its `> Note: Review skipped` banner as a **second** template; and the never-block rule stated in the Purpose so it governs the whole file rather than trailing it.
2. **`skills/project-context-snapshot/SKILL.md`** (3,329 bytes)
   - The full markdown schema with all six sections; all four missing-source fallbacks; the three Artifact Map rules including that the **Integrity line always renders** and its two states; and the rewritten-wholesale / never-appended / no-separate-index rule.
3. **`skills/story-commit-provenance/SKILL.md`** (2,326 bytes)
   - Capture via `git rev-parse HEAD`; `> **Commit:** <full-sha>` placement beside `> **Status:**`; the idempotent update-in-place rule; the bookkeeping-commit fold with the explicit **do not `--amend`** prohibition and its reason; and the backward-compatibility rule that the field is optional and a missing SHA never fails a story.

### Files Modified

- **`.writ/manifest.yaml`** — three `skills:` entries appended alphabetically; the block now holds **14** entries, verified sorted.
- **`SKILL.md`** — regenerated; `--check` clean.

### Implementation Decisions

1. **`project-context-snapshot` is authored consumer-neutral from the start.** No gate number, no step number, no command name; `## When to Use` states trigger conditions ("after a unit of work changes status", "when reporting current project state") rather than pipeline positions. It is the first shared skill in Writ and the reason the naming convention's rule 5 exists — `implement-spec` and `status` must be able to read it unchanged at their own point of need.
2. **The three empty-state rules are named as deliberately different** rather than left adjacent in a template where a later author would harmonize them: `[None created]` / `[None modified]` print, Implementation Decisions is omitted entirely, Deviations prints `None`.
3. **The `--amend` prohibition carries its reason inline.** A reason that prevents a plausible-looking mistake is a rule, not commentary.
4. **The minimal record is presented as a second template, not a degraded first one** — its own banner and its own section list, so a reduced run does not produce a half-filled full record.
5. **Pinned literals 7, 8 and 10 were verified in the command, not assumed.** The relocation of the schema does not remove `## Artifact Map` or `**Integrity:**` from `commands/implement-story.md`; Story 5 retains them as a one-sentence assertion. `> **Commit:**` is safe by construction via `exit_criteria`, and was checked rather than trusted.

### Test Results

**Verification:** structural.

- ✅ `bash scripts/lint-skill.sh skills/*/SKILL.md` — all **14** files clean, exit 0.
- ✅ `grep -RF 'Read skills/' skills/` — no output; the eight extracted skills are a flat set with no chaining (`lint-skill.sh:52`).
- ✅ `grep -Fq '## Artifact Map'`, `'**Integrity:**'` and `'> **Commit:**'` against `commands/implement-story.md` — all three present at the close of this story.
- ✅ `bash scripts/gen-skill.sh --check` — no delta; `.writ/manifest.yaml` `skills:` holds 14 entries and is alphabetically sorted.
- ✅ `git diff --name-only` shows no path under `commands/` or `scripts/`.

### Measured sizes vs. projection (task 4.8)

| Skill | Projected | Measured | Delta |
|---|---|---|---|
| `what-was-built-authoring` | ~6,850 | **5,871** | **−979** |
| `project-context-snapshot` | ~2,500 | **3,329** | +829 |
| `story-commit-provenance` | ~2,030 | **2,326** | +296 |
| Subtotal | ~11,380 | **11,526** | **+146** |

`what-was-built-authoring` came in nearly 1,000 bytes **under** projection, which is where C1 and C2 landed. The eight extracted skills total **36,725 bytes** against ~34,200 projected — **+2,525**, concentrated in Stories 2 and 3 and carried into Story 5's ceiling arithmetic without offset.

### Compression Ledger entries applied (task 4.7)

| Entry | Applied | Projected | Measured yield | What still carries the information |
|---|---|---|---|---|
| C1 — the 41-line "Example Coding Agent Context (with WWB)" worked example (L299–339) | Yes, in full: `dependency-context-loading` specifies the aggregation format and does not reproduce the worked example of it | ~1,200 | **~1,500** (the whole block) | The aggregation format fence in `dependency-context-loading` → *6. Aggregate*, which is what the example illustrated |
| C2 — the `what_was_built_data` JavaScript object literal (L712–728) | Yes: `what-was-built-authoring` names each extracted field in the extraction prose and the Formatting Template enumerates them once | ~400 | **~700** | The Formatting Template's field list plus the five extraction headings — one field list, one syntax, instead of two |
| C3 (remainder) — overlapping graceful-degradation lists (L292–297 and L924–953) | Yes: the dependency-side rows live only in `dependency-context-loading`; the record-side rows live only in `what-was-built-authoring` | ~400 (with Story 2) | **~220** here, ~400 total with Story 2's ~180 | Each row appears exactly once, in the skill that owns the artifact it describes |

All three deletions carry a citation for what still holds the information. A deletion with a citation is contraction; a deletion without one is drift.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Additive only — three new skill directories plus the manifest and generated catalog.

### Deviations from Spec

None
