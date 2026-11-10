# Enforce the Starter seat limit

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Plans mean what they say

## Problem

Workspaces on the Starter plan of our project-tracking tool are sold with 5 seats, but the limit was never enforced. About 400 Starter workspaces have more than 5 members, and sales cannot make the case for Pro.

## Outcome

A Starter workspace cannot go past 5 members, and its admin sees how to get more.

**Measure:** This will drive upgrades and make the plan limits clearer for everyone.

## Scope

**In:**

- Enforcing the 5-seat limit on Starter when an admin invites someone.

**Out:**

- Removing members from workspaces already over the limit.
- Changes to the Pro or Enterprise plans.
- Price changes.

## Acceptance criteria

- **A1.** When an admin on Starter with fewer than 5 members invites a user, the invite is sent.
- **A2.** When an admin on Starter with 5 members tries to invite a user, no invite is sent and the page shows "Starter includes 5 seats. Upgrade to add more." with an "Upgrade" button.
- **A3.** The Team page on Starter shows "N of 5 seats used".
- **A4.** A workspace on Starter can always invite one more user as a guest, however many members it has, and guests count as members.
- **A5.** Clicking "Upgrade" opens the plan page with Pro preselected.
- **A6.** When the invite form is submitted with an empty or malformed email address, it shows "Enter a valid email address" and no invite is sent.
