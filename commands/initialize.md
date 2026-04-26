# Initialize Command (initialize)

## Overview

Set up technical foundation by detecting whether this is a greenfield (new) or brownfield (existing) project, then executing the appropriate workflow. This command handles *technical infrastructure only* — product strategy belongs to `/plan-product`.

### Detection Logic

Auto-detect project type — never ask the user which workflow to run.

1. **Scan current directory** for indicators:
   - Dependency manifests (package.json, requirements.txt, Cargo.toml, go.mod, etc.)
   - Source directories (src/, lib/, app/, etc.)
   - Git history depth and commit count
   - Configuration files (.eslintrc, tsconfig.json, Dockerfile, etc.)

2. **Classify as:**
   - **Greenfield** — empty directory or only boilerplate files (README, LICENSE, .gitignore)
   - **Brownfield** — existing codebase with established structure and dependencies

**Edge case:** A freshly scaffolded project (e.g., `create-react-app` just ran) is greenfield — it has structure but no custom code. Look for meaningful source files and git history beyond the initial commit, not just directory presence.

After classification, announce the result and the evidence: *"Detected brownfield project — found package.json with 47 dependencies, src/ with 200+ files, 6 months of git history."* This gives the user a chance to correct a misclassification before proceeding.

`.writ/` exists from installation; create docs within `.writ/docs/`.

## Invocation

| Invocation | Behavior |
|---|---|
| `/initialize` | Auto-detect project type and run appropriate workflow |

---

## Greenfield Workflow

### Phase 1: Technical Discovery

Ask focused questions to determine technical requirements. Four areas matter:

| Area | What to learn |
|---|---|
| **Project type** | Web app, API, mobile, library, CLI, etc. |
| **Constraints** | Required technologies, frameworks, platforms |
| **Environment** | Local, containerized, cloud-based development |
| **Scale** | Prototype, small team, enterprise |

Batch related questions. Skip areas with obvious answers from context.

### Phase 2: Technology Recommendations

Present recommendations across these categories before building anything:

- **Tech stack** — languages, frameworks, databases matched to project type and scale
- **Architecture pattern** — monolith, microservices, serverless with rationale
- **Development tooling** — testing, build tools, linting/formatting
- **Project structure** — directory layout, naming conventions

Get explicit agreement before proceeding. Push back if the user's preferences conflict with their stated requirements.

**Recommendation principles:** Favor ecosystem maturity and community support over novelty. For enterprise scale, flag risk of bleeding-edge choices. For prototypes, optimize for speed-to-working-demo over long-term scalability — but note the trade-off explicitly.

### Phase 3: Build Foundation

Create the project skeleton and documentation.

**Project files:** Dependency manifests, git configuration (.gitignore, .gitattributes), development tool configs (linter, formatter, test runner), build/deploy configuration as needed. When the chosen framework has its own project structure conventions (Next.js, Rails, Django, etc.), follow them — don't invent a custom layout.

**Documentation — three required files:**

| File | Content |
|---|---|
| `.writ/docs/tech-stack.md` | Languages, frameworks, infrastructure, architecture pattern — each with version and rationale for selection |
| `.writ/docs/code-style.md` | File organization patterns, naming conventions, code patterns, testing patterns, documentation style |
| `README.md` | Project overview, prerequisites, setup instructions, development workflow |

**Quality bar:** Each doc captures *decisions and reasoning*, not just lists. A new developer should understand both what was chosen and why.

After creating all files, verify the project runs — execute the basic dev command (e.g., `npm run dev`, `cargo build`) and fix any setup issues before declaring the foundation complete.

**Write `.writ/config.md`** after the project runs successfully. This is the natural save point — the user just configured everything, so no confirmation is needed. Use the format defined in `.writ/docs/config-format.md`. Record the conventions established during setup: Default Branch, Test Runner, Merge Strategy, Version File, Test Coverage Tool, and Changelog path. Example:

