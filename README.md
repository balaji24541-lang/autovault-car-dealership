# AutoVault — Car Dealership Inventory System

A full-stack car inventory application with customer registration/login, JWT authentication, vehicle filtering, purchasing, and admin inventory management.

## Stack
- Backend: FastAPI, SQLAlchemy, PostgreSQL, JWT, Argon2
- Frontend: React, TypeScript, Vite, Tailwind CSS
- Tests: pytest, FastAPI TestClient, Vitest

## Quick start (Docker)
1. Copy `.env.example` to `.env` and replace `JWT_SECRET` with a strong random value.
2. Run `docker compose up --build`.
3. Open http://localhost:5173. API docs: http://localhost:8000/docs.

## Local setup (without Docker)
1. Start a PostgreSQL server and create an empty database.
2. `cd backend && python -m venv .venv` and activate it (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on macOS/Linux).
3. `pip install -r requirements.txt`.
4. Set `DATABASE_URL` to your PostgreSQL URL (example: `postgresql+psycopg://user:password@localhost:5432/dealership`) and set a strong `JWT_SECRET`.
5. `uvicorn app.main:app --reload`.
6. In a separate terminal: `cd frontend && npm install && npm run dev`.

## Admin account
Public registration always creates customer accounts. To provision a local admin, register an account through the UI and run the following SQL against your **local development database**:
```sql
UPDATE users SET role = 'admin' WHERE email = 'your-admin@example.com';
```
Log out and log in again to receive the admin role in the login response. Never expose public role assignment.

## Endpoints
- `POST /api/auth/register`, `POST /api/auth/login`
- `GET /api/vehicles`, `GET /api/vehicles/search`
- `POST /api/vehicles` (admin)
- `PUT /api/vehicles/{id}` (admin)
- `DELETE /api/vehicles/{id}` (admin)
- `POST /api/vehicles/{id}/purchase` (authenticated)
- `POST /api/vehicles/{id}/restock` (admin)

All vehicle routes require `Authorization: Bearer <token>`. Search supports `make`, `model`, `category`, `min_price`, `max_price`. Stock decrements use an atomic conditional SQL UPDATE to prevent overselling.

## Tests
Backend: `cd backend && pytest -v --disable-warnings`
Frontend: `cd frontend && npm test`
Coverage (optional): `pip install pytest-cov && pytest --cov=app --cov-report=term-missing`.

## Test report
See `TEST_REPORT.md` for verification status. Do not report tests as passed unless executed in your environment.

## Screenshots
Add actual screenshots of the login screen, customer dashboard, and admin inventory screen under `screenshots/` after running the app. Screenshots are not included as real execution evidence in this initial delivery.

## My AI Usage
**Tool:** ChatGPT (OpenAI).

**How:** ChatGPT generated the initial backend, frontend, Docker, documentation and test scaffolding from the supplied kata. The developer must review, run, test, refine, and take responsibility for every change. Do not claim the code or TDD history was written manually when it was AI-generated.

**Reflection:** AI accelerates initial implementation and suggests edge cases, but cannot replace independently running tests, checking security, reviewing concurrency behavior, or producing authentic red/green/refactor commits. Update this reflection with your actual experience before submission.

**Commit co-authorship:** For every AI-assisted commit, append `Co-authored-by: ChatGPT <AI@users.noreply.github.com>` after two newline characters. Do not manufacture a red/green/refactor commit history; run failing tests first during subsequent changes and commit real evidence.

## Before production
Add database migrations, rate limiting, HTTPS, managed secrets, refresh-token/session strategy, and real end-to-end browser tests. This is a kata starter, not a production-certified payment system; purchasing decrements stock and does not charge money.
