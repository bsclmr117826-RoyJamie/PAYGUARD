from django.urls import path

from . import views

app_name = "repos"
urlpatterns = [
    path("", views.list_view, name="list"),
    path("new/", views.create, name="create"),
]
