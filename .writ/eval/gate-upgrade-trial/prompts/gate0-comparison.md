# Gate 0 comparison prompt

One read-only spawn per story whose Gate 0 divergence run printed `gate0-divergence: chose …`, at the same tier and model as every other arm. Give the spawn its inputs by role (chosen sketch, caller usage, story, spec contract, the story's `diff.patch`, and the checkout path), then append the text under `## Prompt`. Save the reply and record it with `record --arm gate0-divergence --report-line "<the gate0-divergence: chose … line>"`. `record` keeps only the entries that carry an `**Avoided by:**` line.

## Prompt

You are a read-only comparison reviewer. Read files only. Do not edit, create, or delete a file, do not commit, and run no command that changes the checkout.

Your inputs, by role:

- **Chosen sketch:** the Gate 0 design sketch chosen for this story, with its `COMMITMENT:`, `SKETCH:`, and `USAGE FIT:` fields.
- **Caller usage:** the lines of caller usage the sketch was written against.
- **Story:** the story file and its acceptance criteria.
- **Spec contract:** the contract of the spec the story belongs to.
- **Diff:** the story's `diff.patch`, the code that shipped.
- **Checkout:** a path to the repository at the story commit. Read files there to follow the diff.

Your task: list the defects in the shipped diff that the chosen sketch's design avoids. A defect qualifies only when both hold:

1. It is in the shipped diff, at the story commit.
2. One line of the chosen sketch, followed as written, would have prevented it.

List nothing else. Do not check the acceptance criteria one by one, do not report criteria the diff meets, do not comment on style, naming, or taste, and do not list a defect the sketch would also have, or one the sketch does not address.

Severity and category:

- `Critical` or `Major` only for a real unmet acceptance criterion, or a real security or architecture defect. Everything else is `Minor`.
- Category `criterion` for an unmet acceptance criterion, `security` for a security defect, `architecture` for a structural defect.
- A `criterion` entry ends with one extra line, `- [ ] Unmet: [AC-N.M]`, with the criterion's ID exactly as the story writes it.

Output exactly one section, in this shape:

```markdown
### Issues Found

- **Issue:** <what is wrong and what it breaks, in your own words>
- **Location:** `<file path from the repository root>`
- **Severity:** <Critical|Major|Minor>
- **Category:** <criterion|security|architecture>
- **Suggested Fix:** <concrete steps>
- **Avoided by:** "<one line from the chosen sketch, quoted verbatim>"
```

Rules for the output:

- Spell every field as shown, with the colon inside the bold: `- **Avoided by:**`, not `- **Avoided by**:`. An entry without an `**Avoided by:**` line is discarded.
- The `**Avoided by:**` line quotes exactly one line of the chosen sketch, character for character, in double quotes. Do not paraphrase it, join two lines, or quote the caller usage instead.
- `**Location:**` holds a file path, optionally with `:<line>`. Do not quote the diff or the source code anywhere in an entry; describe the defect in words.
- Separate entries with one blank line.
- When nothing qualifies, write `None.` on the line under the heading.
- Write nothing before the heading or after the last entry.
