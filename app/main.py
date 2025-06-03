from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
import asyncio
from app.utils.sockets.metrics_task import broadcast_metrics_loop, broadcast_new_alerts_loop, refresh_version_task
from contextlib import asynccontextmanager
from app.core.log_config import setup_logging
from app.core.database import Base, engine
from app.core.version import get_local_version, is_version_outdated
from app.core.router_registry import router_registry
from app.core.bootstrap import ensure_internal_source, init_data

# Init
setup_logging()
Base.metadata.create_all(bind=engine)
ensure_internal_source()
init_data()

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(broadcast_metrics_loop())
    asyncio.create_task(broadcast_new_alerts_loop())
    asyncio.create_task(refresh_version_task(app))
    yield

# App
app = FastAPI(title="Sentinel Commander", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="CHANGE_ME_TO_SOMETHING_RANDOM")

# Routers
for router, prefix in router_registry:
    app.include_router(router, prefix=prefix)

# Static
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def format_datetime(value, format="%Y-%m-%d %H:%M:%S"):
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime(format)
    except Exception:
        return value

templates.env.filters["datetime"] = format_datetime

# Root
@app.get("/")
async def root_redirect(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/web/v1/dashboard")
    return RedirectResponse(url="/web/v1/login")

@app.middleware("http")
async def attach_version_to_request(request: Request, call_next):
    request.state.version = request.app.state.version
    request.state.version_outdated = request.app.state.version_outdated
    return await call_next(request)


