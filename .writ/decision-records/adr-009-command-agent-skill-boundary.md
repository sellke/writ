# ADR-009: Command, Agent, Skill — Three Primitives with Distinct Roles

> **Date:** 2026-05-03
> **Status:** Accepted
> **Category:** Framework Architecture

## Decision

Writ keeps three first-class primitives — **commands**, **agents**, and **skills** — each with a distinct role and a directional composition relationship. Skills are added to the framework as a peer to commands and agents, not as a replacement for either. The file layout stays flat at the source level (`commands/`, `agents/`, `skills/` as siblings); install fanout handles platform-specific placement.

## The Three Primitives

### Command — The Verb

A command is a user-invoked workflow. It owns orchestration, phasing, and lifecycle. The user types `/command-name` to start it; the command runs through phases, may spawn agents to do role-specific work, and produces durable artifacts under `.writ/`. Commands are time-bounded — they begin, do their work, and terminate. Examples: `/create-spec`, `/implement-spec`, `/release`, `/refactor`. If a piece of work has a beginning, middle, and end that the user wants to invoke explicitly, it is a command.

### Agent — The Noun

An agent is a role with inherent behavior. A command spawns an agent to occupy a specific function — reviewer, coder, tester, documenter — for the duration of a phase. An agent has its own context, prompt, and quality bar; it is *not* user-invoked directly. Agents may be instantiated multiple times within a single command run (e.g. `review-agent` runs once per story; `coding-agent` runs once per feature branch). Examples: `coding-agent`, `review-agent`, `architecture-check-agent`. If a piece of work needs a persistent role identity that a workflow steps into, it is an agent.

### Skill — The Tool

A skill is a capability that agents (and commands) wield when relevant. It is not a workflow and it is not a role — it is *how to do a specific thing well*. A skill answers a "how do I X?" question with the right level of detail to do X correctly: how to write a conventional commit, how to structure an ADR, how to run an OWASP review, how to query Exa. Skills do not initiate work; they get pulled in by something that does. Examples (proposed): `tdd-cycle`, `conventional-commits`, `adr-writing`, `exa-search`. If a piece of work is a reusable capability that multiple commands or agents need to perform consistently, it is a skill.

## Composition Rules

Composition is **directional and acyclic**:

```
Commands  →  spawn  →  Agents
Commands  →  use    →  Skills
Agents    →  use    →  Skills
```

- **Commands compose agents.** A command's job is orchestration; agents do the role-specific work within phases.
- **Commands and agents both wield skills.** Skills are leaf-level capabilities with no children of their own.
- **Skills do not call commands.** Skills do not spawn agents. Skills do not call other skills. This keeps the dependency tree clean and prevents skills from quietly becoming workflows.

If a proposed skill needs to invoke a command or coordinate other skills, it is mis-classified — it is a command (or the smaller skills should be combined into the agent that uses them).

## Invocation Mechanism

**Decision: explicit invocation for Writ-authored skills; auto-invocation allowed for user-installed community skills.**

| Skill source | Invocation | Why |
|---|---|---|
| Writ-authored (`skills/` in product source) | Explicit — agent or command reads `skills/<name>/SKILL.md` via the platform's `Read` tool when the relevant phase begins | Deterministic, debuggable, traceable in transcripts; matches Writ's contract-first ethos |
| User-installed community skills (e.g. via `clawhub`, `agentskills.io` catalogs) | Whatever the platform decides — typically auto-invocation by description match | Out of Writ's control; do not fight the platform conventions |

Writ-authored SKILL.md files set `disable-model-invocation: true` in frontmatter so platforms with auto-loading do not silently inject them into command/agent contexts. Commands and agents that need a skill name it explicitly in their prompt with a `Read skills/<name>/SKILL.md` instruction.

This trades some convenience (no ambient skill loading) for predictability (every skill load is traceable). It also keeps Writ's behavior consistent across the four platforms whose skill loaders behave differently.

## File Format

**Decision: SKILL.md with YAML frontmatter, conforming to the AgentSkills open standard.**

Writ skills use the same file format as Cursor, Claude Code, Codex CLI, and OpenClaw skills (per the AgentSkills standard, released December 2025). This buys two things for free:

1. **Cross-platform compatibility.** A Writ skill installed in `.cursor/skills/`, `.claude/skills/`, `.codex/skills/`, or `.openclaw/skills/` works natively on each platform.
2. **Ecosystem distribution channels remain available** — Writ skills can be published to community catalogs if useful, and Writ users can pull in community skills without format translation.

What Writ adds on top of the format is **a role convention enforced by review**: a Writ skill describes a capability, not a workflow or a role. Skill descriptions begin with a verb-phrase ("Write conventional commit messages...", "Run an OWASP-style code review..."). Skills that read like commands ("Run the full spec implementation pipeline...") or like agents ("Acts as a senior staff engineer reviewing...") are rejected as mis-classified and re-homed.

## Boundary Examples

Concrete examples to make the boundary unambiguous:

