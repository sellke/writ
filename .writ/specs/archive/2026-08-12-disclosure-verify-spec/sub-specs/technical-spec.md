# Technical Spec: Progressive Disclosure — `/verify-spec`

> Source: `.writ/specs/2026-08-12-disclosure-verify-spec/spec.md`

All measurements taken 2026-08-12 against this working tree on branch `phase/10-progressive-disclosure`, at `commands/verify-spec.md` = 32,110 bytes / 732 lines.

## Measurement Instrument

`scripts/measure-invocation.py` is new, **and it was fixed on 2026-08-12 (`e8f2a09`) after this spec was authored.** It had treated `required_skills:` as a conditional load and excluded it from the floor. It is eager. The corrected model, which is also the model the maintainer's mechanism ruling adopts:

```
floor   = base + command + eagerly declared skills   always paid
ceiling = floor + inline-read skills                 worst-case path
```

Pre-spec, for `verify-spec`, re-measured against the fixed tool — **unchanged, because the command declares nothing and reads no skill inline today**:

```json
{"command_bytes": 32110, "command_lines": 732, "base_bytes": 24960,
 "eager_bytes": 0, "floor_bytes": 57070, "conditional_bytes": 0,
 "ceiling_bytes": 57070, "eager_skills": [], "conditional_skills": [],
 "resolved_skills": [], "unresolved_skills": [], "base_share_of_floor": 0.4374}
```

Base decomposes as `system-instructions.md` 20,153 + `commands/_preamble.md` 4,807 = **24,960**. That figure is the spec's floor budget: *a command file may not cost more to load than the shared contract it runs inside*.

**Three facts about the script the implementer must not mis-read.**
1. `conditional_bytes` counts **inline `Read skills/<n>/SKILL.md` calls in the body**, frontmatter excluded — which is exactly the mechanism this spec adopts. `eager_bytes` must stay `0`.
2. **It sums every inline read regardless of reachability.** It cannot know `--product` and the default path are mutually exclusive, so `ceiling_bytes` is an **envelope**, not a path anyone walks.
3. Its `*_tokens_estimated` fields are `bytes / 4.0` and are marked `token_method_validated: false`; no tokenizer is installed, so every token figure is an order-of-magnitude estimate and must never be quoted as a measurement. And it always exits 0 — a read-only measurement never blocks a caller, so a green exit proves nothing about the budget. Read the JSON.

It also emits a warning when a skill is **both** declared and inline-read (*"the declaration wins … the inline Read buys no conditionality. Drop one."*). That warning must never appear for `verify-spec`.

**Ceiling arithmetic.** `ceiling_bytes = 24960 + command_bytes + Σ(inline-read skill bytes)`. Holding `ceiling_bytes ≤ 57,070` is exactly `command_bytes + Σ(skill bytes) ≤ 32,110`: **the sum of the parts may not exceed the whole.** Unchanged by the ruling.

## Why the Ceiling Was Paid Every Run, and Why It No Longer Is

`system-instructions.md` § *`required_skills:` frontmatter convention* specifies the harness contract:

> *"When a consumer with `required_skills: [foo]` is invoked, the harness loads `skills/foo/SKILL.md` (typically via `Read skills/foo/SKILL.md`) and makes it accessible to the agent before any phase work begins."*

`adapters/claude-code.md:396` says the same: the harness issues those reads *"before the consumer's first phase begins."* There is no conditional, lazy, or mode-scoped form. Under that mechanism `/verify-spec --product` would have loaded `spec-metadata-diagnosis` and `/verify-spec --check` would have loaded `product-doc-audit`; `conditional_bytes` would have been paid unconditionally, and `floor_bytes` would have been a number nobody pays.

**The maintainer verified and accepted that finding on 2026-08-12 and ruled the mechanism out.** The standing alternative `system-instructions.md:250` documents is used instead:

> *"Without the field, agents and commands continue to inline `Read skills/<name>/SKILL.md` instructions in their prompts at the point where the skill is needed."*

That form is genuinely conditional — the agent issues the call only if execution reaches the step — and seven shipping commands already use it. The mode-aligned skill split this spec chose *for a hypothetical future* is what makes the saving real **today**:

