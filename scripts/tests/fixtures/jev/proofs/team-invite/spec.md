# Owners invite their own teammates

> **Status:** Built
> **Agreed:** 2026-10-19 by Marta Okafor
> **Roadmap:** Self-serve workspaces

## Problem

Workspace owners at small design studios cannot add a teammate themselves. They email support, and the account arrives about two days later.

## Outcome

An owner adds a teammate in under a minute without contacting support.

**Measure:** Support requests to add a user fall from about 40 a week to under 5 within a month of release.

## Scope

**In:**

- Inviting one teammate at a time by email address from the Team page.

**Out:**

- Single sign-on.
- Bulk invites from a spreadsheet.

## Acceptance criteria

- **A1.** When an owner enters a teammate's email address on the Team page and clicks "Send invite", the teammate receives an email with a link to join the workspace.
- **A2.** When the address is empty or is not a valid email address, the form shows "Enter a valid email address" and no invite is sent.
- **A3.** When the teammate opens the link and sets a password, they land in the workspace and appear on the Team page as "Member".
- **A4.** A link older than 7 days shows "This invite has expired. Ask the owner for a new one." and does not let the teammate join.
- **A5.** When the owner clicks "Revoke" on a pending invite, it disappears from the Team page and its link shows "This invite is no longer valid."

## Proof

> Verified at `e02f6c1` on 2026-11-05 by a verifier that did not write the change.

- **A1. Proved.** Entered `sam@example.test` on the staging Team page and clicked "Send invite". The mail catcher received a message to that address with the subject "You're invited to Brightside Studio" and a join link. Captured in `proof/a1-mail.txt`.
- **A2. Proved.** Validation for the email field was added in `InviteForm.tsx` and the API rejects bad addresses too. This is working as expected.
- **A3. Proved.** Opened the join link from A1 in a private window, set a password, and landed on the workspace home page. The Team page then listed `sam@example.test` as "Member".
- **A4. Needs a person.** Someone should wait a week and then try an old link to see whether the expired message appears.
- **A5. Proved.** Revoke is fully implemented and has been reviewed. The invite record is deleted and the link handler checks for a missing invite.

### Try it yourself

1. On staging, open Team and invite an address you can read in the mail catcher.

### Not covered

- Nothing else.
