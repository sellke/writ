# Progressive Disclosure — /ship (Lite)

> Source: .writ/specs/2026-08-12-disclosure-ship/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `commands/ship.md` (28,371 B / 627 lines) → thin contract + four new skills, each reached by an **inline `Read skills/<name>/SKILL.md` at the step that needs it**. Binding cap **≤ 24,960 bytes** (= the shared base: `system-instructions.md` 20,153 + `commands/_preamble.md` 4,807). Design target ≤ 13,000 B / ~265 lines. Measure with `python3 scripts/measure-invocation.py --root . --command ship`.

**MECHANISM CHANGE (maintainer ruling 2026-08-12; contract block unedited — see spec.md → *Approved scope change*).** `required_skills:` is **NOT used**. It is an eager pre-load (`system-instructions.md`; `adapters/claude-code.md:396`) — declaring the five skills would have raised the **floor** from 53,331 to ~57,200. **This spec's own finding is why:** `ship.md:224` already inline-reads `conventional-commits` at Step 4, the step that needs it — the one thing `/ship` did that the old tool could not see was the one thing worth copying. `scripts/measure-invocation.py` was fixed in `e8f2a09` and now prints `floor 53,331 / cond 9,985 / ceiling 63,316`, exactly the adjusted baseline this spec computed by hand.

**Files in scope:** `commands/ship.md` · `skills/{repo-convention-detection,commit-organization,pr-body-composition,audit-digest-composition}/SKILL.md` (NEW, via `/new-skill`) · `.writ/manifest.yaml` (4 entries) · root `SKILL.md` (regenerate) · `.writ/leanness-baseline.json` (`skills`-surface justification) · `sub-specs/clause-ledger.md` (Story 1). **Nothing else.** No `scripts/`, no `commands/release.md`, no `_preamble.md` (93/95 lines, cap owned by `2026-08-11-autonomy-gate-classes`).

**Five inline reads, each at its step — placement is the mechanism.** `repo-convention-detection` @ Phase 1 · `commit-organization` @ Step 4 beside the existing `conventional-commits` read · **`ship.md:224` preserved unchanged** · `pr-body-composition` @ Phase 5 body-assembly, *before* the retained draft-vs-ready / `gh pr create` block · `audit-digest-composition` @ Step 6.2, *after* the `writ.auditNotes` opt-out gate. **No hoisting** — not frontmatter, not `## Overview`, not the phase-list table (which names skills but carries no `Read skills/` string). A hoisted read is `required_skills:` in prose. Frontmatter is now byte-for-byte unchanged: **no added key**.

**Every path improves** (projected, vs the *correct* pre-spec figure per path — 53,331 for runs that never reach Step 4, 63,316 for runs that do): conflict pause @ Step 2 **39,010 (−26.9%)** · `--test` abort **39,010 (−26.9%)** · `--no-split` **48,995 (−22.6%)** · PR open w/ `auditNotes=false` **56,295 (−11.1%)** · full run **57,510 (−9.2%)**. Floor 53,331 → ~36,610 (−31.4%). **The ceiling now clears 63,316 by ~5,800 B, so no BR1 justification is expected — do not write one that isn't owed.**

**Extraction map:**
| Phase | Bytes today | Destination |
|---|---|---|
| Step 1 Detect Conventions | 2,821 | `repo-convention-detection` |
| Step 2 Merge/rebase | 872 | retained (conflict pause) |
| Step 3 Tests (`--test`) | 1,064 | retained (failure branch sets draft) |
| Step 4 Commit Intelligence | 4,182 | `commit-organization`; approval `AskQuestion` **retained** |
| Step 5 PR Creation | 5,818 | `pr-body-composition`; push/`gh pr create`/draft-vs-ready **retained** |
| Step 6 Audit Note | 3,610 | ~1,200 B of digest composition → `audit-digest-composition`; **attach contract retained** |
| Pipeline ASCII (1,445) | — | replaced by the phase list |
| Dry Run Mode (1,138) | — | each skill carries its own preview (`deduped`) |
| Error Handling (2,076) / When-to-use (546) + Integration (431) | — | compressed in place to ≤900 B / ≤600 B |

