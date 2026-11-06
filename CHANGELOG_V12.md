# V12 Change Log — Login Credential Repair

- Added a real initial Platform Super Administrator account to the V12 seed database.
- Added one-time migration repair so V11 browser data cannot prevent the V12 initial credential from working.
- Added `Use Initial Super Admin` login button.
- Added explicit first-login forced password change.
- Records when the bootstrap credential is consumed so the initial password is not re-applied after the user changes it.
- Improved invalid-login guidance.
- Preserved all V11 dashboard/runtime repairs.
