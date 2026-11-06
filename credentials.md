# Tech4Future-Global Management System V13 — Master Credentials Register

This document contains the complete list of seeded user accounts, roles, and credentials for the **Tech4Future-Global Management System V13**.

All accounts below have been generated, seeded into the database, and verified against both the **FastAPI Authentication Endpoint** (`/api/v1/auth/login`) and the **Django User Database**.

---

## 🚀 Access Endpoints

- **Web Platform Portal:** [http://localhost:8000/](http://localhost:8000/)
- **FastAPI Interactive API Documentation:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Django Administration Console:** [http://localhost:8000/django-admin/](http://localhost:8000/django-admin/)

---

## 🔑 Master Credentials Table

| Level / Category | Role Title | Organization | Name | Email / Username | Password | System Role | Django Admin |
|:---|:---|:---|:---|:---|:---|:---|:---:|
| **Platform Executive** | **Platform Super Admin** | Tech4Future-Global Headquarters (`t4f-hq`) | Alex Mercer | `admin@t4f-global.org` | `T4f#2027` | `platform_super_admin` | ✅ Yes |
| **Platform Executive** | **HQ High Super Admin** | Tech4Future-Global Headquarters (`t4f-hq`) | Elena Rostova | `highadmin@t4f-global.org` | `Hgh#2027` | `high_super_admin` | ✅ Yes |
| **Governance** | **Global Board Chair** | Tech4Future-Global Headquarters (`t4f-hq`) | Marcus Vance | `board.chair@t4f-global.org` | `Brd#2027` | `user` (board) | ❌ No |
| **Governance** | **Advisory Council Convener** | Tech4Future-Global Headquarters (`t4f-hq`) | Dr. Amina Touré | `advisor@t4f-global.org` | `Adv#2027` | `user` (advisory) | ❌ No |
| **Global Leadership** | **Global CTO** | Tech4Future-Global Headquarters (`t4f-hq`) | David Chen | `cto@t4f-global.org` | `Cto#2027` | `user` (global_management) | ❌ No |
| **Global Operations** | **Global Finance Manager** | Tech4Future-Global Headquarters (`t4f-hq`) | Sarah Jenkins | `finance.global@t4f-global.org` | `Fin#2027` | `user` (global_employee) | ❌ No |
| **Regional Leadership**| **Regional Coordinator (WA)** | Tech4Future-Global Headquarters (`t4f-hq`) | Kwame Mensah | `regional.westafrica@t4f-global.org` | `Reg#2027` | `user` (regional) | ❌ No |
| **Country Executive** | **Country Super Admin (Ghana)** | Tech4Future-Ghana (`t4f-ghana`) | Kofi Boateng | `director.ghana@t4f-global.org` | `Gha#2027` | `country_super_admin` | ❌ No |
| **Country Admin** | **Country IT Admin (Ghana)** | Tech4Future-Ghana (`t4f-ghana`) | Ama Osei | `it.ghana@t4f-global.org` | `Itg#2027` | `country_it_admin` | ❌ No |
| **Country Operations** | **Finance Manager (Ghana)** | Tech4Future-Ghana (`t4f-ghana`) | Emmanuel Darko | `finance.ghana@t4f-global.org` | `Cfg#2027` | `user` (country) | ❌ No |
| **Country Operations** | **Project Coordinator (Ghana)** | Tech4Future-Ghana (`t4f-ghana`) | Akua Asante | `projects.ghana@t4f-global.org` | `Prj#2027` | `user` (country) | ❌ No |
| **Country Field Staff**| **Technical Instructor (Ghana)** | Tech4Future-Ghana (`t4f-ghana`) | Yaw Appiah | `instructor.ghana@t4f-global.org` | `Trn#2027` | `user` (country) | ❌ No |
| **Volunteer Community**| **Digital Literacy Mentor (Ghana)** | Tech4Future-Ghana (`t4f-ghana`) | Abena Mensah | `volunteer.ghana@t4f-global.org` | `Vol#2027` | `user` (volunteer) | ❌ No |
| **Country Executive** | **Country Super Admin (Nigeria)**| Tech4Future-Nigeria (`t4f-nigeria`) | Chidi Okafor | `director.nigeria@t4f-global.org` | `Nga#2027` | `country_super_admin` | ❌ No |
| **Fiscal Sponsor** | **Fiscal Sponsor Authorized Officer** | FMW Nonprofit Solutions (`fmw`) | Rachel Green | `fiscal.officer@fmwsolutions.org` | `Fmw#2027` | `user` (fiscal_sponsor) | ❌ No |

---

## 👤 Account Role Profiles & Detailed Permissions

### 1. Platform Super Administrator
- **Account:** `admin@t4f-global.org` | Password: `T4f#2027`
- **Organization:** Tech4Future-Global Headquarters (`t4f-hq`)
- **Position:** Global Director, Executive Leadership
- **Permissions:** Unrestricted access across all modules, all countries, database & storage inspection, controlled policy uploads, system configuration, user provisioning, and full Django Administration console access.

### 2. HQ High Super Administrator
- **Account:** `highadmin@t4f-global.org` | Password: `Hgh#2027`
- **Organization:** Tech4Future-Global Headquarters (`t4f-hq`)
- **Position:** Global Director, Strategy & Governance
- **Permissions:** Administrative operations across Headquarters and all subordinate country offices. Can create and manage country offices, assign leadership, and view all global reports and cross-country finances. Staff access to Django Admin.

### 3. Global Board Chair
- **Account:** `board.chair@t4f-global.org` | Password: `Brd#2027`
- **Organization:** Tech4Future-Global Headquarters (`t4f-hq`)
- **Position:** Board Chair
- **Permissions:** Global governance oversight, controlled policy approvals, review workflows, high-level financial audits, and strategic reports. Read-only access to country transactional books.

### 4. Advisory Council Convener
- **Account:** `advisor@t4f-global.org` | Password: `Adv#2027`
- **Organization:** Tech4Future-Global Headquarters (`t4f-hq`)
- **Position:** Advisory Board Chair / Convener
- **Permissions:** Advisory portal, education curriculum review, safeguarding guidance, and global stakeholder reports.

### 5. Global Chief Technology Officer (CTO)
- **Account:** `cto@t4f-global.org` | Password: `Cto#2027`
- **Organization:** Tech4Future-Global Headquarters (`t4f-hq`)
- **Position:** Global Director, Technology, Data & Digital Infrastructure
- **Permissions:** Technology workspace, AI Assistance Center, digital asset governance, infrastructure health metrics, and data integrity monitoring.

### 6. Global Finance Manager
- **Account:** `finance.global@t4f-global.org` | Password: `Fin#2027`
- **Organization:** Tech4Future-Global Headquarters (`t4f-hq`)
- **Position:** Global Finance Manager
- **Permissions:** Comprehensive finance modules, master ledger review, multi-country budget approvals, grant tracking, financial audit reports, and currency reconciliations.

### 7. Regional Coordinator — West Africa
- **Account:** `regional.westafrica@t4f-global.org` | Password: `Reg#2027`
- **Organization:** Tech4Future-Global Headquarters (`t4f-hq`)
- **Position:** Regional Coordinator, West Africa
- **Permissions:** Cross-border monitoring of the 16 West African national hubs, program harmonization, regional training initiatives, and multi-country operational reporting.

### 8. Country Super Administrator — Ghana
- **Account:** `director.ghana@t4f-global.org` | Password: `Gha#2027`
- **Organization:** Tech4Future-Ghana (`t4f-ghana`)
- **Position:** Country Director
- **Permissions:** Complete operational leadership of the Ghana national office. Can create local staff accounts, approve national budgets, sign off on monthly country reports, and manage national projects.

### 9. Country IT Account Administrator — Ghana
- **Account:** `it.ghana@t4f-global.org` | Password: `Itg#2027`
- **Organization:** Tech4Future-Ghana (`t4f-ghana`)
- **Position:** IT Support Specialist
- **Permissions:** Local account creation and password assistance for Ghana office employees, local workstation inventory, and tech support ticketing.

### 10. Country Finance & Administration Manager — Ghana
- **Account:** `finance.ghana@t4f-global.org` | Password: `Cfg#2027`
- **Organization:** Tech4Future-Ghana (`t4f-ghana`)
- **Position:** Country Finance & Administration Manager
- **Permissions:** Daily expense logging, cashbook entry, local supplier invoice verification, Ghana payroll reconciliation, and local financial report generation.

### 11. Country Program & Project Coordinator — Ghana
- **Account:** `projects.ghana@t4f-global.org` | Password: `Prj#2027`
- **Organization:** Tech4Future-Ghana (`t4f-ghana`)
- **Position:** Program / Project Coordinator
- **Permissions:** Project Workspace management, sprint tasks, STEM bootcamps, participant attendance rosters, and field project milestones.

### 12. Technical Trainer & Instructor — Ghana
- **Account:** `instructor.ghana@t4f-global.org` | Password: `Trn#2027`
- **Organization:** Tech4Future-Ghana (`t4f-ghana`)
- **Position:** Technical Trainer / Instructor
- **Permissions:** Time Clock & Attendance logging, lab class scheduling, student attendance registers, and curriculum execution.

### 13. Digital Literacy Mentor & Volunteer — Ghana
- **Account:** `volunteer.ghana@t4f-global.org` | Password: `Vol#2027`
- **Organization:** Tech4Future-Ghana (`t4f-ghana`)
- **Position:** Digital Literacy Mentor
- **Permissions:** Time Clock logging, youth mentoring sessions, and assigned community tech literacy activities.

### 14. Country Super Administrator — Nigeria
- **Account:** `director.nigeria@t4f-global.org` | Password: `Nga#2027`
- **Organization:** Tech4Future-Nigeria (`t4f-nigeria`)
- **Position:** Country Director
- **Permissions:** Complete operational leadership of the Nigeria national office (Abuja hub) for cross-country workflow and governance testing.

### 15. Fiscal Sponsor Authorized Representative
- **Account:** `fiscal.officer@fmwsolutions.org` | Password: `Fmw#2027`
- **Organization:** FMW Nonprofit Solutions (`fmw`)
- **Position:** Global Director, Finance & Administration (Fiscal Officer)
- **Permissions:** Specialized Fiscal Sponsor portal, external income registers, 501(c)(3) compliance reports, grant allocation tracking, and donor governance records.

---

## 🔒 Password & Security Policy

1. **Exact 8-Character Password Requirement:**
   - The platform enforces an exact 8-character password policy (`ExactLengthValidator`).
   - Every generated password adheres to this standard (`T4f#2027`, `Hgh#2027`, etc.).
2. **First Login Reset Cleared:**
   - All seeded demo/test accounts have `must_reset=False` preconfigured so you can log in directly without being forced to change passwords immediately.
3. **Re-seeding Accounts:**
   - To re-seed or reset all accounts back to these exact credentials at any time, execute:
     ```bash
     make seed-users
     ```
     Or manually via the Django CLI:
     ```bash
     DB_ENGINE=sqlite .venv/bin/python backend/manage.py seed_all_users
     ```

