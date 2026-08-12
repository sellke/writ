# Progressive Disclosure — /create-spec (Lite)

> Source: .writ/specs/2026-08-12-disclosure-create-spec/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `commands/create-spec.md` (46,423 B / 871 lines) → thin contract ≤ **24,960 bytes**, procedure extracted to 5 new `skills/<name>/SKILL.md`, each reached by an **inline `Read skills/<name>/SKILL.md` at the step that needs it**. ADR-021.

**MECHANISM RULING (maintainer, 2026-08-12) — read this before anything else.** `required_skills:` is an **eager** pre-load: `system-instructions.md` loads every declared skill *"before any phase work begins"*, and `adapters/claude-code.md:396` says the same. ADR-021 §12's "loaded on demand" is false of it. **This spec does not use the field.** Every extracted skill is inline-read at its point of need — genuinely conditional, and already the shipping pattern in seven commands including this one at line 765. `scripts/measure-invocation.py` was fixed for this (`e8f2a09`): **floor = base + command + eagerly-declared skills; ceiling = floor + inline-read skills.** The extraction map, the 5 names, the 19 pins, the 113-row inventory, and the Compression Ledger are all **unchanged** — only the load mechanism and the ceiling accounting change. Full record: spec.md § *Approved Scope Change*.

**Inherited from the pilot `2026-08-12-disclosure-implement-story`:** (a) ~~declare every extracted skill~~ — **REVERSED 2026-08-12.** Right under eager loading (curating understated the metric); backwards under conditional loading, where precise placement is the point. Each inline `Read` sits at the **narrowest step** that needs it; **hoisting one to the command preamble is forbidden** and re-creates the eager mechanism by hand. (b) The naming rules, documented in `.writ/docs/skills.md` → *Extraction Patterns*. (c) The ADR-021 amendment (byte instrument supersedes the 400-line cap) is authored by the pilot — read it, do not amend again.

**Three figures, all from `python3 scripts/measure-invocation.py --root . --command create-spec` (fixed tool):**
- **Floor:** `command_bytes ≤ 24,960` (`floor_bytes ≤ 49,920`), from 46,423 / 71,383. **`eager_bytes` must be 0.**
- **Worst-path ceiling:** `command_bytes + Σ(inline-read skills) ≤ 52,570` (`ceiling_bytes ≤ 77,530`). Corrected baseline: **77,530 = floor 71,383 + 6,147** for the existing `error-rescue-mapping` read at :765. The old "true worst case" figure is retired — the fixed tool's ceiling *is* that number.
- **≥ 1 realistic partial path**, as arithmetic. `ceiling_bytes` is an **envelope**, not a path: the tool sums every inline read and cannot know which are mutually exclusive. Story 6 names the maximal *reachable* path.

**Extraction map + load placement** (source lines in the 871-line file; one inline read each, no declaration):

| Skill | Source | Bytes | Inline read placed at | Reached when |
|---|---|---|---|---|
| `spec-source-prepopulation` | `--from-prototype` (100–171) + `--from-issue` (172–256) | 7,809 | Step 0, **after** the `--from-*` mode branch | `--from-prototype` / `--from-issue` only |
| `requirements-discovery` | Step 1.3 (307–390) + `## Example Usage` (787–865) | 9,062 | Step 1.3 | discovery runs |
| `contract-lock` | 1.3b (391–404, less the pinned line) + 1.4 (405–453) + 1.4b (454–483) | 4,243 | Step 1.3b — **before** 1.4b and the `--recommend` auto-lock | any contract proposal |
| `spec-package-authoring` | 1.5 (484–520) + 2.2 (529–545) + 2.3 (547–561) + 2.4/2.4b non-pinned + spec-lite template (598–718) | 6,905 | Step 1.5 (UI) or Step 2.2 | Phase 2 |
| `user-story-decomposition` | 2.5–2.8 (719–763) less the subagent dispatch | 2,474 | Step 2.5 | Phase 2 decomposition |
| `error-rescue-mapping` (incumbent, not extracted) | — | 6,147 | Step 2.8, line 765, **unchanged** | data-flow heuristic says include |

**Projected paths:** floor ~40,960 · `--recommend` rejected at the invocation matrix → **~40,960, zero reads, −43% vs today** · bare collaborative docs-only run → ~64,200 (4 of 6 reads) · `--from-issue` + data-flow worst path → ~77,460 after compression. **Note the contrast is at the rejection boundary:** a *successful* `--recommend` run reads the same four skills a collaborative run does.

Names are qualified deliberately: `user-story-decomposition` (sibling claims `phase-decomposition`), `spec-package-authoring` (`layout` is a noun; `what-was-built-authoring` is the shape precedent). **Run the collision protocol** — grep `.writ/manifest.yaml` `skills:` for the name **and its head noun** — before every `/new-skill`. First writer owns the name.

