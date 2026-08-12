# Progressive Disclosure — `implement-story` (Lite)

> Source: .writ/specs/2026-08-12-disclosure-implement-story/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `commands/implement-story.md` (52,709 bytes / 989 lines — the largest command file in Writ) reduced to a thin contract, with per-phase procedure extracted to 8 `skills/<name>/SKILL.md` files, each loaded by an inline `Read skills/<name>/SKILL.md` at the step that needs it. Pilot for five sibling disclosure specs.

> **Mechanism ruling — maintainer, 2026-08-12** (spec.md → *Approved Scope Change*; the locked Contract block still says `required_skills:` and is superseded on that point). `required_skills:` is an **eager** pre-load: `system-instructions.md` loads it *"before any phase work begins"*, `adapters/claude-code.md:396` the same. Static array ⇒ selection is per **command**, never per **run**. **It is not used by this spec.** The inline form is genuinely conditional — the agent issues the `Read` only if execution reaches it — and already ships in 6 commands / 44,580 measured bytes (`implement-story.md:525` → `tdd-cycle` among them). `scripts/measure-invocation.py` was fixed the same day (`e8f2a09`): declared skills → `eager_bytes` → **floor**; inline reads → `conditional_bytes` → **above** floor; both mechanisms on one skill **warns** and the declaration wins.

**Three numbers, from `python3 scripts/measure-invocation.py --root . --command implement-story`:**
- **Floor (binds):** `command_bytes ≤ 24,960` (from 52,709); `eager_bytes` must be **0**. Budget = the irreducible shared base (`system-instructions.md` 20,153 + `_preamble.md` 4,807). A command may not cost more to load than the contract it runs inside.
- **Full-path ceiling (binds):** `ceiling_bytes ≤ 83,770` — the **corrected** baseline (77,669 floor + 6,101 `tdd-cycle`). **Never quote 77,669.** Projected ~87,231, misses by ~3,461 (+4.1%). Close it with the Compression Ledger or escalate for a written maintainer justification. Never by deleting rules.
- **`--quick` ceiling (reported, derived by hand):** projected **~78,861** vs **83,770** paid today — **−5.9%**. This contrast is the spec's proof the mechanism works. `measure-invocation.py` does not model paths; subtract the measured `wc -c` of the skipped gates' skills and show the derivation.

**The 8 skills** (`/new-skill`, born `status: candidate`, clean on `lint-skill.sh`). The **read site** is as load-bearing as the content — it decides which runs pay:

| Skill | Source lines | Bytes | `Read` sits at | On `--quick`? |
|---|---|---|---|---|
| `story-context-assembly` | 95–220 (hints, knowledge, spec-lite sectioning) | ~6,720 | Step 2 | yes |
| `dependency-context-loading` | 221–340 | ~4,772 | Step 2, dependency branch | only with deps |
| `what-was-built-authoring` | 670–733, 842–956 | ~6,198 | Step 4 item 4 (**not** Gate 3.5) | yes |
| `boundary-map-computation` | 436–519 | ~5,708 | **Gate 0.5** | **no** |
| `change-surface-classification` | 571–593 | ~1,646 | Gate 2.5 | yes (2.5 is not skipped) |
| `drift-triage` | 623–669 | ~1,769 | **Gate 3.5 § A** | **no** |
| `project-context-snapshot` **(shared: implement-spec, status)** | 341–396 | ~1,848 | Step 4 item 3 (**not** Step 2) | yes |
| `story-commit-provenance` | 829–841 | ~1,375 | Step 4 item 7 | yes |

`tdd-cycle` is a 9th conditional read, already at Gate 1 (`:525`, 6,101 B). Not extracted, not moved, but counted in every ceiling.

**Not extracted:** the two `STATUS: BLOCKED` `AskQuestion` blocks (L533–551, L754–771). Orchestration belongs to the command under ADR-009 — collapse them into one parameterized block in place.

**Command keeps:** frontmatter (**byte-identical, nothing appended** — the frontmatter diff vs `<base>` is now expected to be *empty*), `## Overview`, `## Required Artifacts`, `## Invocation`, a phase table replacing the 2,021-byte ASCII diagram (it **names** skills, never `Read`s them), Steps 1–4 numbered lists, the per-agent routing table, gate contract stubs, `## Error Handling`, `## Quick Mode`, `## Completion` (byte-identical), `## References` + 8 skill links.

**Also lands:** ADR-021 `## Amendments` (2 entries — instrument lines→bytes; **the mechanism correction**: :12's "on demand" vs :18's eager `required_skills:`, and that :54–58 picked it partly because the convention needed a consumer) and the skill naming convention into `.writ/docs/skills.md` → Extraction Patterns.

**Finding this spec must surface, owner unassigned:** `system-instructions.md`'s `required_skills:` **Status: adopted** paragraph and `adapters/claude-code.md:396` both name Phase 10 progressive disclosure as the convention's first consumer. That becomes false; `required_skills_declarations` stays **0** forever. Neither file is in this spec's file set — record, do not edit.

---

## For Review Agents

**Acceptance Criteria:**
1. `command_bytes ≤ 24,960`, `floor_bytes ≤ 49,920`, `eager_bytes = 0`, `ceiling_bytes ≤ 83,770` — or a written justification naming the measured overage, the compression attempted with its yield, and explicit maintainer acceptance. Plus a derived `--quick` ceiling below both the full ceiling and 83,770.
2. 8 `SKILL.md` files, all `status: candidate`, `lint-skill.sh` clean, named per the convention.
3. `eager_skills` = `[]`, `conditional_skills` = 9 (8 + `tdd-cycle`), `unresolved_skills` = `[]`, no both-mechanisms warning.
4. No-drift inventory matches 1:1 — zero unaccounted removals.
5. `eval.sh` no new findings; `eval-loop-bounds.py` no new SKIPs; `gen-skill.sh --check` passes.

