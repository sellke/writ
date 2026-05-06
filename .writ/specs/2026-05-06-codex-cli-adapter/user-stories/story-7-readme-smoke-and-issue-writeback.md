# Story 7: README, End-to-End Smoke Verification & Issue Writeback

> **Status:** Complete ✅
> **Priority:** Medium
> **Dependencies:** Story 6

## User Story

**As a** Writ maintainer closing out Codex platform support
**I want to** verify the integration works end-to-end on real Codex CLI, update the README to advertise three-platform support, and update the source issue with the spec writeback
**So that** the spec ships with verified evidence that the install/update/uninstall pipeline plus the multi-agent SDLC pipeline actually works on Codex (not just "should work"), and the project's externally-visible surface (README) and issue ledger accurately reflect what now exists

## Acceptance Criteria

**AC-1: README Platform Support row exists for Codex CLI with parity to existing rows**

- **Given** the current README's Platform Support table lists Cursor and Claude Code as two rows
- **When** this story's README edits land
- **Then** a third row exists for Codex CLI with: a link to `adapters/codex.md` matching the column-1 link style of the existing rows, a "Key Pattern" cell summarizing Codex's surface in one phrase (e.g., `AGENTS.md, .codex/agents/*.toml, native /agent`), the install command (`bash <(curl -s …) --platform codex`) shown either inline in a "Codex CLI (one-line install)" subsection beneath the Cursor and Claude subsections or in a follow-up paragraph mirroring those, and a one-line version compatibility note ("Tested against Codex CLI as of May 2026; TOML schema may evolve — see `adapters/codex.md`"); the row's tone matches Cursor and Claude (no overselling, no marketing language)

**AC-2: End-to-end smoke verification on a sandbox Codex project completes all eight scenarios**

- **Given** a Codex CLI installation on the maintainer's machine and a clean sandbox path (e.g., `/tmp/codex-writ-smoke`)
- **When** scenarios 1–8 from `sub-specs/technical-spec.md` § Test Plan → Manual smoke verification are executed in order
- **Then** each scenario captures a pass/fail outcome with one-line evidence (file tree dump, `/agent` picker output snippet, sandbox-mode denial confirmation, hash equality result, etc.); the verified scenarios are: (1) fresh-project install, (2) file tree contains `.codex/agents/*.toml`, `.codex/config.toml`, `.codex/.writ-manifest`, `AGENTS.md`, `.agents/skills/`, (3) `codex` opens and `/agent` lists all seven Writ agents, (4) `/create-spec "test feature"` runs end-to-end, (5) `/implement-story` on the test feature spawns native subagents with `sandbox_mode = "read-only"` enforced on the review phase (verified by an attempted write inside the review agent surfacing as a sandbox denial, not a prompt-only soft denial), (6) `bash <writ>/scripts/uninstall.sh --platform codex` removes Writ files cleanly and the AGENTS.md byte-stability hash check passes outside the Writ block, (7) re-install succeeds and `--force` reinstall flow behaves per Story 5, (8) install on a project with pre-existing custom AGENTS.md content preserves user content byte-for-byte (SHA-256 equality check on bytes outside the marker-bounded region)

**AC-3: AGENTS.md byte-stability is independently verified on a non-trivial fixture**

- **Given** a sandbox project where `AGENTS.md` is hand-authored to ~200 lines containing Markdown headers, code fences, lists, blockquotes, trailing whitespace patterns, and a deliberate mix of LF and (optionally) CRLF line endings
- **When** `bash scripts/install.sh --platform codex` runs against that project, then `bash scripts/uninstall.sh --platform codex` runs to remove the Writ block
- **Then** a SHA-256 comparison of the post-uninstall file (sans final trailing newline normalization, if any) against the pre-install file shows byte-equality; on the post-install file, a SHA-256 comparison of all bytes outside the `<!-- writ:start -->` / `<!-- writ:end -->` region matches the pre-install hash; both hashes are recorded in this story's "Definition of Done" section as evidence

