import asyncio
from app.core.version import get_local_version, is_version_outdated

async def refresh_version_task(app):
    while True:
        try:
            app.state.version = get_local_version()
            app.state.version_outdated = is_version_outdated()
            print("🔄 Refreshed version info.")
        except Exception as e:
            print("❌ Failed to refresh version info:", e)
        await asyncio.sleep(300)  # every 5 minutes