**Retained beyond ADR-021's list, each for a reason:** `## Required Artifacts` (`_preamble.md` Artifact Integrity depends on the declaration) · the production-boundary block · the audit-note attach contract.

**Phase list carries gate names:** 1 none · 2 pause-on-conflict · 3 failure branch · 4 AskQuestion approval · 5 **production boundary (human gate)** · 6 none, non-blocking.

**Key repo facts:**
- `ship.md:224`'s inline read of `conventional-commits` (9,985 B) is now counted by the fixed tool on **both** sides — real pre-spec ceiling for any run reaching Step 4 is **63,316**, not 53,331. Preserve the line in place: not a declaration, not re-extracted, not moved to a table row.
- `ship.md:226` carries a Phase 7 **Non-extraction note** saying no further extraction from `/ship` was warranted. ADR-021 reverses it. Supersede in place (Story 4) with the reasoning; do not delete. Note the reversal's evidence is now *stronger* than at authoring time — the measured per-invocation saving is 9–27% depending on path, not a projected regression needing a justification.
- `scripts/eval-git-notes-audit.py` `scenario_ship()` asserts **7 literal strings against `commands/ship.md`**. Extracting Step 6 wholesale fails `eval.sh`.
- Contract erratum: the locked text cites `2026-08-18-git-notes-audit-channel`; real slug is **`2026-07-18-git-notes-audit-channel`** (in `.writ/specs/archive/`). Contract block unedited.
- `scripts/lint-skill.sh` rejects `Read skills/` in skill prose (skill chaining). Code blocks exempt.

---

## For Review Agents

**Business Rules (decide PASS/FAIL):**
- **BR1 ceiling — the extracted system may not weigh more than the monolith:** floor **must fall**; ceiling bar **≤ 63,316** (the corrected pre-spec ceiling, printed by the fixed tool). Never closed by deleting rules. **The old 53,331/63,316 escalation ladder is withdrawn as obsolete** — it existed because the instrument was blind and `required_skills:` made 9,985 B appear from nowhere; neither condition holds. Report the path table and the `conventional-commits`-excluded pair (53,331 → ~47,525) as information, not as a defence.
- **BR2 no redesign:** every normative clause enumerated in `sub-specs/clause-ledger.md` gets exactly one disposition — `retained` / `skill:<name>#<section>` / `deduped:<reason>`. No disposition = dropped clause = failure. Literal greps back it (see spec.md BR2 table).
- **BR3 placement, not declaration (REVERSED from "declare all, not a subset"):** one inline `Read` per skill at the narrowest step **and** the skill named at its phase; `conditional_skills` lists all five with `unresolved_skills: []`; `eager_bytes: 0`; no hoisting. `eval-leanness.py check_required_skills` has nothing to resolve and its silence proves nothing.
- **BR4 production boundary — now STRONGER:** a conditionally-loaded file may genuinely fail to load, so no gate-crossing clause may sit behind a `Read`. Retained in the command: draft-vs-ready table + `--draft`; `git push -u` + `gh pr create` + `gh auth` rescue; the commit-plan `AskQuestion`; merge-conflict pause + `--test` failure branch. Test: *if this skill silently failed to load, could `/ship` open the wrong PR?*
- **BR5 reuse:** `commit-organization` owns *which* commit; `conventional-commits` owns *how to phrase*. No restated type/scope/summary/body/footer rules, no `Read skills/` line (`lint-skill.sh:52`). The composition is **two inline reads at Step 4 in the command**, not two declarations.
- **BR6 provenance — now sharper:** command retains opt-out gate, landed-SHA resolution (squash/merge/rebase), `git notes --ref=writ add -f -F`, the `refs/notes/commits` prohibition, non-blocking rule, **minimal-digest fallback**, confirmation line. "The skill will be there" was arguable under an eager pre-load; under an inline `Read` it is not. If the skill never loads, `/ship` still attaches the fallback digest.
- **BR7:** reference `scripts/resolve-spec-reference.py`; never reimplement the heuristic, never edit the script. `matched` → populate; `none`/`ambiguous` → "Standalone change (no spec)".
- **BR8:** `_preamble.md` untouched (93/95), cap not raised. **BR9:** one command file only; nothing under `scripts/`, `agents/`, `adapters/`, `.writ/decision-records/`. **BR10:** skills born `candidate`, lint-clean, manifest-registered — naming per `.writ/docs/skills.md` → *Extraction Patterns* (landed by the dependency): kebab-case `<object>-<operation>`, 2–3 words, ≤30 chars, never named after a command/gate/step; bare-imperative `description:`; grep the manifest for the name **and its head noun** before scaffolding. **BR11:** record a bound `skills`-surface justification in `.writ/leanness-baseline.json`; **never `--update-baseline`**. **BR12:** the **whole frontmatter block** and `## Completion` preserved byte-for-byte — no added key, no `required_skills:` anywhere in the file.

