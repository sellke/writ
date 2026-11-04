# Prompting Guide

This guide covers the three parts a request carries, a recipe for each route a request can take, and the pitfalls that waste a run. Read it once before your first request.

## What a request carries

- **Goal**: what should be true afterwards, in your own terms.
- **Done check**: how anyone could tell the work is done.
- **Proof**: the evidence the result must show, such as a test, a screenshot, or a command's output.

The strong examples below state all three in a few sentences.

## Recipes

### An unsettled idea

Weak: `Make the settings page better.`

Strong: `The settings page feels crowded. Try two or three layouts. Done when I can compare them rendered and pick one. Proof: a screenshot of each draft.`

Route: `/prototype`

### A bug or a small change

Weak: `Fix the login bug.`

Strong: `Login fails for emails with a plus sign. Done when the test for a+b@example.com passes. Proof: that test's output.`

Route: `/prototype --no-diverge`

### A feature

Weak: `Add export.`

Strong: `Users can export their invoices as CSV from the billing page. Done when a user with three invoices downloads a three-row file. Proof: a passing acceptance test for that case.`

Route: `/create-spec`

### Roadmap work

Weak: `Keep going on the roadmap.`

Strong: `Build phase 3 of the roadmap. Done when every feature in the phase has shipped and the phase's exit criteria pass. Proof: the exit criteria results.`

Route: `/implement-phase <N>`, where N is the phase number

### A why or how question

Weak: `How does auth work?`

Strong: `Why do sessions expire after one hour on staging but never locally? Done when the answer names the setting that differs and where each environment sets it. Proof: the two values, quoted from their files.`

Route: `/research` (`/why` replaces it when it ships)

## Pitfalls

- No done check: the run ends when the agent decides, so write the check that ends it.
- Asking "A or B?" when running both would answer it: ask `/prototype` to build both and compare them.
- Specifying the how instead of the what: name the outcome and let the agent choose the approach, unless the approach is itself the requirement.
- Bundling several requests into one: split them so each has its own done check and its own run.
- Restating the codebase to the agent: name the files by path and let the agent read them.
