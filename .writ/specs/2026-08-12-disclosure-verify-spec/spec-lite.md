# Progressive Disclosure — `/verify-spec` (Lite)

> Source: .writ/specs/2026-08-12-disclosure-verify-spec/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `commands/verify-spec.md` (32,110 bytes / 732 lines) becomes a thin contract; per-check procedure moves to `skills/<name>/SKILL.md`, each reached by an **inline `Read skills/<name>/SKILL.md` at the step that needs it**.

**MECHANISM RULING (maintainer, 2026-08-12) — read this before anything else.** This spec's finding was right: `required_skills:` is an **eager** pre-load (`system-instructions.md` — *"before any phase work begins"*; `adapters/claude-code.md:396` — same). ADR-021 §12's "loaded on demand" is false of it. **The maintainer accepted the finding and changed the mechanism, not the budget: `required_skills:` is not used.** Each skill is inline-read at its point of need — genuinely conditional, already the shipping pattern in seven commands. `scripts/measure-invocation.py` was fixed for this (`e8f2a09`): **floor = base + command + eagerly-declared skills; ceiling = floor + inline-read skills.** The byte ledger, the 4 names and allocations, the disposition ledger, the frozen numbering, the 6 pinned literals, and the `loop:` block are all **unchanged**. Full record: spec.md § *Approved Scope Change*.

**Thin contract retains (ADR-021):** frontmatter (**nothing appended — no `required_skills:`**), `## Overview`, `## Invocation`, phase list with gate names **and the inline reads inside their steps**, `## Completion`, `## References`. Nothing else — `## Integration with Writ` is removed, its three load-bearing rows condensed into `## References`.

**Three figures, from `python3 scripts/measure-invocation.py --root . --command verify-spec` (fixed tool):**
- **Floor:** `command_bytes` ≤ **24,960** (down from 32,110), `eager_bytes` == **0**. Projected ~7,900 — easy.
- **Worst-path ceiling (the mechanical bar):** `command_bytes + Σ skill bytes` ≤ **32,110**, i.e. `ceiling_bytes` ≤ **57,070**. Unchanged, **including the ~27% compression it demands** — Σ ≤ 24,200 stays. Pre-spec baseline is 57,070 = floor, because this command has no inline read today.
- **Per-path figures (NEW, required):** `ceiling_bytes` is an **envelope**, not a path — the tool sums every inline read and cannot know `--product` and the default path are mutually exclusive. **No invocation reaches all four skills.**

**Projected paths** — this is where the win is: floor ~32,860 · `--product --check` w/ no `.writ/product/` ~37,260 · **`--product` full ~45,460** · `--check` ~50,060 · **default full run (maximal *reachable*) ~52,660** · tool envelope ~57,060. `spec-metadata-diagnosis` (≤11,600) is **never** read under `--product`; `product-doc-audit` (≤4,400) is **never** read on a default run. That ~4,400-byte gap below the envelope is the whole per-invocation saving, and it exists **only because of where the reads sit**.

**Skills (4) + load placement (BR14 — narrowest step, no hoisting)** — named per `2026-08-12-disclosure-implement-story` BR3 (kebab noun phrase, 2–3 words, ≤30 chars, `<object>-<operation>`, never named after the command). Collision-checked 2026-08-12 against the 6 incumbents and all 11 sibling-claimed names: clean.

| Name | Carries | Allocation | Inline read placed at |
|---|---|---:|---|
| `spec-metadata-diagnosis` | Phase 1 loading; Checks 1–8 + sub-checks + dispositions; repairs 4.1–4.3 | ≤ 11,600 | Phase 1 — **never reachable under `--product`** |
| `derivative-regeneration` | Regeneration discipline shared by 4.4 (spec-lite←spec.md) and P3 (mission-lite/context←mission.md) | ≤ 2,600 | step 4.4 **and** Check P3 mechanics |
| `product-doc-audit` | P1–P4, inputs table, graceful skip, `--reconcile` boundary | ≤ 4,400 | the `--product` section — **never reachable on a default run** |
| `verification-report-authoring` | Console table, findings detail, Phase 5 file, product report, 4 completion messages | ≤ 5,600 | Phase 3 **and** the product report |

**Six reads, four skills.** A skill needed on two disjoint paths gets one read **per path**, never one hoisted to their common ancestor — the tool dedupes names, so it costs nothing and it is the difference between `--product` paying 12,600 and paying 24,200. Allocations may be traded; **Σ ≤ 24,200** may not. Compression is possible because the source repeats itself: the regeneration procedure is written twice, the report shape three times, and Phase 1's JSON model is 2,408 bytes of scaffolding around a six-line read list.

