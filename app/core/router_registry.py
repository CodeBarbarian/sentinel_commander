from app.api import alerts, sources, settings_parser, parsers, cases, customers, users, publisher
from app.web.alerts import alerts_view, alerts_detail_view, alerts_categories_view
from app.web.assets import assets_view
from app.web.cases import (
    cases_view, cases_detail_view, cases_note_view, cases_task_view,
    cases_ioc_view, cases_alerts_view, cases_assets_view,
    cases_evidence_view, cases_playbooks_view
)
from app.web.customers import customers_view
from app.web.dashboard import dashboard_view, ws_dashboard
from app.web.iocs import iocs_view
from app.web.modules import modules_view, maxmind_module
from app.web.playbooks import playbooks_view
from app.web.sentineliq import sentineliq_view, sentineliq_search_view, sentineliq_publisher_view, sentineliq_enrichment_view
from app.web.settings import settings_view, settings_yaml_view
from app.web.sources import sources_view
from app.web.users import users_view, auth_view
from app.web.agents import agent_view, agent_detail_view

router_registry = [
    # API routes
    #(alerts.router, "/api/v1"),
    #(sources.router, "/api/v1"),
    #(settings_parser.router, "/api/v1"),
    #(parsers.router, "/api/v1"),
    #(cases.router, "/api/v1"),
    #(customers.router, "/api/v1"),
    #(users.router, "/api/v1"),
    #(publisher.router, "/api/v1"),

    # Web routes
    (agent_view.router, "/web/v1"),
    (agent_detail_view.router, "/web/v1"),
    (dashboard_view.router, "/web/v1"),
    (ws_dashboard.router, "/web/v1"),
    (alerts_categories_view.router, "/web/v1"),
    (alerts_view.router, "/web/v1"),
    (alerts_detail_view.router, "/web/v1"),
    (sources_view.router, "/web/v1"),
    (assets_view.router, "/web/v1"),
    (iocs_view.router, "/web/v1"),
    (playbooks_view.router, "/web/v1"),
    (customers_view.router, "/web/v1"),
    (users_view.router, "/web/v1"),
    (auth_view.router, "/web/v1"),
    (settings_view.router, "/web/v1"),
    (settings_yaml_view.router, "/web/v1"),
    (modules_view.router, "/web/v1"),
    (maxmind_module.router, "/web/v1"),

    # SentinelIQ
    (sentineliq_view.router, "/web/v1"),
    (sentineliq_search_view.router, "/web/v1"),
    (sentineliq_publisher_view.router, "/web/v1"),
    (sentineliq_enrichment_view.router, "/web/v1"),

    # Cases
    (cases_view.router, "/web/v1"),
    (cases_detail_view.router, "/web/v1"),
    (cases_note_view.router, "/web/v1"),
    (cases_task_view.router, "/web/v1"),
    (cases_ioc_view.router, "/web/v1"),
    (cases_alerts_view.router, "/web/v1"),
    (cases_assets_view.router, "/web/v1"),
    (cases_evidence_view.router, "/web/v1"),
    (cases_playbooks_view.router, "/web/v1"),
]