**THE WORST-PATH CEILING IS THE FAILURE MODE.** ~33,650 B of new skills (incl. ~650 B scaffolding each) + 6,147 B incumbent inline read + ~16,000 B command = ~80,760 against a 77,530 bar — **~3,200 over**. The overage is *unchanged* by the mechanism ruling: the same bytes moved across the floor/ceiling line on both sides. `sub-specs/technical-spec.md` → *Compression Ledger* identifies ~3,300 B of permitted contraction. Permitted: delete a worked example of a format specified elsewhere; collapse two near-identical blocks; replace a restated field list with a pointer. Not permitted: dropping a threshold, fallback, degradation path, or always/never clause. Shortfall → written justification (measured overage + compression attempted + maintainer decision), never a shaved skill.

**HARD REPO FACT — `scripts/eval.sh` pins 19 literals into `commands/create-spec.md`** (17 `require_literal`, 2 `forbid_literal`, `eval.sh:1644–1973`) and `check_recommended_spec_implementation` (`eval.sh:737–800`) **parses the markdown table** under `### Authoritative \`--recommend\` Invocation Matrix` and asserts 3 heading-order relations. **This spec may not edit `eval.sh`.** Therefore:
- **`## Recommended Mode` (31–99, 4,130 B) is NOT extracted.** Whole section stays. Contradicts the original scoping sketch; the measurement wins.
- Stays in the command: `## Required Artifacts`; the `spec-status.py` complete-family sentence (396); Step 2.4's `> **Dependencies:**` / `exact spec-folder IDs` / `Canonical complete-family spelling` / `Amends` rules (566–577); Step 2.4b's `supersession-writeback.py` invocation + never-blocks rule; Step 2.8's data-flow heuristic + `error-rescue-mapping` pointer; Step 2.6's parallel-subagent dispatch (`lint-skill.sh` rejects `Task(`).
- `skip specs with \`Status: Complete\`` and `grep -v archive` must stay **absent** from the command and from every skill.

**Preserve byte-identical:** frontmatter `problem:`/`outcome:`/`exit_criteria:` and `## Completion` (Phase 10 foundation). **Append nothing to the frontmatter** — no `required_skills:` block.

