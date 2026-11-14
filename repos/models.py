from django.conf import settings
from django.db import models


class Repository(models.Model):
    organization = models.ForeignKey(
        "accounts.Organization", on_delete=models.CASCADE, related_name="repositories"
    )
    name = models.CharField(max_length=120)
    url = models.URLField(blank=True)
    latest_risk_score = models.PositiveSmallIntegerField(default=0)   # copy of the newest scan's score
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["organization", "name"], name="unique_repo_per_org")
        ]

    def __str__(self):
        return self.name
