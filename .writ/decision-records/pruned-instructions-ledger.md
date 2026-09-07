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
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | ### `required_skills:` frontmatter convention |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | Commands and agents may declare a `required_skills:` array in their frontmatter to have the harness pre-load named skills before the consumer's first phase begins: |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | ```yaml |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | --- |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | name: example-agent |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | required_skills: |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md |   - tdd-cycle |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md |   - conventional-commits |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | --- |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | ``` |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | **Schema:** |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | - `required_skills` is an **optional** array of strings. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | - Values are skill names matching `name:` entries in `.writ/manifest.yaml`. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | - Order is **preserved** — downstream tooling may use it for load priority. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | - Duplicates are **silently deduplicated**. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | - Unknown skill names produce a **warning** at consumer load time, not a hard failure (graceful degradation: a pilot extraction may rename a skill mid-flight; consumers should not hard-fail). |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | **Harness contract:** |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | When a consumer with `required_skills: [foo]` is invoked, the harness loads `skills/foo/SKILL.md` (typically via `Read skills/foo/SKILL.md`) and makes it accessible to the agent before any phase work begins. Per-platform mechanism is documented in each adapter's Skills → Invocation subsection (`adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md`). |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | Without the field, agents and commands continue to inline `Read skills/<name>/SKILL.md` instructions in their prompts at the point where the skill is needed. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | **Status: documented, no consumer.** The 2026-08-03 review resolved **revisit → adopt** on a justification that rested almost entirely on one named future consumer: Phase 10 progressive disclosure. That consumer evaluated the mechanism and did not adopt it. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | `required_skills:` is an **eager pre-load** — the harness loads every declared skill before any phase work begins (see **Harness contract** above), and selection is per **command**, never per **run**. A static array cannot express "only what this invocation needs", so extraction under this field moves the extracted bytes into the floor that every invocation pays, and a disclosed command costs more than the monolith it replaced. Phase 10 uses an inline `Read skills/<name>/SKILL.md` at the point of need instead, which is conditional. [ADR-021](.writ/decision-records/adr-021-progressive-disclosure-token-budget.md)'s 2026-08-12 amendments carry the full record. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | The schema stays documented — `/new-skill`, all three adapters, and `check_required_skills()` reference it. Deprecating it is an ADR-scale decision; the spec that found the mechanism wrong for a single phase does not make it. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | **Review trigger: 2026-11-11**, aligned to ADR-021's own review, which already reads the per-invocation data that would justify a consumer. The trigger is restored because the adoption's premise proved false. **Terms:** if no command or agent declares `required_skills:` by then, deprecate; if one does, record it and reset. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | ### Skill authoring |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | Use `/new-skill <name>` to scaffold a new skill with the role convention (verb-phrase description, `disable-model-invocation: true` frontmatter, boundary lint enforced at authoring time). `/refresh-command` includes a boundary check that lints existing skills. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/skills.md | Writ-authored SKILL.md files set `disable-model-invocation: true` so platforms with skill auto-discovery don't ambient-load them. Every skill load is explicit and traceable. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | Startup sequence: |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | 1. Detect whether the current project appears to use Writ and whether the invocation is already `/update-writ`. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | 2. Read `.writ/state/writ-update-check.json` if it exists. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | 3. If the cache records today's local date in `last_checked_date`, skip upstream network work and continue silently. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | 4. If the cache is missing, stale, malformed, or missing `last_checked_date`, treat it as no valid same-day cache and continue through conservative eligibility checks. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | 5. If no same-day cache exists, perform at most one lightweight, read-only upstream probe using existing manifest/source metadata when available. The probe must compare the installed Writ identity (version, revision, or release tag when available) against the upstream identity; a reachable upstream source or successful network response alone is not evidence of an update. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | 6. Record today's result under `.writ/state/`; create `.writ/state/` only when recording a result. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | 7. Notify only when a copied Writ installation has a strictly newer upstream identity and today's recorded `status` is `update_available`. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | 8. Continue the user's original request, auto-orientation, or command workflow. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | Cache contract: |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - Preferred path: `.writ/state/writ-update-check.json` |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - Required daily-limit field: `last_checked_date` as a local `YYYY-MM-DD` date |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - Recommended metadata: `source`, `installed_version`, `installed_revision`, `latest_seen_version`, `latest_seen_revision`, `status`, and `checked_by` |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - Allowed `status` values: `current`, `update_available`, `skipped_unsupported`, `skipped_source_repo`, `skipped_linked_install`, and `upstream_error` |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | Detection rules: |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - Copied install with usable manifest/source metadata and a strictly newer upstream version, revision, or release tag: record `update_available` and show the `/update-writ` note. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - Copied install with usable manifest/source metadata and matching or older upstream identity: record `current` and stay quiet. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - Copied install where upstream is reachable but installed-vs-upstream comparison is unavailable, ambiguous, or unordered: record `skipped_unsupported` or `upstream_error` and stay quiet. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - Missing manifest/source metadata, uncertain installation class, or unsupported installation shape: record or skip as `skipped_unsupported` and stay quiet. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - Writ source repo: record or skip as `skipped_source_repo`; do not recommend `/update-writ`. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - Linked installation: record or skip as `skipped_linked_install`; do not recommend `/update-writ`. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - Network, timeout, auth, or upstream probe failure: record `upstream_error` for the day and stay quiet. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | - User explicitly invoked `/update-writ`: do not show a duplicate startup update prompt. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | Use this exact notification style only after recording `status: "update_available"` for a copied install with a strictly newer upstream identity: "Writ update available. Run `/update-writ` when you are ready." |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | Stay quiet and continue the original workflow when Writ is current, already checked today, offline, missing usable manifest/source metadata, unsupported, running from the Writ source repo, running from a linked installation, or already executing `/update-writ`. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/startup-update-awareness.md | Startup update discovery is read-only except for the daily cache under `.writ/state/`. It must never apply updates, overwrite Writ files, edit manifests, install packages, create commits, clone or pull repositories, or add an `@sellke/writ` update-check runtime command. `/update-writ` remains the only Writ workflow that applies updates. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md | - **Use evidence, never presentation defaults.** Option order, affirmative wording, and user inactivity are never evidence. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   Evaluate only the domains relevant to the decision, in this precedence: |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   governance and safety eligibility → locked artifacts → current repository or provider state → project conventions → simplicity and reversibility. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   Higher-precedence |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   evidence establishes eligibility or constraints; it does not substitute for |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   missing evidence in another domain. Conflicting authoritative evidence pauses the decision. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md | - **Select or pause transparently.** In `--recommend` mode, automatically select |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   an eligible evidence-supported option. When multiple eligible choices remain |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   low-risk and reversible, select the simplest viable, most reversible choice. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   Pause for safety, security, data integrity, compliance, unexpected cost, destructive or irreversible pre-production behavior, core-contract ambiguity, or subjective taste without evidence. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   Hard platform blockers remain blockers. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   A pause states the classification, missing or conflicting evidence, bounded |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   choices, and a safe next action. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md | - **Emit concise audit rationale.** Briefly show these fields in the active |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   session: Decision, Evidence, Alternatives, Risk, Reversibility, Selection source, and Result/artifact. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   Evidence must be observable; alternatives include only material options. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   Never include private chain-of-thought or transcript content. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md | - **Resume only the answered interaction.** After a required human answer, continue automatically in the same session with recommendation mode retained and do not repeat the answered decision. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   This is an in-session behavioral contract only. |
| 2026-09-07 | system-instructions.md | moved | .writ/docs/recommendation-semantics.md |   Story 3 owns durable logging, execution state, reconciliation, and cross-session resumption. |
