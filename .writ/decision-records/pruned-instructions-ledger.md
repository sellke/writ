# Pruned Instructions Ledger

> Append-only. One row per line removed from system-instructions.md or commands/_preamble.md
> since cf84742 (Phase 11 Stage 1 closeout). Checked by scripts/prune-ledger.py.
> Rule: ADR-026. Columns: date of removal · source file · class (`moved` = reason is the
> destination path; `behavior-request` = why the model does it unprompted, ≤ 120 chars;
> `duplicate` = where the surviving copy lives) · reason · removed text verbatim, `|` escaped as `\|`.

| Date | File | Class | Reason | Text |
|---|---|---|---|---|
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | Writ delegates by role, not by depth — [ADR-024](.writ/decision-records/adr-024-model-delegation.md), which supersedes ADR-016 (history only). Only **agents** carry `model_tier`, in their existing fenced block — `## Agent Configuration` with a plain fence (6 agents) or `## Agent Specification` with a `yaml` fence (`visual-qa-agent.md`). Commands run at the session model and carry `entry_level` (below); skills carry nothing. A concrete `model:` always wins over `model_tier:`. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \| Tier \| Meaning \| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \|---\|---\| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \| `anchor` \| The user's session model — the platform's `inherit`. \| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \| `floor` \| The cheapest same-family configuration at or below the anchor. \| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | **Derive the tier — two questions, in order:** |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \| Question \| Yes \| No \| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \|---\|---\|---\| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \| **Q1.** Does the agent decide anything for others — spawn agents, route context, or judge another agent's output? \| `anchor`. Stop. \| Ask Q2. \| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \| **Q2.** Is its output bounded (a template, a checklist verdict, a summary) **and** checked by a later gate or a human before it takes effect? \| `floor` \| `anchor` \| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | Applied: `coding-agent` (open-ended), `review-agent`, `testing-agent`, `visual-qa-agent` (judge), `documentation-agent` (nothing checks it) → `anchor`; `architecture-check-agent` (checklist verdict; later gates catch a wrong PROCEED), `user-story-generator` (templated; the user reviews before lock) → `floor`. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | **Origin.** Commands that spawn agents read — never ask — the **origin** at entry: `anchor.model` (name or `unknown`), `anchor.effort` (`low\|medium\|high\|…` or `unknown`), `anchor.platform`. It is stamped as `origin=<model>/<effort>@<platform>` on ADR-017 audit records, `recommendation-log.md` entries, and every `escalated`/`degraded` line — no new state file; the user sees it only in the entry notice below. **The anchor is the ceiling:** no spawn resolves above `anchor.model` or `anchor.effort`, and escalation returns to the anchor, never past it. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | **Resolve `floor`**, in order, never crossing vendors: (a) the anchor's family at its lowest tier below `anchor.model`, if the platform exposes one; (b) the anchor at the lowest effort below `anchor.effort` (`low` when unknown); (c) the anchor. When the origin already sits at the family floor, `floor` collapses to `anchor`, the run says so once, and no `degraded` line is emitted — that is correct, not degraded. Otherwise (c) emits `degraded`. Per-platform values live in `adapters/*.md`. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | **Escalate once.** A `floor` result that fails its check, or would interrupt the human, is re-run once at `anchor`; the anchor result stands; the pair counts as one attempt against `loop.max_iterations`; each re-run emits `escalated` (a no-op until ADR-025 Story 1). Sites today: `/create-spec` Step 2.6 story validation and `/implement-story` Gate 0 ABORT. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | **Degradation** — nothing hard-fails: |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \| Condition \| Behavior \| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \|---\|---\| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \| `model_tier` unset \| Inherit (`anchor`). No warning. \| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \| `orchestration` / `capability` \| Lint warns; resolves as `anchor` / `floor`. Rejected after the alias window `scripts/lint-skill.sh` names. \| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \| Unknown value \| Lint fails at authoring; at runtime warn `unknown model_tier '<value>'; running at anchor` and run at `anchor`. \| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | \| Both `model:` and `model_tier:` \| `model:` wins. No warning. \| |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | ### `entry_level` |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | Every command declares `entry_level: high \| standard \| any` in its existing `---` frontmatter, after `outcome:` — not what it runs at (Writ cannot choose) but what it expects the user to have chosen. Derive it: **Q1** — spawns agents, locks a contract (spec/ADR/roadmap/design), or renders an unverified judgment the user acts on (review, audit, research, drift assessment)? → `high`. **Q2** — creates or modifies durable project artifacts (specs, issues, code, docs, git state; derived caches do not count)? → `standard`. Otherwise → `any`. Commands do not repeat the following text: |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | > At entry, compare the captured origin against this command's `entry_level`. If the origin |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | > is below it, print exactly one line and continue: |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | > This command expects `<level>` entry; you're running `<model>/<effort>`. Floor-tier retries cannot escalate above this. Consider re-running at a higher thinking level. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | > Print it at most once per session. Never ask. If the origin is `unknown`, skip the check. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | > "Below" is your own assessment against: `high` — a frontier-class model of its family at a |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | > non-minimal thinking level; `standard` — a non-smallest model, or medium-plus effort; |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/model-tiers.md | > `any` — nothing. |
