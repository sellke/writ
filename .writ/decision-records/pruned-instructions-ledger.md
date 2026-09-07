# Pruned Instructions Ledger

> Append-only. One row per line removed from system-instructions.md or commands/_preamble.md
> since cf84742 (Phase 11 Stage 1 closeout). Checked by scripts/prune-ledger.py.
> Rule: ADR-026. Columns: date of removal · source file · class (`moved` = reason is the
> destination path; `behavior-request` = why the model does it unprompted, ≤ 120 chars;
> `duplicate` = where the surviving copy lives) · reason · removed text verbatim, `|` escaped as `\|`.

| Date | File | Class | Reason | Text |
|---|---|---|---|---|
