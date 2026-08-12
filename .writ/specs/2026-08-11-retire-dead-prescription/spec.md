# Spec: Retire Dead Prescription

> **Status:** Complete
> **Owner:** @AdamSellke
> **Created:** 2026-08-11
> **Dependencies:** []
> **Origin:** Phase 10 discovery (`/plan-product`, 2026-08-11). ADR-020 needed a justification for choosing frontmatter as the component-contract carrier and found one by measuring: `system-instructions.md` asserts commands have no frontmatter mechanism "(verified 0/31 files)" — 32/32 command files carry `---` YAML frontmatter today. The measurement that justified ADR-020 also proved Writ's root contract is lying about its own surface. Adjacent audit of the same file found two review triggers (one fired 8 days ago, one due 2026-10-16), a manifest pinned 15 minor versions behind, and a product-decisions file that claims "Override Priority: Highest" while having been superseded by `.writ/decision-records/` since 2026-03-19.

## Contract (Locked)

**Deliverable:** Correct the stale and false claims in Writ's root contract and metadata so the component contract is built on a truthful foundation.

**Must include:** (a) `system-instructions.md` line ~277 — the claim *"Commands (`commands/*.md`) have no frontmatter or config-block mechanism today (verified 0/31 files)"* is **false**; 32/32 command files carry `---` YAML frontmatter with `name` and `description`. The prose-note workaround for advisory `model_tier` is replaced by frontmatter. (b) The `required_skills:` review trigger fired **2026-08-03** (8 days before this spec); its own terms say "deprecate or revisit" — resolved by **adoption**, naming Phase 10 progressive disclosure as its first consumer. (c) `.writ/manifest.yaml` `version: 0.13.1` → `0.28.0`, and its 45 `file:` entries reconciled against the 31 real commands. (d) `.writt/product/decisions.md` formally deprecated in favor of `.writ/decision-records/`. (e) **The `model_tier` reserved negative ordinal offsets (`-1`, `-2`, …) are DEPRECATED NOW**, ahead of their 2026-10-16 trigger — maintainer decision at phase planning. Keep `orchestration` and `capability`; remove the `-[0-9]+` regex branch, the 2-band clamp prose, the "Reserved ordinal offsets are reserve-only" paragraph, and the 2026-10-16 review-trigger blockquote.

**Hardest constraint:** `system-instructions.md` is Writ's root behavioral contract, guarded by the `prime-directive-sync`, `required-sections`, and `manifest` eval checks. Every edit must leave the full suite at `Findings: 0` — this spec cannot buy truth with a red gate.

### Contract reading notes (not amendments)

Two literals in the locked contract do not match the repository as measured. Neither changes the deliverable; both are recorded here so an implementer does not chase a path or a count that does not exist.

- **`.writt/product/decisions.md` (clause d)** is a typo for **`.writ/product/decisions.md`** — 19,753 bytes, 371 lines, last modified 2026-07-09. No `.writt/` directory exists in this repository.
- **"45 `file:` entries" (clause c)** is a raw `grep -c 'file:'` count. Only **44** are data entries — 31 commands, 7 agents, 6 skills. The 45th occurrence is `file: skills/<name>/SKILL.md` inside the YAML comment block documenting the skills schema (`.writ/manifest.yaml` line 225). `.writ/product/roadmap.md` line 343 states the same figure as 44. The reconciliation target is unaffected: 31 manifest command entries against 31 real command files.

## Why This Exists

ADR-020 chose YAML frontmatter as the carrier for the component contract. Its stated reason for rejecting the prose alternative is that the constraint prose was designed around **has since disappeared**: `system-instructions.md` line 277 says commands have "no frontmatter or config-block mechanism today (verified 0/31 files)," and prescribes a bespoke locked prose note as the workaround. That claim is false. All 32 files in `commands/` — 31 commands plus `_preamble.md` — open with `---` frontmatter carrying `name:` and `description:`.

This is not a cosmetic error. Three artifacts prescribe behavior on top of it:

1. `commands/new-command.md` (line 145) instructs every future command author that "Commands have no frontmatter mechanism, so weight intent ships as a prose note" — teaching the workaround forward into files that already have the mechanism.
2. `.writ/docs/model-tiers.md` (line 45) repeats "verified 0/31 files" as the carrier rationale in the user-facing explainer.
3. `scripts/lint-skill.sh` (lines 253–289) carries a second, format-agnostic regex branch that exists only to pattern-match the locked prose note — the exact per-variant fragility ADR-020 cites as prose's cost.

