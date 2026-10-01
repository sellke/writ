# App Verification Recipe

## Launch
- **Command:** `PORT=8765 python3 scripts/tests/fixtures/app-verify/app.py --never-ready`
- **Ready when:** http://127.0.0.1:8765/
- **Ready timeout:** 2s
- **Reuse running instance:** no

## Safety
- **Safety:** none — fixture app holds no state

## Login
- **Method:** none — the fixture has no accounts

## Feature Map
| ID | Feature | Paths | Check |
|---|---|---|---|
| home | Home page renders | `scripts/tests/fixtures/app-verify/app.py` | `PORT=8765 python3 scripts/tests/fixtures/app-verify/check_home.py` |

## Evidence
- **Artifacts:** none

## Cleanup
- **After:** none
