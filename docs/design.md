# PayGuard Design Document

**Architecture, interface contracts and build instructions**

BCS 3106 Software Engineering group project. Version 1.0, 5 November 2026. Document owner: R1 (Project Manager). Diagram owner: R5. This is the baseline for the rebuild. Any later change is recorded in the decision log (section 9.4).

## 0. About this document

This document is the single source of truth for how the five PayGuard modules fit together. If code and this document disagree, the document wins until the team changes it through the decision log.

**How to read it:** read sections 1 to 3 (about 15 minutes), then your own module brief in section 10, then only the contract sections that brief points to.

**Conventions**

1. Each module owns the files listed for it in section 3.5 and section 10. Do not edit files owned by another module.
2. Names, field names, types, URLs and function signatures in sections 4 and 5 are exact. Do not rename, add or remove fields without a decision log entry.
3. The dependency rules in section 3.3 apply to every module.
4. Evidence is always masked. A full secret is never printed, logged or stored (section 6).

|Section|What it contains|
|---|---|
|1|Purpose, scope, decisions already made|
|2|How the course readings shaped the design|
|3|Architecture: layers, modules, dependency rules, repository layout, decisions|
|4|Data design: exact Django models|
|5|Interface contracts: scanner, services, charts, permissions, URLs, templates|
|6|Security design|
|7|Testing and CI|
|8|Traceability chain from use case to test|
|9|Integration plan, gates, decision log|
|10|One build brief per team role|
|11|Differences from the Part 1 diagrams and the earlier RTM|
|12|References|

## 1. Purpose, scope and decisions

### 1.1 What PayGuard does

PayGuard is a Django web application for fintech development teams. A developer uploads files from a repository (source, configuration, CI workflows, dependency lists). PayGuard scans them with a rule engine, maps every finding to a pillar and technique of the SDLC Infrastructure Threat Framework (SITF), stores the result, and shows risk on a dashboard built with Matplotlib. The five SITF pillars are Endpoint / IDE, VCS, CI/CD, Registry and Production.

### 1.2 Scope of the rebuild

**In scope:** login with three roles (Developer, Auditor, Admin); register a repository; upload files and run a scan; 10 detection rules; SITF mapping; risk score; saved scan history; dashboard with severity, pillar, trend and top-rules charts; update a finding's status; user and rule management through the Django admin site; automated tests in CI.

**Out of scope:** live payment processing, scanning production servers, automatic code fixing, mobile apps, GitHub API integration, ZIP upload.

**Cut order if time runs out** (cut from the top, never from the bottom): 1) CSV export, 2) top-rules chart, 3) trend chart, 4) finding status update. Everything else is the minimum product.

### 1.3 What is kept from earlier work

- The `scanner` package (rule engine, SITF mapper, scoring). It has 32 passing tests and no Django dependency. It is reused as it is and treated as a finished contract (section 5.1).
- The Part 1 use case diagram and class diagram, with the differences listed in section 11.
- The requirement IDs R1 to R13 and test case IDs TC-01 to TC-14 from the traceability matrix.

The earlier Django code was rejected because the parts did not work together. The cause, as best we know it, is that modules were built in parallel against different assumptions and joined at the end. This design removes that cause by fixing every boundary first (section 5) and by building a working end-to-end skeleton before any feature (section 9).

### 1.4 Decisions made now so nobody is blocked

Each decision has a default that everyone builds against. Changing one needs a decision log entry (section 9.4).

|ID|Decision|Default|Owner|
|---|---|---|---|
|D1|Risk score|Sum of severity weights (Critical 10, High 5, Medium 2, Low 1), capped at 100. Implemented in `scanner/scoring.py`.|R3|
|D2|SITF technique names|Placeholders in `scanner/sitf.py` until the official names are copied in. Tests only check that every rule is mapped.|R3|
|D3|Who sees what|Developer sees scans they started. Auditor and Admin see all scans in their own organisation. Nobody sees another organisation's data.|R2|
|D4|Database|SQLite for development and tests, PostgreSQL for the demo. Chosen by environment variable `DB_ENGINE`.|R2|
|D5|CI tool|CircleCI (hosted), config file in the repository. Jenkins only if the lecturer requires it.|R5|
|D6|Rule EP-001 (`.env` not in `.gitignore`)|Project-level rule. Evaluated only by `scanner.scan_directory`, which the management command `scan_folder` uses. The web upload does not evaluate it. State this limitation in the report.|R3|
|D7|Where rule and SITF data live|In code (`scanner` package). The database stores only which rules are switched on.|R3, R2|
|D8|Uploaded file content|Never stored. Only file metadata and masked findings are saved.|R2|
|D9|User and rule management|Done through the built-in Django admin site, restricted to the Admin role. A custom interface is a stretch goal.|R2|
|D10|Cross-organisation access|Returns HTTP 404 (the object is not revealed). Wrong role returns HTTP 403. Not logged in redirects to login (302).|R2|

## 2. How the course readings shaped the design

The project readings (the course reading list) were used for specific decisions, listed below so the report can cite them.

|Reading|Idea taken|Where it is used|
|---|---|---|
|TMS Outsource, software architecture|A decision is architectural if it is expensive to reverse. Qualities such as security and testability come from structure. A small team with unsettled boundaries should start with a modular monolith. Record decisions briefly and review for drift.|Sections 2.2, 3.2 and 3.7 (decision records ADR-01 to ADR-10); section 7 drift test|
|Turing, architecture patterns|A layered architecture suits a system with clear tiers. Monolith is the simplest to deploy.|Layered structure in section 3.2|
|dev.to, architecture versus design patterns|Architecture patterns shape the whole system and design patterns solve problems inside a module. They stack.|MVT/layered architecture; Strategy (rules) and Facade (`run_scan`) inside modules, section 3.2|
|Scaler, design strategies|Top-down decomposition with bottom-up reuse. Object-oriented design with clear responsibilities.|Modules decomposed top-down; the finished `scanner` package reused bottom-up|
|LeewayHertz, software design process|Design moves from requirements to data flow to technical design to prototype to evaluation.|Data flow in section 3.6; contracts in section 5; walking skeleton in section 9|
|IxDF, agile design|Iterate in short cycles; use time-boxed spikes for unknowns; keep roles clear.|Spikes in section 9.3; role briefs in section 10|
|Asana, product development|Build a minimum viable product first; use stage gates.|MVP slice and gates in section 9|
|Asana, process improvement|Lean has five principles (value, value stream, flow, pull, perfection). PDCA gives a repeatable improvement cycle. 5 Whys finds root causes.|Section 9.5 (Lean mapping), weekly PDCA cycle, 5 Whys used on the rejected code|
|Edstellar, capability maturity model|Maturity grows from ad hoc to repeatable to defined.|Target is the Repeatable level: written templates, a defined pull request process and CI on every push (section 7)|
|Productive and Wrike, project management|A plan covers scope, schedule, roles, risks and communication. A software project manager keeps testing and feedback continuous.|Sections 1.2, 9 and 10; R1 owns the plan|
|Open-innovation guide and GitHub, open source|A good repository has a README, contributing rules, issues and pull requests. Open source work depends on shared conventions.|`README.md`, `CONTRIBUTING.md`, branch and pull request rules in section 7.4|

