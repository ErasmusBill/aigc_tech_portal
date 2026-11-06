# Tech4Future-Global Management System V9 — Change Log

## Reliability
- Added safe Edit/Delete controls to Accounts, Organizations, Projects, Reports, Finance and Budgets.
- Added record-sensitive retention rules instead of unsafe hard deletion.
- Added a running Interface Self-Test in Database & Storage.
- Added automated static dashboard/action validation script.

## Readability
- Added black/dark text on light surfaces.
- Added forced white text on navy/blue/gradient surfaces.
- Improved form text size, table text, placeholders, focus outlines and status-pill contrast.
- Improved dense record readability.

## AI Assistance Center
- Added Word / Excel format selection.
- Added automatic Word-vs-Excel recommendation.
- Added real DOCX/XLSX export service in server mode.
- Added standalone DOC/XLS fallback.
- Added My AI Files library.
- Added Download/Delete actions for AI files.
- Added export of saved AI History to Word or Excel.
- Added automatic AI file preservation when the AI modal closes.

## Database & Storage
- Added PostgreSQL architecture.
- Added Database & Storage dashboard.
- Added database health/status.
- Added manual platform sync and snapshot restore.
- Added sanitized JSON backup.
- Added flexible JSONB high-volume record store.
- Added core normalized tables.
- Added JSONB, organization, country, user, project, status and date indexes.
- Added Row-Level Security foundations.
- Added bulk record API and paged record query API.
- Added configurable snapshot maximum size and retention.
- Added database sync token.
- Removed browser passwords and active PINs before DB sync/backups.

## Server
- Added `server/db.mjs`.
- Added `server/exports.mjs`.
- Added PostgreSQL, DOCX and XLSX dependencies.
- Blocked `/server` and `/database` from static web browsing.
- Increased configurable JSON payload capacity for admin synchronization.
