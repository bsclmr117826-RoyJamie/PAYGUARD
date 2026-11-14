from django.urls import path

from . import views

app_name = "scans"
urlpatterns = [
    path("new/", views.upload, name="upload"),
    path("<int:scan_id>/", views.detail, name="detail"),
    path("<int:scan_id>/findings/<int:finding_id>/status/", views.finding_status, name="finding_status"),
    path("<int:scan_id>/export.csv", views.export_csv, name="export"),
]
