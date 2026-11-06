# Tech4Future-Global Management System V13 — Django + FastAPI Rewrite

## UI preservation
The V12 visual interface is preserved. No redesign was applied to the dashboards, colors, spacing, typography, cards, navigation, logo, hierarchy image, forms, or dashboard layout.

- `styles.css` is byte-for-byte identical to V12.
- `assets/t4f-global-logo.jpg` is byte-for-byte identical to V12.
- `assets/leadership-hierarchy-reference.png` is byte-for-byte identical to V12.
- `index.html` differs only by loading the nonvisual `api-client.js` bridge before `app.js`.

## New backend architecture

### Django
Django is the system-of-record layer for:
- users and secure password hashing
- organizations and positions/TOR identity mapping
- role/system-control metadata
- PostgreSQL ORM and migrations
- workspace persistence
- generic high-volume records
- files and metadata
- invitations and email
- immutable-style audit event storage foundation
- Django administration

### FastAPI
FastAPI is mounted at `/api/v1` and provides:
- login, current user, logout and password change
- workspace state load/save
- generic paginated record APIs
- user/invitation APIs
- attendance event API
- protected file upload/download API
- AI assistance endpoint
- Word/Excel AI export API
- database/system health endpoints

### PostgreSQL
PostgreSQL is the production database. SQLite is retained only as a development/test fallback.

## Browser behavior
The existing `app.js` still renders the same UI and retains a local browser cache for resilience. When the Django/FastAPI backend is available:
1. login authenticates through Django;
2. FastAPI returns the session token;
3. the workspace state is loaded from the server;
4. existing dashboard changes are saved locally and synchronized to PostgreSQL in the background;
5. account passwords are hashed by Django before state persistence;
6. passwords and document PINs are stripped from stored workspace snapshots.

## Initial development login
Organization: Tech4Future-Global Headquarters  
Email: `admin@t4f-global.org`  
Default development password: `T4FGlobal@2026!`

Change `INITIAL_ADMIN_PASSWORD` before any real deployment.

## Run with Docker
```bash
cp .env.example .env
# edit .env and replace all secrets/passwords
docker compose up --build
```

Open:
- Platform: `http://localhost:8000/`
- FastAPI docs: `http://localhost:8000/api/v1/docs`
- Django admin: `http://localhost:8000/django-admin/`

## Backend source
- `backend/t4f_backend/` — Django settings, URLs, ASGI composition
- `backend/platform_core/` — Django models, services, admin, migrations and bootstrap
- `backend/api/` — FastAPI application, dependencies, schemas and routers
- `backend/tests/` — Django service tests
- `api-client.js` — nonvisual frontend-to-backend bridge
- `docker-compose.yml` — PostgreSQL + application deployment

## Production requirements
Before live production use:
- set strong Django and PostgreSQL secrets;
- use managed PostgreSQL with TLS, backups and point-in-time recovery;
- set `COOKIE_SECURE=true` and deploy only over HTTPS;
- use MFA/SSO or another centralized identity provider;
- use private object storage for large controlled/financial files;
- add malware scanning and retention policies;
- configure SMTP or transactional email;
- configure real AI provider credentials server-side only;
- use reverse proxy/load balancer, structured logs, monitoring and alerting;
- complete browser acceptance testing on the actual HTTPS staging environment.
