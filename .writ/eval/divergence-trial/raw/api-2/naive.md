## Draft 1
Title: Typed record with inline citations
Structure:
    type Tier = "Recorded" | "Stated" | "Corroborated" | "Inferred" | "Unknown"
    type SourceKind = "ledger" | "git" | "mcp"
    type Citation =
      | { kind: "ledger"; path: string; section: string }
      | { kind: "git"; sha: string }
      | { kind: "mcp"; server: string; itemId: string }
    type Claim = { text: string; tier: Tier; cite: Citation | null }   // cite is null only when tier is Unknown
    type SearchStep = { order: number; kind: SourceKind; target: string; hits: number }   // hits may be 0
    type ChangeGuidance = {
      preserve: Claim[]
      change: Claim[]
      avoid: Claim[]
      risk: Claim[]
    }
    type WhyRecord = {
      question: string
      askedAt: string             // ISO date
      answer: string              // short summary for the developer
      claims: Claim[]
      searched: SearchStep[]      // all ledger steps, then git, then mcp
      guidance?: ChangeGuidance   // present only when a change follows
    }
    function buildWhyRecord(question: string, change?: string): WhyRecord
    function renderWhyRecord(record: WhyRecord): string    // markdown shown to the developer
    function loadWhyRecord(path: string): WhyRecord        // called by /create-spec before planning
Trade-off: the saved file must round-trip through render and load, so a hand edit to the markdown can break /create-spec's read.

## Draft 2
Title: Markdown file with fixed headings and tag grammar
Structure:
    why-record.md, saved to .writ/why/<date>-<slug>.md
      frontmatter:
        question: <one line>
        date: <YYYY-MM-DD>
        change: <one line, or "none">
      ## Answer
        one paragraph; every sentence ends with a tag
      ## Claims
        - <claim text> [Recorded: .writ/decision-records/adr-003.md#Decision]
        - <claim text> [Corroborated: a1b2c3d, .writ/specs/x/spec.md#Scope]
        - <claim text> [Stated: linear:ENG-142]
        - <claim text> [Unknown: no source]
      ## Sources Searched
        1. ledger: .writ/decision-records/ (2 hits)
        2. ledger: .writ/specs/ (0 hits)
        3. git: log search for "<term>" (1 hit)
        4. mcp: linear (0 hits)
      ## Change Guidance   (omitted when change is "none")
        ### Preserve, ### Change, ### Avoid, ### Risk
          - <item> [Tier: source]
    Tag grammar: [Tier: source, source...]
      Tier is one of Recorded, Stated, Corroborated, Inferred, Unknown
      source is path#section, a 7+ character hex SHA, server:item, or "no source" (Unknown only)
Trade-off: easy for a developer to read and diff, but /create-spec must parse tags by pattern, and loose formatting can slip past it.

## Draft 3
Title: JSON claim graph with ID references
Structure:
    WhyRecord (JSON, saved to .writ/why/<slug>.json)
      question: string
      sources: Source[]          in search order: ledger, then git, then mcp
      claims: Claim[]
      guidance: Guidance | null  null when no change follows
    Source
      id: "S1", "S2", ...
      layer: "ledger" | "git" | "mcp"
      locator: string            path#section, commit SHA, or server/item id
      claimIds: string[]         empty when the source held nothing
    Claim
      id: "C1", "C2", ...
      text: string
      tier: "Recorded" | "Stated" | "Corroborated" | "Inferred" | "Unknown"
      sourceIds: string[]        two or more for Corroborated; empty for Unknown
    Guidance
      preserve: GuidanceItem[]
      change: GuidanceItem[]
      avoid: GuidanceItem[]
      risk: GuidanceItem[]
    GuidanceItem
      text: string
      claimIds: string[]         the claims this item rests on
      tier: the weakest tier among the cited claims, computed, not authored
Trade-off: the developer needs a renderer to read it, since raw JSON with ID lookups is hard to follow by eye.