| Concern | Classification | Why |
|---|---|---|
| Run the spec implementation pipeline through dependency-aware story batches | **Command** (`/implement-spec`) | User-invoked workflow with phases, lifecycle, and durable artifacts |
| Act as a code reviewer who verifies acceptance criteria, code quality, tests, and drift | **Agent** (`review-agent`) | Persistent role with its own context and quality bar, instantiated by a command |
| Write a commit message in Conventional Commits format given a diff | **Skill** (`conventional-commits`) | Reusable capability needed by multiple commands (`/ship`, `/release`) and agents (`coding-agent`); no workflow, no role |
| Run a TDD red/green/refactor cycle on a unit of work | **Skill** (`tdd-cycle`) | Reusable capability used by `coding-agent` and `/prototype`; describes *how* to do something, not orchestration |
| Structure an Architecture Decision Record with rigorous alternatives analysis | **Skill** (`adr-writing`) | Capability used by `/create-adr` and potentially `/knowledge`; the *workflow* of producing an ADR is the command, the *how* of writing one well is the skill |
| Run an OWASP Top 10 + STRIDE threat audit and produce a report | **Command** (`/security-audit`) — *not* a skill | User-invoked, multi-phase, produces durable artifacts; the OWASP *patterns* used inside it could be a skill (`owasp-review-patterns`) |
| Be the documentation engineer who detects the framework and updates docs | **Agent** (`documentation-agent`) — *not* a skill | A role with persistent identity and behavior, not a one-shot capability |

When in doubt, ask: *Is this work a workflow (command), a role (agent), or a capability (skill)?* If two answers feel right, the work probably needs to be split.

## Considered Alternatives

**A. Collapse to a single primitive (the GStack model).** GStack treats every workflow, role, and capability as a "skill," using one primitive across the board. This is genuinely simpler and gains it ecosystem leverage on 10+ platforms. Rejected because Writ's value proposition is contract-first methodology with crisp boundaries between specification, role, and capability — collapsing the primitives erodes the conceptual structure that makes Writ different from "another skill pack." We accept the cost of a richer mental model in exchange for the clarity it produces in long-running projects.

**B. Treat skills as tactical reference documentation only (not invocable capabilities).** Earlier iteration considered scoping skills to "shared knowledge between commands/agents," with no executable role. Rejected because it undersells what the SKILL.md format can carry and creates a third category of doc files that competes with `.writ/docs/`. The agents-wield-skills framing is sharper and gives skills a clear job.

**C. Add skills as platform-specific extensions inside each adapter.** Considered authoring skills only in adapter-specific format. Rejected because the AgentSkills open standard already exists and works on all four target platforms; reinventing the format would lose ecosystem compatibility for no gain.

## Consequences

**Positive:**
- Three primitives with verb/noun/tool semantics give users a clear mental model that maps to natural team metaphors
- Composition direction is acyclic, preventing the architectural drift seen when one primitive does everything
- SKILL.md format choice preserves cross-platform reach without compromising Writ's role conventions
- Explicit invocation mechanism keeps every skill load traceable in transcripts — important for contract-first debugging
- The boundary examples give reviewers a concrete test for new contributions

**Negative:**
- Three primitives have higher cognitive cost than one, especially for users coming from single-primitive frameworks (GStack, ClawHub-only setups). Mitigation: lead with the verb/noun/tool framing in `SKILL.md` (root catalog) and the README.
- Explicit invocation means agents and commands must name skills in their prompts — this is more verbose than ambient auto-loading. Mitigation: a small helper convention (e.g. a "Required skills" frontmatter block in agents that the harness pre-loads) can reduce repetition once the pattern stabilizes.
- The boundary requires enforcement during review. Without discipline, skills will drift into mini-workflows and the distinction will collapse in practice. Mitigation: add the boundary check to `/refresh-command` and to a future `/new-skill` command.
- Adapters need updating — none currently document skills. This is a one-time cost.

## Implementation Notes

**Prerequisites for any pilot skill work:**
1. This ADR accepted
2. `skills/` directory added at product source root
3. `scripts/install.sh` updated to fan out `skills/` to platform-specific paths (`.cursor/skills/`, `.claude/skills/`, `.codex/skills/`, `.openclaw/skills/`)
4. Each adapter (`adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md`, plus a new `adapters/codex.md`) gains a "Skills" section documenting where skills install and how they load on that platform
5. `.writ/manifest.yaml` schema extended with a `skills:` section; `scripts/gen-skill.sh` updated to render a Skills table in the root `SKILL.md`

**Pilot scope (separate spec):** 2–3 skills extracted from capabilities currently inlined in agents — strongest candidates by duplication signal are `tdd-cycle`, `conventional-commits`, and `adr-writing`. Pilot proves the integration before any broader extraction.

**Review date:** 90 days after first pilot skill ships — confirm the boundary held in practice or amend.

## References

- ADR-001 — AskQuestion vs Plan Mode in Commands (interaction tool selection precedent)
- ADR-008 — Spec as Team Contract Moat (contract-first ethos this ADR extends)
- AgentSkills open standard — [agentskills.io](https://agentskills.io)
- GStack architecture — [garrytan/gstack](https://github.com/garrytan/gstack) (alternative considered)
- Conversation source — chat session 2026-05-03 on framework skill strategy
