from dataclasses import fields

from scanner import Finding as ScannerFinding
from scans.models import Finding


def test_scanner_finding_fields_match_model():
    scanner_names = {f.name for f in fields(ScannerFinding)}
    model_names = {f.name for f in Finding._meta.get_fields() if f.concrete and not f.primary_key} - {"scan"}
    assert scanner_names == model_names
