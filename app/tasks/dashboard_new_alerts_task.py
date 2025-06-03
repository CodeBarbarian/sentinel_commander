import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.utils.sockets.broadcast import broadcast_dashboard_event
from sqlalchemy import desc
from app.models.alert import Alert
from app.utils.severity import SEVERITY_LABELS

async def broadcast_new_alerts_loop():
    latest_seen_id = None

    while True:
        try:
            db: Session = SessionLocal()
            latest_alert = db.query(Alert).order_by(desc(Alert.id)).first()

            if latest_alert:
                if latest_seen_id is None:
                    latest_seen_id = latest_alert.id
                elif latest_alert.id > latest_seen_id:
                    new_alerts = db.query(Alert).filter(Alert.id > latest_seen_id).order_by(Alert.id.asc()).all()
                    for alert in new_alerts:
                        severity_label = SEVERITY_LABELS.get(alert.severity, "Unknown")

                        await broadcast_dashboard_event({
                            "type": "new_alert",
                            "id": alert.id,
                            "severity": severity_label,  # Now a string!
                            "message": alert.message or "No message",
                        })

                        latest_seen_id = max(latest_seen_id, alert.id)

        except Exception as e:
            print("❌ Error broadcasting new alerts:", e)
        finally:
            db.close()

        await asyncio.sleep(1.0)
