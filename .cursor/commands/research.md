# Research Command

## Overview

Conduct systematic research on a topic using structured phases that build upon each other, creating actionable todos and leveraging web search capabilities.

## When to Use

- Investigating new technologies, frameworks, or tools
- Understanding problem domains before solution design
- Competitive analysis and market research
- Technical feasibility studies
- Learning about best practices in unfamiliar areas

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

1. Use `web_search` with broad search terms related to your topic
2. Search for:
   - Overview articles and introductory content
   - Current trends and recent developments
   - Key players and thought leaders
   - Common terminology and concepts
3. Document initial findings and emerging themes
4. Identify knowledge gaps that need deeper investigation

**Search Strategy:**

- Start with general terms: "[topic] overview", "[topic] 2024", "[topic] trends"
- Look for authoritative sources: documentation, whitepapers, industry reports
- Note recurring themes and terminology for Phase 3

### Phase 3: Deep Dive Analysis

**Objective:** Investigate specific aspects identified in Phase 2

**Actions:**

1. Use `web_search` with specific, targeted queries based on Phase 2 findings
2. Research specific sub-topics:
   - Technical implementation details
   - Pros and cons of different approaches
   - Real-world case studies and examples
   - Performance metrics and benchmarks
3. Compare alternatives and trade-offs
4. Validate claims from multiple sources

**Search Strategy:**

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