### 2.2 Quality attributes, in priority order

1. **Security.** PayGuard handles secrets. It must never store or display one in full, and it must not trust uploaded content.
2. **Testability.** Every module can be tested without the others, because boundaries are plain data.
3. **Modifiability.** Adding a rule touches three places (a check function, one `Rule(...)` line, one SITF line) and no web code.
4. **Learnability.** The team is new to Django. The structure is the standard Django layout with one extra rule: views call services.
5. **Performance.** Low priority. Files are limited to 1 MB and a scan to 20 files.

## 3. Architecture

### 3.1 System context

```
 Developer ---+
 Auditor -----+--- browser ---> PayGuard (one Django project) ---> Database
 Admin -------+                   |  scanner package (rules)         (SQLite / PostgreSQL)
                                  |  charts package (Matplotlib)
 GitHub ---> CircleCI: runs pytest and Bandit on every push
```

### 3.2 Architecture style

PayGuard is a **modular monolith**: one Django project, one database, one deployment, with strict module boundaries. Inside it the structure is **layered** and follows Django's model-template-view pattern with a service layer added between views and models.

```
Presentation   urls.py, views.py, templates/          takes requests, shows pages
      |  calls only
Application    services.py, selectors.py,             the only place logic lives
               accounts/permissions.py
      |  uses
Domain / data  models.py (Django ORM)                 data
               scanner/ (rules)  charts/ (drawing)    independent packages
```

Two design patterns are used and named so they can be explained:

- **Strategy:** each detection rule is a `Rule` object carrying its own `check` function, and the engine runs whichever rules it is given. A new rule needs no change to the engine.
- **Facade:** `scans.services.run_scan` hides validation, scanning, saving and scoring behind one function, so a view makes one call.

### 3.3 Dependency rules

These rules are what stops modules from tangling. Section 7.2 contains a test that enforces rules 1 to 4.

1. `scanner` imports only the Python standard library and PyYAML. It never imports Django or anything else from the project.
2. `charts` imports only the standard library and Matplotlib. It never imports Django or the database.
3. `models.py` files never import from `services`, `selectors`, `views` or `dashboard`.
4. `views.py` files never run database queries. They call selectors and services.
5. Only `scans/services.py` calls `scanner.scan_text`. Only `dashboard/services.py` builds dashboard data.
6. Templates contain display logic only (loops, conditions). They never call chart code.
7. A change to any contract in section 5 needs a decision log entry and a note in the next team check-in.

### 3.4 Module map

|Module|Type|Owner|Responsibility|Depends on|
|---|---|---|---|---|
|`scanner`|Pure Python package|R3|Rules, SITF mapping, risk score, counts|nothing in the project|
|`charts`|Pure Python package|R4|Draw charts from plain numbers, return PNG bytes|nothing in the project|
|`config`|Django project settings|R2|Settings, root URLs, WSGI|all apps|
|`accounts`|Django app|R2|`Organization`, `User` with role, permission helpers, admin|none|
|`repos`|Django app|R2|`Repository`, register and list views|`accounts`|
|`scans`|Django app|R2|`Scan`, `UploadedFile`, `Finding`, `RuleSetting`, validators, `run_scan`, selectors, upload and detail views|`accounts`, `repos`, `scanner`|
|`dashboard`|Django app|R4|`build_dashboard_data`, dashboard and chart views, all templates|`scans`, `repos`, `accounts`, `charts`, `scanner`|
|`tests`, `samples`|Tests and sample files|R5|Contract tests, integration tests, sample files with expected findings|everything (read only)|

### 3.5 Repository layout

```
payguard/
  manage.py
  requirements.txt            pinned versions (R5)
  pytest.ini
  .gitignore                  must list .env
  .env.example                names of variables, no real values
  README.md  CONTRIBUTING.md  (R1, R5)
  .circleci/config.yml        (R5)
  docs/design.md              this document
  docs/decisions.md           decision log (R1)
  scanner/                    (R3)  already built, copy in unchanged
  charts/                     (R4)  __init__.py, render.py
  config/                     (R2)  settings.py, urls.py, wsgi.py
  accounts/                   (R2)  models.py, admin.py, permissions.py
  repos/                      (R2)  models.py, views.py, forms.py, urls.py
  scans/                      (R2)  models.py, validators.py, services.py,
                                    selectors.py, views.py, forms.py, urls.py,
                                    management/commands/scan_folder.py
  dashboard/                  (R4)  services.py, views.py, urls.py
  templates/                  (R4)  base.html and one template per page
  tests/                      (R5)  contracts/, integration/, factories.py
  samples/                    (R5)  sample files and expected.json
```

### 3.6 Data flow

**Flow A: upload and scan** (use cases: register repository, upload files and run scan, validate input, apply rules)

1. Developer submits the upload form (repository, files, paths). `scans.views.UploadView` receives it.
2. The view builds a list of `UploadItem(path, content)` and calls `scans.services.run_scan(user=..., repository=..., uploads=...)`.
3. `run_scan` checks that the user may scan this repository, then validates every file with `scans.validators.validate_upload`. If any file fails, nothing is saved and `ScanValidationError` is raised.
4. For each file: decode as UTF-8 (errors ignored) and call `scanner.scan_text(text, path, rules=active_rules())`.
5. Inside one database transaction it saves the `Scan`, one `UploadedFile` row per file (metadata only) and one `Finding` row per result, computes `risk_score` with `scanner.calculate_risk_score`, and updates `Repository.latest_risk_score`.
6. It returns the `Scan`. The view redirects to `scans:detail`.

**Flow B: dashboard** (use case: view dashboard and findings)

1. Browser requests `/dashboard/?repo=<id>`. `dashboard.views.home` receives it.
2. The view calls `dashboard.services.build_dashboard_data(user, repo_id)`, which returns a plain dictionary (section 5.3).
3. The template shows the numbers and four `<img>` tags pointing at `/dashboard/charts/<kind>.png?repo=<id>`.
4. Each chart request calls the same `build_dashboard_data` (same permissions), passes one part of the dictionary to a function in `charts`, and returns the PNG bytes.

### 3.7 Architecture decision records

