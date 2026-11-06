from django.contrib import admin
from django.urls import path, re_path
from platform_core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("django-admin/", admin.site.urls),
    path("", views.frontend_index, name="frontend-index"),
    path("styles.css", views.frontend_file, {"relative_path": "styles.css"}),
    path("app.js", views.frontend_file, {"relative_path": "app.js"}),
    path("api-client.js", views.frontend_file, {"relative_path": "api-client.js"}),
    path("hierarchy-data.js", views.frontend_file, {"relative_path": "hierarchy-data.js"}),
    re_path(r"^assets/(?P<relative_path>.+)$", views.frontend_asset),
]
