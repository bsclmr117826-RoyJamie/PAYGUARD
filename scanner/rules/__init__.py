"""Rule registry. To add a rule: write its check function, then add one Rule(...) below
and one line in scanner/sitf.py."""
from scanner.models import Rule
from scanner.rules import cicd, production, registry, secrets

ALL_RULES = [
    # --- VCS (MVP secret rules) ---
    Rule("VCS-001", "Hardcoded Daraja consumer key/secret", "Critical",
         lambda path: True, secrets.check_daraja_consumer),
    Rule("VCS-002", "Hardcoded Daraja passkey", "Critical",
         lambda path: True, secrets.check_daraja_passkey),
    Rule("VCS-003", "Hardcoded API token or secret key", "Critical",
         lambda path: True, secrets.check_hardcoded_token),
    # --- CI/CD ---
    Rule("CICD-001", "GitHub Action not pinned to a commit SHA", "High",
         cicd.is_workflow, cicd.check_unpinned_actions),
    Rule("CICD-002", "Risky pull_request_target use", "High",
         cicd.is_workflow, cicd.check_pull_request_target),
    Rule("CICD-003", "Over-broad workflow permissions (write-all)", "High",
         cicd.is_workflow, cicd.check_write_all_permissions),
    # --- Registry ---
    Rule("REG-001", "Dependency not pinned to an exact version", "Medium",
         registry.is_requirements, registry.check_unpinned_dependencies),
    # --- Production ---
    Rule("PROD-001", "DEBUG enabled", "High",
         production.is_debug_file, production.check_debug_enabled),
    Rule("PROD-002", "HTTP instead of HTTPS for a service URL", "High",
         production.is_config_file, production.check_http_endpoint),
]
# The 10th rule, EP-001 (Endpoint / IDE), is project-level: see rules/endpoint.py
