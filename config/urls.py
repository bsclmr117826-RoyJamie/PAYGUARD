from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard:home", permanent=False)),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),   # login, logout (names: login, logout)
    path("dashboard/", include("dashboard.urls")),
    path("repos/", include("repos.urls")),
    path("scans/", include("scans.urls")),
]
