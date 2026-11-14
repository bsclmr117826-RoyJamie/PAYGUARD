from django.conf import settings
from django.db import models
from django.utils import timezone


class Scan(models.Model):
    class Status(models.TextChoices):
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

    repository = models.ForeignKey("repos.Repository", on_delete=models.CASCADE, related_name="scans")
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="scans"
    )
    started_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETE)
    total_findings = models.PositiveIntegerField(default=0)
    risk_score = models.PositiveSmallIntegerField(default=0)   # 0 to 100, from scanner.calculate_risk_score

    class Meta:
        ordering = ["-started_at", "-id"]


class UploadedFile(models.Model):
    """Metadata only. The file content is never stored (decision D8)."""
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="files")
    path = models.CharField(max_length=300)
    extension = models.CharField(max_length=20)
    size_bytes = models.PositiveIntegerField()


class Finding(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = "Critical", "Critical"
        HIGH = "High", "High"
        MEDIUM = "Medium", "Medium"
        LOW = "Low", "Low"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACCEPTED = "accepted-risk", "Accepted risk"
        FIXED = "fixed", "Fixed"

    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name="findings")
    rule_code = models.CharField(max_length=20, db_index=True)
    title = models.CharField(max_length=200)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    pillar = models.CharField(max_length=30)
    technique = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    line_number = models.PositiveIntegerField()
    masked_evidence = models.CharField(max_length=120)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)


class RuleSetting(models.Model):
    """One row per rule code. A missing row means the rule is on."""
    rule_code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.rule_code
