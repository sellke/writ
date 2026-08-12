# Load Report — Progressive Disclosure Pilot (`implement-story`)

> **Measured:** 2026-08-12, branch `writ/phase/10b/2026-08-12-disclosure-implement-story`, base `9e76d1e`.
> **Instrument:** `python3 scripts/measure-invocation.py --root . --command implement-story`, post-`e8f2a09` and post-`a191bd7`.
> **Baseline:** **83,770** for the ceiling, **77,669** for the floor. The pre-`e8f2a09` figure of 77,669 was produced by an instrument blind to inline reads and is never used as a ceiling baseline here.

## The verdict, in two sentences

**The full-path ceiling regressed: 91,904 against an 83,770 allowance — +8,134 bytes, +9.7%.** The floor, which every single invocation pays, fell from 77,669 to **49,797 — −27,872 bytes, −35.9%** — and a `--quick` run, which the eager mechanism could not have moved by a single byte, now costs **82,224 instead of 83,770 (−1.8%)**, or **77,366 (−7.6%)** when the story has no dependencies.

These are different runs. Neither number offsets the other, and the `--quick` saving is **not** offered as compensation for the full-path regression.

## Before and after

| Field | Before | After | Delta |
|---|---|---|---|
| `command_bytes` | 52,709 | **24,837** | −27,872 / **−52.9%** |
| `command_lines` | 989 | **340** | −649 / −65.6% |
| `eager_bytes` | 0 | **0** | unchanged |
| `eager_skills` | `[]` | **`[]`** | unchanged |
| `floor_bytes` | 77,669 | **49,797** | −27,872 / **−35.9%** |
| `conditional_bytes` | 6,101 | **42,107** | +36,006 |
| `conditional_skills` | 1 (`tdd-cycle`) | **9** | +8 |
| `hoisted_skills` | `[]` | **`[]`** | — |
| `unresolved_skills` | `[]` | **`[]`** | — |
| `ceiling_bytes` (envelope) | 83,770 | **91,904** | **+8,134 / +9.7%** |
| `base_share_of_floor` | 32.1% | **50.1%** | the shared base is now half the floor |

Budget checks: `command_bytes` **24,837 ≤ 24,960** ✓ · `floor_bytes` **49,797 ≤ 49,920** ✓ · `eager_bytes` **0** ✓ · no both-mechanisms warning ✓.

## Path-dependent ceilings, with the arithmetic

`ceiling_bytes` is an **envelope**, not a path: it sums every inline read in the file, including reads on mutually exclusive branches no single invocation can both reach. `measure-invocation.py` does not model paths, so each figure below is derived by subtracting the measured `wc -c` of the skills that path never loads.

```
floor            = base 24,960 + command 24,837                      =  49,797
full path        = floor 49,797 + all 9 conditional reads 42,107     =  91,904
--quick          = 91,904 − boundary-map-computation 6,518 (Gate 0.5)
                          − drift-triage             3,162 (Gate 3.5)=  82,224
--quick, no deps = 82,224 − dependency-context-loading 4,858         =  77,366
--review-only    = 91,904 − boundary-map-computation 6,518
                          − tdd-cycle                6,101 (Gate 1)  =  79,285
```

| Path | After | Same path today | Delta |
|---|---|---|---|
| **Floor** — every run, every path | **49,797** | 77,669 | **−27,872 / −35.9%** ✓ |
| **Full path** — every gate fires | **91,904** | 83,770 | **+8,134 / +9.7%** ✗ |
| **`--quick`** | **82,224** | 83,770 | **−1,546 / −1.8%** ✓ |
| **`--quick`, dependency-free story** | **77,366** | 83,770 | **−6,404 / −7.6%** ✓ |
| **`--review-only`** | **79,285** | 83,770 | **−4,485 / −5.4%** ✓ |

### Report the `--quick` saving honestly

`--quick` skips **five** gates — 0, 0.5, 3, 3.5 and 5 — but only **two** of them carry an extracted skill:

| Skipped gate | Carries a skill? | Why |
|---|---|---|
| Gate 0 — Architecture Check | no | agent spawn; its procedure lives in `agents/architecture-check-agent.md` |
| **Gate 0.5 — Boundary Map** | **yes** | `boundary-map-computation`, 6,518 B — genuinely not loaded |
| Gate 3 — Review Agent | no | agent spawn; `agents/review-agent.md` |
| **Gate 3.5 § A — Drift Response** | **yes** | `drift-triage`, 3,162 B — genuinely not loaded |
| Gate 5 — Documentation | no | agent spawn; `agents/documentation-agent.md` |

