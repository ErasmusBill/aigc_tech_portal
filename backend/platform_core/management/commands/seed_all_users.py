import json
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from platform_core.models import Organization, PlatformProfile, Position, WorkspaceState

SEED_ACCOUNTS = [
    {
        "id": "t4f-initial-platform-super-admin",
        "name": "Alex Mercer",
        "first_name": "Alex",
        "last_name": "Mercer",
        "email": "admin@t4f-global.org",
        "password": "T4f#2027",
        "org_id": "t4f-hq",
        "position_id": "global-director-executive-leadership",
        "system_role": "platform_super_admin",
        "country": "United States",
        "bio": "Platform Super Administrator with complete enterprise control.",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "id": "t4f-user-hq-high-super-admin",
        "name": "Elena Rostova",
        "first_name": "Elena",
        "last_name": "Rostova",
        "email": "highadmin@t4f-global.org",
        "password": "Hgh#2027",
        "org_id": "t4f-hq",
        "position_id": "global-director-strategy-governance",
        "system_role": "high_super_admin",
        "country": "Switzerland",
        "bio": "HQ High Super Administrator for global governance and country structures.",
        "is_staff": True,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-global-board-chair",
        "name": "Marcus Vance",
        "first_name": "Marcus",
        "last_name": "Vance",
        "email": "board.chair@t4f-global.org",
        "password": "Brd#2027",
        "org_id": "t4f-hq",
        "position_id": "board-chair",
        "system_role": "user",
        "country": "United Kingdom",
        "bio": "Global Board of Directors Chair overseeing governance and fiduciary policies.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-advisory-convener",
        "name": "Dr. Amina Touré",
        "first_name": "Amina",
        "last_name": "Touré",
        "email": "advisor@t4f-global.org",
        "password": "Adv#2027",
        "org_id": "t4f-hq",
        "position_id": "advisory-board-chair-convener",
        "system_role": "user",
        "country": "Senegal",
        "bio": "Advisory Board Chair providing strategic guidance on international education programs.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-global-cto",
        "name": "David Chen",
        "first_name": "David",
        "last_name": "Chen",
        "email": "cto@t4f-global.org",
        "password": "Cto#2027",
        "org_id": "t4f-hq",
        "position_id": "global-director-technology-data-digital-infrastructure",
        "system_role": "user",
        "country": "Canada",
        "bio": "Global Director of Technology, Data & Digital Infrastructure.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-global-finance-mgr",
        "name": "Sarah Jenkins",
        "first_name": "Sarah",
        "last_name": "Jenkins",
        "email": "finance.global@t4f-global.org",
        "password": "Fin#2027",
        "org_id": "t4f-hq",
        "position_id": "global-finance-manager",
        "system_role": "user",
        "country": "United States",
        "bio": "Global Finance Manager leading enterprise budgets, ledgers, and audit compliance.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-regional-coord-wa",
        "name": "Kwame Mensah",
        "first_name": "Kwame",
        "last_name": "Mensah",
        "email": "regional.westafrica@t4f-global.org",
        "password": "Reg#2027",
        "org_id": "t4f-hq",
        "position_id": "regional-coordinator-west-africa",
        "system_role": "user",
        "country": "Ghana",
        "bio": "Regional Coordinator for West Africa multi-country office operations.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-country-director-ghana",
        "name": "Kofi Boateng",
        "first_name": "Kofi",
        "last_name": "Boateng",
        "email": "director.ghana@t4f-global.org",
        "password": "Gha#2027",
        "org_id": "t4f-ghana",
        "position_id": "country-director",
        "system_role": "country_super_admin",
        "country": "Ghana",
        "bio": "Country Director for Tech4Future-Ghana.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-it-admin-ghana",
        "name": "Ama Osei",
        "first_name": "Ama",
        "last_name": "Osei",
        "email": "it.ghana@t4f-global.org",
        "password": "Itg#2027",
        "org_id": "t4f-ghana",
        "position_id": "it-support-specialist",
        "system_role": "country_it_admin",
        "country": "Ghana",
        "bio": "IT Account Administrator managing local accounts and workstation infrastructure.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-finance-ghana",
        "name": "Emmanuel Darko",
        "first_name": "Emmanuel",
        "last_name": "Darko",
        "email": "finance.ghana@t4f-global.org",
        "password": "Cfg#2027",
        "org_id": "t4f-ghana",
        "position_id": "country-finance-administration-manager",
        "system_role": "user",
        "country": "Ghana",
        "bio": "Country Finance & Administration Manager responsible for Ghana office ledgers.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-projects-ghana",
        "name": "Akua Asante",
        "first_name": "Akua",
        "last_name": "Asante",
        "email": "projects.ghana@t4f-global.org",
        "password": "Prj#2027",
        "org_id": "t4f-ghana",
        "position_id": "program-project-coordinator",
        "system_role": "user",
        "country": "Ghana",
        "bio": "Program & Project Coordinator managing youth coding bootcamps and field tasks.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-instructor-ghana",
        "name": "Yaw Appiah",
        "first_name": "Yaw",
        "last_name": "Appiah",
        "email": "instructor.ghana@t4f-global.org",
        "password": "Trn#2027",
        "org_id": "t4f-ghana",
        "position_id": "technical-trainer-instructor",
        "system_role": "user",
        "country": "Ghana",
        "bio": "Technical Trainer and Instructor delivering hardware and robotics curricula.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-volunteer-ghana",
        "name": "Abena Mensah",
        "first_name": "Abena",
        "last_name": "Mensah",
        "email": "volunteer.ghana@t4f-global.org",
        "password": "Vol#2027",
        "org_id": "t4f-ghana",
        "position_id": "digital-literacy-mentor",
        "system_role": "user",
        "country": "Ghana",
        "bio": "Community digital literacy mentor volunteering in community tech labs.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-country-director-nigeria",
        "name": "Chidi Okafor",
        "first_name": "Chidi",
        "last_name": "Okafor",
        "email": "director.nigeria@t4f-global.org",
        "password": "Nga#2027",
        "org_id": "t4f-nigeria",
        "position_id": "country-director",
        "system_role": "country_super_admin",
        "country": "Nigeria",
        "bio": "Country Director for Tech4Future-Nigeria office.",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "id": "t4f-user-fiscal-sponsor-fmw",
        "name": "Rachel Green",
        "first_name": "Rachel",
        "last_name": "Green",
        "email": "fiscal.officer@fmwsolutions.org",
        "password": "Fmw#2027",
        "org_id": "fmw",
        "position_id": "global-director-finance-administration",
        "system_role": "user",
        "country": "United States",
        "bio": "Authorized Representative from FMW Nonprofit Solutions (Fiscal Sponsor).",
        "is_staff": False,
        "is_superuser": False,
    },
]

