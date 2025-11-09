from app.api import alerts
from app.web.alerts import alerts_view, alerts_detail_view, alerts_categories_view
from app.web.customers import customers_view
from app.web.dashboard import dashboard_view, ws_dashboard
from app.web.sentineliq import sentineliq_view
from app.web.settings import settings_view, settings_yaml_view
from app.web.sources import sources_view
from app.web.users import users_view, auth_view
from app.web.agents import agent_view, agent_detail_view

router_registry = [
    # API routes
    (alerts.router, "/api/v1"),

    # Web routes
    (agent_view.router, "/web/v1"),
    (agent_detail_view.router, "/web/v1"),
    (dashboard_view.router, "/web/v1"),
    (ws_dashboard.router, "/web/v1"),
    (alerts_categories_view.router, "/web/v1"),
    (alerts_view.router, "/web/v1"),
    (alerts_detail_view.router, "/web/v1"),
    (sources_view.router, "/web/v1"),
    (customers_view.router, "/web/v1"),
    (users_view.router, "/web/v1"),
    (auth_view.router, "/web/v1"),
    (settings_view.router, "/web/v1"),
    (settings_yaml_view.router, "/web/v1"),


    # SentinelIQ
    (sentineliq_view.router, "/web/v1"),
]