|ID|Decision|Alternatives considered|Reason|Consequence|
|---|---|---|---|---|
|ADR-01|Modular monolith|Microservices|Five people, one pipeline, boundaries still settling. Microservices add network and deployment cost the project cannot afford.|One repository, one deployment. Boundaries kept by rules, not by network.|
|ADR-02|`scanner` is a framework-free package|Rules inside Django|Testable alone; already built and tested.|Django calls it through a small public API only.|
|ADR-03|Service layer and selectors between views and models|Logic in views|Keeps views thin so modules can be tested without HTTP.|One extra file per app.|
|ADR-04|Charts are pure functions returning PNG bytes, drawn with Matplotlib's `Figure` class (not `pyplot`)|Draw inside views; use `pyplot`|No shared global state, safe under a web server, testable without Django.|Chart views only wrap bytes in a response.|
|ADR-05|Rule and SITF data live in code|Store rules in database tables|One source of truth; no sync problem.|Database stores only `RuleSetting` (on/off).|
|ADR-06|Uploaded content is never stored|Store files|A secrets tool must not become a secrets store.|Findings keep masked evidence only.|
|ADR-07|Django admin for user and rule management|Custom pages|Saves two screens of work; well tested.|Admins see Django's admin styling.|
|ADR-08|Server-rendered templates with Bootstrap|Single-page app|Course skills (Django templates); fewer moving parts.|No JavaScript framework.|
|ADR-09|SQLite for dev and tests, PostgreSQL for demo|PostgreSQL everywhere|Fast local setup and simple CI.|Avoid PostgreSQL-only features.|
|ADR-10|CircleCI hosted|Jenkins|No server to run.|Pipeline file lives in the repo.|

## 4. Data design

### 4.1 Entities and relationships

```
Organization 1 --- * User
Organization 1 --- * Repository
Repository   1 --- * Scan
User         1 --- * Scan          (started_by)
Scan         1 --- * UploadedFile  (composition: deleted with the scan)
Scan         1 --- * Finding       (composition: deleted with the scan)
RuleSetting  (standalone: one row per rule code, says whether the rule is on)
```

Rule, SITFTechnique and Pillar from the Part 1 class diagram are **not** database tables. They are code in the `scanner` package (decision D7). Each `Finding` keeps a copy of its `pillar` and `technique` text so old findings stay correct if the mapping changes later.

### 4.2 Models

Set `AUTH_USER_MODEL = "accounts.User"` **before the first `migrate`**. Changing it later is painful.

`accounts/models.py`

```python
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
```

`repos/models.py`

```python
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
```

`scans/models.py`

```python
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
        ordering = ["-started_at"]


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
```

### 4.3 Mapping from the scanner to the database

The scanner's `Finding` fields and the model's fields have the same names, so saving is one line: `Finding(scan=scan, **scanner_finding.to_dict())`. The nine fields are `rule_code, title, severity, pillar, technique, file_path, line_number, masked_evidence, status`. Do not rename any of them.

### 4.4 Data rules

- Severity values are exactly `Critical`, `High`, `Medium`, `Low`. Status values are exactly `open`, `accepted-risk`, `fixed`.
- Pillar values are exactly `Endpoint / IDE`, `VCS`, `CI/CD`, `Registry`, `Production`.
- `risk_score` and `latest_risk_score` are whole numbers from 0 to 100.
- Deleting a scan deletes its files and findings. Deleting a repository deletes its scans.

## 5. Interface contracts

A contract states exactly what crosses a boundary. If you build to the contract, you do not need to read the other side's code.

### 5.1 Scanner (R3 provides, R2 and R4 use)

The package already exists and has 32 passing tests. Import only from the top level:

```python
from scanner import scan_text, scan_file, scan_directory, Finding
from scanner import calculate_risk_score, count_by_severity, count_by_pillar, top_rules
from scanner.rules import ALL_RULES            # list of Rule objects (9 file-level rules)
from scanner.sitf import PILLARS, SITF_MAP     # constants
```

|Function|Input|Output|
|---|---|---|
|`scan_text(text, file_path, rules=None)`|file text, repository-relative path, optional list of `Rule`|`list[Finding]`|
|`scan_file(full_path, display_path=None)`|path on disk|`list[Finding]` (empty for binary or files over 1 MB)|
|`scan_directory(root)`|folder path|`list[Finding]`, includes project-level rule EP-001|
|`calculate_risk_score(findings)`|any iterable of objects with `.severity`|`int` 0 to 100|
|`count_by_severity(findings)`|iterable with `.severity`|`{"Critical": n, "High": n, "Medium": n, "Low": n}` (all four keys always present)|
|`count_by_pillar(findings)`|iterable with `.pillar`|dict with all five pillar keys always present|
|`top_rules(findings, n=5)`|iterable with `.rule_code`|`list[tuple[str, int]]`, most frequent first|

Guarantees: evidence is masked inside the scanner (first 4 characters plus `********`); the scanner only reads text and never runs it; paths come back with forward slashes; malformed YAML does not raise. Because the count functions only need attributes, Django `Finding` model rows can be passed to them directly.

**Path matters.** CI/CD rules apply only when the path contains `.github/workflows/`. The upload form therefore has a separate input for workflow files (section 5.2).

**Adding a rule** (R3 only): write the check function in `scanner/rules/`, add one `Rule(...)` line in `scanner/rules/__init__.py`, add one line in `scanner/sitf.py`, add a test. No web code changes.

### 5.2 Scans module (R2 provides)

`scans/validators.py`

```python
import os

ALLOWED_EXTENSIONS = {".py", ".txt", ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini", ".env", ".js", ".md"}
MAX_FILE_BYTES = 1_000_000      # same limit as scanner.engine.MAX_FILE_BYTES
MAX_FILES_PER_SCAN = 20
MAX_PATH_LENGTH = 300


def clean_path(raw: str):
    """Safe repository-relative path with forward slashes, or None if unsafe."""
    path = raw.replace("\\", "/").strip()
    parts = [p for p in path.split("/") if p not in ("", ".")]
    if not parts or ".." in parts or "\x00" in path or len(path) > MAX_PATH_LENGTH:
        return None
    return "/".join(parts)


def extension_of(path: str) -> str:
    name = os.path.basename(path).lower()
    if name.startswith(".env"):
        return ".env"
    return os.path.splitext(name)[1]


def validate_upload(path: str, content: bytes) -> list:
    """Return error messages. An empty list means the file is accepted."""
    cleaned = clean_path(path)
    if cleaned is None:
        return ["Unsafe file path."]
    errors = []
    if extension_of(cleaned) not in ALLOWED_EXTENSIONS:
        errors.append("File type not allowed.")
    if not content:
        errors.append("File is empty.")
    if len(content) > MAX_FILE_BYTES:
        errors.append("File is larger than 1 MB.")
    if b"\x00" in content:
        errors.append("Binary files are not accepted.")
    return errors
```

