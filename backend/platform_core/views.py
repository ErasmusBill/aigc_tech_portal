from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404

ROOT = settings.PROJECT_ROOT

def _safe_path(relative_path: str) -> Path:
    p = (ROOT / relative_path).resolve()
    if ROOT.resolve() not in p.parents and p != ROOT.resolve():
        raise Http404
    if not p.is_file():
        raise Http404
    return p

def frontend_index(request):
    return FileResponse(open(_safe_path("index.html"), "rb"), content_type="text/html; charset=utf-8")

def frontend_file(request, relative_path):
    content_types={".css":"text/css; charset=utf-8", ".js":"application/javascript; charset=utf-8"}
    p=_safe_path(relative_path)
    return FileResponse(open(p,"rb"), content_type=content_types.get(p.suffix,"application/octet-stream"))

def frontend_asset(request, relative_path):
    p=_safe_path(f"assets/{relative_path}")
    return FileResponse(open(p,"rb"))

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail

logger = logging.getLogger("platform_core.email")

@csrf_exempt
def send_email_api(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception as exc:
        return JsonResponse({"ok": False, "error": f"Invalid JSON payload: {exc}"}, status=400)

    to_addr = data.get("to")
    subject = data.get("subject", "Tech4Future-Global Notification")
    text_content = data.get("text") or data.get("message") or ""
    html_content = data.get("html")

    if not to_addr:
        return JsonResponse({"ok": False, "error": "Recipient email ('to') is required"}, status=400)

    try:
        recipient_list = [to_addr] if isinstance(to_addr, str) else list(to_addr)
        sent = send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
            html_message=html_content,
        )
        return JsonResponse({"ok": True, "message": f"Email successfully delivered to {to_addr}", "sent_count": sent})
    except Exception as exc:
        logger.error(f"Failed to deliver email to {to_addr}: {exc}", exc_info=True)
        return JsonResponse({"ok": False, "error": str(exc)}, status=500)

