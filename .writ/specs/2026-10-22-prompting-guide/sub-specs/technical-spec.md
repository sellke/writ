# Technical Spec: Prompting Guide

> Spec: [`../spec.md`](../spec.md)

## Current State (audit, 2026-10-22)

- No prompting guidance exists in the repo. `README.md` § Quick Start lists five commands and says "Start here."
- `.writ/docs/` ships every `*.md` except `recommended-delivery-state-format.md` (`is_shippable_writ_doc` in `scripts/install.sh` and `scripts/update.sh`, byte-identical).
- `scripts/eval.sh` `check_referenced_paths` resolves backticked `*.md` tokens in commands against the repo root; `check_shipped_refs` (`scripts/eval-shipped-refs.py`) forbids links to Writ's development history in shipped commands, not in docs.
- `skills/plain-prose/SKILL.md` is the prose standard.

## File Layout

```markdown
# Prompting Guide

One paragraph: a request is a contract in miniature; Writ reads it the way a careful colleague would.

## What a request carries

- **Goal** — …
- **Done check** — …
- **Proof** — …

## Recipes

### An unsettled idea
Weak: …
Strong: …
Route: `/prototype`

### A bug or a small change
… Route: `/prototype --no-diverge`

### A feature
… Route: `/create-spec`

### Roadmap work
… Route: `/implement-phase <N>`

### A why or how question
… Route: `/research` (replaced by `/why` when it ships)

## Pitfalls

- No done check: …
- Asking a fork you could run: …
- Specifying the how: …
- Bundling requests: …
- Restating the codebase: …
```

## README Change

`README.md` § Quick Start, before the five-command table:

> New here? Read [`.writ/docs/prompting-guide.md`](.writ/docs/prompting-guide.md) (two minutes), then type `/writ` followed by what you want.

The `/writ` mention lands with `2026-10-22-front-door`; until then the sentence ends at "(two minutes)." The front-door spec owns the second clause.

## Test (`scripts/tests/test_prompting_guide.py`)

| Test | Assertion |
|---|---|
| `test_exists_and_budget` | File exists; `len(lines) < 150`. |
| `test_headings` | H2 headings, in order: `## What a request carries`, `## Recipes`, `## Pitfalls`. |
| `test_parts` | Under the first H2, list items beginning `- **Goal**`, `- **Done check**`, `- **Proof**`, in order. |
| `test_recipes` | The five H3 headings exist in order; each H3 block contains lines starting `Weak:`, `Strong:`, `Route:`; each `Route:` line names the expected command. |
| `test_no_internal_links` | No `](` target or backticked path starts with `.writ/research/`, `.writ/decision-records/`, `.writ/specs/`, `.writ/product/`. |
| `test_readme_links_guide` | `README.md` § Quick Start contains `.writ/docs/prompting-guide.md`. |
| `test_ships` | For each of `scripts/install.sh`, `scripts/update.sh`: extracting `is_shippable_writ_doc` with `sed -n '/^is_shippable_writ_doc()/,/^}/p'` and calling it with `prompting-guide.md` exits 0. |

## Shadow Paths

- **Happy path:** guide present, README linked, tests green.
- **Nil input:** a recipe without a `Route:` line → `test_recipes` fails naming the recipe.
- **Empty input:** guide exists but no H2s → `test_headings` fails.
- **Upstream error:** `is_shippable_writ_doc` renamed or restructured → `test_ships` fails on extraction; fix the test's extraction, not the guide.

## Error & Rescue Map

Not required: documentation only.
