# Owners invite their own teammates

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Self-serve workspaces

## Problem

Workspace owners at small design studios cannot add a teammate themselves. They email support, and the account arrives about two days later. New hires spend their first days without access.

## Outcome

An owner adds a teammate in under a minute without contacting support.

**Measure:** Support requests to add a user fall from about 40 a week to under 5 within a month of release.

## Scope

**In:**

- Inviting one teammate at a time by email address from the Team page.

**Out:**

- Single sign-on.
- Bulk invites from a spreadsheet.
- Changing a member's role after they join.

## Acceptance criteria

- **A1.** When an owner enters a teammate's email address on the Team page and clicks "Send invite", the teammate receives an email with a link to join the workspace.
- **A2.** When the teammate opens the link and sets a password, they land in the workspace and appear on the Team page as "Member".
- **A3.** The owner sees each pending invite on the Team page with the email address and the date it was sent.
- **A4.** When the owner clicks "Revoke" on a pending invite, it disappears from the Team page.
- **A5.** The owner can upload a spreadsheet of email addresses and all of them receive invites at once.
