# AutoVault Test Report

## Environment

- Date: 2026-10-25.
- OS/shell: Windows, PowerShell.
- Python 3.11.9, pytest 9.1.1, FastAPI 0.162.0, SQLAlchemy 2.1.6.
- Node.js 22.20.0, npm 10.9.3, Vitest 2.1.9, React Testing Library 16.x.
- Backend automated tests use SQLite and FastAPI TestClient. A PostgreSQL service was not available for integration testing.

## Backend tests

Commands, run from `backend/`:

```text
python -m pytest -v
15 passed in 4.07s

python -m pytest --cov=app --cov-report=term-missing
15 passed in 4.59s
app/main.py: 148 statements, 0 missed, 100% statement coverage
TOTAL: 100%
```

The final sequential runs passed. An earlier attempt to run both backend commands at once caused a transient shared SQLite test-database collision; it was rerun sequentially and is not part of the final result.

## Frontend tests and build

Commands, run from `frontend/`:

```text
npm run test:coverage
1 test file passed; 14 tests passed
Statements: 100%; branches: 97.22%; functions: 91.66%; lines: 100%

npm run build
TypeScript check passed; Vite production build passed
```

Vitest and React Testing Library cover auth rendering, registration/login success and login errors, logout, vehicle data and totals, search/category/minimum/maximum filters, empty and failed inventory states, stock-zero disabled purchase, successful purchase refresh, customer/admin control visibility, and admin add/edit/delete/restock flows.

## API and security summary

- Registration and login, role-protected vehicle CRUD, listing/search, purchase, and restock are exercised by backend tests.
- Added regression coverage for customers searching inventory, customers denied admin actions, registration role escalation, inverted price ranges, and short JWT secrets.
- Vehicle input rejects negative price/quantity and blank make/model/category. Purchase uses a conditional atomic database update (`quantity > 0`) and returns conflict when stock is unavailable.
- The test suite verifies sequential oversell prevention. No live PostgreSQL or concurrent multi-connection integration test was possible in this environment; concurrency behavior is supported by the conditional SQL update but remains to be exercised against PostgreSQL.
- JWT secret is now required at startup and must be at least 32 UTF-8 bytes. Password hashing uses Argon2. Public registration always sets the customer role.
- FastAPI startup uses lifespan. The observed Starlette/httpx deprecation was resolved by installing and declaring Starlette's recommended `httpx2` TestClient dependency. Final backend test output had no warnings.

## Docker and running application

- `docker compose config --quiet`: passed when supplied a temporary test-only `JWT_SECRET`. Docker printed a warning that its user configuration file under `C:\Users\spide\.docker` was inaccessible to this sandbox.
- `docker compose up -d --build`: could not run because access to the Docker engine named pipe was denied. `docker compose ps`, live health/API checks, database persistence checks, and frontend-to-backend checks could therefore not be performed.
- No browser session was available against a running app. No screenshots were generated. `screenshots/` contains capture instructions only.

## Dependency audit and remaining warnings

- `npm audit`: reports 10 vulnerabilities in frontend development/build dependencies (6 moderate, 1 high, 3 critical). `npm audit fix` applied non-breaking updates, but the remaining advisories require major tooling upgrades (including Vite/Tailwind/Vitest) according to npm. No forced major upgrade was applied because it could change the existing build/UI stack; review and resolve these before production use.
- `npm install` also reported a deprecated `whatwg-encoding` package; the v8 coverage install reported deprecated `glob` 10.5.0.
- Docker CLI access warnings are environment restrictions, not application output.

## TDD and records

Regression tests were added before implementing their corresponding backend and UI changes. Dependencies were initially unavailable, so the expected failing RED assertions could not be run or committed before implementation. No fabricated RED result or historical commit was created. The final local commit records the combined, tested result; the assignment's strict failing-test-per-commit history is not fully satisfied.

`PROMPTS.md` preserves the existing authentic prompt fragment, marks missing earlier transcripts as TODOs, and includes the exact current Codex task prompt supplied by the developer. It does not invent AI responses. Obtain and paste/link the original unedited chat exports before submission if required.

## Known limitations and conclusion

- No PostgreSQL concurrency/integration run, live Docker deployment, browser screenshots, or API health request was possible because Docker Engine access was denied.
- Earlier ChatGPT logs are incomplete and still require authentic raw exports or links.
- Frontend dev/build dependency audit findings remain unresolved pending a deliberate tooling migration.
- The local implementation, API/UI regression suites, coverage, and production frontend build pass. The project is **not ready for final submission yet** because screenshots, original chat records, Docker/PostgreSQL verification, strict RED/GREEN commit evidence, and dependency-advisory remediation remain outstanding.
