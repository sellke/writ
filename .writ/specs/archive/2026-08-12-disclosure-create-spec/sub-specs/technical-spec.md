# Technical Spec: Progressive Disclosure — `/create-spec`

> Parent: [spec.md](../spec.md)
> All line numbers are against `commands/create-spec.md` at its pre-spec state: **871 lines / 46,423 bytes**, measured 2026-08-12. Byte figures come from `sed -n 'A,Bp' commands/create-spec.md | wc -c`.

## Measurement Protocol

The one instrument:

```bash
python3 scripts/measure-invocation.py --root . --command create-spec           # json
python3 scripts/measure-invocation.py --root . --command create-spec --format table
```

**The script was fixed on 2026-08-12 (`e8f2a09`) and every figure below is re-measured against the fixed version.** It had treated `required_skills:` as a conditional load and excluded it from the floor. It is eager. The corrected model:

```
floor   = base + command + eagerly declared skills   always paid
ceiling = floor + inline-read skills                 worst-case path
```

It reports, per command: `command_bytes`, `command_lines`, `base_bytes`, `eager_bytes`, `floor_bytes`, `conditional_bytes` (= sum of skills reached by an inline `Read skills/<name>/SKILL.md` in the body, frontmatter excluded), `ceiling_bytes`, `eager_skills`, `conditional_skills`, `resolved_skills`, `unresolved_skills`, and `base_share_of_floor`.

**Three things to know about it, and all three matter here.**

1. `conditional_bytes` counts **inline reads**, which is exactly the mechanism this spec adopts (spec § *Approved Scope Change*). The incumbent `error-rescue-mapping` at line 765 is now counted, and the five extracted skills will be too. `eager_bytes` must stay `0`: this command declares no `required_skills:`.
2. **It sums every inline read in the file regardless of reachability.** It cannot know that `spec-source-prepopulation` and a standard run are mutually exclusive. `ceiling_bytes` is therefore an **envelope**, not a path anyone walks. Story 6 must name the maximal reachable path and state whether it equals the envelope.
3. Tokens are an **estimate** (`chars/4`), and the script says so in `token_note` and `token_method_validated: false`. Report bytes. Quote tokens only with the script's own label attached.

The script also emits a warning when a skill is **both** declared and inline-read (*"the declaration wins … the inline Read buys no conditionality. Drop one."*). That warning must never appear for `create-spec`; it would mean the eager mechanism had crept back in.

The separate "true worst case" figure this spec used to carry is **retired**. It was a hand-computed correction for a tool that could not see inline reads. The fixed tool's `ceiling_bytes` *is* that number — and the create-spec agent's hand computation of 77,530 was right.

### The bars

| Bar | Expression | Value |
|---|---|---|
| **Floor** (spec BR1) | `command_bytes ≤ 24,960`, i.e. `floor_bytes ≤ 49,920`, with `eager_bytes == 0` | binding |
| **Worst-path ceiling** (spec BR1, inherited pilot BR1) | `command_bytes + conditional_bytes ≤ 52,570`, i.e. `ceiling_bytes ≤ 77,530` | binding |
| **Partial paths** (spec BR1) | ≥ 1 realistic path reported as arithmetic | binding — a report, not a bar |

### Baseline (re-measured 2026-08-12 against the fixed tool, pre-spec)

| Figure | Bytes |
|---|---|
| `system-instructions.md` | 20,153 |
| `commands/_preamble.md` | 4,807 |
| `base_bytes` | **24,960** |
| `command_bytes` | 46,423 |
| `eager_bytes` | 0 |
| `floor_bytes` | **71,383** |
| `conditional_bytes` — `skills/error-rescue-mapping/SKILL.md`, inline at line 765 | 6,147 |
| `ceiling_bytes` | **77,530** |

### Projected target

| Figure | Projection | Bar |
|---|---|---|
| `command_bytes` | ~16,000 | **≤ 24,960 — binding** |
| `command_lines` | ~300 | ≤ 400, non-binding tripwire |
| `eager_bytes` | 0 | **== 0 — binding** |
| `floor_bytes` | ~40,960 | ≤ 49,920 |
| `conditional_bytes` (5 new + `error-rescue-mapping`, before compression) | ~39,800 | — |
| `ceiling_bytes` (before compression) | ~80,760 | **≤ 77,530 — over by ~3,227** |
| `ceiling_bytes` (after the Compression Ledger) | ~77,460 | ≤ 77,530 |

Projections, not promises. Story 6 replaces every cell with a measurement. **The worst-path ceiling does not clear without compression** — that is the spec's identified failure mode, stated here in numbers rather than discovered in Story 6. The overage is numerically unchanged by the mechanism ruling, because the same bytes moved across the floor/ceiling line on both sides of the comparison.

### Projected paths (the report BR1 now requires)

