# Sentinel Commander
> ⚠️ **Early Alpha Notice**  
> Sentinel Commander is currently in early alpha. While many core features are functional and actively in use, the platform is under continuous development. Expect frequent changes, improvements, and new modules.   

**Sentinel Commander** is a modular, open-source platform for cyber security alert triage, case management, and response orchestration. Designed for modern Security Operations Centers (SOCs), it provides a structured, intuitive interface to track alerts, manage incidents, document findings, and automate triage workflows.

---

## 🚀 Key Features

- **Modular Architecture**: Sentinel Commander is organized into logical modules: Alerts, Cases, Playbooks, Sources, Assets, and more.
- **Alert Ingestion & Triage**:
  - Supports webhook ingestion from SIEMs (e.g., Wazuh) via unique GUID endpoints
  - YAML-based parsers for dynamic field mapping and enrichment
  - Advanced filtering, bulk actions, and tagging in the UI
- **Case Management**:
  - Full incident tracking with Summary, Tasks, IOCs, Notes, Timeline, Evidence, Connected Alerts
  - Optional playbook integration per case
- **Data Enrichment**:
  - Tagging, resolution status, severity mapping, parser-driven field expansion
  - Integration-ready for tools like MISP, OpenCTI, and Velociraptor
- **UI & UX**:
  - Responsive Bootstrap frontend with dark/light mode support
  - Dynamic filtering and bulk editing using modals
  - RESTful API-first design

---

## 🧩 Module Overview

| Module         | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| `Alerts`       | Central alert triage with parser-driven detail views, filters, bulk actions |
| `Cases`        | Incident handling hub with customizable workflows and linked data           |
| `Sources`      | Manage and monitor alert sources with unique webhook keys                   |
| `Parser Sandbox` | Upload and test YAML parsers against raw alert payloads                   |
| `Settings`     | Manage field display settings, parser files, and system options             |
| `Assets`       | Global and case-specific asset tracking and classification                  |
| `IRDB`         | Knowledge base for Indicators, TTPs, and Playbooks                          |

---

## 🛠️ Getting Started

1. **Clone the repository**

```bash
git clone https://github.com/codebarbarian/sentinel-commander.git
cd sentinel-commander
```

2. **Install requirements**
```bash
pip install -r requirements.txt
```

3. **Start the application**
```bash
uvicorn app.main:app --reload
```

## Project Structure
```bash
/app
├── api/                # FastAPI route handlers
│   ├── alerts.py
│   ├── cases.py
│   ├── sources.py
│   └── ...
├── core/               # DB config, utility functions
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic schemas
├── parsers/            # YAML parser config files
├── web/                # Web UI controllers
│   ├── alerts_view.py
│   ├── cases_view.py
│   ├── ...
└── templates/          # HTML templates and partials
```

## Contribution
We welcome contributions! Please fork the repo and open a PR. If you're implementing a new module, try to match the existing design and folder structure. Tests and YAML examples are appreciated.