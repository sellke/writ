# Story 2: Author the `contract-lock` Skill

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer relying on `/create-spec` to never create a file before a contract is locked
**I want to** the cross-spec overlap procedure, the contract format, and the five-option lock decision authored as one skill with its ids, labels, and handlers intact
**So that** ADR-001's contract-first discipline is relocated rather than reinterpreted, and the one skill that every invocation mode reaches is written before the command is rewritten around it

## Acceptance Criteria

- [ ] Given rule-inventory rows 59–70 span the overlap check, the contract format, and the five-option decision, when this story lands, then `skills/contract-lock/SKILL.md` carries rows 60, 62–67, 69, and 70 — the single-level `.writ/specs/*/spec.md` glob with its natural `archive/` exclusion, the `spec-lite.md` read, the five keyword-extraction categories, the overlap comparison, the `⚠️ Cross-Spec Overlap` output format, the "lightweight heuristic, false positives acceptable" caveat, the ten-field contract format block including its emoji-prefixed headings, the five `AskQuestion` option **ids and labels byte-identical**, and all five response handlers.
- [ ] Given `eval.sh:1824` pins `spec-status.py` to the command and `eval.sh:1822`/`:1867` forbid two strings, when this story lands, then rule-inventory row 61 — the complete-family detection sentence with `python3 scripts/spec-status.py is-complete`, the bold/unbold tolerance, the three complete-family values, and the "do **not** match only the literal substring" warning — is **absent from the skill** and left in place in the command for Story 6, and `grep -n 'skip specs with \`Status: Complete\`'` and `grep -n 'grep -v archive'` return no output against `skills/contract-lock/SKILL.md`.
- [ ] Given Business Rule 4 requires the lock discipline to survive verbatim, when this story lands, then the skill's `AskQuestion` block diffs clean against `git show <base>:commands/create-spec.md | sed -n '458,482p'` on every option id, every label string, and every handler line — and the skill states that Phase 2 is reachable only through an explicit `yes` or the `--recommend` auto-lock, naming no third path.
- [ ] Given Compression Ledger entry 5 targets ~300 bytes shared with Story 5, when this story lands, then the contract format block is established as the **one authority** for the standard contract sections, with the measured yield recorded and coordinated against Story 5's use of the same pointer.
- [ ] Given this story is additive, when this story lands, then `git diff --name-only` shows no change to `commands/create-spec.md`, `bash scripts/lint-skill.sh skills/contract-lock/SKILL.md` exits 0, `bash scripts/gen-skill.sh --check` reports no delta, and `bash scripts/eval.sh` reports no new findings.

## Implementation Tasks

- [ ] 2.1 Read Story 1's recorded namespace reconciliation and confirm `contract-lock` survived the collision protocol unchanged. Re-measure `sed -n '391,404p;405,453p;454,483p' commands/create-spec.md | wc -c` against the 4,243 figure
- [ ] 2.2 Run `/new-skill contract-lock` — bare-imperative description covering composing a specification contract, checking it for overlap against in-flight specs, and presenting the bounded lock decision; manifest entry; `gen-skill.sh --check`
- [ ] 2.3 Author rows 60, 62–66 (the overlap procedure minus the pinned detection sentence) and row 67 (the contract format block), keeping the `⚠️ Cross-Spec Overlap` output format and the heuristic caveat
- [ ] 2.4 Author rows 69–70 (the `AskQuestion` block and its five handlers) with ids and labels byte-identical to the base file; verify by diff, not by eye
- [ ] 2.5 Apply Compression Ledger entry 5 — the contract format block becomes the single authority the two source-mode shape blocks point at. Coordinate the pointer wording with Story 5 so both sides name the same anchor; record the measured yield
- [ ] 2.6 Verify: `bash scripts/lint-skill.sh`, `bash scripts/gen-skill.sh --check`, `bash scripts/eval.sh`, the two `forbid_literal` greps against the skill, and `git diff --name-only` for command cleanliness
- [ ] 2.7 Check off rule-inventory rows 59–70 with destinations, marking 59, 61, and 68 as retained in the command for Story 6; record the skill's measured byte size

