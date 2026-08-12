# No-Drift Inventory — `commands/implement-story.md`

> **Captured:** 2026-08-12, Story 1, **before any edit**.
> **Source:** `git show 9e76d1e:commands/implement-story.md` (52,709 bytes / 989 lines).
> `<base>` = `9e76d1ecf50a6e2ecfe86b673175e5fb12ecce1f` — resolved once, used identically by Stories 5 and 6.
> **Purpose:** Business Rule 2's verification method. Story 6 walks this file row by row and fills `Where it lives now`. **Zero unaccounted rows** is the pass condition. A row whose wording changed is fine; a row whose rule is gone is a defect.
> **Built from the file, not from the technical spec's section ledger** — that ledger is a byte accounting of 36 sections; this is a rule accounting of **281 rules**.

**Categories:** `gate` · `agent-binding` · `skip-rule` · `threshold` · `vocabulary` · `degradation` · `log-string` · `output-var` · `rule` (everything else that is a decision rule, format, or always/never clause).

**Legend for `Where it lives now`:** `cmd` = `commands/implement-story.md`; a skill name = that skill's `SKILL.md`; `cmd + <skill>` only where the rule is genuinely split (contract in the command, procedure in the skill).

---

## A. Frontmatter contract and loop bounds (L1–24)

*Preserved byte-identical by Business Rule / Story 5 AC. Listed so the walk proves it.*

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 1 | 7 | rule | Exit criterion: story header reads `Status: Completed` **and** carries a `> **Commit:**` line holding the full SHA, written once rather than duplicated on re-runs | `commands/implement-story.md` |
| 2 | 8 | rule | Exit criterion: story file ends with a `## What Was Built` section naming files created, files modified and test results, and `user-stories/README.md` progress counts match it | `commands/implement-story.md` |
| 3 | 9 | threshold | Exit criterion: Gate 4 recorded a **100 percent** test pass rate with at least **80 percent** line coverage on new files; no gate skipped without the story being marked DEGRADED instead of Completed | `commands/implement-story.md` |
| 4 | 11–14 | threshold | `loop.unit: review_cycle`, `max_iterations: 3`, `on_exhaustion: escalate`; **one shared counter across four increment sites** — Gate 3 FAIL, Gate 3.5 Reject, Gate 3.5 Modify spec, Gate 4.5 FAIL — not four separate budgets | `commands/implement-story.md` |
| 5 | 16–19 | threshold | Nested `testing_cycle`, `max_iterations: 2`, `on_exhaustion: escalate` | `commands/implement-story.md` |
| 6 | 20–23 | threshold | Nested `agent_self_fix`, `max_iterations: 3`, `on_exhaustion: escalate`; transcribes `MAX_SELF_FIX_ITERATIONS = 3` declared in `agents/coding-agent.md` and `agents/testing-agent.md` | `commands/implement-story.md` |

## B. Overview, Required Artifacts, Invocation (L28–48)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 7 | 30 | gate | Pipeline order: architecture check → **boundary map (Gate 0.5)** → coding (TDD) → lint/typecheck → review → drift handling → testing → documentation | `commands/implement-story.md` |
| 8 | 32 | rule | This is the per-story execution engine; full spec execution with dependency resolution and parallel batching is `/implement-spec` | `commands/implement-story.md` |
| 9 | 36 | rule | Verify artifacts per the preamble's **Artifact Integrity** rule before starting | `commands/implement-story.md` |
| 10 | 38 | rule | **Required:** active spec folder (`spec.md`, `user-stories/`) | `commands/implement-story.md` |
| 11 | 39 | rule | **Optional:** `.writ/context.md`, `.writ/knowledge/`, `spec-lite.md`, `mockups/` | `commands/implement-story.md` |
| 12 | 45 | rule | `/implement-story` with no argument → interactive, presents story selection | `commands/implement-story.md` |
| 13 | 46 | rule | `/implement-story story-3` → runs that story through the full pipeline | `commands/implement-story.md` |
| 14 | 47 | skip-rule | `--quick` skips arch-check, review and docs (prototyping) | `commands/implement-story.md` |
| 15 | 48 | skip-rule | `--review-only` runs review + test + docs on existing code, no coding phase | `commands/implement-story.md` |

## C. Agent Pipeline diagram (L50–64)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 16 | 53–58 | gate | Ten gates in order with their names: 0 ARCH CHECK, 0.5 BOUNDARY MAP, 1 CODING AGENT, 2 LINT & TYPECHECK, 3 REVIEW AGENT, 3.5 DRIFT RESPONSE, 4 TESTING AGENT, 4.5 VISUAL QA (optional), 5 DOCS | `commands/implement-story.md` |
| 17 | 57 | gate | Gate modality per gate: read-only / inline / TDD / auto / read-only / auto / +coverage / read-only / adaptive | `commands/implement-story.md` |
| 18 | 59–63 | rule | Control flow: Gate 0 ABORT → ask user; Gate 0.5 fix loop; Gate 3 FAIL → back to Gate 1; Gate 3.5 PAUSE → ask user; Gate 4 FAIL → back to Gate 1; **max 3 iterations total across review + visual QA** | `commands/implement-story.md` |

## D. Step 1 and Step 2's numbered list (L68–93)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 19 | 70 | rule | If no argument provided, present story selection from the current spec — **not-started and in-progress** stories | `commands/implement-story.md` |
| 20 | 74 | rule | Read `.writ/context.md` if present (mission, active spec state, recent drift, open issues) — the **first** context item loaded; it primes all subsequent steps | `commands/implement-story.md` |
| 21 | 75 | rule | Read the story file — tasks, acceptance criteria, dependencies | `commands/implement-story.md` |
| 22 | 76 | rule | Read `spec-lite.md` — overall spec context | `commands/implement-story.md` |
| 23 | 77 | rule | Parse context hints and fetch referenced content | `commands/implement-story.md` |
| 24 | 78 | threshold | Load knowledge context — grep `.writ/knowledge/` for entries matching story keywords; assemble optional `knowledge_context` (**≤2KB**) for architecture-check, coding and review agents | `commands/implement-story.md` |
| 25 | 79 | rule | Extract agent-specific spec-lite sections — parse `spec-lite.md` into per-role sections for targeted delivery | `commands/implement-story.md` |
| 26 | 80 | rule | Scan codebase — identify patterns, related files, tech stack | `commands/implement-story.md` |
| 27 | 81 | rule | Check dependencies — warn if upstream stories aren't complete | `commands/implement-story.md` |
| 28 | 82 | rule | Load "What Was Built" from dependencies | `commands/implement-story.md` |
| 29 | 83–87 | rule | Load visual references when the story has a `## Visual References` section: read linked mockup images via vision model; read `mockups/component-inventory.md`; read `.writ/docs/design-system.md`; pass visual context to the coding agent alongside the story tasks | `commands/implement-story.md` |
| 30 | 89–93 | log-string | Incomplete-dependency warning block: `⚠️ Story 5 depends on Story 2 (not yet complete). / Proceeding anyway — some integration points may be unavailable.` | `commands/implement-story.md` |

## E. Parsing Context Hints and Fetching Referenced Content (L95–141)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 31 | 97 | rule | Authoring reference for hint syntax: `.writ/docs/context-hint-format.md` | `story-context-assembly` |
| 32 | 98 | rule | Executable contract: `scripts/story-context.py` is the **sole** implementation that parses hints and fetches content — this step **invokes** it and **does not restate its algorithm** | `commands/implement-story.md` (delegation rule, Step 2) + `story-context-assembly` |
| 33 | 100 | rule | The orchestrator delegates hint parsing and fetching rather than interpreting `## Context for Agents` itself, so targeted context comes from one deterministic tested implementation instead of agent judgment | `story-context-assembly` |
| 34 | 105 | rule | Invocation: `python3 scripts/story-context.py assemble --story <story-file-path> --budget-bytes 21000` | `commands/implement-story.md` (Step 2 invocation fence — pinned literal 1) + `story-context-assembly` |
| 35 | 108 | threshold | `21000` is `FETCHED_CONTEXT_BUDGET_BYTES`; **read the constant's current value from the script and prefer it over the number in prose** — the script, not this file, owns the derivation | `story-context-assembly` |
| 36 | 112 | rule | The script **always exits 0** and prints one JSON object | `story-context-assembly` |
| 37 | 114–121 | rule | Stdout JSON shape: `fetched_context`, `warnings`, `bytes` (per-category + `total`), `truncated` | `story-context-assembly` |
| 38 | 124 | output-var | `fetched_context` JSON key → `fetched_context` output variable — pass through **unchanged**, keyed by category | `story-context-assembly` |
| 39 | 125 | output-var | `warnings` JSON key → `context_warnings` — pass through **verbatim**; already includes the informational "no hints section" log, every parse/fetch warning, and (when `truncated` is true) the truncation warning naming actual vs. budget bytes. **No separate truncation-handling logic here** — the script embeds it | `story-context-assembly` |
| 40 | 126 | rule | `bytes` is an informational byte report for the invocation; not consumed elsewhere in the pipeline beyond logging | `story-context-assembly` |
| 41 | 132 | degradation | Script missing (`scripts/story-context.py` absent, or the invocation cannot start) → warn `⚠️ story-context.py not found — proceeding with spec-lite only`; set `fetched_context` to `{}`; continue | `story-context-assembly` |
| 42 | 133 | degradation | Non-zero exit → warn `⚠️ story-context.py exited non-zero — proceeding with spec-lite only`; `{}`; continue | `story-context-assembly` |
| 43 | 134 | degradation | Malformed stdout (not valid JSON, or lacking the `fetched_context`/`warnings` keys) → warn `⚠️ story-context.py produced unparseable output — proceeding with spec-lite only`; `{}`; continue | `story-context-assembly` |
| 44 | 136 | rule | A broken assembler **degrades context; it never halts the story** — proceed on `spec-lite.md` alone in every row above | `story-context-assembly` |
| 45 | 139–140 | output-var | Output variables of this block: `fetched_context`, `context_warnings` | `story-context-assembly` |

