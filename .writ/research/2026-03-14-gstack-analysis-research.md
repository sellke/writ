# What Writ Can Learn from gstack

**Date:** 2026-03-14
**Status:** Complete

## Research Question(s)

What design patterns, commands, and philosophical approaches from Garry Tan's gstack could meaningfully improve Writ — particularly in the areas of product orientation, retrospectives, and shipping workflow?

## Executive Summary

gstack and Writ occupy similar territory — both are opinionated AI workflow systems built as Markdown-as-instructions. But they solve different problems with different philosophies. gstack is a **cognitive mode switcher** ("what kind of brain do I need right now?") while Writ is a **pipeline orchestrator** ("how do I move from idea to shipped code?"). The most valuable lessons aren't about copying commands — they're about absorbing gstack's relentless product ambition and feedback loop thinking, then integrating those qualities into Writ's already-strong pipeline.

Three high-impact opportunities emerged:

1. **Inject "10-star product" thinking into `/plan-product` and `/create-spec`** — gstack's CEO review mode challenges premises and pushes scope *up*, not just down. Writ's discovery conversations are thorough but information-gathering; they could be aspirational.
2. **Build `/retro`** — Writ's own SWOT analysis identified this as a priority. gstack's implementation is comprehensive and battle-tested: git-based metrics, session detection, team-aware praise/growth, trend tracking, and streak counting.
3. **Create a `/ship` command** — Writ has `/release` (changelog + versioning) but no unified "merge, test, review, push, open PR" workflow. gstack's `/ship` is the strongest command in the set — fully automated, non-interactive by default, with bisectable commit splitting.

## Background & Context

**gstack** (github.com/garrytan/gstack) is a Claude Code skill pack by Garry Tan (YC President/CEO). Eight workflow commands: `/plan-ceo-review`, `/plan-eng-review`, `/review`, `/ship`, `/browse`, `/qa`, `/setup-browser-cookies`, `/retro`. ~10K stars. Built on Bun/TypeScript with a persistent Chromium daemon for browser automation.

**Writ** is a Cursor-native (but platform-agnostic) AI development partner. 22 commands spanning product planning, spec creation, implementation, review, release, and more. Built as pure Markdown instructions with adapter patterns for different AI platforms.

Both systems share core beliefs: contract-first planning, structured workflows over ad-hoc prompting, and the importance of challenging assumptions. They diverge on execution philosophy — gstack favors explicit cognitive mode selection, Writ favors pipeline orchestration with gates.

## Methodology

