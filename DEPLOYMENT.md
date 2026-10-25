# AutoVault deployment reference

AutoVault is deployed for public demonstration:

- Frontend: [https://autovault-car-dealership.vercel.app/](https://autovault-car-dealership.vercel.app/) (Vercel Hobby)
- Backend: [https://autovault-api-5on9.onrender.com](https://autovault-api-5on9.onrender.com) (Render web service)
- API docs: [https://autovault-api-5on9.onrender.com/docs](https://autovault-api-5on9.onrender.com/docs)
- Database: Render-managed PostgreSQL, referenced by backend-only `DATABASE_URL`.

The browser frontend calls the API over HTTPS. Render CORS is restricted to the production Vercel origin. The hosted API accepts Render's PostgreSQL URL forms and normalizes them for the installed psycopg 3 driver. On startup, additive SQLAlchemy table creation and the idempotent demo seed preserve existing tables, rows, passwords, roles, and changed inventory quantities.

## Provider configuration

The repository contains `render.yaml` for the Render web service/database and `frontend/vercel.json` for the Vite build. Expected settings:

| Setting | Where | Notes |
| --- | --- | --- |
| `DATABASE_URL` | Render backend | Supplied by the managed PostgreSQL resource; never put it in Vercel or Git. |
| `JWT_SECRET` | Render backend | Generated and stored as a secret by Render; keep private. |
| `CORS_ORIGINS` | Render backend | `https://autovault-car-dealership.vercel.app` |
| `DEMO_CUSTOMER_EMAIL`, `DEMO_CUSTOMER_PASSWORD` | Render backend | Configured privately for the seeded demo customer. Customer login details are shared privately with evaluators, not in Git. |
| `DEMO_ADMIN_EMAIL`, `DEMO_ADMIN_PASSWORD` | Render backend | Backend-only provisioning. Privileged credentials are not published or shared with evaluators. |
| `VITE_API_URL` | Vercel production build | `https://autovault-api-5on9.onrender.com`; public API origin only, no credentials. |

The app also supports public customer registration. Registration assigns only the customer role. The seed process refuses to change the role or reset the password of an existing seeded account. Demo customer credentials should be delivered privately by the project owner/interviewer; this repository intentionally does not contain those passwords or privileged admin credentials.

## Free-tier notes

The current deployment uses Vercel Hobby, Render free web service, and Render free PostgreSQL as selected by the owner. Free services can sleep or have usage limits; Render's free PostgreSQL database expires after 30 days. Monitor the provider dashboard and preserve/export any data needed before expiry. Do not upgrade to a paid plan without the owner's approval.

## Local developer setup

For local development, see the Docker Compose and Python/Node setup in [README.md](README.md). Local-only defaults and the Vite API proxy are documented there. Never copy local database credentials or JWT secrets into hosting frontend settings.