**"Five gates skipped" is not "five skills saved."** Gates 0, 3 and 5 are agent spawns whose procedure sits in `agents/*.md`, which this instrument does not measure and this spec did not touch. Note also that Gate 2.5 is **not** in `--quick`'s skip list, so `change-surface-classification` is paid on every run.

The largest single conditional win is mode-independent: **`dependency-context-loading` (4,858 B) is never loaded by a story with no dependencies**, because its read sits inside the has-dependencies branch rather than at the top of Step 2.

## Per-skill sizes and the measured scaffolding cost

| Skill | Source block | Projected | **Measured** | Read placed at | On `--quick`? |
|---|---|---|---|---|---|
| `story-context-assembly` | L95–220 | ~6,750 | **7,454** | Step 2 | yes |
| `boundary-map-computation` | L436–519 | ~5,950 | **6,518** | **Gate 0.5** | **no** |
| `tdd-cycle` *(pre-existing)* | — | 6,101 | **6,101** | Gate 1 (`:157`) | yes |
| `what-was-built-authoring` | L670–733, L842–956 | ~6,850 | **5,859** | Step 4 item 4 | yes |
| `dependency-context-loading` | L221–340 | ~5,400 | **4,858** | Step 2, dependency branch | only with deps |
| `drift-triage` | L623–669 | ~2,420 | **3,162** | **Gate 3.5 § A** | **no** |
| `project-context-snapshot` | L341–396 | ~2,500 | **3,150** | Step 4 item 3 | yes |
| `change-surface-classification` | L571–593 | ~2,300 | **2,761** | Gate 2.5 | yes |
| `story-commit-provenance` | L829–841 | ~2,030 | **2,244** | Step 4 item 7 | yes |
| **Eight new, total** | | ~34,200 | **36,006** | | |

**Per-skill scaffolding — the number the remaining five specs need.** Frontmatter + `# Title` + `## Purpose` + `## When to Use` + `## How to Apply` costs roughly **900–1,000 bytes per file regardless of content**, so eight files carry ≈ **7,600 bytes that did not exist in the monolith** — very nearly the entire +8,134 overage. The clearest instance is `change-surface-classification`: a 1,896-byte source block became a 2,761-byte file, roughly **34% scaffolding**.

**The operational conclusion: fewer, larger skills.** The overhead is charged per *file*, not per byte, so a spec that splits one capability into three small skills pays it three times for the same content. A command whose gates nearly always all fire is also the weakest extraction candidate — it realizes the ceiling and never the floor.

## Did the full-path ceiling regress? Yes — and by more than projected

| | Projected | Measured | Miss |
|---|---|---|---|
| Full-path ceiling | 87,231 (+4.1%) | **91,904 (+9.7%)** | **+4,673 bytes** |
| `command_bytes` | ~20,970 | 24,837 | +3,867 |
| Eight skills | ~34,200 (+~1,000 connective) | 36,006 | +806 |

**Compression attempted, with measured yield:**

| Target | Projected | Measured | Where |
|---|---|---|---|
| C1 — the 41-line worked WWB example | ~1,200 | **~1,500** | Story 4 (realized in `dependency-context-loading`) |
| C2 — the `what_was_built_data` object literal | ~400 | **~700** | Story 4 |
| C3 — overlapping degradation lists | ~400 | **~400** | Stories 2 and 4 |
| C4 — `boundary_map` Flags list vs. schema annotations | ~300 | **~330** | Story 3 |
| C5 — drift-log entry example | ~350 | **~350** | Story 3 |
| C6 — two `STATUS: BLOCKED` blocks → one template | ~950 | **~950** | Story 5 |
| **Ledger total** | **~3,600** | **~4,230** | five of six beat projection |
| Unbudgeted prose compression, command | — | **−2,271** | Story 5, five passes |
| Unbudgeted commentary compression, skills | — | **−1,703** | Stories 2, 3, 5 |

