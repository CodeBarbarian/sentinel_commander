# Sentinel Commander

> ⚠️ **Early Alpha Notice**  
> Sentinel Commander is currently in early alpha. While many core features are functional and actively used, the platform is under continuous development. Expect rapid iteration, breaking changes, and new modules arriving frequently.

**Sentinel Commander** is a modular, open-source platform for cybersecurity alert triage, case management, and response orchestration. Built for modern Security Operations Centers (SOCs), it helps analysts investigate, document, and respond to threats with structure and flexibility.

---

## Top 5 Features

1. **Alert Ingestion via Webhooks**
   - Accept alerts from any external system (e.g., Wazuh) using unique GUID-based webhook endpoints with API key validation.
   
2. **YAML-Based Parsing Engine**
   - Dynamic field mapping and enrichment through editable YAML parser files. Enables structured alert triage, classification, and display customization.

3. **Full-Stack Case Management**
   - Create structured incidents with tabs for Summary, Notes, Tasks, IOCs, Timeline, Evidence, and connected alerts. Supports tagging, severity mapping, and closing workflows.

4. **Triage-Centric UI**
   - Fast, filterable alert views with bulk actions, tagging, and severity badges. Modals for resolution editing, triage workflows, and parser previews.

5. **Parser Sandbox** - (Currently disabled)
   - Upload and test YAML parsers directly in the UI. Validate enrichment logic before applying to production data.

---

## Module Overview

| Module            | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| `Alerts`          | Parser-enhanced triage dashboard with filters, bulk actions, and severity logic |
| `Cases`           | Central incident tracking with linked alerts, tasks, IOCs, and evidence     |
| `Sources`         | Manage alert source integrations and monitor API usage via GUID webhooks   |
| `Parser Sandbox`  | Upload and validate YAML parsers for field mapping and enrichment           |
| `Settings`        | Manage visible fields, YAML files, and system-wide configuration            |
| `Assets`          | Track assets globally or link them to individual cases                      |
| `IRDB`            | Internal reference DB for Indicators, TTPs, and response playbooks          |

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/codebarbarian/sentinel_commander.git
cd sentinel_commander
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
#### 3.1 Development
```bash
uvicorn app.main:app --reload
```
#### 3.2 Production
Use the scripts as provided in the ```scripts``` directory.

## Updating
### 1. Stop the services
Stop Sentinel
```bash
./scripts/stop_sentinel.sh
```
Stop Webhook (Sometimes not needed)
```bash
./scripts/stop_webhook.sh
```
### 2. Pull the new source
```bash
git pull
```

### 3. Start all services
Start Sentinel
```bash
./scripts/start_sentinel.sh
```
Start Webhook (If not already running)
```bash
./scripts/start_webhook.sh
```
## Project Structure
```bash
/app
├── api/                # FastAPI route handlers for backend APIs
├── core/               # DB, logging, bootstrap logic
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic request/response schemas
├── webhook/            # Isolated webhook listener
├── parsers/            # YAML parser files for alert enrichment
├── web/                # UI route controllers (alerts, cases, etc.)
└── templates/          # Jinja2 templates (Bootstrap layout)
```

## Contributing
We welcome contributions!
Please fork the repo and open a pull request. If you're adding a new module, try to match the existing structure and styling. YAML parser examples, test coverage, and UI improvements are always appreciated.

Sentinel Commander is proudly open-source. Built for teams who need control, transparency, and full ownership over their security workflows.