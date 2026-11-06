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
