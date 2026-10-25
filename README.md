# AutoVault Car Dealership Inventory System

AutoVault is a full stack vehicle inventory demo. Customers can create accounts, browse and filter inventory, and record a purchase that decrements stock. Administrators can add, edit, delete, and restock vehicles. A purchase records an inventory action; it does not charge money.

## Features

- JWT login and customer registration with Argon2 password hashing.
- Vehicle listing and case insensitive make, model, and category search, with price bounds.
- Admin inventory management and customer purchase access.
- SQLAlchemy persistence with PostgreSQL in Docker Compose (SQLite is the local fallback).
- Stock decrement uses a conditional database update so concurrent requests cannot reduce stock below zero.
- React interface with inventory totals, responsive vehicle cards, filters, loading/error states, and admin forms.

## Technology and architecture

- Backend: Python, FastAPI, Pydantic, SQLAlchemy, PyJWT, pwdlib/Argon2.
- Frontend: React, TypeScript, Vite, Tailwind CSS, Vitest, React Testing Library.
- Database: PostgreSQL 16 in Compose; SQLite by default for local backend use.
- `frontend/src/App.tsx` calls the REST API. FastAPI validates JWTs and roles before database operations. SQLAlchemy maps users, vehicles, and purchases.

```text
backend/app/main.py       API, schemas, auth, database models, inventory operations
backend/tests/            Pytest API and security regression tests
frontend/src/             React UI and Vitest tests
docker-compose.yml        PostgreSQL, API, and frontend services
screenshots/              Actual app screenshots (not yet captured in this environment)
PROMPTS.md                AI prompt and conversation provenance
TEST_REPORT.md            Environment-specific verification record
```

## Prerequisites

- Python 3.11 or newer and pip.
- Node.js 20 or newer and npm.
- PostgreSQL 16 for a local database, or Docker Desktop with Compose for containers.

## Docker Compose

1. Copy `.env.example` to `.env`.
2. Replace `JWT_SECRET` with at least 32 random bytes. For example, generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
3. For a non-demo deployment, replace the PostgreSQL demo credentials too and restrict network access.
4. Run `docker compose up -d --build`.
5. Visit the frontend at <http://localhost:5173> and the API docs at <http://localhost:8000/docs>. PostgreSQL is published on port 5433 for local tools.
6. Stop services with `docker compose down`. Persistent data remains in the `postgres_data` volume. Do not use `docker compose down -v` unless you intend to erase that data.

Compose requires `JWT_SECRET`; the API refuses to start with a secret shorter than 32 bytes. `.env.example` uses a conspicuous placeholder and is not a production secret.

## Run locally without Docker

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DATABASE_URL = 'postgresql+psycopg://USER:PASSWORD@localhost:5432/dealership'
$env:JWT_SECRET = 'replace-with-at-least-32-random-bytes'
uvicorn app.main:app --reload
```

For quick local evaluation without PostgreSQL, omit `DATABASE_URL`; the API uses `backend/dealership.db` (SQLite). Never use the example secret for a deployed service.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` if the API is not at `http://localhost:8000`.

## Configuration

| Variable | Purpose | Required |
| --- | --- | --- |
| `JWT_SECRET` | HS256 signing secret, at least 32 UTF-8 bytes | Yes |
| `DATABASE_URL` | SQLAlchemy database URL | No (SQLite default) |
| `CORS_ORIGINS` | Comma-separated allowed browser origins | No (`http://localhost:5173`) |
| `VITE_API_URL` | API base URL for the frontend | No (`http://localhost:8000`) |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Compose database configuration | No (demo defaults; replace for deployment) |

## API

All vehicle endpoints require `Authorization: Bearer <access_token>`. Login tokens expire after two hours.

