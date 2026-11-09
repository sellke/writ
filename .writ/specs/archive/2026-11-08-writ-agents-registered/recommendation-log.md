# Recommendation Log

> Spec: 2026-11-08-writ-agents-registered

## 1. Contract lock

- **Decision:** lock the contract as drafted.
- **Evidence:** the issue states the current state, three expected outcomes, and the relevant files; codebase scan confirmed `.claude/agents -> ../agents`, frontmatter only in `claude-code/agents/`, `install.sh` copying `claude-code/agents/`, and no fallback in the adapter or Gate 1.
- **Alternatives:** copy generated files into `.claude/agents/` (rejected: CLAUDE.md forbids regular-file copies there); generate frontmatter into `agents/` (rejected: Cursor and Codex read `agents/` and the canonical files are platform-neutral).
- **Risk and reversibility:** low; a symlink change and prose, reverted with `git revert`.
- **Result:** the maintainer chose "Lock and create" (2026-11-08).

## 2. Inline coding

- **Decision:** never a Gate 1 path; a missing type goes to the fallback spawn, then BLOCKED escalation.
- **Evidence:** the issue's expected outcome ("Inline coding, if allowed at all, is disclosed and makes the supervisor escalate"); Phase 16's waiver needed a person; the 2026-11-08 `archived-dependencies-resolve` run used the general-purpose fallback successfully.
- **Alternatives:** allow inline coding with disclosure (rejected: it is the failure the issue records).
- **Risk and reversibility:** low; prose only.
- **Result:** in the locked contract (Business Rule 4).

## 3. Story decomposition and sub-specs

- **Decision:** two stories (register; fallback rule); technical-spec only.
- **Evidence:** the link and check are independent of the prose rules; no data flow, API, or UI.
- **Result:** acted on.
