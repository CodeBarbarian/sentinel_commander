import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.utils.sockets.broadcast import broadcast_dashboard_event
from sqlalchemy import desc
from app.models.alert import Alert

async def broadcast_new_alerts_loop():
    latest_seen_id = None

    while True:
        print("👀 Polling for new alerts... latest_seen_id =", latest_seen_id)
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

        await asyncio.sleep(0.5)