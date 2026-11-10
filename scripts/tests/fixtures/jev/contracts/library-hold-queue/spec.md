# Place a hold from the catalogue

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** Branch staff off the phone

## Problem

Members of the public library phone their branch to reserve a book that is out on loan. Branches take about 300 of these calls a week, and members have no way to know how long the wait is.

## Outcome

A member places a hold online and sees their place in the queue.

**Measure:** Phone reservations fall from about 300 a week to under 100 within two months of launch, counted from the branch call log.

## Scope

**In:**

- Placing and cancelling holds on physical books from the online catalogue.

**Out:**

- E-books and audiobooks.
- Holds on reference-only items.
- Fines.

## Acceptance criteria

- **A1.** When a signed-in member clicks "Place hold" on a book with no available copy, the page shows "Hold placed. You are number N in the queue", where N is one more than the number of earlier holds on that book.
- **A2.** When a copy is returned, the first member in the queue receives an email saying the book is ready at their chosen branch and will be kept for 7 days.
- **A3.** When the member does not collect within 7 days, the hold is cancelled, the member receives "Your hold has expired", and the next member in the queue is notified.
- **A4.** When a member with 10 active holds clicks "Place hold", the page shows "You have reached the limit of 10 holds" and no hold is placed.
- **A5.** When a member clicks "Cancel hold" and confirms, the hold is removed and every later member in the queue moves up one place.
- **A6.** A visitor who is not signed in sees "Sign in to place a hold" instead of the "Place hold" button.