The same audit found three more claims in the same file that have outlived their evidence. `required_skills:` is marked "**Status: reserve-only**" with a review trigger dated **2026-08-03** — fired, unactioned, 8 days before this spec was written. Its own terms say "deprecate or revisit." ADR-021 revisits it: progressive disclosure needs exactly the declarative, harness-resolved, per-invocation load mechanism `required_skills:` already specifies, including its graceful-degradation rule. Deprecating it would mean designing the same thing again under a new name inside the same phase. The correct resolution is adoption, and it must be written down where the reserve-only claim currently lives — not only in an ADR the root contract does not link.

The `model_tier` negative ordinal offsets (`-1`, `-2`, …) have the opposite disposition. They resolve today only as a 2-band clamp: any offset lands on the same floor as `capability`. No adapter has built N-step resolution. No consumer depends on them — grep across `agents/`, `commands/`, `skills/`, and `.writ/manifest.yaml` finds zero declared ordinal values; the only occurrences are the schema definitions themselves. Their review trigger is 2026-10-16, but nothing between now and then will change the answer, and Phase 10 is actively rewriting the schema prose those offsets live inside. Deciding now avoids rewriting the same paragraphs twice.

`.writ/manifest.yaml` says `version: 0.13.1`. `VERSION` says `0.28.0` — fifteen minor releases of drift in the file that `gen-skill.sh` reads as Writ's identity and that `eval.sh check_manifest` validates commands and agents against.

`.writ/product/decisions.md` was soft-deprecated on 2026-03-19 (`2026-03-19-command-suite-evolution`, Story 8): `/plan-product` stopped emitting it, `/create-adr` documents the replacement, and both commands promise existing files are "not modified, migrated, or deleted." The file itself was never told. It still opens with **"Override Priority: Highest — Instructions in this file override conflicting directives in user memories or project settings."** A superseded file asserting the highest override priority in the repository is the single most consequential stale claim in this spec's scope.

## 📋 Business Rules

1. **Every claim that replaces a false one must be measured, not asserted.** "32/32 command files carry `---` frontmatter" is a reproducible count (`for f in commands/*.md; do head -1 "$f"; done`). Replacing one unverified number with another unverified number fails this spec's own premise.
2. **`cursor/writ.mdc` is a full mirror of `system-instructions.md`, not a Prime-Directive-only mirror.** The two files are byte-identical for lines 1–300; `writ.mdc` adds a 10-line "Self-Dogfooding (Writ Repo Only)" appendix and a 3-line Cursor `alwaysApply` frontmatter header. The `prime-directive-sync` eval check diffs **only** the `## Prime Directive` section, so it will not catch drift in the Skills or Model Tiers sections. Mirror parity for every edited line is a manual obligation of each story, not something the gate enforces.
3. **Deprecation removes the prescription, never the history.** ADRs, archived specs, `CHANGELOG.md`, and `.writ/research/` record what was true when written and are never rewritten. Only the **active surface** — `system-instructions.md`, `cursor/writ.mdc`, `commands/`, `adapters/`, `scripts/`, `.writ/docs/`, `.writ/manifest.yaml`, `.writ/product/` — is corrected. This mirrors the existing `forbid_literal` / `forbid_literal_ci` remediation wording in `eval.sh` ("historical ADRs, specs, and `archive/` may keep it").
4. **Every story ends at `Findings: 0`.** `bash scripts/eval.sh` must report `Findings: 0` after each story, not only after the last. A story that leaves the suite red is not done, and no story may add an `eval-exempt:` marker to make its own change pass.
5. **This spec adds no new contract fields.** It corrects claims and removes retired mechanisms. `problem:` / `outcome:` / `exit_criteria:` (ADR-020) and `required_skills:` adoption in real command files (ADR-021) are separate Phase 10 specs. This spec makes the frontmatter carrier *truthfully documented*; it does not populate it.
6. **Ordinal-offset removal is a deprecation decision, not a discovery.** The maintainer decided at phase planning to retire the reservation ahead of its 2026-10-16 trigger. An implementer who finds the offsets technically harmless does not thereby reopen the decision — the rationale is zero consumers plus an unbuilt N-step resolver, and the standing instruction is to challenge with *evidence*, which here would mean producing a real consumer.
7. **`required_skills:` is resolved by adoption in the same edit that removes the reserve-only status.** The reserve-only line and the fired trigger blockquote are replaced together with an adoption statement naming ADR-021 / Phase 10 progressive disclosure as the first consumer. Deleting the trigger without recording the resolution converts a visible overdue signal into an invisible one.
8. **A stale claim inside a historical record is not a defect, and an unclaimed file is not a free file.** Rule 3 says history is preserved; this rule names the two artifacts an implementer is most likely to "helpfully" fix anyway, and the ownership boundary that governs the rest. `.writ/decision-records/adr-016-model-tier-delegation.md:76` ("commands have no frontmatter or config-block mechanism at all (verified 0/31 command files)") and `CHANGELOG.md:143` ("`/new-command` documents an advisory `model_tier` prose note (commands have no frontmatter mechanism)") both describe the repository accurately as of 2026-07-10. Neither is edited by any story. Separately, every file this spec touches has exactly one owning story, and a file owned by a sibling Phase 10 spec is not claimed here even when it carries the same literal — the fix for a cross-spec divergence is a recorded finding, never a cross-spec edit.

