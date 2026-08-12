# Progressive Disclosure — `/release` (Lite)

> Source: .writ/specs/2026-08-12-disclosure-release/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `commands/release.md` (28,589 B / 640 lines) → thin contract; per-phase procedure → `skills/<name>/SKILL.md`, reached by an **inline `Read skills/<name>/SKILL.md` at the step that needs it**.

**MECHANISM CHANGE (maintainer ruling 2026-08-12; contract block unedited, see spec.md → *Approved scope change*).** `required_skills:` is **NOT used**. It is an eager pre-load (`system-instructions.md`; `adapters/claude-code.md:396`) — declaring the five skills would have raised the floor to ~58,120 from 53,549. The inline read is genuinely conditional. `scripts/measure-invocation.py` was fixed in `e8f2a09`: `floor` = base + command + eager skills; `ceiling` = floor + inline-read skills.

**Budget (binding):** `command_bytes` **≤ 24,960** (shared base: `system-instructions.md` 20,153 + `_preamble.md` 4,807) **and** `ceiling_bytes` **≤ 63,534** — the **corrected** pre-spec ceiling, not the broken tool's 53,549. Pre-spec: floor 53,549 / cond 9,985 (`release.md:88` reads `conventional-commits`) / ceiling 63,534. `eager_bytes` must stay 0. 400 lines is a secondary, non-binding tripwire.

**Projection — report every path, and be honest that the full-release saving is ~nil:**

| Path | Projected | vs pre-spec | Δ |
|---|---|---|---|
| Abort in Phase 1 before Step 1.2 (floor) | 41,551 | 53,549 | −22.4% |
| Gate blocks at Step 1.3 | 57,941 | 63,534 | −8.8% |
| `--no-tag` / `bump_only` | 60,199 | 63,534 | −5.2% |
| **Full release (the common run)** | 63,411 | 63,534 | **−0.2%** |
| Tool worst path (incl. never-reached npm) | 66,165 | 63,534 | +4.1% |

Only the last row misses the bar, and by less than `npm-package-publication`'s own size. `--dry-run` is NOT a saving — it previews the Phase 4 commands, so it reads `git-tag-publication` too.

**Placement is the mechanism — "declare all, don't curate" is REVERSED.** One inline `Read` per skill, at the narrowest step that needs it. **No hoisting**: not in frontmatter, not in `## Overview`, not in the phase-list table (which names skills but carries no `Read skills/` string), not in a batched load block — a hoisted read is `required_skills:` in prose and forfeits the whole saving. `npm-package-publication`'s **exemption is reinstated as correct**: its `Read` sits on the `## References` line marking it manual/out-of-band, no `/release` run reaches it, so no run pays its ~2,754 B. **`conventional-commits` stays an inline read in the command** — not a declaration, not re-extracted (`lint-skill.sh:52` forbids `Read skills/` inside a skill); the corrected tool counts it on **both** sides, so the exclusion is automatic and symmetric (Story 5 also reports the excluded pair, 53,549 → ≈56,180). **Inline reads are a command instrument:** all six live in `commands/release.md`; `grep -n 'Read skills/' skills/*/SKILL.md` → no hits, and a code fence is not a workaround.

**Retained (ADR-021 clause 1 + eval pins + production boundary):** frontmatter contract, `## Overview`, `## Invocation` (the `## Modes` table renamed, 7 rows), phase list with gate names, the **full release gate** (1.3a/b/c + 3-row table), the **archival hook** (154–164, byte-identical), both `AskQuestion` gates (1.5, 2.3), `## Error Handling`, rollup core (405–424, 433–441), `## Completion`, `## References`.

**Extraction map — 15 ranges, 14,468 B out** (line numbers = pre-spec file; delete **bottom-up**):

| Skill | Ranges | B |
|---|---|---|
| `changelog-generation` | E2 78–97 · E5 236–292 | 2,354 |
| `semver-version-bump` | E1 51–76 · E4 203–209 · E6 328–367 · E11 520–545 | 3,201 |
| `git-tag-publication` | E7 371–403 · E8a 425–431 · E8b 443–447 · E9 449–470 · E10 473–518 | 3,912 |
| `readme-freshness-audit` | E3 167–200 | 1,858 |
| `npm-package-publication` | E12a 165 · E12b 600–626 | 2,454 |
| (contracted into `## References`) | E13 548–563 | 689 |

**Naming convention is the pilot spec's (BR8), not this spec's:** kebab-case noun phrase, 2–3 words, ≤30 chars, `<object>-<operation>`, **never named after the extraction site** (this is why `release-publication` became `git-tag-publication`), `description:` a bare imperative. Collision protocol: grep the manifest for the name **and its head noun**; first writer owns it; a later spec declares the existing skill rather than forking. Re-read `ls skills/` before scaffolding — three sibling specs write here in between.

**Owned surfaces, total:** `commands/release.md`, the five `skills/<name>/SKILL.md`, `.writ/manifest.yaml`, root `SKILL.md`, and one bound-justification entry in `.writ/leanness-baseline.json` (never `--update-baseline`). Nothing else — no `scripts/eval.sh`, no `eval-leanness.py`, no `archive-sweep.py`, no other command, no `_preamble.md` (93/95 lines, cap not raised), no ADR (the pilot spec owns the ADR-021 amendment).

---

## For Review Agents

