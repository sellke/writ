# Archive several projects at once

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** A projects list people can read

## Problem

Project managers at agencies finish around ten projects a month and archive them one at a time, four clicks each. Most do not bother, so their projects list fills with finished work and they scroll past it every day.

## Outcome

A workspace admin clears finished projects off the active list in one go.

**Measure:** The share of workspaces with more than 50 active projects falls from 31% to under 15% within 60 days of release.

## Scope

**In:**

- Selecting several projects on the projects list and archiving them together.

**Out:**

- Bulk delete.
- Bulk restore from the archive.
- Archiving from the mobile app.

## Acceptance criteria

- **A1.** When a workspace admin ticks one or more projects on the projects list and clicks "Archive selected", a confirmation dialog states the number of projects selected.
- **A2.** When the admin confirms, every selected project moves from the Active tab to the Archived tab and the list shows "N projects archived".
- **A3.** When the admin cancels the dialog, no project changes and the ticks stay as they were.
- **A4.** When no project is ticked, the "Archive selected" button is disabled.
- **A5.** A project with an unpaid invoice is skipped; after the run the list shows "N archived, M skipped: unpaid invoices" and the skipped projects stay ticked.
- **A6.** A member who is not a workspace admin sees no tick boxes and no "Archive selected" button.