## Detailed Requirements

### (a) The false frontmatter claim, and the carrier it justified

**`system-instructions.md` line 277** (mirrored at `cursor/writ.mdc` line 277) currently reads:

> - **Commands** (`commands/*.md`) have no frontmatter or config-block mechanism today (verified 0/31 files). Advisory tier ships as a prose note:

Replace with the measured truth — commands carry `---` YAML frontmatter in 32/32 files (31 commands + `_preamble.md`), each with `name:` and `description:` — and make advisory `model_tier` a frontmatter field on the same footing as skills, retiring the prose note as the prescribed carrier.

Downstream artifacts prescribing the retired workaround, all in scope:

| File | Location | What it says today |
|---|---|---|
| `commands/new-command.md` | lines 145–151 | "Commands have no frontmatter mechanism, so weight intent ships as a prose note … verbatim in the already-locked phrasing" |
| `commands/new-command.md` | line 171 | Generated-command checklist item requiring the prose note near Overview/Invocation |
| `.writ/docs/model-tiers.md` | line 45 | Carrier table row: "Prose note near Overview/Invocation — commands carry no frontmatter mechanism (verified 0/31 files)" |
| `.writ/docs/model-tiers.md` | line 95 | "`/new-command` emits the locked prose note …" |
| `.writ/docs/model-tiers.md` | line 97 | Describes `lint-skill.sh` validating "a command's prose note" |
| `scripts/lint-skill.sh` | lines 253–283 | Second regex branch matching `**Model tier (advisory only):** <value>`, plus the comment block documenting it |

The only two live occurrences of the locked prose string are both inside `commands/new-command.md` (the template at line 148 and the checklist at line 171) — no shipped command carries the note, so retiring the carrier orphans no existing file.

### (b) `required_skills:` — resolved by adoption

**`system-instructions.md` lines 252 and 254** (mirrored in `cursor/writ.mdc`):

> **Status: reserve-only.** As of the foundation spec (`2026-05-03-skills-foundation`), this convention is documented but *not adopted by any existing agent or command*. …
>
> > **Review trigger: 2026-08-03** (90 days post-ship). If no agent or command has adopted `required_skills:` by this date, deprecate or revisit the convention. Date matches ADR-009's review discipline.

Replace both with an adoption statement: the trigger fired 2026-08-03 and is resolved by **revisit → adopt**, with ADR-021's progressive disclosure named as the first consumer. The schema above it (optional array, order preserved, duplicates deduplicated, unknown names warn) is unchanged — the convention is adopted as specified, not redesigned.

Same claim, same treatment, in three further active-surface locations:

| File | Location |
|---|---|
| `.writ/docs/skills.md` | lines 136 (`**Status: reserve-only.**`) and 138 (the 2026-08-03 trigger blockquote) |
| `adapters/cursor.md` | line 218 — "reserve-only in the foundation spec; pilot skills will adopt it as they ship" |
| `adapters/claude-code.md` | line 396 — same sentence |
| `adapters/openclaw.md` | line 278 — same sentence |

### (c) `.writ/manifest.yaml` reconciliation