`scans/services.py`

```python
from dataclasses import dataclass

from django.core.exceptions import PermissionDenied
from django.db import transaction

from scanner import calculate_risk_score, scan_text
from scanner.rules import ALL_RULES
from scanner.sitf import SITF_MAP

from .models import Finding, RuleSetting, Scan, UploadedFile
from .validators import MAX_FILES_PER_SCAN, clean_path, extension_of, validate_upload


@dataclass(frozen=True)
class UploadItem:
    path: str        # repository-relative, e.g. ".github/workflows/ci.yml" or "settings.py"
    content: bytes


class ScanValidationError(Exception):
    def __init__(self, errors: dict):
        super().__init__("Upload rejected")
        self.errors = errors      # {path: [messages]}; key "" means the whole upload


def active_rules() -> list:
    off = set(RuleSetting.objects.filter(is_active=False).values_list("rule_code", flat=True))
    return [rule for rule in ALL_RULES if rule.code not in off]


def sync_rule_settings() -> None:
    """Make sure every rule code has a RuleSetting row (called by the admin page)."""
    for code in SITF_MAP:
        RuleSetting.objects.get_or_create(rule_code=code)


def run_scan(*, user, repository, uploads: list) -> Scan:
    if user.role != "developer" or repository.organization_id != user.organization_id:
        raise PermissionDenied
    errors = {}
    if not uploads:
        errors[""] = ["Choose at least one file."]
    if len(uploads) > MAX_FILES_PER_SCAN:
        errors[""] = [f"At most {MAX_FILES_PER_SCAN} files per scan."]
    checked = []
    for item in uploads:
        problems = validate_upload(item.path, item.content)
        if problems:
            errors[item.path] = problems
        else:
            checked.append((clean_path(item.path), item.content))
    if errors:
        raise ScanValidationError(errors)        # nothing is saved

    rules = active_rules()
    try:
        with transaction.atomic():
            scan = Scan.objects.create(repository=repository, started_by=user)
            found = []
            for path, content in checked:
                UploadedFile.objects.create(
                    scan=scan, path=path, extension=extension_of(path), size_bytes=len(content)
                )
                found.extend(scan_text(content.decode("utf-8", errors="ignore"), path, rules=rules))
            Finding.objects.bulk_create([Finding(scan=scan, **f.to_dict()) for f in found])
            scan.total_findings = len(found)
            scan.risk_score = calculate_risk_score(found)
            scan.save(update_fields=["total_findings", "risk_score"])
            repository.latest_risk_score = scan.risk_score
            repository.save(update_fields=["latest_risk_score"])
    except Exception:
        Scan.objects.create(repository=repository, started_by=user, status=Scan.Status.FAILED)
        raise
    return scan
```

`scans/selectors.py` and `repos/selectors.py` are the only places that decide what a user may see (decision D3). Views never filter by hand.

```python
# repos/selectors.py
def repositories_for_user(user):             # whole organisation, all roles
    return Repository.objects.filter(organization=user.organization)

def get_repository_for_user(user, repo_id):  # 404 if not in the user's organisation
    return get_object_or_404(repositories_for_user(user), pk=repo_id)

# scans/selectors.py
def scans_for_user(user):
    qs = Scan.objects.filter(repository__organization=user.organization).select_related("repository", "started_by")
    return qs.filter(started_by=user) if user.role == "developer" else qs

def get_scan_for_user(user, scan_id):        # 404 if not visible
    return get_object_or_404(scans_for_user(user), pk=scan_id)

def findings_for_scan(scan):                 # list, Critical first, then by file and line
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    return sorted(scan.findings.all(), key=lambda f: (order[f.severity], f.file_path, f.line_number))
```

**Upload form fields** (`scans/forms.py` and the view): `repository` (id), `files` (multiple files), `workflow_files` (multiple files, optional). The view creates `UploadItem(path=f.name)` for each file in `files` and `UploadItem(path=".github/workflows/" + f.name)` for each file in `workflow_files`. It checks `uploaded.size` against `MAX_FILE_BYTES` **before** calling `.read()`, and reports an oversized file as a validation error instead of reading it.

**Management command** `python manage.py scan_folder <repo_id> <folder>` (R2): runs `scanner.scan_directory(folder)` and saves a `Scan` the same way. It is the only route that evaluates EP-001, and it is used for demos and tests.

### 5.3 Dashboard data and charts (R4 provides)

`dashboard/services.py` contains one function:

```python
def build_dashboard_data(user, repo_id=None) -> dict:
```

It returns this dictionary. Every key is always present.

```python
{
  "repository": {"id": 3, "name": "payments-api"},            # or None
  "latest_scan": {"id": 17, "risk_score": 40, "total_findings": 6,
                  "started_at": "2026-11-08"},               # or None
  "severity_counts": {"Critical": 2, "High": 3, "Medium": 1, "Low": 0},
  "pillar_counts": {"Endpoint / IDE": 0, "VCS": 2, "CI/CD": 3, "Registry": 1, "Production": 0},
  "trend": [{"date": "2026-11-02", "score": 55}, {"date": "2026-11-08", "score": 40}],
  "top_rules": [["VCS-001", 2], ["CICD-001", 2]],
}
```

