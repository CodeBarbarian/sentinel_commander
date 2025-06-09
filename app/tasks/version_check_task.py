import asyncio
from app.core.version import get_local_version, is_version_outdated
import logging

logger = logging.getLogger(__name__)

async def refresh_version_task(app):
    while True:
        try:
            app.state.version = get_local_version()
            app.state.version_outdated = is_version_outdated()
            logger.info("Refreshed version info.")
        except Exception as e:
            logger.error("Failed to refresh version info:", e)
        await asyncio.sleep(300)  # every 5 minutes