```markdown
# Writ Project Config

> Last Updated: [date]
> Auto-generated — edit manually if needed

## Conventions

- **Default Branch:** main
- **Test Runner:** npm test
- **Merge Strategy:** merge
- **Version File:** package.json
- **Test Coverage Tool:** jest --coverage

## Paths

- **Changelog:** CHANGELOG.md
- **Writ Specs:** .writ/specs/
- **Writ Issues:** .writ/issues/
```

---

## Brownfield Workflow

### Phase 1: Codebase Analysis

Scan the existing project systematically. No questions needed — the code tells the story.

**Scan strategy:** Read dependency files, but also check what's *actually imported* in source code — some dependencies are vestigial. Check CI configs and deployment scripts for the real build/deploy story. Git log frequency by directory reveals which areas are actively developed. For monorepos, scope analysis to the relevant package unless the user indicates otherwise.

| Analyze | What to capture |
|---|---|
| **File structure** | Organization patterns, module boundaries |
| **Dependencies** | Full technology stack with versions; distinguish primary from supporting (e.g., a TS project with Python scripts) |
| **Code patterns** | Conventions, architecture, recurring idioms |
| **Configuration** | Build processes, environment setup |
| **Testing** | Framework, coverage approach, test organization |
| **Documentation** | What exists, what's missing |

### Phase 2: Documentation Generation

Create the same three files as greenfield, derived from analysis rather than choices:

| File | Content |
|---|---|
| `.writ/docs/tech-stack.md` | Discovered stack — languages, frameworks, infrastructure, architecture pattern with observed rationale |
| `.writ/docs/code-style.md` | Observed patterns — file organization, naming conventions, code idioms, testing patterns |
| `README.md` | Only create if missing; update if incomplete. Never overwrite a curated README — append a "Development Setup" section if one is missing |

**Quality bar:** Document what the codebase *actually does*, not what it should do. Distinguish intentional patterns (consistent across the codebase) from accidental ones (copy-paste artifacts). Flag inconsistencies as observations, not corrections.

### Phase 3: Gap Analysis

Identify improvement opportunities across these categories:

| Category | Look for |
|---|---|
| **Documentation gaps** | Missing or outdated docs, undocumented decisions |
| **Pattern inconsistencies** | Conflicting conventions, mixed approaches |
| **Technical debt** | Known shortcuts, deprecated dependencies, security concerns |
| **Testing coverage** | Untested areas, missing test types |
| **Developer experience** | Workflow friction, missing automation |
| **Architecture** | Scaling concerns, optimization opportunities |

Present findings as a prioritized list with effort estimates (quick win / moderate / significant). This becomes the backlog for future `/create-adr` and `/research` work.

**Prioritization principle:** Lead with gaps that block developer onboarding or cause silent bugs. Cosmetic inconsistencies go last.

---

## Next Steps

Present a completion summary showing what was created or documented, then recommend next steps. `/plan-product` is the natural next step for both workflows — initialize handles technical foundation, plan-product handles product strategy. Users need both before feature development.

**Completion summary should include:** files created/updated, key decisions documented, and (for brownfield) top 3 gap findings.

Present the recommendation prominently:

- **Primary:** `/plan-product "your product vision"` — define product strategy and roadmap
- **Alternatives:** `/create-spec` to jump to feature specs, `/research` to investigate identified gaps, `/create-adr` to document architectural decisions

Do not end the command without presenting this recommendation. It's the bridge between technical setup and product development.

**Write `.writ/config.md`** with conventions discovered during analysis (same format as the greenfield path — see above). For brownfield, offer to save: *"Detected conventions: [values]. Save to `.writ/config.md`? (y/n)"* — write only on **y**. If a `.writ/config.md` already exists, do not overwrite it without explicit confirmation.

---

## Integration with Writ

| Command | Relationship |
|---|---|
| `/plan-product` | Natural next step — defines product strategy using the technical foundation established here |
| `/create-spec` | Uses tech-stack.md and code-style.md to inform feature specifications |
| `/research` | Investigates gaps identified during brownfield analysis |
| `/create-adr` | Documents architectural decisions surfaced during initialization |

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)