**`lint-skill.sh:52` rejects `Read skills/` INSIDE a skill body (no chaining).** Every inline read this spec introduces therefore lives in `commands/create-spec.md` and nowhere else — verified against the plan 2026-08-12. Cross-skill needs (Story 5 → Story 2's contract-format authority) stay prose references.

**Do NOT touch:** `scripts/eval.sh`, `scripts/eval-leanness.py`, `commands/_preamble.md` (93/95 lines), any other command, `MAX_SKILLS`, ADR-021. **Do NOT add `required_skills:`** — an implementer who adds it "for discoverability" moves every skill into the floor and inverts the result while every check still passes.

---

## For Review Agents

**Acceptance Criteria:**
1. `command_bytes ≤ 24,960`, `floor_bytes ≤ 49,920`, `eager_bytes == 0`, `command_lines ≤ 400`.
2. `ceiling_bytes ≤ 77,530` (i.e. `command_bytes + conditional_bytes ≤ 52,570`), reported with the floor **and** ≥ 1 measured partial path, **and** a statement of whether the maximal reachable path equals the tool's envelope; any overage carries the BR1 written justification.
3. 5 skills, `status: candidate`, named per the inherited convention with collision checks recorded, lint-clean, manifested, `gen-skill.sh --check` clean.
4. **No `required_skills:` block exists** (`grep` returns nothing); `eager_skills: []`; `conditional_skills` holds the five new names + `error-rescue-mapping`; `unresolved_skills` empty; no "loads both ways" warning; `grep -c 'Read skills/' commands/create-spec.md` == 6, **each hit inside the step named in § Load placement** (no tool checks placement — read the line numbers).
5. `bash scripts/eval.sh` — zero new findings; 19 pins pass; matrix scenario passes 8 rows + 3 ordering asserts; neither `forbid_literal` string in the command or any skill.
6. All 113 rule-inventory rows reconcile **both directions**.
7. `## Recommended Mode`, `## Completion`, and the three frontmatter contract fields diff clean against the base commit.
8. `skills/` count (expect 19) reported against `MAX_SKILLS 12`; `skills` growth recorded as a **bound justification** in `.writ/leanness-baseline.json`, not `--update-baseline`.

**Business Rules (decide PASS/FAIL):**
- **BR1** floor, worst-path ceiling, and ≥1 partial path all reported; ceiling may not regress; overage needs measured evidence, not "only 4% worse".
- **BR2 relocate, don't redesign** — verified against the 113-row rule inventory. Compression removes words, never rules.
- **BR3 narrowest placement, no hoisting** (reverses inherited pilot BR8). Each skill inline-read inside the step that needs it; a read hoisted to the preamble is a defect *even though every automated check passes*. The hardest constraint is now satisfied by **ordering**: `contract-lock` is read at 1.3b, strictly before the 1.4b gate and the `--recommend` auto-lock.
- **BR4 contract-lock verbatim** — Step 1.4b's 5 options (`yes`/`edit`/`risks`/`blueprint`/`questions`), same ids, labels, handlers. Phase 2 reachable only via `yes` or `--recommend` auto-lock.
- **BR5 `--recommend` does not move or thin** — no auto-adopt entry, pause condition, or matrix row relocated, reworded, reordered, added, or removed.
- **BR6** 19 pinned strings survive in the command, never in a skill.
- **BR7** every skill reachable by **exactly one** inline read at its step — no declaration, no duplicate read on the same path.
- **BR8** `_preamble.md` untouched, cap not raised.
- **BR9** inherited naming + collision protocol; first writer owns.
- **BR10** one command file; no `scripts/` edits.
- **BR11** Phase 10 foundation byte-identical.
- **BR12** `error-rescue-mapping` stays **inline** at :765 — not re-extracted, not promoted to a declaration. **Strengthened by the 2026-08-12 ruling:** declaring it would move 6,147 B from `conditional_bytes` into `floor_bytes`, and a docs-only run — where the data-flow heuristic says *skip* — would pay them for nothing. Left inline, **a docs-only run's ceiling equals its floor.** It is not a leftover to tidy; it is the pattern the whole spec now adopts.
- **BR13** `skills` growth gets a bound justification, not silence and not `--update-baseline`.

**Preserve existing inconsistencies, do not fix:** "5-7 tasks" (Step 2.5, `## Completion`) vs "no more than 7" (`exit_criteria`). `--from-issue` is documented at line 175 but missing from `## Invocation` — Story 6 adds the row as documentation completion and says so.

---

## For Testing Agents

No application code. Verification is structural and byte-measured.

**Success checks:**
1. `python3 scripts/measure-invocation.py --root . --command create-spec --format table` → `command_bytes ≤ 24,960`; `eager_bytes == 0`; `command_bytes + conditional_bytes ≤ 52,570`.
2. `bash scripts/eval.sh` → no new findings vs pre-spec baseline. Targeted: `--check=length`, `=recommended-spec-implementation`, `=artifact-integrity`, `=spec-status`, `=supersession-writeback`, `=preamble`.
3. `bash scripts/lint-skill.sh skills/*/SKILL.md` → pass for all; `bash scripts/gen-skill.sh --check` → no delta.
4. `python3 scripts/eval-leanness.py --root .` → `required_skills_declarations: 0` for this command **with no finding** (`check_required_skills` reads frontmatter only and is silent on zero); `skills` ceiling warning recorded not silenced. Unresolved inline-read names are caught by `measure-invocation.py`'s `unresolved_skills`, **not** by leanness.
5. `grep -n 'skip specs with \`Status: Complete\`'` and `grep -n 'grep -v archive'` → no output against the command **and** all five skills.
6. Two frozen-region `diff`s vs the base commit (`## Recommended Mode`, `## Completion`) → empty. Re-anchor the first if the following heading changed, and state the anchor used.
7. `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` → `status: ok`, `2026-08-12-disclosure-implement-story` resolving.

**Shadow paths** (rewritten 2026-08-12 — each is now a statement about which reads are issued): standard run (**`spec-source-prepopulation` never read** — mode branch not taken; 7,809 B not paid, where the superseded eager design paid them every time) · invocation rejected at the `--recommend` matrix (**zero reads**, floor only — every read sits downstream of that gate) · `--recommend` with no idea and no candidate (pauses after `requirements-discovery`, before `contract-lock`; auto-lock cannot fire) · `--from-issue` bad path (`spec-source-prepopulation` read at Step 0, then its error block; issue file untouched) · `--from-prototype` clean tree (warning + bounded offer, same skill) · docs-only spec (`error-rescue-mapping` never read — **ceiling equals floor**). The "harness ignores `required_skills:`" path is **retired**: the field is not used, and an inline `Read` is an ordinary file read every adapter implements.

**Edge cases:** table reformatting breaks the matrix parser → matrix is byte-frozen · a "tidied" threshold is a behavioral change · a name that collides with a sibling's head noun must declare the incumbent, not fork it · `.writ/manifest.yaml` is also edited by `2026-08-11-retire-dead-prescription` (`version:` + `commands:`) and by the pilot (`skills:`) — append and re-run `gen-skill.sh`.

**Anti-goals:**
1. A file that hits 24,960 bytes by deleting rules instead of relocating them. That passes every byte check and every eval pin. The 113-row rule inventory is the only defense, and it must be reconciled row by row in both directions, not sampled.
2. **A file whose inline reads all sit near the top.** Byte-identical `ceiling_bytes`, byte-identical `floor_bytes`, every check green — and every run pays every skill, which is the eager mechanism the 2026-08-12 ruling rejected, rebuilt by hand. Placement is checked by reading line numbers against § *Load placement*; nothing automates it.