Selection rules: the repository is `repo_id` if given (404 when it is outside the user's scope, using `get_repository_for_user`), otherwise the repository of the newest scan in the user's scope, otherwise `None`. The latest scan is the newest scan in scope for that repository. The three count fields come from that scan's findings using `count_by_severity`, `count_by_pillar` and `top_rules`. The trend is the last 10 scans in scope for that repository, oldest first, with `date` as `YYYY-MM-DD`. When nothing exists: `repository` and `latest_scan` are `None`, counts are zero, `trend` and `top_rules` are empty lists.

`charts/render.py` is pure Python (no Django). Each chart has a figure builder and a PNG renderer:

```python
from matplotlib.figure import Figure

def severity_figure(counts: dict) -> Figure: ...     # bars in order Critical, High, Medium, Low
def pillar_figure(counts: dict) -> Figure: ...       # bars in the order of scanner.sitf.PILLARS
def trend_figure(points: list) -> Figure: ...        # [{"date": "2026-11-02", "score": 55}, ...]
def top_rules_figure(items: list) -> Figure: ...     # [["VCS-001", 2], ...]

def severity_chart(counts: dict) -> bytes: ...       # same arguments, returns PNG bytes
def pillar_chart(counts: dict) -> bytes: ...
def trend_chart(points: list) -> bytes: ...
def top_rules_chart(items: list) -> bytes: ...
```

Guarantees: each `*_chart` returns bytes starting with `b"\x89PNG"`; none raises for empty or all-zero input (the chart shows the text "No data"); zero values are drawn as zero-height bars; the figures are built with `Figure`, never `pyplot`; image size is 640 by 360 pixels. The `*_figure` functions exist so tests can read bar heights from `fig.axes[0].patches` without comparing pixels (TC-05).

Chart view: `dashboard.views.chart(request, kind)` where `kind` is `severity`, `pillar`, `trend` or `rules`. Any other value returns 404. It calls `build_dashboard_data`, passes the matching part to the chart function, and returns `HttpResponse(png, content_type="image/png")` with `Cache-Control: no-store`.

### 5.4 Permissions (R2 provides, everyone uses)

Response rules: not logged in redirects to login (302); wrong role returns 403; another organisation's object returns 404 (decision D10). All views are **function-based** and use the decorator below on every view except login and logout.

```python
# accounts/permissions.py
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

DEVELOPER, AUDITOR, ADMIN = "developer", "auditor", "admin"

def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return login_required(wrapper)
    return decorator
```

|Action|Not logged in|Developer|Auditor|Admin|
|---|---|---|---|---|
|Dashboard|login page|own scans|organisation|organisation|
|List repositories|login page|organisation|organisation|organisation|
|Register repository|login page|yes|403|403|
|Upload and scan|login page|yes|403|403|
|Scan detail|login page|own scans|organisation|organisation|
|Update finding status|login page|own scans|403|organisation|
|Export CSV (optional)|login page|403|organisation|organisation|
|Django admin (users, rule settings)|admin login page|admin login page|admin login page|own organisation|

`accounts/admin.py` registers `User` and `RuleSetting` with a mixin whose `has_module_permission`, `has_view_permission`, `has_add_permission`, `has_change_permission` and `has_delete_permission` all return `request.user.is_active and request.user.role == "admin"`. The `User` admin limits its queryset to the Admin's own organisation. The `RuleSetting` admin calls `sync_rule_settings()` before showing its list.

### 5.5 URL map

Settings: `LOGIN_URL = "login"`, `LOGIN_REDIRECT_URL = "dashboard:home"`, `LOGOUT_REDIRECT_URL = "login"`. Logout must be a POST form.

|Name|Path|Methods|Roles|Template|
|---|---|---|---|---|
|`login`|`/accounts/login/`|GET, POST|anyone|`registration/login.html`|
|`logout`|`/accounts/logout/`|POST|logged in|none|
|(root)|`/`|GET|logged in|redirects to `dashboard:home`|
|`dashboard:home`|`/dashboard/` (optional `?repo=<id>`)|GET|all roles|`dashboard/home.html`|
|`dashboard:chart`|`/dashboard/charts/<kind>.png` (optional `?repo=<id>`)|GET|all roles|none (PNG)|
|`repos:list`|`/repos/`|GET|all roles|`repos/list.html`|
|`repos:create`|`/repos/new/`|GET, POST|developer|`repos/form.html`|
|`scans:upload`|`/scans/new/`|GET, POST|developer|`scans/upload.html`|
|`scans:detail`|`/scans/<int:scan_id>/`|GET|by section 5.4|`scans/detail.html`|
|`scans:finding_status`|`/scans/<int:scan_id>/findings/<int:finding_id>/status/`|POST (field `status`)|developer (own), admin|redirects to `scans:detail`|
|`scans:export`|`/scans/<int:scan_id>/export.csv`|GET|auditor, admin|none (CSV), optional|
|admin|`/admin/`|Django admin|admin role|built in|

### 5.6 Template contract (R4 writes templates, R2 and R4 write the views that feed them)

Templates receive only what is listed here. If a template needs more, ask for a contract change.

|Template|Context variables|
|---|---|
|`base.html`|blocks `title` and `content`; uses `request.user.role` to show links: Dashboard, Repositories, New scan (developer only), Admin (admin only), and a logout POST form with `{% csrf_token %}`|
|`registration/login.html`|`form`|
|`dashboard/home.html`|`data` (dictionary from section 5.3), `repositories` (list), `selected_repo_id` (int or None). Shows summary numbers and four `<img>` tags whose `src` is `{% url 'dashboard:chart' kind %}?repo=<id>`.|
|`repos/list.html`|`repositories`|
|`repos/form.html`|`form`|
|`scans/upload.html`|`form`, `repositories`, `errors` (dictionary `{path: [messages]}` or empty). Two file inputs named `files` and `workflow_files`, form has `enctype="multipart/form-data"` and `{% csrf_token %}`.|
|`scans/detail.html`|`scan`, `findings` (list from `findings_for_scan`), `can_update_status` (bool), `can_export` (bool), `status_choices` (the `Finding.Status.choices`)|

Finding text such as `masked_evidence` and `file_path` comes from uploaded files, so it is untrusted. Templates must rely on Django's automatic escaping and never use `|safe` or `mark_safe` on it.

## 6. Security design

PayGuard handles secrets, so security is the first quality attribute (section 2.2). Each control below has an owner and a test.

|Threat|Control|Owner|Test|
|---|---|---|---|
|A full secret is stored or shown|The scanner masks evidence to 4 characters plus `********`. Uploaded content is never saved (D8).|R3, R2|TC-01, TC-10|
|Malicious upload (wrong type, huge, binary, path tricks)|`validate_upload` checks path, extension, size and binary content. Files are read in memory only, never written to disk and never executed. Size is checked before reading.|R2|TC-04|
|Script injection through finding text|Django auto-escaping; no `\|safe` or `mark_safe` on finding data.|R4|`test_finding_text_is_escaped`|
|Cross-site request forgery|`CsrfViewMiddleware` stays on. Every POST form has `{% csrf_token %}`. Logout is a POST.|R2, R4|integration tests post without a token and expect 403|
|Broken access control|`role_required` on every view; selectors scope every query; other organisations return 404.|R2|TC-06a to TC-06e|
|SQL injection|Django ORM only. No raw SQL.|All|Bandit in CI|
|Secrets in the repository|Settings read from environment variables. `.env` is in `.gitignore`. Only fake keys appear in tests.|R2, R5|PayGuard scans its own repository in CI review|
|Weak sessions and passwords|Django password validators and hashing; secure cookies when `DEBUG` is off.|R2|settings check test|
|Risky dependencies|Every line in `requirements.txt` pinned with `==` (the same rule REG-001 enforces).|R5|`test_requirements_are_pinned`|
|Unsafe YAML parsing|`yaml.safe_load` only, inside the scanner.|R3|existing scanner tests|

`config/settings.py` must follow this pattern (names fixed, so CI and teammates agree):

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]            # no default on purpose
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"      # off unless asked for
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "login"