- `metadata.version: 0.13.1` → `0.28.0`, matching the `VERSION` file (confirmed: `VERSION` contains `0.28.0`).
- Reconcile the data `file:` entries against disk: **31** under `commands:`, **7** under `agents:`, **6** under `skills:` = 44. (See Contract reading notes for why the raw grep says 45.)
- `eval.sh check_manifest` already enforces both directions of command/agent parity — every manifest `file:` must exist, and every non-`_`-prefixed file in `commands/` and root `agents/` must be listed. It passes today; the reconciliation must record that parity as verified rather than assume it, and must leave the check passing.
- `scripts/gen-skill.sh --check` (exit 0 today) must still exit 0. `SKILL.md` does not render `metadata.version`, so the bump is not expected to make the generated catalog stale — verify rather than assume.

### (d) `.writ/product/decisions.md` formally deprecated

The file carries DEC-001 through DEC-008 (2026-02-27 → 2026-03-22) and opens with:

```
> Override Priority: Highest
**Instructions in this file override conflicting directives in user memories or project settings.**
```

Add a deprecation header that: states the file is superseded by `.writ/decision-records/`, dates the supersession to `2026-03-19-command-suite-evolution` (Story 8), neutralizes the highest-override-priority assertion, and states the file is retained as a historical record of DEC-001–DEC-008 with no migration to ADRs required.

The user-facing soft-deprecation contract in `commands/plan-product.md` (line 345) and `commands/create-adr.md` (line 170) — "existing `.writ/product/decisions.md` files are **not** modified, migrated, or deleted" — is a promise about **other people's projects** and stays exactly as written. This repository's own `.writ/product/decisions.md` is a development-workspace artifact, not a user file, and annotating it does not weaken that promise.

### (e) `model_tier` negative ordinal offsets — deprecated now

Remove four constructs from `system-instructions.md` (and the `cursor/writ.mdc` mirror):

| Location | Construct |
|---|---|
| line 285 | Allowed-values schema: the `-[0-9]+` branch of `^(orchestration\|capability\|-[0-9]+)$`, and "or a reserved negative ordinal offset (`-N`)" |
| line 295 | Behavior-table row: "Reserved ordinal offset beyond available bands \| Clamp to floor …" |
| line 298 | The "**Reserved ordinal offsets (`-1`, `-2`, ...) are reserve-only.**" paragraph and its 2-band clamp prose |
| line 300 | The `> **Review trigger: 2026-10-16**` blockquote |

`orchestration` and `capability` stay. The enforcement boundary (agents enforced at spawn; commands and skills advisory), the precedence rule (`model:` beats `model_tier:`), and the graceful-degradation contract (unknown value warns, falls back to inherit) are all unchanged — an ordinal value declared after this change is simply an unknown value, which the existing degradation row already covers.

Matching removals on the active surface:

| File | Location |
|---|---|
| `scripts/lint-skill.sh` | line 285 — `^(orchestration\|capability\|-[0-9]+)$`; line 286 error text; lines 26–27 usage text |
| `.writ/docs/model-tiers.md` | line 75 (clamp table row), line 82 (ordinal paragraph), line 86 (2026-10-16 trigger), line 103 (schema restatement) |
| `.writ/manifest.yaml` | line 227 — skills schema comment `model_tier: <orchestration\|capability\|-N>` |

`scripts/eval-skill-lifecycle.py` contains no `model_tier` fixture, so the eval `skill-lifecycle` check is not expected to move. Verify rather than assume.

### (f) Approved scope addition, 2026-08-11 — the explainer and the lint

> This clause is **not** part of the `## Contract (Locked)` block above, which remains verbatim as agreed. It is a maintainer-approved addition made on 2026-08-11, after the package was written, and it is delivered by **Story 6**. Clauses (a)–(e) are unchanged.

Clause (a) names `system-instructions.md` line ~277 as the home of the false *"no frontmatter mechanism (verified 0/31 files)"* claim and states that "the prose-note workaround for advisory `model_tier` is replaced by frontmatter." Two further **live prescribing artifacts** carry that same claim and its downstream workaround. Both already appear in clause (a)'s downstream table, but neither was assigned an owning story:

| File | Location | What it says today (verified 2026-08-11) |
|---|---|---|
| `.writ/docs/model-tiers.md` | line 45 | Carrier table's Command row: *"Prose note near Overview/Invocation — commands carry no frontmatter mechanism (verified 0/31 files)"*, with a prose-note example |
| `.writ/docs/model-tiers.md` | line 95 | *"`/new-command` emits the locked prose note …"* |
| `.writ/docs/model-tiers.md` | line 97 | *"`scripts/lint-skill.sh` validates any declared `model_tier` value — in skill frontmatter, an agent's Agent Configuration block, or **a command's prose note**"* |
| `scripts/lint-skill.sh` | lines 279–280 | The `elif` branch of `lint_model_tier()` matching `**Model tier (advisory only):** <value>`, plus its documentation at lines 254 and 260–262 and the `usage()` sentence at line 27 |

