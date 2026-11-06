# Tech4Future-Global Management System V12

V12 is the **working-login release** of the Tech4Future-Global Management Platform.

## Initial Platform Super Administrator

The account below is physically seeded into the V12 browser database and is no longer just a suggested credential.

**Organization:** Tech4Future-Global Headquarters  
**Email:** `admin@t4f-global.org`  
**Initial password:** `T4FGlobal@2026!`

The login page also includes **Use Initial Super Admin**, which fills the organization, email and initial password automatically.

On the first successful login, the account is forced to set a new password. After that change, the new password becomes the valid credential.

## Migration from V11

When V12 opens and imports an older V11 workspace, it checks whether the V12 initial-access credential has ever been issued. If not, V12 creates or repairs the `admin@t4f-global.org` Platform Super Administrator account once. This allows the known V12 credential to work even when older browser data exists.

The bootstrap password is not continuously reset. Once the first-login password change is completed, V12 records the credential as consumed.

## Existing platform features

V12 retains the V11 repaired dashboard actions and the broader platform functions developed in earlier releases, including:
- active dashboard navigation and Add/Edit/Delete/Invite controls
- Time Clock & Attendance
- projects/programmes and project workspaces
- advanced reports
- AI Assistance Center
- Controlled Policy & Governance Library
- Board and Advisory portals
- country portals and leadership directory
- financial management/bookkeeping/budgets
- stakeholder and fiscal-visibility dashboards
- PostgreSQL/database architecture
- Word/Excel exports
- account invitations and email workflows

## Security note

The browser prototype still stores account credentials locally for prototype authentication. Before live deployment, replace browser-password authentication with server-side identity, password hashing, MFA/SSO, session management and server-enforced authorization.
# aigc_tech_portal