- Read all 8 gstack SKILL.md files (full text of each command's instructions)
- Read gstack's ARCHITECTURE.md and CLAUDE.md for design rationale
- Compared against Writ's `/plan-product`, `/create-spec`, `/release`, and pipeline commands
- Cross-referenced with Writ's own SWOT analysis (2026-03-01) for alignment with known gaps

## Key Findings

### Finding 1: Product Orientation — gstack's "10-Star Product" Framing Is Aspirational Where Writ Is Informational

gstack's `/plan-ceo-review` doesn't just gather requirements — it *challenges the premise of the request itself*. Three signature moves:

1. **Premise Challenge:** "Is this the right problem to solve? What would happen if we did nothing?"
2. **Dream State Mapping:** A visual `CURRENT STATE → THIS PLAN → 12-MONTH IDEAL` progression that forces long-horizon thinking
3. **Three Explicit Modes:** SCOPE EXPANSION ("build the cathedral"), HOLD SCOPE ("make it bulletproof"), SCOPE REDUCTION ("strip to essentials") — user picks one, and the AI commits fully to that posture

Writ's `/plan-product` has solid discovery (one question at a time, challenge assumptions, surface risks) but its default posture is *neutral*. It asks "who has this problem?" and "what's your biggest constraint?" — smart questions, but they start from the assumption that the user's framing is roughly correct. gstack starts by questioning whether the framing is *wrong*.

The "delight opportunities" concept is also notable: gstack asks "what adjacent 30-minute improvements would make this feature sing?" — small touches that create outsized user perception.

**Implications:** Writ's `/plan-product` and `/create-spec` could absorb the mode selection pattern and premise-challenging posture without losing their structured discovery flow. The three-mode system (Expansion / Hold / Reduction) is elegant and could map to Writ's existing commands.

### Finding 2: Engineering Review Depth — Error Mapping and Failure Registries

gstack's `/plan-eng-review` has several techniques that go beyond Writ's current review capabilities:

- **Error & Rescue Map:** A mandatory table mapping every new method → what can go wrong → specific exception class → whether it's rescued → what the user sees. "rescue StandardError is ALWAYS a smell" is a rule enforced at the review level.
- **Shadow Paths:** Every data flow must trace 4 paths: happy, nil input, empty input, upstream error. This is more rigorous than typical review.
- **Interaction Edge Cases Table:** Double-click, navigate-away-mid-action, stale state, back button — systematically enumerated for every new user interaction.
- **Failure Modes Registry:** A cross-cutting table that flags any codepath with RESCUED=N, TEST=N, USER SEES=Silent as a **CRITICAL GAP**.
- **Mandatory ASCII Diagrams:** Not optional, not "if helpful" — required for every non-trivial flow.

**Implications:** These patterns could enhance Writ's review agents and the `/create-spec` contract. The Error & Rescue Map format is particularly actionable — it could be a required section in technical sub-specs.

### Finding 3: The `/retro` Command Is Exactly What Writ Needs

Writ's SWOT analysis (2026-03-01) already identified `/retrospective` as a planned command. gstack's implementation is mature and well-designed:

- **Git-based metrics:** Commits, LOC, test LOC ratio, PR sizes, fix ratio, version range
- **Session detection:** Uses 45-minute gap threshold between commits. Classifies deep (50+ min), medium (20-50 min), and micro (<20 min) sessions.
- **Team awareness:** Identifies who's running the retro, gives them the deepest treatment, then per-person breakdowns for teammates with specific praise and growth opportunities.
- **Streak tracking:** Consecutive days with commits — motivational and reveals consistency patterns.
- **Persistent history:** JSON snapshots in `.context/retros/` with trend comparison.
- **Compare mode:** This-period vs prior-period side-by-side.
- **Ship of the Week:** Auto-identifies the highest-impact PR.
- **Tweetable summary:** One-line format for quick sharing.

Design decisions worth adopting:
- ALL narrative output goes to the conversation. The ONLY file written is the JSON snapshot.
- Pacific time normalization (this should be configurable for Writ).
- The praise/growth format: "anchored in actual commits, not generic — what would you actually say in a 1:1?"
- Focus score: % of commits touching the single most-changed directory.

Design decisions to adapt for Writ:
- gstack hardcodes Pacific time and `origin/main` — Writ should detect timezone and default branch.
- gstack's Greptile integration is specific to that toolchain — Writ could have a similar hook for whatever CI/review tools the project uses.
- Storage path should be `.writ/retros/` instead of `.context/retros/`.

### Finding 4: The `/ship` Command Fills a Gap Between Writ's Pipeline and Release

Writ's pipeline is `create-spec → implement-story → verify-spec → release`. The gap: after implementation and before release, there's no single command that handles the "last mile" — merge main, run tests, review the diff one more time, push the branch, open the PR. The user does this manually or pieces it together.

gstack's `/ship` is purpose-built for this:
- Fully automated, non-interactive by default
- Merges origin/main before tests (catches integration issues)
- Runs test suites in parallel
- Pre-landing review against a checklist
- Bisectable commit splitting (infrastructure → models → controllers → version bump)
- Auto-generates CHANGELOG from diff
- Pushes and opens PR with structured body

The philosophy is "user says `/ship`, next thing they see is the PR URL." Momentum over ceremony.

**Implications:** A `/ship` command would sit between `/implement-story` (code is written, tests pass) and `/release` (formal versioning/tagging). It handles the "boring but critical" release engineering that causes branches to rot.

### Finding 5: Browser-Based QA Is a Capability Gap

gstack's `/browse` and `/qa` give the AI "eyes" — it can navigate real web pages, fill forms, take screenshots, and check console errors. The diff-aware QA mode is particularly clever: analyze `git diff`, identify affected routes, auto-test them.

Writ has no browser automation capability. This is a significant gap for web application development, though it's also the most platform-dependent feature (requires a browser daemon, compiled binary, etc.).

**Implications:** This is worth noting but likely a longer-term investment for Writ. The Cursor browser MCP tools may partially fill this gap.

### Finding 6: Opinionated Posture vs. Neutral Posture

Throughout gstack's commands, there's a consistent design pattern: **lead with the recommendation, explain why, then offer alternatives.** Every AskUserQuestion must state "We recommend [LETTER]: [reason]" before listing options. The engineer preferences are stated upfront (DRY, explicit > clever, minimal diff) and every recommendation maps back to them.

Writ has "challenge ideas that don't make business or technical sense" and "disagree constructively" in its DNA, but it's more politely neutral in practice. gstack is aggressively opinionated: "Be opinionated. I'm paying for your judgment, not a menu."

**Implications:** This is a tone/philosophy adjustment rather than a feature. Writ could strengthen its opinionated posture in review phases.

## Options Analysis

### Option A: Focused Uplift (3 commands)

Enhance `/plan-product` with 10-star thinking + mode selection. Build `/retro`. Build `/ship`.

- **Pros:** High-impact, manageable scope, addresses known SWOT gaps
- **Cost/Effort:** Medium — 2-3 focused specs
- **Risk Level:** Low — all three are well-understood patterns with gstack as reference

### Option B: Comprehensive Adoption (5+ changes)

Option A plus: standalone `/review` command, enhanced error mapping in specs, browser QA integration.

- **Pros:** Most thorough improvement, closes multiple gaps
- **Cost/Effort:** High — 5+ specs, browser infra is complex
- **Risk Level:** Medium — browser automation adds platform-specific complexity

### Option C: Philosophy-First (tone + 1 command)

Strengthen opinionated posture across existing commands. Build `/retro` only.

- **Pros:** Least disruption, improves everything incrementally
- **Cost/Effort:** Low — mostly editing existing command files
- **Risk Level:** Low — but misses the bigger structural opportunities

## Recommendations

### Primary Recommendation

**Option A: Focused Uplift** — Enhance `/plan-product` with aspirational framing, build `/retro`, build `/ship`.

This targets the three highest-leverage gaps: product ambition, feedback loops, and shipping momentum. All three have proven implementations in gstack to reference, and all three align with Writ's existing SWOT priorities.

### Specific Recommendations

#### 1. Enhance `/plan-product` with "10-Star Product" Thinking

Add a mode selection step early in the discovery phase:

```
Before we dive into discovery, what posture should I take?

A) SCOPE EXPANSION — Dream big. Find the 10-star product hiding in this idea.
B) HOLD SCOPE — Your framing is right. Let me pressure-test it for gaps.
C) SCOPE REDUCTION — Strip to the absolute minimum that delivers value.
```

Add Premise Challenge (before discovery):
- "Is this the right problem to solve?"
- "What would happen if we did nothing?"
- "What's the version that's 10x more ambitious for 2x the effort?"

Add Dream State Mapping:
- `CURRENT STATE → THIS PLAN → 12-MONTH IDEAL`

Add Delight Opportunities (in EXPANSION mode):
- "What adjacent 30-minute improvements would make this feature sing?"

These additions layer onto the existing discovery conversation without replacing it.

#### 2. Build `/retro` Command

Adapt gstack's retro structure for Writ's ecosystem:

- Same git-based metrics approach (commits, LOC, test ratio, sessions, streaks)
- Store in `.writ/retros/` instead of `.context/retros/`
- Auto-detect timezone instead of hardcoding Pacific
- Auto-detect default branch instead of hardcoding `main`
- Keep team-aware analysis with specific, commit-anchored praise
- Add persistent JSON snapshots + compare mode
- Ship of the week + tweetable summary
- Integration with Writ's spec system: "Specs completed this period: [list]"

#### 3. Build `/ship` Command

Create a unified shipping workflow between implementation and formal release:

- Merge origin/default-branch before tests
- Run test suites (detect test runner from project)
- Pre-landing diff review (lightweight checklist, not full `/review` pipeline)
- Bisectable commit splitting
- Auto-generate PR body from commits/diff
- Push and open PR
- Non-interactive by default — momentum over ceremony
- Respect Writ's existing `/release` for formal versioning/tagging

#### 4. Strengthen Opinionated Posture (Cross-Cutting)

In review phases across all commands:
- Lead with recommendation, then explain, then offer alternatives
- Map every recommendation to stated engineering preferences
- "We recommend B: [reason]" format instead of neutral option listing

### Implementation Considerations

- All three recommendations can be parallel-tracked as independent specs
- `/retro` is the most self-contained — could ship first as a quick win
- `/plan-product` enhancement is mostly editing an existing file
- `/ship` requires the most new design work but has the clearest reference implementation

## Risks & Mitigation

- **Risk 1:** Over-adopting gstack's Claude Code-specific patterns (e.g., `AskUserQuestion` API) → **Mitigation:** Translate to Writ's `AskQuestion` tool and Plan Mode conventions
- **Risk 2:** `/ship` overlapping with `/release` → **Mitigation:** Clear boundary: `/ship` = branch → PR, `/release` = PR → tagged version. Different lifecycle stages.
- **Risk 3:** "10-star product" framing feeling performative without real substance → **Mitigation:** Keep it grounded — premise challenge + dream state mapping are concrete techniques, not just hype language

## Further Research Needed

- How gstack's Greptile integration could map to Writ's review pipeline (or other automated code review tools)
- Whether browser QA should be a Writ command or stay delegated to Cursor's MCP browser tools
- How gstack's eval infrastructure (LLM-as-judge, E2E test tiers) could inform Writ's own quality testing approach

## Sources

- [gstack repo](https://github.com/garrytan/gstack) — all SKILL.md files, ARCHITECTURE.md, CLAUDE.md, README.md
- Writ commands: `plan-product.md`, `create-spec.md`, `release.md`, `system-instructions.md`
- Writ SWOT analysis: `.writ/docs/swot-2026-03-01.md`

## Appendix: Command Mapping

| gstack Command | Writ Equivalent | Gap |
|---|---|---|
| `/plan-ceo-review` | `/plan-product` | Writ lacks mode selection, premise challenging, 10-star framing |
| `/plan-eng-review` | `/create-spec` (technical sub-specs) | Writ lacks error/rescue maps, mandatory failure registries |
| `/review` | Built into implement-spec pipeline | No standalone pre-landing review command |
| `/ship` | None (gap between `/implement-story` and `/release`) | **Full gap** — biggest opportunity |
| `/browse` | None | Browser automation not in Writ's scope yet |
| `/qa` | None | Diff-aware QA testing not available |
| `/setup-browser-cookies` | None | N/A — browser-specific |
| `/retro` | Planned but not built | **Full gap** — already identified in SWOT |

## Appendix: gstack Design Principles Worth Adopting

1. **Explicit cognitive modes** — Tell the AI what kind of thinking you need right now, not just what task to do.
2. **Lead with the recommendation** — Be opinionated. The user is paying for judgment, not a menu.
3. **Momentum over ceremony** — When execution is needed, execute. Don't ask for confirmation on things you can auto-decide.
4. **Diagrams are mandatory** — ASCII art forces hidden assumptions into the open. Required, not optional.
5. **Everything deferred must be written down** — "Vague intentions are lies. TODOS.md or it doesn't exist."
6. **Praise should be specific and earned** — "Anchored in actual commits, not generic."