**Required outcome.** Line 45 states the measured carrier: `---` YAML frontmatter, present in 32/32 files in `commands/` (31 commands + `_preamble.md`), with an example in the same shape as the Skill row. Lines 95 and 97 are each verified against the artifact they describe before being rewritten — line 95 describes `commands/new-command.md`, which this spec does not own (see below), so a divergence there is recorded, not papered over. The `lint-skill.sh` branch is **removed, not retargeted**: `lint_model_tier()`'s first branch (`line 277`) is an unanchored `model_tier:[[:space:]]*([A-Za-z0-9-]+)` match applied to every raw line of the file, so a command's frontmatter field is already captured by it and there is no second frontmatter shape to retarget to.

**`lint-skill.sh` is load-bearing for a currently-passing eval check.** `check_skill_lifecycle()` (`scripts/eval.sh:2476`) drives fixtures through the script and asserts four literals inside it — `candidate|proven|promoted`, `State is EARNED from evidence`, `Lifecycle-unearned`, `Lifecycle-evidence` — all of which live in `lint_lifecycle()`, not `lint_model_tier()`. `scripts/eval-skill-lifecycle.py` contains no `model_tier` line at all. The full suite must still report `Findings: 0` and the `skill-lifecycle` check must still report PASS; Story 6 proves both rather than assuming them.

**Ownership boundaries this clause does not cross:**

- **`commands/new-command.md:145` belongs to the sibling spec `2026-08-11-component-contract` (its Story 1).** Story 6 does not claim it. Note that this spec's own Story 1 (Task 1.4) currently also claims it, and the two specs want opposite outcomes for the prose note — see `user-stories/README.md` → "Open conflict".
- **`system-instructions.md:277` belongs to this spec's Story 1**, per clause (a).
- **`.writ/decision-records/adr-016-model-tier-delegation.md:76` and `CHANGELOG.md:143` are historical records and are edited by no story** (Business Rules 3 and 8).

### Verification bar (every story)

- `bash scripts/eval.sh` → `Findings: 0`
- `bash scripts/gen-skill.sh --check` → exit 0
- For any story touching `system-instructions.md`: `diff <(sed -n '1,300p' cursor/writ.mdc | tail -n +4) …` or an equivalent line-for-line comparison confirming the edited passages are identical in both files

## Out of Scope

- **Populating `problem:` / `outcome:` / `exit_criteria:` in command frontmatter.** ADR-020's migration pass across 31 commands and 7 agents is a separate Phase 10 spec. This spec makes the carrier truthfully documented; it does not author contracts.
- **Declaring `required_skills:` in any real command or agent file.** The first *actual* declaration lands with ADR-021's progressive-disclosure extraction. This spec resolves the convention's status, not its consumption.
- **Extracting procedural detail into skills, or changing `check_length`'s 2000-line command limit.** ADR-021 and the "Make the governor bite" roadmap item own those.
- **Rewriting ADR-016.** The ordinal-offset reservation originates there. ADRs record what was decided when it was decided (Business Rule 3); a superseding decision is recorded forward, not retrofitted. Whether the ordinal deprecation warrants its own ADR or rides on ADR-021 is a maintainer call outside this spec's file set.
- **Migrating DEC-001–DEC-008 into numbered ADRs.** The 2026-03-19 deprecation was explicitly unscripted and optional. This spec adds a header; it does not convert eight decisions.
- **Changing the user-facing soft-deprecation promise** in `commands/plan-product.md` or `commands/create-adr.md` about other projects' `decisions.md` files.
- **Historical artifacts.** `CHANGELOG.md`, `.writ/decision-records/`, `.writ/specs/archive/`, and `.writ/research/` keep every claim they recorded, including `.writ/research/2026-08-03-writ-vs-openspec-analysis.md`'s references to the 2026-10-16 trigger and `.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md`'s "Writ (v0.13.1)" heading.
- **Any new eval check.** This spec must keep the existing suite green; adding structural checks belongs to "Make the governor bite."
