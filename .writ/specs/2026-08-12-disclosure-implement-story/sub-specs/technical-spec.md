# Technical Spec: Progressive Disclosure — `implement-story`

> Parent: [spec.md](../spec.md) · Governing decision: [ADR-021](../../../decision-records/adr-021-progressive-disclosure-token-budget.md) · Boundary: [ADR-009](../../../decision-records/adr-009-command-agent-skill-boundary.md) · Lifecycle: [ADR-014](../../../decision-records/adr-014-skill-lifecycle.md)

All measurements in this document were taken against the working tree on branch `phase/10-progressive-disclosure`, 2026-08-12. Every figure is reproducible with the command shown beside it. **Re-measure before relying on any of them** — this file records what was true at authoring time, not a contract about what the implementer will find.

> **Amended 2026-08-12 (maintainer):** the load mechanism is an inline `Read skills/<name>/SKILL.md` at the point of need; `required_skills:` is not used. See `spec.md` → *Approved Scope Change*. The baseline below is re-measured against `scripts/measure-invocation.py` **after** `e8f2a09`, which corrected the tool's treatment of `required_skills:` from conditional to eager and made inline reads visible. Figures quoted before that commit — in particular a `77,669` ceiling — are wrong and must not be reused.

## Measured Baseline

```bash
python3 scripts/measure-invocation.py --root . --command implement-story --format table
```

| Field | Value | Note |
|---|---|---|
| `base.components["system-instructions.md"]` | 20,153 | |
| `base.components["commands/_preamble.md"]` | 4,807 | |
| `base.bytes` (shared, irreducible) | **24,960** | |
| `command_bytes` | **52,709** | |
| `command_lines` | 989 | |
| `eager_bytes` / `eager_skills` | 0 / `[]` | no `required_skills:` anywhere in the product |
| `floor_bytes` | **77,669** | base + command |
| `conditional_bytes` / `conditional_skills` | **6,101** / `["tdd-cycle"]` | the inline read at `implement-story.md:525` |
| `ceiling_bytes` | **83,770** | floor + `tdd-cycle` |
| `base_share_of_floor` | 32.1% | |
| `unresolved_skills` | `[]` | |

**83,770 is the ceiling bar, not 77,669.** The pre-`e8f2a09` instrument read frontmatter only and reported floor = ceiling = 77,669 for this command. It was blind to 44,580 bytes of inline reads across six commands, 6,101 of them here. Business Rule 1's ceiling is set against the corrected number.

Corpus context: 31 commands, 555,965 command bytes total, mean 53.3 bytes per command line for `implement-story`. `implement-story` is the largest floor in the corpus.

### The two mechanisms, and why only one of them can help

| | `required_skills:` frontmatter | inline `Read skills/<n>/SKILL.md` |
|---|---|---|
| When the load happens | *"before any phase work begins"* (`system-instructions.md`; `adapters/claude-code.md:396`) | when execution reaches the line |
| Selection granularity | per **command** (static array) | per **run** |
| Where the bytes land | `eager_bytes` → **floor** | `conditional_bytes` → **above** the floor |
| Cost of a skipped gate | full price | **zero** |
| Adoptions in the product | 0 | 7 commands |

A skill declared *and* inline-read is charged once, as eager, with a warning (`measure-invocation.py:262–267`). Business Rule 8 forbids that shape. `scripts/lint-skill.sh:52` forbids `Read skills/` **inside a skill**, so every inline read in this spec lives in `commands/implement-story.md` and nowhere else.

### Why lines are the wrong instrument

```bash
python3 scripts/measure-invocation.py --root . --format table   # bytes/line column derivable
```