class Command(BaseCommand):
    help = "Seed comprehensive accounts for all user and stakeholder roles across the platform."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding comprehensive platform users..."))

        ws, _ = WorkspaceState.objects.get_or_create(key="t4f-global", defaults={"state": {}, "revision": 1})
        state = ws.state or {}
        users_list = state.get("users", [])
        existing_ws_by_email = {u.get("email", "").lower(): u for u in users_list if u.get("email")}

        seeded_count = 0

        for a in SEED_ACCOUNTS:
            email = a["email"].strip().lower()
            org = Organization.objects.filter(pk=a["org_id"]).first()
            if not org:
                org = Organization.objects.create(
                    id=a["org_id"],
                    name=a["org_id"],
                    organization_type="organization",
                    status="Active",
                )

            pos = Position.objects.filter(pk=a["position_id"]).first()

            user, _ = User.objects.get_or_create(
                username=email,
                defaults={
                    "email": email,
                    "first_name": a["first_name"],
                    "last_name": a["last_name"],
                    "is_staff": a["is_staff"],
                    "is_superuser": a["is_superuser"],
                    "is_active": True,
                },
            )
            user.email = email
            user.first_name = a["first_name"]
            user.last_name = a["last_name"]
            user.is_staff = a["is_staff"]
            user.is_superuser = a["is_superuser"]
            user.is_active = True
            user.set_password(a["password"])
            user.save()

            PlatformProfile.objects.update_or_create(
                user=user,
                defaults={
                    "platform_user_id": a["id"],
                    "organization": org,
                    "position": pos,
                    "system_role": a["system_role"],
                    "status": "Active",
                    "must_reset": False,
                    "profile_data": {
                        "country": a["country"],
                        "bio": a["bio"],
                    },
                },
            )

            # Update or create in WorkspaceState state['users']
            ws_user = existing_ws_by_email.get(email)
            user_data = {
                "id": a["id"],
                "orgId": a["org_id"],
                "name": a["name"],
                "email": email,
                "password": a["password"],
                "systemRole": a["system_role"],
                "positionId": a["position_id"],
                "status": "Active",
                "mustReset": False,
                "profile": {
                    "country": a["country"],
                    "bio": a["bio"],
                },
            }
            if ws_user:
                ws_user.update(user_data)
            else:
                users_list.append(user_data)
                existing_ws_by_email[email] = user_data

            # Verify Django authentication works
            auth_ok = authenticate(username=email, password=a["password"])
            if not auth_ok:
                self.stderr.write(self.style.ERROR(f"Failed authentication verification for {email}"))
            else:
                seeded_count += 1
                self.stdout.write(self.style.SUCCESS(f"  [OK] {a['name']:<25} ({a['system_role']:<22}) -> {email}"))

        state["users"] = users_list
        ws.state = state
        ws.revision = (ws.revision or 1) + 1
        ws.save()

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully seeded and verified {seeded_count} user accounts."))

