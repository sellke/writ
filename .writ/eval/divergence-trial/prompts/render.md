# Render prompt (UI briefs)

One spawn per UI draft, after `blind`, from the blinded sheet text only: twelve spawns (ui-1 and ui-2, Set X and Set Y, Drafts 1 to 3), all with this prompt. Fill `{brief}` with the brief file's text below its `id:` and `medium:` lines and `{draft}` with the draft's blinded text from `rating-sheet.md`. Each spawn writes `render/<brief>/<set>-<n>.html`.

## Prompt

Render the UI design draft below as one self-contained HTML page.

What the page is for:
{brief}

The draft:
{draft}

Rules:
- Follow the draft's Structure exactly. Do not add views, controls, or sections it does not name, and do not drop any it names.
- Fill it with small, plausible sample data for a Writ spec or /prototype record so the layout reads as real.
- One file: inline CSS, and inline JavaScript only if the draft needs an interaction (a click to expand, a tab switch). No external scripts, stylesheets, fonts, or images.
- Neutral styling: system font, gray and one accent color. The styling must not favor this draft over others.
- Do not name the draft, its set, or any design method in the page.
