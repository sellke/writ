# Refresh Docs Command (refresh-docs)

> **⚠️ DEPRECATED:** This command is superseded by `/verify-spec`, which provides all the same functionality plus comprehensive validation:
>
> **Migration:**
> - `/refresh-docs feature` → `/verify-spec` (auto-fix mode syncs README, checkboxes, changelog)
> - `/refresh-docs feature --pre-deploy` → `/verify-spec --pre-deploy`
> - `/refresh-docs feature --skip-trello` → `/verify-spec` (Trello is opt-in via `--sync-trello`)
> - `/refresh-docs feature --dry-run` → `/verify-spec --check`
>
> **What verify-spec adds over refresh-docs:**
> - Story file integrity checks (orphans, phantoms, missing sections)
> - Acceptance criteria & Definition of Done verification
> - Dependency graph validation
> - Coverage enforcement
> - Spec contract vs implementation drift detection
> - Structured verification report file
>
> This file is retained for reference. Use `/verify-spec` for all new work.

---

*Original refresh-docs documentation preserved below for reference.*

## Overview

Synchronize documentation, specifications, and Trello tracking with completed implementation work. Uses test results as the source of truth to automatically update specs, mark deliverables complete, generate completion reports, and update Trello cards.

*(See git history for full original documentation)*