if os.environ.get("DB_ENGINE", "sqlite") == "postgres":
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"], "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "localhost"), "PORT": os.environ.get("DB_PORT", "5432"),
    }}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

## 7. Testing and CI

### 7.1 Test levels

|Level|What it proves|Where|Owner|
|---|---|---|---|
|Unit|One function behaves (rules, validators, charts, scoring)|`scanner/` tests (32, exist), `tests/unit/`|R3, R2, R4|
|Contract|A boundary still matches section 4 and 5|`tests/contracts/`|R5|
|Architecture|The dependency rules in section 3.3 hold|`tests/contracts/test_architecture_rules.py`|R5|
|Integration|The whole flow works across modules|`tests/integration/`|R5|
|Permission|Roles and organisations are enforced (TC-06)|`tests/integration/test_permissions.py`|R2, R5|

Tests use SQLite and `pytest-django`. `pytest.ini` sets `DJANGO_SETTINGS_MODULE = config.settings` and `pythonpath = .`. Shared helpers live in `tests/factories.py`: `make_org(name)`, `make_user(org, role)`, `make_repo(org, name)`.

### 7.2 Architecture test (enforces rules 1 to 4 of section 3.3)

```python
# tests/contracts/test_architecture_rules.py
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = {"config", "accounts", "repos", "scans", "dashboard", "charts", "scanner", "django"}


def imports_of(folder):
    names = set()
    for path in (ROOT / folder).rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.add(node.module.split(".")[0])
    return names


def test_scanner_is_framework_free():
    assert not imports_of("scanner") & (PROJECT - {"scanner"})


def test_charts_are_framework_free():
    assert not imports_of("charts") & (PROJECT - {"charts"})


def test_models_do_not_import_upper_layers():
    for path in ROOT.glob("*/models.py"):
        text = path.read_text(encoding="utf-8")
        for word in ("services", "selectors", "views", "dashboard"):
            assert f"import {word}" not in text and f"from .{word}" not in text, (path, word)


def test_views_do_not_query_the_database():
    for path in ROOT.glob("*/views.py"):
        assert ".objects." not in path.read_text(encoding="utf-8"), path
```

### 7.3 Contract tests

```python
# tests/contracts/test_scanner_matches_models.py
from dataclasses import fields
from scanner import Finding as ScannerFinding
from scans.models import Finding


def test_scanner_finding_fields_match_model():
    scanner_names = {f.name for f in fields(ScannerFinding)}
    model_names = {f.name for f in Finding._meta.get_fields()
                   if f.concrete and not f.primary_key} - {"scan"}
    assert scanner_names == model_names
```

|Test|Protects|
|---|---|
|`test_dashboard_data_has_every_key` (with data and with an empty database)|Section 5.3 dictionary shape|
|`test_charts_return_png_for_empty_and_zero_input`|Section 5.3 chart guarantees|
|`test_chart_view_unknown_kind_is_404`|Section 5.3 chart view|
|`test_validate_upload_rules` (exe, 2 MB file, empty file, `../x.py`, binary content, valid `.py`)|Section 5.2 validator, TC-04|
|`test_requirements_are_pinned`|Section 6|

### 7.4 Integration tests

The main flow test is written first and fails until the walking skeleton exists (section 9).

```python
# tests/integration/test_flow.py
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from scans.models import Finding, Scan
from tests.factories import make_org, make_repo, make_user

SECRET_FILE = b'consumer_secret = "abc123XYZ789secretKEY"\nDEBUG = True\n'


@pytest.mark.django_db
def test_upload_scan_save_and_chart(client):
    org = make_org()
    dev = make_user(org, "developer")
    repo = make_repo(org)
    client.force_login(dev)

    response = client.post(reverse("scans:upload"), {
        "repository": repo.pk,
        "files": [SimpleUploadedFile("settings.py", SECRET_FILE)],
    })

    scan = Scan.objects.get()
    assert response.status_code == 302
    assert response["Location"] == reverse("scans:detail", args=[scan.pk])
    codes = set(Finding.objects.values_list("rule_code", flat=True))
    assert {"VCS-001", "PROD-001"} <= codes
    assert scan.total_findings == Finding.objects.count()
    assert all("abc123XYZ789secretKEY" not in f.masked_evidence for f in Finding.objects.all())

    chart = client.get(reverse("dashboard:chart", args=["severity"]))
    assert chart.status_code == 200 and chart.content.startswith(b"\x89PNG")
```

Permission tests (TC-06) use `client.force_login` and the factories. They cover: anonymous user to dashboard returns 302 to login (06a); Developer to `/admin/` returns 302 to the admin login (06b); Developer in organisation A requesting a scan in organisation B returns 404 (06c); Auditor upload returns 403 and Auditor findings page returns 200 (06d); Admin to `/admin/` returns 200 (06e).

Chart tests (TC-05) call the `*_figure` functions and read `fig.axes[0].patches`: counts 2, 3, 1, 0 give four bars with those heights; the pillar chart gives five bars `2, 3, 1, 0, 0` for the sample scan; empty input does not raise; the trend chart for scores 40, 25, 10 has three points in date order.

### 7.5 Samples

`samples/` holds small files and `samples/expected.json`, a list of `{file, expected_rule_codes}`. One test loops over it, scans each file with `scan_text`, and checks the codes match. Adding a sample is the cheapest way to add a test.

### 7.6 Continuous integration and team workflow

`.circleci/config.yml`

```yaml
version: 2.1
jobs:
  test:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - run: pip install -r requirements.txt
      - run:
          name: Tests
          command: pytest
          environment:
            DJANGO_SECRET_KEY: ci-only-not-a-real-secret
            DJANGO_SETTINGS_MODULE: config.settings
      - run:
          name: Security scan of our own code
          command: bandit -r accounts repos scans dashboard charts scanner -q
workflows:
  main:
    jobs:
      - test
```

`requirements.txt` (R5 pins exact versions at setup): Django 5.2 LTS, matplotlib, PyYAML 6.0.2, pytest 8.3.3, pytest-django, bandit, and `psycopg[binary]` for PostgreSQL.

**Branch and pull request rules** (Repeatable-level practice from the maturity model reading): `main` is protected. Work happens on branches named `r<role number>/<short-name>`. A pull request needs one reviewer and a green CI run. The description names the design sections it touches and the tests run. Each person commits their own work in small steps.

## 8. Traceability chain

