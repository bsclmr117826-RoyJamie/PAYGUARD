"""Create a demo organisation, one user per role and one repository (for local demos only)."""
import secrets

from django.core.management.base import BaseCommand

from accounts.models import Organization, User
from repos.models import Repository


class Command(BaseCommand):
    help = "Create demo data. Prints a random password once; nothing is stored in the code."

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(name="Demo Fintech Ltd")
        password = secrets.token_urlsafe(10)
        for username, role in (("dev1", "developer"), ("auditor1", "auditor"), ("admin1", "admin")):
            user, created = User.objects.get_or_create(username=username, defaults={"role": role, "organization": org})
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f"created {username} ({role})")
        Repository.objects.get_or_create(organization=org, name="payments-api", defaults={"url": ""})
        self.stdout.write(f"Password for the demo users created now: {password}")