| Path | Inline reads issued | Projected bytes |
|---|---|---:|
| Floor — before any branch | none | ~40,960 |
| `--recommend` rejected at the invocation matrix | none | **~40,960** (−43% vs today's 71,383) |
| Bare collaborative run, docs-only, no UI | 4 of 6 | ~64,200 |
| `--from-issue` + data-flow feature — worst path | all 6 | ~77,460 |

Story 6 measures each path by summing the byte counts of the skills that path's reads would issue, and states which path is maximal.

## Compression Ledger

Business Rule 2 permits three contraction moves: deleting a worked example that illustrates a format specified elsewhere in the same text; collapsing two near-identical blocks into one parameterized block; replacing a restated field list with a pointer to the one authority. Nothing else. Each entry below names its category, and each carries a **measured** yield at implementation time — the estimates are targets, not credits.

| # | Target | Category | Est. yield | Lands in |
|---|---|---|---|---|
| 1 | `## Example Usage` lines 829–859 — the transcript's `## Specification Contract` echo restates the Step 1.4 format block field-for-field, 400 lines after it is specified | worked example of a format specified elsewhere | ~1,200 | Story 1 (`requirements-discovery`) |
| 2 | The two source modes' *Step 2: Contract Proposal* paragraphs (139–141 and 223–225) are near-identical, differing only in "Present in Plan Mode for review" vs "Present for review" | two near-identical blocks → one parameterized block | ~400 | Story 5 |
| 3 | The two `--from-*` contract shape blocks (144–156, 228–239) share their header, their `Files in Scope` line, and the identical trailing `[standard contract sections: Constraints, Success Criteria, Scope Boundaries]` | two near-identical blocks → one parameterized block | ~500 | Story 5 |
| 4 | *Line Budget Enforcement* (697–706) restates the 35/35/30 figures already stated three times inside the template itself (608, 632, 661) plus the total already stated at 598 | restated field list → pointer to the authority | ~500 | Story 3 |
| 5 | Step 1.4's contract format block and the two source-mode shape blocks both enumerate the same "standard contract sections" — one authority, two pointers | restated field list → pointer | ~300 | Stories 2 + 5 |
| 6 | Skill scaffolding discipline: `## Purpose` and `## When to Use` written at the density of the six incumbent skills (which run 5,997–9,985 bytes total each), not padded to the scaffold's suggested shape | — | ~400 | all five |
| | **Total** | | **~3,300** | |

**Not on this ledger, and not eligible:** the nine/eight/seven discovery topic questions (each names a distinct failure the conversation misses without it); the four gap categories; the seven pushback phrasings; any threshold; any degradation or fallback path; the two source modes' *distinct* anchor questions, framings, and exchange budgets. Compression removes words, never rules.

If the measured yield falls short of the overage, Story 6 does not shave a skill to fit. It records the shortfall, states what was attempted and what it yielded, and produces the written justification Business Rule 1 requires — ADR-021's tracked-exemption path, taken deliberately.

## Rule Inventory

Business Rule 2's verification method. Every rule, gate, heuristic, threshold, and policy in `commands/create-spec.md` appears exactly once below with its source range and its destination. `C` = stays in `commands/create-spec.md`. `S:<name>` = moves to that skill.

**How a story uses this:** at Definition of Done, quote the destination for every row assigned to that story — a file path plus a heading or line. A row with no destination is a dropped rule. A rule found in a destination but absent from this table is an invented rule. Both are defects under Business Rule 2.

### Frontmatter and header (1–30)

| # | Rule | Src | Dest |
|---|---|---|---|
| 1 | `name` / `description` / `problem` / `outcome` / `exit_criteria` values, unchanged | 1–10 | C |
| 2 | **No `required_skills:` block.** Five inline `Read skills/<name>/SKILL.md` calls, each inside the step that needs it, per spec § *Load placement* (maintainer ruling 2026-08-12; supersedes inherited pilot BR8) | new | C |
| 3 | Contract-first framing; Plan Mode for discovery, AskQuestion for bounded decisions | 14–16 | C |
| 4 | Required Artifacts: none required; `.writ/product/` docs and `.writ/context.md` optional | 18–23 | C |
| 5 | Three invocation forms: bare, `--from-prototype`, `--recommend [idea]` | 25–29 | C (as table) |
| 6 | `--from-issue [path]` is a fourth form, documented at 175 but absent from `## Invocation` | 175 | C (as table row — recording an existing omission, not adding behavior; see Story 6 notes) |

### `## Recommended Mode` (31–99) — all `C`, Business Rule 6

| # | Rule | Src | Dest |
|---|---|---|---|
| 7 | Parse `--recommend` exactly once at command entry; store `recommend_mode`; branch before discovery or file creation | 33–34 | C |
| 8 | Normal branch is authoritative when `--recommend` is absent | 36–38 | C |
| 9 | `--recommend` makes authoring autonomous: contract-first discovery still runs, routine gates auto-adopt, rationale recorded | 40–44 | C |
| 10 | Terminal scope: produces a locked validated package and stops; never triggers `/implement-spec` | 46–49 | C |
| 11 | Invocation matrix, 8 rows, `Supported`/`Reject` prefixes, parsed by `eval.sh:757` | 56–65 | C — table shape preserved verbatim |
| 12 | Validate the complete invocation before creating files, updating an issue, or launching discovery | 53–54 | C — must precede `### Autonomous Authoring Boundary` |
| 13 | On rejection, print the supported forms and stop before mutation | 67 | C |
| 14 | Auto-adopt set: feature selection, contract lock, story decomposition + sub-spec set, visual references, source pre-population | 74–89 | C |
| 15 | `recommendation-log.md` records decision, evidence, material alternatives, risk/reversibility, result — never private chain-of-thought or transcript content | 73–74 | C |
| 16 | Pause set: no idea and no single candidate; conflicting/infeasible requirements (core-contract *ambiguity*, not the lock); a blocking cross-spec overlap | 90–93 | C |
| 17 | After auto-lock: run ordinary Phase 2, write `recommendation-log.md`, apply `spec_ref` writeback under `--from-issue`, then stop | 95–99 | C |

### `--from-prototype` (100–171) → `S:spec-source-prepopulation`

| # | Rule | Src | Dest |
|---|---|---|---|
| 18 | Trigger: a `/prototype` run raised scope-escalation signals | 107 | S |
| 19 | Replaces Phase 1 with a shorter prototype-anchored flow | 109 | C (phase list) + S |
| 20 | Read `git diff HEAD`, or `git diff --cached` if staged; extract files changed, lines added/removed, new dependencies | 113 | S |
| 21 | Read the coding-agent implementation summary from the thread if available | 114 | S |
| 22 | Pre-populated draft: Deliverable from diff+summary, Files in Scope from diff, Approach from summary else diff, Story 1 = prototype work marked complete | 115–119 | S |
| 23 | Clean tree → exact warning text, then offer manual description or cancel | 121 | S |
| 24 | Shortened discovery: Plan Mode, do not re-litigate what was built, 3–5 exchanges | 123–137 | S |
| 25 | Opening framing line, verbatim | 128 | S |
| 26 | Five forward-looking anchor questions | 131–135 | S |
| 27 | Skip questions the diff already answers | 137 | S |
| 28 | Contract proposal uses the Step 0 draft as base, augmented by discovery, presented in Plan Mode | 139–141 | S |
| 29 | `--from-prototype` contract shape block | 144–156 | S |
| 30 | Story 1 generated `Status: Completed ✅`, tasks `- [x]`, DoD checked, later stories `Not Started`, README reflects it | 158–167 | S |
| 31 | Why Story 1 is auto-complete: the work exists; `Not Started` would misrepresent state and confuse `/implement-spec` | 169 | S |

### `--from-issue` (172–256) → `S:spec-source-prepopulation`

| # | Rule | Src | Dest |
|---|---|---|---|
| 32 | Trigger: a captured `.writ/issues/` issue is ready for promotion | 177 | S |
| 33 | Validate path under `.writ/issues/{bugs,features,improvements}/`; exact error block; **do not modify the issue file on error** | 183–189 | S |
| 34 | Parse Type, Priority, Effort, TL;DR, Current State, Expected Outcome, Relevant Files | 191–198 | S |
| 35 | Pre-populated draft: Deliverable, Origin, Files in Scope, Priority signal, Effort signal | 200–205 | S |
| 36 | Shortened discovery: do not re-ask what the issue documents; 2–4 exchanges | 207–221 | S |
| 37 | Opening framing line, verbatim | 212 | S |
| 38 | Five gap-filling anchor questions | 215–219 | S |
| 39 | `--from-issue` contract shape block | 228–239 | S |
| 40 | After `spec.md` is written, replace the issue's `spec_ref:` line with the spec path; **only that line changes**; issue never deleted or archived | 245–252 | S |
| 41 | Absent `spec_ref` line → append to frontmatter rather than fail | 254 | S |

### Phase 1 (258–520)

| # | Rule | Src | Dest |
|---|---|---|---|
| 42 | Mission statement, including "Challenge ideas that don't make technical or business sense" | 260–262 | C (phase list preface) |
| 43 | Step 1.0 feature selection `AskQuestion` block, options generated from a codebase scan, `other` → free-text follow-up | 264–288 | S:requirements-discovery |
| 44 | Step 1.1 context scan: `.writ/specs/` for related specs, `codebase_search` for architecture, load `tech-stack.md` / `code-style.md` / `objective.md`, output a summary, **create no files** | 290–295 | C (phase list — the no-file-creation rule is a gate) + S:requirements-discovery (the scan detail) |
| 45 | Step 1.2 Plan Mode: user controls the switch; read-only enforcement; conversational UX; clear phase signal | 297–304 | C — and the `requirements-discovery` load point |
| 46 | ADR-001 design principle: AskQuestion when you know the option space, Plan Mode when you need to discover it | 305 | S:requirements-discovery |
| 47 | Step 1.3 internal process before speaking: list missing facts, identify ambiguities, note integration points, catalog unknowns | 309–314 | S:requirements-discovery |
| 48 | Four gap categories with their members: Experience, Business rule, Technical, Scope | 316–319 | S:requirements-discovery |
| 49 | Conversation rules: one question at a time; re-scan after answers; **95% confidence** threshold; never declare "final question"; user signals readiness; challenge bad ideas | 321–328 | S:requirements-discovery |
| 50 | Topic ordering: experience → rules → technical, with the stated reason | 330–332 | S:requirements-discovery |
| 51 | Nine experience questions, verbatim | 334–343 | S:requirements-discovery |
| 52 | Eight business-rule questions, verbatim | 345–353 | S:requirements-discovery |
| 53 | Seven technical questions, verbatim | 355–362 | S:requirements-discovery |
| 54 | Eight critical-analysis responsibilities | 364–373 | S:requirements-discovery |
| 55 | Seven pushback phrasing examples, verbatim | 375–383 | S:requirements-discovery |
| 56 | Transition to contract: present when confident, still in Plan Mode; suggested phrasings; always leave room for more questions | 385–389 | S:requirements-discovery |
| 57 | Worked transcript demonstrating pushback, cost framing, and the lock handoff | 787–864 | S:requirements-discovery (`## Examples`) |
| 58 | "Key UX difference" note: Plan Mode for discovery, AskQuestion for decisions | 864 | S:requirements-discovery |
| 59 | Step 1.3b runs **before** the contract is presented | 393 | C (gate) + S:contract-lock |
| 60 | Single-level glob `.writ/specs/*/spec.md`; naturally excludes `archive/`; **no parallel `grep -v archive`** (`forbid_literal`) | 395 | S:contract-lock — and the forbidden string must not appear anywhere in either file |
| 61 | Complete-family filter via `python3 scripts/spec-status.py is-complete`; bold and unbold labels; `Complete` / `Completed ✅` / `Closed — Abandoned`; trailing emoji ignored; **never** match the bare substring `Status: Complete`; no status header → not complete | 396 | **C** — `spec-status.py` is `require_literal`-pinned |
| 62 | Read each remaining `spec-lite.md` | 397 | S:contract-lock |
| 63 | Extract domain keywords: models/entities, routes/endpoints, shared utilities, domain terms, files to be modified | 398 | S:contract-lock |
| 64 | Compare for keyword overlap in domain areas | 399 | S:contract-lock |
| 65 | Overlap → add a `⚠️ Cross-Spec Overlap` section; no overlap → proceed silently | 400–401 | S:contract-lock |
| 66 | The check is a lightweight keyword heuristic; false positives acceptable; goal is catching planning-level conflicts before implementation | 403 | S:contract-lock |
| 67 | Step 1.4 contract format block — Deliverable, Must Include, Hardest Constraint, 🎯 Experience Design (5 fields), 📋 Business Rules, Success Criteria, Scope Boundaries, ⚠️ Technical Concerns, 💡 Recommendations, ⚠️ Cross-Spec Overlap | 411–450 | S:contract-lock |
| 68 | Present in Plan Mode; discuss refinements conversationally; confirm with AskQuestion on return to Agent Mode | 452 | C (gate) + S:contract-lock |
| 69 | Step 1.4b five-option `AskQuestion`: ids `yes`/`edit`/`risks`/`blueprint`/`questions` with their exact labels | 458–475 | S:contract-lock — ids and labels verbatim |
| 70 | Five response handlers: proceed / free-text follow-up / risk analysis then re-present / show folder structure then re-present / back to Plan Mode | 477–482 | S:contract-lock |
| 71 | Step 1.5 runs after contract lock, before file creation, only when the feature has UI | 486–488 | C (gate) + S:spec-package-authoring |
| 72 | Five-option visual-reference `AskQuestion`: `screenshots`/`sketch`/`generate`/`existing`/`none` | 491–506 | S:spec-package-authoring |
| 73 | Five handlers, including vision-model analysis, `.excalidraw` parsing, `/design` wireframe conventions, `mockups/current/` "before" state, and empty `mockups/` for `none` | 509–514 | S:spec-package-authoring |
| 74 | When mockups exist: `## Visual References` per story, `mockups/component-inventory.md`, design-system tokens from `.writ/docs/design-system.md` or extracted | 516–519 | S:spec-package-authoring |

### Phase 2 (521–770)

| # | Rule | Src | Dest |
|---|---|---|---|
| 75 | Phase 2 is triggered only after the contract is confirmed with `yes` | 523 | C (gate) |
| 76 | Step 2.1 track progress with `todo_write` across five workstreams | 525–527 | C (phase list) |
| 77 | Step 2.2 date: `npx @sellke/writ date` when available, else local `YYYY-MM-DD`; used for folder naming | 529–533 | S:spec-package-authoring |
| 78 | Owner resolution shell block; `@` + `git config user.name` with spaces stripped; no external directory; unset → `@unknown` + warning | 535–545 | S:spec-package-authoring |
| 79 | Step 2.3 directory tree | 549–560 | S:spec-package-authoring |
| 80 | `spec.md` header block: Status, Created, Owner, Dependencies | 566–572 | **C** — `> **Dependencies:**` is pinned |
| 81 | Emit `> **Dependencies:**` for every new spec; never omit; `[]` when none | 573 | **C** — pinned |
| 82 | Values are exact spec-folder IDs in declared order; titles and fuzzy matches invalid | 574 | **C** — `exact spec-folder IDs` pinned |
| 83 | Spec-level `Dependencies` ≠ story-level `Dependencies:`; do not conflate the graphs | 575 | **C** |
| 84 | Canonical complete-family spelling, forward-only: `> **Status:** Complete`; detection stays tolerant of legacy spellings; governs new specs only | 576 | **C** — `Canonical complete-family spelling` pinned |
| 85 | Supersession banners: `> **Amends:**` (replaces) vs `> **Extends:**` (builds on); markdown link, text = prior folder name, target = relative `spec.md` | 577 | **C** — `Amends` pinned |
| 86 | `spec.md` body: contract echoed verbatim, experience design expanded, business rules expanded, detailed requirements, implementation approach | 578–582 | S:spec-package-authoring |
| 87 | Step 2.4b fires when the header carries `Amends:`/`Extends:`, uniformly across standard, `--from-issue`, `--from-prototype` | 586 | **C** |
| 88 | Invoke `python3 scripts/supersession-writeback.py apply --new-spec-file …` rather than hand-editing headers | 588–592 | **C** — `supersession-writeback.py` pinned |
| 89 | The helper parses every link target on the line (a line may carry more than one), resolves relative to the new spec's folder, writes/updates a `Superseded by:` line without duplicating, and leaves every other line — including `> **Status:**` — untouched | 594 | S:spec-package-authoring |
| 90 | Non-spec targets → `skipped_other`; broken paths → `broken`, never a hard failure; **this step never blocks package creation** — proceed to 2.5 and surface `broken` as an informational note | 596 | **C** (the never-blocks rule is a gate) + S:spec-package-authoring (the disposition detail) |
| 91 | `spec-lite.md` three-audience template, verbatim | 600–686 | S:spec-package-authoring |
| 92 | Total budget < 100 lines, hard limit | 598 | S:spec-package-authoring |
| 93 | Section budgets 35 / 35 / 30 lines | 608, 632, 661 | S:spec-package-authoring |
| 94 | Content selection by feature type: data flow / UI / refactor / docs-tooling | 688–695 | S:spec-package-authoring |
| 95 | Budget breakdown: ~5 header + ~10 structural + 35 + 35 + 30 = ~90 content + 10 structural | 697–706 | S:spec-package-authoring |
| 96 | Four over-budget tactics, in order: cut nice-to-haves, prioritize critical info, use references, truncate proportionally | 708–713 | S:spec-package-authoring |
| 97 | Backward compatibility: older single-block spec-lites are expected; do not retroactively convert unless asked | 715–717 | S:spec-package-authoring |
| 98 | Step 2.5: analyze deliverable and scope, break into standalone-value stories, identify dependencies, **5-7 implementation tasks max** | 721–726 | S:user-story-decomposition |
| 99 | Story plan output format | 730–735 | S:user-story-decomposition |
| 100 | Step 2.6 references `agents/user-story-generator.md` for the agent spec and prompt template | 739 | S:user-story-decomposition |
| 101 | Per-story agent inputs: output path, number, title, description, dependencies, priority, locked contract, codebase patterns, full spec content | 741 | S:user-story-decomposition |
| 102 | Context hint parameters `spec_content` and `technical_spec_content`; empty string plus a note when the technical spec does not exist yet | 743–745 | S:user-story-decomposition |
| 103 | Timing note: 2.6 in parallel with 2.8 means scoping hints to `spec.md` sections only, with the exact fallback phrasing | 747 | S:user-story-decomposition |
| 104 | Story file contents: status/priority/dependencies, As-a/I-want/So-that, **3-5 Given/When/Then criteria**, **5-7 tasks** (tests first, verification last), technical notes, DoD, `## Context for Agents` hints | 749 | S:user-story-decomposition |
| 105 | **Launch parallel Task subagents** (`generalPurpose`, model `fast`) in a single message; up to 4 at once; batch beyond 4 | 737–741, 751 | **C** — orchestration; `lint-skill.sh` rejects subagent dispatch in a skill body |
| 106 | Step 2.7 README: summary table (status, task counts, progress), dependency descriptions, quick links | 755 | S:user-story-decomposition |
| 107 | Step 2.8 sub-spec set: `technical-spec.md` always; `database-schema.md` / `api-spec.md` / `ui-wireframes.md` as needed; each references its stories | 759 | S:user-story-decomposition |
| 108 | Step 2.8 may run in parallel with 2.6 | 759 | **C** (orchestration) |
| 109 | Error-mapping applicability heuristic: include for API routes, auth, payments, file ops, external integrations; skip for pure UI/CSS, docs, config, internal refactors; **when in doubt, include** | 761–763 | **C** — the command owns *when* |
| 110 | `Read skills/error-rescue-mapping/SKILL.md` for the map, shadow paths, edge cases, `[UNPLANNED]` discipline, user-visible framing, drift-signal framing; the command owns *when* and which sub-specs carry the tables, the skill owns *how* | 765 | **C** — the pointer stays; Business Rule 12 |
| 111 | Step 2.9 final package review: file tree, story and task counts, review items, suggested next steps | 769 | C (phase list) |

### Completion and references (771–872)

| # | Rule | Src | Dest |
|---|---|---|---|
| 112 | Five success conditions; `--from-prototype` / `--from-issue` clause; suggested next step; terminal constraint | 771–785 | **C** — unchanged, Business Rule 11 |
| 113 | References: `commands/_preamble.md`, `system-instructions.md` | 868–871 | C — extended with the five skills |

**Row count: 113.** Story 6 asserts that all 113 have a named destination and that no destination carries a rule absent from this table.

## Skill Authoring Constraints

`bash scripts/lint-skill.sh skills/<name>/SKILL.md` must pass. The rejection grammar that actually bites here:

| Pattern | Category | Effect on this spec |
|---|---|---|
| `Read commands/` | command invocation | no skill may point back into `commands/` |
| `Read skills/` (`lint-skill.sh:52`) | skill chaining | no extracted skill references another; shared pointers live in the command. **This is why every inline read introduced by the 2026-08-12 mechanism ruling is placed in `commands/create-spec.md` and never inside a `SKILL.md`.** Checked against this spec's plan at amendment time: all six placements are in the command; the two cross-skill dependencies in the plan (Story 5's contract-shape blocks pointing at Story 2's format authority, Compression Ledger entry 5) are prose references, not reads |
| `Task(` | subagent dispatch | rule 105 stays in the command |
| `^/[a-z][a-z-]+` | slash command | a line may not *begin* with `/create-spec` etc.; inline backticked mentions are fine |
| `Acts as`, `Is responsible for`, `The … agent`, `Run the full`, `Execute the entire` | role/workflow shape | descriptions are verb-phrases |

Every skill carries `## Purpose` and `## When to Use` (asserted by lint), plus `## How to Apply` and `## Examples` per the `/new-skill` Step 3.1 scaffold. Frontmatter: `name`, `description`, `disable-model-invocation: true`, `status: candidate`, `status_evidence` naming the extraction date and the single **actual** consumer — prospective consumers named in spec.md's extraction map are not evidence and must not be written as though they were.

### Naming, inherited from `2026-08-12-disclosure-implement-story` BR3

Kebab-case noun phrase, 2–3 words, ≤ 30 characters, unique across `commands:` / `agents:` / `skills:` in `.writ/manifest.yaml`; shape `<object>-<operation>` or `<operation>-<object>`; never named after the extraction site (no command name, no step number); `description:` a bare-imperative verb phrase ("Compose…", "Assemble…", "Classify…"); a shared skill carries no consumer's vocabulary. Full convention in `.writ/docs/skills.md` → *Extraction Patterns*, written by the pilot's Story 1 — read it there rather than from this table.

**Collision protocol.** Before `/new-skill`, grep the manifest's `skills:` block for the intended name **and its head noun**. First writer owns the name; a later spec declares the existing skill and records an ADR-014 `type: promotion` evidence entry rather than authoring a near-duplicate. Names claimed by sibling specs at the time of writing (2026-08-12), to be re-checked rather than trusted:

| Claimed by | Names |
|---|---|
| incumbent | `code-explanation`, `conventional-commits`, `error-rescue-mapping`, `gbrain-interop`, `safe-refactor-loop`, `tdd-cycle` |
| `disclosure-implement-story` (pilot) | `story-context-assembly`, `dependency-context-loading`, `what-was-built-authoring`, `boundary-map-computation`, `change-surface-classification`, `drift-triage`, `project-context-snapshot`, `story-commit-provenance` |
| other siblings | `phase-decomposition`, `phase-lane-execution`, `audit-digest-composition`, `pr-body-composition`, `user-challenge-presentation` |

Two of this spec's names are qualified because of that list: `user-story-decomposition` (not `story-decomposition`, whose operation noun the sibling `phase-decomposition` already carries) and `spec-package-authoring` (not `spec-package-layout` — "layout" is a noun, and `what-was-built-authoring` is the shape precedent).

Manifest: `/new-skill` Step 3.2 appends an alphabetically-placed `skills:` entry to `.writ/manifest.yaml`; Step 3.3 runs `bash scripts/gen-skill.sh --check` and regenerates the root `SKILL.md` on delta. `.writ/manifest.yaml` is also edited by `2026-08-11-retire-dead-prescription` (version bump and command-entry reconciliation) — that spec touches `version:` and the `commands:` list, this one appends under `skills:`. Disjoint keys, but if both are in flight the manifest is the one file where a conflict is possible; land them in sequence.

## Verification

Run after every story, not only at the end:

```bash
# budget
python3 scripts/measure-invocation.py --root . --command create-spec --format table

# structure and pins
bash scripts/eval.sh --check=length
bash scripts/eval.sh --check=recommended-spec-implementation
bash scripts/eval.sh --check=artifact-integrity
bash scripts/eval.sh --check=spec-status
bash scripts/eval.sh --check=supersession-writeback
bash scripts/eval.sh --check=preamble
bash scripts/eval.sh                       # full sweep vs. the pre-spec baseline

# skills
bash scripts/lint-skill.sh skills/*/SKILL.md
bash scripts/gen-skill.sh --check
python3 scripts/eval-leanness.py --root .  # required_skills_declarations, skills ceiling

# reachability (each skill: exactly one inline Read, inside its step; nothing declared)
grep -n 'required_skills:' commands/create-spec.md          # expect NO output
grep -n 'Read skills/' commands/create-spec.md              # expect exactly 6 lines
grep -c 'Read skills/' commands/create-spec.md              # expect 6
python3 -c "import json,subprocess; d=json.loads(subprocess.run(['python3','scripts/measure-invocation.py','--root','.','--command','create-spec'],capture_output=True,text=True).stdout)['commands']['create-spec']; print(d['eager_skills'], d['conditional_skills'], d['unresolved_skills'], d['command_bytes']+d['conditional_bytes'])"
# eager_skills must be [] ; conditional_skills must hold the 5 new names plus
# error-rescue-mapping ; last value is the ceiling expression: must be <= 52,570
python3 scripts/measure-invocation.py --root . --command create-spec | grep -i 'both ways'   # expect no output

# placement (BR3 — no tool checks this; read the line numbers)
grep -n 'Read skills/' commands/create-spec.md
# each hit must fall INSIDE the phase-list step named in spec.md § Load placement.
# A hit above the first phase heading is a hoisted read and a BR3 defect.

# forbidden strings must stay absent
grep -n 'skip specs with `Status: Complete`' commands/create-spec.md   # expect no output
grep -n 'grep -v archive' commands/create-spec.md                      # expect no output

# no drift in the two frozen regions
diff <(git show <base>:commands/create-spec.md | sed -n '/^## Recommended Mode/,/^## Command Process/p') \
     <(sed -n '/^## Recommended Mode/,/^## Command Process/p' commands/create-spec.md)
diff <(git show <base>:commands/create-spec.md | sed -n '/^## Completion/,/^## References/p') \
     <(sed -n '/^## Completion/,/^## References/p' commands/create-spec.md)
```

`<base>` is the spec's base commit on `phase/10-progressive-disclosure`. The two `diff`s must be empty — the `## Command Process` anchor in the first will move as extraction proceeds, so Story 6 re-anchors it on whatever heading follows `## Recommended Mode` in the final file and states which anchor it used.

## Error & Rescue Map

| Operation | What can fail | Planned handling | How it is caught |
|---|---|---|---|
| Extract the `--recommend` matrix by mistake | `check_recommended_spec_implementation` row parse returns `{}`; 8 assertions fail | Business Rule 6 forbids it; revert the extraction | `bash scripts/eval.sh --check=recommended-spec-implementation` |
| A pinned literal moves into a skill | `require_literal` finding on `commands/create-spec.md` | Restore the sentence to the command; the skill keeps the surrounding prose only | full `eval.sh` sweep after every story |
| Table rows reformatted while "tidying" | Row keys no longer match the eight expected strings | Matrix is byte-frozen | matrix scenario |
| An inline read is **hoisted** to the command preamble "so the reader sees the skills up front" | Every run pays every skill; the eager mechanism is reproduced by hand; `ceiling_bytes` is unchanged so nothing reports it | Business Rule 3: narrowest step, no hoisting. **No tool catches this** | Story 6 placement evidence: `grep -n 'Read skills/'` line numbers checked against § *Load placement* |
| `required_skills:` is added back "for discoverability" | Skills move from `conditional_bytes` into `floor_bytes`; the floor bar is blown and the phase's result inverts | Out of Scope; maintainer ruling 2026-08-12 | `grep -n 'required_skills:'` returns nothing; `eager_bytes == 0` |
| A skill is both declared **and** inline-read | The declaration wins, the inline read buys nothing, and the measurement misleads | Declare nothing | `measure-invocation.py` emits its "loads both ways" warning |
| `contract-lock`'s read drifts below Step 1.4b while "tidying" the phase list | `--recommend` auto-locks a contract using a procedure it has not loaded — an *unreviewed* wrong lock | Business Rule 3's ordering half; the read sits at Step 1.3b | Story 2 + Story 6 evidence; no automated check exists |
| `spec-source-prepopulation`'s read is placed before the mode branch | The largest skill becomes a cost on every standard run | § *Load placement* puts it inside the `--from-*` Step 0 | placement grep |
| Worst-path ceiling lands above 77,530 after compression | Business Rule 1 bar missed | Written justification: measured overage, compression attempted with its yield, explicit maintainer decision. Never a silently trimmed skill | Story 6 evidence; Compression Ledger measured column |
| Skill created but never referenced | `grep -c 'Read skills/'` finds no call for it | Story 6 wires all five in one commit, one read each, at the named step | Business Rule 7 check |
| Inline read name typo | `measure-invocation.py` lists it under `unresolved_skills` and warns the ceiling is a lower bound. `eval-leanness.py check_required_skills` **will not catch it** — that check reads `required_skills:` frontmatter only, and there is none | Fix the name | `unresolved_skills` must be empty |
| Name collides with a sibling spec's claim | Two near-duplicate skills for one capability | Collision protocol: first writer owns; the later spec declares the existing skill with an ADR-014 `type: promotion` entry | manifest grep on name **and head noun**, before `/new-skill` |
| Skills grow past `MAX_SKILLS = 12` | `check_ceilings` warning on the `skills` surface | 19 expected with the pilot's eight landed; warning only, reported and handed to `governor-enforcement`. Cap not raised here | leanness output |
| `skills` surface growth trips the ADR-019 ratchet | unjustified-growth warning | A **bound justification** — `(surface, metric)`-scoped `{date, value, text}` naming this spec, the bytes moved, and the `commands` reduction. Not `--update-baseline`, which moves every surface's floor and records no reason | `.writ/leanness-baseline.json`; leanness output |
| Compression silently drops a rule | Rule inventory row has no destination | Per-story checkoff of every assigned row | rule inventory, Story 6 reconciliation |
| A threshold is "fixed" during relocation (5-7 vs 3-5 vs 7) | Behavioral change disguised as tidying | Preserve verbatim; record the inconsistency in story notes | rule inventory diff |
| `gen-skill.sh --check` delta after a manifest append | Root `SKILL.md` stale | Run `bash scripts/gen-skill.sh` | `--check` in each story's DoD |

## Shadow Paths

Rewritten 2026-08-12 for the inline-read mechanism. Every path below is now a statement about *which reads are issued*, which is the same thing as what the run costs.

- **Happy path** — standard `/create-spec`: reads `requirements-discovery` at 1.3, `contract-lock` at 1.3b, `spec-package-authoring` at 1.5 or 2.2, `user-story-decomposition` at 2.5. **`spec-source-prepopulation` is never read** — the mode branch is not taken — so its 7,809 bytes are not paid. Under the superseded eager design this run paid them on every invocation.
- **Invocation rejected at the `--recommend` matrix** — every skill read sits downstream of the validation gate, so a rejected invocation issues **zero** reads and pays the floor alone. This is the spec's cheapest real path and the clearest demonstration that the mechanism works.
- **`--recommend`, no idea, no unambiguous candidate** — pauses before discovery, after `requirements-discovery` is read but before `contract-lock` would be. The auto-lock cannot fire on this path, so the ordering guarantee is not exercised; on the paths where it *does* fire, `contract-lock`'s Step 1.3b read is what makes it safe.
- **`--from-issue` with a bad path** — the mode branch is taken, so `spec-source-prepopulation` is read at Step 0; its error block then fires. The read precedes the path validation because the validation procedure lives in the skill. The issue file is not modified.
- **`--from-prototype` with a clean tree** — warning and a bounded offer, from the same skill, read at the same point.
- **Platform does not honor an inline `Read`** — no longer a distinct shadow path. `Read skills/<name>/SKILL.md` is an ordinary file read every platform adapter already implements (`adapters/claude-code.md` maps it to the native `Read` tool), and it is the pattern seven shipping commands already use. The `required_skills:` graceful-degradation clause is now irrelevant here because the field is not used. `## References` still lists every skill for a human reader.
- **Documentation-only spec** — `error-rescue-mapping` is never read; the data-flow heuristic in the command is what makes that decision, and it stays in the command. **This run's ceiling equals its floor**, and that fact is the spec's own proof of the mechanism it adopts (Business Rule 12).