This table is the answer to "how do features link to each other". Each use case from the Part 1 diagram is followed from request to test. Requirement IDs extend the earlier matrix: R14 (register a repository) and R15 (update a finding's status) are new.

|Use case|Requirements|Entry point|Code path|Data|Screen|Tests|
|---|---|---|---|---|---|---|
|Log in|R5|`login`|Django auth views|`User`|`registration/login.html`|TC-06a|
|Register repository|R14|`repos:create`|`repos.views.create`|`Repository`|`repos/form.html`|TC-15|
|Upload files and run scan|R1, R2, R6, R9, R10|`scans:upload`|`scans.views.upload` then `scans.services.run_scan`|`Scan`, `UploadedFile`, `Finding`|`scans/upload.html`|TC-01, 02, 03, 07, 10, 11|
|Validate input (included)|R3|inside `run_scan`|`scans.validators.validate_upload`|none|errors on `scans/upload.html`|TC-04|
|Apply rules and map to SITF (included)|R1, R2, R6, R7, R8|inside `run_scan`|`scanner.scan_text`, `calculate_risk_score`|`Finding`|none|TC-01, 02, 03, 07, 08, 09|
|View dashboard and findings|R4, R5, R10|`dashboard:home`, `dashboard:chart`, `scans:detail`|`dashboard.services.build_dashboard_data`, `charts.render`|`Scan`, `Finding`|`dashboard/home.html`, `scans/detail.html`|TC-05, TC-06|
|Update finding status (extends view)|R15|`scans:finding_status`|`scans.views.finding_status`|`Finding`|`scans/detail.html`|TC-16|
|Export report (optional)|R13|`scans:export`|`scans.views.export_csv`|`Finding`|none (CSV)|TC-14|
|Manage users and roles|R5, R11|`/admin/`|`accounts.admin`|`User`, `Organization`|Django admin|TC-06b, TC-06e|
|Manage rules and SITF mappings|R7, R11|`/admin/`|`scans.admin`, `sync_rule_settings`|`RuleSetting`|Django admin|TC-08, TC-12|
|Run tests on every push|R12|CircleCI|`.circleci/config.yml`|none|CircleCI|TC-13|

Checks that keep the chain complete: every use case has an entry point, a code path, data, a screen and a test; every test traces to a requirement; every model field is used by a service or a template. TC-15 is the register-repository test (a Developer posts the form and the repository exists in their organisation only). TC-16 is the status test (a Developer changes a finding to `accepted-risk`, an Auditor attempting the same gets 403).

## 9. Integration plan, gates and decision log

The earlier build failed at integration. This plan joins the modules first, while they are nearly empty, and fills them in afterwards. A passing end-to-end flow is the proof that the parts fit.

### 9.1 Build order and gates

|Gate|Date|What must be true|Who signs|
|---|---|---|---|
|G1 Contracts agreed|6 Nov|All five members have read sections 0 to 5 and their brief. Open questions are answered in the decision log.|All|
|G2 Walking skeleton|7 Nov|The repository exists with every app, model and migration; all URLs from section 5.5 resolve; the `scanner` package is copied in; charts and templates are stubs; `tests/integration/test_flow.py` passes; CI is green.|R5, R2|
|G3 Features merged|11 Nov|Every stub is replaced by real code, each through a pull request with CI green.|Module owners|
|G4 Everything passes|13 Nov|All test cases in section 8 pass in CI; Bandit is clean; documents are frozen.|R5, R1|
|G5 Submit|14 Nov|Final submission, one day before the deadline.|All|

**Stubs for G2.** `charts/render.py` returns a fixed valid PNG for every chart. `dashboard/services.py` returns the section 5.3 dictionary with fixed numbers. Templates are plain pages that print their context variables. Because the stubs obey the contracts, replacing them later cannot break the other modules.

**Between gates** work flows as a Kanban board with the lists Backlog, Ready, In progress, In review, Testing and Done. Each person has at most two cards in progress. Every card names its design section and test case IDs. Cards on the critical path (R2 models, upload and scan service; R3 rule fixes; the integration tests) are marked and checked first.

### 9.2 Definition of done for any module

1. Everything in its brief (section 10) exists at the stated paths.
2. Its unit tests and its contract tests pass.
3. The integration test `test_flow.py` still passes after its merge.
4. Bandit reports nothing for its code.
5. It is merged through a pull request with one review.
6. The owner has written half a page for the report (what it does, why designed this way) and sent it to R1.

### 9.3 Spikes (time-boxed to two hours each, from the agile design reading)

|Spike|Question|Owner|
|---|---|---|
|A|What are the official SITF technique names and IDs for our 10 rules?|R3|
|B|Can a `Figure` built without `pyplot` be returned as PNG from a Django view?|R4|
|C|Does a hello-world CircleCI job run and pass on our repository?|R5|
|D|Does a fresh project with the custom user model migrate cleanly?|R2|

If a spike runs past two hours, the owner says so at the next check-in and the team decides whether to cut scope.

### 9.4 Decision log

File: `docs/decisions.md`, kept by R1. One entry per change, newest first:

```
2026-11-09 | D1 | Risk score now divides by files scanned | Why: caps hide differences | Sections: 1.4, 5.1, TC-09 | Agreed: R1 R2 R3 R4 R5
```

A change to any contract (sections 4 and 5) needs three things in the same pull request: the code, the edit to `docs/design.md`, and a decision log line. If the log has no entry, the change is not accepted. This is also the source for the architecture justification in the Part 2 report.

### 9.5 How the process readings are applied

|Idea|Use in PayGuard|
|---|---|
|Lean: value|Every feature traces to a requirement (section 8). Features without one are not built.|
|Lean: value stream|The one flow that matters is upload, scan, save, dashboard. The skeleton builds exactly that.|
|Lean: flow|Small pull requests, two cards in progress per person.|
|Lean: pull|Work is taken from the Ready list, not pushed onto people.|
|Lean: perfection|A 15-minute review each check-in: what slowed us down, what changes.|
|PDCA|Plan (this document), Do (build to a gate), Check (tests and CI), Act (decision log entry). Repeated at every gate.|
|5 Whys|Used when a test fails twice or a gate is missed: ask why five times, record the root cause in the decision log.|
|Maturity model (Repeatable level)|Written templates, a defined pull request process, and CI on every push, so results do not depend on who did the work.|

## 10. Build briefs

Each brief lists what a role owns, the order to build in, the tests it must pass and what it must not do. Read it together with the contract sections it points to.

### 10.1 R1 Project Manager and Documentation Lead

**Owns:** `README.md`, `CONTRIBUTING.md`, `docs/decisions.md`, this document, the Trello board, the SRS, the traceability matrix, the Part 2 report. No application code.

**Does:** runs gates G1 to G5; keeps section 8 and the traceability matrix in step with the code (adds R14, R15, TC-15, TC-16); collects half a page from each member; applies the differences in section 11 in the Part 2 report; watches the critical-path cards daily.

**Done when:** every contract question has a decision log entry, the RTM matches section 8, and the Part 2 documents are complete by 13 Nov.

### 10.2 R2 Backend Lead

**Owns:** `config/`, `accounts/`, `repos/`, `scans/`, `manage.py`. Includes models (section 4), permissions and admin (5.4), validators and services (5.2), selectors, views, forms, URLs (5.5), and the `scan_folder` command. R4's templates are not yours, but your views must pass exactly the context in section 5.6.

**Order:** 1) settings and custom user model, migrate on SQLite; 2) models and migrations; 3) URLs and stub views that return the right template and context; 4) selectors and `role_required`; 5) validators and `run_scan`; 6) upload, repository and finding status views; 7) admin; 8) `scan_folder`.