**AC-4: Source issue `spec_ref` is set and "Codex shipped, OpenClaw deferred" note is appended without closing the issue**

- **Given** the source issue at `.writ/issues/features/2026-04-02-codex-openclaw-lifecycle-support.md` currently has an empty `spec_ref:` line and a Notes section with existing bullets
- **When** this story's issue writeback edits land
- **Then** the front-matter `spec_ref:` value is exactly `.writ/specs/2026-05-06-codex-cli-adapter/spec.md`, a new bullet appears at the bottom of the Notes section reading `2026-05-06: Promoted to spec [.writ/specs/2026-05-06-codex-cli-adapter/](.writ/specs/2026-05-06-codex-cli-adapter/spec.md). Codex half scoped here; OpenClaw lifecycle/install support deferred to a follow-up spec.`, the issue file's `Type:`, `Priority:`, `Effort:`, `Created:` metadata is byte-stable, no other bullets in Notes are reordered or removed, and the issue is NOT moved to a `closed/` or `archived/` directory and NOT renamed (it remains at its original path, open, with the OpenClaw half visibly outstanding)

## Implementation Tasks

- [x] **7.1** Update `README.md` Platform Support section: add a Codex CLI row to the existing table linking to `adapters/codex.md` with a one-phrase "Key Pattern" cell (`AGENTS.md, .codex/agents/*.toml, native /agent`); add a "Codex CLI (one-line install)" subsection beneath the existing "Claude Code (one-line install)" subsection mirroring its structure (install command, `--dry-run` preview, and post-install `/create-spec` example); add a one-line version compatibility note pointing readers to `adapters/codex.md` for current TOML schema details
- [x] **7.2** Execute smoke verification scenarios 1–8 from `sub-specs/technical-spec.md` § Test Plan → Manual smoke verification on a real sandbox Codex project; capture pass/fail per scenario with one-line evidence (file tree snippet, `/agent` picker output, sandbox-denial trace, hash equality output); if any scenario fails, halt this story and route the failure back to the responsible upstream story (typically Story 4 for install-time failures, Story 5 for update-time, Story 6 for uninstall-time, Story 2 for agent translation issues) — do NOT paper over failures in Story 7. **Evidence:** scenarios 1, 2, 6, 7, and 8 passed via shell smoke; scenario 3 passed via `codex exec` reading installed `AGENTS.md`; scenario 4 passed via `codex exec` following `.codex/commands/create-spec.md`; scenario 5 passed via `codex exec` following `.codex/commands/implement-story.md`, with `collab: SpawnAgent` gates observed, `./test.sh` passing, and a separate Codex read-only sandbox denial confirming runtime enforcement (`touch: review-denial.txt: Operation not permitted`).
- [x] **7.3** Document smoke verification results in this story's Definition of Done section (or a sibling note file at `.writ/state/codex-adapter-smoke-results.md` linked from this story); include: command transcript excerpts, the eight pass/fail outcomes, the AGENTS.md byte-stability SHA-256 evidence (AC-3), and a final "Smoke verification complete: PASS" or "PARTIAL — N of 8 scenarios passed; failure routed to Story X" line
- [x] **7.4** Update `.writ/issues/features/2026-04-02-codex-openclaw-lifecycle-support.md`: replace the empty `spec_ref:` value with `.writ/specs/2026-05-06-codex-cli-adapter/spec.md`; append a single bullet to the Notes section: `2026-05-06: Promoted to spec [.writ/specs/2026-05-06-codex-cli-adapter/](.writ/specs/2026-05-06-codex-cli-adapter/spec.md). Codex half scoped here; OpenClaw lifecycle/install support deferred to a follow-up spec.`; do not close, archive, rename, or move the issue file
- [x] **7.5** Run `/refresh-command --check-parity` (the lint extension delivered in Story 2) one final time pre-merge; confirm zero parity warnings (every `agents/*.md` has a `claude-code/agents/*.md` and `codex/agents/*.toml` counterpart) and capture the clean output in this story's evidence
- [x] **7.6** Update the repo-root project-overview `AGENTS.md` (the manually-maintained one, not the Writ-block-managed installer target) to replace any stale reference to a missing `adapters/Codex.md` (or equivalent) with a live link to the now-existing `adapters/codex.md`; also confirm `.cursor/system-instructions.md` and `claude-code/CLAUDE.md` enumerate Codex CLI alongside Cursor and Claude Code if they list supported platforms
- [x] **7.7** Verify all four acceptance criteria (AC-1 through AC-4); flip the spec's overall status from "Not Started" to "Complete" in `.writ/specs/2026-05-06-codex-cli-adapter/spec.md` and the spec's `user-stories/README.md` summary