| Command | Bytes | Lines | Bytes/line | Over a 400-line cap? | In the top 6 by bytes? |
|---|---|---|---|---|---|
| `implement-phase` | 29,136 | 321 | 90.8 | **no** | **yes (#4)** |
| `implement-story` | 52,709 | 989 | 53.3 | yes | yes (#1) |
| `create-spec` | 46,423 | 871 | 53.3 | yes | yes (#2) |
| `verify-spec` | 32,110 | 732 | 43.9 | yes | yes (#3) |
| `migrate` | 13,656 | 396 | 34.5 | no (barely) | no |
| `create-uat-plan` | 16,239 | 417 | 38.9 | **yes** | no |

Spread: **34.5 → 90.8 = 2.63×**. A 400-line cap exempts the 4th-heaviest file in the product and fires on a file less than half its weight. That is the evidence behind the ADR-021 amendment.

## Section Ledger — `commands/implement-story.md`

Byte counts per section, produced by splitting the file on non-fenced markdown headings. Line ranges are inclusive and refer to the pre-edit file.

| Lines | Section | Bytes | Disposition | Target |
|---|---|---|---|---|
| 1–27 | frontmatter + `# ` title | 2,710 | **KEEP byte-identical — nothing appended** | command |
| 28–33 | `## Overview` | 361 | keep | command |
| 34–40 | `## Required Artifacts` | 245 | keep (pinned literal) | command |
| 41–49 | `## Invocation` | 388 | keep | command |
| 50–65 | `## Agent Pipeline` (ASCII diagram) | 2,021 | **replace** with phase table (~1,300) | command |
| 66–71 | `## Command Process` + Step 1 | 156 | keep | command |
| 72–94 | Step 2: Load Context (10-item list) | 1,437 | keep | command |
| 95–141 | Parsing Context Hints | 3,437 | extract, retain ~450 | skill 1 |
| 142–195 | Loading Knowledge Context | 2,383 | extract, retain ~120 | skill 1 |
| 196–220 | Extracting Agent-Specific Spec-Lite Sections | 1,696 | extract ~900; **retain the routing table** ~850 | skill 1 |
| 221–340 | Loading "What Was Built" from Dependencies | 5,072 | extract, retain ~300 | skill 2 |
| 341–396 | `.writ/context.md` Format & Regeneration | 2,148 | extract, retain ~300 | skill 7 |
| 397–404 | Step 3: Run Pipeline | 816 | keep | command |
| 405–426 | Gate 0: Architecture Check | 1,110 | contract stub ~350 | command |
| 427–435 | Gate 0.5 intro | 758 | contract stub ~350 | command |
| 436–459 | `boundary_map` schema | 1,258 | extract | skill 4 |
| 460–496 | Computation algorithm | 3,123 | extract | skill 4 |
| 497–519 | Check 5 persistence | 927 | extract | skill 4 |
| 520–553 | Gate 1: Coding Agent | 2,276 | keep ~1,300 (collapse BLOCKED template) | command |
| 554–570 | Gate 2: Lint/Typecheck | 539 | keep | command |
| 571–593 | Gate 2.5: Change Surface | 1,896 | extract, retain ~250 | skill 5 |
| 594–616 | Gate 3: Review Agent | 1,930 | keep ~1,400 (**pinned regex**) | command |
| 617–622 | Gate 3.5 heading | 227 | keep | command |
| 623–669 | A. Drift Response | 2,219 | extract, retain ~450 | skill 6 |
| 670–733 | B. WWB Data Extraction | 2,725 | extract | skill 3 |
| 734–774 | Gate 4: Testing Agent | 1,697 | keep ~900 (**pinned regex**, shared BLOCKED template) | command |
| 775–797 | Gate 4.5: Visual QA | 782 | keep | command |
| 798–815 | Gate 5: Documentation | 644 | keep | command |
| 816–828 | Step 4: Story Completion (8-item list) | 796 | keep | command |
| 829–841 | Recording the Story Commit SHA | 1,725 | extract, retain ~350 | skill 8 |
| 842–956 | "What Was Built" Record Assembly | 3,473 | extract | skill 3 |
| 957–965 | `## Error Handling` | 701 | keep | command |
| 966–975 | `## Quick Mode` | 329 | keep | command |
| 976–985 | `## Completion` | 539 | **keep byte-identical** | command |
| 986–990 | `## References` | 165 | keep + 8 skill links (~350) | command |

Section sum: 49,999. Frontmatter/title remainder: 2,710. Total: **52,709** ✓.

## Projected Budget

| Quantity | Before | Projected after | Binding limit | Source |
|---|---|---|---|---|
| `command_bytes` | 52,709 | **~20,970** | **≤ 24,960** | Business Rule 1 |
| `eager_bytes` | 0 | **0** | must stay 0 | Business Rule 8 rule 3 |
| `conditional_bytes` | 6,101 (`tdd-cycle`) | **~41,300** | — | 8 new skills + `tdd-cycle` |
| `floor_bytes` | 77,669 | **~45,930** (−40.9%) | ≤ 49,920 | base + command |
| `ceiling_bytes` (all gates fire) | 83,770 | **~87,231** (+4.1%) | **≤ 83,770** | Business Rule 1 |
| `command_lines` | 989 | ~390 | (non-binding tripwire) | amended ADR-021 |

**The projected full-path ceiling misses by roughly 3,461 bytes.** That gap is the spec's central risk and the reason the Compression Ledger below exists. The mechanism change does **not** shrink it: it lifts both the baseline and the projection by the same 6,101 bytes of `tdd-cycle` that the old instrument could not see. The floor lands comfortably.

### Per-skill projections — the input to every path figure

Projected authored size = source bytes − retained stub + ~650 scaffolding. Story 2/3/4 record `wc -c` actuals against these and flag overshoot immediately; the `--quick` derivation below is only as good as this column.

| Skill | Source | Retained stub | Projected `SKILL.md` | Gate/step that reads it | On `--quick`? |
|---|---|---|---|---|---|
| `story-context-assembly` | 7,516 | 1,420 | **~6,750** | Step 2 | yes |
| `dependency-context-loading` | 5,072 | 300 | **~5,400** | Step 2, dependency branch | only if the story has dependencies |
| `what-was-built-authoring` | 6,198 | — | **~6,850** | Step 4 item 4 | yes |
| `boundary-map-computation` | 5,308 | — | **~5,950** | **Gate 0.5** | **no** |
| `change-surface-classification` | 1,896 | 250 | **~2,300** | Gate 2.5 | yes |
| `drift-triage` | 2,219 | 450 | **~2,420** | **Gate 3.5 § A** | **no** |
| `project-context-snapshot` | 2,148 | 300 | **~2,500** | Step 4 item 3 | yes |
| `story-commit-provenance` | 1,725 | 350 | **~2,030** | Step 4 item 7 | yes |
| *(existing)* `tdd-cycle` | — | — | **6,101** *(measured)* | Gate 1 (`:525`, unchanged) | yes |
| **Eight new, subtotal** | | | **~34,200** | | |
| **+ connective prose** | | | ~1,000 | | |
| **Skills total incl. `tdd-cycle`** | | | **~41,300** | | |

Existing skills range 5,997–9,985 bytes for reference, so no projected file is anomalous.

### Path-dependent ceilings

Ceiling is no longer one number. `measure-invocation.py` reports only the all-inline-reads figure; the rest are derived by subtracting measured skill sizes for the reads a path never reaches, and the derivation is shown in the load report.

| Path | Composition | Projected after | Same path today | Delta |
|---|---|---|---|---|
| **Floor** (always paid) | base 24,960 + command ~20,970 | **~45,930** | 77,669 | **−31,739 / −40.9%** |
| **Full path** (every gate fires) | floor + all 9 conditional reads | **~87,231** | 83,770 | **+3,461 / +4.1%** ✗ |
| **`--quick`** (Gates 0, 0.5, 3, 3.5, 5 skipped) | full − `boundary-map-computation` ~5,950 − `drift-triage` ~2,420 | **~78,861** | 83,770 | **−4,909 / −5.9%** ✓ |
| **`--quick`, no dependencies** | above − `dependency-context-loading` ~5,400 | **~73,461** | 83,770 | **−10,309 / −12.3%** ✓ |
| **`--review-only`** (Gates 0, 0.5, 1 skipped) | full − `boundary-map-computation` − `tdd-cycle` 6,101 | **~75,180** | 83,770 | **−8,590 / −10.3%** ✓ |

**The `--quick` row is the spec's proof the mechanism works**, and it is the row the eager mechanism could not have moved by a single byte: under `required_skills:` every one of those runs pays ~87,231 regardless of which gates fire.

**Report it honestly.** `--quick` skips five gates but only **two** of them carry an extracted skill — Gate 0 (arch-check), Gate 3 (review) and Gate 5 (docs) are agent spawns whose procedure lives in `agents/*.md`, outside both this instrument and this spec. "Five gates skipped" is not "five skills saved". The largest single conditional win in the table is `dependency-context-loading`, which is mode-independent.

## Compression Ledger

Business Rule 2 permits contraction and forbids redesign. These are the identified targets — each one is a *duplicate* of something specified elsewhere in the same text, not a rule. Yields are estimates from the measured block sizes; the implementer records actuals.

| # | Target | Location | Est. yield | Why removing it is contraction, not redesign |
|---|---|---|---|---|
| C1 | "Example Coding Agent Context (with WWB)" — a 41-line worked example | L299–339 (~1,500 B) | ~1,200 | Illustrates the aggregation format specified 20 lines above it at L274–286. The format is the rule; the example is a second copy of it. |
| C2 | `what_was_built_data` JavaScript object literal | L712–728 (~700 B) | ~400 | Restates the exact field list the Formatting Template at L858–915 already enumerates. One field list, two syntaxes. |
| C3 | Overlapping "Graceful Degradation" lists | L292–297 and L924–953 | ~400 | The dependency-incomplete and missing-WWB rows appear in both. Consolidate into the one skill that owns the record. |
| C4 | `boundary_map` Flags list vs. the schema block's inline annotations | L440–458 | ~300 | The `(overlap: …)` and `(⚠️ high-overlap: …)` semantics are stated twice, once as a comment inside the schema and once as a Flags list beneath it. |
| C5 | Drift-log entry format example | L659–668 (~350 B) | ~350 | `.writ/docs/drift-report-format.md` is already cited as the format reference two lines earlier. Point at the authority instead of copying it. |
| C6 | The two `STATUS: BLOCKED` `AskQuestion` blocks | L533–551, L754–771 | ~950 | Byte-identical except for the agent name and gate number. Collapse to one parameterized block in the command (this is a command-side saving, already reflected in the projection). |
| | **Total identified** | | **~3,600** | |

If C1–C5 land in the skills and C6 in the command, the ceiling closes. **If measured yields fall short, Business Rule 1's justification path opens — do not manufacture the remainder by deleting rules.**

## Pinned Literals — strings that must stay in `commands/implement-story.md`

`scripts/eval.sh` asserts these against **this file specifically**. Moving one into a skill turns a passing check into a finding, and Business Rule 7 forbids editing `eval.sh` to compensate.

| # | Literal | Asserted at | Currently at | Minimum retained carrier |
|---|---|---|---|---|
| 1 | `scripts/story-context.py assemble` | `eval.sh:2134` | L105 | The invocation fence in Step 2 stays in the command; the script owns the algorithm anyway. |
| 2 | `| Architecture Check (Gate 0) |` | `eval.sh:2137` | L208 | Per-agent routing table — all five rows stay as a block. |
| 3 | `| Coding Agent (Gate 1) |` | `eval.sh:2138` | L209 | same table |
| 4 | `| Review Agent (Gate 3) |` | `eval.sh:2139` | L210 | same table |
| 5 | `| Testing Agent (Gate 4) |` | `eval.sh:2140` | L211 | same table |
| 6 | `| Documentation Agent (Gate 5) |` | `eval.sh:2141` | L212 | same table |
| 7 | `## Artifact Map` | `eval.sh:2721` | L363 | One sentence in Step 4 asserting the regenerated snapshot carries an `## Artifact Map`, pointing at `project-context-snapshot` for the schema. |
| 8 | `**Integrity:**` | `eval.sh:2722` | L369 | Same sentence: the `**Integrity:**` line always renders. |
| 9 | `## Required Artifacts` | `eval.sh:2727` | L34 | The section itself is retained. |
| 10 | `> **Commit:**` | `eval.sh:2787` | L7 (frontmatter), L836–840 | Already in `exit_criteria`, which is preserved byte-identical. Safe by construction — but verify, do not assume. |
| 11 | `Skip reverted records` | `eval.sh:2788` | L249 | One line in Step 2 stating that a WWB record carrying a `> **Reverted:**` banner is skipped as non-authoritative, pointing at `dependency-context-loading`. |

**Two `forbid_literal` strings must remain absent — from the command and from every skill:**

| Literal | Asserted at | Meaning |
|---|---|---|
| `Store parsed hints in \`context_hints\` map` | `eval.sh:2135` | Retired prose parsing step, replaced by `scripts/story-context.py`. |
| `For bracketed references: search source file for matching rows/entries by name` | `eval.sh:2136` | Retired prose fetch-and-aggregate step, same replacement. |

`eval.sh` scopes these to the command file only, so reintroducing them inside `story-context-assembly` would not trip the check — and would still be a defect. The assembler script owns that algorithm; a skill restating it recreates the divergence Story 4 of the context-hints work eliminated.

## Pinned Regexes — `scripts/eval-loop-bounds.py`

`body_of("commands/implement-story.md")` strips the frontmatter and then searches the **body**, deliberately, *"so a cross-read never matches the very declaration it is meant to be checking"* (`eval-loop-bounds.py:388–390`).

| Regex | Source line | Expected value | Currently at | Consequence if it moves |
|---|---|---|---|---|
| `Max (\d+) iterations across review` | `eval-loop-bounds.py:485` | 3 | L615 — *"Review loop: Max 3 iterations across review and visual QA gates"* | `first_int` returns `None` → `emit_skip("drift-review-cycle", …)`. Reported, not failed — a determinism check silently stops checking. |
| `(\d+) fix iterations max` | `eval-loop-bounds.py:488` | 2 | L752 — *"2 fix iterations max (separate from the review loop's 3-iteration cap)"* | Same: `emit_skip("drift-testing-cycle", …)`. |

Both sentences stay in the command body. An iteration cap is contract, not procedure, so this constraint and ADR-021's thin-contract definition agree.

`MAX_SELF_FIX_ITERATIONS = 3` is read from `agents/coding-agent.md` and `agents/testing-agent.md`, not from the command, so the collapsed BLOCKED escalation block may reference it freely.

## Skill Specifications

Each is scaffolded with `/new-skill <name>`, which validates the name, runs `lint-skill.sh` on the captured frontmatter, writes `status: candidate`, appends to `.writ/manifest.yaml`, and regenerates `SKILL.md`. Descriptions below are drafts that satisfy Business Rule 3 rule 4 and clear `lint-skill.sh`'s `DESC_PATTERNS`; the authoring command may refine them.

| # | Name | Draft `description:` | Source | Read placed at | Story |
|---|---|---|---|---|---|
| 1 | `story-context-assembly` | "Assemble the targeted context payload each pipeline agent receives — parsed hints, knowledge entries, and role-specific spec-lite sections." | L95–220 | Step 2 | 2 |
| 2 | `dependency-context-loading` | "Load, filter, and truncate upstream stories' implementation records into dependency context." | L221–340 | Step 2, dependency branch | 2 |
| 3 | `what-was-built-authoring` | "Extract implementation facts from agent output and format them into a What Was Built record." | L670–733, L842–956 | Step 4 item 4 | 4 |
| 4 | `boundary-map-computation` | "Compute an owned / readable / out-of-scope file ownership map from tasks, imports, and overlap data." | L436–519 | Gate 0.5 | 3 |
| 5 | `change-surface-classification` | "Classify a change set as style-only, single-component, cross-component, or full-stack." | L571–593 | Gate 2.5 | 3 |
| 6 | `drift-triage` | "Triage implementation deviations by severity and route each to amend, warn, or pause." | L623–669 | Gate 3.5 § A | 3 |
| 7 | `project-context-snapshot` | "Regenerate a whole-file project context snapshot from product, spec, drift, and issue sources." | L341–396 | Step 4 item 3 | 4 |
| 8 | `story-commit-provenance` | "Record a completion commit SHA into a story file header idempotently and without amending it." | L829–841 | Step 4 item 7 | 4 |

**Read placement is Story 5's work, not Stories 2–4's** — the skills are authored first and additively, and no `Read` exists until the command is rewritten. The column is recorded here so the authoring stories know which run pays for what and can size accordingly: a skill destined for Gate 0.5 or Gate 3.5 is free on `--quick`, and a skill destined for Step 2 or Step 4 is paid on every run and is therefore the one worth compressing hardest.

### Boundary rules that constrain authoring

`scripts/lint-skill.sh` rejects, outside fenced code blocks and outside 4-space-indented lines:

- `Read commands/` — command invocation
- `Read skills/` — skill chaining
- `Task(` not preceded by a letter or underscore — subagent dispatch
- a line beginning `/<lowercase-command>` — slash-command invocation

Three consequences for this extraction:

1. **Gate 1's current sentence is the exemplar for all eight.** L525 reads *"Spawns the coding agent to run the red → green → refactor loop via `Read skills/tdd-cycle/SKILL.md`, … This gate owns *when* coding runs, the context it routes below, and `STATUS: BLOCKED` handling; the skill owns *how* the test-first cycle runs."* That is exactly the shape Story 5 writes eight more times: orchestration sentence, inline read, one clause naming the split. Copy the form.
2. **Every inline read lives in the command — `lint-skill.sh:52` guarantees it.** `Read skills/` inside a `SKILL.md` is a Skill-chaining violation (*"Skills do not call other skills. Combine them into the consumer (agent/command) that uses both"*). The eight extracted skills are a flat set: none loads another, none references another's file path as a load, and `grep -RF 'Read skills/' skills/` must return nothing. Stories 2–4 verify this as part of their existing lint step; no new check is needed.
3. **Agent-spawn language does not travel.** "Spawns a read-only sub-agent" and every `AskQuestion` escalation stay in the command. A skill describes the transformation, given inputs; it never says who runs it.

`lint_lifecycle` requires `status:` in the closed vocabulary `candidate|proven|promoted`. `candidate` needs no `evidence:` block. Do not author `promoted` on day one — L3/L4 would reject it as unearned, and correctly.

## `.writ/manifest.yaml` and `SKILL.md`

`/new-skill` appends each entry alphabetically and re-runs `scripts/gen-skill.sh`. After all eight land, `skills:` holds 14 entries and `bash scripts/gen-skill.sh --check` must pass. Stories 2–4 all write this file; if they run in parallel worktrees the last to land re-runs the generator and confirms `--check`.

## Leanness Disposition

`.writ/leanness-baseline.json` (schema 3, recorded 2026-08-04):

| Surface | Baseline lines | Baseline chars | Existing justification | Expected direction |
|---|---|---|---|---|
| `commands` | 10,974 | 514,594 | lines→11,411, chars→560,772 (2026-08-11) | **falls** by ~31,700 chars |
| `skills` | 932 | 41,620 | **none** | **rises** by ~35,200 chars |

The `skills` rise needs a **bound justification** — the `(surface, metric)`-scoped `{date, value, text}` record that `2026-08-11-governor-instrumentation` Story 1 built, which silences one recorded increment per metric and warns again on any growth past it. Text must name this spec, the byte count relocated, and the corresponding `commands` reduction, so a reader sees a transfer rather than growth. **Do not run `--update-baseline`** — it moves every surface's floor and records no reason (`eval-leanness.py:590–595`).

`check_ceilings` compares the skill count against `MAX_SKILLS = 12`; 14 exceeds it and emits a **warning**, never a structural finding. Report the number; do not edit the constant (Business Rule 7).

## Verification

```bash
# 1. The budget — floor and full-path ceiling, before and after
python3 scripts/measure-invocation.py --root . --command implement-story --format table
#    command_bytes <= 24960 ; floor_bytes <= 49920 ; ceiling_bytes <= 83770
#    eager_bytes == 0 ; eager_skills == []          (no required_skills:)
#    no "loads `<n>` **both** ways" warning in the warnings array

# 1b. The --quick ceiling — derived, because the tool does not model paths
python3 - <<'PY'
import json, subprocess, os
d = json.loads(subprocess.check_output(
    ["python3", "scripts/measure-invocation.py", "--root", ".",
     "--command", "implement-story"]))["commands"]["implement-story"]
skipped = ["boundary-map-computation", "drift-triage"]      # Gates 0.5 and 3.5
saved = sum(os.path.getsize(f"skills/{s}/SKILL.md") for s in skipped)
print("full ceiling :", d["ceiling_bytes"])
print("--quick      :", d["ceiling_bytes"] - saved, f"(-{saved} for {skipped})")
print("no-deps too  :", d["ceiling_bytes"] - saved
      - os.path.getsize("skills/dependency-context-loading/SKILL.md"))
PY
#    --quick must be strictly below both the full ceiling and 83,770

# 2. Pinned literals present (expect 11 hits, one per literal)
for s in 'scripts/story-context.py assemble' '| Architecture Check (Gate 0) |' \
         '| Coding Agent (Gate 1) |' '| Review Agent (Gate 3) |' \
         '| Testing Agent (Gate 4) |' '| Documentation Agent (Gate 5) |' \
         '## Artifact Map' '**Integrity:**' '## Required Artifacts' \
         '> **Commit:**' 'Skip reverted records'; do
  grep -Fq "$s" commands/implement-story.md || echo "MISSING: $s"
done

# 3. Forbidden literals absent from the command AND every skill (expect no output)
grep -RF 'Store parsed hints in `context_hints` map' commands/implement-story.md skills/
grep -RF 'For bracketed references: search source file' commands/implement-story.md skills/

# 4. Loop-bound cross-reads still resolve (expect no new SKIP lines)
python3 scripts/eval-loop-bounds.py | grep -E 'drift-review-cycle|drift-testing-cycle'

# 5. Frontmatter byte-identical — the diff is now expected to be EMPTY
diff <(git show <base>:commands/implement-story.md | sed -n '1,24p') \
     <(sed -n '1,24p' commands/implement-story.md)
grep -c '^required_skills:' commands/implement-story.md   # expect 0

# 6. Skills lint clean, all candidate, and no skill chains to another skill
bash scripts/lint-skill.sh skills/*/SKILL.md
grep -c '^status: candidate' skills/*/SKILL.md
grep -RF 'Read skills/' skills/          # expect no output (lint-skill.sh:52)

# 7. Reachability and placement (Business Rules 4 and 8)
python3 scripts/measure-invocation.py --root . --command implement-story \
  | python3 -c "import json,sys; d=json.load(sys.stdin)['commands']['implement-story']; \
print(d['eager_skills'], len(d['conditional_skills']), d['unresolved_skills'])"
#    expect: [] 9 []      (8 extracted + tdd-cycle)

#    exactly one Read per skill, and none above '### Step 1'
grep -n 'Read skills/' commands/implement-story.md          # expect 9 lines, no duplicates
step1=$(grep -n '^### Step 1' commands/implement-story.md | cut -d: -f1)
grep -n 'Read skills/' commands/implement-story.md | awk -F: -v s="$step1" '$1 < s'
#    expect no output — a Read above Step 1 is an eager load in disguise

# 8. Graceful degradation probe on the mechanism actually used (revert afterwards)
#    insert `Read skills/deliberately-missing-skill/SKILL.md` at a real step, then:
python3 scripts/measure-invocation.py --root . --command implement-story; echo "exit=$?"
#    expect exit=0, the name in unresolved_skills, and a WARNING that the
#    figures are "a lower bound" — never a hard failure
#    NOTE: eval-leanness.py's check_required_skills reads FRONTMATTER ONLY and
#    has nothing to resolve here (required_skills_declarations stays 0). Record
#    that as the finding; do not add a declaration just to make the probe pass.

# 9. Regression + spec integrity
bash scripts/eval.sh
bash scripts/gen-skill.sh --check
python3 scripts/spec-deps.py validate --specs-dir .writ/specs
bash scripts/check-agent-parity.sh

# 10. No script edits beyond the permitted comment-only exception
git diff --name-only | grep '^scripts/'   # expect nothing, or only eval-story-context.py
```

## Error & Rescue Map

| Failure | Detection | Rescue |
|---|---|---|
| Full-path ceiling exceeds 83,770 after C1–C5 | Verification 1 | Record measured overage, compression attempted and its yield, then escalate for an explicit maintainer decision (Business Rule 1). Do **not** delete rules to close the gap. Do **not** silently pass. Do **not** offer the `--quick` saving as compensation — different run, different number. |
| `--quick` ceiling equals the full ceiling | Verification 1b | A `Read` sits outside the gate that needs it, or above `### Step 1`. Move it to the narrowest step (Business Rule 8). Placement, not content, is the defect. |
| `eager_bytes` is non-zero, or a "both ways" warning appears | Verification 1 / 7 | A `required_skills:` key was added. Remove it — the mechanism was ruled out on 2026-08-12 (`spec.md` → *Approved Scope Change*), and a declaration silently converts a conditional skill into a floor cost. |
| A `Read skills/` appears inside a `SKILL.md` | Verification 6, `lint-skill.sh:52` | Skills do not chain. The read belongs in `commands/implement-story.md`; if two skills genuinely need each other's content, they are one skill. |
| A pinned literal moved into a skill | Verification 2, then `eval.sh` finding | Restore the minimum carrier named in the Pinned Literals table. Never edit `eval.sh`. |
| `drift-review-cycle` / `drift-testing-cycle` newly SKIP | Verification 4 | The prose cap left the body. Restore the sentence verbatim — the number in frontmatter and the number in prose must both exist and agree. |
| `lint-skill.sh` rejects a skill body for `Read skills/` or `Task(` | Verification 6 | The line is orchestration. Move it back to the command; do not paraphrase it into passing. |
| `lint-skill.sh` rejects a description as role-shape | Verification 6 | Rewrite to a bare-imperative verb phrase (Business Rule 3 rule 4). |
| Frontmatter reflowed during the rewrite | Verification 5 | Restore from `git show <base>:commands/implement-story.md`. `eval-loop-bounds.py` and `eval-leanness.py` both parse it. |
| `gen-skill.sh --check` stale after parallel stories | Verification 9 | Re-run `bash scripts/gen-skill.sh`; the generator is deterministic. |
| An extracted skill has no inline read, or has two | Verification 7 + a read of the phase table | Give it exactly one read at its point of need, or fold its content back — an unreferenced skill fails Business Rule 4, and a doubly-read one breaks the `--quick` derivation. |
| Harness hard-fails on an unreadable skill path | Verification 8 or a real run | **Surface it.** `system-instructions.md` → *Schema* and `eval-leanness.py:1239` specify warn-never-fail for the declarative form; the inline form degrades to a failed `Read` the agent must handle in the same spirit. A harness that hard-fails is a finding for ADR-021's review trigger, not something to work around. |

## Interaction Edge Cases

- **`--quick` mode** skips Gates 0, 0.5, 3, 3.5 and 5. Two of those five carry an extracted skill — `boundary-map-computation` (Gate 0.5) and `drift-triage` (Gate 3.5 § A) — and under the inline mechanism both are **genuinely not loaded**. This is the case that motivated the 2026-08-12 mechanism ruling and it is the spec's proof the mechanism works; the derived figure belongs at the top of the Story 6 load report. Gate 2.5 is **not** in the skip list, so `change-surface-classification` is still paid.
- **`--quick` still writes a What Was Built record** — the minimal one with the `> Note: Review skipped` banner. `what-was-built-authoring` is therefore read at Step 4, not at Gate 3.5, even though half its source lives in Gate 3.5 § B. Placing it at 3.5 would make `--quick` runs write a record whose rules were never loaded.
- **`--review-only` mode** skips Gate 1 as well, so `boundary_map` is passed as the literal `(none)` and `tdd-cycle` is not read either. That rule (L529) is contract and stays in the command.
- **A story with no dependencies** never reaches the `dependency-context-loading` read, so it never pays its ~5,400 bytes. This is the largest mode-independent conditional saving in the spec and it exists only because the read sits inside the dependency branch rather than at the top of Step 2.
- **Gate 0.5 is not on the `/prototype` path** (L434). `commands/prototype.md` does not run `implement-story` and gains neither a declaration nor an inline read from this work.
- **Legacy spec-lite without `## For {Role} Agents` headers** falls back to full content per L215–217. That degradation row travels with `story-context-assembly` and must appear in the no-drift inventory.
- **`.writ/knowledge/` absent** is a silent no-op, not a warning (L188). Silence is the specified behavior; a skill that "improves" it to a warning has changed behavior.
- **Reverted WWB records** are skipped as non-authoritative (L249–253) with a specific `ℹ️` log line. Both the rule and the literal string travel.
- **Mixed drift severities** pause for Large while still auto-amending Small (L651). Easy to lose when a severity table is rewritten as a list.

## Testing Strategy

There is no application code and no test suite. Verification is structural, and the substantive test is the **no-drift inventory** (Business Rule 2), not any script.

The inventory is built in Story 1 from `git show <base>:commands/implement-story.md` and stored at `.writ/specs/2026-08-12-disclosure-implement-story/no-drift-inventory.md`. It enumerates, one row per item with its pre-edit line number:

1. Gate numbers and names (0, 0.5, 1, 2, 2.5, 3, 3.5, 4, 4.5, 5)
2. Agent bindings (`agents/*.md` per gate) and inline-orchestration gates
3. Skip-mode rules per gate (`--quick`, `--review-only`, conditional activation)
4. Every numeric threshold: 3 review iterations, 2 testing iterations, `MAX_SELF_FIX_ITERATIONS = 3`, 80% coverage, 100% pass rate, 85%/70% visual match, 1000-line WWB truncation, 2KB `knowledge_context`, 21000-byte context budget, depth-1 import graph, <10s Gate 0.5 target, scoring weights +3/+2/+1/+1
5. Result vocabularies: PROCEED/CAUTION/ABORT, PASS/FAIL/PAUSE, PASS/SOFT PASS/FAIL, Small/Medium/Large, style-only/single-component/cross-component/full-stack, Owned/Readable/Out-of-scope
6. Every graceful-degradation row in every table
7. Every literal log or warning string (`⚠️`, `ℹ️`, `✅`)
8. Every named output variable: `fetched_context`, `context_warnings`, `knowledge_context`, `spec_lite_for_coding|review|testing`, `boundary_map`, `boundary_overlap_summary`, `change_surface`, `what_was_built_data`, `dependency_wwb_context`

Story 6 walks the inventory and records, per row, where it now lives. **Zero unaccounted removals** is the pass condition. A row whose wording changed is fine; a row whose rule is gone is a defect.

## Non-Goals (restated from spec.md → Out of Scope)

- No edit to `scripts/eval.sh`, `scripts/eval-leanness.py`, or `commands/_preamble.md`.
- No `MAX_SKILLS` change, no `check_length` change, no severity flip.
- No edit to `commands/implement-spec.md`, `commands/status.md`, or any other command.
- No agent definition changes; no adapter changes — including the stale first-consumer sentence at `adapters/claude-code.md:396`.
- No edit to `system-instructions.md`. Its `required_skills:` **Status: adopted** paragraph names Phase 10 progressive disclosure as the convention's first consumer; that becomes false when Story 5 lands. Recorded as an unassigned follow-up in `spec.md` → § Technical Concerns, not fixed here.
- No `required_skills:` declaration anywhere. `eager_bytes` must measure 0.
- No skill promotion beyond `status: candidate`.
- No roadmap edit — the stale 400-line criterion is flagged and assigned, not fixed.
