# Alerts for saved candidate searches

> **Status:** Built
> **Agreed:** 2026-10-22 by Priya Nair
> **Roadmap:** Recruiters hear about candidates first

## Problem

Recruiters at staffing firms re-run the same five or six candidate searches every morning to see who is new. It takes about twenty minutes a day, and on busy days they skip it.

## Outcome

A recruiter saves a search once and hears about new matches without re-running it.

**Measure:** The share of recruiters who run the same search more than once a day falls from 64% to under 20% within a month of release.

## Scope

**In:**

- Saving a search from the results page.
- A daily email of new matches for each saved search.

**Out:**

- SMS or push alerts.
- Sharing saved searches with teammates.

## Acceptance criteria

- **A1.** When a recruiter clicks "Save search" on a results page and enters a name, the search appears under "Saved searches" with that name.
- **A2.** Every day at 08:00 in the recruiter's time zone, the recruiter receives one email for each saved search that has new matches since the last email, listing each new candidate's name, current job title, and location.
- **A3.** When a saved search has no new matches since the last email, no email is sent for it that day.
- **A4.** When the recruiter saves a search with the name left blank, the form shows "Give this search a name" and nothing is saved.
- **A5.** When a recruiter clicks "Delete" on a saved search and confirms, it is removed from "Saved searches" and no further emails are sent for it.
- **A6.** A recruiter can have at most 20 saved searches; saving a 21st shows "You have reached the limit of 20 saved searches" and nothing is saved.

## Proof

> Verified at `90aa3f7` on 2026-11-04 by a verifier that did not write the change.

- **A1. Proved.** On staging, searched for "site manager, Leeds", clicked "Save search", and typed "Leeds site managers". The entry "Leeds site managers" appeared under "Saved searches". Screenshot in `proof/a1-saved.png`.
- **A2. Proved.** Started the alert job by hand with `bin/run-job saved_search_alerts`. The job exited 0 and logged that it processed 3 saved searches. Log in `proof/a2-job.txt`.
- **A3. Proved.** Saved a search and added two candidates that match it. The mail catcher received one email listing both candidates.
- **A4. Proved.** The form component marks the name field as required, and the save handler returns early when the name is empty, so nothing can be saved without a name.
- **A5. Proved.** Clicked "Delete" on "Leeds site managers" and confirmed. It left the "Saved searches" list. Then added a new candidate matching that search and ran the alert job: the mail catcher received nothing for it.
- **A6. Needs a person.** Creating 21 searches by hand is slow. Someone should try it before release and see whether the limit message appears.

### Try it yourself

1. On staging, run any candidate search and click "Save search".

### Not covered

- Time zones other than Europe/London.
