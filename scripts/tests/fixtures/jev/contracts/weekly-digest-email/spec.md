# Monday digest of vehicle services

> **Status:** Draft
> **Agreed:** not yet
> **Roadmap:** No surprise failures

## Problem

Fleet managers at logistics firms find out a vehicle's service is overdue when it fails a roadside inspection. They would have to open the maintenance tool and filter by date to see it earlier, and most do not.

## Outcome

Each Monday a fleet manager knows which vehicles are overdue without opening the tool.

**Measure:** To be decided after launch.

## Scope

**In:**

- A weekly email to fleet managers listing overdue and upcoming services.

**Out:**

- SMS or in-app notifications.
- Daily or monthly schedules.
- Sending the digest to drivers.

## Acceptance criteria

- **A1.** Every Monday at 07:00 in the depot's time zone, each fleet manager receives one email titled "Fleet services this week".
- **A2.** The email lists every vehicle whose service is overdue, with its registration, the service type, and the number of days overdue, most overdue first.
- **A3.** Drivers also receive the digest for the vehicles assigned to them.
- **A4.** When no vehicle is overdue or due in the next 7 days, the email says "Nothing due this week" and lists no vehicles.
- **A5.** When a manager clicks "Unsubscribe" in the email and confirms, they receive no further digests.
