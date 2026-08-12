# Technical Spec: Retire Dead Prescription

> Source: `.writ/specs/2026-08-11-retire-dead-prescription/spec.md`

All measurements below were taken against `writ/phase/10` on 2026-08-11 with a clean baseline of `bash scripts/eval.sh` → `Findings: 0` (report: `.writ/state/eval-20260811-200730.md`). Line numbers are as-measured and will shift as stories land — later stories must re-locate by literal, not by line.

## The mirror constraint (applies to Stories 1, 2, 3)

`cursor/writ.mdc` is not a partial mirror. Measured:

```
$ diff system-instructions.md cursor/writ.mdc
300a301,310
> ## Self-Dogfooding (Writ Repo Only)   ← plus 9 more lines
```

`system-instructions.md` is 300 lines; `cursor/writ.mdc` is 310 and additionally carries a 3-line Cursor `---\nalwaysApply: true\n---` header (which is why its body still aligns 1:1 by content, not by absolute line index — the `.mdc` header is counted in its 310). Every line of `system-instructions.md` appears verbatim in `writ.mdc`, and `writ.mdc` appends the Writ-repo-only dogfooding section.

`check_prime_directive_sync()` (`scripts/eval.sh:302`) extracts **only** the `## Prime Directive` section from each file via awk and diffs those two extracts. Sections `## Skills` and `## Model Tiers` — the entirety of this spec's edit surface in these two files — are **outside** what the gate compares.

**Consequence:** a story can edit `system-instructions.md`, skip `cursor/writ.mdc`, and still see `Findings: 0`. The mirror is a manual obligation with no automated backstop. Each of Stories 1–3 must run an explicit content diff of the edited passages as a task, not rely on the suite.

## (a) The false frontmatter claim — Story 1

### Measured ground truth

```
$ ls commands/*.md | wc -l
32
$ for f in commands/*.md; do head -1 "$f" | grep -q '^---$' || echo "NO $f"; done
(no output — zero files without frontmatter)
```

