# Story 2: Context Assembly Skills

> **Status:** Completed ✅ (2026-08-12)
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer extracting `implement-story`'s heaviest non-gate block
**I want to** `story-context-assembly` and `dependency-context-loading` authored as capability prose that carries every parsing rule, scoring weight, truncation priority, and degradation row from Step 2 unchanged
**So that** roughly 11,500 bytes of procedure leaves the command file without a single rule leaving the product, and the two skills read as tools any consumer could wield rather than as `implement-story`'s Step 2 with the headings filed off

## Acceptance Criteria

- [x] Given `commands/implement-story.md` lines 95–220 specify hint parsing, knowledge loading and spec-lite sectioning, when this story lands, then `skills/story-context-assembly/SKILL.md` exists with `status: candidate`, carries the `## Purpose` / `## When to Use` / `## How to Apply` body convention, and `bash scripts/lint-skill.sh skills/story-context-assembly/SKILL.md` reports it clean.
- [x] Given lines 221–340 specify how upstream stories' implementation records are located, filtered and truncated, when this story lands, then `skills/dependency-context-loading/SKILL.md` exists on the same terms and lints clean.
- [x] Given `scripts/story-context.py` is the sole implementation that parses hints and fetches content and the command explicitly *"does not restate its algorithm"* (L98), when this story lands, then `story-context-assembly` preserves that boundary — it describes invoking the assembler, mapping its three JSON keys to output variables, and the three-row assembler-failure degradation table, and it does **not** restate the parsing algorithm the script owns.
- [x] Given `scripts/eval.sh:2135–2136` forbids two retired prose strings in the command, when this story lands, then neither `Store parsed hints in \`context_hints\` map` nor `For bracketed references: search source file for matching rows/entries by name` appears in either skill — `grep -RF` across `skills/` returns nothing for both.
- [x] Given the knowledge-loading block carries rules nothing else records, when this story lands, then `story-context-assembly` preserves verbatim in meaning: the keyword normalization steps (lowercase, split path segments and hyphenated/slashed terms, drop the named stop words, keep 3+ character tokens plus exact path fragments), the `+3` tag / `+2` title-or-filename / `+1` body / `+1` related-artifact-path scoring weights, the per-agent category preferences for architecture-check, coding and review, the ~2KB cap, the truncate-by-score-before-dropping-entries rule, and all four graceful-degradation rows — including that a missing `.writ/knowledge/` is a **silent** no-op and not a warning.
- [x] Given the spec-lite sectioning block feeds five agents, when this story lands, then `story-context-assembly` carries the three `spec_lite_for_*` extraction rules and all three degradation rules (legacy format → full content for all agents; a missing section → full content plus the specific `⚠️` log line; empty `fetched_context` → spec-lite section only) — while the **per-agent routing table stays behind in the command**, because `scripts/eval.sh:2137–2141` pins all five of its rows to that file.
- [x] Given `dependency-context-loading` carries the record-reading rules, when this story lands, then it preserves: the two dependency-parsing sources, the story path construction, the completion check and its warning, the reverted-record skip with its `ℹ️` log line, the missing-WWB warning, the 1000-line threshold with all seven truncation-priority tiers in order, the truncation log line, the preserve-markdown-structure rule, the **direct dependencies only, never transitive** rule, the aggregation format, the position-in-prompt rule, and all four graceful-degradation cases.
- [x] Given Business Rule 3 rule 5 bans consumer vocabulary in a skill body and Business Rule 10 bans orchestration, when this story lands, then neither skill names a gate number, says "Step 2", says "spawn", contains `Read commands/`, `Read skills/`, a bare `Task(`, or a line-initial `/command` outside a fenced block — and both `description:` values are bare-imperative verb phrases.
- [x] Given this story is additive, when this story lands, then `git diff --name-only` lists only the two new `skills/*/SKILL.md` paths, `.writ/manifest.yaml`, and `SKILL.md` — `commands/implement-story.md` is untouched and still carries the source prose.

## Implementation Tasks

- [x] 2.1 Read `commands/implement-story.md` lines 95–340 in full, plus `.writ/docs/context-hint-format.md`, `.writ/docs/what-was-built-format.md`, and `scripts/story-context.py`'s CLI contract — the skill must agree with the script, not with a memory of it
- [x] 2.2 Check the two intended names against `.writ/manifest.yaml`'s `skills:` block and against their head nouns per the Story 1 collision protocol, then scaffold both with `/new-skill`
- [x] 2.3 Author `story-context-assembly` — hint-assembler invocation and output mapping, the three-row assembler-failure degradation table, the full knowledge keyword/scoring/cap/degradation ruleset, and the three `spec_lite_for_*` extraction rules with their degradations. Leave the per-agent routing table out; it stays in the command
- [x] 2.4 Author `dependency-context-loading` — dependency parsing, path construction, completion and reverted-record handling, the seven-tier truncation priority, direct-only scoping, aggregation format, and the four degradation cases
- [x] 2.5 Apply the Compression Ledger entries that fall in this story's blocks and record the measured yield per entry — C3 (the overlapping graceful-degradation lists) applies here in part; note explicitly if a target yields less than projected rather than making up the difference elsewhere
- [x] 2.6 Run `bash scripts/lint-skill.sh` on both files; run the two `grep -RF` forbidden-string checks across `skills/`; confirm both files carry `status: candidate` and no `evidence:` block
- [x] 2.7 Run `bash scripts/gen-skill.sh` and `--check`; record each skill's byte size (`wc -c`) against the per-skill projections in `sub-specs/technical-spec.md` → *Per-skill projections* (`story-context-assembly` ~6,750, `dependency-context-loading` ~5,400), and flag any overshoot immediately rather than at Story 5 — the full-path ceiling has ~3,461 bytes of projected deficit and no room for a surprise, and both of these skills sit on the always-paid path

