# Shift swaps in the rota app

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** The rota is the truth

## Problem

Nurses on a hospital ward arrange shift swaps on a paper sheet at the nurses' station. The ward manager re-enters each one into the rota app, about three hours a week, and a missed entry means the rota shows the wrong nurse on shift.

## Outcome

A nurse proposes a swap in the rota app and the ward manager approves it in one tap.

**Measure:** The ward manager's weekly time spent re-entering swaps falls from about 3 hours to under 30 minutes, from her own log over the four weeks after launch.

## Scope

**In:**

- Swap requests between two nurses on the same ward.

**Out:**

- Swaps across wards.
- Agency staff.
- Automatic approval.

## Acceptance criteria

- **A1.** When a nurse opens one of their own upcoming shifts, taps "Propose swap", picks a colleague's shift, and adds a note, the colleague receives a notification naming both shifts.
- **A2.** When the colleague accepts, the request appears in the ward manager's "Swaps to approve" list.
- **A3.** When the manager approves, both shifts change owner on the rota and both nurses receive "Swap approved".
- **A4.** The rota should handle swaps that cause problems sensibly.
- **A5.** When the manager declines, the rota does not change and both nurses receive "Swap declined" with the manager's reason.
