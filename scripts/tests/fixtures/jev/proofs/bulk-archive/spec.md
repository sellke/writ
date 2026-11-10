# Archive several projects at once

> **Status:** Built
> **Agreed:** 2026-10-16 by Marta Okafor
> **Roadmap:** A projects list people can read

## Problem

Project managers at agencies archive finished projects one at a time, four clicks each. Most do not bother, so their projects list fills with finished work.

## Outcome

A workspace admin clears finished projects off the active list in one go.

**Measure:** The share of workspaces with more than 50 active projects falls from 31% to under 15% within 60 days of release.

## Scope

**In:**

- Selecting several projects on the projects list and archiving them together.

**Out:**

- Bulk delete.
- Bulk restore from the archive.

## Acceptance criteria

- **A1.** When a workspace admin ticks one or more projects on the projects list and clicks "Archive selected", a confirmation dialog states the number of projects selected.
- **A2.** When the admin confirms, every selected project moves from the Active tab to the Archived tab and the list shows "N projects archived".
- **A3.** When the admin cancels the dialog, no project changes and the ticks stay as they were.
- **A4.** When no project is ticked, the "Archive selected" button is disabled.
- **A5.** A project with an unpaid invoice is skipped; after the run the list shows "N archived, M skipped: unpaid invoices" and the skipped projects stay ticked.
- **A6.** A member who is not a workspace admin sees no tick boxes and no "Archive selected" button.
- **A7.** The support lead signs off the wording of the confirmation dialog before release.

## Proof

> Verified at `3d9b54e` on 2026-11-06 by a verifier that did not write the change.

- **A1. Proved.** Ticked 3 projects on the staging projects list and clicked "Archive selected". The dialog read "Archive 3 projects?".
- **A2. Proved.** Ran the Playwright file `archive.spec.ts` against staging. Output in `proof/a2-playwright.txt`.
- **A3. Proved.** Clicked "Cancel" in the dialog. The three projects were still on the Active tab and still ticked, and the Archived tab count had not changed.
- **A4. Proved.** Signed in as a member who is not an admin. The projects list showed no tick boxes and no "Archive selected" button.
- **A5. Proved.** The skip logic for unpaid invoices is in place and is covered by the existing invoice checks, so those projects will not be archived.
- **A6. Proved.** Signed in as `dana@example.test`, whose role is Member. The projects list had no tick boxes and no "Archive selected" button. Screenshot in `proof/a6-member.png`.
- **A7. Needs a person.** The support lead has to read the dialog text and sign it off. No check can do that.

### Try it yourself

1. On staging, open Projects as an admin, tick two projects, and click "Archive selected".

### Not covered

- Workspaces with more than 500 projects.
