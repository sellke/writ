# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.21.1] - 2026-07-18

**Housekeeping** — README and `/status` reconciled with shipped reality; the workspace ledger swept clean.

### Fixed

- **`/status` command allowlist reconciled** — added `/new-skill`, `/create-uat-plan`, and `/knowledge` to both allowlist locations, so `/status` can suggest every command that actually exists in `commands/*.md`.

### Changed

- **README brought current with v0.21.0 state** — all six live skills cataloged with descriptions, the two-command `--recommend` policy summarized with per-command annotations ([ADR-013](.writ/decision-records/adr-013-recommended-autonomous-delivery.md)), native-memory interop noted, the OpenClaw adapter added to Platform Support, the command count corrected to 30, and `uat-plan.md` / `recommendation-log.md` shown in the spec-package tree.

### Internal

- Workspace ledger reconciled: 9 stale spec headers set to terminal states with commit-level evidence (`infrastructure-command-refinement` closed as Abandoned — its targets left the suite), all 7 stale issues triaged (5 closed with evidence and deleted, 1 parked to the roadmap parking lot, 1 kept open), completed execution state purged from `.writ/state/`, and `.writ/context.md` regenerated.

## [0.21.0] - 2026-07-17

**Recommend Redistribution** — `--recommend` moves to the right seams. Experience showed a single command carrying one spec all the way through a production-approval boundary was the wrong first cut; per [ADR-013 (revised 2026-07-17)](.writ/decision-records/adr-013-recommended-autonomous-delivery.md), evidence-backed autonomy now lives on exactly two commands, and neither merges, opens PRs, nor releases — production stays a human decision.

### Added

- **`/implement-phase --recommend`** — the sole end-to-end autonomous loop: auto-authors missing specs (via `/create-spec --recommend`), auto-accepts its decomposition and execution-plan confirmations, and runs `/implement-spec` per spec through the existing isolated-lane flow. Terminal scope unchanged: honest completion report with manual UAT handoff.

### Changed

- **`/create-spec --recommend` authors and stops.** It autonomously runs contract-first discovery, auto-adopts the evidence-backed contract lock, story decomposition, sub-spec set, and visual-reference default — recording each material decision in `recommendation-log.md` — then delivers the locked, validated package without implementing.
- **`/implement-spec` is a plain execute command** — no confirmation gate, no flag. Invoking it runs the plan.
- **ADR-013 rewritten as a single coherent decision** — the current two-command policy stated directly, with the original single-spec shape recorded under Rejected Alternatives and Revision History. Policy (`system-instructions.md`, `cursor/writ.mdc`, `commands/_preamble.md`), product (mission, mission-lite, roadmap), and adapter surfaces reconciled to match.

### Removed

- **`--recommend` from `/implement-spec`, `/ship`, and `/create-uat-plan`.** The autonomous staging → production-approval flow is deferred ("bigger loops later"); its machinery (`scripts/recommend-state.py`, `.writ/docs/recommended-delivery-state-format.md`) is kept dormant as the preserved design — still eval-guarded, not deleted.

### Internal

- **Eval falsifiability gate reconciled in the same change:** `autonomy-governance` repointed to the revised policy literals with regression forbids; `recommended-spec-implementation` static assertions reconciled to the two-command model (162/162 scenarios, 16/16 static); `recommended-staging` redirected to guard only the dormant machinery plus an adapter merge-forbid (60/60 scenarios). Full suite green — 0 findings.
- `commands/_preamble.md` trimmed to 79 lines (within the 80-line eval limit).

## [0.20.1] - 2026-07-11

Internal eval robustness patch. Hardens the `recommended-spec-implementation` check against a pathological subprocess-spawn cost that read as a hang under x86_64 Python via Rosetta, and clears a Python 3.13+ deprecation warning. No user-facing feature or command changes.

### Fixed

- **Eval Python 3.13+ compatibility.** `scripts/eval-refresh-evidence.py` passes `maxsplit` to `re.split` by keyword, clearing a `DeprecationWarning` surfaced under native arm64 Python 3.14.

### Internal

- **Eval fixture-template reuse.** The `recommended-spec-implementation` check builds its git fixture repo once and `copytree`s it per fixture across both Python phases (`scripts/eval.sh`, `scripts/eval-recommend-state-adversarial.py`), cutting fixture-setup subprocess spawns (`git init` 40→3, `git config` 80→6) with all 36/36 static assertions still passing. Root cause traced to aggregate cross-arch spawn cost, not git or the helper — see [the improvement issue](.writ/issues/improvements/2026-07-11-eval-recommended-spec-spawn-heaviness.md).
- **Eval progress heartbeats.** The check emits stderr progress markers (fixture-template build, sandbox source build, per-platform install/update/unlink, adversarial suite) so a slow run is visibly progressing rather than looking hung.

