# V13 Hybrid Architecture

```text
Browser — existing V12 UI (unchanged visual design)
    |
    | HTTPS / JSON / Bearer token
    v
FastAPI /api/v1
    |-- Auth endpoints -> Django authentication/password hashing
    |-- Workspace/records -> Django ORM
    |-- Users/invitations -> Django ORM + email
    |-- Attendance -> Django ORM
    |-- Files -> Django storage
    |-- AI / Word / Excel exports -> Python services
    |
    v
Django platform_core
    |-- Organization
    |-- Position
    |-- PlatformProfile
    |-- ApiSession
    |-- WorkspaceState
    |-- PlatformRecord
    |-- AuditEvent
    |-- FileObject
    |-- Invitation
    |
    v
PostgreSQL
```

The root ASGI application is FastAPI. It mounts the FastAPI application at `/api/v1` and the Django ASGI application at `/`. This provides one origin and avoids changing the existing UI URLs.