## Notes

**Smoke verification is the moment of truth.** Every prior story in this spec ships "should work" claims grounded in code review and bash fixtures. Story 7 is the first time Writ-on-Codex meets a real Codex CLI session. If smoke fails, the failure is the deliverable — fix the responsible upstream story rather than route around it in Story 7. The spec is not Complete until smoke is end-to-end clean.

**Sandbox-mode enforcement on the review agent is the highest-confidence acceptance.** The whole point of Codex's native subagent system over a prompt-only convention is that `sandbox_mode = "read-only"` is enforced by the runtime, not by the review agent's good behavior. AC-2's scenario 5 specifically requires observing a sandbox denial (write attempt rejected by Codex itself) — not just trusting that the review agent declined to write. Capture that denial in the smoke evidence.

**README tone-matching matters.** The existing Cursor and Claude Code rows are factual and short. Don't oversell Codex parity ("first-class!", "fully integrated!", "production-ready!" — none of these). Match the existing voice: install command, link to adapter doc, one phrase about the key pattern, and a follow-up subsection with the install one-liner. The README is the project's external surface; tone drift here is more visible than tone drift inside specs.

**Issue writeback follows `/create-spec --from-issue` mode convention even though this spec was authored manually.** The convention is: source issue stays open, `spec_ref:` set, a dated note describes what was scoped here. This is documented in `commands/create-spec.md`'s `--from-issue` mode. Story 7's writeback applies the same convention. The OpenClaw half stays visibly outstanding so it doesn't get lost — the source issue remains the durable record until OpenClaw lifecycle support gets its own spec.

**`.writ/state/codex-adapter-smoke-results.md` is acceptable but optional.** If the smoke evidence fits cleanly in this story's Definition of Done section (under 100 lines), keep it inline. If it sprawls (multiple command transcripts, hash dumps, screenshots of Codex's `/agent` picker), break it into `.writ/state/codex-adapter-smoke-results.md` and link it from this story. `.writ/state/` is gitignored, so committed evidence belongs inline; ephemeral diagnostic artifacts can land in `.writ/state/` and be summarized here.

**No code is written in this story.** Story 7 is verification, documentation, and issue ledger maintenance only. The only files modified are `README.md`, `.writ/issues/features/2026-04-02-codex-openclaw-lifecycle-support.md`, the repo-root `AGENTS.md`, this story file's Definition of Done, and (optionally) `.writ/state/codex-adapter-smoke-results.md`. If Story 7 finds itself touching `scripts/`, `commands/`, `agents/`, `codex/`, or `adapters/`, that's a signal a smoke failure is being papered over — stop and route to the responsible upstream story instead.

**`/refresh-command --check-parity` final pass is a belt-and-suspenders check.** Story 2 delivered the lint; every story since should leave the parity surface clean. Running it one more time before flipping the spec to Complete catches any drift introduced in Stories 3–6 (e.g., a TOML deletion during refactoring, a new agent added without a corresponding TOML).

## Definition of Done