**Files in Scope:** `commands/verify-spec.md` · the 4 new `skills/<name>/SKILL.md` · `.writ/manifest.yaml` (append-only, via `/new-skill`) · regenerated root `SKILL.md`. **Nothing else** — no other command, no `scripts/`, no `_preamble.md` (93/95 lines, cap owned by `2026-08-11-autonomy-gate-classes`). **Do NOT add `required_skills:`** — it moves all four skills into `floor_bytes`, blows the floor budget, erases both mode exclusions, and inverts the result while `ceiling_bytes` is unchanged and every check passes. **`lint-skill.sh:52` rejects `Read skills/` INSIDE a skill body (no chaining)**, so every inline read lives in `commands/verify-spec.md` and nowhere else — verified against the plan 2026-08-12; Check 7 → regeneration is control flow the command sequences (its step 4.4 read is the load), not a skill loading a skill.

---

## For Review Agents

**Business Rules (the ones that decide PASS/FAIL):**

- **BR1 ceiling + path report:** `ceiling_bytes` ≤ 57,070 (the envelope). A rise is not auto-fail but must be *written up* citing ADR-021 caveat 2 and naming what would have had to be cut. **Reporting floor only = fail. Reporting ceiling only = fail.** Three figures required: floor (`eager_bytes` == 0), worst-path ceiling, and per-path figures naming the **maximal reachable path** (~52,660, the default full run) and its gap to the envelope.
- **BR2 floor + precedence:** `command_bytes` ≤ 24,960. **fidelity > floor > ceiling.** 400 lines is a non-binding tripwire.
- **BR3 no redesign — the disposition ledger.** Story 1 transcribes every check (number, verbatim heading, sub-checks, run-order position, disposition) from `git show <base>:commands/verify-spec.md`. Story 5 rebuilds it from command + skills. **Must match cell for cell.** Where the source states no disposition (Check 1), the ledger says `unstated in source` and it stays unstated — **resolving an ambiguity is redesigning.**
- **BR4 numbering frozen:** checks 1–8, 1a–1d/2a–2c/3a–3d/4a–4d/5a–5b, steps 4.1–4.4, P1–P4 keep numbers and heading strings. `release.md:106` cites checks 1–6, `ship.md:335` cites 1–3, `README.md:134` cites 1–8 — all out of scope, so a break cannot be repaired.
- **BR5 pinned strings — the highest-risk rule.** `scripts/eval.sh` pins six literals in `commands/verify-spec.md`; `require_literal` tests the **command**, not command+skills, and `eval.sh` is out of scope.
  - Must be **present in the command**: `Cross-spec dependency validation` (:1781), `self-reference` (:1782), `story dependency validation is unchanged` (:1783) — all three inside Check 4d — and `spec-lifecycle.md` (:1901), in Phase 1's `--all` prose. Moving them into a skill = four blocking findings.
  - Must be **absent**, command and skills: `specs/**` (`forbid_literal`, :1902).
  - Must survive **byte-identical**: the heading `## Product Consistency Checks (\`--product\`)`. Nothing checks it — `plan-product.md:39` deep-links `#product-consistency-checks---product` and `check_broken_refs` resolves paths, never fragments. This is the one that fails silently.
- **BR6 hybrid boundary locked:** derivatives regenerated, authoritative files never written. `spec.md` never a target of Check 7 / 4.4. `mission.md` / `roadmap.md` never targets of `--product`. 4a–4c report-only; 4d blocking except duplicates (order-preserving dedupe); 6 report-only heuristic; 7 auto-fix in default; 8 warning-only, no backfill without approval; P1/P2 report-only; P3 auto-fix; P4 report-only heuristic.
- **BR7 no re-check step — in the command *or any skill*.** `eval-loop-bounds.py`'s `verify-spec-no-recheck-step` scans only the command's structural lines for `re-?(check|verify|run)`; a re-check hidden in a skill would pass the guard and still change the loop's shape. **This gap is extended into skills by contract with nothing enforcing it, and the 2026-08-12 mechanism ruling does not change that** — the guard does not read `skills/` at all, so it is indifferent to how a skill is loaded. Accepted, unchanged, still flagged for governor-enforcement. The hand-run grep over command + skills is the only substitute.
- **BR8 `loop:` preserved byte-identical** (`autofix_pass`, `max_iterations: 1`, `on_exhaustion: halt_reported`, full `calibrated_against`) plus `problem`/`outcome`/`exit_criteria`. The citation asserts Phase 2 = checks 1–8, Phase 4 = 4.1–4.4, Phase 5 = report file — so **Phase 1–5 numbering and 4.1–4.4 sub-numbering stay** in the phase list, or a preserved string becomes false.
- **BR9 ownership:** one command file + its skills. No `scripts/` edits. No `_preamble.md`.
- **BR10 reachability:** no declaration; every skill reached by a literal `Read skills/<name>/SKILL.md` **inside** the phase-list row whose detail it carries. `eager_skills` empty, `conditional_skills` = the four, `unresolved_skills` empty, no "loads both ways" warning. Two disjoint paths → **one read per path**.
- **BR14 placement is the mechanism (NEW):** narrowest step, **no hoisting**. `spec-metadata-diagnosis` must not be reachable under `--product`; `product-doc-audit` must not be reachable on a default run. A read hoisted to the preamble reports an identical `ceiling_bytes` and passes every check while restoring the eager behavior. **No tool checks placement** — Story 5's recorded line numbers are the only enforcement.
- **BR11 naming + collision protocol** (inherited from the dependency spec): grep the intended name **and its head noun** in `.writ/manifest.yaml` before `/new-skill`. If a sibling claimed the noun, **declare their skill** and add an ADR-014 `type: promotion` evidence entry — do not author a near-duplicate. First writer owns the name. 6 + 4 = 10 vs `MAX_SKILLS` 12 (warn-only).
- **BR13 skills-surface growth is justified, not absorbed.** Baseline 932 lines / 41,620 chars; +58%. Write a bound justification naming this spec, the bytes moved, and the `commands` reduction. **Never `--update-baseline`.**
- **BR12 lint-clean:** `/new-skill`, `status: candidate`, `disable-model-invocation: true`, verb-phrase description, `## Purpose` + `## When to Use`, `lint-skill.sh` exit 0, `gen-skill.sh --check` no delta. Bodies may not contain `Read commands/`, `Read skills/`, `Task(`, or a line starting with a slash command.