## F. Loading Knowledge Context (L142–195)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 46 | 144 | rule | Load knowledge **after** parsing context hints, so agents inherit durable project knowledge without the maintainer prompting for it | `story-context-assembly` |
| 47 | 148–151 | rule | Keyword sources: story title; the story file's `## Context for Agents` block; file paths in scope from implementation tasks, boundary candidates and context hints | `story-context-assembly` |
| 48 | 152–156 | rule | Normalization, in order: lowercase; split path segments and hyphenated/slashed terms; drop common stop words (`the`, `and`, `story`, `file`, `task`, `spec`, etc.); keep meaningful tokens of **3+ characters** plus exact path fragments like `commands/implement-story.md` | `story-context-assembly` |
| 49 | 160 | degradation | If `.writ/knowledge/` does not exist, **skip silently** | `story-context-assembly` |
| 50 | 161 | rule | Grep `.writ/knowledge/` for keyword matches against frontmatter tags, titles, TL;DR text and body content | `story-context-assembly` |
| 51 | 162–166 | threshold | Scoring weights: **+3** tag match, **+2** title or filename match, **+1** body/content match, **+1** related artifact path matching a file in scope | `story-context-assembly` |
| 52 | 167–170 | rule | Category preference by agent: Architecture Check → `decisions/`, `conventions/`, then other; Coding → all categories with `conventions/` and `glossary/` boosted; Review → `lessons/`, `decisions/`, then other | `story-context-assembly` |
| 53 | 171–180 | rule | Assemble a shared `knowledge_context` markdown block capped at **~2KB**, in the given shape: `## Loaded Knowledge Entries`, then per entry a `###` path heading with `- Category:`, `- Tags:`, `- TL;DR:` lines | `story-context-assembly` |
| 54 | 182 | rule | If the block exceeds 2KB, **keep higher-scoring entries first and truncate lower-scoring details before dropping whole entries** | `story-context-assembly` |
| 55 | 188 | degradation | `.writ/knowledge/` missing → **silent no-op** (not a warning); set `knowledge_context` to empty string | `story-context-assembly` |
| 56 | 189 | degradation | No keyword matches → silent no-op; empty string | `story-context-assembly` |
| 57 | 190 | degradation + log-string | Entry has malformed frontmatter → skip that entry and log `⚠️ Knowledge entry skipped: malformed frontmatter in {path}` | `story-context-assembly` |
| 58 | 191 | degradation + log-string | Context exceeds 2KB → truncate by relevance score and log `ℹ️ knowledge_context truncated to 2KB` | `story-context-assembly` |
| 59 | 194 | output-var | `knowledge_context` — optional markdown block of loaded entries; **empty string** when no relevant entries were found | `story-context-assembly` |

## G. Extracting Agent-Specific Spec-Lite Sections (L196–220)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 60 | 200 | output-var | `spec_lite_for_coding` — content of `## For Coding Agents` (header to next `---` or `##` heading) | `story-context-assembly` |
| 61 | 201 | output-var | `spec_lite_for_review` — content of `## For Review Agents` | `story-context-assembly` |
| 62 | 202 | output-var | `spec_lite_for_testing` — content of `## For Testing Agents` | `story-context-assembly` |
| 63 | 208 | rule | Routing row: **Architecture Check (Gate 0)** ← `spec_lite_for_coding` + `fetched_context` (all categories) + `knowledge_context` | `commands/implement-story.md` (Step 2 routing table — pinned literals 2–6) |
| 64 | 209 | rule | Routing row: **Coding Agent (Gate 1)** ← `spec_lite_for_coding` + `fetched_context` (error maps, business rules) + `knowledge_context` + dependency WWB records | `commands/implement-story.md` (Step 2 routing table — pinned literals 2–6) |
| 65 | 210 | rule | Routing row: **Review Agent (Gate 3)** ← `spec_lite_for_review` + `fetched_context` (business rules, experience) + `knowledge_context` | `commands/implement-story.md` (Step 2 routing table — pinned literals 2–6) |
| 66 | 211 | rule | Routing row: **Testing Agent (Gate 4)** ← `spec_lite_for_testing` + `fetched_context` (shadow paths, edge cases) | `commands/implement-story.md` (Step 2 routing table — pinned literals 2–6) |
| 67 | 212 | rule | Routing row: **Documentation Agent (Gate 5)** ← full spec-lite content + `fetched_context` (all categories) | `commands/implement-story.md` (Step 2 routing table — pinned literals 2–6) |
| 68 | 215 | degradation | Legacy spec-lite without `## For {Role} Agents` headers → use **full** spec-lite content for **all** agents | `story-context-assembly` |
| 69 | 216 | degradation + log-string | Specific section missing → fall back to full spec-lite for that agent and log `⚠️ Spec-lite.md missing "## For {Role} Agents" section — using full content` | `story-context-assembly` |
| 70 | 217 | degradation | `fetched_context` empty (no hints parsed or all references missing) → agents receive the spec-lite section only (still an improvement over the full file for non-legacy specs) | `story-context-assembly` |

