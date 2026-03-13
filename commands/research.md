# Research Command

## Overview

Conduct systematic research on a topic using structured phases that build upon each other, creating actionable todos and leveraging high-quality web search capabilities.

## When to Use

- Investigating new technologies, frameworks, or tools
- Understanding problem domains before solution design
- Competitive analysis and market research
- Technical feasibility studies
- Learning about best practices in unfamiliar areas

## Search Tooling

Choose the best available search tool. Exa produces higher-quality results with richer content extraction and should be preferred when available.

### With Exa (preferred)

If the **Exa skill** is listed in your available skills, read it first to learn the API. Use Exa as your primary search engine throughout the research.

Key capabilities to leverage:
- **`/search`** — Primary search. Use `type: "auto"` by default.
- **`/answer`** — Quick Q&A with citations. Ideal for getting oriented on a topic fast.
- **`/contents`** — Extract full text from known URLs. Use to deep-read important pages found during search.
- **Categories** — `github`, `paper`, `news`, `company`, `people`, `tweet` — focus results by type.
- **Domain filtering** — `includeDomains` / `excludeDomains` to target authoritative sources.
- **Date filtering** — `startPublishedDate` to limit to recent content.
- **Content options** — `text` for full content, `highlights` for key excerpts, `summary` for AI summaries.

### Without Exa (fallback)

Use the built-in `web_search` tool. It works for all phases but returns less structured content. When using `web_search`, compensate by:
- Running more queries with varied phrasing
- Using `fetch_url` to extract full content from promising results
- Being more aggressive about cross-referencing

## Process

### Phase 1: Define Research Scope

**Objective:** Establish clear research boundaries and questions

**Actions:**

1. Create todos for the research phases using `todo_write`
2. Define primary research question(s)
3. Identify key stakeholders and their information needs
4. Set success criteria for the research

**Todo Structure:**

```
- Phase 1: Define scope and questions [in_progress]
- Phase 2: Initial discovery [pending]
- Phase 3: Deep dive analysis [pending]
- Phase 4: Synthesis and recommendations [pending]
```

### Phase 2: Initial Discovery

**Objective:** Gather broad understanding of the topic landscape

**Actions:**

1. Run broad searches to map the topic landscape
2. Search for:
   - Overview articles and introductory content
   - Current trends and recent developments
   - Key players and thought leaders
   - Common terminology and concepts
3. Document initial findings and emerging themes
4. Identify knowledge gaps that need deeper investigation

**With Exa:**

- Start with `/answer` to get a cited overview: `"What is [topic] and what are the current best practices?"`
- Follow with `/search` using `type: "auto"` and broad queries
- Use `category: "news"` to find recent developments
- Request `highlights` (not full text) to scan many results quickly without burning tokens

**Without Exa:**

- Start with general terms: "[topic] overview", "[topic] [current year]", "[topic] trends"
- Look for authoritative sources: documentation, whitepapers, industry reports
- Note recurring themes and terminology for Phase 3

### Phase 3: Deep Dive Analysis

**Objective:** Investigate specific aspects identified in Phase 2

**Actions:**

1. Run targeted searches based on Phase 2 findings
2. Research specific sub-topics:
   - Technical implementation details
   - Pros and cons of different approaches
   - Real-world case studies and examples
   - Performance metrics and benchmarks
3. Compare alternatives and trade-offs
4. Validate claims from multiple sources

**With Exa:**

- Use `category: "paper"` for academic/technical depth, `"github"` for implementation examples
- Use `includeDomains` to target authoritative sources (e.g., `["arxiv.org", "docs.python.org"]`)
- Use `startPublishedDate` to filter for recent content on fast-moving topics
- Request `text` with `max_characters` for full content on the most relevant results
- Use `/contents` to deep-read specific URLs found in Phase 2

**Without Exa:**

- Use specific terminology discovered in Phase 2
- Search for: "[specific approach] vs [alternative]", "[topic] case study", "[topic] performance"
- Look for criticism and limitations, not just benefits

### Phase 4: Synthesis and Recommendations

**Objective:** Transform research into actionable insights and document findings

**Actions:**

1. Synthesize findings into key insights
2. Create recommendations based on research
3. Identify next steps or areas requiring further investigation
4. Document sources and evidence for claims
5. Determine current date using robust file system method (see Date Determination Process below)
6. Create research document in `.writ/research/` folder using the standardized format below
7. Present findings in appropriate format (ADR, proposal, summary document)

**Deliverables:**

- Executive summary of key findings
- Pros/cons analysis of options
- Specific recommendations with rationale
- Risk assessment and mitigation strategies
- Further research needs
- **Research document:** `.writ/research/[DATE]-[topic-name]-research.md` (get DATE using file system method below)

## Output Structure

### Research Summary

- **Research Question(s):** [What you set out to learn]
- **Key Findings:** [3-5 bullet points of most important discoveries]
- **Recommendations:** [Actionable next steps based on research]

### Detailed Findings

