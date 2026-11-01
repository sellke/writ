## Draft 1
Title: Single-pass evidence record with explicit source outcomes
Commitment: one call; an unreachable or empty source comes back as a value in the record — the caller always gets a full record and must check each source's outcome itself, because nothing raises when a search fails
Structure:
  Tier = enum { Recorded, Stated, Corroborated, Inferred, Unknown }
  SourceRef = one of
      FileRef   { path: str, section: str }
      CommitRef { sha: str }
      McpRef    { server: str, item_id: str }
  Claim = { tier: Tier, text: str, source: SourceRef | None }   # source is None only when tier is Unknown
  SourceKind = enum { Ledger, Git, Mcp }
  SourceOutcome = enum { Found, Empty, Unreachable }
  SourceSearched = { kind: SourceKind, name: str, outcome: SourceOutcome,
                     detail: str, claim_count: int }   # detail: what was searched, or why it failed
  GuidanceItem = { text: str, tier: Tier, source: SourceRef | None }
  ChangeGuidance = { preserve: list[GuidanceItem], change: list[GuidanceItem],
                     avoid: list[GuidanceItem], risk: list[GuidanceItem] }
  EvidenceRecord = {
      question: str,
      asked_at: datetime,
      claims: list[Claim],                     # strongest tier first
      sources_searched: list[SourceSearched],  # always ledger, then git, then one entry per MCP server
      change_guidance: ChangeGuidance | None,  # None when no change is proposed
  }
  why(question: str, proposed_change: str | None = None) -> EvidenceRecord   # never raises on a source failure
  save_record(record: EvidenceRecord, path: str) -> None      # markdown with a JSON front-matter block
  read_saved_record(path: str) -> EvidenceRecord              # raises only if the file is missing or malformed
Trade-off: A failed or empty source looks like any other entry, so a reader who skips sources_searched can mistake missing evidence for a confident answer.

## Draft 2
Title: Inquiry handle with three narrow reads
Commitment: several small calls (claims, sources, guidance); an unreachable or empty source comes back as a value — three calls share one inquiry id, so a caller that skips one gets an incomplete picture and every call pays the lookup cost again
Structure:
  Tier = "Recorded" | "Stated" | "Corroborated" | "Inferred" | "Unknown"
  SourceKind = "ledger" | "git" | "mcp"
  Cite = LedgerCite(path: str, section: str)
       | CommitCite(sha: str)
       | McpCite(server: str, item_id: str)
       | NothingFound(kind: SourceKind, name: str)   # backs an Unknown claim: the search that came up empty
  Claim = { tier: Tier, text: str, source: Cite }
  SourceStatus = Found(hits: int) | Empty | Unreachable(reason: str)
  SourceResult = { order: int, kind: SourceKind, name: str, status: SourceStatus }
      # name: ".writ/ ledger", "git log", or the MCP server name; order runs ledger -> git -> each MCP server
  Advice = { text: str, tier: Tier, source: Cite }
  ChangeGuidance = { preserve: list[Advice], change: list[Advice], avoid: list[Advice], risk: list[Advice] }
  WhyRecord = { question: str, asked_at: date, claims: list[Claim],
                sources_searched: list[SourceResult], change_guidance: ChangeGuidance | None }

  open_inquiry(question: str) -> InquiryId                     # resolves terms, fixes the source order
  read_claims(id: InquiryId) -> list[Claim]                     # never raises; gaps become Unknown claims
  read_sources(id: InquiryId) -> list[SourceResult]             # every source tried, Empty and Unreachable included
  read_guidance(id: InquiryId, change: str | None) -> ChangeGuidance | None   # None when no change is proposed
  why(question: str, change: str | None = None) -> WhyRecord    # opens, calls all three, packs the results unchanged
  save_record(record: WhyRecord, path: str) -> None             # writes .writ/why/<slug>.md with a typed front block
  read_saved_record(path: str) -> WhyRecord                     # same shape back; stale sources keep their saved status
Trade-off: no single atomic answer; the three reads can drift if the ledger or git changes between calls, and why() hides that only by calling them back to back.

## Draft 3
Title: All-or-nothing evidence record
Commitment: one call; an unreachable source raises and unwinds — a single down MCP server yields no record at all, even when the ledger and git already answered
Structure:
    Tier = Enum("Recorded", "Stated", "Corroborated", "Inferred", "Unknown")
    SourceKind = Enum("ledger", "git", "mcp")
    Source = { kind: SourceKind, ref: str, locator: str }
        # ledger: ref = file path, locator = section heading
        # git: ref = commit SHA, locator = "" ; mcp: ref = server name, locator = item id
    Claim = { tier: Tier, text: str, source: Source }
    SearchStep = { kind: SourceKind, name: str, queried: list[str], hits: int }
        # hits = 0 is kept; an empty source still appears in its slot
    GuidanceItem = { text: str, tier: Tier, source: Source }
    ChangeGuidance = { preserve: list[GuidanceItem], change: list[GuidanceItem],
                       avoid: list[GuidanceItem], risk: list[GuidanceItem] }
    WhyRecord = { question: str, asked_at: datetime, claims: list[Claim],
                  sources_searched: list[SearchStep],   # fixed order: ledger, git, then each MCP server
                  change_guidance: ChangeGuidance | None, saved_to: path | None }
    SourceUnreachable(Exception) = { kind: SourceKind, name: str, reason: str }
    why(question: str, intended_change: str | None = None, save: bool = True) -> WhyRecord
        # searches every source in order; the first unreachable source raises SourceUnreachable
        # and discards everything gathered so far; nothing is written to disk
        # change_guidance is filled only when intended_change is given
        # a claim with no source found is emitted as tier Unknown with the searched steps as its source list
    read_saved_record(path: path) -> WhyRecord
        # raises RecordInvalid if any claim or guidance item lacks a tier or source,
        # or if sources_searched is not in ledger, git, MCP order
    RecordInvalid(Exception) = { path: path, field: str, reason: str }
Trade-off: the developer gets no partial answer when any one source is down, so a flaky MCP server blocks the whole explanation and the /create-spec step behind it.
