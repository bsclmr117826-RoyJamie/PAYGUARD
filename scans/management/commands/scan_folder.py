"""python manage.py scan_folder <repo_id> <folder> --username <developer>

The only route that evaluates the project-level rule EP-001 (decision D6).
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from repos.models import Repository
from scanner import scan_directory
from scans.services import save_scan_results


class Command(BaseCommand):
    help = "Scan a folder on disk and save the result as a Scan."

    def add_arguments(self, parser):
        parser.add_argument("repo_id", type=int)
        parser.add_argument("folder")
        parser.add_argument("--username", required=True, help="Developer who owns the scan")

    def handle(self, *args, **options):
        folder = Path(options["folder"])
        if not folder.is_dir():
            raise CommandError(f"{folder} is not a folder.")
        try:
            user = User.objects.get(username=options["username"], role="developer")
            repo = Repository.objects.get(pk=options["repo_id"], organization=user.organization)
        except (User.DoesNotExist, Repository.DoesNotExist):
            raise CommandError("Unknown developer or repository in that organisation.")
        findings = scan_directory(str(folder))
        scan = save_scan_results(user=user, repository=repo, files=[], findings=findings)
        self.stdout.write(f"Scan {scan.pk}: {scan.total_findings} findings, risk score {scan.risk_score}.")