| Path | Inline reads issued | Projected bytes |
|---|---|---:|
| Floor — before any branch | none | ~32,860 |
| `--product --check`, no `.writ/product/` | `product-doc-audit` | ~37,260 |
| `--product` full run | `product-doc-audit`, `derivative-regeneration`, `verification-report-authoring` | ~45,460 |
| `--check` — read-only, no regeneration | `spec-metadata-diagnosis`, `verification-report-authoring` | ~50,060 |
| **Default full run — maximal reachable** | `spec-metadata-diagnosis`, `derivative-regeneration`, `verification-report-authoring` | **~52,660** |
| *tool envelope — all four, unreachable* | all four | ~57,060 |

`spec-metadata-diagnosis` (≤ 11,600) is never read under `--product`; `product-doc-audit` (≤ 4,400) is never read on a default run. **That is the entire per-path saving, and it exists only because of where the two reads sit** (spec BR14). The compression requirement is unchanged: Σ ≤ 24,200 remains the bar Business Rule 1 checks, because it is what a tool can check and because a bar redrawn at the reachable path would be a bar chosen after the fact.

## The Byte Ledger

| Lines | Section | Bytes | Lines | Destination |
|---|---|---:|---:|---|
| 1–15 | frontmatter incl. `loop:` | 1,729 | 15 | command (verbatim), **nothing appended** — no `required_skills:` (2026-08-12 ruling) |
| 16–24 | title + `## Overview` | 502 | 9 | command |
| 25–37 | `## Modes` + `--product` boundary note | 1,386 | 13 | command, renamed `## Invocation` |
| 38–110 | Phase 1 discovery + load + JSON model | 2,408 | 73 | `spec-metadata-diagnosis` |
| 112–122 | Phase 2 header + mode behavior | 433 | 11 | `spec-metadata-diagnosis` |
| 124–155 | Check 1 story file integrity | 784 | 32 | `spec-metadata-diagnosis` |
| 157–180 | Check 2 status consistency | 609 | 24 | `spec-metadata-diagnosis` |
| 182–211 | Check 3 completion integrity | 903 | 30 | `spec-metadata-diagnosis` |
| 213–260 | Check 4 dependency validation | 2,053 | 48 | `spec-metadata-diagnosis` |
| 262–280 | Check 5 deliverables checklist | 532 | 19 | `spec-metadata-diagnosis` |
| 282–299 | Check 6 contract vs implementation | 567 | 18 | `spec-metadata-diagnosis` |
| 301–352 | Check 7 spec-lite integrity | 2,897 | 52 | split three ways (below) |
| 354–389 | Check 8 spec owner field | 1,321 | 36 | `spec-metadata-diagnosis` |
| 391–444 | Phase 3 console report | 2,479 | 54 | `verification-report-authoring` |
| 446–485 | Phase 4 auto-fix 4.1–4.4 + bound | 2,235 | 40 | split (below) |
| 487–541 | Phase 5 report file | 1,720 | 55 | `verification-report-authoring` |
| 544–702 | `--product` P1–P4 + mechanics + report | 7,744 | 159 | split (below) |
| 704–718 | `## Integration with Writ` | 1,081 | 15 | 3 rows → `## References`; 3 rows dropped |
| 719–727 | `## Completion` | 541 | 9 | command |
| 728–733 | `## References` | 166 | 6 | command, extended |

Sum of the table: 32,090; file total 32,110 (the delta is the `---` rules and blank lines between sections). **Retained source = 4,324 bytes.**

### The three-way splits

**Check 7 (2,897 bytes)** — the section mixes three concerns:
- Purpose, skip rule, section-mapping table, heading normalization, material-divergence criteria (~1,900) → `spec-metadata-diagnosis`
- *Report shape for Check 7* fenced block (~350) → `verification-report-authoring`
- *`--fix` behavior* + the auto-fixable disposition blockquote (~650) → `derivative-regeneration`, with the disposition sentence **also** restated in the command's phase-list row (dispositions are contract, not procedure)

