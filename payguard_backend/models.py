# payguard_backend/models.py
from django.db import models
from django.contrib.auth.models import User

class Organization(models.Model):
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

class Repository(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    url = models.URLField()
    risk_score = models.IntegerField(default=0)

class SITFPillar(models.Model):
    name = models.CharField(max_length=50) # Endpoint/IDE, VCS, CI/CD, Registry, Production

class SITFTechnique(models.Model):
    pillar = models.ForeignKey(SITFPillar, on_delete=models.CASCADE)
    technique_id = models.CharField(max_length=20)
    name = models.CharField(max_length=200)

class Scan(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    total_findings = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='COMPLETED')

class Finding(models.Model):
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=500)
    line_number = models.IntegerField()
    severity = models.CharField(max_length=20) # CRITICAL, HIGH, MEDIUM, LOW
    masked_evidence = models.CharField(max_length=255)
    rule_code = models.CharField(max_length=50)