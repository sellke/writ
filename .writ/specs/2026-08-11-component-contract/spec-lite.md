# Component Contract (Lite)

> Source: .writ/specs/2026-08-11-component-contract/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `problem:` / `outcome:` / `exit_criteria:` in all 31 commands' existing `---` frontmatter and all 7 agents' existing fenced config block, plus a `## Completion` section in all 31 commands (13 exist, 18 to write).

**Schema (commands — after `description:`, fixed order):**
```yaml
problem: "..."        # one line: what goes wrong without this command
outcome: "..."        # one line: the artifact/state that exists after
exit_criteria:        # 2-4 machine-checkable assertions
  - "..."
```
**Agents:** same three keys appended to the existing fenced block. 6 agents use `## Agent Configuration` + plain fence (line 7); `visual-qa-agent.md` uses `## Agent Specification` + ` ```yaml ` fence (line 18). Write to both as-is — never convert one style to the other.

**Files in Scope:**
- `commands/*.md` — 31 files (NOT `_preamble.md`, which is not a command).
- `agents/*.md` — 7 files.
- `commands/new-command.md` — adds a `## Completion` row + the 3-field contract to its generated-command structure table; adds swap/restatement-test coaching; corrects its false "Commands have no frontmatter mechanism" clause (the `model_tier` prose-note format itself stays locked).
- `.writ/docs/component-contract.md` — NEW. Schema, both carriers, both authoring tests, line budget.
- `.writ/decision-records/adr-020-component-contract.md` — Story 1. Dated `## Amendments` entry (ADR-009 convention) + 4 in-place premise fixes. Amend, never delete: the Decision (three carriers, frontmatter over prose) and the `13 of 32` row stay byte-for-byte.
- `.writ/product/roadmap.md` — Story 1. Phase 10 lines 316 and 330 replaced **one-for-one**, Revision Log note appended to the existing 2026-08-11 row. `wc -l` must stay 424 — `2026-08-11-retire-dead-prescription` cites `roadmap.md:341` and `:343`.

**Batches (by pipeline role):** planning/spec (10: plan-product, create-spec, edit-spec, assess-spec, create-adr, create-uat-plan, research, design, knowledge, create-issue) · implementation/recovery (6: implement-phase, implement-spec, implement-story, prototype, refactor, revert) · quality/release (7: review, verify-spec, security-audit, retro, ship, release, status) · meta/install (7: new-skill, refresh-command, initialize, migrate, reinstall-writ, uninstall-writ, update-writ) · `new-command` in Story 1.

**18 commands missing `## Completion`:** assess-spec, implement-spec, implement-story, initialize, migrate, prototype, refactor, refresh-command, reinstall-writ, release, retro, revert, security-audit, ship, status, uninstall-writ, update-writ, verify-spec. Place each immediately before the file's final `## References`.

**Key repo fact:** `commands/new-command.md` does NOT mandate `## Completion`. `Completion` appears exactly once (line 202, its own heading); the structure table at lines 136–143 has six rows and no Completion row. **The contract is missing, not unenforced** — Story 1 *creates* the mandate. Work size is unchanged (18 sections). Banned strings in commits/changelog: "template violation", "19 files", "unenforced". Note `13 of 32` (raw files, ADR/roadmap) and `13 of 31` (commands, this spec) are both correct — do not "fix" either.

**Scope addition (2026-08-11, @AdamSellke, contract block unchanged):** Story 1 also amends ADR-020 and the roadmap Phase 10 lines. Exact before/after text is in `spec.md` → Detailed Requirements → *ADR-020 and roadmap premise corrections* — use it verbatim. Do NOT re-decide ADR-020, and do NOT edit the sibling specs that repeat the premise (`governor-instrumentation` `spec.md:19`/`:49`, `loop-bounds` `spec.md:26`).

---

## For Review Agents

**Acceptance Criteria:**
1. 31 commands carry all three fields (2–4 `exit_criteria` entries each); `_preamble.md` untouched.
2. 7 agents carry all three fields, both carrier styles preserved unconverted.
3. 31 commands carry `## Completion` immediately before `## References`.
4. `new-command.md` mandates both the section and the fields for generated commands; stale frontmatter claim corrected.
5. Measured added lines ≤ 518 total, reported from `git diff --stat` (commands/ + agents/ only).
6. ADR-020 carries a dated `## Amendments` entry stating what was measured, when, by whom; Decision items 1–3 and the `13 of 32` row unchanged. Roadmap Phase 10 asserts no template violation; `wc -l` = 424; `git diff --numstat` added = deleted.

**Business Rules (the ones that decide PASS/FAIL):**
- **Swap test (BR1):** paste any field into a different command's frontmatter — if it stays plausible there, it is boilerplate. Rewrite.
- **Restatement test (BR2):** `exit_criteria` may never restate `description:`. Banned: "the command completes successfully", "the report is generated", "the user is informed", "the output is correct", any criterion whose verb is the command's own name.
- **Observable required (BR3):** every criterion names a file path, field value, count/comparison, process outcome, or command-observable state. Present-tense assertion about post-run state. `<placeholders>` are fine.
- **Line budget (BR4):** 7 frontmatter lines/command (hard), 7 config lines/agent (hard), 14 lines per NEW `## Completion` (hard — incumbents run 12–18, median 15–16). Aggregate 518 = 31×7 + 7×7 + 18×14. Hitting the ceiling on every file is evidence the swap test was skipped.
- **One line each (BR5):** `problem`/`outcome` are single sentences. No block scalars, no lists, no continuations.
- **No carrier normalization (BR6).**
- **No contradiction (BR7):** frontmatter = machine-checkable summary, `## Completion` = human elaboration. Where a Completion section already exists, derive `exit_criteria` FROM it.
- **No eval checks (BR9):** zero edits to `scripts/eval*.py` or `scripts/eval.sh` — `2026-08-11-governor-instrumentation` owns enforcement.
- **No substance rewrite (BR10):** additive only. Scoping defects the audit surfaces get recorded in story notes, not fixed here.

---

## For Testing Agents

There is no application code and no test suite. Verification is structural.

**Success Criteria:**
1. `grep -c '^problem:' commands/*.md` → 1 for all 31 commands, 0 for `_preamble.md`.
2. `grep -l '^## Completion' commands/*.md | wc -l` → 31.
3. All 7 `agents/*.md` contain `problem:`/`outcome:`/`exit_criteria:` inside their existing fence; `agents/visual-qa-agent.md` still has `## Agent Specification` and ` ```yaml `; the other 6 still have `## Agent Configuration` and a plain fence.
4. `bash scripts/eval.sh` → no new findings vs. the pre-spec baseline.
5. `bash scripts/check-agent-parity.sh` → still "parity OK".
6. `git diff --stat` added-line total ≤ 518 across `commands/` + `agents/`; no single command over 7 frontmatter lines or 14 new `## Completion` lines. The ADR-020 / roadmap edits are outside this budget.
7. **Swap-test spot check:** draw 10 `exit_criteria` entries from 10 different commands, paste each into a different command — every one must read as false or nonsensical there.
8. `grep -n 'template violation\|19 file\|already mandating' .writ/product/roadmap.md` → no output; `wc -l .writ/product/roadmap.md` → 424; `sed -n '341p;343p'` still shows the lines `2026-08-11-retire-dead-prescription` cites; `grep -n '^## Amendments' .writ/decision-records/adr-020-component-contract.md` → one hit.

**Edge Cases:**
- `_preamble.md` has `disable-model-invocation: true` and a frontmatter terminator at line 5, not 4 — excluded entirely.
- The 6 plain-fence agent blocks are not valid YAML today (`model: default (inherits from parent)`). Appending is fine; do not "fix" them.
- `new-command.md` gets its own contract in Story 1 as the worked exemplar, so it is absent from Stories 2–5's batches.
- 17 of the 18 Completion-section files are also edited by Stories 2–5 — Story 6 is sequenced after them to avoid merge conflicts.

**Anti-goal to watch for:** fields that are present and informationally empty. That state passes every automated check the next spec will build. Criteria 6 and 7 are the only defenses.
