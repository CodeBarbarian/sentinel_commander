import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.utils.sockets.broadcast import broadcast_dashboard_event
from app.utils.metrics import get_current_metrics
from sqlalchemy import desc
from app.models.alert import Alert
from app.core.version import get_local_version, is_version_outdated

async def broadcast_metrics_loop():
    while True:
        try:
            # Create a new DB session (FastAPI dependency injection not available here)
            db: Session = SessionLocal()
            metrics = get_current_metrics(db)
            await broadcast_dashboard_event(metrics)
        except Exception as e:
            print("❌ Error broadcasting metrics:", e)
        finally:
            db.close()

        await asyncio.sleep(1)  # wait 1 second before next push



async def broadcast_new_alerts_loop():
    latest_seen_id = None

    while True:
        try:
            db: Session = SessionLocal()

            # Get the most recent alert
            latest_alert = db.query(Alert).order_by(desc(Alert.id)).first()

            if latest_alert:
                if latest_seen_id is None:
                    latest_seen_id = latest_alert.id  # Init only
                elif latest_alert.id > latest_seen_id:
                    # There is a new alert(s)
                    new_alerts = db.query(Alert).filter(Alert.id > latest_seen_id).order_by(Alert.id.asc()).all()
                    for alert in new_alerts:
                        await broadcast_dashboard_event({
                            "type": "new_alert",
                            "id": alert.id,
                            "severity": alert.severity,
                            "message": alert.message or "No message",
                        })
                        latest_seen_id = max(latest_seen_id, alert.id)

        except Exception as e:
            print("❌ Error broadcasting new alerts:", e)
        finally:
            db.close()

        await asyncio.sleep(1)



async def refresh_version_task(app):
    while True:
        try:
            app.state.version = get_local_version()
            app.state.version_outdated = is_version_outdated()
            print("🔄 Refreshed version info.")
        except Exception as e:
            print("❌ Failed to refresh version info:", e)
        await asyncio.sleep(300)  # every 5 minutes