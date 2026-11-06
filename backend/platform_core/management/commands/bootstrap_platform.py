import csv, json, os, re
from pathlib import Path
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from platform_core.models import Organization, PlatformProfile, Position, WorkspaceState

class Command(BaseCommand):
    help = "Seed Tech4Future-Global organizations, positions, initial administrator, and initial workspace state."

    @transaction.atomic
    def handle(self, *args, **options):
        root = Path(__file__).resolve().parents[4]
        data_js = (root / "hierarchy-data.js").read_text(encoding="utf-8")
        prefix = "window.T4F_DATA = "
        data = json.loads(data_js[len(prefix):].strip().rstrip(";"))
        for o in data.get("organizations", []):
            Organization.objects.update_or_create(id=o["id"], defaults={
                "name":o.get("name") or o["id"], "organization_type":o.get("type") or "organization",
                "country":o.get("country") or "", "parent_id":o.get("parentId") or "",
                "status":o.get("status") or "Active", "contact":o.get("contact") or {}, "metadata":o,
            })
        pos_csv = root / "POSITION_REGISTER.csv"
        with pos_csv.open(newline="",encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                Position.objects.update_or_create(id=r["Position ID"], defaults={
                    "title":r["Position"], "family":r["Family"], "group":r["Group"],
                    "reports_to":r["Reports To"], "role_purpose":r["Role Purpose"], "metadata":r,
                })
        email=os.getenv("INITIAL_ADMIN_EMAIL","admin@t4f-global.org").strip().lower()
        password=os.getenv("INITIAL_ADMIN_PASSWORD","T4FGlobal@2026!")
        name=os.getenv("INITIAL_ADMIN_NAME","Tech4Future-Global Super Administrator")
        user,_=User.objects.get_or_create(username=email, defaults={"email":email,"is_staff":True,"is_superuser":True})
        user.email=email; user.is_active=True; user.is_staff=True; user.is_superuser=True
        parts=name.split(" ",1); user.first_name=parts[0]; user.last_name=parts[1] if len(parts)>1 else ""; user.set_password(password); user.save()
        org=Organization.objects.get(pk="t4f-hq")
        pos=Position.objects.filter(pk="global-director-executive-leadership").first()
        PlatformProfile.objects.update_or_create(user=user, defaults={
            "platform_user_id":"t4f-initial-platform-super-admin", "organization":org, "position":pos,
            "system_role":"platform_super_admin", "status":"Active", "must_reset":True,
            "profile_data":{"country":"United States","bio":"Initial Platform Super Administrator account."},
        })
        seed_state={
            "organizations":data.get("organizations",[]), "users":[{
                "id":"t4f-initial-platform-super-admin","orgId":"t4f-hq","name":name,"email":email,
                "systemRole":"platform_super_admin","positionId":"global-director-executive-leadership",
                "status":"Active","mustReset":True,"profile":{"country":"United States"}
            }],
            "documents":data.get("documents",[]), "projects":[],"projectTasks":[],"reports":[],"financeRecords":[],
            "ledger":[],"budgets":[],"timeEntries":[],"attendanceReports":[],"audit":[],"requests":[],"grants":[],
            "contributions":[],"programs":[],"documentReviews":[],"documentVersions":[],"reportReviews":[],
            "projectDocuments":[],"aiHistory":[],"aiFiles":[],"emailLog":[],
            "settings":{"version":"13.0","backend":"django-fastapi","controlledLibrarySource":"T4FG-LIB-004 v2.0"},
        }
        WorkspaceState.objects.update_or_create(key="t4f-global", defaults={"state":seed_state,"revision":1,"last_saved_by":user})
        self.stdout.write(self.style.SUCCESS(f"Platform bootstrapped. Initial administrator: {email}"))
