## Draft 1
Title: Flat Criteria Grid
Commitment: many items with little detail; everything visible — every story and every criterion sits on one screen as a short label and a glyph, so criterion wording is clipped and test details are left out
Structure:
  type StoryStatus = "NotStarted" | "InProgress" | "Completed" | "Blocked"
  type TestState = "pass" | "fail" | "none"            // none = no test linked yet
  type Criterion = { id: string; label: string; test: TestState }   // label clipped to 40 chars
  type Story = { n: number; title: string; status: StoryStatus; criteria: Criterion[] }  // 3..8 criteria
  type Spec = { name: string; updatedAt: string; stories: Story[] }                       // 3..8 stories
  type Remaining = { storiesOpen: number; criteriaOpen: number; blocked: number }
  function remaining(spec: Spec): Remaining   // criteriaOpen = criteria with test != "pass"
  function glyph(t: TestState): "●" | "✕" | "○"   // pass, fail, no test
  SpecGrid(spec: Spec)
    HeaderBar: spec.name · "updated " + updatedAt · RemainingCounts(remaining(spec))
    RemainingCounts: "5 stories open · 14 criteria not passing · 1 blocked"
    StoryTable: one row per story, all rows always rendered, no collapse, no pagination
      StoryRow(story: Story)
        StatusChip(status)        // 2-letter tag + color: NS grey, IP blue, OK green, BL red
        StoryTitle(n, title)      // single line, truncated with ellipsis
        PassRatio                 // "3/6"
        CriteriaStrip: up to 8 CriterionCell, fixed width so columns align across rows
          CriterionCell(c)        // glyph(c.test) above c.label at 11px, full label in title attribute
    Legend: ● passing test  ✕ failing test  ○ no test  — fixed to the bottom edge
  Row order: Blocked, InProgress, NotStarted, Completed; story number breaks ties
  Rows with every criterion passing render at reduced contrast so open work stands out
Trade-off: Criterion wording is clipped and failing-test output, test names, and story notes never appear, so diagnosing why a criterion fails still means opening the story or test run.

## Draft 2
Title: Open Ledger
Commitment: few items with full detail; everything visible — every story and every criterion is printed in full on one long page, so at eight stories the maintainer scrolls instead of scanning a summary
Structure:
  type StoryStatus = "Not Started" | "In Progress" | "Completed" | "Blocked"
  type TestResult = "passing" | "failing" | "no test"
  type Criterion = { id: string; text: string; result: TestResult; testName?: string; lastRun?: Date }
  type Story = { number: number; title: string; status: StoryStatus; blockedBy?: string; criteria: Criterion[] }
  type Spec = { name: string; folder: string; stories: Story[]; refreshedAt: Date }
  function remaining(spec: Spec): Criterion[]  // every criterion whose result is not "passing"
  SpecProgressPage(spec: Spec)
    Header
      SpecName (spec.name, spec.folder)
      Tally: "{passing} of {total} criteria pass · {completed} of {stories} stories done · refreshed {refreshedAt}"
      RemainingLine: one sentence per non-Completed story, e.g. "Story 3: 2 criteria failing, 1 untested"
    StoryList (all stories in number order, none collapsible, no filters)
      StoryCard(story) for each story
        CardHeader: "Story {number} — {title}" + StatusBadge(status)
        BlockedNote: shown only when status is "Blocked", prints blockedBy in full
        CriteriaTable (every criterion, always rendered)
          Row: ResultMark(result) | criterion text in full | testName or "no test" | lastRun
        CardFooter: "{passing}/{criteria.length} passing"
    StatusBadge(status): text label plus color; Blocked red, In Progress amber, Completed green, Not Started gray
    ResultMark(result): "pass" green check, "fail" red cross, "none" gray dash; label text always shown beside the icon
Trade-off: No collapsing, filtering, or sorting by what is left, so finished stories take the same space as open ones and the page can run to 64 criterion rows.

## Draft 3
Title: Story Strip Board
Commitment: many items with little detail; details behind a click — the text of a failing criterion and its test name are one click away, so the board alone shows how much is left per story, not exactly what it is
Structure:
  type Status = "NotStarted" | "InProgress" | "Completed" | "Blocked"
  type Criterion = { id: string; text: string; testName: string | null; passing: boolean }
  type Story = { id: string; title: string; status: Status; blockedBy: string | null; criteria: Criterion[] }
  type Spec = { name: string; updatedAt: string; stories: Story[] }
  remaining(spec: Spec): { stories: number; criteria: number; blocked: number }
  passCount(story: Story): { passing: number; total: number }
  SpecProgressPage(spec: Spec)
    RemainingBar(remaining(spec))  // "3 stories open · 11 criteria failing · 1 blocked" plus last-updated time
    StoryStrip[]  // one row per story, all 3-8 visible without scrolling, ordered Blocked, InProgress, NotStarted, Completed
      StatusChip(status)  // color plus label text, so status reads without color
      Title(title)  // truncated to one line
      CriteriaDots(criteria)  // one filled dot per passing criterion, hollow per failing, in criterion order
      PassFraction(passCount)  // "4/6"
      BlockedNote(blockedBy)  // short reason, shown only when status is Blocked
      onClick -> toggle StoryDetail inline below the row; several rows may be open at once
    StoryDetail(story)
      CriterionRow[]  // failing rows first: pass/fail mark, criterion text, test name or "no test yet"
  Completed rows collapse to a single muted line; open/closed state of each row persists across reloads
  Page refreshes data on focus, so a return visit shows current state without a manual reload
Trade-off: Gives up seeing which specific criteria fail across the whole spec at once; the board shows counts and dots, and the criterion text needs a click per story.
