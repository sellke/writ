# Story 1: Namespace Reconciliation and the `requirements-discovery` Skill

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** maintainer whose `skills/` namespace is being written into by six specs at once
**I want to** the pilot's naming convention read and the collision protocol run for all five of this spec's names **before** any skill file exists, and then the largest extraction authored as the worked example
**So that** four sibling stories are not each re-deciding a shared namespace, and the extraction pattern is proven on the block furthest from any `eval.sh` pin before it is applied to blocks that are pinned

## Acceptance Criteria

- [ ] Given `2026-08-12-disclosure-implement-story` owns the naming convention and writes it into `.writ/docs/skills.md` → *Extraction Patterns*, when this story lands, then that section has been read and all five of this spec's names have been checked against the live `.writ/manifest.yaml` `skills:` block **by name and by head noun** — with the result of each check recorded in this story's notes, and any name that collides replaced or resolved by declaring the incumbent with an ADR-014 `type: promotion` entry rather than authoring a near-duplicate.
- [ ] Given Step 1.3 (307–390) and `## Example Usage` (787–865) total 9,062 bytes, when this story lands, then `skills/requirements-discovery/SKILL.md` exists carrying rule-inventory rows 43, 46–58 and the scan detail of row 44 — with the 95%-confidence threshold, the "never declare final question" rule, the four gap categories, the nine/eight/seven topic questions, the eight critical-analysis responsibilities, and the seven pushback phrasings all present at their current values.
- [ ] Given Compression Ledger entry 1 targets ~1,200 bytes, when this story lands, then the worked transcript's `## Specification Contract` echo (829–859) — which restates the Step 1.4 format block field-for-field 400 lines after it is specified — is contracted to a pointer, the **measured** yield is recorded, and every rule-bearing line of the transcript (the pushback exchanges, the cost framing, the lock handoff) survives.
- [ ] Given `lint-skill.sh` rejects command invocation, skill chaining, subagent dispatch, and line-initial slash commands, when this story lands, then `bash scripts/lint-skill.sh skills/requirements-discovery/SKILL.md` exits 0, the file carries `status: candidate`, `disable-model-invocation: true`, a bare-imperative `description:`, `## Purpose`, and `## When to Use`, its `status_evidence` names only the **actual** consumer (not the prospective `plan-product` / `edit-spec` readers), and `.writ/manifest.yaml` holds an alphabetically-placed entry with `bash scripts/gen-skill.sh --check` reporting no delta.
- [ ] Given this story is additive and Story 6 is the only writer on the command, when this story lands, then `git diff --name-only` shows **no change to `commands/create-spec.md`**, the command still carries its Step 1.3 prose, and `bash scripts/eval.sh` reports no new findings against the pre-story baseline.

## Implementation Tasks

- [ ] 1.1 Read `.writ/docs/skills.md` → *Extraction Patterns* and the pilot spec's Business Rule 3. If the pilot's Story 1 has not landed that section yet, stop and escalate rather than inventing a second convention
- [ ] 1.2 Run the collision protocol for all five names — `requirements-discovery`, `contract-lock`, `spec-package-authoring`, `user-story-decomposition`, `spec-source-prepopulation` — grepping the live `.writ/manifest.yaml` `skills:` block for each name **and its head noun**. Record every result; resolve any collision per the protocol before Stories 2–5 start
- [ ] 1.3 Re-measure the baseline: `python3 scripts/measure-invocation.py --root . --command create-spec` and `sed -n '307,390p;787,865p' commands/create-spec.md | wc -c`. Record actuals; do not carry the spec's figures forward unverified
- [ ] 1.4 Run `/new-skill requirements-discovery` — bare-imperative description, `status: candidate`, manifest entry, `bash scripts/gen-skill.sh --check`
- [ ] 1.5 Author the body from rule-inventory rows 43, 46–58 and row 44's scan detail, preserving every threshold and every question verbatim; place the worked transcript under `## Examples` with row 58's UX note
- [ ] 1.6 Apply Compression Ledger entry 1 to the transcript's contract echo; measure and record the yield; confirm no pushback exchange, cost-framing line, or lock-handoff line was lost
- [ ] 1.7 Verify: `bash scripts/lint-skill.sh`, `bash scripts/gen-skill.sh --check`, `bash scripts/eval.sh`, `git diff --name-only` shows nothing under `commands/`. Check off rule-inventory rows 43, 44 (scan detail), 46–58 with destination headings

