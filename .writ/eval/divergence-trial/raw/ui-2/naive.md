## Draft 1
Title: Verdict banner over equal columns
Structure:
  type DraftBody = { kind: "page"; html: string } | { kind: "code"; lang: string; source: string }
  type Draft = { id: string; label: string; body: DraftBody; commitsTo: string[] }
  type Outcome = { chosenId: string; whyChosen: string; lostBecause: Record<string, string> }
  type ExplorationRecord = { title: string; date: string; drafts: Draft[]; outcome: Outcome }

  ExplorationViewer(record: ExplorationRecord)
    VerdictBanner
      shows: "Chose <chosen.label>: <outcome.whyChosen>"
      shows: one line per loser: "<label> lost: <lostBecause[id]>"
    DraftColumns            // CSS grid, one column per draft (2 or 3), equal width
      DraftColumn(draft: Draft, isChosen: boolean, lostReason?: string)
        ColumnHeader        // label + "CHOSEN" badge or muted "lost" tag
        CommitList          // draft.commitsTo as bullets, top of column
        DraftPreview        // iframe sandbox for page; highlighted <pre> for code
                            // fixed height, scrolls inside the column
        LostReason          // lostReason repeated at column foot, absent when chosen
    RecordFooter            // title, date, link to source branch

  renderPreview(body: DraftBody): Element
Trade-off: Three full previews side by side get cramped below about 1200px, so rendered pages are shown scaled down rather than at real size.

## Draft 2
Title: Decision card with draft tabs
Structure:
  type Sketch = { format: "rendered-page"; url: string } | { format: "code"; language: string; text: string }
  type Commitment = { text: string }
  type Candidate = { name: string; sketch: Sketch; commitments: Commitment[]; rejection: string | null }
  type Record = { slug: string; question: string; candidates: Candidate[]; decidedAt: string }
  // invariant: exactly one candidate has rejection === null; that is the chosen one

  chosen(r: Record): Candidate
  losers(r: Record): Candidate[]

  RecordPage(r: Record)
    QuestionHeader          // r.question, e.g. "How should the settings form save?"
    DecisionCard
      ChosenLine            // "Went with <chosen.name>"
      RejectionList         // "<loser.name>: <loser.rejection>" one row each
    CandidateTabs           // tabs default to the chosen candidate
      TabLabel(c: Candidate)          // name + check mark or strike
      CandidatePane(c: Candidate)
        CommitmentChips     // c.commitments as short chips
        SketchFrame         // full-width render or code block
    CompareToggle           // splits CandidatePane into two panes, pick any two
Trade-off: Drafts are seen one at a time by default; true side-by-side needs a click on the compare toggle and caps at two.

## Draft 3
Title: Commitment matrix with thumbnails
Structure:
  type Artifact = { type: "page"; screenshot: string; liveHtml: string } | { type: "code"; snippet: string }
  type Option = { key: "A" | "B" | "C"; name: string; artifact: Artifact; commitments: string[] }
  type Verdict = { winner: "A" | "B" | "C"; losses: { key: "A" | "B" | "C"; oneLine: string }[] }
  type Exploration = { id: string; summary: string; options: Option[]; verdict: Verdict }

  axes(e: Exploration): string[]   // union of all commitments, deduped, in first-seen order

  ExplorationMatrix(e: Exploration)
    SummaryRow              // e.summary + "Winner: <key> <name>"
    Table
      HeaderRow             // one column per option; winner column outlined
        OptionHeader(o: Option)       // key, name, thumbnail of artifact
      AxisRow(axis: string) for each axes(e)
        Cell(o: Option, axis: string) // filled dot if o.commitments includes axis, blank if not
      LossRow               // per column: losses[key].oneLine, or "chosen" for winner
    ArtifactDrawer(o: Option)         // opens on header click
      full screenshot or live page, or the code snippet at full size
Trade-off: The matrix only works when commitments are worded consistently across drafts, and the drafts themselves shrink to thumbnails until opened.
