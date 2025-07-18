import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import SessionLocal
from app.utils.sockets.broadcast import broadcast_dashboard_event
from app.models.alert import Alert
from app.utils.severity import SEVERITY_LABELS
from fastapi.encoders import jsonable_encoder
import logging

async def broadcast_open_alerts_loop():
    logger = logging.getLogger(__name__)

    while True:
        try:
            db: Session = SessionLocal()

            open_alerts = (
                db.query(Alert)
                .filter(Alert.status != "done")
                .order_by(desc(Alert.severity), desc(Alert.created_at))
                .all()
            )

            alert_list = []
            for alert in open_alerts:
                alert_list.append({
                    "id": alert.id,
                    "severity": SEVERITY_LABELS.get(alert.severity, "Unknown"),
                    "message": alert.message,  # Use existing field!
                    "status": alert.status,
                    "resolution": alert.resolution,
                    "created_at": alert.created_at.isoformat() if alert.created_at else None,
                })

            await broadcast_dashboard_event({
                "type": "open_alerts_update",
                "alerts": alert_list
            })

        except Exception as e:
            logger.exception("Error in broadcast_open_alerts_loop")
        finally:
            db.close()

        await asyncio.sleep(5)  # Or 10 seconds if less frequent updates are fine