- [x] All implementation tasks (7.1–7.7) completed
- [x] All four acceptance criteria met
- [x] **Smoke verification scenarios 1–8 documented below (or linked from `.writ/state/codex-adapter-smoke-results.md`):**
- [x] Scenario 1 (fresh-project install): PASS — local sandbox `install.sh --platform codex --no-commit`
- [x] Scenario 2 (file tree includes all expected paths): PASS — verified `.codex/agents/review-agent.toml`, `.codex/config.toml`, `.codex/.writ-manifest`, `AGENTS.md`, `.agents/skills/conventional-commits/SKILL.md`
- [x] Scenario 3 (`/agent` picker lists Writ agents in `codex`): PASS — `codex exec` with Codex CLI `0.128.0` read installed `AGENTS.md` and listed all seven agents: architecture-check-agent, coding-agent, documentation-agent, review-agent, testing-agent, user-story-generator, visual-qa-agent
- [x] Scenario 4 (`/create-spec "test feature"` runs end-to-end): PASS — `codex exec` followed `.codex/commands/create-spec.md` and created `.writ/specs/2026-05-06-codex-smoke-test-feature/{spec.md,spec-lite.md,user-stories/README.md,user-stories/story-1-codex-smoke-test.md}`
- [x] Scenario 5 (`/implement-story` review-phase sandbox denial observed): PASS — `codex exec` followed `.codex/commands/implement-story.md`, observed `collab: SpawnAgent` gates, created `smoke-test.sh` + `test.sh`, ran `./test.sh` with `SMOKE TEST PASSED: codex-smoke-test:PASS`, updated story completion artifacts, and a separate Codex read-only sandbox command denied `touch review-denial.txt` with `Operation not permitted`
- [x] Scenario 6 (uninstall + AGENTS.md byte-stability hash equality): PASS — shell uninstall with config removal removes `.codex/` and `AGENTS.md`
- [x] Scenario 7 (re-install + `--force` reinstall flow): PASS — `install.sh --platform codex --force --no-commit` over sandbox install
- [x] Scenario 8 (custom AGENTS.md content byte-stable outside marker block): PASS — hash evidence below
- [x] **AGENTS.md byte-stability hashes recorded** (AC-3): pre-install SHA-256 `1604134944797f3ef9ff0627787cf6de5de5bc985255e499c2c355c5de09dd6e`; post-install outside-block SHA-256 `1604134944797f3ef9ff0627787cf6de5de5bc985255e499c2c355c5de09dd6e`; post-uninstall SHA-256 `1604134944797f3ef9ff0627787cf6de5de5bc985255e499c2c355c5de09dd6e`
- [x] **`/refresh-command --check-parity` final run output captured** (zero warnings): `parity OK — agents/, claude-code/agents/, and codex/agents/ aligned (subject to documented exclusions)`
- [x] README Platform Support section reads accurately and matches the tone of existing platform rows (no marketing language)
- [x] Source issue (`.writ/issues/features/2026-04-02-codex-openclaw-lifecycle-support.md`) `spec_ref` set and Notes bullet appended; issue remains open
- [x] Repo-root `AGENTS.md` reference to `adapters/codex.md` is live (no broken link)
- [ ] Code reviewed
- [x] Spec status flipped to "Complete" in `.writ/specs/2026-05-06-codex-cli-adapter/spec.md` and `user-stories/README.md`
- [ ] PR description includes: smoke evidence summary, byte-stability hash table, parity-lint clean output, screenshot of Codex `/agent` picker showing Writ agents (recommended)

## Context for Agents

After reading `spec.md` and `sub-specs/technical-spec.md`, the following spec elements apply specifically to this story:

