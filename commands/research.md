# Research Command

## Overview

Conduct systematic research through four progressive phases — scoping, discovery, deep dive, synthesis — producing an actionable research document with evidence-backed recommendations.

**When to use:** Before solution design when you need to understand a problem domain, evaluate technologies or approaches, or build evidence for architectural decisions. Not for quick lookups — for structured investigation where getting it wrong has real cost.

## Invocation

| Invocation | Behavior |
|---|---|
| `/research` | Interactive — ask for topic and scope |
| `/research "topic"` | Start research with topic pre-loaded |

## Search Tooling

Exa produces higher-quality results with richer content extraction. If the **Exa skill** is listed in available skills, read it first and use Exa as your primary search engine.

| Tool | When | Key Advantage |
|---|---|---|
| **Exa** (preferred) | Available in skills | Structured content extraction, categories, domain filtering |
| **`web_search`** (fallback) | Exa unavailable | Compensate with more queries, varied phrasing, and `fetch_url` for full content |

**Exa capabilities at a glance:**

| Endpoint / Feature | Purpose |
|---|---|
| `/search` (type: `"auto"`) | Primary search — auto-selects best mode |
| `/answer` | Quick cited Q&A — ideal for orientation |
| `/contents` | Extract full text from known URLs |
| Categories: `github`, `paper`, `news`, `company`, `tweet` | Focus results by type |
| `includeDomains` / `excludeDomains` | Target or exclude specific domains (e.g., `["arxiv.org", "docs.python.org"]`) |
| `startPublishedDate` | Filter for recent content on fast-moving topics |
| `highlights` vs `text` | Scanning (cheap) vs reading (rich) — choose intentionally |
| `summary` | AI-generated page summary — useful for quick triage |

## Command Process

### Phase 1: Define Research Scope

Establish clear boundaries before searching anything. This phase prevents the most common research failure: going broad and shallow instead of targeted and deep.

1. Define primary research questions — specific enough to know when they're answered
2. Identify who needs this research and what decisions it informs
3. Set success criteria: what would a "useful" result look like?
4. Calibrate depth (see Research Depth below)
5. Create todos for the four phases

Good research questions are falsifiable. "Is React good?" is vague. "Does React's concurrent mode improve perceived performance for data-heavy dashboards?" is researchable.

### Phase 2: Initial Discovery

Map the topic landscape broadly. The goal is orientation, not depth — identify themes, key players, terminology, and knowledge gaps that Phase 3 will address.

**With Exa:**

- Start with `/answer`: `"What is [topic] and what are the current best practices?"`
- Follow with `/search` using broad queries and `type: "auto"`
- Use `category: "news"` for recent developments
- Request `highlights` (not full text) to scan many results without burning tokens

**Without Exa:**

- Search general terms: "[topic] overview", "[topic] [current year]", "[topic] trends"
- Prioritize authoritative sources: documentation, whitepapers, industry reports
- Note recurring themes and terminology for Phase 3

End Phase 2 by listing specific questions for Phase 3. This sharpening step is what makes the deep dive productive rather than wandering.

### Phase 3: Deep Dive Analysis

Investigate specific sub-topics surfaced in Phase 2 — implementation details, trade-offs, case studies, benchmarks. Compare alternatives and validate claims across multiple sources.

**With Exa:**

- `category: "paper"` for technical depth, `"github"` for implementation examples
- `includeDomains` to target authoritative sources (e.g., `["arxiv.org", "docs.python.org"]`)
- `startPublishedDate` to filter for recent content on fast-moving topics
- `text` with `max_characters` (10000–20000) for full content on the most relevant results
- `/contents` to deep-read specific URLs found in Phase 2

**Without Exa:**

- Use specific terminology discovered in Phase 2
- Search for: "[approach] vs [alternative]", "[topic] case study", "[topic] performance"
- Actively seek criticism and limitations, not just benefits

Cross-reference key claims across sources. A finding supported by one blog post is an anecdote; supported by three independent sources, it's evidence.

### Phase 4: Synthesis and Recommendations

