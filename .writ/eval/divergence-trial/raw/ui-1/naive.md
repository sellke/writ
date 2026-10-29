## Draft 1
Title: Story cards with a remaining-work header
Structure:
  type StoryStatus = "Not Started" | "In Progress" | "Completed" | "Blocked"
  type Criterion = { id: string; text: string; testPassing: boolean }
  type Story = { id: string; title: string; status: StoryStatus; criteria: Criterion[] }
  type Spec = { id: string; title: string; stories: Story[] }
  SpecProgressPage(spec: Spec)
    RemainingHeader(spec)
      shows: "N of M stories completed", "K of T criteria passing"
      shows: count per status, Blocked count in red when above zero
    StoryCardList(spec.stories)            sorted Blocked, In Progress, Not Started, Completed
      StoryCard(story)
        CardTitle: story.id + story.title
        StatusBadge(story.status)          color per status
        CriteriaCount: "passing / total"
        CriteriaList(story.criteria)       expanded unless story is Completed with all passing
          CriterionRow(criterion)          check mark or empty box, then criterion.text
        Mismatch flag: shown when status is Completed but a criterion is failing
  function remaining(spec: Spec): { stories: Story[]; failingCriteria: Criterion[] }
    returns stories not Completed and every criterion with testPassing false
  RemainingHeader reads its counts from remaining(spec)
Trade-off: Each story takes vertical space, so an eight-story spec needs scrolling to see every criterion.

## Draft 2
Title: Story-by-criterion grid
Structure:
  type StoryStatus = "Not Started" | "In Progress" | "Completed" | "Blocked"
  type Criterion = { index: number; text: string; testPassing: boolean }
  type Story = { id: string; title: string; status: StoryStatus; criteria: Criterion[] }
  type Spec = { title: string; stories: Story[] }
  SpecGridPage(spec: Spec)
    PageTitle: spec.title
    SummaryLine: "Stories done X/Y . Criteria passing P/T . Blocked B"
    Grid
      header row: Story | Status | AC1 | AC2 | ... | AC8 | Passing
      one row per story, in spec order
        cell Story: story.id + story.title
        cell Status: StatusChip(story.status)
        cells AC1..AC8: green filled square if passing, empty outlined square if not,
          blank cell when the story has fewer criteria than the column
        cell Passing: "p/n" for that story
    CriterionTooltip(criterion): shows criterion.text on hover or focus of an AC cell
    Legend: filled = passing test, outlined = no passing test, chip colors per status
  function cellState(story: Story, column: number): "pass" | "fail" | "none"
  function totals(spec: Spec): { storiesDone: number; storyCount: number;
    passing: number; criteriaCount: number; blocked: number }
Trade-off: Criterion text is hidden behind tooltips, so the maintainer sees where gaps are but must hover to read what they are.

## Draft 3
Title: To-do list of open work, completed work folded away
Structure:
  type StoryStatus = "Not Started" | "In Progress" | "Completed" | "Blocked"
  type Criterion = { id: string; text: string; hasPassingTest: boolean }
  type Story = { id: string; title: string; status: StoryStatus; criteria: Criterion[] }
  type Spec = { title: string; stories: Story[] }
  type OpenItem = { story: Story; failing: Criterion[] }
  function openItems(spec: Spec): OpenItem[]
    includes a story if status is not Completed or any criterion lacks a passing test
    orders Blocked first, then In Progress, then Not Started
  SpecTodoPage(spec: Spec)
    ProgressBar: share of criteria with a passing test across the spec
    OpenSection(openItems(spec))
      heading: "Left to do: S stories, C criteria"
      OpenStoryBlock(item) for each OpenItem
        line: StatusTag(item.story.status) + story.id + story.title
        FailingCriterionLine for each item.failing entry: criterion.text
        PassingNote: "+N criteria already passing" as one muted line
    DoneSection(collapsed by default)
      heading: "Done: D stories"
      DoneStoryLine: story.id + story.title + "all criteria passing"
Trade-off: Passing criteria on open stories collapse to a count, so the full criteria list per story is not visible at once.