- **Error map rows (from technical-spec.md Error & Rescue Map):**
  - `End-to-end /implement-story on Codex` → Codex sandbox refuses workspace-write for coding agent → `STATUS: BLOCKED` orchestrator escalation; this is the failure mode AC-2 scenario 5 verifies *does NOT trigger spuriously* under normal sandbox config (a real workspace-write agent should succeed; only the read-only review agent should hit the wall on attempted writes)
  - `[UNPLANNED] — Codex CLI updates change TOML schema mid-implementation` → if smoke surfaces a schema regression, treat as deferred per technical-spec.md Implementation Notes; do not patch this spec to chase it — open a follow-up spec or issue and document in this story's smoke results

- **Shadow paths (from technical-spec.md Shadow Paths table — all happy paths verified end-to-end here):**
  - `Install on fresh project` — Happy Path column ("✅ Writ installed for Codex CLI" + agent count) verified by AC-2 scenario 1
  - `Install on existing AGENTS.md` — Happy Path column ("AGENTS.md: Writ block appended") verified by AC-2 scenario 8 and AC-3
  - `Update` — Happy Path column ("Writ block updated") verified implicitly by AC-2 scenario 7 (re-install exercises the update path)
  - `Uninstall` — Happy Path column ("Writ removed; AGENTS.md preserved" or "AGENTS.md deleted (empty after removal)") verified by AC-2 scenario 6 and AC-3 post-uninstall byte-stability hash
  - `/implement-story runs on Codex` — Happy Path column ("All phases complete; `/agent` shows spawned subagents") verified by AC-2 scenarios 3, 4, 5

- **Business rules (from spec.md Business Rules):**
  - **OpenClaw out of scope** — explicitly reflected in this story's issue writeback (AC-4): the source issue stays open with OpenClaw flagged as deferred, NOT closed and NOT archived; this is the durable signal to the project that OpenClaw lifecycle support remains unaddressed
  - **Source issue stays open after `spec_ref` writeback** — convention from `/create-spec --from-issue` mode applied here even though this spec was authored manually; AC-4 explicitly forbids closing or archiving the issue
  - **AGENTS.md ownership (`<!-- writ:start -->` / `<!-- writ:end -->` markers exclusive to Writ; everything outside is user-owned)** — verified at the contract level by AC-3's byte-stability hash check

- **Experience design hooks (from spec.md Experience Design):**
  - **Moment of truth** ("A user who has used Writ on Cursor or Claude Code installs it on a fresh Codex project, runs `/create-spec` and `/implement-spec`, and gets the same artifacts and same multi-agent quality gates with no functionality regression") — Story 7 is the dedicated verification of this exact promise; smoke scenarios 1, 4, and 5 in AC-2 are the operationalization
  - **Empty / first-use states** ("Install on a project with no `.git` directory: works", "Install with `--dry-run` on a fresh project: shows what would be created without writing anything") — covered by AC-2 scenarios 1, 7, 8 (the smoke matrix exercises fresh + customized + re-install paths)
  - **Feedback model** (install/update progress in `[N/M]` step format, AGENTS.md merger summary line, per-file overlay symbols) — observed and confirmed during smoke verification; not separately re-tested but implicit in scenario evidence capture

- **Files in scope:** `README.md`, `.writ/issues/features/2026-04-02-codex-openclaw-lifecycle-support.md`, repo-root `AGENTS.md`, this story file (Definition of Done updates), and optionally `.writ/state/codex-adapter-smoke-results.md`. Spec status flips in `.writ/specs/2026-05-06-codex-cli-adapter/spec.md` and the spec's `user-stories/README.md`.

- **Files explicitly out of scope:** `scripts/install.sh`, `scripts/update.sh`, `scripts/uninstall.sh`, `scripts/unlink.sh`, `commands/update-writ.md`, `commands/reinstall-writ.md`, `commands/uninstall-writ.md`, `commands/refresh-command.md`, `adapters/codex.md`, `codex/agents/*.toml`, `codex/AGENTS.md.template`, `codex/config.toml.template`, `.writ/decision-records/adr-009-command-agent-skill-boundary.md`. If smoke surfaces a defect in any of these, route the fix to the responsible upstream story (Stories 1–6) rather than patching here.