**Phase 4 (2,235 bytes)**:
- 4.1 README sync, 4.2 deliverables sync, 4.3 status headers (~600) → `spec-metadata-diagnosis` (they are the repairs for checks 1/2/3/5)
- 4.4 spec-lite regeneration (~640) → `derivative-regeneration`
- The **Iteration bound** paragraph (~1,000) → **stays in the command.** It is the prose half of the preserved `loop:` block and names `autofix_pass`, the bound, `halt_reported`, and the resume command. Moving it separates a declaration from its explanation and puts the words "re-running Phase 2" where the `verify-spec-no-recheck-step` guard cannot see them.

**`--product` (7,744 bytes)**:
- Section intro + boundary paragraph + Inputs table + graceful skip + P1, P2, P4 + the P3 *check* (~4,600) → `product-doc-audit`
- *Auto-Fix Mechanics (Check P3 only)* + the never-touch-authoritative-prose paragraph (~1,300) → `derivative-regeneration`
- Report block + output path + two completion messages (~1,800) → `verification-report-authoring`
- The `## Product Consistency Checks (\`--product\`)` **heading itself stays in the command** (Business Rule 5)

## The Disposition Ledger

Business Rule 3's verification instrument. Story 1 transcribes it from `git show <base>:commands/verify-spec.md`; Story 5 rebuilds it from the thin command plus its skills and diffs. This table is the **expected** transcription — Story 1 verifies it rather than copying it, and a discrepancy between this table and the source file is resolved in favor of **the source file**.

| # | Heading (verbatim) | Sub-checks | Disposition as stated in source | Source locus |
|---|---|---|---|---|
| 1 | `Check 1: Story File Integrity` | 1a orphan, 1b phantom, 1c status header, 1d required sections | **unstated in source** — no disposition blockquote exists. Repairs 4.1/4.3 cover status and README sync; orphan/phantom have no stated fix. Preserve as unstated. | 124–155 |
| 2 | `Check 2: Status Consistency` | 2a README↔file sync, 2b task counts, 2c total progress | **unstated** as a blockquote; auto-fixed in default mode via 4.1 | 157–180 |
| 3 | `Check 3: Completion Integrity` | 3a acceptance criteria, 3b DoD, 3c tasks, 3d premature status | **unstated** as a blockquote; 3d auto-fixed via 4.3 | 182–211 |
| 4 | `Check 4: Dependency Validation` | 4a satisfaction, 4b cycles, 4c missing declarations, 4d cross-spec | 4a–4c **report-only in both default and `--check`**. 4d **blocking** (`malformed_dependencies`, `missing_reference`, `self_reference`, `dependency_cycle`) **except duplicates**, which auto-fix by first-occurrence-preserving dedupe. Executable reference: `scripts/spec-deps.py validate`. Overlap heuristics may only *warn* and may never reorder a valid explicit graph. | 213–260 |
| 5 | `Check 5: Deliverables Checklist (spec.md)` | 5a file existence, 5b spec status header | **unstated** as a blockquote; auto-fixed via 4.2 | 262–280 |
| 6 | `Check 6: Spec Contract vs Implementation` | Included / Excluded scope drift | **report-only in both modes — heuristic; may have false positives** | 282–299 |
| 7 | `Check 7: Spec-Lite Integrity` | section mapping, heading normalization, material divergence | **auto-fixable in default mode** (triggers regeneration). `--check`: report only. `--fix`: run and regenerate. **Skipped entirely** if `spec-lite.md` absent — no flag. | 301–352 |
| 8 | `Check 8: Spec Owner Field Presence` | ≥ 2026-04-24 requires owner; earlier is legacy | **warning/report-only by default.** Does not fail verification. Backfill only on explicit approval. Legacy: reported, never warned, never auto-fixed. | 354–389 |
| P1 | `Check P1: Phase-Status Parity (mission ↔ roadmap) — report-only` | mission Key Features ↔ roadmap phase status | **report-only.** Authoritative disagreement; `--product` never rewrites `mission.md` or `roadmap.md` prose. | 581–596 |
| P2 | `Check P2: ADR Reference Resolution — report-only` | `adr-0NN` ids in mission/roadmap/mission-lite | **report-only.** Do not auto-create. | 598–610 |
| P3 | `Check P3: Derivative Freshness — auto-fix (regenerate)` | `mission-lite.md`, `.writ/context.md` vs `mission.md` | **auto-fix in default `--product`.** `--product --check`: report only, regenerate nothing. Same materiality threshold as Check 7. | 612–628 |
| P4 | `Check P4: Shipped-Claim Sanity — report-only (heuristic)` | roadmap shipped claims vs spec folders / changelog | **report-only, heuristic.** High false-positive tolerance by design; never a failure. | 630–643 |

