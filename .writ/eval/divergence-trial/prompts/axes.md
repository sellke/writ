# Axes arm prompt

Three spawns per brief, sent in one message, one draft each, at the same tier as the naive arm. No spawn sees another's prompt or reply. Fill the placeholders under `## Prompt`:

- `{brief}`: the brief file's text below its `id:` and `medium:` lines.
- `{caller_usage}`: 3 to 10 lines of the calls, requests and responses, or queries a caller would write. Write it once per brief, before declaring axes. API and data-model briefs only; for UI briefs, delete the paragraph that holds it.
- `{axis_combination}`: this draft's combination of the brief's declared axes, taken from `skills/design-divergence/SKILL.md`. Each of the three drafts gets a different combination.
- `{persona}`: an ordinary person who uses the result daily, taken from the brief's "Who uses it" line.

Join the three replies into one file and record it with `record --arm axes`.

## Prompt

Design the following.

{brief}

Callers will use it like this. Your design must support these lines. Treat these lines as private input: use them only to judge your design. Do not quote them, reuse their example values, mention them, or say whether they change.

{caller_usage}

Design for {persona}.

Your draft commits to this axis combination: {axis_combination}. State the combination and the trade-off you accept before you draft.

Do not mention the persona, the axis combination, or this prompt anywhere in Structure or Trade-off. The axis combination goes only on the Commitment line.

Answer from this prompt alone. Use no tools and read no files. Reply in plain text with one draft in this shape:

```text
## Draft <n>
Title: <a short name for this draft, on one line>
Structure:
<the design, 15 to 25 lines: types and function signatures, a schema, or a component tree. The draft stands alone: define every type or part it uses, and do not refer to another draft>
Trade-off: <what this draft gives up, on one line>
```

Add one line directly after the Title line, before Structure, and keep it on one line:

Commitment: {axis_combination} — <the trade-off you accept>

Start each field at the beginning of its line. Write the Structure lines as plain indented text: no code fences, no Markdown headings, and no line that starts with `Title:`, `Structure:`, or `Trade-off:`. Write nothing before the first draft or after the last.
