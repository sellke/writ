# Changelog — Model-Tier Delegation Spec

## 2026-07-18 — Pre-implementation contract correction

**Change type:** Contract correction (no completed work affected — spec was 0/24 tasks, Not Started)

**Trigger:** `/assess-spec` codebase verification surfaced four implementability risks before Story 1 execution.

**What changed:**

1. **ADR renumbering (🛑 collision fix).** `adr-014-model-tier-delegation.md` → `adr-016-model-tier-delegation.md` across all references (10 occurrences). `adr-014` and `adr-015` were claimed by sibling same-day specs (`skill-lifecycle`, `leanness-guardian`) before this spec's Story 1 could run; `adr-016` was confirmed free at edit time.
2. **Carrier terminology clarified.** "Agent frontmatter" language replaced with "Agent Configuration block" (the actual fenced `subagent_type:`/`model:`/`readonly:` block in `agents/*.md` — verified no `---` YAML header exists there). Skills retain real `---` frontmatter (unchanged).
3. **Command tier mechanism corrected.** Verified 0/31 `commands/*.md` files carry a `---` frontmatter block. Story 4 (and all references) now specify that `/new-command` documents advisory `model_tier` as a **prose note** near Overview/Invocation, not YAML frontmatter. Introducing real command frontmatter is now explicitly out of scope.
4. **Claude Code adapter scope firmed up.** `adapters/claude-code.md` § Model Selection already runs a concrete `inherit`/`sonnet`/`haiku` mapping, not a clean binary fast/inherit primitive. Story 3's conditional "defer if no native distinction" task replaced with a firm task: fold in using concrete model names, mirroring the Codex mini-ID pattern. Added Scenario 6 to Story 3's acceptance criteria.

**Files updated:** `spec.md`, `spec-lite.md`, `sub-specs/technical-spec.md`, `user-stories/README.md`, `user-stories/story-1-tier-contract-adr.md`, `user-stories/story-2-agent-adoption.md`, `user-stories/story-3-adapter-resolution.md`, `user-stories/story-4-authoring-lint-docs.md`

**Backup:** `.writ/specs/2026-07-10-model-tier-delegation/backups/20260718-105002/`

**Task count:** 4 stories, 25 tasks total (was 24). Story 1 gained one implementation task (carrier-per-file-type note), bringing its count to 7 (previously 6). Still well under the assess-spec sizing thresholds (>7 tasks/story warns).
