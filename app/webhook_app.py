from fastapi import FastAPI
from app.api import webhook
from app.core.database import Base, engine
from app.core.log_config import setup_logging

setup_logging()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sentinel Commander - Webhook Handler",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json"
)