## [0.20.0] - 2026-07-11

**Phase 8 (Memory Interop)** completes the 2026 harness-audit roadmap — Writ's markdown stays canonical while external memory layers become documented, optional indexes. Ships alongside two self-governance features: **Leanness Guardian** (the framework audits its own weight) and **Product Reconciliation** (verify/revise the product layer, closing the gap that only specs previously had).

### Added

- **Memory Interop — GBrain compatibility.** A new `gbrain-interop` skill plus `.writ/docs/gbrain-recipe.md` let a GBrain-equipped project register `.writ/` as a source (markdown-canonical routing, artifact→page mapping, graceful absence when no brain is installed) — grounded in GBrain's real interface, zero new Writ infrastructure.
- **Native-memory guidance per adapter.** All four adapters (Cursor, Claude Code, Codex, OpenClaw) document what belongs in native memory (session prefs, trivia) vs. the reviewable ledger (negotiated decisions, conventions, lessons), backed by a `memory-interop` eval check.
- **Leanness Guardian.** A Tier A eval tripwire (aggregate-weight + registry-parity) and a Tier B audit ritual let Writ govern its own growth, per [ADR-015](.writ/decision-records/adr-015-leanness-self-governance.md).
- **Product Reconciliation.** `/verify-spec --product` (a P1–P4 consistency lint over `.writ/product/`), `/plan-product --reconcile` (a targeted revision posture), and a read-only `/retro` product-drift nudge — the product-layer equivalent of spec verify/revise.

### Changed

- **Product docs reconciled with reality.** Mission, roadmap, and context realigned; Phase 8 marked implemented across all product docs (first dogfood output of `/plan-product --reconcile`).

### Internal

- **Two Tier 1 eval checks added** — `memory-interop` and `leanness` — both green on CI.

## [0.19.0] - 2026-07-11

Two phases ship together: **Phase 6 (Autonomy Ceiling)** — supervised multi-spec execution replacing the Ralph loop — and **Phase 7 (Compounding Layer)** — making Writ's self-improvement falsifiable and its skills primitive adopted.

### Added