| Method and path | Access | Description |
| --- | --- | --- |
| `POST /api/auth/register` | Public | Register a customer account; role assignment from request data is ignored. |
| `POST /api/auth/login` | Public | Verify credentials and return a JWT and role. |
| `GET /api/vehicles` | Customer or admin | List inventory. |
| `GET /api/vehicles/search` | Customer or admin | Filter by `make`, `model`, `category`, `min_price`, and `max_price`. |
| `POST /api/vehicles` | Admin | Add a vehicle. |
| `PUT /api/vehicles/{id}` | Admin | Replace vehicle fields. |
| `DELETE /api/vehicles/{id}` | Admin | Delete a vehicle. |
| `POST /api/vehicles/{id}/purchase` | Customer or admin | Decrement stock and record a purchase, or return conflict if out of stock. |
| `POST /api/vehicles/{id}/restock` | Admin | Increase stock by a positive quantity. |

Prices must be positive and have at most two decimal places. Quantities cannot be negative. Missing vehicles return 404, invalid data returns 422, duplicate registration returns 409, bad credentials/token returns 401, and customer attempts at admin routes return 403.

## Accounts and permissions

Public registration always creates a customer. The app intentionally has no public admin registration or default admin credentials. To create a local demo admin, first register normally, then update that account in your local development database:

```sql
UPDATE users SET role = 'admin' WHERE email = 'your-admin@example.com';
```

Log in again to receive a token containing the updated role. Do not expose this database operation as a public endpoint. For a real deployment, provision admin accounts through a controlled operator process.

## Tests and current verification

Run backend checks from `backend/`:

```bash
python -m pytest -v
python -m pytest --cov=app --cov-report=term-missing
```

Run frontend checks from `frontend/`:

```bash
npm test -- --run
npm run test:coverage
npm run build
```

Docker checks: `docker compose config`, `docker compose up -d --build`, and `docker compose ps`. Actual results and remaining audit findings from this workspace are recorded in [TEST_REPORT.md](TEST_REPORT.md).

## Screenshots

These are genuine captures from the running Compose application using Playwright Core with Microsoft Edge. The displayed screenshot records were clearly labeled `DEMONSTRATION ONLY`; temporary demo users, vehicles, and the purchase test row were removed after capture. Existing inventory records were preserved.

### Login

![AutoVault login page](screenshots/login.png)

### Registration

![AutoVault registration page](screenshots/registration.png)

### Vehicle inventory

![Vehicle inventory showing demonstration-only vehicles](screenshots/inventory.png)

### Search and filter

![Vehicle search filtered to a demonstration-only roadster](screenshots/search-filter.png)

### Admin inventory

![Admin inventory management showing demonstration-only vehicles](screenshots/admin-dashboard.png)

### Add vehicle form

![Admin add vehicle form](screenshots/add-vehicle.png)

### Purchase

![Successful purchase and updated demonstration stock](screenshots/purchase.png)

## Known limitations and future work

- Purchases only update inventory; there is no payment integration, cart, or purchase history UI.
- Tables are created at application startup; schema migrations are not configured.
- Admin provisioning currently requires controlled database access.
- The frontend relies on local storage for the session and role display; backend authorization remains authoritative.
- Add database migrations, rate limiting, HTTPS deployment, managed secrets, refresh/session management, and browser end-to-end testing before production use.

## Repository

<https://github.com/balaji24541-lang/autovault-car-dealership>

# My AI Usage

**AI tools used:**
- ChatGPT
- OpenAI Codex in VS Code

**How AI was used:**
- Initial project scaffolding.
- FastAPI and React implementation assistance.
- Debugging Docker and PostgreSQL issues.
- Authentication and authorization debugging.
- Automated test generation and improvements.
- Security review.
- Documentation assistance.
- Code refactoring.

**Human involvement:** The supplied project brief reports that the developer configured and ran Docker, tested the application locally, inspected results, configured Git, and pushed the repository. Those earlier actions cannot be independently verified here. During this finalization pass, Codex ran the tests, brought up the Compose stack, checked the PostgreSQL data, and captured the screenshots. The developer should review the remaining dependency advisories and supply authentic earlier conversation exports.

**Reflection:** AI accelerated scaffolding, implementation suggestions, test improvements, and documentation. Verification was necessary because generated code can miss security and edge cases; in this finalization, the test runs, PostgreSQL checks, browser flows, and screenshots exposed issues that required corrections. Human review and repeatable tests remain important, especially for the unresolved npm findings and the missing historical conversation exports.
