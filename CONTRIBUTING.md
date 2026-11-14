# Contributing to PayGuard

## Rules
1. `main` is protected. Work on a branch named `r<role number>/<short-name>`, for example `r2/upload-view`.
2. Open a pull request. It needs one reviewer and a green CI run before it is merged.
3. The pull request description names the design sections it touches and the tests you ran.
4. Commit your own work in small steps.
5. Never weaken or delete a failing test to make CI pass. A failing test means a contract is broken: raise it in `docs/decisions.md`.
6. Never commit secrets. `.env` is ignored; use fake values in tests.

## Changing a contract
Contracts live in sections 4 and 5 of `docs/design.md`. A change needs the code, the document edit and a
line in `docs/decisions.md` in the same pull request.

## Definition of done for a module
- Everything in your brief (design section 10) exists at the stated paths.
- Your unit and contract tests pass: `pytest`.
- `tests/integration/test_flow.py` still passes after your merge.
- `bandit -r accounts repos scans dashboard charts scanner -q` reports nothing.
- You have written half a page for the report (what it does, why it is designed this way) and sent it to R1.
