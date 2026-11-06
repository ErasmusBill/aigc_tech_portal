# Tech4Future-Global Management System V12 — Login Validation

- **PASS** — `app.js` syntax
- **PASS** — `server/server.mjs` syntax
- **PASS** — `server/db.mjs` syntax
- **PASS** — `server/exports.mjs` syntax
- **PASS** — `tests/validate-v11.mjs` syntax
- **PASS** — `tests/validate-v12.mjs` syntax

## Initial credential validation

```text
PASS  V12 database key active
PASS  initial admin email is seeded
PASS  initial admin password is seeded
PASS  initial account has Platform Super Admin role
PASS  clean V12 seed contains the initial account
PASS  V11 migration repair for initial account is active
PASS  bootstrap credential is consumed after password change
PASS  login quick-fill button is present
PASS  login quick-fill function is defined
PASS  login quick-fill action is exported
PASS  login organization exists
PASS  initial admin position exists
PASS  exact supplied credential satisfies V12 login predicate

All V12 initial-login checks passed.
```

The exact V12 initial credential is seeded into the database, the Headquarters organization exists, the assigned position exists, and the credential satisfies the same organization/email/password/status predicate used by the login form.