## H. Loading "What Was Built" from Dependencies (L221–340)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 71 | 223 | rule | Format reference: `.writ/docs/what-was-built-format.md` | `dependency-context-loading` |
| 72 | 225 | rule | Applies to stories with dependencies (from the story's `## User Story` or `Dependencies:` metadata); purpose is cross-story continuity from **completed upstream** stories | `dependency-context-loading` |
| 73 | 230–232 | rule | Parse dependencies: check `> **Dependencies:** Story 1, Story 2` metadata; or parse the `## User Story` section for dependency mentions; extract story numbers or IDs | `dependency-context-loading` |
| 74 | 235–236 | rule | Locate files by constructing `.writ/specs/{spec-folder}/user-stories/story-{N}-{slug}.md`, then read each | `dependency-context-loading` |
| 75 | 239 | rule | Completion check: look for `> **Status:** Completed ✅` in the story file header | `dependency-context-loading` |
| 76 | 240–244 | degradation + log-string | Dependency not complete → log `⚠️ Story 3 depends on Story 1 (not yet complete). / Proceeding anyway — some integration points may be unavailable.` and continue | `dependency-context-loading` |
| 77 | 247 | rule | For each **completed** dependency, locate its `## What Was Built` section | `dependency-context-loading` |
| 78 | 248 | rule | Read the entire section — from `## What Was Built` to the next `##` heading or EOF | `dependency-context-loading` |
| 79 | 249–253 | degradation + log-string | **Skip reverted records:** a section beginning with a `> **Reverted:**` banner is **not authoritative**; do NOT load it as live dependency context — skip it (or flag it as reverted) and log `ℹ️ Story N's "What Was Built" is marked Reverted — skipping as non-authoritative dependency context.` See `.writ/docs/what-was-built-format.md → Reverted Records` | `commands/implement-story.md` ("Skip reverted records" — pinned literal 11) + `dependency-context-loading` |
| 80 | 254–258 | degradation + log-string | Section not found → log `⚠️ Story 1 is marked complete but has no "What Was Built" record. / Proceeding with reduced context — cross-story continuity may be degraded.` | `dependency-context-loading` |
| 81 | 261 | rule | For each WWB record, count lines | `dependency-context-loading` |
| 82 | 262 | threshold | If a record exceeds **1000 lines**, truncate using the priority order below | `dependency-context-loading` |
| 83 | 263 | rule | Truncation tier **1**: Files Created — keep full (highest priority) | `dependency-context-loading` |
| 84 | 264 | rule | Truncation tier **2**: Files Modified — keep full | `dependency-context-loading` |
| 85 | 265 | rule | Truncation tier **3**: Implementation Decisions — keep full if space allows, otherwise first **20 lines** | `dependency-context-loading` |
| 86 | 266 | rule | Truncation tier **4**: Test Results — keep the summary line only, drop the detailed test list | `dependency-context-loading` |
| 87 | 267 | rule | Truncation tier **5**: Review Outcome — keep full | `dependency-context-loading` |
| 88 | 268 | rule | Truncation tier **6**: Deviations from Spec — keep DEV-IDs and titles, truncate details to first **2 lines** each | `dependency-context-loading` |
| 89 | 269 | rule | Truncation tier **7**: Lessons Learned (if present) — drop if space needed | `dependency-context-loading` |
| 90 | 270 | log-string | Truncation log: `⚠️ Truncated Story {N} "What Was Built" record ({original} → 1000 lines)` | `dependency-context-loading` |
| 91 | 271 | rule | Preserve markdown structure in the truncated version | `dependency-context-loading` |
| 92 | 272 | rule | **Only load direct dependencies — never transitive** (Story 3 loads Story 2's WWB, not Story 1's even if Story 2 depended on Story 1) | `dependency-context-loading` |
| 93 | 275–285 | rule | Aggregate: collect all WWB sections (full or truncated) from completed dependencies and format as `## Dependency Context: What Was Built in Upstream Stories` with one `### From Story N: {story title}` block per record | `dependency-context-loading` |
| 94 | 288–290 | rule | Pass to the coding agent: include the aggregated records in its prompt, **positioned after story content and spec context, before implementation tasks**, so the agent sees what dependencies actually produced | `dependency-context-loading` |
| 95 | 294 | degradation | Dependency incomplete → continue with warning | `dependency-context-loading` |
| 96 | 295 | degradation | Dependency complete but no WWB section → continue with warning, note degraded context | `dependency-context-loading` |
| 97 | 296 | degradation | Multiple dependencies, some with WWB and some without → include available records, log warnings for the missing | `dependency-context-loading` |
| 98 | 297 | degradation | **No dependencies → skip this step entirely** | `dependency-context-loading` |
| 99 | 299–339 | rule | Worked example "Example Coding Agent Context (with WWB)" — illustrates the aggregation format specified at L274–286. *Compression target C1: a duplicate of a format specified above it, deletable under BR2 only if the format itself survives* | **contracted (C1)** — the aggregation format it illustrated is in `dependency-context-loading` § 6; the worked copy is deleted |

## I. `.writ/context.md` — Format & Regeneration (L341–396)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 100 | 343 | rule | `.writ/context.md` is the running project context snapshot, **always fully regenerated** (never patched or appended) by `implement-story`, `implement-spec` and `status`; it lives at the project root, not inside a spec folder | `commands/implement-story.md` (Step 4 item 3, once-here-never-between-gates) + `project-context-snapshot` |
| 101 | 347–378 | rule | Schema, six sections in order: `# Writ Project Context`; `> Last Updated: {ISO 8601 timestamp}`; `## Product Mission`; `## Active Spec`; `## Artifact Map`; `## Recent Drift`; `## Open Issues` | `project-context-snapshot` |
| 102 | 354 | rule | Product Mission body = 1–3 sentences from `.writ/product/mission-lite.md` | `project-context-snapshot` |
| 103 | 358–361 | rule | Active Spec fields: `**Spec:** {spec-folder-id} — {spec title}`, `**Status:**`, `**Story:** {N} of {M} — {title} ({status})`, `**Progress:** {X}/{Y} tasks complete ({Z}%)` | `project-context-snapshot` |
| 104 | 365–369 | rule | Artifact Map items: Product (roadmap/mission/mission-lite present-or-missing), Active spec path (+ spec-lite.md, user-stories/, sub-specs/ if present), Knowledge ({N} entries or "none"), Docs ({count} files), Integrity | `project-context-snapshot` |
| 105 | 373 | threshold | Recent Drift = **last 3 entries** from `.writ/specs/{spec}/drift-log.md` | `project-context-snapshot` |
| 106 | 377 | rule | Open Issues = count of files in `.writ/issues/` subdirectories | `project-context-snapshot` |
| 107 | 381 | degradation | `mission-lite.md` absent → omit the "Product Mission" section entirely | `project-context-snapshot` |
| 108 | 382 | degradation | No active spec → omit the "Active Spec" section | `project-context-snapshot` |
| 109 | 383 | degradation | `drift-log.md` absent or empty → omit the "Recent Drift" section | `project-context-snapshot` |
| 110 | 384 | degradation | `.writ/issues/` absent → omit the "Open Issues" section | `project-context-snapshot` |
| 111 | 387–388 | rule | Artifact Map is present-conditional: omit sub-items whose files are absent — **the Integrity line always renders** | `commands/implement-story.md` (Step 4 item 3 — pinned literals 7–8) + `project-context-snapshot` |
| 112 | 389–391 | vocabulary | Integrity reflects the preamble's Required/Optional semantics: `✅ all required present` when every required artifact exists, otherwise `⚠️ missing required: <list>` | `commands/implement-story.md` (Step 4 item 3 — required by `eval-artifact-integrity.py:96`) + `project-context-snapshot` |
| 113 | 392–393 | rule | Rewritten **wholesale** on every regeneration — never appended or patched. **No separate index/pointer file is ever created** | `project-context-snapshot` |

## J. Step 3 preamble (L397–404)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 114 | 399 | rule | Context refresh: `.writ/context.md` is regenerated **once at Story Completion (Step 4)**, not between gates; each write replaces the entire file — do not append, merge or patch | `commands/implement-story.md` |
| 115 | 401 | rule | File-creation discipline: agents create only files explicitly listed in the story's implementation tasks. Verification results, validation reports, AC checklists, test plans and other analysis artifacts belong in the agent's **structured output** — never as new files on disk. The orchestrator does not commit files that aren't in the task list or a known pipeline output (drift-log, context.md, story status updates) | `commands/implement-story.md` |

## K. Gate 0 — Architecture Check (L405–426)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 116 | 407 | agent-binding | Agent: `agents/architecture-check-agent.md` | `commands/implement-story.md` |
| 117 | 408 | skip-rule | Skip in `--quick` mode and `--review-only` mode | `commands/implement-story.md` |
| 118 | 410 | rule | Spawns a **read-only** sub-agent to review the planned approach before any code is written | `commands/implement-story.md` |
| 119 | 413–416 | rule | Reviews: approach viability; integration risk; complexity assessment; missing considerations (migrations, env changes, error handling) | `commands/implement-story.md` |
| 120 | 419 | vocabulary | **PROCEED** → continue to coding | `commands/implement-story.md` |
| 121 | 420 | vocabulary | **CAUTION** → continue, inject warnings into the coding agent prompt | `commands/implement-story.md` |
| 122 | 421 | vocabulary | **ABORT** → present findings to user, ask whether to proceed / modify / skip | `commands/implement-story.md` |
| 123 | 423 | rule | Context routing: pass `spec_lite_for_coding` as `spec_lite_content`; if agent-specific sections are unavailable pass full spec-lite; also pass `fetched_context` if hints were parsed in Step 2; pass `knowledge_context` when populated | `commands/implement-story.md` |

## L. Gate 0.5 — Boundary Computation (L427–519)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 124 | 429 | agent-binding | Agent: **None** — an inline orchestration step (data transformation, not a judgment call) | `commands/implement-story.md` |
| 125 | 430 | skip-rule | Skip in `--quick` mode, `--review-only` mode, and the `/prototype` path | `commands/implement-story.md` |
| 126 | 432 | rule | Before Gate 1 compute a `boundary_map` so coding and review agents have explicit **owned / readable / out-of-scope** scope | `commands/implement-story.md` |
| 127 | 432 | rule | Boundaries are **advisory**: the coding agent **flags** cross-boundary edits in its output; the review agent **verifies** compliance at Gate 3. **There is no hard file locking** | `commands/implement-story.md` |
| 128 | 434 | skip-rule | Not applicable to `/prototype`: `commands/prototype.md` does not run `implement-story`; that path stays boundary-free. Gate 0.5 exists only on the full pipeline | `commands/implement-story.md` |
| 129 | 438 | output-var | Pass the block as the `boundary_map` parameter to the coding agent and review agent; use **file paths or globs**; annotate entries when needed | `commands/implement-story.md` (Gate 0.5 → Gates 1 and 3 routing) + `boundary-map-computation` |
| 130 | 440–454 | rule | Schema, three headings: **Owned** (create or modify); **Readable** (import/reference; do not modify unless you emit a `BOUNDARY_DEVIATION`); **Out-of-scope** (do not modify; if you must, emit `BOUNDARY_VIOLATION`), whose body line is "Everything not listed above as Owned or Readable" | `boundary-map-computation` |
| 131 | 448 | rule | Annotation `_(imported by owned files)_` marks Readable entries added by the import scan | `boundary-map-computation` |
| 132 | 457 | rule | Flag `(overlap: …)` — the file area appears in **assess-spec Check 5** as shared between stories; still **Owned** if the current story's tasks explicitly name that path, otherwise prefer **Readable** with this note | `boundary-map-computation` |
| 133 | 458 | rule | Flag `(⚠️ high-overlap: …)` — Check 5 severity was **warn** (e.g. three+ stories share the area); the review agent treats it as **higher scrutiny** for boundary compliance and integration | `boundary-map-computation` |
| 134 | 462 | rule | The computation steps **run in order** | `boundary-map-computation` |
| 135 | 464–466 | rule | Step 1 — collect candidate OWNED paths: from the story file's `## Implementation Tasks` and inline task bullets, extract paths matching common phrasing (`` `path` ``, "Modify `path`", "Create `path`", "Update `path`", "Add to `path`", file paths in fenced or inline code that look like project paths — contain `/` or `.`); from `sub-specs/technical-spec.md` **File Map** / architecture sections, a row tied to **this** story → OWNED, a row tied to **another** story → overlap hint for step 5 | `boundary-map-computation` |
| 136 | 468–470 | rule | Step 2 — normalize: deduplicate; preserve globs as written; if a path is listed as both owned and readable, **Owned wins unless step 3 or 4 demotes it** | `boundary-map-computation` |
| 137 | 472–474 | threshold | Step 3 — import graph, **depth 1**: for each **existing** OWNED file, list **direct** imports/references the orchestrator can resolve (language-aware scan: `import`, `require`, `#include`, etc.); imported files not already OWNED → add to **Readable** with `_(imported by owned files)_` | `boundary-map-computation` |
| 138 | 476–478 | rule | Step 4 — Gate 0 overrides: parse Architecture Check's `### Warnings for Coding Agent`; for each path the warning says **not** to modify, demote it — OWNED → **Readable** plus `_(arch-check: do not modify — boundary override)_`; if it must not even be edited with a deviation, mark it out-of-scope in the narrative (list under Readable with strong wording, or exclude from Owned and treat as readable-only for review). Prefer matching explicit `` `...` `` paths from warnings | `boundary-map-computation` |
| 139 | 480–484 | rule | Step 5 — assess-spec Check 5 (**optional**): if persisted overlap data exists, merge — paths/areas flagged as shared and **not** explicitly OWNED by this story's tasks → **Readable** with `_(overlap: …)_`; items with **warn** / "three+ stories" / **⚠️** → add `_(⚠️ high-overlap: …)_` on the Readable line (or on Owned if the tasks own the path but overlap remains). **If no persisted data → skip this step**; baseline map from steps 1–4 only | `boundary-map-computation` |
| 140 | 486–489 | degradation + log-string | Step 6 — fallback when steps 1–2 yield **no** OWNED paths: infer approximate directories from task wording and list **candidate Owned** globs (e.g. `src/auth/**`) **only** if the story clearly implies that directory; emit the visible warning `⚠️ boundary_map approximate — no concrete file paths in tasks; review agent should use extra caution.` | `boundary-map-computation` |
| 141 | 491–493 | rule | Step 7 — **Readable** = union of steps 3, 4 and 5 additions plus any tech-spec "other story" files, minus anything still OWNED. **Out-of-scope is implicit** (everything else) — do not enumerate the whole tree; the schema sentence is enough | `boundary-map-computation` |
| 142 | 495 | threshold | Performance: heuristic string extraction + shallow import scan only; target **< 10 seconds** pre–Gate 1 | `boundary-map-computation` |
| 143 | 499 | rule | Assess-spec output is often chat-only; to feed Check 5 into Gate 0.5, persist overlap data in either location below | `boundary-map-computation` |
| 144 | 501–512 | rule | Persistence location 1 (**recommended**): `.writ/specs/{spec-folder}/assessment-report.md`, containing a section headed exactly `## Check 5 — File overlap`, with an optional table (File / area · Stories sharing · Severity note/warn); **warn** maps to high-overlap annotations on the boundary map | `boundary-map-computation` |
| 145 | 514 | rule | Persistence location 2 (**optional**): the same `## Check 5 — File overlap` section embedded in `user-stories/README.md` or `spec.md` / `spec-lite.md` notes — same parsing rules | `boundary-map-computation` |
| 146 | 516 | degradation | If no such section exists in the active spec folder, Gate 0.5 proceeds **without** Check 5 data (graceful degradation) | `boundary-map-computation` |

## M. Gate 1 — Coding Agent (L520–551)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 147 | 522 | agent-binding | Agent: `agents/coding-agent.md` | `commands/implement-story.md` |
| 148 | 523 | skip-rule | Skip in `--review-only` mode | `commands/implement-story.md` |
| 149 | 525 | rule | Spawns the coding agent to run the red → green → refactor loop via `Read skills/tdd-cycle/SKILL.md`, with full story context, optional `knowledge_context`, any arch-check warnings, and `boundary_map` from Gate 0.5. **The gate owns *when* coding runs, the context it routes, and `STATUS: BLOCKED` handling; the skill owns *how* the test-first cycle runs** | `commands/implement-story.md` |
| 150 | 527 | rule | Context routing: pass `spec_lite_for_coding` as `spec_lite_content` and relevant `fetched_context` (error maps, business rules); pass `knowledge_context` **after** spec context and **before** dependency records when populated; if dependency stories have completed WWB records, pass aggregated `dependency_wwb_context` **after knowledge context, before implementation tasks** | `commands/implement-story.md` |
| 151 | 529 | skip-rule | When Gate 0.5 was skipped (`--quick`, `--review-only`): pass `boundary_map` = the literal `(none)` and do **not** pass a boundary block — agents treat `(none)` as "no boundary checking" | `commands/implement-story.md` |
| 152 | 531 | rule | Report: files changed, tests written, deviations from plan, concerns | `commands/implement-story.md` |
| 153 | 533–548 | rule | On `STATUS: BLOCKED` (agent hit `MAX_SELF_FIX_ITERATIONS = 3`), surface to the user **immediately** with an `AskQuestion` titled "Coding Agent Blocked", question id `blocked_action`, prompt carrying agent name, `FAILURE` and `PARTIAL_STATE`, and three options: `retry` (restart Gate 1 with fresh context), `skip` (skip gate with warning — continue pipeline, story marked degraded), `abort` (abort pipeline — preserve current state) | `commands/implement-story.md` |
| 154 | 550 | rule | Skip with warning: continue the pipeline but add a visible `⚠️ DEGRADED` flag to the final story report. The story is **NOT** marked `Completed ✅` — it is marked `In Progress` with the note *"Gate 1 skipped after BLOCKED — review required."* | `commands/implement-story.md` |

## N. Gate 2 — Lint, Typecheck & Format (L554–568)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 155 | 556 | agent-binding | Runs **inline** — no sub-agent needed | `commands/implement-story.md` |
| 156 | 558–561 | rule | Auto-detect and run project linters: Node/TS `tsc --noEmit`, `eslint`, `prettier --check`; Python `mypy`, `ruff`, `black --check`; Rust `cargo check`, `cargo clippy`, `cargo fmt --check` | `commands/implement-story.md` |
| 157 | 564 | rule | On failure step 1: auto-fix what's fixable (`eslint --fix`, `prettier --write`, `black`, `cargo fmt`) | `commands/implement-story.md` |
| 158 | 565 | rule | On failure step 2: re-run checks | `commands/implement-story.md` |
| 159 | 566 | rule | On failure step 3: if typecheck still fails → send errors back to the coding agent | `commands/implement-story.md` |
| 160 | 567 | rule | On failure step 4: if still failing after auto-fix → flag for the review agent | `commands/implement-story.md` |

## O. Gate 2.5 — Change Surface Classification (L571–591)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 161 | 573 | agent-binding | Runs **inline** — no sub-agent needed | `commands/implement-story.md` |
| 162 | 575 | rule | After lint/typecheck passes, classify the change surface from the files the coding agent created or modified; the classification determines how the review agent allocates attention. Optionally cross-check those paths against `boundary_map` (Gate 0.5) when present — e.g. an unexpected **full-stack** classification for a file listed as Readable may warrant a stricter review posture | `commands/implement-story.md` |
| 163 | 579 | vocabulary | **style-only** — only CSS/SCSS/Tailwind files changed, or only `className`/`style` props modified in component files (e.g. `max-h-[85vh]`, colors, responsive tweaks, CSS module changes) | `change-surface-classification` |
| 164 | 580 | vocabulary | **single-component** — changes scoped to one component file (state, handlers, props, JSX) | `change-surface-classification` |
| 165 | 581 | vocabulary | **cross-component** — shared code changed: hooks, utils, context, types used by multiple components | `change-surface-classification` |
| 166 | 582 | vocabulary | **full-stack** — API routes, schema, migrations, auth, middleware, or multiple system layers | `change-surface-classification` |
| 167 | 585 | rule | Heuristic step 1: list all files created/modified from the coding agent output | `change-surface-classification` |
| 168 | 586 | rule | Heuristic step 2: if ALL changes are `.css`, `.scss`, `.module.css`, Tailwind config, or only `className`/`style` prop changes in `.tsx`/`.jsx` → **style-only** | `change-surface-classification` |
| 169 | 587 | rule | Heuristic step 3: if changes touch exactly one component file (plus its test file) → **single-component** | `change-surface-classification` |
| 170 | 588 | threshold | Heuristic step 4: if changes touch shared code (files in `hooks/`, `utils/`, `context/`, `lib/`, or files imported by **>3** other files) → **cross-component** | `change-surface-classification` |
| 171 | 589 | rule | Heuristic step 5: if changes touch API routes, database schema, migrations, auth or middleware → **full-stack** | `change-surface-classification` |
| 172 | 590 | rule | Heuristic step 6: **when ambiguous, classify UP one level** (prefer more scrutiny over less) | `change-surface-classification` |

## P. Gate 3 — Review Agent (L594–615)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 173 | 596 | agent-binding | Agent: `agents/review-agent.md` | `commands/implement-story.md` |
| 174 | 598 | rule | Spawns a **read-only** sub-agent for code review | `commands/implement-story.md` |
| 175 | 600 | rule | Input: all standard review inputs plus `spec_lite_for_review` as `spec_lite_content` for drift analysis, optional `knowledge_context`, and `change_surface` (from Gate 2.5) to guide review depth allocation; also `boundary_map` (the same markdown block as Gate 0.5) and, if present, a one-line `boundary_overlap_summary` distilled from Readable lines carrying `overlap` or `high-overlap`. If agent-specific sections are unavailable (legacy spec-lite), pass full spec-lite content | `commands/implement-story.md` |
| 176 | 603–608 | rule | Reviews: acceptance criteria verification; code quality (patterns, errors, readability); security (injection, auth, secrets, vulnerable deps); test coverage (all AC covered? edge cases?); integration (breaking changes, circular deps, migrations); **drift analysis** — compare implementation against spec contract and classify deviations | `commands/implement-story.md` |
| 177 | 611 | vocabulary | **PASS** → continue to testing (may include Small or Medium drift) | `commands/implement-story.md` |
| 178 | 612 | vocabulary | **FAIL** → send feedback to the coding agent for fixes | `commands/implement-story.md` |
| 179 | 613 | vocabulary | **PAUSE** → Large drift detected; surface the conflict to the user before continuing | `commands/implement-story.md` |
| 180 | 615 | threshold | Review loop: **Max 3 iterations across review and visual QA gates** (Gate 3 FAIL → recode, Gate 3.5 "Reject" → recode, Gate 3.5 "Modify spec" → re-review, Gate 4.5 FAIL → recode all count). Those four sites share **one** counter — not four independent budgets. Gate 4 testing failures have a separate **2-iteration** cap. After either cap → escalate to the user. Both caps are declared as `loop.max_iterations` and the nested `testing_cycle` entry in this file's frontmatter with `on_exhaustion: escalate`: the existing `AskQuestion` escalations **are** the implementation, and **no cap may be silently continued past** | `commands/implement-story.md` |

## Q. Gate 3.5 §A — Drift Response (L617–669)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 181 | 619 | rule | Format references: `.writ/docs/drift-report-format.md`, `.writ/docs/what-was-built-format.md` | `commands/implement-story.md` |
| 182 | 621 | rule | After the review agent returns, perform **two** operations (§A drift response, §B WWB extraction) | `commands/implement-story.md` |
| 183 | 625 | rule | Inspect the `### Drift Analysis` section; handle by severity | `drift-triage` |
| 184 | 627 | vocabulary | **Small drift** = naming, cosmetic — spec intent preserved | `commands/implement-story.md` (Gate 3.5 § A severity stub) + `drift-triage` |
| 185 | 628–629 | rule | Small: capture the exact **pre-edit SHA-256**, auto-amend **only** `spec-lite.md`, and append **one unique `DEV-NNN` entry** to `drift-log.md` | `drift-triage` |
| 186 | 630–632 | rule | Small, recommended mode: return a canonical `recommend-spec-lite-review-v1` result bound to execution ID, story ID, `outcome: passed`, `drift_severity: small`, the DEV-ID list, and a **non-empty** summary | `drift-triage` |
| 187 | 633–636 | rule | Small: the parent must **durably** call `scripts/recommend-state.py record-spec-lite-amendment` with the state, repository, story ID, DEV ID, prior SHA-256 and review-result file before continuing. **A missing acknowledgment blocks** | `drift-triage` |
| 188 | 637 | rule | Small: continue **PASS** | `drift-triage` |
| 189 | 638 | rule | Small: **always** include spec-lite changes in the pipeline summary | `drift-triage` |
| 190 | 640 | vocabulary | **Medium drift** = scope/integration impact — spec intent met with notable changes | `commands/implement-story.md` (Gate 3.5 § A severity stub) + `drift-triage` |
| 191 | 641–643 | rule | Medium: flag with a ⚠️ warning in pipeline output; log to `drift-log.md`; continue **PASS** | `drift-triage` |
| 192 | 645 | vocabulary | **Large drift** = fundamental deviation — spec intent NOT met or constraints violated | `commands/implement-story.md` (Gate 3.5 § A severity stub) + `drift-triage` |
| 193 | 646–648 | rule | Large: **PAUSE** the pipeline; present to the user with options accept deviation / reject (send back to coding agent) / modify spec; **wait for the user decision** before continuing | `commands/implement-story.md` (Gate 3.5 § A — Large PAUSE is orchestration) + `drift-triage` |
| 194 | 651 | rule | Overall drift = **highest severity present**. **Mixed runs pause for Large while still auto-amending Small** deviations | `drift-triage` |
| 195 | 652 | rule | Only `spec-lite.md` is auto-modified. Full `spec.md` is **never** auto-modified — it remains the human-approved contract | `commands/implement-story.md` (Gate 3.5 § A) + `drift-triage` |
| 196 | 653 | rule | Log all drift to `.writ/specs/[spec-folder]/drift-log.md` — **append-only, never modify existing entries**. Continue DEV-ID numbering from the highest existing entry | `drift-triage` |
| 197 | 654–657 | rule | Recommended mode: **never batch** multiple spec-lite byte revisions into one amendment record — each record must form a **contiguous prior/resulting digest link**. Duplicate/missing DEV IDs, a broken chain, or another locked-artifact mutation **blocks reconciliation** | `drift-triage` |
| 198 | 659–668 | rule | Drift-log entry format example (`#### [DEV-003] …` with **Severity**, **Spec said**, **Implementation did**, **Resolution**, **Spec-lite updated** fields). *Compression target C5: the authoritative format is `.writ/docs/drift-report-format.md`, cited two lines earlier* | **contracted (C5)** — `.writ/docs/drift-report-format.md` owns the entry format and is cited by `drift-triage` and by the command |

## R. Gate 3.5 §B — "What Was Built" Data Extraction (L670–733)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 199 | 672 | rule | Extract implementation data from review agent output and store it in orchestrator state for later use at Gate 5. **Parse defensively with graceful degradation** | `commands/implement-story.md` (Gate 3.5 § B) + `what-was-built-authoring` |
| 200 | 676–679 | rule | **Files Created/Modified (mandatory)**: source = coding agent output sections inside the review agent response; parse `### Files Created` and `### Files Modified`; extract file paths (in backticks) and descriptions | `what-was-built-authoring` |
| 201 | 680 | degradation | Files fallback: if the sections are missing, run `git diff --name-status` against branch start | `what-was-built-authoring` |
| 202 | 681 | degradation + log-string | Files validation: if no files found, log `⚠️ "What Was Built" record incomplete — no files found` and continue with **empty lists** | `what-was-built-authoring` |
| 203 | 683–686 | degradation | **Implementation Decisions (best-effort)**: source `### Implementation Decisions`; parse list items or paragraphs; fallback — **omit the section** in the final record | `what-was-built-authoring` |
| 204 | 688–691 | degradation | **Test Results (best-effort)**: source review agent `### Test Coverage` and Gate 4 results if available; extract coverage percentages and verification approach; fallback `**Verification:** N/A` | `what-was-built-authoring` |
| 205 | 693–694 | rule | **Review Outcome — Result (mandatory)**: parse `### REVIEW_RESULT: [PASS/FAIL/PAUSE]` | `what-was-built-authoring` |
| 206 | 695 | degradation | Review Outcome — **Drift (best-effort)**: parse `### Drift Analysis → **Overall Drift:** [level]` | `what-was-built-authoring` |
| 207 | 696 | degradation | Review Outcome — **Security (best-effort)**: parse `### Security Assessment → **Risk Level:** [level]` | `what-was-built-authoring` |
| 208 | 697 | degradation | Review Outcome — **Boundary Compliance (best-effort)**: parse `### Boundary Compliance → **Summary:**` line | `what-was-built-authoring` |
| 209 | 698 | rule | Review Outcome — **Iteration count**: tracked in the orchestrator (number of Gate 3 review loops) | `what-was-built-authoring` |
| 210 | 699 | degradation | Review Outcome validation: if Result is missing, **log an error and use "Unknown"** | `what-was-built-authoring` |
| 211 | 700 | degradation | Review Outcome fallbacks for missing best-effort fields: `"None"` / `"Not assessed"` / omit | `what-was-built-authoring` |
| 212 | 702–706 | degradation | **Deviations from Spec (best-effort)**: source review agent `### Drift Analysis` deviation entries; parse `#### [DEV-NNN]` entries with all fields; **preserve DEV-ID numbering**; fallback — if "Overall Drift: None", use `"None"` | `what-was-built-authoring` |
| 213 | 710–728 | output-var | Store a `what_was_built_data` object with fields: `implementation_date` (YYYY-MM-DD), `files_created`, `files_modified`, `implementation_decisions`, `test_results{verification, coverage, details}`, `review_outcome{result, iteration_count, drift, security, boundary_compliance}`, `deviations` (full DEV entries). *Compression target C2: restates the field list the Formatting Template already enumerates* | **contracted (C2)** — the field list survives once, in `what-was-built-authoring`'s extraction sources and Formatting Template |
| 214 | 730 | rule | **Do NOT append to the story file yet** — that happens at Gate 5 / Step 4 after documentation completes | `commands/implement-story.md` (Gate 3.5 § B) |

## S. Gate 4 — Testing Agent (L734–771)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 215 | 736 | agent-binding | Agent: `agents/testing-agent.md` | `commands/implement-story.md` |
| 216 | 738 | rule | Context routing: pass `spec_lite_for_testing` as `spec_lite_content` — success criteria, shadow paths and edge cases relevant to testing. If agent-specific sections are unavailable, pass full spec-lite | `commands/implement-story.md` |
| 217 | 741–745 | rule | Process, in order: run story-specific tests; run regression tests (related suites); run coverage analysis; fix failures (**prefer fixing implementation over changing tests**); add missing test coverage if needed | `commands/implement-story.md` |
| 218 | 748 | threshold | **100% test pass rate — mandatory** | `commands/implement-story.md` |
| 219 | 749 | threshold | **≥80% line coverage on new files — mandatory** | `commands/implement-story.md` |
| 220 | 750 | threshold | **Coverage must not decrease on modified files** | `commands/implement-story.md` |
| 221 | 752 | threshold | On failure: send test output back to the coding agent. **2 fix iterations max** (separate from the review loop's 3-iteration cap), then escalate | `commands/implement-story.md` |
| 222 | 754–769 | rule | On `STATUS: BLOCKED` (agent hit `MAX_SELF_FIX_ITERATIONS = 3`), surface to the user with an `AskQuestion` titled "Testing Agent Blocked", id `blocked_action`, carrying agent name, `FAILURE` and `PARTIAL_STATE`, and three options: `retry` (restart Gate 4 with fresh context), `skip` (skip gate with warning — continue to docs, story marked degraded), `abort` (abort pipeline — preserve current state) | `commands/implement-story.md` |
| 223 | 771 | rule | Skip with warning: continue to Gate 5 but mark the story `⚠️ DEGRADED` in the final report. **Do NOT mark `Completed ✅`** | `commands/implement-story.md` |

## T. Gate 4.5 — Visual QA (L775–794)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 224 | 777 | agent-binding | Agent: `agents/visual-qa-agent.md` | `commands/implement-story.md` |
| 225 | 778 | skip-rule | Skip in `--quick` mode, and when no visual references exist for this story | `commands/implement-story.md` |
| 226 | 780–782 | rule | Auto-activates when the story file has a `## Visual References` section, or the spec has a `mockups/` directory with files | `commands/implement-story.md` |
| 227 | 784–787 | rule | Spawns a **read-only** sub-agent that captures the current UI via browser/Playwright, compares against mockups linked in the story, and reports structural, spacing and styling matches/mismatches | `commands/implement-story.md` |
| 228 | 790 | vocabulary + threshold | **PASS** (**≥85%** match) → continue to docs | `commands/implement-story.md` |
| 229 | 791 | vocabulary + threshold | **SOFT PASS** (**≥70%** match, only cosmetic issues) → continue, log issues | `commands/implement-story.md` |
| 230 | 792 | vocabulary + threshold | **FAIL** (**<70%** match or high-priority mismatches) → send fixes back to the coding agent | `commands/implement-story.md` |
| 231 | 794 | threshold | Gate 4.5 failures **count toward the shared 3-iteration review loop cap** | `commands/implement-story.md` |

## U. Gate 5 — Documentation Agent (L798–812)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 232 | 800 | agent-binding | Agent: `agents/documentation-agent.md` | `commands/implement-story.md` |
| 233 | 801 | skip-rule | Skip in `--quick` mode | `commands/implement-story.md` |
| 234 | 803 | rule | Context routing: pass **full spec-lite content** as `spec_context` — documentation agents need a cross-cutting view across all spec sections. Also pass `fetched_context` if available | `commands/implement-story.md` |
| 235 | 805 | rule | Auto-detects the documentation framework (VitePress, Docusaurus, Nextra, MkDocs, Storybook, or plain README) | `commands/implement-story.md` |
| 236 | 808–812 | rule | Updates: inline docs (JSDoc/docstrings) for new public APIs; README if user-facing features were added; CHANGELOG entry; framework-specific docs pages if detected; Mermaid diagrams where appropriate | `commands/implement-story.md` |

## V. Step 4 — Story Completion (L816–828)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 237 | 818 | rule | Step 4 runs **after all gates pass** | `commands/implement-story.md` |
| 238 | 820 | rule | Item 1: update story status → `Completed ✅` with date | `commands/implement-story.md` |
| 239 | 821 | rule | Item 2: mark tasks and acceptance criteria as checked in the story file | `commands/implement-story.md` |
| 240 | 822 | rule | Item 3: regenerate `.writ/context.md` — **full rewrite** using the schema, reflecting the newly completed story status and updated progress counts | `commands/implement-story.md` |
| 241 | 823 | rule | Item 4: append `## What Was Built` to the story file | `commands/implement-story.md` |
| 242 | 824 | rule | Item 5: update `user-stories/README.md` progress percentages | `commands/implement-story.md` |
| 243 | 825 | rule | Item 6: commit with a descriptive message including story title, file counts, test results and drift status | `commands/implement-story.md` |
| 244 | 826 | rule | Item 7: record the story commit SHA into the story file header | `commands/implement-story.md` |
| 245 | 827 | rule | Item 8: report pipeline results — per-gate status, file counts, drift summary, and next action (`/ship`) | `commands/implement-story.md` |

## W. Recording the Story Commit SHA (L829–841)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 246 | 831 | rule | Consumer: `/revert` + `scripts/revert-resolve.py` map a story to its exact commit via this field — their **highest-confidence resolution layer** | `story-commit-provenance` |
| 247 | 835 | rule | Capture the SHA with `git rev-parse HEAD` — the completion commit from item 6, the one carrying the status flip, checked tasks/AC and `## What Was Built` | `story-commit-provenance` |
| 248 | 836 | rule | Write `> **Commit:** <full-sha>` into the story file's header block (the `> **Status:** …` metadata block near the top), so provenance sits beside status | `commands/implement-story.md` (Step 4 item 7 — pinned literal 10, also frontmatter `exit_criteria`) + `story-commit-provenance` |
| 249 | 837 | rule | **Idempotent write:** if a `> **Commit:**` line already exists (re-run / re-implementation), **update it in place — never append a duplicate** | `story-commit-provenance` |
| 250 | 838 | rule | **Land the field:** the SHA is unknown before the commit exists, so it cannot live inside the commit it names. Fold the one-line header write into the immediately-following bookkeeping commit (e.g. `git commit -am "chore(story): record commit SHA"`). **Do NOT `--amend` the completion commit — amending would rewrite the very SHA just recorded.** The recorded SHA points at the completion commit (the revert target); the tiny record-SHA commit is inert | `story-commit-provenance` |
| 251 | 840 | degradation | **Backward compatibility:** the field is **optional**. Stories completed before this convention (or `--quick` runs that skip bookkeeping) simply lack `> **Commit:**`; `scripts/revert-resolve.py` tolerates its absence and falls back to later resolution layers (`/ship` `Ref:` footer, phase-state JSON, ghost-commit match). **Never fail a story for a missing SHA field** | `story-commit-provenance` |

## X. "What Was Built" Record Assembly (L842–956)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 252 | 844 | rule | Format reference: `.writ/docs/what-was-built-format.md` | `what-was-built-authoring` |
| 253 | 846 | rule | The WWB record captures **implementation reality** for cross-story continuity; data is extracted at Gate 3.5 into `what_was_built_data`, then formatted and appended to the story file at Step 4 | `what-was-built-authoring` |
| 254 | 850 | rule | Data flow 1 — **Gate 3.5:** extract and validate data from review agent output | `commands/implement-story.md` (Gate 3.5 § B data flow) + `what-was-built-authoring` |
| 255 | 851 | rule | Data flow 2 — **Gate 4:** update `what_was_built_data.test_results` with testing agent results | `commands/implement-story.md` (Gate 3.5 § B data flow) + `what-was-built-authoring` |
| 256 | 852 | rule | Data flow 3 — **Step 4:** format `what_was_built_data` as markdown and append to the story file | `commands/implement-story.md` (Step 4 item 4) + `what-was-built-authoring` |
| 257 | 859–863 | rule | Template: leading `---` separator, `## What Was Built`, `**Implementation Date:** {implementation_date}` | `what-was-built-authoring` |
| 258 | 865–871 | rule | Template `### Files Created`: numbered entries `**\`{path}\`** ({line_count} lines)` with a description bullet; **if empty print `[None created]`** | `what-was-built-authoring` |
| 259 | 873–879 | rule | Template `### Files Modified`: bulleted `**\`{path}\`** ({section_reference})` with a changes bullet; **if empty print `[None modified]`** | `what-was-built-authoring` |
| 260 | 881–886 | rule | Template `### Implementation Decisions`: numbered `**{title}** — {rationale}`; **if empty, omit the section entirely — do not write "None"** | `what-was-built-authoring` |
| 261 | 888–893 | rule | Template `### Test Results`: `**Verification:** {verification}`; `**Coverage:** {coverage}%` only if coverage is present; then one `- ✅ {detail}` bullet per detail | `what-was-built-authoring` |
| 262 | 895–902 | rule | Template `### Review Outcome`: `**Result:** {result}`, then `- **Iteration count:** {n} iteration(s)`, `- **Drift:** {drift}`, `- **Security:** {security}`, and `- **Boundary Compliance:** {…}` only if present | `what-was-built-authoring` |
| 263 | 904–914 | rule | Template `### Deviations from Spec`: `None` if `deviations` is empty or drift is "None"; otherwise per deviation `**[{id}] {title}** — Severity: {severity}` with Spec said / Reality / Resolution bullets, plus `Spec amendment` only if present | `what-was-built-authoring` |
| 264 | 919 | rule | Append step 1: open the story file for append (e.g. `.writ/specs/{spec-folder}/user-stories/story-N-{slug}.md`) | `what-was-built-authoring` |
| 265 | 920 | rule | Append step 2: add the separator `\n---\n\n` | `what-was-built-authoring` |
| 266 | 921–922 | rule | Append step 3–4: add the formatted WWB content from the template, then save the file | `what-was-built-authoring` |
| 267 | 926–944 | degradation | `--quick` mode (Gate 3.5 skipped): no `what_was_built_data` available → construct a **minimal record** from coding and testing agent outputs, carrying the banner `> Note: Review skipped (\`--quick\` mode) — record sourced from coding and testing agents only` and the sections Implementation Date, `### Files Created`, `### Files Modified`, `### Test Results` | `what-was-built-authoring` |
| 268 | 946–948 | degradation | Incomplete data at Gate 3.5: already handled via validation warnings and fallback values in `what_was_built_data` — use partial data, log warnings, but continue | `what-was-built-authoring` |
| 269 | 950–951 | degradation | Missing Gate 4 results: if testing was skipped or failed, use `**Verification:** N/A` in `test_results` | `what-was-built-authoring` |
| 270 | 953 | rule | **The pipeline must NEVER block story completion due to incomplete WWB data. Partial records are better than no records.** | `what-was-built-authoring` |

## Y. Error Handling, Quick Mode, Completion, References (L957–989)

| # | Line(s) | Category | Rule | Where it lives now |
|---|---|---|---|---|
| 271 | 959 | rule | Agent crash: retry **once** automatically; if the retry fails, present the error to the user | `commands/implement-story.md` |
| 272 | 960 | threshold | Review loop exceeded (**3 iterations**): surface remaining issues and offer continue-anyway (noted), manual intervention, or skip story | `commands/implement-story.md` |
| 273 | 961 | rule | Blocking issue during coding: surface the blocker, what was attempted and partial progress; offer guidance + retry, or skip story | `commands/implement-story.md` |
| 274 | 962 | rule | `STATUS: BLOCKED` from coding or testing agent: the agent hit `MAX_SELF_FIX_ITERATIONS = 3`; parse the `FAILURE` and `PARTIAL_STATE` fields and present the AskQuestion repair decision at the relevant gate. **Never silently continue past a BLOCKED result** | `commands/implement-story.md` |
| 275 | 968 | skip-rule | `--quick` **skips:** Gate 0 (arch-check), **Gate 0.5 (boundary map)**, Gate 3 (review), Gate 3.5 (drift handling), Gate 5 (docs) | `commands/implement-story.md` |
| 276 | 969 | skip-rule | `--quick` **keeps:** Gate 1 (coding/TDD), Gate 2 (lint), Gate 4 (testing) | `commands/implement-story.md` |
| 277 | 971–974 | rule | Use `--quick` for prototyping, spikes, internal tools; run the full pipeline later via `/implement-story story-3 --review-only` | `commands/implement-story.md` |
| 278 | 978 | rule | Completion: the command succeeds when the story file reads `Status: Completed`, carries the completion commit SHA in its header, and ends with a `## What Was Built` section whose file and test counts match `user-stories/README.md` | `commands/implement-story.md` |
| 279 | 980 | rule | A story that cannot clear every gate is marked **DEGRADED** rather than Completed. That is a valid terminal state and **must not be relabelled to make a batch look clean** | `commands/implement-story.md` |
| 280 | 982 | rule | **Terminal constraint:** this command closes out one story. Do not start the next story, merge the branch, or update the roadmap | `commands/implement-story.md` |
| 281 | 988–989 | rule | References: `commands/_preamble.md` (standing instructions), `system-instructions.md` (Identity & Prime Directive) | `commands/implement-story.md` |

---

## Z. Cross-cutting indexes (the walk's spot-check lists)

These restate rows already above, grouped so a reviewer can check a whole category at once.

### Z1. Every numeric threshold

| Value | Meaning | Rows |
|---|---|---|
| 3 | review-loop iterations across review + visual QA, one shared counter | 4, 18, 180, 231, 272 |
| 2 | Gate 4 testing fix iterations, separate cap | 5, 180, 221 |
| 3 | `MAX_SELF_FIX_ITERATIONS`, declared in the agent files | 6, 153, 222, 274 |
| 100% | test pass rate, mandatory | 3, 218 |
| ≥80% | line coverage on new files, mandatory | 3, 219 |
| (no decrease) | coverage on modified files | 220 |
| 85% / 70% | visual QA PASS / SOFT PASS thresholds; <70% FAIL | 228, 229, 230 |
| 1000 lines | WWB record truncation trigger | 82 |
| 20 lines / 2 lines | truncation tier 3 and tier 6 sub-limits | 85, 88 |
| ~2KB | `knowledge_context` cap | 24, 53, 54, 58 |
| 21000 bytes | `FETCHED_CONTEXT_BUDGET_BYTES`, script-owned | 34, 35 |
| depth 1 | import graph scan depth | 137 |
| < 10 seconds | Gate 0.5 performance target | 142 |
| +3 / +2 / +1 / +1 | knowledge scoring weights | 51 |
| 3+ characters | keyword token minimum | 48 |
| >3 files | "imported by many" cross-component heuristic | 170 |
| last 3 | drift entries in the context snapshot | 105 |
| 1–3 sentences | product mission in the context snapshot | 102 |

### Z2. Every result vocabulary

| Vocabulary | Gate | Rows |
|---|---|---|
| PROCEED / CAUTION / ABORT | Gate 0 | 120, 121, 122 |
| Owned / Readable / Out-of-scope | Gate 0.5 | 130 |
| PASS / FAIL / PAUSE | Gate 3 | 177, 178, 179 |
| Small / Medium / Large | Gate 3.5 §A | 184, 190, 192 |
| style-only / single-component / cross-component / full-stack | Gate 2.5 | 163–166 |
| PASS / SOFT PASS / FAIL | Gate 4.5 | 228, 229, 230 |
| `✅ all required present` / `⚠️ missing required: <list>` | context snapshot Integrity | 112 |
| `Completed ✅` / `In Progress` / `⚠️ DEGRADED` | story terminal states | 154, 223, 238, 279 |

### Z3. Every named output variable

| Variable | Produced at | Rows |
|---|---|---|
| `fetched_context` | Step 2, assembler | 38, 45 |
| `context_warnings` | Step 2, assembler | 39, 45 |
| `knowledge_context` | Step 2, knowledge load | 24, 59 |
| `spec_lite_for_coding` | Step 2, spec-lite sectioning | 60 |
| `spec_lite_for_review` | Step 2, spec-lite sectioning | 61 |
| `spec_lite_for_testing` | Step 2, spec-lite sectioning | 62 |
| `dependency_wwb_context` | Step 2, dependency WWB | 93, 150 |
| `boundary_map` | Gate 0.5 | 129, 151 |
| `boundary_overlap_summary` | Gate 3 input | 175 |
| `change_surface` | Gate 2.5 | 162, 175 |
| `what_was_built_data` | Gate 3.5 §B | 213 |

### Z4. Every literal log / warning string

| String | Rows |
|---|---|
| `⚠️ Story 5 depends on Story 2 (not yet complete). / Proceeding anyway — some integration points may be unavailable.` | 30, 76 |
| `⚠️ story-context.py not found — proceeding with spec-lite only` | 41 |
| `⚠️ story-context.py exited non-zero — proceeding with spec-lite only` | 42 |
| `⚠️ story-context.py produced unparseable output — proceeding with spec-lite only` | 43 |
| `⚠️ Knowledge entry skipped: malformed frontmatter in {path}` | 57 |
| `ℹ️ knowledge_context truncated to 2KB` | 58 |
| `⚠️ Spec-lite.md missing "## For {Role} Agents" section — using full content` | 69 |
| `ℹ️ Story N's "What Was Built" is marked Reverted — skipping as non-authoritative dependency context.` | 79 |
| `⚠️ Story 1 is marked complete but has no "What Was Built" record. / Proceeding with reduced context — cross-story continuity may be degraded.` | 80 |
| `⚠️ Truncated Story {N} "What Was Built" record ({original} → 1000 lines)` | 90 |
| `⚠️ boundary_map approximate — no concrete file paths in tasks; review agent should use extra caution.` | 140 |
| `⚠️ "What Was Built" record incomplete — no files found` | 202 |
| `⚠️ DEGRADED` | 154, 223 |
| `> Note: Review skipped (\`--quick\` mode) — record sourced from coding and testing agents only` | 267 |
| `✅` bullets in the WWB Test Results template | 261 |

### Z5. Skip-mode matrix

| Gate | `--quick` | `--review-only` | Other conditions | Rows |
|---|---|---|---|---|
| 0 Architecture Check | skip | skip | — | 117, 275 |
| 0.5 Boundary Map | skip | skip | also skipped on the `/prototype` path | 125, 128, 275 |
| 1 Coding | keep | **skip** | `boundary_map` = `(none)` when 0.5 was skipped | 148, 151, 276 |
| 2 Lint | keep | keep | — | 276 |
| 2.5 Change Surface | keep (**not** in the skip list) | keep | — | 161 |
| 3 Review | skip | keep | — | 275 |
| 3.5 Drift + WWB extraction | skip | keep | `--quick` still writes the minimal WWB record | 267, 275 |
| 4 Testing | keep | keep | — | 276 |
| 4.5 Visual QA | skip | keep | also skipped when no visual references exist | 225 |
| 5 Docs | skip | keep | — | 233, 275 |

---

## AA. Walk record (Story 6, 2026-08-12)

**Result: 281 rows, 281 accounted for, zero unaccounted removals.**

### Method

Worked from this inventory, not from the diff — a diff shows what moved and is blind to what was dropped, which is the failure mode Business Rule 2 exists to catch. Every row's `Where it lives now` names `commands/implement-story.md`, exactly one of the eight `SKILL.md` files, both (where a contract stub stayed behind and the procedure left), or a **contracted** disposition citing what still carries the information.

Then the walk was **machine-checked**: 75 exact strings — every literal log line, every numeric threshold, every result-vocabulary token, every named fallback value and every schema marker — were grepped across `commands/implement-story.md` plus all 14 `skills/*/SKILL.md`. **All 75 present.** Four initially reported missing and all four were line-wrap artifacts rather than drops; re-checked whitespace-normalized, all four resolved. One of them — the `⚠️ Spec-lite.md missing "## For {Role} Agents" section — using full content` log line — was **unwrapped onto a single line in the skill anyway**, because a user-visible log string broken across source lines is a string a future author can silently reflow.

### Disposition summary

| Disposition | Rows |
|---|---|
| `commands/implement-story.md` only | 119 |
| Exactly one `SKILL.md` only | 142 |
| Both (contract stub in the command, procedure in a skill) | 17 |
| **Contracted** — deleted duplicate, information carried elsewhere with a citation | 3 (rows 99, 198, 213) |
| **Unaccounted** | **0** |

### The three contracted rows, each with its citation

| Row | What was deleted | What carries it now |
|---|---|---|
| 99 | C1 — the 41-line "Example Coding Agent Context (with WWB)" worked example (L299–339) | The aggregation format it illustrated, specified once in `dependency-context-loading` → *6. Aggregate*. The example was a second copy of a format stated 20 lines above it. |
| 198 | C5 — the ten-line `#### [DEV-003]` drift-log entry example (L659–668) | `.writ/docs/drift-report-format.md`, which the source already cited two lines earlier as the format authority and which `drift-triage` and the command both point at. |
| 213 | C2 — the `what_was_built_data` JavaScript object literal (L712–728) | `what-was-built-authoring`'s five extraction sources plus its Formatting Template, which enumerate every field once. One field list, one syntax, instead of the same list in two. |

None of the three deleted a rule. Each deleted a *second copy* of something specified elsewhere in the same text, which is the contraction Business Rule 2 explicitly permits.

### Rewording ledger

Rows whose wording changed materially. Every other row transferred verbatim or with only whitespace, heading-level or list-marker changes — and the 75-string grep above is the check on that claim.

| Row(s) | What changed | Note confirming the rule is the same |
|---|---|---|
| 7 | The Overview's arrow sequence became "architecture check through documentation; the Pipeline table below is the stage list" | The full ordered stage list is the Pipeline table, one row per stage in pipeline order — the same ten gates plus Steps 2 and 4. |
| 16, 17 | The ASCII diagram became the Pipeline table | Same ten gates, same names, same modality (read-only / inline / TDD / auto / + coverage / adaptive) now in a `Runs as` column rather than a box. |
| 18 | Arrow annotations became one **Control flow** sentence | Same five transitions and the same parenthetical "max 3 iterations total across review + visual QA". Deliberately phrased *"iterations total across review"* so it does not match `eval-loop-bounds.py:485`'s `Max (\d+) iterations across review` regex ahead of the Gate 3 sentence that check is meant to read. |
| 29 | Four sub-bullets became one inline list | Same four actions in the same order. |
| 32, 33 | Delegation prose condensed | Both clauses survive: the script is the **sole** implementation, and the caller **does not restate its algorithm**. |
| 52 | "Prefer categories by agent" now names consuming roles ("Architecture review", "Coding", "Code review") instead of gate-bound agent names | Same three preference orders. The rename is Business Rule 3 rule 5 — a shared skill carries no consumer's vocabulary. |
| 119, 176, 217, 227, 236 | Gate 0, Gate 3, Gate 4, Gate 4.5 and Gate 5 bullet lists became inline semicolon lists | Same items, same order, no item dropped. Kept in the **command**, not moved to `agents/*.md`, precisely so this walk can count them. |
| 130 | The `boundary_map` schema fence transferred whole to the skill | Byte-identical fenced block; fenced content is lint-exempt so nothing needed rewriting. |
| 132, 133 | The separate **Flags (annotations)** list became one paragraph beneath the schema (C4) | Both flag semantics survive in full — the still-Owned-if-tasks-name-it rule and the warn → higher-scrutiny rule. |
| 138 | "Gate 0 overrides" became "Architecture-review overrides" | Same `### Warnings for Coding Agent` parse, same demotion, same `_(arch-check: do not modify — boundary override)_` annotation. The gate number left because a skill may not name its extraction site. |
| 143–145 | "Check 5 persistence (for Gate 0.5 step 5)" became "Persistence of the overlap data step 5 reads" | Both locations, the exact `## Check 5 — File overlap` heading, the table, the warn → high-overlap mapping and the degradation all survive. |
| 153, 222 | The two `STATUS: BLOCKED` `AskQuestion` blocks became one parameterized `### BLOCKED Agent Escalation` template (C6) | Same three options with the same ids and labels, same `FAILURE` / `PARTIAL_STATE` fields, same title pattern. The two gate-specific skip-with-warning notes stay at Gate 1 and Gate 4, which is the only thing that ever differed. |
| 156–160 | Gate 2's linter list and four-step failure ladder became inline | Same three toolchains, same four steps in order. |
| 162 | Gate 2.5's framing condensed | Classification still drives review attention, is still passed as `change_surface`, and the `boundary_map` cross-check is still optional with the same full-stack-on-a-Readable-file example. |
| 175 | Gate 3's Input paragraph condensed | Every parameter survives by name, including `boundary_overlap_summary` and its "distilled from Readable lines carrying overlap or high-overlap" derivation. |
| 183–197 | Drift severities split — a three-clause stub in the command, full procedures in `drift-triage` | The command keeps the vocabulary, the PAUSE-and-ask-the-user orchestration and "spec.md is never auto-modified"; the skill keeps the Small-drift sequence, the blocking acknowledgment, the mixed-severity rule and the append-only DEV-ID rules. |
| 199, 214 | Gate 3.5 § B reduced to the extraction contract plus the three-hop data flow | The five sources and their fallbacks live in `what-was-built-authoring`, read at Step 4 item 4. **Recorded consequence:** the spec's own placement ruling (one read per skill, at Step 4 because `--quick` still writes the minimal record) means the extraction rules are not loaded at the gate that extracts. The command names where they live; the rule itself is unchanged. |
| 209 | "number of Gate 3 review loops" became "the number of review loops", tracked by the caller | Same counter, same owner. The gate number left the skill for the same reason as row 138. |
| 246–251 | Provenance prose tightened | All five rules survive verbatim in meaning: `git rev-parse HEAD`, placement beside `> **Status:**`, update-in-place-never-duplicate, the bookkeeping-commit fold with the **do not `--amend`** prohibition *and its reason*, and the optional-field fallback chain. |
| 252–270 | The record's template and append procedure moved whole to `what-was-built-authoring` | The three deliberately different empty states (`[None created]` / `[None modified]`, omit-Implementation-Decisions-entirely, print `None` for Deviations) are called out explicitly in the skill so a later author does not harmonize them. |
| 267 | The `--quick` minimal record is labelled "a second template, not a degraded copy of the first" | Same banner, same four sections. |
| 112 | The Integrity line's two states now appear in **both** the command and `project-context-snapshot` | Required by `scripts/eval-artifact-integrity.py:96`, which asserts the command contains both `**Integrity:**` and `missing required` — a twelfth pinned constraint the technical spec's Pinned Literals table did not list. |

### Rows deliberately kept in the command against byte pressure

Rows 119, 176, 217, 227 and 236 — Gate 0's and Gate 3's review dimensions, Gate 4's process, Gate 4.5's capture steps and Gate 5's updates — also appear in the corresponding `agents/*.md`. Pointing at those files would have saved roughly 1,500 bytes and closed part of the ceiling regression. It was rejected: an agent definition is neither `commands/implement-story.md` nor one of the eight `SKILL.md` files, so each of those rows would have become **unaccounted** in this walk. The byte cost is recorded in the load report instead.