## Notes

**Technical considerations:**

- The two skills split on **read side vs. own side**. `story-context-assembly` builds the payload from the current story and its spec; `dependency-context-loading` reads records other stories already wrote. They share `.writ/docs/what-was-built-format.md` as a format authority but not a rule.
- `story-context-assembly` is the largest single extraction in this spec at roughly 6,720 source bytes. That is within the existing skill range (`conventional-commits` is 9,985 bytes), so it does not need splitting for size.
- The assembler-failure degradation table is mirrored in Python at `scripts/eval-story-context.py:436–460`, and three comments there cite it by location. If the table moves, Business Rule 7 permits updating those three pointers **as comments only**. That is the single permitted `scripts/` write in the entire spec; it is not a wedge for touching the file's logic.
- `21000` is `FETCHED_CONTEXT_BUDGET_BYTES`, and L108 instructs the reader to prefer the constant's current value in `scripts/story-context.py` over the number in prose. That deference rule is itself a rule — it travels.
- The `⚠️` / `ℹ️` log strings are user-visible output. Rewording them is a behavioral change under Business Rule 2 even though nothing lints them.

**Risks / challenges:**

- **The knowledge-loading block is the easiest place in this spec to lose a rule.** It is a nested procedure — extraction, then normalization, then search, then scoring, then per-agent preference, then assembly, then truncation — with four degradation rows appended. Reads as boilerplate; is not.
- **"Silent no-op" is a rule that looks like an omission.** A missing `.writ/knowledge/` produces *no* warning, deliberately. An author tidying the degradation table into consistency will "fix" it into a warning and change behavior.
- **Restating the assembler algorithm.** The command was deliberately rewritten to delegate to `scripts/story-context.py`, and `eval.sh` forbids the old prose by literal. Re-deriving it inside a skill would be invisible to that check and would recreate the exact divergence the delegation eliminated.
- **The seven truncation tiers are ordered.** Order is the rule. A bulleted list that loses the numbering loses the priority.
- **Skill-shaped prose vs. step-shaped prose.** These blocks are written as "do this, then this". `## How to Apply` may keep an ordered procedure — that is allowed and normal for a skill — but the framing must not reference a pipeline position it no longer occupies.

**Integration points:**

- Story 5 replaces lines 95–340 with the assembler invocation fence (pinned literal 1), the per-agent routing table (pinned literals 2–6), and a one-line reverted-record assertion (pinned literal 11), then places one inline `Read skills/<name>/SKILL.md` per skill: `story-context-assembly` at Step 2, `dependency-context-loading` **inside the has-dependencies branch** so a story with no dependencies never pays its ~5,400 bytes.
- **Both of these skills are on the always-paid path** (`story-context-assembly` on every run; `dependency-context-loading` on every run that has dependencies, regardless of mode). Neither is skipped by `--quick`. They are therefore the two extractions where compression yield matters most — a byte saved here is saved on nearly every invocation, while a byte saved in `boundary-map-computation` is only saved on full-pipeline runs.
- Story 6 walks the no-drift inventory rows for lines 95–340 against these two files. Every knowledge scoring weight and truncation tier is an inventory row.
- `story-context-assembly` is a plausible declaration for `implement-spec` later; nothing in its body may assume `implement-story`.
- `dependency-context-loading` and `what-was-built-authoring` (Story 4) are the read and write halves of the same record. They must agree on the record's shape without either restating the other — `.writ/docs/what-was-built-format.md` is the shared authority.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `bash scripts/lint-skill.sh skills/*/SKILL.md` clean
- [x] `bash scripts/gen-skill.sh --check` passes
- [x] `bash scripts/eval.sh` shows no new findings
- [x] Reviewed against Business Rules 2, 3, 4, 10
- [x] Measured byte size of both skills recorded against the technical spec's projections
- [x] `git diff --name-only` shows no path under `commands/` or `scripts/`

## Context for Agents