## Notes

**Technical considerations:**

- **This story carries the namespace work for the whole spec.** Four sibling stories run in parallel after it; if each ran its own collision protocol they would race against each other and against the pilot's eight names. One reconciliation, recorded once, is the point.
- The extraction itself is deliberately first among the five: largest single block (19.5% of the file), no `eval.sh` literal pin, so a mistake is cheap and the shape is established where it costs least.
- The worked transcript is 3,491 bytes of a single blockchain-chat example. It teaches the pushback discipline, so it belongs with the pushback rules. Its *contract echo* half restates the Step 1.4 format — that half is Compression Ledger entry 1 and is the only part eligible for contraction.
- Row 44 splits. The Step 1.1 scan *detail* (which files, which search) moves; the **no files are created during Phase 1** rule is a gate and stays in the command for Story 6 to place in the phase list.
- Row 46 — ADR-001's "AskQuestion when you know the option space, Plan Mode when you need to discover it" — moves with the discovery rules. It is the principle behind the conversation, not a gate.
- `status_evidence` names `commands/create-spec.md` as the one consumer. `plan-product` and `edit-spec` are *prospective* readers named in spec.md's extraction map; writing them in as evidence would assert multi-consumer use that does not exist and would inflate the ADR-014 lifecycle state.

**Risks / challenges:**

- **Compressing the topic questions into categories.** The nine experience / eight rule / seven technical questions read as redundant and are not: each names a distinct failure the conversation misses without it. They are explicitly excluded from the Compression Ledger.
- The 95% confidence threshold is a number someone chose. Preserved as-is.
- `lint-skill.sh` rejects lines *beginning* with a slash command. The transcript's `Developer: /create-spec "…"` line does not begin with `/`, so it passes — verify rather than assume.
- Treating Compression Ledger entry 1 as a licence to trim the transcript generally. It is scoped to lines 829–859, the contract-format echo, and nothing else.

**Integration points:**

- Stories 2–5 depend on this story only for the namespace reconciliation and the established shape. Their file sets are otherwise disjoint.
- Story 6 reads the rule-inventory checkoffs from all five extraction stories when it reconciles all 113 rows.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Collision-protocol results recorded for all five names
- [ ] `bash scripts/lint-skill.sh skills/requirements-discovery/SKILL.md` exits 0
- [ ] `bash scripts/gen-skill.sh --check` reports no delta
- [ ] `bash scripts/eval.sh` shows no new findings vs. the pre-story baseline
- [ ] `git diff --name-only` shows no path under `commands/`
- [ ] Compression Ledger entry 1's measured yield recorded
- [ ] Rule-inventory rows 43, 44 (scan detail), 46–58 each checked off with a destination heading
- [ ] Authored skill's measured byte size recorded for Story 6's ceiling arithmetic

## Context for Agents

- **Load mechanism (amended 2026-08-12):** no `required_skills:`; each skill inline-read at the narrowest step; the declare-everything clause is **reversed** — from spec.md → *Approved Scope Change — Load Mechanism* and → *Load placement*. This story authors a skill and does not place any read (Story 6 does), but the ruling is what makes the extraction worth doing at all
- **Inherited convention:** naming rules and collision protocol — from spec.md → Inherited Convention, and `.writ/docs/skills.md` → *Extraction Patterns*
- **Business rules:** BR2 (rule inventory), BR7 (reachability), BR9 (naming + collision), BR10 (one command file), BR13 (leanness disposition) — from spec.md → 📋 Business Rules
- **Rule inventory rows:** 43, 44 (partial), 46–58 — from sub-specs/technical-spec.md → Rule Inventory
- **Compression Ledger entry 1** — from sub-specs/technical-spec.md → Compression Ledger
- **Skill authoring constraints:** lint grammar, required sections, `status_evidence` honesty — from sub-specs/technical-spec.md → Skill Authoring Constraints
