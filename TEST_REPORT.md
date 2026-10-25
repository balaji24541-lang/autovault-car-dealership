# AutoVault Test Report

## Environment

- Date: 2026-10-25.
- Windows PowerShell, Python 3.11.9, pytest 9.1.1, FastAPI 0.162.0, SQLAlchemy 2.1.6.
- Node.js 22.20.0, npm 10.9.3, Vite 6.4.5, Vitest 2.1.9, React Testing Library 16.x.
- API tests use SQLite and FastAPI TestClient. Docker verification uses PostgreSQL 16 in the Compose stack.

## Backend tests

Run from `backend/`:

```text
python -m pytest -v
15 passed in 4.14s

python -m pytest --cov=app --cov-report=term-missing
15 passed in 4.16s
app/main.py: 148 statements, 0 missed, 100% statement coverage
TOTAL: 100%
```

The final test runs completed without warnings. Regression tests cover authentication, customer/admin permissions, role escalation, vehicle listing and search, invalid values, purchases, restocking, and short or malformed JWTs.

## Frontend tests and build

Run from `frontend/`:

```text
npm test -- --run
1 test file passed; 14 tests passed

npm run test:coverage
1 test file passed; 14 tests passed
Statements: 100%; branches: 97.22%; functions: 91.66%; lines: 100%

npm run build
TypeScript check passed; Vite 6.4.5 production build passed
```

UI tests cover auth rendering, registration/login and login errors, logout, vehicle cards and totals, make/model/category/price filters, empty and failed inventory states, stock-zero purchase behavior, successful purchase refresh, customer/admin visibility, and admin add/edit/delete/restock actions.

## Docker, PostgreSQL, and API

- `docker compose config`: passed using the ignored local `.env` secret.
- `docker compose up -d --build`: passed after adding `frontend/.dockerignore` and rebuilding with Vite 6.4.5.
- `docker compose ps`: backend and frontend are running; PostgreSQL is healthy.
- PostgreSQL accepted connections. After verification and screenshot cleanup, the persistent database contains 1 user, 4 vehicles, and 2 purchases, matching the original counts. No volume was removed or reset.
- Persistence was verified across Compose container recreation and a backend restart. A labeled demo purchase persisted, then only the temporary screenshot users, their purchase, and three `DEMONSTRATION ONLY` vehicles were removed. Existing rows were left unchanged.
- A live PostgreSQL concurrency check sent 12 simultaneous purchases against a temporary vehicle with stock 5: 5 requests returned 200, 7 returned 409, final quantity was 0, and exactly 5 purchase rows were written. The temporary user, vehicle, and purchase rows were then removed; original row counts returned to 1 user, 4 vehicles, and 2 purchases.
- `/openapi.json` returned HTTP 200 and the frontend returned HTTP 200. Playwright/Edge exercised customer login, inventory loading, filtering, purchasing, admin login, and the add form against the running Compose application.

## Screenshots

Genuine Edge screenshots driven by Playwright Core are in `screenshots/`:

- `login.png`, `registration.png`
- `inventory.png`, `search-filter.png`
- `admin-dashboard.png`, `add-vehicle.png`
- `purchase.png`

The displayed demo records are marked `DEMONSTRATION ONLY`. Screenshot-only accounts and inventory were cleaned from PostgreSQL after capture.

## Dependency security audit

- Applied the non-forced compatible npm updates and upgraded direct Vite to 6.4.5; the Vite peer compatibility was checked, and the test suite and production build pass.
- `npm audit` still reports **10 findings: 6 moderate, 1 high, 3 critical**. Affected packages include `@vitest/coverage-v8`, `@vitest/mocker`, `vitest`, `vite-node`, `tinypool`, nested `vite`/`esbuild`, `tailwindcss`, `postcss-nested`, and `postcss-selector-parser`. The direct Vite dependency is 6.4.5; remaining Vite advisories are through the older test-tool dependency tree.
- `npm audit --omit=dev` reports 0 findings. The Compose frontend currently installs dev dependencies to run Vite, so the remaining findings still exist in the development/test toolchain used by that container.
- npm reports that clearing the remaining findings requires major toolchain changes. An attempt to update Vitest and its coverage provider to 4.1.12 failed in npm's resolver with `Cannot read properties of null (reading 'edgesOut')`; the tested manifest and lock were retained. No `npm audit fix --force` was run.
- Remaining install/build warnings include deprecated `whatwg-encoding` and `glob` packages. The frontend security findings need a deliberate follow-up migration.

## AI records and TDD

- `README.md` contains the required **My AI Usage** section and distinguishes the supplied account of earlier developer work from actions verified during this finalization.
- `PROMPTS.md` preserves the available original prompt fragment, records both supplied Codex prompts verbatim, and leaves TODOs for missing authentic ChatGPT/Codex conversation exports. No AI responses or conversation logs were invented.
- Tests were authored before corresponding improvements, but missing dependencies prevented observing and committing RED failures before implementation. No historical commits or failing results were fabricated. The required strict RED/GREEN/REFACTOR commit sequence remains unverified.

## Conclusion and remaining work

Docker/PostgreSQL startup, persistence, API connectivity, frontend-to-backend flows, screenshots, automated tests, and the production build have been verified. The original database counts were preserved. The project still needs authentic earlier AI conversation exports, a deliberate frontend toolchain migration to resolve the full npm audit findings, and genuine RED/GREEN/REFACTOR evidence if the assignment requires it. Until those items are addressed, this is **not yet ready for final submission**.
