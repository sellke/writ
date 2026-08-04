# Writ vs. Code Captain — Fork Origin Competitive Analysis (July 2026)

**Date:** 2026-07-20
**Status:** Complete
**Subject:** [devobsessed/code-captain](https://github.com/devobsessed/code-captain) v0.6.0 (npm `@devobsessed/code-captain@0.6.0`, manifest timestamp 2026-05-14)
**Method:** Shallow clone of `main` at analysis time; read README, `manifest.json` changelog, Cursor/Copilot/Claude command trees, Claude skills (`analyze-repos`, `mcp-analysis`, ports), installer (`bin/install.js`), Vitest suite, and recent commit history. Compared against Writ product source at `VERSION` 0.23.0 / local methodology (npm `@sellke/writ` is a separate tiny runtime helper at 0.15.0).

---

## Research Questions

1. How has Code Captain evolved since Writ forked?
2. What is genuinely remarkable that Writ should reconsider?
3. Where does Writ hold durable advantages?
4. What's the honest strategic takeaway?

---

## Executive Summary

Code Captain has **not** continued as a competing methodology framework. Since the fork, its evolution is concentrated in three places: (1) **Copilot / Visual Studio packaging** (Solution View, prompt hardening, monorepo/working-directory bootstrap), (2) a **Claude Code parity pass** (v0.5–0.6.0, May 2026) that ports Cursor commands into Claude commands/skills, and (3) **two new Claude-only skills** — `analyze-repos` and `mcp-analysis` — plus an `.mcp.json` template.

The **core SDLC loop** (`initialize → plan-product → create-spec → execute-task`) and the Cursor command bodies are effectively frozen near the pre-Writ shape (Cursor tree last touched substantively in early 2026 for lint/formatting; methodology content still carries `version: "0.3.0"` hashes in the manifest). There is no multi-agent gated pipeline, no phase orchestration, no drift reconciliation, no UAT generation, no bounded `--recommend` autonomy, no eval/anti-sycophancy substrate, and no self-improvement loop.

**Writ has leapfrogged the shared ancestry on methodology depth.** Code Captain retains advantages in **distribution UX** (polished `npx` wizard + SHA manifest updates), **Copilot/VS reach**, and **two practical skills** Writ does not ship. Only those skills (especially MCP trust analysis) and possibly compressed `AGENTS.md` indexing are worth a deliberate reconsideration — and both fit Writ's skill primitive without expanding the command surface.

---

## Side-by-Side

| Dimension | Writ (local 0.23.0 methodology) | Code Captain (0.6.0) |
|---|---|---|
| **Origin relationship** | Fork / evolution of CC patterns | Upstream ancestor |
| **Surface area** | ~32 commands, 7 agents, 6 skills, 4 adapters, eval Tier 1 | ~11 Cursor cmds; Claude cmds + 6 skills; Copilot prompts; 4 Claude agents |
| **Source-of-truth model** | Single `commands/` + `agents/` + `skills/`; adapters map | **Triplicated** trees (`cursor/`, `copilot/`, `claude-code/`) |
| **Unit of work** | Roadmap phase → spec → story → 6-gate agents | Spec → story → `/execute-task` (single-agent TDD) |
| **Orchestration depth** | 4 levels (`implement-phase` → spec → story → gates) | 1–2 levels (command → optional Claude subagents for *authoring*) |
| **Implementation agents** | architecture-check, coding, review, testing, docs, visual-qa | Claude: `code-captain`, `spec-generator`, `story-creator`, `tech-spec` (spec *creation*, not gated impl) |
| **Quality gates** | Arch → boundary map → TDD → lint → review+drift → coverage → visual QA → docs | TDD + "100% tests pass" mandate in execute-task |
| **Drift / healing** | First-class Small/Medium/Large + `/edit-spec` + verify | None observed |
| **UAT** | `/create-uat-plan` auto from implement-phase | None |
| **Autonomy** | `--recommend` on exactly 2 commands; human production boundary | None (human-driven commands) |
| **Governance** | Prime Directive, ADRs, eval Tier 1, leanness guardian | Personality prose; no eval gate |
| **Self-improvement** | Evidence-bound `/refresh-command`, skill lifecycle, knowledge consolidate | `/new-command` meta only |
| **Knowledge** | Consolidating `.writ/knowledge/` ledger + GBrain interop | `.code-captain/` docs/research folders |
| **Platforms** | Cursor, Claude Code, Codex, OpenClaw guide | Cursor, Copilot (VS Code + **Visual Studio**), Claude Code |
| **Install** | `install.sh` / `update.sh` with 3-way local-mod awareness | Interactive `npx` wizard + remote `manifest.json` SHA change detection |
| **Tests** | `scripts/eval.sh` methodology integrity (CI) | Vitest: structure, content phrase consistency, command availability |
| **npm package** | `@sellke/writ` = tiny date/timestamp runtime | `@devobsessed/code-captain` = full installer + platform trees |
| **Open issues signal** | (Writ product track) | AntiGravity, Windsurf, dual Cursor+Claude install, submodules |

---

## How Code Captain Evolved (Post-Fork Timeline)

Evidence from `manifest.json` changelog + `git log`:

| Version / date | What shipped |
|---|---|
| **≤0.3.x** (through early 2026) | Shared ancestral command set on Cursor/Copilot; identity prose matches Writ's early DNA |
| **0.3–0.4.x** (Feb–Mar 2026) | Copilot/VS focus: Solution View via `Directory.Build.props`, `.slnx` support, prompt hardening (terminal safety, monorepo awareness), working-directory bootstrap |
| **0.5.0** (2026-05-14) | **`analyze-repos`**, **`mcp-analysis`**, `.mcp.json` (Atlassian + GitHub MCP templates), installer component options for Claude Skills / MCP config |
| **0.6.0** (2026-05-14) | Claude Code parity: port create-adr/edit-spec/execute-task/plan-product/new-command; port explain-code/research/status/swab → **skills**; drop `cc-` prefix |

**What did *not* evolve:** Cursor methodology commands remain at the ancestral contract-first / execute-task shape. No implement-phase, no review agent loop, no ship/release/retro/refresh, no Prime Directive enforcement layer.

---

## What Is Genuinely Remarkable (Reconsider for Writ)

### 1. `mcp-analysis` skill — **Recommend adopting (as a skill)**

A structured, read-only MCP supply-chain audit: repo metadata → MCP surface → source security categories → **A–F trust rating** per category → RECOMMEND / USE WITH CAUTION / NOT RECOMMENDED / DO NOT USE → alternatives.

**Why it matters:** 2026 agent workflows load MCP servers with filesystem, network, and credential reach. Writ's `/security-audit` is project-scoped; ADR-018 reserves trust for *skills*, not MCP servers. Neither covers "should I connect this MCP?"

**Fit:** New first-party skill (not a command) — e.g. `mcp-trust-audit` — wielded by `/security-audit` or invoked standalone. Aligns with ADR-009 boundary and ADR-015 leanness (capability, not workflow).

**Caveat:** Their skill forbids cloning and relies on GitHub web/API reads; a Writ port should keep the same read-only constraint and cite evidence paths.

### 2. `analyze-repos` / compressed `AGENTS.md` indexes — **Selective adopt**

Multi-repo discovery (including nested repos and `.sln` paths) producing:

- Per-repo compressed `AGENTS.md` (≤100 lines, **pointers not extracts** — Vercel-style)
- Tech-stack / code-style / architecture docs under `.code-captain/docs/`
- Cross-repo dependency map + master TOC

**Why it matters:** Writ deferred full multi-repo orchestration (ADR-007) — correctly, absent team signal. The **compressed index pattern for a single repo** is still dual-use: Codex/`AGENTS.md` consumers, brownfield `/initialize`, and context-budget hygiene.

**Fit:** Extend `/initialize` (brownfield path) and/or a `codebase-index` skill that writes/updates an `AGENTS.md` "Codebase Index" section without inventing multi-repo orchestration. Do **not** ship workspace-wide multi-repo orchestration until ADR-007's trigger fires.

### 3. Distribution UX (`npx` wizard + remote SHA manifest) — **Optional polish, not methodology**

CC's installer is a productized Node wizard with component selection, existing-install detection, and hash-diff updates against published `manifest.json`. Writ's bash installer + 3-way merge is **more correct** for local modifications and dogfooding symlinks, but less inviting for first-time install.

**Fit:** If Writ ever packages a fuller `@sellke/writ` installer (today the npm package is intentionally tiny), borrow UX patterns — not the triplicated content model. Keep single-source product files.

### 4. Copilot + Visual Studio depth — **Do not chase without market signal**

CC invested heavily in `.csproj` / Solution View / Copilot prompts. Writ's persona (solo builder on Cursor/Claude/Codex) and ADR-007 sequencing argue against opening a fourth platform tree unless a concrete user needs .NET/VS.

### 5. `/swab` (Boy Scout one-shot) — **Do not re-adopt**

Writ intentionally replaced `/swab` with `/refactor` (scoped, verified, commit-per-change). CC's swab is lighter and friendlier for tiny cleanups; Writ already has `/prototype` for low ceremony and `/refactor --dry-run`. Reintroducing swab would reopen surface bloat (ADR-015).

### 6. Shipped `.mcp.json` templates — **Probably skip**

Convenient, but MCP config is platform/user-environment territory. Shipping Atlassian/GitHub templates risks stale formats and credential-footgun docs. Prefer documenting in an adapter or skill ("how to register MCP") over shipping secrets-shaped config.

### 7. Vitest cross-platform consistency tests — **Already superseded**

CC needs them because content is duplicated. Writ's single source + eval Tier 1 + leanness registry checks are the stronger equivalent. Do not add phrase-consistency tests across adapters unless adapters start forking command bodies again (they should not).

---

## Where Writ Holds Clear Advantages

1. **Contract layer depth** — Plan Mode discovery, AskQuestion bounded choices, locked contracts, assess/verify, product reconciliation (`--product` / `--reconcile`).
2. **Execution rigor** — Multi-agent gates, worktree lanes, quarantine, dependency sequencing, What Was Built, context hints, UAT plans.
3. **Observable autonomy** — ADR-013 `--recommend` with audit summaries and a hard human production boundary; CC has no analogue.
4. **Non-degrading memory** — Knowledge ledger consolidation, drift logs, GBrain as disposable index (ADR-011) vs folder dumping.
5. **Falsifiable self-improvement** — Evidence-bound `/refresh-command`, skill lifecycle, eval CI — CC's methodology does not improve itself under gates.
6. **Architectural hygiene** — One product source + adapters vs three diverging trees (CC Cursor already lagging Claude skills).
7. **Recovery & provenance** — `/revert`, git-notes audit channel, artifact-integrity handshake (Phase 9) — absent in CC.
8. **Governance identity** — Prime Directive as hard constraints with eval scanning; CC retains "critically minded" prose without enforcement.

---

## Divergence Diagnosis

| Pressure | Code Captain response | Writ response |
|---|---|---|
| Harness absorbs mechanics | Port more platform packaging (VS, Claude skills folders) | Shed mechanics; own contracts (roadmap strategic frame 2026-07) |
| Platform coverage | Duplicate content per IDE | Adapter abstraction + symlink dogfood |
| Autonomy hype | Stay human-paced execute-task | Bounded supervised phase + recommend |
| Supply chain (MCP/skills) | Practical `mcp-analysis` skill | Reserve ADR-018 for 3p skills; gap on MCP servers |
| Multi-repo / enterprise | `analyze-repos` skill | Explicitly deferred (ADR-007) |
| Leanness | Growing Claude skill set + installer components | Leanness guardian + prune discipline |

They are no longer solving the same problem at the same altitude. CC is an **IDE integration kit** with a stable mid-2025 methodology core. Writ is a **contract-and-execution methodology** that treats IDE integration as adapter work.

---

## Recommendations (Prioritized)

| Priority | Action | Rationale |
|---|---|---|
| **P1** | Spec a first-party `mcp-trust-audit` (or similar) skill; optionally wire into `/security-audit` | Unique practical gap; high leverage; fits skill primitive |
| **P2** | Add compressed codebase-index generation to brownfield `/initialize` or a small skill (single-repo first) | Improves AGENTS.md/Codex onboarding without multi-repo scope creep |
| **P3** | No Copilot/VS adapter unless a named user needs it | Market signal rule (ADR-007) |
| **P4** | Do not reintroduce `/swab` or triplicated command trees | Writ already chose better shapes |
| **P5** | Treat CC as a distribution-UX reference only if packaging a fuller installer | Methodology lead is already Writ's |

---

## Honest Caveats

- Analysis is of public `main` as of 2026-07-20; private forks or unreleased branches are out of scope.
- Line-count parity (~13–15k markdown) is misleading: CC's lines are largely duplicated across platforms; Writ's are unique methodology depth.
- Writ `VERSION` (0.23.0) vs `@sellke/writ` npm (0.15.0) vs methodology richness is an **internal packaging clarity** issue unrelated to CC competitiveness — but CC's single npm package that *is* the product remains clearer for newcomers.
- Open CC issues (AntiGravity, Windsurf, dual-IDE) suggest community pull toward **more platforms**, reinforcing their packaging-first trajectory.

---

## Sources

- https://github.com/devobsessed/code-captain
- Local clone inventory: `/tmp/code-captain-analysis` (analysis-time)
- Writ: `README.md`, `.writ/product/roadmap.md`, `.writ/product/mission.md`, ADR-007/009/011/013/015/018, prior research `2026-07-18-writ-vs-conductor-analysis.md`
