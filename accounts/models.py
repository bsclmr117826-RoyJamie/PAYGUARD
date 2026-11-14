from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        DEVELOPER = "developer", "Developer"
        AUDITOR = "auditor", "Auditor"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.DEVELOPER)
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="users", null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if not self.is_superuser:
            self.is_staff = self.role == self.Role.ADMIN   # only Admins may open /admin/
        super().save(*args, **kwargs)