**Business Rules (the ones that decide PASS/FAIL):**
- **BR1 — report floor, full-path ceiling AND `--quick` ceiling; the full-path ceiling may not regress past 83,770.** "Only 4% worse" is not a justification, and a `--quick` saving does not buy off a full-path regression.
- **BR2 — relocate and contract, never redesign.** Verified by the no-drift inventory. *Permitted contraction:* deleting an example of a format specified elsewhere, collapsing byte-identical blocks, replacing a restated field list with a pointer. *Not permitted:* dropping a degradation row, threshold, fallback, or an always/never clause.
- **BR3 — naming convention:** kebab-case noun phrase, 2–3 words, ≤30 chars; `<object>-<operation>`; **never named after command, gate, or step**; `description:` is a bare-imperative verb phrase; a shared skill carries no consumer vocabulary; collision protocol — grep `.writ/manifest.yaml` for the name and its head noun first, inline-read an existing skill rather than fork it.
- **BR4 — every extracted skill must be reachable exactly once:** one inline `Read` AND a phase-table row naming it at that gate. Unreferenced = the surface got worse; read twice = the `--quick` derivation is wrong.
- **BR5 — 11 literals are pinned in this file by `eval.sh`** (:2134, :2137–2141, :2721–2722, :2727, :2787–2788) and 2 regexes by `eval-loop-bounds.py:485,488`. All stay in the command. 2 `forbid_literal` strings stay absent from the command **and** all skills.
- **BR6 — `_preamble.md` is 93/95 lines. Not the escape valve, cap not raised** (`2026-08-11-autonomy-gate-classes` owns it).
- **BR7 — zero edits to `scripts/eval.sh` and `scripts/eval-leanness.py`.** Only permitted `scripts/` write: comment-only pointer fixes in `eval-story-context.py:32,436,442`.
- **BR8 — placement is the mechanism.** Each inline `Read` sits at the **narrowest** step/gate that needs its skill. A `Read` hoisted into frontmatter, `## Overview`, `## Invocation`, the phase table, or anything above `### Step 1` is **forbidden** — every run reaches it, so it is an eager load in conditional syntax. No `required_skills:`; never both mechanisms for one skill; one `Read` per skill. *(Supersedes the old "declare all, don't curate", which was right only under eager loading.)*
- **BR9 — `skills` surface growth gets a bound justification** in `.writ/leanness-baseline.json` (baseline 932 lines / 41,620 chars, no justification today). Never `--update-baseline`.
- **BR10 — skill bodies must pass `lint-skill.sh` as capability prose.** No `Read commands/`, `Read skills/`, bare `Task(`, or line-initial `/command` outside fences. Agent-spawn and `AskQuestion` language stays in the command. **`lint-skill.sh:52` forbids `Read skills/` inside a skill**, so all 9 inline reads live in the command and nowhere else — skills do not chain.

---

## For Testing Agents

No application code, no test suite. Verification is structural.

**Commands:**
1. `python3 scripts/measure-invocation.py --root . --command implement-story --format table` — floor, full ceiling, `eager_bytes = 0`; then derive the `--quick` ceiling by subtracting `wc -c` of `boundary-map-computation` + `drift-triage`.
1b. `grep -n 'Read skills/' commands/implement-story.md` — 9 lines, no duplicates, **none above `### Step 1`**. `grep -RF 'Read skills/' skills/` — no output.
2. `grep -Fq` each of the 11 pinned literals in `commands/implement-story.md` — all present.
3. `grep -RF` both `forbid_literal` strings across `commands/implement-story.md` and `skills/` — no output.
4. `python3 scripts/eval-loop-bounds.py | grep -E 'drift-review-cycle|drift-testing-cycle'` — no new SKIP. The body must still contain `Max 3 iterations across review` and `2 fix iterations max`.
5. `bash scripts/lint-skill.sh skills/*/SKILL.md` — all clean; 14 files at `status: candidate`/`proven`.
6. `bash scripts/eval.sh` — no new findings vs. pre-spec baseline. `bash scripts/gen-skill.sh --check`. `python3 scripts/spec-deps.py validate --specs-dir .writ/specs`.
7. **Graceful-degradation probe on the mechanism used:** insert `Read skills/deliberately-missing-skill/SKILL.md` at a real step; `measure-invocation.py` must warn, list it in `unresolved_skills`, and exit 0. Revert. `eval-leanness.py`'s `check_required_skills` reads frontmatter only and **cannot** be exercised — record that, do not add a declaration to make it pass. If a harness hard-fails, **surface it** — a finding for ADR-021's 2026-11-11 review trigger.
8. `git diff --name-only | grep '^scripts/'` — empty, or only `eval-story-context.py` comments.

**Edge cases:** `--quick` skips Gates 0/0.5/3/3.5/5 but only **2** of them carry a skill (Gate 0/3/5 are agent spawns) — do not report "5 gates" as "5 skills saved" · `--quick` still writes the minimal WWB record, so that skill is read at Step 4 · `--review-only` skips Gate 1 too, so `tdd-cycle` is unread and `boundary_map` is the literal `(none)` · `/prototype` never runs this pipeline and gains no read · legacy spec-lite without `## For {Role} Agents` falls back to full content · missing `.writ/knowledge/` is a **silent** no-op, not a warning · reverted WWB records are skipped with a specific `ℹ️` line · mixed drift pauses for Large while still auto-amending Small.

**Anti-goal:** a file that hits 24,960 bytes by losing rules. The budget is trivially satisfiable by deleting behavior, and nothing automated would notice. The no-drift inventory is the only defense, and it must actually be walked.
