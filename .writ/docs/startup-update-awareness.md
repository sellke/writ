# Startup Update Awareness

> **Status:** Normative. This is the procedure that lived in `system-instructions.md` → Startup Update Awareness until 2026-09-07, moved here under [ADR-026](../decision-records/adr-026-constraint-test-pruning.md) (every removed line is in [`pruned-instructions-ledger.md`](../decision-records/pruned-instructions-ledger.md)). The base keeps the trigger sentence and one pointer line to this file.
> **Applies:** Cursor, Claude Code, Codex CLI. `scripts/install.sh` ships `.writ/docs/*.md`, so installed projects carry this file.
> **Related:** [`commands/update-writ.md`](../../commands/update-writ.md) — the only workflow that applies updates.

When first invoked in a session, run a quiet Writ update awareness check before session auto-orientation or any command-specific workflow. Preserve the user's original request as the main task; update discovery must never block, replace, or expand that task.

Startup sequence:

1. Detect whether the current project appears to use Writ and whether the invocation is already `/update-writ`.
2. Read `.writ/state/writ-update-check.json` if it exists.
3. If the cache records today's local date in `last_checked_date`, skip upstream network work and continue silently.
4. If the cache is missing, stale, malformed, or missing `last_checked_date`, treat it as no valid same-day cache and continue through conservative eligibility checks.
5. If no same-day cache exists, perform at most one lightweight, read-only upstream probe using existing manifest/source metadata when available. The probe must compare the installed Writ identity (version, revision, or release tag when available) against the upstream identity; a reachable upstream source or successful network response alone is not evidence of an update.
6. Record today's result under `.writ/state/`; create `.writ/state/` only when recording a result.
7. Notify only when a copied Writ installation has a strictly newer upstream identity and today's recorded `status` is `update_available`.
8. Continue the user's original request, auto-orientation, or command workflow.

Cache contract:

- Preferred path: `.writ/state/writ-update-check.json`
- Required daily-limit field: `last_checked_date` as a local `YYYY-MM-DD` date
- Recommended metadata: `source`, `installed_version`, `installed_revision`, `latest_seen_version`, `latest_seen_revision`, `status`, and `checked_by`
- Allowed `status` values: `current`, `update_available`, `skipped_unsupported`, `skipped_source_repo`, `skipped_linked_install`, and `upstream_error`

Detection rules:

- Copied install with usable manifest/source metadata and a strictly newer upstream version, revision, or release tag: record `update_available` and show the `/update-writ` note.
- Copied install with usable manifest/source metadata and matching or older upstream identity: record `current` and stay quiet.
- Copied install where upstream is reachable but installed-vs-upstream comparison is unavailable, ambiguous, or unordered: record `skipped_unsupported` or `upstream_error` and stay quiet.
- Missing manifest/source metadata, uncertain installation class, or unsupported installation shape: record or skip as `skipped_unsupported` and stay quiet.
- Writ source repo: record or skip as `skipped_source_repo`; do not recommend `/update-writ`.
- Linked installation: record or skip as `skipped_linked_install`; do not recommend `/update-writ`.
- Network, timeout, auth, or upstream probe failure: record `upstream_error` for the day and stay quiet.
- User explicitly invoked `/update-writ`: do not show a duplicate startup update prompt.

Use this exact notification style only after recording `status: "update_available"` for a copied install with a strictly newer upstream identity: "Writ update available. Run `/update-writ` when you are ready."

Stay quiet and continue the original workflow when Writ is current, already checked today, offline, missing usable manifest/source metadata, unsupported, running from the Writ source repo, running from a linked installation, or already executing `/update-writ`.

Startup update discovery is read-only except for the daily cache under `.writ/state/`. It must never apply updates, overwrite Writ files, edit manifests, install packages, create commits, clone or pull repositories, or add an `@sellke/writ` update-check runtime command. `/update-writ` remains the only Writ workflow that applies updates.
