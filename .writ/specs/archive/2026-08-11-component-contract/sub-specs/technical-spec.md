# Technical Spec: Component Contract

> Source: `.writ/specs/2026-08-11-component-contract/spec.md`

## Carrier Analysis (verified against the working tree, 2026-08-11)

### Command frontmatter

All 32 files in `commands/` open with a `---` block. Thirty-one terminate at line 4:

```
---
name: implement-story
description: "Run a single user story through the full SDLC pipeline: architecture check, boundary map, TDD coding, lint, review, testing, documentation."
---
```

`commands/_preamble.md` terminates at line 5 because it carries a third key:

```
---
name: _preamble
description: "Shared standing instructions referenced by every Writ command. Not directly invocable."
disable-model-invocation: true
---
```

The three new keys append after the last existing key, so the terminator moves from line 4 to line 9–11 depending on `exit_criteria` length. No other file content shifts semantically — line-number references inside command bodies are already forbidden by `new-command.md`'s own quality bars ("No hardcoded line numbers or brittle references to other files"), so the offset is safe. Verify this claim per batch rather than assuming it: `grep -n 'line [0-9]' commands/<file>.md` before editing.

### Agent config blocks — two carriers

Six agents (`architecture-check-agent`, `coding-agent`, `documentation-agent`, `review-agent`, `testing-agent`, `user-story-generator`) share this shape, with `## Agent Configuration` at line 7:

````
## Agent Configuration

```
subagent_type: "generalPurpose"
model: default (inherits from parent)
model_tier: orchestration
readonly: false
```
````

The fence is **unlabeled**. The block is a documented convention, not a parsed document — `model: default (inherits from parent)` would parse as a plain string under YAML but has never actually been fed to a parser.