---

## For Testing Agents

No application code. Verification is structural, from the repo root:

```bash
python3 scripts/measure-invocation.py --root . --command verify-spec   # command_bytes ≤ 24,960; eager_bytes == 0; ceiling ≤ 57,070; unresolved_skills empty
python3 scripts/measure-invocation.py --root . --command verify-spec | grep -i 'both ways'  # expect none
grep -n 'required_skills:' commands/verify-spec.md                     # expect NO output
grep -n 'Read skills/'     commands/verify-spec.md                     # expect 6 hits / 4 names, each INSIDE its step (BR14 — read the line numbers)
python3 scripts/eval-loop-bounds.py | grep verify-spec                 # PASS verify-spec-no-recheck-step
bash scripts/lint-skill.sh skills/*/SKILL.md                           # exit 0
bash scripts/gen-skill.sh --check                                      # no delta
bash scripts/eval.sh                                                   # no new findings vs pre-spec baseline
python3 scripts/spec-deps.py validate --specs-dir .writ/specs
git diff --name-only                                                   # only verify-spec.md, new skills, manifest, SKILL.md

# pinned literals — 4 present in the command, 1 absent everywhere
for l in 'Cross-spec dependency validation' 'self-reference' \
         'story dependency validation is unchanged' 'spec-lifecycle.md'; do
  grep -qF "$l" commands/verify-spec.md || echo "MISSING: $l"; done
grep -rF 'specs/**' commands/verify-spec.md skills/*/SKILL.md   # expect none

# fidelity
git show <base>:commands/verify-spec.md > /tmp/before.md
grep -o '^#### Check [^$]*' /tmp/before.md   # every heading must appear verbatim in command + skills
grep -c 'Product Consistency Checks' commands/verify-spec.md            # heading byte-identical
grep -rEn '^\s*(#{2,4} |[0-9]+\.[0-9]* ).*re-?(check|verify|run)' commands/verify-spec.md skills/*/SKILL.md   # expect none
git diff commands/verify-spec.md | grep -c '^[-+].*calibrated_against'  # expect 0
```

**Edge Cases:**
- `--product` is a **distinct check set**, not spec checks pointed at product docs. Never merge P1–P4 with 1–8.
- Check 7 is **skipped** (not failed, not flagged) when `spec-lite.md` is absent; row 7 is omitted from the table with a note.
- `--product` skips gracefully with no error and no files written when `.writ/product/` is absent; a missing `.writ/context.md` is not an error — it is a P3 regeneration target.
- Check 8's owner requirement applies only to specs created on/after 2026-04-24; legacy specs report, never warn, never backfill.
- `commands/migrate.md:323` already says "checks 1–7" (stale since Check 8 landed). **Do not fix** — out of scope; recorded as a finding.

**Anti-goals:**
1. An extraction that is smaller but no longer says what each check auto-fixes versus reports. That passes every byte check and destroys the command. BR3's ledger is the only defense.
2. **A command whose six inline reads all sit near the top.** Identical `floor_bytes`? No — worse: they land *in* the floor. Identical `ceiling_bytes`, every check green, and both mode exclusions gone, so `--product` pays for the eight-check diagnostic again. This is the eager mechanism the 2026-08-12 ruling rejected, rebuilt by hand. Placement is checked by reading line numbers; nothing automates it.