- **Skill lifecycle.** Every skill carries a lifecycle state — `candidate` → `proven` → `promoted` — with supporting evidence in frontmatter. The boundary lint and `eval.sh` enforce that a skill's claimed maturity matches its recorded evidence, and the generated catalog renders lifecycle at a glance. See [ADR-014](.writ/decision-records/adr-014-skill-lifecycle.md).
- **Four skills extracted from commands.** `tdd-cycle` (from `/implement-story`'s coding phase), `error-rescue-mapping` (from `/create-spec`), `safe-refactor-loop`, and `code-explanation` are now first-class reusable capabilities instead of logic locked inside a single command — all lint-clean per `scripts/lint-skill.sh`.
- **`/knowledge --consolidate`.** A new mode that merges duplicate knowledge entries, surfaces contradictions for human resolution, and prunes stale ones — non-destructively, with a reviewable diff. Backed by a consolidation reducer, a registered eval check, and a `/retro` nudge to run it.

### Changed

- **Supervised multi-spec execution replaces the loop.** Use `/implement-phase` for multi-spec work: it sequences specs by authoritative cross-spec `Dependencies`, runs each spec in a fresh isolated execution lane (branch + worktree), quarantines terminal failures while independent specs continue, reconciles state read-only on resume, and reports categorical production health. Bounded single-spec autonomy remains separately supported via `/implement-spec --recommend <one-spec>`; multi-spec `/implement-phase --recommend` stays excluded per [ADR-013](.writ/decision-records/adr-013-recommended-autonomous-delivery.md).
- **`/implement-phase` gains a decomposition pre-pass.** When a roadmap phase has unspecced features, the command can propose a spec breakdown — dependency graph, single-writer file ownership, and named seams — for one planning confirmation, then seed `/create-spec` per spec. The phase→specs boundary becomes an explicit, contract-first artifact bound to the current codebase instead of tacit judgment made once at the first `/create-spec`.
- **`/refresh-command` is evidence-bound.** Command refinements now require a cited transcript signal (source transcript, observable signal, affected section). A fixture-driven `refresh-evidence` eval check and a pre-merge acceptance gate keep the refresh log honest; entries dated before `LEARNING_CONTRACT_SINCE = 2026-07-11` are grandfathered.

### Removed

- **Ralph, the autonomous CLI loop, is retired.** The `/ralph` command, `ralph.sh` loop, `PROMPT_build.md` prompt template, and CLI-pipeline/state-format docs are archived under `archive/ralph/` (preserved, not deleted) and removed from command discovery, the generated `SKILL.md` catalog, `.writ/manifest.yaml`, `.writ/docs/config-format.md`, all platform adapters, the README, and `/status` suggestions. See [ADR-012](.writ/decision-records/adr-012-ralph-deprecation.md).
- **`/explain-code` is retired into the `code-explanation` skill.** The capability is preserved as a reusable skill; the standalone command is removed from discovery and the catalog.

### Migration

- **This release does not migrate Ralph state.** There is no compatibility reader for `ralph-*.json`. **Finish or abandon any in-flight `ralph-*.json` run before upgrading**, then drive remaining multi-spec work with `/implement-phase`. The deliberate trade-off is the loss of opaque unbounded execution in exchange for isolation, resumability, and honest evidence.

## [0.18.1] - 2026-05-08

### Fixed

- **Startup update check false positives.** Writ now only recommends `/update-writ` after a copied installation proves upstream is strictly newer than the installed identity, preventing successful upstream reachability checks from triggering unnecessary update prompts.

### Internal

- **Issue backlog captured.** Added tracked issue records for the update-check false positive, spec branch preflight, and Writ business-process pipeline follow-ups.

## [0.18.0] - 2026-05-06

### Added

- **Codex CLI adapter support.** Writ now installs natively for Codex CLI with `adapters/codex.md`, Codex TOML agent translations, `AGENTS.md` Writ-block integration, `.codex/config.toml` seeding, and self-dogfooding `.codex/agents` support.

- **Codex lifecycle script parity.** `install.sh`, `update.sh`, `unlink.sh`, and `uninstall.sh` now understand `--platform codex`, including AGENTS.md merge/removal safeguards, install-once config behavior, and Codex-specific agent parity tooling.

### Changed

- **Lifecycle commands and README now document Codex.** `/update-writ`, `/reinstall-writ`, `/uninstall-writ`, `/refresh-command`, and README platform guidance cover Codex paths, TOML agents, restart expectations, and `.agents/skills/` behavior.

### Internal

- **Codex adapter spec package completed.** Added the completed `.writ/specs/2026-05-06-codex-cli-adapter/` audit trail with smoke evidence, story completion records, and source issue writeback.

## [0.17.0] - 2026-05-04

### Added

- **Skills — the third Writ primitive.** Reusable capability files (`skills/<name>/SKILL.md`) sit alongside commands and agents; commands and agents `Read` skills at the moment they need a tool. Foundation includes manifest schema, root catalog auto-render via `scripts/gen-skill.sh`, install/update fanout with three-way overlay, and boundary lint (`scripts/lint-skill.sh`) enforcing the verb/noun/tool roles per [ADR-009](.writ/decision-records/adr-009-command-agent-skill-boundary.md). All Writ-authored skills set `disable-model-invocation: true` so platforms don't ambient-load them. (Stories 1–3, 7)

- **`/new-skill` command** — three-phase scaffolder (capture → lint → write). Coaches verb-phrase descriptions before writing, runs the boundary lint pre-write, appends manifest entry alphabetically. (Story 6)

- **`/refresh-command --lint-skills`** — lints all `skills/*/SKILL.md` against the ADR-009 boundary; never auto-rewrites skill bodies. New Phase 5 in the standard `/refresh-command` flow. (Story 6)

- **`required_skills:` frontmatter convention** — schema documented across `system-instructions.md`, `cursor/writ.mdc`, and all three platform adapters (`cursor.md`, `claude-code.md`, `openclaw.md`). Reserve-only this release; no agent or command declares it yet. Review trigger: 2026-08-03. (Stories 4, 5)

- **`conventional-commits` skill — first pilot extraction.** Authors Conventional Commits messages (type, scope, summary, body, footers) from a diff; matches the project's existing convention when one exists; covers common anti-patterns. Lint-clean per `scripts/lint-skill.sh`.

- **Documentation surface for skills** — new `.writ/docs/skills.md` (canonical user-facing explainer), README "Three Primitives" + "Skills" sections, AGENTS.md updates, `.writ/docs/self-dogfooding.md` Skills section. (Story 7)

### Changed

- **`/ship`, `/release`, and the coding agent defer commit-format guidance to the `conventional-commits` skill** instead of inlining duplicate format spec. Single source of truth for message grammar; the commands retain orchestration concerns (splitting heuristic, source-mapping table, parsing-direction notes). Coding-agent commits now match `/ship`'s downstream format.

- **Root catalog `SKILL.md`** auto-renders the new "Available Skills" section when the manifest's `skills:` list is non-empty.

- **README refreshed for the new primitive** — "Three Primitives" section reflects the shipped pilot, "Skills" table added (parallel to the Agents table), `/new-skill` row added to "Setup & Lifecycle", command count corrected (30 → 31).

### Internal

- **Self-dogfooding parity for skills** — `.cursor/skills` and `.claude/skills` symlink to repo-root `skills/`, matching the existing pattern for `commands/` and `agents/`. Edits to any skill propagate to all three platforms via symlink.

- **Spec workspace** — `.writ/specs/2026-05-03-skills-foundation/` ships as the audit trail (spec, spec-lite, technical spec, 7 user stories, verification report).

## [0.16.0] - 2026-04-28

### Added

- **Daily Writ update awareness** — startup instructions now define a quiet first-in-session update check that runs before auto-orientation or command workflows, uses a once-per-day `.writ/state/` cache, and points copied installations to `/update-writ` only when an upstream update appears available. ([Daily Story 1], [Daily Story 2], [Daily Story 3])

### Internal

- **Daily update check spec package** — added the completed spec, technical spec, verification checklist, source issue linkage, and What Was Built records for the startup update awareness work.

## [0.15.0] - 2026-04-28

### Added

- **Writ runtime timestamp helper** — added the tiny `@sellke/writ` npm package surface for deterministic `date`, `timestamp`, and compact timestamp output, plus release guidance for public scoped publishing. This is a runtime helper for command metadata and filenames, not a general Writ CLI.

### Changed

- **Date helper references** — active Writ command docs now reference `npx @sellke/writ date` with local system date fallback where package availability should not block work.

## [0.14.0] - 2026-04-26

### Added

- **Knowledge ledger** — `.writ/knowledge/` directory for cross-cutting institutional
  knowledge (decisions, conventions, glossary, lessons), with the `/knowledge` command
  for capture and agent context-loading hooks at task start. Substrate is plain-text
  markdown over a database — see ADR-005. ([Story 1])

- **Spec `owner:` field** — recognized in `spec.md` frontmatter; `/verify-spec` Check 8
  flags missing owners (warning for legacy specs, required for new specs). Supports the
  team-readiness trajectory in ADR-007. ([Story 2])

- **SKILL.md auto-generation** — `.writ/manifest.yaml` is the single source of truth
  for command and agent listings; `scripts/gen-skill.sh` regenerates `SKILL.md` from it
  and CI fails if it drifts (`--check`). ([Story 3])

- **Preamble standing instructions** — `commands/_preamble.md` houses Prime Directive
  recap, knowledge-loading hook, and references convention; every command and agent
  gained a `## References` footer pointing to it. ([Story 4])

- **Eval Tier 1 static checks** — `scripts/eval.sh` runs required-section validation,
  broken-reference detection, length sanity, and anti-sycophancy phrase scanning across
  `.writ/` artifacts. GitHub Actions workflow (`.github/workflows/eval.yml`) enforces
  the gate on every PR and push. ([Story 5])

### Changed

- **Mission reframed** — `mission.md`, `mission-lite.md`, and `roadmap.md` name "code
  and methodology that doesn't degrade as projects, teams, and AI platforms churn
  around them" as Writ's destination, with audience sequencing solo-now → team-forward.
  See ADR-006, ADR-007, ADR-008.

- **Adapter docs** — Cursor, Claude Code, and OpenClaw guides each gained sections
  covering knowledge loading and the preamble convention.

- **`/implement-story` and core agents** — `coding-agent`, `documentation-agent`, and
  `user-story-generator` integrate the knowledge-loading hook directly; all other
  agents and commands carry the `## References` footer.

- **README** — `/knowledge` added to the Planning & Specification table;
  `.writ/knowledge/` and `.writ/eval/` added to the directory tree.

### Internal

- **Decision records** — ADR-005 (knowledge substrate: markdown over database), ADR-006
  (non-degrading destination), ADR-007 (team audience sequencing), ADR-008
  (spec-as-team-contract moat).
- **Spec format doc** — `.writ/docs/spec-format.md` formalizes spec frontmatter
  including the new `owner:` field.
- **Research** — `2026-04-24-writ-vs-gstack-rigor-comparison.md` informs the strategic
  refresh.
- **Phase 4 spec package** — full spec, sub-specs, 5 user stories with relocated
  verification checklists, two verification reports, and a CHANGELOG capturing the
  post-ship contract update.
- **Organic-validation issues** — two issues track Story 1 (knowledge loading on next
  Phase 5 feature) and Story 5 (remote CI gate). Story 5 confirmed in real-time on
  PR #15 (both eval CI runs PASS, ~6-8s).

[Daily Story 1]: .writ/specs/2026-04-28-daily-writ-update-check/user-stories/story-1-startup-protocol.md
[Daily Story 2]: .writ/specs/2026-04-28-daily-writ-update-check/user-stories/story-2-cache-and-detection-contract.md
[Daily Story 3]: .writ/specs/2026-04-28-daily-writ-update-check/user-stories/story-3-verification-and-issue-linkage.md

[Story 1]: .writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-1-knowledge-ledger.md
[Story 2]: .writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-2-spec-owner-field.md
[Story 3]: .writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-3-skill-md-generation.md
[Story 4]: .writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-4-preamble-enforcement.md
[Story 5]: .writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-5-eval-tier-1.md

## [0.13.1] - 2026-04-08

### Added

- **Plan Mode workflow integrity constraint** — Fourth Hard Constraint in Prime Directive: "Never let Plan Mode absorb a command's workflow." Prevents AI platforms from treating planning conversations as deliverables instead of producing documented artifacts. Applied to both `system-instructions.md` and `cursor/writ.mdc`.

- **Per-command Completion sections** — All 9 planning commands (`/create-spec`, `/plan-product`, `/new-command`, `/create-issue`, `/create-adr`, `/create-uat-plan`, `/research`, `/design`, `/edit-spec`) now have `## Completion` sections with concrete artifact requirements, suggested next steps, and terminal constraints prohibiting implementation offers.

- **Adapter Command Workflow Integrity** — Each adapter (Cursor, Claude Code, OpenClaw) has a `## Command Workflow Integrity` section naming its platform-specific tendency and countermeasure. `/prototype` signposted as escape valve for users who want fast implementation.

## [0.13.0] - 2026-04-02

### Added

- **Writ lifecycle management commands** — `/update-writ` (interactive update with per-file customization control), `/reinstall-writ` (full removal + fresh install), `/uninstall-writ` (remove platform files, preserve `.writ/`). Supports Cursor and Claude Code platforms. Codex and OpenClaw deferred to future work.
- **`scripts/uninstall.sh`** — Non-interactive terminal counterpart to `/uninstall-writ` with `--dry-run`, `--no-commit`, `--platform`, and `--include-writ` flags.

### Changed

- **README platform support** — Removed OpenClaw (deferred to future work alongside Codex). Command count updated 27→29. "Setup & Utilities" section renamed to "Setup & Lifecycle" with new lifecycle commands.
- **`/status` command allowlist** — Added `update-writ`, `reinstall-writ`, `uninstall-writ`.

## [0.12.0] - 2026-04-01

### Added

- **Ralph review sub-agent (Phase 2.5)** — Read-only review sub-agent in the Ralph CLI pipeline between validate and commit. Verifies acceptance criteria (per-criterion VERIFIED/UNVERIFIED), code quality, security, and spec drift before marking a story complete. PASS/FAIL/PAUSE contract matching Cursor's Gate 3 review agent. Closes the primary quality parity gap between CLI autonomous execution and supervised `/implement-story`.

- **Review back pressure** — Max 2 fix-and-re-review iterations per story (3 total reviews). Separate from the test/lint fix loop cap (3). Large drift triggers quarantine branching (`ralph/quarantine/{storyKey}`) and escalation to developer via `/ralph status`.

- **Ralph state schema extensions** — `reviewResult` (unknown/passed/failed/paused), `acVerified` ("N/M" format), `quarantineBranch` fields. Iteration log enriched with review data. New escalation types: `drift`, `review`.

### Changed

- **`/ralph status` display** — Completed stories show AC verification count and drift level. Failed stories surface review-specific errors (`review-failed`, `large-drift`) with quarantine branch guidance.
- **Ralph pipeline diagram** — Updated from 4 phases to 5 phases across `commands/ralph.md`, `PROMPT_build.md`, `ralph-cli-pipeline.md`, and `README.md`.
- **Claude Code adapter** — Key differences section updated for review sub-agent, architecture check omission, and sub-agent spawning clarification.
- **Changelog trimmed** — Entries for 0.7.0–0.11.0 archived in GitHub releases.

## [0.6.1] - 2026-03-20

### Fixed

- **`/implement-story` context schema title** — `context.md` schema heading corrected from `# Writ Context` to `# Writ Project Context`, matching the authoritative definition in the technical spec. Eliminates title inconsistency that could cause schema validation or parsing failures.
- **`/implement-story` context regeneration note** — Step 3 preamble now accurately states that `.writ/context.md` is regenerated once at Story Completion (Step 4), not after each gate. The prior wording implied per-gate regeneration that no gate implementation actually performed.

## [0.6.0] - 2026-03-20

### Added

- **Config persistence layer** (`/initialize`, `/ship`, `/release`, `/status`) — `.writ/config.md` as a shared convention store; commands load from it first, fall back to detection, and offer to persist detected values. Eliminates repeated convention re-detection across sessions.
- **Agent iteration caps** (`coding-agent`, `testing-agent`, `/implement-story`) — `MAX_SELF_FIX_ITERATIONS = 3` hard limit; agents emit `STATUS: BLOCKED` after 3 attempts; orchestrator surfaces a repair decision (retry / skip / abort) instead of silently continuing.
- **Spec-lite integrity check** (`/verify-spec`) — Check 9 detects material divergence between `spec-lite.md` and `spec.md`; `--fix` flag (and default auto-fix mode) fully regenerates spec-lite from the authoritative spec.
- **`/status` North Star rewrite** — Reads `.writ/config.md` for instant orientation; surfaces in-flight batch jobs from execution state files; surfaces `/refresh-command --batch` opportunities when 3+ transcripts accumulate; removes all legacy phantom command references.
- **Prototype → spec escalation** (`/prototype`, `/create-spec`) — On scope escalation, `/prototype` actively offers `/create-spec --from-prototype`; the new `--from-prototype` mode reads the current git diff, pre-populates the discovery contract, and marks Story 1 complete.
- **ADR unification** (`/plan-product`, `/create-adr`) — `/plan-product` now outputs foundational decisions as numbered ADR files (ADR-000-series) in `.writ/decision-records/` instead of `decisions.md`; `/create-adr` documents both ADR families and when to use each.
- **`.writ/context.md` auto-loading** (`/implement-story`, `/implement-spec`, `/status`, coding/review/arch-check agents) — Auto-maintained context snapshot (product mission, active spec, recent drift, open issue count); fully regenerated at each gate transition and story completion; loaded as the first context item by all three implementation agents.
- **Issue → spec promotion pipeline** (`/create-issue`, `/create-spec`, `/status`) — `spec_ref` field in issue template; `/create-spec --from-issue [path]` pre-populates the discovery contract from issue fields and writes `spec_ref` back on completion; `/status` surfaces stale untriaged issues (7+ days, no spec_ref).
- **`/refresh-command --batch` mode** — Ingests last N transcripts (default 5, overridable via `--n`); detects friction patterns recurring across 2+ sessions; recurrence-weighted proposals include frequency strings ("Observed in N/M sessions"); `/status` auto-triggers the suggestion when 3+ new transcripts accumulate since the last logged refresh.

## [0.5.0] - 2026-03-19

### Changed

- **Pipeline streamlining** (`/verify-spec`, `/ship`, `/release`) — each command owns one job. `/verify-spec` is a metadata-only diagnostic (checks 1–5 and 8) with default auto-fix; `/ship` skips tests unless `/ship --test`; `/release` runs an inline gate (spec validation, build probes when configured, conditional full test suite via `gh` merge-commit vs `HEAD`) before changelog work. Added `/release --skip-gate`. README command summaries aligned.
- **Migration docs** — `SKILL.md` and `commands/migrate.md` updated for the new flow (no `--pre-deploy` / Trello).

## [0.4.4] - 2026-03-19

### Fixed

- `unlink.sh` crashing with `unbound variable` on bash 3.2 (macOS default) when `DIR_SYMLINKS` array is empty — `set -u` treats `"${arr[@]}"` on an empty array as unbound. Fixed all four array iterations to use the `${arr[@]+"${arr[@]}"}` safe expansion pattern.

## [0.4.3] - 2026-03-19

### Removed

- **Symlink install mode** — `install.sh --link` is no longer offered. Copy mode is the only installation method for external users. Linked installations posed risks around shared mutable state and non-portable `.cursor/` directories.
- Link mode update handler in `update.sh` — now errors with guidance to convert via `unlink.sh`
- README "Link mode (power users)" section and "Copy vs Link" callout

### Added

- `scripts/unlink.sh` — converts existing symlinked Writ installations to independent file copies with manifest rewrite, supporting both per-file and directory-level symlinks
- `/migrate` entry in README command table (was documented in migration section but missing from the table)

### Changed

- `install.sh` retains defensive symlink-removal when it detects an existing linked installation, ensuring a clean conversion to copy mode
- `update.sh` rejects linked installations with a clear error pointing to `unlink.sh`

## [0.4.2] - 2026-03-19

### Fixed

- `install.sh` and `update.sh` `overlay_scan` silently exiting on `set -e` when the last file alphabetically needed an update — `[ "$mode" = "apply" ] && cp ...` returns exit code 1 in preview mode, which became the function's return value and killed the script. Replaced all `[ ... ] && ...` conditionals with `if/fi` blocks. Affected copy-mode install and update on all platforms.

## [0.4.1] - 2026-03-18

### Added

- **README freshness check in `/release`** — new Step 1.3 cross-references `README.md` against the repo before each release, catching silent staleness in command tables, agent tables, pipeline diagrams, and install URLs. Structural drift detection only; semantic accuracy remains a human judgment call.

## [0.4.0] - 2026-03-18

### Changed

- **A-Grade Command Refinement** — 12 commands refined across 4 spec batches, applying the litmus test: every line must teach something non-obvious, set a quality bar, or prevent a specific mistake — or it gets cut. Templates become principles. Net reduction of ~2,700 lines, zero capability lost.
  - `assess-spec` and `edit-spec` — continued core refinement; compressed assessment tables, replaced edit-spec templates with principles (-633 lines)
  - `initialize`, `research`, `create-adr` — utility commands refined ~57%; cut duplicate next-steps blocks, replaced 86-line document template and 155-line ADR template with principles, converted auto-execute research to prerequisite gate
  - `create-issue`, `design`, `prototype` — secondary commands refined ~47%; cut Excalidraw JSON schema and component primitives, rewrote 80-line agent prompt to 25 lines of principles
  - `new-command`, `refactor`, `review`, `retro` — remaining commands refined ~47%; collapsed 5 mode-specific refactor workflows into one principle, cut JSON/markdown templates and bash pseudocode

### Removed

- Verbose templates in all 12 commands — replaced with concise principles the AI can generalize from
- Redundant "AI Implementation Prompt," "Best Practices," "Common Pitfalls," "Future Enhancements," and "Integration Notes" sections across all refined commands
- Hardcoded line-number references in `new-command` template selection logic (broke on any edit)
- Excalidraw JSON schema and component primitive definitions in `design` (the AI knows SVG primitives)
- Dialog mockups and bash pseudocode that restated CLI behavior the AI already knows

### Added

- Refinement specs for 4 command groups: utility, secondary, remaining, infrastructure (Specs: `2026-03-18-*-command-refinement`)
- Infrastructure command refinement spec for the next batch (migrate, prisma-migration, test-database) — planning documentation, not yet implemented

## [0.3.0] - 2026-03-18

### Changed

- **Core A-Grade Refinement** — all 9 core command and agent files refined from mixed B-/B/B+/A- grades to A-grade quality (Spec: `2026-03-18-core-agrade-refinement`)
  - Templates replaced with principles — the AI knows how to format; tell it what matters
  - `/plan-product` reduced 56% (623 → 272 lines) — Phase 1 discovery preserved intact, Phase 2 templates replaced with principles
  - `/create-spec` reduced 43% (805 → 458 lines) — discovery phase untouched, file-creation templates condensed to principled guidance
  - `/implement-story` reduced 39% (469 → 285 lines) — drift response rewritten from 117 procedural lines to ~40 lines of principles
  - `/implement-spec` reduced 17% (294 → 244 lines) — already near A-grade, minor tightening
  - Review agent: 31-item checklist → 5 categorized review dimensions; examples condensed 50%
  - Documentation agent: framework-specific sections (VitePress, Docusaurus, Nextra, MkDocs, Storybook) replaced with single "follow detected conventions" principle
  - Coding agent: verbose scope detection heuristic → single-paragraph principle
  - Architecture-check and testing agents: condensed examples and removed redundant sections
- Clean testing boundaries between `/implement-spec` and `/verify-spec` — clarified which command owns test execution vs. verification

### Removed

- Redundant "Key Improvements," "Best Practices," "Tool Integration," and "Integration with Writ Ecosystem" sections from all commands
- `SwitchMode` API calls replaced with natural language guidance (Cursor doesn't support programmatic mode switching)
- Verbose output format examples in review and documentation agents — one example demonstrates judgment, not three

## [0.2.0] - 2026-03-16

### Added

- `/assess-spec` command — pre-implementation health check that flags oversized stories, deep dependency chains, context accumulation risks, and file-overlap conflicts with specific decomposition recommendations
- Pre-flight assessment hook in `/implement-spec` (Step 2.3b) — runs lightweight sizing checks automatically before showing the execution plan, with option to hand off to full `/assess-spec`
- AI workflow best practices research (`.writ/research/2026-03-16-ai-workflow-best-practices-research.md`) with self-challenge appendix validating Writ's thin-rule architecture

### Changed

- `install.sh` link mode now creates per-file symlinks instead of directory symlinks, enabling per-project command customization alongside linked Writ commands
- `install.sh` link mode auto-cleans stale symlinks when source files are removed upstream
- `install.sh` link mode now commits linked command and agent files to git (previously only committed manifest)
- README updated with `/assess-spec` in pipeline diagram, commands table, and key features

## [0.1.0] - 2026-03-15

First public release. Three completed specs deliver the full Writ pipeline — from product planning through retrospective.

### Added

**Phase 1 — Foundation** (Spec: `2026-02-27-phase1-foundation`)

- `/prototype` command — lightweight executor for quick changes without a full spec, with auto-escalation to `/create-spec` when complexity warrants it
- Tiered spec-healing review agent with drift detection and auto-amendment
- Drift report format (`drift-log.md`) for tracking spec amendments across story implementation
- `/refresh-command` — learning loop that scans agent transcripts and proposes concrete command diffs
- `/refresh-command` promotion pipeline for staged rollout of command updates
- Command overlay system enabling per-project customization of Writ commands
- `/plan-product` gstack enhancement with opinionated posture and strategic framing (DEC-006)

**Pipeline Quality Improvements** (Spec: `2026-03-13-pipeline-quality-improvements`)

- Coding agent self-check to reduce pipeline round-trips
- Weighted review with change surface classification for proportional review depth
- "What Was Built" record auto-generated on story completion
- Living spec auto-amendment when drift is detected during implementation
- Cross-spec consistency check in `/create-spec` to catch planning-level conflicts
- Documentation agent framework agnosticism — adapts to VitePress, Docusaurus, README, etc.

**Phase 2a — Shipping & Review** (Spec: `2026-03-15-phase2a-shipping-review`)

- `/ship` command — unified shipping workflow: merge default branch, run tests, split commits by concern, create PR with structured body and auto-labels
- `/review` command — standalone pre-landing code review with error & rescue maps, shadow path tracing, interaction edge cases, and failure modes registry
- `/retro` command — git-based retrospective with session detection, streak tracking, Ship of the Week, persistent JSON snapshots, and rolling trend analysis
- Error mapping in `/create-spec` for systematic error handling and rescue paths

**Infrastructure & Platform**

- Install script (`install.sh`) with manifest tracking, three-way merge, and `--link` mode for multi-project sync
- Update script (`update.sh`) with file-level preservation of user customizations
- Migration script (`migrate.sh`) for Code Captain → Writ transition with full artifact preservation
- Platform adapters: Cursor (native), Claude Code (subagent system), OpenClaw
- `/implement-spec` orchestrator with parallel batch execution and dependency graph resolution
- `/implement-story` 6-gate SDLC pipeline: arch-check → code → lint → review → test → docs
- Proportional verification strategy for `/implement-spec` — scales validation to change scope
- Plan Mode for open-ended discovery, AskQuestion for bounded decisions (ADR-001)
- Visual design system — `/design` command, visual QA agent, mockup management
- `.writ/` workspace directory structure for specs, research, retros, decision records, and documentation

### Fixed

- Cross-platform migration script compatibility (macOS + Linux)
- Documentation bugs across commands and agents
- Retro data contract: `test_ratio` uses numeric `0` instead of `null` for zero-test periods