import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "t4f_backend.settings")
import django
django.setup()
from django.core.asgi import get_asgi_application
from fastapi import FastAPI
from api.main import api_app

django_application = get_asgi_application()
application = FastAPI(title="Tech4Future-Global Hybrid Platform", docs_url=None, redoc_url=None, openapi_url=None)
application.mount("/api/v1", api_app)
application.mount("/", django_application)