- **Business rules:** [BR2 relocate-and-contract, BR3 naming convention and collision protocol, BR4 reachability, BR7 no `scripts/` edits beyond the comment-only exception, BR10 skill bodies pass `lint-skill.sh` as capability prose] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The eight extracted skills — rows 1 and 2] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [`lint-skill.sh` forbids the vocabulary the gate blocks are written in; `scripts/eval-story-context.py` cites the assembler-degrade table by location] — from spec.md → ## Technical Concerns
- **Technical spec:** [Section Ledger rows for L95–340; Skill Specifications rows 1–2; Boundary rules that constrain authoring; Compression Ledger C3; Interaction Edge Cases — legacy spec-lite, absent knowledge dir, reverted records] — from sub-specs/technical-spec.md
- **Pinned literals:** [1 `scripts/story-context.py assemble`, 2–6 the routing table rows, 11 `Skip reverted records` — all stay in the command, not in these skills] — from sub-specs/technical-spec.md → Pinned Literals

---

## What Was Built

**Implementation Date:** 2026-08-12

### Files Created

1. **`skills/story-context-assembly/SKILL.md`** (7,414 bytes)
   - Three payloads in one capability: the assembler invocation with its output mapping and three-row invocation-failure degradation table; the full knowledge ruleset (keyword sources, four normalization steps, silent-skip, grep targets, the `+3`/`+2`/`+1`/`+1` weights, per-role category preferences, the ~2KB cap, the truncate-details-before-dropping-entries rule, four degradation rows); and the three `spec_lite_for_*` extraction rules with their three degradations. The per-agent routing table is deliberately **not** here.
2. **`skills/dependency-context-loading/SKILL.md`** (5,211 bytes)
   - Dependency parsing from both sources, story-path construction, the completion check with its warning, the reverted-record skip with its `ℹ️` line, the missing-WWB warning, the 1000-line threshold with all seven ordered truncation tiers, the truncation log line, preserve-markdown-structure, direct-only/never-transitive, the aggregation format, the position-in-prompt rule, and the four-row degradation table.

### Files Modified

- **`.writ/manifest.yaml`** — two `skills:` entries appended alphabetically, both `status: candidate`, no `evidence:` block.
- **`SKILL.md`** — regenerated by `scripts/gen-skill.sh`; `--check` clean.

### Implementation Decisions

1. **The assembler boundary is preserved, not re-derived.** `story-context-assembly` describes *invoking* `scripts/story-context.py` and mapping its three JSON keys; it does not restate the parsing algorithm the script owns. The `21000` deference rule travels with it — read the constant's current value from the script and prefer it over prose.
2. **"Silent no-op" is carried as a rule with its reason attached.** A missing `.writ/knowledge/` produces no warning, deliberately, and the skill says so — the row most likely to be "tidied" into a warning by a later author.
3. **The seven truncation tiers stay numbered.** Order is the rule; a bulleted list would lose the priority.
4. **The two skills split read-side vs. own-side.** `story-context-assembly` builds the payload from the current story and its spec; `dependency-context-loading` reads records other stories wrote. They share `.writ/docs/what-was-built-format.md` as an authority and restate none of each other.

### Test Results

**Verification:** structural.

- ✅ `bash scripts/lint-skill.sh skills/story-context-assembly/SKILL.md skills/dependency-context-loading/SKILL.md` — both clean, exit 0.
- ✅ Both files carry `status: candidate` with no `evidence:` block.
- ✅ `grep -RF 'Store parsed hints in \`context_hints\` map' skills/ commands/implement-story.md` — no output. `grep -RF 'For bracketed references: search source file' skills/ commands/implement-story.md` — no output.
- ✅ `bash scripts/gen-skill.sh --check` — no delta after regeneration.
- ✅ `git diff --name-only` shows no path under `commands/` or `scripts/`; `commands/implement-story.md` still carries the source prose (this story is additive).

### Measured sizes vs. projection (task 2.7)

| Skill | Projected | Measured | Delta |
|---|---|---|---|
| `story-context-assembly` | ~6,750 | **7,414** | **+664** |
| `dependency-context-loading` | ~5,400 | **5,211** | −189 |
| Subtotal | ~12,150 | **12,625** | **+475** |

**Overshoot flagged now, not at Story 5.** `story-context-assembly` came in at 8,048 bytes on first authoring and was compressed to 7,414 (−634) by tightening Purpose, When to Use and four prose transitions — no rule was removed to do it. The residual +664 is the honest cost of carrying three independent rulesets with four degradation tables in one file, and both of these skills sit on the always-paid path, so the +475 subtotal lands in **every** path figure Story 5 reports.

### Compression Ledger entries applied (task 2.5)

| Entry | Applied where | Projected | Measured yield |
|---|---|---|---|
| C3 (part) | The dependency-incomplete and missing-WWB degradation rows appear once, in `dependency-context-loading`'s four-row table, rather than duplicated between the loader and the record writer | ~400 total across C3 | ~180 realized in this story; the remainder falls to Story 4 |

No other ledger entry falls in L95–340.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** None
- **Security:** Clean
- **Boundary Compliance:** Additive only — two new skill directories plus the manifest and generated catalog.

### Deviations from Spec

None
