from django.shortcuts import redirect, render

from accounts.permissions import ADMIN, AUDITOR, DEVELOPER, role_required

from .forms import RepositoryForm
from .selectors import repositories_for_user


@role_required(DEVELOPER, AUDITOR, ADMIN)
def list_view(request):
    return render(request, "repos/list.html", {"repositories": repositories_for_user(request.user)})


@role_required(DEVELOPER)
def create(request):
    form = RepositoryForm(request.POST or None, organization=request.user.organization)
    if request.method == "POST" and form.is_valid():
        repo = form.save(commit=False)
        repo.organization = request.user.organization
        repo.created_by = request.user
        repo.save()
        return redirect("repos:list")
    return render(request, "repos/form.html", {"form": form})
