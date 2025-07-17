import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.utils.sockets.broadcast import broadcast_dashboard_event
from app.utils.sockets.metrics import get_current_metrics
import logging

async def broadcast_metrics_loop():

    logger = logging.getLogger(__name__)
    while True:
        try:
            # Create a new DB session (FastAPI dependency injection not available here)
            db: Session = SessionLocal()
            metrics = get_current_metrics(db)
            await broadcast_dashboard_event(metrics)
        except Exception as e:
            logger.error("Error broadcasting metrics:", e)
        finally:
            db.close()

        await asyncio.sleep(1)  # wait 1 second before next push