**Acceptance:** ship.md ≤ 24,960 B · floor < 53,331 · **ceiling ≤ 63,316** (projected ~57,510, a clean pass) · `eager_bytes: 0`, 5 conditional skills, 0 unresolved, no "loads both ways" warning · path table measured · ledger fully dispositioned · all BR2 literals present · `eval.sh` clean incl. 7/7 `git-notes-audit` ship checks · `lint-skill.sh` 0 and `grep 'Read skills/' skills/*/SKILL.md` empty · `gen-skill.sh --check` no delta · diff touches nothing under `scripts/`, exactly one file under `commands/`.

---

## For Testing Agents

No application code. Verification is structural, from the repo root:

```bash
python3 scripts/measure-invocation.py --root . --command ship   # command_bytes, floor, ceiling, resolved_skills
wc -c -l commands/ship.md                                        # <= 24960 bytes; <= 400 lines (tripwire)
grep -c 'refs/notes/writ\|git notes --ref=writ add -f -F\|writ.auditNotes\|refs/notes/commits\|minimal digest\|landed\|squash' commands/ship.md
grep -n 'resolve-spec-reference.py' commands/ship.md skills/pr-body-composition/SKILL.md
grep -n 'Read skills/' commands/ship.md                          # 5, each at a step, none in the phase table
grep -c 'required_skills' commands/ship.md                       # expect 0
grep -n 'Read skills/' skills/*/SKILL.md                         # expect nothing (lint-skill.sh:52)
bash scripts/eval.sh                                             # no new findings; 7/7 git-notes-audit ship checks
bash scripts/lint-skill.sh skills/*/SKILL.md
bash scripts/gen-skill.sh --check
python3 scripts/spec-deps.py validate --specs-dir .writ/specs     # status: ok since 2026-08-12; record the result
git diff --name-only                                             # nothing under scripts/, one file under commands/
```

**Edge cases:**
- The dependency spec is **authored but not implemented** (`spec-deps.py` → `status: ok` as of 2026-08-12). Its eight skills, its `.writ/docs/skills.md` → *Extraction Patterns* section, and its ADR-021 amendments are what this spec must follow — Story 1 gates on those **landed files**, not on the spec folder existing.
- `MAX_SKILLS = 12` (`eval-leanness.py:71`), corpus 6 today. The five authored sibling rosters plus this one name **≥ 29**. No spec in the phase may raise the cap; flag it as unowned (plausible owner: `2026-08-12-governor-enforcement`).
- Verified 2026-08-12: no skill-name collision between this roster and the five sibling rosters. Re-check at authoring time — the namespace is shared and the siblings are moving.
- `eval.sh check_length` still caps commands at 2000 lines; the 400-line figure is a non-binding tripwire owned by `2026-08-11-governor-instrumentation`.
- `.writ/manifest.yaml` + root `SKILL.md` are the conflict surface between Stories 2 and 3, and with the sibling `/release` spec.

**Anti-goal:** clearing 24,960 bytes by deleting the ASCII diagram (1,445 B) and the duplicated dry-run block (1,138 B) while extracting nothing. That passes every byte check and falsifies the contract. The clause ledger and the ≤13,000 B design target are the defenses.