## Notes

**Technical considerations:**

- **This is the spec's highest-risk skill.** Every other extraction can produce a visibly wrong prompt; this one can produce an *unreviewed* wrong contract lock under `--recommend`, where no human sees the gate. **Amended 2026-08-12:** the maintainer ruling replaced eager `required_skills:` pre-loading with inline `Read skills/<name>/SKILL.md` at the point of need, so the failure class is now closed by **ordering, not eagerness** — `contract-lock`'s read is placed at Step 1.3b, strictly before the Step 1.4 proposal, the Step 1.4b decision, and the `--recommend` auto-lock. No path reaches the lock without it. That guarantee holds exactly as long as the read stays above the gate, and **nothing automated checks it**: this story's DoD and Story 6's placement evidence are the only enforcement. The content still has to be right on top of that.
- Row 61 is the one sentence in Step 1.3b that `eval.sh` pins, and it also encodes a real bug fix: the literal-substring match never worked against the bold `> **Status:** Complete` form. Relocating it would risk reintroducing exactly the defect the `forbid_literal` exists to prevent. It stays in the command; the skill describes the surrounding procedure without restating the detection rule.
- The overlap check is advisory in normal mode; under `--recommend` a *blocking* conflict is one of only three pause conditions (row 16). That pause lives in `## Recommended Mode` and is untouched.
- The ten-field contract format block is echoed verbatim into `spec.md` by Step 2.4 (row 86) and is what `/edit-spec` and `/verify-spec` read back. It is not a template to improve.
- `edit-spec` is a prospective consumer, named in spec.md's extraction map. `status_evidence` records only the actual consumer.

**Risks / challenges:**

- **Rewording an `AskQuestion` label.** The five options are a bounded decision surface. Shortening `blueprint`'s label from "See the planned folder structure and documents" changes what the user is agreeing to.
- **Merging the overlap check into the contract format** because both are "contract stuff." They are sequential steps with different triggers; the inventory keeps them as separate rows for that reason.
- Adding a sixth option, or collapsing `edit` and `questions`, is a redesign (Business Rule 2) even though it looks like cleanup.
- Compression Ledger entry 5 is shared with Story 5. If both stories independently invent a pointer, the "one authority" is two. Coordinate or sequence.

**Integration points:**

- Story 5's two source-mode contract shape blocks point at this skill's format block. `lint-skill.sh` forbids `Read skills/` inside a skill body, so the pointer is prose ("the standard contract sections") resolved by the command's phase list, not a cross-skill read.
- Story 6 names the contract lock gate in the phase list and places this skill's inline `Read` at Step 1.3b; the gate name must match what this skill describes, and the read must sit **above** the gate.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/contract-lock/SKILL.md` exits 0
- [ ] `bash scripts/gen-skill.sh --check` reports no delta
- [ ] `bash scripts/eval.sh` shows no new findings
- [ ] `AskQuestion` block diffed clean against the base file on ids, labels, and handlers
- [ ] Both `forbid_literal` strings absent from the skill
- [ ] `git diff --name-only` shows no path under `commands/`
- [ ] Compression Ledger entry 5's measured yield recorded and coordinated with Story 5
- [ ] Rule-inventory rows 59–70 checked off; 59, 61, 68 marked as retained in the command
- [ ] Skill's measured byte size recorded for Story 6's ceiling arithmetic

## Context for Agents

- **Business rules:** BR2, BR3 (declaration complete, phase list carries load discipline), BR4 (contract-lock verbatim), BR5 (`--recommend` untouched), BR6 (pinned strings), BR9 — from spec.md → 📋 Business Rules
- **Rule inventory rows:** 59–70, with 59, 61, 68 retained in the command — from sub-specs/technical-spec.md → Rule Inventory
- **Pin table:** `spec-status.py`, and the two `forbid_literal` strings — from spec.md → The finding that reframes the work
- **Compression Ledger entry 5** — from sub-specs/technical-spec.md → Compression Ledger
- **Technical concerns:** "`--recommend` is the mode most exposed to load-order defects" — from spec.md → Technical Concerns