**Run order (also part of the ledger):** Phase 1 load → Phase 2 checks 1→8 collecting every finding before reporting → Phase 3 console report → Phase 4 auto-fix 4.1→4.4 (default only) → Phase 5 report file. `--product` is a **separate path**: P1→P4 collected, then P3 regeneration, then its own report to `.writ/product/verification-YYYY-MM-DD.md`.

## The Preserved `loop:` Block

Copied byte-identical. Its `calibrated_against` string asserts three things about the file that must remain true after extraction:

1. *"runs Phase 2 (checks 1-8) then Phase 4 (auto-fixes 4.1-4.4) then Phase 5 (report file)"* → the thin contract keeps Phases 1–5 with those numbers, checks 1–8 named under Phase 2, and steps 4.1–4.4 named under Phase 4.
2. *"contains no re-check, re-run, or re-verify step"* → Business Rule 7, extended to skills.
3. *"the only 'again' in the file describes `/release` invoking checks 1-8 through its own entry point"* → the `/release` relationship row must survive the removal of `## Integration with Writ`, which is why it is one of the three rows condensed into `## References`.

`scripts/eval-loop-bounds.py` also checks that path tokens inside `calibrated_against` resolve; `commands/verify-spec.md` continues to exist, so that check is unaffected.

### The guard's exact grammar

```python
structural = [line.strip() for line in verify_body.split("\n")
              if re.match(r"^\s*(#{2,4} |\d+\.\d* )", line)]
offenders = [line for line in structural
             if re.search(r"re-?(check|verify|run)", line, re.IGNORECASE)]
```

`verify_body` is the command **with frontmatter stripped**, so the `calibrated_against` string's own use of the words is deliberately invisible to it. Structural lines are `##`/`###`/`####` headings and lines beginning `N.` or `N.M `. The match is case-insensitive and unanchored: a heading `### Re-run the diagnostic` trips it; a prose sentence containing "re-run" does not. Skills are never read.

**Practical consequence for authoring:** the phase list may say `Phase 5: Verification Report File` but must never say anything like `4.5 Re-check after fixes`. In skills, the same prohibition applies by contract (Business Rule 7) with no automated backstop.

## Pinned Literals (`scripts/eval.sh`)

Six strings are pinned inside `commands/verify-spec.md` by tooling this spec may not edit. Four must **survive in the command file** — `require_literal` tests the command, never the command plus its skills. One must **stay absent**. One is pinned by nothing, which is why it is the most dangerous.