Transform raw findings into an actionable research document. Synthesis means connecting findings to the original questions and forming a position — not restating what each source said.

1. Distill findings into key insights that directly answer Phase 1's research questions
2. Build options analysis with honest pros/cons and effort/risk assessment
3. Form recommendations with clear rationale — explain *why*, not just *what*
4. Identify remaining unknowns and flag where further research is needed
5. Determine current date and create the output document (see Output below)

## Research Depth

Calibrate effort to the decision's stakes and reversibility. Not all research needs all four phases at full depth.

| Signal | Depth |
|---|---|
| High-stakes, irreversible (architecture, vendor lock-in) | Full 4-phase, multiple sources per claim |
| Moderate with alternatives (library choice, pattern selection) | Standard 4-phase, focused deep dive |
| Low-stakes or easily reversible (convention, minor tool choice) | Abbreviated — Phase 1 + lightweight Phase 2, skip deep dive if answer is clear |
| Exploratory / learning-oriented | Emphasis on Phase 2 breadth, Phase 3 on most promising directions |

Over-researching a trivial decision wastes tokens and time. Under-researching a critical one creates expensive mistakes.

## Output

**Date:** Run `npx @devobsessed/writ date` — returns `YYYY-MM-DD`.

**File path:** `.writ/research/[DATE]-[topic-name]-research.md`

### Research Document Quality Bar

These are quality principles, not a template. Structure the document naturally — every section must meet its bar.

| Section | Quality Bar |
|---|---|
| **Research Questions** | Specific, scoped questions this research answers — not vague topic labels |
| **Executive Summary** | 2-3 paragraphs a busy stakeholder can read and act on. Lead with findings and recommendation, not background |
| **Key Findings** | Each finding backed by evidence (sources, data, quotes) with implications for the decision at hand |
| **Options Analysis** | Each option: pros, cons, effort/cost, risk level. Honest — don't sandbag the option you didn't pick |
| **Recommendations** | Primary recommendation with rationale. Alternatives if primary isn't feasible. Implementation considerations |
| **Risks & Mitigation** | Specific risks with concrete mitigations — not generic "things could go wrong" |
| **Further Research** | Honest about what questions remain unanswered and why they matter |
| **Sources** | Every claim traceable to a source with URL. No orphaned assertions |

## Exa Tips

Non-obvious tips that meaningfully improve research quality:

- **`type: "auto"` is the safe default** — built-in fallback between neural and keyword search
- **`highlights` for scanning, `text` for reading** — don't request full text on exploratory queries; this is the #1 token-saving lever
- **Set `max_characters` on text content** (10000–20000) to avoid token blowout on long pages
- **Run parallel searches with different categories** to cover more ground in fewer round trips
- **`/answer` for factual questions, `/search` for open-ended exploration** — different engines, different strengths
- **Combine `startPublishedDate` with `category: "news"`** for current events research
- **`excludeDomains` is underused** — filter out content farms and SEO-bait sites to improve signal

---

## Integration with Writ

| Command | Relationship |
|---|---|
| `/create-spec` | Research informs spec creation — run research first when domain is unfamiliar |
| `/create-adr` | Research feeds directly into Architecture Decision Records |
| `/design` | Research provides evidence base for design decisions |
| `/edit-spec` | Research may reveal need for spec changes — use findings to justify edits |
| `/implement-spec` | Reference research documents for implementation context |

## Completion

This command succeeds when:

1. **Research document created** — a `.md` file exists in `.writ/research/` following the `YYYY-MM-DD-{topic}-research.md` naming convention
2. **Research questions answered** — the document contains specific findings backed by evidence with source URLs
3. **Recommendations formed** — the document includes a primary recommendation with rationale and alternatives analysis
4. **Summary presented** — the user received a completion summary with key findings and suggested next steps

**Suggested next step:** `/create-spec` to spec a feature informed by the research, or `/create-adr` to formalize an architectural decision from the findings.

**Terminal constraint:** This command produces research documentation (`.writ/research/`). Do not offer to implement, build, or execute what was researched. For specification, the user should run `/create-spec` or `/create-adr`. For quick prototyping, use `/prototype`.
