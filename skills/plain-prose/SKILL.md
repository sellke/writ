---
name: plain-prose
description: "Detect and rewrite mannered prose in instructional markdown — commands, agents, skills, adapters — into plain, direct text that keeps every rule, literal, and structure the file carries."
disable-model-invocation: true
status: candidate
---

# Plain Prose

## Purpose

Instruction files are loaded by a model on every invocation. Each word costs
tokens, and each flourish invites the model to weight tone over rule. This
skill converts mannered prose into plain prose: the same rules in fewer words,
with no atmosphere.

Mannered prose performs instead of informs. It shows up as literary framing,
rhetorical flourish, promotional adjectives, throat-clearing, stacked hedges,
fake contrasts, self-justifying asides, redundant summaries, shouting, and
emphasis inflation. Plain prose leads with the instruction, uses active voice
and concrete nouns, and stops when the rule has been stated.

This skill owns how to find and rewrite mannered sentences. The consumer owns
which files to touch and when to run repository checks.

## When to Use

- Writing or revising a command, agent, skill, adapter, or system-instruction file
- Reviewing a diff that adds instructional prose
- Auditing a file whose scan counts (step 1) are high relative to its size

## How to Apply

### 1. Scan, then read everything

Grep first so the worst sentences are known before reading. Run from the
repository root, substituting the target path:

```bash
# Marker words and phrases that almost always signal manner
grep -nwiE "comprehensive|robust|seamless(ly)?|elegant(ly)?|powerful|crucial|meticulous(ly)?|genuinely|truly|holistic|paramount|pivotal|leverage|streamline|delve|journey|landscape|navigate|unlock|non-negotiable|note that|it'?s (important|worth) (to note|noting)|keep in mind|remember:|this ensures|ensures? that|earns its place|the beauty of|think of (it|this) as" FILE

# Fake contrasts: an alternative nobody proposed, introduced to be rejected
grep -nE "— not [a-z]|: not [a-z]|not (just|only|merely|simply) [^.]{0,40},? but|isn'?t (just|only|merely|simply) |is more than (just )?an?\b" FILE

# Shouting, whole-sentence bold, em-dash density (per 1000 words)
grep -nE "\b(MUST|NEVER|ALWAYS|MAX|NOT)\b|^\*\*[^*]{30,}\*\*\.?$" FILE
echo "$(grep -o '—' FILE | wc -l) em-dashes / $(wc -w < FILE) words"
```

The grep finds a small fraction of the manner. Most of it is ordinary
sentences carrying an extra clause, adjective, or justification, and no
pattern catches those. After the scan, read every paragraph and apply step 2
to each sentence. On a file that has never had this pass, expect to change
most paragraphs, not the four or five lines the grep flagged.

Hits are candidates, not verdicts. "Competitive landscape" in a template
heading and "Navigate to `/settings`" in a UAT step are literal uses.

### 2. Classify each sentence

| Pattern | Example from this repository | Rewrite |
|---|---|---|
| Promotional adjective | "comprehensive test coverage" | Name the measurable property or drop it: "all criteria covered by tests" |
| Filler adjective pair | "clear, actionable reasoning" | One concrete noun: "specific reasons" |
| Nominalization | "performs spec drift detection — comparing the implementation..." | The verb: "compares the implementation against the spec and reports deviations" |
| Role preamble | "Specialized agent for reviewing implementations and determining if they meet standards" | What it does: "Reviews implementations against quality standards" |
| Throat-clearing | "It's important to note that hints reference spec.md" | State the fact: "Hints reference spec.md" |
| Fake contrast | "Speed over completeness — get it documented, not perfect" | Keep the instruction; drop the strawman: "Document it in under 2 minutes" |
| Self-justifying aside | "This is non-negotiable — every criterion must map to a test" | The rule alone: "Every criterion must map to a passing test" |
| Literary framing | "`/implement-story` is the quarterback" | The literal role: "`/implement-story` runs the per-story pipeline" |
| Shouting | "Ask 2-3 questions MAX", "ALWAYS scanned — no category is ever skipped" | Plain imperative: "Ask at most three questions", "Scan every category" |
| Emphasis inflation | "**Do not** auto-FAIL solely for a justified deviation" | Plain text; bold marks a term a reader scans for, never a sentence |
| Hedge stack | "it might be worth considering whether" | One verb: "consider" |
| Redundant summary | "This ensures every agent run starts with fresh context." | Delete; the preceding steps already say it |
| Rhetorical question in instruction voice | "Why does this matter? Because..." | The statement, and cut "because" when the reason is obvious |
| Anthropomorphic verdict | "a diagram that merely restates the prose is noise" | The condition: "Skip diagrams that restate the prose" |

Leave questions that are literal prompts to the user, quoted persona strings,
and the wording of example output that a test or reader matches on. Those are
product voice, and changing them is a design decision for the consumer.

### 3. Rewrite

