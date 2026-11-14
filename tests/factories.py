from accounts.models import Organization, User
from repos.models import Repository


def make_org(name="Org A"):
    return Organization.objects.create(name=name)


def make_user(org, role="developer", username=None):
    username = username or f"{role}-{org.pk}"
    return User.objects.create_user(username=username, password="pw-for-tests-only", role=role, organization=org)


def make_repo(org, name="payments-api"):
    return Repository.objects.create(organization=org, name=name)
