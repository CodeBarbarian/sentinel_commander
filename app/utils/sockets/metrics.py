from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.alert import Alert
from app.utils.severity import SEVERITY_MAP

def get_current_metrics(db: Session):
    return {
        "type": "metrics",
        "critical_alerts_count": db.query(func.count(Alert.id))
            .filter(Alert.severity.in_(SEVERITY_MAP["Critical"]), Alert.status == "new")
            .scalar(),
        "open_alerts_count": db.query(func.count(Alert.id))
            .filter(Alert.status == "new")
            .scalar(),
    }