**What was not done to close the gap.** No gate, threshold, result value, degradation row, fallback, log string or always/never clause was deleted. The no-drift inventory (281 rows, zero unaccounted) is the evidence. The one remaining large lever — pointing Gates 0, 3, 4, 4.5 and 5's dimension and process lists at the `agents/*.md` files that also carry them, worth roughly 1,500 bytes — was rejected because an agent definition is neither the command nor one of the eight skills, so every one of those rows would have become unaccounted.

**Where this escalates.** ADR-021 sequenced `implement-story` first *"since a failure there should stop the phase rather than surface after five easier wins."* This is that signal, arriving on schedule. It is recorded as a tracked exemption in ADR-021's amendment entry 2 and is a finding for its **2026-11-11 review trigger** — which asks whether measured per-invocation load dropped for at least 4 of the 6 targeted commands. For this command the honest answer is **the floor did, by 35.9%; the all-gates path did not, by 9.7%**, and a single "per-invocation load" number no longer describes a run.

## Graceful-degradation probe — on the mechanism actually used

`Read skills/deliberately-missing-skill/SKILL.md` was inserted at a real step (Step 4, immediately above item 7's provenance read) and `measure-invocation.py` re-run:

- **Exit code: 0** — never a hard failure.
- `unresolved_skills`: `["deliberately-missing-skill"]`
- `conditional_skills`: still 9 resolvable names; `ceiling_bytes` 91,965 with the unresolved name contributing nothing.
- Warning emitted, verbatim: *"commands/implement-story.md references skills that resolve to no file: deliberately-missing-skill. Their load is unmeasurable, so the figures below are a lower bound."* — printed to stderr in `--format table` and present in the JSON `warnings` array.

The probe was reverted; `git diff commands/implement-story.md` returned empty and a re-measurement reported `command_bytes` 24,837 with `unresolved_skills` `[]`.

**`scripts/eval-leanness.py`'s `check_required_skills` could not be exercised and is reported unexercised, not passed.** It reads **frontmatter only**, and this command declares nothing, so it has nothing to resolve — `metrics.required_skills_declarations` is **0**. Its pin to the `warnings` bucket (`eval-leanness.py:1239`, `emit_contract_findings(..., severity="warnings")`), which exists so that a later severity flip cannot make an unknown skill name blocking, therefore remains **untested in the product**. No declaration was added to manufacture a pass.

## Harness observation

**Honest answer: not determinable from this run.**

This spec was implemented by an agent executing `/implement-spec` over the spec's six stories; no `/implement-story` invocation of the rewritten command occurred, so there is no transcript in which the nine inline reads either fired or did not. Recording "could not determine" is the instruction the story gives for exactly this case, and it is the accurate one.

What *is* established, and what is not:

- **Established structurally.** All nine reads resolve to real files (`unresolved_skills` empty); none sits above `### Step 1` (`hoisted_skills` empty, lowest read at line 102 against Step 1 at line 73); each skill is read exactly once; no skill reads another (`grep -RF 'Read skills/' skills/` is empty, per `lint-skill.sh:52`).
- **Established by tooling behavior.** An unreadable skill path degrades to a warning and exit 0 in the measuring instrument.
- **Not established.** Whether a real harness issues a `Read` only on reaching the line — i.e. whether loading is *actually* lazy at runtime — and whether an unreadable path degrades gracefully in the harness as opposed to the instrument. The roadmap's Phase 10 manual success criterion (*"One real `/implement-story` run completes with progressive disclosure active and every gate firing"*) is **not** satisfied by this spec and is not automatable. **A `--quick` run is the one to observe**, because its two skipped skills are the mechanism's whole claim.

If a harness is found to hard-fail on an unreadable skill path, or to pre-load reads it has not reached, that is a **finding for ADR-021's 2026-11-11 review trigger**, not something to work around.

## The ownerless correction — `required_skills:` loses its only announced consumer

`metrics.required_skills_declarations` reports **0** today, and will still report **0** after all six disclosure specs land. Two files assert otherwise:

| File | The now-false claim | In this spec's file set? | Owner |
|---|---|---|---|
| `system-instructions.md` → *`required_skills:` frontmatter convention* | *"**Status: adopted.** … The first consumer is Phase 10 progressive disclosure (ADR-021), which needs exactly the declarative, harness-resolved, **per-invocation** load contract this convention specifies … The first real declarations land with progressive disclosure's extraction work"* | **no** | **none assigned** |
| `adapters/claude-code.md:396` | *"Phase 10 progressive disclosure (ADR-021) is its first consumer, and no consumer declares the field yet"* | **no** | **none assigned** |

The same sentence also appears in `.writ/docs/skills.md` → *`required_skills:` frontmatter convention*, which **is** in this spec's file set but whose `Status: adopted` paragraph was deliberately left alone: correcting one carrier of a three-carrier claim would be worse than correcting none, and the adoption decision belongs to `system-instructions.md`.

**Neither file was edited.** `system-instructions.md` is the root behavioral contract; retiring or re-justifying a convention from inside an extraction spec would change it without a decision, and both files sit outside the locked file set this spec promised a reviewer. The second half of each claim — *"no consumer declares the field yet"* — becomes **permanently** true rather than temporarily.

**This needs a maintainer action this spec cannot take.** The adoption may still be correct — `required_skills:` remains the right mechanism for a skill a consumer genuinely needs on *every* invocation — but its stated justification (*"per-invocation"*, *"the exact contract"*) is precisely the claim this pilot disproves. `2026-08-12-governor-enforcement` is the nearest candidate owner and already carries two orphaned obligations from this spec, but it owns `scripts/`, not `system-instructions.md`, so naming it here would assign work outside its own locked file set. **Recorded, unassigned, surfaced.**

## Handoffs to `2026-08-12-governor-enforcement`

| Handoff | Measured input |
|---|---|
| Implement the 24,960-byte command budget in `scripts/eval.sh` / `eval-leanness.py` | Until it lands, `commands/implement-story.md` is compliant with a budget nothing checks — the "ratchet at a bloated baseline" failure ADR-021 diagnosed, one level up |
| Raise `MAX_SKILLS` (currently 12, `eval-leanness.py:71`) | Count is now **14**; `check_ceilings` emits a **warning**, never a finding, so nothing breaks. Per-skill overhead measured here is ~900–1,000 B; if the remaining five specs average six skills each the surface reaches ~44. Do not set the new cap by extrapolating from six unextracted files — this is the first real datapoint |
| `CONTRACT_CHECK_SEVERITY` flip | Note that `check_required_skills` will have **nothing to assert** after the flip: a permanent 0 |
| `.writ/product/roadmap.md` Phase 10's stale 400-line success criterion | Superseded as the binding instrument by ADR-021's amendment entry 1; the roadmap line is now stale and that spec must edit it when it changes the code |

## A twelfth pinned constraint the spec's table did not list

`sub-specs/technical-spec.md` → *Pinned Literals* lists eleven `require_literal` strings from `scripts/eval.sh` and two `eval-loop-bounds.py` regexes. There is a **twelfth**, in a third script: **`scripts/eval-artifact-integrity.py:96`** asserts the command contains both `**Integrity:**` **and** the substring `missing required`. Retaining only `**Integrity:**` satisfied every literal in the spec's table and still produced `FAIL (1 finding)` — `artifact-integrity:context-schema-integrity-line`.

Fixed by restoring both Integrity states verbatim to Step 4 item 3 (+60 bytes), which also returns no-drift inventory row 112 to the command. **The five sibling disclosure specs should grep `scripts/` for `read("commands/<their file>.md")` rather than trusting a hand-built literal table** — `eval.sh` is not the only asserter.

## Clean-tree verification

| Check | Result |
|---|---|
| `bash scripts/eval.sh` | **Findings: 0, Run errors: 0** |
| `python3 scripts/eval-loop-bounds.py` | `PASS drift-review-cycle`, `PASS drift-testing-cycle` — no SKIP |
| `bash scripts/lint-skill.sh skills/*/SKILL.md` | all **14** clean |
| `bash scripts/gen-skill.sh --check` | no delta; `.writ/manifest.yaml` `skills:` holds 14 alphabetical entries |
| `bash scripts/check-agent-parity.sh` | clean |
| `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` | `status: ok` |
| `git diff --name-only \| grep '^scripts/'` | **no output** — no script edited, including the permitted comment-only exception |
| `.writ/leanness-baseline.json` | bound justifications recorded for `skills.lines` (1814) and `skills.chars` (77625); `--update-baseline` **not** run; both unjustified-growth warnings cleared, leaving only the `MAX_SKILLS` soft-ceiling warning |
