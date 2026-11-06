# Naive arm prompt

One spawn per brief, at the same tier as the axes arm. Send the text under `## Prompt` with `{brief}` replaced by the brief file's text below its `id:` and `medium:` lines. Record the reply with `record --arm naive`.

## Prompt

Give me three options for the following.

{brief}

Answer from this prompt alone. Use no tools and read no files. Reply in plain text with three drafts in one response, numbered 1 to 3, each in this shape:

```text
## Draft <n>
Title: <a short name for this draft, on one line>
Structure:
<the design, 15 to 25 lines: types and function signatures, a schema, or a component tree. The draft stands alone: define every type or part it uses, and do not refer to another draft>
Trade-off: <what this draft gives up, on one line>
```

Start each field at the beginning of its line. Write the Structure lines as plain indented text: no code fences, no Markdown headings, and no line that starts with `Title:`, `Structure:`, or `Trade-off:`. Write nothing before the first draft or after the last.