**Acceptance Criteria:**
1. `command_bytes` ≤ 24,960; `floor_bytes` < 53,549; `unresolved_skills: []`; `eager_bytes: 0`; no "loads both ways" warning.
2. `ceiling_bytes` ≤ 63,534, or a three-part justification: measured overage + compression attempted with **measured** yield + explicit maintainer acceptance. "Only 4% worse" is not a justification, and a cheaper path is an explanation, not a retirement.
2a. Every named partial path measured, not projected — and a ~0% full-release result reported in those words.
3. `bash scripts/eval.sh` — no new findings vs. the base-SHA baseline. All 15 pins present, `is_complete_family` absent.
4. Archival hook (154–164) byte-identical and still nested inside `LAST_MERGED_SHA == HEAD_SHA`, itself inside `Unless --skip-gate is set`.
5. The **whole frontmatter block** and `## Completion` byte-for-byte unchanged — no added key, no `required_skills:` anywhere in the file.
6. Drift ledger: 15 rows, every `semantic delta` ∈ {`none (verbatim)`, `contracted: <reason>`}.

**Business Rules (the ones that decide PASS/FAIL):**
- **BR1 floor AND worst-path ceiling AND paths:** floor-only (or best-path-only) reporting is a failed story. `command_bytes ≤ 24,960`, `ceiling_bytes ≤ 63,534`; overage needs the three-part justification.
- **BR2 no redesign:** relocate and contract only. Proof = drift ledger checked with `git show <base>:commands/release.md | sed -n '<range>p'`. No step added, removed, reordered, or re-defaulted. The extraction map is unchanged by the mechanism ruling.
- **BR3 placement, not declaration:** one inline `Read` per skill at its narrowest step **and** the skill named in the phase list; no `required_skills:`; no hoisting; `unresolved_skills: []`.
- **BR4 production boundary — now STRONGER:** a conditionally-loaded skill may genuinely fail to load, so nothing that decides may sit behind a `Read`. Release gate, `--skip-gate`, both `AskQuestion` blocks, the dirty-tree/no-changes prompts, and the rollup's non-blocking + `writ.auditNotes` guarantees stay in the command. Test: *if this `Read` never fires, does `/release` still refuse to release when it should?*
- **BR5 archival hook placement:** stays in the command, verbatim, in the same branch. It is silent and best-effort — a `Read` that never fires would disable it with no signal, and under conditional loading that is the ordinary case, not a hypothetical.
- **BR6 eval pins:** 15 required literals + 1 forbidden, asserted against the command file itself. `require_literal` does not follow `required_skills:`.
- **BR7:** `_preamble.md` is not a destination and its 95-line cap is not raised.
- **BR8:** naming convention + collision protocol inherited from the pilot spec; consume a sibling's skill, never fork it.
- **BR9:** skills born `candidate`, `disable-model-invocation: true`, lint-clean; no `Read commands/`, `Read skills/`, `Task(`, or a line opening with a slash command.
- **BR10:** findings in files this spec doesn't own get recorded, not fixed.

---

## For Testing Agents

No application code. Verification is structural and byte-measured.

**Success Criteria:**
1. `python3 scripts/measure-invocation.py --root . --command release --format table` → `command_bytes` ≤ 24,960, floor down, ceiling reported, `unresolved_skills: []`.
2. Pin script (`sub-specs/technical-spec.md` → *Pin verification command*) → `PINS OK`.
3. `bash scripts/eval.sh --check=post-merge-archival --check=git-notes-audit --check=artifact-integrity --check=preamble --check=length` → no findings; then a full `eval.sh` run vs. baseline.
4. `git show <base>:commands/release.md | sed -n '154,164p'` diffs clean against the rewritten hook block; same for frontmatter (1–10) and `## Completion` (627–634).
5. `grep -rn -- '--skip-gate\|AskQuestion\|Proceed with this release\|Block release' skills/*/SKILL.md` → no output; each term present in `commands/release.md`.
6. `bash scripts/lint-skill.sh skills/*/SKILL.md` → exit 0. `bash scripts/gen-skill.sh --check` → no delta.
7. `python3 scripts/eval-post-merge-dogfood.py` → still reports its pre-spec 0-of-2 count, not an error.
8. `wc -l commands/release.md` → recorded; under 400 is the target, a miss is reported not failed.
9. `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` → `status: ok`, this spec ordered after `2026-08-12-disclosure-implement-story` and before `2026-08-12-governor-enforcement`. Anything else means a sibling moved — investigate, don't edit the dependency line.
10. `.writ/leanness-baseline.json` carries a bound justification for the `skills` surface naming this spec; `--update-baseline` not run.

**Edge Cases:**
- `--dry-run` reads everything except `npm-package-publication` — it previews the Phase 4 commands, and E10's preview block lives in `git-tag-publication`. Don't claim a saving that isn't there; don't move E10 to manufacture one (redesign).
- `--no-tag` / `bump_only` skip Phases 4–5 entirely; that is `git-tag-publication`'s whole load (~3,212 B) and the largest real conditional win among completed releases.
- A repo with no `README.md` never issues the Step 1.4 `Read` — ~2,258 B genuinely unpaid. That is the mechanism working.
- `release.md:88` contains `Read skills/conventional-commits/SKILL.md` — the lint rejects it inside a skill. Leave it in the command at its own step; don't duplicate the vocabulary, don't declare the skill, don't put it on a phase-list row.
- `semver-version-bump` is read at two anchors and charged once (the tool dedupes by name).
- E6's `sed -i` lines are GNU-flavored and break on BSD `sed`. Pre-existing defect: carry it across unchanged, record it (BR2, BR10).
- `MAX_SKILLS = 12` is crossed before this spec runs (6 today, pilot adds 8 → 14; this spec → 19). Record it for `2026-08-12-governor-enforcement`; do not raise the cap.

**Anti-goal to watch for:** a thin contract that is thin in name only — bytes relocated into skills every invocation loads anyway (which is exactly what `required_skills:` would have produced, and what a hoisted `Read` still produces), a path table nobody measured, and 15 ledger rows reading "verbatim" that nobody diffed.
