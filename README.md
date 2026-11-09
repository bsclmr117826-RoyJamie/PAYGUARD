[project_readme.md](https://github.com/user-attachments/files/34592676/project_readme.md)
# PayGuard 🛡️

> **SDLC Security Dashboard for Fintech Development Teams**  
> *Course Unit: BCS 3106 Software Engineering | Target Delivery: October/November 2026*

PayGuard is a specialized security analysis platform designed to mitigate vulnerabilities within the fintech **"code factory"**—spanning developer IDE environments, Version Control Systems (VCS), CI/CD pipelines, package registries, and production settings. 

By mapping codebase vulnerabilities directly to the **SDLC Infrastructure Threat Framework (SITF)**, PayGuard empowers engineering teams to detect financial-grade secrets (e.g., Safaricom Daraja API keys, passkeys), unpinned pipeline action runners, and unvalidated M-Pesa STK push callback handlers before deployment.

---

## 🌟 Key Features

* **SITF 5-Pillar Vulnerability Mapping:** Scans and categorizes threats across **Endpoint/IDE**, **VCS**, **CI/CD**, **Package Registry**, and **Production Gate**.
* **Fintech Rule Engine:** Pre-configured regex patterns designed for financial pipelines (Daraja Consumer Secrets, raw passkeys, unpinned GitHub Actions, missing callback signature verifications).
* **Automated Masking:** Automatically masks sensitive findings (retaining only the first 4 characters) to prevent secret leakage in logging databases.
* **Matplotlib Visualization Backend:** Server-side rendered visual analytics (`chart_service.py`) delivering high-resolution Radar and Bar charts directly to the interface.
* **Role-Based Access Control (RBAC):** Customized view permissions for **Developers**, **Auditors**, and **Admins**.
* **REST API & Source Exporter:** Full API endpoints (`/api/v1/scan/`, `/api/v1/findings/`, etc.) paired with an in-app zip exporter for backend source files.

---

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend Structure** | HTML5 / Tailwind CSS (CDN) | Responsive, framework-free UI layout |
| **Frontend Behavior** | Vanilla JavaScript (ES6+ / Fetch API) | Client-side tab routing & REST API requests |
| **Visualization** | Chart.js & Matplotlib (`Agg` backend) | Client canvas preview & server PNG chart rendering |
| **Backend Language** | Python 3.12 | Primary execution language |
| **Backend Framework**| Django 5.0 / Django REST Framework | ORM models, auth middleware, and API views |
| **Database** | PostgreSQL (SQLite for local dev) | Scans, findings, and rule metadata storage |
| **Parser Tooling** | PyYAML (`safe_load`), `re`, `packaging` | Safe pipeline parsing & dependency inspection |
| **Testing & CI/CD** | `pytest`, `pytest-django`, Bandit, Jenkins | Automated test suites and pipeline security checks |

---

## 🏛️ System Architecture

PayGuard uses a layered Django architecture to isolate scanning logic from presentation:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│           (Single-Page HTML5 / JavaScript / Tailwind)       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / REST API
┌──────────────────────────────▼──────────────────────────────┐
│                    Application Layer                        │
│             (Django Views, Forms, RBAC Auth)               │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────┐┌──────────────▼──────────────┐
│        Domain Layer         ││        Chart Service         │
│ ┌─────────────────────────┐ ││    (Matplotlib Backend)     │
│ │   PayGuard Rule Engine  │ │└──────────────┬──────────────┘
│ └────────────┬────────────┘ │               │
│ ┌────────────▼────────────┐ │               │
│ │       SITF Mapper       │ │               │
│ └────────────┬────────────┘ │               │
│ ┌────────────▼────────────┐ │               │
│ │     Scoring Service     │ │               │
│ └────────────┬────────────┘ │               │
└──────────────┼──────────────┘               │
               │                              │
┌──────────────▼──────────────────────────────▼──────────────┐
│                     Data Access Layer                       │
│            (Django ORM ──► PostgreSQL Database)             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Directory Structure

```text
payguard_backend/
├── core/
│   ├── settings.py          # Django settings & PostgreSQL database configuration
│   ├── urls.py              # Root URL router
│   └── wsgi.py              # WSGI server entry point
├── domain/
│   ├── rule_engine.py       # Core SITF regex execution engine
│   └── sitf_mapper.py       # Maps rule matches to 5 SITF pillars
├── services/
│   └── chart_service.py     # Matplotlib Agg chart generation service
├── models.py                # Django ORM models (Organization, Repo, Scan, Finding)
├── views.py                 # REST API endpoints & Scan controllers
├── tests/
│   └── test_rules.py        # Pytest suite for rule validation
└── static/ & templates/     # Single-page frontend dashboard files
```

---

## 🚀 Quickstart Guide

### Prerequisites
* **Python 3.12+**
* **PostgreSQL** (or SQLite for quick testing)
* **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/payguard.git
cd payguard
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install django djangorestframework matplotlib pyyaml pytest pytest-django bandit
```

### 3. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Launch Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser to access the PayGuard Dashboard.

---

## 📡 REST API Documentation

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/scan/` | `POST` | Uploads code/YAML content, runs SITF rules, and returns findings. |
| `/api/v1/findings/` | `GET` | Fetches saved findings from PostgreSQL (Secrets masked). |
| `/api/v1/rules/` | `GET` | Returns list of active SITF rules and severity weights. |
| `/api/v1/stats/` | `GET` | Retrieves aggregate system risk scores and pillar metrics. |

### Sample API Request (`POST /api/v1/scan/`)
```json
{
  "file_path": "payments/daraja_config.py",
  "content": "daraja_secret = \"bf918342abcdef123456\""
}
```

### Sample API Response (`200 OK`)
```json
{
  "status": "success",
  "findings_count": 1,
  "calculated_risk_score": 100,
  "findings": [
    {
      "rule_code": "RULE-VCS-01",
      "pillar": "VCS",
      "description": "Hardcoded Daraja Consumer Key / Secret in Source Code",
      "severity": "CRITICAL",
      "weight": 10,
      "file_path": "payments/daraja_config.py",
      "line_number": 1,
      "masked_evidence": "daraja_secret...[MASKED_BY_PAYGUARD]"
    }
  ]
}
```

---

## 🧪 Testing & CI/CD Pipeline

Run the automated `pytest` test suite and static code analyzer (`Bandit`):

```bash
# Run Django unit tests
pytest

# Run security static analysis on PayGuard's own codebase
bandit -r payguard_backend/
```

---

## 📄 License & Course Attribution

This project is submitted under **Unit BCS 3106 Software Engineering** 
```


