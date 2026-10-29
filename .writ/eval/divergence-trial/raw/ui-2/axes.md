## Draft 1
Title: Decision-first single page
Commitment: one scrolling page; everything visible — the page gets long with three drafts, and wide renders shrink to fit their columns
Structure:
  type DraftKind = "page" | "code"
  type Draft = { id: string; label: string; kind: DraftKind; body: string; commitments: string[]; lostBecause?: string }
  type ExplorationRecord = { title: string; date: string; question: string; chosenId: string; chosenWhy: string; drafts: Draft[] }
  RecordPage(record: ExplorationRecord)
    DecisionBanner            // top of page, first thing read
      Question                // the question the exploration answered
      ChosenLine              // "Chose <label>: <chosenWhy>"
      LossList                // one row per non-chosen draft: "<label> lost: <lostBecause>"
    CommitmentGrid            // one column per draft, rows aligned so the same row compares across drafts
      ColumnHeader(draft)     // label, plus a "chosen" badge on the winner and a "lost" badge on the others
      CommitmentRow[]         // draft.commitments, one per line; rows padded so columns stay level
      LossNote(draft)         // lostBecause repeated under the column; empty for the winner
    DraftBodies               // side-by-side columns, same order as CommitmentGrid
      PageRender(body)        // kind "page": scaled iframe, fixed height, no internal scroll
      CodeSketch(body)        // kind "code": full sketch, monospace, wraps instead of scrolling sideways
    RecordFooter              // date, and the branch or commit the chosen draft shipped on
  layout(width: number): "columns" | "stacked"   // below 720px columns stack in draft order, winner first
  rule: no tabs, toggles, or collapsed sections; every draft, commitment, and reason renders on load
Trade-off: Gives up focus on any one draft; full renders and long code sketches push the bodies far down the page, so detailed comparison of bodies needs scrolling past the summary.

## Draft 2
Title: Verdict Rail with Two Open Views
Commitment: tabs or a sidebar between views; everything visible — the rail costs a column of width, and nothing collapses, so long code sketches make the page scroll instead of folding away
Structure:
  type DraftKind = "page" | "code"
  type Draft = { id: string; label: string; kind: DraftKind; artifact: string; commitments: string[]; chosen: boolean; lostBecause?: string }
  type ExplorationRecord = { title: string; date: string; question: string; drafts: Draft[]; chosenId: string; choiceReason: string }
  type ViewId = "compare" | "reasons"
  RecordViewer(record: ExplorationRecord, view: ViewId)
    VerdictRail (left, fixed, always on screen)
      RecordHeader: title, date, the question the prototype set out to answer
      ChosenLine: "Chose <label>: <choiceReason>"
      LossList: one row per non-chosen draft -> "<label> lost: <lostBecause>"
      ViewSwitch: two rail entries, "Compare" and "Reasons"; the active one is underlined
    MainPane (right)
      CompareView (view = "compare")
        DraftColumns: one column per draft, equal width, 2 or 3 across
          DraftColumn(draft: Draft)
            ColumnHeader: label, kind badge, "Chosen" badge or "Lost" badge
            ArtifactFrame: rendered page at fixed scale, or code sketch in full with line numbers
            CommitmentList: every commitment as a bullet, never truncated
            LossNote: lostBecause printed under the list when chosen = false
      ReasonsView (view = "reasons")
        ReasonTable: rows = commitments merged across drafts, columns = drafts, cells = kept / dropped / not addressed
        ChoiceParagraph: choiceReason in full, with the losing drafts' lostBecause lines beneath
  Rule: no accordions, tooltips, or hover-only text; every field in Draft renders in at least one view and the rail renders in both
Trade-off: the per-commitment table sits behind a second view, so seeing which commitment decided the choice takes one click away from the side-by-side drafts

## Draft 3
Title: Verdict-First Strip
Commitment: one scrolling page; details behind a click — the drafts show as thumbnails only, so comparing their full content takes an extra click per draft
Structure:
  type DraftKind = "page" | "code"
  type Draft = { id: string; label: string; kind: DraftKind; preview: string; body: string; commitments: string[] }
  type Outcome = { draftId: string; chosen: boolean; reason: string }   // reason: one line, required for every losing draft
  type Record = { title: string; date: string; question: string; drafts: Draft[]; outcomes: Outcome[]; choiceSummary: string }
  RecordPage(record: Record)                       // one vertical page, no tabs or routes
    Header                                         // title, date, the question the prototype set out to answer
    VerdictBanner(chosen: Draft, summary: string)  // "Chose B: <choiceSummary>", pinned at the top of the scroll
    DraftRow(drafts: Draft[], outcomes: Outcome[]) // 2 or 3 equal-width columns, side by side
      DraftCard(draft: Draft, outcome: Outcome)
        CardHead                                   // label, kind badge, "Chosen" or "Lost" tag
        Preview(draft.preview)                     // fixed-height thumbnail or first 8 lines of code
        CommitmentList(draft.commitments, max=3)   // first three commitments; "+N more" if longer
        LossReason(outcome.reason)                 // shown only when chosen=false, one line, never truncated
        ExpandButton -> opens DraftDetail inline below the row
    DraftDetail(draft: Draft)                      // collapsed by default; one open at a time
      FullBody(draft.body)                         // full rendered page in an iframe, or full code with line numbers
      AllCommitments(draft.commitments)
      CloseButton
    CommitmentMatrix(drafts: Draft[])              // collapsed section: rows = commitments, columns = drafts, marks where each applies
  Rules: verdict and loss reasons are always visible without clicking; full bodies and the matrix are always behind a click
Trade-off: a side-by-side look at full draft content needs one draft opened at a time, so close detail comparison means toggling between drafts