`agents/visual-qa-agent.md` differs on three axes: heading text (`## Agent Specification`), heading position (line 18, after `## Role` and `## Activation` rather than after `## Purpose`), and fence label (` ```yaml `):

````
## Agent Specification

```yaml
name: visual-qa
description: Validates UI implementation against mockups and design specifications
tools: Read, Bash, Browser
disallowedTools: Write, Edit
model: inherit
model_tier: orchestration
readonly: true
maxTurns: 20
```
````

It also uses `## Role` where the other six use `## Purpose`. **None of this is normalized by this spec** (Business Rule 6). The edit in both cases is identical in kind: append `problem:`, `outcome:`, `exit_criteria:` after the last existing key, inside the existing fence.

Implementation note: an agent-file editor that matches on `^## Agent Configuration$` alone will silently skip `visual-qa-agent.md` and report 6/7 as success. Match on `^## Agent (Configuration|Specification)$`, or handle the seventh file explicitly.

## Authoring `exit_criteria` — worked examples

The difference between a criterion that carries information and one that does not is the whole spec. Illustrative only — the implementing agent derives each command's real criteria from that command's actual body, not from this table.

| Command | ✗ Boilerplate (fails BR2) | ✓ Derived (satisfies BR3) |
|---|---|---|
| `/create-spec` | "a complete specification is created" | `".writ/specs/<slug>/spec.md contains a '## Contract (Locked)' section"` · `"user-stories/README.md row count equals the number of story-N-*.md files"` · `"every story file's Status header reads 'Not Started'"` |
| `/release` | "the release completes successfully" | `"VERSION differs from its pre-run value"` · `"a git tag matching v<VERSION> exists"` · `"CHANGELOG.md contains a heading for <VERSION>"` |
| `/ship` | "a pull request is opened" | `"gh pr view returns an open PR whose head is the current branch"` · `"the PR body contains a '## Spec Reference' section"` · `"git status reports no unpushed commits on the current branch"` |
| `/verify-spec` | "the spec is verified" | `"every check in the diagnostic reports PASS or a recorded, non-auto-fixable finding"` · `"no story file's status contradicts its checkbox state"` |
| `/knowledge` | "knowledge is captured" | `"a new file exists under .writ/knowledge/ dated today"` · `"the entry is under the size bar the command states"` |

**The swap test in practice.** Take `"a git tag matching v<VERSION> exists"` and paste it into `/review`'s frontmatter: false and nonsensical — `/review` creates no tag. Take `"the command completes successfully"` and paste it anywhere: plausible everywhere, therefore worthless. Take `"the report is saved"` and paste it into `/retro`, `/review`, `/security-audit`, `/research`: plausible in all four, therefore it must be sharpened by naming *which* report at *which* path.

**Anti-pattern to reject in review:** a criterion that names a path but asserts nothing about it. `".writ/state/review-<branch>.md"` is not an assertion. `".writ/state/review-<branch>.md exists and contains a Recommendation section"` is.

## Line Budget Arithmetic

| Surface | Files | Per-file ceiling | Ceiling total |
|---|---|---|---|
| Command frontmatter | 31 | 7 lines | 217 |
| Agent config blocks | 7 | 7 lines | 49 |
| New `## Completion` sections | 18 | 14 lines | 252 |
| **Total** | | | **518** |

The 7-line frontmatter ceiling decomposes as 1 (`problem`) + 1 (`outcome`) + 1 (`exit_criteria:` key) + 4 (max entries). Two entries (5 lines) is the floor; three (6 lines) is the expected shape. A command needing more than four assertions to describe its terminal state is a signal about the command, not about the budget.

The 14-line `## Completion` ceiling is derived, not invented. Measured across the 13 incumbent sections (heading to next `## `, inclusive of trailing blank and separator):

```
knowledge 12 · create-issue 14 · create-uat-plan 15 · implement-phase 15 · new-command 15 · research 15
create-adr 16 · create-spec 16 · plan-product 16 · review 16 · new-skill 17 · design 18 · edit-spec 18
```

Median 15–16. New sections may not exceed 14 — one line under the tightest incumbent cluster, because a section written today for a command that never had one should be leaner than sections that accreted.

**Reporting.** The final story runs `git diff --stat <base>..HEAD -- commands/ agents/` and records added-line count in its evidence. This is not a check the spec builds; it is a number a human reads.

## Placement Rules

- **Frontmatter keys:** after the last existing key, in the order `problem`, `outcome`, `exit_criteria`. Never before `name` or `description`.
- **Agent keys:** after the last existing key inside the existing fence. Never a second fence, never a new heading.
- **`## Completion`:** immediately before the file's final `## References` section, matching all 13 incumbents. Where a file has a `---` horizontal rule before `## References`, the new section goes before that rule, preserving the existing rule-then-References pattern.

## `commands/new-command.md` — Exact Edit Set (Story 1)

Four edits, all in Phase 2 / Step 2.1, plus the file's own frontmatter.

1. **Structure table** — the table currently has six rows (Overview, Invocation, Command Process, Core rules or conventions, Integration with Writ, References). Add a **Completion** row between "Integration with Writ" and "References", matching the placement rule above.
2. **Frontmatter contract** — a short block stating the three fields, the fixed key order, and the 7-line budget, placed with the other quality bars for the generated file.
3. **Authoring coaching** — the swap test and the restatement test, plus one contrasting example pair. Compact: this is coaching, not a second copy of the schema. Point at `.writ/docs/component-contract.md` for the full rules.
4. **Model tier note — NOT IN SCOPE (ownership ruling, 2026-08-11).** An earlier draft of this section specified a correction here. It is withdrawn. The note, the Step 2.2 model-tier checklist bullet, and the whole prose-note carrier belong to **`2026-08-11-retire-dead-prescription`** — this spec's dependency, ordered first — under its locked contract clause (a): *"The prose-note workaround for advisory `model_tier` is replaced by frontmatter."*

   The withdrawn rationale was that the format is load-bearing for `.writ/docs/model-tiers.md` and `scripts/lint-skill.sh`. That dependency does not survive the phase: the owning spec's **Story 6** removes the `lint-skill.sh` prose-note regex branch and rewrites the `model-tiers.md` rows. Correcting the justification here while the dependency deletes the convention would leave `new-command.md` teaching a carrier nothing parses.

   **Verification for Story 1:** `git diff commands/new-command.md` must show zero changes to Step 2.1's Model tier note or the Step 2.2 bullet. If those lines still prescribe a prose note when this story runs, the dependency did not land — escalate, do not repair in place.

## ADR-020 and roadmap — Exact Edit Surface (Story 1)

Approved scope addition, 2026-08-11 (`spec.md` → § Approved Scope Additions). Six edits across two files. Every one is a replacement in place; the exact after-text is authoritative in `spec.md` → *Detailed Requirements → ADR-020 and roadmap premise corrections* and is not duplicated here.

### `.writ/decision-records/adr-020-component-contract.md` (113 lines)

| # | Locus | Line (pre-edit) | Nature |
|---|---|---|---|
| 1 | Header `> **Date:**` | 3 | Append `(amended 2026-08-11 — see Amendments)` |
| 2 | Decision, sentence following carrier item 3 | 31 | Replace — drops "**already mandates**", points at the amendment |
| 3 | `### The finding that reframed the decision` heading | 47 | Rename → `### The finding: nothing checks the components themselves` |
| 4 | Same subsection, body | 49–51 | Delete the false first paragraph; replace the "The contract is not missing; it is **unenforced**" clause. **Preserve verbatim** the tooling-inventory sentence beginning "Writ has extensive deterministic tooling" and the "guardian measures its own byte count" sentence |
| 5 | Consequences → Positive, third bullet | 87 | Replace "closing a template violation that has been accumulating unnoticed" |
| 6 | New `## Amendments` section | before line 104 (`## References`) | Insert — ADR-009 convention |

**Untouched, and verified untouched by `git diff`:** the Decision's three numbered carriers (lines 13–29), the Context measurement table (lines 41–45, including `| Commands with a `## Completion` section | **13 of 32** |`), "Why frontmatter and not prose" (53–57), "Why This Is Not Another Token Tax" (59–63), all five Considered Alternatives (65–80), the Negative consequences, the Enforcement-sequencing block, and the 2026-11-11 review trigger.

**Anchor note.** Edit 2 links to `[Amendments](#amendments)`. GitHub and most markdown renderers slugify `## Amendments` to `#amendments`; `scripts/eval.sh check_broken_refs` does not scan `.writ/decision-records/`, so this is a readability concern, not a check. Verify by eye.

**ADR-009 is the format exemplar** — `.writ/decision-records/adr-009-command-agent-skill-boundary.md`, `## Amendments` → `### 2026-05-06 — Codex CLI skills install path` → **Correction:** / **Rationale:** / **Originating work:**. This entry adds a **Measured:** line, because the whole point of the amendment is that the original claim was never measured.

### `.writ/product/roadmap.md` (424 lines)

| # | Locus | Line (pre-edit) | Nature |
|---|---|---|---|
| 1 | Revision Log, 2026-08-11 row | 17 | Append a sentence to the existing Change cell — **not** a new row |
| 2 | Phase 10 "Problem (measured, not assumed)" table, `## Completion` row | 316 | Replace the trailing clause only; `**13 of 32**` is verified and stays |
| 3 | Phase 10 Success Criteria | 330 | Replace the whole line |

**Line-count neutrality is a hard constraint, not a preference.** `2026-08-11-retire-dead-prescription` cites `.writ/product/roadmap.md:341` (`required_skills:` adoption described forward-looking) and `:343` (the 44-entry manifest figure) by line number in `user-stories/story-3-required-skills-adoption.md:39` and `user-stories/README.md:47`. All three edits stay on their own line, which is why the Revision Log correction is appended to the 2026-08-11 row rather than added as a new row above it.

### Verification

```bash
# ADR-020: amendment present, decision untouched
grep -n '^## Amendments' .writ/decision-records/adr-020-component-contract.md
grep -c 'already mandates\|template violation\|it is \*\*unenforced\*\*' \
  .writ/decision-records/adr-020-component-contract.md   # expect 0
git diff -U0 -- .writ/decision-records/adr-020-component-contract.md   # inspect: no hunk inside lines 13-29 or 41-45

# roadmap: corrected, and exactly as long as before
grep -n 'template violation\|19 file\|already mandating' .writ/product/roadmap.md   # expect no output
wc -l .writ/product/roadmap.md                              # expect 424
git diff --numstat -- .writ/product/roadmap.md              # added must equal deleted
sed -n '341p;343p' .writ/product/roadmap.md                 # must still be the lines the sibling spec cites

# spec integrity
bash scripts/eval.sh
python3 scripts/spec-deps.py validate --specs-dir .writ/specs
```

## `.writ/docs/component-contract.md` (Story 1)

New file, alongside `model-tiers.md` / `skills.md` / `spec-format.md`. Ships to installed projects through `install.sh`'s doc fan-out (`append_manifest_writ_docs` at line ~807, `overlay_scan_flat_dir "$WRIT_SRC/.writ/docs"` at line ~1029), so Writ users authoring their own commands read it, not just this repo's maintainer.

Contents: the schema for both carriers · field order · the two authoring tests with a worked example pair · the line budget with its derivation · the explicit statement that `exit_criteria` is only nominally machine-checkable and why the field is still worth its lines (ADR-020 Consequences) · a pointer to ADR-020.

Match the density and length of `.writ/docs/model-tiers.md`. This is a reference doc, not a second spec.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling |
|---|---|---|
| Append keys to command frontmatter | A file's `---` terminator is mis-detected and keys land in the body | Verify per file that the terminator moved by exactly the number of lines added; `grep -c '^---$'` must stay at 2 for every command file |
| Append keys to an agent fence | `visual-qa-agent.md` skipped because the editor matched only `## Agent Configuration` | Match `^## Agent (Configuration\|Specification)$`; assert 7/7 files changed, not ≥6 |
| Insert `## Completion` | Section lands after `## References`, or duplicates an existing one | Assert exactly one `^## Completion` per file and that its line number is below the file's last `^## References` |
| Author `exit_criteria` under time pressure | Fields present, informationally empty — passes every automated check | Success Criterion 6 (10-entry swap-test spot check) is run and its result recorded, not assumed |
| Parallel batch execution (Stories 2–5) | Two stories edit the same file | File sets are disjoint by construction; Story 6 is sequenced after all four because it re-enters 17 of their files |
| Line budget overrun | Aggregate creeps past 518 while every file is individually "fine" | Measured `git diff --stat` in the final story; over-budget is a review failure, not a note |
| Amend ADR-020 | The correction spreads into the Decision, the alternatives, or the review trigger — a re-decision wearing an amendment's clothes | Six named loci only (see Exact Edit Surface). `git diff -U0` must show no hunk inside lines 13–29 or 41–45 |
| Amend ADR-020 | The false subsection is deleted rather than corrected, erasing the reasoning trail | Replace the false sentences; preserve the tooling-inventory sentences verbatim; the `## Amendments` entry carries the history |
| Correct the roadmap | An edit changes the file's line count and silently breaks `roadmap.md:341` / `:343` in `2026-08-11-retire-dead-prescription` | One-for-one line replacement; Revision Log note appended to the existing 2026-08-11 row. Assert `wc -l` = 424 and equal added/deleted in `git diff --numstat` |
| Correct the roadmap | A verified number gets "corrected" alongside the false clause — `13 of 32` looks wrong next to this spec's `13 of 31` | Both are correct against different populations (raw file list vs. commands). `2026-08-11-governor-instrumentation` `story-3:37` says explicitly not to touch either. Only mandate clauses change |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| `commands/_preamble.md` | Excluded (BR8). It is counted in "32/32 carry frontmatter" and excluded from "all 31 commands." Do not add fields; do not add a `## Completion`. |
| A command whose `## Completion` already exists but is stale | `exit_criteria` derives from the *file's actual behavior*; if the incumbent section contradicts it, fix the section (BR7) and note it in the story. This is the only case where an incumbent section is edited. |
| `implement-story.md` (961 lines) and `create-spec.md` (865 lines) | Progressive disclosure will rewrite these files wholesale in a later spec. Keep the edit surgical and additive so the later rewrite has minimal merge surface. |
| `refresh-command.md` | Its Evidence Gate is the eventual consumer of `status:`/`evidence:` per ADR-014, but those fields are **not** part of this contract. Add only the three fields. |
| `visual-qa-agent.md` uses `## Role`, not `## Purpose` | Irrelevant to this spec — the contract lives in the fenced block, not in the prose heading. Do not rename. |
| A command where `problem:` cannot be stated in one line | Record the scoping defect in the story's notes and write the tightest one-line version available. Do not use a YAML block scalar (BR5), do not consolidate or delete the command (BR10). |

## Testing Strategy

No application code, no test suite. Verification is structural and runs from the repo root:

```bash
# 1. Command contract coverage — expect 31, and 0 for _preamble
grep -l '^problem:' commands/*.md | grep -v _preamble | wc -l
grep -c '^problem:' commands/_preamble.md

# 2. Completion coverage — expect 31
grep -l '^## Completion' commands/*.md | wc -l

# 3. Frontmatter integrity — expect '2' for every command file
for f in commands/*.md; do echo "$f $(grep -c '^---$' "$f")"; done

# 4. Agent coverage — expect 7, both carriers intact
grep -l '^problem:' agents/*.md | wc -l
grep -n '^## Agent \(Configuration\|Specification\)$' agents/*.md

# 5. Line budget — expect total added ≤ 518
git diff --stat <base>..HEAD -- commands/ agents/

# 6. Regression
bash scripts/eval.sh
bash scripts/check-agent-parity.sh
```

Checks 1–5 are run by the implementing agent as story evidence; none of them are added to `scripts/eval.sh` (Business Rule 9). `2026-08-11-governor-instrumentation` converts them into blocking `structural` findings, landing as warnings first per ADR-020's enforcement-sequencing note.

## Non-Goals (restated from spec.md → Out of Scope)

No eval/lint/CI check. No loop bounds. No progressive disclosure or skill extraction. No `system-instructions.md` edit. No `claude-code/agents/` or `codex/agents/` mirror updates. No skill fields. No `_preamble.md` changes. No carrier normalization. No relocation of `model_tier`. No rewriting of command substance and no consolidation of commands the audit reveals as redundant. No re-decision of ADR-020 — the amendment corrects a premise and reopens nothing. No edits to the sibling Phase 10 specs that repeat the premise (`2026-08-11-governor-instrumentation` `spec.md:19`, `:49`; `2026-08-11-loop-bounds` `spec.md:26`).