| String | Call | `eval.sh` line | Current locus | Minimum retained carrier in the thin contract |
|---|---|---:|---|---|
| `Cross-spec dependency validation` | `require_literal` | 1781 | `verify-spec.md:234` (`**4d. Cross-spec dependency validation:**`) | Check 4d's name in the Phase 2 gate list |
| `self-reference` | `require_literal` | 1782 | `:246` (4d blocking-finding list) | 4d's blocking findings named in the Phase 2 gate list |
| `story dependency validation is unchanged` | `require_literal` | 1783 | `:237` (4d's two-graph note) | The 4a–4c / 4d boundary sentence |
| `spec-lifecycle.md` | `require_literal` | 1901 | `:46` (Phase 1 `--all` prose) | The `--all` row's link to the archive-exclusion doc |
| `specs/**` | **`forbid_literal`** | 1902 | absent | Must stay absent — command **and** skills |
| `## Product Consistency Checks (\`--product\`)` | *(unchecked)* | — | `:544` | The heading itself, byte-identical (`plan-product.md:39` fragment link) |

The failure asymmetry is the point: four strings fail **loudly** through `check_spec_dependencies` and `check_spec_lifecycle_docs`, while the heading fails **silently** because `check_broken_refs` resolves paths and never fragments. An implementer who tests only with `eval.sh` will catch four of the five real hazards and miss the one that never comes back.

A skill may also carry these strings — nothing forbids duplication — but it may never carry them *instead*.

## Skills-Surface Growth

`.writ/leanness-baseline.json` records the `skills` surface at **932 lines / 41,620 chars** (recorded 2026-08-04, no justifications). Four skills at the Σ ≤ 24,200 allocation grow it by roughly **58%**, which raises an unjustified-growth warning in `eval-leanness.py`.

The disposition is a **bound justification** — the `(surface, metric)`-scoped `{date, value, text}` record built by `2026-08-11-governor-instrumentation` Story 1 — naming this spec, the bytes moved into `skills`, and the matching reduction in `commands`. `--update-baseline` is **not** used: it lifts every surface's floor at once and records no reason, which is the mechanism by which the four growth warnings ADR-021 complains about became invisible. The baseline file is data, not a script, so writing a justification is inside Business Rule 9.

## Cross-File Reference Surface

Verified by `grep -rn "verify-spec" commands/*.md agents/*.md adapters/*.md system-instructions.md README.md`:

| File:line | Cites | Risk |
|---|---|---|
| `commands/release.md:106-107` | *"checks 1–6 inline … same logic as the standalone command"*, auto-fix the same way | Renumbering breaks it; out of scope to repair |
| `commands/release.md:490`, `:554`, `:563` | checks 1–6, re-runs internally | Same |
| `commands/ship.md:335`, `:610` | *"checks 1–3 only … definitions identical to the standalone command"* | Same |
| `commands/plan-product.md:39` | `[…](verify-spec.md#product-consistency-checks---product)` — **the only fragment link into this file** | Deleting the heading breaks it **silently** (BR5) |
| `commands/plan-product.md:43`, `:66`, `:74`, `:106` | `--product` / `--reconcile` before-after discipline, Check P1 by number | Boundary note must survive in `## Invocation` |
| `commands/implement-spec.md:52` | *"the same single-level glob shape `commands/status.md` and `commands/verify-spec.md` use"* | After extraction the glob lives in a skill; the citation degrades to imprecise, not broken. Recorded, not fixed. |
| `commands/migrate.md:323` | *"checks 1–7"* | **Already stale** — Check 8 landed and this was never updated. Not fixed here (BR9). |
| `README.md:134` | checks 1–8, all eight named | Renumbering breaks it |
| `commands/retro.md:157`, `:170` | *"same bidirectional test as `/verify-spec`"*, `--product` vs `--reconcile` | Prose; unaffected |
| `adapters/claude-code.md:447` | `claude -p "/verify-spec --check"` | Invocation surface must not change |

**`check_broken_refs` (`scripts/eval.sh:362-392`)** extracts `](target)` from `commands/`, `agents/`, `adapters/`, `system-instructions.md`, and `SKILL.md`, then tests `[ -e "$resolved" ]`. It resolves the **path only**. A dangling `#fragment` is never reported. Business Rule 5 exists because nothing else enforces it.

## Skill Authoring Constraints

`scripts/lint-skill.sh` runs at authoring time via `/new-skill` and rejects, in the body:

| Pattern | Category | Bearing on this extraction |
|---|---|---|
| `Read commands/` | Command invocation | Extracted text must not tell the reader to open a command file |
| `Read skills/` (`lint-skill.sh:52`) | Skill chaining | The four skills may not reference each other; shared facts are stated where they are used or hoisted to the command. **This is why every inline read introduced by the 2026-08-12 mechanism ruling is placed in `commands/verify-spec.md` and never inside a `SKILL.md`.** Checked against this plan at amendment time: all six placements are in the command. The Check 7 → regeneration relationship is control flow the command sequences (its step 4.4 read is the load), not a skill loading a skill |
| `Task(` | Subagent dispatch | Not present in the source |
| `^/[a-z][a-z-]+` | Slash command | A line may not **begin** with `/verify-spec` or `/plan-product`. Source lines like `` **If `/verify-spec --spec [path]`:** `` begin with `**` and are safe; bare-slash line starts must be re-shaped |

Description shape is also linted: verb-phrase, no `Acts as` / `Is responsible for` / `The … agent` / `Run the full` / `Execute the entire`. Lifecycle vocabulary is closed — `status:` ∈ {`candidate`, `proven`, `promoted`}, earned from `evidence:` entries. New skills are born `candidate` with zero evidence, which is correct and must not be inflated.

**Frontmatter overhead is real budget.** `skills/tdd-cycle/SKILL.md`'s frontmatter is ~700 bytes; `## Purpose` and `## When to Use` together run ~1,300 more before any procedure. Budget ~1,400 bytes of unavoidable per-skill overhead — 5,600 across four skills — inside the Σ ≤ 24,200 allocation.

## Where the Compression Comes From

The ~27% reduction of extracted prose is not achieved by editing everything down 27%. It comes from three specific redundancies in the source:

1. **The regeneration procedure appears twice** (step 4.4 and `--product`'s *Auto-Fix Mechanics*, which opens *"Reuse default `/verify-spec`'s derivative-regeneration pattern"*). One skill states it once, with two instantiations: `spec-lite.md ← spec.md` and `mission-lite.md` / `.writ/context.md ← mission.md`. Saves ~900 bytes and closes a drift seam.
2. **The report shape appears three times** — the eight-row console table, the Phase 5 markdown file, and the product report that *"mirrors Phase 5's file"* with a P1–P4 table. One skill, one shape, three instantiations. Saves ~1,200 bytes.
3. **Phase 1's JSON data model is 2,408 bytes** wrapped around a six-item read list. The model illustrates a structure the agent builds anyway; a compact schema statement carries the same information. Saves ~1,000 bytes.

That is ~3,100 bytes of genuine redundancy. The remaining ~3,000 comes from ordinary tightening of prose that survived unedited since the file was written — which ADR-021 permits explicitly as *"a tactic within extraction, not the strategy."* Nothing in this list touches a check, a sub-check, a disposition, or a run-order fact.

## Verification Commands

```bash
# 0. Baseline (Story 1) — record and keep
BASE=$(git rev-parse HEAD)
git show $BASE:commands/verify-spec.md > /tmp/verify-spec.before.md
python3 scripts/measure-invocation.py --root . --command verify-spec > /tmp/measure.before.json

# 1. Budgets (Story 5)
python3 scripts/measure-invocation.py --root . --command verify-spec | \
  python3 -c 'import json,sys; d=json.load(sys.stdin)["commands"]["verify-spec"]; print(d["command_bytes"], d["eager_bytes"], d["floor_bytes"], d["conditional_bytes"], d["ceiling_bytes"], d["eager_skills"], d["conditional_skills"], d["unresolved_skills"])'
# command_bytes <= 24960 ; eager_bytes == 0 ; eager_skills == [] ;
# conditional_skills == the four names ; ceiling_bytes <= 57070 ; unresolved_skills == []
python3 scripts/measure-invocation.py --root . --command verify-spec | grep -i 'both ways'   # expect no output

# 1a. Load mechanism and placement (BR10, BR14) — no tool checks placement
grep -n 'required_skills:' commands/verify-spec.md    # expect NO output
grep -n 'Read skills/'     commands/verify-spec.md    # expect 6 hits, 4 distinct names
# Each hit must sit INSIDE its phase/check row per spec.md § The thin contract's shape:
#   spec-metadata-diagnosis      -> Phase 1            (NOT reachable under --product)
#   verification-report-authoring-> Phase 3  and  the product report
#   derivative-regeneration      -> step 4.4  and  Check P3 mechanics
#   product-doc-audit            -> the --product section  (NOT reachable on a default run)
# A hit above `## Command Process` is a hoisted read and a BR14 defect.

# 1b. Per-path arithmetic (BR1) — sum the skills each path's reads would issue
#   default full run (maximal reachable) = floor + diagnosis + regeneration + report
#   --product full run                   = floor + product-audit + regeneration + report
#   --check                              = floor + diagnosis + report
# Report each against the pre-spec 57,070 and state the gap to ceiling_bytes.

# 2. Fidelity — every check heading survives verbatim
grep -o '^#### Check [A-Za-z0-9: ()—-]*' /tmp/verify-spec.before.md | while read -r h; do
  grep -qF "$h" commands/verify-spec.md skills/*/SKILL.md || echo "LOST: $h"
done

# 3. Pinned literals — four must be present, one must be absent everywhere
for lit in 'Cross-spec dependency validation' 'self-reference' \
           'story dependency validation is unchanged' 'spec-lifecycle.md'; do
  grep -qF "$lit" commands/verify-spec.md || echo "MISSING require_literal: $lit"
done
grep -rF 'specs/**' commands/verify-spec.md skills/*/SKILL.md   # expect no output
grep -n '^## Product Consistency Checks' commands/verify-spec.md

# 4. No re-check step, command AND skills
grep -rEn '^\s*(#{2,4} |[0-9]+\.[0-9]* ).*re-?(check|verify|run)' \
  commands/verify-spec.md skills/*/SKILL.md   # expect no output
python3 scripts/eval-loop-bounds.py | grep verify-spec

# 5. Frontmatter preserved
git diff commands/verify-spec.md | grep -E '^[-+].*(calibrated_against|max_iterations|on_exhaustion|^problem:|^outcome:)'  # expect no '-' lines

# 6. Skills healthy
bash scripts/lint-skill.sh skills/*/SKILL.md
bash scripts/gen-skill.sh --check
grep -c 'status: candidate' skills/*/SKILL.md

# 7. Regression + scope
bash scripts/eval.sh
python3 scripts/spec-deps.py validate --specs-dir .writ/specs
git diff --name-only
```

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling |
|---|---|---|
| Extract checks 1–8 | A sub-check (e.g. 1d, 3d, 4c) is silently dropped as "minor" | Ledger diff (BR3) compares sub-check lists cell for cell, not check counts |
| Extract dispositions | An `unstated in source` disposition gets "helpfully" resolved | BR3's ambiguity clause; the ledger carries the literal string `unstated in source` and Story 5 asserts it is still there |
| Extract `--product` | P1–P4 get folded into checks 1–8 as "checks 9–12" | BR4 freezes the P-prefix; the source says twice that these are *not* spec checks pointed at product docs |
| Remove `## Integration with Writ` | `plan-product.md`'s anchor breaks, or the `/release` re-entry fact is lost | BR5 keeps the `--product` heading; the `/release` and `/ship` rows move to `## References` because `calibrated_against` depends on the first |
| Rename `## Modes` → `## Invocation` | An external link to `#modes` breaks | Verified: no file links to `verify-spec.md#modes` |
| Extract Check 4d | Three `require_literal` strings leave the command file | Phase 2's Check 4 gate row carries all three; Story 5 greps each before running `eval.sh` |
| Extract Phase 1 | The `spec-lifecycle.md` link leaves the command file | The `--all` row in `## Invocation` carries the link; same grep |
| Compress the `--all` prose | A rewrite introduces `specs/**` as a "clearer" glob | `forbid_literal` catches it in the command; nothing catches it in a skill, so the grep spans both |
| Author four skills | The `skills` surface growth warning is absorbed with `--update-baseline` | Bound justification instead, per BR13 — `--update-baseline` records no reason and moves every surface |
| Author a skill | `lint-skill.sh` rejects a line beginning with a slash command | Re-shape the line (BR12); deleting the content to pass the lint is a BR3 violation |
| Author a skill | Skill cross-references another skill (`Read skills/…`) | Lint rejects it. Hoist the shared fact to the command or restate it where used |
| Place an inline read | A skill name is misspelled | `measure-invocation.py` reports it under `unresolved_skills` and warns that the ceiling is a lower bound. **`eval-leanness.py check_required_skills` will NOT catch it** — it reads `required_skills:` frontmatter only, and there is none. `unresolved_skills` is the only detector, and Story 5 runs it |
| Place an inline read | It is **hoisted** to the command preamble "so the reader sees the skills up front" | Every run pays every skill; both mode exclusions vanish; `ceiling_bytes` is identical so nothing reports it. **No tool catches this.** BR14; Story 5 records each read's line number against § *The thin contract's shape* |
| Place an inline read | `required_skills:` is added back "for discoverability" | Skills move into `floor_bytes`, the 24,960 floor bar is blown, and the spec's result inverts | `grep -n 'required_skills:'` returns nothing; `eager_bytes == 0` |
| Place an inline read | A skill needed on two disjoint paths gets one read at their common ancestor instead of one per path | `--product` starts paying for `spec-metadata-diagnosis` again | BR10's one-read-per-path clause; the six-hit / four-name grep |
| Parallel skill stories | Two stories append to `.writ/manifest.yaml` and one entry is lost | Story 1 records the current `skills:` block; Story 5 runs `gen-skill.sh --check`; a lost entry also surfaces as an unresolved `required_skills` name |
| Measure the result | Only `floor_bytes` is reported and the ceiling rise goes unnoticed | BR1 requires floor, worst-path ceiling, **and** per-path figures; ADR-021 caveat 2 is cited by name in the story evidence |
| Measure the result | `ceiling_bytes` is reported as though a run pays it | It is an **envelope**: no invocation reaches all four skills, since `--product` and the default path are mutually exclusive. BR1 requires naming the maximal *reachable* path and the gap to the envelope |
| Compress prose | Compression reaches the checks themselves | Fidelity outranks both budgets (BR2 precedence). A written ceiling-rise justification is the correct outcome, not a thinner check |
| Preserve `loop:` | The phase list renumbers and `calibrated_against` becomes false while remaining byte-identical | BR8; Story 5 re-reads the citation against the new phase list as an explicit task |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| `spec-lite.md` absent | Check 7 **skips** — no flag, no failure — and row 7 is omitted from the report table with `(Check 7 skipped — no spec-lite.md found)`. Preserve exactly; a skip is not a pass. |
| `.writ/product/` absent | `--product` prints `No .writ/product/ found — nothing to verify. Run /plan-product first.`, exits with no error, writes nothing. |
| `.writ/context.md` absent | **Not** an error — it is a P3 regeneration target, created if missing. |
| Spec created before 2026-04-24 | Check 8 reports `legacy — owner not required`. Never a warning, never auto-fixed. |
| `--all` and `.writ/specs/archive/` | The single-level glob `.writ/specs/*/` excludes archived specs **by construction**; the source states explicitly that no `archive/` filter should be added. Preserve the reasoning, not just the glob. |
| Duplicate cross-spec dependency entry | The one 4d finding that auto-fixes — dedupe preserving first-occurrence order. Every other 4d finding blocks. |
| `--fix` without `--product` | Runs Check 7 only, then regenerates if diverged. It is not a full diagnostic and must not become one. |
| A future conditional `required_skills:` | Out of scope, and **no longer needed for this spec to pay off.** The 2026-08-12 ruling reaches conditionality through inline reads at the point of need, which `system-instructions.md:250` already documents and seven commands already ship. The mode-aligned skill split is what makes it pay off, and it pays off now rather than hypothetically. |
| Dependency spec created an equivalent skill | Reuse it, drop the allocation, and record the reuse in the story notes. Do not author a near-duplicate (BR11). |

## Non-Goals (restated from spec.md → Out of Scope)

No other command file. No `scripts/` changes of any kind. No `commands/_preamble.md` edit. No check redesigned, renumbered, or disambiguated. No re-check pass and no `loop:` change. No `--include-archived`. No skill promoted past `candidate` (except an ADR-014 `type: promotion` evidence entry added to a *sibling's* skill if the collision protocol requires declaring it). No sibling spec's skill edited or renamed. No conditional form of `required_skills:`. No repair of `commands/migrate.md:323`'s stale "checks 1–7", and no reconciliation of the ADR-021 / `new-command.md` template conflict.