- **Background/Context:** [Setting the stage]
- **Current State:** [What exists today]
- **Options Analysis:** [Comparison of alternatives]
- **Evidence:** [Supporting data, quotes, sources]

### Next Steps

- **Immediate Actions:** [What to do next]
- **Further Research:** [What questions remain]
- **Decision Points:** [Key choices that need to be made]

## Date Determination

Get current date by running: `npx @devobsessed/writ date`

This returns the current date in `YYYY-MM-DD` format for folder naming:
`.writ/research/[DATE]-[topic-name]-research.md`

## Research Document Template

**First, determine the current date using the process above.**

Create a markdown file in `.writ/research/[DATE]-[topic-name]-research.md` where `[DATE]` is determined using the robust date process.

**Example:** `.writ/research/2024-01-15-blockchain-supply-chain-research.md`

Use the following structure:

```markdown
# [Topic Name] Research

**Date:** [Use date from file system determination process]
**Researcher:** [Name]
**Status:** [In Progress/Complete]

## Research Question(s)

[Primary questions this research aimed to answer]

## Executive Summary

[2-3 paragraph overview of key findings and recommendations]

## Background & Context

[Why this research was needed, current situation, stakeholders involved]

## Methodology

[How the research was conducted, sources used, timeframe]

## Key Findings

### Finding 1: [Title]

- **Evidence:** [Supporting data/sources]
- **Implications:** [What this means for the project/decision]

### Finding 2: [Title]

- **Evidence:** [Supporting data/sources]
- **Implications:** [What this means for the project/decision]

[Continue for each major finding...]

## Options Analysis

### Option 1: [Name]

- **Pros:** [Benefits and advantages]
- **Cons:** [Drawbacks and limitations]
- **Cost/Effort:** [Implementation requirements]
- **Risk Level:** [High/Medium/Low with explanation]

### Option 2: [Name]

- **Pros:** [Benefits and advantages]
- **Cons:** [Drawbacks and limitations]
- **Cost/Effort:** [Implementation requirements]
- **Risk Level:** [High/Medium/Low with explanation]

[Continue for each option...]

## Recommendations

### Primary Recommendation

[Specific recommended course of action with rationale]

### Alternative Approaches

[Secondary options if primary recommendation isn't feasible]

### Implementation Considerations

[Key factors to consider when moving forward]

## Risks & Mitigation

- **Risk 1:** [Description] → **Mitigation:** [How to address]
- **Risk 2:** [Description] → **Mitigation:** [How to address]

## Further Research Needed

- [Question/area that needs additional investigation]
- [Question/area that needs additional investigation]

## Sources

- [Source 1 with URL and access date]
- [Source 2 with URL and access date]
- [Continue listing all sources used...]

## Appendix

[Additional detailed information, raw data, extended quotes, etc.]
```

## Best Practices

### Search Strategy

- Start broad, then narrow down
- Use multiple search terms and phrasings
- Look for recent content (last 1-2 years) for rapidly evolving topics
- Cross-reference information from multiple sources
- Search for both benefits AND criticisms

**Exa-specific tips:**

- Use `type: "auto"` unless you have a reason not to — it has built-in fallback
- Use `highlights` for scanning, `text` for reading — don't request full text on exploratory queries
- Set `max_characters` on text content (10000–20000) to avoid token blowout
- Run parallel searches with different categories to cover more ground efficiently
- Use `/answer` for factual questions; use `/search` for open-ended exploration
- Combine `startPublishedDate` with `category: "news"` for current events

### Critical Thinking

- Question assumptions and biases in sources
- Look for evidence, not just opinions
- Consider the source's credibility and potential conflicts of interest
- Distinguish between correlation and causation
- Identify what information is missing

### Documentation

- Keep track of sources for all claims
- Note the date of information (especially for fast-moving topics)
- Document your search process for reproducibility
- Save important quotes with proper attribution

## Common Pitfalls to Avoid

- Confirmation bias (only seeking information that supports preconceived notions)
- Stopping research too early when findings seem obvious
- Not considering implementation challenges
- Ignoring edge cases or limitations
- Failing to consider stakeholder perspectives beyond your own

## Example Todo Progression

**Initial:**

```
- Research blockchain solutions for supply chain [in_progress]
- Analyze implementation approaches [pending]
- Evaluate vendor options [pending]
- Create research document in .writ/research/ [pending]
- Create recommendation report [pending]
```

**After Phase 2:**

```
- Research blockchain solutions for supply chain [completed]
- Analyze implementation approaches [in_progress]
- Evaluate vendor options [pending]
- Determine date using file system method [pending]
- Create research document in .writ/research/ [pending]
- Create recommendation report [pending]
```

**Final:**

```
- Research blockchain solutions for supply chain [completed]
- Analyze implementation approaches [completed]
- Evaluate vendor options [completed]
- Determine date using file system method [completed]
- Create research document in .writ/research/ [completed]
- Create recommendation report [completed]
```