32/32. The set is 31 commands + `commands/_preamble.md` (excluded from `check_manifest`'s parity scan by the `_*.md` prefix rule at `scripts/eval.sh:490`). Sample:

```yaml
---
name: status
description: "Orient in under 10 seconds: config, active spec, in-flight batch work, and what to do next."
---
```

### Current text (`system-instructions.md:273-282`, mirrored in `cursor/writ.mdc`)

```markdown
**Carrier per file type** ("frontmatter" is the umbrella term — the literal carrier differs by file type):

- **Skills** (`skills/*/SKILL.md`) carry `model_tier` in real `---` YAML frontmatter, advisory only.
- **Agents** (`agents/*.md`) carry `model_tier` in their existing fenced **Agent Configuration** block — not a new `---` header. …
- **Commands** (`commands/*.md`) have no frontmatter or config-block mechanism today (verified 0/31 files). Advisory tier ships as a prose note:

  ```markdown
  > **Model tier (advisory only):** orchestration — commands run at the user's session model.
  ```
```

The Skills and Agents bullets are accurate and stay. Only the Commands bullet and its fenced prose-note example are replaced — commands carry `model_tier` in the same `---` YAML frontmatter that already holds `name:` and `description:`, advisory only.

### The lint branch this orphans

`scripts/lint-skill.sh:268-289` recognizes two shapes:

```bash
if [[ "$line" =~ model_tier:[[:space:]]*([A-Za-z0-9-]+) ]]; then
  value="${BASH_REMATCH[1]}"
elif [[ "$line" =~ Model[[:space:]]tier[[:space:]]\(advisory[[:space:]]only\):\*{0,2}[[:space:]]*([A-Za-z0-9-]+) ]]; then
  value="${BASH_REMATCH[1]}"
```

The first branch already handles frontmatter. The second exists solely for the prose note — the bespoke per-variant regex ADR-020 names as prose's cost. **Story 6 owns its removal** (transferred out of Story 1 on 2026-08-11); Story 1 no longer decides its disposition. See "(f) Explainer and lint carrier retirement — Story 6" below for the measured edit surface and the reason removal beats retargeting.

### Downstream files (exact literals to relocate)

| File:line | Literal | Owning story |
|---|---|---|
| `commands/new-command.md:145` | `Commands have no frontmatter mechanism, so weight intent ships as a prose note` | 1 (contested — see below) |
| `commands/new-command.md:148` | `> **Model tier (advisory only):** <tier> — commands run at the user's session model, not Writ-selectable.` | 1 (contested) |
| `commands/new-command.md:171` | checklist bullet requiring that note near Overview/Invocation | 1 (contested) |
| `.writ/docs/model-tiers.md:45` | `commands carry no frontmatter mechanism (verified 0/31 files)` | **6** |
| `.writ/docs/model-tiers.md:95` | `**/new-command** emits the locked prose note …` | **6** |
| `.writ/docs/model-tiers.md:97` | `… or a command's prose note …` | **6** |

`grep -rn -F "Model tier (advisory only)" commands/ agents/ skills/ .writ/docs/ scripts/ system-instructions.md cursor/` returns **6 live hits**: `commands/new-command.md:148` and `:171`, `.writ/docs/model-tiers.md:45` and `:95`, `scripts/lint-skill.sh:260`, `system-instructions.md:280`. Use `-F` — without it, `grep` treats the parentheses inconsistently and silently under-reports. No *shipped* command carries the note (the two `new-command.md` hits are template and checklist text), so retiring the carrier orphans nothing.

**Contested ownership of `commands/new-command.md`.** The sibling Phase 10 spec `2026-08-11-component-contract` claims the same three lines in its own Story 1 (Task 1.6) and its `spec.md:122` states the prose-note *format* "stays locked" because "`lint-skill.sh` and `.writ/docs/model-tiers.md` depend on it, and moving `model_tier` into frontmatter is not this spec's decision." That spec declares this one as its dependency, so it lands second. Two specs, one file, opposite outcomes — a maintainer ruling is required before either Story 1 starts. Story 6's Task 6.3 is written so that whichever way the ruling goes, `.writ/docs/model-tiers.md:95` describes what `new-command.md` actually does at implementation time.

### Anti-sycophancy interaction

`check_anti_sycophancy()` scans `commands/*.md`, `agents/*.md`, `system-instructions.md`, and `cursor/writ.mdc` against `.writ/eval/anti-sycophancy-phrases.txt`. New prose in any of these files is subject to it. Write plainly; state the count and move on.

## (e) Ordinal-offset deprecation — Story 2

### Zero consumers (measured)

`grep -rn "model_tier" agents/*.md skills/*/SKILL.md .writ/manifest.yaml` returns only `orchestration` and `capability` values across all 7 agents and the manifest. No file anywhere in `commands/`, `agents/`, `skills/`, or `.writ/manifest.yaml` declares a negative ordinal. The only `-[0-9]+` occurrences are the schema definitions themselves.

### Removal set

| File:line | Construct |
|---|---|
| `system-instructions.md:285` | `regex ^(orchestration\|capability\|-[0-9]+)$` + "or a reserved negative ordinal offset (`-N`)" |
| `system-instructions.md:295` | table row `\| Reserved ordinal offset beyond available bands \| Clamp to floor …` |
| `system-instructions.md:298` | `**Reserved ordinal offsets (-1, -2, ...) are reserve-only.**` paragraph |
| `system-instructions.md:300` | `> **Review trigger: 2026-10-16** …` blockquote |
| `cursor/writ.mdc` | all four, mirrored |
| `scripts/lint-skill.sh:285` | `^(orchestration\|capability\|-[0-9]+)$` → `^(orchestration\|capability)$` |
| `scripts/lint-skill.sh:286` | error text "…or a reserved negative offset (e.g. -1)." |
| `scripts/lint-skill.sh:26-27` | usage text naming the reserved offset (ordinal half only — the "command prose note" clause on line 27 is Story 6's) |
| `scripts/lint-skill.sh:253-265` | comment block describing the two shapes (ordinal half only — the prose-note half is Story 6's) |
| `.writ/docs/model-tiers.md:75` | clamp table row |
| `.writ/docs/model-tiers.md:82` | negative-ordinal-form paragraph |
| `.writ/docs/model-tiers.md:86` | 2026-10-16 review trigger |
| `.writ/docs/model-tiers.md:97` | allow-list inside the lint-validation sentence — narrow the regex only; the "or a command's prose note" clause on the same line is Story 6's |
| `.writ/docs/model-tiers.md:103` | schema restatement `^(orchestration\|capability\|-[0-9]+)$` |
| `.writ/manifest.yaml:227` | schema comment `model_tier: <orchestration\|capability\|-N>  # optional, advisory only` |

### What survives

The graceful-degradation row (`system-instructions.md:294`) already covers what happens to a value that is no longer allowed: *"`model_tier` value unrecognized at resolution time → warn … fall back to parent model."* A post-deprecation `-1` is simply unrecognized. No new failure path is introduced, and no adapter table changes — `adapters/{cursor,claude-code,codex,openclaw}.md` map `orchestration`/`capability` only and never mention ordinals.

`scripts/eval-skill-lifecycle.py` builds its fixtures from `status:`/`evidence:` frontmatter and contains **no `model_tier` line**, so the `skill-lifecycle` eval check has no ordinal fixture to break. Verify with a full suite run rather than assuming.

### Regression risk

`lint-skill.sh` is invoked by `eval.sh check_skill_lifecycle` against generated fixtures and by `/new-skill` / `/refresh-command` at authoring time. Narrowing the grammar can only turn previously-passing values into failures, and no such value exists in the repo. Exercise all three cases (`orchestration` pass, `capability` pass, `-1` reject) before closing.

## (b) `required_skills:` adoption — Story 3

### Current text (`system-instructions.md:252-254`)

```markdown
**Status: reserve-only.** As of the foundation spec (`2026-05-03-skills-foundation`), this convention is documented but *not adopted by any existing agent or command*. Adoption happens organically during pilot skill extraction (separate specs). Defining the schema now prevents pilot specs from inventing competing conventions.

> **Review trigger: 2026-08-03** (90 days post-ship). If no agent or command has adopted `required_skills:` by this date, deprecate or revisit the convention. Date matches ADR-009's review discipline.
```

The trigger fired 8 days before this spec. Its terms offer two outcomes; ADR-021 § "Why `required_skills:` gets adopted instead of deprecated" (line 54) selects revisit-and-adopt, with the reasoning that progressive disclosure needs exactly the contract `required_skills:` already specifies — including its graceful-degradation rule — and deprecating it would mean redesigning the same mechanism under a new name inside the same phase.

### Required replacement content

The replacement must carry all four facts, or the resolution is not auditable: (1) the trigger fired on 2026-08-03; (2) the outcome is **revisit → adopt**, not deprecate; (3) the first consumer is ADR-021 progressive disclosure, Phase 10; (4) the schema above is adopted **unchanged** (optional array, order preserved, duplicates deduplicated, unknown names warn rather than hard-fail).

Deleting the trigger blockquote without recording the resolution turns a visible overdue signal into an invisible one — the failure mode ADR-020 names for the four ignored leanness warnings.

### Parallel locations

`.writ/docs/skills.md:136` (`**Status: reserve-only.**`) and `:138` (trigger blockquote) carry the same claim in the user-facing explainer. `adapters/cursor.md:218`, `adapters/claude-code.md:396`, and `adapters/openclaw.md:278` each end their Skills → Invocation paragraph with the identical sentence: *"`required_skills:` is reserve-only in the foundation spec; pilot skills will adopt it as they ship."* The three adapter sentences are byte-identical to each other; treat them as one edit applied three times.

`commands/new-skill.md:242` and `skills/gbrain-interop/SKILL.md:155` reference `required_skills:` as the promotion criterion under ADR-014's lifecycle ladder. Those are accurate today and stay — adoption does not change the promotion bar.

## (c) Manifest reconciliation — Story 4

### Structure (measured)

| Section | Start line | Data `file:` entries |
|---|---|---|
| `metadata:` | 2 | 0 (`runtime_contract:`, not `file:`) |
| `categories:` | 8 | 0 |
| `commands:` | 28 | **31** |
| `agents:` | 185 | **7** |
| (skills schema comment block) | ~219–244 | 1 non-data occurrence at line 225 |
| `skills:` | 245 | **6** |

`grep -c "file:"` = 45; data entries = 44. The 45th is `#     file: skills/<name>/SKILL.md     # required, must exist on disk` inside the schema documentation comment. `.writ/product/roadmap.md:343` states 44.

### What `check_manifest` already enforces (`scripts/eval.sh:454-521`)

1. `bash scripts/gen-skill.sh --dry-run` parses the manifest without error.
2. Every `file:` under `commands:` and `agents:` exists on disk.
3. Every `commands/*.md` not matching `_*.md` appears in the manifest.
4. Every root `agents/*.md` appears in the manifest.

All four pass today. Parity is therefore already correct — the reconciliation deliverable is **verification recorded as evidence**, plus the version bump. Do not invent drift that the gate would have caught.

### Version bump

`.writ/manifest.yaml:4` → `version: 0.28.0`. `VERSION` contains `0.28.0` (confirmed). `gen-skill.sh` reads `metadata.version` into `METADATA_VERSION` (line 127 / fallback parser line 314) and validates it is non-empty (line 424). Measured: the generated `SKILL.md` does not render the version string, and `bash scripts/gen-skill.sh --check` exits 0 today — re-run after the bump to confirm it still does.

The stale `0.13.1` also appears in `.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md` (lines 37, 175) as a point-in-time comparison heading. Historical; out of scope per Business Rule 3.

## (d) `decisions.md` deprecation — Story 5

### Current head (lines 1–6)

```markdown
# Writ — Product Decisions Log

> Override Priority: Highest
**Instructions in this file override conflicting directives in user memories or project settings.**

---
```

371 lines, 19,753 bytes, last modified 2026-07-09. Contains DEC-001 … DEC-008 (2026-02-27 → 2026-03-22).

### What supersedes it

`2026-03-19-command-suite-evolution` Story 8 moved foundational product decisions to numbered ADRs in `.writ/decision-records/`. `CHANGELOG.md:442` records the change. The deprecation was deliberately **soft** — the spec's own scope boundary says *"Existing `decisions.md` files are not migrated … No migration story for old files."*

Nothing was added to the file itself, so it still asserts highest override priority over user memories and project settings while having been superseded for nearly five months.

### The header must

- Mark the file **deprecated**, superseded by `.writ/decision-records/`, dated to `2026-03-19-command-suite-evolution` (Story 8).
- Neutralize the "Override Priority: Highest" assertion — a deprecated file cannot claim precedence over active directives.
- State the file is retained as the historical record of DEC-001–DEC-008, with no migration to ADRs required or planned.

### The promise that must survive

`commands/plan-product.md:345` and `commands/create-adr.md:170` both tell **users** their existing `.writ/product/decisions.md` is "**not** modified, migrated, or deleted." That is a contract about other people's repositories. This repository's copy is a development-workspace artifact under `.writ/` (per `CLAUDE.md`'s three-concern split), not product source. Annotating it changes nothing about what `/plan-product` or `/create-adr` do to a user's project, and neither command file is edited by this story.

## (f) Explainer and lint carrier retirement — Story 6

> Approved scope addition, 2026-08-11. Not part of the locked contract's clauses (a)–(e); the Contract block is unchanged. See `spec.md` → Detailed Requirements → "(f)".

### Measured edit surface — `.writ/docs/model-tiers.md` (117 lines)

| Line | Current text | Required change |
|---|---|---|
| 45 | Carrier table, Command row: `Prose note near Overview/Invocation — commands carry no frontmatter mechanism (verified 0/31 files)`; Example column holds `> **Model tier (advisory only):** orchestration — commands run at the user's session model, not Writ-selectable.` | Carrier becomes the existing `---` YAML frontmatter (32/32 files in `commands/`); Example becomes `model_tier: orchestration   # advisory only`, matching the Skill row at line 43 |
| 95 | `**/new-command** emits the locked prose note … near the generated command's Overview/Invocation section` | Describe what `commands/new-command.md` actually does at implementation time. That file is sibling-owned; verify before rewriting |
| 97 | `… validates any declared model_tier value — in skill frontmatter, an agent's Agent Configuration block, or a command's prose note — against the shared allow-list (^(orchestration\|capability\|-[0-9]+)$)` | Drop `or a command's prose note`; name command **frontmatter** instead. Story 2 will already have narrowed the allow-list on this line |

Lines 43–44 (Skill and Agent rows) and line 47 (the umbrella-term sentence) are accurate and stay. **No eval check reads this file** — `grep -n "model-tiers" scripts/eval.sh scripts/*.py` returns nothing — so the acceptance criteria, not the gate, are the verification.

### Measured edit surface — `scripts/lint-skill.sh`

```bash
277    if [[ "$line" =~ model_tier:[[:space:]]*([A-Za-z0-9-]+) ]]; then
278      value="${BASH_REMATCH[1]}"
279    elif [[ "$line" =~ Model[[:space:]]tier[[:space:]]\(advisory[[:space:]]only\):\*{0,2}[[:space:]]*([A-Za-z0-9-]+) ]]; then
280      value="${BASH_REMATCH[1]}"
281    else
282      continue
283    fi
```

**Remove lines 279–280. Do not retarget them.** `lint_model_tier()` (lines 268–290) loops over every raw line of the file — its own comment at 255–257 says it "is format-agnostic and scans the ENTIRE raw file (unlike `extract_frontmatter`, which is fence-gated)". Line 277's regex is unanchored, so `model_tier: capability` in a command's `---` frontmatter is already captured by branch 1. There is no second frontmatter shape for the `elif` to be retargeted to; retargeting would duplicate branch 1. Lines 281–283 (`else` / `continue` / `fi`) stay.

Supporting prose in the same file, also Story 6's:

| Line | Text |
|---|---|
| 27 | `usage()`: `or command prose note) must be 'orchestration', 'capability', or a` — remove the prose-note clause (Story 2 removes the ordinal clause on the same line) |
| 254 | Comment: `Advisory (skills, command prose notes) and enforced (agent config blocks)` |
| 257–262 | Comment: `it recognizes two shapes:` … `2. Locked prose: **Model tier (advisory only):** <value>` — collapse to one recognized shape |

### The eval check this touches

`check_skill_lifecycle()` (`scripts/eval.sh:2476`) is **PASSING today** and must remain so. It does two things with `lint-skill.sh`:

1. Runs `python3 scripts/eval-skill-lifecycle.py`, which generates fixtures and drives them through the lint, emitting `PASS`/`FAIL` scenario rows. Measured: `grep -n "model_tier\|Model tier" scripts/eval-skill-lifecycle.py` returns **zero lines** — there is no `model_tier` fixture of any shape.
2. Asserts four literals are present in `scripts/lint-skill.sh` via `require_literal`: `candidate|proven|promoted`, `State is EARNED from evidence`, `Lifecycle-unearned`, `Lifecycle-evidence`. All four are inside `lint_lifecycle()` (lines ~180–251), none inside `lint_model_tier()`.

The removal therefore has no mechanical path to the check. Story 6 proves it anyway: `bash scripts/eval.sh --check=skill-lifecycle` → PASS, plus the full suite at `Findings: 0`.

### What the removal gives up

After this story no lint validates a `> **Model tier (advisory only):** <value>` note. If the sibling spec keeps `commands/new-command.md` emitting that note, `/new-command` will scaffold an unvalidated string. Measured today: zero shipped commands carry the note, so nothing currently validated stops being validated. This is an accepted consequence recorded by Task 6.6, not an oversight — the alternative is keeping a bespoke per-variant regex alive for a carrier the root contract has retired, which is the exact cost ADR-020 cites against prose.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Edit `system-instructions.md` | `cursor/writ.mdc` not mirrored; suite stays green because `prime-directive-sync` only diffs the Prime Directive | Explicit per-story diff task comparing every edited passage across both files | Deliberately edit one file only in a scratch copy; confirm the suite passes; confirm the manual diff catches it |
| Narrow `lint-skill.sh` model_tier grammar | A fixture or real file declares an ordinal → lint fails | Zero such values exist (measured). If one appears, it is a genuine consumer and Business Rule 6 requires surfacing it, not silently re-widening the regex | Run `lint-skill.sh` over all 6 skills, all 7 agents, and a synthetic `-1` case |
| Bump `metadata.version` | Generated `SKILL.md` goes stale → `gen-skill.sh --check` non-zero | `SKILL.md` does not render the version (measured); if `--check` fails, regenerate rather than reverting the bump | `bash scripts/gen-skill.sh --check` before and after |
| Remove a literal from the active surface | Over-broad `sed`/global replace also rewrites `.writ/decision-records/`, `.writ/specs/archive/`, `.writ/research/`, `CHANGELOG.md` | Scope every replacement to named files; never run a repo-wide substitution | Per-story grep of the historical surface confirming its hit count is unchanged |
| Annotate `.writ/product/decisions.md` | Reads as a change to the user-facing soft-deprecation promise | Header states the file is retained; `plan-product.md` and `create-adr.md` are untouched | Diff confirms zero changes to either command file |
| Any story | Suite red at close | Story is not done. No `eval-exempt:` marker may be added to make the story's own change pass (Business Rule 4) | `bash scripts/eval.sh` → `Findings: 0`, recorded per story |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Literal removal + mirror | Literal gone from active surface, both mirrors identical, suite green | Story with no code change (docs-only) still runs the full suite | Grep finds the literal already absent (a prior story removed it) → record and move on, do not re-add context to justify the task | Suite red → diagnose before proceeding; never exempt |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Stories 1, 2, 3 all edit `system-instructions.md` § Skills / § Model Tiers and `cursor/writ.mdc` | Serialize 1 → 2 → 3. Parallel execution would conflict in both files and double the mirror-drift risk |
| Line numbers shift as stories land | Later stories locate edits by literal string, never by the line numbers recorded here |
| Stories 2 and 6 both edit `lint_model_tier()`, its `usage()` text, and `.writ/docs/model-tiers.md:97` | Story 6 depends on Story 2 and runs after it. Story 2 touches the ordinal half only and leaves the `elif` at 279–280 in place; Story 6 then removes it. Story 6 locates by literal, never by the line numbers above |
| Stories 3 and 6 both become runnable when Story 2 lands | Their file sets are disjoint (Story 3: `system-instructions.md` § Skills, `cursor/writ.mdc`, `.writ/docs/skills.md`, `adapters/`; Story 6: `.writ/docs/model-tiers.md`, `scripts/lint-skill.sh`). Run them in parallel |
| `commands/new-command.md` is claimed by both this spec's Story 1 and `2026-08-11-component-contract`'s Story 1, with opposite intent | Not resolvable inside this spec. Recorded in `user-stories/README.md` → "Open conflict" and escalated for a maintainer ruling. Story 6 measures the file's actual state instead of assuming either outcome |
| A future command declares `model_tier: -1` after deprecation | Existing unrecognized-value degradation applies: warn, fall back to inherit. No new failure path |
| `.writ/research/*` mentions the retired triggers and `v0.13.1` | Out of scope — research records a point in time (Business Rule 3) |

## Testing Strategy

- **Story 1:** frontmatter count reproduced (`32`); zero hits for `verified 0/31 files` and `no frontmatter mechanism` in `system-instructions.md`, `cursor/writ.mdc`, and `commands/new-command.md`; mirror diff; full suite. `.writ/docs/model-tiers.md` and `scripts/lint-skill.sh` are Story 6's and are not cleared here.
- **Story 2:** zero active-surface hits for `-[0-9]+`-bearing schemas, the clamp row, the reserve-only paragraph, and `2026-10-16`; `lint-skill.sh` exercised for `orchestration` / `capability` / rejected `-1`; mirror diff; full suite.
- **Story 3:** zero active-surface hits for `reserve-only` and `2026-08-03`; replacement text carries all four required facts; mirror diff; full suite.
- **Story 4:** `metadata.version` equals `VERSION`; 31/7/6 entry counts confirmed against disk; `gen-skill.sh --check` exit 0; `eval.sh --check=manifest` PASS; full suite.
- **Story 5:** deprecation header present; "Override Priority: Highest" no longer asserted as live; DEC-001–DEC-008 bodies byte-unchanged; `commands/plan-product.md` and `commands/create-adr.md` unchanged; full suite.
- **Story 6:** zero hits for `verified 0/31 files`, `no frontmatter mechanism`, and (via `grep -F`) `Model tier (advisory only)` in `.writ/docs/model-tiers.md` and `scripts/lint-skill.sh`; `lint-skill.sh` still captures and validates `model_tier:` in all 6 skills and all 7 agents; a synthetic prose note with a bogus value produces no finding while a synthetic `model_tier: bogus` still does; `bash scripts/eval.sh --check=skill-lifecycle` PASS; `git diff` proves `adr-016-model-tier-delegation.md`, `CHANGELOG.md`, and `commands/new-command.md` unchanged; full suite.
- **Every story:** `bash scripts/eval.sh` → `Findings: 0`, plus a historical-surface grep confirming ADRs, `CHANGELOG.md`, `.writ/specs/archive/`, and `.writ/research/` retained their original hit counts.

## Non-Goals (restated from spec.md Out of Scope)

No population of `problem:` / `outcome:` / `exit_criteria:`. No real `required_skills:` declarations in command or agent files. No skill extraction, no `check_length` limit change, no new eval check. No rewrite of ADR-016. No migration of DEC-001–DEC-008 into ADRs. No change to the user-facing soft-deprecation promise. No edits to `CHANGELOG.md`, `.writ/decision-records/`, `.writ/specs/archive/`, or `.writ/research/`.
