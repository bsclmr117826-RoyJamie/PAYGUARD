from django.shortcuts import get_object_or_404

from .models import Repository


def repositories_for_user(user):
    """Whole organisation, all roles."""
    return Repository.objects.filter(organization=user.organization)


def get_repository_for_user(user, repo_id):
    """404 if the repository is not in the user's organisation."""
    return get_object_or_404(repositories_for_user(user), pk=repo_id)