- Lead with the instruction. Put the condition after the verb: "Omit the line
  when there are no findings", not "When there are no findings, and because an
  empty block is worse than none, omit the line".
- One idea per sentence, about 20 words, active voice.
- Replace each adjective with the property it stands for, or delete it. A
  reader cannot act on "robust"; they can act on "retries three times".
- Keep a contrast only when the rejected alternative is a mistake the reader
  would plausibly make. "Compare against the spec, not your own preferences"
  survives; "a report, not a novel" does not.
- Cut a sentence that restates the one before it. Cut closing lines that
  summarize the section.
- Break em-dash chains into sentences or a colon. One parenthetical per
  sentence at most. Em-dashes inside table cells and after a bolded list lead
  ("**Term** — definition") are structural in this repository; leave them.
- Unbold sentences. Keep bold on the one or two words a reader scans for.
- When a flourish is the only statement of a rule, rewrite it plainly instead
  of deleting it. Plain prose removes tone, never content.

### 4. Preserve

Some text looks like prose but is load-bearing. Do not change:

- YAML frontmatter. `description:` is mirrored in `.writ/manifest.yaml` and
  the generated root catalog; revise it only through the manifest.
- Tagged code fences (` ```bash `, ` ```yaml `, ` ```json `, ` ```mermaid `,
  and other languages), inline code spans, file paths, command and flag names.
- Headings and anchors. Links across files depend on them.
- Table structure. Edit the prose inside a cell; do not merge or drop cells.
- Every `{placeholder}`, section marker, and field name inside a template.
- AskQuestion prompt text and persona strings.
- Pinned literals. `scripts/eval.sh` `require_literal` bindings and the
  Python tests assert exact sentences from commands, agents, and system
  instructions. Before rewriting a sentence in `commands/`, `agents/`, or
  `system-instructions.md`, grep `scripts/` for a distinctive fragment of it.
  If it is pinned, leave it or update the binding in the same change.
- Every rule, threshold, number, ordering, and exception. If a deleted
  sentence carried one, the sentence that now carries it must be identifiable
  in the diff.

Untagged fences are a different case. In `agents/*.md` the untagged fence is
the prompt template, which is the instruction prose a model reads at runtime,
and it usually holds most of the file's manner. Rewrite it like any other
prose, keeping every placeholder and section marker. An untagged fence that
shows example output defines a shape; keep the shape and change only mannered
sentences inside it.

### 5. Verify

- Re-run the step 1 scan. Remaining hits should be literal uses or quoted text.
- Read the diff. For each deleted sentence, name the surviving sentence that
  carries its rule, or confirm it carried none.
- Check the word count. A first pass on a file usually removes 5 to 20 percent
  of the words. Under 3 percent means only the grep hits were fixed; go back
  to step 1's "read everything". Above about 30 percent on a file that was
  mostly rules is a signal to re-check for lost content.
- Run the repository checks the consumer names. In this repository that is
  `bash scripts/lint-skill.sh` on any touched skill, `uv run pytest`, and
  `bash scripts/eval.sh`.

## Examples

**Self-justifying aside.**

Before: "Surface the count and the newest finding code only; the enumeration
lives in the baseline file. A block listing forty baselined items defeats a
command meant to orient in under ten seconds."

After: "Surface the count and the newest finding code only; the full list is
in the baseline file."

**Literary framing plus emphasis.**

Before: "Its defining quality is that depth scales with the target: a ten-line
utility *earns* three sentences, a multi-branch state machine *earns* a full
walkthrough and a diagram."

After: "Depth scales with the target: a ten-line utility gets three sentences,
a multi-branch state machine gets a full walkthrough and a diagram."

**Fake contrast that hides the rule.**

Before: "Pushback should feel like a colleague raising a concern, not a critic
finding fault."

After: "Back every pushback with specific evidence. Do not editorialize."

**Shouting inside an agent prompt template.**

Before: "**All 5 categories are ALWAYS scanned** — no category is ever skipped."

After: "Scan all five categories on every review."

## Anti-patterns

| Pattern | Why it fails |
|---|---|
| Fixing only the grep hits | The grep finds a fraction of the manner. Read every paragraph. |
| Deleting the rule along with the flourish | The file now says less than it did. Rewrite the sentence plainly instead. |
| Skipping an agent's prompt template because it is fenced | The template is the instruction prose. Only tagged code fences are off limits. |
| Replacing every em-dash with a comma | Produces run-on sentences. Split into sentences or use a colon. |
| Rewriting AskQuestion or persona text | Changes product voice through a prose edit. Route it through the consumer. |
| Changing a pinned literal | Breaks `require_literal` bindings or unit tests. Grep `scripts/` first. |
| Adding MUST, NEVER, or all-caps to sound firm | Emphasis inflation. A plain imperative is already firm. |
| Rewriting a table header or heading | Breaks anchors and cross-references. |
