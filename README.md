# PayGuard

**SDLC security dashboard for fintech development teams**

Course unit: BCS 3106 Software Engineering. Target delivery: October to November 2026.

PayGuard analyses the fintech "code factory": developer machines and IDEs, version control, CI/CD pipelines,
package registries and production settings. A developer uploads files from a repository, PayGuard scans them with
a rule engine built for payment code, maps every finding to a pillar and technique of the
**SDLC Infrastructure Threat Framework (SITF)**, stores the result and shows the risk on a dashboard.

It looks for the weaknesses that matter in a payment pipeline: hardcoded Safaricom Daraja keys and passkeys, GitHub
Actions that are not pinned to a commit, loosely pinned dependencies, debug mode left on, and service or callback
URLs that use plain HTTP.

Specification: [`docs/design.md`](docs/design.md) | Decisions: [`docs/decisions.md`](docs/decisions.md) |
How to work in this repository: [`CONTRIBUTING.md`](CONTRIBUTING.md)

---

## Key features

- **SITF five-pillar mapping.** Every finding is tied to one of Endpoint / IDE, VCS, CI/CD, Registry or Production,
  with an SITF technique.
- **Fintech rule engine.** Ten rules covering Daraja consumer keys and secrets, passkeys, API tokens, unpinned
  actions, risky workflow triggers, over-broad pipeline permissions, unpinned dependencies, debug mode, plain HTTP
  URLs and an exposed `.env` file. See [Detection rules](#detection-rules).
- **Masking by design.** Evidence is masked to the first 4 characters. Uploaded file content is never stored, only
  file names, sizes and masked findings.
- **Risk score.** Each scan gets a score from 0 to 100, and every repository keeps a history so the dashboard can
  show a trend.
- **Matplotlib dashboard.** Four charts drawn on the server: findings by severity, findings by SITF pillar, risk
  score over time and the most frequent rules.
- **Role-based access control.** Developer, Auditor and Admin roles, scoped to an organisation. Another
  organisation's data is never visible.
- **Triage and reporting.** Developers mark findings as open, accepted risk or fixed. Auditors and Admins export a
  scan to CSV.
- **Tested and checked on every push.** More than 100 automated tests, the Bandit security scanner and a GitHub
  Actions pipeline.

---

## Technology stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| Language | Python 3.12 | Everything on the server |
| Web framework | Django 5.2 (LTS) | ORM, authentication, sessions, CSRF protection, admin site |
| Pages | Django templates with Bootstrap 5.3.3 (CDN) | Server-rendered, no JavaScript framework |
| Charts | Matplotlib (`Figure` class, Agg backend) | PNG charts rendered on the server |
| Database | SQLite for development and tests, PostgreSQL for the demo | Scans, findings, users, rule settings |
| Parsing | PyYAML (`safe_load` only), regular expressions | Reading workflow files and matching patterns |
| Testing and checks | pytest, pytest-django, Bandit | Automated tests and static security analysis |
| CI | GitHub Actions | Runs the tests and Bandit on every push and pull request |

---

## System architecture

PayGuard is a modular monolith: one Django project and one database, with strict boundaries between the modules.
It is layered, and a service layer sits between the views and the models.

```
+-------------------------------------------------------------+
|                     Presentation layer                      |
|        urls.py, views.py, templates (Bootstrap pages)       |
+------------------------------+------------------------------+
                               | calls only
+------------------------------v------------------------------+
|                     Application layer                       |
|   services.py, selectors.py, permissions (role_required)    |
+---------+------------------------------+--------------------+
          |                              |
+---------v-----------+       +----------v-------------------+
|   scanner package   |       |       charts package         |
|  rules, SITF map,   |       |  Matplotlib figures -> PNG   |
|  masking, scoring   |       |  (no Django, no database)    |
|  (no Django)        |       +------------------------------+
+---------+-----------+
          |
+---------v---------------------------------------------------+
|                       Data layer                            |
|        Django ORM models -> SQLite / PostgreSQL             |
+-------------------------------------------------------------+
```

Dependency rules, enforced by `tests/contracts/test_architecture_rules.py`:

1. `scanner` and `charts` never import Django or anything else from the project.
2. Models never import services, selectors or views.
3. Views never query the database. They call selectors and services.
4. Only `scans/services.py` calls `scanner.scan_text`.

### How a scan works

1. A Developer picks a repository and uploads files. Workflow files go in a separate input so that the CI/CD rules
   can see their `.github/workflows/` path.
2. `scans.services.run_scan` checks the role and organisation, then validates every file (type, size, path, binary
   content). If any file fails, nothing is saved.
3. Each file is scanned in memory with the rules that are switched on.
4. In one database transaction PayGuard saves the scan, the file metadata and the findings, calculates the risk
   score and updates the repository's latest score.
5. The Developer is sent to the scan page. The dashboard reads the saved data and draws the charts.

---

## Detection rules

| Code | Rule | Severity | Pillar |
| :--- | :--- | :--- | :--- |
| VCS-001 | Hardcoded Daraja consumer key or secret | Critical | VCS |
| VCS-002 | Hardcoded Daraja passkey | Critical | VCS |
| VCS-003 | Hardcoded API token or secret key | Critical | VCS |
| CICD-001 | GitHub Action not pinned to a commit SHA | High | CI/CD |
| CICD-002 | Risky `pull_request_target` use | High | CI/CD |
| CICD-003 | Over-broad workflow permissions (`write-all`) | High | CI/CD |
| REG-001 | Dependency not pinned to an exact version | Medium | Registry |
| PROD-001 | `DEBUG` enabled | High | Production |
| PROD-002 | HTTP instead of HTTPS for a service URL | High | Production |
| EP-001 | `.env` file is not listed in `.gitignore` | Medium | Endpoint / IDE |

- **Risk score:** the sum of severity weights (Critical 10, High 5, Medium 2, Low 1), capped at 100.
- **Masking:** a secret such as `abc123XYZ789secretKEY` is shown as `abc1********`.
- **EP-001 is a project-level rule.** It needs a whole folder, so it runs only through the `scan_folder` command,
  not through a web upload (see [Scan a folder](#scan-a-folder)).
- SITF technique wording is provisional until the official names are copied into `scanner/sitf.py` (decision D2).
- To add a rule: write its check function in `scanner/rules/`, add one `Rule(...)` line in
  `scanner/rules/__init__.py`, one line in `scanner/sitf.py`, and a test.

---

## Project directory structure

```text
payguard/
├── manage.py
├── requirements.txt            # pinned versions
├── pytest.ini
├── .env.example                # names of settings, no real values
├── config/                     # settings.py, urls.py, wsgi.py
├── accounts/                   # Organization, User with role, permissions, admin site, seed_demo command
├── repos/                      # Repository model, selectors, forms, views
├── scans/                      # Scan, UploadedFile, Finding, RuleSetting; validators, services, selectors,
│                               #   views, admin, scan_folder command
├── dashboard/                  # build_dashboard_data, dashboard and chart views
├── charts/                     # Matplotlib charts (pure Python)
├── scanner/                    # rule engine, SITF map, scoring (pure Python)
│   └── rules/                  # one module per pillar
├── templates/                  # base.html and one page per screen
├── tests/
│   ├── unit/                   # scanner rules, charts, BUG-001 regression
│   ├── contracts/              # architecture rules, models vs scanner, validators, samples
│   └── integration/            # full flow, permissions (TC-06), features
├── samples/                    # sample files and expected.json
├── docs/                       # design.md, decisions.md, prototype/
└── .github/workflows/ci.yml    # GitHub Actions pipeline
```

---

## Quickstart

### Prerequisites

- Python 3.12 or newer
- Git
- PostgreSQL only if you want it. SQLite is used by default.

### 1. Clone the repository

```bash
git clone https://github.com/bsclmr117826-RoyJamie/PAYGUARD.git
cd PAYGUARD
```

### 2. Create a virtual environment and install the dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Choose your settings

For local development turn on debug mode (it is off by default):

```bash
export DJANGO_DEBUG=1            # Windows cmd: set DJANGO_DEBUG=1    PowerShell: $env:DJANGO_DEBUG=1
```

Without debug mode you must set `DJANGO_SECRET_KEY` (see [Configuration](#configuration)).

### 4. Create the database and demo data

```bash
python manage.py migrate
python manage.py seed_demo
```

`seed_demo` creates an organisation, one user per role (`dev1`, `auditor1`, `admin1`) and one repository. It prints
a random password once, so copy it. To create your own accounts instead, run
`python manage.py createsuperuser` and add users in the admin site.

### 5. Start the server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ and log in. Log in as `dev1`, choose **New scan**, upload a file from `samples/` and
open the dashboard.

---

## Configuration

| Variable | Default | Meaning |
| :--- | :--- | :--- |
| `DJANGO_DEBUG` | `0` | `1` turns on debug mode (local use only) |
| `DJANGO_SECRET_KEY` | none | Required when debug is off. No default on purpose. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names |
| `DB_ENGINE` | `sqlite` | `sqlite` or `postgres` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | none, none, none, `localhost`, `5432` | Needed only for PostgreSQL |
| `DJANGO_SSL_REDIRECT`, `DJANGO_HSTS_SECONDS`, `DJANGO_BEHIND_PROXY` | `1`, `3600`, off | HTTPS settings used when debug is off |

Copy `.env.example` to `.env` for reference. `.env` is ignored by Git and must never be committed.

---

## Using PayGuard

### Roles

| Role | Can do |
| :--- | :--- |
| Developer | Register repositories, upload and scan, see their own scans, update finding status |
| Auditor | See every scan in the organisation, export a scan to CSV |
| Admin | See every scan in the organisation, update finding status, export CSV, manage users and rules in `/admin/` |

### Pages

| Page | Address | Who |
| :--- | :--- | :--- |
| Log in | `/accounts/login/` | everyone |
| Dashboard | `/dashboard/` (optional `?repo=<id>`) | all roles |
| Repositories | `/repos/` and `/repos/new/` | all roles, Developers register |
| New scan | `/scans/new/` | Developers |
| Scan detail | `/scans/<id>/` | by role (see above) |
| CSV export | `/scans/<id>/export.csv` | Auditors, Admins |
| Admin site | `/admin/` | Admins |

### Switch a rule on or off

Log in as an Admin, open `/admin/`, choose **Rule settings** and tick or untick **Is active**. A rule that is off
produces no findings in later scans.

### Scan a folder

The only way to run the project-level rule EP-001:

```bash
python manage.py scan_folder <repository id> <folder path> --username <developer username>
```

---

## Testing and CI

```bash
pytest                                                        # all tests
bandit -r accounts repos scans dashboard charts scanner -q    # security analysis of PayGuard's own code
```

| Level | What it proves | Where |
| :--- | :--- | :--- |
| Unit | Rules, masking, scoring and charts behave | `tests/unit/` |
| Contract | Boundaries still match the design, dependency rules hold | `tests/contracts/` |
| Integration | Upload, scan, save, dashboard, roles and exports work together | `tests/integration/` |

GitHub Actions (`.github/workflows/ci.yml`) runs the tests and Bandit on every push and pull request to `main`. The
two actions it uses are pinned to commit SHAs, which is exactly what rule CICD-001 asks of other projects.

---

## Known limitations

- Ten rules only. Payment callback signature checking is not included.
- EP-001 runs only through `scan_folder`, not through the web upload.
- A scan takes at most 20 files of 1 MB each, and only the file types listed in `scans/validators.py`.
- SITF technique names are placeholders until the official names are added.
- There is no REST API, source exporter or password-reset page in this version. The earlier prototype had a
  single-page interface that is kept in `docs/prototype/` for reference only.

---

## Documentation

- [`docs/design.md`](docs/design.md): architecture, data model, interface contracts, security design, build briefs
- [`docs/decisions.md`](docs/decisions.md): every change to a decision or contract
- [`CONTRIBUTING.md`](CONTRIBUTING.md): branches, pull requests, definition of done

## Team

| Role | Area |
| :--- | :--- |
| R1 Project Manager and Documentation Lead | `docs/`, planning, SRS, traceability matrix, reports |
| R2 Backend | `config/`, `accounts/`, `repos/`, `scans/` |
| R3 Rule Engine | `scanner/` |
| R4 Dashboard and Frontend | `charts/`, `dashboard/`, `templates/` |
| R5 QA and DevOps | `tests/`, `samples/`, CI |

R1: Elvis Ngari Wambugu
R2: Roy James Karoki
R3: Janet Ndunda
R4: Jamhuri Simeon Nzisi
R5: Magdalene Nzilani Wambua

## License and course attribution

This project is submitted under unit **BCS 3106 Software Engineering**. Add the group name or number and the
lecturer's name here before submission.