**Must pass:** `tests/contracts/`, `tests/integration/`, TC-04, TC-06, TC-11, TC-12, TC-15, TC-16.

**Do not:** query the database in a view; store file content; skip `role_required`; rename any model field.

### 10.3 R3 Rule Engine Developer

**Owns:** `scanner/` (already built, 10 rules, 32 tests).

**Remaining:** replace the placeholder names in `scanner/sitf.py` with the official SITF names (spike A) and keep rule codes unchanged; add edge-case tests (empty file, very long line, Windows line endings, `.env.production`); confirm decision D1 with the team; review R2's `run_scan` against the scanner guarantees; add planned rules only after G4.

**Must pass:** the existing 32 tests plus the architecture test for `scanner`; TC-01, TC-02, TC-03, TC-07, TC-08, TC-09, TC-10.

**Do not:** change a public function signature, a field of `Finding`, or the pillar and severity strings. Never import Django.

### 10.4 R4 Dashboard and Frontend Developer

**Owns:** `charts/`, `dashboard/`, `templates/`.

**Order:** 1) `charts/render.py` with the four `*_figure` and four `*_chart` functions (spike B); 2) `dashboard/services.py` `build_dashboard_data`; 3) `dashboard/views.py` and URLs; 4) `base.html` with Bootstrap 5.3.3 loaded from a pinned CDN link; 5) one template per row of section 5.6.

**Must pass:** TC-05 (all four cases), `test_dashboard_data_has_every_key`, `test_charts_return_png_for_empty_and_zero_input`, `test_chart_view_unknown_kind_is_404`, `test_finding_text_is_escaped`.

**Do not:** import Django inside `charts/`; query the database inside a view; use `|safe` on finding text; use `pyplot`.

### 10.5 R5 QA and DevOps Engineer

**Owns:** `.circleci/`, `requirements.txt`, `pytest.ini`, `.gitignore`, `.env.example`, `tests/`, `samples/`. Also owns the diagrams for the Part 2 design document, drawn from sections 3 and 5.

**Order:** 1) repository and branch protection (spike C); 2) walking skeleton with R2 (gate G2); 3) `tests/factories.py`, the architecture and contract tests, `test_flow.py`; 4) samples and `expected.json`; 5) permission and chart tests with R2 and R4; 6) Bandit in CI; 7) Part 2 diagrams and test plan.

**Must pass:** TC-13 and every test in section 7. Report weekly which TC numbers are green.

**Do not:** weaken a failing test to make CI pass. A failing test means a contract is broken, so raise it in the decision log.

## 11. Differences from the Part 1 diagrams and the earlier RTM

Part 1 has been submitted. Part 2 must state these differences openly and explain each one.

|Part 1 or RTM|Now|Reason|
|---|---|---|
|Rule, SITFTechnique and Pillar shown as classes with relationships|Code in the `scanner` package; the database holds only `RuleSetting`|ADR-05: one source of truth, no sync problem|
|No `UploadedFile` class|`UploadedFile` stores metadata only|Part of Scan, supports validation and history; ADR-06 keeps content out|
|Repository had `latestRiskScore` and Scan had `riskScore`|Same (`latest_risk_score`, `risk_score`)|Needed for the trend chart|
|Repository had name, url and score only|Adds `organization`, `created_by`, `created_at`|Needed for access control (D3)|
|TC-06b: Developer to user management page returns 403|Developer to `/admin/` redirects to the admin login (302)|User management uses the Django admin site (D9, ADR-07)|
|TC-06c: 403 or 404 for another organisation's scan|Always 404|Decision D10|
|RTM stops at R13 and TC-14|Adds R14 (register repository, TC-15) and R15 (update finding status, TC-16)|Both use cases existed in Part 1 but had no requirement|
|Use case diagram shows no login|Log in is a real use case, shown as a note in Part 1|Section 8 treats it as one|
|Rule EP-001 applies to a repository|Evaluated only by `scan_folder`, not by web upload|D6: a single upload has no project folder; state it as a limitation|

## 12. References

SDLC Infrastructure Threat Framework (SITF), Wiz. https://wiz-sec-public.github.io/SITF/

Berkovich, S. (2026) Securing the code factory: why SDLC infrastructure has become a core cloud risk. SD Times, 20 March.

Poppendieck, M. and Poppendieck, T. (2003) Lean Software Development: An Agile Toolkit. Boston: Addison-Wesley.

Course readings used in section 2:

- Asana. Process improvement methodologies. https://asana.com/resources/process-improvement-methodologies
- Asana. Product development process. https://asana.com/resources/product-development-process
- Wrike. What is software project management? https://www.wrike.com/project-management-guide/faq/what-is-software-project-management/
- Productive. What is a project management plan? https://productive.io/blog/project-management-plan/
- Edstellar. Capability maturity model. https://www.edstellar.com/blog/capability-maturity-model
- TMS Outsource. What is software architecture? https://tms-outsource.com/blog/posts/software-architecture/
- Turing. Software architecture patterns. https://www.turing.com/blog/software-architecture-patterns-types
- dev.to (mohammed_zrar). Architecture patterns vs design patterns. https://dev.to/mohammed_zrar/architecture-patterns-vs-design-patterns-with-examples-5fcp
- LeewayHertz. Software design process. https://www.leewayhertz.com/software-design-process/
- Scaler Topics. Design strategies in software engineering. https://www.scaler.com/topics/software-engineering/design-strategies-in-software-engineering/
- Interaction Design Foundation. What is agile design? https://ixdf.org/literature/topics/agile-design
- Open Innovation Projects. Creating an open source project on GitHub. https://open-innovation-projects.org/blog/beginners-guide-on-creating-open-source-projects-in-github-for-collaboration-and-code-sharing
- GitHub. What is open source software? https://github.com/resources/articles/what-is-open-source-software
- Edureka. What is Agile? (video) https://youtu.be/WjwEh15M5Rw