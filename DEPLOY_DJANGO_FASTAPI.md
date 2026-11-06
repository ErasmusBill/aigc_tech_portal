# Tech4Future-Global Django + FastAPI Deployment

## Architecture
- **Django 6.1.2**: ORM, PostgreSQL models, users, password hashing, admin, organization/role data, files, email configuration, migrations and bootstrap.
- **FastAPI 0.162.0**: mounted at `/api/v1`, serving authentication, workspace state, high-volume record reads, invitations, attendance, AI and export APIs.
- **Existing UI**: unchanged V12 `index.html`, `styles.css`, images and dashboard rendering. Only a non-visual `api-client.js` bridge was inserted before `app.js`.
- **PostgreSQL**: central durable data store. Browser localStorage remains a resilience cache, not the primary system of record when the backend is online.

## Quick start
1. Copy `.env.example` to `.env` and replace secrets/passwords.
2. Run `docker compose up --build`.
3. Open `http://localhost:8000/`.
4. Initial development credential: `admin@t4f-global.org` / `T4FGlobal@2026!` unless changed in `.env`.
5. Django administration: `http://localhost:8000/django-admin/`.
6. FastAPI interactive documentation: `http://localhost:8000/api/v1/docs`.

## Production
Use HTTPS, `COOKIE_SECURE=true`, a strong Django secret, managed PostgreSQL with TLS/backups, object storage for large files, MFA/SSO, reverse proxy/load balancer, centralized logs and secrets management.
