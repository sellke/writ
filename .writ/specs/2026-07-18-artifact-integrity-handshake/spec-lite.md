# Artifact Integrity + Handshake (Lite)

> Source: .writ/specs/2026-07-18-artifact-integrity-handshake/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** (1) "Artifact Integrity" standing rule in `_preamble.md` — verify Required Artifacts before work; required missing → HALT + bounded repair; optional missing → warn+degrade. (2) "Artifact Map" section in the regenerated `.writ/context.md`. (3) Required Artifacts declarations on 7 high-traffic commands. NO new files.

**Implementation Approach:**
- Markdown-only product edits + one eval check.
- Extend the existing `context.md` schema (in implement-story Step 2) — do not create `.writ/index.md`.
- Required vs optional distinction; only required halts.
- Bounded repair: name the creating command, never auto-run mutation.

**Files in Scope:**
- `commands/_preamble.md` — Artifact Integrity section
- `commands/implement-story.md`, `implement-spec.md`, `status.md` — context.md Map schema + Required Artifacts
- `commands/create-spec.md`, `implement-phase.md`, `ship.md`, `release.md` — Required Artifacts blocks
- `scripts/eval.sh` (+ helper)

**Error Handling:**
- Required missing → HALT + bounded repair AskQuestion
- Optional missing → warn + degrade
- Repair declined → clean HALT, no mutation

**Integration Points:**
- Reuses `context.md` regeneration in implement-story/implement-spec/status; adapter-neutral existence checks.

---

## For Review Agents

**Acceptance Criteria:**
1. Missing required artifact → specific HALT + bounded repair offer.
2. Missing optional artifact → warn + continue.
3. Regenerated `context.md` has an Artifact Map + integrity line.
4. No `.writ/index.md` created.
5. `eval.sh` asserts preamble rule + 7 declarations and passes.

**Business Rules:**
- Required vs optional explicit; only required halts.
- Bounded repair (name creating command); no auto-mutation.
- Map lives in context.md (regenerated, never patched).
- Adapter-neutral.

**Experience Design:**
- Entry: automatic at top of commands with Required Artifacts.
- Happy path: check → present → proceed.
- Moment of truth: early specific halt instead of cryptic mid-run failure.
- Error: required HALT+repair; optional warn+degrade.

---

## For Testing Agents

**Success Criteria:**
1. HALT fires only for required-artifact absence.
2. Optional absence degrades gracefully.
3. Artifact Map present after regeneration.
4. eval check passes.

**Shadow Paths to Verify:**
- **Happy:** all required present → proceed.
- **Nil:** required missing → HALT + repair offer.
- **Empty:** optional missing → warn + continue.
- **Upstream error:** repair declined → clean halt.

**Edge Cases:**
- `context.md` absent → regenerated with Map.
- Legacy command without declaration → unaffected (only 7 declare).
- No `.writ/index.md` ever created.

**Verification Strategy (methodology repo):**
- Markdown deliverables → verified via `scripts/eval.sh` static checks + manual command runs on this repo. No code coverage target.
