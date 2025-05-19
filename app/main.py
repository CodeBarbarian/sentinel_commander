from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.database import Base, engine

# API's
from app.api import alerts
from app.api import webhook
from app.api import sources
from app.api import settings_parser
from app.api import parsers
from app.api import cases
from app.api import customers
from app.api import users

# Alerts View
from app.web.alerts import alerts_view, alerts_detail_view

# Dashboard view
from app.web.dashboard import dashboard_view

# Sources View
from app.web.sources import sources_view

# Settings View
from app.web.settings import settings_view

# Cases Views
from app.web.cases import cases_view
from app.web.cases import cases_detail_view
from app.web.cases import cases_note_view
from app.web.cases import cases_task_view
from app.web.cases import cases_ioc_view
from app.web.cases import cases_alerts_view
from app.web.cases import cases_assets_view
from app.web.cases import cases_evidence_view
from app.web.cases import cases_playbooks_view


from app.web.assets import assets_view
from app.web.iocs import iocs_view
from app.web.playbooks import playbooks_view
from app.web.sentineliq import sentineliq_view
from app.web.customers import customers_view
from app.web.users import users_view
from app.web.users import auth_view

from datetime import datetime
import app.models
# Bootstrap:
from app.core.bootstrap import ensure_internal_source, init_data
from starlette.middleware.sessions import SessionMiddleware

# Create all tables in the DB
Base.metadata.create_all(bind=engine)

# Run bootstrap (will only do anything if DB is empty)
ensure_internal_source()
init_data()

app = FastAPI(title="Sentinel IR")
app.add_middleware(SessionMiddleware, secret_key="CHANGE_ME_TO_SOMETHING_RANDOM")
# Webhook / Main Entrypoint for alerts
app.include_router(webhook.router, tags=["Webhook"])

# API's
app.include_router(alerts.router, prefix="/api/v1", tags=["Alerts API"])
app.include_router(sources.router, prefix="/api/v1", tags=["Sources API"])
app.include_router(settings_parser.router, prefix="/api/v1", tags=["Settings Parser API"])
app.include_router(parsers.router, prefix="/api/v1", tags=["Parsers API"])
app.include_router(cases.router, prefix="/api/v1", tags=["Cases API"])
app.include_router(customers.router, prefix="/api/v1", tags=["Customers API"])
app.include_router(users.router, prefix="/api/v1", tags=["Users API"])

# Sentinel IQ
app.include_router(sentineliq_view.router, prefix="/web/v1", tags=["SentinelIQ"])


# Dashboard
app.include_router(dashboard_view.router, prefix="/web/v1", tags=["Dashboard"])

# Alerts
app.include_router(alerts_view.router, prefix="/web/v1", tags=["Alerts"])
app.include_router(alerts_detail_view.router, prefix="/web/v1", tags=["Alerts"])

# Sources
app.include_router(sources_view.router, prefix="/web/v1", tags=["Sources"])

# Assets
app.include_router(assets_view.router, prefix="/web/v1", tags=["Assets"])

# IOCs
app.include_router(iocs_view.router, prefix="/web/v1", tags=["IOCs"])

# Settings
app.include_router(settings_view.router, prefix="/web/v1", tags=["Settings"])

# Users
app.include_router(users_view.router, prefix="/web/v1", tags=["Users"])
app.include_router(auth_view.router, prefix="/web/v1", tags=["Users"])
# Playbooks
app.include_router(playbooks_view.router, prefix="/web/v1", tags=["Playbooks"])

# Customers
app.include_router(customers_view.router, prefix="/web/v1", tags=["Customers"])

# Cases Routers
app.include_router(cases_view.router, prefix="/web/v1", tags=["Cases View"])
app.include_router(cases_detail_view.router, prefix="/web/v1", tags=["Cases Detail View"])
app.include_router(cases_note_view.router, prefix="/web/v1", tags=["Cases"])
app.include_router(cases_task_view.router, prefix="/web/v1", tags=["Cases"])
app.include_router(cases_ioc_view.router, prefix="/web/v1", tags=["Cases"])
app.include_router(cases_alerts_view.router, prefix="/web/v1", tags=["Cases"])
app.include_router(cases_assets_view.router, prefix="/web/v1", tags=["Cases"])
app.include_router(cases_evidence_view.router, prefix="/web/v1", tags=["Cases"])
app.include_router(playbooks_view.router, prefix="/web/v1", tags=["Cases"])

# (Optional)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# Templates
templates = Jinja2Templates(directory="app/templates")

def format_datetime(value, format="%Y-%m-%d %H:%M:%S"):
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime(format)
    except Exception:
        return value  # fallback if formatting fails

templates.env.filters["datetime"] = format_datetime

